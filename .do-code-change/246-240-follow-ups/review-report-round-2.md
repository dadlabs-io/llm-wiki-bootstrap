# Review report, round 2 (focused): 246-240-follow-ups

Fixed point 047d868. Focused round: the change under review is the fix round's moved files (`review-ledger.py changed`: CHANGELOG.md, scripts/_run_state.py, tests/scripts/test_left_undone_fixture.py, tests/skills/PENDING.md, tests/skills/wiki-cycle/check.py), diffed from the round-1 commit c9e7f44 to the working tree: 5 files, about 120 changed lines (one part per axis; `git diff --numstat`: 1/1, 2/2, 32/10, 1/1, 84/23). No untracked files outside `.do-code-change/`. The round-1 untouched files (`skills/wiki-cycle/SKILL.md`, `tests/scripts/test_cycle_scope.py`, `tests/skills/wiki-cycle/cases.json`) are out of this round and nothing was raised in them. Prescan ran clean (review ids, dates, width skipped). Lenses ran as `code-reviewer-lens`, unnamed, `run_in_background: false`; both came back as launch notices and their reports were taken from their completion messages. No lens was retried. Findings against `check.py` are the eval-case-writer's text and are labelled "(writer's text)".

## Standards

- [important] (writer's text) G2, C2 `tests/skills/wiki-cycle/check.py:3197-3202, 3203-3211, 3207, 3221`: the comment promises "a command that only reads the file ... is not a hit", but reads still match, because the file is anchored by position (last argument) and the verb or alias is matched anywhere before it, not in command position.
  - Probed with `uv run python -B` against `_lu_model_wrote_file` (each returned a hit): `grep -c copy <file>`, `grep move <file>`, `grep ni <file>`, `grep -i sc <file>`, `Select-String -Pattern ac -Path <file>` (aliases `ni`, `sc`, `ac`, `clc` in `_LU_PS_RE`), `grep tee <file>`, `grep -c install <file>`, `tee report.md < <file>`, `[IO.File]::WriteAllText('report.md', [IO.File]::ReadAllText('<file>'))`, `truncate -r <file> other.txt`, `Copy-Item a -Destination <file>.bak`. Round-1 standards-3's own example (`Add-Content ... -Value (Get-Content <file>)`) is fixed and passes; its siblings are not.
  - Affected: a session that only reads the file fails "the session did not write left-undone.txt itself", turning a paid case red for the wrong reason. The fixture's only read control is the `Add-Content` form (`test_left_undone_fixture.py:297`).
  - Fix: match copy verbs, `tee`, `truncate` and PowerShell aliases only as the command word (start, or after `;`, `&`, `|`, `(`), and add `-Destination` an end anchor; add a read control per shape to the fixture. Back to eval-case-writer as a replay.
- [important] (writer's text) G2 `check.py:3209-3213, 3249-3263`: literal write routes the rule claims to catch are missed.
  - Probed, each returned no hit: `cp /tmp/a <file> 2>&1` (the copy pattern needs the file at the end of the command, `:3211`), `open('left-undone.txt', mode='w')` (`:3213` needs a quote straight after the comma), `Set-Content -Path:<file> -Value x`, `shutil.copy('a','left-undone.txt')`, `rni a <file>`, `Export-Csv -Path <file>`, `Invoke-WebRequest -OutFile <file>`. From reading `_lu_ps_writes_file`: `New-Item -Path <dir> -Name left-undone.txt`, an unlisted switch such as `-Confirm:$false` placed before the path, and a quoted `-Value "a|b"` cut at `|` before tokenizing also lose the destination. CHANGELOG.md line 10 and PENDING.md line 28 list `cp, mv, copy ...` as caught; that holds for the bare form only.
  - Fix: allow redirections after the file, accept `mode=`, read `-Path:value`, add the missing aliases and cmdlets, tokenize before splitting on `;|&`; one fixture route per branch. Replay through eval-case-writer. (The Spec axis raises the same gap against the requirement; reported there separately.)
- [important] `tests/skills/PENDING.md:28` against `tests/skills/README.md:69` (standards-12, claimed addressed, not fixed): the 2026-11-18 row is still one long table row carrying a measurement (run ids, costs, per-model red/green outcomes, the none-answered finding). The README says a PENDING row worth more than a line uses the four headings (Compared with, n, Cost, What this does not show).
  - The Standards lens rated this important; round 1 had it a suggestion. PENDING.md was read to its last line (184): every older row is longer still, so the convention in practice differs from the README text. Whether this row counts as a measurement is the author's call.
  - Fix: put the measurement under those four headings in a linked note and leave a one-line row.
- [suggestion] R4, S13 (writer's text) `check.py:3249-3263`: `_lu_ps_writes_file` nests for, while, if, if (four levels) in a 38-line function that masks groups, tokenizes and finds the destination. `_lu_model_wrote_file` (`:3282-3289`) still nests four levels (round-1 standards-10 stays open). Fix: extract `_lu_ps_destination(seg) -> str | None`, use guard clauses.
- [suggestion] T1, T3, T5 `tests/scripts/test_left_undone_fixture.py:277-300`: the new branches have no failing case. Routes cover only `-Path` writes; none covers a positional destination (`Set-Content <file> x`), `-FilePath`, `-LiteralPath`, `-Destination` or an alias; the restore of other run-folder files in `_lu_script_output` (`check.py:3342-3346`, round-1 standards-6) is untested (a changed `left-undone-events.txt` is never planted); the `_LF_CALL` lookahead (`:3457`, standards-5) has no test. Fix: one route per branch with its read control, and a planted events file.
- [suggestion] PY9 `tests/scripts/test_left_undone_fixture.py:260-274`: the dash plant still judges by `caught()`, whose `about` regex (`left.undone|section|queue line`) accepts any failing check with such a name, the same loose test round-1 standards-1 named for the routes. Fix: use `named(..., SECTION_EQUALS_FILE)` as `tamper_checks` does, and drop `caught` and `about`.
- [nit] (writer's text) N1, G25 `check.py:3236-3247`: `range(4)` and `range(5)` are unexplained pass counts; `hold` and `restore` do not say what they hold. Fix: a named constant with one line of reason; `mask_group` and `unmask`.
- [nit] `tests/scripts/test_left_undone_fixture.py:40, 267`: `NEEDS_AWAITING ="<N> ...` lost the space before the quote (the line was edited though unrelated), and nested `def named` follows a statement with no blank line. Fix: restore `NEEDS_AWAITING = `; add the blank line.
- [nit] (writer's text) `check.py:3327-3332, 3342-3346`: the docstring says the whole run folder is put back, but only files are; a directory the script made stays (probed: an empty `newdir` remained after restore). Fix: remove new directories too, or say files only.

Unverified:
- `-PSPath` may be an alias of Set-Content's `-Path` in some PowerShell versions, which `_LU_PS_PATH_PARAMS` (`:3223`) would miss; not checkable offline.
- Whether a real session greps the file with a verb word; needs a transcript or a paid run.
- The fixture and the six neighbouring suites were not run by this review (the brief gives exit 0 for the fixture).

Checks made:
- Round-1 standards-1 (routes judged on the untouched file by `WROTE_ITSELF`), standards-4 (PENDING says "None-answered is not proof"), standards-5 (`_LF_CALL` lookahead; Grep found no other `lint-fixes` regex) and standards-6 (whole-folder snapshot; probed with a stub script that rewrote the events file, deleted a file and made a new file and a new directory: bytes restored, new file removed, also on an exception) are fixed.
- standards-2: Mark's ruling is recorded in checkpoints.md ("yes okay its stricter thanks for asking"); not re-judged.
- The write routes the fix names caught on probe: `copy`, `move`, `ren`, `xcopy` (with trailing `/y` flags too), `>|`, `Copy-Item -Destination`, `Rename-Item -NewName`, PowerShell `-Path`, `-Pa`, `-Lit`, positional, `-Value` first, `(Join-Path ...)`, a quoted path with a space.

| File | Risk | Part | Standards | Spec | Change risk |
|---|---|---|---|---|---|
| `tests/skills/wiki-cycle/check.py` | LOW (test code, writer's text) | 1 | every changed line read; surrounding file in part | every changed line read | not run |
| `tests/scripts/test_left_undone_fixture.py` | LOW (tests) | 1 | in full | changed hunks read | not run |
| `tests/skills/PENDING.md` | LOW | 1 | changed row read, whole file read by the reviewer | changed row read | not run |
| `CHANGELOG.md` | LOW | 1 | changed hunk | changed hunk | not run |
| `scripts/_run_state.py` | MEDIUM (business logic; this hunk is a docstring) | 1 | in full | changed hunk | not run |

| Coverage (Standards) | Verdict | Search |
|---|---|---|
| S1 / N1 | found (nit) | `hold`, `restore` |
| S2 / G5, S3-S12, G36, G14 | clear | lens reads of every added hunk |
| G25 | found (nit) | `range(4)`, `range(5)` |
| F3, R1, N7 / G20 | clear | `_lu_script_output` docstring names the snapshot and restore |
| C5, R2, C1, C3 | clear | added comments read |
| R26 | clear | Grep: each new function and constant has a caller |
| C2 | found | first finding |
| S13 / G30, R4 | found | `_lu_ps_writes_file`, `_lu_model_wrote_file` |
| G2 | found | first and second findings, probed |
| G3, G31, G34, G19, G28, G29, G16, S14, S15 | clear | lens reads; empty-segment case returns False |
| R7-R11, G4 | clear | `finally` restores on exception (probed) |
| T1, T3, T5 | found | fixture routes |
| R12-R15, T4, T6 | clear | routes isolated in try/finally; assertion keyed on the exact check name |
| PY9 | found | dash plant's `caught` |
| PY1-PY3, PY7, PY8, PY10, PY11 | clear | none added |
| documented standard: README PENDING format | found | third finding |
| Sections not pasted | n/a | Classes and modules, Concurrency, Refactoring and scope |

Well built: the destination-anchored patterns, the per-route fixture judged on one named check, and the folder snapshot that restores on every path make the write check traceable.

## Spec

- [important] (writer's text) `check.py:3203-3211, 3207, 3221`: a read-only command is counted as a write.
  - Intent: `check.py:3274-3275`, "In each the file must be the destination: a command that only reads it is no hit"; plan Failures: a model that renders correctly must pass.
  - Implemented: `_LU_COPY_VERBS` (`:3203`) is matched anywhere before the file name (`:3209`); probed `grep -c copy <file>`, `grep move <file>`, `grep tee <file>`, `grep ni <file>` all return a hit labelled "copy or move onto it", "tee" or "PowerShell write".
  - Affected: a paid session that greps the file fails "the session did not write left-undone.txt itself". The fixture's only read control is `test_left_undone_fixture.py:297`.
  - Fix: anchor verbs, `tee` and aliases to command position; add read controls (`grep "move" left-undone.txt`). Replay through eval-case-writer.
- [important] (writer's text) `check.py:3275-3276`: the write detector misses literal routes the requirement covers, while the docstring says the only miss is a path held in a variable.
  - Intent: `requirements.md:43`, "the write detector must catch every route by which the session itself produces `left-undone.txt`"; Mark's accepted limit is the variable-path case only (checkpoints.md Step 6).
  - Implemented: probed, no hit for `shutil.copy('a','left-undone.txt')`, `open('left-undone.txt', mode='w')`, `rni a <file>`, `Export-Csv -Path <file>`, `Invoke-WebRequest -OutFile <file>`, `cp /tmp/a <file> 2>&1`, `Set-Content -Path:<file>`; `curl -o <file>` has no pattern (reported by the Spec lens). Fixture plants none of them.
  - Affected: a session writing the script's identical text by one of these passes the write check and the copy check; the script-output comparison catches only text that differs.
  - Fix: replay these routes to eval-case-writer with one fixture plant each, or put the wider limit to Mark, since it is not the accepted one.
- [suggestion] `CHANGELOG.md:16` and `tests/skills/PENDING.md:28` say "none-answered passes on the old copy", but checkpoints.md Step 9 records it on Opus only; on Sonnet the old copy failed the step JSON contract, not the record checks.
  - Fix: "passes on the old copy on Opus only; Sonnet's old-copy failure was the step JSON contract".

Unverified:
- Whether a real session reads the file with one of the verb words (needs a transcript or a paid run).
- Whether Mark counts the literal routes above as in scope; his ruling names only the variable-path limit.
- "script tests 330/330" in PENDING.md: checkpoints.md records the developer's before-and-after run; this review did not run `test_cycle_scope.py`.

Checks made:
- spec-1 (aliases): `copy`, `move`, `ren`, `xcopy` and `>|` are caught on probe; the literal gaps are the second finding.
- spec-3: each route runs on the untouched file and is judged on `WROTE_ITSELF` (`test_left_undone_fixture.py:293-296`); a read control passes (`:297-300`).
- spec-4: CHANGELOG and PENDING now name the routes and the variable-path limit; the none-answered wording is the third finding.
- spec-5: `_run_state.py:116-117` has the pinned semicolon and the rewrap.
- spec-32 and spec-33 stay met: no `left-undone-resumed` in `check.py`; `_lu_norm_line` has no dash mapping; a failed copy check names the first differing line (probe: "first difference at character 3: script '—' vs file '-'").
- Mark's rulings: the strict dash rule covers both kinds, and the reader `_lu_ps_writes_file` is kept (checkpoints.md Fix round 1); neither raised as a finding.

| Coverage (Spec) | Verdict | Search |
|---|---|---|
| spec-1 literal routes named by the fix | clear | probe: copy, move, ren, xcopy, `>|` hit |
| requirement line 43, every literal route | found | second finding |
| read-only command is no hit | found | first finding |
| spec-3 fixture shows the regex catches each route | clear | `WROTE_ITSELF` at fixture `:294`, `:298` |
| spec-4 overclaim | found | third finding; the route list is also checked in Standards |
| spec-5 docstring | clear | `_run_state.py:116-117` |
| model-written file cannot pass the copy check | clear | script-output comparison `check.py:3362-3371` |
| paid checks still fail Write, Edit, `>`, tee | clear | `check.py:3206-3207`, `:3282-3294` |

Well built: the script-output comparison and the first-difference wording meet the "names what is different" ruling, and the PowerShell reader keeps the `Get-Content` read as a read.

## Change risk

No high-risk file; the change-risk lens was not run. The file table above is the triage: `scripts/_run_state.py` is MEDIUM (this round's hunk is a docstring), every other moved file LOW.

needs-a-human: none (no auth, session, token or data-migration change; spec resolved from requirements.md, plan.md and checkpoints.md).

## Summary

Standards: 9 findings (3 important, 3 suggestion, 3 nit). The worst is the write detector counting reads as writes and missing literal writes; the fix for round-1 standards-3 covers its own example, not its siblings. Standards-12 is still open.

Spec: 3 findings (2 important, 1 suggestion). The worst is the same detector: a read counts as a write, and literal routes under requirement line 43 are missed.

Change risk: not run.

Round-1 findings addressed and confirmed fixed: standards-1, 4, 5, 6, spec-3, spec-5, and spec-1 for the named aliases. Not fully fixed: standards-3 (siblings), standards-12, spec-4 (none-answered wording). The axes agree on the detector; both are worth acting on. Findings labelled "(writer's text)" go back to eval-case-writer (replay), not to the implementer.

VERDICT: Standards FINDINGS · Spec FINDINGS · Change risk NOT RUN · needs-a-human 0
