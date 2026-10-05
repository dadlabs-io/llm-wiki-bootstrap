#!/usr/bin/env python3
"""
new-wiki.py — bootstrap a new project with the LLM-wiki framework.

Runs in two phases:

  --phase A  : global install of the /new-wiki skill + record the bootstrap source
  --mode status : report the global tooling state as JSON (what /new-wiki reads before its skills question)
  --phase B  : per-project scaffold (folder + git + the wiki folders + CLAUDE.md/README/.gitignore)

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
import os
import shutil
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

# Atomic-write helper (icarus §8).
sys.path.insert(0, str(Path(__file__).resolve().parent))
from _atomic_io import atomic_write_text  # noqa: E402
from _wiki_config import taxonomy_for, FOLDER_CHOICES, PROJECT_TAXONOMY, RESEARCH_TAXONOMY  # noqa: E402 — single canonical taxonomy
# Tooling-install manifests + loop live in _install_tooling (shared with
# wiki-upgrade.py — the standalone upgrade command). Single source of truth.
from _install_tooling import (  # noqa: E402
    TRAVEL_SKILLS, TRAVEL_SCRIPTS, TOOLING_HELPER_SCRIPTS, SHARED_HELPER_SCRIPTS,
    install_tooling as _install_tooling,
    print_summary as _print_tooling_summary,
    global_tooling_status, format_tooling_status, is_bootstrap_source,
    InstallIncomplete, report_incomplete,
    build_tooling_env, find_uv,
    seed_toolset, toolset_status, undocumented_artifacts, load_install_skill_fn,
)
from _wiki_config import toolset_location  # noqa: E402
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


def project_paths(tool: str, target: Path, llm_wiki_root: Path = None) -> dict:
    """Per-project install layout. The .claude/ (or .cursor/) tool dir is always
    under --target-folder; the wiki CONTENT (llm_wiki) defaults to
    <target>/llm-wiki/ but can be relocated anywhere via llm_wiki_root (e.g. a
    separate `C:\\github.com\\project-notebooks\\<name>` so the wiki never bloats
    the code repo).

    Layout for claude-code:
      <target>/.claude/skills/         ← runnable skills (Claude Code auto-loads)
      <target>/.claude/wiki-scripts/   ← Python helpers
      <target>/.claude/wiki-templates/ ← project-bootstrap templates
      <target>/.claude/wiki-config.json
      <target>/llm-wiki/               ← human-readable wiki content
        ├── README.md                  ← how to use this framework
        └── wiki/                     ← project's research/dev wiki entries
                                         (was previously vault/<topic>/)

    Layout for cursor (parallel, with .cursor/ instead of .claude/):
      Skills land in <target>/.cursor/skills/ as a staging area — until the
      cursor adapter generates .mdc rules from them, they're reference docs.
      Settings (MCP) go to <target>/.cursor/mcp.json.
    """
    if tool == "claude-code":
        tool_dir = target / ".claude"
        # Claude Code reads project-scoped MCP servers from <target>/.mcp.json
        # at the project root, NOT from <target>/.claude/settings.json (which
        # is for permissions/hooks/env). See:
        #   https://docs.claude.com/en/docs/claude-code/mcp#project-scope
        settings = target / ".mcp.json"
    elif tool == "cursor":
        tool_dir = target / ".cursor"
        settings = tool_dir / "mcp.json"
    else:
        raise ValueError(f"unknown tool: {tool}")

    llm_wiki = Path(llm_wiki_root) if llm_wiki_root else (target / "llm-wiki")
    return {
        "tool_dir": tool_dir,
        "skills": tool_dir / "skills",
        "scripts": tool_dir / "wiki-scripts",
        "templates": tool_dir / "wiki-templates",
        "config": tool_dir / "wiki-config.json",
        "settings": settings,
        "llm_wiki": llm_wiki,
        "llm_wiki_readme": llm_wiki / "README.md",
        "llm_wiki_wiki": llm_wiki / "wiki",
    }


def _enclosing_notebook_vault(target, registry_arg=None):
    """The notebooks-vault folder governing ``target``, or None.

    A target is a notebook-in-a-vault when a ``linked-notebooks.json`` registry
    lives in an ancestor folder (or --registry points at one that does/will).
    Such targets get the FLAT layout — wiki/, raw/, _inbox/, _signals/ directly
    at the notebook root — instead of the in-project <target>/llm-wiki/ nesting.
    """
    target = Path(target).resolve()
    for d in target.parents:
        if (d / "linked-notebooks.json").exists():
            return d
    if registry_arg:
        # Registry may not exist yet on a first install — trust the pointer if
        # its folder contains the target.
        reg_dir = Path(registry_arg).resolve().parent
        if reg_dir in target.parents:
            return reg_dir
    return None


DEFAULT_DRIVE_PARENT = "__FOR CLAUDE"

# Skills that travel — keep in sync with INSTALL-INVENTORY.md.
# TRAVEL_SKILLS / TRAVEL_SCRIPTS are imported from _install_tooling above
# (single source of truth, shared with wiki-upgrade.py).

# Single merged folder taxonomy (the research/development split was removed
# 2026-06-15 — every project now gets BOTH capabilities). Four-layer memory
# model: research/ = ingested external content, project/ = our own decisions +
# components, sessions/ = episodic logs. Matches the live agentic-design layout.
# Canonical taxonomy now lives in _wiki_config (the single source every script reads
# folder names from). Imported below near the other helpers.


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
    atomic_write_text(config_path, json.dumps(cfg, indent=2, sort_keys=True))
    _ok(f"wrote {config_path}")


def _upsert_registry(registry_path: Path, name: str, root_value: str, options: dict = None):
    """Add/update one notebook in the shared linked-notebooks.json registry.
    Preserves any existing entries + _comment. Creates the file if absent.

    If ``options`` is given, the entry is written as an object
    ``{"root": <root_value>, **options}`` so per-notebook settings (e.g.
    confirm_before_create, confirm_before_promote) live in the registry — the single
    source of truth that travels with the notebook. Without options it stays a flat
    string (back-compat). An existing object entry is merged (root + options updated,
    other keys kept)."""
    data = {}
    if registry_path.exists():
        try:
            data = json.loads(registry_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            data = {}
    if "_comment" not in data:
        data["_comment"] = ("Single registry of every notebook and its root + per-notebook "
                            "settings, used to resolve ANY cross-notebook link. Entry is either "
                            "a flat \"root\" string OR an object {\"root\": <path>, <settings...>} "
                            "(booleans confirm_before_create + confirm_before_promote, both "
                            "default true; project_root = the project's repo, which the lint "
                            "resolves `describes` paths against, absent for a notebook with no "
                            "code). Relative roots resolve from this file's folder; "
                            "absolute point outside. Standard layout: wiki/, _inbox/, raw/.")
    nbs = data.setdefault("notebooks", {})
    if options:
        existing = nbs.get(name)
        merged = dict(existing) if isinstance(existing, dict) else {}
        merged["root"] = root_value
        merged.update(options)
        nbs[name] = merged
    else:
        nbs[name] = root_value
    registry_path.parent.mkdir(parents=True, exist_ok=True)
    atomic_write_text(registry_path, json.dumps(data, indent=2))


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
    atomic_write_text(mdc_path, mdc_text)
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
    if not dry_run:                       # P6 — keep --dry-run fully dry (no dir creation)
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
    walking up looking for `scripts/new-wiki.py` beside `skills/new-wiki/SKILL.md` (the repo root,
    since `bootstrap/` was removed 2026-10-01)."""
    if args.bootstrap_source:
        return Path(args.bootstrap_source).resolve()

    cfg = _load_config()
    if cfg and cfg.get("bootstrap_source"):
        return Path(cfg["bootstrap_source"]).resolve()

    # Try: am I inside an llm-wiki-bootstrap checkout?
    here = Path(__file__).resolve()
    for parent in [here.parent, *here.parents]:
        if is_bootstrap_source(parent):
            return parent.resolve()

    cwd_root = Path.cwd()
    for parent in [cwd_root, *cwd_root.parents]:
        if is_bootstrap_source(parent):
            return parent.resolve()

    return None


