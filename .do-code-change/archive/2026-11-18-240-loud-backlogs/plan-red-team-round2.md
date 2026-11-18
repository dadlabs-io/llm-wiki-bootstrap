# Red-team: plan.md revision 1 (240-loud-backlogs, round 2)

Written by the orchestrator from the red-team's report: a fresh architect running strategy-red-team, with one red-team-reviewer (haiku) spawn. readonly-guard check: PASS (638 files, HEAD unchanged). Round 1 is in plan-red-team-round1.md.

## Round-1 kill-assumptions: resolved or turned into a Decision?
- **KA1:** mostly resolved. Three holes remain: attacks 4, 5 and 6.
- **KA2:** resolved.
- **KA3:** became Decision 1. Attack 7 covers the fixture holes.
- **KA4:** became Decision 2. Attack 3 finds a new defect in it.
- **KA5:** partly resolved. Decision 3 has a new defect (attack 3), and Decision 4 is pre-empted by the plan (attack 8).

## Kill-assumptions (ranked)

### 1. Mechanical findings read as "awaiting your approval" after Step 5 fixed them
The plan counts the mechanical kinds from `lint-mechanical.json`'s summary and subtracts nothing.
- **Fails if:** a `--full` run has `confirm_before_promote: true` and the user approves mechanical fixes at Step 5. The JSON is re-run only in Step 5.5, and only when promotion is automatic (`SKILL.md:156,163`). The stale JSON then lists fixed findings as awaiting approval.
- **Kill criterion:** any path where a fixed finding stays in a Left undone line.
- **Cheapest test:** a `--full` run with the setting true, the JSON showing 2 broken links, and `lint-fixes.txt` at `applied: 2`.
- **Fix class:** choice. Re-run the mechanical lint after Step 5, or make `applied`/`declined` per category, or word the line "found by the lint, fixes not confirmed".

### 2. `--report-only` reads each input from a different place
- **Fails if (a):** the counts read `lint-fixes.txt` from the last run, but the "did it run" check looks for it in the current folder, so the line reads `no fix step in this mode`.
- **Fails if (b):** "last run folder" is never defined, and an unfinished run with no step JSONs has no stated line.
- **Cheapest test:** a last-run folder holding `lint-fixes.txt`, with an empty current folder.
- **Fix class:** plan error. The "did it run" checks read the same folder as the counts. Define "last run" as the newest earlier folder holding a run-cycle report, or state the line when none exists.

### 3. The two model-written files make a silent failure the default
Both `tier4-deferred.txt` (Step 1.5) and `lint-fixes.txt` (Step 5) are files the model has to remember to write.
- **Fails if:** the model skips a write. The scope script's docstring says a sentence asking the model to do a step was skipped in 21 of 22 runs (`wiki-cycle-scope.py:55-58`, task #99). Steps 1.5 and 5 carry no write instruction today (`SKILL.md:93-97,154`).
- **Kill criterion:** no test where the file is absent and the section still says something true.
- **Cheapest test:** a `--full` folder with `lint-semantic.json` and no `lint-fixes.txt` must read `not checked`, not `no fix step`.
- **Fix class:** plan error for the `--full` case: a missing `lint-fixes.txt` after a `--full`-class step reads `not checked (no lint-fixes.txt)`. Tier-4 stays a choice inside Decision 2, which gains a third option: take tier-4 from the checklist's "(NEEDS HUMAN REVIEW)" labels (`wiki-discover/SKILL.md:273`), with no new model-written file.

### 4. A partial or failed step has its whole scope subtracted
- **Fails if:** the step's JSON has `status: partial` or `failed` (`cycle-step-return-format.md:119`; a failed step does not block later steps, `SKILL.md:69`), or one lint slice failed with no per-slice status in the merged JSON (`SKILL.md:152`). The line then reads `nothing`. Stems can also collide across folders.
- **Cheapest test:** `lint-semantic.json` with `status: partial` and a scope file of 3 entries must read `not checked (the step did not complete)`.
- **Fix class:** plan error. Subtract only when the status is `completed`, else print `not checked`. Compare full relative paths, using stems only to bridge the move from `_inbox/proposed/` to `wiki/`.

