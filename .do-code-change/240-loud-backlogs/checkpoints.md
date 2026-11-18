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

## Plan confirmation — 2026-11-17
Plan revision 7; red-team round 8: VERDICT NONE FOUND (375bcf7). The twelve Decisions needed, asked one at a time.

### Decision 1 (lint findings fixed at cycle Step 5)
Asked: A, re-run the mechanical lint once after Step 5 (show, apply, record with lint-fixes, re-run), with the staleness guard; or B, no re-run, lines worded "found before the fix step; approved fixes are not subtracted".

Mark (terminal): "A"

### Decision 2 (tier-4 deferrals in an unattended run)
Asked: A, the checklist's tier field, only for a run whose folder holds discover.json and whose scratchpad lists --no-confirm-discovery (silent miss accepted and stated); or B, no flag gate (any run that ran discovery names its unticked tier-4 candidates). Other options (label, new text file, contract edit) named, not recommended.

Mark (terminal): "A"

### Decision 3 (how far the paid test reaches)
Asked: A, case A a seeded resume at cycle Step 8 plus case B a clean --lint-only (8 sessions, unpaid fixture test first); or B, case A as a plain --lint-only, the event lines proved by script tests only.

Mark (terminal): "A -- but shouldnt we run the linter first? wont it show some standard issues we can fix and thats mechanical and doesnt require tokens?"

Answered: yes, already in the plan. test_left_undone_fixture.py (unpaid, no model tokens) runs the real mechanical lint on case B's built notebook before any paid session; the builder repairs the seed's known issues (6 orphans, 1 entry missing frontmatter/tier/confidence, past review_after dates) in code, and the backlink blocks are rebuilt by the integration scripts; no paid session runs until that lint reads completed with zero findings.

### Decision 4 (the "script many skills call" trigger)
Asked: A, the trigger does not fire (targeted cases + the six script tests, logged in PENDING.md, no full suite); or B, a full suite once after the targeted cases on Mark's yes. Third option (no extraction) named, not recommended.

Mark (terminal): "A"

### Decision 5 (discovery's own drops)
Asked: A, name each discovery drop with its reason except "already covered"; or B, one line with a count and a pointer to discover.md.

Mark (terminal): "A" (also: "we can just chat here... Im back for some time." — questions move to the terminal)

### Decision 6 (tickets already in Needs you, in the sources list)
Asked: A, leave out any source whose ticket carries retry: or save_as_pdf: (each item in one place); or B, list everything, repeats included.

Mark (terminal): "shouldnt I know about them if they need me? I need notification as part of the run."
Answered: under both answers they are in the run's report; Needs you (the report's last section) names every retry and Save-as-PDF ticket; A names each once there, B also in Left undone; no ping either way (settled earlier).

Mark (terminal): "A"

### Decision 7 (bucket tickets)
Asked: A, count only bucket files with a source: line; or B, every .md except README, triage-log.md and _-prefixed files.

Mark (terminal): "A"

### Decision 8 (same-day under-count)
Asked: A, accept the under-count and label it in the line; or B, compare by time with one git log call.

Mark (terminal): "A"

### Decision 9 (concept gaps)
Asked: A, leave them out (Pending-work row already carries count and action); or B, add a Concept gaps line to Left undone.

Mark (terminal): "A"

### Decision 10 (earlier-run semantic findings)
Asked: A, the newest lint's unresolved findings plus a "superseded by a newer lint; no longer shown in full" line per older lint with unresolved findings, in every run; B, newest only (older ones silenced); C, every lint back to the last answered one, summed.

Mark (terminal): "A"

### Decision 11 (the Numbers row's Stale count)
Asked: A, the Numbers row takes the Left undone past count (0 with no past line, not checked with no file); or B, leave it (two numbers).

Mark (terminal): "A"

### Decision 12 (a paid case for --brief)
Asked: A, no third case (case A grades Needs you and the Numbers row; the --brief string read by hand once); or B, a third paid case for --brief.

Mark (terminal): "A"

All twelve answered with the recommended form.

### Build in one go or two parts
Asked: A, one go (all seven steps, one paid red-green run of 8 sessions, one install); or B, two parts (Part 1 installed first; 16 sessions, two installs, an interim "Not counted yet" line).

Mark (terminal): "A"

Build: one go.

## Frozen step-1 tests and step 4 — 2026-11-17
Step 4 adds the Not semantically linted and No claims lines to a never-linted notebook (the plan's rule), so 6 checks in two frozen step-1 tests (left_undone_counts_review_dates, left_undone_names_what_it_cannot_check) expect 3 lines and now see 5. Asked: update the two tests (3 → 5, the new lines named), re-freeze each with the reason recorded, and the same for any later frozen test of this run that changes only because a later step adds lines as planned (step 6 removing the interim line).

Mark (terminal): "yes updated tests"

## Step 6 hand-back readings — 2026-11-17 (orchestrator, no question asked)
- Re-freezing tests whose "only left-undone.txt is new" assertion now allows left-undone-events.txt: covered by Mark's approval above (plan Invariant: a non-report-only Part 2 run writes left-undone-events.txt as planned).
- `Past review_after: 0, not checked (refresh left no refresh.json)` in a mode that runs refresh: follows the plan (third state: "the count is still printed in the line, before not checked"; Testing Decisions: the fixture with refresh.json removed "must give the third state on the past-due line, and not nothing"). Accepted as the plan's rule; the reviewer may weigh it.
- Gaps named by the developer for review: discover.json deferred/errors not read; update.json/discover.json status not read (a partial step with no items prints nothing).
