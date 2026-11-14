# Review report, round 3 (focused): 240-unfinished-run-check

Fixed point `08d9c6cb7db1df6d731976fc00fd326fde8e0b09` resolves (`git log` lists the run's commits since it); the diff against it is non-empty (13 files, one part per axis, far under 3,000 lines); no untracked files outside `.do-code-change/`. Focused round: the scope is the 10 files in `round3-changed.txt` (what fix round 2 moved), read as the diff from the round-2 commit `efb6ab0` to the working tree, plus the sibling sites of each addressed finding. Spec source: `plan.md` and `requirements.md` (both read; both already carry the rulings and the `--topic <notebook>` forms). The prescan ran clean, so the Standards lens raised no dates, review ids or width in `.py` files. Lenses ran as `code-reviewer-lens`, foreground flag set, default tier; both reported after a launch notice and were waited for. Items left open with reasons (standards-17 to -20, spec-12, -15, -17; round-1 standards-4, -6, -7, -14, spec-4, -7, -8, -9) were not re-raised; the Standards lens found none of them made worse.

## Standards

- [important] `tests/skills/wiki-cycle/check.py:2292` [eval-case-writer] — R15 softened assertion: `not re.search(way_out("resume", oid), corpus),` replaced the old `r"--resume\s+`?(?:" + re.escape(oid) + r"|<)"`, whose `|<` branch failed a generic `--resume <cycle_id>` offered for a run with no scratchpad; that generic offer now passes.
  - Note for the reader: round-2 spec-14 asked for exactly this `|<` drop, and the Spec lens finds it clear. The axes differ here; both are reported as given. The Standards point is that adding `<notebook>` to the printed line did not require the loosening.
  - Fix: `not re.search(way_out("resume", oid) + r"|--resume\s+`?<", corpus),`, or record in the check's docstring that a generic `--resume <cycle_id>` is allowed.
- [suggestion] `tests/skills/wiki-cycle/check.py:2309` [eval-case-writer] — S2 `not re.search(r"--(?:resume|mark-interrupted)[\s=]+[`\"']?" + re.escape(i), corpus)` re-spells the pattern `way_out` builds at `:2246`, in the same function.
  - Fix: `not re.search(way_out("resume", i) + "|" + way_out("mark-interrupted", i), corpus)`.
- [suggestion] `tests/skills/wiki-cycle/check.py:2239` and `:2286` [eval-case-writer] — the check is stricter than the rule it tests: `oid in final` ("named in the final reply") against SKILL.md `:63` "tell the user each line now", which an interim text satisfies; a run that told the user at Step 0 and left the id out of its final reply now fails. The old check read `reply` (all assistant text).
  - Fix: keep `reply` for "told the user" and add a separate final-reply check if wanted. (Same-expression note, S2: the `final` expression is written in five other suites; each is self-contained, so a note only.)
- [nit] `scripts/wiki-cycle-scope.py:558` and `:560` — S2 the literal `r"^## Decisions log$"` appears twice in `mark_interrupted`.
  - Fix: one module constant.
- [nit] `scripts/wiki-cycle-scope.py:521-523` (and the module docstring at `:86`) — C2 the docstring says a run folder is `_inbox/reports/<date>/<YYYY-MM-DD>-<NN>/`, but the guard at `:528` now also requires the id's own date.
  - Fix: add "under the id's own date" to both.

Unverified:
- `tests/skills/wiki-cycle/baseline-opus.json` `earlier-complete-and-interrupted-runs-not-named`: the key `"run: read reference.md before writing the scratchpad": true` was removed by the re-merge from run `164536`, while the same key stays in every other Opus case and in the sibling new case (and Sonnet's baseline has none). Whether it hides a failed trajectory check or is a merge artifact (the rule `trajectory_rules.py:21` only fires on a `Write` of the scratchpad) is not settled; the opus result for that case in run `164536` would settle it.
- `scripts/wiki-cycle-scope.py:204` and `:264` glob `*/*/lint-semantic.json` and `*/*/synthesis.json` with no date check; whether a misfiled run folder changes their cut-off was not traced.
- Baseline JSON validity after the re-merge: read at the changed keys only, not parsed (no shell in the lens).

Checks made:
- standards-15 addressed: `wiki-cycle-scope.py:528` `if d != run_folder_of(nb, d.name):`; `run_folder_of` (`:543-545`) is the one builder of the id path, used at `:550`, `:569`, `:581`; the new test `unfinished_skips_a_folder_filed_under_another_date` (`test_cycle_scope.py:390-398`) lists the misfiled folder without the guard. (The Spec lens's first finding disputes the behaviour the guard chose, not that it is applied.)
- standards-16 addressed: the script's own sentences `"not both and not neither"` (`:710`) and `"--mark-interrupted needs --reason"` (`:712`) are what the tests assert (`:510`, `:519`, `:530`); argparse's usage line prints neither, so they bite. The remaining stderr check at `:500` matches the bad id, not an option name.
- Round-2 items left open (standards-17 to -20, round-1 standards-4, -6, -7, -14) not made worse by the fix.

| Rule | Verdict | Search |
|---|---|---|
| S2 | found | `check.py:2309` vs `:2246`; script `:558/:560`; `final` expression across suites |
| S1, S3-S11, S12, G25, F3, R1, N7, C5 | clear (S12 n/a, no subclass) | every added identifier and function read in context |
| R26 | clear | callers of `way_out`, `run_folder_of`, the new test function: all used |
| C1, C3, R2 | clear | added comments and docstrings read; no TODO/FIXME |
| C2 | found | `:521-523`, `:86` |
| N2, N3, N5, N6, R3 | clear | new names read; "close it" / "mark-interrupted" grep in the changed skill pages |
| S13, G34, S14, G19, G28, G29, R4, G31, G16, Dead Code | clear | `cmd_unfinished`, `mark_interrupted`, `way_out`, `_check_unfinished` read |
| G3, G33, G26, G2 | clear | EOF-heading and misfiled-folder tests cover the new boundaries; `now_stamp()` used |
| T1, T3, T5, T6, R12, R13, R14, T4 | clear | each new branch has a test that fails without it; no skips; R14 order dependence ruled in round 1 |
| R15 | found | `check.py:2292` |
| PY1-PY3, PY7, PY8, PY10, PY11 | clear | changed `.py` lines read |
| PY9 | clear | the EOF test fails on the old regex; the misfiled test fails without the guard; error assertions match script sentences |
| PY4-PY6; Classes, Error handling, Concurrency, Refactoring sections | n/a | no async; sections not met by this diff |

Read depth: changed lines of the ten moved files read (see the file table); `wiki-cycle.md`, `wiki-report/SKILL.md` and `PENDING.md` read in the diff only.
Well built: each new test fails without the fix it covers, the error assertions match the script's own sentences, and `run_folder_of` is the single builder of the run-folder path.

## Spec

- [important] `scripts/wiki-cycle-scope.py:528-529` — a run folder filed under the wrong date is dropped without a line in the listing, the report or the close-out.
  - Intent: plan.md:16 "run folders are directories two levels under `_inbox/reports/` whose name matches `^\d{4}-\d{2}-\d{2}-\d{2}$`, the current one (`rf`) left out"; plan Step 1 "a run folder with no report and no scratchpad is printed".
  - Implemented: `if d != run_folder_of(nb, d.name):    # filed under another date: the close-out would refuse it` then `continue`; the test `test_cycle_scope.py:390-398` pins the exclusion; the close-out refuses such a folder at `:569`.
  - Affected: a dead run filed under a wrong date is never named, never reaches Needs you and cannot be closed, which is the failure lesson #10 exists to catch. The fix narrows the plan's definition without a recorded ruling. (Round-2 standards-15 itself suggested the skip; the axes pull in different directions and both are reported.)
  - Fix: list the folder and let the close-out find it by searching `_inbox/reports/*/<cycle_id>`; or, if the narrowing is wanted, record it as a Decision in requirements.md and tell the user such folders are invisible.
