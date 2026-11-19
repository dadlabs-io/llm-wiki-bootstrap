# Implement log — 243-framework-docs-master

One block per step, written by the orchestrator from the developer's hand-back and its own re-run.

## Step 1 — 2026-11-19
- Developer hand-back: green; orchestrator re-run `uv run python tests/scripts/test_global_toolset.py` → `50/50 passed`. Other suites the developer ran, all exit 0: test_tooling_state_seam 23/23, test_install_manifest 21/21, test_refresh_prunes 11/11, test_install_incomplete 25/25, test_not_checked 23/23, test_html_markdown 13/13, test_standalone 21/21.
- Changed: `scripts/_install_tooling.py`, `scripts/_wiki_config.py`, `scripts/new-wiki.py`, `scripts/wiki-update.py`, `agents/wiki-ingester/wiki-ingester-reading-list.json`, `tests/scripts/test_global_toolset.py`.
- Taken early from step 5: the reading list's 4 old-path links. The plan's own Invariant says the reading-list check moves to the new path in step 1, and that check can only pass if the file moves too. Step 5's sweep will find nothing left in that file.
- Plan correction (callers of `seed_toolset`'s dict): `phase_docs`, plus `_install_tooling_steps` → `install_tooling()` → `print_summary` (called by the global install in `new-wiki.py` and by `wiki-upgrade.py:68`). `--mode status` reads `toolset_status`, not the dict. Both are covered by tests.
- Accepted trade-off (doubt-log): the old copy is unlinked even when the new copy's write failed. A doc can then exist at neither path until the next refresh, whose status reports the add. This follows the plan's "all removals and copies still run".
- Not guarded, outside the plan's Failures: reads, `glob` and `iterdir`. An unreadable file can raise out of `seed_toolset`.
- `TOOLSET_LOCAL_DIR` deferred to step 2. Old-path comments and docstrings are left for step 5's sweep.
- Grep for `agentic-design` over `scripts/`: 38 occurrences in 16 files, the same as before the change (Invariant holds).
- Python pack (step 1): `gating-python-changes` is red at gate 1 (ruff format/check on the 5 changed files). The repo has no ruff config and the errors read were pre-existing; the repo is off the python baseline (`scaffolding-python-projects --check` 4/14). Not a workflow gate here (no signed `step_gates`), so it is parked.

## Step 2 — 2026-11-19
- Developer hand-back: green after Mark's "yes" (21:25Z) to update step 1's frozen `test_write_failure_is_listed_failed_rest_refreshed`. It now expects the six docs plus `local/README.md` in `failed`, and the "rest still written" filter skips `wiki/best-practices/`. Re-frozen with the unfrozen and green reasons. check-freeze: PASS, 27 entries plus 164 from earlier changes.
- Orchestrator re-run: `test_global_toolset.py` → `80/80 passed`; `test_standalone.py` → `21/21 passed`.
- Changed: `scripts/_wiki_config.py` (`TOOLSET_LOCAL_DIR`), `scripts/_install_tooling.py` (`toolset_files()` lists `local/README.md`), new `seed/best-practices-local/README.md`, `tests/scripts/test_global_toolset.py` (13 new tests).
- Deviation from the plan: "README held open on Windows" is tested with a read-only file instead. A Python open handle does not block `copyfile`, so it cannot make the write fail.

## Step 3 — 2026-11-19 (hand-back 1, not green)
- Built: `taxonomy_for` appends `best-practices/local` before `sessions` for all nine pairs; `new-wiki.py` adds the missing-source guard before B1, the `folder_notes` row `best-practices/local`, and the README render at the end of B6.5. Tests in new `tests/scripts/test_local_folder.py`: 12/13 pass. Also green: global_toolset 80/80, standalone 21/21, tooling_state_seam 23/23, git_hooks_optin 17/17. check-freeze PASS (39 entries).
- Red: the plan's "lint reports no finding from `best-practices/`" premise is false. The lint names the README for: orphan (no `standalone:`), missing confidence, missing last_reviewed/review_after. A fresh scaffold's HOME.md and README.md already draw the confidence and lifecycle findings. Put to Mark on Discord with a recommendation (parity with HOME.md).
- Plan corrections: `.claude/wiki-config.json`'s `wiki_folders` holds the two answers, not the folder list; the folder list is Phase B's stdout JSON `wiki_folders` (tested). The `folder_notes` key is `best-practices/local`.
- Folder-guard findings, listed and not fixed:
  - `wiki-update.py` `validate_folder`: a bare `--folder best-practices` in a new wiki now passes Case 1 (its top segment exists on disk) and files into `wiki/best-practices/`; it was refused as ambiguous before.
  - `MERGED_TAXONOMY` lacks `best-practices/local`, and the `SCAFFOLD_TAXONOMY` comment is stale.
  - `wiki-map-compile.py:378` `CONTAINER_FOLDERS = {"research","project"}`: `local/` notes never reach `_MAP.md`.

## Step 3 — hand-back 2, green
- Mark's decision (21:44Z) applied. The README gains `confidence: high` and `standalone: "the folder's guide: nothing links to it by design"`, with no lifecycle dates. The lint test is now `test_lint_of_a_fresh_scaffold_draws_no_finding_on_the_local_readme_that_home_does_not` (the README's finding kinds must be a subset of HOME.md's). It was re-frozen and the old name retired.
- Orchestrator re-run: test_local_folder 13/13, test_global_toolset 80/80. The developer also reports standalone 21/21 and check-freeze PASS (40 entries plus 164 earlier).
- Limit: the parity test has not been seen failing on a README with an extra finding. Its bite rests on the earlier 12/13 red against the old README.
