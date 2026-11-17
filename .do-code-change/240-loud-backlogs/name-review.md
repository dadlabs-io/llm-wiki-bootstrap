# Name review

## Step 1 (one doubt-reviewer, haiku, foreground; briefed with the `check-freeze.py names` output, with two long tests summarised in prose rather than pasted, which left that reviewer unable to see their source)

Contract: each test's name claims nothing its assertions do not check.

- left_undone_counts_review_dates: does not over-claim.
- left_undone_reads_the_mode: does not over-claim.
- left_undone_names_what_it_cannot_check: over-claims (the name implies every uncheckable case is named; the assertions cover the enumerated cases: missing and partial refresh.json, mismatch, unreadable mode, the nine step-file contradictions, the report-only line).
- left_undone_refuses_bad_input: over-claims, mild (three --today values, a missing run folder, a notebook with no wiki/).
- left_undone_mode_table_matches_skill: over-claims (agreement is asserted for the skill's five modes only, which is what the plan says the drift test covers).

Reconciliation: the names are the developer's own, not fixed by the plan. Renaming a frozen test needs a retire and a new freeze, which the step's test-run budget did not allow after the final run. Left as named; the five-mode limit and the enumerated cases are stated in the test source and in the script docstring. Named in the hand-back for the code-reviewer.

## Step 3 (one doubt-reviewer, haiku, foreground; briefed with the `check-freeze.py names` output file, contract: each test's name claims nothing its assertions do not check)

- intake_tickets_lists_source_carrying_tickets_once: does not over-claim.
- left_undone_counts_bucket_tickets: does not over-claim.
- left_undone_counts_pending_tickets: does not over-claim.
- left_undone_counts_staged_entries: does not over-claim (a check label says "Needs you has them", which only the absence of a line pins).
- left_undone_counts_discovery_checklists: does not over-claim (its label names which files are excluded; the count of 1 does not show which was counted).
- left_undone_falls_back_to_one_bucket_on_an_unparseable_intake_readme: over-claims (the fixture holds only main/, so "one bucket" as a rule is not told apart from other fallbacks).
- left_undone_docstring_names_the_unsupported_working_folder: over-claims (two substring checks on the docstring, not behaviour).

Reconciliation: the names are the developer's own; renaming a frozen test needs a retire and a re-freeze and the step's test-run budget is spent. Left as named, for the code-reviewer. The weak check labels are named, not changed.

## Step 4 (one doubt-reviewer, haiku, foreground; briefed with the `check-freeze.py names` output file, contract: each test's name claims nothing its assertions do not check)

- newest_step_returns_the_newest_matching_result: does not over-claim.
- left_undone_counts_entries_not_linted: over-claims in two check labels (the "no line" label says the scope lists "both" while the call passes both plus new-d; the same-day check asserts only the count 1, which an inverted date rule could also give).
- left_undone_counts_entries_without_claims: over-claims in one check (the index check asserts the count 3 only, so which three are not shown).
- left_undone_counts_entries_not_synthesised: over-claims in one label (the "Needs you has it" parenthesis is not asserted).
- The reviewer also noted the `names` output lists only `check` and `results` as module-level names for tests 2-4 (the helpers sit in the enclosing `with` block), so it judged from source alone.

Reconciliation: names are the developer's own; the over-claims are check labels and count-only assertions, not the names. Left as is; the test-run budget is spent; named for the code-reviewer.
