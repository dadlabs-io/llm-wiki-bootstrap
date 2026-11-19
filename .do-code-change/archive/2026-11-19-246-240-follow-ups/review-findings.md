# Review report, round 4 (focused, last round the cap allows): 246-240-follow-ups

Fixed point 047d868 (resolves; `git merge-base 047d868 HEAD` is 047d868; 17 commits in `git log 047d868..HEAD`). Focused round: the change under review is what fix round 3 moved, diffed from ddcf3fe (the tree round 3 reviewed) to the working tree: `CHANGELOG.md` (1/1), `tests/scripts/test_left_undone_fixture.py` (30/2), `tests/skills/PENDING.md` (1/1), `tests/skills/wiki-cycle/check.py` (11/8), 55 changed lines, no untracked files outside `.do-code-change/`. The set equals `review-ledger.py changed`'s four files. One part per axis. Files round 3 reviewed and the fix left alone (`scripts/_run_state.py`, `skills/wiki-cycle/SKILL.md`, `tests/scripts/test_cycle_scope.py`, `tests/skills/wiki-cycle/cases.json`) are out of this round; nothing was raised in them. One lens remark on an untouched line (check.py:3364 calls `_lu_model_wrote_file(run)` twice) is out of scope for the same reason and is not counted. Prescan was clean (review ids, round numbers, dates and width skipped). Lenses ran as `code-reviewer-lens`, unnamed, `run_in_background: false`, on the `sonnet` tier (raised from the default tier because the last round cannot be repeated; the cause-of-failure question in CHANGELOG needed a careful read). Both came back as launch notices and their reports were taken from their completion messages. The Standards lens did not open CHANGELOG.md, so that file got its one retry (a further lens on line 16 only), which read it in full. Rulings 1-3 were passed to both lenses and are raised nowhere. Findings in `check.py` would be the writer's text; none was raised there that counts. Both axes ran on all four files; every file is LOW, so Change risk was not run. The fixture (exit 0) and `test_cycle_scope.py` (330/330) were not run by this review (a review runs no test); their results are in checkpoints.md.

## Standards

- [important] PY9, T3, T5 `tests/scripts/test_left_undone_fixture.py:326-332`: the "script-output check fails a changed left-undone.txt written by <route>" plants (all 14 shell routes, and the "none" plant) cannot show that the one changed count is what fails them, and the exact comparison has no case of its own.
  - The fixture writes the changed file in text mode: `lu_file.write_text(changed, encoding="utf-8")`. On Windows `write_text` turns "\n" into CRLF. The script writes `left-undone.txt` with `newline=""` (`scripts/_atomic_io.py:80`, `open(tmp, "w", encoding=encoding, newline="")`), so its output is bare LF. `_lu_copy_checks` now compares bytes (`if raw == made:`, check.py:3286), so each plant fails on CRLF against LF alone, with or without the count change; the expected verdict is False, so they pass either way.
  - A Grep of the fixture for `trailing|rstrip|\r|final newline|line ending` finds only the `rstrip` calls in `compose_report` (lines 122-123). Round-3 standards-26's fix asked for "a plant for a trailing-space edit"; none exists, and the branch `diff or "same lines, different line endings or final newline"` (check.py:3289-3292) has no case.
  - The restores at fixture lines 333 and 342 use `write_text(original)` too and change the file from LF to CRLF; no assertion expecting a pass runs after them today (`session_write_plants` is the last call in `grade`, line 421; the plain pass run is at 415), so nothing fails yet.
  - Fix: write the changed file with `lu_file.write_bytes(changed.encode("utf-8"))` (and the restores likewise), so only the count differs; add one plant that changes only a trailing space and one that changes only the line endings, each required to fail the script-output check.
