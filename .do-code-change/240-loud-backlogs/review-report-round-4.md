# Review report, round 4 (focused, last within the cap), 240-loud-backlogs

Change under review: the files moved since round 3 (reviewed at c66f855), the diff c66f855 -> HEAD c069fbd, `.do-code-change/` excluded (2 files: `tests/scripts/test_left_undone_fixture.py` 16 added / 12 removed, `tests/skills/PENDING.md` 1 / 1; so one part per axis), plus plan.md step 3's amendment, checkpoints.md's two new sections, and the sibling sites of the addressed findings. Fixed point 6f23c8c (`git rev-parse` resolves; diff non-empty). Addressed in fix round 3: standards-50, standards-51, spec-31, standards-59, spec-34, spec-28, standards-62. The other round-3 items are open by decision and were not re-raised. Prescan: passed on the earlier tree, this round adds only test and doc lines (the lenses were told). Two lenses (Standards, Spec), `code-reviewer-lens`, foreground, unnamed, `run_in_background: false` written out; each came back as a launch notice and its report was taken from its hand-back. Default model tier; no retry needed.

## Standards

- [important] C2 / PY11 `tests/scripts/test_left_undone_fixture.py:16-18` (docstring) and `:56-62` (comment): the new wording says the COMPOSED checks "cannot fail here", but several entries read the script's own wording and can fail in grade().
    Quote: "the checks that read only its shape (its sections and their order, the Left undone section as the file's text, the Numbers row, the Needs-you line; names in COMPOSED) cannot fail here". `check.py:3110-3111` reads the script's "awaiting your approval" wording and its `past review_after` line, and `compose_report` line 110 branches on `"awaiting your approval" in rest`; a reworded script line gives a FAIL (`report()` line 139). `check.py:3142` and `:3081` ("the section reads / does not read 'Left undone: nothing'", COMPOSED lines 66 and 68) read the same file wording as the excluded "Left undone line: ..." checks.
    Fix: move the wording-reading entries (Numbers row, Needs you carries, the two 'Left undone: nothing' checks) out of COMPOSED, or reword the docstring and comment to say they pass by construction only while the script keeps its wording.
- [suggestion] S5 `tests/scripts/test_left_undone_fixture.py:65-68` and `report()` line 138: a check's name is carried as a raw prefix string in two files and nothing validates it.
    `startswith(COMPOSED)` silently falls back to plain "PASS" when a check.py name changes; the round-3 rename at line 189 shows the drift already happened once.
    Fix: after the run, assert that every COMPOSED prefix matches at least one emitted check name, and fail otherwise.

Unverified:

- Whether PENDING row 28 lost any word beyond the restored "and": the lens had no earlier text to compare (the diff shows only the one change, a comma and "and" before "the no-file `--brief` line").

Checks made:
  - standards-50: the rename at fixture line 189 ("compose_report words 'Nothing.' ...") matches the COMPOSED prefix "compose_report words"; a grep of tests/ for "compose_report writes" finds none left.
  - standards-51 / standards-59: the three added prefixes each match an emitted check name (`check.py:3052`, `:3076`, `:3081`, `:3138`, `:3236`).
  - standards-62: PENDING.md line 28 reads ", and the no-file `--brief` line"; the diff changes only that.
  - The docstring's "an unpaid smoke of it was run by hand, checkpoints.md" (the lens could not find it): recorded at checkpoints.md:210 ("Unpaid smoke (scratchpad `smoke_old_run.py` ...)"), so true.

| Row | Verdict | Search or reason |
|---|---|---|
| S1 Mysterious Name | clear | added lines read: string literals and comment words |
| S2 Duplicated Code | clear | new COMPOSED strings compared with check.py names |
| S3, S6 to S12, F3, R1, N7, R26 | n/a | no function, class or parameter added |
| S4 Data Clumps | clear | none in the added lines |
| S5 Primitive Obsession | found | prefix strings (finding 2) |
| G25 Magic numbers | clear | no literal beyond strings |
| C5 Commented-out code | clear | added comment lines read |
| C1 Metadata in a comment | clear | one `checkpoints.md` reference, a pointer |
| C2 Obsolete comment | found | finding 1 |
| C3 Redundant comment | clear | rationale, not restatement |
| R2 TODO | clear | grep of the diff: none |
| T1, T3, T5, T6 | clear / found | T6 neighbour of standards-50: the prefix validation (finding 2) |
| R12 to R15, T4 | clear | no test added, no assert changed, no skip |
| PY1 to PY3, PY7, PY8, PY10 | clear | grep of the diff and a whole-file read |
| PY4 to PY6 | n/a | no async code |
| PY9 | clear | label accuracy is in finding 1 |
| PY11 | found | "cannot fail here" (finding 1) |
| Names, Functions, Classes, Error handling, Boundary, Concurrency, Refactoring | n/a | the diff changes one string literal, one tuple and comments only |
| Repo convention (tests/skills/README.md "Who writes the cases") | clear | the diff edits only the fixture, PENDING and plan; check.py untouched |

