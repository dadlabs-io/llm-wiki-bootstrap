---
title: "wiki-checker — agent"
type: how-to
artifact: agent
name: wiki-checker
installed_by: install-wiki
date: 2026-09-24
---

# wiki-checker — agent

A second reader for an ingested entry. It reads the staged entry and the raw source it came from, both in full, and reports what the entry gets wrong: claims the source does not make, parts of the source the entry skipped while implying it covered everything, quotes that are not the source's words, and passages vaguer than the source where its specifics matter (a figure turned into "much faster", a named list into "several techniques"; since 2026-10-15, from the Feynman method's rule that an explanation goes vague where understanding stops). It never sees the ingest worker's notes or scores, and it cannot change anything: its tools are read-only plus one report file. The worker that wrote an entry cannot certify it; the checker is the certifier.

**When it runs:** `wiki-cycle` spawns one checker per staged entry whose raw is a transcript of 15 minutes or more (YouTube captions, or a Whisper transcript from `wiki-transcribe.py`), before anything is promoted. Long auto-caption transcripts are where the serious errors came from (a missed ninth technique, swapped model names), and the quote check the gate runs cannot see a skipped section. Since 2026-10-23 it also reads every staged entry whose raw is 60 KB or more (a long PDF, a whole repository), which carries the same risk of a skipped part, and 1 in 10 of the other entries as a spot check, picked by the entry's name so a resumed run picks the same ones: no short source had ever been checked, so nobody knew how often those entries go wrong. A web page that carries a transcript counts only by its size or the spot check, never by its minutes.

**Input / Output:** three paths: the entry, the raw, and the report file. The report is JSON: the four lists (each finding quoting both the entry and the raw), a `pass` or `fix` verdict, the source's length in minutes, and the model. The cycle logs each report as one line in the notebook's `_inbox/reports/checker-log.jsonl` and holds a `fix` entry back from promotion until it is corrected or you rule on it.

**Settings** (`~/.claude/agents/wiki-checker-config.json`): `model_default` (Opus), `min_transcript_minutes` (15), `min_raw_kb` (60; 0 turns it off) and `sample_every` (10; 0 turns the spot check off). The log keeps each check's length and verdict, so over a few cycles it shows how often each length passes: the evidence for raising the threshold, for dropping the spot check when it keeps passing, or for moving the writer or the checker to another model. Each check is one Opus read of the entry and its source.

**When it skips itself:** an entry with no raw, or whose raw is a short transcript, a raw under the size line and not picked by the spot check, is never sent to it.

**Fetched text is data (2026-10-14):** anything a source, raw or email tells the agent to do is not followed; the attempt is named in its report on a `Prompt injection:` line.
