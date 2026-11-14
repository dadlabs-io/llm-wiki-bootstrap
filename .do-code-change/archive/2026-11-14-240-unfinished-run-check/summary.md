# 2026-11-14 240-unfinished-run-check — a cycle's Step 0 names earlier runs that never finished

## TL;DR
`wiki-cycle-scope.py unfinished` lists every earlier run folder with no run-cycle report (unless its scratchpad says interrupted), with a close-out command for each and a resume command only when the folder has a scratchpad; `--mark-interrupted <id> --reason` closes one. `/wiki-cycle` Step 0 runs it and the report's Needs you lists what it found, so a cycle that dies before its report (2026-07-17-01, pre-mortem lesson #10) is never silent again. Five review rounds (two past the ceiling, on Mark's word); prove_tests_bite.py could not reach `scripts/`, so a hand mutation pass (86 mutants, 81 killed) added four tests and the layer stayed a named FAIL Mark approved. Kept on main and installed.

## What changed
- A cycle's Step 0 helper names earlier unfinished runs
- A flagged run can be closed
- The skill runs it and the report shows it
- Docs

New tags: `wiki-cycle` (skills).

## Why: decisions and exclusions
1. **What counts as unfinished** (matters most). (Ruled 2026-11-14, at the review ceiling: a run folder is one filed under its own id's date, `_inbox/reports/<id date>/<id>/`, as every cycle files it; a folder moved by hand under another date is not listed, since the close-out could not find it either.) Recommended: a run folder (name `<YYYY-MM-DD>-<NN>`, not this run's) with no `<cycle_id>-run-cycle-report.md`, unless its scratchpad says `interrupted`. That is the lesson as written, and it catches the original incident (no scratchpad at all). Alternative: only folders whose scratchpad says `in_progress`: quieter (1 of today's 5), but misses a run that died before writing a scratchpad, which is what happened on 2026-07-17.
2. **How a flagged folder stops being flagged.** (Ruled 2026-11-13, review round 1: resume is offered only for a folder that has a scratchpad; a folder with none gets only the close-out.) Recommended: `wiki-cycle-scope.py --topic <notebook> unfinished --mark-interrupted <cycle_id> --reason "<why>"` sets its scratchpad's status to `interrupted` with the reason in its Decisions log (writing a short scratchpad when there is none); `/wiki-cycle <notebook> --resume <cycle_id>` finishes it the other way. Alternative: look back only 30 days, so old folders age out with no command; but a recent hand-run step folder would be named every cycle for a month.
3. **Where it shows.** Recommended: Step 0 prints each folder and the two ways out, writes `unfinished-runs.txt` in the run folder and a line in the scratchpad; the report's ⚠️ Needs you carries one line per folder. Alternative: Step 0 output only (easy to miss in a long run).

- Nothing is resumed, deleted or repaired automatically: the check only names the folders and what to do.
- Not lessons #11, #12 or #9 (later changes on card #240).
- No lock against two cycles at once: one cycle per notebook at a time (Mark, 2026-11-13); the skill states the rule.
- No change to how a run writes its report or scratchpad, beyond Decision 3's one scratchpad line and one Needs-you line.

## What the review found
- spec-1 (round 1, important): [important] `scripts/wiki-cycle-scope.py` (`unfinished_runs` no-scratchpad branch, and the printed line in `cmd_unfinished`) — the "resume" way out is… — addressed
- spec-2 (round 1, important): [important] `tests/skills/wiki-cycle/baseline-sonnet.json`, `baseline-opus.json` — plan Step 3's done criterion ("red on the installed skill and green… — addressed
- spec-3 (round 1, suggestion): [suggestion] `tests/skills/wiki-cycle/check.py` (`corpus = "\n".join([reply, rtext, utext, stext])`) — the naming checks read a merged corpus, so Step… — addressed
- spec-4 (round 1, suggestion): [suggestion] `skills/wiki-cycle/reference.md` (scratchpad template line), `skills/wiki-cycle/SKILL.md` Step 8 vs requirements Exclusions "No change to… — open
- spec-5 (round 1, suggestion): [suggestion] `skills/wiki-report/wiki-seed/wiki-report.md:22` — the usage page's Needs-you list omits the new item. Stale intent (plan Scope and Step… — addressed
- spec-6 (round 1, suggestion): [suggestion] `tests/skills/wiki-cycle/cases.json` (second new case) — plan Testing Decisions names "one new case"; two were added. The second is the n… — addressed
- spec-7 (round 1, nit): [nit] `plan.md` format line vs `cmd_unfinished` print — the plan's `(<why>: no scratchpad | ...)` has a slot the printed `({w})` does not fill. Fix: a… — open
- spec-8 (round 1, nit): [nit] requirements Decision 3 "one line per folder" vs the wiki-report template's one bullet "each id, why, and the two ways out". Fix: say "one line… — open
- spec-9 (round 1, nit): [nit] `plan.md` Invariant "pinned by step 2's Failures bullet" — that bullet lists only unknown-id and missing-reason; the listing's no-edit is checke… — open
- spec-10 (round 1, nit): [nit] `tests/skills/wiki-cycle/check.py` (`_unfinished_ids`) — `earlier` is an unvalidated free string; any value other than `"open"` takes the comple… — addressed
- spec-11 (round 2, important): [important] `scripts/wiki-cycle-scope.py:577-580` and `skills/wiki-cycle/SKILL.md:63` — the printed close-out (and the resume line) omits `--topic`, s… — addressed
- spec-12 (round 2, suggestion): [suggestion] `scripts/wiki-cycle-scope.py:115` (print branch, `:577` in the file as numbered by the retry lens) — a scratchpad whose Status is `comple… — open
- spec-13 (round 2, suggestion): [suggestion] `tests/skills/wiki-cycle/check.py:2237` [eval-case-writer] — the "Step 0 told the user" check reads every assistant message (`reply = run… — addressed
- spec-14 (round 2, suggestion): [suggestion] `tests/skills/wiki-cycle/check.py:2283` [eval-case-writer] — `r"--resume\s+`?(?:" + re.escape(oid) + r"|<)"`: the `|<` alternative fails… — addressed
- spec-15 (round 2, nit): [nit] `scripts/wiki-cycle-scope.py:113` — the plan invariant "never deletes or edits an earlier run folder except through `--mark-interrupted`" is not… — open
- spec-16 (round 2, nit): [nit] `scripts/wiki-cycle-scope.py:555-556` — a scratchpad ending in `## Decisions log` with no trailing newline gets a second heading (`re.search(r"^… — addressed
- spec-17 (round 2, nit): [nit] `tests/skills/wiki-cycle/check.py:2263-2265` [eval-case-writer] — a quoted flag such as `'--mark-interrupted'` is stripped as text, so a real cl… — open
- spec-18 (round 3, important): [important] `scripts/wiki-cycle-scope.py:528-529` — a run folder filed under the wrong date is dropped without a line in the listing, the report or th… — addressed
- spec-19 (round 3, suggestion): [suggestion] `tests/skills/wiki-cycle/check.py:2239` and `:2286-2287` [eval-case-writer] — the Step 0 "tell the user" check tests only the final reply… — open
- spec-20 (round 3, suggestion): [suggestion] `CHANGELOG.md:16` — the corrected "What" entry still carries bare forms beside the fixed ones: `unfinished --run-folder <rf>`, "(`/wiki-c… — addressed
- spec-21 (round 3, nit): [nit] `scripts/wiki-cycle-scope.py:95` — the docstring prose "`--mark-interrupted <cycle_id> --reason \"<why>\"` closes one" has no `--topic`; it is n… — addressed
- spec-22 (round 5, suggestion): [suggestion] `tests/skills/wiki-cycle/check.py:2254` — a negated mention is counted as an offer, so a correct reply can fail the open case. Intent: re… — addressed
- spec-23 (round 5, nit): [nit] `scripts/wiki-cycle-scope.py:557` — the surviving mutant `count=0` is called equivalent, which holds only for template-shaped scratchpads. Inten… — addressed
- standards-1 (round 1, important): [important] `tests/skills/wiki-cycle/cases.json` (whole file) — R25 cleanup past the task: the file was re-serialised from one case per line to indent… — addressed
- standards-2 (round 1, important): [important] `scripts/wiki-cycle-scope.py` (`unfinished_runs`, `mark_interrupted`) — G26/G2 a run another session is still writing (scratchpad `in_prog… — addressed
- standards-3 (round 1, suggestion): [suggestion] `scripts/wiki-cycle-scope.py` (`unfinished_runs` / `mark_interrupted` / `cmd_unfinished`) — S2/S5/S7 the `_inbox/reports/<date>/<id>` pat… — addressed
- standards-4 (round 1, suggestion): [suggestion] `scripts/wiki-cycle-scope.py` (`mark_interrupted`) — G16/G19/S13 status rewrite, heading insertion and section append are interleaved in… — open
- standards-5 (round 1, suggestion): [suggestion] `scripts/wiki-cycle-scope.py` (`cmd_unfinished`) — S15 `out = write_scope(...)` is never read, while the sibling `promote` print ends `->… — addressed
- standards-6 (round 1, suggestion): [suggestion] `skills/wiki-cycle/SKILL.md` (Step 8) and `skills/wiki-report/SKILL.md` (Needs-you item) — S2 the "nothing about earlier runs when none"… — open
- standards-7 (round 1, suggestion): [suggestion] `tests/scripts/test_cycle_scope.py` (`unfinished_names_runs_without_report`) — R14 `ids == ["2026-09-10-01", "2026-09-24-01", "2026-10-01… — open
- standards-8 (round 1, suggestion): [suggestion] `scripts/wiki-cycle-scope.py` (`main`, `cmd_unfinished`) — T3 no test runs `unfinished` with neither flag, or with both `--run-folder` an… — addressed
- standards-9 (round 1, suggestion): [suggestion] `tests/skills/wiki-cycle/check.py` (`_check_unfinished`, the "does not name the {name} run" check) — PY9 `i not in utext` passes when no… — addressed
- standards-10 (round 1, suggestion): [suggestion] `tests/skills/wiki-cycle/check.py` (`_runs_mark_interrupted`) — G16 a 15-line command parser whose `\$\{?\w+\}?` alternative counts any s… — addressed
- standards-11 (round 1, nit): [nit] `scripts/wiki-cycle-scope.py` — R3 `RUN_ID` against `cycle_id` for the same concept. Fix: rename to `CYCLE_ID`. — addressed
- standards-12 (round 1, nit): [nit] `scripts/wiki-cycle-scope.py` (`cmd_unfinished`) — R3 `cid = args.mark_interrupted` is bound, then `args.mark_interrupted` is read again. Fix: u… — addressed
- standards-13 (round 1, nit): [nit] `scripts/wiki-cycle-scope.py` (`unfinished_runs`) — R24 `return sorted(out)` repeats the order of the `sorted(...glob("*/*"))`. Fix: drop one so… — addressed
- standards-14 (round 1, nit): [nit] `tests/skills/wiki-cycle/check.py` (`_unfinished_ids`) — R24 `from datetime import date, timedelta` inside a function with no reason. [eval-case… — open
- standards-15 (round 2, suggestion): [suggestion] `scripts/wiki-cycle-scope.py:524` — S2 sibling of round-1 standards-3, not converted to the helper: `for d in sorted((nb / "_inbox" / "re… — addressed
- standards-16 (round 2, suggestion): [suggestion] `tests/scripts/test_cycle_scope.py:486` (also `:495`, `:506`) — PY9 the error assertions pass on argparse's own usage text: `p.returncode… — addressed
- standards-17 (round 2, suggestion): [suggestion] `skills/wiki-cycle/SKILL.md:63` and `:175`, `skills/wiki-report/SKILL.md:276`, `skills/wiki-cycle/wiki-seed/wiki-cycle.md:43` — S2/S7 the… — open
- standards-18 (round 2, nit): [nit] `scripts/wiki-cycle-scope.py:708` — G2 `--reason` given with `--run-folder` passes every check and is ignored. Fix: also refuse `args.reason and… — open
- standards-19 (round 2, nit): [nit] `tests/skills/wiki-cycle/check.py:2253` [eval-case-writer] — G16/G17 `_runs_mark_interrupted` is a shell-text parser nested inside `_check_unfin… — open
- standards-20 (round 2, nit): [nit] `tests/skills/wiki-cycle/check.py:2168` [eval-case-writer] — R3 the `earlier` value `"open"` / `"complete-and-interrupted"` against the kind, sk… — open
- standards-21 (round 3, important): [important] `tests/skills/wiki-cycle/check.py:2292` [eval-case-writer] — R15 softened assertion: `not re.search(way_out("resume", oid), corpus),` repl… — addressed
- standards-22 (round 3, suggestion): [suggestion] `tests/skills/wiki-cycle/check.py:2309` [eval-case-writer] — S2 `not re.search(r"--(?:resume|mark-interrupted)[\s=]+[`\"']?" + re.escape(… — addressed
- standards-23 (round 3, suggestion): [suggestion] `tests/skills/wiki-cycle/check.py:2239` and `:2286` [eval-case-writer] — the check is stricter than the rule it tests: `oid in final` ("n… — open
- standards-24 (round 3, nit): [nit] `scripts/wiki-cycle-scope.py:558` and `:560` — S2 the literal `r"^## Decisions log$"` appears twice in `mark_interrupted`. Fix: one module const… — addressed
- standards-25 (round 3, nit): [nit] `scripts/wiki-cycle-scope.py:521-523` (and the module docstring at `:86`) — C2 the docstring says a run folder is `_inbox/reports/<date>/<YYYY-M… — addressed
- standards-26 (round 4, suggestion): [suggestion] `scripts/wiki-cycle-scope.py:555` and `:562` — G5/S2: the heading text `## Decisions log` is still written out in both write sites (the n… — addressed
- standards-27 (round 5, suggestion): [suggestion] S2 `tests/skills/wiki-cycle/check.py:2300-2302` vs `:2317-2318` — two detectors for one "way out" rule: the open branch uses `offers = re… — addressed
- standards-28 (round 5, suggestion): [suggestion] PY9 (reversed: fails a correct answer) `tests/skills/wiki-cycle/check.py:2254` — `found += [l.strip() for l in corpus.splitlines() if i i… — addressed
- standards-29 (round 5, suggestion): [suggestion] R14 `tests/skills/wiki-cycle/check.py:2408` with `baseline-opus.json:730` and `baseline-sonnet.json:723` — the check name embeds the run'… — open
- standards-30 (round 5, nit): [nit] S2 `tests/skills/wiki-cycle/check.py:2253-2254` — the two clauses of `resume_offers` overlap: every single-line match of `re.finditer(way_out("r… — addressed
- standards-31 (round 5, nit): [nit] C2 `tests/skills/wiki-cycle/check.py:2242-2246` — the `way_out` docstring says `--<option> <id>` (one option name), but `:2318` passes the alter… — addressed
- standards-32 (round 5, nit): [nit] S1/C3 `tests/scripts/test_cycle_scope.py:564` — the label `"unfinished_offers_resume_or_close_as_one_choice: the printed line is the resume or t… — addressed
- standards-33 (round 5, nit): [nit] T6 `tests/scripts/test_cycle_scope.py:564-567` — the exact-line check covers only the scratchpad branch; the no-scratchpad branch (`resume = ""`… — addressed
- standards-34 (round 5, nit): [nit] R14 `tests/scripts/test_cycle_scope.py:396-397` and `:407-408` — `p.stdout.strip() == "unfinished: none"` holds only because `unfinished_none_ca… — open
- standards-35 (round 5, nit): [nit] R24 `tests/skills/PENDING.md:28` — the Date cell of the Task #240 row says `2026-11-13`, but the Change cell now also carries the round-4 check… — open

## What was verified
tests: PASS — `uv run python tests/scripts/test_cycle_scope.py` ran fresh; the tool reported no non-zero exit (the plain script prints no exit line of its own, so exit 0 is read from the absence of an error status, and from its last line), last line `91/91 passed`, every line `PASS`, the new-code groups among them (`unfinished_names_runs_without_report`, `unfinished_none_case`, `unfinished_skips_a_folder_filed_under_another_date`, `unfinished_skips_a_file_named_like_a_run`, `unfinished_without_a_reports_folder`, the `mark_interrupted_*` and `unfinished_*` groups). Plan step 3's skill-suite criterion (red on the old copy, green on the new, Sonnet and Opus) is read from the saved reports, not re-run (each costs money; the requester named the run ids): run `20261114-131226-red-green-1d6b03c`, "Red then green" table: case `earlier-complete-and-interrupted-runs-not-named` "red then green: proves the change" on both models; case `earlier-run-without-report-or-scratchpad-gets-close-out-only` Sonnet "red then green: proves the change", Opus **"fails on the new copy"** (old copy failed on the real checks; the new copy failed one check only: "no permission denials (read-guard and the blocked Skill tool counted apart): other: ['Write']", a Write of `_scratch/.../report.py` refused). Run `20261114-132626` (Opus, case 1, new copy alone): "PASS · 23 turns · $1.34", "0 regressions, 0 newly passing". The Opus case-1 green therefore rests on a rerun of one session, not on the same run as its red: the report's own caveat reads "One session per case and model: a single pass or fail can be noise". The cause given in checkpoints.md (the global do-code-change edit gate refusing a sandbox helper .py) is the run's own account; the report shows only the refused Write. Both reports also list permission-denial entries under "Failed checks" for sessions that scored PASS (Sonnet in 131226, Opus in 132626); I did not open the run's per-session data to see which denial class they are.

diff-contains-fix: PASS — `git diff 08d9c6cb7db1df6d731976fc00fd326fde8e0b09 --stat -- . ':!.do-code-change'` lists every file the plan's steps name, each checked once: `scripts/wiki-cycle-scope.py | 101 +++++++++-` (step 1, 2), `tests/scripts/test_cycle_scope.py | 277 ++` (step 1, 2), `skills/wiki-cycle/SKILL.md | 5 +-` (step 3), `skills/wiki-report/SKILL.md | 3 +-` (step 3), `skills/wiki-cycle/wiki-seed/wiki-cycle.md | 3 +-` and `CHANGELOG.md | 6 +` (step 4), `tests/skills/wiki-cycle/{cases.json,check.py,baseline-opus.json,baseline-sonnet.json}` and `tests/skills/PENDING.md` (step 3), plus `skills/wiki-cycle/reference.md` and `skills/wiki-report/wiki-seed/wiki-report.md`; "13 files changed, 731 insertions(+), 6 deletions(-)". `git status --short` printed nothing: no named file is untracked or uncommitted. The step 3 text is in the diff: Step 0's `unfinished` command line in `skills/wiki-cycle/SKILL.md` and the wiki-report Needs-you line "Unfinished earlier runs (from `<run-folder>/unfinished-runs.txt`)".

findings-addressed: PASS — `review-ledger.py query --diff-base 08d9c6cb7db1df6d731976fc00fd326fde8e0b09 --cap 5 --ledger .do-code-change/240-unfinished-run-check/review-ledger.json`: "review-ledger: met - no open blocking item, every verdict current (7 closed, 51 non-blocking), 5 round(s)" / "review-ledger: exit 0 - met". The ledger is read with `--cap 5` on the requester's word (checkpoints.md, "Retry-ceiling exhaustion — 2026-11-14": past the default cap of 3 for round 4; the fix after round 4 and round 5 follow). The 7 blocking items are all `important` and all `addressed` in the ledger file (read with a script, no field showing a wontfix). The closing sequence matches checkpoints.md: standards-21, open after round 4, was fixed by the eval-case-writer replay on Mark's "yes please fix :D" (no longer a kept exception).

frozen tests: PASS — `check-freeze.py .do-code-change/240-unfinished-run-check/test-freeze.json --repo C:/github.com/llm-wiki-bootstrap` exit 0, "frozen-tests layer: PASS — 19 entries checked (+ 28 from earlier changes), all match or unfrozen with a reason (2 retired: deleted on purpose) (38 frozen green, each with its reason)", last line "check-freeze: exit 0 - PASS: every frozen test matches, or changed with a reason". Entries whose hash matches only through a recorded unfreeze (each with its reason on the record, listed by the script): [8] `mark_interrupted_closes_a_scratchpad_with_no_status_line` (1), [9] `unfinished_names_runs_without_report` (4), [10] `mark_interrupted_needs_a_reason` (1), [11] `unfinished_needs_a_flag` (1), [12] `mark_interrupted_refuses_a_run_folder_beside_it` (1), [19] `unfinished_offers_resume_or_close_as_one_choice` (1). Each unfreeze's own reason is in the script's output (spec-1 split, spec-11 `--topic`, standards-16 assertions on the script's own sentences, a comment-only edit, a reworded label); the one reading of intent I made: the standards-16 and standards-32 rewordings tightened an assertion (the script's own error sentence, the exact offered line) rather than loosening it. Green-frozen entries of this change (12 of the 19) carry their reasons in the script's list; the 2 retired entries are earlier changes' (`p3`, `p21`), not this one's.

coverage: PASS — every done criterion has an `existing` row, each confirmed by reading the test in the diff (not by the suite being green). Step 4 is `manual` in plan.md's Testing Decisions ("manual: step 4").

bar unmoved: PASS — `floor-guard.py --base 08d9c6cb7db1df6d731976fc00fd326fde8e0b09` exit 0, "floor-guard: clean (731 added, 6 removed lines checked)" / "floor-guard: exit 0 - clean: no move lowers the bar".

in scope: PASS — `scope-guard.py check --artifact-dir .do-code-change/240-unfinished-run-check` exit 0, "scope-guard: PASS - 13 touched file(s), all inside the declared scope (scripts/wiki-cycle-scope.py, tests/scripts/test_cycle_scope.py, skills/wiki-cycle/**, skills/wiki-report/**, tests/skills/wiki-cycle/**, tests/skills/PENDING.md, CHANGELOG.md)" / "scope-guard: exit 0 - PASS: every touched file is inside the declared scope". The scope was widened out loud twice (checkpoints.md: PENDING.md; `skills/wiki-report/**`), both recorded.

tests bite: FAIL — approved exception (named, approval beside it). `prove_tests_bite.py --check --base 08d9c6cb7db1df6d731976fc00fd326fde8e0b09` exit 2: "no mutation report: run the pass on the change (or record each trivial-stakes file with --exempt)" / "tests-bite layer: COULD-NOT-RUN against 08d9c6cb7db1df6d731976fc00fd326fde8e0b09 (0 changed source file(s)); report .artifacts/python-mutation.json" / "VERDICT: COULD-NOT-RUN". By the skill's rule exit 2 is `not checked`, and it counts as FAIL in the VERDICT line; the cause is the tool's reach, not this change: it mutates only `src/**/*.py` and this repo's code is in `scripts/` (checkpoints.md, "Fix after round 4"; skill suggestion filed to the tool's owner). Approval: Mark (Discord), recorded in checkpoints.md, "Tests-bite layer: approved exception — 2026-11-14": accepted this once as a named FAIL, evidence `hand-mutation-result.json` plus the four tests added from it. That evidence, read here (not re-run): `hand-mutation-result.json` holds 86 mutants on the added lines of `scripts/wiki-cycle-scope.py`, 81 killed, 5 survived (lines 530, 557, 577, 584, 714). Four survivors became tests, each frozen with a witness: 530 → `unfinished_skips_a_file_named_like_a_run`, 577 → `mark_interrupted_prints_what_it_closed`, 584 → `unfinished_offers_resume_or_close_as_one_choice`, 557 (`count=0`) → `mark_interrupted_rewrites_the_first_status_line_only` (round 5); line 714 (one word of argparse error text) is left, as checkpoints.md says, with its reason. The hand pass ran before the round-5 test changes and before the round-5 relabelling, and no mutation pass was re-run after them: the claim that the four new tests kill their mutants rests on the freeze entries' own `green_reason` text (e.g. "fails alone on the surviving mutant count=0 (90/91)"), which I read and did not reproduce. The gate stops for Mark on this layer; this report does not pass it.

VERDICT: FAIL — tests-bite (a named FAIL Mark approved; every other layer PASS)

## Working files
Unchanged copies in the notebook's raw folder; the same files are archived in the code repository at `.do-code-change/archive/2026-11-14-240-unfinished-run-check/`.

- [budget.json](../../../raw/code-changes/2026-11-14-240-unfinished-run-check/budget.json)
- [checkpoints.md](../../../raw/code-changes/2026-11-14-240-unfinished-run-check/checkpoints.md)
- [doubt-log.md](../../../raw/code-changes/2026-11-14-240-unfinished-run-check/doubt-log.md)
- [hand-mutation-result.json](../../../raw/code-changes/2026-11-14-240-unfinished-run-check/hand-mutation-result.json)
- [hand-mutation.py.txt](../../../raw/code-changes/2026-11-14-240-unfinished-run-check/hand-mutation.py.txt)
- [name-review.md](../../../raw/code-changes/2026-11-14-240-unfinished-run-check/name-review.md)
- [parked.md](../../../raw/code-changes/2026-11-14-240-unfinished-run-check/parked.md)
- [plan.md](../../../raw/code-changes/2026-11-14-240-unfinished-run-check/plan.md)
- [readonly-review.json](../../../raw/code-changes/2026-11-14-240-unfinished-run-check/readonly-review.json)
- [requirements.md](../../../raw/code-changes/2026-11-14-240-unfinished-run-check/requirements.md)
- [review-findings.md](../../../raw/code-changes/2026-11-14-240-unfinished-run-check/review-findings.md)
- [review-ledger.json](../../../raw/code-changes/2026-11-14-240-unfinished-run-check/review-ledger.json)
- [review-report-round-1.md](../../../raw/code-changes/2026-11-14-240-unfinished-run-check/review-report-round-1.md)
- [review-report-round-2.md](../../../raw/code-changes/2026-11-14-240-unfinished-run-check/review-report-round-2.md)
- [review-report-round-3.md](../../../raw/code-changes/2026-11-14-240-unfinished-run-check/review-report-round-3.md)
- [review-report-round-4.md](../../../raw/code-changes/2026-11-14-240-unfinished-run-check/review-report-round-4.md)
- [review-report-round-5.md](../../../raw/code-changes/2026-11-14-240-unfinished-run-check/review-report-round-5.md)
- [round2-changed.txt](../../../raw/code-changes/2026-11-14-240-unfinished-run-check/round2-changed.txt)
- [round3-changed.txt](../../../raw/code-changes/2026-11-14-240-unfinished-run-check/round3-changed.txt)
- [round4-changed.txt](../../../raw/code-changes/2026-11-14-240-unfinished-run-check/round4-changed.txt)
- [round5-changed.txt](../../../raw/code-changes/2026-11-14-240-unfinished-run-check/round5-changed.txt)
- [scope-baseline.json](../../../raw/code-changes/2026-11-14-240-unfinished-run-check/scope-baseline.json)
- [test-freeze.json](../../../raw/code-changes/2026-11-14-240-unfinished-run-check/test-freeze.json)
- [verification-result.md](../../../raw/code-changes/2026-11-14-240-unfinished-run-check/verification-result.md)

## Related
- [code-changes/ — the folder and its tags](README.md)
- Previous change: [2026-11-12 242-dcc-test-tidy](2026-11-12-242-dcc-test-tidy-the-git-hook-tests-share-one-harness-one-function-p.md) (not revised)
- Implements lesson #10 of [research cycle failures we hit, 2026-04 to 10](../troubleshooting/research-cycle-failures-we-hit-2026-04-to-10.md)
