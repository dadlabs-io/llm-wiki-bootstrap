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

## Full walkthrough

The main pipeline. Discover new sources, ingest approved items, lint, fix, generate a morning report, optionally promote. Resumable via scratchpad if the session dies mid-run.

### Most common usage

```
/wiki-cycle
```

Default `--quick` mode: Drive-fetch → Discover → Confirm → Ingest (each entry must pass the script's mechanical gate before it is written — see [`wiki-update`](./wiki-update.md)) → **Dequeue** (move ingested items `pending/`→`done/`) → Mechanical lint → **Normalize links** (`wiki-fix-links.py`) → Reciprocate backlinks → INDEX regen → MAP regen → Morning report → Promote checkpoint. ~5-10 min for ≤20 items.

Ingest runs via the **`wiki-ingester` subagent** (installed to `~/.claude/agents/` with this
framework; falls back to a general-purpose worker if absent). Before the workers launch you may be
asked which model to use for the batch — the default and the ask-every-time flag live in
`~/.claude/agents/wiki-ingester-config.json` (`model_default`, `confirm_model_each_run`).

### Mode flags

| Flag | Effect |
|---|---|
| `--full` | Adds semantic lint (4 parallel AI agents) + claims extraction + refresh scan. ~30-40 min. Run weekly. |
| `--ingest-only` | Skip discover; just drain the `_inbox/pending/` queue |
| `--discover-only` | Discovery only — produces checklist, stops before ingest |
| `--lint-only` | Mechanical lint only; print report; done |
| `--lint-only --semantic` | + 4-agent semantic pass |
| `--claims-only` | Contradiction extraction only |
| `--refresh-only` | Stale-entry scan only |
| `--report-only` | Regen morning report from last run's JSONs |
| `--auto-promote` | Skip the promote checkpoint, auto-promote everything staged |
| `--no-promote` | Skip the promote checkpoint, leave staging intact |

### The two human checkpoints

Default `/wiki-cycle` pauses at two points:

1. **After discovery**: shows what was queued / skipped / deferred. You confirm "go" or edit the list.
2. **Before promote**: shows what's staged in `_inbox/proposed/`. You decide promote-all / hold / review / partial / skip.

To skip both for trusted full-auto runs:
```
/wiki-cycle --full --auto-promote --no-confirm-discovery <topic>
```

### Drive-fetch step

If you enabled Drive ingest at `/new-wiki` time, the cycle starts by pulling URLs from `<parent-folder>/<project-slug>/` in your Drive. URLs are canonicalized first (tracking params such as UTM, HubSpot `_hsenc`/`_hsmi` and YouTube `si` stripped, every YouTube form collapsed to `watch?v=<id>`), then deduped against pending/proposed/wiki/done by that canonical form and queued into `_inbox/pending/`. A URL whose article is already in the wiki is reported as *known*, not re-queued, and its Drive file is archived with the rest. Processed files move to `_completed/<cycle-id>/`.

### Don't

- Don't run `/wiki-cycle` and walk away on the first install — read the morning report before promoting
- Don't run `--full` every cycle — semantic lint is expensive (~20-30 min); weekly is fine
- Don't auto-promote until you've seen several clean cycles and trust the staging quality

### Resuming an interrupted cycle

```
/wiki-cycle --resume <cycle-id>
```

Cycle IDs are `<YYYY-MM-DD>-<NN>` (e.g., `2026-05-13-02`). The scratchpad at `_inbox/reports/<date>/<cycle-id>/scratchpad.md` records phase-by-phase progress.

### Cycle report folder

Every run writes to:
```
llm-wiki/wiki/_inbox/reports/<YYYY-MM-DD>/<YYYY-MM-DD>-<NN>/
```

This folder holds: per-step JSON+MD sidecars, scratchpad, aggregated morning report. Keep these — they're your audit trail.

