# Review findings — 242-dcc-test-tidy, round 2 (focused)

Scope: what fix round 1 moved (665ba18 → HEAD) plus the sibling sites of its addressed findings. Prescan clean; read-only guard PASS.

## Standards

- [important] `tests/scripts/test_git_hooks.py:101` (and `:90`) — PY9: `assert blocked.returncode != 0, "the private word was not blocked first"` passes for any refusal, never reading stderr. Fix: also assert "private word" in stderr.
- [suggestion] `tests/scripts/test_git_hooks.py:41` and `:130` — S2: the same marker-hook script is written twice. Fix: a harness helper.
- [nit] `tests/scripts/test_git_hooks_dcc.py:79-80` — S2: the hook file is read twice. Fix: read once.
- [suggestion] `tests/scripts/test_git_hooks_harness.py:36` — R13: the check pins the runner's exact print format, two spaces included. Fix: assert the parts.

Unverified:
- `test_git_hooks.py:49` reads hooks.conf's text (R13), a line the fix did not touch: out of this round.

Coverage: S2 found; S9/R26, S15, R14, R15, G31, R12 clear; R13 found; PY9 found.
Well built: `run_tests` prints the exact lines the runner's own checks assert.

## Spec

- [important] `tests/scripts/test_git_hooks_dcc.py:76` — the plan invariant "Every dcc check still passes on the current hook and fails at the fixed point bc898ad's hook" is a test for the refusal check only; the other four checks' failure at bc898ad is still only in the notes. Fix: one test running every dcc check against bc898ad's hook, expecting each to fail.
- [suggestion] `tests/scripts/test_git_hooks.py:122-126` — the plan says the refactor "change[s] no assertion", but the hand-over check's text assertion was replaced by a behavioural one. Fix: record the departure in plan.md.
- [nit] `.do-code-change/242-dcc-test-tidy/plan.md:17` — the harness API list lacks `machine()`, `collect_tests`, `GITHUB_TOKEN_BODY_LEN`. Fix: add them.

Unverified:
- The 0/5 run and the bc898ad hook contents (no shell).

Coverage: spec-1 found (partial); spec-2 clear; spec-3 clear; scope clear; plan wording found.
Well built: the runner checks assert the exact strings the runner prints.

## Change risk

| File | Risk | Part | Standards | Spec | Change risk |
|---|---|---|---|---|---|
| `tests/scripts/_git_hooks_harness.py` | LOW (test) | 1 | in full | in full | — |
| `tests/scripts/test_git_hooks.py` | LOW (test) | 1 | in full | in part (diff) | — |
| `tests/scripts/test_git_hooks_dcc.py` | LOW (test) | 1 | in full | in full | — |
| `tests/scripts/test_git_hooks_harness.py` | LOW (test) | 1 | in full | in full | — |

No high-risk file; the change-risk lens was not run.

Standards: 4 findings (1 important). Spec: 3 findings (1 important). Change risk: not run.

VERDICT: Standards FINDINGS · Spec FINDINGS · Change risk NOT RUN · needs-a-human 0
