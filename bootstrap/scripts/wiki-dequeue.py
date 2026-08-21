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
import urllib.parse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _wiki_config  # noqa: E402


def _norm(u: str) -> str:
    """Normalize a URL for matching: strip scheme/www, decode %-escapes,
    collapse arxiv ids, drop query/fragment.

    GitHub URLs: keep the full blob/tree path when one is present (only
    normalizing away the `blob/<branch>/` or `tree/<branch>/` noise) — do
    NOT collapse to a bare `github:user/repo` key unless the URL genuinely
    has no path beyond the repo root. Collapsing every `github.com/u/r/...`
    URL to `github:u/r` was the root cause of a real over-match bug (2026-07-10,
    see wiki/project/troubleshooting/wiki-dequeue-url-over-match-bug-2026-07-10.md):
    a queue item citing `.../blob/main/skills/codex-first/SKILL.md` matched
    an unrelated existing entry whose source_url was `.../skills/codex-review/SKILL.md`
    — same repo, different file, silently treated as already-ingested and
    dequeued without ever being ingested. wiki-update.py never rewrites a
    filed entry's `source_url` away from what the user/caller originally gave
    it (see wiki-update.py's acquire_source(), which returns the ORIGINAL
    `source` string, not the fetch-rewritten URL) — so a bare repo-root
    citation and a deep-link into the same repo are never the same intended
    URL, and must not share a match key. This does mean a bare
    `github.com/user/repo` queue item and a `.../blob/main/README.md` entry
    for the "same" content will now be treated as different keys (they were
    conflated before) — that's the safer direction to err: a false negative
    here just means an already-covered item gets manually re-checked and
    re-queued (recoverable); a false positive silently drops a genuinely new
    source (not recoverable without exactly this kind of forensic dig).
    """
    u = (u or "").strip().lower().rstrip("/")
    u = re.sub(r"^https?://", "", u)
    u = re.sub(r"^www\.", "", u)
    u = u.split("?")[0].split("#")[0]
    u = urllib.parse.unquote(u)  # decode %2F etc. BEFORE matching, not after
    m = re.search(r"arxiv\.org/(?:abs|pdf|html)/(\d+\.\d+)", u)
    if m:
        return "arxiv:" + m.group(1)
    m = re.match(r"github\.com/([^/]+)/([^/]+)(/.*)?$", u)
    if m:
        user, repo, rest = m.group(1), m.group(2), m.group(3) or ""
        repo = repo.replace(".git", "")
        if rest:
            rest = re.sub(r"^/(?:blob|tree)/[^/]+/", "/", rest)
            return f"github:{user}/{repo}{rest}"
        return f"github:{user}/{repo}"
    return u


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
