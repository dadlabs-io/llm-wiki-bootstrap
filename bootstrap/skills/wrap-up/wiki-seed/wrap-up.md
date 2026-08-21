---
title: "wrap-up — skill"
type: how-to
artifact: skill
name: wrap-up
installed_by: install-wiki
date: 2026-07-31
---

# wrap-up — skill

The single session-close command. It turns "we just spent two hours figuring out X" into a record you (or a teammate) can read in sixty seconds: a running journal of what happened, refreshed dashboards that say where to resume, and distilled entries for the durable decisions, components, patterns, and bugs the session produced. It writes about *your own* work — external articles and videos belong to [`wiki-update`](./wiki-update.md). It deliberately distills rather than dumping: the transcript is raw material, the entry is the synthesis.

**Trigger:** */wrap-up*, plus natural phrasings like "wrap up this session", "document what we did", "save progress", or "save state".

**Input / Output:** consumes the current conversation, changed files, and recent commits. Produces three things every run: a per-session journal entry at `wiki/sessions/<persona>/<YYYY-MM>/`, upserted so repeat wrap-ups in one session append to the same file; refreshed working-memory dashboards at `sessions/<persona>/handoff.md`, `sessions/<persona>/task.md`, and `sessions/active-context.md`; and durable entries (component, decision, architecture, pattern, troubleshooting) staged to `_inbox/proposed/` with a `<slug>.proposed_metadata.json` sidecar naming their target folder under `wiki/project/`. Optionally it also writes a session snapshot to `raw/sessions/` so every derived entry stays traceable to its source.

Two per-notebook settings control how much it asks: `confirm_before_create` gates the proposal table of candidate entries, and `confirm_before_promote` gates whether staged entries get promoted inline at the end of the run. Both default to asking.

**Works with:** [`wiki-promote`](./wiki-promote.md) finishes the job — wrap-up stages entries and offers to promote them immediately, and anything you decline stays in `_inbox/proposed/` for a later `/wiki-promote --review`. [`wiki-update`](./wiki-update.md) is the counterpart for external sources into `research/`; wrap-up redirects there if a session turns out to be pure ingest. [`upd-docs`](./upd-docs.md) is retired and its dashboard refresh now happens here.

**Note:** if you only want the fast dashboard refresh without filing anything, run `/wrap-up` and answer `none` at the proposal table — the journal and dashboards still update.

Full walkthrough: [`../../wrap-up.md`](../../wrap-up.md)
