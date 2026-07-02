#!/usr/bin/env python3
"""wiki-dequeue.py — move already-ingested items out of the pending queue.

The ingest queue (`_inbox/pending/*.md`) is supposed to drain to `_inbox/done/`
as items get ingested. `wiki-update.py` does that move ONLY on its direct
from-queue path (Step 9). The `--staged` batch path used by `/wiki-cycle` files
the entry to `_inbox/proposed/` and never touches the queue file, so ingested
items pile up in `pending/`. Every subsequent cycle then has to hand-reconcile
"which of these 60 pending items did we already ingest?" before it can drain the
queue — exactly what happened at the start of cycles 2026-07-01 and 2026-07-02.

This is the permanent, source_url-based reconciler. An item counts as ingested
if its `source:` URL matches the `source_url:` of any entry already in `wiki/`
OR in `_inbox/proposed/` (staged-but-not-yet-promoted still counts — the work is
done, promotion is a separate step). Matched items move to `_inbox/done/`;
everything else (genuinely-unprocessed, or deferred placeholders like unreadable
X links) stays put.

Run it as a cycle step right after ingest, or standalone any time to tidy the
queue. Registry-aware via _wiki_config. Idempotent.
"""
import argparse
import json
import os
import re
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _wiki_config  # noqa: E402


def _norm(u: str) -> str:
    """Normalize a URL for matching: strip scheme/www, collapse arxiv ids and
    github user/repo, drop query/fragment."""
    u = (u or "").strip().lower().rstrip("/")
    u = re.sub(r"^https?://", "", u)
    u = re.sub(r"^www\.", "", u)
    m = re.search(r"arxiv\.org/(?:abs|pdf|html)/(\d+\.\d+)", u)
    if m:
        return "arxiv:" + m.group(1)
    m = re.search(r"github\.com/([^/]+/[^/]+)", u)
    if m:
        return "github:" + m.group(1).replace(".git", "")
    return u.split("?")[0].split("#")[0]


def _ingested_source_urls(wiki_dir: Path, proposed_dir: Path):
    urls = set()
    scan = [wiki_dir]
    if proposed_dir.exists():
        scan.append(proposed_dir)
    for base in scan:
        for f in base.rglob("*.md"):
            # wiki_dir contains _inbox/proposed as a child in some layouts; only
            # skip _inbox subtrees that are NOT the proposed dir we explicitly scan.
            if "_inbox" in f.parts and proposed_dir not in f.parents and f.parent != proposed_dir:
                continue
            try:
                head = f.read_text(encoding="utf-8", errors="ignore")[:1500]
            except OSError:
                continue
            for m in re.finditer(r"source_url:\s*(\S+)", head):
                urls.add(_norm(m.group(1)))
    return urls


def main():
    ap = argparse.ArgumentParser(description="Move already-ingested pending items to _inbox/done/.")
    ap.add_argument("--topic", help="Topic name (registry-resolved).")
    ap.add_argument("--vault", help="Vault root override.")
    ap.add_argument("--dry-run", action="store_true", help="Report without moving.")
    ap.add_argument("--json", action="store_true", help="Emit JSON summary.")
    args = ap.parse_args()

    topic_root = Path(_wiki_config.topic_root(args.topic))
    wiki_dir = Path(_wiki_config.wiki_dir(args.topic, args.vault))
    pending = topic_root / "_inbox" / "pending"
    done = topic_root / "_inbox" / "done"
    proposed = topic_root / "_inbox" / "proposed"
    if not pending.exists():
        print(f"No pending dir at {pending}; nothing to dequeue.")
        return 0

    ingested = _ingested_source_urls(wiki_dir, proposed)

    moved, kept = [], []
    for p in sorted(pending.glob("*.md")):
        txt = p.read_text(encoding="utf-8", errors="ignore")
        m = re.search(r"^source:\s*(\S+)", txt, re.M)
        src = m.group(1) if m else ""
        if src and _norm(src) in ingested:
            if not args.dry_run:
                done.mkdir(parents=True, exist_ok=True)
                shutil.move(str(p), str(done / p.name))
            moved.append(src)
        else:
            kept.append(src or p.name)

    summary = {"status": "completed", "dry_run": args.dry_run,
               "moved": len(moved), "kept": len(kept)}
    if args.json:
        print(json.dumps({**summary, "moved_urls": moved, "kept": kept}, indent=2, ensure_ascii=False))
    else:
        verb = "WOULD DEQUEUE" if args.dry_run else "DEQUEUED"
        print(f"{verb} {len(moved)} already-ingested item(s) -> _inbox/done/; kept {len(kept)} in pending.")
        for s in kept:
            print(f"  KEPT: {s}")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:  # noqa: BLE001
        print(f"wiki-dequeue.py failed: {e}", file=sys.stderr)
        sys.exit(1)
