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
