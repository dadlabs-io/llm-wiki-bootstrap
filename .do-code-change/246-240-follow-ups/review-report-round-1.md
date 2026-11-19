# Review report, round 1: 246-240-follow-ups

Fixed point 047d868 (merge-base 047d868) .. working tree; `.do-code-change/` left out; no untracked files outside it. 8 commits, 8 changed files, about 390 changed lines (one part per axis). Lenses ran as `code-reviewer-lens`, unnamed, with `run_in_background: false`; both came back as launch notices and their reports were taken from their completion messages. No lens was retried.

## Standards

- [important] `tests/scripts/test_left_undone_fixture.py`, `session_write_plants` (PY9, R15): the route checks pass for the wrong reason.
  - The file is tampered before the routes run (`lu_file.write_text(original.replace(first, re.sub(r"(?<=: )\d+", ...` at about line 270). The loop then asserts `own("A", f"a check fails a session that wrote left-undone.txt by {name}", bool(hit), ...)`, where `caught()` accepts any failing check whose name matches `left.undone|section|queue line`.
  - The script-output check fails on every route, so a route the detector misses still passes.
  - Fix: run each route on the untampered file and assert that "the session did not write left-undone.txt itself" fails for it.
- [important] (writer's text) `tests/skills/wiki-cycle/check.py` `_lu_copy_checks` (about 3288) and `_check_left_undone_old_run` (about 3371-3382): existing kinds now grade differently.
  - The diff removes the dash mapping in `_lu_norm_line`. `tests/skills/README.md` says an existing kind is never changed.
  - Plan and requirements line 40 override this for the two named kinds; the finding is the repo-standard conflict, for a person to rule on.
  - Fix: get Mark's ruling that the override covers the old-run kind too, or return the stricter rule as a new kind.
- [important] (writer's text) `check.py:3198-3208`: the comment says a command "that only reads it, or reads it and writes something else, is not a hit". The pattern `\b(?:Set-Content|Add-Content|Out-File|Clear-Content|New-Item)\b[^\n;&|]*left-undone\.txt` matches `Add-Content -Path report.md -Value (Get-Content left-undone.txt)`, which is a read.
  - Fix: anchor the file to the write's destination argument.
- [important] `tests/skills/PENDING.md` 2026-11-18 row against `tests/skills/README.md`: "A case that passes on the old copy goes back to `eval-case-writer` (mode `replay`) ... it is not counted as proof". The row says none-answered "does not discriminate (Opus passes on the old text)".
  - The requester accepted the outcome and carded #247 (not a finding in itself). The finding is that the row records the change as proven while one case is not.
  - Fix: say in the row that none-answered is not proof, or replay it.
- [suggestion] (writer's text) `check.py:3396`: `_LF_CALL = re.compile(r"\blint-fixes\b")` also matches `lint-fixes.txt`, so `recording` counts a `cat .../lint-fixes.txt`. Fix: `r"\blint-fixes(?![\w.-])"`.
- [suggestion] (writer's text) G20/R1 `check.py` `_lu_script_output` (about 3277-3285): re-running `wiki-cycle-scope.py left-undone` also writes `left-undone-events.txt` (`scripts/_run_state.py:958`), and only `left-undone.txt` is restored. Fix: snapshot and restore the run folder, or name the side effect.
- [suggestion] (writer's text) S2: the shell-call test at `check.py:3229` repeats at `:3419`. Fix: one helper.
- [suggestion] (writer's text) S2: `drop = {"quick steps all wrote their pair", ...}` (about 3441) repeats the set in `_check_promote_setting` (about 539). Fix: a shared constant.
- [suggestion] (writer's text) S4/S2: `run_dir = ctx["notebook"] / "_inbox" / "reports" / cid[:10] / cid` (about 3299) rebuilds the path `_check_left_undone_verbatim` already holds. Fix: pass `run_dir` into `_lu_copy_checks`.
- [suggestion] (writer's text) R4: `_lu_model_wrote_file` nests for, if, if, for, if in the shell branch. Fix: extract `_lu_shell_write(cmd)` and use guard clauses.
- [suggestion] (writer's text) R9: `except json.JSONDecodeError: step = {}` (about 3447) reports a corrupt `lint-semantic.json` as absent. Fix: report the parse error.
- [suggestion] `tests/skills/PENDING.md` row: a measurement longer than a line, where the README says such a row uses the four headings (Compared with, n, Cost, What this does not show). Fix: put the measurement in a linked note under those headings.
- [nit] (writer's text) G25/F3/N1/G16/C1/PY3 in `check.py`:
  - `_lu_first_diff` windows `k - 25`, `k + 45`, `[:150]` and `_lf_bare_flags` `m.end() + 30` are bare numbers.
  - `show_line: bool = True` is a flag argument.
  - Parameters `a`, `b` carry labels only.
  - `_LU_WRITE_RES` is an eight-part regex table with no per-pattern comment.
  - The header `(task #246) ----------` carries a ticket.
  - `_lu_script_output` returns `(text, why)` with `None` first on failure.
  - Fix each: named constants, a label parameter, a comment per pattern, a result type.
- [nit] `tests/scripts/test_cycle_scope.py`: `wiki_cycle_skill_says_to_leave_out_a_flag_with_no_ids` (R13) asserts prose substrings, and `left_undone_claims_count_with_no_index_uses_the_claims_run_as_cutoff` (R12) holds three scenarios. Fix: split, or name the first as a text check.
- [nit] `tests/scripts/test_left_undone_fixture.py`: `session_with(step8_call(suite, rf))` repeats four times (S2). Fix: one helper.

Unverified:
- Whether the 11-18 cases were replayed or the change installed (PENDING says "Run on Mark's yes"; no run log was in the brief).
- Whether the saved `check.py` text equals the eval-case-writer's return.
- Whether the events-file rewrite changes content at grading time.
- Whether `ctx["started"]` is timezone-aware (`datetime.fromisoformat(ctx["started"])` in `_prepare_lint_fixes_record`).

Read depth: every changed line of every file was read; the lens marked `check.py` "in part" only for the surrounding file.

| File | Risk | Part | Standards | Spec | Change risk |
|---|---|---|---|---|---|
| `scripts/_run_state.py` | MEDIUM (business logic: the claims count) | 1 | in full | in full | not run |
| `skills/wiki-cycle/SKILL.md` | LOW (skill text) | 1 | in full | in full | not run |
| `CHANGELOG.md` | LOW | 1 | in full | in full | not run |
| `tests/scripts/test_cycle_scope.py` | LOW (tests) | 1 | in full | in full | not run |
| `tests/scripts/test_left_undone_fixture.py` | LOW (tests) | 1 | in full | in full | not run |
| `tests/skills/PENDING.md` | LOW | 1 | in full | in full | not run |
| `tests/skills/wiki-cycle/cases.json` | LOW (test data) | 1 | in full | in full | not run |
| `tests/skills/wiki-cycle/check.py` | LOW (test code, writer's text) | 1 | in full (changed lines; surrounding file in part) | in full | not run |

| Coverage (Standards) | Verdict | Search |
|---|---|---|
| S1 | found (nit) | `a`, `b`, `w`, `g` in `_lu_first_diff` |
| S2, S4 | found | shell-call test and drop-set repeats; `run_dir` rebuilt |
| G25, F3, R1, G20, C1, G16, PY3 | found (nit or suggestion) | see findings |
| R4, R9, R12, R13 | found | see findings |
| R15, PY9 | found | route checks in the fixture |
| repo rule "existing kind never changed", repo rule "red then green" | found | README quotes in the important findings |
| S3, S5-S11, S13/G30, S14, S15, G19, G28, G29, G31, G34 | clear | lens's reads of every added function |
| R2, R3, R7, R8, R10, G3, G33, G26, G2, G4, R26 | clear | each new function called inside the diff; G26 see Unverified |
| T1, T3, T5, T6, R14, T4 | clear | claims cut-off (4 tests), SKILL text (1), copy checks and two new cases |
| PY1, PY2, PY7, PY8, PY10, PY11 | clear | none added |
| C2, C3, C5, N2, N3, N5, N6 | clear | scanned the added lines |
| frozen tests | clear | additions only |
| S12, R11 | n/a | no subclass; no error path refactored |

Sections not pasted: Classes and modules, Concurrency, Refactoring and scope. Clear rows were backed by the lens's greps and reads.

Well built: the claims cut-off fix is one line with four tests across the index, no-index and partial states, and the lint-fixes check reads tool calls and the file, not the model's wording.

## Spec

- [important] (writer's text) `tests/skills/wiki-cycle/check.py:3203-3204`: the write detector misses routes the requirement names.
  - Intent, requirements line 43: "the write detector must catch every route by which the session itself produces `left-undone.txt`".
  - Implemented: the "copy or move into it" pattern lists `cp|mv|install|ln|rsync|Copy-Item|Move-Item|Rename-Item`. It has no `copy`, `move`, `ren` or `xcopy` aliases, and no `>|`.
  - Affected: a session that writes identical text with PowerShell `copy` passes. The script-output check catches only text that differs. Mark accepted only the variable-path case (checkpoints.md Step 6, "yes").
  - Fix: add the aliases and `>|`, through a replay by eval-case-writer, not a session edit.
- [suggestion] (writer's text) `check.py:3426` and `:3433`: an empty quoted value counts as a value.
  - Intent, requirement A1: the session "leaves out a flag that has no ids". `lint-fixes --applied "" --declined ""` passes the no-bare-flag check and the two-empty-lists check (`:3473`), though the flag was not left out.
  - Fix: count an empty quoted value as not left out; replay through the writer.
- [suggestion] `tests/scripts/test_left_undone_fixture.py:270-273`: each route plant also rewrites the on-disk file, so the script-output check fails for every route whatever the regex does.
  - Plan step 5 specified this design, so it is not a deviation. The fixture cannot show that `_LU_WRITE_RES` catches cp, mv, sed, python or PowerShell. Same root cause as the first Standards finding; reported on each axis separately.
  - Fix: run each route on the unmodified file and require a route-named failure.
- [suggestion] `CHANGELOG.md:16` ("the session writing `left-undone.txt` by any route fails") and `tests/skills/PENDING.md:28` ("every write route caught") overclaim against the first Spec finding and Mark's accepted limit. Fix: name the routes checked and the variable-path limit.
- [nit] `scripts/_run_state.py:116-117`: the plan pins "...since the index was written; every entry only when there is no index", and the code has a comma. Line 117 also runs past the docstring's wrap. Fix: use the pinned semicolon and rewrap.
- [nit] Plan drift, no defect:
  - `test_cycle_scope.py:2064` adds `old-b` at D1 (plan step 2 names only old-a), and `:2116` lists old-a and old-c in the claims.json scope.
  - `s3_indexed_nb` and `step8_call` are helpers the plan does not name; `tamper_checks` now uses `session_with(step8_call(...))`.
  - Fix: update the plan text or accept.

Unverified:
- "script tests 330/330" (`PENDING.md:28`): `hand-mutation-claims-result.json` shows 329/330 under mutants, so the suite has 330 checks. The unmutated pass is not recorded, and the diff adds 8 `check(` calls, so 318 + 8 = 326 does not reconcile with 330. One unmutated run settles it.
- Red-first runs for steps 1, 2 and 5, and step 5's "exit 1 on today's check.py": not in checkpoints.md.
- `check-freeze.py` and the six neighbouring suites: not run.
- `check.py` byte-identity to the writer's answer: asserted by checkpoints.md Step 6, not evidenced.
- Step 4's frozen docstring tests (`:1050`, `:1727`): the edit does not touch their windows; not run.
- The implementing session writing no check: checkpoints Step 6 claim only.

Checks made:
- The git pre-flight: `047d868` resolves, the merge-base is 047d868, the diff is non-empty (8 files), and no untracked file lies outside `.do-code-change/`.
- Spec plan step 2, the two pinned lines: `scripts/_run_state.py:554-555` is `scope, _all, _why, written = claims_scope(nb)` then `cutoff = written or cutoff`. The diff touches neither `claims_scope` nor `cmd_claims`.

Read depth: `in full` for all eight files (surrounding files in part).

| Coverage (Spec) | Verdict | Search |
|---|---|---|
| Plan 1 (A1 clause and test name) | clear | diff of SKILL.md item 3; Grep `leaving out`, `wiki_cycle_skill_says` |
| Plan 2 (A2(b) fix, test names, expected values) | clear | `_run_state.py:554-555`; Grep `claims_scope(`: 3 callers, `wiki-cycle-scope.py:143` discards `_written` |
| Plan 3 (index-rule tests) | clear | diff `:2085-2110`; M1-M5 results show the index tests killing mutants |
| Plan 4 (docstring, two clauses) | found (nit) | diff `_run_state.py:106-107, 116-117` |
| Plan 5 (planted defects) | found (suggestion) | diff `session_write_plants`; Grep `routes = {` |
| Plan 6 (writer's checks) | found (important) | Grep `left-undone-resumed` (none in check.py); Grep `\bcopy\b`, `2014` in check.py |
| Plan 7 (bite) | clear | `hand-mutation-claims-result.json`: M1 to M4 killed by the named tests |
| Plan 8 (record) | found (suggestion) | diff CHANGELOG.md:16, PENDING.md:28 |
| Plan 9(a) shape, 9(b) costs | clear | cases.json diff; `_check_lint_fixes_record`; $3.60 = 0.51+1.10+0.37+1.62 |
| Requirements Decisions 1-5 | clear | `claims_scope` unchanged; checkpoints Q1-Q3; `_lu_norm_line` has no dash mapping |
| Keep rows (claims with index, claims scope, header count) | clear | `cutoff = written or cutoff`; diff file list |
| Keep and Inv rows "old write routes fail", "paid checks fail as today" | found | via the plan 5 finding |
| Exclusions (other 240 findings, rows, lint-fixes script, A1 one sentence, no other case re-run, 240 archive) | clear | diff file list; single-line SKILL.md hunk; checkpoints Step 9 |
| Exclusion "implementing session writes no check" | unverified | checkpoints Step 6 claim only |
| Inv frozen tests unmodified, `git diff --stat` on excluded files | clear | additions-only hunk at `@@ -2045,6 +2045,80 @@`; diff file list |
| Inv suites green, plant-free fixtures pass | unverified | not run; checkpoints Step 6 "exit 0" only |

Well built: the A2 fix is exactly the two pinned lines, with a control notebook and a partial-claims check. The frozen tests are untouched, and the dash, copy and route checks are shaped as the requirement asks.

## Change risk

No high-risk file; the change-risk lens was not run. The file table above is the triage: `scripts/_run_state.py` is MEDIUM, every other file LOW.

needs-a-human: none (no auth, session, token or data-migration change; a spec resolved from requirements.md, plan.md and checkpoints.md).

## Summary

Standards: 14 findings (4 important, 7 suggestion, 3 nit). The worst is the route checks in `session_write_plants` passing for the wrong reason, which the Spec axis also raised from its side.

Spec: 6 findings (1 important, 3 suggestion, 2 nit). The worst is the write detector not covering literal alias routes (`copy`, `move`, `ren`, `xcopy`, `>|`) that requirements line 43 names.

Change risk: not run.

The two axes agree that the fixture's route plants cannot show the detector works, and that the CHANGELOG and PENDING text claims more than the checks prove. Both are worth acting on. Findings labelled "(writer's text)" go back to eval-case-writer (replay), not to the implementer.

VERDICT: Standards FINDINGS · Spec FINDINGS · Change risk NOT RUN · needs-a-human 0
