# Name review

## Step 1 (one doubt-reviewer, haiku, foreground; briefed with the `check-freeze.py names` output, with two long tests summarised in prose rather than pasted, which left that reviewer unable to see their source)

Contract: each test's name claims nothing its assertions do not check.

- left_undone_counts_review_dates: does not over-claim.
- left_undone_reads_the_mode: does not over-claim.
- left_undone_names_what_it_cannot_check: over-claims (the name implies every uncheckable case is named; the assertions cover the enumerated cases: missing and partial refresh.json, mismatch, unreadable mode, the nine step-file contradictions, the report-only line).
- left_undone_refuses_bad_input: over-claims, mild (three --today values, a missing run folder, a notebook with no wiki/).
- left_undone_mode_table_matches_skill: over-claims (agreement is asserted for the skill's five modes only, which is what the plan says the drift test covers).

Reconciliation: the names are the developer's own, not fixed by the plan. Renaming a frozen test needs a retire and a new freeze, which the step's test-run budget did not allow after the final run. Left as named; the five-mode limit and the enumerated cases are stated in the test source and in the script docstring. Named in the hand-back for the code-reviewer.