### 5. Day granularity reports linted entries as not linted
- **Fails if:** an entry has `last_reviewed` = D (the ingest stamps today, per the reviewer, `wiki-update.py:822`) and a lint on day D covered it. Every later cycle that skips the lint counts it as not linted, until the next lint. That is a false count, against requirements line 75.
- **Cheapest test:** a lint on 2026-09-10 whose scope file lists an entry with `last_reviewed` 2026-09-10 should count 0.
- **Fix class:** choice. Label the line "may include entries linted that day", or also subtract the previous run's scope file, or compare by timestamp (which changes the step's own behaviour).

### 6. Entries with zero claims stay "no claims" forever
- **Fails if:** an entry yields no claims. The index has one record per claim, so it never names that entry (`wiki-cycle-scope.py:249-251`), and no mode can clear the count.
- **Cheapest test:** a read-only claims-scope run on the live notebooks.
- **Fix class:** choice. Accept it with reason text, or record claim-less entries in the index, or keep the line out of modes other than `--full`.

### 7. The seeded resume case is under-specified
- **(a)** A resume continues from the phase after the last `done` (`SKILL.md:67`). The existing `fixtures/resume/scratchpad.md` is interrupted with phases 2.5-9 pending, so unless every earlier phase is seeded `done`, the model re-runs them.
- **(b)** Without seeded `semantic-scope.txt`, `claims-scope.txt` and `promote-setting.txt`, the counter prints `not checked`. Case B also depends on git state: untracked files look added after any cut-off (`scope.py:172-177`), so it needs the orphan-branch backdating helper at `check.py:1815-1834` and far-future `review_after` dates.
- **(c)** A seeded `lint-semantic.json` trips the presence-keyed guards in `check.py:546-547,1163,1307,1548`.
- **Fix class:** plan error. State the fixture contents, and have an unpaid test run the fixture builder first.

### 8. The settled sources decision is applied before it is asked
The counting rule drops "already covered" items whatever Mark answers.
- **Fix class:** plan error. Move the exclusion into the Decision's recommended form, and say what steps 4 and 5 do under each answer.

### 9. Smaller points
- **Script tests left out (plan error):** the extraction's script tests miss `test_synthesis_scope.py`, `test_checker_hold.py` and `test_promote_setting.py`. Add them to "run at every step".
- **Lint within 24 hours (plan error):** Step 4 is skipped when a lint ran in the last 24 hours (`SKILL.md:146`). The reason and the way out are then wrong, so add a "ran within 24 hours" reason.
- **Tickets with no `source:` (choice):** they are not counted (`wiki-dequeue.py:25`), but D6 asks for the count still to be processed.

## Skip, drop, exempt and default rules
**Hold:**
- `sessions/` and `tasks/` not counted.
- Strict `review_after < today`.
- Standalone pages excluded.
- Staged entries, Drive, held, retry, PDF and unfinished-run items left to Needs you.

**Conflict:**
- "Already covered" drops left out (attack 8).
- Absent events files add no line (attack 3).
- Day granularity (attack 5).
- Subtracting a partial or failed step (attack 4).
- Rows 15, 22 and 23 excluded: requirements line 54 excludes them, but line 66 says every queue that can be non-empty. That is a conflict inside the requirements.

**No standing rule found:**
- A missing bucket folder counts 0.
- `--report-only` reasons.
- The `Sources: not checked` and `(no reason recorded)` defaults.
- A malformed `review_after` getting its own line.

## The README trigger claim
- The extraction of `cmd_semantic`, `cmd_claims` and `cmd_synthesis` is not additive. Only wiki-cycle calls those three subcommands.
- `tests/skills/README.md:9` says "a script many skills call", and the plan reads that as not firing here. That reading is defensible, but it is Mark's judgement. Either run the full wiki-cycle suite, or accept the targeted cases plus the script tests.

## What holds up
- The `.txt` file needs no contract edit.
- The marker filter (`retry:`, `save_as_pdf:`).
- The live-data arithmetic.
- The claims cut-off moving does not hide entries.
- The three-state template, and the old ordering checks.
- Reusing `buckets()`/`me()`.
- Dedup hits left out.
- Only `left-undone.txt` is written.

## Could not assess
- Live counts not measured: duplicate basenames, zero-claim entries, and entries whose `last_reviewed` equals the lint day.
- Whether the semantic lint writes `last_reviewed`.
- Whether `buckets()`/`me()` import unchanged by importlib.
- The `lint-mechanical.json` summary keys (`:1487-1505`), not read.
- `trajectory_rules.py`, not read.
- Whether the model copies the lines: only the paid run shows that.
- The scope script's skill-file count (4 or 11).

VERDICT: KILL-ASSUMPTIONS FOUND
