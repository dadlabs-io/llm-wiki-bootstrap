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
