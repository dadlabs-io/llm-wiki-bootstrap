# Verification result — 243-framework-docs-master (verify round 2)

Verified by the architect (verify step only), 2026-11-20. Fixed point `7b66e2a92fc2cfa3892050f143bd35fe0e6bd40d`; HEAD `89f72bd`; branch `features/243-framework-docs-master`; `git status --short` prints nothing before and after this run's commands. Every command below was run fresh in this session, one per call, `uv run python <absolute path>`. Round 1 (against `2d962d4`'s tree) is kept in git at `89f72bd` as this file; it failed coverage and bar-unmoved. Since then only `89f72bd` landed: `git diff 2d962d4 HEAD --stat` lists `checkpoints.md` (+3), `plan.md` (4 lines), the round-1 report, and one-line comment edits in `tests/scripts/test_global_toolset.py`, `test_local_folder.py` (two lines) and `test_search_mode.py`. No source file under `scripts/` moved.

Layers, one line each (fixed shape):

- tests: PASS — four named suites 91/91, 23/23, 40/40, 82/82; rest of `tests/scripts/` 61 files exit 0, `test_fetch_repo.py` exit 1 11/27, identically at the fixed point (run fresh here), so it predates the change
- diff-contains-fix: PASS — every file the plan's steps name is in `git diff 7b66e2a… --stat` (55 files, 2001 insertions, 103 deletions), nothing untracked, notebook repository clean
- findings-addressed: FAIL — review-ledger.py exit 1, "review-ledger: not yet met - 0 open blocking item(s), 2 stale verdict(s); 4 closed and current"
- frozen-tests: PASS — check-freeze.py exit 0, "frozen-tests layer: PASS — 86 entries checked (+ 164 from earlier changes), all match or unfrozen with a reason (7 retired: deleted on purpose) (118 frozen green, each with its reason)"
- coverage: FAIL — one clause of plan step 3 has no test: "`.claude/wiki-config.json`'s `wiki_folders` keeps only the interview's two answers" (row 3c); the rest of the map is `existing` or a recorded manual line
- bar-unmoved: PASS — floor-guard.py exit 0, "floor-guard: exit 0 - clean: no move lowers the bar"
- in-scope: PASS — scope-guard.py exit 0, "scope-guard: exit 0 - PASS: every touched file is inside the declared scope"
- tests-bite: off — on demand by project setting (Mark, 2026-11-20), prove_tests_bite.py `--check` exit 4, "tests-bite layer: OFF - mutation testing is on demand in this project (.claude/do-code-change.json: decided by Mark, 2026-11-20); no pass runs with each change (exit 4)" / "VERDICT: OFF"

---

## 1. tests — PASS

Proving commands (fresh, run alone). The four suites print no exit-code line; the pass is the `N/N passed` last line with no `FAIL` line in the output read.

| Command | Result |
|---|---|
| `uv run python C:/github.com/llm-wiki-bootstrap/tests/scripts/test_global_toolset.py` | last line `91/91 passed` |
| `… test_local_folder.py` | last line `23/23 passed` |
| `… test_standalone.py` | last line `40/40 passed` |
| `… test_search_mode.py` | last line `82/82 passed` |

The rest of `tests/scripts/` (62 files) was run once by a scratch runner in the session scratchpad (`run_all.py`, outside the repository), which printed each file's exit code, last line and every line starting `FAIL`. Result read from its output: 61 files exit 0 with 0 FAIL lines; 1 file exit 1. Of the 61, most end on an `N/N passed` count; three end on something else (`test_cycle_script_fixes.py`: `Wrote step JSON: …\drive-fetch.json`; `test_drive_access.py`: `Cached token missing required scopes; will re-authenticate …`; `test_fetch_page.py`: `2 page fetches already running … waiting for one`). Their exit is 0 and they print no FAIL line; I did not read their per-check output.

