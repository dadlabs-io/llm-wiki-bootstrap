#!/usr/bin/env python3
"""wiki-fix-links.py — resolve bare-slug / wrong-depth markdown links to their
correct relative path.

The staged-ingest contract tells ingest agents to author cross-links by BARE
SLUG (``[Title](other-slug.md)``) and promises the paths are "normalized
mechanically". That normalization was NOT actually happening end-to-end: a bare
``](mem0-chhikara-et-al.md)`` in ``wiki/research/long-term/`` resolves to
``wiki/research/long-term/mem0-chhikara-et-al.md`` — but the target lives in
``research/active/``, so the link breaks the moment the target is in a different
folder. Same failure mode hit cycles 2026-06-24, 2026-07-01, and 2026-07-02
(≈50 broken links each), every time hand-repaired with a one-off script. This is
that one-off generalized into a permanent, idempotent cycle step.

What it does, per markdown link ``](target)`` in scope:
  * Skip external (http/mailto/#anchor) and non-.md targets.
  * If ``(source_dir / target)`` already exists → leave it (already correct).
  * Else take the basename and look it up in a prebuilt index of every real
    file under ``wiki/`` (excluding ``_inbox/``) plus every file under ``raw/``:
      - exactly one match  → rewrite to the correct relpath from source_dir
      - multiple matches   → AMBIGUOUS, skip + warn (don't guess)
      - zero matches       → MISSING, skip + warn (target truly doesn't exist)

Preserves already-correct links (never turns a good link bad). Idempotent:
running twice is a no-op on the second pass.

Resolution of which wiki is registry-aware via _wiki_config (same as the rest of
the tooling). Run from a cwd whose .claude/wiki-config.json resolves the topic
(e.g. the project/hub root), or pass --vault to override.
"""
import argparse
import json
import os
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _wiki_config  # noqa: E402

# ](target)  — inline markdown link target, no surrounding capture of the text.
_LINK_RE = re.compile(r'(?<=\]\()([^)\s]+?\.md)(?=\))')


def _is_external(target: str) -> bool:
    return target.startswith(("http://", "https://", "mailto:", "#"))


def _build_index(wiki_dir: Path, raw_dir: Path):
    """basename -> list[abs Path] across wiki/ (minus _inbox) and raw/."""
    idx = {}
    for base in (wiki_dir, raw_dir):
        if not base.exists():
            continue
        for f in base.rglob("*.md"):
            if "_inbox" in f.parts:
                continue
            idx.setdefault(f.name, []).append(f)
    return idx


def _fix_file(path: Path, index, dry_run: bool):
    text = path.read_text(encoding="utf-8", errors="ignore")
    src_dir = path.parent
    fixed, ambiguous, missing = [], [], []

    def _sub(m):
        target = m.group(1)
        if _is_external(target):
            return target
        # Already resolves from the source location? leave it.
        if (src_dir / target).resolve().exists():
            return target
        basename = target.rsplit("/", 1)[-1]
        matches = index.get(basename, [])
        if len(matches) == 1:
            newrel = os.path.relpath(matches[0], src_dir).replace(os.sep, "/")
            if newrel != target:
                fixed.append((target, newrel))
            return newrel
        if len(matches) > 1:
            ambiguous.append((target, [str(x) for x in matches]))
            return target
        missing.append(target)
        return target

    new_text = _LINK_RE.sub(_sub, text)
    if new_text != text and not dry_run:
        path.write_text(new_text, encoding="utf-8")
    return fixed, ambiguous, missing


def main():
    ap = argparse.ArgumentParser(description="Resolve bare-slug/wrong-depth markdown links to correct relative paths.")
    ap.add_argument("--topic", help="Topic name (registry-resolved).")
    ap.add_argument("--vault", help="Vault root override (forces <vault>/<topic>/wiki).")
    ap.add_argument("--files", nargs="*", help="Specific entry files to fix (default: whole wiki/).")
    ap.add_argument("--dry-run", action="store_true", help="Report actions without writing.")
    ap.add_argument("--json", action="store_true", help="Emit a JSON summary to stdout.")
    args = ap.parse_args()

    wiki_dir = Path(_wiki_config.wiki_dir(args.topic, args.vault))
    topic_root = Path(_wiki_config.topic_root(args.topic))
    raw_dir = topic_root / "raw"
    if not wiki_dir.exists():
        print(f"ERROR: wiki dir not found: {wiki_dir}", file=sys.stderr)
        return 2

    index = _build_index(wiki_dir, raw_dir)

    if args.files:
        targets = [Path(f) for f in args.files]
    else:
        targets = [f for f in wiki_dir.rglob("*.md")
                   if "_inbox" not in f.parts and f.name != "_INDEX.md" and f.name != "_MAP.md"]

    total_fixed = total_ambig = total_missing = 0
    per_file = []
    for f in targets:
        if not f.exists():
            continue
        fixed, ambiguous, missing = _fix_file(f, index, args.dry_run)
        if fixed or ambiguous or missing:
            per_file.append({"file": str(f.relative_to(wiki_dir)).replace(os.sep, "/"),
                             "fixed": fixed, "ambiguous": ambiguous, "missing": missing})
        total_fixed += len(fixed)
        total_ambig += len(ambiguous)
        total_missing += len(missing)

    summary = {"status": "completed", "wiki": str(wiki_dir),
               "files_touched": len([p for p in per_file if p["fixed"]]),
               "links_fixed": total_fixed, "ambiguous": total_ambig,
               "missing": total_missing, "dry_run": args.dry_run}

    if args.json:
        print(json.dumps({**summary, "details": per_file}, indent=2, ensure_ascii=False))
    else:
        verb = "WOULD FIX" if args.dry_run else "FIXED"
        print(f"{verb} {total_fixed} link(s) across {summary['files_touched']} file(s); "
              f"ambiguous={total_ambig}, missing={total_missing}")
        for pf in per_file:
            for old, new in pf["fixed"]:
                print(f"  {pf['file']}: {old} -> {new}")
            for old, cands in pf["ambiguous"]:
                print(f"  [AMBIGUOUS] {pf['file']}: {old} matches {len(cands)} files — left as-is")
            for old in pf["missing"]:
                print(f"  [MISSING] {pf['file']}: {old} — target not found anywhere, left as-is")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:  # noqa: BLE001
        print(f"wiki-fix-links.py failed: {e}", file=sys.stderr)
        sys.exit(1)
