#!/usr/bin/env python3
"""
wiki-verify.py — Verify primitive (icarus §5).

Flips an entry's truth-status from `unverified` → `verified` via sidecar update,
recording who certified, when, and (optionally) what evidence. Enforces the
icarus invariant that an entry CANNOT self-certify on initial write — only this
script (or `/wiki-verify`) can set verified=verified.

Algorithm:
  1. Resolve entry
  2. Read current verified state (frontmatter wins, sidecar fallback)
  3. Refuse to "re-verify" if already verified (no-op with informative message)
  4. Refuse to verify a `contradicted` or `rolled_back` entry (use rollback's
     reverse-flow instead — manual review required)
  5. Write sidecar with verified=verified, verified_at=now, verified_by=<who>,
     verified_evidence=<optional>
  6. (Optional, off by default) Mirror back to frontmatter

Usage:
  python wiki-verify.py <slug> --topic <topic> [options]

Options:
  --by {human,agent,tool}    Who certified. Default: human.
                             - human  → editorial signoff
                             - agent  → LLM judge / automated review
                             - tool   → sandbox / test / static analyzer (Aardvark-style)
  --evidence "<text>"        Optional one-line description of the evidence basis.
  --mirror                   Also update frontmatter `verified: verified` (default off — keeps
                             git clean per memory-signals doc; sidecar is the truth).
  --dry-run                  Show what would change without writing.

Exit codes:
  0 — success (or already-verified no-op)
  1 — entry is `contradicted` or `rolled_back` (refused; manual review needed)
  2 — slug not found or other usage error
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

# Atomic-write helper (icarus §8).
sys.path.insert(0, str(Path(__file__).resolve().parent))
from _atomic_io import atomic_write_text  # noqa: E402

FM_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)
VERIFIED_LINE_RE = re.compile(r"^verified:\s*\S+\s*$", re.MULTILINE)


# Path-resolution helper lives in the shared _wiki_config module (single
# source of truth for the multi-wiki config schema).
sys.path.insert(0, str(Path(__file__).resolve().parent))
from _wiki_config import default_vault as _default_vault  # noqa: E402


def iso_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def resolve_entry(topic_root: Path, slug_or_path: str) -> Path | None:
    p = Path(slug_or_path)
    candidates = [p, topic_root / p, topic_root / "wiki" / p]
    for c in candidates:
        if c.exists() and c.is_file():
            return c.resolve()
    basename = p.name if p.suffix == ".md" else p.name + ".md"
    matches = list((topic_root / "wiki").rglob(basename))
    if len(matches) == 1:
        return matches[0].resolve()
    if len(matches) > 1:
        print(f"ERROR: slug {slug_or_path!r} matches multiple entries:", file=sys.stderr)
        for m in matches:
            print(f"  {m.relative_to(topic_root)}", file=sys.stderr)
        sys.exit(2)
    return None


def parse_fm(entry: Path) -> dict[str, str]:
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


def read_verified(topic_root: Path, entry: Path, fm: dict) -> str | None:
    v = fm.get("verified", "").strip()
    if v:
        return v
    return read_sidecar(topic_root, entry).get("verified")


def mirror_frontmatter(entry: Path, dry_run: bool) -> bool:
    """Update or insert `verified: verified` in the entry's frontmatter. Returns True if changed."""
    text = entry.read_text(encoding="utf-8")
    m = FM_RE.match(text)
    if not m:
        # No frontmatter — skip the mirror (don't try to invent one)
        print(f"WARN: {entry.name} has no frontmatter; skipping mirror.", file=sys.stderr)
        return False
    fm_block = m.group(1)
    if VERIFIED_LINE_RE.search(fm_block):
        new_fm_block = VERIFIED_LINE_RE.sub("verified: verified", fm_block, count=1)
    else:
        # Insert at end of frontmatter
        new_fm_block = fm_block.rstrip() + "\nverified: verified"
    if new_fm_block == fm_block:
        return False
    new_text = text[:m.start(1)] + new_fm_block + text[m.end(1):]
    if not dry_run:
        atomic_write_text(entry, new_text)
    return True