**Exit 1, predates this change:** `test_fetch_repo.py` — at HEAD, `11/27 passed`, 16 `FAIL` lines (`FAIL exit 0 [Cloning: …\demo-skills (current commit only) / ERROR: git ls-tree failed: fatal: Not a valid object name HEAD`, `FAIL one raw written`, `FAIL README.md is in, under its File heading, with its text`, and the rest). At the fixed point, run fresh this session (`git archive 7b66e2a… scripts tests/scripts pyproject.toml` extracted into a scratch folder, `uv run python <scratch>/fp/tests/scripts/test_fetch_repo.py`): exit 1, the same 16 FAIL lines, `11/27 passed`. `wiki-fetch-repo.py` is not among this change's files; the cause is the fixture repo's `HEAD` in this environment.

The paid skill suite was not re-run (instructed). Recorded reports: `tests/skills/.results/new-wiki/20261119-223534-red-green-7b66e2a92fc2cfa3892050f143bd35fe0e6bd40d/report.md` ($3.18; `local-readme-project-none` PASS on both models but also passes on the old copy; `local-readme-project-default-stubs` FAIL on the new copy on both, the auto-mode classifier refused the Phase B call) and `tests/skills/.results/new-wiki/20261119-224512/report.md` (`local-readme-project-default-stubs` PASS on Sonnet and Opus). Step 17's red rests on the free old-vs-new script check, which Mark settled (DM 2026-11-20 15:28Z, "It meant what you recommended"; `checkpoints.md`, entry "spec-1 settled"). Not a pass of the plan's literal "red then green" for `local-readme-project-none`; named here as a settled exception, card #252 for the harness gap.

## 2. diff-contains-fix — PASS

`git -C C:/github.com/llm-wiki-bootstrap diff 7b66e2a92fc2cfa3892050f143bd35fe0e6bd40d --stat -- . :!.do-code-change` lists 55 files, 2001 insertions, 103 deletions (the same total as round 1, since 89f72bd changed comments only). `git status --short` prints nothing (nothing untracked, nothing uncommitted). Files each step names, each in the stat: `scripts/{_install_tooling,_wiki_config,new-wiki,wiki-update,wiki-qmd-query,wiki-map-compile,wiki-upgrade}.py`, `seed/best-practices-local/README.md` (new, 21 lines), the six `framework-docs/*.md`, `agents/wiki-ingester/wiki-ingester-reading-list.json`, `templates/{CLAUDE.md.tmpl,feeds.md.tmpl}`, the 17 `skills/` files, `wiki-seed/{install,obsidian,user-guide}.md`, `CLAUDE.md`, `INSTALL-INVENTORY.md`, `V2_ROADMAP.md`, `CHANGELOG.md`, tests `test_global_toolset.py`, `test_local_folder.py` (new, 470 lines), `test_search_mode.py`, `test_standalone.py`, `test_link_gaps.py`, and `tests/skills/{PENDING.md,new-wiki/*}`.

Notebook steps (6 to 8, 13 to 16) are not in this repository's diff by design: `git -C C:/github.com/project-notebooks status --short` over `notebooks/agentic-design/wiki/research/wiki`, `notebooks/llm-wiki-bootstrap/wiki/project/decisions`, `notebooks/agentic-design/wiki/project/best-practices` and `notebooks/agentic-design/_INDEX.md` prints nothing (committed). Their step commits and the step 13 link repoint were read in round 1 (git log) and not re-listed.

## 3. findings-addressed — FAIL

`uv run python C:/Users/mark/.claude/workflows/do-code-change/scripts/review-ledger.py query --diff-base 7b66e2a92fc2cfa3892050f143bd35fe0e6bd40d --cap 3 --ledger C:/github.com/llm-wiki-bootstrap/.do-code-change/243-framework-docs-master/review-ledger.json`, exit 1:

```
  [spec-1] STALE - the diff of its file changed since the verdict; re-verify, never trust
  [standards-2] STALE - the diff of its file changed since the verdict; re-verify, never trust
review-ledger: not yet met - 0 open blocking item(s), 2 stale verdict(s); 4 closed and current
review-ledger: exit 1 - not yet met (the open or stale items are above)
```

