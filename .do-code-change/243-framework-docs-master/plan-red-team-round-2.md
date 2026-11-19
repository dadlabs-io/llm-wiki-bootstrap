## Red-team round 2: 243-framework-docs-master (revised plan: `wiki/best-practices/{framework,local}`, practice-page links, notebook moves and repoints)

Written by the orchestrator from the red-team's report (a fresh `architect` instance running `strategy-red-team`, one `red-team-reviewer` on haiku, 37 of 40 reads); `readonly-guard.py check --step red-team` exited 0 (694 files compared, HEAD unchanged) before this file was written. Round 1 is `plan-red-team-round-1.md`. "Verified" = re-checked against the code by the red-team; "reviewer-cited" = not re-read.

### Kill-assumptions (ranked)

1. **Claim:** Phase B copies `seed/best-practices-local/README.md` on every run via `_copy_tree(names=…)`, restoring the shipped bytes over an edited README (step 3).
   **Fails if:** `_copy_tree` skips a destination whose mtime is at or after the source's (`scripts/new-wiki.py:316-318`, verified), so an edited README is never restored; the toolset side compares bytes (`_install_tooling.py:188`), so only Phase B is affected. Second break (reviewer-cited, `new-wiki.py:1064-1070`, `_render_template` `skip_if_exists=False`): Phase B re-renders `README.md`, `HOME.md`, `_MAP.md` on every run, and adding `best-practices` to `WIKI_FOLDERS` changes the rendered README, so "a re-run adds only the local README" fails on a populated wiki.
   **Evidence to get now:** edit the README in a temp wiki, run Phase B, compare bytes; Phase B over a populated wiki without `best-practices/`, diff names and bytes.
   **Kill criterion:** shipped bytes not restored, or the diff shows any file besides the new README.
   **Cheapest test:** the two runs, as step 3's first tests.
   **Fix class:** plan error for the copy (take the byte-comparing write as the primary route). Choice for Mark on the re-render: state that a re-run also re-renders README/HOME/_MAP, or render those only when the wiki is new.

