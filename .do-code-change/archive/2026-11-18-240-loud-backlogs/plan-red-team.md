# Red-team: plan.md revision 7 (240-loud-backlogs, round 8, narrow verification)

The orchestrator wrote this from the red-team's report. A fresh architect ran strategy-red-team, limited to three things:
- verifying the round-7 items;
- reading the whole plan for consistency;
- attacking the text that revision 7 changed.

No reviewer was spawned, which is within that scope. The readonly-guard check passed (644 files, HEAD unchanged). Rounds 1-7 are in plan-red-team-round1..7.md.

## Round-7 items: resolved in the text?
- **KA1, step 4's Invariant:** resolved. It now asserts no Part 2 line and that the interim line is still present (plan:275). The `nothing` assertion moved to step 6 (:102, :287).
- **KA2, Needs you with no left-undone.txt:** resolved. The generic count-less line is kept (:83), and it appears in the Invariants (:169) and in step 5's Failures (:280).
- **KA3, Decision 10:** resolved.
  - (a) The rule now covers every run, and step 5 tests `--full` and lint-only-semantic.
  - (b) The wording now says "not shown again".
  - (c) Only lints with a non-empty list count.
  - (d) The parenthesis is dropped, and the folder is named.
- **The six minor items:** all present (:19, :20, :62, :57, :64, :291).

## Consistency read (whole plan)
The plan is consistent:
- the steps and their blocked-by lines;
- the Part lists against the Part text;
- the twelve Decisions and the references to them;
- the Needs-you text (:83), the Invariant (:169) and step 5;
- the header N rule against step 1's example;
- the wording table against the counting rules.

## Attack on the text revision 7 changed
**Kill-assumptions:** none. Nothing found prints a false line or goes silent in a way the plan doesn't already state.

**Minor, fix in implementation:**
1. **Interim line and N:** the interim `Not counted yet:` line is not a queue line and doesn't count toward N. Say so in one sentence.
2. **Older partial lints:** an older `partial` lint with unresolved findings is ignored. Say so in Decision 10, or extend the rule to `not checked`.
3. **Superseded-line wording:** "not shown again" can read as false, since the superseded line repeats every run. "no longer shown in full" is safer.
4. **lint-only-semantic in Needs you:** "applied or declined not recorded" is odd in that mode. Add "(no fix step in this mode)".

## What holds up
- The mode design, the third state, the cross-check on named step files, and the handling from the Part 1 interim to Part 2.
- The Needs-you rewording has no silent path:
  - the file's N is printed when there is one;
  - the generic line is printed when there is no file;
  - nothing is printed only for 0 findings, a fully answered record, no semantic lint, or an unusable list, which Left undone carries.
- The report-only rules (disk state counted fresh, events copied, earlier-run lines counted fresh, no nesting).

## Could not assess
- **Resume at Step 8:** whether a model resumes at Step 8 and copies the section. The first paid session will show it.
- **Case B lint:** whether B's real lint reaches `completed`. The unpaid fixture test will show it.

## Complete enough to build
Yes. There are no plan errors and no choices beyond the twelve Decisions. The four minor items are settled in implementation.

VERDICT: NONE FOUND