def main() -> int:
    ap = argparse.ArgumentParser(description="Verify a wiki entry (set verified=verified via sidecar)")
    ap.add_argument("slug", help="Entry to verify (slug, relative path, or absolute path)")
    ap.add_argument("--topic", required=True)
    ap.add_argument("--vault", default=_default_vault())
    ap.add_argument("--by", choices=["human", "agent", "tool"], default="human",
                    help="Who certified. Default: human (editorial signoff).")
    ap.add_argument("--evidence", default="",
                    help="Optional one-line description of evidence basis.")
    ap.add_argument("--mirror", action="store_true",
                    help="Also mirror verified=verified into the entry frontmatter. Default off (sidecar is the truth, frontmatter mirror keeps git clean).")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    topic_root = (Path(args.vault) / args.topic).resolve()
    if not topic_root.exists():
        print(f"ERROR: topic root not found: {topic_root}", file=sys.stderr)
        return 2

    entry = resolve_entry(topic_root, args.slug)
    if entry is None:
        print(f"ERROR: entry not found: {args.slug}", file=sys.stderr)
        return 2

    fm = parse_fm(entry)
    current = read_verified(topic_root, entry, fm)
    print(f"Target: {entry.relative_to(topic_root)}", file=sys.stderr)
    print(f"Current verified state: {current or '(unset)'}", file=sys.stderr)

    if current == "verified":
        print("Already verified — no-op.", file=sys.stderr)
        json.dump({"status": "no-op-already-verified", "target": str(entry.relative_to(topic_root))},
                  sys.stdout, indent=2)
        sys.stdout.write("\n")
        return 0

    if current in ("contradicted", "rolled_back"):
        print(f"\nERROR: entry is currently {current!r}. Cannot directly verify it.", file=sys.stderr)
        print("If you want to restore this entry as the canonical state:", file=sys.stderr)
        print("  1. Manually review what contradicted/rolled it back", file=sys.stderr)
        print("  2. Either fix the entry and create a new revising entry, or", file=sys.stderr)
        print("  3. Write a new entry that revises BOTH this and the contradicting/successor entry, then verify the new one", file=sys.stderr)
        return 1

    # Update sidecar
    sc = read_sidecar(topic_root, entry)
    sc["slug"] = entry.stem
    sc["verified"] = "verified"
    sc["verified_at"] = iso_now()
    sc["verified_by"] = args.by
    if args.evidence:
        sc["verified_evidence"] = args.evidence

    sc_path = sidecar_path(topic_root, entry)
    if args.dry_run:
        print(f"DRY RUN: would write sidecar {sc_path.relative_to(topic_root)}", file=sys.stderr)
        print(f"  contents preview: verified=verified, verified_by={args.by}, verified_at={sc['verified_at']}", file=sys.stderr)
    else:
        sc_path.parent.mkdir(parents=True, exist_ok=True)
        atomic_write_text(sc_path, json.dumps(sc, indent=2))
        print(f"Sidecar updated: {sc_path.relative_to(topic_root)}", file=sys.stderr)

    mirrored = False
    if args.mirror:
        mirrored = mirror_frontmatter(entry, args.dry_run)
        if mirrored:
            print(f"Frontmatter mirror: {entry.relative_to(topic_root)} → verified: verified", file=sys.stderr)

    json.dump({
        "status": "verified" if not args.dry_run else "dry-run",
        "target": str(entry.relative_to(topic_root)),
        "verified_by": args.by,
        "verified_at": sc["verified_at"],
        "evidence": args.evidence or None,
        "frontmatter_mirrored": mirrored,
        "sidecar": str(sc_path.relative_to(topic_root)),
    }, sys.stdout, indent=2)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