Round 1's query printed `met`; the two stale items are a consequence of commit 89f72bd, which edited the file each verdict's fingerprint covers: `standards-2` sits in `tests/scripts/test_global_toolset.py` (the noqa comment removal changed that file's diff), `spec-1` in `checkpoints.md` (three entries appended). The verdict is the script's exit code, so the layer is FAIL; the cause is named, not argued away.

Written beside it, as a finding and never as the verdict: each stale item's site was re-read once. `standards-2` (a skipped case recorded a PASS): `_skip()` is defined at `tests/scripts/test_global_toolset.py:40` and the root-user case at `:469` calls it; no `check(..., True)` stands for the skip; the 89f72bd edit to that file is the one comment line in `_run` (`:686`). `spec-1`: closed on Mark's word, `checkpoints.md` entry "spec-1 settled" (DM 15:28Z, "It meant what you recommended"), still present and unchanged. Route: the orchestrator records a fresh verdict for both items with `review-ledger.py verdict <id> addressed` and re-runs `query` (a ledger action of the orchestrating session, which verify does not take). The five other closed blocking items (standards-1, standards-3, risk-1, risk-5, spec-6) are current. The 39 non-blocking items are not part of this layer.

## 4. frozen-tests — PASS

`uv run python C:/Users/mark/.claude/skills/verifying-before-done/scripts/check-freeze.py C:/github.com/llm-wiki-bootstrap/.do-code-change/243-framework-docs-master/test-freeze.json --repo C:/github.com/llm-wiki-bootstrap` (it reads the project record `.do-code-change/test-freeze.json` beside it):

```
frozen-tests layer: PASS — 86 entries checked (+ 164 from earlier changes), all match or unfrozen with a reason (7 retired: deleted on purpose) (118 frozen green, each with its reason)
check-freeze: exit 0 - PASS: every frozen test matches, or changed with a reason
```

The 89f72bd comment edits sit inside `_run` helpers (not frozen tests) and one import line; every entry's hash, including entry [24] in `test_local_folder.py`, still matches. The 118 green-frozen entries are each printed by the script with its reason (41 belong to this change: invariants that held before, bite shown by transient mutation, or a red watched before the fix; the other 77 belong to earlier changes' project record); none moved.

## 5. coverage — FAIL

Rows are read from the named tests' names and the fresh run's check lines, not from the suite being green alone. `existing` = a named test asserts it today. The map below is round 1's, re-checked against the rewritten plan lines; rows unchanged since round 1 are summarised, the changed rows are in full.

