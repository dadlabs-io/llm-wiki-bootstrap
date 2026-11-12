# Verification — 241-pre-commit-dcc-check (2026-11-12)

tests: PASS — `uv run python tests/scripts/test_git_hooks_dcc.py` "4/4 passed" (exit 0); `uv run python tests/scripts/test_git_hooks.py` "18/18 passed" (exit 0); both run fresh after the last commit (e3bea6b)
diff contains the change: PASS — `git diff bc898ad --stat` lists every file the plan's steps name (tools/git-hooks/pre-commit, tests/scripts/test_git_hooks_dcc.py, tools/git-hooks/README.md, wiki-seed/install.md, CHANGELOG.md), 166 insertions, 6 deletions; `git status --short` prints nothing (all committed, none untracked)
findings addressed: PASS — `review-ledger.py query --cap 3` exit 0, "met - no open blocking item, every verdict current (1 closed, 17 non-blocking), 2 round(s)"; the one important finding (standards-1) re-read at its sites: pre-commit:8 and :31, README:21, install.md:124 now say "the machine's owner"
frozen tests: PASS — check-freeze.py exit 0, "frozen-tests layer: PASS — 5 entries checked, all match or unfrozen with a reason (1 retired: deleted on purpose) (2 frozen green, each with its reason)"
   frozen green: test_absent_pack_commits_with_a_not_checked_line — Step 1's two lines carry both branches; bite shown by hand: with the hook stashed back to HEAD the test failed (0/1), with the change it passes.
   frozen green: test_dcc_pass_lets_the_commit_through — bite shown by hand: with the hook restored to the fixed point bc898ad the test fails ("the dcc check did not run"); with the change it passes.
coverage: PASS — every done criterion pinned by an existing test or marked manual (map below)
bar unmoved: PASS — floor-guard.py exit 0, "floor-guard: exit 0 - clean: no move lowers the bar" (166 added, 6 removed lines checked)
in scope: PASS — scope-guard.py exit 0, "scope-guard: exit 0 - PASS: every touched file is inside the declared scope"
tests-bite: not checked — prove_tests_bite.py --check: "tests-bite layer: COULD-NOT-RUN against bc898ad (0 changed source file(s))", "VERDICT: COULD-NOT-RUN"; the changed production code is a POSIX sh hook, and no mutation skill exists for shell. Each new test's bite was shown by hand against the fixed point's hook (freeze records above and the red witnesses of the refusal and closing-line tests).

## Coverage map

| Plan criterion | Expected (incl. negative) | Test | Status |
|---|---|---|---|
| 1 Expected: a passing check lets a clean commit through, nothing printed | check ran (marker), exit 0, a commit made, no dcc text | `test_dcc_pass_lets_the_commit_through` | existing |
| 1 Failures: a refusing check blocks the commit | exit non-zero, the check's message on stderr, HEAD unchanged | `test_dcc_refusal_blocks_the_commit` | existing |
| 1 Invariant: a staged secret still blocked | blocked, file named | `test_git_hooks.py` "a staged GitHub token is blocked" | existing |
| 1 Invariant: a private word still blocked, file and line | blocked, `report.md:2:` | `test_git_hooks.py` private-word checks | existing |
| 1 Invariant: missing gitleaks still NOT checked | blocked | `test_git_hooks.py` "no gitleaks" | existing |
| 1 Invariant: repo's own hooks still run and can block | runs; failing local blocks | `test_git_hooks.py` `_local` checks | existing |
| 1 Invariant: `--no-verify` still commits | commit made | `test_git_hooks.py` "--no-verify commits anyway" | existing |
| 2 pack absent: commit goes on, NOT CHECKED line | exit 0, commit made, the line on stderr | `test_absent_pack_commits_with_a_not_checked_line` | existing |
| 3 the closing line after a block | last stderr line is the owner line; no "commit anyway" | `test_blocked_commit_says_no_verify_needs_the_owner` | existing |
| 3 README and install.md name the check and the hint | each sentence true of steps 1-2's tests | manual: step 3 — README:12-16 and :21, install.md:123-124 read against the tests; the python-missing sentence stands by Mark's "fail loud" ruling, no test | manual |
| 3 CHANGELOG one dated entry | entry under 2026-11-12 | manual: CHANGELOG.md:14-16 read | manual |

VERDICT: FAIL — tests-bite
