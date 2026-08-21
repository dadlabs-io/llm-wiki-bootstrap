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
/wiki-cycle --full                # COMPLETE cycle: + semantic lint + claims + best-practices synthesis + refresh. "full" means FULL. (also accepts `/wiki-cycle full`)
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

**`--full` mode** (also written `/wiki-cycle full`): the COMPLETE pipeline. Adds Semantic lint (parallel agents by folder) + Claims scan + **Best-Practices Synthesis** (review the new research against the canonical `project/best-practices/*` pages and propose watch-notes / doctrine updates — see Step 6.5) + Refresh pass. ~40-50 min. **"full" means full — it MUST include the synthesis step; do not skip it.** Run weekly or when an ingest batch is ≥25 items, cross-cuts many existing entries, or semantic lint hasn't run in >7 days.

## Multi-wiki (which wiki does a cycle run against?)

Resolution is **per-project** — the cycle operates on whatever `<cwd>/.claude/wiki-config.json` declares. There is no global fallback; run the tooling from inside the project that owns the wiki. The shared resolver is `scripts/_wiki_config.py` (single source of truth — do not re-add per-script copies).

Config schema (v2):

```json
{
  "vault_root":    "<abs path to the folder that CONTAINS the topic folders>",
  "default_topic": "agentic-design",
  "topics":        ["agentic-design", "cottage-build"],
  "wiki_topic":    "agentic-design"
}
```

- A topic's root is always `<vault_root>/<topic>`. To move a wiki out of a repo (e.g. when it grows large enough to slow git), point `vault_root` at any absolute folder and relocate the topic folders there — names stay the same.
- `default_topic` is used when `<topic>` is omitted. `wiki_topic` is the v1 alias kept for back-compat (`default_topic` wins if both present).
- **Target a non-default wiki**: pass the topic as the positional modifier, e.g. `/wiki-cycle --full cottage-build`. The orchestrator passes `--topic cottage-build` to every step.
- **Run every declared wiki** (`--all-topics`): iterate `_wiki_config.list_topics()` and run the chosen mode once per topic, each writing to its own `<topic>/_inbox/reports/` tree. Use only when you explicitly want to sweep all wikis; default is the single `default_topic`.

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
_inbox/reports/<YYYY-MM-DD>/<YYYY-MM-DD>-<NN>/scratchpad.md
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

### Phase 7.5: Best-Practices Synthesis (`--full` only)
- **Status**: pending | running | done | skipped
- **Pages reviewed**: N
- **Proposed changes**: N (watch-notes N, doctrine N, confirm-only N)
- **Approved + applied**: N
- **Deferred to candidate-concepts**: N
- **Report**: _inbox/reports/<cycle-id>/synthesis-*.md

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
2. Scan `_inbox/reports/<date>/` for existing `<date>-NN` subfolders. Pick the next unused `NN` (starts at `01`).
3. Create the run folder:

```bash
mkdir -p _inbox/reports/<date>/<date>-<NN>/
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
python {{WIKI_SCRIPTS_DIR}}/wiki-fetch-drive-folder.py \
  --folder-name "__FOR CLAUDE" \
  --subfolder <topic> \
  --queue-into <topic> \
  --queue-priority 3 \
  --queue-added-by drive-fetch \
  --move-handled \
  --archive-subfolder <cycle_id> \
  --out <run-folder>/drive-fetch.md
```

(**`--queue-vault` removed from this example 2026-08-13** — the script's registry-aware default resolves the topic's real root; the hardcoded `llm-wiki/wiki` value this example used to show pointed cross-notebook topics at the WRONG vault. Omit it unless deliberately overriding.)

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

**Spawn ingest workers as `subagent_type="wiki-ingester"`** (the dedicated ingest agent, installed to `~/.claude/agents/` by this framework) — fall back to `general-purpose` only if it isn't installed. Spawner contract: read `~/.claude/agents/wiki-ingester-config.json` first; if `confirm_model_each_run` is true, ask the user which model to use for this batch (default = `model_default`) and pass it as the Agent tool's spawn-time `model` override.

Each agent follows the full `/wiki-update` flow including the eval gate (step 5).

**Staging**: unless `--direct` was passed, all agents use `--staged` so entries land in `_inbox/proposed/`. This is the default — overnight runs should never file directly to wiki/ without morning review.

Update scratchpad Phase 3 with each completion.

### Step 2.5 — Dequeue ingested items (ALWAYS run after ingest)

```bash
python C:/Users/mark/.claude/wiki-scripts/wiki-dequeue.py --topic <topic>
```

Moves every `_inbox/pending/` item whose `source:` URL now matches an ingested entry (in `wiki/` OR staged in `_inbox/proposed/`) into `_inbox/done/`. Genuinely-unprocessed and deferred items (e.g. unreadable X links) stay put.

