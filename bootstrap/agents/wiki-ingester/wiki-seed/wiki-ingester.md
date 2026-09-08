---
title: "wiki-ingester — agent"
type: how-to
artifact: agent
name: wiki-ingester
installed_by: install-wiki
date: 2026-09-08
---

# wiki-ingester — agent

A spawnable worker that owns **delegated ingestion**: hand it a list of external sources — URLs,
YouTube videos, PDFs, GitHub repositories, X posts, local files — and it turns each one into a
staged, eval-gated wiki entry through the full `wiki-update` flow, one source at a time, each read
in full. It is the worker `wiki-cycle` delegates to when the queue is drained, and the right choice
for any batch you would rather not sit through. It never files directly into `wiki/`: everything it
writes lands in `_inbox/proposed/`, and it returns a compressed receipt of what it staged.

**Carries the skill(s):** [`wiki-update`](../skills/wiki-update.md),
[`wiki-search`](../skills/wiki-search.md), [`wiki-list`](../skills/wiki-list.md).

## When to hand work to it

- *"Drain the pending queue for agentic-design, staged."*
- *"Ingest these six URLs into agentic-design's research folder, staged."*
- The ingest step of `wiki-cycle`, multi-URL batches, overnight runs — anywhere the ingestion is
  handed off rather than watched. For one source you are looking at right now, run `wiki-update`
  inline instead; the worker's fresh context and full-depth reads pay off on batches.

## How it is spawned

Its model is set in `~/.claude/agents/wiki-ingester-config.json`. While that file's confirm flag is
on, the session that spawns it asks you which model to use for the batch, defaulting to the
configured one, and passes your choice at spawn time. Turn the flag off to stop being asked.

## What you get back

Staged entries in `_inbox/proposed/`, one per source, each with its sidecar and each having passed
the same mechanical checks `wiki-update` applies (no entry floats disconnected from the wiki it
joins; source tiers are conservative). Plus a receipt: per source, filed / skipped / failed, with the
reason for anything not filed. Promotion into `wiki/` stays with you, through `wiki-promote`.

## Limits

- It reads every source completely — whole repositories, full transcripts, every page of a PDF —
  so a large batch takes real time and model spend. That depth is the point; do not use it for a
  quick look.
- It stages; it never promotes, never verifies an entry's truth status, and never edits an existing
  entry in place.
