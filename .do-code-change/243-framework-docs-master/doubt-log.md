## Step 1: toolset refresh (remove scan, _guarded, rmdir of the emptied old folder)

CLAIM: "seed_toolset writes the six docs at wiki/best-practices/framework/, deletes the old copies and the emptied old folder only, names any OSError from a copy or delete in `failed` and carries on, and a dry run has no `failed`."
Cycle 1: reads (`read_bytes` in toolset_status), `glob` and `iterdir` are not guarded, so an unreadable or unlistable file raises out of seed_toolset — trade-off (plan scopes the guard to writes, unlink and rmdir; a read failure is not in step 1's Failures); every `*.md` in the old folder is deleted, not only the six — noise (plan Implementation Decisions: "remove scan extended to TOOLSET_OLD_FRAMEWORK_DOCS/*.md"); the old copy is unlinked even when the new copy's write failed, so a doc may exist at neither path until the next run — trade-off (the plan says all removals and copies still run; the next status reports the add, so it self-heals), named in the hand-back; `glob("*.md")` also matches `.MD` on Windows — noise (same file type there, unconfirmed by a run)
STOP: trivial findings (no finding changed the artifact; no plan sentence is contradicted by an accepted trade-off)

## Step 2: toolset `local/README.md` as a listed framework file

no non-trivial decision (step 2): the change is one added entry in `toolset_files()`, one constant and one shipped text. The property "a user's file in `local/` is never added, changed, removed or listed in `remove`" is held by adding no code (the remove scan is not extended to `local/`, and only the README is listed) and is pinned by `test_user_files_in_local_are_untouched`, so a behavioural test covers it and no doubt cycle was spawned.
