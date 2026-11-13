# 2026-11-12 242-dcc-test-tidy — the git-hook tests share one harness, one function per check

## TL;DR
The machine-wide git hook's tests now share `tests/scripts/_git_hooks_harness.py` (a temporary-HOME `Machine`, `machine()`, a runner that reports a crash as ERROR and refuses an unknown name), and `test_git_hooks.py`'s 18 checks are one function each. New checks: a gitleaks block ends on the owner line; every dcc check fails on the hook from before #241 with its own message; the runner's two paths. It answers #241's open review nits (Mark: fix what is worth fixing now). The run went from small to full at its second fix round and reached the retry ceiling at review round 4; Mark chose to continue manually. Kept on main.

## What changed
- 1. Shared harness, and the dcc test file moved onto it
- 2. `test_git_hooks.py` converted to one function per check on the harness
- 3. The runner reports any exception and refuses an unknown name
- 4. A gitleaks block also ends on the owner line
- 5. Docstrings say why each check gets its own HOME, and the README's Tests paragraph names the harness

New tags: none.

## Why: decisions and exclusions
Decisions:

1. **Which findings to fix** — decided by Mark (Discord, 2026-11-13 00:52): "If the work's fixing, let's fix them now." Fix standards-3, -4, -5 (first half), -6, -8, -9, -10, -13 and also -2 and -7: `tests/scripts/test_git_hooks.py` is converted to one function per check, both test files share one harness module, and `repo()` becomes `new_repo()` in both. Drop -11 and -12 (Exclusions).

Exclusions:

- No change to `tools/git-hooks/pre-commit`: standards-11 (the "NOT CHECKED -" wording) and standards-12 (the one-line conditional) are agent-builder's lines as given; dropped as not worth fixing (Mark, 2026-11-13: "If they're not worth fixing then we can put them off").
- No python-absent test (standards-5's second half): Mark ruled no special handling.

## What the review found
Four review rounds (two lenses each; no high-risk file). Each round after the first reviewed only the previous fix, and each found faults in that fix's own new code, mostly the old-hook bite test as it grew; none were regressions.
- Round 1 (14): copied lifecycle and runner line, unused parameters and import, an unexplained 36, a text-coupled hand-over check, an unasserted setup step — addressed; three token checks on separate machines, moves and new checks in one step, a repeated constructor guard — left open (reasons in checkpoints.md). Spec: no proof the restructured dcc checks fail on the old hook, and none of the runner's crash path — addressed as real tests on Mark's word ("Make them real tests").
- Round 2 (7): setup blocks checked only the exit code; a copied marker hook; the bite test covered one check of five; the plan's "no assertion changed" — addressed.
- Round 3 (9): the bite loop counted any failure; a process-wide override reset to None; the ERROR line matched in parts; a hand-typed check list; plan wording — addressed.
- Round 4 (5, at the cap): an assert order and an expected message taken from hook output, and the plan's missing bite-test bullet — addressed by hand (Mark: continue manually); two small S2 nits left open.

## What was verified
- tests: PASS — test_git_hooks_dcc.py "6/6 passed"; test_git_hooks_harness.py "2/2 passed"; test_git_hooks.py "18/18 passed"; run fresh after the last edit
- diff contains the change: PASS — the five Scope files, 430 insertions, 223 deletions; nothing untracked
- findings addressed: PASS — review-ledger.py query exit 0, "met - no open blocking item, every verdict current (9 closed, 26 non-blocking), 4 round(s)"; continue manually at the ceiling (Mark)
- frozen tests: PASS — check-freeze.py exit 0, "frozen-tests layer: PASS — 27 entries checked (+ 5 from earlier changes), all match or unfrozen with a reason (2 retired: deleted on purpose) (26 frozen green, each with its reason)"
- coverage: PASS — each step pinned by its suite or named check; the invariant's fail side by test_every_dcc_check_fails_on_the_hook_before_241
- bar unmoved: PASS — floor-guard.py exit 0, "clean: no move lowers the bar" (a `# noqa: BLE001` it first flagged was removed)
- in scope: PASS — scope-guard.py exit 0
- tests-bite: not checked — prove_tests_bite.py "VERDICT: COULD-NOT-RUN" (0 changed source files; test-only change); bite shown by hand per test; accepted by Mark
- VERDICT: FAIL — tests-bite (approved)

## Working files
Unchanged copies in the notebook's raw folder; the same files are archived in the code repository at `.do-code-change/archive/2026-11-12-242-dcc-test-tidy/`.

- [budget.json](../../../raw/code-changes/2026-11-12-242-dcc-test-tidy/budget.json)
- [checkpoints.md](../../../raw/code-changes/2026-11-12-242-dcc-test-tidy/checkpoints.md)
- [doubt-log.md](../../../raw/code-changes/2026-11-12-242-dcc-test-tidy/doubt-log.md)
- [name-review.md](../../../raw/code-changes/2026-11-12-242-dcc-test-tidy/name-review.md)
- [plan.md](../../../raw/code-changes/2026-11-12-242-dcc-test-tidy/plan.md)
- [readonly-review.json](../../../raw/code-changes/2026-11-12-242-dcc-test-tidy/readonly-review.json)
- [requirements.md](../../../raw/code-changes/2026-11-12-242-dcc-test-tidy/requirements.md)
- [review-findings.md](../../../raw/code-changes/2026-11-12-242-dcc-test-tidy/review-findings.md)
- [review-ledger.json](../../../raw/code-changes/2026-11-12-242-dcc-test-tidy/review-ledger.json)
- [run.json](../../../raw/code-changes/2026-11-12-242-dcc-test-tidy/run.json)
- [scope-baseline.json](../../../raw/code-changes/2026-11-12-242-dcc-test-tidy/scope-baseline.json)
- [test-freeze.json](../../../raw/code-changes/2026-11-12-242-dcc-test-tidy/test-freeze.json)
- [verification-result.md](../../../raw/code-changes/2026-11-12-242-dcc-test-tidy/verification-result.md)

## Related
- [code-changes/ — the folder and its tags](README.md)
- revises: [2026-11-12 241-pre-commit-dcc-check](2026-11-12-241-pre-commit-dcc-check-the-machine-pre-commit-runs-do-code-change-s.md) — the change whose test file this tidies
- [90 Safety guards and hooks](../architecture/90-safety-guards-and-hooks.md)
