# Review report, round 2 (focused): 240-unfinished-run-check

Fixed point `08d9c6cb7db1df6d731976fc00fd326fde8e0b09` resolves; merge-base with HEAD is the same commit; no untracked files outside `.do-code-change/`; the diff is non-empty (12 files, about 640 changed lines, one part per axis). Focused round: the scope is the 12 files in `round2-changed.txt` plus the sibling sites of each addressed round-1 finding. Spec source: `plan.md` and `requirements.md` (rewritten in place with the rulings). The prescan (dates, review ids, width) ran clean, so the Standards lens raised none of those in `.py` files. Lenses ran as `code-reviewer-lens`, foreground flag set, default tier, each reporting after a launch notice. The Spec lens marked four files `in part`, so it got its one retry on those four files, which read them in full. Items standards-4, -6 (as first raised), -7, -14 and the plan nits were not re-raised, as briefed.

## Standards

- [suggestion] `scripts/wiki-cycle-scope.py:524` — S2 sibling of round-1 standards-3, not converted to the helper: `for d in sorted((nb / "_inbox" / "reports").glob("*/*")):` while `run_folder_of` (`:540-542`) builds `nb / "_inbox" / "reports" / cycle_id[:10] / cycle_id`. A run filed under a different date folder is listed with a close-out command that `cmd_unfinished` refuses (`:566`, exit 2).
  - Fix: in `unfinished_runs` skip any `d` where `d != run_folder_of(nb, d.name)`, so listing and close-out use one rule.
- [suggestion] `tests/scripts/test_cycle_scope.py:486` (also `:495`, `:506`) — PY9 the error assertions pass on argparse's own usage text: `p.returncode == 2 and "--reason" in p.stderr`, and `"--run-folder" in p.stderr and "--mark-interrupted" in p.stderr`. The subparser's usage line already prints those option names, so the checks hold if the error sentence is deleted.
  - Fix: assert the sentences: `"needs --reason" in p.stderr` (script `:709`) and `"not both and not neither" in p.stderr` (script `:707`).
- [suggestion] `skills/wiki-cycle/SKILL.md:63` and `:175`, `skills/wiki-report/SKILL.md:276`, `skills/wiki-cycle/wiki-seed/wiki-cycle.md:43` — S2/S7 the ruling's rule "resume only for a run with a scratchpad" is now restated in four prose places plus the script (`:577`). Raised because the fix added the clause to Step 8, the report template and the usage page, which widens the duplication that standards-6 declined.
  - Fix: state it once (Step 0) and have Step 8, the report and the usage page say "the way out Step 0 printed".
- [nit] `scripts/wiki-cycle-scope.py:708` — G2 `--reason` given with `--run-folder` passes every check and is ignored.
  - Fix: also refuse `args.reason and not args.mark_interrupted` with `un.error(...)`.
- [nit] `tests/skills/wiki-cycle/check.py:2253` [eval-case-writer] — G16/G17 `_runs_mark_interrupted` is a shell-text parser nested inside `_check_unfinished`, while the file's other helpers (`_needs_you`, `_unfinished_ids`) sit at module level.
  - Fix: move it to module level beside `_needs_you`.
- [nit] `tests/skills/wiki-cycle/check.py:2168` [eval-case-writer] — R3 the `earlier` value `"open"` / `"complete-and-interrupted"` against the kind, skill and script word "unfinished". May predate round 1.
  - Fix: rename the value to `"unfinished"` in check.py and cases.json.

Unverified:
- `unfinished_without_a_reports_folder` restores the renamed folder with no try/finally (`reports.rename(away)` ... `away.rename(reports)`); if `run()` raises, the notebook stays renamed. Round-1 status unknown; not run.
- The new `drop` set (check.py `:2227`) and the parser could not be told apart from round-1 code by the lens (diff is against the fixed point); reviewed as fix-round code.
- Baseline JSON validity: the lens read the joins and file ends but could not parse it (no shell). See Checks made.

