# Checkpoints — 240-loud-backlogs

## Requirements confirmation — 2026-11-16

### Decision 1 (scope)
Asked: A (overdue entries + entries with no review date) or B (a general rule naming anything waiting more than one cycle, in every queue).

Mark (terminal): "Is this about a louder notification?" Answered: no ping; one line in the cycle report's Needs you, every cycle.

Mark (terminal): "this is after we run, after we run everything should be comnpleted no? otherwise we should know about it and why?"

Read as a new option C: at the end of every cycle run, anything the cycle leaves undone (any queue it owns that is not empty) is named in the report, with the count and the reason it was left. No age rule. Overdue entries are one case. Next: list the queues the cycle owns and whether each is already reported when left non-empty.

Inventory done (product-manager, requirements.md rewritten; 8 gaps sent to Mark on Discord).

### Decision 2 (where the lines go)
Asked: A, a new "Left undone" section just above Needs you ("Left undone: nothing" when empty), or B, lines inside Needs you.

Mark (Discord): "A"

### Decision 3 (backlogs a mode skips on purpose)
Asked: A, each of the five (overdue, no review date, not semantically linted, no claims, not synthesised) gets a count and reason, counted fresh without running the step; or B, counts for the two review-date lines only.

Mark (Discord): "A"

### Decision 4 (sources dropped, failed or deferred, tier-4 deferrals included)
Asked: A, each named in Left undone with its reason; or B, counts only with a pointer to the run's notes.

Mark (terminal): "A"

### Decision 5 (lint findings left unfixed)
Asked: A, every kind above 0 with a reason, plus a count on the fixes-awaiting line; or B, keep the 5 shown kinds and add a reason.

Mark (terminal): "A"

### Decision 6 (other readers' and `mark` buckets)
Asked: A, each named in Left undone with count and owner; or B, left in the Pending-work table as today.

Mark (terminal): "If its not your bucket you dont really care. Naming them once with the left to be processed is fine"

Read as: one line in Left undone naming the other buckets once, each with its count left to be processed; no owner or reason detail, and no per-item listing.

requirements.md updated with D2-D6 (product-manager). Follows-from Facts shown to Mark on Discord.

### Size
Proposed full. Criteria: (1) no open design decision fails, because two are open: step-summary counter vs the step-return contract, and whether failed tickets stay in their bucket. (2) No outside users fails: the lint summary JSON and the report template are read by other steps. (3)-(6) hold.

Mark (terminal): "A"

Size: full

### Branch
Asked: A, stay on main (as lessons #10-#12 did); or B, features/240-loud-backlogs.

Mark (terminal): "A"

Branch: main

## Scope question after red-team round 2 — 2026-11-16
Asked: A, build half 1 (disk-state counts) now and half 2 (what a step that ran left behind) as its own change; or B, keep everything and work through the ~10 decisions.

Mark (terminal): "No lets fix the plan solidly first, we can still decide to do it in 2 parts, but lets make sure the plan is complete before we start"

Read as: revise the whole plan (both halves) until it holds; the split stays open and is decided once the plan is complete.
