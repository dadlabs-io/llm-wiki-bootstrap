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

# Atomic-write helper (icarus §8).
sys.path.insert(0, str(Path(__file__).resolve().parent))
from _atomic_io import atomic_write_text  # noqa: E402
from _wiki_config import MERGED_TAXONOMY  # noqa: E402 — single canonical taxonomy
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
      <target>/.mcp.json               ← MCP wiring (agentmemory) at project root
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

# Single merged folder taxonomy (the research/development split was removed
# 2026-06-15 — every project now gets BOTH capabilities). Four-layer memory
# model: research/ = ingested external content, project/ = our own decisions +
# components, sessions/ = episodic logs. Matches the live agentic-design layout.
# Canonical taxonomy now lives in _wiki_config (single source shared with wiki-init
# so the two scaffolders can't drift). Imported below near the other helpers.


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
    wrap_up_auto_promote) live in the registry — the single source of truth that
    travels with the notebook. Without options it stays a flat string (back-compat).
    An existing object entry is merged (root + options updated, other keys kept)."""
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
                            "(e.g. wrap_up_auto_promote). Relative roots resolve from this file's "
                            "folder; absolute point outside. Standard layout: wiki/, _inbox/, raw/.")
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

    pkg = bootstrap / "bootstrap" / "workflows" / "llm-wiki"
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

# Extra helper scripts copied alongside TRAVEL_SCRIPTS in tooling mode (not
# directly user-invoked, but imported/called by the tooling). Copied only if
# present in the package scripts dir.
TOOLING_HELPER_SCRIPTS = ["install-skill.py", "_atomic_io.py", "_wiki_config.py"]

# Shared helper modules imported by the travel scripts (config + atomic IO).
# These are NOT user-invoked but MUST ship anywhere the scripts run — both the
# global tooling install and per-project Phase B.
SHARED_HELPER_SCRIPTS = ["_atomic_io.py", "_wiki_config.py"]


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

    pkg = bootstrap / "bootstrap" / "workflows" / "llm-wiki"
    scripts_src = pkg / "scripts"
    skills_src = pkg / "skills"
    if not scripts_src.is_dir() or not skills_src.is_dir():
        _err(f"package scripts/ or skills/ missing under {pkg}")
        return 1

    skills_dest = CC_GLOBAL_SKILLS_DIR
    scripts_dest = CC_GLOBAL_WIKI_SCRIPTS_DIR
    scripts_dest_value = scripts_dest.expanduser().resolve().as_posix()

    dry = args.dry_run
    _info(f"bootstrap source: {bootstrap}")
    _info(f"mode: tooling (global, claude-code)")
    _info(f"skills  → {skills_dest}")
    _info(f"scripts → {scripts_dest}")
    print()

    # 1) Copy scripts (TRAVEL_SCRIPTS + helpers) → ~/.claude/wiki-scripts/
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

    print()

    # 2) Install each skill via the install-skill primitive (imported).
    install_fn = _load_install_skill_fn(scripts_src)
    skills_installed = 0
    skills_failed = []
    for skill in TRAVEL_SKILLS:
        rc = install_fn(
            skill=skill,
            tool="claude-code",
            skills_src=skills_src,
            skills_dest=skills_dest,
            scripts_dir=scripts_dest,
            dry_run=dry,
        )
        if rc == 0:
            skills_installed += 1
        else:
            skills_failed.append(skill)
    if skills_failed:
        _warn(f"skills that failed to install: {skills_failed}")

    print()
    print("=" * 60)
    print("Global tooling-only install summary")
    print("=" * 60)
    verb = "would be copied" if dry else "copied"
    print(f"  scripts {verb}:   {travel_copied}  (+ {helpers_copied} helpers)  → {scripts_dest}")
    verb_s = "would be installed" if dry else "installed"
    print(f"  skills {verb_s}: {skills_installed}  → {skills_dest}")
    print(f"  placeholder {{{{WIKI_SCRIPTS_DIR}}}} → {scripts_dest_value}")
    print()
    print("  Restart Claude Code if these dirs are new so it picks up the")
    print("  new skills + scripts.")
    print("=" * 60)
    return 0


def _load_install_skill_fn(scripts_src: Path):
    """Import install_skill() from the package's install-skill.py. Falls back to
    a subprocess shim if the import fails for any reason (kept to one prefer-import
    code path, but resilient)."""
    install_path = scripts_src / "install-skill.py"
    if install_path.is_file():
        import importlib.util
        spec = importlib.util.spec_from_file_location("_install_skill_mod", install_path)
        if spec and spec.loader:
            mod = importlib.util.module_from_spec(spec)
            try:
                spec.loader.exec_module(mod)
                if hasattr(mod, "install_skill"):
                    return mod.install_skill
            except Exception as e:  # noqa: BLE001
                _warn(f"could not import install_skill() ({e}); using subprocess fallback")

    def _subprocess_install(skill, tool, skills_src, skills_dest, scripts_dir, dry_run):
        cmd = [
            sys.executable, str(install_path),
            "--skill", skill,
            "--tool", tool,
            "--skills-src", str(skills_src),
            "--skills-dest", str(skills_dest),
            "--scripts-dir", str(scripts_dir),
        ]
        if dry_run:
            cmd.append("--dry-run")
        return subprocess.run(cmd).returncode

    return _subprocess_install


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
        # Claude Code: install /new-wiki skill folder → ~/.claude/skills/new-wiki/
        _info(f"installing /new-wiki skill: {new_project_skill_src} -> {new_project_skill_dst}")
        c, s = _copy_tree(new_project_skill_src, new_project_skill_dst, dry_run=args.dry_run)
        _ok(f"/new-wiki skill: {c} files copied, {s} unchanged")

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
#   <target>/.mcp.json               (if dev project, agentmemory MCP wiring at project root)
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

    paths = project_paths(args.tool, target, llm_wiki_root=llm_wiki_root)

    if target.exists() and any(target.iterdir()) and not args.force:
        # Allow if the only entries are the dirs we're about to populate
        unexpected = [p for p in target.iterdir() if p.name not in (".git", ".claude", ".cursor", "llm-wiki")]
        if unexpected:
            _err(f"target folder {target} has unexpected entries: {[p.name for p in unexpected][:5]}")
            _info("This looks like an existing project (migration / re-run). Re-run with --force — "
                  "it is now NON-DESTRUCTIVE: existing CLAUDE.md / README.md / .gitignore are preserved, "
                  "not overwritten (P2 fix).")
            return 1

    description = args.project_description or ""
    # research/development split removed 2026-06-15 — every project gets both.
    # --project-type is accepted but ignored (back-compat); recorded as "merged".
    project_type = "merged"

    wiki_src = bootstrap / "bootstrap" / "workflows" / "llm-wiki"
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

    # B6 — apply the single merged folder taxonomy under llm-wiki/wiki/
    folders = MERGED_TAXONOMY
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
    _ok(f"merged wiki folder taxonomy applied: {len(folders)} folders")

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
    # CLAUDE.md @-imports: relative paths for an in-project wiki, absolute for an
    # external vault (the wiki isn't under the project dir).
    if external_vault:
        llm_wiki_path_str = paths["llm_wiki"].as_posix()
        wiki_path_str = paths["llm_wiki_wiki"].as_posix()
    else:
        llm_wiki_path_str = "llm-wiki"
        wiki_path_str = "llm-wiki/wiki"
    template_vars = {
        "PROJECT_NAME": name,
        "PROJECT_DESCRIPTION": description,
        "LLM_WIKI_PATH": llm_wiki_path_str,
        "WIKI_PATH": wiki_path_str,
        "PROJECT_TYPE": project_type,
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
        nb_options = {"wrap_up_auto_promote": args.wrap_up_auto_promote}
        if args.dry_run:
            print(f"WOULD register notebook '{name}' -> {{root: {entry}, "
                  f"wrap_up_auto_promote: {args.wrap_up_auto_promote}}} in {registry_path}")
        else:
            _upsert_registry(registry_path, name, entry, options=nb_options)
            _ok(f"registered '{name}' -> {entry} (wrap_up_auto_promote={args.wrap_up_auto_promote}) "
                f"in {registry_path.name}")
        project_cfg = {
            "tool": args.tool,
            "project_name": name,
            "notebook": name,
            "registry": registry_path.as_posix(),
            "project_description": description,
            "skills_install": skills_install,
            # NOTE: wrap_up_auto_promote lives in the REGISTRY entry (per-notebook,
            # travels with the notebook), not here — see _upsert_registry above.
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
        # Review gate for /wrap-up: ask (prompt) | true (auto-promote) | false (stay staged).
        "wrap_up_auto_promote": args.wrap_up_auto_promote,
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

    needs_restart = False

    # B10 — agentmemory was removed 2026-05-14. The proactive-listener pattern
    # (agent files durable items to _inbox/proposed/ inline) replaces it.
    # See the comment above _agentmemory_wired (deleted) for the retrospective.

    # B11 — summary + next steps (single merged flow: ingest research AND
    # capture project knowledge — every project does both).
    start_cmd = "claude" if args.tool == "claude-code" else "cursor ."

    next_steps = [
        f"cd {target}",
        f"Start Claude Code: `{start_cmd}`",
        "Read `llm-wiki/README.md` (project overview) + `llm-wiki/how-to/commands.md` (command reference)",
        "INGEST research: `/wiki-update <url>` ad-hoc, OR drop links into Drive (__FOR CLAUDE/<project-slug>/) and run `/wiki-cycle` to discover → ingest → lint → promote",
        "CAPTURE project knowledge: as you code/decide/debug, the agent files durable items (decisions, components, patterns, gotchas) to `llm-wiki/wiki/_inbox/proposed/` inline; run `/wrap-up` at session-end to catch the rest",
        "Promote: `/wiki-promote --review` accepts/rejects proposed entries (research → research/, project knowledge → project/)",
        "Search: `/wiki-search \"<query>\"` (hybrid BM25 + vector + LLM rerank)",
        "Source tiers (research): T1 peer-reviewed/primary, T2 vendor/official, T3 expert, T4 community. Both-sides-stay: never delete contradictory entries, cross-link them",
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
    parser.add_argument("--phase", choices=["A", "B", "sync"], default=None,
                        help="A = install /new-wiki skill globally + record bootstrap source. "
                             "B = scaffold a per-project install (skills/scripts/llm-wiki/) at --target-folder. "
                             "sync = re-run A to refresh the global /new-wiki skill. "
                             "Mutually exclusive with --mode.")
    parser.add_argument("--mode", choices=["tooling"], default=None,
                        help="tooling = GLOBAL tooling-only install (all skills + scripts into "
                             "~/.claude/, no project scaffold). Mutually exclusive with --phase.")
    parser.add_argument("--tool", choices=["claude-code", "cursor"], default="claude-code",
                        help="Which AI tool to install for (default: claude-code)")
    parser.add_argument("--project-name")
    parser.add_argument("--project-description", default="")
    parser.add_argument("--project-type", default=None,
                        help="(deprecated, ignored as of 2026-06-15 — research/development "
                             "split removed; every project gets the merged taxonomy)")
    parser.add_argument("--target-folder",
                        help="Project root folder (required for --phase B)")
    parser.add_argument("--wrap-up-auto-promote", choices=["ask", "true", "false"], default="ask",
                        help="Review gate for /wrap-up's staged entries: 'ask' (prompt each time — "
                             "manual review, default), 'true' (auto-promote, no prompt), 'false' "
                             "(stay staged, promote later). Written to wiki-config.json; changeable anytime.")
    parser.add_argument("--skills-install", choices=["global", "bundled"], default="global",
                        help="global (default) = use shared ~/.claude/skills + wiki-scripts, "
                             "no per-project copy; bundled = copy skills+scripts into the project "
                             "(self-contained). Cursor always bundles.")
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
    args = parser.parse_args()

    if args.mode and args.phase:
        _err("pass exactly one of --mode or --phase, not both")
        return 1
    if not args.mode and not args.phase:
        _err("one of --mode or --phase is required")
        return 1

    if args.mode == "tooling":
        return phase_tooling(args)
    if args.phase == "A":
        return phase_a(args)
    if args.phase == "B":
        return phase_b(args)
    if args.phase == "sync":
        # Re-run Phase A to refresh the global /new-wiki skill
        return phase_a(args)


if __name__ == "__main__":
    sys.exit(main())
