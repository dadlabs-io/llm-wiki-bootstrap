---
name: wiki-cycle
description: Run the full research cycle — discover, ingest, lint, fix, report. Maintains a scratchpad so the run can be resumed if interrupted. This is the "update the wiki" command. Use when the user says "update the database", "run the cycle", "wiki-cycle", "update the wiki", "full wiki update".
---

# /wiki-cycle

Run the full research cycle end-to-end. Discovers new sources, ingests approved items, lints the wiki, fixes issues, and generates a morning report. Maintains a persistent scratchpad so the run survives session interruptions.

## Usage

```
# Mode flags (pick one; --quick is default)
/wiki-cycle                       # default: quick cycle (discover → confirm → ingest → lint → backlinks → indexes → map → report)
/wiki-cycle --full                # + semantic lint + claims + refresh (weekly / big batches)
/wiki-cycle --lint-only           # mechanical lint only; print report; done
/wiki-cycle --lint-only --semantic # + 4-agent semantic pass
/wiki-cycle --discover-only       # discovery only — produces checklist, stops before ingest
/wiki-cycle --ingest-only         # skip discovery; drain the pending queue; cleanup
/wiki-cycle --prompt-for-urls     # pause, user pastes URLs, ingest them (no discovery)
/wiki-cycle --report-only         # regen morning report from last run's JSONs; no work
/wiki-cycle --refresh-only        # stale-entry scan only
/wiki-cycle --claims-only         # contradiction extraction only

# Modifiers (combine with any mode)
/wiki-cycle <topic>               # specific topic (default: (your configured topic))
/wiki-cycle --direct              # file to wiki/ not _inbox/proposed/
/wiki-cycle --resume <cycle_id>   # resume an interrupted cycle from its scratchpad
/wiki-cycle --no-confirm-discovery # skip Step 1.5 human checkpoint (cron/headless)
/wiki-cycle --since <hours>       # discovery window (default: 24h)
```

**This is the universal interface.** The other `wiki-*` skills (discover, lint, claims, refresh, report, list, promote) are INTERNAL — they exist as scripts + SKILL.md for programmatic invocation, but users normally go through `/wiki-cycle` with the right flag. Public-facing user commands are just four: `/wiki-cycle`, `/wiki-update`, `/wiki-search`, `/wiki-init`.

**Default behavior (`--quick`)**: Discover → Confirm → Ingest → Mechanical lint → Reciprocate backlinks → Per-folder INDEX regen → _MAP.md regen → Morning report. ~5-10 min for ≤20 items. Entries go to `_inbox/proposed/` (staged) by default. User reviews in the morning via `/wiki-promote`. Pass `--direct` to bypass staging.

**`--full` mode**: adds Semantic lint (4 parallel AI agents by folder) + Claims scan + Refresh pass. ~30-40 min. Run weekly or when an ingest batch is ≥25 items, cross-cuts many existing entries, or semantic lint hasn't run in >7 days.

## Cycle ID and report folder

Every cycle run is assigned a `cycle_id` in the form `<YYYY-MM-DD>-<NN>` where `NN` is `01` for the first run that day, `02` for the second, and so on. On start, the orchestrator scans `_inbox/reports/<YYYY-MM-DD>/` and picks the next unused `NN`.

All artifacts for one cycle run live in:

```
_inbox/reports/<YYYY-MM-DD>/<YYYY-MM-DD>-<NN>/
```

This folder holds:
- Per-step JSON + MD sidecars (`discover.json`, `discover.md`, `update.json`, etc. — see [cycle-step-return-format](./best-practices/framework/cycle-step-return-format.md))
- The aggregated `<cycle_id>-run-cycle-report.md` + `<cycle_id>-run-cycle-report.json`

## The scratchpad

Every cycle run creates a scratchpad at:
```
docker/shared/openclaw/vault/wikis/<topic>/_inbox/reports/<YYYY-MM-DD>/<YYYY-MM-DD>-<NN>/scratchpad.md
```

The scratchpad is updated after EVERY phase. If the session dies mid-cycle, the next session can `--resume <cycle_id>` from where it left off. The scratchpad lives inside the cycle's report folder so it's archived with the rest of the cycle's artifacts.