# ---------- Cursor global paths ----------
CURSOR_GLOBAL_DIR = Path.home() / ".cursor"
CURSOR_GLOBAL_RULES_DIR = CURSOR_GLOBAL_DIR / "rules"
CURSOR_GLOBAL_SCRIPTS_DIR = CURSOR_GLOBAL_DIR / "wiki-scripts"


def _phase_tooling_cursor(args):
    """Global Cursor tooling install: generate .mdc rules → ~/.cursor/rules/,
    copy scripts → ~/.cursor/wiki-scripts/. No project scaffold. Idempotent."""
    bootstrap = _derive_bootstrap_source(args)
    if not bootstrap:
        _err("could not find bootstrap source. Pass --bootstrap-source <path>.")
        return 1

    pkg = bootstrap
    scripts_src = pkg / "scripts"
    skills_src = pkg / "skills"
    if not scripts_src.is_dir() or not skills_src.is_dir():
        _err(f"package scripts/ or skills/ missing under {pkg}")
        return 1

    rules_dir = CURSOR_GLOBAL_RULES_DIR
    scripts_dest = CURSOR_GLOBAL_SCRIPTS_DIR
    dry = args.dry_run

    _info(f"bootstrap source: {bootstrap}")
    _info(f"mode: tooling (global, cursor)")
    _info(f"rules   → {rules_dir}")
    _info(f"scripts → {scripts_dest}")
    print()

    # 1) Copy scripts (TRAVEL_SCRIPTS + helpers) → ~/.cursor/wiki-scripts/
    if not dry:
        scripts_dest.mkdir(parents=True, exist_ok=True)
    script_names = list(TRAVEL_SCRIPTS)
    for helper in TOOLING_HELPER_SCRIPTS:
        if (scripts_src / helper).is_file():
            script_names.append(helper)
    travel_copied = 0
    helpers_copied = 0
    scripts_missing = []
    for name in script_names:
        s = scripts_src / name
        if not s.is_file():
            scripts_missing.append(name)
            continue
        d = scripts_dest / name
        if dry:
            print(f"  WOULD copy {s} -> {d}")
        else:
            shutil.copy2(s, d)
        if name in TOOLING_HELPER_SCRIPTS:
            helpers_copied += 1
        else:
            travel_copied += 1
    if scripts_missing:
        _warn(f"scripts not found in package (skipped): {scripts_missing}")

    # 1b) The scripts' own uv environment, beside them (task #71)
    try:
        env_line = build_tooling_env(pkg, scripts_dest, dry_run=dry)
    except (FileNotFoundError, RuntimeError) as e:
        _err(str(e))
        return 1
    _ok(f"environment: {env_line}")

    print()

    # 2) Generate .mdc rules from each travel skill → ~/.cursor/rules/
    if not dry:
        rules_dir.mkdir(parents=True, exist_ok=True)
    n = 0
    for skill_name in TRAVEL_SKILLS:
        skill_md = skills_src / skill_name / "SKILL.md"
        mdc_path = rules_dir / f"{skill_name}.mdc"
        if _skill_to_mdc(skill_md, mdc_path, dry_run=dry):
            n += 1
    if n == 0 and not dry:
        _warn("no SKILL.md files found to convert — check TRAVEL_SKILLS paths")

    print()
    print("=" * 60)
    print("Global tooling-only install summary (cursor)")
    print("=" * 60)
    verb = "would be copied" if dry else "copied"
    print(f"  scripts {verb}:  {travel_copied}  (+ {helpers_copied} helpers)  → {scripts_dest}")
    verb_r = "would be generated" if dry else "generated"
    print(f"  rules {verb_r}: {n} .mdc files  → {rules_dir}")
    print()
    print("  Restart Cursor or reload the window for rules to register.")
    print("  Skills invoke via '/skill-name' in Cursor Agent chat.")
    print("=" * 60)
    return 0


# ---------- Mode: tooling (global tooling-only install) ----------
# A GLOBAL Claude Code install with NO project/content scaffold. Installs the
# full skill + script toolkit into ~/.claude/ so every project on the machine
# can invoke /wiki-* without a per-project copy. Idempotent.
#
#   skills  → ~/.claude/skills/<skill>/   (per-skill via install-skill primitive)
#   scripts → ~/.claude/wiki-scripts/     (TRAVEL_SCRIPTS + install-skill.py + _atomic_io.py)
#
# This intentionally does NOT scaffold llm-wiki/, CLAUDE.md, taxonomy folders,
# or wiki-config content — it only lays down the reusable tooling.

CC_GLOBAL_WIKI_SCRIPTS_DIR = CC_GLOBAL_DIR / "wiki-scripts"

# TOOLING_HELPER_SCRIPTS / SHARED_HELPER_SCRIPTS are imported from
# _install_tooling above (single source of truth).


