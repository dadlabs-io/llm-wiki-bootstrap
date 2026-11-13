# Requirements — tidy test_git_hooks_dcc.py (task #242)

## Facts

- earlier change 241-pre-commit-dcc-check: its review left 12 non-blocking findings open on `tests/scripts/test_git_hooks_dcc.py` and the hook (standards-2 to -13; ledger in `.do-code-change/archive/2026-11-12-241-pre-commit-dcc-check/review-ledger.json`).
- user confirmed (Mark, Discord 2026-11-12 23:21): "Please do ... five" (the 12 small review nits).
- earlier change 241, Decision 2 (Mark): the change request's hook line is used as given; a missing python fails loud with no special handling.
- found in `tests/scripts/test_git_hooks.py`: the sibling test runs its checks at import, so it cannot be imported as a helper; it names its helper `repo()` too.
- the test file is a test only: nothing ships it, nothing imports it.

## Exclusions

- No change to `tools/git-hooks/pre-commit`: standards-11 (the "NOT CHECKED -" wording) and standards-12 (the one-line conditional) are agent-builder's lines as given; dropped as not worth fixing (Mark, 2026-11-13: "If they're not worth fixing then we can put them off").
- No python-absent test (standards-5's second half): Mark ruled no special handling.

## Decisions

1. **Which findings to fix** — decided by Mark (Discord, 2026-11-13 00:52): "If the work's fixing, let's fix them now." Fix standards-3, -4, -5 (first half), -6, -8, -9, -10, -13 and also -2 and -7: `tests/scripts/test_git_hooks.py` is converted to one function per check, both test files share one harness module, and `repo()` becomes `new_repo()` in both. Drop -11 and -12 (Exclusions).