### Scratchpad format

```markdown
# Cycle Run — <date>

**Status**: in_progress | completed | interrupted
**Started**: <timestamp>
**Topic**: <topic>

## Run config
- Skip discover: yes/no
- Skip ingest: yes/no
- Triggered by: user / cron / resume

## Phase log

### Phase 1.0: Drive-fetch
- **Status**: pending | running | done | skipped
- **Folder scanned**: `__FOR CLAUDE/<topic>/`
- **Files found**: N
- **Unique URLs**: N (after dedup)
- **Queued**: N (failed: N)
- **Moved to `_completed/<cycle_id>/`**: N (failed: N — left in scan folder)
- **Notes**: <re-auth prompt fired? new files left for retry?>

### Phase 1: Discover
- **Status**: pending | running | done | skipped
- **Queries run**: N
- **Candidates found**: N (after dedup: N)
- **Checklist**: _inbox/discovered/<date>-discovery.md
- **Notes**: <anything notable>

### Phase 2: Human review #1 (URL approval)
- **Status**: pending | done | skipped (auto-approve for tier 1-3)
- **Approved**: N
- **Rejected**: N
- **Deferred**: N

### Phase 3: Ingest
- **Status**: pending | running | done | skipped
- **Items to ingest**: N
- **Agents dispatched**: N
- **Completed**: 
  - <slug> → wiki/<folder>/ (eval score: N.N)
  - <slug> → wiki/<folder>/ (eval score: N.N)
- **Failed**:
  - <slug> — reason: <error>
- **Notes**: <any issues>

### Phase 4: Mechanical lint
- **Status**: pending | done
- **Broken links**: N
- **Orphans**: N
- **Missing metadata**: N

### Phase 5: Semantic lint
- **Status**: pending | running | done | skipped
- **Agents dispatched**: N (by folder)
- **Issues found**: contradictions N, missing cross-refs N, thin N, gaps N, tier N, other N
- **Reports**: _inbox/semantic-lint-*-<date>.md

### Phase 6: Fix lint issues
- **Status**: pending | running | done
- **Fix agents dispatched**: N
- **Files modified**: N
- **Fixes applied**: <summary>

### Phase 7: Claims extraction
- **Status**: pending | running | done | skipped
- **Claims extracted**: N
- **Contradictions found**: N (high N, medium N, low N)
- **Report**: _inbox/claims-report-<date>.md

### Phase 8: Refresh scan
- **Status**: pending | done | skipped
- **Overdue entries**: N
- **Low confidence**: N
- **Report**: _inbox/reports/refresh-report-<date>.md

### Phase 9: Morning report
- **Status**: pending | done
- **Report**: _inbox/reports/morning-report-<date>.md

### Phase 10: Commit
- **Status**: pending | done
- **Commits**: N
- **Hashes**: <list>

## Decisions log
- <timestamp> — <decision made during the run>
- <timestamp> — <e.g., "rejected entry X — tier 4, no corroboration">
- <timestamp> — <e.g., "skipped semantic lint — ran 2 hours ago">

## Unresolved for next run
- <anything that needs follow-up>
```

## What You Must Do When Invoked

### Step 0 — Assign cycle_id + create run folder

1. Compute today's date in `YYYY-MM-DD` format.
2. Scan `docker/shared/openclaw/vault/wikis/<topic>/_inbox/reports/<date>/` for existing `<date>-NN` subfolders. Pick the next unused `NN` (starts at `01`).
3. Create the run folder:

```bash
mkdir -p docker/shared/openclaw/vault/wikis/<topic>/_inbox/reports/<date>/<date>-<NN>/
```

4. Create the scratchpad at `<run-folder>/scratchpad.md`. Set status to `in_progress`, record the `cycle_id`.

If `--resume <cycle_id>`: read the existing scratchpad in that cycle's folder, find the last completed phase, continue from the next one.

### Step contract for every step

Every step-skill MUST follow the [Cycle Step Return Format contract](./best-practices/framework/cycle-step-return-format.md):

