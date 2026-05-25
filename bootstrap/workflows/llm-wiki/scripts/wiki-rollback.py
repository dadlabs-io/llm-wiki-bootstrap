#!/usr/bin/env python3
"""
wiki-rollback.py — First-class rollback primitive for the wiki (icarus §4).

Walks the `revises:` chain backward from a target entry to find the verified
ancestor it restores. Marks every intermediate entry `verified: rolled_back`
in its sidecar (no frontmatter mutation). Writes a new entry with
`type: rollback` documenting what was rolled back and why.

Algorithm (from icarus-integration-plan.md §4):
  1. Walk `revises:` backward from <slug>
  2. Find the first ancestor with `verified: verified` (frontmatter or sidecar)
  3. Mark every intermediate entry `verified: rolled_back` (sidecar update)
  4. Write a new entry with `type: rollback` whose `revises:` points at the
     verified ancestor

Hard rule: if no `verified: verified` ancestor exists in the chain, the rollback
FAILS with an explicit error. Don't corrupt the chain by guessing.

Usage:
  python wiki-rollback.py <slug> --reason "<why>" --topic <topic>
  python wiki-rollback.py wiki/active/foo-2026.md --reason "..." --topic agentic-design

  # Optional cluster-walk: flag sibling entries in the same folder for review
  # (does NOT auto-roll-back siblings; just emits a review list to stderr).
  python wiki-rollback.py <slug> --reason "..." --topic <topic> --cluster-walk

  # Dry-run: show what would change without writing.
  python wiki-rollback.py <slug> --reason "..." --topic <topic> --dry-run

Exit codes:
  0 — success
  1 — chain has no verified ancestor (rollback refused)
  2 — slug not found, or other usage error
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

# Atomic-write helper (icarus §8).
sys.path.insert(0, str(Path(__file__).resolve().parent))
from _atomic_io import atomic_write_text  # noqa: E402

FM_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)
TITLE_RE = re.compile(r"^title:\s*(.+?)\s*$", re.MULTILINE)
VERIFIED_RE = re.compile(r"^verified:\s*(\S+)\s*$", re.MULTILINE)
REVISES_RE = re.compile(r"^revises:\s*(.+?)\s*$", re.MULTILINE)


def _default_vault() -> str:
    cfg = Path.cwd() / ".claude" / "wiki-config.json"
    if cfg.exists():
        try:
            v = json.loads(cfg.read_text(encoding="utf-8")).get("vault_root")
            if v:
                return str(Path(v))
        except (json.JSONDecodeError, OSError):
            pass
    return str(Path.cwd())


def iso_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def resolve_entry(topic_root: Path, slug_or_path: str) -> Path | None:
    """Find an entry by slug (basename) or relative/absolute path."""
    p = Path(slug_or_path)
    candidates = [p, topic_root / p, topic_root / "wiki" / p]
    for c in candidates:
        if c.exists() and c.is_file():
            return c.resolve()
    # Fall back to glob by basename
    basename = p.name if p.suffix == ".md" else p.name + ".md"
    matches = list((topic_root / "wiki").rglob(basename))
    if len(matches) == 1:
        return matches[0].resolve()
    if len(matches) > 1:
        print(f"ERROR: slug {slug_or_path!r} matches multiple entries:", file=sys.stderr)
        for m in matches:
            print(f"  {m.relative_to(topic_root)}", file=sys.stderr)
        print("Pass an explicit relative path to disambiguate.", file=sys.stderr)
        sys.exit(2)
    return None


def parse_fm(entry: Path) -> dict[str, str]:
    """Parse frontmatter into a flat dict. Returns empty dict if no frontmatter."""
    text = entry.read_text(encoding="utf-8", errors="replace")
    m = FM_RE.match(text)
    if not m:
        return {}
    fm = {}
    for line in m.group(1).splitlines():
        if not line.strip() or line.strip().startswith("#") or ":" not in line:
            continue
        k, _, v = line.partition(":")
        fm[k.strip()] = v.strip().strip("\"' ")
    return fm


def sidecar_path(topic_root: Path, entry: Path) -> Path:
    return topic_root / "_signals" / (entry.stem + ".json")


def read_sidecar(topic_root: Path, entry: Path) -> dict:
    sc = sidecar_path(topic_root, entry)
    if not sc.exists():
        return {}
    try:
        return json.loads(sc.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def write_sidecar(topic_root: Path, entry: Path, data: dict, dry_run: bool) -> Path:
    sc = sidecar_path(topic_root, entry)
    if dry_run:
        return sc
    sc.parent.mkdir(parents=True, exist_ok=True)
    atomic_write_text(sc, json.dumps(data, indent=2))
    return sc


def read_verified(topic_root: Path, entry: Path, fm: dict) -> str | None:
    """Read verified status; frontmatter wins, sidecar is fallback."""
    v = fm.get("verified", "").strip()
    if v:
        return v
    sc = read_sidecar(topic_root, entry)
    return sc.get("verified")


def read_revises(fm: dict, entry: Path, topic_root: Path) -> Path | None:
    """Resolve revises: field to an absolute entry path, or None."""
    rev = fm.get("revises", "").strip()
    if not rev:
        return None
    # revises: is a relative path from the entry's folder (same as markdown link semantics)
    candidates = [
        (entry.parent / rev).resolve(),
        topic_root / rev,
        topic_root / "wiki" / rev,
    ]
    for c in candidates:
        if c.exists() and c.is_file():
            return c.resolve()
    return None


def walk_chain(topic_root: Path, target: Path) -> list[Path]:
    """Walk revises backward from target. Returns chain [target, parent, grandparent, ...].
    The verified ancestor (if any) is the last element. Detects cycles."""
    chain = [target]
    seen = {target}
    current = target
    while True:
        fm = parse_fm(current)
        parent = read_revises(fm, current, topic_root)
        if parent is None:
            break
        if parent in seen:
            print(f"ERROR: revises chain cycle detected at {parent.relative_to(topic_root)}", file=sys.stderr)
            sys.exit(2)
        chain.append(parent)
        seen.add(parent)
        current = parent
    return chain


def find_verified_ancestor(topic_root: Path, chain: list[Path]) -> Path | None:
    """Return the FIRST ancestor in chain[1:] that has verified='verified'."""
    for entry in chain[1:]:  # skip target itself
        fm = parse_fm(entry)
        if read_verified(topic_root, entry, fm) == "verified":
            return entry
    return None


def mark_rolled_back(topic_root: Path, entry: Path, dry_run: bool) -> Path:
    """Update sidecar to set verified=rolled_back + rolled_back_at."""
    sc = read_sidecar(topic_root, entry)
    sc["slug"] = entry.stem
    sc["verified"] = "rolled_back"
    sc["rolled_back_at"] = iso_now()
    return write_sidecar(topic_root, entry, sc, dry_run)


def write_rollback_entry(topic_root: Path, verified_ancestor: Path, rolled_back_entries: list[Path],
                          reason: str, dry_run: bool) -> Path:
    """Write a new entry with type: rollback pointing at the verified ancestor."""
    today = datetime.now(timezone.utc).date().isoformat()
    short = uuid.uuid4().hex[:6]
    ancestor_slug = verified_ancestor.stem
    new_slug = f"rollback-to-{ancestor_slug}-{today}-{short}"
    # File next to the verified ancestor by default
    new_path = verified_ancestor.parent / f"{new_slug}.md"

    ancestor_rel = ancestor_slug + ".md"  # same folder → relative is just basename
    rolled_back_list_md = "\n".join(
        f"- `{e.relative_to(topic_root).as_posix()}`" for e in rolled_back_entries
    ) if rolled_back_entries else "_(none — direct rollback)_"

    body = f"""---
