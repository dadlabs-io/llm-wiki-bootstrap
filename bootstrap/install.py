#!/usr/bin/env python3
"""
llm-wiki installer — cross-platform.

Installs the framework (scripts + skills) into a target project and
creates a new topic from the topic-template.

Usage
-----
    # Fresh install of llm-wiki + a new topic:
    python install.py --target /path/to/project --topic my-topic

    # Update framework only (preserve existing user content):
    python install.py --target /path/to/project --update

    # Dry-run (show what would happen, write nothing):
    python install.py --target /path/to/project --topic my-topic --dry-run

What gets copied
----------------

Framework (always overwritten on update):
- `scripts/` → <target>/scripts/llm-wiki/
- `skills/`  → <target>/.claude/skills/  (flat — Claude Code expects one level)
- `topic-template/wiki/best-practices/framework/` → ...
                                                  /<vault>/<topic>/wiki/best-practices/framework/
- `topic-template/wiki/llm-wiki-user-guide.md` → user-guide (contract)

User content (NEVER touched by --update):
- `<vault>/<topic>/wiki/<topic-folders>/`  — your entries
- `<vault>/<topic>/raw/`                    — your source dumps
- `<vault>/<topic>/_inbox/`                 — your live state
- `<vault>/<topic>/_config/feeds.md`        — your trusted sources (template only on first install)

Detection logic
---------------

- Fresh install: `<target>/<vault>/<topic>/` doesn't exist → copy whole topic-template
- Update mode: topic exists → only refresh framework files; flag user-edited
  framework files for review (don't overwrite silently)
"""

from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

WORKFLOW = Path(__file__).parent
TEMPLATE_DIR = WORKFLOW / "topic-template"
SCRIPTS_DIR = WORKFLOW / "scripts"
SKILLS_DIR = WORKFLOW / "skills"

# Files in topic-template that ARE framework contracts (always overwrite on update)
FRAMEWORK_PATHS_RELATIVE_TO_TOPIC = [
    "wiki/best-practices/framework/cycle-step-return-format.md",
    "wiki/best-practices/framework/tiered-context-loading.md",
    "wiki/best-practices/framework/wiki-authoring-best-practices.md",
    "wiki/best-practices/framework/wiki-frontmatter-best-practices.md",
    "wiki/llm-wiki-user-guide.md",
]


def log(msg: str, dry: bool = False):
    prefix = "[dry-run] " if dry else ""
    print(f"{prefix}{msg}")


def copy_tree(src: Path, dst: Path, dry: bool):
    if dry:
        for p in src.rglob("*"):
            if p.is_file():
                rel = p.relative_to(src)
                print(f"  [dry-run] would copy {rel}")
        return
    shutil.copytree(src, dst, dirs_exist_ok=True)


def copy_file(src: Path, dst: Path, dry: bool):
    if dry:
        print(f"  [dry-run] would copy {src.name} → {dst}")
        return
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)


def install_scripts(target: Path, dry: bool):
    """Install Python scripts to <target>/scripts/llm-wiki/.

    Also copies topic-template alongside the scripts so wiki-init.py can find
    it when scaffolding additional topics post-install.
    """
    dst = target / "scripts" / "llm-wiki"
    log(f"Installing scripts → {dst}", dry)
    if not dry:
        dst.mkdir(parents=True, exist_ok=True)
    for src in SCRIPTS_DIR.glob("*.py"):
        copy_file(src, dst / src.name, dry)

    # Colocate topic-template so /wiki-init <new-topic> finds it later.
    template_dst = dst / "topic-template"
    log(f"Installing topic-template → {template_dst}", dry)
    copy_tree(TEMPLATE_DIR, template_dst, dry)


def install_skills(target: Path, dry: bool):
    """Install SKILL.md files to <target>/.claude/skills/<skill-name>/SKILL.md.

    Claude Code expects flat layout one-level deep.
    """
    dst_root = target / ".claude" / "skills"
    log(f"Installing skills → {dst_root}", dry)
    if not dry:
        dst_root.mkdir(parents=True, exist_ok=True)
    for src_skill_dir in SKILLS_DIR.iterdir():
        if not src_skill_dir.is_dir():
            continue
        skill_md = src_skill_dir / "SKILL.md"
        if not skill_md.exists():
            continue
        dst_skill_dir = dst_root / src_skill_dir.name
        if not dry:
            dst_skill_dir.mkdir(parents=True, exist_ok=True)
        copy_file(skill_md, dst_skill_dir / "SKILL.md", dry)


def fresh_install_topic(target: Path, vault_rel: str, topic: str, dry: bool):
    """Copy the whole topic-template to a new topic location."""
    dst = target / vault_rel / topic
    if dst.exists() and any(dst.iterdir()):
        print(f"error: topic already exists at {dst}", file=sys.stderr)
        print("       use --update to refresh framework only", file=sys.stderr)
        sys.exit(2)
    log(f"Fresh install of topic '{topic}' → {dst}", dry)
    copy_tree(TEMPLATE_DIR, dst, dry)


def update_framework(target: Path, vault_rel: str, topic: str, dry: bool):
    """Refresh framework files only — preserve user content."""
    topic_root = target / vault_rel / topic
    if not topic_root.exists():
        print(f"error: topic '{topic}' not found at {topic_root}", file=sys.stderr)
        print("       use without --update to do a fresh install", file=sys.stderr)
        sys.exit(2)

    log(f"Updating framework files in topic '{topic}'", dry)
    for rel in FRAMEWORK_PATHS_RELATIVE_TO_TOPIC:
        src = TEMPLATE_DIR / rel
        dst = topic_root / rel
        if not src.exists():
            log(f"  skip (template missing): {rel}", dry)
            continue
        if dst.exists():
            # TODO future: compare framework-version frontmatter; warn if user
            # edited a framework file. For v1, just overwrite (with a notice).
            log(f"  overwriting: {rel}", dry)
        else:
            log(f"  installing (new): {rel}", dry)
        copy_file(src, dst, dry)


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Install or update llm-wiki in a target project."
    )
    ap.add_argument("--target", required=True, type=Path,
                    help="Target project root (where .claude/, scripts/, vault/ go)")
    ap.add_argument("--topic", default=None,
                    help="Topic name (required for fresh install; ignored with --update unless updating one specific topic)")
    ap.add_argument("--vault", default="vault/wikis",
                    help="Vault path relative to --target (default: vault/wikis)")
    ap.add_argument("--update", action="store_true",
                    help="Refresh framework only — preserve user content")
    ap.add_argument("--dry-run", action="store_true",
                    help="Show what would change without writing")
    args = ap.parse_args()

    target: Path = args.target.expanduser().resolve()
    if not target.exists():
        print(f"error: target not found: {target}", file=sys.stderr)
        return 2

    if args.update:
        if not args.topic:
            print("error: --update requires --topic to know which topic to refresh", file=sys.stderr)
            return 2
        install_scripts(target, args.dry_run)
        install_skills(target, args.dry_run)
        update_framework(target, args.vault, args.topic, args.dry_run)
    else:
        if not args.topic:
            print("error: --topic required for fresh install", file=sys.stderr)
            return 2
        install_scripts(target, args.dry_run)
        install_skills(target, args.dry_run)
        fresh_install_topic(target, args.vault, args.topic, args.dry_run)

    if args.dry_run:
        print("\n[dry-run] Nothing was written. Re-run without --dry-run to apply.")
    else:
        print(f"\n✓ Done. Topic root: {target / args.vault / args.topic if args.topic else '(no topic)'}")
        print("  Next: edit _config/feeds.md and run /wiki-update <url> for your first entry.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