- [suggestion] `tests/skills/wiki-cycle/check.py:2239` and `:2286-2287` [eval-case-writer] — the Step 0 "tell the user" check tests only the final reply, not the timing SKILL.md `:63` asks for ("tell the user each line now"); the harness keeps text and tool calls in separate lists (`run_skill_test.py:285`, `:288`), so no check can order a text before the Step 0 call.
  - Intent: SKILL.md `:63`. Affected: the eval signal for "now"; a final reply naming the id from Needs you passes even if Step 0 never told the user.
  - Fix: keep the final-reply check and say in PENDING.md or the check's docstring that the timing is untested; testing it needs a text-order record in `parse_events`.
- [suggestion] `CHANGELOG.md:16` — the corrected "What" entry still carries bare forms beside the fixed ones: `unfinished --run-folder <rf>`, "(`/wiki-cycle --resume` only for a folder with a scratchpad ...)" and "`unfinished --mark-interrupted <cycle_id> --reason \"<why>\"` closes one" sit in the same sentence as the added "(the printed lines carry `--topic <notebook>` ...)".
  - Intent: spec-11's fix says the notebook-carrying forms are in the CHANGELOG. Affected: a reader copying the entry's commands gets a form that acts on the default notebook; spec-11 is only partly addressed there.
  - Fix: write `/wiki-cycle <notebook> --resume` and `--topic <notebook> unfinished --mark-interrupted` in that sentence.
