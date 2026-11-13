# Review findings — 242-dcc-test-tidy, round 3 (focused)

Scope: fix round 2's diff (5adfcaf → HEAD) and the sibling sites of its addressed findings. Prescan clean; read-only guard PASS.

## Standards

- [important] `tests/scripts/test_git_hooks_dcc.py:92-93` — PY9: `except AssertionError: continue` counts any assertion, a setup failure or a missing gitleaks included, as the old hook failing. Fix: verify the override first, and require each check's own expected failure.
- [suggestion] `tests/scripts/_git_hooks_harness.py:38` — S17: `pre_commit_override` is process-wide state reset to None, not restored. Fix: a context manager that saves and restores it.
- [suggestion] `tests/scripts/test_git_hooks_harness.py:36` — R15: the ERROR line's parts can match separately. Fix: one regex for the line.
- [nit] `tests/scripts/test_git_hooks_dcc.py:84-86` — R12: the five checks are hand-listed; a sixth would escape. Fix: derive them from the module.

Unverified:
- That bc898ad's hook exists and lacks the dcc lines (no shell; the returncode assert would fail loudly).

Coverage: S2 clear; S17 found; R14 clear; R15 found; PY9 found; R12 found; S9/R26 clear.
Well built: each check builds its own Machine under machine(), and the override is cleared in finally.

## Spec

- [important] `.do-code-change/242-dcc-test-tidy/plan.md:25` — "The refactor steps change no assertion" is untrue after fix round 2 (two private-word asserts added, the ERROR check changed); only the hand-over departure is in the plan. Fix: list all three departures.
- [suggestion] `.do-code-change/242-dcc-test-tidy/plan.md:17` — the API list omits ROOT, HOOKS, SH, DCC_REL, close and the Machine attributes. Fix: add them or say it lists helpers only.
- [suggestion] `tests/scripts/test_git_hooks_harness.py:36` — the plan's `ERROR <name>  [<type>: <message>]` format is no longer pinned. Fix: an exact-format assertion.
- [suggestion] `tests/scripts/test_git_hooks_dcc.py:84-86` — the hand-typed five-check list. Fix: derive it.
- [suggestion] `tests/scripts/test_git_hooks_dcc.py:92-93` — any assertion counts as the old hook failing. Fix: assert the expected message.

Unverified:
- bc898ad's hook content not read; the bite run in test-freeze.json not re-run.

Coverage: invariant (five checks, bc898ad hook, fails if any passes) met; hand-over departure met; API list partly met; plan wording found; scope clear.
Well built: the bite test reads the old hook from git history, and the override is applied in Machine.__init__.

## Change risk

| File | Risk | Part | Standards | Spec | Change risk |
|---|---|---|---|---|---|
| `tests/scripts/_git_hooks_harness.py` | LOW (test) | 1 | in full | in full | — |
| `tests/scripts/test_git_hooks_dcc.py` | LOW (test) | 1 | in full | in full | — |
| `tests/scripts/test_git_hooks.py` | LOW (test) | 1 | in part (diff) | in part (diff) | — |
| `tests/scripts/test_git_hooks_harness.py` | LOW (test) | 1 | in part (diff) | in part (diff) | — |

No high-risk file; the change-risk lens was not run.

Standards: 4 findings (1 important). Spec: 5 findings (1 important). Change risk: not run.

VERDICT: Standards FINDINGS · Spec FINDINGS · Change risk NOT RUN · needs-a-human 0
