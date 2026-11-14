# name-review — 240-backlink-block-check

## Steps 1-2 (one doubt-reviewer over all 40 frozen tests in tests/scripts/test_backlink_blocks.py; the full `check-freeze.py names` output was 96 KB of repeated helpers, so the reviewer was pointed at the test file instead)

Verdict: 33 of 40 names fit (the seven below were flagged; one more had a label fixed).

- over-claim: `test_report_section_names_each_out_of_step_page_with_its_pages` checked only that four paths occur in the section. Strengthened (the section must read "`research/b.md` — extra `research/d.md`" and "`research/c.md` — missing `research/a.md`"), re-frozen with an unfrozen reason.
- label over-claim: `test_unclosed_block_page_stays_listed_after_one_rebuild`'s check label claimed a property no assertion reads. Label trimmed, re-frozen with an unfrozen reason.
- over-claim, left as is (six): `test_link_target_with_whitespace_does_not_count`, `test_link_to_an_index_page_does_not_count`, `test_link_to_a_sessions_page_does_not_count`, `test_link_to_a_task_card_does_not_count`, `test_link_to_a_dot_file_does_not_count`, `test_link_to_an_inbox_page_does_not_count`. The reviewer: each checks that the target page is absent from the report, which holds whether the link is ignored or the target is excluded as an entry. Ruling: the plan words these expectations as "a target outside the entry set does not count", whose only observable is the target absent from the report, and each was red against the first implementation (the target was reported); each check's label says "is no entry". A rename needs a plan amendment (tdd-implementation step 5b: the plan fixes the wording), so it is named for the plan, not made here.
- could not settle (reviewer): `test_matching_block_is_not_reported` would pass under a lint that never reads blocks; the other block tests catch that.
