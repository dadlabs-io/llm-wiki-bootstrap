# Name review (one doubt-reviewer per step, fed `check-freeze.py names` output only)

## Step 1
- `wiki_cycle_skill_says_to_leave_out_a_flag_with_no_ids`: does not over-claim. Notes (not name issues): substring match, so polarity is not checked; "Step 5" in the detail text is not asserted.

## Step 2
- `left_undone_claims_count_with_no_index_uses_the_claims_run_as_cutoff`: OVER-CLAIMED (round 1): no entry was re-reviewed between the commit day and the claims run's day, so a commit-day cut-off passed. Name fixed by the plan, so the assertions were strengthened: `old-b` re-reviewed on the claims run's own day (D1) must not be counted, which a D0 cut-off would count. Re-frozen with `--unfrozen-reason "name review round 1"`. Not re-reviewed (one round).

## Step 3
- `left_undone_claims_count_with_an_index_but_no_claims_json_is_the_unindexed_plus_revised`: OVER-CLAIMED (round 1): "plus revised" was not exercised. Added a second notebook (`s3a2`) with an indexed entry re-reviewed after the index: count 2. Re-frozen with a reason.
- `left_undone_claims_cutoff_is_the_index_time_whatever_claims_json_says`: OVER-CLAIMED (round 1): "whatever" varied one stamp only; and the count line does not name which entry is counted. Added a run with a `claims.json` stamped before the index (D0). The which-entry gap is left: the scope file lists `old-a` and `old-c`, and no output line names an entry, so the count of 1 is the only observable (named in the hand-back).

## Step 5
- `session_write_plants` is a helper in a plain script, not a test function the freeze can locate (its red command's output never names it); no names output, `NOT CHECKED`. Its checks print their own names (`a check fails a session that wrote left-undone.txt by cp`, ...).