Well built: the tamper variants (invented, reworded, dropped queue line) run through `check()` and are restored in `finally`; each COMPOSED addition matches an emitted check name exactly.

## Spec

- [important] `tests/skills/wiki-cycle/check.py:3354` and COMPOSED (fixture lines 65-68): the check "the cycle report's last section is Needs you" is satisfied by construction yet prints a plain PASS.
    Intent: fixture docstring lines 16-18, "the checks that read only its shape (its sections and their order, ... the Needs-you line ...) cannot fail here: they print "PASS (composed)"" (spec-31's own criterion).
    Code: `add("the cycle report's last section is Needs you", bool(heads) and "needs you" in heads[-1].lower(),` (check.py:3354); the composer always ends with `"## ⚠️ Needs you", "", *needs, ""` (fixture line 121); no COMPOSED prefix matches it.
    Affected: a reader of the fixture output takes the plain PASS as a graded /wiki-report result. A sibling site of spec-31 that the fix missed.
    Fix: add "the cycle report's last section is Needs you" to COMPOSED.
- [important] `tests/skills/wiki-cycle/check.py:3142`, `:3081`, `:3145`: "the section reads 'Left undone: nothing'", "the section does not read ...", "no queue line under 'Left undone: nothing'" read the script's own line 1 and bullets, yet COMPOSED (fixture lines 66, 67-68) prints them "PASS (composed)".
    Intent: fixture comment lines 60-61, "The 'Left undone line: ...' checks are not here: they read the script's own wording in the file, which can fail in grade()".
    Code: the composer copies the file verbatim (`"## Left undone", "", lu.rstrip()`, fixture line 121) and the script writes the wording (`head = f"Left undone: {len(queues)} queue(s)" if queues else "Left undone: nothing"`, `scripts/_run_state.py:949`), so these checks depend on the script, not the composer.
    Affected: a script wording change would print "PASS (composed)" and be read as not graded here. Same root as the Standards finding 1.
    Fix: remove those prefixes from COMPOSED so they print plain PASS.
- [nit] `.do-code-change/240-loud-backlogs/plan.md:272`: the amended bullet says an unparseable-frontmatter README "falls to `buckets()`'s one-bucket default", but the default lives in `session_buckets`.
    Code: `except parse_errors:` / `return [{"folder": "main", "reader": tri.me()}]` (`scripts/_run_state.py:427-428`); `buckets()` (`scripts/wiki-triage.py:125-132`) raises on a YAML syntax error. The behaviour matches the code and the test (`test_cycle_scope.py:1037-1043`, `1080-1085`); only the function name is wrong (the phrase predates the amendment).
    Fix: write "`session_buckets`' one-bucket default".
- [nit] `tests/scripts/test_left_undone_fixture.py:45-46`: "scratchpad: Phase 8 done" and "Phase 9 done" are listed NEEDS-PAID-SESSION although the fixture sets both itself (`finish_scratchpad`, lines 125-131).
    Fix: say so in the docstring, or move them to COMPOSED.

Unverified:

- The command-level outcome for a non-UTF-8 intake README (plan step 3: "the command exits non-zero and writes no file"): traced (`_run_state.py:944` raises before the `:956` write; `wiki-cycle-scope.py:527` has no try), not run; the only test (`test_cycle_scope.py:1086-1092`) calls `session_buckets` alone. Settle: run `wiki-cycle-scope.py --topic <nb> left-undone --run-folder <rf>` on a README holding bytes `\xff\xfe`.
- "Needs you carries '2 semantic lint findings awaiting your approval'" (`check.py:3109`) depends on the composer's branch matching the script's wording (fixture line 110); not decided; it belongs with Spec finding 2.

Checks made:
  - Plan step 3's amended Failures bullet against the code and test: the ruling (frontmatter that does not parse falls to the default; a non-UTF-8 README raises) matches `_run_state.py:413-428` and `test_cycle_scope.py:1086-1092`, and checkpoints.md:213 records it.
  - Sibling search for "unparseable", "one-bucket", "does not parse", "not valid UTF" over plan.md, requirements.md, `skills/wiki-cycle`, `skills/wiki-report`: only plan.md:272 and checkpoints.md:213 match, and they agree.
  - Fixture docstring statements: "the left-undone-old-run case is not run here" (no old-run call in `main()`), "case A's folder is also graded by the left-undone-verbatim kind" (lines 282-285) and "an invented, a reworded and a dropped queue line" (`tamper_checks`, 192-215) are true.
  - Plan step 7's "the section equals the script's file" is carried by the verbatim kind (`check.py:3215-3216`, dispatch `:3726`) and graded on case A by the fixture; PENDING row 28's statement about it matches.

| Spec item | Verdict | Search or reading |
|---|---|---|
| 1 Step 3 Failures states the UTF-8 ruling, matches code and test | clear (nit above) | `_run_state.py:413-428`, `test_cycle_scope.py:1086-1092`, checkpoints.md:213 |
| 2 No sibling text contradicts it | clear | the grep above |
| 3 spec-31 composed labels correct and complete | found | check.py:3052, 3076, 3081, 3109, 3116, 3138, 3142, 3145, 3215, 3219, 3236, 3354 against COMPOSED |
| 4 Fixture docstring and comment statements true | found | the "PASS (composed)" statement is false for check.py:3354, 3142, 3081, 3145 |
| 5 Step 7 criterion carried and graded on case A | clear | check.py:3215-3216, 3726; fixture 282-285 |
| 6 PENDING row statements match the fixture | clear | PENDING.md:28 against `tamper_checks` and the verbatim run |

Well built: the ruling, the code and the test agree, and the tamper variants show the section-against-file check bites on an invented, a reworded and a dropped line.

## Change risk

No file is HIGH, so the lens was not run. Triage from the diff alone:

| File | Risk | Why | Part | Standards | Spec | Change risk |
|---|---|---|---|---|---|---|
| `tests/scripts/test_left_undone_fixture.py` | LOW | tests | 1 | in full | in full | not run |
| `tests/skills/PENDING.md` | LOW | docs | 1 | in part (the changed row, whole) | in part (the changed row, whole) | not run |

No high-risk file; the change-risk lens was not run. Out of the round (reviewed in earlier rounds and not moved since c66f855): every other file of the change, among them `scripts/_run_state.py`, `scripts/wiki-cycle-scope.py`, `tests/scripts/test_cycle_scope.py`, `tests/skills/wiki-cycle/check.py` and `cases.json`; nothing new is raised in them. `.do-code-change/` notes (plan.md step 3, checkpoints.md) were read as the spec and the ruling record, not as change.

needs-a-human: none (0). No finding touches auth, authz, tokens or sessions or a production-data migration. A spec resolved.

Summary. Standards: 2 findings (1 important, 1 suggestion); worst: the COMPOSED comment and docstring say the composed checks "cannot fail here" while several read the script's wording. Spec: 4 findings (2 important, 2 nit); worst: composed labelling is still wrong in both directions: "the cycle report's last section is Needs you" prints a plain PASS, and three checks reading the script's own wording print "PASS (composed)". The axes agree on the second point (Standards finding 1, Spec finding 2). The round-3 fixes themselves landed (rename at line 189, three added prefixes, plan step 3 and the ruling, PENDING's "and"); the findings above are residual labelling items in the same fixture lines. Worth acting on before the change moves on. Change risk: lens not run, no HIGH file.

The five confirmations are under `## Standards` / `## Spec` as their claims fall; as asked, in one place:

Checks made:
  - 1. spec-3 (round 1): confirmed. The `left-undone-verbatim` kind exists (check.py dispatch 3726, `_lu_copy_checks` 3206-3219 compares the section's lines with left-undone.txt's), and the paid run `20261118-154943-red-green-b7401bb` reports it "red then green" on sonnet and opus (old copy failed for the right reason). Caveat stays unverified: the report does not record which check.py commit it graded.
  - 2. standards-14 (round 1): confirmed. Every `Left undone: <N> queue(s)` header in tests/scripts/test_cycle_scope.py (a grep of all 28 sites) is a literal; line 1763 computes `n` from the output but compares it with the literal 9 beside the literal header.
  - 3. standards-15 (round 1): confirmed in part. "PASS (composed)" is printed through COMPOSED for the composer's checks, but the mechanism is both over- and under-inclusive (Spec findings 1 and 2, Standards finding 1).
  - 4. spec-28 (round 3): confirmed. Plan step 3's Failures bullet and checkpoints.md:213 state the UTF-8 ruling that `session_buckets` implements (`_run_state.py:425-428`); one wrong function name in the bullet (Spec nit).
  - 5. spec-31 (round 3): confirmed that the three named shape-only checks and the 'Nothing.' check now print "PASS (composed)" (the fix is in COMPOSED, not check.py); the sibling search found the residual items in Spec findings 1 and 2.

VERDICT: Standards FINDINGS · Spec FINDINGS · Change risk NOT RUN · needs-a-human 0