def phase_tooling(args):
    """Global tooling-only install.

    claude-code: skills → ~/.claude/skills/, scripts → ~/.claude/wiki-scripts/
    cursor:      rules  → ~/.cursor/rules/,  scripts → ~/.cursor/wiki-scripts/
    No project scaffold in either case. Idempotent.
    """
    if args.tool not in ("claude-code", "cursor"):
        _err(f"--tool must be 'claude-code' or 'cursor', got {args.tool!r}")
        return 1

    if args.tool == "cursor":
        return _phase_tooling_cursor(args)

    bootstrap = _derive_bootstrap_source(args)
    if not bootstrap:
        _err("could not find bootstrap source. Pass --bootstrap-source <path>.")
        return 1

    # Delegate the actual copy/install to the shared _install_tooling module
    # (same implementation wiki-upgrade.py uses — single source of truth).
    _info(f"bootstrap source: {bootstrap}")
    _info("mode: tooling (global, claude-code)")
    _info("Tip: the standalone `wiki-upgrade.py` runs this same install — prefer it for "
          "refreshing global tooling (this --mode tooling path is kept for back-compat).")
    print()
    try:
        summary = _install_tooling(
            bootstrap, dry_run=args.dry_run,
            skills_dest=CC_GLOBAL_SKILLS_DIR, scripts_dest=CC_GLOBAL_WIKI_SCRIPTS_DIR,
        )
    except InstallIncomplete as e:  # stopped partway: say so, keep the full error in a log
        report_incomplete(e)
        return 1
    except FileNotFoundError as e:
        _err(str(e))
        return 1
    _print_tooling_summary(summary)
    if summary.get("frontmatter_failed"):
        _err("one or more skills/agents were refused (frontmatter does not parse) — fix and re-run")
        return 1
    return 0


# ---------- --mode status (read-only) ----------