1. Invoke the step-skill with `--cycle-id <cycle_id>` so it knows where to write its sidecars.
2. The step writes `<run-folder>/<step>.json` and `<run-folder>/<step>.md`.
3. Orchestrator reads `<step>.json` after the step completes — this is what drives the aggregated report.
4. If the step JSON has `status != completed` or non-empty `errors[]`, flag in scratchpad and decide whether to continue (most step failures are non-blocking).

### Step 1.0 — Drive-fetch (queue from `__FOR CLAUDE/<topic>/`)

Pull URLs the user dropped into Drive throughout the week, queue them into `_inbox/pending/`, and **move handled files into `_completed/<cycle_id>/`** so the active scan folder stays clean across cycles.

Invocation:

```bash
python bootstrap/workflows/llm-wiki/scripts/wiki-fetch-drive-folder.py \
  --folder-name "__FOR CLAUDE" \
  --subfolder <topic> \
  --queue-into <topic> \
  --queue-vault docker/shared/openclaw/vault/wikis \
  --queue-priority 3 \
  --queue-added-by drive-fetch \
  --move-handled \
  --archive-subfolder <cycle_id> \
  --out <run-folder>/drive-fetch.md
```

Behavior:

- Files whose URLs successfully queue → **moved** to `__FOR CLAUDE/<topic>/_completed/<cycle_id>/`. Folders auto-created if missing.
- Files whose queueing failed → **left in place** in `__FOR CLAUDE/<topic>/` so the user can investigate / retry next cycle.
- `_completed/` is a one-time bucket the user can periodically delete from. Each cycle's files are grouped under their `cycle_id` subfolder for traceability — "which cycle did this file get pulled into?".
- First run with `--move-handled` triggers a one-time OAuth re-prompt because the script needs to upgrade from `drive.readonly` to full `drive` scope to re-parent files. Browser will open; user approves.

Update scratchpad Phase 1 with `unique_urls`, `queued`, `queue_failed`, `moved`, `move_failed` from `drive-fetch.json`.

### Step 1 — Discover (unless --skip-discover)

Run `/wiki-discover <topic> --cycle-id <id>`. It writes `discover.json` + `discover.md` into the run folder. Update scratchpad with results.

### Step 1.5 — Discovery confirmation checkpoint (human review #1)

**On by default until turned off.** After Discover completes, the orchestrator pauses and shows the user the Queued / Skipped / Deferred tables from `discover.md` (the JSON is authoritative; markdown is the human view). The user confirms:

- **"yes go"** → proceed to Ingest with the Queued items
- **"no"** / **"abort"** → mark cycle as interrupted, do not ingest anything
- **"tweak X"** / **"move X to Queued"** → user edits `discover.md` (move a row from Skipped to Queued, or vice versa); re-read to pick up the change; then proceed
- **"show me the raw JSON"** → print `discover.json` verbatim so user can verify the return-format contract is being honored

This step is a **temporary training wheel** while we validate the discovery → report contract. Once we've seen a few cycles where the JSON faithfully represents discovery's decisions, we can relax this to `--no-confirm-discovery` or auto-approve tier 1-3 / ask-on-tier-4.

**Flag**: `--no-confirm-discovery` skips this pause (for cron-driven runs where no human is around — but those should use `--direct` staging to land entries in `_inbox/proposed/` for later review anyway).

Update scratchpad Phase 2 with the user's decision.

### Step 2 — Ingest (unless --skip-ingest)

