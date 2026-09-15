---
title: "wiki-list — skill"
type: how-to
artifact: skill
name: wiki-list
installed_by: install-wiki
date: 2026-07-31
---

# wiki-list — skill

Low-friction capture for things you want in the wiki but don't want to stop and process right now. It splits ingestion into a producer and a consumer: drop URLs, file paths, or pasted text onto a queue throughout the day, then drain the whole queue in one batch later. One command with three modes — add, process, and show.

**Trigger:** */wiki-list* — also "add to the wiki list", "queue this for the wiki", "process the wiki list", "drain the queue", "what's in the wiki list". With no arguments it defaults to `show`.

**Input / Output:**
- `add` takes a source (URL, file path, or pasted text) plus optional folder, title, tags and priority (1–5, default 3), and writes a small Markdown ticket, `<priority>-<timestamp>-<slug>.md`, to `_inbox/pending/`. Nothing is fetched. A URL already in `pending/`, `_inbox/proposed/`, `wiki/` or `done/` (exact match) is not queued again; it prints where it already is.
- `process` runs the filing script (`wiki-update.py`) on each ticket in filename order, so lower priority numbers go first, with no model in the loop, passing through who captured it. Each ticket moves to `_inbox/done/`, or to `_inbox/failed/` with an `.error` file saying why; the INDEX is regenerated once at the end if anything succeeded. For a synthesized entry (searches, cross-links, the judgment scores) use [`wiki-update`](./wiki-update.md) or `/wiki-cycle --ingest-only` instead.
- `show` lists what is pending, with each ticket's source URL, target folder, who added it, and when.

A readable view of the queue, `_inbox/pending/_pending-list.md`, is refreshed after every add and every processed ticket.

**Works with:** [`wiki-discover`](./wiki-discover.md) and the Drive fetch are the main producers: approved discovery candidates and Drive links are added to this queue. [`wiki-cycle`](./wiki-cycle.md) uses the same queue — it adds approved candidates and, after its own ingest workers finish, moves the ingested tickets to `done/`; it does not run `process`. [`wiki-report`](./wiki-report.md) reports the pending count.

**Note:** `process` supports `--dry-run` and `--limit N`; do a dry run first when the queue holds more than about five items. It exits non-zero when any item failed.
