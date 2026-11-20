# Verification result — 243-framework-docs-master (verify round 3)

Verified by the architect (verify step only), 2026-11-20. Fixed point `7b66e2a92fc2cfa3892050f143bd35fe0e6bd40d`; HEAD `f522f96`; branch `features/243-framework-docs-master`; `git status --short` printed nothing before the run. Every command below was run fresh in this session, one per call, `uv run python <absolute path>`. Earlier rounds are kept in git (round 2 at `9e79fc9`, round 1 at `89f72bd`). Round 2 failed findings-addressed and coverage; the retry ceiling was reached and Mark chose one more review round (`checkpoints.md`, "Retry-ceiling exhaustion, 2026-11-20", Mark 16:02Z, "1"), after which review round 4 ran.

Nothing in the code or tests moved since round 2's tree: `git diff 89f72bd HEAD --stat -- . :!.do-code-change` printed nothing (empty). The only changes since are in `.do-code-change/` (plan.md, checkpoints.md, ledger, round-4 report). So round 2's test and coverage reading carries to HEAD, and every command below was nonetheless re-run.

Layers, one line each:

- tests: PASS — four named suites exit 0 ("91/91 passed", "23/23 passed", "40/40 passed", "82/82 passed"); rest of `tests/scripts/` 61 files exit 0 with 0 FAIL lines, `test_fetch_repo.py` exit 1 "11/27 passed" (16 FAIL lines), the same count and failures as at the fixed point in rounds 1 and 2
- diff-contains-fix: PASS — every file the plan's steps name is in `git diff 7b66e2a… --stat` (55 files, 2001 insertions, 103 deletions), nothing untracked or uncommitted, notebook repository clean
- findings-addressed: PASS — review-ledger.py exit 0, "review-ledger: met - no open blocking item, every verdict current (7 closed, 45 non-blocking), 4 round(s)" / "review-ledger: exit 0 - met"
- frozen-tests: PASS — check-freeze.py exit 0, "frozen-tests layer: PASS — 86 entries checked (+ 164 from earlier changes), all match or unfrozen with a reason (7 retired: deleted on purpose) (118 frozen green, each with its reason)" / "check-freeze: exit 0 - PASS: every frozen test matches, or changed with a reason"
- coverage: PASS — every plan step's done criterion maps to an `existing` test or a `manual:` line in plan.md's Testing Decisions; row 3c is now `manual: step 3` (plan.md:79); step 17 is manual and met only under Mark's recorded ruling (spec-18 open, non-blocking)
- bar-unmoved: PASS — floor-guard.py exit 0, "floor-guard: exit 0 - clean: no move lowers the bar"
- in-scope: PASS — scope-guard.py exit 0, "scope-guard: exit 0 - PASS: every touched file is inside the declared scope"
- tests-bite: off — on demand by project setting (Mark, 2026-11-20), prove_tests_bite.py `--check` exit 4, "tests-bite layer: OFF - mutation testing is on demand in this project (.claude/do-code-change.json: decided by Mark, 2026-11-20); no pass runs with each change (exit 4)" / "VERDICT: OFF"

---

## 1. tests — PASS

The four suites print no exit-code line; the Bash tool reported no non-zero exit for any, so each is exit 0, and each ends on its `N/N passed` line with no `FAIL` line in the output read.

| Command | Last line |
|---|---|
| `uv run python C:/github.com/llm-wiki-bootstrap/tests/scripts/test_global_toolset.py` | `91/91 passed` |
| `… test_local_folder.py` | `23/23 passed` |
| `… test_standalone.py` | `40/40 passed` |
| `… test_search_mode.py` | `82/82 passed` |

The other 62 files in `tests/scripts/` were run once by a scratch runner in the session scratchpad (`run_rest.py`, outside the repository), which printed each file's exit code, last line and its `FAIL` lines. Read from its output: 61 files exit 0 with 0 FAIL lines; 1 file exit 1. Most end on `N/N passed`; three end on something else (`test_cycle_script_fixes.py`: `Wrote step JSON: …\drive-fetch.json`; `test_drive_access.py`: `Cached token missing required scopes; will re-authenticate …`; `test_fetch_page.py`: `2 page fetches already running … waiting for one`); their exit is 0 with no FAIL line, and I did not read their per-check output.