title: "Rollback to {ancestor_slug}"
date: {today}
source_url: internal://rollback/{today}-{new_slug}
ingested_by: claude-code
tier: self
confidence: high
last_reviewed: {today}
review_after: {today}
raw_path: (none — self-authored)
type: rollback
revises: {ancestor_rel}
verified: unverified
tags: [rollback, icarus-schema, self-authored]
---

# Rollback to {ancestor_slug}

This entry restores the verified state of [`{ancestor_slug}.md`](./{ancestor_rel}) by rolling back the intermediate entries between it and the most recent revision.

## What was rolled back

The following entries are marked `verified: rolled_back` in their sidecars and excluded from default retrieval:

{rolled_back_list_md}

## Why

{reason}

## What stays in place

- The rolled-back entries remain on disk and remain searchable with `--include-rolled-back` (audit view).
- The verified ancestor is the canonical state going forward.
- Raw archives in `raw/` are untouched (per the no-deletion-only-forgetting principle).

## Next

Any newer entry that should revise the verified ancestor should set `revises: {ancestor_rel}` directly, not chain through the rolled-back intermediates.
"""

    if dry_run:
        print(f"DRY RUN: would write {new_path}", file=sys.stderr)
    else:
        atomic_write_text(new_path, body)
    return new_path


def cluster_walk(topic_root: Path, rolled_back_entries: list[Path]) -> list[Path]:
    """Return sibling entries in same folders as rolled-back ones — for human review only."""
    folders = {e.parent for e in rolled_back_entries}
    rb_set = set(rolled_back_entries)
    flagged = []
    for folder in folders:
        for sib in folder.glob("*.md"):
            if sib.resolve() in rb_set:
                continue
            if sib.name.startswith("_"):
                continue
            flagged.append(sib.resolve())
    return sorted(set(flagged))


def main() -> int:
    ap = argparse.ArgumentParser(description="Rollback a wiki entry to its verified ancestor")
    ap.add_argument("slug", help="Entry to roll back (slug, relative path, or absolute path)")
    ap.add_argument("--reason", required=True, help="One-paragraph explanation of why this rollback")
    ap.add_argument("--topic", required=True, help="Wiki topic name")
    ap.add_argument("--vault", default=_default_vault(), help="Vault root containing the topic folder")
    ap.add_argument("--cluster-walk", action="store_true",
                    help="Also flag sibling entries in the same folder(s) for human review (does NOT auto-roll them back). Refinement from cycle 2026-05-24-01 / Oblivion cluster-decay.")
    ap.add_argument("--dry-run", action="store_true",
                    help="Show what would change without writing.")
    args = ap.parse_args()

    topic_root = (Path(args.vault) / args.topic).resolve()
    if not topic_root.exists():
        print(f"ERROR: topic root not found: {topic_root}", file=sys.stderr)
        return 2

    target = resolve_entry(topic_root, args.slug)
    if target is None:
        print(f"ERROR: entry not found: {args.slug}", file=sys.stderr)
        return 2

    print(f"Target: {target.relative_to(topic_root)}", file=sys.stderr)
    chain = walk_chain(topic_root, target)
    print(f"Chain length (target + ancestors): {len(chain)}", file=sys.stderr)
    for e in chain:
        fm = parse_fm(e)
        v = read_verified(topic_root, e, fm) or "(unset)"
        print(f"  - {e.relative_to(topic_root)} [verified={v}]", file=sys.stderr)

    verified_ancestor = find_verified_ancestor(topic_root, chain)
    if verified_ancestor is None:
        print("\nERROR: no verified ancestor found in the revises: chain.", file=sys.stderr)
        print("Rollback refused — would corrupt the chain by guessing.", file=sys.stderr)
        print("To restore: verify an ancestor first via /wiki-verify, then retry.", file=sys.stderr)
        return 1

    print(f"\nVerified ancestor: {verified_ancestor.relative_to(topic_root)}", file=sys.stderr)
    # Intermediate entries: everything in chain between target and verified ancestor (inclusive of target, exclusive of ancestor)
    intermediates = [e for e in chain if e != verified_ancestor]
    print(f"Will mark {len(intermediates)} entries as rolled_back:", file=sys.stderr)
    for e in intermediates:
        print(f"  - {e.relative_to(topic_root)}", file=sys.stderr)

    if args.dry_run:
        print("\nDRY RUN — no files written.", file=sys.stderr)
    else:
        for e in intermediates:
            sc = mark_rolled_back(topic_root, e, dry_run=False)
            print(f"  sidecar updated: {sc.relative_to(topic_root)}", file=sys.stderr)

    new_entry = write_rollback_entry(topic_root, verified_ancestor, intermediates, args.reason, dry_run=args.dry_run)
    print(f"\nRollback entry: {new_entry.relative_to(topic_root)}", file=sys.stderr)

    if args.cluster_walk:
        siblings = cluster_walk(topic_root, intermediates)
        print(f"\n--cluster-walk: {len(siblings)} sibling entries to review (NOT auto-rolled-back):", file=sys.stderr)
        for s in siblings:
            print(f"  - {s.relative_to(topic_root)}", file=sys.stderr)

    # Emit machine-readable summary on stdout
    json.dump({
        "status": "completed" if not args.dry_run else "dry-run",
        "target": str(target.relative_to(topic_root)),
        "verified_ancestor": str(verified_ancestor.relative_to(topic_root)),
        "rolled_back": [str(e.relative_to(topic_root)) for e in intermediates],
        "new_rollback_entry": str(new_entry.relative_to(topic_root)),
        "cluster_walk_siblings": [str(s.relative_to(topic_root)) for s in cluster_walk(topic_root, intermediates)] if args.cluster_walk else [],
        "timestamp": iso_now(),
    }, sys.stdout, indent=2)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
