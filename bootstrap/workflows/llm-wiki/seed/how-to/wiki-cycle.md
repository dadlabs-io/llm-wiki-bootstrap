# /wiki-cycle — full ingest orchestrator

The main pipeline. Discover new sources, ingest approved items, lint, fix, generate a morning report, optionally promote. Resumable via scratchpad if the session dies mid-run.

## Most common usage

```
/wiki-cycle
```

Default `--quick` mode: Drive-fetch → Discover → Confirm → Ingest → Mechanical lint → Reciprocate backlinks → INDEX regen → MAP regen → Morning report → Promote checkpoint. ~5-10 min for ≤20 items.

## Mode flags

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

## The two human checkpoints

Default `/wiki-cycle` pauses at two points:

1. **After discovery**: shows what was queued / skipped / deferred. You confirm "go" or edit the list.
2. **Before promote**: shows what's staged in `_inbox/proposed/`. You decide promote-all / hold / review / partial / skip.

To skip both for trusted full-auto runs:
```
/wiki-cycle --full --auto-promote --no-confirm-discovery <topic>
```

## Drive-fetch step

If you enabled Drive ingest at `/new-wiki` time, the cycle starts by pulling URLs from `<parent-folder>/<project-slug>/` in your Drive. Files get deduped against pending/proposed/wiki/done and queued into `_inbox/pending/`. Processed files move to `_completed/<cycle-id>/`.

## Don't

- Don't run `/wiki-cycle` and walk away on the first install — read the morning report before promoting
- Don't run `--full` every cycle — semantic lint is expensive (~20-30 min); weekly is fine
- Don't auto-promote until you've seen several clean cycles and trust the staging quality

## Resuming an interrupted cycle

```
/wiki-cycle --resume <cycle-id>
```

Cycle IDs are `<YYYY-MM-DD>-<NN>` (e.g., `2026-05-13-02`). The scratchpad at `_inbox/reports/<date>/<cycle-id>/scratchpad.md` records phase-by-phase progress.

## Cycle report folder

Every run writes to:
```
llm-wiki/wiki/_inbox/reports/<YYYY-MM-DD>/<YYYY-MM-DD>-<NN>/
```

This folder holds: per-step JSON+MD sidecars, scratchpad, aggregated morning report. Keep these — they're your audit trail.
