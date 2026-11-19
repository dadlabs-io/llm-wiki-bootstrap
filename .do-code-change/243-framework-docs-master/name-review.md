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
