# Review report, round 3 (focused), 240-loud-backlogs

Change under review: the files moved since round 2 (reviewed at 6954da3), the diff 6954da3 -> HEAD c66f855, `.do-code-change/` excluded, plus the sibling sites of the addressed findings. Fixed point `6f23c8c` (`git rev-parse` resolves; the diff is non-empty; 6 files, 189 added and 25 removed lines, so one part per axis). Addressed in round 2: standards-38 and spec-23, standards-40, standards-41, spec-19, spec-20, standards-42 and spec-22, standards-43. The other round-2 items are open by decision and were not re-raised. Spec source: `plan.md` (revision 8), `requirements.md`, `doubt-log.md`, `checkpoints.md` from "Review round 2", and the paid report `tests/skills/.results/wiki-cycle/20261118-154943-red-green-b7401bb/report.md`. Prescan passed (clean) and the lenses were told so. Two lenses (Standards, Spec), both `code-reviewer-lens`, foreground, unnamed, `run_in_background: false` written out; each came back as a launch notice and its report was taken from its hand-back message and completion notification. Default model tier. No retry was needed. Findings labelled "(writer's text)" are in `check.py` or `cases.json` kinds `left-undone-verbatim` and `left-undone-old-run`, which are eval-case-writer's text saved unchanged: the fix goes back to the writer, not to the editing session.

## Standards

- [important] PY11 `tests/scripts/test_left_undone_fixture.py:185`: the composer's own check prints as proof.
    Quote: `own(label, "compose_report writes 'Nothing.' when the file has no semantic line", tail == ["Nothing."], tail)`. It grades the test's own composer, but its name misses the COMPOSED prefix "compose_report words" (line 182 matches), so it prints a plain PASS. Sibling of standards-42. Fix: rename it to start "compose_report words ..." or add "compose_report writes" to COMPOSED.
- [important] C2 `tests/scripts/test_left_undone_fixture.py:56-57`: the new COMPOSED comment is wrong both ways.
    It says the section checks "pass by construction in grade() and bite only in tamper_checks". "the report has a Left undone section" (check.py:3076) and "Left undone is the second-to-last section" (check.py:3052, via `_lu_position`) pass by construction and print plain PASS because neither is in COMPOSED, while "Left undone line: ..." (check.py:3105) reads the script's own wording and can fail in grade(). Fix: add the composed names to COMPOSED and reword the comment to name which checks grade script output.
