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

**Input / Output:** `add` takes a source (URL, file path, or pasted text) plus optional folder, title, and tags, and writes a `.queue` file to `_inbox/pending/` — nothing is fetched at this point. `process` drains that queue, ingesting each item, then moves each queue file to `_inbox/done/` or to `_inbox/failed/` with an `.error` sidecar explaining the failure, and regenerates the INDEX once at the end. `show` lists what is pending, with each item's source URL, target folder, who added it, and when.

**Works with:** [`wiki-discover`](./wiki-discover.md) is the main producer — approved discovery candidates are added straight to this queue. `process` hands each item to [`wiki-update`](./wiki-update.md) for the actual ingest, passing through who originally captured it. [`wiki-cycle`](./wiki-cycle.md) runs it as a cycle step, and [`wiki-report`](./wiki-report.md) reports the pending count.

**Note:** `process` supports `--dry-run` and `--limit N`; do a dry run first when the queue holds more than about five items.
