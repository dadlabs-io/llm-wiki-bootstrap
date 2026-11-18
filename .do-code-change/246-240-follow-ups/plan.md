# Plan: the three small follow-ups from change 240-loud-backlogs (task #246)

Classification: **vertical slice**, three of them. Each follow-up (A1 the skill sentence, A2 the claims count, A3 the paid checks) is built end to end on its own, test and fix together; nothing is layered and nothing is renamed, so it is not a wide refactor. The three share no step, function or file (see Decisions needed 1). Lowercase "step N" is a step of this plan.

## Problem Statement

Change 240's review left five findings open: the cycle skill does not say to leave out a `lint-fixes` flag that has no ids (A1, spec-15); the claims line of `left-undone` skips the later-day rule when there is no claims index but a completed `claims.json` exists, and the rule's docstring is wrong about the index-only case (A2, spec-1); and the paid checks for the two `left-undone` cases accept a dash turned into a hyphen, miss most ways a session can write `left-undone.txt` itself, and carry a header naming a kind that does not exist (A3, spec-32, spec-33, standards-52).

## Solution

- A1: one clause in cycle Step 5 item 3 of the cycle skill. No code.
- A2: keep the code's rule for an index with no `claims.json` (Mark's confirmed Decision 1) and pin it with a new test; fix the no-index case in `entry_backlog_lines`, not in `claims_scope`: the cut-off stays the index's written time when the index exists, and is the newest completed `claims.json`'s timestamp otherwise. Correct the `_run_state.py` docstring in the two places it is wrong.
- A3: the checks in the wiki-cycle suite's `check.py` are `eval-case-writer`'s text, so the session never writes them. The orchestrator briefs the writer from the three findings and saves its answer unchanged. The session's own free test, `test_left_undone_fixture.py`, first gains planted defects that must make a check fail (red against today's `check.py`), and goes green once the writer's text is saved. The paid re-run is a manual step that waits for Mark's yes.

## Implementation Decisions

