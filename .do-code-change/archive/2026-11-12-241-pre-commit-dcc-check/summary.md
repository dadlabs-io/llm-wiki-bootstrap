# 2026-11-12 241-pre-commit-dcc-check — the machine pre-commit runs do-code-change's commit check

## TL;DR
`tools/git-hooks/pre-commit` now runs agent-builder's `dcc-commit-check.py` after the private-words check when the do-code-change pack is installed, so a commit that stages a script no open run covers is blocked; without the pack it prints NOT CHECKED and the commit goes on. The closing line after any block became "fix the lines above. --no-verify only when the machine's owner has said so." It was agent-builder's change request (its task 260), which Mark accepted on 2026-11-12, and it was the first change in this repo made through do-code-change (small path: one fix round, two review rounds). Kept on main.

## What changed
- 1. A commit whose dcc check refuses is blocked
- 2. With the pack absent, the commit goes on and says NOT CHECKED
- 3. The closing hint and the docs say what the hook now does

New tags: `git-hooks` (tooling), `do-code-change` (tooling).

## Why: decisions and exclusions
Decisions:

1. **The closing hint after a block** — decided by Mark (2026-11-12): every block is fixed; `--no-verify` only when the machine's owner (Mark, here) has said so. The line becomes "pre-commit: fix the lines above. --no-verify only when the machine's owner has said so." (wording ruled at fix round 1: the bypass rule names no person; the hook's header and README still name Mark elsewhere, outside this ruling)
2. **`python` cannot run** — decided by Mark (2026-11-12): fail loud, no special handling. The change request's line is used as given: a missing python makes the shell print its own error and sets status=1, so the commit is blocked. Alternative was a guard with its own BLOCKED line (dropped as unneeded).

Exclusions:

- No change to `dcc-commit-check.py` or any do-code-change file (agent-builder's).
- No change to install.sh, `_install_tooling.py` or `--mode status`.
- No new check for repos that set their own `core.hooksPath` (they skip this hook today and still will).

## What the review found
Round 1 (two lenses, Standards and Spec; no high-risk file):
- standards-1 [important] R3: the bypass rule named a person in the shipped hook and disagreed with install.md — addressed (fix round 1: "the machine's owner" everywhere, Mark's ruling)
- spec-1 [suggestion] install.md stated a different `--no-verify` rule from the hook — addressed
- spec-3 [nit] plan step 3's wording against the test's own refusal — addressed (plan amended)
- spec-2 [suggestion] README/CHANGELOG state that a missing python blocks, with no test — open (stands by Mark's "fail loud" ruling)
- standards-2 to -4 [suggestion] S2: test setup copied from the sibling test; the fake written inline; the refusal set up twice — open
- standards-5 [suggestion] T1: the closing line pinned on the dcc path only; python-missing untested — open
- standards-6 [suggestion] PY10: a fixture class in the test module — open
- standards-7 to -13 [nit] N7 `repo()` name; R10 cleanup on a failed install; G4 git return codes; R9 `main` catches only AssertionError; R3 "NOT checked" vs "NOT CHECKED"; G16 one-line conditional; R8 `head()` returns "" — open

Round 2 (focused on the fix): Standards clear; spec-4 [nit] and spec-5 [suggestion], two wording slips in the run's own notes — addressed (notes amended).

## What was verified
- tests: PASS — `uv run python tests/scripts/test_git_hooks_dcc.py` "4/4 passed" (exit 0); `uv run python tests/scripts/test_git_hooks.py` "18/18 passed" (exit 0); both run fresh after the last commit (e3bea6b)
- diff contains the change: PASS — `git diff bc898ad --stat` lists every file the plan's steps name, 166 insertions, 6 deletions; `git status --short` prints nothing
- findings addressed: PASS — `review-ledger.py query --cap 3` exit 0, "met - no open blocking item, every verdict current (1 closed, 17 non-blocking), 2 round(s)"
- frozen tests: PASS — check-freeze.py exit 0, "frozen-tests layer: PASS — 5 entries checked, all match or unfrozen with a reason (1 retired: deleted on purpose) (2 frozen green, each with its reason)"
- coverage: PASS — every done criterion pinned by an existing test or marked manual
- bar unmoved: PASS — floor-guard.py exit 0, "floor-guard: exit 0 - clean: no move lowers the bar"
- in scope: PASS — scope-guard.py exit 0, "scope-guard: exit 0 - PASS: every touched file is inside the declared scope"
- tests-bite: not checked — prove_tests_bite.py --check "VERDICT: COULD-NOT-RUN" (0 changed source files); the changed code is a POSIX sh hook, no mutation skill exists for shell; bite shown by hand against the fixed point. Accepted by Mark (2026-11-12).
- VERDICT: FAIL — tests-bite (approved)

## Working files
Unchanged copies in the notebook's raw folder; the same files are archived in the code repository at `.do-code-change/archive/2026-11-12-241-pre-commit-dcc-check/`.

- [budget.json](../../../raw/code-changes/2026-11-12-241-pre-commit-dcc-check/budget.json)
- [checkpoints.md](../../../raw/code-changes/2026-11-12-241-pre-commit-dcc-check/checkpoints.md)
- [doubt-log.md](../../../raw/code-changes/2026-11-12-241-pre-commit-dcc-check/doubt-log.md)
- [name-review.md](../../../raw/code-changes/2026-11-12-241-pre-commit-dcc-check/name-review.md)
- [plan.md](../../../raw/code-changes/2026-11-12-241-pre-commit-dcc-check/plan.md)
- [readonly-review.json](../../../raw/code-changes/2026-11-12-241-pre-commit-dcc-check/readonly-review.json)
- [requirements.md](../../../raw/code-changes/2026-11-12-241-pre-commit-dcc-check/requirements.md)
- [review-findings.md](../../../raw/code-changes/2026-11-12-241-pre-commit-dcc-check/review-findings.md)
- [review-ledger.json](../../../raw/code-changes/2026-11-12-241-pre-commit-dcc-check/review-ledger.json)
- [run.json](../../../raw/code-changes/2026-11-12-241-pre-commit-dcc-check/run.json)
- [scope-baseline.json](../../../raw/code-changes/2026-11-12-241-pre-commit-dcc-check/scope-baseline.json)
- [test-freeze.json](../../../raw/code-changes/2026-11-12-241-pre-commit-dcc-check/test-freeze.json)
- [verification-result.md](../../../raw/code-changes/2026-11-12-241-pre-commit-dcc-check/verification-result.md)

## Related
- [code-changes/ — the folder and its tags](README.md)
- [Machine-wide pre-commit hook: gitleaks and a private-words list](../decisions/machine-wide-pre-commit-hook-gitleaks-and-private-words-2026-10-14.md) — the hook this change extends
- [90 Safety guards and hooks](../architecture/90-safety-guards-and-hooks.md)
