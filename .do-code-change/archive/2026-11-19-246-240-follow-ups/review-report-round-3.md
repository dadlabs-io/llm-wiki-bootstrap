# Review report, round 3 (focused): 246-240-follow-ups

Fixed point 047d868 (resolves). Focused round: the change under review is what fix round 2 moved, diffed from the round-2 review commit f2b243b to the working tree (`review-ledger.py changed`: CHANGELOG.md, tests/scripts/test_left_undone_fixture.py, tests/skills/PENDING.md, tests/skills/wiki-cycle/check.py), about 300 changed lines, one part per axis, no untracked files outside `.do-code-change/`. Files the round-2 review read and the fix left alone (`scripts/_run_state.py`, `skills/wiki-cycle/SKILL.md`, `tests/scripts/test_cycle_scope.py`, `tests/skills/wiki-cycle/cases.json`) are out of this round; nothing was raised in them. Prescan ran clean (review ids, round numbers, dates, width skipped). Lenses ran as `code-reviewer-lens`, unnamed, `run_in_background: false`; both came back as launch notices and their reports were taken from their completion messages; no retry. Mark's ruling (shell writes are not detected by design; two exact checks) was passed to both lenses and is raised nowhere. Findings in `check.py` are the eval-case-writer's text and are labelled "(writer's text)".

## Standards