| # | Plan step, rule | Pinning test | Status |
|---|---|---|---|
| 1a-1i | Step 1: new layout written, old copy stale and removed, `--phase docs --check` and refresh, spec lookup, held-file / non-`.md` / unregistered failures, existing invariants | `test_empty_toolset_gets_docs_at_new_layout`, `test_old_copy_makes_status_stale_naming_the_six`, `test_refresh_clears_old_framework_folder_only`, `test_phase_docs_check_lists_old_files_as_remove_without_writing`, `test_phase_docs_refresh_turns_check_current`, `test_spec_lookup_*` (2), `test_held_old_file_is_named_in_failed_rest_proceeds`, `test_phase_docs_reports_held_file_as_failed`, `test_dry_run_lists_no_failed_entries`, `test_non_md_items_in_old_folder_keep_the_folder`, `test_unregistered_toolset_with_only_old_docs_is_migrated`, and the pre-existing replace / remove / other-pack / line-ending checks, all PASS in the fresh run | existing (held-file cases Windows-only, run and passed on Windows) |
| 2a-2i | Step 2: README created, replaced, re-added, user files untouched, dry run, shipped text names both places and says to ask, plain file / unwritable / missing-source failures | `test_empty_toolset_gets_local_readme_with_shipped_bytes`, `test_edited_local_readme_is_replaced_by_refresh`, `test_deleted_local_readme_is_added_again`, `test_user_files_in_local_are_untouched`, `test_dry_run_reports_local_readme_writes_nothing`, `test_shipped_local_readme_*` (4), `test_plain_file_where_local_belongs_lists_readme_in_failed`, `test_unwritable_readme_replacement_is_listed_failed_rest_done`, `test_missing_readme_source_is_skipped_by_status` | existing (2h skipped as root only) |
| 3a | Step 3: `taxonomy_for` gives `best-practices/local` before `sessions` for nine pairs | `test_taxonomy_puts_best_practices_local_before_sessions_for_all_nine_pairs` | existing |
| 3b | Step 3 (rewritten line 189, first part): Phase B creates the README with shipped bytes for stubs, empty and none; `best-practices/local` is in the wiki's README folder list (`folder_notes`) and in `taxonomy_for`'s return | `test_phase_b_writes_local_readme_with_shipped_bytes_for_stubs`/`_empty`/`_none`, `test_phase_b_readme_folder_list_has_a_best_practices_local_line`, `test_phase_b_readme_local_line_carries_its_note`, `test_phase_b_summary_lists_best_practices_local_before_sessions`, `test_taxonomy_…` | existing |
| 3c | Step 3 (rewritten line 189, last clause): "`.claude/wiki-config.json`'s `wiki_folders` keeps only the interview's two answers (`project`, `research`)" | none. `grep wiki_folders tests/` finds only `test_local_folder.py:145-146`, which reads the Phase B summary's `wiki_folders` list on stdout (`new-wiki.py:1345`), a different value. No test reads `<target>/.claude/wiki-config.json`. The behaviour itself is true: a probe run of Phase B (a scratch script in the session scratchpad using the suite's `Scaffold` helper) printed `{'project': 'stubs', 'research': 'stubs'}` from the written config, and `new-wiki.py:1218` and `:1256` build it from the two answers. A probe is evidence, not a test | **none** |
| 3d | Step 3 (rewritten line 190): the mechanical lint over the fresh scaffold reports no finding on `best-practices/local/README.md` that `HOME.md` does not also get; the README carries `confidence: high` and a `standalone:` reason (read in `seed/best-practices-local/README.md` lines 6-7) | `test_lint_of_a_fresh_scaffold_draws_no_finding_on_the_local_readme_that_home_does_not` (README kinds a subset of HOME's, with a control that the same lint names a bad note in `local/`) | existing (the line now says what the test asserts) |
| 3e-3h | Step 3: `--dry-run` writes nothing, README source missing stops the scaffold, existing CLAUDE.md kept, `_MAP`/README/HOME rendered on a first run, folder guard accepts `best-practices/local` | `test_dry_run_prints_would_lines_for_the_local_folder_with_its_readme`, `test_dry_run_leaves_the_temp_tree_unchanged`, `test_missing_readme_source_stops_the_scaffold_before_any_best_practices_folder`, `test_existing_claude_md_is_kept_byte_for_byte`, `test_first_run_renders_the_three_wiki_scaffold_files`, `test_filing_into_best_practices_local_is_accepted_in_a_wiki_that_lacks_the_folder` | existing |
| 4a-4e, 4b | Step 4 and 4b: `sample_titles`, `drop_machine_files`, lint treats `local/` notes as entries, `_MAP.md` lists them, no-folder wiki unchanged | the four `test_search_mode.py` checks and the five `test_map_*` / `test_wiki_with_no_best_practices_folder_*` / `test_a_best_practices_local_folder_*` / `test_the_shipped_local_readme_*` / `test_valid_note_*` / `test_note_without_*` checks in `test_local_folder.py`; `manual: step 4` (qmd collection pattern, one keyword search) read in `implement-log.md` "Step 4 manual evidence" | existing; manual evidence read, not re-run |
| 5 | Step 5: no shipped file names the old path | `test_no_shipped_file_names_the_old_toolset_framework_path`; the install frontmatter gate over the changed skills (quoted in implement-log, not re-run) | existing |
| 9a-9d | Step 9: Local changes line, Practice page line, link path arithmetic, versions and floors | `test_each_doc_opens_with_a_local_changes_line_naming_its_own_file`, `test_each_doc_has_a_practice_page_line_right_after_the_local_changes_line`, `test_each_practice_link_normalises_to_its_page_path_from_the_toolset_folder`, `test_the_where_we_stand_link_in_wiki_authoring_normalises_to_its_notebook_path`, `test_each_doc_version_is_at_least_the_planned_number`, the two raised floors; `manual: step 9` (resolve run, temp-wiki lint) in implement-log | existing; manual evidence read, not re-run |
| 10 | Step 10: tier rules and repository sentence inside the `tier_rubric_text()` span; `status`, `origin`, `cycle_id` rows | `test_the_rubric_span_holds_the_vendor_post_rule`, `…_holds_the_repository_sentence`, `…_lacks_the_old_repository_cell_text`, `test_status_row_*`, `test_origin_row_*` (3), `test_cycle_id_row_*` | existing |
| 12 | Step 12: template precedence entry | the five `test_precedence_entry_*` checks and `test_rendered_template_lacks_the_old_toolset_framework_path` | existing |
| 6-8, 11, 13-16 | Notebook and doc steps | `manual:` lines in Testing Decisions; evidence in implement-log.md (checkpoints.md line 84 points to it) | manual, evidence read, not re-run |
| 17 | New cases red then green on both models; PENDING rows | `manual: step 17`; the two reports above; `tests/skills/PENDING.md` | manual, with the settled exception (layer 1) |

Layer verdict: FAIL, on row 3c alone. Round 1's rows 3c and 3d are fixed as far as the plan text goes: line 190 now says what its test asserts (3d is `existing`), and line 189 no longer says `best-practices` is in `wiki_folders`. But the rewritten line 189 states a new positive clause ("`wiki_folders` keeps only the interview's two answers") that no test asserts. It is unchanged behaviour and the probe shows it holds; the coverage layer asks for a named test or a `manual:` line in `## Testing Decisions`, and neither exists. Cheapest route: one check in `tests/scripts/test_local_folder.py` reading `<target>/.claude/wiki-config.json` (a new frozen test, so back to implement), or a `manual: step 3 — <evidence>` line added to plan.md's Testing Decisions with this probe's output quoted. Not passed here.

## 6. bar-unmoved — PASS

`uv run python C:/Users/mark/.claude/skills/constraint-driven-development/scripts/floor-guard.py --base 7b66e2a92fc2cfa3892050f143bd35fe0e6bd40d --repo C:/github.com/llm-wiki-bootstrap`, exit 0:

```
floor-guard: clean (2001 added, 103 removed lines checked)
floor-guard: exit 0 - clean: no move lowers the bar
```

Round 1's four `# noqa` violations are gone. `Grep noqa` over `tests/scripts` shows no `noqa` on any line this change added (the remaining hits are older files and the fixed point's own `test_search_mode.py:63`, `:323`, `:324`, and `test_standalone.py:25`, all present at the fixed point). No `floor-approvals.json` was needed.