- [suggestion] PY9 (writer's text) `tests/skills/wiki-cycle/check.py:3198-3200`: the write detector misses routes.
    Quote: `elif c["name"] == "Bash" and re.search(r"(?:>>?|\btee\b(?:\s+-a)?)...left-undone\.txt", ...)`. It backs "the session did not write left-undone.txt itself" (:3211) and the old-run check (:3279) but misses `cp`, `mv`, `sed -i` and `python -c "open('left-undone.txt','w')"`; a model-written file would then make "the section's lines are the file's lines" pass against the model's own file. Fix: widen the pattern, or add a positive check that a call ran `wiki-cycle-scope.py ... left-undone`, or compare the file with the script's own output.
- [suggestion] R9 `scripts/_run_state.py:426`: the re-raised error carries no path.
    Quote: `raise  # an undecodable README is a read error, though UnicodeDecodeError is a ValueError`. The error gives a byte offset but not the README path; callers at :447 and :610 add none in their windows. Fix: re-raise with the path (for example `raise OSError(f"{readme}: not UTF-8: {e}") from e`) and update the test at test_cycle_scope.py:1086-1092, which catches UnicodeDecodeError.
- [suggestion] R3 `scripts/_run_state.py:676` (`step_data`: `except (OSError, ValueError): return {}`) and `:400` (`step_status`: `return "unreadable"`): sibling of standards-38.
    An undecodable file now raises for the README (:426) but is classed as `{}` or "unreadable" for step files. Both docstrings are truthful. Fix: pick one classification for undecodable files and state it in each docstring.
- [suggestion] S14/S15 (writer's text) `check.py` `_lu_copy_checks(add, ctx: dict, run: dict, rtext: str, ftext: str)`: `ctx` is never used in the body. Fix: drop the parameter and its argument.
- [suggestion] S2 (writer's text) `check.py:3030` `_lu_section` and `_lu_section_lines`: `re.search(r"^##\s+([^\n]*left undone[^\n]*)\n(.*?)(?=^##\s|\Z)", ...)` repeats `_lu_section`'s regex. Fix: `_lu_section_lines` calls `_lu_section`.
- [suggestion] C2/R3 (writer's text) `check.py:3148`: the header names `"left-undone-resumed"`, a kind `check()` never dispatches (dispatch at :3726 and :3728 uses `left-undone-verbatim` and `left-undone-old-run`). Fix: correct the header.
- [suggestion] PY9 (writer's text) `_lu_report_text` in check.py: the fallback `sorted(run_dir.glob("*report*.md"))` can grade a different file as the report.
    "the report never says 'Left undone: nothing'" (check.py:3280) passes on empty text when no report exists; the section check still fails, so the case stays red. Fix: drop the fallback and skip the empty-text check.
- [suggestion] C2 `tests/scripts/test_left_undone_fixture.py:16-19`: "the two checks that read them (names in COMPOSED) cannot fail here" and "the Left undone section check is shown to fail a tampered report" are stale; COMPOSED now has seven prefixes and `tamper_checks` runs three checks. Fix: update the docstring.
- [suggestion] T5 `tests/scripts/test_left_undone_fixture.py:188-211` (`tamper_checks`): the variants are invented, reworded and dropped lines only.
    The `_lu_norm_line` docstring promises that reordered and joined or split lines are caught, and no variant shows allowed formatting still passes. PENDING says the criterion "is shown by ... the unpaid fixture's tampered reports". Fix: add a reorder variant and a formatting-only variant that must pass.
- [nit] PY9 `tests/scripts/test_left_undone_fixture.py:52`: `"left-undone-verbatim": (..., "triage ran: one log row")`. check.py emits that check only for ingest-only and triage (check.py:3385), so the "dropped by the branch" entry is vacuous here. Fix: remove the entry.
- [nit] `tests/skills/PENDING.md` (the added 2026-11-17 row): "keeping the first wording) the no-file `--brief` line and the standalone-report Left undone line" lost its "and", so two list items run together. Fix: restore "and".

Unverified:

- PENDING "`test_cycle_scope.py` 318/318 (measured 2026-11-18)": the diff adds one `check()` (test_cycle_scope.py:1091) and does not explain 302 to 318; no run in a review. Settle: run the file or read the saved run.
- PENDING "`left-undone-planted`'s check is the one both 11-17 runs graded" against the removal of two hand-written checks from that function: whether the 11-17 runs graded text that held them. Settle: `git log -p` on check.py for those lines against the 11-17 run folders.
- A PowerShell write into left-undone.txt is not caught since the detector reads only Bash; whether a sandbox session has or uses a PowerShell tool is not shown. Settle: a run transcript's tool names.
- Callers of `bucket_ticket_lines` and `ticket_marked_sources` outside the 3-line windows were not read. Settle: grep both names for try blocks.

Checks made:
  - standards-38/spec-23 fix: `except UnicodeDecodeError: raise` sits before `except parse_errors:` (`_run_state.py:425-428`), the new test bytes fail UTF-8 before any yaml runs, and the docstring at :414-416 is truthful.
  - standards-40: the diff removes only the two `add(...)` calls, their comment, and `lu_file`, `file_lines` and `section_lines`; `run_dir` (check.py:3064) and `_lu_lines` (:3080) are still used.
  - standards-42: the COMPOSED prefixes match the check names they point to (check.py:3109, 3116, 3142, 3145, 3215, 3219); the two findings above are the siblings it missed.
  - standards-43: the exact check is at test_cycle_scope.py:1881; a grep of tests/ and check.py for `startswith("Left undone: ")` and `endswith(" queue(s)")` finds no other.

| Row | Verdict | Search or reason |
|---|---|---|
| S1 Mysterious Name N1 | clear | new names read in context |
| S2 Duplicated Code G5 | found | `_lu_section` vs `_lu_section_lines` |
| S3 to S12 (Feature Envy, Data Clumps, Primitive Obsession, Repeated Switches, Shotgun Surgery, Divergent Change, Speculative Generality, Message Chains, Middle Man, Refused Bequest) | clear | diff read; one new elif per kind in the existing dispatch |
| G25 Magic numbers | clear | "4 queue(s)" is an expected value |
| F3 Flag Argument | clear | no mode or bool parameter added |
| R1 Answers and mutates | clear | `_lu_*` return values read |
| N7 Hidden Side Effect | clear | writes are in prepare_/check functions |
| C5 Commented-out Code | clear | added lines read |
| R26 New code nothing uses | clear | each new name read in a call or dispatch line |
| Comments C1, C3, R2 | clear | "task #240" tags match the existing precedent (check.py:3350); no TODO |
| Comments C2 | found | fixture:16-19, :56-57; check.py:3148 |
| Names N2, N3, N5, N6 | clear | new names read |
| Names R3 | found | step_data/step_status vs README; "left-undone-resumed" |
| Functions S13, G34, G19, G28, G29, R4, G31, G16 | clear | new functions read; nesting at most 2 |
| Functions S14, S15 | found | unused `ctx` in `_lu_copy_checks` |
| Error handling R7, R8, G4, R10, R11 | clear | the new except re-raises; step_data is pre-existing (R3 above) |
| Error handling R9 | found | `_run_state.py:426` |
| Tests T1, T3, T6, R12, R13, R14, R15, T4 | clear | README-bytes case sits beside the four bad-README cases; header check tightened to exact (test_cycle_scope.py:1881); no skip added |
| Tests T5 | found | tamper set, fixture:188-211 |
| Python PY1, PY2, PY3, PY7, PY8, PY10 | clear | diff read; plain functions as the file uses |
| Python PY9 | found | write detector; DROPPED entry; report fallback |
| Python PY11 | found | fixture:185 |
| Classes/modules, Boundary conditions, Concurrency, Refactoring | n/a | the diff does not meet their paste-when lines |
| Repo convention (tests/skills/README.md "Who writes the cases") | clear | the two earlier hand-written checks are removed; the new kinds are labelled writer's text and the editing session's edits are confined to `_run_state.py`, the two test files and PENDING |

Well built: the README fix and its test are paired, the removal left no residue, and the header-count check is now exact.

## Spec

- [important] S1 `scripts/_run_state.py:425-426`: plan step 3 still promises the default for a bad README, but the code now raises for a non-UTF-8 one.
    Intent, plan.md:272: "an unparseable intake README falls to `buckets()`'s one-bucket default (its existing behaviour) without a crash". Code: `except UnicodeDecodeError:` / `raise  # an undecodable README is a read error, though UnicodeDecodeError is a ValueError`, over `scripts/wiki-triage.py:129` `read_text(encoding="utf-8")`. Affected: cycle Step 8 and `--report-only` on any notebook whose intake README is not UTF-8; the command exits with a traceback (`wiki-cycle-scope.py:509-531` has no try around dispatch), writes no file, and the report reads the not-checked state. The invariant "A false line is never written" holds, and the test bytes do reach the read error. The defect is that the ruling lives only in a code comment: plan step 3 and checkpoints 196-215 do not record it, and "unparseable" is not defined to cover "undecodable". Fix: amend the plan step 3 Failures bullet (a README whose frontmatter does not parse falls to the default; one that is not UTF-8 raises, exits non-zero, writes no file) and record the ruling in checkpoints; or, if the default is wanted, remove the `raise` and the new test case.
- [suggestion] S2/S7 `tests/skills/wiki-cycle/check.py:3268-3288` (`_check_left_undone_old_run`) and the PENDING row: the old-run case does not grade the Numbers row's `not checked` state.
    Intent, plan.md:83: "With no `left-undone.txt` in the run folder there is no N to copy, so Needs you keeps today's generic line ... with no count"; Decisions needed 11: the Numbers row is "`not checked` when there is no file". The branch has no Numbers or Needs-you check; the row's "not shown by any case" list names the generic line but omits the Numbers `not checked` state. Fix: add the Numbers-row check to the old-run branch (writer's text), or add that state to the row's not-shown list.
- [suggestion] S6 (writer's text) `check.py:3193-3204` (`_lu_model_wrote_file`): it sees only Write, Edit and Bash redirect or tee.
    In the verbatim kind the only file test is "left-undone.txt is in the run folder" (check.py:3229), so a model-written file lets "the section's lines are the file's lines" (:3215) pass against the model's own file (`python -c open(...)`, `cp`, a PowerShell tool). Fix: a positive check that a call ran `wiki-cycle-scope.py ... left-undone`, or compare the file with the script's own output. Same root as the Standards PY9 finding above.
- [suggestion] S3 `tests/skills/wiki-cycle/check.py:3052, 3076, 3138, 3236, 3274, 3081` and `tests/scripts/test_left_undone_fixture.py:185`: checks the composer satisfies by construction print as plain PASS.
    The fixture's own rule (docstring 16-19, 54-61) says such passes read "PASS (composed)". Affected: "Left undone is the second-to-last section", "the report has a Left undone section", "the section does not read 'Left undone: nothing'", and the `compose_report writes 'Nothing.'` check, which does not match the `"compose_report words"` prefix. Fix: add these prefixes to COMPOSED and rename the fixture:185 text to "compose_report words ...". Same root as the two Standards PY11 and C2 findings above.
- [nit] (writer's text) `check.py:3148`: the header names `left-undone-resumed`, a kind that does not exist (checkpoints 207-210: held, not saved). Fix: name `left-undone-verbatim` / `left-undone-old-run`.
- [nit] (writer's text) `_lu_norm_line` (check.py:3150-3163): it maps em and en dashes to hyphens, so a section that changes "—" to "-" passes "word for word". Fix: drop the mapping, or say in the plan that dash changes are allowed.
- [nit] `tests/scripts/test_left_undone_fixture.py:2, 9-14`: the docstring describes "two Left undone cases" (A and B); the verbatim kind is now graded in the same test and the old-run kind is not run by the fixture at all (checkpoints 210: scratch smoke only). Fix: say so.

Unverified:

- "318/318" for `test_cycle_scope.py`, the four neighbouring suites and the fixture being green after this round's edits. Settle: run `tests/scripts/test_cycle_scope.py` and `test_left_undone_fixture.py` (the fixture needs qmd).
- "Red then green ... on both models" for the two 11-17 cases (A planted, B clean) and the 11-17 run folders `193036` and `222534`: those reports were not read by the lens. Settle: read them.
- "left-undone-planted's check is the one both 11-17 runs graded" and "check.py restored to 1913d55". Settle: `git diff 1913d55 HEAD -- tests/skills/wiki-cycle/check.py`, limited to the planted function and its prepare function.
- Red-green exit code 0 for run 20261118-154943: the report does not print it. Settle: the run's console output.
- Whether run 20261118-154943 graded HEAD's check.py and skill text: the report says "skill from the working tree" and records no commit for check.py.

Checks made:
  - Step 7's two new cases against the paid report: both PASS on sonnet and opus, and both red on the old copy for the stated reasons (the report's "Red then green" table).
  - Plan step 7's section-equals-file criterion is carried by the verbatim kind (`_lu_copy_checks`, check.py:3206-3219) after the hand-written checks were removed from `_check_left_undone_planted`.
  - The header pin `Left undone: 4 queue(s)` derived from the s6h fixture's queue lines (`_run_state.py:362-378, 515-560, 903-958`; test lines 1871-1883): matches.
  - Invariants: the six `diff --git` headers read; none under `framework-docs/` or `scripts/wiki-lint-mechanical.py`.
  - Sibling search for `.buckets(` in scripts/: only `_run_state.py:424`.

| Spec item | Verdict | Search or reading |
|---|---|---|
| S1 spec-23 undecodable README raises | found | wiki-triage.py:129, _run_state.py:413-428, test_cycle_scope.py:1086-1092; grep `.buckets(` |
| S2 spec-19/20 PENDING row truthful | found (omission only) | row read in full; check.py:3116 is the only Numbers check |
| S3 spec-22 fixture composed labels and wiring | found | COMPOSED prefixes matched to check names (clear); case_of, DROPPED, NEEDS_SESSION wiring read (clear) |
| S4 standards-40 removal clean; criterion carried | clear | check.py:3056-3118 read after the diff |
| S5 header pin and siblings | clear | derivation above; grep `queue(s)` in the test file |
| S6 verbatim case grades "equal the file" | found | check.py:3206-3279 read |
| S7 old-run case grades the third state | found | wiki-report SKILL.md:281-286, 317; plan.md:13, 83 |
| S8 plan step 7 red then green on both models | found (A and B rest on unread 11-17 reports) | 20261118 report: verbatim and old-run PASS on both, old copy red |
| S9 invariants | clear | six diff headers read |

Well built: the UnicodeDecodeError test uses bytes that fail UTF-8 before any yaml runs, so it proves the read-error path, and the verbatim check is tampered three ways that each must fail.

## Change risk

No file is HIGH, so the lens was not run. Triage from the diff alone (no auth, authz, sessions or tokens, crypto, payments, external call, data migration or removed validation; the two added lines in `_run_state.py` make one read error surface instead of being swallowed, which is business logic, MEDIUM, and not a removed check).

| File | Risk | Why | Part | Standards | Spec | Change risk |
|---|---|---|---|---|---|---|
| `scripts/_run_state.py` | MEDIUM | business logic: which read error surfaces | 1 | in part (380-430, 664-680, callers) | in part (362-485, 515-560, 600-615, 700-745, 903-958; the hunk in full) | not run |
| `tests/scripts/test_cycle_scope.py` | LOW | tests | 1 | in part (the changed hunks) | in part (the changed hunks and neighbours) | not run |
| `tests/scripts/test_left_undone_fixture.py` | LOW | tests | 1 | in full | in full | not run |
| `tests/skills/PENDING.md` | LOW | docs | 1 | in part (the changed row, in full) | in part (the changed row, in full) | not run |
| `tests/skills/wiki-cycle/cases.json` | LOW | tests | 1 | in part (the two added lines) | in part (the two added lines) | not run |
| `tests/skills/wiki-cycle/check.py` | LOW | tests | 1 | in part (the whole delta plus 2552, 2897-2986, 3027-3151, 3700-3740) | in part (the whole delta, 823-829, 3027-3291) | not run |

Every changed line of the round was read by both lenses; files named "in part" are read by their changed hunks plus context, so no retry was spawned. Out of the round (reviewed in earlier rounds and not moved since 6954da3): every other file of the change, among them `scripts/wiki-cycle-scope.py`, `scripts/_cycle_common.py`, `scripts/wiki-triage.py`, the skill and usage pages and CHANGELOG; nothing new is raised in them.

needs-a-human: none (0). No finding touches auth, authz, tokens or sessions (the "session" in the code is the cycle's session buckets) or a production-data migration. A spec resolved, so there is no no-spec line.

Summary. Standards: 12 findings (2 important, 8 suggestion, 2 nit); worst: the composed-label gaps in the fixture (the `compose_report writes 'Nothing.'` check printing a plain PASS, and the COMPOSED comment that is wrong both ways); 5 of the 12 are marked writer's text (PY9 write detector, unused `ctx`, duplicated section regex, the stale `left-undone-resumed` header, the report-file fallback). Spec: 7 findings (1 important, 3 suggestion, 3 nit); worst: the non-UTF-8 README now raises, which plan step 3 does not record; 4 of the 7 touch the writer's text. The axes point the same way on the fixture's composed labels (fixture:185) and on the write detector in `check.py`. The round-2 fixes themselves landed: the README raise and its test, the removal of the two hand-written checks, the pinned header, the PENDING row's new content and the composed labels for the prefixes it named. The findings above are worth acting on before the change moves on; those labelled "(writer's text)" go back to eval-case-writer. Change risk: lens not run, no HIGH file.

Notes for the caller: both lenses returned complete reports on the first spawn; no retry. Bash use in this review stayed within budget.

VERDICT: Standards FINDINGS · Spec FINDINGS · Change risk NOT RUN · needs-a-human 0
