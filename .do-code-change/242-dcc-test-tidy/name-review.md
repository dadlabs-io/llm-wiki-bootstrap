
## Name review — 2026-11-13

One doubt-reviewer over all 23 checks (check-freeze.py names output only). OVER-CLAIMS: test_install_writes_the_hand_over_hooks ("hand-over" unchecked), test_private_word_blocked_in_any_case (one case only), test_repo_commit_msg_hook_can_refuse (exit code only, no control). Notes: test_no_verify_commits_anyway, test_committed_word_is_not_rechecked (setup outcomes unasserted), test_remove_unsets_the_hooks_path (--remove exit unasserted). All six strengthened (assertions only added) and re-frozen with --unfrozen-reason "name review round 1: ..."; suite 18/18. The rest PASS.
