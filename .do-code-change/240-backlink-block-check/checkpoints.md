# Checkpoints — 240-backlink-block-check

## Size proposed — 2026-11-14

Size: full — a caller outside the change: `wiki-promote.py` runs `wiki-reciprocate-backlinks.py` after every promotion, and Decision 3 changes which links that script reads. Other criteria: no open design decision once Decisions 1-4 were answered; no schema; no live data written by the tests; no HIGH file; no existing refusal changed. Production files: 2 scripts (lint, backlink rebuild), 2 skill texts (wiki-cycle, wiki-report).

## Requirements confirmation — 2026-11-14

Mark (Discord), each Decision answered in turn: (a) the lint check, not a self-check in the script ("Regular lint that runs at the 2nd of each cycle? That makes sense"); one lint run, the order swapped ("I think it only needs to run once didn't it? What will it catch between the 2 runs", then "Excellent"); the script reads section links and bracketed link text, the red-then-green run and install, tests-bite accepted once more ("Agreed with all. Ignore the limit. Please continue"). Before leaving he asked that every blocker be cleared ("I'll be away for sometime so want to make sure all blockers clear").
Size: full (above; decided by the run under the workflow's criteria, put to Mark with the plan below).
Branch: stays on main — decided by the run under Mark's "Please continue" with him away (asking would block the run; the previous changes on card #240 stayed on main).
