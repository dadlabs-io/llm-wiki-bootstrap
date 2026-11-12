# Checkpoints — 241-pre-commit-dcc-check

## Size proposed — 2026-11-12

Size: small (proposed; Mark confirms at Change confirmation)
- No open design decision: plan.md's Decisions needed is "none"; the two choices are requirements Decisions 1-2, put below.
- Nothing outside the change uses what it changes: the hook's interface to git (exit code, stderr) is unchanged; install.sh and `_install_tooling.py` copy it without reading it.
- No schema change or migration.
- No write to live data outside the tests (tests run under a temporary HOME; the install on this machine is the finish).
- No HIGH file (auth, sessions, tokens, crypto, payments, external calls).
- No existing refusal changed: gitleaks, private words and the repo hook refuse as before (pinned by existing tests); only the closing hint's wording changes.
- Production files in Scope: 1 (pre-commit) plus docs and the test file. Shown, not deciding.

## Change confirmation — 2026-11-12 (in part; size still open)

Mark (Discord, 22:14): "2. Agreed. We don't ignore changes we need to do they need to be fixed? No verify is strictly. I need to say that's okay to do" → Decision 1: closing line "fix the lines above. --no-verify only when Mark has said so."
"3. If python can't be found, fail loud. We don't need to handle how we're going to do this if it's not there." → Decision 2: no guard; the change request's line as given; plan step 3 (python not found) removed, steps renumbered.
Size: small — Mark (Discord, 22:16): "Okay yeah so this is a small change so create the small change process."

Scope widened (implement, before the first red): the new checks go in `tests/scripts/test_git_hooks_dcc.py`, not `test_git_hooks.py`. Reason: that file has no test functions (it runs its checks at import), so check-freeze would hash the whole file and step 2's additions would break step 1's freeze; one function per check in a new file keeps each freeze to its own test. `test_git_hooks.py` is unchanged and still runs as the invariants' check.

## Fix round 1 — 2026-11-12

Mark (Discord, 22:49), on standards-1: "It should say the human. Machine owner. Operator. Something consistent" → the closing line, the hook's header, README, install.md and CHANGELOG all say "--no-verify only when the machine's owner has said so". The test was renamed `test_blocked_commit_says_no_verify_needs_the_owner` (old entry retired with that reason) and frozen red before the hook changed. Plan step 3's wording amended in place (spec-3).
Left open (non-blocking, a verdict of open in the ledger): standards-2 to -13 and spec-2. spec-2 (README/CHANGELOG state that a missing python blocks, with no test) stands by Mark's ruling "fail loud, no special handling"; the rest are test-file layout and naming suggestions, parked for Mark at the finish.