- [nit] `scripts/wiki-cycle-scope.py:95` — the docstring prose "`--mark-interrupted <cycle_id> --reason \"<why>\"` closes one" has no `--topic`; it is not a printed line.
  - Fix: `--topic <notebook> unfinished --mark-interrupted`, matching `:14-15` and `:89`.

Unverified:
- `tests/skills/PENDING.md:28` cites run `20261113-164536-red-green-1d6b03c`, "red then green on both models"; the run folder is outside the repo and was not read (producer claim).
- The `baseline-opus.json` key removal (see Standards Unverified).
- Whether the existing `test_cycle_scope.py` checks stay green (plan Invariant 1) is a producer claim; a review runs no test.

Checks made:
- plan.md line 16 read whole: it carries `/wiki-cycle <notebook> --resume` and `--topic <notebook> unfinished --mark-interrupted`; requirements.md `:27` carries the `--topic` form (grep of both).
- spec-11 mostly addressed: script `:580-583` prints the notebook from `args.topic_name` (set at `:717` from the same `topic` the listing used); `/wiki-cycle <notebook>` is a form SKILL.md `:25` accepts; SKILL.md `:63`, wiki-report `:276`, the usage page and the tests carry it; SKILL.md `:175` says "the way out as Step 0 printed it" and `reference.md:23` names no command. Residue: the two findings above (CHANGELOG, docstring `:95`).
- spec-16 addressed: `mark_interrupted` traced for a heading mid-file, last with newline, last without newline and missing: correct in each; the new test (`test_cycle_scope.py:476-488`) pins the no-newline case.
- spec-13 addressed in form (harness has `run["result"]` and `run["texts"]`, `run_skill_test.py:269-300`); the timing caveat is the suggestion above.
- spec-14 addressed: `way_out` matches the printed forms and not generic `--resume <cycle_id>` text.
- Rulings not reversed: resume only with a scratchpad (`:580-581`, SKILL.md `:63`, wiki-report `:276`, usage page, test `:368`); one cycle per notebook with no lock or age check (none in `:520-586`, `:548-563`; stated at SKILL.md `:182`).

| Spec item | Verdict | Evidence |
|---|---|---|
| spec-11 notebook in printed lines | found (residue) | grep of `--resume` / `--mark-interrupted` outside `.do-code-change` and baselines; CHANGELOG and docstring `:95` |
| spec-13 final reply | found (suggestion) | `check.py:2239`, `:2286` |
| spec-14 `way_out` | clear | `check.py:2246` against `test_cycle_scope.py:364`, `:368` |
| spec-16 heading | clear | `mark_interrupted` traced, four positions |
| Ruling 1, ruling 2 | clear | cited above |
| Plan Step 1 listing | found | misfiled folders (important) |
| Plan Step 2 mark-interrupted | clear | `:566-574`, `:709-712` |
| Plan Step 3 cases | clear (run unverified) | `cases.json:62-63`, `check.py:2224-2311` |
| Invariants | clear (suite unverified) | listing writes only `rf` (`:575-578`); `mark_interrupted` writes one scratchpad |
| Plan Step 4 | n/a | install deliberately at the finish |

