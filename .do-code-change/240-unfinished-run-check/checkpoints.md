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
