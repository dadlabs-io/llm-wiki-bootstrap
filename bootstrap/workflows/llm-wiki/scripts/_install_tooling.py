#!/usr/bin/env python3
"""_install_tooling.py — shared global tooling-install logic for the LLM-wiki
framework.

Single source of truth for: the script + skill manifests, bootstrap-source
discovery, and the copy/install loop (built on the install-skill.py per-skill
primitive). Imported by BOTH:

  - wiki-upgrade.py   — the standalone "refresh global tooling from master" command
  - new-wiki.py       — project bootstrap (also lays down the global tooling)

Keeping this here means the manifests and the install loop are defined ONCE.
This module is claude-code-focused for the global install; Cursor's rule-based
install stays in new-wiki.py (_phase_tooling_cursor) but reuses these manifests.
"""
from __future__ import annotations

import importlib.util
import json
import shutil
import subprocess
import sys
from pathlib import Path

# ---------- Global install targets (claude-code) ----------
CC_GLOBAL_DIR = Path.home() / ".claude"
CC_GLOBAL_SKILLS_DIR = CC_GLOBAL_DIR / "skills"
CC_GLOBAL_WIKI_SCRIPTS_DIR = CC_GLOBAL_DIR / "wiki-scripts"
CC_GLOBAL_CONFIG_PATH = CC_GLOBAL_DIR / "wiki-config.json"

# ---------- Manifests (single source of truth) ----------
# User-invokable scripts that travel to every install.
TRAVEL_SCRIPTS = [
    "new-wiki.py",
    "wiki-init.py",
    "wiki-fetch-drive-folder.py",
    "wiki-fetch-pdf.py",
    "wiki-fetch-youtube.py",
    "wiki-index.py",
    "wiki-index-per-folder.py",
    "wiki-lint-mechanical.py",
    "wiki-fix-links.py",
    "wiki-dequeue.py",
    "wiki-list-add.py",
    "wiki-list-process.py",
    "wiki-list-render.py",
    "wiki-map-compile.py",
    "wiki-promote.py",
    "wiki-reciprocate-backlinks.py",
    "wiki-update.py",
    "wiki-upgrade.py",
]

# Skill directories that travel to every install.
TRAVEL_SKILLS = [
    "new-wiki", "wrap-up", "upd-docs",
    "wiki", "wiki-init", "wiki-update", "wiki-search", "wiki-cycle",
    "wiki-discover", "wiki-list", "wiki-claims", "wiki-refresh",
    "wiki-report", "wiki-lint", "wiki-promote",
]

# Helper scripts copied alongside TRAVEL_SCRIPTS in a tooling install (not
# user-invoked; imported/called by the tooling). Copied only if present.
TOOLING_HELPER_SCRIPTS = ["install-skill.py", "_atomic_io.py", "_wiki_config.py", "_install_tooling.py"]

# Shared helper modules imported by the travel scripts — MUST ship anywhere the
# scripts run (both global tooling install and per-project Phase B).
SHARED_HELPER_SCRIPTS = ["_atomic_io.py", "_wiki_config.py", "_install_tooling.py"]


def _log(msg):
    print(f"[install-tooling] {msg}")


def derive_bootstrap_source(explicit=None):
    """Find the workflows-core / llm-wiki-bootstrap source. Order: explicit arg,
    ~/.claude/wiki-config.json `bootstrap_source`, walk up from this script,
    walk up from CWD — looking for `bootstrap/workflows/llm-wiki`."""
    if explicit:
        return Path(explicit).resolve()
    try:
        if CC_GLOBAL_CONFIG_PATH.exists():
            cfg = json.loads(CC_GLOBAL_CONFIG_PATH.read_text(encoding="utf-8"))
            if cfg.get("bootstrap_source"):
                return Path(cfg["bootstrap_source"]).resolve()
    except (json.JSONDecodeError, OSError):
        pass
    here = Path(__file__).resolve()
    for parent in [here.parent, *here.parents]:
        if (parent / "bootstrap" / "workflows" / "llm-wiki").is_dir():
            return parent.resolve()
    cwd_root = Path.cwd()
    for parent in [cwd_root, *cwd_root.parents]:
        if (parent / "bootstrap" / "workflows" / "llm-wiki").is_dir():
            return parent.resolve()
    return None


