# Checkpoints — 242-dcc-test-tidy

## Size proposed — 2026-11-12

Size: small (proposed). No open design decision (plan Decisions needed: none; the one choice is requirements Decision 1); nothing outside the change uses the test file; no schema, no live data, no HIGH file; no existing refusal changed (one assertion added). Production files: 0 (one test file).

## Change confirmation — 2026-11-13

Size: small — Mark (Discord): "If the work's fixing, let's fix them now. If they're not worth fixing then we can put them off." → fix the 8 plus standards-2 and -7 (old test converted, shared harness, `new_repo` in both); drop -11 and -12 (agent-builder's given lines). Requirements Decision 1 and the plan rewritten in place; scope widened to `test_git_hooks.py`, the new harness module and the hooks README.

## Implement — 2026-11-13

Mark (Discord, 00:55): "Let's do 3 4 then" (confirms standards-2 and -7 in scope).
Steps 1-2: both files moved onto `_git_hooks_harness.py`; before: dcc 4/4, old suite 18/18 (as one import-time script); after: dcc 4/4, old suite 18/18 as functions. Step 3: `run_tests` refuses an unknown name — `test_git_hooks_dcc.py no_such_check` printed "unknown check(s): no_such_check" and the known list, exit 2. Step 4: `test_gitleaks_block_ends_on_the_owner_line` frozen red against the fixed point bc898ad's hook (exit 1), green on the current hook; dcc file 5/5. Step 5: README Tests paragraph names the harness. Order note: the runner (step 3) was written with the harness in step 1.

## Fix round 1 — 2026-11-13

Fixed: standards-1 (`with machine()` in the harness), -2 (`collect_tests`), -4 (`run(env)` and `commit(*extra)` dropped), -5 (hand-over check now runs each stub in a scratch repo and asserts it reached the repo's own hook), -8 (unused `Path` import), -9 and spec-3 (committed-word setup asserted), -11 (`GITHUB_TOKEN_BODY_LEN`).
Evidence for spec-1: the five dcc checks run against the fixed point bc898ad's hook: "0/5 passed" — FAIL pass ("the dcc check did not run"), refusal ("the commit went through"), absent pack (no NOT CHECKED line), owner line ("the commit went through"), gitleaks owner line (old closing line); on the current hook 5/5. The plan's invariant is narrowed in place: the 18 #135 checks test behaviour bc898ad already had, so only the dcc checks can fail there.
Evidence for spec-2 and standards-7: a throwaway run of `run_tests` with a raising check printed "ERROR test_raises  [RuntimeError: deliberate]", "1/2 passed", exit 1; the unknown-name run (Implement) exit 2.
Left open, with reasons: standards-3 (three token checks each own one concept, R12), -6 (moves and new checks already committed; history is not rewritten), -10 (the constructor guard is the fixture's; `test_install_exits_zero` keeps #135's check).
Suites: test_git_hooks.py 18/18, test_git_hooks_dcc.py 5/5; all 23 re-frozen with reason "fix round 1".

## Fix round 1, continued — 2026-11-13

Mark (terminal, 2026-11-13) on spec-1 and spec-2: "Make them real tests" (not accepted on recorded evidence). Scope widened: `tests/scripts/test_git_hooks_harness.py`, the runner's own checks (spec-2: a crashing check reported as ERROR; an unknown name refused). spec-1 becomes `test_refusal_needs_the_hook_dcc_lines` in the dcc file: with the dcc lines stripped from the installed hook, a refusing fake no longer blocks.

Ledger after the real tests: `query --cap 3` met (2 closed, 12 non-blocking); `fixed` still exit 1 on spec-1/spec-2 ("checkpoints.md did not move since round 1"), its round-1 fingerprint of the notes path never moving (skill suggestion filed). The focused round is dispatched with the fix diff, which now holds both tests.

Size: full — second fix round (review round 2 found two important findings); the rounds already spent count toward the full ceiling of 3.

## Fix round 2 — 2026-11-13

spec-1 (round 2): `test_every_dcc_check_fails_on_the_hook_before_241` runs all five dcc checks with the hook from bc898ad installed over the new one (`Machine.pre_commit_override`) and requires each to fail; bite shown: with HEAD's hook it failed. It replaces `test_refusal_needs_the_hook_dcc_lines` (retired with that reason). standards-1 (round 2): both setup blocks assert the private-word message too. S2: `write_marker_hook` in the harness. R13: the ERROR check asserts its parts. spec-2/nit (round 2): plan's API list and the hand-over departure recorded in place. Suites 6/6, 18/18, 2/2; check-freeze PASS.

## Fix round 3 — 2026-11-13

The bite test now: checks the old hook has no dcc call, installs it through `hook_override` (saves and restores), verifies a Machine got it, derives the checks from the module (the bite test excluded) and requires each to fail with its own message in `OLD_HOOK_FAILURES` (a set equality makes a new check need an entry); anything else is re-raised. The absent-pack assert gained a message for that match. The runner's ERROR line is matched whole by one regex. Plan Testing Decisions and the harness API list rewritten in place. Suites 6/6, 2/2, 18/18; check-freeze PASS. Bite with HEAD's hook: refused by the precondition.
