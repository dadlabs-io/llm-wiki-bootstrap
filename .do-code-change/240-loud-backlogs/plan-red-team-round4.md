# Red-team: plan.md revision 3 (240-loud-backlogs, round 4)

The orchestrator wrote this from the red-team's report. The red-team was a fresh architect running strategy-red-team, with one red-team-reviewer (haiku) spawn. The readonly-guard check passed: 640 files, HEAD unchanged. Rounds 1-3 are in plan-red-team-round1/2/3.md.

The architect read:
- check.py 2694-2851
- wiki-triage.py 1-190 and 290-360
- wiki-cycle-scope.py 100-340
- the SKILL.md of wiki-report, wiki-cycle and wiki-discover
- wiki-cycle reference.md
- wiki-feeds.py `known`
- the framework-docs step contract
- tests/skills/README.md

## Round-3 kill-assumptions: resolved, or turned into a Decision?
- **KA1:** resolved in substance, with gaps:
  - The table stops at 2781, which misses the kind-gated check at 2788-2790 (it needs triage-log.md and applies to `ingest-only` and `triage`).
  - check.py has no `--lint-only` case yet, so B would be the suite's first.
  - The Step-8 resume is still unproven, and is rightly deferred to the first paid session.
- **KA2:** the cross-check is resolved. Reading the mode has new problems (KA2 below).
- **KA3:** partly resolved.
  - The partial lint and the `findings` shape are resolved.
  - The ids have no source (KA3 below).
  - Same-day is Decision 8.
- **KA4:** resolved.
- **KA5:** partly resolved.
  - The cmd_retry_list migration is not behaviour-preserving (KA4 below).
  - Two tier-4 holes remain (KA7).
- **Contract gaps:**
  - The interim form and the Part 1 step-file wording are resolved.
  - The single past-due number names a heading that has no N, and it redefines the Numbers row (KA5).
  - The Needs-you wording contradicts the plan's invariant.
  - Concept gaps are Decision 9.

## Kill-assumptions (ranked)

### 1. No third state: the mode runs the step, but its JSON is absent or not completed
The wording table (plan:54-69) has two columns, "Mode does not run it" and "Ran".

**Fails if:**
- `--full` with no refresh.json, which is exactly case A as planted (plan:114). The only wording available is "this mode does not run refresh", which is false.
- The same gap applies to:
  - triage (A seeds no triage.json);
  - the ingest-based ticket lines;
  - the lint kinds;
  - three Part 1 rows that have a "Ran" column.
- A resumed or interrupted `--full` run gets a confident false reason, against plan:154.

**Kill criterion:** any row whose mode runs the step but whose JSON is missing prints "does not run" or "ran".

**Cheapest test:** a `--full` scratchpad with no refresh.json or triage.json. Every such line must read `not checked (<step> left no <file>)`.

**Fix class:** plan error. Add the third state to every row that has a "Ran" column, and reword A's expected lines.

### 2. The mode and its modifiers are read from free text
**Fails if:**
- reference.md:15 gives only `(<mode>)`, while :18 has a separate `- Mode: <mode and flags>` line. A run that puts `--no-confirm-discovery` only on that line gets no tier-4 line and no "not checked".
- SKILL.md:19 allows `/wiki-cycle full`, but the plan's token list has `--full` only with dashes.
- "12 of 12 parse" doesn't show that the modifiers get copied.
- plan:50: a missing update.json or discover.json, in a mode that runs that step, reads as "none".

**Kill criterion:** a live run with the flag only on the `Mode:` line, or a mode word the tokenizer misses.

**Cheapest test:**
- `(full)`
- `(--full, --no-confirm-discovery)`
- the flag only on `- Mode:`
- `--ingest-only` with no update.json

**Fix class:** plan error.
- Read the mode from `**Cycle**` and the modifiers from both lines.
- Accept bare `full`.
- Change the reference.md template to `(<mode>[, <modifiers>])`.
- A step the mode runs that left no file reads `not checked`.

### 3. `lint-fixes` ids are unreachable, and mechanical-only fixes leave no record
**Fails if:**
- Step 4 merges findings without numbering (SKILL.md:152), and Step 5 approves fixes by category (:154). Nobody is shown a position, so the model counts positions in a list of up to 193. A wrong id that is still in range passes validation silently.
- Mechanical-only approvals record no id, so the staleness guard ("records fixes applied") doesn't fire. If the lint re-run is skipped, already-fixed broken links are still named.
- An earlier run's unfixed semantic findings (agentic-design's 193 from 2026-10-30) appear in no later Left undone: the entries count as covered, and only this run folder is read.

**Kill criterion:** the lint .md has no position numbers, or a `--full` run with mechanical-only fixes prints the pre-fix counts.

**Fix class:**
- Plan error:
  - The guard fires whenever lint-fixes.txt exists, with zero ids included and an `at:` stamp.
  - The lint report shows the ids, so the model copies them.
  - State the order of lint-fixes and the re-run.
- Choice for Mark: whether a standing semantic backlog from an earlier run is named in later runs (read the newest completed lint-semantic.json minus the fix record), or the limit is stated.

