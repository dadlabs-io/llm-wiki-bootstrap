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
wiki entry through the full `wiki-update` flow, one source at a time, each read in full. It is the
worker `wiki-cycle` delegates to when the queue is drained, and the right choice for any batch you
would rather not sit through. It stages by default: entries land in `_inbox/proposed/` (beside
`wiki/` at the notebook root) and nothing in `wiki/` changes. It files directly only when the caller
explicitly asks. It returns a compressed receipt of what it did.

**Carries the skill(s):** [`wiki-update`](../skills/wiki-update.md),
[`wiki-search`](../skills/wiki-search.md), [`wiki-list`](../skills/wiki-list.md).

## When to hand work to it

- *"Drain the pending queue, staged."*
- *"Ingest these six URLs into the research folder, staged."*
- The ingest step of `wiki-cycle`, multi-URL batches, overnight runs — anywhere the ingestion is
  handed off rather than watched. For one source you are looking at right now, run `wiki-update`
  inline instead; the worker's fresh context and full-depth reads pay off on batches.

## How it is spawned

Its model is set in `~/.claude/agents/wiki-ingester-config.json` (if that file is missing, the
agent's own default, Sonnet, is used). While that file's confirm flag is on, an interactive session
that spawns it asks you which model to use for the batch, defaulting to the configured one, and
passes your choice at spawn time. A session that cannot ask (an autonomous or unattended run) uses
the configured default without asking and names the model in the batch receipt, so you can see
afterwards what ran. Turn the flag off to stop being asked in interactive sessions too.

## What you get back

- One entry per source, with its sidecar. Each passed `wiki-update`'s mechanical gate: the filing
  script refuses an entry without a TL;DR, without a Related section holding at least two wiki
  links, with its layout out of order, or with frontmatter that would not parse, and it reports any
  link it could not resolve. Each also scored 3 or more (of 5) on the worker's own two judgment
  scores, extraction fidelity and synthesis value.
- A source that still falls short of those scores after one fix is not staged: its draft and a
  review note quoting why stay in `_inbox/temp/`, so you can finish it, file it anyway or drop it.
- Before reporting done, it runs the promote script's check on every staged entry, so a broken
  sidecar is caught by the script rather than reported as conforming.
- A receipt: per source, staged / skipped / failed with the reason for anything not staged, and a
  line reconciling the counts (assigned = staged + failed + skipped). Queue items it processed move
  from `_inbox/pending/` to `_inbox/done/`, which is what lets an interrupted batch resume.

Promotion into `wiki/` stays with you, through `wiki-promote`.

## When it skips or fails an item

- A source already in `wiki/` or `_inbox/proposed/` is reported as a duplicate, with the existing
  entry named, and not ingested unless the caller said force.
- It has no browser. A login-gated page must be captured by your own session first and handed over
  as a saved raw; without one the item fails as "needs browser capture".
- It always uses the full search (keyword, meaning and rerank on the GPU), scoped to the target
  notebook. It checks for CUDA once and stops the batch if CUDA is missing. A search that still fails
  after one retry fails the item ("full search unavailable") rather than filing it without
  cross-links; run fewer workers next time.
- A fetch that fails on the documented fallback fetcher too, or an item that runs past about 15
  minutes, fails with its reason. Nothing is dropped silently.

## Limits

- It reads every source completely — whole repositories, full transcripts, every page of a PDF —
  so a large batch takes real time and model spend. That depth is the point; do not use it for a
  quick look.
- It never promotes, never verifies an entry's truth status, never commits (the caller does), and in
  staged mode never touches an existing entry. It works on one source and one fetch at a time and
  cannot spawn workers of its own.
