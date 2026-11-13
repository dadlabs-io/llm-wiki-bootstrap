# Checkpoints — 242-dcc-test-tidy

## Size proposed — 2026-11-12

Size: small (proposed). No open design decision (plan Decisions needed: none; the one choice is requirements Decision 1); nothing outside the change uses the test file; no schema, no live data, no HIGH file; no existing refusal changed (one assertion added). Production files: 0 (one test file).

## Change confirmation — 2026-11-13

Size: small — Mark (Discord): "If the work's fixing, let's fix them now. If they're not worth fixing then we can put them off." → fix the 8 plus standards-2 and -7 (old test converted, shared harness, `new_repo` in both); drop -11 and -12 (agent-builder's given lines). Requirements Decision 1 and the plan rewritten in place; scope widened to `test_git_hooks.py`, the new harness module and the hooks README.

## Implement — 2026-11-13

Mark (Discord, 00:55): "Let's do 3 4 then" (confirms standards-2 and -7 in scope).
Steps 1-2: both files moved onto `_git_hooks_harness.py`; before: dcc 4/4, old suite 18/18 (as one import-time script); after: dcc 4/4, old suite 18/18 as functions. Step 3: `run_tests` refuses an unknown name — `test_git_hooks_dcc.py no_such_check` printed "unknown check(s): no_such_check" and the known list, exit 2. Step 4: `test_gitleaks_block_ends_on_the_owner_line` frozen red against the fixed point bc898ad's hook (exit 1), green on the current hook; dcc file 5/5. Step 5: README Tests paragraph names the harness. Order note: the runner (step 3) was written with the harness in step 1.
