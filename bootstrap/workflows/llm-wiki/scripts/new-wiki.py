#!/usr/bin/env python3
"""
new-wiki.py — bootstrap a new project with the LLM-wiki framework.

Runs in two phases:

  --phase A  : global install (skills + scripts + templates + config + agentmemory)
  --phase B  : per-project scaffold (folder + git + wiki-init + CLAUDE.md/README/.gitignore)

Both phases are idempotent. Phase A checks state before doing work; running
it twice is a no-op if everything is already installed. Phase B refuses to
overwrite an existing project folder unless --force is passed.

Discovery is the calling skill's job (`new-wiki/SKILL.md`); this script
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

# Global Claude Code path — used only for the ONE creator skill (/new-wiki)
# that lives globally so users can invoke it from anywhere. Everything else
# is per-project.
CC_GLOBAL_DIR = Path.home() / ".claude"
CC_GLOBAL_SKILLS_DIR = CC_GLOBAL_DIR / "skills"
CC_GLOBAL_CONFIG_PATH = CC_GLOBAL_DIR / "wiki-config.json"
CC_GLOBAL_SETTINGS_PATH = CC_GLOBAL_DIR / "settings.json"


def project_paths(tool: str, target: Path) -> dict:
    """Per-project install layout. Always rooted at --target-folder.

    Layout for claude-code:
      <target>/.claude/skills/         ← runnable skills (Claude Code auto-loads)
      <target>/.claude/wiki-scripts/   ← Python helpers
      <target>/.claude/wiki-templates/ ← project-bootstrap templates
      <target>/.claude/wiki-config.json
      <target>/.claude/settings.json   ← MCP wiring (agentmemory)
      <target>/llm-wiki/               ← human-readable wiki content
        ├── README.md                  ← how to use this framework
        ├── how-to/                    ← seed how-to docs
        ├── best-practices/            ← seeded dev best practices
        └── wiki/                      ← project's research/dev wiki entries
                                         (was previously vault/<topic>/)

    Layout for cursor (parallel, with .cursor/ instead of .claude/):
      Skills land in <target>/.cursor/skills/ as a staging area — until the
      cursor adapter generates .mdc rules from them, they're reference docs.
      Settings (MCP) go to <target>/.cursor/mcp.json.
    """
    if tool == "claude-code":
        tool_dir = target / ".claude"
        settings = tool_dir / "settings.json"
    elif tool == "cursor":
        tool_dir = target / ".cursor"
        settings = tool_dir / "mcp.json"
    else:
        raise ValueError(f"unknown tool: {tool}")

    llm_wiki = target / "llm-wiki"
    return {
        "tool_dir": tool_dir,
        "skills": tool_dir / "skills",
        "scripts": tool_dir / "wiki-scripts",
        "templates": tool_dir / "wiki-templates",
        "config": tool_dir / "wiki-config.json",
        "settings": settings,
        "llm_wiki": llm_wiki,
        "llm_wiki_readme": llm_wiki / "README.md",
        "llm_wiki_how_to": llm_wiki / "how-to",
        "llm_wiki_best_practices": llm_wiki / "best-practices",
        "llm_wiki_wiki": llm_wiki / "wiki",
    }


DEFAULT_DRIVE_PARENT = "__FOR CLAUDE"

# Skills that travel — keep in sync with INSTALL-INVENTORY.md.
# `wiki` is the browse-the-wiki helper (invoked by /wiki-cycle); it must
# travel so /wiki-cycle works in per-project installs.
TRAVEL_SKILLS = [
    "new-wiki", "wrap-up",
    "wiki", "wiki-init", "wiki-update", "wiki-search", "wiki-cycle",
    "wiki-discover", "wiki-list", "wiki-claims", "wiki-refresh",
    "wiki-report", "wiki-lint", "wiki-promote",
]

# Scripts that travel — kept in sync with the actual contents of
# bootstrap/workflows/llm-wiki/scripts/. Verified via build-wiki-package.py
# on each release. wiki-promote.py is intentionally OMITTED until the
# /wiki-promote skill grows a backing script.
TRAVEL_SCRIPTS = [
    "new-wiki.py",
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
    "wiki-promote.py",
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
    print(f"[new-wiki] {msg}", file=sys.stderr)


def _ok(msg):
    print(f"[new-wiki] ✓ {msg}", file=sys.stderr)


def _warn(msg):
    print(f"[new-wiki] ! {msg}", file=sys.stderr)


def _err(msg):
    print(f"[new-wiki] ✗ {msg}", file=sys.stderr)


def _load_config(config_path: Path = CC_GLOBAL_CONFIG_PATH):
    """Read wiki-config.json or return None if absent."""
    if config_path.exists():
        try:
            return json.loads(config_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError) as e:
            _warn(f"wiki-config.json at {config_path} unreadable ({e}); treating as first-time")
            return None
    return None


def _save_config(cfg, config_path: Path = CC_GLOBAL_CONFIG_PATH):
    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text(
        json.dumps(cfg, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    _ok(f"wrote {config_path}")


def _skill_to_mdc(skill_md_path: Path, mdc_path: Path, dry_run: bool = False) -> bool:
    """Convert a Claude-Code SKILL.md to a Cursor .mdc rule.

    Frontmatter shape diverges:
      SKILL.md:  name: <slug>, description: <hint>
      .mdc:      description: <hint>, alwaysApply: false

    Cursor's rules system reads .mdc files from .cursor/rules/. The body
    stays in markdown — Cursor's agent uses the rule as context-aware
    instructions. alwaysApply=false means the rule only loads when the
    description matches the conversation; this is the right default for
    skills (which the user invokes by name, like /wiki-cycle).
    """
    if not skill_md_path.exists():
        return False
    text = skill_md_path.read_text(encoding="utf-8")
    name = skill_md_path.parent.name
    description = ""
    body = text
    if text.startswith("---"):
        end = text.find("---", 3)
        if end > 0:
            header = text[3:end].strip()
            body = text[end + 3:].lstrip("\n")
            for line in header.split("\n"):
                if line.startswith("description:"):
                    description = line.split(":", 1)[1].strip()
                    break
    if not description:
        description = f"Cursor rule generated from /{name} skill. Invoke when user mentions '{name}'."
    mdc_text = (
        "---\n"
        f"description: {description}\n"
        "alwaysApply: false\n"
        "---\n\n"
        f"# /{name}\n\n"
        f"> Cursor rule generated from `.cursor/skills/{name}/SKILL.md`. "
        f"Invoke when the user says `/{name}` or references the skill by name.\n\n"
        f"{body}"
    )
    if dry_run:
        print(f"WOULD write {mdc_path} ({len(mdc_text)} chars)")
        return True
    mdc_path.parent.mkdir(parents=True, exist_ok=True)
    mdc_path.write_text(mdc_text, encoding="utf-8")
    return True


def _generate_cursor_rules(skills_dir: Path, rules_dir: Path, dry_run: bool = False) -> int:
    """Generate .cursor/rules/<name>.mdc for every SKILL.md in skills_dir."""
    count = 0
    if not skills_dir.exists():
        return 0
    for skill_md in skills_dir.glob("*/SKILL.md"):
        name = skill_md.parent.name
        mdc_path = rules_dir / f"{name}.mdc"
        if _skill_to_mdc(skill_md, mdc_path, dry_run=dry_run):
            count += 1
    return count


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


# ---------- Phase A (global) ----------
# Phase A installs ONLY the /new-wiki creator skill globally + records
# the bootstrap source so subsequent /new-wiki invocations can find it.
# All other skills + scripts + templates ship per-project (Phase B).

def phase_a(args):
    """Global install: ONLY /new-wiki skill goes to ~/.claude/skills/.
    Writes ~/.claude/wiki-config.json so future /new-wiki runs know where
    the bootstrap source lives.

    This is the install-wiki.ps1 / install-wiki.sh entry point. After this
    succeeds, the user can cd to any project folder, start Claude Code, and
    run /new-wiki to scaffold per-project structure.
    """
    bootstrap = _derive_bootstrap_source(args)
    if not bootstrap:
        _err("could not find bootstrap source. Pass --bootstrap-source <path>.")
        return 1
    _info(f"bootstrap source: {bootstrap}")

    skills_src = bootstrap / "bootstrap" / "workflows" / "llm-wiki" / "skills"
    new_project_skill_src = skills_src / "new-wiki"
    new_project_skill_dst = CC_GLOBAL_SKILLS_DIR / "new-wiki"

    if not new_project_skill_src.exists():
        _err(f"new-wiki skill missing in bootstrap source: {new_project_skill_src}")
        return 1

    _info(f"installing /new-wiki skill: {new_project_skill_src} -> {new_project_skill_dst}")
    c, s = _copy_tree(new_project_skill_src, new_project_skill_dst, dry_run=args.dry_run)
    _ok(f"/new-wiki skill: {c} files copied, {s} unchanged")

    # Persist bootstrap source path so the skill can find it next time
    cfg = _load_config(CC_GLOBAL_CONFIG_PATH) or {}
    cfg.update({
        "bootstrap_source": str(bootstrap),
        "install_version": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        "last_phase_a": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    })
    # Preserve any default drive config from prior installs
    if args.drive_enabled == "yes":
        cfg.setdefault("drive", {})["enabled"] = True
        cfg["drive"]["parent_folder"] = args.drive_parent_folder or DEFAULT_DRIVE_PARENT
    elif args.drive_enabled == "no":
        cfg.setdefault("drive", {})["enabled"] = False

    if args.dry_run:
        print(f"WOULD write wiki-config.json to {CC_GLOBAL_CONFIG_PATH}: {json.dumps(cfg, indent=2)}")
    else:
        _save_config(cfg, CC_GLOBAL_CONFIG_PATH)

    print()
    _ok("Global install complete.")
    print()
    print("Next steps:")
    print("  1. cd <your-project-folder>")
    print("  2. Start Claude Code (or Cursor) in that folder")
    print("  3. Run /new-wiki to scaffold per-project structure")
    return 0


def _agentmemory_wired(settings_path: Path = CC_GLOBAL_SETTINGS_PATH):
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


def _merge_agentmemory_mcp(settings_path: Path = CC_GLOBAL_SETTINGS_PATH, tool: str = "claude-code"):
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
    # Canonical entry from rohitg00/agentmemory README:
    # https://github.com/rohitg00/agentmemory#claude-desktop
    # Package: @agentmemory/mcp (thin shim that exposes @agentmemory/agentmemory's MCP entrypoint)
    mcp["agentmemory"] = {
        "command": "npx",
        "args": ["-y", "@agentmemory/mcp"],
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
        _err("  4. Re-run /new-wiki --sync to complete Drive setup.")
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


# ---------- Phase B (per-project) ----------
# Phase B is the bulk of the work: scaffold a project folder with everything
# the user needs to run /wiki-cycle, /wrap-up, /wiki-search, etc.
#
# Layout (per project_paths()):
#   <target>/.claude/skills/         (or .cursor/skills/)
#   <target>/.claude/wiki-scripts/
#   <target>/.claude/wiki-templates/
#   <target>/.claude/wiki-config.json
#   <target>/.claude/settings.json   (if dev project, agentmemory MCP wiring)
#   <target>/llm-wiki/
#     ├── README.md                  (rendered from seed/llm-wiki-readme.md.tmpl)
#     ├── how-to/                    (seeded from seed/how-to/)
#     ├── best-practices/            (seeded from seed/best-practices/)
#     └── wiki/                      (project's research/dev wiki — was vault)
#   <target>/CLAUDE.md, README.md, .gitignore (rendered from templates)

def phase_b(args):
    """Per-project scaffold."""
    target = Path(args.target_folder).resolve() if args.target_folder else None
    if target is None:
        _err("--target-folder is required for Phase B")
        return 1

    bootstrap = _derive_bootstrap_source(args)
    if not bootstrap:
        _err("could not find bootstrap source. Pass --bootstrap-source <path> "
             "or run Phase A first to record it.")
        return 1

    paths = project_paths(args.tool, target)

    name = _slugify(args.project_name or "")
    if not name:
        _err("--project-name is required")
        return 1

    if target.exists() and any(target.iterdir()) and not args.force:
        # Allow if the only entries are the dirs we're about to populate
        unexpected = [p for p in target.iterdir() if p.name not in (".git", ".claude", ".cursor", "llm-wiki")]
        if unexpected:
            _err(f"target folder {target} has unexpected entries (use --force to override): {[p.name for p in unexpected][:5]}")
            return 1

    description = args.project_description or ""
    project_type = args.project_type
    if project_type not in TAXONOMY:
        _err(f"--project-type must be 'research' or 'development', got {project_type!r}")
        return 1

    wiki_src = bootstrap / "bootstrap" / "workflows" / "llm-wiki"
    skills_src = wiki_src / "skills"
    scripts_src = wiki_src / "scripts"
    templates_src = wiki_src / "templates"
    seed_src = wiki_src / "seed"

    # B1 — mkdir + git init
    _info(f"project folder: {target}")
    if args.dry_run:
        print(f"WOULD mkdir {target} + git init")
    else:
        target.mkdir(parents=True, exist_ok=True)
        if not (target / ".git").exists():
            subprocess.run(["git", "init"], cwd=target, capture_output=True, text=True)
        _ok(f"project folder ready: {target}")

    # B2 — copy skills into <target>/.claude/skills/ (or .cursor/skills/)
    _info(f"copying skills: {skills_src} -> {paths['skills']}")
    c, s = _copy_tree(skills_src, paths["skills"], names=TRAVEL_SKILLS, dry_run=args.dry_run)
    _ok(f"skills: {c} copied, {s} unchanged")

    if args.tool == "cursor":
        # Cursor adapter: generate .cursor/rules/<name>.mdc for each skill so
        # Cursor's agent picks them up natively. The .cursor/skills/<name>/
        # SKILL.md copies remain as reference / source of truth for re-generation.
        # Read from bootstrap source (skills_src) since we know all TRAVEL_SKILLS
        # exist there — same source the copy step uses.
        rules_dir = target / ".cursor" / "rules"
        # Restrict to TRAVEL_SKILLS so we don't generate rules for skills we
        # didn't install.
        n = 0
        for skill_name in TRAVEL_SKILLS:
            skill_md = skills_src / skill_name / "SKILL.md"
            mdc_path = rules_dir / f"{skill_name}.mdc"
            if _skill_to_mdc(skill_md, mdc_path, dry_run=args.dry_run):
                n += 1
        _ok(f"cursor rules generated: {n} .mdc files at {rules_dir}")

    # B3 — copy scripts
    _info(f"copying scripts: {scripts_src} -> {paths['scripts']}")
    c, s = _copy_tree(scripts_src, paths["scripts"], names=TRAVEL_SCRIPTS, dry_run=args.dry_run)
    _ok(f"scripts: {c} copied, {s} unchanged")

    # B4 — copy templates
    _info(f"copying templates: {templates_src} -> {paths['templates']}")
    c, s = _copy_tree(templates_src, paths["templates"], dry_run=args.dry_run)
    _ok(f"templates: {c} copied, {s} unchanged")

    # B5 — create <target>/llm-wiki/ with seed content
    if args.dry_run:
        print(f"WOULD mkdir {paths['llm_wiki']} and seed how-to/, best-practices/, wiki/")
    else:
        paths["llm_wiki"].mkdir(parents=True, exist_ok=True)

    # Seed: how-to/
    if seed_src.exists() and (seed_src / "how-to").exists():
        c, s = _copy_tree(seed_src / "how-to", paths["llm_wiki_how_to"], dry_run=args.dry_run)
        _ok(f"seeded how-to/: {c} files")
    else:
        if not args.dry_run:
            paths["llm_wiki_how_to"].mkdir(parents=True, exist_ok=True)
        _info("no seed/how-to/ found in bootstrap — created empty folder")

    # Seed: best-practices/
    if seed_src.exists() and (seed_src / "best-practices").exists():
        c, s = _copy_tree(seed_src / "best-practices", paths["llm_wiki_best_practices"], dry_run=args.dry_run)
        _ok(f"seeded best-practices/: {c} files")
    else:
        if not args.dry_run:
            paths["llm_wiki_best_practices"].mkdir(parents=True, exist_ok=True)
        _info("no seed/best-practices/ found in bootstrap — created empty folder")

    # B6 — apply project-type folder taxonomy under llm-wiki/wiki/
    folders = TAXONOMY[project_type]
    wiki_root = paths["llm_wiki_wiki"]
    for sub in folders:
        path = wiki_root / sub
        if args.dry_run:
            print(f"WOULD mkdir {path}")
        else:
            path.mkdir(parents=True, exist_ok=True)
    # raw/sessions/ for development wrap-ups (sibling of wiki/, under llm-wiki/)
    if project_type == "development":
        sessions_dir = paths["llm_wiki"] / "raw" / "sessions"
        if args.dry_run:
            print(f"WOULD mkdir {sessions_dir}")
        else:
            sessions_dir.mkdir(parents=True, exist_ok=True)
    _ok(f"wiki folder taxonomy applied ({project_type}): {len(folders)} folders")

    # B6.5 — render wiki scaffold files (_MAP.md, _INDEX.md, README.md, HOME.md)
    # inside <target>/llm-wiki/wiki/ from seed/wiki/*.tmpl. These give the agent
    # orientation on day 1 and prevent the CLAUDE.md @-import from silently
    # failing on a fresh project. wiki-map-compile.py / wiki-index-per-folder.py
    # will regenerate _MAP.md and _INDEX.md once entries exist.
    wiki_scaffold_vars = {
        "PROJECT_NAME": name,
        "PROJECT_DESCRIPTION": description or f"{name} project wiki",
        "PROJECT_TYPE": project_type,
    }
    wiki_seed = seed_src / "wiki"
    if wiki_seed.exists():
        for tmpl_name, out_name in [
            ("README.md.tmpl", "README.md"),
            ("HOME.md.tmpl", "HOME.md"),
            ("_MAP.md.tmpl", "_MAP.md"),
            ("_INDEX.md.tmpl", "_INDEX.md"),
        ]:
            _render_template(wiki_seed / tmpl_name, wiki_root / out_name,
                             wiki_scaffold_vars, args.dry_run)
    else:
        _warn(f"seed/wiki/ not found in bootstrap; wiki scaffold files skipped")

    # B7 — render top-level project files: CLAUDE.md / README.md / .gitignore
    template_vars = {
        "PROJECT_NAME": name,
        "PROJECT_DESCRIPTION": description,
        "LLM_WIKI_PATH": "llm-wiki",
        "WIKI_PATH": "llm-wiki/wiki",
        "PROJECT_TYPE": project_type,
    }
    _render_template(templates_src / f"CLAUDE.md.{project_type}.tmpl",
                     target / "CLAUDE.md", template_vars, args.dry_run)
    _render_template(templates_src / f"README.md.{project_type}.tmpl",
                     target / "README.md", template_vars, args.dry_run)
    _render_template(templates_src / ".gitignore.tmpl",
                     target / ".gitignore", template_vars, args.dry_run)

    # B7.5 — render llm-wiki/README.md from seed template
    seed_readme = seed_src / "llm-wiki-readme.md.tmpl"
    if seed_readme.exists():
        _render_template(seed_readme, paths["llm_wiki_readme"],
                         template_vars, args.dry_run)

    # B8 — write per-project wiki-config.json
    drive_subfolder = args.drive_subfolder if args.drive_subfolder is not None else name
    # Global config (~/.claude/wiki-config.json) holds the bootstrap_source + drive parent
    global_cfg = _load_config(CC_GLOBAL_CONFIG_PATH) or {}
    drive_parent = (global_cfg.get("drive") or {}).get("parent_folder") or DEFAULT_DRIVE_PARENT
    drive_enabled_global = (global_cfg.get("drive") or {}).get("enabled", False)
    # Per-CLI overrides at Phase B time
    if args.drive_enabled == "yes":
        drive_enabled_global = True
    elif args.drive_enabled == "no":
        drive_enabled_global = False

    project_cfg = {
        "tool": args.tool,
        "project_name": name,
        "project_type": project_type,
        "project_description": description,
        "target_folder": str(target),
        "llm_wiki_root": str(paths["llm_wiki"]),
        # vault_root + wiki_topic together resolve to <target>/llm-wiki/wiki/
        # under the existing scripts' <vault>/<topic>/wiki/ assumption.
        # We keep that layout so wiki-update, wiki-init, wiki-cycle, etc.
        # work unchanged in a per-project install. wiki_topic is always
        # "llm-wiki" in the v1 single-wiki-per-project model; v2 may relax
        # this to support multi-wiki.
        "vault_root": str(target),
        "wiki_topic": "llm-wiki",
        "wiki_path": str(paths["llm_wiki_wiki"]),
        "skills_installed_at": str(paths["skills"]),
        "scripts_installed_at": str(paths["scripts"]),
        "templates_installed_at": str(paths["templates"]),
        "bootstrap_source": str(bootstrap),
        "install_version": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        "last_phase_b": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "drive": {
            "enabled": bool(drive_enabled_global),
            "parent_folder": drive_parent,
            "subfolder": drive_subfolder if drive_enabled_global else None,
        },
    }
    if args.dry_run:
        print(f"WOULD write {paths['config']}: {json.dumps(project_cfg, indent=2)}")
    else:
        _save_config(project_cfg, paths["config"])

    # B9 — Drive OAuth walkthrough (if enabled and global token isn't cached yet)
    if drive_enabled_global:
        if args.dry_run:
            print("WOULD walk user through Drive OAuth (if token not already cached)")
        else:
            ok = _drive_oauth_walkthrough(paths["scripts"])
            if not ok:
                _warn("Drive auth did not complete. Project scaffold is still ready,")
                _warn("but Drive ingest won't work until you fix the OAuth setup.")

    needs_restart = False

    # B10 — agentmemory (development only)
    if project_type == "development":
        if _agentmemory_wired(paths["settings"]) and _agentmemory_reachable():
            _ok("agentmemory already wired in this project")
        else:
            _info("agentmemory: install + wire (per-project)")
            if args.dry_run:
                print("WOULD run: npx @agentmemory/agentmemory (background)")
                print(f"WOULD merge agentmemory MCP entry into {paths['settings']}")
            else:
                ok = _install_agentmemory()
                if not ok:
                    _err("agentmemory install failed; surface this to user")
                    return 1
                _merge_agentmemory_mcp(paths["settings"], tool=args.tool)
                needs_restart = True
                project_cfg["agentmemory_wired"] = True
                _save_config(project_cfg, paths["config"])

    # B11 — summary + project-type-specific next steps
    start_cmd = "claude" if args.tool == "claude-code" else "cursor ."

    if project_type == "development":
        next_steps = [
            f"cd {target}",
            start_cmd,
            "Read llm-wiki/README.md (project overview)",
            "Read llm-wiki/how-to/commands.md (full command reference)",
            "Code + decide + investigate as normal",
            "/wrap-up at session-end — distills the session into proposed wiki entries (components, decisions, architecture, patterns, troubleshooting)",
            "/wiki-promote --review — accept/reject the proposed entries",
            "/wiki-search \"<query>\" — look up prior decisions / components",
            "/wiki-update <url> — add an external reference (article, doc, paper)",
            "Ask the agent in plain English anytime: 'what commands do I have', 'how do I X'",
        ]
    else:  # research
        next_steps = [
            f"cd {target}",
            start_cmd,
            "Read llm-wiki/README.md (project overview)",
            "Read llm-wiki/how-to/commands.md (full command reference)",
            "Add URLs: /wiki-update <url>  OR  drop links into Drive (__FOR CLAUDE/<project-slug>/)",
            "/wiki-cycle once a day/week — discovers new sources, ingests, lints, promotes",
            "Source tier rules: T1 peer-reviewed/primary, T2 vendor/official docs, T3 expert, T4 community — pass --tier on every ingest",
            "/wiki-search \"<query>\" — hybrid BM25 + vector + LLM rerank",
            "Both-sides-stay rule: never delete contradictory entries, cross-link them",
            "Ask the agent in plain English anytime: 'how do I add a URL', 'show me the wiki', 'what's the discovery process'",
        ]

    print(json.dumps({
        "status": "ok",
        "phase": "B",
        "tool": args.tool,
        "project_name": name,
        "project_type": project_type,
        "target_folder": str(target),
        "llm_wiki_root": str(paths["llm_wiki"]),
        "wiki_folders": folders,
        "drive_enabled": bool(drive_enabled_global),
        "drive_subfolder": drive_subfolder if drive_enabled_global else None,
        "agentmemory_wired": project_cfg.get("agentmemory_wired", False) if project_type == "development" else None,
        "needs_restart": needs_restart,
        "next_steps": next_steps,
        "help_anytime": "Ask in plain English. The agent has llm-wiki/how-to/*.md and llm-wiki/README.md loaded as context.",
    }, indent=2))

    if needs_restart:
        restart_target = "Claude Code" if args.tool == "claude-code" else "Cursor"
        print()
        _info("===========================================")
        _info(f"RESTART {restart_target.upper()} to load the new agentmemory MCP server.")
        _info("===========================================")
        return 2

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
    parser.add_argument("--phase", choices=["A", "B", "sync"], required=True,
                        help="A = install /new-wiki skill globally + record bootstrap source. "
                             "B = scaffold a per-project install (skills/scripts/llm-wiki/) at --target-folder. "
                             "sync = re-run A to refresh the global /new-wiki skill.")
    parser.add_argument("--tool", choices=["claude-code", "cursor"], default="claude-code",
                        help="Which AI tool to install for (default: claude-code)")
    parser.add_argument("--project-name")
    parser.add_argument("--project-description", default="")
    parser.add_argument("--project-type", choices=["research", "development"])
    parser.add_argument("--target-folder",
                        help="Project root folder (required for --phase B)")
    parser.add_argument("--bootstrap-source",
                        help="Path to the llm-wiki-bootstrap checkout (or workflows-core dev source)")
    parser.add_argument("--drive-enabled", choices=["yes", "no"], default=None,
                        help="Enable Google Drive ingest? Triggers OAuth walkthrough if 'yes'.")
    parser.add_argument("--drive-parent-folder", default=None,
                        help=f"Parent Drive folder for ingest (default: {DEFAULT_DRIVE_PARENT})")
    parser.add_argument("--drive-subfolder", default=None,
                        help="Per-project Drive subfolder (default: project slug)")
    parser.add_argument("--force", action="store_true",
                        help="Continue even if target folder has unexpected entries")
    parser.add_argument("--dry-run", action="store_true",
                        help="Print actions without writing")
    args = parser.parse_args()

    if args.phase == "A":
        return phase_a(args)
    if args.phase == "B":
        return phase_b(args)
    if args.phase == "sync":
        # Re-run Phase A to refresh the global /new-wiki skill
        return phase_a(args)


if __name__ == "__main__":
    sys.exit(main())
