# Name review — 240-unfinished-run-check

Steps 1, 2 and fix-1 (10 tests), one fresh doubt-reviewer (orchestrator, 2026-11-13) over `check-freeze.py names`' output, contract "each test's name claims nothing its assertions do not check":

- 9 OK: unfinished_names_runs_without_report, unfinished_none_case, unfinished_without_a_reports_folder, mark_interrupted_closes_a_scratchpad_run, mark_interrupted_puts_the_reason_inside_the_log_section, mark_interrupted_writes_a_scratchpad_for_a_run_with_none, mark_interrupted_adds_the_log_heading_when_missing, mark_interrupted_refuses_an_unknown_run, mark_interrupted_needs_a_reason.
- OVER-CLAIM: mark_interrupted_closes_a_scratchpad_with_no_status_line — no assertion read the scratchpad. Fixed by the reviewer's second option: an assertion that the scratchpad gains `**Status**: interrupted` and the reason under the Decisions log; name kept; re-frozen with that reason. Suite 79/79.