Checks made:
- Round-1 items against the diff, one by one. standards-1 addressed: `git diff --stat` on cases.json is 3 insertions, 1 deletion (the old last line gains a comma, two case lines appended). standards-2 addressed as ruled: no lock or age check in the code; the one-cycle rule is in SKILL.md `Don't` list (`:182`), Step 0 text, the script docstring and the usage page; a grep of `skills/wiki-cycle` for concurrent / second cycle / another cycle found nothing that permits overlap. standards-3 partly addressed (see the first finding). standards-5, -8, -9, -10, -11, -12, -13 addressed (no `RUN_ID` left in the repo outside `.do-code-change/`; one `sorted`; no unused assignment; two new exit-2 tests; first line `#` asserted; the shell-variable alternative gone).
- The two new case ids are in both baseline files, each as a whole entry with every check true; the renamed case's old id appears nowhere in the repo; the PENDING row carries "Baselines merged per case from `161525`".

| Rule | Verdict | Search |
|---|---|---|
| S1, S3, S4, S6, S8-S12, G25, F3, R1, N7, C5 | clear | each added function and identifier read in the diff |
| S2, S7 | found | glob at `:524` against `run_folder_of`; four prose restatements |
| S5 | clear | `CYCLE_ID` defined once, used at `:525`, `:566` |
| R26 | clear | callers: `main` dispatch, check.py dispatch |
| Comments C1-C3, R2 | clear | docstrings read against the code |
| Names N2, N3, N5, N6 | clear | added names read |
| R3 | found | `earlier` value (nit) |
| Functions S13, G34, S14, G19, G28, G29, R4, G31, Dead Code | clear | read; imports `shutil`, `timedelta` used |
| G16 | found | nested parser (nit) |
| Classes S16, G8, G7, G17, G18, G13, S17, S18, R5, R6, G35, G1 | clear | no class added; `CYCLE_ID` immutable |
| Error handling R7-R11, G4 | clear | `unknown` status is shown, not a failure return; R10 see Unverified |
| Boundary G3, G33, G26 | clear | empty, none and header-only cases tested |
| G2 | found | `--reason` ignored with `--run-folder` (nit) |
| Tests T1, T3, T4, T5, T6, R12, R13, R15 | clear | each new branch has a test |
| R14 | clear | order dependence declined in round 1, not raised |
| PY9 | found | argparse usage text satisfies the assertions |
| PY1-PY3, PY7, PY8, PY10, PY11 | clear | added lines read |
| PY4-PY6, Concurrency | n/a | no async or threads |
| Refactoring R21-R25 | clear | diff adds only; R25 round-1 finding fixed |

Read depth: all twelve files `in full` (every changed line, via the diff; baselines plus file ends).
Well built: one flag or the other is enforced before any write; the listing and the close-out share `run_folder_of`; the lock-free ruling is stated where the listing relies on it and nothing contradicts it.

## Spec

- [important] `scripts/wiki-cycle-scope.py:577-580` and `skills/wiki-cycle/SKILL.md:63` — the printed close-out (and the resume line) omits `--topic`, so the command is not complete for a cycle on a notebook other than the project's. Note: the clause predates the fix and the plan's own sample (`plan.md:16`) omits it too; it is in lines the fix reshaped (the resume conditional) and was not raised in round 1, so the caller may treat it as new rather than a regression.
  - Intent: docstring `:15` gives `--topic N unfinished --mark-interrupted`; SKILL.md Step 0 takes a `<notebook>`; plan Invariants, the check changes an earlier folder "only through `--mark-interrupted` on the one named".
  - Implemented: `f'wiki-cycle-scope.py unfinished --mark-interrupted {cid} --reason "<why>"'` (`:579-580`); SKILL.md `:63` the same. The topic falls back to the project's notebook (`:710`).
  - Affected: a user pasting the line for another notebook closes the wrong run when the same `<date>-01` exists there, otherwise gets exit 2.
  - Fix: print `--topic <notebook>` in both lines (the script has the topic before dispatch) and in SKILL.md `:63`; amend the plan's sample.
- [suggestion] `scripts/wiki-cycle-scope.py:115` (print branch, `:577` in the file as numbered by the retry lens) — a scratchpad whose Status is `completed` (or has no Status line) and no report is still offered `--resume`; no spec text says whether that is right. This is the remaining part of round-1 spec-1; the ruling covered only the no-scratchpad case.
  - Intent: plan Step 1, "`resume: /wiki-cycle --resume <cycle_id>` only when the folder has a scratchpad"; SKILL.md "`--resume <cycle_id>`: ... continue from the phase after the last `done`"; `completed` is set only after the Step 8 report.
  - Implemented: `if (run_folder_of(nb, cid) / "scratchpad.md").is_file()`, true for `completed`.
  - Affected: a user offered resume on a run with no phase left and no report.
  - Fix: state in requirements Decision 2 whether `completed` with no report is resumed or only closed, and make the line match.
