---
title: "wiki-update — skill"
type: how-to
artifact: skill
name: wiki-update
installed_by: install-wiki
date: 2026-07-31
---

# wiki-update — skill

Ingests an external source into the wiki's `research/` layer. You hand it whatever you have — a link, a YouTube video, a PDF, a local file, or pasted text — and it works out the right fetcher, saves the verbatim original, and writes a curated summary that is cross-linked into what the wiki already knows. Integration is the point: a summary that sits alone is half the value, so every entry links to related entries and notes where the new source agrees with, extends, or contradicts them.

**Trigger:** */wiki-update <source>*, plus natural phrasings like "add this to the wiki", "save this article", "wiki this", or "ingest this video".

**Input / Output:** consumes exactly one URL, file path, or block of pasted text. Produces a verbatim raw capture under `raw/` and a curated entry at `wiki/<folder>/<slug>.md` with full frontmatter (title, date, source_url, raw_path, tier, confidence, review dates, tags), plus regenerated indexes and backlinks added to the related entries it found. With `--staged` the entry lands in `_inbox/proposed/` alongside a `<slug>.proposed_metadata.json` sidecar instead, leaving existing entries untouched until promotion. Hand it two or more URLs and it switches to batch-queue mode, queueing each for later draining rather than ingesting inline.

Before filing, every entry passes an eval gate scoring extraction fidelity, cross-link quality, synthesis value, structural completeness, and metadata accuracy; a below-threshold entry is reported to you rather than filed silently.

**Works with:** [`wrap-up`](./wrap-up.md) is the counterpart for internal session work — run `/wiki-update` with no source and it redirects there. [`wiki-list`](./wiki-list.md) holds the queue that batch mode writes into, and [`wiki-cycle`](./wiki-cycle.md) drains that queue by running this flow across many sources at once. [`wiki-promote`](./wiki-promote.md) moves staged entries into the wiki and wires their backlinks. [`wiki-search`](./wiki-search.md) is what the synthesis step uses to find the existing entries worth linking to.

Full walkthrough: [`../../wiki-update.md`](../../wiki-update.md)
