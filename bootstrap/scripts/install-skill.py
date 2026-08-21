#!/usr/bin/env python3
"""
install-skill.py — copy ONE skill from this package onto the local system,
substituting path placeholders. The reusable per-skill primitive: the wiki
installer calls it once per skill, and it works for any skill we ship.

What it does (Claude Code):
  - Copies  <skills-src>/<name>/  →  <skills-dest>/<name>/   (the whole dir:
    SKILL.md plus any bundled files).
  - Substitutes the {{WIKI_SCRIPTS_DIR}} placeholder in every copied text file
    with the resolved absolute scripts dir (forward-slash form so the path
    works in both bash and Windows Python).
  - Idempotent — re-running overwrites the installed copy.

Cursor:
  - Not supported yet. Prints a notice and exits 0 (so a per-skill loop in the
    orchestrator doesn't break). A real Cursor branch (.cursor/rules) comes later.

Usage:
  python install-skill.py --skill wiki-cycle
  python install-skill.py --skill wiki-update --tool claude-code \
      --skills-src  <pkg>/bootstrap/skills \
      --skills-dest ~/.claude/skills \
      --scripts-dir ~/.claude/wiki-scripts \
      [--dry-run]

Defaults: tool=claude-code; skills-src = this package's skills dir;
skills-dest = ~/.claude/skills; scripts-dir = ~/.claude/wiki-scripts.

Exit codes: 0 ok / skipped(cursor); 2 bad args / source skill missing.
"""
from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

PLACEHOLDER = "{{WIKI_SCRIPTS_DIR}}"
# Repo layout: scripts/install-skill.py → skills/ is ../skills relative to here.
_PKG_SKILLS_DEFAULT = Path(__file__).resolve().parent.parent / "skills"


def _norm(p: Path) -> str:
    """Absolute path in forward-slash form (safe for bash + Windows Python)."""
    return p.expanduser().resolve().as_posix()


def _substitute_placeholders(dest_dir: Path, scripts_dir_value: str, dry_run: bool) -> int:
    """Replace {{WIKI_SCRIPTS_DIR}} in every text file under dest_dir. Returns count."""
    changed = 0
    for f in sorted(dest_dir.rglob("*")):
        if not f.is_file():
            continue
        try:
            text = f.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue  # skip binaries / unreadable
        if PLACEHOLDER in text:
            new_text = text.replace(PLACEHOLDER, scripts_dir_value)
            if not dry_run:
                f.write_text(new_text, encoding="utf-8", newline="")
            changed += 1
    return changed


def install_skill(skill: str, tool: str, skills_src: Path, skills_dest: Path,
                  scripts_dir: Path, dry_run: bool) -> int:
    if tool == "cursor":
        print(f"  - {skill}: Cursor not supported yet — skipped.")
        return 0
    if tool != "claude-code":
        print(f"ERROR: unknown tool {tool!r} (expected claude-code | cursor)", file=sys.stderr)
        return 2

    src = skills_src / skill
    if not (src / "SKILL.md").is_file():
        print(f"ERROR: skill {skill!r} not found at {src} (no SKILL.md)", file=sys.stderr)
        return 2

    dest = skills_dest / skill
    scripts_value = _norm(scripts_dir)

    if dry_run:
        print(f"  - {skill}: would copy {src} → {dest}  ({PLACEHOLDER} → {scripts_value})")
        return 0

    if dest.exists():
        shutil.rmtree(dest)
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(src, dest)
    subbed = _substitute_placeholders(dest, scripts_value, dry_run=False)
    print(f"  - {skill}: installed → {dest}  ({subbed} file(s) path-substituted)")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="Copy one skill onto the local system (reusable primitive).")
    ap.add_argument("--skill", required=True, help="Skill directory name (e.g. wiki-cycle)")
    ap.add_argument("--tool", default="claude-code", choices=["claude-code", "cursor"])
    ap.add_argument("--skills-src", default=str(_PKG_SKILLS_DEFAULT),
                    help="Source skills dir in this package (default: ../skills)")
    ap.add_argument("--skills-dest", default="~/.claude/skills",
                    help="Destination skills dir (default: ~/.claude/skills)")
    ap.add_argument("--scripts-dir", default="~/.claude/wiki-scripts",
                    help="Absolute scripts dir substituted for {{WIKI_SCRIPTS_DIR}} (default: ~/.claude/wiki-scripts)")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    return install_skill(
        skill=args.skill,
        tool=args.tool,
        skills_src=Path(args.skills_src).expanduser(),
        skills_dest=Path(args.skills_dest).expanduser(),
        scripts_dir=Path(args.scripts_dir),
        dry_run=args.dry_run,
    )


if __name__ == "__main__":
    raise SystemExit(main())
