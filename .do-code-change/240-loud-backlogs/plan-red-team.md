# Red-team: plan.md revision 6 (240-loud-backlogs, round 7, narrow verification)

The orchestrator wrote this from the red-team's report. A fresh architect ran strategy-red-team, scoped to three things: verifying the round-6 items, a consistency read of the plan end to end, and the new claims. It spawned no reviewer: by the brief's scope, it read the plan against the code itself. readonly-guard check: PASS (643 files, HEAD unchanged). Rounds 1-6 are in plan-red-team-round1..6.md.

## Round-6 items: resolved in the text?
- **KA1:** resolved. Silence is stated (plan:58, :237), the contradiction is gone, and Decision 10 adds the "superseded" form.
- **KA2:** resolved (plan:47, :79).
- **KA3:** resolved (plan:36, step 1 Failures).
- **KA4:** resolved in the text. Finding 2 below is a hole it leaves.
- **KA5:** resolved. `files_scanned` and `standalone` are real keys (wiki-lint-mechanical.py:1488, :1491).
- **Minor list and writer-brief note:** all present.
- **"3 such files in agentic-design":** correct (09-23, 10-12, 10-30).

## Kill-assumptions (ranked)

### 1. Step 4's Invariant cannot be met (plan error)
**Fails if:** step 4 asserts `Left undone: nothing`, but the interim line stays until step 6 (plan:21), and the lint and source lines don't exist until steps 5-6.

**Fix:** move the Invariant to step 6. At step 4, assert no Part 2 queue line and the interim line still present.

### 2. The reworded Needs-you line goes silent when left-undone.txt is missing (plan error)
**Fails if:** no left-undone.txt exists (a resume of a pre-install run, a skipped command, a report on an old run). The lint found findings, but there is no N to copy, so no line is written. Today it prints "lint fixes awaiting approval". This regresses against plan:31.

**Cheapest test:** a `--full` run with a 5-finding lint-semantic.json and no left-undone.txt must still print a Needs-you line.

**Fix:** with no file, keep today's generic `lint fixes awaiting approval — <path>`, with no count. Add it to the Invariant and step 5's Failures.

### 3. Decision 10's recommended "superseded; not read" form
- **(a) Silent hole (plan error).** The superseded lines are specified only for a run without its own lint (plan:58), so `--full` and `lint-only-semantic` runs skip them. **Fix:** every older completed lint is considered whenever any lint is newest, this run's own included.
- **(b) "not read" contradicts the cost (plan error).** The script does read each older file. **Fix:** say "not shown again".
- **(c) The collapsed line can be false (plan error).** It would count a 0-finding lint with no fixes note. **Fix:** collapse only lints whose findings list is non-empty.
- **(d) Minor (fix in implementation):** drop the parenthesis "(all made before the install)", and name the folder read (`_inbox/reports/*/*/`).

**The unknown-mode and mismatch queue line:** cannot print a false line. It is counted in N, so the header is never `nothing`.

## Minor, fix in implementation
- **plan:19:** say "presence and status".
- **plan:20:** the Part 2 list omits Decision 10's earlier-run lines.
- **`--report-only`:** say whether earlier-run lines are copied or counted fresh.
- **plan:57:** say whether a partial lint's N is the length or awaiting.
- **Wording table:** call it "the step-dependent rows".
- **Step 7, Part 1 alone:** case B reads the interim form there.

## What holds up
- The steps, the blocked-by lines and the Part lists are consistent.
- There are twelve Decisions, and each reference points at the right one.
- The header N rule, the report-only line, the `--brief` rule and case A's counts agree (2 awaiting = 5 - 3).
- plan:83 and :169 agree with each other.
- The wording table matches the counting rules.
- The cross-check is keyed on named files.
- The walkers exist (scope.py:202, :261).

## Could not assess
- B's real lint reaching completed with 0 counts (the unpaid test decides).
- The resume at Step 8 (the first paid session decides).
- How a model writes the `**Cycle**` line.
- The check.py line references, which were taken as settled by rounds 5-6.

## Complete enough to build?
Not as written. Findings 1 and 2 are one sentence each. Finding 3 (a)-(c) is one short revision to Decision 10's recommended form. Nothing needs a re-plan, and no further full round is needed. The only choice for Mark is Decision 10's form, which is already asked.

VERDICT: KILL-ASSUMPTIONS FOUND
