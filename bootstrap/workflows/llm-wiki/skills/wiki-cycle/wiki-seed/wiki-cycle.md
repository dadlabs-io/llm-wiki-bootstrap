---
title: "wiki-cycle — skill"
type: how-to
artifact: skill
name: wiki-cycle
installed_by: install-wiki
date: 2026-07-31
---

# wiki-cycle — skill

Runs the whole research pipeline end to end: discover new sources, confirm them with you, ingest them, lint the wiki, fix what broke, regenerate the indexes and map, and hand you a morning report. It is the universal interface — the other `wiki-*` maintenance skills exist as steps you can invoke directly, but normally you reach them through this command with the right flag. Every run keeps a scratchpad updated after each phase, so a cycle interrupted halfway can be resumed instead of restarted.

**Trigger:** */wiki-cycle*, plus natural phrasings like "run the cycle", "update the wiki", or "full wiki update".

**Input / Output:** consumes the pending queue, any URLs dropped into the configured Google Drive folder, and the wiki's current state. Produces new entries staged in `_inbox/proposed/` (pass `--direct` to file straight into `wiki/`), plus a full set of artifacts under `_inbox/reports/<date>/<cycle_id>/` — per-step JSON and markdown sidecars, the scratchpad, and an aggregated cycle report. Each run gets a `cycle_id` of the form `<YYYY-MM-DD>-<NN>`, which is also what you pass to `--resume`.

The default `--quick` mode takes roughly five to ten minutes for twenty items. `--full` adds semantic lint, claims extraction, a best-practices synthesis pass that proposes doctrine updates from the new research, and a staleness refresh; it runs closer to forty minutes and is a weekly rather than daily thing. Narrower flags — `--lint-only`, `--discover-only`, `--ingest-only`, `--report-only`, `--refresh-only`, `--claims-only` — run a single slice.

There are two human checkpoints by design: you approve the discovered URLs before anything is ingested, and you review the staged entries the next morning.

**Works with:** it orchestrates [`wiki-discover`](./wiki-discover.md), [`wiki-update`](./wiki-update.md), [`wiki-lint`](./wiki-lint.md), [`wiki-claims`](./wiki-claims.md), [`wiki-refresh`](./wiki-refresh.md), and [`wiki-report`](./wiki-report.md) as steps, each writing back through a shared return-format contract. Morning review is [`wiki-promote`](./wiki-promote.md); [`wiki-list`](./wiki-list.md) owns the pending queue the cycle drains.

Full walkthrough: [`../../wiki-cycle.md`](../../wiki-cycle.md)
