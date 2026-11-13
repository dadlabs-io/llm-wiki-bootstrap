# Checkpoints — 242-dcc-test-tidy

## Size proposed — 2026-11-12

Size: small (proposed). No open design decision (plan Decisions needed: none; the one choice is requirements Decision 1); nothing outside the change uses the test file; no schema, no live data, no HIGH file; no existing refusal changed (one assertion added). Production files: 0 (one test file).

## Change confirmation — 2026-11-13

Size: small — Mark (Discord): "If the work's fixing, let's fix them now. If they're not worth fixing then we can put them off." → fix the 8 plus standards-2 and -7 (old test converted, shared harness, `new_repo` in both); drop -11 and -12 (agent-builder's given lines). Requirements Decision 1 and the plan rewritten in place; scope widened to `test_git_hooks.py`, the new harness module and the hooks README.