Read depth: `CHANGELOG.md` line 16 and `check.py` `:2224-2311` in full; the script, SKILL.md, the usage page, wiki-report SKILL.md, test_cycle_scope.py, PENDING.md and the baselines read at the changed functions and hunks (the lens's table marks them `in part`).
Well built: the printed close-out and resume lines take the notebook from the same `args.topic_name` the listing used; the heading fix handles all four heading positions and the new test pins the no-newline case; `way_out` matches only this run's id.

## Change risk

| File | Risk | Part | Standards | Spec | Change risk |
|---|---|---|---|---|---|
| `scripts/wiki-cycle-scope.py` | MEDIUM (new public CLI, rewrites a scratchpad) | 1 | in full (changed lines) | in part (changed functions) | — |
| `skills/wiki-cycle/SKILL.md` | MEDIUM (procedure the cycle follows) | 1 | in part (lines 60-76) | in part (63-69, 175) | — |
| `skills/wiki-report/SKILL.md` | LOW | 1 | in part (diff only) | in part (276) | — |
| `skills/wiki-cycle/wiki-seed/wiki-cycle.md` | LOW | 1 | in part (diff only) | in part (43) | — |
| `CHANGELOG.md` | LOW | 1 | in full | in part (line 16) | — |
| `tests/scripts/test_cycle_scope.py` | LOW | 1 | in full (changed lines) | in part | — |
| `tests/skills/wiki-cycle/check.py` | LOW | 1 | in full (changed lines) | in full (2224-2311) | — |
| `tests/skills/wiki-cycle/baseline-opus.json`, `baseline-sonnet.json` | LOW | 1 | in part | in part | — |
| `tests/skills/PENDING.md` | LOW | 1 | in part (diff only) | in part (diff only) | — |

Files the earlier rounds reviewed and the fix did not move (`skills/wiki-cycle/reference.md`, `skills/wiki-report/wiki-seed/wiki-report.md`, `tests/skills/wiki-cycle/cases.json`) are out of this round: nothing raised there. No high-risk file (no auth, sessions, crypto, payments, external call, migration or removed validation); the change-risk lens was not run.

## needs-a-human

None. No auth, authz, token or session handling, and no production-data migration.

## Summary

Standards: 5 findings (1 important, 2 suggestion, 2 nit; the first three are for the eval-case-writer; worst: the no-resume check lost its generic `--resume <...>` branch, which the Spec axis counts as the fix of spec-14, so the axes differ). Spec: 4 findings (1 important, 2 suggestion incl. 1 for the eval-case-writer, 1 nit; worst: the listing now silently drops a run folder filed under another date, narrowing the plan's definition, and the close-out refuses it, so such a run is never named). Change risk: not run. Of the round-2 findings marked addressed, standards-15, standards-16, spec-16, spec-13 and spec-14 are addressed in form; spec-11 is addressed in the script, SKILL.md, wiki-report, the usage page and the tests, with the CHANGELOG sentence and docstring `:95` still carrying bare forms. Both rulings hold. The axes agree the misfiled-folder rule (listing, close-out, docstring) should be one stated definition: the Standards docstring nit and the Spec important finding point at the same lines. Worth acting on the misfiled-folder finding and the CHANGELOG forms; findings tagged [eval-case-writer] go back to that agent. This is the third round, the retry ceiling.

Risks or assumptions: several files are marked `in part` by the lenses because they read changed hunks and context, not whole current files; no read-depth retry was spawned, so a reader should treat those rows as read at the changed lines only. The lenses saw the fix-round-2 delta (from `efb6ab0`), not a fresh diff against the fixed point.

VERDICT: Standards FINDINGS · Spec FINDINGS · Change risk NOT RUN · needs-a-human 0
