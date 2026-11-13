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
