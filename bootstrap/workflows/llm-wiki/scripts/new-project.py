#!/usr/bin/env python3
"""
new-project.py — bootstrap a new project with the LLM-wiki framework.

Runs in two phases:

  --phase A  : global install (skills + scripts + templates + config + agentmemory)
  --phase B  : per-project scaffold (folder + git + wiki-init + CLAUDE.md/README/.gitignore)

Both phases are idempotent. Phase A checks state before doing work; running
it twice is a no-op if everything is already installed. Phase B refuses to
overwrite an existing project folder unless --force is passed.

Discovery is the calling skill's job (`new-project/SKILL.md`); this script
runs once the user has confirmed.

Exit codes:
  0  success
  1  unrecoverable error
  2  restart required (Claude Code must restart before Phase B can run)
  3  user cancelled
"""

import argparse
import json
import shutil
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

# Force UTF-8 on Windows so emoji / unicode in templates don't crash printing
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


# ---------- Paths and defaults ----------

# Claude Code (global)
CC_DIR = Path.home() / ".claude"
CC_SKILLS_DIR = CC_DIR / "skills"
CC_SCRIPTS_DIR = CC_DIR / "wiki-scripts"
CC_TEMPLATES_DIR = CC_DIR / "wiki-templates"
CC_CONFIG_PATH = CC_DIR / "wiki-config.json"
CC_SETTINGS_PATH = CC_DIR / "settings.json"

# Cursor (per-project; populated when --tool cursor)
# These get computed relative to --target-folder at runtime
def cursor_paths(target: Path):
    wiki_root = target / ".wiki"
    return {
        "skills": wiki_root / "skills",
        "scripts": wiki_root / "scripts",
        "templates": wiki_root / "templates",
        "config": wiki_root / "config.json",
        "settings": target / ".cursor" / "mcp.json",
        "rules": target / ".cursor" / "rules",
    }


def install_paths(tool: str, target: Path | None = None):
    """Return install paths dict for the chosen tool. For cursor, target must be provided."""
    if tool == "claude-code":
        return {
            "skills": CC_SKILLS_DIR,
            "scripts": CC_SCRIPTS_DIR,
            "templates": CC_TEMPLATES_DIR,
            "config": CC_CONFIG_PATH,
            "settings": CC_SETTINGS_PATH,
            "rules": None,
        }
    if tool == "cursor":
        if target is None:
            raise ValueError("cursor install requires --target-folder")
        return cursor_paths(target)
    raise ValueError(f"unknown tool: {tool}")


DEFAULT_VAULT_ROOT_HINT = "docker/shared/openclaw/vault/wikis"
DEFAULT_DRIVE_PARENT = "__FOR CLAUDE"

# Skills that travel — keep in sync with INSTALL-INVENTORY.md
TRAVEL_SKILLS = [
    "new-project", "wrap-up",
    "wiki-init", "wiki-update", "wiki-search", "wiki-cycle",
    "wiki-discover", "wiki-list", "wiki-claims", "wiki-refresh",
    "wiki-report", "wiki-lint", "wiki-promote",
]

# Scripts that travel — kept in sync with the actual contents of
# bootstrap/workflows/llm-wiki/scripts/. Verified via build-wiki-package.py
# on each release. wiki-promote.py is intentionally OMITTED until the
# /wiki-promote skill grows a backing script.
TRAVEL_SCRIPTS = [
    "new-project.py",
    "wiki-init.py",
    "wiki-fetch-drive-folder.py",
    "wiki-fetch-pdf.py",
    "wiki-fetch-youtube.py",
    "wiki-index.py",
    "wiki-index-per-folder.py",
    "wiki-lint-mechanical.py",
    "wiki-list-add.py",
    "wiki-list-process.py",
    "wiki-list-render.py",
    "wiki-map-compile.py",
    "wiki-reciprocate-backlinks.py",
    "wiki-update.py",
]

# Folder taxonomies per project type
TAXONOMY = {
    "research": [
        "active", "long-term", "tooling", "best-practices",
        "implementation", "skills", "orchestration", "interesting-docs",
    ],
    "development": [
        "components", "decisions", "architecture", "patterns",
        "troubleshooting", "best-practices",
    ],
}


# ---------- Helpers ----------

def _info(msg):
    print(f"[new-project] {msg}", file=sys.stderr)


def _ok(msg):
    print(f"[new-project] ✓ {msg}", file=sys.stderr)