Queue approved items via `wiki-list-add.py`, then ingest via parallel agents (4 at a time, same pattern as today's session).

Each agent follows the full `/wiki-update` flow including the eval gate (step 5).

**Staging**: unless `--direct` was passed, all agents use `--staged` so entries land in `_inbox/proposed/`. This is the default — overnight runs should never file directly to wiki/ without morning review.

Update scratchpad Phase 3 with each completion.

### Step 3 — Mechanical lint

Run `wiki-lint-mechanical.py`. Update scratchpad Phase 4.

### Step 3.5 — Integration scripts (Phase 5 — always run, cheap)

Three Python scripts that are cheap, deterministic, and run every cycle in order:

1. `wiki-reciprocate-backlinks.py` — ensures every outbound `.md` link has a reciprocal BACKLINKS-AUTO section in the target
2. `wiki-index-per-folder.py` — regenerates `<folder>/_INDEX.md` for each subfolder (tier-2 map)
3. `wiki-map-compile.py` — regenerates `wiki/_MAP.md` (tier-1 compressed always-loaded orientation, ~2K tokens)

All three emit cycle-contract JSON when given `--cycle-id` + `--run-folder`. All three are idempotent. Total wall-clock: ~15 seconds for a 250-entry wiki.

Update scratchpad Phase 5 with results.

### Step 4 — Semantic lint (`--full` mode only)

**In default `--quick` mode, skip this step.** Semantic lint is expensive (4 parallel AI agents reading ~60 files each, 20-30 min wall-clock). Run weekly or when the wiki has grown substantially, not every cycle.

In `--full` mode: Spawn 4 parallel agents by folder (active/, long-term/, tooling/, orchestration+impl+root).

Update scratchpad Phase 5 with results (or note "skipped — quick mode").

### Step 5 — Fix lint issues

Spawn fix agents for the issues found (same pattern as today — backlinks agent, stale data agent, concept gaps agent).

Update scratchpad Phase 6.

### Step 6 — Claims extraction (if claims index exists or first run)

Run `/wiki-claims`. If this is the first run (no claims-index.json), do a full extraction. If index exists, run `--compare` for just the new entries.

Update scratchpad Phase 7.

### Step 7 — Refresh scan

Run `/wiki-refresh --overdue-only`. Flag stale entries in the scratchpad.

Update scratchpad Phase 8.

### Step 8 — Morning report

Run `/wiki-report`. This generates the full report including best practices gap analysis.

Update scratchpad Phase 9.

### Step 9 — Commit

Stage all changes and commit with a summary message:

```
Wiki cycle <date> — N ingested, N fixes, N contradictions, wiki at N entries
```

Update scratchpad Phase 10. Set overall status to `completed`.

### Step 10 — Show the user the morning report

Print the morning report inline. Offer to act on recommendations.

## Morning review workflow (after overnight cycle)

When the user comes back after an overnight `/wiki-cycle` run:

1. **User asks**: "what did we load?" or "morning report" or "what's in proposed?"
2. **Run `/wiki-report`** — shows everything that happened overnight including new entries in proposed/
3. **Run `/wiki-promote --review`** — shows each proposed entry with TL;DR, lets user approve/reject
4. **For approved entries**: promote to wiki/, add backlinks, regen INDEX
5. **For rejected entries**: move to `_inbox/rejected/`

This is human review checkpoint #2. The cycle did all the work overnight; the morning is a 5-minute approval pass.

## Resuming an interrupted cycle

If `--resume`:
1. Read the latest scratchpad in `_inbox/runs/`
2. Find the last phase with status `done`
3. Start from the next phase
4. The scratchpad has all the state needed — which items were approved, which agents completed, etc.

## Parallel agent patterns (proven this session)

| Task | Agent count | Split by |
|---|---|---|
| Ingestion | 4 at a time | Individual entries |
| Semantic lint | 4 | Wiki folder (active, long-term, tooling, orch+impl+root) |
| Lint fixes | 3 | Fix category (backlinks, stale data, concept gaps) |

Always use `subagent_type="general-purpose"` and `run_in_background=true`.

## Key paths

- Scratchpad: `docker/shared/openclaw/vault/wikis/<topic>/_inbox/runs/<date>-cycle.md`
- All other paths inherited from the sub-skills (discover, update, lint, claims, refresh, report)

## Don't

- Don't skip the scratchpad — it's the resume mechanism
- Don't run semantic lint if one ran in the last 24 hours (check scratchpad history) — too expensive
- Don't auto-approve tier 4 sources — always ask
- Don't run more than 4 parallel agents at once — diminishing returns + rate limits
- Don't commit mid-cycle — one commit at the end covers everything
- Don't skip the morning report — it's the user's review checkpoint
