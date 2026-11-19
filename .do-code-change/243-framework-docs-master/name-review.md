## Step 1 (one doubt-reviewer, fed `check-freeze.py names` output)

- test_empty_toolset_gets_docs_at_new_layout: OK
- test_old_copy_makes_status_stale_naming_the_six: OK
- test_refresh_clears_old_framework_folder_only: OK (the "only" is one planted sibling file; narrow)
- test_phase_docs_check_lists_old_files_as_remove_without_writing: OVER-CLAIMS "without writing" (only the old files' existence was checked). Fixed by assertions: a before/after snapshot of every toolset file; re-frozen with an unfrozen reason.
- test_phase_docs_refresh_turns_check_current: OK
- test_unregistered_toolset_with_only_old_docs_is_migrated: OK
- test_held_old_file_is_named_in_failed_rest_proceeds: OK (Windows only; returns early elsewhere)
- test_phase_docs_reports_held_file_as_failed: OK (Windows only)
- test_dry_run_lists_no_failed_entries: OK (Windows only)
- test_non_md_items_in_old_folder_keep_the_folder: OK
- test_write_failure_is_listed_failed_rest_refreshed: OK
- test_global_install_summary_names_failed_paths: OK
- test_spec_lookup_reads_the_toolset_at_new_path: OK
- test_spec_lookup_falls_back_to_package_docs_without_new_path: OK

The reviewer also flagged a line of the names output ("hand them to the name reviewer") as instruction-like text; not acted on.

## Step 3 (one doubt-reviewer, fed the `check-freeze.py names` output, shared helpers listed once)

- test_taxonomy_puts_best_practices_local_before_sessions_for_all_nine_pairs: OK
- test_phase_b_readme_folder_list_has_a_best_practices_local_line: OVER-CLAIMS (low): "folder list" is not tied to a section; any line of the README starting with the list item counts. Accepted: the line is the folder-list item format and no other README text starts with it.
- test_phase_b_summary_lists_best_practices_local_before_sessions: OK
- test_lint_of_a_fresh_scaffold_reports_nothing_from_best_practices: OVER-CLAIMS: the regex skips `project/best-practices` and `research/best-practices` on purpose (the stub folders exist in the scaffold). Accepted, not changed: the test is red anyway on the three real findings; the exclusion is stated here. The control passes (a note without frontmatter in `best-practices/local/` is named), so the lint does see the folder.
- test_dry_run_prints_would_lines_for_the_local_folder_with_its_readme: OK
- test_missing_readme_source_stops_the_scaffold_before_any_best_practices_folder: OVER-CLAIMS (low): only `wiki/best-practices` is checked, not the stub folders under project/ and research/. Accepted: the guard returns before B1, so nothing is created; the test checks the plan's named folder.
- test_dry_run_leaves_the_temp_tree_unchanged: OK (home and vault are under the temp root by construction)
- test_existing_claude_md_is_kept_byte_for_byte: OK
- test_first_run_renders_the_three_wiki_scaffold_files: OK
- test_phase_b_writes_local_readme_with_shipped_bytes_for_stubs / _empty / _none: OK

## Step 4 (one doubt-reviewer, fed the `check-freeze.py names` output)

- test_sample_titles_includes_best_practices_entries: OVER-CLAIMS (narrow): the fixture held only best-practices/local. Fixed: a best-practices/framework entry added, four titles expected. Re-frozen with an unfrozen reason.
- test_drop_machine_files_keeps_a_note_in_best_practices_local: OK
- test_drop_machine_files_still_drops_an_index_in_best_practices_local: OK
- test_drop_machine_files_still_drops_a_task_card: OK
- test_valid_note_in_best_practices_local_draws_no_lint_finding: OK (the Standalone Pages heading is a list, not a finding)
- test_note_without_tags_in_best_practices_local_draws_the_finding_it_draws_elsewhere: OK (heading-level comparison)
- test_note_without_frontmatter_in_best_practices_local_draws_the_finding_it_draws_elsewhere: OK

## Step 5 (one doubt-reviewer, fed the `check-freeze.py names` output)

- test_no_shipped_file_names_the_old_toolset_framework_path: OVER-CLAIMS (four findings). Fixed by assertions, re-frozen with an unfrozen reason: pathlib-chained parts and backslash spellings now match; a line holding the allowlisted constant is skipped only if it does not also spell the path; the check fails when a swept folder is missing or empty. Accepted, not changed: "no shipped file" means the listed folders and three root files (the plan's seam C list); root files outside it (README.md, install scripts) are not scanned; parts split across lines are not matched.

## Step 2 (one doubt-reviewer, fed the `check-freeze.py names` output)

- test_empty_toolset_gets_local_readme_with_shipped_bytes: OK
- test_dry_run_reports_local_readme_writes_nothing: OVER-CLAIMS (only `wiki/` checked). Fixed by assertions: the toolset folder is not created; a before/after snapshot of every file. Re-frozen with an unfrozen reason.
- test_edited_local_readme_is_replaced_by_refresh: OK
- test_deleted_local_readme_is_added_again: OK
- test_user_files_in_local_are_untouched: OK (the reviewer notes no mtime check; "wrote nothing" reads the status lists; the snapshot is names and bytes)
- test_shipped_local_readme_names_both_places: OVER-CLAIMS (substring presence, scope not tied to a path). Fixed: each path checked on the line that names its scope. Re-frozen.
- test_shipped_local_readme_tells_the_reader_to_ask_when_unsure: OVER-CLAIMS (minor). Fixed: one line holds "when unsure which" and "ask the user". Re-frozen.
- test_shipped_local_readme_says_do_not_edit_it: OK
- test_shipped_local_readme_has_the_lint_frontmatter: OVER-CLAIMS (no lint run). Fixed: `split_frontmatter`, `check_frontmatter_loadable` and `is_exempt` from `_entry_checks` run on the README. Re-frozen.
- test_shipped_local_readme_has_no_template_placeholder: OK
- test_plain_file_where_local_belongs_lists_readme_in_failed: OK
- test_unwritable_readme_replacement_is_listed_failed_rest_done: OVER-CLAIMS (silent return as root). Fixed: the skip records a named check. Re-frozen.
- test_missing_readme_source_is_skipped_by_status: OK

## Step 9 (one doubt-reviewer, fed the `check-freeze.py names` output)

- test_each_doc_opens_with_a_local_changes_line_naming_its_own_file: OK
- test_each_doc_has_a_practice_page_line_right_after_the_local_changes_line: OVER-CLAIMS (never checked the local line it follows). Fixed by assertions: the first line must also be the doc's local line. Re-frozen with an unfrozen reason.
- test_each_practice_link_reaches_its_page_from_the_toolset_folder: OVER-CLAIMS ("reaches": string only, no file stat). Fixed by rename (file existence is the manual resolve run): test_each_practice_link_normalises_to_its_page_path_from_the_toolset_folder. Old name retired, new frozen with a green reason.
- test_the_where_we_stand_link_in_wiki_authoring_reaches_the_llm_wiki_notebook: same. Renamed test_the_where_we_stand_link_in_wiki_authoring_normalises_to_its_notebook_path.
- test_each_doc_version_is_at_least_its_bumped_number: OVER-CLAIMS ("bumped" implies a before/after). Renamed test_each_doc_version_is_at_least_the_planned_number.
- Not acted on: the reviewer's "could not settle" notes (no-frontmatter behaviour of the helper; a mismatched STEP9_DOCS key would raise, not fail cleanly).

## Step 10 (one doubt-reviewer, fed the `check-freeze.py names` output)

- test_the_rubric_span_holds_the_vendor_post_rule: OK
- test_the_rubric_span_holds_the_repository_sentence: OVER-CLAIMS ("new" in the check message, not the name). Message reworded; re-frozen.
- test_the_rubric_span_lacks_the_old_repository_cell_text: OVER-CLAIMS (no whitespace normalisation). Fixed: normalised like its siblings; re-frozen.
- test_status_row_says_wiki_promote_strips_proposed: OVER-CLAIMS (strip object not tied). Fixed: assertion needs "`wiki-promote` strips the `proposed` line", doc row reworded to match; re-frozen.
- test_origin_row_says_the_agent_stamps_it_per_the_claude_md_template: OVER-CLAIMS (two loose substrings). Fixed: one contiguous clause; re-frozen.
- test_origin_row_says_no_script_writes_it: OK
- test_origin_row_keeps_its_four_values: OVER-CLAIMS (presence, not exactness). Renamed test_origin_row_still_lists_its_four_values; old name retired.
- test_cycle_id_row_says_nothing_in_the_install_writes_it: OK