- [important] T1, T3, T5 (writer's text for check.py:3207-3211; the gap is in `tests/scripts/test_left_undone_fixture.py:290-295`): the new `_lu_model_wrote_file` branches have no case. The fixture plants only `Write` and `Edit` on `file_path` (`tool = {"Write": ...`), while its docstring and CHANGELOG.md:16 promise "a Write, Edit, MultiEdit or NotebookEdit".
  - MultiEdit, NotebookEdit (`notebook_path`), the `path` key, `edits[].file_path`, a backslash path, the `_LU_READ_TOOLS` skip (a Read of the file must pass), and the old-run kind's call at check.py:3361 are not exercised.
  - Fix: one plant per route that must fail the write check, a Read plant on the target that must pass, and one old-run plant.
- [important] C2 (writer's text) `check.py:3285-3286` against `CHANGELOG.md:16` and `check.py:3268-3269`: the copy check compares `[l.rstrip() for l in ftext.splitlines()]`, so a trailing-space edit passes, while CHANGELOG says "any changed text fails whatever route wrote it" and the `_lu_copy_checks` docstring says "no route by the session can make the copy check pass against a file the session wrote".
  - Fix: compare unstripped lines, or word both as "any change other than trailing spaces"; add a plant for a trailing-space edit.
- [suggestion] C2 (writer's text) `check.py:3275`, `:3281`: the names "the session did not write left-undone.txt itself (one script writes it; the model composes no count)" and "(not changed or made by the session)" are now false for an identical shell rewrite, which passes both. Fix: rename to what is checked (no Write, Edit, MultiEdit or NotebookEdit aimed at the file; the text equals the script's own output), then update `WROTE_ITSELF` (fixture:72) and `NEEDS_SESSION` (fixture:49), which match on the name.
- [suggestion] S2 (writer's text) `check.py:3209-3212`: the target normalisation (`file_path`, `path`, `notebook_path`, backslash to slash) repeats `tests/skills/task-list/check.py:386` and `tests/skills/dream/check.py:402`. Fix: one helper in `tests/skills/_trajectory.py`. A judgement call: the three checks ask different questions.
- [suggestion] PY9 `tests/scripts/test_left_undone_fixture.py:326-330`: the events-file plant passes whenever the script does not rewrite the events file, so the restore is not shown to bite. The Spec lens traced that the fixture's case A is a `--full` run, so `_run_state.py:957-959` does rewrite it; the test still does not assert it. The deletion branch (`check.py:3260-3261`, files the script made) has no plant. Fix: assert the bytes changed during the run (wrap `suite._script`), and plant a new file that must be gone after `check()`.
- [suggestion] PY9 `tests/scripts/test_left_undone_fixture.py:318-320`: the 14-route loop repeats one assertion; the script-output check reads only the disk, so the route names change labels, not outcomes. Fix: keep one case and say in the docstring that routes do not change this verdict, or keep the labels for readability.
- [suggestion] `tests/skills/PENDING.md:28`: "Run on Mark's yes: results in ..." sits in the "Why it was not run" column and "Next full wiki-cycle run checks these" says the change is unrun, so the row reads as both run and pending; it also omits the Opus-only caveat on none-answered that CHANGELOG.md:16 carries. Fix: say what has not been run and state the caveat.
- [nit] `tests/scripts/test_left_undone_fixture.py:254-256` against `:308`: the docstring says "the same shell routes with the text identical"; the loop runs three of the 14. Fix: "three shell routes".
- [nit] S13 `tests/scripts/test_left_undone_fixture.py:250`: `session_write_plants` is about 90 lines in six phases. Fix: one function per phase, or keep the docstring's phase list in step with the code.

Unverified:
- `.do-code-change/archive/2026-11-18-246-240-follow-ups/` (the PENDING pointer) does not exist yet; earlier runs were archived under that date-slug pattern at finish. Step 9's results are in the live `.do-code-change/246-240-follow-ups/checkpoints.md:27-33`.
- `check.py:3210` reads `edits[].file_path`; whether a real MultiEdit call carries that key was not checkable offline.
- `tests/skills/.results/wiki-cycle/20261118-195236/report.md` was not opened (Glob timed out).
- The fixture and `test_cycle_scope.py` were not run by this review (checkpoints.md gives exit 0 and 330/330).

Checks made:
- Round-2 Standards findings confirmed fixed by the reviewer's own reads: the detector, its reader and its regexes are gone (Grep for `_LU_FILE`, `_lu_ps_writes_file`, `_LU_WRITE_RES`, `_LU_PS_`, `_LU_COPY_VERBS`, `caught(` over the repo outside `.do-code-change/` found nothing), so the read-counted-as-write, literal-route-missed, nesting and `range(4)`/`range(5)` findings no longer have code to stand on; the dash plant is judged by `named(..., SECTION_EQUALS_FILE)`; `NEEDS_AWAITING = ` spacing and the blank line before `def named` are fixed; the `_lu_script_output` docstring says a made directory is not removed and matches the body.
- The PENDING row is no longer a measurement (README format satisfied).
- The events-file plant does bite on the restore: `scripts/_run_state.py:957-959` writes `left-undone-events.txt` on a non-`--report-only` run, and the check runs the script without that flag.
- Every function and constant the diff adds has a caller (R26): `_lu_model_wrote_file` at check.py:3274 and :3361, `session_write_plants` at fixture:394.

| File | Risk | Part | Standards | Spec | Change risk |
|---|---|---|---|---|---|
| `tests/skills/wiki-cycle/check.py` | LOW (test code, writer's text) | 1 | in part: 3180-3309 (every changed line) | in part: 2554-2555, 2732-2745, 3150-3374 | not run |
| `tests/scripts/test_left_undone_fixture.py` | LOW (tests) | 1 | in full | in full | not run |
| `tests/skills/PENDING.md` | LOW | 1 | in part: 1-89 (changed row read) | in part: 1-89 | not run |
| `CHANGELOG.md` | LOW | 1 | in part: 1-80 (changed block) | in part: 13-18 | not run |

Every changed line was read by each lens; the unread parts are context only.

| Coverage (Standards) | Verdict | Search |
|---|---|---|
| S1, S3-S12, G25, F3, C5, C1, C3, R2 | clear | lens reads of every added name, literal and comment |
| S2 / G5 | found | Grep `file_path\|notebook_path` in tests/ |
| R1, N7 / G20 | clear | `_lu_script_output` docstring announces the run and restore |
| R26 | clear | Grep of call sites, see Checks made |
| C2 | found | check.py:3275, 3281, 3268-3269; fixture:255 |
| S13 / G30 | found | fixture:250 |
| G34, S14, G19, G28, G29, R4, G31, G16, S15 | clear | read; max nesting three, guarded; no hits for removed names |
| R7-R11, G4 | clear | `finally` at check.py:3259-3264 covers every return |
| T1, T3, T5, T6 | found | fixture:290-295 |
| R12-R15, T4 | clear | each verdict names one concept; writes confined to the sandbox run folder and restored in `finally`; no skip |
| PY9 | found | events plant and the 14-route loop |
| PY1-PY8, PY10, PY11 | clear / n/a | none added; no async code; `difflib` is stdlib |
| documented standard: tests/skills/README.md PENDING format | clear | row read against it |
| Sections not pasted | n/a | Names, Classes and modules, Boundary conditions, Concurrency, Refactoring and scope |

Well built: `_lu_model_wrote_file` is short and its docstring states the ruling; the dash plant is judged by name, the restores run in `finally`, and the fixture's cleanup is in one place.

## Spec

- [important] `CHANGELOG.md:16` names the wrong cause of Sonnet's none-answered old-copy failure.
  - Intent: the brief asked for "Sonnet's old-copy failure was the step JSON contract"; that wording is copied from `checkpoints.md:30` ("sonnet old FAIL (no permission denials; step JSON contract: NOT the record checks)").
  - Implemented: `tests/skills/.results/wiki-cycle/20261118-195235-red-green-047d868/report.md:29` (the run report the reviewer read) says "old failed: no permission denials (read-guard and the blocked Skill tool counted apart); every step JSON follows the contract (fields, cycle_id)". CHANGELOG.md:16 says the opposite.
  - Affected: a reader of CHANGELOG who wants to know why the none-answered case does not discriminate.
  - Fix: say Sonnet's old-copy failure was "no permission denials" (read-guard and the blocked Skill tool counted apart), and correct `checkpoints.md:30` the same way, unless a fresh read of the old-copy report shows the step-JSON cause.
- [suggestion] `CHANGELOG.md:16` omits that both `lint-fixes-record` cases fail on Opus's new copy while it calls none-answered "kept as a regression case".
  - Intent: `checkpoints.md:30-31`: Opus "new FAIL (1)" in both cases, a sandbox Write refused by the edit gate; `report.md:29-30` "fails on the new copy".
  - Fix: state that both fail on Opus's new copy on that denial, parked under #247.
- [suggestion] (writer's text) `check.py:3281` and `:3268-3269`: the check name "(not changed or made by the session)" and the docstring "no route by the session can make the copy check pass against a file the session wrote" contradict `requirements.md:43` ("a session that rewrites the file with text identical to the script's output by a shell route is accepted"). Fix: name it "(the text equals the script's own output)" and say an identical rewrite by any route passes.
- [suggestion] The fixture does not plant the other Write-type routes the ruling names, nor the old-run write check: `test_left_undone_fixture.py:290-291` plants Write and Edit only; check.py:3361 has no plant (only the verbatim kind gets `session_write_plants`, line 394). Fix: MultiEdit (`edits[0].file_path`), NotebookEdit (`notebook_path`), a backslash Write and an old-run plant.
- [nit] (writer's text) `check.py:3285-3286`: `[l.rstrip() ...]` lets trailing-space or final-newline changes pass the script-output check, though `requirements.md:43` says "the file must equal the script's own output". Changed words and counts still fail. Fix: compare without `rstrip`, both sides read the same way.
- [nit] (writer's text) `check.py:3199-3200`, `:3211`: the docstring says "any other non-read tool whose file_path ... ends in left-undone.txt", and `endswith("left-undone.txt")` also matches a name such as `copy-of-left-undone.txt`; the ruling names four tools aimed at the file. Fix: name the four tools; match the run folder's own file name.
- [nit] `tests/skills/PENDING.md:28`: a result pointer sits in the "Why it was not run" column. Fix: put the reason there ("next full run checks these; paid results in ...").

Unverified:
- The PENDING pointer `.do-code-change/archive/2026-11-18-246-240-follow-ups/checkpoints.md` does not exist yet; it resolves when the run is archived.
- `tests/skills/.results/wiki-cycle/20261118-195236/report.md` was not opened.
- Spec-side, not raised (files not moved this round): `requirements.md:56` and `plan.md:70` still say a `>` or `tee` write must fail; `requirements.md:43` supersedes that and the fixture follows line 43.

Checks made:
- Round-2 Spec findings: the shell-detector findings (a read counted as a write; literal routes missed) are moot by the ruling and the code now matches it: `check.py:3198-3213` reads tool targets only, and Grep for `_lu_model_wrote_file(` hits only `_lu_copy_checks` (3274) and the old-run kind (3361), so both callers are served.
- The none-answered "Opus only" part of round-2 spec-3 is fixed in CHANGELOG.md and PENDING.md; the cause given for Sonnet is the first finding.
- A session-written differing file cannot pass the copy check: `_fb_read` (check.py:2554-2555) is a plain read, the script-output check at 3285-3289 compares it with the script's re-run output; only trailing whitespace passes (the nit above).
- Dash strictness unchanged (`_lu_norm_line` has no dash mapping; Grep of the dash characters finds only docstrings); a failed copy check names the first differing line (`_lu_first_diff`, check.py:3226-3240); no `left-undone-resumed` in `check.py`.
- The events plant is real (case A is `--full`, `_run_state.py:941, 957-959`); the dash plant is non-vacuous (`dash_line` is read from the file); the identical-text Bash plants pass because command text is not read, which is the ruling.

| Coverage (Spec) | Verdict | Search |
|---|---|---|
| a detector matches the ruling | clear | `check.py:3198-3213`; Grep for removed names, no hits; two callers |
| b none-answered wording | found | CHANGELOG.md:16 against checkpoints.md:30 and report.md:29-30 |
| c fixture shows each claim | found | Write-type routes and old-run unplanted; events and dash plants confirmed |
| d requirement line 43: a differing file cannot pass | clear | `_fb_read`, check.py:3285-3289; trailing whitespace is the nit |
| e PENDING pointer | found | live checkpoints.md:27-33 holds Step 9; archive path does not exist yet |
| ruling and the old-run write check | found | check.py:3361 has no plant |
| dash strictness; first differing line named | clear | Grep of dash characters; `_lu_first_diff` |

Well built: the detector is now the ruling's two checks, both callers are wired, and the dash mapping is gone from `_lu_norm_line`.

## Change risk

No high-risk file; the change-risk lens was not run. The file table above is the triage: every moved file is LOW (test code, tests, release notes, a docs table).

needs-a-human: none (no auth, session, token or data-migration change; spec resolved from requirements.md, plan.md and checkpoints.md).

## Summary

Standards: 8 findings (2 important, 4 suggestion, 2 nit). The worst: the new write-detector branches have no fixture case beyond Write and Edit, and the copy check's `rstrip` makes the documented "any changed text fails" broader than the code.

Spec: 7 findings (1 important, 3 suggestion, 3 nit). The worst: CHANGELOG.md:16 gives the wrong cause for Sonnet's old-copy failure, contradicted by the run report.

Change risk: not run.

The axes agree on two gaps: the unplanted MultiEdit, NotebookEdit and old-run routes, and the `rstrip` and stale check names in `check.py`. Round-2 findings confirmed fixed: the detector findings (removed), PENDING row format, the dash plant, the nits, the none-answered "Opus only" wording (its Sonnet cause is still wrong). Findings marked "(writer's text)" go back to eval-case-writer as a replay; the rest are the developer's. Both axes are worth acting on.

VERDICT: Standards FINDINGS · Spec FINDINGS · Change risk NOT RUN · needs-a-human 0
