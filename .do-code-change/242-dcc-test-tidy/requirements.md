# Requirements — tidy test_git_hooks_dcc.py (task #242)

## Facts

- earlier change 241-pre-commit-dcc-check: its review left 12 non-blocking findings open on `tests/scripts/test_git_hooks_dcc.py` and the hook (standards-2 to -13; ledger in `.do-code-change/archive/2026-11-12-241-pre-commit-dcc-check/review-ledger.json`).
- user confirmed (Mark, Discord 2026-11-12 23:21): "Please do ... five" (the 12 small review nits).
- earlier change 241, Decision 2 (Mark): the change request's hook line is used as given; a missing python fails loud with no special handling.
- found in `tests/scripts/test_git_hooks.py`: the sibling test runs its checks at import, so it cannot be imported as a helper; it names its helper `repo()` too.
- the test file is a test only: nothing ships it, nothing imports it.

## Exclusions

- No change to `tools/git-hooks/pre-commit` (standards-11, the "NOT CHECKED -" wording, and standards-12, the one-line conditional, are the change request's text as given; changing them diverges from agent-builder's tested lines).
- No change to `tests/scripts/test_git_hooks.py` (standards-2's shared helper would mean rewriting the sibling's import-time layout; standards-7's rename would have to touch both).
- No python-absent test (standards-5's second half): Mark ruled no special handling.

## Decisions

1. **Which findings to fix.** Recommendation: fix standards-3 (the pass test uses `fake_dcc` with a body), -4 (one constant for the refusal message), -5 first half (the closing line also asserted on a gitleaks block), -6 (docstring says why a per-test HOME class), -8 (temp dir cleaned when the install fails), -9 (git setup return codes checked), -10 (`main` reports any exception per test and refuses an unknown name), -13 (`head()` returns `None` with no HEAD). Decline -2, -7, -11, -12 and -5's second half for the reasons under Exclusions. Alternative: fix all twelve, including the hook's given text and the sibling test.