- **A2 fix, the one decision a cheaper implementer must not make.** In `entry_backlog_lines`, the claims branch keeps its loop-top `cutoff` (the newest completed `claims.json`'s timestamp, or None) and takes the index's written time only when `claims_scope` returns one:
  ```python
  scope, _all, _why, written = claims_scope(nb)
  cutoff = written or cutoff
  ```
  Not `cutoff = found[0] if found else written` (that would let a `claims.json` override the index's time, which `cmd_claims` does not). `claims_scope`, `cmd_claims` and `uncovered` are not touched. Only a *completed* result sets `cutoff`, as today (`newest_step(..., "completed")`), so a partial `claims.json` with no index still counts every entry.
- **New tests are new functions with new names**, added after the last existing test in `test_cycle_scope.py`, reusing the harness helpers that are already nested there (`mknb`, `lu_run`, `s4_lu`, `s4_step`, `s4_entry`, `s4_commit`, `s4_stamp`, `s4_line`, `D0`..`D3`, `CLM`, `CLM_OFF`, `CLM_RAN`, `s4_claims_nb`). The freeze hashes a test plus the *module-level* names it loads (`check-freeze.py` `_toplevel_defs` reads the file's top-level statements only); the harness helpers and constants are nested inside the file's one block, so they are not hashed, and the top-level names (`SCRIPT`, `RUN_STATE`, `check`, `entry`, `git` and the rest) are what an edit would move. No existing function, constant or top-level name is edited; a new test name has no `and` segment (the freeze refuses one). A test that needs an entry reviewed after the claims stamp uses `s4_step` with an earlier stamp, never `s4_claims` (it stamps `D3`, the last day).
- **The (b) test notebook:** no claims index; `old-a` and `old-b` committed `D0`; `old-a` re-written `D2`; a completed `claims.json` stamped `s4_stamp(D1)` with a `claims-scope.txt` listing both. Run `--full`. Before the fix no claims line is printed (no cut-off, so both are covered); after it, exactly `f"{CLM}1 — {CLM_RAN}"`.
- **A3 planted defects** in the fixture test are driven by two things the plant sets together, so a check fails whichever detection the writer chooses (widen the pattern; require a call that ran the script; compare the file with the script's own output): the route in the session's `tool_calls`, and an on-disk `left-undone.txt` that differs from what the script writes (one count changed) with a report section copying it. They are read from `check()`'s results directly, as `tamper_checks` does, never through `report()` (its `NEEDS_SESSION` list files "the session did not write left-undone.txt itself" as needing a paid session and never counts its failure). The plant-free sessions carry one legitimate call, the script as cycle Step 8 prints it, so a writer's positive check ("a call ran `wiki-cycle-scope.py ... left-undone`") does not fail every plant-free run; under the other two designs that call is inert.
- **Helpers, searched for.** A2: `uses: newest_step, uncovered, read_scope_file, claims_scope` (`_run_state.py`, `_cycle_common.py`); no new function. A3 fixture: `uses: empty_session, compose_report, tamper_checks, own, case_of, build` (the fixture file); new function `session_write_plants`, searched for `tool_calls`, `empty_session`, `plant`: none builds a session with calls, so a small `session_with(*calls)` joins it; both are used only in that file, so neither is a shared helper and no migrate step follows. The suite's own `_lu_*` helpers are the writer's.
- **The A3 brief to `eval-case-writer`**, mode `replay` (the three findings are failures seen in review): the suite folder and `cases.json`; the quoted requirement (240's plan Solution: "pastes the file word for word", "The model computes no count and writes no reason", one script writes the file); `spec-32`, `spec-33`, `standards-52` verbatim from the archived `review-ledger.json` and `review-report-round-3.md`; the current text of `_lu_norm_line`, `_lu_norm_lines`, `_lu_section_lines`, `_lu_model_wrote_file`, `_lu_copy_checks`, `_check_left_undone_verbatim`, `_check_left_undone_old_run` and every caller (`_lu_copy_checks` is called by the verbatim kind only; `_lu_model_wrote_file` also by the old-run kind; `_lu_norm_line` feeds the verbatim and old-run kinds only, the planted and clean kinds read their section through `_lu_section`, `_lu_lines` and `_lu_find`); and the two rulings it must meet: a changed dash fails the copy check (Decision 5, dash character included in "word for word"), and a `left-undone.txt` the session wrote by any route cannot make the copy check pass. The README's "an existing kind is never changed" rule is overridden here by requirements line 40 (the findings are in two existing kinds' checks). Its questions go to Mark, never answered by the session.
- **Paid cases whose checks change:** the verbatim and old-run cases (`left-undone-section-is-the-file-line-for-line-with-nothing-added-or-reworded`, `report-rebuilt-from-old-run-without-left-undone-file-reads-not-checked-above-needs-you-and-creates-no-file`), the two 240 ran for $6.27. The planted and clean cases read none of the changed helpers. The re-run is a plain `--cases` run on both models, not `--red-green`: the skill is unchanged, so the old copy would pass too and the exit would read "passes on the old copy".
- **Docstring.** The `_run_state.py` module docstring is the one source for the covered-set rule. Two edits: where it says the claims cut-off "C is when claims-index.json was last written" it gains "(with no index: the newest completed claims.json's timestamp)", and "With no completed result anywhere, nothing is covered and scope-now is every entry" gains the claims case ("claims: scope-now is the entries no index claim comes from plus those revised since the index was written; every entry only when there is no index"). Two frozen tests read the docstring, for "names another notebook" and "not a supported case", and for "only completed lints are read" with "partial" in the 600 characters from 300 before it; those phrases and their neighbourhood are left as they are.
- **Living pages (outside the repo, after verify, by the orchestrator, not in Scope):** `project/architecture/30-the-research-cycle.md` (one clause where it names the covered-set rule) and the wiki code-change record `project/code-changes/2026-11-18-240-loud-backlogs-...md` (line 22), both in the notebook `C:/github.com/project-notebooks/notebooks/llm-wiki-bootstrap`, each given the corrected claims wording by pointing at the docstring, not copying it. The installed copy follows at finish: `.\install-wiki.ps1 -RefreshOnly`, then `uv run python scripts/new-wiki.py --mode status` reading installed and current.

## Testing Decisions

Seams, put to Mark at Change confirmation (not confirmed by trying them):
- **Seam 1:** `wiki-cycle-scope.py left-undone`'s output lines through the harness's `s4_lu` in `tests/scripts/test_cycle_scope.py`, run as `uv run python tests/scripts/test_cycle_scope.py` (exit 0 = all pass; about 2 minutes).
- **Seam 2:** the suite's `check()` over a built sandbox with a synthetic session, in `tests/scripts/test_left_undone_fixture.py`, run as `uv run python tests/scripts/test_left_undone_fixture.py` (needs `qmd` on PATH; the embed takes up to 600 s). Free; no model.
- Also run at the end of every code step: the six neighbouring suites of 240's plan (`test_wiki_triage.py`, `test_synthesis_scope.py`, `test_checker_hold.py`, `test_promote_setting.py`, `test_dequeue_intake.py`), each `uv run python tests/scripts/<name>`.

- manual: step 1 — the sentence read against `wiki-cycle-scope.py lint-fixes --help` (both flags optional, each takes a value) and against the frozen `lint_fixes_writes_the_fixes_record`, whose no-flag call (`lf()`, both lists empty) already pins the behaviour the sentence names; no new test.
- manual: step 4 — the docstring text read against steps 2 and 3's tests; its two frozen pins by running seam 1.
- manual: step 6's save — the diff of `check.py` is the writer's answer byte for byte (the orchestrator compares), and the session edits only the fixture test's constants.
- manual: step 8 — the CHANGELOG entry and the PENDING rows read against steps 1 to 7.
- manual: step 9 — the paid run's report path and result, recorded in `checkpoints.md`; runs only on Mark's yes.

## Out of Scope

- Every other open 240 finding (spec-2, spec-13, spec-14, spec-16, spec-17 and the rest).
- `claims_scope`, `cmd_claims`, `wiki-cycle-scope.py`, `_cycle_common.py`, the claims scope file, the semantic and synthesis rows, any report line or queue, `wiki-report`, the `lint-fixes` script and its flags.
- A new test for A1 (the frozen test above pins it); a paid case for A1.
- A re-run of any other wiki-cycle case; `baseline-*.json` (they hold none of the `left-undone` cases) and `cases.json` (the cases are unchanged; the checks are the writer's).
- The living pages and the installed copy: done by the orchestrator after verify and at finish (above), not edits of this change.
- Look-alikes outside Scope: none found that this change would copy.

## Scope

- scripts/_run_state.py
- skills/wiki-cycle/SKILL.md
- tests/scripts/test_cycle_scope.py
- tests/scripts/test_left_undone_fixture.py
- tests/skills/wiki-cycle/check.py
- tests/skills/PENDING.md
- CHANGELOG.md
- .do-code-change/246-240-follow-ups/**

## Invariants

- The 56 frozen tests of `tests/scripts/test_cycle_scope.py` and every other frozen test stay unmodified: `check-freeze.py` at verify. The three new tests are added beside them; none of the 56 changes.
- `uv run python tests/scripts/test_cycle_scope.py` and the five neighbouring suites stay green at the end of every code step (the claims row with an index, the claims step's own scope and every other row are pinned by the existing `s4f`-`s4h` claims tests, the `lint_fixes_refuses_ids_it_cannot_place` exit-2 refusals, and the covered-set tests).
- `git diff --stat -- scripts/wiki-cycle-scope.py scripts/_cycle_common.py scripts/wiki-triage.py skills/wiki-report framework-docs tests/skills/wiki-cycle/cases.json tests/skills/wiki-cycle/baseline-sonnet.json tests/skills/wiki-cycle/baseline-opus.json` prints nothing at verify.
- The paid checks keep failing for what they fail for today (an invented, a reworded, a dropped queue line; the session writing the file by `Write`, `Edit`, `>` or `tee`): pinned by the fixture's existing three tampers and by control plants for the four old write routes, which must fail before and after step 6.
- The plant-free fixtures (case A's and case B's graded runs, every check the fixture grades today) still pass after step 6.
- `check.py` changes only by the writer's text; the session writes no check (README rule): the orchestrator's byte comparison at step 6.

## Decisions needed

1. **One change or three?** A1 (the cycle skill), A2 (`_run_state.py`) and A3 (the suite's `check.py`) share no step, function or file, so `writing-implementation-plans` proposes them as separate changes, split recommended by the skill. This plan is written for the whole set.
   Recommendation: keep them as one change, the way Mark's card #246 defines it ("three steps", before #243): the three are 1 sentence, about 1 line plus tests, and one check rewrite, and three runs would each pay their own confirmation, review, verify and finish for that. This departs from the skill's default and is put to Mark for that reason.
   Alternative: split in the order A1, A2, A3 (A3 last, since it waits on the writer and on the paid run). Risk: three sets of ceremony for about 60 changed lines in all; in return, a failure or a wait in A3 (the writer's answer, Mark's go for $6) would not hold A1 and A2.
   [ ] keep as one change  [ ] split

(Requirements Decisions 2-5, the paid re-run, A1 with no new test, the (b) cut-off and the dash, are put at Change confirmation from `requirements.md` and are not repeated here.)

## Steps

1. **A1.** Cycle Step 5 item 3 of the cycle skill says to leave out a flag that has no ids — done when the sentence reads, after "instead of `--show`": ", leaving out a flag that has no ids (with neither flag it records two empty lists)", the item is otherwise unchanged (a diff of the skill file shows that one clause), and it agrees with `lint-fixes --help` (the manual check above).
   Failures: none (wording only; the no-flag behaviour is already pinned by `lint_fixes_writes_the_fixes_record`).
   Trivial stakes: yes — one wording clause in a skill file; no test can catch it and no code changes.

2. **A2(b).** With no claims index and a completed `claims.json`, an entry re-reviewed after that run's day is counted — done when the new test `left_undone_claims_count_with_no_index_uses_the_claims_run_as_cutoff` passes in `uv run python tests/scripts/test_cycle_scope.py`, having been red first (run on HEAD it fails for the right reason: the claims line is absent where `f"{CLM}1 — {CLM_RAN}"` is expected), and the whole file is green after the fix.
   - Expected: the (b) notebook above, `--full` → `f"{CLM}1 — {CLM_RAN}"` (the re-reviewed `old-a`); the control notebook, the same but nothing re-reviewed → no claims line (covered, not over-counted).
   - Failures: no index and a *partial* `claims.json` → every entry counted with `not checked (the claims step ended partial; what it covered is unknown)` (only a completed result sets the cut-off; green on first run, it pins that the fix did not widen it); no index and no `claims.json` → every entry counted, as the existing `s4f` check says (unchanged).
   - Invariant: with an index the cut-off stays the index's written time (step 3's test).
   uses: `newest_step`, `uncovered`, `claims_scope`; the fix is the two lines in Implementation Decisions. New function: none.
   Trivial stakes: no

3. **A2(a) and the index rule.** The pre-existing behaviours the finding left unpinned get their own tests — done when `uv run python tests/scripts/test_cycle_scope.py` passes with two new tests green on first run: `left_undone_claims_count_with_an_index_but_no_claims_json_is_the_unindexed_plus_revised` (an index naming all but one entry, nothing revised, `--lint-only`: `f"{CLM}1 — {CLM_OFF}"`, where "every entry" would read 3) and `left_undone_claims_cutoff_is_the_index_time_whatever_claims_json_says` (an index written `D1`, `old-a` re-reviewed `D2`, a completed `claims.json` stamped `D3` listing `old-a`: `old-a` is counted, `--full`; a cut-off taken from the `claims.json` would cover it). Their bite is shown at step 7, not here (code that already exists is green on first run).
   - Invariant: the frozen `s4g` already tells 3 from 4 for the index-only count; the new test is the by-name pin the finding asked for.
   blocked by: 2 (the index-time test is written against the fixed code, so it pins the fix's index branch).
   Trivial stakes: no

4. **Docstring.** The `_run_state.py` docstring states the claims cases correctly — done when the two clauses of Implementation Decisions are in it, no other line of it changed, and `uv run python tests/scripts/test_cycle_scope.py` is still all green (its two docstring-pin tests included).
   Trivial stakes: yes — docstring wording only; the two frozen docstring-substring tests are run, and the behaviour is steps 2 and 3's.

5. **A3, the planted defects (red first).** The fixture test fails the three defects the writer's checks must catch — done when `uv run python tests/scripts/test_left_undone_fixture.py`, run against the current `check.py`, prints a FAIL line for each of: the first queue line's "—" changed to "-" in the report section (the section-equals-file check passes it today); the session writing `left-undone.txt` by `cp`, by `mv`, by `sed -i`, by `python -c` and by a PowerShell tool call; and prints PASS for the control plants (the old routes `Write`, `Edit`, `>`, `tee`, which fail the write check today) and for the plant-free A and B runs (each carrying the legitimate script call).
   - Expected: each route's plant (tool_calls route, on-disk file differing in one count, section copying it) → at least one `check()` result about the file or the section fails; the exit code is 1 on today's `check.py` because the new-route plants and the dash plant are not caught.
   - Failures (what must not happen): a plant-free run failing any check it passes today; a control route no longer failing.
   uses: `empty_session`, `compose_report`, `tamper_checks` pattern, `own`; new `session_write_plants`, `session_with`.
   Trivial stakes: no

6. **A3, the writer's checks.** The orchestrator briefs `eval-case-writer` (mode `replay`, brief in Implementation Decisions), saves its answer into `check.py` unchanged, then the session re-points the fixture test's check-name constants (`SECTION_EQUALS_FILE`, `NO_FOREIGN_QUEUE_LINE`, the `COMPOSED` prefixes and `NEEDS_SESSION` entries) at the names the writer used — done when `uv run python tests/scripts/test_left_undone_fixture.py` exits 0: every step-5 plant fails a check, the four old-route controls still fail, the three tampers still fail, case A and B plant-free runs pass, and `main()` reports no prefix that names no emitted check; and the orchestrator confirms the `check.py` diff is the writer's text and that the header at the old line 3148 no longer names a kind the file does not have.
   - Failures: a writer's answer that fails a plant-free run, or catches only some routes, goes back to the writer with the fixture's output (a replay), never patched by the session; its questions go to Mark.
   blocked by: 5 (the plants are the red).
   Trivial stakes: no

7. **Bite, by hand.** The three fixes and tests are shown to bite — done when a hand mutation pass (harness and result file in the artifact directory, the 240 harness `hand-mutation-lu.py.txt` as the pattern, mutants planted in a scratch copy and never the repo) shows each mutant killed by the named test: (M1) `cutoff = written or cutoff` → `cutoff = written` killed by step 2's test; (M2) `cutoff = found[0] if found else written` killed by step 3's second test; (M3) the claims scope taken as every entry (`scope = _all`) killed by step 3's first test (and by the frozen `s4g` as well, said in the result); (M4) a partial `claims.json` allowed to set the cut-off killed by step 2's partial check. Every survivor is explained or gets a test. A3's bite is step 5's red before step 6's save.
   blocked by: 2, 3.
   Trivial stakes: yes — runs and records evidence; adds no code to the product.

8. **Record.** The CHANGELOG gets one entry dated 2026-11-18 (A1's clause, A2's no-index count and the docstring, A3's stricter checks, each naming the finding) and `tests/skills/PENDING.md` gets a wiki-cycle row (A1 is a small wording change logged there per the README; A3's checks changed and the paid re-run's state, run or not run on Mark's answer) — done when both are read against steps 1 to 7 and name only what changed.
   Trivial stakes: yes — changelog and log wording only.

9. **Paid re-run, only on Mark's yes (requirements Decision 2).** The verbatim and old-run cases are run on both models against the new checks — done when `uv run python tests/skills/run_skill_test.py wiki-cycle --cases left-undone-section-is-the-file-line-for-line-with-nothing-added-or-reworded,report-rebuilt-from-old-run-without-left-undone-file-reads-not-checked-above-needs-you-and-creates-no-file` (about $6; 240's was $6.27) finishes with both cases passing on both models, its report path and cost recorded in `checkpoints.md`.
   - Failures: a model that writes "—" as "-" turns a case red: that is the check working, reported and not patched around; the session never edits a check to get green.
   - Declined (Mark says no): the step is not run, PENDING's row says "not run" and the checks stay unexercised against a live model, as the requirements' Decision 2 states.
   blocked by: 6, and Mark's go.
   Trivial stakes: yes — no code; a run and its record.