def phase_status(args):
    """Print the global tooling state as JSON: which skills / scripts / agents are
    installed, missing or stale against the bootstrap source. Writes nothing.
    /new-wiki runs this before its skills question so the question reflects the
    machine (use the global install / refresh it / install it / bundle) instead
    of being asked blind (2026-09-09)."""
    bootstrap = _derive_bootstrap_source(args)
    if not bootstrap:
        print(json.dumps({"status": "error", "state": "no-bootstrap-source",
                          "message": "could not find bootstrap source — run install-wiki.ps1 / install-wiki.sh once"}, indent=2))
        return 1
    status = global_tooling_status(bootstrap)
    print(format_tooling_status(status), file=sys.stderr)
    print(json.dumps({"status": "ok", **status}, indent=2))
    return 0


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

    skills_src = bootstrap / "skills"
    new_project_skill_src = skills_src / "new-wiki"
    new_project_skill_dst = CC_GLOBAL_SKILLS_DIR / "new-wiki"

    if not new_project_skill_src.exists():
        _err(f"new-wiki skill missing in bootstrap source: {new_project_skill_src}")
        return 1

    if args.tool == "cursor":
        # Cursor: install /new-wiki as a global .mdc rule → ~/.cursor/rules/new-wiki.mdc
        # so the user can invoke /new-wiki from Cursor Agent chat in any new project.
        new_wiki_mdc_dst = CURSOR_GLOBAL_RULES_DIR / "new-wiki.mdc"
        _info(f"installing /new-wiki rule: {new_project_skill_src / 'SKILL.md'} -> {new_wiki_mdc_dst}")
        if not args.dry_run:
            CURSOR_GLOBAL_RULES_DIR.mkdir(parents=True, exist_ok=True)
        ok = _skill_to_mdc(new_project_skill_src / "SKILL.md", new_wiki_mdc_dst,
                           dry_run=args.dry_run)
        if ok:
            _ok(f"/new-wiki rule: {new_wiki_mdc_dst}")
        else:
            _warn(f"could not generate /new-wiki.mdc (SKILL.md missing?)")
    else:
        # Claude Code: install /new-wiki skill folder → ~/.claude/skills/new-wiki/, through the same
        # primitive as the full install, so its {{TOOLSET_DIR}} / {{WIKI_SCRIPTS_DIR}} are filled in
        _info(f"installing /new-wiki skill: {new_project_skill_src} -> {new_project_skill_dst}")
        rc = load_install_skill_fn(bootstrap / "scripts")(
            skill="new-wiki", tool="claude-code", skills_src=skills_src, skills_dest=CC_GLOBAL_SKILLS_DIR,
            scripts_dir=CC_GLOBAL_WIKI_SCRIPTS_DIR, dry_run=args.dry_run)
        if rc:
            _err(f"/new-wiki skill not installed (exit {rc})")
            return 1
        _ok("/new-wiki skill installed")

    # Persist bootstrap source path so the skill can find it next time
    cfg = _load_config(CC_GLOBAL_CONFIG_PATH) or {}
    cfg.update({
        "bootstrap_source": str(bootstrap),
        "install_version": datetime.now().strftime("%Y-%m-%d"),
        "last_phase_a": datetime.now().astimezone().isoformat(timespec="seconds"),
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
    if args.tool == "cursor":
        print("  2. Open the folder in Cursor")
        print("  3. Open Agent chat and run /new-wiki to scaffold per-project structure")
    else:
        print("  2. Start Claude Code: `claude`")
        print("  3. Run /new-wiki to scaffold per-project structure")
    return 0


# NOTE: agentmemory integration was removed 2026-05-14. The cost-benefit didn't
# justify the complexity (Docker, iii-engine, three "OFF by default" env vars,
# upstream issues #138/#143/#308/#338, API-key compression burn). The
# "proactive listener" pattern in the CLAUDE.md template — agent files durable
# items to _inbox/proposed/ inline — covers ~80% of the value at zero infra
# cost. See agentic-design wiki for the full retrospective. Add back as an
# opt-in flag if a future user actually wants the hook-driven auto-capture
# path; the git history has the wiring (commit 9f94cb9 and earlier).


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
        _err("  4. Then authorise once: uv run --project ~/.claude/wiki-scripts python "
             "~/.claude/wiki-scripts/wiki-fetch-drive-folder.py --auth-only")
        _err("     (it reads the secrets from the path above; /new-wiki --sync does not run this step).")
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
            [find_uv() or "uv", "run", "--project", str(scripts_dir), "python", str(fetch_script), "--auth-only",
             "--client-secrets", str(DRIVE_CLIENT_SECRETS_PATH)],
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
#   <target>/llm-wiki/
#     ├── README.md                  (rendered from seed/llm-wiki-readme.md.tmpl)
#     ├── _config/feeds.md           (only with research/: templates/feeds.md.tmpl, the empty trusted-sources page)
#     └── wiki/                     (project's research/dev wiki — was vault)
#   <target>/CLAUDE.md, README.md, .gitignore (rendered from templates)

def phase_docs(args):
    """--phase docs: refresh ONLY the global toolset's docs (task #25, 2026-10-04) -- the llm-wiki pack's
    usage pages (how-to/llm-wiki/), the how-to root marker and the six framework-contract docs
    (wiki/project/best-practices/framework/), kept once in the global-toolset notebook. No project wiki
    carries a copy any more, so nothing else is touched. A global install (`--mode tooling`,
    `install-wiki.ps1 -RefreshOnly`) does the same as one of its steps; this is the narrow path after a
    docs-only change. The toolset is created and registered when it is not there yet.

    --check reports what a refresh would add, replace or remove and writes nothing: exit 1 when anything
    would change, so a script can gate on it."""
    bootstrap = _derive_bootstrap_source(args)
    if not bootstrap:
        _err("could not find bootstrap source. Pass --bootstrap-source <path> or run Phase A first.")
        return 1
    undocumented = undocumented_artifacts(bootstrap)
    if undocumented:
        _warn("shipped without a usage page (add <artifact>/wiki-seed/<name>.md -- every skill and "
              "agent must carry one): " + ", ".join(undocumented))
    if getattr(args, "check", False):
        root, _reg, registered = toolset_location()
        status = toolset_status(bootstrap, root)
        for key in ("add", "replace", "remove"):
            for rel in status[key]:
                print(f"  {key.upper():<8} {rel}")
        if not registered:
            print(f"  not registered: a refresh would create and register {root.as_posix()}")
        if status["state"] == "current" and registered:
            _ok(f"docs check: the global toolset at {status['root']} matches the framework")
            return 0
        _warn(f"docs check: the global toolset at {status['root']} is {status['state']} -- nothing written "
              "(--check); run the same command without --check to refresh it")
        return 1
    status = seed_toolset(bootstrap, dry_run=args.dry_run)
    verb = "would be " if args.dry_run else ""
    for key, label in (("add", "added"), ("replace", "replaced"), ("remove", "removed")):
        for rel in status[key]:
            print(f"  {verb}{label}: {rel}")
    _ok(f"global toolset docs at {status['root']}: {len(status['add'])} {verb}added, "
        f"{len(status['replace'])} {verb}replaced, {len(status['remove'])} {verb}removed; "
        f"registry: {status['registered']}")
    return 0


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

    name = _slugify(args.project_name or "")
    if not name:
        _err("--project-name is required")
        return 1

    # Wiki content location: external (a separate vault folder, e.g.
    # C:\github.com\project-notebooks\<name>) keeps the wiki out of the code repo.
    # In-project (<target>/llm-wiki) is the self-contained default.
    if args.vault_root:
        external_vault = True
        vault_root = Path(args.vault_root).resolve()
        llm_wiki_root = vault_root / name
    else:
        # Notebook-vault detection: when the target ITSELF is a notebook inside a
        # notebooks vault (a linked-notebooks.json in an ancestor, or --registry
        # pointing at one), scaffold FLAT at the notebook root — wiki/, raw/,
        # _inbox/, _signals/ as direct children, NO intermediate llm-wiki/ level.
        # The nested <target>/llm-wiki/ default applies only to true in-project
        # installs (a wiki living inside a code repo). Without this branch, a
        # notebook-vault install produced <notebook>/llm-wiki/wiki while migrated
        # notebooks are <notebook>/wiki — two path shapes for every downstream
        # rule (qmd collections, _inbox/ staging, _signals/ sidecars). That is
        # how agent-builder-bootstrap got its snowflake nested layout.
        vault_dir = _enclosing_notebook_vault(target, args.registry)
        if vault_dir is not None:
            external_vault = True
            vault_root = target.parent
            llm_wiki_root = target
            _info(f"target is a notebook inside a vault ({vault_dir}) — "
                  f"scaffolding FLAT at the notebook root, no llm-wiki/ level")
        else:
            external_vault = False
            vault_root = target
            llm_wiki_root = target / "llm-wiki"

    # Skills install: 'global' (default) uses ~/.claude/skills + ~/.claude/wiki-scripts
    # (shared, no per-project copy); 'bundled' copies them into the project
    # (self-contained, version-pinned). Cursor always bundles (no global skill dir).
    skills_install = (args.skills_install or "global")
    if args.tool == "cursor":
        skills_install = "bundled"
    bundle = (skills_install == "bundled")

    # Guard (2026-09-09): in global mode never point a project at a global folder that
    # does not hold the tooling. Phase A installs only /new-wiki; the full tooling
    # install is a separate step (install-wiki.ps1 with no flags, ./install-wiki.sh,
    # or --mode tooling). Before this, a fresh machine's `install-wiki.ps1 -TargetFolder`
    # produced a project whose config pointed at skills that did not exist. Refuse,
    # unless --install-global-if-missing, which runs that install once and continues.
    global_tooling_installed_now = False
    tooling_state = None
    if not bundle:
        tooling = global_tooling_status(bootstrap)
        tooling_state = tooling["state"]
        if not tooling["complete"]:
            print(format_tooling_status(tooling))
            if not args.install_global_if_missing:
                _err("global tooling is not installed (or only partly) — a project in global mode "
                     "would point at skills that do not exist.")
                _info("Install it once (`install-wiki.ps1` with no flags / `./install-wiki.sh` / "
                      "`new-wiki.py --mode tooling`), or re-run with --install-global-if-missing, "
                      "or pass --skills-install bundled.")
                return 1
            _info("global tooling incomplete — installing it now (--install-global-if-missing)")
            if not args.dry_run:
                try:
                    summary = _install_tooling(bootstrap, skills_dest=CC_GLOBAL_SKILLS_DIR,
                                               scripts_dest=CC_GLOBAL_WIKI_SCRIPTS_DIR)
                except InstallIncomplete as e:  # stopped partway: say so, keep the full error in a log
                    report_incomplete(e)
                    return 1
                except FileNotFoundError as e:
                    _err(str(e))
                    return 1
                _print_tooling_summary(summary)
                if summary.get("frontmatter_failed"):
                    _err("one or more skills/agents were refused (frontmatter does not parse) — fix and re-run")
                    return 1
                global_tooling_installed_now = True
                tooling_state = "installed"
        elif not tooling["current"]:
            _warn("global tooling is installed but differs from the bootstrap source "
                  f"({', '.join(tooling['stale_skills'] + tooling['stale_scripts'] + tooling['stale_agents'])}) — "
                  "not refreshed here; run `install-wiki.ps1 -RefreshOnly` when you want the current copies")
        else:
            _ok(f"global tooling: installed and current ({tooling['skills_expected']} skills, "
                f"{tooling['scripts_expected']} scripts, {tooling['agents_expected']} agents)")

    paths = project_paths(args.tool, target, llm_wiki_root=llm_wiki_root)

    if target.exists() and any(target.iterdir()) and not args.force:
        # Allow if the only entries are the dirs we're about to populate
        unexpected = [p for p in target.iterdir() if p.name not in (".git", ".claude", ".cursor", "llm-wiki")]
        if unexpected:
            _err(f"target folder {target} has unexpected entries: {[p.name for p in unexpected][:5]}")
            # Worded as a question for the user, not a next step: an agent reading "Re-run with
            # --force" did exactly that without asking (sonnet, 3 of 3 runs, 2026-09-18).
            _info("This looks like an existing project (migration / re-run). Nothing was written. "
                  "Ask the user before re-running with --force: it keeps an existing CLAUDE.md / "
                  "README.md / .gitignore and writes everything else into this folder.")
            return 1

    description = args.project_description or ""
    # research/development split removed 2026-06-15 — every project gets both.
    # --project-type is accepted but ignored (back-compat); recorded as "merged".
    project_type = "merged"

    wiki_src = bootstrap
    skills_src = wiki_src / "skills"
    scripts_src = wiki_src / "scripts"
    templates_src = wiki_src / "templates"
    seed_src = wiki_src / "seed"

    # B1 — mkdir + git init (skip if already inside a repo → no nested repo)
    _info(f"project folder: {target}")
    if args.dry_run:
        print(f"WOULD mkdir {target} (+ git init only if not already inside a repo)")
    else:
        target.mkdir(parents=True, exist_ok=True)
        # Don't create a nested repo: if target already lives inside an existing git
        # work tree (e.g. a notebook under project-notebooks), DON'T init a new one.
        inside = subprocess.run(
            ["git", "rev-parse", "--is-inside-work-tree"],
            cwd=target, capture_output=True, text=True,
        )
        already_in_repo = inside.returncode == 0 and inside.stdout.strip() == "true"
        if already_in_repo:
            _info("target is inside an existing git repo — skipping git init (no nested repo)")
        elif not (target / ".git").exists():
            subprocess.run(["git", "init"], cwd=target, capture_output=True, text=True)
        _ok(f"project folder ready: {target}")

    # B2/B3/B4 — copy skills + scripts + templates into the project ONLY when
    # bundling. In 'global' mode (default for claude-code) the project uses the
    # shared ~/.claude install and carries only wiki-config.json + content.
    if not bundle:
        _ok("skills:    using global ~/.claude/skills (no per-project copy)")
        _ok("scripts:   using global ~/.claude/wiki-scripts (no per-project copy)")
        _ok("templates: rendered from bootstrap at scaffold time (no per-project copy)")
    else:
        # B2 — copy skills into <target>/.claude/skills/ (or .cursor/skills/)
        _info(f"copying skills: {skills_src} -> {paths['skills']}")
        c, s = _copy_tree(skills_src, paths["skills"], names=TRAVEL_SKILLS, dry_run=args.dry_run)
        _ok(f"skills: {c} copied, {s} unchanged")

        if args.tool == "cursor":
            # Cursor adapter: generate .cursor/rules/<name>.mdc for each skill so
            # Cursor's agent picks them up natively. The .cursor/skills/<name>/
            # SKILL.md copies remain as reference / source of truth for re-generation.
            rules_dir = target / ".cursor" / "rules"
            n = 0
            for skill_name in TRAVEL_SKILLS:
                skill_md = skills_src / skill_name / "SKILL.md"
                mdc_path = rules_dir / f"{skill_name}.mdc"
                if _skill_to_mdc(skill_md, mdc_path, dry_run=args.dry_run):
                    n += 1
            _ok(f"cursor rules generated: {n} .mdc files at {rules_dir}")

        # B3 — copy scripts (travel scripts + shared helper modules they import)
        _info(f"copying scripts: {scripts_src} -> {paths['scripts']}")
        c, s = _copy_tree(scripts_src, paths["scripts"],
                          names=TRAVEL_SCRIPTS + SHARED_HELPER_SCRIPTS, dry_run=args.dry_run)
        _ok(f"scripts: {c} copied, {s} unchanged")
        # B3b — the scripts' own uv environment, beside them (task #71)
        try:
            _ok(f"environment: {build_tooling_env(bootstrap, paths['scripts'], dry_run=args.dry_run)}")
        except (FileNotFoundError, RuntimeError) as e:
            _err(str(e))
            return 1

        # B4 — copy templates
        _info(f"copying templates: {templates_src} -> {paths['templates']}")
        c, s = _copy_tree(templates_src, paths["templates"], dry_run=args.dry_run)
        _ok(f"templates: {c} copied, {s} unchanged")

    # B5 — create the wiki root. No docs are copied into a project since 2026-10-04 (task #25): the pack
    # usage docs and the framework-contract docs live once, in the global toolset, which the global
    # install keeps current; CLAUDE.md imports the command reference from there.
    if args.dry_run:
        print(f"WOULD mkdir {paths['llm_wiki']} and wiki/")
    else:
        paths["llm_wiki"].mkdir(parents=True, exist_ok=True)

    # B6 — the wiki folders: each half (project/, research/) created with its default
    # stubs, as an empty root, or not at all — the two /new-wiki questions (2026-09-09).
    # sessions/ is always created (/wrap-up writes there).
    folders = taxonomy_for(args.project_folder, args.research_folder)
    wiki_root = paths["llm_wiki_wiki"]
    for sub in folders:
        path = wiki_root / sub
        if args.dry_run:
            print(f"WOULD mkdir {path}")
        else:
            path.mkdir(parents=True, exist_ok=True)
    # raw/sessions/ for session wrap-ups (sibling of wiki/, under llm-wiki/) —
    # always created now that every project supports the episodic layer.
    sessions_dir = paths["llm_wiki"] / "raw" / "sessions"
    if args.dry_run:
        print(f"WOULD mkdir {sessions_dir}")
    else:
        sessions_dir.mkdir(parents=True, exist_ok=True)
    _ok(f"wiki folders applied: {len(folders)} (project/: {args.project_folder}, "
        f"research/: {args.research_folder}, sessions/: always)")

    # B6.5 — render wiki scaffold files (_MAP.md, README.md, HOME.md) inside the
    # wiki/ folder from seed/wiki/*.tmpl. These give the agent orientation on day 1
    # and keep the CLAUDE.md @-import of _MAP.md from failing on a fresh project;
    # wiki-map-compile.py regenerates _MAP.md once entries exist. No wiki/_INDEX.md:
    # the full index is <wiki root>/_INDEX.md, beside wiki/, written by wiki-index.py
    # on the first filing (a placeholder here was never regenerated; removed 2026-09-25).
    # A markdown list of the folders this scaffold actually created, for the READMEs
    # (they used to print a fixed research list that no longer matched the wiki).
    folder_notes = {
        "research": "external content — articles, papers, videos (`/wiki-update`, `/wiki-cycle`)",
        "project": "what we build — decisions, components, patterns, troubleshooting (`/wrap-up`)",
        "sessions": "per-persona episodic logs and working-memory dashboards (`/wrap-up`)",
    }
    wiki_folders_md = "\n".join(
        f"- `{f}/` — {folder_notes[f]}" if f in folder_notes else f"- `{f}/`"
        for f in folders
    )
    if args.research_folder == "empty":
        wiki_folders_md += "\n- (`research/` subfolders appear on the first ingest — `/wiki-update` proposes one)"
    if args.project_folder == "empty":
        wiki_folders_md += "\n- (`project/` subfolders appear as `/wrap-up` files into them)"
    wiki_scaffold_vars = {
        "PROJECT_NAME": name,
        "PROJECT_DESCRIPTION": description or f"{name} project wiki",
        "PROJECT_TYPE": project_type,
        "WIKI_FOLDERS": wiki_folders_md,
        "TOOLSET_DIR": toolset_location()[0].as_posix(),
    }
    wiki_seed = seed_src / "wiki"
    if wiki_seed.exists():
        for tmpl_name, out_name in [
            ("README.md.tmpl", "README.md"),
            ("HOME.md.tmpl", "HOME.md"),
            ("_MAP.md.tmpl", "_MAP.md"),
        ]:
            _render_template(wiki_seed / tmpl_name, wiki_root / out_name,
                             wiki_scaffold_vars, args.dry_run)
    else:
        _warn(f"seed/wiki/ not found in bootstrap; wiki scaffold files skipped")

    # B7 — render top-level project files: CLAUDE.md / README.md / .gitignore
    # CLAUDE.md @-imports: relative paths for an in-project wiki, absolute for an
    # external vault (the wiki isn't under the project dir).
    if external_vault:
        llm_wiki_path_str = paths["llm_wiki"].as_posix()
        wiki_path_str = paths["llm_wiki_wiki"].as_posix()
    else:
        llm_wiki_path_str = "llm-wiki"
        wiki_path_str = "llm-wiki/wiki"
    toolset_dir = toolset_location()[0].as_posix()
    template_vars = {
        "TOOLSET_DIR": toolset_dir,
        "PROJECT_NAME": name,
        "PROJECT_DESCRIPTION": description,
        "LLM_WIKI_PATH": llm_wiki_path_str,
        "WIKI_PATH": wiki_path_str,
        "PROJECT_TYPE": project_type,
        "WIKI_FOLDERS": wiki_folders_md,
    }
    # Non-destructive: never overwrite a CLAUDE.md / README.md / .gitignore that
    # already exists in the target repo (migrating into an established project, or
    # re-running to pick up framework updates). skip_if_exists preserves the user's
    # hand-authored files. (Fix P2 — clobbering tracked files is too sharp.)
    claude_existed = (target / "CLAUDE.md").exists()
    wrote_claude = _render_template(templates_src / "CLAUDE.md.tmpl",
                     target / "CLAUDE.md", template_vars, args.dry_run, skip_if_exists=True)
    _render_template(templates_src / "README.md.tmpl",
                     target / "README.md", template_vars, args.dry_run, skip_if_exists=True)
    _render_template(templates_src / ".gitignore.tmpl",
                     target / ".gitignore", template_vars, args.dry_run, skip_if_exists=True)
    if claude_existed and not wrote_claude:
        _info(f"NOTE: existing CLAUDE.md preserved. To wire the wiki, manually add an "
              f"@-import of `{wiki_path_str}/_MAP.md` (and the memory/how-to pointers) "
              f"into it — see templates/CLAUDE.md.tmpl for the canonical block.")

    # B7.5 — render llm-wiki/README.md from seed template
    seed_readme = seed_src / "llm-wiki-readme.md.tmpl"
    if seed_readme.exists():
        _render_template(seed_readme, paths["llm_wiki_readme"],
                         template_vars, args.dry_run)

    # B7.6 — the trusted-sources page /wiki-discover reads, beside wiki/, created empty whenever
    # research/ exists (2026-09-26): the user fills it, or names sources at /new-wiki's optional
    # question and the skill adds them. An existing page is never overwritten.
    feeds_file = paths["llm_wiki"] / "_config" / "feeds.md" if args.research_folder != "none" else None
    if feeds_file:
        _render_template(templates_src / "feeds.md.tmpl", feeds_file, template_vars,
                         args.dry_run, skip_if_exists=True)

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

    if args.registry:
        # v3 registry mode: the project's wiki-config is a THIN pointer; this
        # notebook's location is recorded in the shared registry (single source of
        # truth). Resolver: config.notebook + config.registry → registry[name] → root.
        registry_path = Path(args.registry).resolve()
        nb_root = paths["llm_wiki"]  # topic_root (holds wiki/, _inbox/, raw/)
        try:
            entry = nb_root.relative_to(registry_path.parent).as_posix()
        except ValueError:
            entry = nb_root.as_posix()
        nb_options = {
            "confirm_before_create": args.confirm_before_create == "true",
            "confirm_before_promote": args.confirm_before_promote == "true",
        }
        # project_root (2026-09-17): the repo this notebook's `describes` paths
        # resolve against, relative to the registry like root. A target that IS
        # the notebook (a notebook-only project in the vault) has no repo.
        if target.resolve() != nb_root.resolve():
            try:
                nb_options["project_root"] = Path(os.path.relpath(target.resolve(), registry_path.parent)).as_posix()
            except ValueError:  # another drive on Windows
                nb_options["project_root"] = target.resolve().as_posix()
        project_note = f", project_root: {nb_options['project_root']}" if "project_root" in nb_options else ""
        if args.dry_run:
            print(f"WOULD register notebook '{name}' -> {{root: {entry}, "
                  f"confirm_before_create: {nb_options['confirm_before_create']}, "
                  f"confirm_before_promote: {nb_options['confirm_before_promote']}{project_note}}} in {registry_path}")
        else:
            _upsert_registry(registry_path, name, entry, options=nb_options)
            _ok(f"registered '{name}' -> {entry} (confirm_before_create="
                f"{nb_options['confirm_before_create']}, confirm_before_promote="
                f"{nb_options['confirm_before_promote']}{project_note}) in {registry_path.name}")
        # Record the registry machine-wide too (2026-09-13, defect 1 of the
        # 2026-09-12 batch): a script run from a cwd with no project config (a
        # foreign folder, a worker) falls back to ~/.claude/wiki-config.json for
        # the registry pointer, so `--topic <notebook>` resolves without --vault.
        if not global_cfg.get("registry"):
            global_cfg["registry"] = registry_path.as_posix()
            if args.dry_run:
                print(f"WOULD record registry {registry_path.as_posix()} in {CC_GLOBAL_CONFIG_PATH}")
            else:
                _save_config(global_cfg, CC_GLOBAL_CONFIG_PATH)
                _ok(f"registry recorded in {CC_GLOBAL_CONFIG_PATH.name} (machine-wide fallback)")
        project_cfg = {
            "tool": args.tool,
            "project_name": name,
            "notebook": name,
            "registry": registry_path.as_posix(),
            "project_description": description,
            "skills_install": skills_install,
            # the two /new-wiki folder answers (stubs | empty | none), so a re-scaffold or
            # --phase docs can tell what this wiki was given (2026-09-09)
            "wiki_folders": {"project": args.project_folder, "research": args.research_folder},
            # NOTE: confirm_before_create / confirm_before_promote live in the REGISTRY
            # entry (per-notebook, travels with the notebook), not here — see
            # _upsert_registry above.
            "scripts_installed_at": str(paths["scripts"]) if bundle
                                    else str(CC_GLOBAL_DIR / "wiki-scripts"),
            "skills_installed_at": str(paths["skills"]) if bundle
                                   else str(CC_GLOBAL_SKILLS_DIR),
            "bootstrap_source": str(bootstrap),
            "install_version": datetime.now().strftime("%Y-%m-%d"),
            "last_phase_b": datetime.now().astimezone().isoformat(timespec="seconds"),
            "drive": {
                "enabled": bool(drive_enabled_global),
                "parent_folder": drive_parent,
                "subfolder": drive_subfolder if drive_enabled_global else None,
            },
        }
    else:
      project_cfg = {
        "tool": args.tool,
        "project_name": name,
        "project_type": project_type,
        "project_description": description,
        "target_folder": str(target),
        "llm_wiki_root": str(paths["llm_wiki"]),
        # vault_root + wiki_topic resolve to <vault_root>/<wiki_topic>/wiki/ (the
        # scripts' <vault>/<topic>/wiki/ assumption). Two layouts:
        #   in-project  → vault_root=<target>,     wiki_topic="llm-wiki"  → <target>/llm-wiki/wiki/
        #   external    → vault_root=<vault-root>, wiki_topic=<name>      → <vault-root>/<name>/wiki/
        # External keeps the wiki out of the code repo (e.g. project-notebooks/).
        "vault_root": str(vault_root) if external_vault else str(target),
        # default_topic + topics[] are the v2 multi-wiki keys; wiki_topic is the
        # v1 alias kept for back-compat.
        "default_topic": name if external_vault else "llm-wiki",
        "topics": [name] if external_vault else ["llm-wiki"],
        "wiki_topic": name if external_vault else "llm-wiki",
        # skills_install: 'global' (shared ~/.claude) or 'bundled' (per-project copy).
        "skills_install": skills_install,
        "wiki_folders": {"project": args.project_folder, "research": args.research_folder},
        # Review gates for /wrap-up: confirm_before_create (Step 2 filing) + confirm_before_promote
        # (Step 6 promote-to-canonical), both boolean, default true (prompt/ask).
        "confirm_before_create": args.confirm_before_create == "true",
        "confirm_before_promote": args.confirm_before_promote == "true",
        "scripts_installed_at": str(paths["scripts"]) if bundle
                                else str(CC_GLOBAL_DIR / "wiki-scripts"),
        "wiki_path": str(paths["llm_wiki_wiki"]),
        "skills_installed_at": str(paths["skills"]) if bundle
                               else str(CC_GLOBAL_SKILLS_DIR),
        "templates_installed_at": str(paths["templates"]) if bundle else None,
        "bootstrap_source": str(bootstrap),
        "install_version": datetime.now().strftime("%Y-%m-%d"),
        "last_phase_b": datetime.now().astimezone().isoformat(timespec="seconds"),
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

    # Claude Code only discovers ~/.claude/skills at startup: if the global tooling was
    # installed during this run, the new skills are not visible until a restart.
    # (agentmemory, the earlier reason for this flag, was removed 2026-05-14.)
    needs_restart = global_tooling_installed_now

    # B11 — summary + next steps (single merged flow: ingest research AND
    # capture project knowledge — every project does both).
    start_cmd = "claude" if args.tool == "claude-code" else "cursor ."

    next_steps = [
        f"cd {target}",
        f"Start Claude Code: `{start_cmd}`",
        # The wiki root is <target>/llm-wiki for an in-project wiki and the notebook folder for a
        # vault notebook, so name it by its real path (it said `llm-wiki/` for both until 2026-09-26).
        f"Read `{paths['llm_wiki_readme']}` (wiki overview) + "
        f"`{toolset_dir}/how-to/llm-wiki/commands.md` (command reference, in the global toolset)",
    ]
    if args.research_folder != "none":
        next_steps += [
            f"TRUSTED SOURCES: list the blogs, channels and repos you trust in `{feeds_file}` (or ask the agent "
            "to add them); `/wiki-discover` searches them for new material",
            "INGEST research: `/wiki-update <url>` ad-hoc, OR drop links into Drive (__FOR CLAUDE/<project-slug>/) and run `/wiki-cycle` to discover → ingest → lint → promote",
            "Source tiers (research): T1 peer-reviewed/primary, T2 vendor/official, T3 expert, T4 community. Both-sides-stay: never delete contradictory entries, cross-link them",
        ]
    if args.project_folder != "none":
        next_steps += [
            "CAPTURE project knowledge: as you code/decide/debug, the agent files durable items (decisions, components, patterns, gotchas) to `_inbox/proposed/` (beside `wiki/`) inline; run `/wrap-up` at session-end to catch the rest",
        ]
    next_steps += [
        "Promote: `/wiki-promote --review` accepts/rejects proposed entries (research → research/, project knowledge → project/)",
        "Search: `/wiki-search \"<query>\"` (hybrid BM25 + vector + LLM rerank)",
        "Ask the agent in plain English anytime — 'what commands do I have', 'how do I X', 'show me the wiki'",
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
        "project_folder": args.project_folder,
        "research_folder": args.research_folder,
        "feeds_file": str(feeds_file) if feeds_file else None,
        "skills_install": skills_install,
        "global_tooling": tooling_state,
        "global_tooling_installed_now": global_tooling_installed_now,
        "drive_enabled": bool(drive_enabled_global),
        "drive_subfolder": drive_subfolder if drive_enabled_global else None,
        "needs_restart": needs_restart,
        "next_steps": next_steps,
        "help_anytime": f"Ask in plain English. CLAUDE.md loads the command reference ({toolset_dir}/how-to/llm-wiki/commands.md, in the global toolset) and the wiki README; the agent reads the other how-to pages there when a question needs them.",
    }, indent=2))

    if needs_restart:
        restart_target = "Claude Code" if args.tool == "claude-code" else "Cursor"
        print()
        _info("===========================================")
        _info(f"RESTART {restart_target.upper()} so it picks up the newly installed global skills.")
        _info("===========================================")
        # Exit 0 even when restart needed — exit-2 was a clever signal that
        # gets misread as a script failure by tool wrappers. The restart
        # message above is enough; the JSON above also has needs_restart: true.

    return 0


def _render_template(src: Path, dst: Path, vars: dict, dry_run: bool, skip_if_exists: bool = False):
    """Render a {{VAR}} template to dst. If skip_if_exists is True and dst already
    exists, DON'T overwrite it (non-destructive — preserves a user's hand-authored
    file when scaffolding into an existing repo, or re-running to pick up updates).
    Returns True if it wrote (or would write), False if it skipped an existing file."""
    if not src.exists():
        _warn(f"template missing: {src}")
        return False
    if skip_if_exists and dst.exists():
        if dry_run:
            print(f"WOULD SKIP {dst} (already exists — not overwriting)")
        else:
            _warn(f"{dst.name} already exists — preserved (not overwritten)")
        return False
    text = src.read_text(encoding="utf-8")
    for k, v in vars.items():
        text = text.replace(f"{{{{{k}}}}}", v)
    if dry_run:
        print(f"WOULD write {dst} ({len(text)} chars)")
    else:
        dst.parent.mkdir(parents=True, exist_ok=True)
        atomic_write_text(dst, text)
        _ok(f"wrote {dst}")
    return True


# ---------- Main ----------

def main():
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--phase", choices=["A", "B", "sync", "docs"], default=None,
                        help="A = install /new-wiki skill globally + record bootstrap source. "
                             "B = scaffold a per-project install (skills/scripts/llm-wiki/) at --target-folder. "
                             "sync = re-run A to refresh the global /new-wiki skill (touches no project). "
                             "docs = refresh only the global toolset's docs (the pack usage pages and the "
                             "framework-contract docs; created and registered if missing). Mutually exclusive "
                             "with --mode.")
    parser.add_argument("--mode", choices=["tooling", "status"], default=None,
                        help="tooling = GLOBAL tooling-only install (all skills + scripts into "
                             "~/.claude/, no project scaffold). status = report the global tooling "
                             "state as JSON (installed / stale / partial / missing per manifest), "
                             "writes nothing. Mutually exclusive with --phase.")
    parser.add_argument("--tool", choices=["claude-code", "cursor"], default="claude-code",
                        help="Which AI tool to install for (default: claude-code)")
    parser.add_argument("--project-name")
    parser.add_argument("--project-description", default="")
    parser.add_argument("--project-type", default=None,
                        help="(deprecated, ignored as of 2026-06-15 — research/development "
                             "split removed; every project gets the merged taxonomy)")
    parser.add_argument("--target-folder",
                        help="Project root folder (required for --phase B)")
    parser.add_argument("--confirm-before-create", choices=["true", "false"], default="true",
                        help="Review gate for /wrap-up's Step 2 (the durable-work proposal table): "
                             "'true' (prompt + wait before filing anything, default), 'false' "
                             "(auto-accept every candidate, still print the table, skip the wait). "
                             "Written to the registry (or wiki-config.json for in-project wikis); "
                             "changeable anytime.")
    parser.add_argument("--confirm-before-promote", choices=["true", "false"], default="true",
                        help="Review gate for /wrap-up's Step 6 (promoting staged entries into the "
                             "canonical wiki/ + committing): 'true' (prompt each time, default), "
                             "'false' (auto-promote + commit, no prompt). Written to the registry "
                             "(or wiki-config.json for in-project wikis); changeable anytime.")
    parser.add_argument("--skills-install", choices=["global", "bundled"], default="global",
                        help="global (default) = use shared ~/.claude/skills + wiki-scripts, "
                             "no per-project copy; bundled = copy skills+scripts into the project "
                             "(self-contained). Cursor always bundles. In global mode Phase B "
                             "refuses when the global tooling is missing or partial (see "
                             "--install-global-if-missing).")
    parser.add_argument("--install-global-if-missing", action="store_true",
                        help="With --phase B --skills-install global: if the global tooling is "
                             "missing or partial, run the tooling install once and continue "
                             "(the installer wrappers pass this). Never refreshes an installed "
                             "set that is merely stale — that is install-wiki.ps1 -RefreshOnly.")
    parser.add_argument("--project-folder", choices=list(FOLDER_CHOICES), default="stubs",
                        help="wiki/project/ (what we build; /wrap-up files here): stubs = create it "
                             "with " + ", ".join(f.split("/")[1] for f in PROJECT_TAXONOMY) + " (default); "
                             "empty = the folder only, subfolders appear as /wrap-up files into them; "
                             "none = no project/.")
    parser.add_argument("--research-folder", choices=list(FOLDER_CHOICES), default="stubs",
                        help="wiki/research/ (what we ingest; /wiki-update files here): stubs = create it "
                             "with " + ", ".join(f.split("/")[1] for f in RESEARCH_TAXONOMY) + " (default); "
                             "empty = the folder only, /wiki-update proposes a subfolder on the first "
                             "ingest; none = no research/.")
    parser.add_argument("--vault-root", default=None,
                        help="If set, the wiki CONTENT lives at <vault-root>/<name>/ instead of "
                             "<target>/llm-wiki/ — keeps the wiki out of the code repo "
                             "(e.g. C:\\github.com\\project-notebooks).")
    parser.add_argument("--registry", default=None,
                        help="Path to a shared linked-notebooks.json registry. When set, the "
                             "project's wiki-config becomes a thin pointer (notebook + registry) "
                             "and this notebook's root is recorded in the registry — the single "
                             "source of truth for locations.")
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
    parser.add_argument("--no-agentmemory", action="store_true",
                        help="(deprecated, no-op as of 2026-05-14 — agentmemory removed)")
    parser.add_argument("--dry-run", action="store_true",
                        help="Print actions without writing")
    parser.add_argument("--check", action="store_true",
                        help="With --phase docs only: list what a refresh of the global toolset would add, "
                             "replace or remove, and write nothing. Exit 1 when anything would change.")
    args = parser.parse_args()

    if args.mode and args.phase:
        _err("pass exactly one of --mode or --phase, not both")
        return 1
    if not args.mode and not args.phase:
        _err("one of --mode or --phase is required")
        return 1
    if args.check and args.phase != "docs":
        _err("--check is only meaningful with --phase docs")
        return 1

    if args.mode == "tooling":
        return phase_tooling(args)
    if args.mode == "status":
        return phase_status(args)
    if args.phase == "A":
        return phase_a(args)
    if args.phase == "B":
        return phase_b(args)
    if args.phase == "sync":
        # Re-run Phase A to refresh the global /new-wiki skill
        return phase_a(args)
    if args.phase == "docs":
        return phase_docs(args)


if __name__ == "__main__":
    sys.exit(main())