**Exit 1, predates this change:** `test_fetch_repo.py`: `exit 1; 16 FAIL line(s); last: 11/27 passed` (first FAIL line: `FAIL exit 0 [  Cloning: …\demo-skills (current commit only)`; also `FAIL one raw written`, `FAIL README.md is in, under its File heading, with its text`, and the rest). This is the known fact the brief gives: the same file fails 11/27 at the fixed point (extracted 7b66e2a, run in rounds 1 and 2), with the same 16 FAIL lines. I did not re-run it at the fixed point this round. `wiki-fetch-repo.py` is not among this change's files. The count and the failure set match the recorded fixed-point run, so the failure is not covered by this change; the layer's verdict rests on the four named suites and the other 61 files.

The paid skill suite was not re-run (instructed). Recorded reports: `tests/skills/.results/new-wiki/20261119-223534-red-green-7b66e2a92fc2cfa3892050f143bd35fe0e6bd40d/report.md` ($3.18) and `tests/skills/.results/new-wiki/20261119-224512/report.md` (`local-readme-project-default-stubs` PASS on Sonnet and Opus). See coverage row 17.

## 2. diff-contains-fix — PASS

`git -C C:/github.com/llm-wiki-bootstrap diff 7b66e2a92fc2cfa3892050f143bd35fe0e6bd40d --stat -- . :!.do-code-change` lists 55 files, 2001 insertions, 103 deletions (the same totals as round 2). `git status --short` printed nothing. Files each step names, each in the stat: `scripts/{_install_tooling,_wiki_config,new-wiki,wiki-update,wiki-qmd-query,wiki-map-compile,wiki-upgrade}.py`, `seed/best-practices-local/README.md` (new, 21 lines), the six `framework-docs/*.md`, `agents/wiki-ingester/wiki-ingester-reading-list.json`, `templates/{CLAUDE.md.tmpl,feeds.md.tmpl}`, the 17 `skills/` files, `wiki-seed/{install,obsidian,user-guide}.md`, `CLAUDE.md`, `INSTALL-INVENTORY.md`, `V2_ROADMAP.md`, `CHANGELOG.md`, tests `test_global_toolset.py`, `test_local_folder.py` (new, 470 lines), `test_search_mode.py`, `test_standalone.py`, `test_link_gaps.py`, and `tests/skills/{PENDING.md,new-wiki/*}`.

Notebook steps (6 to 8, 13 to 16) are not in this repository's diff by design: `git -C C:/github.com/project-notebooks status --short` over `notebooks/agentic-design/wiki/research/wiki`, `notebooks/llm-wiki-bootstrap/wiki/project/decisions`, `notebooks/agentic-design/wiki/project/best-practices` and `notebooks/agentic-design/_INDEX.md` printed nothing (committed).

## 3. findings-addressed — PASS

The query is run with `--cap 4`, because Mark approved a fourth review round at the retry-ceiling checkpoint (`checkpoints.md`, "Retry-ceiling exhaustion, 2026-11-20": Mark, DM 16:02Z, verbatim "1", recorded as continue manually with review round 4). `uv run python C:/Users/mark/.claude/workflows/do-code-change/scripts/review-ledger.py query --diff-base 7b66e2a92fc2cfa3892050f143bd35fe0e6bd40d --cap 4 --ledger C:/github.com/llm-wiki-bootstrap/.do-code-change/243-framework-docs-master/review-ledger.json`, exit 0:

```
review-ledger: met - no open blocking item, every verdict current (7 closed, 45 non-blocking), 4 round(s)
review-ledger: exit 0 - met
```

Written beside it, as a finding and never as the verdict: round 4's only `important` finding was spec-15 (plan step 3's `wiki_folders` clause had no test). Its site, re-read once: `plan.md:79` now holds `manual: step 3 (the wiki_folders clause only; …) — one scratch Phase B run's written .claude/wiki-config.json wiki_folders, quoted in checkpoints.md (verify round 2: {'project': 'stubs', 'research': 'stubs'}); review round 4 ruled this the fix over a new frozen test (spec-15)`, and `checkpoints.md` carries the "Review round 4" entry with that evidence. spec-1 and standards-2 are re-recorded (the ledger shows 7 closed, none stale).

