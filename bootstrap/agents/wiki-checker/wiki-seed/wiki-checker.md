---
title: "wiki-checker — agent"
type: how-to
artifact: agent
name: wiki-checker
installed_by: install-wiki
date: 2026-09-24
---

# wiki-checker — agent

A second reader for an ingested entry. It reads the staged entry and the raw source it came from, both in full, and reports what the entry gets wrong: claims the source does not make, parts of the source the entry skipped while implying it covered everything, and quotes that are not the source's words. It never sees the ingest worker's notes or scores, and it cannot change anything: its tools are read-only plus one report file. The worker that wrote an entry cannot certify it; the checker is the certifier.

**When it runs:** `wiki-cycle` spawns one checker per staged entry whose raw is a YouTube transcript of 15 minutes or more, before anything is promoted. Long auto-caption transcripts are where the serious errors came from (a missed ninth technique, swapped model names), and the quote check the gate runs cannot see a skipped section.

**Input / Output:** three paths: the entry, the raw, and the report file. The report is JSON: the three lists (each finding quoting both the entry and the raw), a `pass` or `fix` verdict, the source's length in minutes, and the model. The cycle logs each report as one line in the notebook's `_inbox/reports/checker-log.jsonl` and holds a `fix` entry back from promotion until it is corrected or you rule on it.

**Settings** (`~/.claude/agents/wiki-checker-config.json`): `model_default` (Opus) and `min_transcript_minutes` (15). The log keeps each check's length and verdict, so over a few cycles it shows how often each length passes: the evidence for raising the threshold, or for moving the writer or the checker to another model.

**When it skips itself:** an entry whose raw is not a transcript, or is shorter than the threshold, is never sent to it.