- [suggestion] `tests/skills/wiki-cycle/check.py:2237` [eval-case-writer] — the "Step 0 told the user" check reads every assistant message (`reply = run["text"]`), so a later mention of the id passes even when Step 0 never told the user.
  - Intent: SKILL.md `:63`, "tell the user each line now".
  - Fix: check the assistant text after the Step 0 `unfinished` call, or the final reply.
- [suggestion] `tests/skills/wiki-cycle/check.py:2283` [eval-case-writer] — `r"--resume\s+`?(?:" + re.escape(oid) + r"|<)"`: the `|<` alternative fails "no resume is offered" on any generic `--resume <cycle_id>` text in a reply, which SKILL.md `:63` itself contains.
  - Intent: Decision 2 ruling, resume only for a folder with a scratchpad.
  - Fix: drop the `|<` alternative and match only the earlier id.
- [nit] `scripts/wiki-cycle-scope.py:113` — the plan invariant "never deletes or edits an earlier run folder except through `--mark-interrupted`" is not enforced for an earlier folder passed as `--run-folder` (`write_scope` writes into any folder named). SKILL.md always passes the current one, so this is misuse only. Round-1 spec-9 asked "correct the pin text; guard or document": only the pin text was done.
  - Fix: reject a `--run-folder` under `_inbox/reports/` whose id is not the current one, or document it in the docstring.
- [nit] `scripts/wiki-cycle-scope.py:555-556` — a scratchpad ending in `## Decisions log` with no trailing newline gets a second heading (`re.search(r"^## Decisions log\n", ...)`). Intent: plan `:17`, "adding the heading if missing". Round-1 unverified item, now confirmed by reading the regex; not run.
  - Fix: accept end-of-string as the heading match.
- [nit] `tests/skills/wiki-cycle/check.py:2263-2265` [eval-case-writer] — a quoted flag such as `'--mark-interrupted'` is stripped as text, so a real close can pass "no command closes an earlier run"; the folder-untouched check still catches a changed or added scratchpad.
  - Fix: strip only the quoted `--reason` value.

Unverified:
- Red/green run `20261113-161525-red-green-1d6b03c` and the 84/84 suite result are producer claims (PENDING row, checkpoints); the run folder is outside the repo. The earlier checkpoint said case 2 passed on the old copy on Opus; round 3 says red then green on all four, so the check changes since then are what the claim rests on.
- `--mark-interrupted` on a folder that already has its report: line `:566` checks only that the folder exists; the spec is silent.
- Requirements' "5 of 37 run folders with no report" not re-checked.
- Plan Step 4's refresh and `--mode status` are not in the diff, by design (moved to the finish).

Checks made:
- Round-1 Spec findings: spec-1 (no-scratchpad part) addressed: `cmd_unfinished` prints resume only when `scratchpad.md` exists; SKILL.md Step 0 and Step 8, wiki-report SKILL.md, the usage page, CHANGELOG, plan Step 1 and requirements Decision 2 all say the same; `test_cycle_scope.py` pins resume for the in_progress folder only; the eval case checks no resume for the no-scratchpad folder. spec-2 addressed (baselines, see Standards Checks made; run result unverified). spec-3 addressed in form (see the check.py suggestion). spec-5 addressed (wiki-report usage page names the item). spec-6 addressed (plan Testing Decisions says two cases). spec-10 addressed (`earlier` validated in `_unfinished_ids`).
- spec-4, -7, -8, -9: the brief calls these declined, but checkpoints.md says they were taken in the artifacts. Checked in the artifacts: requirements Exclusions reads "beyond Decision 3's one scratchpad line and one Needs-you line"; plan's output-format line matches the printed form; the wiki-report template says "one line per run"; plan Invariants' pin text now names the folder-untouched check. The ledger still lists them `open` because the artifacts carry no fingerprint, so the ledger keeper may need to close them. The no-edit guard part of spec-9 is the nit above.
- Rulings applied as recorded: Decision 2 and plan Step 1 rewritten for resume-only-with-scratchpad; the one-cycle-per-notebook rule has no lock or age check in code (grep of the script for lock/age found none) and is stated in the SKILL.md Don't list, the docstring, the usage page and requirements Exclusions.