**Why this exists**: the `--staged` batch path does NOT run `wiki-update.py`'s from-queue Step-9 dequeue, so ingested items otherwise pile up in `pending/` and every later cycle has to hand-reconcile them (this bit cycles 2026-07-01 and 2026-07-02, 61 stale items each). `wiki-dequeue.py` is the permanent, idempotent, source_url-based reconciler — run it here so the queue always reflects reality. Safe to run standalone any time.

### Step 3 — Mechanical lint

Run `wiki-lint-mechanical.py`. Update scratchpad Phase 4.

**If any entries were promoted into `wiki/` this cycle** (`--direct`, or an in-cycle `/wiki-promote`), run the link normalizer FIRST so mechanical lint sees clean links:

```bash
python C:/Users/mark/.claude/wiki-scripts/wiki-fix-links.py --topic <topic>
```

`wiki-fix-links.py` resolves every bare-slug / wrong-depth markdown link to its correct relative path (bare `](slug.md)` → `](../folder/slug.md)`, and depth over/under-shoots). Ingest agents author cross-links by BARE slug per contract; that normalization was historically NOT happening end-to-end (≈50 broken links per cycle, hand-fixed each time). This tool is the permanent fix. Idempotent, 0-ambiguous/0-missing on a clean run. (In default `--quick` staging mode entries aren't promoted in-cycle, so this runs at `/wiki-promote` time instead — see wiki-promote SKILL.)

### Step 3.5 — Integration scripts (Phase 5 — always run, cheap)

Three Python scripts that are cheap, deterministic, and run every cycle in order:

1. `wiki-reciprocate-backlinks.py` — ensures every outbound `.md` link has a reciprocal BACKLINKS-AUTO section in the target
2. `wiki-index-per-folder.py` — regenerates `<folder>/_INDEX.md` for each subfolder (tier-2 map)
3. `wiki-map-compile.py` — regenerates `wiki/_MAP.md` (tier-1 compressed always-loaded orientation, ~2K tokens)

All three emit cycle-contract JSON when given `--cycle-id` + `--run-folder`. All three are idempotent. Total wall-clock: ~15 seconds for a 250-entry wiki.

Update scratchpad Phase 5 with results.

### Step 4 — Semantic lint (`--full` mode only)

**In default `--quick` mode, skip this step.** Semantic lint is expensive (4 parallel AI agents reading ~60 files each, 20-30 min wall-clock). Run weekly or when the wiki has grown substantially, not every cycle.

In `--full` mode: Spawn N parallel agents (4 is the proven pattern) partitioned over `research/*` + `project/*` + wiki-root files, **balanced by file count per agent for the wiki's current shape** — the partition is chosen per run, not a frozen folder list. (Reworded 2026-08-13: this line previously froze a four-way folder split that no longer matched the taxonomy — a three-way disagreement between this file, `cycle-step-return-format.md`, and actual dispatch, caught by the 2026-08-04-01 drift-watch pass. Distribute any drift-watch deep-compare entries across the agents too.)

Update scratchpad Phase 5 with results (or note "skipped — quick mode").

### Step 5 — Fix lint issues

Spawn fix agents for the issues found (same pattern as today — backlinks agent, stale data agent, concept gaps agent).

Update scratchpad Phase 6.

### Step 5.5 — Promote staged entries (required before Steps 6/6.5 in `--full` mode)

**Bug discovered + fixed 2026-07-11 (cycle 2026-07-10-01): Steps 6 (claims) and 6.5 (synthesis) both
operate on "the wiki" / "new `research/` entries" — but the default ingest path (Step 2, `--staged`)
files new entries to `_inbox/proposed/`, NOT `wiki/research/`. Nothing between Step 2 and Step 6
promoted them. Result: synthesis agents wrote proposed-diff text that cross-linked staged entries by
their eventual `wiki/research/<folder>/` path, which didn't exist yet — 7 broken links surfaced only
at the post-synthesis mechanical re-lint, several steps after the mistake was made.**

**Rule**: if this cycle run will execute Step 6 and/or Step 6.5 (i.e. any `--full` run, or `--quick`
run with `--include-claims`/`--include-synthesis`), **promote all of this cycle's staged entries
before running them**:

```bash
python C:/Users/mark/.claude/wiki-scripts/wiki-promote.py --vault <topic_root>/wiki --auto
python C:/Users/mark/.claude/wiki-scripts/wiki-fix-links.py --topic <topic> --vault <vault_root>
python C:/Users/mark/.claude/wiki-scripts/wiki-lint-mechanical.py --topic <topic> --vault <vault_root>  # confirm 0 broken links before proceeding
```

Note `wiki-promote.py --vault` wants the **wiki dir itself** (`<topic_root>/wiki`), not the
vault_root — different convention from `wiki-update.py`/`wiki-lint-mechanical.py`, which want
vault_root + `--topic`. Get this wrong and the script silently reports "nothing to promote."

This is a deliberate exception to the normal staged-entries-wait-for-morning-review discipline
(Step 2's rationale still holds for `--quick` runs where no human is watching) — but a `--full` run
already has the human present in the same session (Step 1.5's discovery gate, and the Step 6.5
synthesis human-gate that follows), and Steps 6/6.5 need live `wiki/research/` content to cite
correctly. If the human explicitly wants staged entries held back from promotion even in a `--full`
run, tell Steps 6/6.5's agents to treat everything still in `_inbox/proposed/` as out-of-scope
(confirm-only "will review once promoted," no cross-links into it) rather than promoting — but
promoting first is simpler and is what actually happened when this bug was fixed.

After promoting: re-run Step 3.5's integration scripts (backlinks/index/map) since promotion adds a
large batch of new entries + backlinks at once.

Update scratchpad Phase 6 (or a new sub-phase) with promotion counts.

### Step 6 — Claims extraction (if claims index exists or first run)

Run `/wiki-claims`. If this is the first run (no claims-index.json), do a full extraction. If index exists, run `--compare` for just the new entries.

Update scratchpad Phase 7.

### Step 6.5 — Best-Practices Synthesis (`--full` mode only — DO NOT SKIP)

This is the step that turns ingested **research** into updated **canon**. A cycle WITHOUT this only grows `research/`; "full" requires it. (User-flagged 2026-06-23: "full wiki cycle" means complete, including this synthesis.)

Spawn synthesis agents (REPORT-ONLY — they do NOT edit the canon) that review the cycle's new `research/` entries against the canonical `project/best-practices/*` pages:
1. For each best-practices page whose domain the new entries touch, ask: does the new research (a) CONFIRM existing doctrine, (b) warrant a new dated **watch-note** (emerging / single-source / contested), or (c) warrant an actual DOCTRINE CHANGE (well-corroborated, shifts a stated position)? Be conservative — prefer watch-notes; flag contradictions both-sides-stay.
2. Net-new doctrine areas with no home page, and design-gaps, go to `project/best-practices/best-practices-candidate-concepts.md` (the integration backlog), NOT a shoehorned edit.
3. Agents write a proposed-diff report to the run folder (e.g. `synthesis-<area>.md`): exact section, proposed text in the page's voice + dated, source entry, rationale + confidence.

**HUMAN GATE:** present the consolidated proposed diff to the user (take-all / pick / none). Apply ONLY what they approve to the `project/best-practices/*` pages; bump each touched page's `last_reviewed`. Log deferred items to candidate-concepts. (In `--no-confirm` / headless runs, write the proposal to the run folder and leave canon unchanged for later review — never auto-write canon.)

Update scratchpad Phase 7.5.

### Step 7 — Refresh scan

Run `/wiki-refresh --overdue-only`. Flag stale entries in the scratchpad.

Update scratchpad Phase 8.

### Step 8 — Morning report

Run `/wiki-report`. This generates the full report including best practices gap analysis.

Update scratchpad Phase 9.

### Step 9 — Commit

**Stray-file sweep FIRST.** Before staging, run `git status --short` and delete any 0-byte / junk droppings from shell-redirect or quoting artifacts (own or sub-agent: e.g. files named `output`, `#`, `${...}`, a stray word, etc.). These are tooling junk, not content — clean them yourself, don't leave them for the user or commit them.

Then **scope the add to the notebook path** (NOT `git add -A` — other notebooks/sessions may have uncommitted work) and commit:

```
Wiki cycle <date> — N ingested, N fixes, N contradictions, N synthesis changes, wiki at N entries
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
1. Read the scratchpad in the cycle's run folder (`_inbox/reports/<date>/<cycle_id>/scratchpad.md`)
2. Find the last phase with status `done`
3. Start from the next phase
4. The scratchpad has all the state needed — which items were approved, which agents completed, etc.

## Parallel agent patterns (proven this session)

| Task | Agent count | Split by |
|---|---|---|
| Ingestion | 4 at a time | Individual entries |
| Semantic lint | 4 | Wiki folder (active, long-term, tooling, orch+impl+root) |
| Lint fixes | 3 | Fix category (backlinks, stale data, concept gaps) |

Use `subagent_type="wiki-ingester"` for ingestion workers (fallback: `general-purpose` if not installed — see Step 2); `subagent_type="general-purpose"` for all other worker types. Always `run_in_background=true`.

## Key paths

- Scratchpad: `_inbox/reports/<YYYY-MM-DD>/<cycle_id>/scratchpad.md` (corrected 2026-08-13 — two references in this file previously said `_inbox/runs/`, an obsolete location contradicting Step 0; caught by the 2026-08-04-01 semantic lint's drift-watch pass)
- All other paths inherited from the sub-skills (discover, update, lint, claims, refresh, report)

## Don't

- Don't skip the scratchpad — it's the resume mechanism
- Don't run semantic lint if one ran in the last 24 hours (check scratchpad history) — too expensive
- Don't auto-approve tier 4 sources — always ask
- Don't run more than 4 parallel agents at once — diminishing returns + rate limits
- Don't commit mid-cycle — one commit at the end covers everything
- Don't skip the morning report — it's the user's review checkpoint