### 4. The cmd_retry_list migration changes behaviour, and the tests can't see it
**Fails if:**
- Today it walks every .md in a bucket, filters on `retry:`, and falls back to the file name when there is no `source:` (wiki-triage.py:316-320). `intake_tickets` skips `_`-prefixed files and files with no `source:`, so a retry ticket with no source vanishes from Needs you's retry line.
- The fixtures in test_wiki_triage.py:234-277 all carry a source, so the tests stay green regardless.
- "Named by seven skills" is wrong: the reviewer counted four SKILL.md files.

**Fix class:** plan error. Leave cmd_retry_list alone and list it under Out of Scope. Or keep the migration, add a no-source fixture, and give `intake_tickets` a `require_source` flag.

### 5. The one past-due number changes a contract, and Needs you and `--brief` are undefined
**Fails if:**
- The `### Stale entries (review_after passed)` heading (wiki-report:163) carries no N.
- Step 1G's awk counts tasks/ and sessions/. The Numbers row would be filtered and the table unfiltered: on llm-wiki-bootstrap, 6 against 186 rows.
- Every other mode's Numbers row is redefined without a Decision, and no eval check covers the Numbers row.
- plan:75 rewords a Needs-you line, against "keeps every line it has today", and doesn't say what Needs you prints for `not checked` or `0`.
- The `--brief` content is never stated. Its precedent (wiki-report:301) is silent at zero, and a line the model composes would be a computed count.

**Fix class:**
- Plan error:
  - Drop the heading claim.
  - Fix the brief to a stated string, e.g. `Left undone: <first line of the file> — see the full report`.
  - Rewrite the invariant.
  - Define Needs you for `not checked` and `0`.
- Choice for Mark: redefine the Numbers row (excluding task cards), or leave it and show the Left undone count separately.

### 6. Gaps in the common-check table and the fixture
**Fails if:**
- The table omits 2788-2790.
- `me()` reads load_config() from the cwd (wiki-triage.py:87-92; _wiki_config.py:205), so a live run from another project labels the wrong bucket. The harness sets the cwd, so the tests pass anyway.
- B's earlier folders need a run-cycle report each, or Step 0 lists them as unfinished.
- B needs the backdating helper.

**Fix class:** plan error.
- Name the new case kinds.
- Add 2788-2790.
- State the live cwd.

### 7. The tier-4 line can name sources this run didn't defer
**Fails if:**
- `--ingest-only --no-confirm-discovery` runs no discovery (SKILL.md:32), so an earlier checklist in `_inbox/done/` produces false lines.
- Two cycles on the same day share the file name.
- wiki-feeds.py `known` reads only the first 30 lines of a ticket (:106).

**Fix class:** plan error. Gate the tier-4 read on discover.json existing in this run folder.

### 8. Behavioural text is checked by manual reading only
The Needs-you rewording, the Numbers rule, the `--brief` line and Step 5's text all change the report with no red-then-green case. tests/skills/README.md:20 asks for "two fresh cases".

**Fix class:** choice for Mark. Add a third case, or accept manual reading.

## What holds up
- **Contract and order:** no contract change, and the section order is fine.
- **Scope counting:** the covered-set rule, the newest_step migration (exactly two walkers), and the tasks/ filter.
- **Mode table:** the cross-check table matches SKILL.md:28-45.
- **Discovery:** `known` and the checklist template.
- **Errors and last run:** the update.json errors shape, and the report-only last-run rule.
- **Existing tests:** the last_semantic and last_synthesis tests.
- **Decision 4:** its reading is arguable.
- **Lint design:** the partial-lint handling and the id validation.

## Skip, drop, exempt and default rules against the standing rules
**Holds:**
- tasks/ and sessions/ are not counted.
- No repeats of what Needs you already shows.
- Staged entries are counted only when the setting is false. That is a reasoned reading of requirements:68.
- Rows 15, 22 and 23 (Decision 9).
- Other buckets on one line (D6).
- A mode mismatch reads `not checked`.

**Open or conflicting:**
- Decision 5, the "already covered" drops: update.json's "already covered" skips are listed every cycle while discovery's are not. State the difference.
- Decision 8, the same-day under-count.
- KA8, behavioural wording checked by hand.

**No standing rule found:**
- a missing bucket folder counts 0
- a non-date review_after gets its own line
- bucket files with no source: are not counted (D7)
- the regex fallback is not exercised
- the drift test covers 5 of 9 modes
- Part 1 never writes "nothing"
- the `not checked` and `(no reason recorded)` defaults
- the lint keys left out
- the `--today` default
- the first-token mode rule

## Complete enough to build?
No, but it is close. A revision 4 can settle every plan error without a new question. KA1, KA2 and KA5 sit in Part 1's step 1.

**Plan errors (7):** KA1-KA7, each with one correct fix as above.

**Choices for Mark:**
- a standing semantic backlog from earlier runs
- the Numbers row
- a third paid case for the brief and Needs you
- the nine existing Decisions

## Could not assess
- Whether the session resumes at Step 8.
- How lint-semantic.md presents findings.
- The live counts in agentic-design.
- Whether /wiki-refresh changes entries.
- PyYAML in the scripts environment.
- check.py past line 3113, and test_wiki_triage.py past line 277.

VERDICT: KILL-ASSUMPTIONS FOUND
