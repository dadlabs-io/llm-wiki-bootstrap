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

The default `--quick` mode takes roughly five to ten minutes for twenty items. `--full` adds semantic lint, promotion of this cycle's staged entries, claims extraction, a best-practices synthesis pass that proposes doctrine updates from the new research, and a scan for overdue entries; it runs forty to fifty minutes and is a weekly rather than daily thing. Narrower flags — `--lint-only`, `--discover-only`, `--ingest-only`, `--report-only`, `--refresh-only`, `--claims-only` — run a single slice.

There are two human checkpoints by design: you approve the discovered URLs before anything is ingested, and you review the staged entries the next morning.

**Works with:** it orchestrates [`wiki-discover`](./wiki-discover.md), [`wiki-update`](./wiki-update.md), [`wiki-lint`](./wiki-lint.md), [`wiki-claims`](./wiki-claims.md), [`wiki-refresh`](./wiki-refresh.md), and [`wiki-report`](./wiki-report.md) as steps, each writing back through a shared return-format contract. Morning review is [`wiki-promote`](./wiki-promote.md). The cycle adds approved candidates to the pending queue that [`wiki-list`](./wiki-list.md) also uses, and moves each ingested ticket to `done/`.

## Full walkthrough

The main pipeline. Discover new sources, ingest approved items, lint, fix, generate a morning report, optionally promote. Resumable via scratchpad if the session dies mid-run.

### Most common usage

```
/wiki-cycle
```

Default `--quick` mode: Drive-fetch → Discover → Confirm → Ingest → **Dequeue** (move ingested tickets `pending/`→`done/`) and a check of what the workers staged → Mechanical lint → Reciprocate backlinks → INDEX regen → MAP regen → Morning report → one commit, scoped to the notebook's folder. ~5-10 min for ≤20 items. Staged entries then wait for your morning review; a quick run promotes nothing.

Ingest runs via the **`wiki-ingester` subagent** (installed to `~/.claude/agents/` with this
framework; falls back to a general-purpose worker if absent), up to four at a time. Before the workers
launch you may be asked which model to use for the batch — the default and the ask-every-time flag live
in `~/.claude/agents/wiki-ingester-config.json` (`model_default`, `confirm_model_each_run`); a session
that cannot ask uses the default and names it.

- Every worker searches the wiki with the full qmd search. At most three searches share the GPU at once; the rest wait for a slot, and none falls back to keyword search. The cycle report says how long searches waited — if waiting slowed the batch, run three or two workers next time. `--full` also checks that the search's candidate limit never cut what the reranker sees; the report says so, or says to raise the limit, or says the check could not measure anything (never a pass).
- Each entry passes the filing script's gate before it is written (see [`wiki-update`](./wiki-update.md)). The gate refuses frontmatter that would not parse, and broken links are reported for staged entries as well as filed ones.
- Workers report on their own work, so the cycle checks what they staged: an entry whose sidecar is missing, is not valid JSON, or names no target folder is listed and fixed before the commit.

### Mode flags

| Flag | Effect |
|---|---|
| `--full` | Adds semantic lint (4 parallel agents), promotion of this cycle's staged entries (the claims and synthesis steps need them in `wiki/`), claims extraction, a best-practices synthesis whose proposed doctrine changes you approve before any is applied, and a scan for overdue entries. ~40-50 min. Run weekly. |
| `--ingest-only` | Skip discover; just drain the `_inbox/pending/` queue |
| `--prompt-for-urls` | Pause for you to paste URLs, then ingest them (no discovery) |
| `--discover-only` | Discovery only — produces checklist, stops before ingest |
| `--lint-only` | Mechanical lint only; print report; done |
| `--lint-only --semantic` | + 4-agent semantic pass |
| `--claims-only` | Contradiction extraction only |
| `--refresh-only` | Stale-entry scan only |
| `--report-only` | Regen morning report from last run's JSONs |

Modifiers, combinable with any mode: `<topic>` (run against another registered notebook), `--direct` (file into `wiki/` instead of staging), `--no-confirm-discovery` (skip the discovery pause, for headless runs), `--since <hours>` (discovery window, default 24), `--resume <cycle_id>`, `--all-topics` (every registered notebook in turn).

### The two human checkpoints

1. **After discovery** (a pause in the run): shows what was queued / skipped / deferred. You confirm "go" or edit the list.
2. **Morning review** (after the run): `/wiki-report` summarises it and `/wiki-promote --review` walks each staged entry for approve or reject.

For a headless run with no discovery pause:
```
/wiki-cycle --no-confirm-discovery <topic>
```
Entries still stage for the morning review. A `--full` run is the exception: it promotes this cycle's staged entries itself before its claims and synthesis steps.

### Drive-fetch step

If you enabled Drive ingest at `/new-wiki` time, the cycle starts by pulling URLs from `<parent-folder>/<project-slug>/` in your Drive. URLs are canonicalized first (tracking params such as UTM, HubSpot `_hsenc`/`_hsmi` and YouTube `si` stripped, every YouTube form collapsed to `watch?v=<id>`), then checked by that canonical form against the source of every entry in `wiki/` and `_inbox/proposed/`. A URL already there is reported as *known*, not queued, and its Drive file is archived with the rest. The others are queued into `_inbox/pending/`, which skips a URL already in pending, proposed, wiki or done (exact match). Handled files move to `_completed/<cycle-id>/` inside the Drive folder; a file whose URL failed to queue stays put for the next cycle.

### Don't

- Don't run `/wiki-cycle` and walk away on the first install — read the morning report before promoting
- Don't run `--full` every cycle — semantic lint is expensive (~20-30 min); weekly is fine
- Don't pass `--direct` on an unattended run — staging exists so a person reviews overnight work

### When steps skip themselves

- **Drive-fetch** runs only if Drive ingest was enabled for the project.
- **Link normalization** (`wiki-fix-links.py`) runs only when entries were promoted into `wiki/` during the cycle (`--direct`, or `--full`); otherwise it runs at `/wiki-promote`.
- **Semantic lint** is skipped in quick mode, and in `--full` if one ran in the last 24 hours.
- **Claims** does a full extraction the first time, then compares only the new entries.
- **Synthesis** in a run nobody is watching writes its proposal to the report folder and leaves the best-practices pages unchanged.
- **Refresh** runs only in `--full` and `--refresh-only`, and then covers overdue entries only.

### Resuming an interrupted cycle

```
/wiki-cycle --resume <cycle-id>
```

Cycle IDs are `<YYYY-MM-DD>-<NN>` (e.g., `2026-05-13-02`). The scratchpad at `_inbox/reports/<date>/<cycle-id>/scratchpad.md` records phase-by-phase progress.

### Cycle report folder

Every run writes to:
```
_inbox/reports/<YYYY-MM-DD>/<YYYY-MM-DD>-<NN>/
```

The `_inbox/` here is the one beside `wiki/` in the notebook root. This folder holds: per-step JSON+MD sidecars, scratchpad, aggregated morning report. Keep these — they're your audit trail.