def load_install_skill_fn(scripts_src: Path):
    """Import install_skill() from the package's install-skill.py. Falls back to
    a subprocess shim if the import fails for any reason."""
    install_path = scripts_src / "install-skill.py"
    if install_path.is_file():
        spec = importlib.util.spec_from_file_location("_install_skill_mod", install_path)
        if spec and spec.loader:
            mod = importlib.util.module_from_spec(spec)
            try:
                spec.loader.exec_module(mod)
                if hasattr(mod, "install_skill"):
                    return mod.install_skill
            except Exception as e:  # noqa: BLE001
                _log(f"WARN: could not import install_skill() ({e}); using subprocess fallback")

    def _subprocess_install(skill, tool, skills_src, skills_dest, scripts_dir, dry_run):
        cmd = [
            sys.executable, str(install_path),
            "--skill", skill, "--tool", tool,
            "--skills-src", str(skills_src), "--skills-dest", str(skills_dest),
            "--scripts-dir", str(scripts_dir),
        ]
        if dry_run:
            cmd.append("--dry-run")
        return subprocess.run(cmd).returncode

    return _subprocess_install


def install_tooling(bootstrap_source: Path, dry_run: bool = False,
                    skills_dest: Path = None, scripts_dest: Path = None) -> dict:
    """Global claude-code tooling install: copy TRAVEL_SCRIPTS (+ helpers) to
    the scripts dir and install each TRAVEL_SKILLS dir via the install-skill
    primitive. Idempotent. Returns a summary dict (caller prints)."""
    bootstrap = Path(bootstrap_source)
    pkg = bootstrap / "bootstrap" / "workflows" / "llm-wiki"
    scripts_src = pkg / "scripts"
    skills_src = pkg / "skills"
    if not scripts_src.is_dir() or not skills_src.is_dir():
        raise FileNotFoundError(f"package scripts/ or skills/ missing under {pkg}")

    skills_dest = Path(skills_dest) if skills_dest else CC_GLOBAL_SKILLS_DIR
    scripts_dest = Path(scripts_dest) if scripts_dest else CC_GLOBAL_WIKI_SCRIPTS_DIR
    scripts_dest_value = scripts_dest.expanduser().resolve().as_posix()

    # 1) Copy scripts (TRAVEL_SCRIPTS + helpers)
    if not dry_run:
        scripts_dest.mkdir(parents=True, exist_ok=True)
    script_names = list(TRAVEL_SCRIPTS)
    for helper in TOOLING_HELPER_SCRIPTS:
        if (scripts_src / helper).is_file():
            script_names.append(helper)
    travel_copied = helpers_copied = 0
    scripts_missing = []
    for name in script_names:
        s = scripts_src / name
        if not s.is_file():
            scripts_missing.append(name)
            continue
        if dry_run:
            print(f"  WOULD copy {s} -> {scripts_dest / name}")
        else:
            shutil.copy2(s, scripts_dest / name)
        if name in TOOLING_HELPER_SCRIPTS:
            helpers_copied += 1
        else:
            travel_copied += 1

    # 2) Install each skill via the install-skill primitive
    install_fn = load_install_skill_fn(scripts_src)
    skills_installed = 0
    skills_failed = []
    for skill in TRAVEL_SKILLS:
        rc = install_fn(skill=skill, tool="claude-code", skills_src=skills_src,
                        skills_dest=skills_dest, scripts_dir=scripts_dest, dry_run=dry_run)
        if rc == 0:
            skills_installed += 1
        else:
            skills_failed.append(skill)

    return {
        "bootstrap": str(bootstrap),
        "scripts_copied": travel_copied,
        "helpers_copied": helpers_copied,
        "skills_installed": skills_installed,
        "skills_failed": skills_failed,
        "scripts_missing": scripts_missing,
        "scripts_dest": str(scripts_dest),
        "skills_dest": str(skills_dest),
        "scripts_dest_value": scripts_dest_value,
        "dry_run": dry_run,
    }


def print_summary(summary: dict):
    dry = summary.get("dry_run")
    if summary.get("scripts_missing"):
        _log(f"WARN: scripts not found in package (skipped): {summary['scripts_missing']}")
    if summary.get("skills_failed"):
        _log(f"WARN: skills that failed to install: {summary['skills_failed']}")
    print()
    print("=" * 60)
    print("Global tooling install summary")
    print("=" * 60)
    verb = "would be copied" if dry else "copied"
    print(f"  scripts {verb}:   {summary['scripts_copied']}  (+ {summary['helpers_copied']} helpers)  → {summary['scripts_dest']}")
    verb_s = "would be installed" if dry else "installed"
    print(f"  skills {verb_s}: {summary['skills_installed']}  → {summary['skills_dest']}")
    print(f"  placeholder {{{{WIKI_SCRIPTS_DIR}}}} → {summary['scripts_dest_value']}")
    print()
    print("  Restart Claude Code if these dirs are new so it picks up the")
    print("  new skills + scripts.")
    print("=" * 60)
