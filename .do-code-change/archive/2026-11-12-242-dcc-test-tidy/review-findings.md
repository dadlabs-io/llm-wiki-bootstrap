# Review findings — 242-dcc-test-tidy, round 4 (focused, the last the cap allows)

Scope: fix round 3's diff (5ce9661 → HEAD). Prescan clean; read-only guard PASS.

## Standards

- [important] `tests/scripts/test_git_hooks_dcc.py:78-79` — PY9: in the pass check the marker assert runs before the exit-code assert, so a commit blocked for an unrelated reason still matches its expected message. Fix: assert the exit code first.
- [important] `tests/scripts/test_git_hooks_dcc.py:83` — PY9: the gitleaks check's expected message "commit anyway" is hook output, not a message the test wrote. Fix: give the owner-line assert its own message and key on it.
- [suggestion] `tests/scripts/test_git_hooks_dcc.py:92` — S2: `collect_tests` is run again where `TESTS` already holds the map. Fix: filter `TESTS`.
- [nit] `tests/scripts/test_git_hooks_dcc.py:42` — S2: "the commit went through" repeated five times. Fix: one constant.

Unverified:
- What the pre-#241 hook prints on a gitleaks block (no shell).

Coverage: PY9 found; S17, R14, R15, R12, S9/R26 clear; S2 found.
Well built: one context manager sets and restores the override; the set-equality guard keeps a new check from going untested.

## Spec

- [important] `.do-code-change/242-dcc-test-tidy/plan.md:22-29` — Testing Decisions names neither the bite test nor `OLD_HOOK_FAILURES`, though checkpoints says it was rewritten. Fix: add a bullet and correct the checkpoint sentence.

Unverified:
- bc898ad's closing line not read.

Coverage: the five round-3 claims met; scope clear; the invariant is a test.
Well built: the bite check now fails on a setup error, a wrong-reason failure, or a list mismatch.

## Change risk

| File | Risk | Part | Standards | Spec | Change risk |
|---|---|---|---|---|---|
| `tests/scripts/test_git_hooks_dcc.py` | LOW (test) | 1 | in full | in full | — |
| `tests/scripts/_git_hooks_harness.py` | LOW (test) | 1 | in full | in full | — |
| `tests/scripts/test_git_hooks_harness.py` | LOW (test) | 1 | in full | in full | — |

No high-risk file; the change-risk lens was not run.

Standards: 4 findings (2 important). Spec: 1 finding (important). Change risk: not run.

VERDICT: Standards FINDINGS · Spec FINDINGS · Change risk NOT RUN · needs-a-human 0
