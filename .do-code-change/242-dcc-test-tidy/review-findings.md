# Review findings — 242-dcc-test-tidy, round 1

Fixed point 58767fd; 4 files, tests and one README. Prescan clean; read-only guard PASS.

## Standards

- [suggestion] `tests/scripts/test_git_hooks.py:26` and 22 other test bodies — S2: the `m = Machine()` / `try` / `finally: m.close()` lifecycle is copied in 23 tests. Fix: a context manager in the harness.
- [suggestion] `tests/scripts/test_git_hooks.py:224` and `tests/scripts/test_git_hooks_dcc.py:91` — S2: the same `TESTS = {...}` line in both files. Fix: `collect_tests(globals())` in the harness.
- [suggestion] `tests/scripts/test_git_hooks.py:70`, `:79`, `tests/scripts/test_git_hooks_dcc.py:78` — S2: three checks each plant a token on a fresh Machine. Fix: one commit, or a harness helper.
- [suggestion] `tests/scripts/_git_hooks_harness.py:44` and `:72` — S9/R26: `run(env=None)` and `commit(*extra)` have no caller using them. Fix: drop both.
- [suggestion] `tests/scripts/test_git_hooks.py:48` — R13: the hand-over check reads the stub's text. Fix: run the stub in a scratch repo and assert it reaches the repo's own hook.
- [suggestion] `tests/scripts/test_git_hooks.py` and `tests/scripts/test_git_hooks_dcc.py:78` — R22/R25: moves and new checks land in one step. Fix: separate commits.
- [nit] `tests/scripts/_git_hooks_harness.py:108` and `:95-98` — R21/T3: the runner's ERROR and unknown-name branches are exercised by no check. Fix: a check each, or record the runs.
- [nit] `tests/scripts/test_git_hooks.py:14` — S15: `Path` imported, never used. Fix: delete.
- [nit] `tests/scripts/test_git_hooks.py:128` — G31: the setup commit's result unasserted. Fix: assert it was blocked.
- [nit] `tests/scripts/test_git_hooks.py:28` — G16: the assert repeats the constructor's own guard. Fix: drop it.
- [nit] `tests/scripts/_git_hooks_harness.py:25` — G25: `range(36)` unexplained. Fix: a named constant.

Unverified:
- `tests/scripts/test_git_hooks_optin.py` still has its own setup (outside the diff); 23 installs' runtime not measured.

Coverage: every every-diff rule and pasted section has a row in the lens report; found S2, S9/R26, G25, R13, G31, G16, S15, R21/T3, R22/R25; the rest clear or n/a.
Well built: each check has its own temporary HOME, and both files share one harness.

## Spec

- [important] `.do-code-change/242-dcc-test-tidy/checkpoints.md` (Implement) — the plan's invariant says every existing check "still fails at the fixed point's hook"; the four restructured dcc checks were shown green only, and the pass test's body changed. Fix: run them against bc898ad's hook and record the red tails.
- [important] `.do-code-change/242-dcc-test-tidy/checkpoints.md` (step 3) — the plan names evidence for "a deliberately raising test"; only the unknown-name run is recorded. Fix: run a throwaway raising check and record the ERROR line and exit 1.
- [suggestion] `tests/scripts/test_git_hooks.py:127-130` — `test_committed_word_is_not_rechecked`'s setup commit is unasserted though its unfreeze reason says "the setup commit's outcome". Fix: assert it was blocked.

Unverified:
- The step 4 red tail and the 18/18 claims are producer records, not re-run by the lens.

Coverage: every plan step, invariant, decision, exclusion and the harness API has a row in the lens report; found: the invariant, step 3; the rest clear.
Well built: one harness owns setup and the runner; the 18 checks survive as functions with their assertions kept or strengthened.

## Change risk

| File | Risk | Part | Standards | Spec | Change risk |
|---|---|---|---|---|---|
| `tests/scripts/_git_hooks_harness.py` | LOW (test) | 1 | in full | in full | — |
| `tests/scripts/test_git_hooks.py` | LOW (test) | 1 | in full | in part (diff) | — |
| `tests/scripts/test_git_hooks_dcc.py` | LOW (test) | 1 | in full | in part (diff) | — |
| `tools/git-hooks/README.md` | LOW (docs) | 1 | in full (hunk) | in part | — |

No high-risk file; the change-risk lens was not run.

Standards: 11 findings (6 suggestions, 5 nits). Spec: 3 findings (2 important: the invariant's red evidence, the runner's raising path). Change risk: not run.

VERDICT: Standards FINDINGS · Spec FINDINGS · Change risk NOT RUN · needs-a-human 0