## 4. frozen-tests — PASS

`uv run python C:/Users/mark/.claude/skills/verifying-before-done/scripts/check-freeze.py C:/github.com/llm-wiki-bootstrap/.do-code-change/243-framework-docs-master/test-freeze.json --repo C:/github.com/llm-wiki-bootstrap` (it reads the project record `.do-code-change/test-freeze.json` beside it), exit 0:

```
frozen-tests layer: PASS — 86 entries checked (+ 164 from earlier changes), all match or unfrozen with a reason (7 retired: deleted on purpose) (118 frozen green, each with its reason)
check-freeze: exit 0 - PASS: every frozen test matches, or changed with a reason
```

The 118 green-frozen entries are each printed by the script with its reason (41 belong to this change; the other 77 to earlier changes' project record); none moved. One extra run, over the budget of once, was made on the project record alone (`.do-code-change/test-freeze.json --no-project`) and read: "frozen-tests layer: PASS — 164 entries checked, all match or unfrozen with a reason (2 retired: deleted on purpose) (77 frozen green, each with its reason)" / "check-freeze: exit 0 - PASS: every frozen test matches, or changed with a reason". It adds nothing the first run did not cover; the layer's verdict is the first run.

## 5. coverage — PASS

Rows are read from the named tests' names and the fresh run's check lines, not from the suite being green alone. `existing` = a named test asserts it today. No code or test moved since round 2 (`git diff 89f72bd HEAD`, empty outside `.do-code-change/`), so round 2's rows are carried, with the changed plan lines re-read.

| # | Plan step, rule | Pinning test | Status |
|---|---|---|---|
| 1a-1i | Step 1: new layout written, old copy stale and removed, `--phase docs --check` and refresh, spec lookup, held-file / non-`.md` / unregistered failures, existing invariants | `test_empty_toolset_gets_docs_at_new_layout`, `test_old_copy_makes_status_stale_naming_the_six`, `test_refresh_clears_old_framework_folder_only`, `test_phase_docs_check_lists_old_files_as_remove_without_writing`, `test_phase_docs_refresh_turns_check_current`, `test_spec_lookup_*` (2), `test_held_old_file_is_named_in_failed_rest_proceeds`, `test_phase_docs_reports_held_file_as_failed`, `test_dry_run_lists_no_failed_entries`, `test_non_md_items_in_old_folder_keep_the_folder`, `test_unregistered_toolset_with_only_old_docs_is_migrated`, and the pre-existing replace / remove / other-pack / line-ending checks, all PASS in this run | existing |
| 2a-2i | Step 2: README created, replaced, re-added, user files untouched, dry run, shipped text names both places and says to ask, plain file / unwritable / missing-source failures | `test_empty_toolset_gets_local_readme_with_shipped_bytes`, `test_edited_local_readme_is_replaced_by_refresh`, `test_deleted_local_readme_is_added_again`, `test_user_files_in_local_are_untouched`, `test_dry_run_reports_local_readme_writes_nothing`, `test_shipped_local_readme_*` (4), `test_plain_file_where_local_belongs_lists_readme_in_failed`, `test_unwritable_readme_replacement_is_listed_failed_rest_done`, `test_missing_readme_source_is_skipped_by_status` | existing |
| 3a | Step 3: `taxonomy_for` gives `best-practices/local` before `sessions` for nine pairs | `test_taxonomy_puts_best_practices_local_before_sessions_for_all_nine_pairs` | existing |
| 3b | Step 3: Phase B creates the README with shipped bytes for stubs, empty and none; `best-practices/local` in the README folder list and `taxonomy_for`'s return | `test_phase_b_writes_local_readme_with_shipped_bytes_for_stubs`/`_empty`/`_none`, `test_phase_b_readme_folder_list_has_a_best_practices_local_line`, `test_phase_b_readme_local_line_carries_its_note`, `test_phase_b_summary_lists_best_practices_local_before_sessions` | existing |
| 3c | Step 3: `.claude/wiki-config.json`'s `wiki_folders` keeps only the interview's two answers (`project`, `research`) | no test reads the written config (`test_local_folder.py:145-146` reads the stdout summary, a different value). `manual: step 3` at plan.md:79: round 2's scratch Phase B run printed `{'project': 'stubs', 'research': 'stubs'}` (read via `git show 9e79fc9:…/verification-result.md`, row 3c; valid at HEAD because no code moved). I re-read the writers in this run: `scripts/new-wiki.py:1218` and `:1256` both write `"wiki_folders": {"project": args.project_folder, "research": args.research_folder}`; `:1345` is the stdout list from `taxonomy_for`. I did not re-run the probe | manual (round 4 ruled this the fix, spec-15) |
| 3d | Step 3: lint of the fresh scaffold draws no finding on `best-practices/local/README.md` that `HOME.md` does not also get | `test_lint_of_a_fresh_scaffold_draws_no_finding_on_the_local_readme_that_home_does_not` (README kinds a subset of HOME's, plus a control that the same lint names a bad note) | existing |
| 3e-3h | Step 3: `--dry-run` writes nothing, README source missing stops the scaffold, existing CLAUDE.md kept, `_MAP`/README/HOME rendered on a first run, folder guard accepts `best-practices/local` | `test_dry_run_prints_would_lines_for_the_local_folder_with_its_readme`, `test_dry_run_leaves_the_temp_tree_unchanged`, `test_missing_readme_source_stops_the_scaffold_before_any_best_practices_folder`, `test_existing_claude_md_is_kept_byte_for_byte`, `test_first_run_renders_the_three_wiki_scaffold_files`, `test_filing_into_best_practices_local_is_accepted_in_a_wiki_that_lacks_the_folder` | existing |
| 4a-4e, 4b | Step 4 and 4b: `sample_titles`, `drop_machine_files`, lint treats `local/` notes as entries, `_MAP.md` lists them, no-folder wiki unchanged | `test_sample_titles_includes_best_practices_entries`, the three `test_drop_machine_files_*`, and in `test_local_folder.py` `test_valid_note_in_best_practices_local_*`, `test_note_without_tags_*`, `test_note_without_frontmatter_*`, `test_map_lists_a_note_in_best_practices_local`, `test_existing_map_sections_do_not_change_*`, `test_wiki_with_no_best_practices_folder_*`, `test_a_best_practices_local_folder_with_no_titled_note_*`, `test_the_shipped_local_readme_is_treated_in_the_map_*`; `manual: step 4` read in `implement-log.md` "Step 4 manual evidence" this run (all 10 collections `Pattern:  **/*.md`; the temp-index keyword search found `best-practices/local/my-notes.md`) | existing; manual evidence read, not re-run |
| 5 | Step 5: no shipped file names the old path | `test_no_shipped_file_names_the_old_toolset_framework_path` (passes); the install frontmatter gate (implement-log step 5: 11/11 parse), not re-run | existing |
| 9a-9d | Step 9: Local changes line, Practice page line, link path arithmetic, versions and floors | `test_each_doc_opens_with_a_local_changes_line_naming_its_own_file`, `test_each_doc_has_a_practice_page_line_right_after_the_local_changes_line`, `test_each_practice_link_normalises_to_its_page_path_from_the_toolset_folder`, `test_the_where_we_stand_link_in_wiki_authoring_normalises_to_its_notebook_path`, `test_each_doc_version_is_at_least_the_planned_number`, and the two raised floors (cycle-step-return-format 10, frontmatter 20); `manual: step 9` (resolve run `dead: 0`, temp-wiki lint) read in implement-log this run | existing; manual evidence read, not re-run |
| 10 | Step 10: tier rules and repository sentence inside the `tier_rubric_text()` span; `status`, `origin`, `cycle_id` rows | `test_the_rubric_span_holds_the_vendor_post_rule`, `…_holds_the_repository_sentence`, `…_lacks_the_old_repository_cell_text`, `test_status_row_says_wiki_promote_strips_proposed`, `test_origin_row_*` (3), `test_cycle_id_row_says_nothing_in_the_install_writes_it` | existing |
| 12 | Step 12: template precedence entry | the five `test_precedence_entry_*` checks and `test_rendered_template_lacks_the_old_toolset_framework_path` | existing |
| 6, 7, 8, 11, 13-16 | Notebook and doc steps | each has a `manual:` line in plan.md's Testing Decisions; the evidence blocks for steps 6, 7, 8, 11, 13, 14, 15 and 16 (and the step 7 federation follow-up) were read in implement-log.md this run; they are the developer's recorded outputs, not re-run | manual, evidence read, not re-run |
| 17 | New cases red then green on both models; PENDING rows | `manual: step 17`; the two recorded reports; implement-log "Step 17". `local-readme-project-none` passed on the old copy, so the literal "red then green" is not met for it; the red rests on the free old-vs-new script check, accepted under Mark's recorded ruling (`checkpoints.md`, "spec-1 settled", DM 2026-11-20 15:28Z, "It meant what you recommended"). spec-18 (the ruling does not say in words that the free check is model-independent) is still open, non-blocking | manual, met under the ruling (judgment call, see risks) |

Layer verdict: PASS. Every criterion has an `existing` test or a manual line in Testing Decisions; none is `none` or `proposed`. Row 3c, the round-2 FAIL, is now a recorded manual line backed by the writers read in this run. Row 17 stands on the settled exception, named, not argued away.

## 6. bar-unmoved — PASS

`uv run python C:/Users/mark/.claude/skills/constraint-driven-development/scripts/floor-guard.py --base 7b66e2a92fc2cfa3892050f143bd35fe0e6bd40d --repo C:/github.com/llm-wiki-bootstrap`, exit 0:

```
floor-guard: clean (2001 added, 103 removed lines checked)
floor-guard: exit 0 - clean: no move lowers the bar
```

No `floor-approvals.json` was needed.

## 7. in-scope — PASS

`uv run python C:/Users/mark/.claude/skills/verifying-before-done/scripts/scope-guard.py check --artifact-dir C:/github.com/llm-wiki-bootstrap/.do-code-change/243-framework-docs-master`, exit 0:

```
scope-guard: PASS - 55 touched file(s), all inside the declared scope (…)
scope-guard: exit 0 - PASS: every touched file is inside the declared scope
```

The script's note lists 20 declared globs that match no file here (the `notebooks/…` paths, which live in project-notebooks, `tests/skills/.results/new-wiki/**`, and misread prose words `No`, `The`, `_INDEX.md`, `framework/`, `checkpoints.md`); a warning, exit unchanged. Checked in the 55-file `[in-scope]` list: no touched file is in scope only through a misread glob; each matches a real path glob (`scripts/…`, `seed/**`, `framework-docs/**`, `skills/**`, `tests/…`, the root docs, `.claude/do-code-change.json`).

## 8. tests-bite — off

`uv run python C:/Users/mark/.claude/skills/proving-python-tests-bite/scripts/prove_tests_bite.py --check --base 7b66e2a92fc2cfa3892050f143bd35fe0e6bd40d`, exit 4:

```
tests-bite layer: OFF - mutation testing is on demand in this project (.claude/do-code-change.json: decided by Mark, 2026-11-20); no pass runs with each change (exit 4)
VERDICT: OFF
```

A recorded standing decision (Mark, `checkpoints.md`, 04:29Z), not a FAIL. The hand mutation pass in implement-log.md (92 mutants, 89 killed, 3 equivalent) is extra evidence only.

---

Not checked or only partly read: the paid skill suite was not re-run (instructed); the notebook steps' resolve and lint runs were not repeated, only their recorded evidence and git state read; `test_fetch_repo.py` was not re-run at the fixed point this round (the brief's known fact, from rounds 1 and 2); `test_cycle_script_fixes`, `test_drive_access` and `test_fetch_page` were read by exit code, last line and FAIL lines only; the plan.md:79 probe output was read from round 2's report, not re-run.

VERDICT: PASS
