# Name review — 241-pre-commit-dcc-check

## Step 2 — 2026-11-12 (one doubt-reviewer, briefed with `check-freeze.py names` output only; steps 2 and 3 in one spawn)

- `test_absent_pack_commits_with_a_not_checked_line` — PASS. Reviewer's open points, settled from the file: `Machine` writes no fake check unless `fake_dcc` is called, and `repo()` makes no commit (`git init` and config only), so `head(r)` is real evidence of the commit.

## Step 3 — 2026-11-12 (same spawn)

- `test_blocked_commit_says_no_verify_needs_mark` — PASS. Reviewer's caveat (not a name word): the test does not assert the fake's refusal text, so it does not itself prove the dcc path caused the block; that is step 1's `test_dcc_refusal_blocks_the_commit`, which asserts the fake's message. Left as is.

## Step 1 — 2026-11-12 (one doubt-reviewer, `check-freeze.py names` output only)

- `test_dcc_refusal_blocks_the_commit` — PASS.
- `test_dcc_pass_lets_the_commit_through` — OVER-CLAIMS, round 1: "dcc pass" was unchecked, since nothing showed the check ran. Fixed: the fake writes a marker file and the test asserts it exists (assertions only added); re-frozen with `--unfrozen-reason "name review round 1: ..."`. Bite shown by hand: with the hook restored to the fixed point the test fails ("the dcc check did not run").
