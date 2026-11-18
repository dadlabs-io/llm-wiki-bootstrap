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

## Paid red-green run — 2026-11-17
Unpaid fixture test green (24 s) after the writer's three builder fixes. Asked: go for the red-green run of cases A and B, both models, --red-green b7401bb (8 sessions, ~$10-15).

Mark (terminal): "go"

## Paid re-run of case A — 2026-11-17

Asked: "go for the test A re-run (about $3.60)?" (case full-run-resumed-at-report-names-every-planted-backlog-in-left-undone, red-green against b7401bb, both models, after the writer's Numbers-row check fix 8b9cd93).
Mark: "yes"
Result: red then green on both models ($3.31; report tests/skills/.results/wiki-cycle/20261117-222534-red-green-b7401bb/report.md). Old copy failed for the right reason (no Left undone section); new copy passed. The report lists a permission denial per model (a `cd …; ls` Bash on sonnet, a Read of the run scratchpad on opus) under failed checks; the case still passed.

## Live read-only run — 2026-11-17

`wiki-cycle-scope.py left-undone` (repo copy, not yet installed) on agentic-design and llm-wiki-bootstrap, each into a scratch run folder in the session scratchpad holding only a `quick` scratchpad.md, so nothing was written into either notebook (`git status` of each notebook folder the same before and after). Run from llm-wiki-bootstrap for both: no project folder's `.claude/wiki-config.json` names agentic-design, and this session (bot llm-wiki) is the reader of its `llm-wiki` bucket, so `me()` labels the right bucket.
- Wall time: agentic-design 2.4 s (1,713 entries), llm-wiki-bootstrap 0.4 s.
- Past review_after: agentic-design 615 today; 605 with `--today 2026-11-16` against requirements' 607: the 2 are folder READMEs (`research/interesting-docs/README.md`, `research/skills/README.md`, review_after 2026-11-04) that the entries rule leaves out (tasks/ holds no review_after, so it is not the difference the plan guessed); the 10 between 605 and 615 are entries whose review_after is 2026-11-16. llm-wiki-bootstrap 6 on both days, equal to requirements' 6.
- agentic-design, 12 queues: also not semantically linted 116, no claims 163, synthesis 7 not checked, semantic findings from 2026-10-30-01 193 with no fixes record, two older lints without a usable findings list, 2 pending tickets, other readers' buckets agent-builder 50 and ai-money 15. llm-wiki-bootstrap, 7 queues: no review_after 1, not semantically linted 281, no claims 281. The lint and sources lines read not checked because the scratch folder holds no step files, as a quick run with none would.

## Mutation pass — 2026-11-17

`prove_tests_bite.py --base 6f23c8c --files scripts/wiki-cycle-scope.py scripts/wiki-triage.py` → "note: ignoring paths outside src/**/*.py … FAIL no changed source file under src/ to mutate (exit 2) VERDICT: COULD-NOT-RUN" (developer hand-back; suite on clean code ~134 s, all seven files green). Skill suggestion written: `_inbox/skill-suggestions/proving-python-tests-bite--prove-tests-bite-py-mutates-only.md`.
Asked (one question): hand pass of ~100 bugs on the new left-undone and lint-fixes code like lesson #11, skip, or mutation on-demand for the repo.
Mark: "Hand pass, ~100 bugs (Recommended)". tests-bite is recorded as a named exception with the hand pass as evidence.
Hand pass result (developer, harness `hand-mutation-lu.py.txt`, results `hand-mutation-lu-result.json`): 119 mutants (M000 a canary), 111 killed, 6 real survivors each killed by a new test in `test_cycle_scope.py` (red against its mutant on a scratch copy, frozen at step `mutation-1`: M018, M034, M059, M063, M078, M103), 2 equivalent (M042 a 24 h boundary to the microsecond, M046 unreachable for a report-only folder), 0 timeouts; no implementation bug found, no implementation code changed. Checked by the orchestrator: `test_cycle_scope.py` 310/310, check-freeze PASS, `git diff -- scripts/` empty.
Next (morning session): code review (code-reviewer, cap 3), verify (architect; tests-bite a named exception with this pass as evidence), the finishing decision, finish, the install SOP, card 240 step 4.

## Review round 1 — 2026-11-18
Verdict: not yet met, 10 open blocking items (review-findings.md, ledger round 1). Back to implement: fix round 1, the first of the 3 retries; the next review is round 2.

## Module question — 2026-11-18
Asked: move the counter out of wiki-cycle-scope.py into its own module, or keep it and move only the file-shape docstring out.
Mark (terminal): "ok sounds good, lets do that" — read as: finish this change first with the docstring move and the fixes, keep the counter in place; the split is a separate later run (its own clarify, baseline-move-compare testing; it would take `left-undone` and `unfinished` together, the run-state reporting block).

## Module question, corrected — 2026-11-18
The orchestrator misread Mark's question ("we want to test this as is and then do the change after? that seems excessive? doesnt it make more sense to do it right from the start?"): he meant doing the split inside this change rather than testing and installing lesson #9 and then reopening the code. The docstring-only move was also wrong on its own terms: the script's docstring is the one source of the rules (CHANGELOG), so moving the file-shape part out would split the spec. The developer was told to skip the docstring move (item 1).
Asked: put the split (left-undone, lint-fixes and unfinished into their own module) into this change before verify, or keep it a separate run after install.
Mark (terminal): "yes please" — the split goes into this change, as the fix for standards-1, tested by baseline-move-compare (unpaid script suite before and after, byte-compare of left-undone output on both notebooks); the docstring moves with its code.

## Step 8 hand-back readings — 2026-11-18 (orchestrator, no question asked)
- Split done by developer: `_cycle_common.py` 14 names (the shared helpers, plus the three scope functions and their four helpers, which the moved code also calls), `_run_state.py` 52 names, `wiki-cycle-scope.py` 31. Saved outputs byte-identical (left-undone and unfinished on both notebooks, lint-fixes --show), suites equal before and after (test_cycle_scope 316 → 317, the one new check the drift test's tightening).
- After the move the prescan named two dates in moved docstrings (`write_scope`, `_front`); the orchestrator removed them, so `split-ast-check.py.txt` reports 95 names identical and those 2 different, docstring text only. Re-checked by the orchestrator: test_cycle_scope 317/317, fixture test every check passed, prescan clean.
- Frozen tests changed, awaiting Mark's yes to re-freeze: 6 from fix round 1 (header counts pinned) and 3 from step 8 (the mode-table drift test tightened and pointed at `_run_state.py`; the newest_step test pointed at `_cycle_common.py`; the docstring test pointed at `_run_state.py`).

## Review round 2 — 2026-11-18
Verdict: 25 findings, 5 blocking (standards-40, -41, -42, -43, spec-19), all in tests and the PENDING log; the pure move found clean on both axes. standards-40 was caused by the orchestrator's fix-round-1 brief, which had the developer write two case-A checks into check.py by hand (README: the editing session never writes the cases that grade its change). Back to implement: fix round 2, the second of 3 retries.

## Budget — 2026-11-18
Asked: raise the run's cost cap from $120 to $150 ($98.29 used; fix round 2, the case-writer, review round 3 and verify estimated at $25-30).
Mark (terminal): "yes please contninue" — read as yes to the raise only; the re-freeze question stays open and is asked again before verify.

## The strict section check (standards-40) — 2026-11-18
The case writer stopped (no mode named), and its rules showed the first plan was wrong too: an existing kind's check is never changed, so it could not rewrite the hand-written checks inside `left-undone-planted`. Asked: A, remove the hand-written checks and have eval-case-writer (mode `fresh`) write new cases for the strict check, then a small paid red-then-green; or B, remove them and record that no paid case compares the section to the file.
Mark (terminal): "A sounds better I think eh" — A. check.py restored to 1913d55 (the version both paid runs used); the writer's answer is saved unchanged; the fixture's tamper lookups and COMPOSED names follow its new names; the paid run waits for Mark's go.

## The no-file case — 2026-11-18
The writer's first answer saved only in part: case 1 (`left-undone-verbatim`) saved unchanged; case 2 (`left-undone-resumed`) held, because a resumed run reaches cycle Step 8 and writes the file, so its no-file branch would likely never run (the writer's own question 1). Asked: A, re-brief case 2 as `/wiki-report` on an old run folder with no `left-undone.txt`; B, keep it as written; C, drop it.
Mark (terminal): "A". Mode `fresh` returns two cases, so the brief pairs it with the third state (a standalone report, no run folder); Mark can drop that one at the paid-run go.
Writer's answer: one case, `left-undone-old-run` (`/wiki-report` on a finished run folder with no left-undone.txt), saved unchanged. The standalone state was not written: every case's common checks need a run folder and a commit, and an existing check may not change, so it has no paid case (writer's question 1, carried to the finish as a gap). Unpaid smoke (scratchpad `smoke_old_run.py`, built with the suite's own setup and prompt): the correct no-file report passes; "nothing", computed queue lines and a missing section each fail.

## Ruling: an undecodable intake README — 2026-11-18 (orchestrator, made in fix round 2; Mark told, did not object)
A README that is not valid UTF-8 is a read error, not a parse error: `session_buckets` re-raises it, so `left-undone` exits non-zero and writes no file, and the report reads the no-file state, rather than silently counting the default `main` bucket. A README whose frontmatter does not parse still falls to the default. Plan step 3's Failures bullet amended in place (review round 3, spec-28).

## Review round 3 and fix round 3 — 2026-11-18
Round 3: 20 findings, 3 blocking (standards-50, standards-51: the fixture's composed labels and comment; spec-28: plan step 3 silent on the UTF-8 ruling), plus 5 round-1 verdicts STALE (their files changed again). Fix round 3 (the third and last retry), inline: COMPOSED gains the shape-only checks, the fixture's comment and docstring say which checks are composed, the 'Nothing.' check renamed into the composed prefix, plan step 3 amended, the ruling recorded above, PENDING's missing "and". Fixture test: every check passed. Five writer's-text findings (write detector routes, unused ctx, duplicated regex, stale `left-undone-resumed` header, report fallback) and the dash mapping left open: a fix to them goes back to eval-case-writer.
`review-ledger.py fixed` exit 1 on 5 items, none an unfixed defect: spec-3, standards-14, standards-15 (stale verdicts re-verified and re-set; their fixes landed in earlier rounds, so their files did not move since round 3), spec-28 (fixed in plan.md, which the ledger's diffs leave out: the same gap as the waiting suggestion `do-code-change--review-ledger-py-fixed-refused-spec.md`), spec-31 (finding cites check.py, the fix is in the fixture). Skill suggestion written: `do-code-change--review-ledger-py-fixed-refuses-a.md`. The gate fails closed, so the run stops for Mark.
Asked: A, override the gate and dispatch review round 4 with the five items named for the reviewer to confirm; or B, stop and continue manually.
Mark (terminal): "A" — the `fixed` gate overridden for these five items only; review round 4 is the last within the cap.

## Mark's standing word — 2026-11-18
Mark (terminal): "dont worry about retry cap etc for now. Just get 'er done". Read as: finish the run without stopping on the retry cap or similar process gates, the calls stated and recorded here; it covers re-freezing the tightened tests (stricter, not looser) and the install at the finish; it does not cover a paid run or a push.

## Review round 4 and fix round 4 — 2026-11-18
Round 4: 6 findings, 3 blocking, all the fixture's composed labelling (standards-63, spec-35, spec-36); the five overridden items confirmed (spec-3, standards-14, spec-28, spec-31 confirmed; standards-15 confirmed in part, its residue being the same labelling). Fix round 4, inline: one rule, "PASS (composed)" only for a check that cannot fail in grade() whatever the script writes; the 'Left undone: nothing' checks, the Numbers row and the Needs-you line leave COMPOSED (they read the script's wording), "the cycle report's last section is Needs you" joins it; main() fails a COMPOSED prefix that names no emitted check (standards-64); plan step 3 names `session_buckets` (spec-37). Fixture test: every check passed. Seven earlier verdicts went stale on the fixture and PENDING edits and were re-verified against the fixture's output. Ledger: met (21 closed, 81 non-blocking open, 4 rounds). No review round 5, on Mark's standing word.

## Verify, first pass — 2026-11-18
architect (verifying-before-done): FAIL on bar-unmoved and coverage; tests-bite the named exception (Mark, "Mutation pass"). Tests, diff, findings, frozen and scope PASS. Routed back to implement and plan (orchestrator, inline, on Mark's standing word):
- bar unmoved: floor-guard flagged 11 `# noqa` markers (8 the old file's E402 pattern moved or re-split by step 8; a new E731 lambda; two BLE001 in test files). The guard has no approval path for `silenced-checker`, and the repo runs no linter, so the markers suppressed nothing: removed (the unchanged E402 marker in the same import block too, for one style), the lambda made a local `def`, the two broad excepts' reasons kept as plain comments. floor-guard: clean.
- coverage 3d: new test `left_undone_refuses_an_undecodable_intake_readme` (the command exits non-zero and writes no file). 8d: new test `scope_script_runs_from_the_installed_file_set` (the script runs from a folder holding exactly the install manifests' files). Both shown to bite on a scratch copy of scripts/ (no re-raise; `_run_state.py` dropped from the manifests): 317/322, each new check failing for its own reason; frozen green with that evidence. 8b: plan Testing Decisions gains `manual: step 8`.
- `test_wiki_triage.py`'s frozen intake test re-frozen (its comment changed, no assertion).
- Fresh: test_cycle_scope 322/322, triage 67/67, synthesis 9/9, checker-hold 12/12, promote 14/14, dequeue 10/10, fixture every check passed; check-freeze PASS; scope-guard PASS (18 files); ledger met after 11 stale verdicts re-verified against those runs.

## Verify, second pass — 2026-11-18
architect: tests, diff, findings, frozen, coverage, bar, scope all PASS; tests-bite FAIL as the named exception Mark approved (checkpoints.md "Mutation pass"). verification-result.md "Second pass".

## Finishing decision — 2026-11-18
keep — verify VERDICT: FAIL on tests-bite only, the named exception Mark approved 2026-11-17 ("Hand pass, ~100 bugs (Recommended)"), every other layer PASS (verification-result.md, second pass); on the branch the run started on (main). No push (asked for by name, separately).
Record tags (on Mark's standing word, reused from the code-changes README table): `code-change`, group `skills`, `wiki-cycle`, `wiki-report`. Revises no earlier record; it moves lesson #10's `unfinished` code (record 2026-11-14 240-unfinished-run-check) into `_run_state.py`, linked from the summary.

## Paid red-green run of the two new cases — 2026-11-18
Asked: go for `run_skill_test.py wiki-cycle --cases <verbatim>,<old-run> --red-green b7401bb` (8 sessions, about $7-8).
Mark (terminal): "proceed"
