# Verification result — 240-backlink-block-check (task #240, lesson #11)

Fixed point `f9b3aa200a86ce60716ce42dae48b6cff1022f88`; HEAD `a2cea87` on `main`; `git status --short` prints nothing (every step is committed, nothing untracked). Every command below was run fresh in this session, each alone; nothing was committed, fixed or installed.

## Layers

tests: PASS — fresh runs of the five proving files, each ending on its all-passed line: `test_backlink_blocks.py` "99/99 passed", `test_promote_backlinks.py` "14/14 passed", `test_cycle_script_fixes.py` "44/44 passed", `test_lint_spec_values.py` "11/11 passed", `test_hub_tag.py` "12/12 passed". The plan names no other script test. The wiki-cycle skill suite (three cases, Sonnet and Opus) was not re-run here: it bills headless models, and the red-then-green run (`20261114-162044`, recorded in `checkpoints.md`) is a recorded claim, not a fresh result; the baselines do hold all three case ids (3 matches in each of `baseline-sonnet.json` and `baseline-opus.json`).
diff-contains-fix: PASS — `git diff f9b3aa2 --stat` (`.do-code-change/` left out) lists every file `plan.md`'s Scope names: `scripts/wiki-lint-mechanical.py` (143), `scripts/wiki-reciprocate-backlinks.py` (116), `scripts/wiki-promote.py` (4), `tests/scripts/test_backlink_blocks.py` (764 new), `skills/wiki-cycle/` (SKILL.md, reference.md, wiki-seed page), `skills/wiki-report/` (SKILL.md, wiki-seed page), `skills/wiki-lint/` (SKILL.md, wiki-seed page), `tests/skills/wiki-cycle/` (cases.json, check.py, both baselines, four fixture scratchpads), `tests/skills/PENDING.md`, `framework-docs/cycle-step-return-format.md`, `CHANGELOG.md`, `INSTALL-INVENTORY.md`; 23 files, 1311 insertions, 78 deletions; nothing untracked, on `main` as `checkpoints.md` records.
findings-addressed: PASS — `review-ledger.py query --diff-base f9b3aa2 --cap 10`: "review-ledger: met - no open blocking item, every verdict current (17 closed, 50 non-blocking), 6 round(s)" / "review-ledger: exit 0 - met". The five verdicts the orchestrator set without a round are re-confirmed below against the current code (all five hold). The round-6 important finding (standards-34) holds: the file has no literal U+2028; line 625 reads `for sep in ("\x0c", "\u2028")`.
frozen-tests: PASS — check-freeze.py exit 0, "frozen-tests layer: PASS — 71 entries checked (+ 47 from earlier changes), all match or unfrozen with a reason (2 retired: deleted on purpose) (61 frozen green, each with its reason)"; last line "check-freeze: exit 0 - PASS: every frozen test matches, or changed with a reason". The 61 green-frozen reasons were printed by the script (23 for this change's `test_backlink_blocks.py`, each naming the mutant that kills it or why it could not fail first).
coverage: FAIL — two Step 3 done criteria have no test and no `manual: step 3` line in `## Testing Decisions` (only step 4 has one); see the map below, rows 3c and 3d. I checked both by Grep, which is a reading, not a test. The fix is a plan amendment (a `manual: step 3` line naming the Grep and the template read) or a test; routing is the caller's.
bar-unmoved: FAIL — floor-guard.py exit 1, "floor-guard: 2 floor violation(s): [unfinished-work] INSTALL-INVENTORY.md: | `wiki-lint-mechanical.py` | Deterministic lint: broken links, orphans, frontmatter loadability, body checks (warn-only … [silenced-checker] tests/scripts/test_backlink_blocks.py: from _fake_qmd import fake_qmd_env  # noqa: E402"; last line "floor-guard: exit 1 - FAIL: a move lowers the bar (the violations are above); fix the code or route it through a tracked exception". Suspected tool false positives, named beside the layer and not its verdict: (1) the INSTALL-INVENTORY row already held the words `not yet built` / `TODO:` (the stale-pending description) and the change appended to that row, so the whole line reads as added work; (2) the `# noqa: E402` on the `_fake_qmd` import is the repo's own idiom for a test that edits `sys.path` first (the same suppression sits on `test_cycle_script_fixes.py:29` and `test_design_drift.py:24`). No approval is recorded for either; the requester decides (approve, or reword the row and drop the noqa).
in-scope: PASS — scope-guard.py exit 0, "scope-guard: PASS - 23 touched file(s), all inside the declared scope"; last line "scope-guard: exit 0 - PASS: every touched file is inside the declared scope".
tests-bite: FAIL (named; approved exception, Mark 2026-11-14, requirements Decision 4: "prove_tests_bite.py's COULD-NOT-RUN on `scripts/` accepted once more as a named FAIL with a hand mutation pass as evidence") — prove_tests_bite.py --check exit 2, "tests-bite layer: COULD-NOT-RUN against f9b3aa200a86ce60716ce42dae48b6cff1022f88 (0 changed source file(s)); report .artifacts/python-mutation.json" / "VERDICT: COULD-NOT-RUN". Fresh evidence: the hand mutation pass re-run on the current scripts, 157 mutants, 135 killed, 22 survived, 7 of the survivors real gaps (section below); result saved as `hand-mutation-bl-result-verify.json`.

## Five verdicts re-confirmed against the current code

Each frozen test was shown passing in the fresh 99/99 run above, and, because a pass proves little, each was also shown failing on a planted mutant of the current script (scratch copies of `scripts/` and `tests/scripts/`, only that test run; the repo untouched).

| Verdict | What it says | Pinning frozen test (passing) | Planted mutant, result on the mutant |
|---|---|---|---|
| spec-17 | an indented block is still found by the rebuild | `test_rebuild_finds_a_block_with_indented_markers` (and the lint's `test_lint_reads_a_block_whose_markers_are_indented`) | rebuild's `START_LINE_RE` loses its `[ \t]*` prefix: 0/2 passed ("b holds one START line", "the lint lists nothing" fail) |
| spec-22 | an in-fence page gets one block, then is left alone | `test_rebuild_appends_one_block_to_an_unclosed_fence_page_over_three_rebuilds` | `if unclosed: return True` in `has_unusable_start` turned to `if False:`: 3/5 passed ("the second rebuild changes nothing", "the third rebuild changes nothing" fail) |
| standards-27 | same page shape as spec-22 | the same test | the same mutant |
| spec-23 | END then a stray START is left open; the rebuild leaves it | `test_rebuild_leaves_a_page_with_an_end_then_a_stray_start_untouched_over_two_rebuilds` | `max(open_starts - 1, 0)` turned to `open_starts - 1` in the rebuild's `has_unusable_start`: 1/4 passed (byte-identical after one and two rebuilds, and the lint row, fail); the same edit in the lint's `backlink_start_unclosed`: 3/4 passed (the lint row fails) |
| standards-28 | the START left open after pairing | the same test | the same two mutants |

None of the five fails, so none is reopened.

## Coverage map (plan step done criteria; each `Expected:` and `Failures:` bullet, each `## Invariants` entry)

| # | Criterion | Pinning test | Status |
|---|---|---|---|
| 1a | block listing a page that does not link here: reported, that page as extra | `test_block_listing_a_page_that_does_not_link_here_is_reported_as_extra` | existing |
| 1b | linker left out / page with no block: reported as missing | `test_linker_left_out_of_a_block_is_reported_as_missing`, `test_linked_page_with_no_block_is_reported_as_missing` | existing |
| 1c | matching block not reported | `test_matching_block_is_not_reported` | existing |
| 1d | summary line, JSON key and array carry counts and pages | `test_summary_line_reads_pages_then_extra_then_missing_counts`, `test_json_summary_carries_the_out_of_step_page_count`, `test_json_array_rows_have_file_extra_missing_unclosed_by_file`, `test_report_section_names_each_out_of_step_page_with_its_pages` | existing |
| 1e | section link, bracketed text, empty text count | `test_link_to_a_section_of_a_page_counts_as_a_link`, `test_link_text_holding_brackets_counts_as_a_link`, `test_link_with_empty_text_counts_as_a_link` | existing |
| 1f | no count inside inline code, a ``` fence, a ~~~ fence, after an unclosed fence | `test_link_inside_inline_code_does_not_count`, `test_link_inside_a_backtick_fence_does_not_count`, `test_link_inside_a_tilde_fence_does_not_count`, `test_link_after_an_unclosed_fence_does_not_count` | existing |
| 1g | no count: own block, self-link, target with whitespace, target outside the entry set (`_INDEX.md`, `sessions/`, task card, dot-file, `_inbox/`) | `test_a_pages_own_block_does_not_make_it_a_linker`, `test_self_link_does_not_count`, `test_link_target_with_whitespace_does_not_count`, `test_link_to_an_index_page_does_not_count`, `test_link_to_a_sessions_page_does_not_count`, `test_link_from_a_sessions_page_does_not_count`, `test_link_to_a_task_card_does_not_count`, `test_link_to_a_dot_file_does_not_count`, `test_link_to_an_inbox_page_does_not_count` | existing (six assert absence of the target from the report, which also holds when the target is no entry: the ruling in `name-review.md`) |
| 1h | Failures: a START with no END is "block not closed", never a crash | `test_block_with_a_start_marker_lacking_its_end_is_marked_unclosed` (JSON), `..._is_named_in_the_report` (see survivor B: its report assertion is vacuous for the row text) | existing (report text row weak, below) |
| 1i | Failures: exit 0 in non-strict mode with `fake_qmd_env` | `test_lint_exits_zero_with_blocks_out_of_step` | existing |
| 1j | Failures (amendment): a block after an unclosed fence is "inside an unclosed code fence" | `test_block_after_an_unclosed_fence_is_named_for_the_fence_not_its_linkers_after_one_rebuild`, `test_report_says_a_block_sits_inside_an_unclosed_code_fence` | existing |
| 2a | rebuild puts section / bracketed / empty-text linkers in the block | `test_rebuild_lists_the_linker_of_a_section_link`, `..._of_a_link_text_holding_brackets`, `..._of_a_link_with_empty_text` | existing |
| 2b | rebuild: no linker from code (inline, ``` , ~~~, after an unclosed fence, indented fence, info-string fence) or from `_inbox/`; no block written into `_inbox/` | `test_rebuild_ignores_a_link_inside_inline_code`, `..._inside_a_backtick_fence`, `..._inside_a_tilde_fence`, `..._after_an_unclosed_fence`, `test_rebuild_reads_no_link_inside_an_indented_fence`, `test_rebuild_treats_a_fence_with_an_info_string_as_a_fence`, `test_rebuild_takes_no_linker_from_a_page_under_inbox`, `test_rebuild_writes_no_block_into_a_page_under_inbox` | existing |
| 2c | after one rebuild the lint lists nothing (unclosed and in-fence pages aside, which stay listed) | `test_lint_lists_nothing_after_one_rebuild`, `test_unclosed_block_page_stays_listed_after_one_rebuild`, `test_rebuild_appends_one_block_to_an_unclosed_fence_page_over_three_rebuilds` | existing |
| 2d | Invariant 2: byte-identical blocks on a notebook using none of the new forms | `test_block_text_is_byte_identical_to_the_golden_for_ordinary_links` | existing (frozen green on arrival; bite shown by a heading mutant, per its freeze reason) |
| 3a | new wiki-cycle cases red on the old copy, green on the new, both models | `tests/skills/wiki-cycle/cases.json` `backlinks` dirty and clean cases; `check.py` `_check_backlink_lint_zero` | existing (the run is recorded in `checkpoints.md`, not re-run here) |
| 3b | hub case's final lint reads 0 out of step | `hub-misses-one-tagged-entry-gets-one-line-others-untouched` via `_check_backlink_lint_zero` (`check.py:2917`) | existing (same caveat) |
| 3c | suite fixtures and `reference.md` carry one Phase 3 | none (my Grep for `Step 3.5` / `Phase 3.5` over the touched folders finds only the intended history lines: `reference.md:124`, `SKILL.md:141`, wiki-lint's own Step 3.5, wrap-up's own) | none: no test, no `manual: step 3` line |
| 3d | `/wiki-report`'s Needs-you template carries the backlink line when the count is above zero | none (`skills/wiki-report/SKILL.md:188` has the lint-table row, `:278` the Needs-you text; both suite cases read zero, so no case plants a non-zero count) | none: no test, no `manual: step 3` line |
| 4 | docs say what changed; `wiki-promote.py` comment names Step 3 | `manual: step 4` in `## Testing Decisions` | manual; evidence run here is the Grep in 3c and the diff stat only, the docs were not read again against steps 1-3 (the review rounds read them) |
| I1 | the four invariant files stay green | `test_promote_backlinks.py` 14/14, `test_cycle_script_fixes.py` 44/44, `test_lint_spec_values.py` 11/11, `test_hub_tag.py` 12/12 | existing |
| I2 | block format and placement unchanged for ordinary links | as 2d, plus `test_rebuild_replaces_the_real_block_below_a_block_example_in_a_code_fence` | existing |
| I3 | lint exit codes unchanged | as 1i | existing |

## Tests bite — hand mutation pass on the current scripts

Method: `hand-mutation-bl.py.txt`'s, one planted bug at a time on every line the change added to `scripts/wiki-lint-mechanical.py` and `scripts/wiki-reciprocate-backlinks.py` (against the fixed point; docstrings left out), run on scratch copies of `scripts/` and `tests/scripts/` (the repo is never written). Four changes from the first pass, all of method and not of bar: a mutant that does not compile is dropped (8) instead of scored as a kill; an operator is applied only to the code part of a line, never a trailing comment; a mutant `test_backlink_blocks.py` lets through is also run against the four invariant files (killed if any fails); mutants run 14 at a time, each in its own copy. The unmutated copy passed all five files first (baseline 99/99, 14/14, 44/44, 11/11, 12/12). Result file: `hand-mutation-bl-result-verify.json` (each survivor carries its classification). After the pass `git diff --stat -- scripts/` prints nothing.

Killed 135 of 157 (lint 78 of 93, rebuild 57 of 64). Every kill was by `test_backlink_blocks.py`; the invariant files killed none that it let through. 22 survivors:

| Survivor | Verdict |
|---|---|
| lint `:332` `continue` to `pass` (two forms) | equivalent: the last statement of the loop body |
| lint `:1452`, `:1460`, `:1474` `out.append("")` to `pass` | equivalent: a blank line in the report |
| lint `:1454` (x2), `:1457` (x2), `:1458` (x2): wording of the section's prose ("does not link" to "does link", "and if" to "and if not", "not closed" to "closed") | equivalent for behaviour: report prose, not pinned by any test; the mutants do make that prose false, so a person may want one assertion on it |
| rebuild `:104` `opened = 0` to `pass` | equivalent: dead initial value, `opened` is set before any use |
| rebuild `:110` fence-line flag `(line, True, True)` | equivalent: the third value is read only on START lines, which a fence line never is |
| rebuild `:300` (x2): wording of the skipped-pages report line | equivalent for behaviour: report prose, not pinned |
| **A.** lint `:302` `if in_fence:` to `if not in_fence:` and `:303` `opened = i` to `pass` | **real gap** (one gap, two mutants): no test has a closed block above a later unclosed fence. Shown by experiment: a page `block, then "```" never closed` is clean unmutated, and gets an `in_fence` row on either mutant (a false row on a correct page). |
| **B.** lint `:1466` "block not closed" row text to "block closed" and to `pass` | **real gap** (two mutants): `test_block_with_a_start_marker_lacking_its_end_is_named_in_the_report` asserts `"block not closed" in s`, and the section's own prose (lines 1458-1459) always holds those words, so the row's text is unpinned. The first pass killed this mutant; the prose added in fix rounds 2-3 made the frozen test vacuous. |
| **C.** rebuild `:110` fence-line flag `(line, False, False)` | **real gap**, contrived: a link written on a fence line (`` ``` see [B](b.md) ``) counts in the rebuild and not in the lint. Shown by experiment: unmutated "updated 0"; mutant "updated 1, +1 backlinks", b gets a block. |
| **D.** rebuild `:162` `text = BLOCK_RE.sub("", text)` to `pass` | **real gap**: no test has a link written below the page's real block. Shown by experiment: unmutated, `b.md` gets its block; mutant, it gets none (the stray-START cut then takes the block and everything after it). Real pages with text after the block are plausible; not measured here. |
| **E.** rebuild `:193` `return False, [], []` to `return True, [], []` | **real gap**, low impact: a skipped page is counted as updated. Shown by experiment: unmutated "Processed 2 entries; updated 0"; mutant "updated 1". No test reads the summary count of a skipped page. |

Seven of the 22 are real gaps (A x2, B x2, C, D, E). They are findings; none changes the layer's named-FAIL status. Gap D and gap A are the two a real notebook could meet.

## Read-only dry run of the current backlink script (`--dry-run`, no `--cycle-id`, so nothing is written)

| Notebook | Recorded before fix round 1 | Today | Difference |
|---|---|---|---|
| llm-wiki-bootstrap | +10 / -0 | "Processed 281 entries; updated 8; +10 backlinks, -0." | none |
| agentic-design | +20 / -0 | "Processed 1718 entries; updated 5; +20 backlinks, -0." | none |
| investment-agent | +187 / -0 | "Processed 319 entries; updated 100; +187 backlinks, -0." | none |
| agent-builder-bootstrap | +3 / -3 | "Processed 465 entries; updated 6; +3 backlinks, -3." | none |

No count moved through six fix rounds. The -3 are the agent-builder page `project/decisions/intake-build-candidates-seven-skills-built-derive-tests-folded-into-verify-2026-09-08.md`: its line 99 reads `  ```flow block is in the file …` and is the only fence line in the file, so everything after it (the three Related links on lines 115-117 included) is code under the rule, and its three targets (`do-code-change-pack-2026-07-22.md`, `noun-verb-test-…-2026-09-06.md`, `self-testing-checkers-…-2026-09-06.md`) each lose that one backlink line (shown as `+0 -1` in the dry run). The +3 there are `50-do-code-change.md`, `55-the-guard-scripts.md` and `misplaced-wiki-inbox-folder-backlink-bloat-2026-07-18.md`, one each. (Requirements Fact 9's older figures, such as investment-agent "98 pages (+161)", were taken with the old rule on 2026-11-14 before the section-link and bracketed-text forms were read; they are not comparable.)

## The lint's backlink check, read-only (on scratch copies of each notebook's `wiki/`, because the lint always writes `lint-report.md` into its notebook; `--vault` pointed at the copies; the real notebooks were not touched)

Row counts by kind, before any rebuild, then after one rebuild of the copy (exit 3 on every run is the lint's own "part of it checked nothing", the scratch copy being no qmd collection; not about this check):

| Notebook | Before: pages listed | extra / missing pages (links) | not closed | in fence | After one rebuild |
|---|---|---|---|---|---|
| llm-wiki-bootstrap | 8 | 0 extra / 8 missing pages (10 links) | 0 | 0 | 0 |
| agentic-design | 5 | 0 extra / 5 missing pages (20 links) | 0 | 0 | 0 |
| agent-builder-bootstrap | 7 | 3 extra pages (3 links) and 3 missing pages (3 links) | 0 | 1 (the intake page above) | 1 (the intake page, in_fence, needs a hand fix) |
| investment-agent | 100 | 0 extra / 100 missing pages (187 links) | 0 | 0 | 0 |

The "before" figures equal the dry run's (+10, +20, +3/-3, +187), and "after" is 0 everywhere except the one page the rebuild is meant to leave for a hand fix.

## The two recorded trade-offs, measured (the four notebooks' `wiki/**/*.md`, 2640 pages hold a block, so the glob reached them)

- (a) spec-31, a markdown link inside a double-backtick span (pattern: two backticks, no backtick between, then a `](…).md` target): 0 hits in each of the four notebooks, 0 in total.
- (b) spec-32, any link whose target is `x.md` or ends in `/x.md`: 0 hits in total; there is also no page named `x.md` in any notebook (a Glob for `**/x.md` finds none).

## Not checked, or checked weaker than named

- The wiki-cycle skill suite was not re-run (cost; recorded red-then-green only).
- Step 5.5's re-run order (automatic promotion) is not covered by any suite case (`checkpoints.md` and `PENDING.md` say so).
- `prove_tests_bite.py` cannot see `scripts/`; the hand pass above is the evidence, with the real gaps A-E open.
- Docs (step 4) were not re-read against the steps, only Grepped.
- Whether real pages carry text after their block (gap D) was not measured.

## Routing

Three layers are not PASS and none was fixed here. Floor (bar-unmoved): approve both named moves or reword the INSTALL-INVENTORY row and drop the noqa (implement or the requester). Coverage: add a `manual: step 3` line to `plan.md` or write the two tests (plan or implement). Tests-bite: the named FAIL stands under Decision 4; the seven real survivor gaps (A-E) go to the requester as findings, with tests proposed for A, B, D and E.

VERDICT: FAIL — bar-unmoved, coverage, tests-bite
