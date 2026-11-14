# Checkpoints — 240-unfinished-run-check

## Size proposed — 2026-11-13

Size: small (proposed). Decisions needed in plan.md: none (the choices are requirements Decisions 1-3); the new subcommand has no callers outside the change; no schema, no live data written (the tests use a throwaway notebook); no HIGH file; no existing refusal changed. Production files: 1 script, 2 skill texts.

## Change confirmation — 2026-11-13

Size: small. Mark (terminal), after the plain restatement (name every run folder without its report unless marked interrupted; a command marks one interrupted with a reason, or --resume finishes it; shown at Step 0 and in the report's Needs you): "yes that sounds right - we should probably do that BEFORE we strart anything cortrect?" -> Decisions 1-3 as recommended. Read as: the check runs at Step 0, before any other step of the cycle (as planned). After install, the 3 hand-run agentic-design folders are marked interrupted by the session (Mark agreed); the other two are put to him by the first cycle's Step 0.

## Plan amended — 2026-11-13

Step 4 no longer installs: the refresh and --mode status move to the finish, after verify (nothing unreviewed installed). Rewritten in place.

## Implement: suite red then green, round 1 — 2026-11-13

Run 20261113-144230-red-green-1d6b03c ($7.63, 8 sessions). Old copy: case 1 red on both models (no unfinished-runs.txt, no ways out); case 2 red on Sonnet, passed on Opus. New copy: case 1 failed only "no command closes an earlier run", a false alarm (the flagged commands wrote the scratchpad and the report JSON quoting the way out; folder-untouched passed) -> eval-case-writer replay narrowed that check (saved unchanged; replayed offline on both runs' events: nothing flagged; a real close-out command flagged). Case 2 failed on both models: Needs you mentioned the interrupted run / "no unfinished earlier runs" -> skill text now says nothing about earlier runs when the file names none. The writer's question (is an already-interrupted run silent?) is settled by Mark's yes on 2026-11-13: once marked, never named again; case 2 kept whole.

## Implement: suite red then green, round 2 — 2026-11-13

Run 20261113-145815-red-green-1d6b03c (~$7.6): new copy 4/4 PASS. Case 1 red then green on Sonnet and Opus; case 2 red then green on Sonnet, passes on the old copy on Opus (kept as a guard, not counted as proof). Scope widened out loud: tests/skills/PENDING.md (the suite README says a skill change is logged there); row added.

## Review round 1: design questions — 2026-11-13

Mark (terminal), on spec-1 (resume offered for a folder with no scratchpad) and standards-2 (a live run listed, and --mark-interrupted could rewrite it): "should we jave a process start a notes file first thing? there really shouldnt be 2 runs running at the same time."
- spec-1: Step 0 already writes the scratchpad first thing (status in_progress), so a run folder with no scratchpad is a hand-run step folder or one older than that rule; nothing in it can be resumed. Ruling: such a folder gets only the close-out way; resume is offered only when a scratchpad exists. Requirements Decision 2 and plan step 1 rewritten in place.
- standards-2: one cycle per notebook at a time (Mark). Addressed by stating that rule in the skill's Don't list and the script's docstring, which the listing relies on; no lock or age refusal (no new code).
Fix round 1 (the small path's one round): spec-1, standards-2 as above; cheap suggestions and nits taken where they touch the same lines (standards-5, -8, -11, -12, -13; spec-5 usage page, scope widened to skills/wiki-report/**; spec-4, -7, -8, -9 in the artifacts). check.py/cases items (standards-9, -10, -14; spec-3, -10; and case 1's resume check under the new ruling) go back to eval-case-writer (replay). standards-1 and spec-2 fixed by the orchestrator (3325ec7). standards-3, -4 (refactors), -6 (one-source rule for Step 8 vs wiki-report), -7 (test order) considered in the round.

## Fix round 1 — 2026-11-13

Developer: spec-1 (resume only with a scratchpad; frozen test split and re-frozen with the ruling as reason), standards-2 (Don't line + docstring + usage page), standards-3 (`run_folder_of` helper: a small design addition, three sites), -5 (dropped the unused assignment instead of printing; the frozen none-case pins stdout), -8 (exactly one of --run-folder / --mark-interrupted, two new tests; the neither case's bite shown by a mutant in a scratch copy, 83/84), -11, -12, -13; spec-5, spec-8. Not done with reasons: standards-4 (refactor with no failing test), -6 (both skill rules covered by suite cases), -7 (the file's one-notebook pattern). Red 81/84, green 84/84; check-freeze PASS. Case writer (replay): case renamed `earlier-run-without-report-or-scratchpad-gets-close-out-only`, checks: no resume for the no-scratchpad folder, close-out offered, the reply names the id, Step 0 ran (own scratchpad; header-only file in the none case), `earlier` validated, the shell-variable alternative dropped; saved unchanged; old baseline entry for the renamed id removed. Small path: this was its one fix round; a second moves the run to full.

## Suite red then green, round 3 — 2026-11-13

Run 20261113-161525-red-green-1d6b03c (~$7.4): RED THEN GREEN on all four (both cases, both models). Baselines merged per case from it; PENDING row rewritten in place.

## Review round 2 — 2026-11-13

Focused round: 13 findings, 1 blocking (spec-11: the printed close-out and resume lines omit `--topic`, so for a cycle on another notebook, e.g. agentic-design run from this project, a pasted close-out falls back to the project's notebook). Round-1 rulings confirmed applied; round-1 addressed items confirmed except standards-3's one sibling (standards-15).
Size: full — second fix round. The rounds already spent count toward the full ceiling of 3.
Fix round 2 takes: spec-11 (blocking), standards-15 (listing skips a folder not under its own date folder, one definition of a run folder), standards-16 (assert the script's own error sentences), spec-16 (no-newline heading). To the case writer: spec-14 (the `|<` alternative fails on generic text) and spec-13. Left open, non-blocking: standards-17 (one-source wording across four prose places: suite-covered text), -18, -19, -20; spec-12 (a `completed` scratchpad with no report keeps resume: the ruling covers only the no-scratchpad case; resume can still write its report), spec-15, spec-17.

## Fix round 2 — 2026-11-13

Developer: spec-11 (both printed ways out carry the notebook: `wiki-cycle-scope.py --topic <nb> unfinished --mark-interrupted ...`, `/wiki-cycle <nb> --resume <id>`; script, docstring, SKILL.md Step 0, wiki-report, usage page, CHANGELOG, plan sample; requirements Decision 2's forms by the orchestrator), standards-15 (listing skips a folder filed under another date), standards-16 (refusals assert the script's own sentences; bite by a scratch mutant, 83/86), spec-16 (no second heading). Red 82/86, green 86/86; check-freeze PASS. Case writer (replay): spec-14 (only this run's id matches a way out; generic text never fails), spec-13 (the final reply must name the id), new forms matched; saved unchanged.

## Suite red then green, round 4 — 2026-11-13

Run 20261113-164536-red-green-1d6b03c (~$6.9): RED THEN GREEN on all four. Baselines re-merged per case; PENDING row updated in place.

## Review round 3 (the cap) — 2026-11-13

9 findings, 2 blocking, each reversing an earlier round's own ask: spec-18 (a folder filed under another date is now skipped: round 2's standards-15 asked for that skip) and standards-21 (the no-resume check no longer fails on generic `--resume <cycle_id>` text: round 2's spec-14 asked for that). Ledger query: not yet met, 2 open. Round 3 is the retry ceiling: Retry-ceiling exhaustion, to Mark.

## Retry-ceiling exhaustion — 2026-11-14

Put to Mark: the two blocking findings each reverse an earlier round's ask; recommended continue manually, keep both behaviours, fix the CHANGELOG and docstring wording by hand. Mark (terminal): "oplease proceed and fix and do anotyher round" -> continue manually, plus one more review round (round 4, past the ceiling, on his word).
Rulings (one each, for two lenses' opposite asks):
- spec-18 (misfiled folder skipped): kept. A run folder is one under its own id's date (every cycle files it there); written into requirements Decision 1 and the script's docstrings (module and `unfinished_runs`).
- standards-21 (generic `--resume <cycle_id>` text not failed): kept, as round 2's spec-14 asked; the check still fails a resume offered for the run's own id. `way_out`'s docstring already states it. check.py unchanged.
- standards-23 / spec-19 (final reply vs any reply for "told the user"): kept on the final reply (spec-13's ask); the timing of "now" is untested, as spec-19 notes.
- standards-22 (way_out re-spelled in the negative case): left open, a suggestion in eval-case-writer's file; no suite rerun for it.
Hand fixes (orchestrator): spec-20 CHANGELOG forms carry the notebook; spec-21 docstring `--topic <notebook> unfinished --mark-interrupted`; standards-24 one `DECISIONS_LOG` constant; standards-25 docstrings name the own-date rule. test_cycle_scope.py 86/86; check-freeze PASS.

## Review round 4 (past the ceiling, on Mark's word) — 2026-11-14

Spec CLEAR; Standards 1 suggestion (standards-26: the heading text still written out twice beside the new pattern), none blocking. Fixed by hand: one `DECISIONS_HEADING`, the pattern built from it; test_cycle_scope.py 86/86, check-freeze PASS. The Spec lens's unverified point (are real run folders filed under their own date?) settled by a walk of every notebook's `_inbox/reports/*/*`: none filed under another date.
Stale verdicts re-verified against round 4's report (the script moved under them): spec-1 (resume only with a scratchpad, `:583-584`), spec-11 (notebook in every printed form), spec-18 (own-date rule, Decision 1), standards-2 (one-cycle rule at SKILL.md and the docstring), spec-2 (both baselines carry both new cases). Ledger: not yet met, 1 open: standards-21, kept by Mark's ruling; it goes to verify as a named FAIL for his approval, beside the mutation-tool gap.

## Fix after round 4: the two known failures — 2026-11-14

Mark (terminal), on going to verify with standards-21 and the mutation-tool gap as approved FAILs: "please contoinue debugging", then "yes please fix :D" -> fix both rather than accept them.
- standards-21 (and standards-22): eval-case-writer replay, saved unchanged: the no-resume check counts `--resume <id>` or any `--resume` on a line naming the earlier run's id (the generic offer the reviewer named), and a `--resume` on a line without the id stays clear (round 2's false alarm); the negative case builds its pattern from `way_out`. The writer's two notes: a negated mention on the id's line ("no --resume for <id>") would count, and a wrap across lines is not caught. Saved replies regraded offline: the new-copy replies of runs 161525 and 164536 clean on both models. Case 1 ran red then green on both models in run 20261114-122942-red-green-1d6b03c ($3.53); baselines merged for that case only (check renamed, date line moved); PENDING row updated in place.
- Mutation gap: root cause, prove_tests_bite.py mutates only `src/**/*.py` (`SRC_RE`) and ignores `--files` outside it; this repo's code is in `scripts/` and its tests run as plain scripts, so it is COULD-NOT-RUN on every change here. The tool is agent-builder's: skill suggestion filed (proving-python-tests-bite). Stand-in: a hand-written pass that plants one bug at a time in the change's added code lines of scripts/wiki-cycle-scope.py and runs tests/scripts/test_cycle_scope.py against the copy (WIKI_SCOPE_SCRIPT); result below once it ends.
Hand mutation pass (`hand-mutation.py.txt`, kept as text, result `hand-mutation-result.json`): 86 mutants on the added code lines of scripts/wiki-cycle-scope.py (docstrings left out), each run against tests/scripts/test_cycle_scope.py: 81 killed, 5 survived. Three were real gaps, now tests, each shown to fail alone on its mutant (88/89) and frozen at step `mutation`: `unfinished_skips_a_file_named_like_a_run` (`and` for `or` in the folder filter), `mark_interrupted_prints_what_it_closed` (the close-out's print dropped), `unfinished_offers_resume_or_close_as_one_choice` ("; and close it" for "; or close it"). Two left, with reasons: `count=0` in the Status substitution (a scratchpad has one Status line: equivalent), and one word of the argparse error text (wording; the asserted part is unchanged). test_cycle_scope.py 89/89; check-freeze PASS. prove_tests_bite.py itself still reports COULD-NOT-RUN here (src/ only): the verify layer stays a named FAIL with this pass as its evidence until agent-builder's tool takes scripts/.

## Fix after round 5 — 2026-11-14

Round 5: 0 blocking; 11 suggestions and nits. Taken:
- standards-28 / spec-22 (a negated `--resume` mention on the id's line counted as an offer, e.g. "You didn't pass `--resume`, so I left it"), standards-27 (one detector for both cases), standards-30 (dedupe), standards-31 (way_out docstring): eval-case-writer replay, saved unchanged: on the id's line `--resume` counts only when directly followed by the id or a `<...>` placeholder; the negative case uses the same `resume_offers`. No check name changed. Regrade of 28 saved sessions (reply text): every new-copy reply clean in both cases; the old false alarm gone; one old-copy reply caught offering `--resume <interrupted id>` (a real offer).
- standards-32 (label), standards-33 (exact printed line for a no-scratchpad run: `unfinished_offers_only_the_close_out_without_a_scratchpad`), spec-23 (first Status line only: `mark_interrupted_rewrites_the_first_status_line_only`, kills the count=0 survivor): each new test fails on its mutant (89/91, 90/91); frozen; the relabelled test re-frozen with its reason. test_cycle_scope.py 91/91; check-freeze PASS.
Left, with reasons: standards-29 (the shared check name "one run folder, <id>" carries the date, so a baseline comparison on another day skips it: pre-existing in every wiki-cycle case, not this change's; parked), standards-34 (order-dependent `unfinished: none`: the file is one sequential notebook by design), standards-35 (PENDING row date: the row is updated in place, as the suite's README asks).
Suite after the round-5 fix: run 20261114-131226-red-green-1d6b03c (~$8.3): both cases red on the old copy on both models; green on the new copy except Opus case 1, which failed only "no permission denials" (a Write of a helper `_scratch/.../report.py` in the sandbox refused by the global do-code-change edit gate, because this repo has an open run whose Scope does not list that path; every check of this change passed; skill suggestion filed for do-code-change). Opus case 1 rerun on the new copy alone: PASS, run 20261114-132626 ($1.34). Baselines merged per case from those two runs; the Opus case 2 entry again carries "run: read reference.md before writing the scratchpad" (round 3's unverified point: the trajectory check fires only when the session Writes the scratchpad). PENDING row updated in place.