def _warn(msg):
    print(f"[new-project] ! {msg}", file=sys.stderr)


def _err(msg):
    print(f"[new-project] ✗ {msg}", file=sys.stderr)


def _load_config(config_path: Path = CC_CONFIG_PATH):
    """Read wiki-config.json or return None if absent."""
    if config_path.exists():
        try:
            return json.loads(config_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError) as e:
            _warn(f"wiki-config.json at {config_path} unreadable ({e}); treating as first-time")
            return None
    return None


def _save_config(cfg, config_path: Path = CC_CONFIG_PATH):
    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text(
        json.dumps(cfg, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    _ok(f"wrote {config_path}")


def _copy_tree(src: Path, dst: Path, names=None, dry_run=False):
    """Copy contents of src to dst. If names is given, only copy those
    top-level entries. Existing files in dst are overwritten only if
    bootstrap is newer (mtime). Returns (copied, skipped) counts."""
    src = Path(src)
    dst = Path(dst)
    if not src.exists():
        _warn(f"source missing: {src}")
        return 0, 0
    dst.mkdir(parents=True, exist_ok=True)

    if names is None:
        names = [p.name for p in src.iterdir()]

    copied = 0
    skipped = 0
    for name in names:
        s = src / name
        d = dst / name
        if not s.exists():
            continue
        if s.is_dir():
            # Recurse
            sub_copied, sub_skipped = _copy_tree(s, d, dry_run=dry_run)
            copied += sub_copied
            skipped += sub_skipped
        else:
            if d.exists() and d.stat().st_mtime >= s.stat().st_mtime:
                skipped += 1
                continue
            if dry_run:
                print(f"  WOULD copy {s} -> {d}")
            else:
                d.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(s, d)
            copied += 1
    return copied, skipped


def _slugify(text):
    """Lowercase, hyphenate, ASCII-safe."""
    import re
    s = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return s or "untitled"


def _derive_bootstrap_source(args):
    """Find the workflows-core bootstrap path. Checks in order: --bootstrap-source
    arg, wiki-config.json bootstrap_source, walking up from script location,
    walking up from CWD looking for `.git` + `bootstrap/workflows/llm-wiki`."""
    if args.bootstrap_source:
        return Path(args.bootstrap_source).resolve()

    cfg = _load_config()
    if cfg and cfg.get("bootstrap_source"):
        return Path(cfg["bootstrap_source"]).resolve()

    # Try: am I inside a workflows-core checkout?
    here = Path(__file__).resolve()
    for parent in [here.parent, *here.parents]:
        candidate = parent / "bootstrap" / "workflows" / "llm-wiki"
        if candidate.is_dir():
            return parent.resolve()

    cwd_root = Path.cwd()
    for parent in [cwd_root, *cwd_root.parents]:
        candidate = parent / "bootstrap" / "workflows" / "llm-wiki"
        if candidate.is_dir():
            return parent.resolve()

    return None


# ---------- Phase A ----------

def phase_a(args):
    """Global install: skills + scripts + templates + config + agentmemory (dev)."""
    bootstrap = _derive_bootstrap_source(args)
    if not bootstrap:
        _err("could not find workflows-core bootstrap. Pass --bootstrap-source <path>.")
        return 1
    _info(f"bootstrap source: {bootstrap}")
    _info(f"tool: {args.tool}")

    # Resolve install paths per tool. For cursor we need --target-folder up front
    # so we can land everything inside the per-project .wiki/ folder.
    target = Path(args.target_folder).resolve() if args.target_folder else None
    if args.tool == "cursor" and target is None:
        _err("cursor install requires --target-folder (Cursor has no global skills dir)")
        return 1
    paths = install_paths(args.tool, target=target)

    if args.tool == "cursor":
        _warn("Cursor adapter is partial: skills will be copied as-is (CC SKILL.md format).")
        _warn("Until adapters/cursor/ generates .mdc rules, you'll invoke these manually.")

    skills_src = bootstrap / "bootstrap" / "workflows" / "llm-wiki" / "skills"
    scripts_src = bootstrap / "bootstrap" / "workflows" / "llm-wiki" / "scripts"
    templates_src = bootstrap / "bootstrap" / "workflows" / "llm-wiki" / "templates"

    # A2 — copy skills
    _info(f"copying skills: {skills_src} -> {paths['skills']}")
    c, s = _copy_tree(skills_src, paths["skills"], names=TRAVEL_SKILLS, dry_run=args.dry_run)
    _ok(f"skills: {c} copied, {s} unchanged")

    # A3 — copy scripts
    _info(f"copying scripts: {scripts_src} -> {paths['scripts']}")
    c, s = _copy_tree(scripts_src, paths["scripts"], names=TRAVEL_SCRIPTS, dry_run=args.dry_run)
    _ok(f"scripts: {c} copied, {s} unchanged")

    # A4 — copy templates
    _info(f"copying templates: {templates_src} -> {paths['templates']}")
    c, s = _copy_tree(templates_src, paths["templates"], dry_run=args.dry_run)
    _ok(f"templates: {c} copied, {s} unchanged")

    # A5 — write wiki-config.json (location depends on tool)
    cfg = _load_config(paths["config"]) or {}
    vault_root = args.vault_root or cfg.get("vault_root") or str(bootstrap / DEFAULT_VAULT_ROOT_HINT)
    cfg.update({
        "tool": args.tool,
        "vault_root": str(Path(vault_root).resolve()),
        "skills_installed_at": str(paths["skills"]),
        "scripts_installed_at": str(paths["scripts"]),
        "templates_installed_at": str(paths["templates"]),
        "bootstrap_source": str(bootstrap),
        "install_version": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        "last_phase_a": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    })
    # Drive config: persist if user opted in. wiki-fetch-drive-folder.py reads this.
    if args.drive_enabled == "yes":
        cfg["drive"] = {
            "enabled": True,
            "parent_folder": args.drive_parent_folder or DEFAULT_DRIVE_PARENT,
        }
    elif args.drive_enabled == "no":
        cfg["drive"] = {"enabled": False}
    # else: leave drive config untouched (Phase A re-run shouldn't clobber it)

    if args.dry_run:
        print(f"WOULD write wiki-config.json to {paths['config']}: {json.dumps(cfg, indent=2)}")
    else:
        _save_config(cfg, paths["config"])

    # A5.5 — Drive OAuth walkthrough (if Drive ingest enabled)
    if args.drive_enabled == "yes":
        if args.dry_run:
            print("WOULD walk user through Drive OAuth (if token not already cached)")
        else:
            ok = _drive_oauth_walkthrough(paths["scripts"])
            if not ok:
                _warn("Drive auth did not complete. /new-project will continue,")
                _warn("but Drive ingest won't work until you re-run /new-project --sync")
                _warn("with valid client_secrets.json in place.")

    needs_restart = False

    # A6, A7 — agentmemory (development only)
    if args.project_type == "development":
        if _agentmemory_wired(paths["settings"]) and _agentmemory_reachable():
            _ok("agentmemory already installed + wired")
        else:
            _info("agentmemory: install + wire")
            if args.dry_run:
                print("WOULD run: npx @agentmemory/agentmemory (background)")
                print(f"WOULD merge agentmemory MCP entry into {paths['settings']}")
            else:
                ok = _install_agentmemory()
                if not ok:
                    _err("agentmemory install failed; surface this to user and abort")
                    return 1
                _merge_agentmemory_mcp(paths["settings"], tool=args.tool)
                needs_restart = True
                cfg["agentmemory_wired"] = True
                _save_config(cfg, paths["config"])

    if needs_restart:
        restart_target = "Claude Code" if args.tool == "claude-code" else "Cursor"
        _info("===========================================")
        _info("RESTART REQUIRED")
        _info(f"{restart_target} must restart to pick up the new MCP server.")
        _info(f"Restart {restart_target}, then re-run /new-project to continue with Phase B.")
        _info("===========================================")
        return 2

    return 0


def _agentmemory_wired(settings_path: Path = CC_SETTINGS_PATH):
    """Check if settings file has an agentmemory MCP entry."""
    if not settings_path.exists():
        return False
    try:
        data = json.loads(settings_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return False
    return bool(data.get("mcpServers", {}).get("agentmemory"))


def _agentmemory_reachable():
    """HTTP probe agentmemory's /livez endpoint. Returns False on any failure."""
    import urllib.request
    import urllib.error
    for port in (7890, 7891, 3000):  # try a few common ports
        try:
            req = urllib.request.Request(f"http://localhost:{port}/livez", method="GET")
            with urllib.request.urlopen(req, timeout=2) as resp:
                if resp.status == 200:
                    return True
        except (urllib.error.URLError, OSError):
            continue
    return False


def _install_agentmemory():
    """Run `npx @agentmemory/agentmemory` and wait for /livez. Returns True on success."""
    _info("starting agentmemory via npx (this may take a minute on first run)...")
    try:
        # Start as a detached background process — npx will pull + run the server
        # On Windows we don't have a clean detach; use Popen and let it run.
        proc = subprocess.Popen(
            ["npx", "-y", "@agentmemory/agentmemory"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except FileNotFoundError:
        _err("npx not found on PATH. Install Node.js first: https://nodejs.org/")
        return False

    # Poll /livez for up to 90 seconds
    for i in range(45):
        if _agentmemory_reachable():
            _ok("agentmemory server is up")
            return True
        time.sleep(2)
    _err("agentmemory did not respond on /livez within 90s")
    return False


def _merge_agentmemory_mcp(settings_path: Path = CC_SETTINGS_PATH, tool: str = "claude-code"):
    """Add an agentmemory entry to mcpServers in the right settings file.
    Format is identical for claude-code and cursor (both use mcpServers map).
    Preserves existing entries."""
    if settings_path.exists():
        try:
            data = json.loads(settings_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            data = {}
    else:
        data = {}
    mcp = data.setdefault("mcpServers", {})
    # Canonical entry per the wiki's implementation/agentmemory-setup.md.
    mcp["agentmemory"] = {
        "command": "npx",
        "args": ["-y", "@agentmemory/agentmemory-mcp"],
    }
    settings_path.parent.mkdir(parents=True, exist_ok=True)
    settings_path.write_text(
        json.dumps(data, indent=2),
        encoding="utf-8",
    )
    _ok(f"merged agentmemory entry into {settings_path}")


# ---------- Google Drive OAuth walkthrough ----------

DRIVE_TOKEN_PATH = Path.home() / ".config" / "wiki-cycle" / "drive-token.json"
DRIVE_CLIENT_SECRETS_PATH = Path.home() / ".config" / "wiki-cycle" / "client_secrets.json"
DRIVE_FULL_SCOPE = "https://www.googleapis.com/auth/drive"


def _drive_token_status():
    """Returns ('ok', scopes), ('wrong_scope', scopes), or ('missing', None)."""
    if not DRIVE_TOKEN_PATH.exists():
        return "missing", None
    try:
        data = json.loads(DRIVE_TOKEN_PATH.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return "missing", None
    scopes = data.get("scopes") or []
    if DRIVE_FULL_SCOPE in scopes:
        return "ok", scopes
    return "wrong_scope", scopes


def _drive_oauth_walkthrough(scripts_dir: Path):
    """Trigger OAuth via wiki-fetch-drive-folder.py in --auth-only mode.

    If the helper script doesn't support --auth-only yet, fall back to a
    minimal probe call that forces the OAuth dance to run.
    """
    status, scopes = _drive_token_status()
    if status == "ok":
        _ok(f"Drive auth already configured (full drive scope cached at {DRIVE_TOKEN_PATH})")
        return True

    if status == "wrong_scope":
        _warn(f"Drive token cached with wrong scopes: {scopes}")
        _info(f"Removing stale token at {DRIVE_TOKEN_PATH} to force re-auth")
        try:
            DRIVE_TOKEN_PATH.unlink()
        except OSError as e:
            _err(f"could not delete stale token: {e}")
            return False

    if not DRIVE_CLIENT_SECRETS_PATH.exists():
        _err("============================================================")
        _err("Drive OAuth client secrets not found.")
        _err(f"Expected at: {DRIVE_CLIENT_SECRETS_PATH}")
        _err("")
        _err("To enable Drive ingest, create OAuth credentials:")
        _err("  1. https://console.cloud.google.com/apis/credentials")
        _err("  2. Create Project → Enable Drive API → Create OAuth Client ID")
        _err("     (Desktop application)")
        _err(f"  3. Download JSON → save as {DRIVE_CLIENT_SECRETS_PATH}")
        _err("  4. Re-run /new-project --sync to complete Drive setup.")
        _err("============================================================")
        return False

    fetch_script = scripts_dir / "wiki-fetch-drive-folder.py"
    if not fetch_script.exists():
        _err(f"wiki-fetch-drive-folder.py not found at {fetch_script}")
        return False

    _info("============================================================")
    _info("Drive OAuth: a browser window will open shortly.")
    _info("Sign in with the Google account that holds your __FOR CLAUDE folder.")
    _info("Approve the 'See, edit, create, and delete all of your Google Drive files' scope.")
    _info("After the 'authentication complete' page, return to this terminal.")
    _info("============================================================")

    # --auth-only: run OAuth, cache full-drive-scope token, exit.
    # No folder listing, no queueing, no file moves.
    try:
        result = subprocess.run(
            [sys.executable, str(fetch_script), "--auth-only"],
            capture_output=True, text=True, timeout=300,
        )
        if result.returncode == 0:
            new_status, _ = _drive_token_status()
            if new_status == "ok":
                _ok("Drive auth complete — token cached with full drive scope")
                return True
            _warn("auth-only exited 0 but token not cached at expected path")
            return False
        _warn(f"Drive --auth-only exited {result.returncode}")
        _warn(f"stderr: {result.stderr[:400]}")
        return False
    except subprocess.TimeoutExpired:
        _err("Drive OAuth timed out after 5 minutes")
        return False


# ---------- Phase B ----------

def phase_b(args):
    """Per-project scaffold: folder + git + wiki-init + CLAUDE.md/README/.gitignore."""
    target = Path(args.target_folder).resolve() if args.target_folder else None
    paths = install_paths(args.tool, target=target)
    cfg = _load_config(paths["config"])
    if not cfg:
        _err(f"no wiki-config.json at {paths['config']} — run --phase A first.")
        return 1

    name = _slugify(args.project_name or "")
    if not name:
        _err("--project-name is required")
        return 1
    if target is None:
        _err("--target-folder is required")
        return 1
    if target.exists() and any(target.iterdir()) and not args.force:
        _err(f"target folder {target} exists and is not empty (use --force to override)")
        return 1

    description = args.project_description or ""
    project_type = args.project_type
    if project_type not in TAXONOMY:
        _err(f"--project-type must be 'research' or 'development', got {project_type!r}")
        return 1

    vault_root = Path(cfg["vault_root"])

    # B1 — mkdir + git init
    _info(f"creating project folder: {target}")
    if args.dry_run:
        print(f"WOULD mkdir {target} + git init")
    else:
        target.mkdir(parents=True, exist_ok=True)
        if not (target / ".git").exists():
            subprocess.run(["git", "init"], cwd=target, capture_output=True, text=True)
        _ok(f"project folder ready: {target}")

    # B2 — wiki-init
    wiki_init = Path(cfg["scripts_installed_at"]) / "wiki-init.py"
    if not wiki_init.exists():
        # Fall back to bootstrap copy
        wiki_init = Path(cfg["bootstrap_source"]) / "bootstrap" / "workflows" / "llm-wiki" / "scripts" / "wiki-init.py"
    _info(f"running wiki-init for topic {name}")
    cmd = [
        sys.executable, str(wiki_init),
        "--topic", name,
        "--description", description or f"{name} project wiki",
        "--vault", str(vault_root),
    ]
    if args.dry_run:
        print(f"WOULD run: {' '.join(cmd)}")
    else:
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            _warn(f"wiki-init exited {result.returncode}: {result.stderr}")
        else:
            _ok(f"wiki topic created: {vault_root / name}")

    # Apply project-type folder taxonomy (wiki-init writes a default; we override)
    folders = TAXONOMY[project_type]
    topic_root = vault_root / name
    for sub in folders:
        path = topic_root / "wiki" / sub
        if args.dry_run:
            print(f"WOULD mkdir {path}")
        else:
            path.mkdir(parents=True, exist_ok=True)
    # Also create raw/sessions/ for development wrap-ups
    if project_type == "development":
        sessions_dir = topic_root / "raw" / "sessions"
        if args.dry_run:
            print(f"WOULD mkdir {sessions_dir}")
        else:
            sessions_dir.mkdir(parents=True, exist_ok=True)

    # B3, B4, B5 — render templates
    templates_dir = Path(cfg["templates_installed_at"])
    _render_template(
        templates_dir / f"CLAUDE.md.{project_type}.tmpl",
        target / "CLAUDE.md",
        {
            "PROJECT_NAME": name,
            "PROJECT_DESCRIPTION": description,
            "VAULT_TOPIC_PATH": str(topic_root).replace("\\", "/"),
            "PROJECT_TYPE": project_type,
        },
        args.dry_run,
    )
    _render_template(
        templates_dir / f"README.md.{project_type}.tmpl",
        target / "README.md",
        {
            "PROJECT_NAME": name,
            "PROJECT_DESCRIPTION": description,
            "VAULT_TOPIC_PATH": str(topic_root).replace("\\", "/"),
            "PROJECT_TYPE": project_type,
        },
        args.dry_run,
    )
    _render_template(
        templates_dir / ".gitignore.tmpl",
        target / ".gitignore",
        {"PROJECT_TYPE": project_type},
        args.dry_run,
    )

    # B6 — record per-project Drive subfolder + register project in global config
    drive_subfolder = args.drive_subfolder if args.drive_subfolder is not None else name
    drive_cfg = cfg.get("drive") or {}
    if drive_cfg.get("enabled") and drive_subfolder:
        projects = cfg.setdefault("projects", {})
        projects[name] = {
            "target_folder": str(target),
            "topic_root": str(topic_root),
            "project_type": project_type,
            "drive_subfolder": drive_subfolder,
            "created": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        }
        if args.dry_run:
            print(f"WOULD register project {name} (Drive subfolder: {drive_subfolder}) in {paths['config']}")
        else:
            _save_config(cfg, paths["config"])
            _ok(f"project registered; Drive ingest will pull from {drive_cfg.get('parent_folder', DEFAULT_DRIVE_PARENT)}/{drive_subfolder}/")
    elif drive_cfg.get("enabled") is False:
        _info("Drive ingest disabled for this install — skip /wiki-cycle drive fetch")

    # B7 — summary
    start_cmd = "claude  # start a Claude Code session here" if args.tool == "claude-code" else "cursor .  # open in Cursor"
    print(json.dumps({
        "status": "ok",
        "phase": "B",
        "tool": args.tool,
        "project_name": name,
        "project_type": project_type,
        "target_folder": str(target),
        "wiki_topic_root": str(topic_root),
        "wiki_folders": folders,
        "drive_enabled": bool(drive_cfg.get("enabled")),
        "drive_subfolder": drive_subfolder if drive_cfg.get("enabled") else None,
        "agentmemory_wired": cfg.get("agentmemory_wired", False) if project_type == "development" else None,
        "next_steps": [
            f"cd {target}",
            start_cmd,
            "/wrap-up at session-end to crystallize work into wiki entries",
            "/wiki-search to look up prior decisions/components",
        ],
    }, indent=2))
    return 0


def _render_template(src: Path, dst: Path, vars: dict, dry_run: bool):
    if not src.exists():
        _warn(f"template missing: {src}")
        return
    text = src.read_text(encoding="utf-8")
    for k, v in vars.items():
        text = text.replace(f"{{{{{k}}}}}", v)
    if dry_run:
        print(f"WOULD write {dst} ({len(text)} chars)")
    else:
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_text(text, encoding="utf-8")
        _ok(f"wrote {dst}")


# ---------- Main ----------

def main():
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--phase", choices=["A", "B", "sync"], required=True)
    parser.add_argument("--tool", choices=["claude-code", "cursor"], default="claude-code",
                        help="Which AI tool to install for (default: claude-code)")
    parser.add_argument("--project-name")
    parser.add_argument("--project-description", default="")
    parser.add_argument("--project-type", choices=["research", "development"])
    parser.add_argument("--target-folder")
    parser.add_argument("--bootstrap-source", help="Path to workflows-core checkout")
    parser.add_argument("--vault-root", help="Override vault root (default: bootstrap/docker/shared/openclaw/vault/wikis)")
    parser.add_argument("--drive-enabled", choices=["yes", "no"], default=None,
                        help="Enable Google Drive ingest? Triggers OAuth walkthrough if 'yes'.")
    parser.add_argument("--drive-parent-folder", default=None,
                        help=f"Parent Drive folder for ingest (default: {DEFAULT_DRIVE_PARENT})")
    parser.add_argument("--drive-subfolder", default=None,
                        help="Per-project Drive subfolder (default: project slug)")
    parser.add_argument("--force", action="store_true", help="Overwrite non-empty target folder")
    parser.add_argument("--dry-run", action="store_true", help="Print actions without writing")
    args = parser.parse_args()

    if args.phase == "A":
        return phase_a(args)
    if args.phase == "B":
        return phase_b(args)
    if args.phase == "sync":
        # Same as Phase A but only the copy + config steps (no agentmemory)
        args.project_type = "research"  # sync doesn't need dev-specific work
        return phase_a(args)


if __name__ == "__main__":
    sys.exit(main())
