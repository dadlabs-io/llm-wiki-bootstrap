# Name review — 241-pre-commit-dcc-check

## Step 2 — 2026-11-12 (one doubt-reviewer, briefed with `check-freeze.py names` output only; steps 2 and 3 in one spawn)

- `test_absent_pack_commits_with_a_not_checked_line` — PASS. Reviewer's open points, settled from the file: `Machine` writes no fake check unless `fake_dcc` is called, and `repo()` makes no commit (`git init` and config only), so `head(r)` is real evidence of the commit.

## Step 3 — 2026-11-12 (same spawn)

- `test_blocked_commit_says_no_verify_needs_mark` — PASS. Reviewer's caveat (not a name word): the test does not assert the fake's refusal text, so it does not itself prove the dcc path caused the block; that is step 1's `test_dcc_refusal_blocks_the_commit`, which asserts the fake's message. Left as is.

## Step 1

Pending: `test_dcc_pass_lets_the_commit_through` is not green (its fake prints on a pass); waiting on Mark's OK to change that test's one line.