- [nit] C2/C3 `tests/skills/wiki-cycle/check.py:3199-3201` (writer's text): the edited docstring reads "whose file_path, path or notebook_path, or whose edits[].file_path, whose last path part is left-undone.txt"; the double "whose" is hard to parse. Fix: "any other non-read tool with a file_path, path, notebook_path or edits[].file_path whose last path part is left-undone.txt".
- [nit] G2 `CHANGELOG.md:16`, the parenthetical about Sonnet's old copy: "read-guard and the blocked Skill tool counted apart" is unclear and three clauses chain on commas. Fix: split into short clauses (moot if the Spec finding's rewrite is taken, which replaces this sentence).

Unverified:
- The fixture's exit 0 and `test_cycle_scope.py` 330/330 (checkpoints.md, Fix round 3) were not re-run here.
- That the CRLF write happens on this machine rests on the Windows platform and `Path.write_text`'s default newline translation; the fixture was not run to print the bytes.
- Whether a real MultiEdit call carries `edits[].file_path`: not checkable offline (a real call carries a top-level `file_path`, which the Edit plant already covers).

Checks made:
- Round-3 Standards findings, fixed and confirmed by the lens's and my own reads: standards-25 (the fixture now plants MultiEdit, NotebookEdit, a `path`-keyed tool, a backslash Write, a Read and a Write to `copy-of-left-undone.txt` as pass controls, and `old_run_write_plants` for the old-run kind, called from `main`, fixture 485); standards-31 (PENDING columns now hold the reason and the pointer in their own cells; the Opus-only caveat is in the Change column); standards-32 (the docstring says "three of the shell routes"; the loop runs `cp`, `PowerShell Set-Content`, `>`); standards-26's code half (exact byte comparison, no `rstrip`; its plant half is the finding above).
- Round-1 re-verification, standards-1 (fixture route plants judged on the untouched file): still fixed. The tool plants and the not-the-file plants run on the untouched file and are judged by `named(..., WROTE_ITSELF)`, a prefix match on the check's own name, not the old loose `caught()`; the three identical shell rewrites and three reads are judged on the same untouched file expecting a pass; only the shell routes with a changed count are judged by `SCRIPT_OUTPUT` (ruling 1), subject to the first finding.
- Round-1 re-verification, standards-2 (old-run kind graded stricter, Mark's ruling): still fixed. `_check_left_undone_old_run` reaches `_lu_norm_line` through `_lu_section_lines` (check.py:3358); `_lu_norm_line` (3152-3165) has no dash mapping (Read). The shared `_lu_model_wrote_file` now matches the last path part exactly: narrower than `endswith` only for names such as `copy-of-left-undone.txt`, which is the round-3 spec-15 fix and sits inside ruling 1; ruling 2 concerns text grading. Shell writes to the file in the old-run kind are still caught by "no left-undone.txt in the run folder after the run" (check.py:3362, `not f.exists()`), so removing shell-text detection opened no hole there. README line 21 ("an existing kind is never changed") is overridden for these kinds by the requester ("yes okay its stricter thanks for asking").
- Round-1 re-verification, standards-4 (PENDING row does not count none-answered as proof): still fixed. The row says "only lint-within-24h discriminates ... none-answered passes the old copy on Opus only and is a regression case; both fail on Opus's new copy on the sandbox edit gate, task #247". It does not name the replay step README line 49 describes; CHANGELOG assigns the sharpening to #247.
- Grep over `tests/` for `_LU_WRITE_RES|_lu_ps_writes_file|_LU_PS_|_LU_COPY_VERBS|_LU_FILE|Copy-Item|xcopy|caught(` finds only the fixture's `xcopy` plant string.

| File | Risk | Part | Standards | Spec | Change risk |
|---|---|---|---|---|---|
| `tests/skills/wiki-cycle/check.py` | LOW (test code, writer's text) | 1 | in full (3140-3380) | in part: 3190-3379 (every changed line) | not run |
| `tests/scripts/test_left_undone_fixture.py` | LOW (tests) | 1 | in full | in part: 235-512 (every changed line) | not run |
| `tests/skills/PENDING.md` | LOW | 1 | in full (line 28, the changed row) | in part: line 28 | not run |
| `CHANGELOG.md` | LOW | 1 | in full after the retry (14-19) | in part: 14-17 | not run |

| Coverage (Standards) | Verdict | Search |
|---|---|---|
| S1, S3-S12, G25, F3, C5, R2, C1 | clear | lens reads of every added name and literal (`made[-20:]` is a display window) |
| S2 / G5 | clear | the old-run write check calls the one shared helper |
| R1, N7 / G20 | clear | `_lu_script_output` docstring announces snapshot and restore |
| R26 | clear | `old_run_write_plants` called from `main` |
| C2, C3 | found | check.py:3199-3201 docstring; CHANGELOG.md:16 wording |
| Names N2-N6, R3 | clear | `raw`, `made`, `not_the_file` read in context |
| Functions S13-G16, R4 | clear | the new `_lu_copy_checks` branch is short, nesting two |
| Tests T1, T3, T5, T6 | found | whitespace and line-ending branch unplanted |
| R12-R15, T4 | clear | each plant names one outcome; nothing loosened or skipped |
| PY9 | found | CRLF-overdetermined plants |
| PY1-PY8, PY10, PY11 | clear / n/a | no new imports, Any or async |
| Boundary G3, G33, G26, G2 | clear | empty `edits` and non-dict entries handled; `[-1]` guarded by `split` |
| Classes, Error handling, Concurrency, Refactoring sections | n/a | not pasted (no class, no handler change, no concurrency, not a refactor) |
| Documented standard: tests/skills/README.md | clear | "existing kind", "not counted as proof", PENDING row read against it |
| Re-verify standards-1, 2, 4 | clear | see Checks made |

Well built: each tool-route plant is judged on the untouched file by the write check's own name, and `_lu_script_output` restores the run folder byte for byte.

## Spec

- [important] `CHANGELOG.md:16` still misstates why Sonnet's none-answered old copy failed, now in the opposite direction (round-3 spec-10 was not fixed; its premise was a misread).
  - Intent: `tests/skills/.results/wiki-cycle/20261118-195235-red-green-047d868/report.md:29` reads "old failed: no permission denials (read-guard and the blocked Skill tool counted apart); every step JSON follows the contract (fields, cycle_id)". `tests/skills/README.md:49` defines that parenthetical as "the checks that failed on the old copy". Both strings are check names: `tests/skills/wiki-cycle/check.py:896` ("no permission denials (read-guard and the blocked Skill tool counted apart)") and `check.py:3508` ("every step JSON follows the contract (fields, cycle_id)"). So on Sonnet's old copy two checks failed, the permission-denials check and the step JSON contract check, and neither is a record check; the new copy passed (report.md:36). `checkpoints.md:30` ("no permission denials; step JSON contract: NOT the record checks") says the same and is right.
  - Implemented: CHANGELOG.md:16 now says "Sonnet's old copy failed it on "no permission denials" alone, ... and every step JSON followed the contract, so neither the record checks nor the contract told the copies apart". Wrong on three counts: "alone", "every step JSON followed the contract", and "the contract [did not] tell the copies apart" (the contract check failed on the old copy and passed on the new one). Round 3 read the second item as a passing check and its fix wrote that into the changelog.
  - Affected: a reader judging whether none-answered is evidence. The case's Sonnet red is for a wrong reason (permission and contract checks), which is why it does not discriminate.
  - Fix: "Sonnet's old copy failed it on two checks, no permission denials (read-guard and the blocked Skill tool counted apart) and the step JSON contract (fields, cycle_id); the record checks did not fail". Leave `checkpoints.md:30` as it is; round 3's request to correct it was wrong too.

Unverified:
- The PENDING pointer `.do-code-change/archive/2026-11-18-246-240-follow-ups/checkpoints.md` does not exist yet (it resolves when the run is archived; the archive date slug is not known now).
- The fixture's exit 0 and `test_cycle_scope.py` 330/330 (checkpoints.md) were not re-run here.
- The "edit gate" cause of Opus's Write denial rests on `checkpoints.md:30` (`dcc-edit-gate --explain`); `report.md:49-52` shows only the denied Writes of `build.py` and `build_index.py`.

Checks made:
- Round-1 re-verification, spec-1 (alias routes `copy`, `move`, `ren`, `xcopy`, `>|`): SUPERSEDED by ruling 1, not "fixed". `requirements.md:43` was rewritten after the requester's "a" and replaces the earlier catch-every-route reading; the detector is gone from `check.py` (Grep above). Changed-text writes by those routes are caught by the exact script-output comparison (check.py:3280-3292); the fixture plants all 14 shell routes (fixture 274-289), judged by that check, subject to the Standards finding's CRLF caveat. An identical rewrite is accepted by ruling.
- Round-3 Spec findings fixed and confirmed: spec-11 (CHANGELOG and PENDING now say both cases fail on Opus's new copy on the edit gate, #247; `report.md:36-37` shows FAIL (1) twice); spec-13 (plants at fixture 290-295 and `old_run_write_plants`); spec-14 (check.py:3285-3292 compares `raw == made` with no `rstrip`, matching `requirements.md:43`); spec-15 (check.py:3211 matches the last path part; control at fixture 296-298); spec-16 (the "Why it was not run" column holds no result pointer).
- CHANGELOG's "a Write, Edit, MultiEdit or NotebookEdit aimed at `left-undone.txt` fails" agrees with `_lu_model_wrote_file` (check.py:3198-3213) and the plants. The PENDING row's none-answered and Opus statements agree with `report.md:36-37, 49-52` and `checkpoints.md:30-32`.
- Sibling search for the same wrong wording: `Grep "step JSON contract|none-answered"` over the repo finds the sentence only in CHANGELOG.md:16 and PENDING.md:28 (PENDING does not repeat the contract claim) and in `checkpoints.md:30` (correct).

| Coverage (Spec) | Verdict | Search |
|---|---|---|
| spec-10 cause of Sonnet's old-copy failure | found | Grep of both check names in `tests/skills/*.py` (check.py:896, 3508) |
| spec-11 Opus new-copy denial named | clear | report.md:36-37, 49-52; checkpoints.md:30-32 |
| spec-13 plants and old-run plant | clear | fixture 290-298, 350-364, 485 |
| spec-14 exact comparison | clear | check.py:3285-3292 |
| spec-15 basename match | clear | check.py:3211; fixture 296-298 |
| spec-16 PENDING columns | clear | PENDING.md:28 read |
| spec-1 re-verification | clear (superseded by ruling 1) | Grep for the old detector names, none |
| (a) CHANGELOG/PENDING Opus claim | clear | report.md:49-52 |
| (b) PENDING result pointers | clear, archive path Unverified | checkpoints.md Step 9 |
| (c) CHANGELOG write-check sentence | clear | check.py:3198-3213 |
| (d) requirements.md:43 "equal the script's own output" | clear | check.py:3286 |

Well built: the exact byte comparison names the first differing line, and the fixture pins every tool route with its pass controls.

## Change risk

No high-risk file; the change-risk lens was not run. The file table under Standards is the triage: every moved file is LOW (test code, tests, release notes, a docs table).

needs-a-human: none (no auth, session, token or data-migration change; spec resolved from `requirements.md`, `plan.md` and `checkpoints.md`).

## Summary

Standards: 3 findings (1 important, 2 nit). The worst: the changed-count plants fail on CRLF against LF alone on Windows, and the new exact comparison has no trailing-space or line-ending plant.

Spec: 1 finding (important). CHANGELOG.md:16 states Sonnet's old-copy failure wrongly again: two checks failed (permission denials and the step JSON contract), not "alone" with the contract followed.

Change risk: not run.

Re-verified STALE round-1 items: spec-1 superseded by ruling 1; standards-1, standards-2 and standards-4 still fixed. The axes do not overlap. Both axes are worth acting on; the Spec finding's fix is one sentence, and the Standards finding's is a `write_bytes` change plus two plants.

VERDICT: Standards FINDINGS · Spec FINDINGS · Change risk NOT RUN · needs-a-human 0
