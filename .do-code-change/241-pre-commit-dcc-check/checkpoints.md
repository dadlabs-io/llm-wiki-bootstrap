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
Size: asked again in plain words; waiting.
