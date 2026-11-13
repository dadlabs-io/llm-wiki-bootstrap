# Plan — Step 0 names an earlier run that never finished (task #240, lesson #10)

Classification: vertical slice (one user-visible behaviour: a cycle tells the user about an earlier unfinished run).

## Problem Statement

A cycle that dies before its report leaves a run folder nobody looks at again (2026-07-17-01); nothing checks for one.

## Solution

A new `unfinished` subcommand in the cycle's step helper lists earlier run folders without their report (unless marked interrupted), writes them to the run folder, and can mark one interrupted. Step 0 runs it; the report's Needs you lists what it found.

## Implementation Decisions

- In the existing step helper (`wiki-cycle-scope.py`), beside `promote`; searched for an existing run-folder walker: `last_semantic` and `last_synthesis` glob `_inbox/reports/*/*/<file>`; the new function walks `_inbox/reports/*/*/` the same way. No shared helper is worth adding (each walk reads a different file).
- `unfinished --run-folder <rf>`: run folders are directories two levels under `_inbox/reports/` whose name matches `^\d{4}-\d{2}-\d{2}-\d{2}$`, the current one (`rf`) left out. Unfinished = no `<id>-run-cycle-report.md` in it and its `scratchpad.md` (if any) has no `**Status**: interrupted`. Output, sorted oldest first, one line each: `unfinished: <cycle_id> (<why>)` then its ways out: `resume: /wiki-cycle <notebook> --resume <cycle_id>` only when the folder has a scratchpad (Step 0 writes one first thing, so a folder without one has nothing to resume), and always `close it: wiki-cycle-scope.py --topic <notebook> unfinished --mark-interrupted <cycle_id> --reason "<why>"` (`<notebook>` the one the listing ran on, so a pasted line acts on the right notebook); none → `unfinished: none`. Always writes `<rf>/unfinished-runs.txt` by `write_scope` (header line, one `<cycle_id>\t<why>` per folder). Exit 0 either way (a finding, not a failure).
- `unfinished --mark-interrupted <cycle_id> --reason "<text>"` (no `--run-folder` needed): finds the folder under `_inbox/reports/<date>/<cycle_id>/`; sets the scratchpad's `**Status**:` line to `interrupted` and appends `- <now_stamp()> — marked interrupted: <reason>` under `## Decisions log` (adding the heading if missing); with no scratchpad, writes one: `# Cycle Run — <date>`, `**Status**: interrupted`, the Decisions log line. Prints what it did.
- Skill text: Step 0 runs `unfinished` after `promote` and, when it names any, tells the user and puts the lines in the scratchpad; Step 8's Needs-you list and `/wiki-report`'s Needs-you template gain "Unfinished earlier runs — each with resume / mark-interrupted".

## Testing Decisions

- Seam: the script through its command line on a throwaway notebook, in `tests/scripts/test_cycle_scope.py` (the file's existing pattern).
- Seam: the wiki-cycle skill suite (`tests/skills/run_skill_test.py wiki-cycle`), two new cases (the second the negative one, finished and interrupted runs not named): a fixture notebook with an earlier run folder lacking its report; Step 0 must name it. Red on the installed skill, green after.
- manual: step 4 — usage page and CHANGELOG read against steps 1-3 (the install itself is the finish's, output in checkpoints.md).

## Out of Scope

- Lessons #11, #12, #9; resuming or deleting anything automatically.

## Scope

- scripts/wiki-cycle-scope.py
- tests/scripts/test_cycle_scope.py
- skills/wiki-cycle/**
- skills/wiki-report/**
- tests/skills/wiki-cycle/**
- tests/skills/PENDING.md
- CHANGELOG.md

## Invariants

- Every existing check in `test_cycle_scope.py` stays green (the existing subcommands unchanged).
- The check never deletes or edits an earlier run folder except through `--mark-interrupted` on the one named — the listing's no-edit pinned by the suite's folder-untouched check; `--mark-interrupted`'s refusals by step 2's Failures bullet.

## Decisions needed

none beyond requirements Decisions 1-3

## Steps

1. A cycle's Step 0 helper names earlier unfinished runs — done when the `unfinished` checks in `test_cycle_scope.py` pass:
   - Expected: a run folder with no report and no scratchpad is printed with its why and the close-out only; one whose scratchpad says `in_progress` with its why, resume and the close-out; and listed in `<rf>/unfinished-runs.txt`; a folder with its report, one whose scratchpad says `interrupted`, the current run folder and a non-run folder (`checker/`) are not.
   - Expected: with none unfinished, `unfinished: none` and the file holds only its header line (not zero bytes).
   - Failures: `_inbox/reports/` missing → `unfinished: none`, exit 0, nothing created outside `rf`.
   Trivial stakes: no
2. A flagged run can be closed — done when the `--mark-interrupted` checks pass:
   - Expected: on a folder with a scratchpad, its Status line becomes `interrupted`, the reason is appended under `## Decisions log`, and the next `unfinished` run leaves it out; on a folder with no scratchpad, one is written with that status and reason.
   - Failures: an unknown `<cycle_id>` (or a name not matching `<YYYY-MM-DD>-<NN>`) → exit 2, error names it, nothing written; `--reason` missing → exit 2 (argparse), nothing written.
   Trivial stakes: no
3. The skill runs it and the report shows it — done when the new wiki-cycle suite case is red on the installed skill and green on the changed one (Sonnet and Opus baselines), and the wiki-report Needs-you template names the line. Trivial stakes: no
4. Docs — the wiki-cycle usage page and CHANGELOG say what changed (manual: step 4). The refresh and `--mode status` run at the finish, after verify, so nothing unreviewed is installed. Trivial stakes: yes — docs only