2. **Claim:** the global install removes the old `wiki/project/best-practices/framework/*.md` so nothing is in two places; existing wikis are retrofitted later.
   **Fails if:** consumers installed or rendered before the change still name the old path: (a) eight project CLAUDE.md files rendered from `templates/CLAUDE.md.tmpl:94,164` with `skip_if_exists=True` (investment-agent, spotify-app, soundboard-app, soundboard-app-api, sudoku-app-api, workflows-core, the equal-experts project, llm-wiki-bootstrap's own; verified by grep); line 94 names the old path as the authority for the frontmatter spec; (b) rpg-strategist's project-level skills (7 files; out of scope per Mark's memory, noted only); (c) `--phase docs` runs only `seed_toolset` (reviewer-cited), so on a machine whose installed skills still name the old path it removes what they read; (d) the install writes skills at steps 2-3 and the toolset at step 7 (`_install_tooling.py:770`, verified), so a failure in steps 4-6 leaves new skills with an old toolset (reported by `InstallIncomplete`, not repaired).
   **Evidence to get now:** `--phase docs` alone on the changed tree, then resolve one `{{TOOLSET_DIR}}` link from an installed skill; grep every `CLAUDE.md` under `C:\github.com`.
   **Kill criterion:** a live consumer on this machine resolves to a deleted path.
   **Fix class:** choice for Mark: (a) remove now and accept dead lines in ~8 CLAUDE.md files until the retrofit card; (b) keep the old copy until the retrofit card; (c) add the CLAUDE.md line fix to the retrofit card and say so in the plan.

3. **Claim:** the repoint lists are complete (63 occurrences in 34 repo files; 19 live pages; 128 links in 84 agentic-design files).
   **Fails if:** live pages outside both lists link the old toolset path: a notebook grep outside agentic-design found 37 matches in 25 files, including llm-wiki-bootstrap `project/architecture/00-system-overview.md`, `20-ingesting-a-source.md`, `50-quality-and-promotion.md`, `best-practices/wiki-authoring-where-we-stand.md`, `memory-architecture-where-we-stand.md` and several decisions; also `agent-builder-bootstrap/CLAUDE.md`, `cottage-build/wiki/project/best-practices/README.md` (4), the soundboard-app and spotify-app READMEs. A broader count (any `best-practices/framework/` mention outside agentic-design) was 79 files, unclassified.
   **Evidence to get now:** resolve every `global-toolset/wiki/project/best-practices/framework/` link across the notebooks, split into live pages, records, machine files.
   **Fix class:** choice for Mark: widen the repoint to the live pages found, or list them for a later card. Plan error: Scope / Out of Scope must name the decision either way; agent-builder's CLAUDE.md stays out (Exclusions), listed not edited.

4. **Claim:** step 2's "`local` exists as a plain file → the refresh does not raise ... still refreshes every other file"; step 1 "No new function".
   **Fails if:** `seed_toolset`'s `mkdir(..., exist_ok=True)` and `shutil.copyfile` (`_install_tooling.py:230-231`, verified) raise on a plain file and stop the loop; `unlink()` (`:233`) raises on a held file on Windows after earlier copies ran.
   **Cheapest test:** a temp toolset with a plain file at `wiki/best-practices/local`, then `seed_toolset`.
   **Fix class:** plan error: a per-file guard with a reported result in step 2; drop "No new function".

5. **Claim:** step 4's scan check vs step 10's conditional `V2_ROADMAP.md` edit; requirements' "the 2026-10-05 decision still holds".
   **Fails if:** `V2_ROADMAP.md:56` names the old path, so the scan fails or step 10's condition is moot (reviewer-cited). The 2026-10-05 global-toolset decision states the docs live at `wiki/project/best-practices/framework/` (its line 29, verified), which the path change reverses; only the 2026-11-13 decision is superseded.
   **Fix class:** plan error: V2_ROADMAP edited in step 4's sweep; a one-line "layout moved by #243" note on the 10-05 decision under step 13 (or superseded, if Mark prefers).

6. **Claim:** trivial-stakes proposals (step 9 "no", steps 5 and 8 "yes").
   **Fails if (step 9, reviewer-cited):** `wiki-update.py:1269` `tier_rubric_text` returns only the span from `### Tier rubric` to `### Review cadence` (doc lines 103-138); a rule placed after it is never shown to ingest. **Fails if (step 5):** applied while the plan's Decisions needed 1 is open (Mark's "settle conventions before applying"); folding the seven decisions' reasons into practice text falls under "entries say only what the source says". **Holds:** step 8 "yes" (no script reads `framework-version`; floors updated).
   **Fix class:** plan error: step 9 states where the rules land and tests that `tier_rubric_text()` holds both. Choices for Mark: Decisions needed 1; the trivial-stakes "yes" on steps 5 and 10 (the template line is read by every new project's agents).

7. **Claim:** step 4's file list and Scope cover every test and guard naming the path; step 3's lint invariant.
   **Fails if (reviewer-cited):** `tests/skills/new-wiki/check.py:368-372` asserts no docs are copied to `wiki/project/best-practices/framework` (a guard on a path that can no longer hold a copy; outside the plan's test Scope). A user note without frontmatter in a wiki's `best-practices/local/` is linted as an entry (`wiki-lint-mechanical.py:189-195` skips only `_INDEX`, `_MAP`, `_inbox`, `sessions`, `tasks`). `wiki-qmd-query.py:773` indexes only `research` and `project`, so `best-practices/local/` notes are never searched.
   **Fix class:** plan error: `tests/skills/new-wiki/check.py` into Scope (red-then-green per the repo's tests/skills rule). Choices for Mark: exempt `best-practices/local/` user files from the entry checks; whether search indexes it.

### What holds up
- Counts re-counted: 63 occurrences in 34 files for the old path; 83 files for `architecture-decisions`; 128 in 84 confirmed by the reviewer; the class split sums to 83 with `231-split-plan.md` counted as a journal.
- The dry-run: `seed_toolset` builds `status` before the early return (`_install_tooling.py:221,225-226`), so the README appears in a dry run with no new key.
- `local/` is safe from every code path found: no `"local"` in `scripts/`; the manifest records scripts, skills, agents, hooks only; uninstall does not reach the toolset (reviewer-cited `_install_tooling.py:779-792,939-978`); the remove scan covers only the pack folders and the planned old folder.
- Taxonomy and lint accept a new top-level folder: `wiki-map-compile.py:378-386` maps only direct `.md` children of non-container folders; `SYSTEM_STEMS` exempts `README` from body checks (`_entry_checks.py:63`); no lint folder list rejects it.
- `framework-contract: true` pages stay exempt from body checks.
- Link depth: four `../` reaches `notebooks/` from the new toolset folder; wiki-authoring line 221's llm-wiki link drops from five to four. `_cycle_common.py:158` and `tests/skills/wiki-cycle/check.py:1124` read the project's own canon, so leaving them is right.
- agent-builder: no `best-practices/framework` hit in its repo.
- Round 1's findings are fixed in the steps (README frontmatter and lint test, dry-run placement, `pool.json` out with a reason, counts and class split, `Failures:` lines, step 11's anchors and `.obsidian`), except attacks 4 and 5 above.

### Could not assess
- no standing rule found: `pool.json` and `tests/search/.results/` out of scope (frozen question set).
- no standing rule found: journals, archives and reports left as records (Mark's Choice 2 decides it).
- no standing rule found: existing wikis keep the old layout (Mark's Choice 3).
- no standing rule found: `_cycle_common.py:158` and `tests/skills/wiki-cycle/check.py:1124` left alone.
- no standing rule found: rerank spec "Practice page: none".
- no standing rule found: the moved decision record "not shipped, no local file".
- no standing rule found: agentic-design's own folder not moved (Decisions needed 1 open).
- The old toolset copy removed: "No dead code or retired skills" supports it; attack 2 sets the cost beside it.
- `CONSTRAINTS.md` does not exist.
- Not read or not run: step 11's real anchors; Windows unlink and rmdir under a held file; whether an exception in install steps 4-6 is caught before step 7; where the install places `framework-docs/` for the `wiki-update.py:1265` fallback; `40-search-and-indexing.md`; classification of the 79 other-notebook matches; the full per-class split of the 128 links.

VERDICT: KILL-ASSUMPTIONS FOUND
