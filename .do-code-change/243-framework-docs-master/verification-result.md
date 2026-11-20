# Verification result — 243-framework-docs-master

Verified by the architect (verify step only), 2026-11-20. Fixed point `7b66e2a92fc2cfa3892050f143bd35fe0e6bd40d`; HEAD `2d962d4`; branch `features/243-framework-docs-master`; `git status --short` prints nothing (everything committed). Every command below was run fresh in this session, one per call, `uv run python <absolute path>`.

Layers, one line each (fixed shape):

- tests: PASS — the four named suites and every other `tests/scripts/` suite ran fresh; `test_fetch_repo.py` fails 11/27 at HEAD and identically (11/27, same checks) at the fixed point, so it predates the change (see layer 1)
- diff-contains-fix: PASS — every file the plan's steps name is in `git diff 7b66e2a… --stat`, nothing untracked; the notebook-repository steps are committed in project-notebooks
- findings-addressed: PASS — review-ledger.py exit 0, "review-ledger: met - no open blocking item, every verdict current (6 closed, 39 non-blocking), 3 round(s)"
- frozen-tests: PASS — check-freeze.py exit 0, "frozen-tests layer: PASS — 86 entries checked (+ 164 from earlier changes), all match or unfrozen with a reason (7 retired: deleted on purpose) (118 frozen green, each with its reason)"
- coverage: FAIL — two plan lines (step 3's `wiki_folders` and lint "no finding") are `none` as written; the plan was not rewritten after the rulings that changed them (rows 3c and 3d below); step 2's held-file case is Windows-only
- bar-unmoved: FAIL — floor-guard.py exit 1, "floor-guard: exit 1 - FAIL: a move lowers the bar (the violations are above); fix the code or route it through a tracked exception"
- in-scope: PASS — scope-guard.py exit 0, "scope-guard: exit 0 - PASS: every touched file is inside the declared scope"
- tests-bite: off — on demand by project setting (Mark, 2026-11-20), prove_tests_bite.py `--check` exit 4, "tests-bite layer: OFF - mutation testing is on demand in this project (.claude/do-code-change.json: decided by Mark, 2026-11-20); no pass runs with each change (exit 4)" / "VERDICT: OFF"

---

## 1. tests — PASS

Proving commands (fresh, run alone):

| Command | Result |
|---|---|
| `uv run python C:/github.com/llm-wiki-bootstrap/tests/scripts/test_global_toolset.py` | last line `91/91 passed` |
| `… test_local_folder.py` | last line `23/23 passed` |
| `… test_standalone.py` | last line `40/40 passed` |
| `… test_search_mode.py` | last line `82/82 passed` |

The four suites print no exit-code line, and the shell call was not allowed to append one; the pass is the `N/N passed` last line with no `FAIL` line in the output read.

Every other file in `tests/scripts/` (64 files) was run once by a scratch runner in the session scratchpad (`run_all.py`, outside the repository), which printed each file's exit code and last line. What I read for them is the exit code, the last line and any line starting `FAIL`; I did not read their full output.

- Exit 0 with a last line `N/N passed` (or `every check passed` / `N/N checks passed`): test_arxiv_abs 20, attach_pdfs 18, backlink_blocks 106, checker_hold 12, claims_corroborate 28, completeness 26, cycle_scope 330, dedup_content 15, dequeue_intake 10, design_drift 15, drive_files 21, feeds 51, fetch_only_reuse 11, fetch_pdf_columns 4, fetch_tweet 31, fetch_youtube_429 8, folder_readme 11, frontmatter_parser 21, git_hooks 18, git_hooks_dcc 6, git_hooks_harness 2, git_hooks_optin 17, gmail_api_errors 16, gmail_fetch 43, html_markdown 13, hub_tag 12, install_incomplete 25, install_manifest 21, left_undone_fixture (every check passed), link_gaps 21, lint_spec_values 11, list_add_intake (4/4 checks), living_body_checks 10, not_checked 23, promote_backlinks 14, promote_setting 14, qmd_launcher 5, quote_check 40, raw_parts 30, refresh_prunes 11, related_section 9, renamed_terms 18, self_source_url 4, session_start_no_wrapup 7, skill_runner 57, skill_suggestions (12/12 checks), source_identity 30, stale_pending 15, synthesis_scope 9, task_cards 72, tooling_env 20, tooling_state_seam 23, trajectory 9, transcribe 29, unknown_notebook 12, utf8_output 16, wiki_triage 67, wiki_upgrade 5.
- Exit 0 whose last line is not an `N/N passed` count (named, not counted as a pass count): `test_cycle_script_fixes.py` (last line `Wrote step JSON: …\drive-fetch.json`), `test_drive_access.py` (last line `Cached token missing required scopes; will re-authenticate with upgraded scope (browser will open).`), `test_fetch_page.py` (last line `2 page fetches already running — waiting for one`). Their exit code is 0; I did not read their per-check output.
- **Exit 1, predates this change:** `test_fetch_repo.py` — `11/27 passed`, `FAIL exit 0 [Cloning: …\demo-skills (current commit only)`, `FAIL one raw written`, `FAIL README.md is in, under its File heading, with its text`, and the rest. The same test extracted at the fixed point (`git archive 7b66e2a… scripts tests/scripts pyproject.toml` into the scratchpad, run there) printed `ERROR: git ls-tree failed: fatal: Not a valid object name HEAD` and the same 16 FAIL checks, `11/27 passed`, exit 1. `wiki-fetch-repo.py` is not among this change's files; the cause is the fixture repo's `HEAD` in this environment, not this change.

The skill suite (paid) was not re-run, as instructed. Recorded reports, both read: `tests/skills/.results/new-wiki/20261119-223534-red-green-7b66e2a92fc2cfa3892050f143bd35fe0e6bd40d/report.md` ($3.18; `local-readme-project-none` PASS on both models but "passes on the old copy too"; `local-readme-project-default-stubs` FAIL on the new copy on both, Phase B refused by the auto-mode classifier) and `tests/skills/.results/new-wiki/20261119-224512/report.md` ($0.27; `local-readme-project-default-stubs` PASS on Sonnet and Opus, 0 regressions). Step 17's red rests on the free old-vs-new script check, which Mark settled (DM 2026-11-20 15:28Z, "It meant what you recommended"; `checkpoints.md`). Not a pass of the plan's literal "red then green" line for `local-readme-project-none`; named here as a settled exception, with card #252 for the harness gap.

Hand mutation pass (implement-log.md, "Mutation pass (by hand)"): 92 mutants, 89 killed, 3 recorded equivalent. Extra evidence only; the tests-bite layer is `off` (layer 8).

## 2. diff-contains-fix — PASS

`git -C C:/github.com/llm-wiki-bootstrap diff 7b66e2a92fc2cfa3892050f143bd35fe0e6bd40d --stat -- . :!.do-code-change` lists 55 files, 2001 insertions, 103 deletions. `git status --short` prints nothing (nothing untracked, nothing uncommitted). Files each step names, each present in the stat:

- Step 1/2/3/4/4b: `scripts/_install_tooling.py`, `scripts/_wiki_config.py`, `scripts/new-wiki.py`, `scripts/wiki-update.py`, `scripts/wiki-qmd-query.py`, `scripts/wiki-map-compile.py`, `scripts/wiki-upgrade.py` (fix round 1; in `## Scope`), `seed/best-practices-local/README.md` (new, 21 lines), `agents/wiki-ingester/wiki-ingester-reading-list.json`, tests `test_global_toolset.py`, `test_local_folder.py` (new, 470 lines), `test_search_mode.py`, `test_standalone.py`, `test_link_gaps.py`.
- Step 5/9/10/11/12: the six `framework-docs/*.md`, `CLAUDE.md`, `INSTALL-INVENTORY.md`, `V2_ROADMAP.md`, `CHANGELOG.md`, `seed/global-toolset-README.md`, `seed/how-to/_FRAMEWORK_MANAGED.md`, `wiki-seed/{install,obsidian,user-guide}.md`, `templates/{CLAUDE.md.tmpl,feeds.md.tmpl}`, the skill files (17 under `skills/`).
- Step 17: `tests/skills/new-wiki/{cases.json,check.py,baseline-opus.json,baseline-sonnet.json}`, `tests/skills/PENDING.md`.
- Steps 6 to 8 and 13 to 16 (notebooks): not in this repository's diff by design. `git -C C:/github.com/project-notebooks status --short` over `notebooks/agentic-design/wiki/research/wiki`, `notebooks/llm-wiki-bootstrap/wiki/project/decisions`, `notebooks/agentic-design/wiki/project/best-practices` and `notebooks/agentic-design/_INDEX.md` prints nothing, and `git log --oneline` over the first two paths lists the step commits (`ecdbc15e` step 6 hub and pages, `86990bc3` step 7, `9d270e22` step 8, `6a2c83f1` step 14, `f69c201d` step 15, `80f14173` step 16, `0219783e` federation lesson, `04c30a33` wrap-up). Not re-read by me beyond the log; step 13's link repoint (80 files in agentic-design) was not re-listed.

The Invariant "nothing in `scripts/` names agentic-design": `git grep -c agentic-design` over `scripts/` gives the same 16 files with the same counts at `7b66e2a…` and at `HEAD` (no new hit).

## 3. findings-addressed — PASS

`uv run python C:/Users/mark/.claude/workflows/do-code-change/scripts/review-ledger.py query --diff-base 7b66e2a92fc2cfa3892050f143bd35fe0e6bd40d --cap 3 --ledger …/review-ledger.json`:

```
review-ledger: met - no open blocking item, every verdict current (6 closed, 39 non-blocking), 3 round(s)
review-ledger: exit 0 - met
```

The six closed blocking items, each site re-read once:

- CHANGELOG 2026-11-19 entry: line 16 now says a failed toolset write lists `FAILED <path>: <reason>`, finishes the rest and exits 1 on `--phase docs`, `--mode tooling` and `wiki-upgrade.py`, and the scaffold's `--install-global-if-missing` stops before the project. Matches the code sites below.
- standards-2 (`test_global_toolset.py:459`, a skipped case recorded a PASS): `_skip()` is defined at `tests/scripts/test_global_toolset.py:40` and the root-user case at `:467-471` calls it and returns, no `check(..., True)`.
- standards-3 (`PRACTICE_PAGE_ROOT` unused constant): `grep PRACTICE_PAGE_ROOT tests/scripts` finds nothing.
- spec-1 (step 17 red-then-green for `local-readme-project-none`): not a code change; settled by Mark's own word, `checkpoints.md` entry "spec-1 settled" (DM 15:28Z). Closed `addressed` on that record, not by a change at a site.
- standards-1 / risk-1 (a global refresh with a failed toolset write exited 0): `scripts/new-wiki.py:514` (`phase_tooling`), `:919` (`phase_b`), `scripts/wiki-upgrade.py:73-76` each test `summary["toolset"]["failed"]` and return 1; tests `test_wiki_upgrade_exits_1_when_a_toolset_write_failed`, `test_new_wiki_tooling_mode_exits_1_when_a_toolset_write_failed` and `test_scaffold_stops_when_the_global_install_it_runs_failed_a_toolset_write` all PASS in the fresh run.
- risk-5 (`new-wiki.py:925`, a re-run after a failed toolset write warns and proceeds): the site changed in fix round 2 to name "toolset docs" and the refresh command (`new-wiki.py:927-933`) and `test_scaffold_warning_names_a_stale_toolset` PASSES. The finding asked for "stopping or refreshing"; the fix names the repair and still proceeds (implement-log fix round 2: "No refresh added"). Review round 3 re-verified it and raised no blocking item. Recorded as addressed by the ledger; named here because the change is the message, not a stop.

The 39 non-blocking items (suggestions and nits, six from round 3) are not part of this layer and stay open.

## 4. frozen-tests — PASS

`uv run python C:/Users/mark/.claude/skills/verifying-before-done/scripts/check-freeze.py C:/github.com/llm-wiki-bootstrap/.do-code-change/243-framework-docs-master/test-freeze.json` (it reads the project record `.do-code-change/test-freeze.json` beside it):

```
frozen-tests layer: PASS — 86 entries checked (+ 164 from earlier changes), all match or unfrozen with a reason (7 retired: deleted on purpose) (118 frozen green, each with its reason)
check-freeze: exit 0 - PASS: every frozen test matches, or changed with a reason
```

Green-frozen entries of this change (41 of the 118; each reason as the script prints it, shortened):

- `test_global_toolset.py`: `test_write_failure_is_listed_failed_rest_refreshed` (expectation updated for step 2, Mark's yes 21:25Z), `test_install_summary_counts_the_failed_operations` (mutant M53), `test_failed_reason_reads_error_class_colon_message` (M29, M30), `test_unremovable_old_folder_is_listed_failed_not_raised` (M47), `test_phase_docs_failure_line_is_a_warning_with_the_count` (M64, M65), `test_held_old_file_is_named_in_failed_rest_proceeds`, `test_phase_docs_reports_held_file_as_failed`, `test_dry_run_lists_no_failed_entries`, `test_unwritable_readme_replacement_is_listed_failed_rest_done` (only the skip branch changed), `test_wiki_upgrade_exits_1_when_a_skill_was_refused` and `test_scaffold_warning_names_a_stale_toolset` (watched red before the fix this round; the red command cannot be re-run).
- `test_local_folder.py`: `test_dry_run_leaves_the_temp_tree_unchanged`, `test_existing_claude_md_is_kept_byte_for_byte`, `test_first_run_renders_the_three_wiki_scaffold_files` (invariants that held before, bite by transient mutation), `test_lint_of_a_fresh_scaffold_draws_no_finding_on_the_local_readme_that_home_does_not` (red shown 12/13 before the README gained confidence and standalone), `test_valid_note_in_best_practices_local_draws_no_lint_finding`, `test_note_without_tags_…`, `test_note_without_frontmatter_…` (lint already treats `local/` notes as entries; bite on a scratch copy), the four map tests (`…compiles_a_map_with_no_best_practices_section`, `test_existing_map_sections_do_not_change_…`, `test_the_shipped_local_readme_is_treated_in_the_map_…`, `test_a_best_practices_local_folder_with_no_titled_note_…`), `test_phase_b_readme_local_line_carries_its_note` (M73-M75).
- `test_search_mode.py`: `test_drop_machine_files_keeps_a_note_in_best_practices_local`, `…_still_drops_an_index_in_best_practices_local`, `…_still_drops_a_task_card` (behaviour already existed; bite by transient mutation), `test_sample_titles_includes_best_practices_entries` (strengthened after its red).
- `test_standalone.py`: `test_no_shipped_file_names_the_old_toolset_framework_path`, the five step-9 tests (renames of tests frozen red), `test_the_rubric_span_lacks_the_old_repository_cell_text`, `test_origin_row_says_the_agent_stamps_it_per_the_claude_md_template`, `test_the_rubric_span_holds_the_repository_sentence`, `test_origin_row_still_lists_its_four_values`, `test_status_row_says_wiki_promote_strips_proposed`, `test_rendered_template_lacks_the_old_toolset_framework_path`, `test_precedence_entry_says_to_read_the_local_file_after_the_framework_doc`, `test_precedence_entry_points_to_the_local_changes_line`, `test_precedence_entry_does_not_copy_the_local_changes_sentence`.

The other 77 green-frozen entries belong to earlier changes' project record (git-hooks, cycle-scope, backlink-block tests); the script prints each with its reason, and none moved.

## 5. coverage — FAIL

Rows are read from the named tests' names and the fresh run's check lines (each test passed), not from the suite being green alone. `existing` = a named test asserts it today.

| # | Plan step, rule (expected or failure) | Pinning test | Status |
|---|---|---|---|
| 1a | 1: empty toolset gets six docs at `wiki/best-practices/framework/`, status current, nothing under `wiki/project/` | `test_empty_toolset_gets_docs_at_new_layout` (3 checks) | existing |
| 1b | 1: old copy makes status stale, `remove` names the six | `test_old_copy_makes_status_stale_naming_the_six` | existing |
| 1c | 1: refresh deletes the six and the emptied folder, `project/best-practices/` untouched, current after | `test_refresh_clears_old_framework_folder_only` | existing |
| 1d | 1: `--phase docs --check` exits 1 naming REMOVE, writes nothing; plain `--phase docs` clears it | `test_phase_docs_check_lists_old_files_as_remove_without_writing`, `test_phase_docs_refresh_turns_check_current` | existing |
| 1e | 1: spec lookup reads the new path, falls back to `framework-docs/` | `test_spec_lookup_reads_the_toolset_at_new_path`, `test_spec_lookup_falls_back_to_package_docs_without_new_path` | existing |
| 1f | 1 Failure: held old file named in `failed`, rest proceeds; `phase_docs` exits 1 with `FAILED <path>: <reason>`; dry run lists none | `test_held_old_file_is_named_in_failed_rest_proceeds`, `test_phase_docs_reports_held_file_as_failed`, `test_dry_run_lists_no_failed_entries` | existing; the held-file case is Windows-only (`_skip` on other platforms), so on Windows it ran and passed |
| 1g | 1 Failure: non-`.md` item or subfolder keeps the folder, no error | `test_non_md_items_in_old_folder_keep_the_folder` | existing |
| 1h | 1 Failure: docs only at the old path, no registry entry: new added, old removed | `test_unregistered_toolset_with_only_old_docs_is_migrated` | existing |
| 1i | 1 Invariant: replace, remove, other-pack, line-ending checks green | the pre-existing checks in `test_global_toolset.py` ("the hand edit replaced", "the retired page removed", "another pack's folder untouched", "current again", "a copy differing only in line endings … is current") | existing |
| 2a | 2: README created with shipped bytes; add before, current after | `test_empty_toolset_gets_local_readme_with_shipped_bytes` | existing |
| 2b | 2: edited or older README is replaced; `--check` 1 then 0 | `test_edited_local_readme_is_replaced_by_refresh` | existing |
| 2c | 2: deleted README is added again | `test_deleted_local_readme_is_added_again` | existing |
| 2d | 2: user files and subfolders untouched, never in `remove`, status stays current | `test_user_files_in_local_are_untouched` | existing |
| 2e | 2: dry run reports the README, writes nothing | `test_dry_run_reports_local_readme_writes_nothing` | existing |
| 2f | 2: shipped README names both places, the "ask" sentence | `test_shipped_local_readme_names_both_places`, `test_shipped_local_readme_tells_the_reader_to_ask_when_unsure`, `test_shipped_local_readme_says_do_not_edit_it` | existing |
| 2g | 2 Failure: plain file where `local` belongs: README in `failed`, rest refreshed, exit 1 | `test_plain_file_where_local_belongs_lists_readme_in_failed` | existing |
| 2h | 2 Failure: README held when replaced: same `failed` entry, rest done (tested as a read-only file, a recorded deviation: an open handle does not block `copyfile`) | `test_unwritable_readme_replacement_is_listed_failed_rest_done` | existing; skipped when running as root |
| 2i | 2 Failure: README source missing: status skips it, no error | `test_missing_readme_source_is_skipped_by_status` | existing |
| 3a | 3: `taxonomy_for` gives `best-practices/local` before `sessions` for nine pairs | `test_taxonomy_puts_best_practices_local_before_sessions_for_all_nine_pairs` | existing |
| 3b | 3: Phase B creates the README with shipped bytes for stubs, empty and none; `best-practices` in the folder list | `test_phase_b_writes_local_readme_with_shipped_bytes_for_stubs`/`_empty`/`_none`, `test_phase_b_readme_folder_list_has_a_best_practices_local_line`, `test_phase_b_summary_lists_best_practices_local_before_sessions` | existing |
| 3c | 3: "`best-practices` is in … `.claude/wiki-config.json`'s `wiki_folders`" (plan line 189) | none: `wiki_folders` there keeps the two interview answers; the folder list is only in Phase B's stdout JSON (tested in 3b) | **none** — the orchestrator ruled the plan line the error (checkpoints.md, review round 1 spec-6), but plan.md line 189 still reads as written |
| 3d | 3: "the mechanical lint over the freshly scaffolded wiki reports no finding from `best-practices/`" (plan line 190) | `test_lint_of_a_fresh_scaffold_draws_no_finding_on_the_local_readme_that_home_does_not` pins a weaker claim (parity with HOME.md); the plan's own premise was false (implement-log step 3), Mark chose parity at 21:44Z | **none** against the plan line as written; the weaker form is `existing` |
| 3e | 3: `--dry-run` prints `WOULD …`, writes nothing | `test_dry_run_prints_would_lines_for_the_local_folder_with_its_readme`, `test_dry_run_leaves_the_temp_tree_unchanged` | existing |
| 3f | 3 Failure: README source missing stops the scaffold, no `best-practices/` folder | `test_missing_readme_source_stops_the_scaffold_before_any_best_practices_folder` | existing |
| 3g | 3 Failure/Invariant: existing CLAUDE.md kept; `_MAP`, README, HOME rendered on a first run | `test_existing_claude_md_is_kept_byte_for_byte`, `test_first_run_renders_the_three_wiki_scaffold_files` | existing |
| 3h | 3 Failure: folder guard (`MERGED_TAXONOMY`) must accept `best-practices/local` | `test_filing_into_best_practices_local_is_accepted_in_a_wiki_that_lacks_the_folder` | existing |
| 4a | 4: `sample_titles` returns titles from research, project, best-practices | `test_sample_titles_includes_best_practices_entries` | existing |
| 4b | 4: `drop_machine_files` keeps the note, drops `_INDEX.md` and a task card | `test_drop_machine_files_keeps_a_note_in_best_practices_local`, `…_still_drops_an_index_…`, `…_still_drops_a_task_card` | existing |
| 4c | 4: lint treats a `local/` note as an entry (valid note: none; no tags / no frontmatter: the usual finding; skip list unchanged) | `test_valid_note_in_best_practices_local_draws_no_lint_finding`, `test_note_without_tags_…`, `test_note_without_frontmatter_…` | existing |
| 4d | 4 manual: qmd collection pattern covers `best-practices/`; one keyword search finds a `local/` note | `manual: step 4`, evidence in implement-log.md "Step 4 manual evidence" (all 10 collections `**/*.md`; temp-index search found `best-practices/local/my-notes.md`; index removed) | manual, evidence read, not re-run |
| 4e | 4b: `_MAP.md` lists a `best-practices/local/` note; research and project sections unchanged; no-folder wiki unchanged | `test_map_lists_a_note_in_best_practices_local`, `test_existing_map_sections_do_not_change_…`, `test_wiki_with_no_best_practices_folder_compiles_…`, `test_a_best_practices_local_folder_with_no_titled_note_…`, `test_the_shipped_local_readme_is_treated_in_the_map_…` | existing |
| 5 | 5: no shipped file names the old path, spelled out or built from parts | `test_no_shipped_file_names_the_old_toolset_framework_path`; the install frontmatter gate over 11 changed skills (implement-log step 5, "11/11 parse") | existing; the frontmatter gate is a quoted hand-back result, not re-run |
| 9a | 9: each doc's Local changes line names its own file; Practice page line follows (rerank: `none`) | `test_each_doc_opens_with_a_local_changes_line_naming_its_own_file`, `test_each_doc_has_a_practice_page_line_right_after_the_local_changes_line` | existing |
| 9b | 9: each link normalises to its page from the toolset folder; wiki-authoring where-we-stand link at the new depth | `test_each_practice_link_normalises_to_its_page_path_from_the_toolset_folder`, `test_the_where_we_stand_link_in_wiki_authoring_normalises_to_its_notebook_path` | existing |
| 9c | 9: versions at least 10, 4, 4, 17, 20, 3; the two raised floors | `test_each_doc_version_is_at_least_the_planned_number`, the two floor checks (`cycle-step-return-format framework-version bumped to 10 or later`, `wiki-frontmatter-best-practices framework-version bumped to 20 or later`) | existing |
| 9d | 9 manual: resolve run over the six links and a temp-wiki lint | implement-log "Step 9 — manual evidence" (`dead: 0`; lint exit 0, one pre-existing broken example link) | manual, evidence read, not re-run |
| 10 | 10: both tier rules and the repository sentence inside the `tier_rubric_text()` span, old cell text gone; `status`, `origin`, `cycle_id` rows | `test_the_rubric_span_holds_the_vendor_post_rule`, `…_holds_the_repository_sentence`, `…_lacks_the_old_repository_cell_text`, `test_status_row_says_wiki_promote_strips_proposed`, `test_origin_row_says_the_agent_stamps_it_…`, `…_says_no_script_writes_it`, `…_still_lists_its_four_values`, `test_cycle_id_row_says_nothing_in_the_install_writes_it` | existing |
| 12 | 12: template precedence entry names `wiki/best-practices/local/<doc name>`, read after the doc, points to the Local changes line, no old path, no copied sentence | the five `test_precedence_entry_*` and `test_rendered_template_lacks_the_old_toolset_framework_path` tests | existing |
| 6-8, 11, 13-16 | notebook and doc steps | `manual:` lines in Testing Decisions; evidence is in implement-log.md (the plan says checkpoints.md; the implement-log says the evidence lives there; checkpoints.md line 84 points to it) | manual, evidence read, not re-run |
| 17 | 17: new cases red then green on both models; PENDING rows | `manual: step 17`; the two reports above; `tests/skills/PENDING.md` (3 rows added, `git diff --stat`) | manual, with the settled exception (see layer 1): the none case did not show red in the suite |

Layer verdict: FAIL, on rows 3c and 3d. Both are plan lines that the run's own rulings made untrue and that the plan was never rewritten to match (the workflow asks a round's rulings be applied in place, not left beside an unchanged body). Neither is a missing behaviour: the behaviour the rulings chose is pinned (3b's folder-list check, 3d's parity form). Route: the orchestrator rewrites plan.md lines 189 and 190 to the ruled wording (an edit of the plan, no code); if the requester prefers, the two rows are accepted as a named FAIL with the approval recorded beside them. The layer is not passed here.

## 6. bar-unmoved — FAIL

`uv run python C:/Users/mark/.claude/skills/constraint-driven-development/scripts/floor-guard.py --base 7b66e2a92fc2cfa3892050f143bd35fe0e6bd40d`, exit 1:

```
floor-guard: 4 floor violation(s):
  [silenced-checker] tests/scripts/test_global_toolset.py: except Exception as e:  # noqa: BLE001 - a crash is a failed check named after the test, not the end of the file
  [silenced-checker] tests/scripts/test_local_folder.py: import _wiki_config as wc  # noqa: E402
  [silenced-checker] tests/scripts/test_local_folder.py: except Exception as e:  # noqa: BLE001 - a crash is a failed check named after the test, not the end of the file
  [silenced-checker] tests/scripts/test_search_mode.py: except Exception as e:  # noqa: BLE001 - a crash is a failed check named after the test, not the end of the file

Each is a move that lowers the bar. Fix the code, or route it through a tracked exception (a test file deleted on its owner's word: `floor-guard.py approve-deletion`).
floor-guard: exit 1 - FAIL: a move lowers the bar (the violations are above); fix the code or route it through a tracked exception
```

No `floor-approvals.json` exists in the artifact directory, so no approval is on record. Context only, not a reason to pass: `git grep noqa` at the fixed point finds `# noqa: E402` and two `# noqa: E731` in `test_search_mode.py` only; all four flagged lines are new in this change (the `E402` pattern in `test_local_folder.py` copies the fixed point's own `test_search_mode.py:63`). Route: implement (remove the four suppressions or restructure so none is needed), or the requester approves them and an approvals record is written; the report does not decide.

## 7. in-scope — PASS

`uv run python C:/Users/mark/.claude/skills/verifying-before-done/scripts/scope-guard.py check --artifact-dir C:/github.com/llm-wiki-bootstrap/.do-code-change/243-framework-docs-master`:

```
scope-guard: PASS - 55 touched file(s), all inside the declared scope (…)
scope-guard: exit 0 - PASS: every touched file is inside the declared scope
```

Warnings the script printed (exit unchanged): 20 declared globs match no file in this repository. They are the notebook paths (`notebooks/…`, not in this repository) and misread prose bullets, `No` (from "No other suite is touched…"), `The` and `checkpoints.md` (from the last Scope bullet). The bare `No` and `The` read as globs match no real file and widen nothing. The guard checks this repository only: the notebook edits in project-notebooks were not scope-checked by it (the notebook repository is clean and committed, layer 2).

## 8. tests-bite — off

`uv run python C:/Users/mark/.claude/skills/proving-python-tests-bite/scripts/prove_tests_bite.py --check --base 7b66e2a92fc2cfa3892050f143bd35fe0e6bd40d`, exit 4:

```
tests-bite layer: OFF - mutation testing is on demand in this project (.claude/do-code-change.json: decided by Mark, 2026-11-20); no pass runs with each change (exit 4)
VERDICT: OFF
```

A recorded standing decision, not a FAIL (Mark, `checkpoints.md`, 04:29Z). The hand mutation pass in implement-log.md (92 mutants, 89 killed, 3 equivalent; four of its new tests are frozen) is kept as extra evidence and is not this layer's verdict.

---

Not checked or only partly read, stated plainly: the paid skill suite was not re-run (instructed); the notebooks' resolve runs and lint runs (steps 6 to 8, 13 to 16) were not repeated, only their recorded evidence and git state read; `test_cycle_script_fixes`, `test_drive_access` and `test_fetch_page` were read by exit code and last line only, and `test_drive_access` printed that a browser re-authentication would open (it exited 0 in 1 second, so it did not wait for one); the sweep of the other 59 suites was read by exit code, last line and FAIL lines.

VERDICT: FAIL — coverage, bar-unmoved
