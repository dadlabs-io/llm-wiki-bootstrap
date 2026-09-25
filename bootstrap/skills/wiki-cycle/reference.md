# /wiki-cycle — reference

Read on demand: the scratchpad template when a run creates one, the other sections when a step points here. `SKILL.md` holds the steps; this file holds the detail they need only sometimes.

## The scratchpad

Created at Step 0 as `<run-folder>/scratchpad.md` and updated after every phase; `--resume <cycle_id>` continues from the last phase marked `done`. One section per phase the run's mode includes (the mode table in `SKILL.md`); a phase outside the mode is listed once as `skipped (mode)`.

```markdown
# Cycle Run — <date>

**Status**: in_progress | completed | interrupted
**Started**: <timestamp>
**Topic**: <notebook>
**Cycle**: <cycle_id> (<mode>)

## Run config
- Mode: <mode and flags>
- Triggered by: user / cron / resume
- This session reads as: <reader name from wiki-triage.py buckets>

## Phase log

### Phase 1.0: Drive-fetch
- **Status**: pending | running | done | skipped (<why>)
- **Unique URLs**: N · **Queued**: N (failed N) · **Moved to `_completed/<cycle_id>/`**: N (failed N)

### Phase 1: Discover
- **Status**: … · **Candidates**: N after dedup · **Checklist**: _inbox/discovered/<date>-discovery.md

### Phase 1.5: Human review #1
- **Status**: … · **Approved** N · **Rejected** N · **Deferred** N

### Phase 1.7: Triage
- **Status**: … · **Routed**: N (per folder: …) · **Raws captured for other readers**: N · **Readers told**: …

### Phase 1.8: Browser capture
- **Status**: … · **Captured**: N · **Left for a browser session**: N

### Phase 2: Ingest
- **Status**: … · **Items**: N · **Workers**: N (model) · **YouTube**: N, on worker K
- **Completed**: <slug> → <folder> (scores) … · **Failed**: <item> — <reason>

### Phase 2.5: Dequeue + staging check
### Phase 2.6: Checker
- **Status**: … · **Checked**: N (pass N, fix N) · **Corrected**: N · **Held for the user**: N

### Phase 3: Mechanical lint
### Phase 3.5: Integration scripts
### Phase 4: Semantic lint (scope N: added or revised since <cut-off> + N staged)
### Phase 5: Fix lint issues
### Phase 5.5: Promote
### Phase 6: Claims (scope N)
### Phase 6.5: Best-practices synthesis
### Phase 7: Refresh scan
### Phase 8: Report
### Phase 9: Commit

## Decisions log
- <timestamp> — <decision and why>

## Unresolved for next run
- <follow-ups>
```

## Cycle id and run folder

`cycle_id` is `<YYYY-MM-DD>-<NN>`: the local date (`today_label()`), and `NN` the next unused number in `_inbox/reports/<date>/` (`01` first). Everything a run writes lives in `_inbox/reports/<date>/<cycle_id>/`: the scratchpad, each step's `<step>.json` + `<step>.md` (the [cycle step return format](./best-practices/framework/cycle-step-return-format.md); the JSON is authoritative), the scope files, the checker reports under `checker/`, and `<cycle_id>-run-cycle-report.md` + `.json`.

## Step 1.0 — Drive-fetch, in detail

The folder names come from `.claude/wiki-config.json`: `<parent>` is `drive.parent_folder` (default `__FOR CLAUDE`), `<subfolder>` is `drive.subfolder` (default the notebook name). OAuth reads the client secrets from `~/.config/wiki-cycle/client_secrets.json` unless `--client-secrets` or `WIKI_DRIVE_CLIENT_SECRETS` says otherwise.

- Files whose URLs queue are **moved** to `<parent>/<subfolder>/_completed/<cycle_id>/` (created if missing; the scan folder itself must exist). Files whose queueing failed stay where they are, for a retry next cycle. A URL already in the wiki is reported, not queued, and its file is archived with the rest.
- The first run with `--move-handled` asks for OAuth again, once, to widen the scope from read-only to full Drive (it re-parents files).
- `--out <run-folder>/drive-fetch.md` writes the report and, beside it, `drive-fetch.json` in the step contract's shape (since 2026-09-24; before that the orchestrator wrote the JSON by hand). The scratchpad's counts come from its `summary`.

## Which notebook a cycle runs against

The one `<cwd>/.claude/wiki-config.json` names (`notebook` + `registry`), resolved by `_wiki_config.py`; a notebook's root is `notebooks[<name>].root` in `linked-notebooks.json`, relative to that file, and `_inbox/`, `raw/`, `how-to/` sit beside its `wiki/`. `/wiki-cycle <notebook>` targets another registered notebook: every script gets `--topic <notebook>`, never `--vault` (a legacy in-project wiki without a registry is the one exception). `--all-topics` iterates `_wiki_config.list_topics()` and runs the mode once per notebook.

## Morning review, after an unattended run

The user asks "what did we load?" or "morning report": show the run's report (`/wiki-report` reads the step JSONs), then `/wiki-promote --review` for the staged entries (approve → `wiki/`, reject → `_inbox/rejected/`), including any the checker held with its report beside it. This is human review #2: the cycle did the work, the morning is the approval pass.

## Parallel work

| Task | At once | Split by |
|---|---|---|
| Ingest | up to 4 workers | items; every YouTube item of a batch with more than one on the same worker |
| Checker | up to 4 | one staged entry each (read-only; no GPU) |
| Semantic lint | 1 agent per ~100 entries in scope, up to 4 | a partition of the scope balanced by file count, chosen per run |
| Lint fixes | up to 3 | fix category |

Ingest workers share three GPU slots for their searches (`wiki-qmd-query.py`); waiting is expected. Spawn every helper **unnamed** (no `name`, no `team_name`): with agent teams enabled a named spawn becomes a teammate whose report never comes back (found by agent-builder, 2026-09-21).

## History behind the rules

- **Staged entries before Steps 6 and 6.5** (2026-07-11, cycle 2026-07-10-01): claims and synthesis read `wiki/`, but ingest stages to `_inbox/proposed/`. Synthesis agents cross-linked staged entries by paths that did not exist yet: 7 broken links, found several steps later. Hence Step 5.5 promotes before them in a `--full` run.
- **Link normaliser before the mechanical lint** when entries were promoted in-cycle: ingest workers write bare-slug links by contract, and until `wiki-fix-links.py` ran end to end every cycle had about 50 broken links fixed by hand.
- **Dequeue after ingest** (cycles 2026-07-01 and 07-02, 61 stale items each): the staged batch path never moved queue tickets, so every later cycle reconciled them by hand. `wiki-dequeue.py` matches by source URL and is idempotent.
- **Staging check after ingest** (cycle 2026-09-14-01): a worker's receipt said every sidecar conformed while one had invalid JSON; `wiki-promote.py --check` is the check, not the receipt.
- **The cycle's 2026-09-23 live run** (`2026-09-23-01`) found the gaps this version closes: no triage step, a Drive and a lint step whose JSON the orchestrator wrote by hand, a semantic lint scoped to "every entry" (1,284 files, ~3.2M tokens), workers told to write `update.json`, no place for browser capture, parallel YouTube fetches hitting 429s, and `--ingest-only` read two ways by two models (the 2026-09-24 baseline).