## 7. in-scope — PASS

`uv run python C:/Users/mark/.claude/skills/verifying-before-done/scripts/scope-guard.py check --artifact-dir C:/github.com/llm-wiki-bootstrap/.do-code-change/243-framework-docs-master`, exit 0:

```
scope-guard: PASS - 55 touched file(s), all inside the declared scope (…)
scope-guard: exit 0 - PASS: every touched file is inside the declared scope
```

The script's note lists 20 declared globs that match no file in this repository (the `notebooks/…` paths, which live in project-notebooks, and misread prose words `No`, `The`, `_INDEX.md`, `framework/`, `checkpoints.md`); a warning, exit unchanged. The guard checks this repository only; the notebook repository is clean and committed (layer 2).

## 8. tests-bite — off

`uv run python C:/Users/mark/.claude/skills/proving-python-tests-bite/scripts/prove_tests_bite.py --check --base 7b66e2a92fc2cfa3892050f143bd35fe0e6bd40d`, exit 4:

```
tests-bite layer: OFF - mutation testing is on demand in this project (.claude/do-code-change.json: decided by Mark, 2026-11-20); no pass runs with each change (exit 4)
VERDICT: OFF
```

A recorded standing decision (Mark, `checkpoints.md`, 04:29Z), not a FAIL. The hand mutation pass in implement-log.md (92 mutants, 89 killed, 3 equivalent) is extra evidence only.

---

Not checked or only partly read: the paid skill suite was not re-run (instructed); notebook resolve and lint runs (steps 6 to 8, 13 to 16) were not repeated, only their recorded evidence and git state read; `test_cycle_script_fixes`, `test_drive_access` and `test_fetch_page` were read by exit code, last line and FAIL lines only; the sweep of the other `tests/scripts/` suites was read by exit code, last line and FAIL lines.

VERDICT: FAIL — findings-addressed, coverage
