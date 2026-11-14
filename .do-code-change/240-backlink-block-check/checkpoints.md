# Checkpoints — 240-backlink-block-check

## Size proposed — 2026-11-14

Size: full — a caller outside the change: `wiki-promote.py` runs `wiki-reciprocate-backlinks.py` after every promotion, and Decision 3 changes which links that script reads. Other criteria: no open design decision once Decisions 1-4 were answered; no schema; no live data written by the tests; no HIGH file; no existing refusal changed. Production files: 2 scripts (lint, backlink rebuild), 2 skill texts (wiki-cycle, wiki-report).

## Requirements confirmation — 2026-11-14

Mark (Discord), each Decision answered in turn: (a) the lint check, not a self-check in the script ("Regular lint that runs at the 2nd of each cycle? That makes sense"); one lint run, the order swapped ("I think it only needs to run once didn't it? What will it catch between the 2 runs", then "Excellent"); the script reads section links and bracketed link text, the red-then-green run and install, tests-bite accepted once more ("Agreed with all. Ignore the limit. Please continue"). Before leaving he asked that every blocker be cleared ("I'll be away for sometime so want to make sure all blockers clear").
Size: full (above; decided by the run under the workflow's criteria, put to Mark with the plan below).
Branch: stays on main — decided by the run under Mark's "Please continue" with him away (asking would block the run; the previous changes on card #240 stayed on main).

## Red-team — 2026-11-14

`plan-red-team.md`: VERDICT KILL-ASSUMPTIONS FOUND (8). Plan errors applied in place by the planner (the orchestrator): 1 Step 5.6 rebuilds before its re-lint; 2 `--direct`'s fix-links stays first; 4 one entry set and one text/fence rule for both, real-notebook agreement at verify; 6 `fake_qmd_env` in the lint test; 7 a planted fixture and the hub case's final lint for the suite cases; 8 `framework-docs/cycle-step-return-format.md` and `scripts/wiki-promote.py` (comment) in Scope, fixtures and the resume rule. Contract gaps applied: `--lint-only` now rebuilds too (stated); Step 5.5's lint gets `--cycle-id`; requirements Fact 15 corrected (the order can move counts either way).

## Plan confirmation — 2026-11-14

Mark is away; before leaving he answered every Decision ("Agreed with all. Ignore the limit. Please continue") and asked that all blockers be cleared. The two red-team choices are decided by the run under his rulings, to be shown to him at the finish:
- Choice 3 (code stripping removes a backticked link from blocks): strip, under Decision 3 ("the script reads links the way the check does"; the check's rule is the lint's, which strips code). Kill criterion kept: verify reports how many block lines a real notebook loses; if any, they are named to Mark before install.
- Choice 5 (a START with no END): the lint lists it as "block not closed"; the rebuild is not changed (the Exclusions: no change to how blocks are placed). A named trade-off.

## Implement steps 1-2 (developer) and step 3 text (orchestrator) — 2026-11-14

Developer: lint section + `backlink_blocks_out_of_step` / `backlink_blocks` (`unclosed` rows), its own link functions; backlink script reads section links, bracketed and empty text, strips code, drops anything after an unclosed START, excludes `_inbox/`; block format unchanged. `tests/scripts/test_backlink_blocks.py` 41/41 (40 functions, each red first, frozen; Invariant 2's golden test green on arrival, bite shown by a heading mutant). Invariants: test_promote_backlinks 14/14, test_cycle_script_fixes 44/44, test_lint_spec_values 11/11, test_hub_tag 12/12 (rerun by the orchestrator: same). One doubt cycle: a marker quoted in code made a page look unclosed -> code is stripped before blocks are found (both scripts; the plan said block first: same result except that case). Six "does not count" tests check absence from the report, which also holds when the target is not an entry: kept, the plan's wording covers both readings.
Orchestrator: SKILL.md Step 3 (fix-links, rebuild/index/map, lint once), Steps 5.5 and 5.6 rebuild before re-linting, `--lint-only` note, Needs-you line; reference.md one Phase 3; wiki-report Needs-you line and lint row. eval-case-writer (fresh + replay), saved unchanged: two `backlinks` cases (dirty, clean), `_check_backlink_lint_zero` called in the hub branch, four fixture scratchpads with one Phase 3. Its open note: the automatic-promotion case could also assert the final lint reads 0 (an existing kind's branch): left, named as not covered.

## Red-team choice 3 kill criterion — 2026-11-14

Dry run of the changed backlink script on the four notebooks (read-only): llm-wiki-bootstrap +10 -0, agentic-design +20 -0, investment-agent +187 -0, agent-builder-bootstrap +3 -3. The three removals are all from one linker, agent-builder's `project/decisions/intake-build-candidates-seven-skills-built-derive-tests-folded-into-verify-2026-09-08.md`: its line 99 starts `  ```flow block is in the file ...`, which markdown reads as an unclosed fence, so everything after it (the page's Related links included) renders as code; the new rule reads it as markdown does. Not code stripping of an inline span. To be named to Mark before install, as recorded; the page's fix is agent-builder's (close or reword the fence).

## Step 4 docs — 2026-11-14

Usage pages (wiki-cycle: mode table and `--lint-only` line; wiki-lint: the new section; wiki-report: the Needs-you line), CHANGELOG 2026-11-14 entry, INSTALL-INVENTORY rows for both scripts, `framework-docs/cycle-step-return-format.md` (framework-version 8 -> 9: Step 3 order, the lint's new summary key and array, Step 5.5's re-run), `scripts/wiki-promote.py` comment (Step 3.5 -> Step 3). `grep -rn "Step 3\.5\|Phase 3\.5"` over skills/wiki-cycle, skills/wiki-report, framework-docs, scripts, the suite: only the two intended history mentions (reference.md history line, SKILL.md resume rule) and wrap-up's own Step 3.5 in the authoring doc.

## Suite red then green — 2026-11-14

Run 20261114-162044-red-green-84cdf16_6 (~$15.70; old copy f9b3aa2, before the run): RED THEN GREEN on all three cases, both models: the two `backlinks` cases and `hub-misses-one-tagged-entry-gets-one-line-others-untouched`. Each old-copy session failed only "the final lint reads backlink_blocks_out_of_step 0" (the old lint has no key / ran before the rebuild). Baselines merged per case; PENDING row added. Regression run (Sonnet) of `resume` and `confirm-false-ingest-only-resume-promotes-at-end` started.
