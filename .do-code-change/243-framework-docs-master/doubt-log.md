## Step 9: no non-trivial decision (doc text, links and version numbers only; Trivial stakes: yes)

## Step 10: no non-trivial decision (doc wording in framework-docs/wiki-frontmatter-best-practices.md, no Python line changed)

The wording changes are pinned by eight tests in test_standalone.py (seam C). Readers checked first: the only reader of the rubric is `tier_rubric_text()` in wiki-update.py, which cuts the span between the headings `### tier rubric` and `### review cadence` and prints it; no script or skill parses the cell text. The old cell text "code read beyond the README" occurs in no other shipped file (agents/wiki-ingester/AGENT.md:83 says "beyond the README" about how deep to read a repo, a different sentence).

## Step 1: toolset refresh (remove scan, _guarded, rmdir of the emptied old folder)

CLAIM: "seed_toolset writes the six docs at wiki/best-practices/framework/, deletes the old copies and the emptied old folder only, names any OSError from a copy or delete in `failed` and carries on, and a dry run has no `failed`."
Cycle 1: reads (`read_bytes` in toolset_status), `glob` and `iterdir` are not guarded, so an unreadable or unlistable file raises out of seed_toolset — trade-off (plan scopes the guard to writes, unlink and rmdir; a read failure is not in step 1's Failures); every `*.md` in the old folder is deleted, not only the six — noise (plan Implementation Decisions: "remove scan extended to TOOLSET_OLD_FRAMEWORK_DOCS/*.md"); the old copy is unlinked even when the new copy's write failed, so a doc may exist at neither path until the next run — trade-off (the plan says all removals and copies still run; the next status reports the add, so it self-heals), named in the hand-back; `glob("*.md")` also matches `.MD` on Windows — noise (same file type there, unconfirmed by a run)
STOP: trivial findings (no finding changed the artifact; no plan sentence is contradicted by an accepted trade-off)

## Step 2: toolset `local/README.md` as a listed framework file

no non-trivial decision (step 2): the change is one added entry in `toolset_files()`, one constant and one shipped text. The property "a user's file in `local/` is never added, changed, removed or listed in `remove`" is held by adding no code (the remove scan is not extended to `local/`, and only the README is listed) and is pinned by `test_user_files_in_local_are_untouched`, so a behavioural test covers it and no doubt cycle was spawned.

## Step 3: scaffold writes `wiki/best-practices/local/README.md`

no non-trivial decision (step 3): the production change is one list append in `taxonomy_for`, one `folder_notes` row, one `_render_template` call and one early `is_file()` guard (new branching, one `if`, returns 1 before the project folder or wiki is created). The guard's behaviour is a behavioural claim pinned by `test_missing_readme_source_stops_the_scaffold_before_any_best_practices_folder` (red first, then green), so no doubt cycle was spawned. Not decided here, sent back to the plan: how the shipped README passes the real mechanical lint (see the hand-back).

## Step 5: sweep of the old toolset framework path

no non-trivial decision (step 5): text substitutions at every site, plus one scan test. The only judgement calls, an allowlist for the line naming `TOOLSET_OLD_FRAMEWORK_DOCS` (only when the line does not also spell the path) and leaving the historical `topic-template/wiki/best-practices/framework/` text in INSTALL-INVENTORY.md line 72, are pinned by the scan test itself.

## Step 4: search and lint over `best-practices/local/`

no non-trivial decision (step 4): the only production change is one folder name added to the tuple of halves in `sample_titles` (no new branching, no boundary crossed, nothing irreversible). Its behaviour is pinned by `test_sample_titles_includes_best_practices_entries` (red first, then green). The other six tests pin behaviour that already held (`drop_machine_files`, the lint over `local/`); each was shown to bite by a transient mutation (production, reverted, `git diff` checked) or on a scratch copy of `scripts/` outside the repo (the lint file is outside the edit gate's scope), so no doubt cycle was spawned.