| Spec item | Verdict | Evidence |
|---|---|---|
| Plan Step 1: listing, ways out, none, missing reports folder | found | `--topic` omission; completed-scratchpad resume |
| Plan Step 2: `--mark-interrupted`, refusals | clear (nit) | `:83-109`, `:139-142`; tests; heading nit |
| Plan Step 3: cases, baselines, template | clear (run unverified) | both ids in both baselines; template line |
| Plan Step 4: usage page, CHANGELOG | clear | wiki-cycle.md `:204`; CHANGELOG `:13` |
| Plan Invariants | found (nit) | `write_scope` into an earlier `--run-folder` |
| Out of Scope / Exclusions | clear | no resume, delete or repair path added |
| Requirements Decisions 1, 2, 3 | clear except Decision 2's completed case | see findings |
| Ruling on spec-1 | clear for no scratchpad; remainder found | see above |
| Ruling on standards-2 | clear | grep of script and skills |
| Fix code: one-of-two flags, `run_folder_of`, `CYCLE_ID` | clear | `main`, tests, grep for `RUN_ID` |

Read depth: nine files `in full` on the first pass; `scripts/wiki-cycle-scope.py`, `skills/wiki-cycle/SKILL.md`, `cases.json` and `check.py` `in part` on the first pass and `in full` on the retry.
Well built: the listing and the close-out for a folder with no scratchpad follow the plan and both rulings line for line, and the mark path validates the id before any write.

## Change risk

| File | Risk | Part | Standards | Spec | Change risk |
|---|---|---|---|---|---|
| `scripts/wiki-cycle-scope.py` | MEDIUM (new public CLI, rewrites a scratchpad) | 1 | in full | in full (retry) | — |
| `skills/wiki-cycle/SKILL.md` | MEDIUM (procedure the cycle follows) | 1 | in full | in full (retry) | — |
| `skills/wiki-report/SKILL.md` | LOW | 1 | in full | in full | — |
| `skills/wiki-cycle/wiki-seed/wiki-cycle.md` | LOW | 1 | in full | in full | — |
| `skills/wiki-report/wiki-seed/wiki-report.md` | LOW | 1 | in full | in full | — |
| `CHANGELOG.md` | LOW | 1 | in full | in full | — |
| `tests/scripts/test_cycle_scope.py` | LOW | 1 | in full | in full | — |
| `tests/skills/wiki-cycle/check.py` | LOW | 1 | in full | in full (retry) | — |
| `tests/skills/wiki-cycle/cases.json` | LOW | 1 | in full | in full (retry) | — |
| `tests/skills/wiki-cycle/baseline-opus.json`, `baseline-sonnet.json` | LOW | 1 | in full | in full | — |
| `tests/skills/PENDING.md` | LOW | 1 | in full | in full | — |

`skills/wiki-cycle/reference.md` was reviewed in round 1 and not moved by the fix: out of this round, nothing raised there. No high-risk file (no auth, sessions, crypto, payments, external call, migration or removed validation); the change-risk lens was not run.

## needs-a-human

None. No auth, authz, token or session handling, and no production-data migration.

## Summary

Standards: 6 findings (3 suggestion, 3 nit; 2 nits for the eval-case-writer; worst: the listing's glob and the close-out's path rule can disagree, and the argparse-usage-text assertions pass for the wrong reason). Spec: 7 findings (1 important, 3 suggestion incl. 2 for the eval-case-writer, 3 nit incl. 1 for it; worst: the printed close-out command omits `--topic`). Change risk: not run. Of round 1's twelve findings marked addressed, all but standards-3 are addressed in full; standards-3 leaves one sibling site, and the completed-scratchpad part of spec-1 is not covered by the ruling. Both rulings were applied as recorded. The axes agree that the listing, the printed commands and the rule that `--mark-interrupted` and `--resume` act on a run folder should use one definition. Worth acting on the `--topic` finding and the two path-rule suggestions; findings tagged [eval-case-writer] go back to that agent.

VERDICT: Standards FINDINGS · Spec FINDINGS · Change risk NOT RUN · needs-a-human 0
