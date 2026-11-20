# Implement log — 243-framework-docs-master

One block per step, written by the orchestrator from the developer's hand-back and its own re-run.

## Step 1 — 2026-11-19
- Developer hand-back: green; orchestrator re-run `uv run python tests/scripts/test_global_toolset.py` → `50/50 passed`. Other suites the developer ran, all exit 0: test_tooling_state_seam 23/23, test_install_manifest 21/21, test_refresh_prunes 11/11, test_install_incomplete 25/25, test_not_checked 23/23, test_html_markdown 13/13, test_standalone 21/21.
- Changed: `scripts/_install_tooling.py`, `scripts/_wiki_config.py`, `scripts/new-wiki.py`, `scripts/wiki-update.py`, `agents/wiki-ingester/wiki-ingester-reading-list.json`, `tests/scripts/test_global_toolset.py`.
- Taken early from step 5: the reading list's 4 old-path links. The plan's own Invariant says the reading-list check moves to the new path in step 1, and that check can only pass if the file moves too. Step 5's sweep will find nothing left in that file.
- Plan correction (callers of `seed_toolset`'s dict): `phase_docs`, plus `_install_tooling_steps` → `install_tooling()` → `print_summary` (called by the global install in `new-wiki.py` and by `wiki-upgrade.py:68`). `--mode status` reads `toolset_status`, not the dict. Both are covered by tests.
- Accepted trade-off (doubt-log): the old copy is unlinked even when the new copy's write failed. A doc can then exist at neither path until the next refresh, whose status reports the add. This follows the plan's "all removals and copies still run".
- Not guarded, outside the plan's Failures: reads, `glob` and `iterdir`. An unreadable file can raise out of `seed_toolset`.
- `TOOLSET_LOCAL_DIR` deferred to step 2. Old-path comments and docstrings are left for step 5's sweep.
- Grep for `agentic-design` over `scripts/`: 38 occurrences in 16 files, the same as before the change (Invariant holds).
- Python pack (step 1): `gating-python-changes` is red at gate 1 (ruff format/check on the 5 changed files). The repo has no ruff config and the errors read were pre-existing; the repo is off the python baseline (`scaffolding-python-projects --check` 4/14). Not a workflow gate here (no signed `step_gates`), so it is parked.

## Step 2 — 2026-11-19
- Developer hand-back: green after Mark's "yes" (21:25Z) to update step 1's frozen `test_write_failure_is_listed_failed_rest_refreshed`. It now expects the six docs plus `local/README.md` in `failed`, and the "rest still written" filter skips `wiki/best-practices/`. Re-frozen with the unfrozen and green reasons. check-freeze: PASS, 27 entries plus 164 from earlier changes.
- Orchestrator re-run: `test_global_toolset.py` → `80/80 passed`; `test_standalone.py` → `21/21 passed`.
- Changed: `scripts/_wiki_config.py` (`TOOLSET_LOCAL_DIR`), `scripts/_install_tooling.py` (`toolset_files()` lists `local/README.md`), new `seed/best-practices-local/README.md`, `tests/scripts/test_global_toolset.py` (13 new tests).
- Deviation from the plan: "README held open on Windows" is tested with a read-only file instead. A Python open handle does not block `copyfile`, so it cannot make the write fail.

## Step 3 — 2026-11-19 (hand-back 1, not green)
- Built: `taxonomy_for` appends `best-practices/local` before `sessions` for all nine pairs; `new-wiki.py` adds the missing-source guard before B1, the `folder_notes` row `best-practices/local`, and the README render at the end of B6.5. Tests in new `tests/scripts/test_local_folder.py`: 12/13 pass. Also green: global_toolset 80/80, standalone 21/21, tooling_state_seam 23/23, git_hooks_optin 17/17. check-freeze PASS (39 entries).
- Red: the plan's "lint reports no finding from `best-practices/`" premise is false. The lint names the README for: orphan (no `standalone:`), missing confidence, missing last_reviewed/review_after. A fresh scaffold's HOME.md and README.md already draw the confidence and lifecycle findings. Put to Mark on Discord with a recommendation (parity with HOME.md).
- Plan corrections: `.claude/wiki-config.json`'s `wiki_folders` holds the two answers, not the folder list; the folder list is Phase B's stdout JSON `wiki_folders` (tested). The `folder_notes` key is `best-practices/local`.
- Folder-guard findings, listed and not fixed:
  - `wiki-update.py` `validate_folder`: a bare `--folder best-practices` in a new wiki now passes Case 1 (its top segment exists on disk) and files into `wiki/best-practices/`; it was refused as ambiguous before.
  - `MERGED_TAXONOMY` lacks `best-practices/local`, and the `SCAFFOLD_TAXONOMY` comment is stale.
  - `wiki-map-compile.py:378` `CONTAINER_FOLDERS = {"research","project"}`: `local/` notes never reach `_MAP.md`.

## Step 3 — hand-back 2, green
- Mark's decision (21:44Z) applied. The README gains `confidence: high` and `standalone: "the folder's guide: nothing links to it by design"`, with no lifecycle dates. The lint test is now `test_lint_of_a_fresh_scaffold_draws_no_finding_on_the_local_readme_that_home_does_not` (the README's finding kinds must be a subset of HOME.md's). It was re-frozen and the old name retired.
- Orchestrator re-run: test_local_folder 13/13, test_global_toolset 80/80. The developer also reports standalone 21/21 and check-freeze PASS (40 entries plus 164 earlier).
- Limit: the parity test has not been seen failing on a README with an extra finding. Its bite rests on the earlier 12/13 red against the old README.

## Step 4 manual evidence

(a) `qmd collection list` on the machine's real collections (read-only; no collection was added, edited or removed). Every collection, the llm-wiki-bootstrap one included, carries the pattern `**/*.md` over the notebook's whole `wiki/` folder, which covers `best-practices/` and `best-practices/local/`:

```
C:\github.com\project-notebooks\notebooks\llm-wiki-bootstrap\wiki (qmd://C:\github.com\project-notebooks\notebooks\llm-wiki-bootstrap\wiki/)
  Pattern:  **/*.md
  Files:    564
  Updated:  16h ago
```
(the same `Pattern:  **/*.md` line for agentic-design, 1731 files, and for all eight others; 10 collections before and after the temp run below)

(b) One keyword search (`qmd search`, no model, no GPU) over a temp named index `tmp243step4` holding one collection `tmp243step4` over a temp folder (`<scratchpad>\qmdtmp\wiki`) with a note at `best-practices/local/my-notes.md`:

```
> qmd --index tmp243step4 collection add <scratchpad>/qmdtmp/wiki --name tmp243step4
Collection: <scratchpad>\qmdtmp\wiki (**/*.md)
Indexed: 1 new, 0 updated, 0 unchanged, 0 removed
> qmd --index tmp243step4 search zephyrquartz
qmd://tmp243step4/best-practices/local/my-notes.md?index=tmp243step4:2 #de6d37
Title: Zephyrquartz local best practice note
Score:   0%
```
Cleanup: `qmd --index tmp243step4 collection remove tmp243step4` printed `Removed collection 'tmp243step4'`; the temp index file `~/.cache/qmd/tmp243step4.sqlite` (created by the `--index` name) was then deleted; `qmd collection list` afterwards again shows the same 10 real collections.

Plan notes for this step: `skills/wiki-search/SKILL.md` and its wiki-seed page hold no searched-folders line naming only `research/` and `project/` (grep over `skills/wiki-search`; the only `research/`/`project/` mentions are an agentic-design path in a source note and the `project/` entry the skill offers to file), so no skill text changed. `40-search-and-indexing.md`'s depth-check line is the finish step's wiki record (Out of Scope).

## Step 4 — 2026-11-19, green
- `sample_titles` halves gain `best-practices`. Tests: 4 in test_search_mode (82/82), 3 lint tests in test_local_folder (16/16); orchestrator re-ran both. The `drop_machine_files` and lint tests were already green, so they are coverage tests, frozen green with reasons; their bite was shown by transient mutations, reverted (the lint mutation on a scratch copy). check-freeze PASS (47 entries).
- The wiki-search skill text has no searched-folders line naming only research/ and project/, so it is unchanged.
- The manual evidence is above (qmd pattern `**/*.md` on all 10 collections; a temp-index keyword search found `best-practices/local/my-notes.md`; the temp index was removed). The plan says checkpoints.md; it lives here, and checkpoints.md points here.

## Step 5 — 2026-11-19, green
- Scan test `test_no_shipped_file_names_the_old_toolset_framework_path` in test_standalone: red 21/22 (47 hits), green 22/22 (orchestrator re-ran). 47 hits rewritten in 33 files: root docs, 11 SKILL.md, wiki-cycle reference, 5 skill wiki-seed pages, 2 templates, the global-toolset README seed, 2 wiki-seed pages, the frontmatter doc, and comments/docstrings in 3 scripts. Also test_link_gaps' fixture.
- Orchestrator grep afterwards (excluding .do-code-change, tests/search, archive): only CHANGELOG history, the step-1 `OLD_DIR` fixture, the scan test's own constant, and PENDING.md:65 (a record).
- Frontmatter gate over the 11 changed skills: 11/11 parse, 0 would be refused.
- Plan corrections: CLAUDE.md:172 held no old path. The template's project-canon line is now at line 51.
- Departure: the developer read only the edited regions of new-wiki.py, wiki-update.py, _install_tooling.py and the frontmatter doc (one-token path edits at grep-located lines), not those files whole.

## Step 6 — manual evidence
Written by the developer, 2026-11-19. No test (Trivial stakes: yes). Nothing committed in either repo.

Pages (all new, in `C:\github.com\project-notebooks\notebooks\agentic-design\wiki\research\wiki\`):
- `wiki-best-practices.md` (hub), `wiki-best-practices-authoring.md`, `wiki-best-practices-frontmatter-and-tiers.md`, `wiki-best-practices-context-loading.md`.

Conventions noted (read first):
- agentic-design has no CLAUDE.md or README at the notebook root; its entry frontmatter spec is the toolset's frontmatter doc (read whole): required `title, date, source_url, ingested_by, tier, confidence, last_reviewed, review_after, tags (3+)`; a self-authored entry is `tier: self`, `source_url: internal://synthesis/<date>-<slug>`, no `raw_path`, review_after +3 months. Body checks (even at `self`): `## TL;DR`, `## Related` with 2+ wiki links, numbers on `>` lines (so the pages carry no digits in prose; figures are pointed at in their entries).
- Every research topic folder holds `_INDEX.md` (all nine: active, agents, best-practices, implementation, interesting-docs, long-term, orchestration, skills, tooling), each headed "AUTO-GENERATED by wiki-index-per-folder.py, do not hand-edit"; four also hold a hand-written `README.md` (folder purpose). The root `_INDEX.md` is auto-generated by `wiki-index.py`. `wiki-index-per-folder.py` takes `--topic` only (no single-folder option), so running it would rewrite every folder's index: not run. `research/wiki/_INDEX.md` is left to step 15, which already owns it.
- A new topic folder is registered only through those generated indexes plus the hub/HOME pointer; no registry entry is needed.
- Partial reads, stated: the root `_INDEX.md` was read to line 80, `skills/_INDEX.md` to line 154 of 208, and `implementation/_INDEX.md` not at all (the read-guard blocked a limited read). Only their header and convention lines were used; no claim rests on the unread parts.

Existing wiki research entries (the grep): Grep of `^title:.*(LLM Wiki|llm-wiki|[Ww]iki|Karpathy.*(pattern|gist)|knowledge base|Memex)` (case-insensitive) over `agentic-design/wiki/research` found about 45 entry titles in active, best-practices, implementation, long-term, orchestration, skills and tooling. The hub lists 27 entries in four groups (the pattern and lineage, production extensions and implementations, walkthroughs and surveys, forgetting and confidence; one of them is the pre-mortem under `project/architecture/`), plus the memory page `project/best-practices/memory-architecture-best-practices.md` in its own section; entries matching "wiki" only as a product name or as Instagram-reel roundups were not linked. Entries named in the source docs' `(agentic-design :: ...)` pointers were confirmed with `ls` and linked from the practice pages.

Lint (`wiki-lint-mechanical.py --topic agentic-design`; outputs saved in the session scratchpad as `lint-before.txt` and `lint-after.txt`):
- Before: files scanned 1718; broken links 0; orphans 0; missing frontmatter 0; body checks hard 192, warnings-only 781; backlink blocks out of step 5 pages (missing 20).
- After: files scanned 1722; broken links 4; orphans 0; missing frontmatter 0; body checks hard 192, warnings-only 782; backlink blocks out of step 46 pages (missing 83).
- The 4 broken links are the required link to `./lessons-from-llm-wiki/README.md` (one per page), which step 7 creates. Expected and transient.
- Backlink blocks, 5 to 46 pages: my pages link to existing entries that lack the reciprocal backlink; the backlink rebuild (`wiki-reciprocate-backlinks.py`, run by the cycle) clears it. Not run here, since it edits other entries.
- Warnings-only 781 to 782: none of my pages appears in the body-check sections (a grep of the report for `wiki-best-practices` finds only the broken-link and backlink sections), so the extra warning belongs to another file; the notebook is live (1722 files against 1718).
- Side effect of the lint the brief asked for: it rewrote `notebooks/agentic-design/_inbox/reports/lint-report.md` (mtime 17:06, my first run; the second run wrote it again). Not mine to commit; not reverted, since another session may hold an earlier change in it. `.obsidian/workspace.json` also shows modified in `git status`; not mine.

No-llm-wiki proof (Grep over the four pages): the pattern `llm-wiki-bootstrap|global-toolset|framework-docs|best-practices/framework|architecture-decisions|llm-wiki ::` has exactly one hit, `wiki-best-practices.md:60`, the link target of the existing agentic-design entry `karpathy-llm-wiki-bootstrap-skill-nanzhipro-...md` (a third party's skill, not the llm-wiki-bootstrap notebook or repo). Every other link target containing "llm-wiki" is an existing agentic-design entry slug (`karpathy-s-llm-wiki-pattern`, `llm-wiki-v2-...`, and so on) or `./lessons-from-llm-wiki/` (the folder the plan names). No `(llm-wiki-bootstrap :: ...)` pointer was carried over, and the hyphenated architecture-decisions slug appears 0 times (the decisions are cited in prose as "the seven architecture decisions"). llm-wiki is named in prose only in the flow statement and the lessons pointers.

Ideas left out because they need build detail (none written as llm-wiki detail):
- authoring: the ten-agent roster with skill names; the unattended `--no-confirm-discovery` exception; enforcement names (`_entry_checks.py`, `wiki-list-add.py`, the Drive fetcher dedup, `/wiki-claims`); the JSON skeleton, per-step summary keys and run-folder layout of the cycle-step doc (only its checkpoint ideas kept); the default folders per page kind and the mapping of Asel's layers to llm-wiki folders; the status notes on decisions 2, 4 and 6; llm-wiki incident counts (the 22 of 26 rejected URLs, the 91% and 189-behaviour check, the 4 of 10 injection runs, the Ruflo deep dive).
- frontmatter: the optional `hub_tag` field (it needs the lint and the cycle that act on it), the exact enum values for `ingested_by` and `origin`, lint check lists and error codes, the example frontmatter blocks.
- context loading: the search helper's preflight, GPU-slot wait times, the "no cloud fallback, never switch to keyword mode" policy of the search decision (the decision gives no reason beyond the build), qmd version and file counts, the `/wiki-signals-decay` and `/wiki-verify` command names, the implementation-status table and the one-day estimate.
- The two mechanism docs get no practice page; the rerank spec added only the ranking order that the frontmatter doc itself states.

Decisions folded in (each page names the decision it adds): authoring adds markdown-not-SQLite, never-suppress-contradictions, two-human-checkpoints, federation and database-first-loop-later; frontmatter adds the tier-system decision; context loading adds grep-then-search. No reason was written that its source does not give; the two new tier rules carry no reason.

Plan inconsistencies: (1) the plan's `manual: step 6` measures lint "before step 6 and after step 15", while the brief asks for no new error from these pages now; the lessons link is a broken link until step 7, and the 41 new backlink-block findings clear only when the backlink rebuild runs. (2) Step 6 is silent on `_INDEX.md`; step 15 owns `research/wiki/_INDEX.md`, and every topic folder's index is generated, so none was written. (3) No page outside the folder links the hub until step 15's pointer; lint shows 0 orphans only because the three pages link back to it.

## Step 7 — manual evidence
Written by the developer, 2026-11-19. No test (Trivial stakes: yes). Nothing committed in either repo. The plan says checkpoints.md; per plan line 84 and step 6's practice it lives here.

File written: `C:\github.com\project-notebooks\notebooks\agentic-design\wiki\research\wiki\lessons-from-llm-wiki\README.md` (new). No lesson page, no edit to any step-6 page, no other file touched.

Per decision (read against the three practice pages; test: a departure only if what was built contradicts what the page says, a build that does more than the page asks is not one):
- tier system: no departure. The record links the rubric, which the frontmatter page now carries.
- federation of specialists: HELD FOR MARK (see below). Not listed as "no departure" in the README; listed there as "Open".
- never suppress contradictions: no departure. Page and record agree; the duplicate carve-out is about identical copies, not contradictions.
- database first, loop later: no departure. The record marks it satisfied.
- markdown not SQLite: no departure. Same three reasons and trade-off on the authoring page.
- two human checkpoints: no departure. The restated note says "exactly two" is too strong because a full run asks approval for more; the authoring page says keep two and do not soften, never "exactly two". More gates is not softening, so the page stands. The note gives no reason for the extra approvals either, so even on a departure reading it would be held, not a lesson.
- grep then search: no departure. The context loading page says when a search layer replaces the index; the build does that. The no-fallback / no-keyword-switch policy is a build rule the page makes no claim about; the record gives no design reason for it (step 6 already left it out for that).

Held for Mark: the federation decision. Practice (authoring page, "Federation of single-purpose agents"): agents with one job each, each isolatable ("if the gap finder breaks, the contradiction hunter still works"). Built, per the record's 2026-10-30 status note: skills plus two agents instead of six agents; contradiction detection is the claims skill plus the semantic lint, gap detection and tier audits are the semantic lint. The note says "not a reversal" and gives no reason. Not written as a lesson. When Mark gives the reason, one lesson page and a link from the authoring page follow.

Lint (`uv run --project <repo> python scripts/wiki-lint-mechanical.py --topic agentic-design`, output in scratchpad `lint-step7.txt`): Broken links 0 (was 4 after step 6); Orphan pages 0; spec enforcement all 0. The only findings naming the new folder are backlink-block "out of step" lines (README missing links to the three pages and the hub; 47 pages out of step, missing 91), the same kind as step 6, cleared by the backlink rebuild, not run here. No body-check finding names the new page.

No-llm-wiki grep over `lessons-from-llm-wiki/` for `llm-wiki-bootstrap|global-toolset|framework-docs|best-practices/framework|architecture-decisions|llm-wiki ::`: 0 matches. Link targets containing "llm-wiki": 0 (the folder name itself appears only in the page's own path).

Side effect: the lint rewrote `notebooks/agentic-design/_inbox/reports/lint-report.md` again; not mine, not reverted.

Plan inconsistencies:
1. The hub and all three practice pages say the lessons section "is being written" / "has nothing to open". Stale now that the README exists; the brief allows only a link-add edit, so left. Needs a one-line fix in step 15 or a later pass.
2. The practice pages already link the README, so "a practice page changed by a lesson links to the lesson" had nothing to add: no lesson, no edit.
3. Plan manual line says checkpoints.md; the evidence is here.
4. The README covers six of seven decisions as "no departure"; the seventh is open.

## Step 8 — manual evidence
Written by the developer, 2026-11-19. No test (Trivial stakes: yes). Nothing committed; the only staged change in project-notebooks is the `git mv`.

New path: `C:\github.com\project-notebooks\notebooks\llm-wiki-bootstrap\wiki\project\decisions\architecture-decisions-2026-04-10.md` (`git mv` from `notebooks/agentic-design/wiki/research/implementation/architecture-decisions.md`; git status shows `RM`). The old path no longer exists. Filename choice: that folder's pages are `<slug>-<date>.md`; the date is the page's original `date: 2026-04-10`. The target did not exist beforehand (Glob `architecture*` found none).

Counts (Grep of `architecture-decisions` over `notebooks/`, before any edit): 83 files, 181 occurrences (the plan says 180; the extra one is in card 243, edited by another session after the plan was written).
- left as records, 60 files, unchanged: agentic-design `_inbox/archive/**` 30, `_inbox/reports/**` 24, claims-index `.bak` 2, llm-wiki `sessions/**` 4 (three journals plus `231-split-plan.md`).
- machine files, 3, listed and not edited (below).
- live pages, 19: 14 in agentic-design, 3 llm-wiki pages, 2 task cards.
- the page itself, 1. 60 + 3 + 19 + 1 = 83.
After: the 60 records and 3 machine files unchanged (git status shows no `_inbox`, `sessions` or `_signals`/`_config` change from this step; `_inbox/reports/lint-report.md` and `.obsidian/workspace.json` were already modified by other sessions). Of the 19 live pages, 13 agentic-design files were edited (15 links); 6 were not edited (below). Grep of the old name (`architecture-decisions` not followed by `-`) in `wiki/` now: 13 occurrences in 11 files, all in the left/listed classes or prose (below).

Moved page, read against its rules: frontmatter keeps `tier: self`, `date: 2026-04-10`, `source_url`, `confidence`, `last_reviewed`, `review_after`; adds `category: decision`, tags `llm-wiki-bootstrap, decision` first; drops `raw_path: (none — self-authored)` (decision 2026-09-15: self-authored entries omit `raw_path`). No `origin` added (the old page had none; not invented). The page opens, under the title, with `## The flow this record belongs to` (agentic-design says how, llm-wiki builds and records why, a departure sends the lesson and reason back to the practice page; links to the hub and to the lessons README, depth `../../../../agentic-design/wiki/research/wiki/`). Body otherwise unchanged except link targets. All 25 relative links that changed were rewritten by script (relative to the new location; same targets); `## Related` was among them. The auto Backlinks block keeps its markers, heading and the "do not hand-edit" line; its three entries are removed (the one agentic-design page that linked it, getting-started, now links the record directly; the backlink tool rebuilds the block).

Resolve run (scratch `resolve.py`, path-exists plus anchor-heading check): moved page 30 links, 0 dead; each of the 13 edited agentic-design files, changed lines only, 0 dead (`_INDEX.md` 1, 3 architecture pages 1 each, chappy 1, implementation `_INDEX.md` 1, getting-started 2, karpathy 1, orchestration 2, anywhere-agents 3 lines, qmd 1, qmd-v2-5 2); 15 links repointed in all. The script's final loop crashed on an unrelated deleted file of another session after listing all of mine; nothing of mine was after it.

The 3 machine files, for Mark (not edited), matching lines:
- `notebooks/agentic-design/_config/drift-watch.md:21`: `| [`research/implementation/architecture-decisions.md`](../wiki/research/implementation/architecture-decisions.md) | Recent commits + bootstrap-sync state | Decisions referenced still in force; any reversed decisions noted |` (a drift-watch row; its link is now dead).
- `notebooks/agentic-design/_signals/architecture-decisions.json:2`: `"slug": "architecture-decisions",` (the page's signals sidecar; slug-keyed, now orphaned from its page).
- `notebooks/agentic-design/_inbox/claims-index.json`, 14 lines: `"source_entry": "implementation/architecture-decisions.md"` at lines 23457, 23468, 23479, 23490 (the claim at 23456 reads "...as of the architecture-decisions doc"), and `"source_entry": "research/implementation/architecture-decisions.md"` at lines 67966, 67978, 67990, 68002, 68014, 97281, 97296, 97311, 97326.

Not edited, listed for the orchestrator:
1. The 3 llm-wiki live pages (the 2026-09-25 decision line 41, the 2026-11-13 decision line 31, troubleshooting line 60) and cards 231 (lines 16, 40) and 243 (lines 7, 16) name the page in prose (`architecture-decisions.md`, "the architecture-decisions page") with no link; there is no link target to repoint. Card 243 not edited per the brief; card 231 also left, since the hits are rough-note prose, not links. The 2026-11-13 decision is step 16's.
2. agentic-design root `_INDEX.md:471`, a generated tree line `├── architecture-decisions.md` under `implementation/`: not a link; the indexer drops it on its next run (step 15).
3. `moe-foundry-...-ruv-cohen.md:58` names `docs/architecture-decisions.md` in the third-party `ruvnet/MoE-Foundry` repo: not our page, not repointed.
4. The moved page's line 26 still links the toolset's old layout `global-toolset/wiki/project/best-practices/framework/wiki-frontmatter-best-practices.md#tier-rubric` (the new `wiki/best-practices/framework/` does not exist in the toolset until the install). It resolves today; step 14 repoints it.
5. The remaining `source_url: internal://synthesis/2026-04-10-architecture-decisions` in the moved page is an identifier, kept.

Plan inconsistencies:
1. The plan counts the 19 live pages as links to repoint; only 13 agentic-design files carry link targets. The 3 llm-wiki pages and 2 cards hold prose, and `moe-foundry` (counted among the 9 research files) is a false positive. So 13 files, not 19.
2. Decision 2 says agentic-design pages are repointed "to the practice pages (Decision 5)"; step 8 says "to its new place". Followed step 8 as the brief says. The 15 repointed agentic-design links now point INTO llm-wiki, against Mark's "agentic-design does not link to llm-wiki". Orchestrator to decide per link; each is an `## Related` list entry or a see-also (`anywhere-agents-yzhao.md:59` is an inline link whose text is "settings.json hook usage").
3. 181 occurrences, not 180 (card 243).
4. The plan's `manual: step 8` says evidence goes to `checkpoints.md`; it is here, as for steps 4, 6 and 7.

## Step 8 — repoint to the hub (Mark 23:12Z)
Mark, Discord 2026-11-19 23:12Z: "LLM-WIKI might point and AgentiucDEsign, but Agentic_Degsign does NOT poiunt at LKLM wiki. If its important, it goes in Agentic-Desgign". Nothing committed.
- 13 links in 11 agentic-design files repointed from the llm-wiki record to `wiki/research/wiki/wiki-best-practices.md` (relative per file; link text and prose untouched): the 3 `project/architecture/` pages, chappy-asel, getting-started (2), karpathy, the 2 orchestration pages, anywhere-agents-yzhao (line 59; no practice page covers hook usage, so the hub), the qmd page, qmd-v2-5 (2).
- The two generated indexes, `_INDEX.md` (root) and `wiki/research/implementation/_INDEX.md`: my one-line edit was each file's only change, so both were restored with `git checkout`. They again list the old path; the indexer drops the entry on its next run (step 15).
- Resolve (`resolve2.py`): 13 links to the hub, 0 dead.
- Grep for `architecture-decisions-2026-04-10` over all of agentic-design: 0 matches. A grep for any link to `llm-wiki-bootstrap` under agentic-design `wiki/` still finds 85 occurrences in 70 files; those existed before this step (other pages, including 5 of the 11 files above, outside the framework docs; out of this change per the plan's Exclusions) and are not touched.

## Step 9 — manual evidence
Written by the developer, 2026-11-19. Trivial stakes: yes (no mutation pass). Nothing committed.

(a) Resolve run: `uv run python <scratchpad>/resolve_step9.py C:/github.com/llm-wiki-bootstrap/framework-docs C:/github.com/project-notebooks/notebooks/global-toolset/wiki/best-practices/framework` (each `Practice page:` link and the where-we-stand link, joined by path arithmetic onto the toolset root, which does not exist yet; the target file is then checked):
```
OK   cycle-step-return-format.md: ../../../../agentic-design/wiki/research/wiki/wiki-best-practices-authoring.md -> ...\notebooks\agentic-design\wiki\research\wiki\wiki-best-practices-authoring.md
OK   memory-signals-sidecar-vs-frontmatter-pattern.md: ../../../../agentic-design/wiki/research/wiki/wiki-best-practices-context-loading.md -> (same folder)
OK   tiered-context-loading.md: ../../../../agentic-design/wiki/research/wiki/wiki-best-practices-context-loading.md -> (same folder)
OK   wiki-authoring-best-practices.md: ../../../../agentic-design/wiki/research/wiki/wiki-best-practices-authoring.md -> (same folder)
OK   wiki-authoring-best-practices.md: ../../../../llm-wiki-bootstrap/wiki/project/best-practices/wiki-authoring-where-we-stand.md -> ...\notebooks\llm-wiki-bootstrap\wiki\project\best-practices\wiki-authoring-where-we-stand.md
OK   wiki-frontmatter-best-practices.md: ../../../../agentic-design/wiki/research/wiki/wiki-best-practices-frontmatter-and-tiers.md -> (same folder)
wiki-search-bucket-rerank-spec.md: Practice page: none
dead: 0
```
(b) Mechanical lint (`wiki-lint-mechanical.py`, scratch `lint_step9.py`, the test_standalone harness with the fake qmd): a temp notebook `t` holding the six docs at `wiki/best-practices/framework/` plus a HOME, with stub files at `<tmp>/notebooks/agentic-design/wiki/research/wiki/<page>.md` and the llm-wiki-bootstrap page, so the links are at the real depth. Exit 0; summary: files_scanned 7, broken_links 1, orphans 0, missing_frontmatter 0, missing_tier 0, missing_confidence 0, unquoted_yaml 0, backlink_blocks_out_of_step 6. The one broken link: `wiki-frontmatter-best-practices.md` -> `old-slug.md` (link text "old title"), an example sentence in the doc's "On retirement" bullet, present before step 9. A first run without the stubs showed the six practice links and the where-we-stand link as broken (7 broken_links), as expected for a bare temp tree; with the stubs they resolve, which proves the depth. The six backlink-block findings (not investigated further) name docs whose backlink blocks are missing links to their siblings, as in any wiki without the backlink rebuild.

Step 9 result: `test_standalone.py` red 20/27 first (7 FAIL: the two raised floors and the five new tests), green 27/27 after. test_global_toolset 80/80. check-freeze over the project record: PASS. Name review: see name-review.md (three renames, one strengthened).

Other relative links in the six docs, at the new depth:
- sibling `./<doc>.md` links in all six docs: unchanged, resolve in the same folder.
- `./wiki-frontmatter-best-practices.md#tier-rubric` (authoring principle 7; the frontmatter doc's heading is `### tier rubric`): ok.
- in-page anchors of the frontmatter doc: `#source_url-conventions`, `#tier-rubric`, `#review-cadence` (line 34) and `#review-cadence-default-review_after-offset` (line 60). The heading is "review cadence (default `review_after` offset)", so `#review-cadence` does not match it; it predates step 9, listed not fixed.
- external https links (Karpathy, Asel, Bush, rohitg00, lucasastorian, SamurAIGPT, yzhao062): unchanged, not depth dependent.
- `(agentic-design :: ...)` and `(llm-wiki-bootstrap :: ...)` pointers: plain text, not links.
- `../active/newer-revising-entry-2026.md` in the memory-signals JSON example: example data.
- the wiki-authoring where-we-stand link: five `../` -> four, resolves (above).

Plan inconsistencies: (1) the plan's Implementation Decisions line for the Local changes sentence omits the `Local changes: ` label that requirements Decision 3 has; the label is used. (2) The plan names no test names for step 9; three were renamed after name review (listed in name-review.md).

## Step 10 — 2026-11-19, green
- Frontmatter doc: the vendor-post rule sits under the posts table, inside the span `tier_rubric_text()` returns. The repository Tier 3 cell carries the reading rule, ending "ask the user" (generic for a shipped doc). New `status` and `cycle_id` rows; the `origin` row says who stamps it. The broken `#review-cadence` anchor is fixed. Added beyond the plan, so the doc does not contradict itself: the top table's Tier 2 row and the posts table's Tier 2 cell point at the vendor-post rule. No version bump (step 9 did it).
- 8 new tests in test_standalone. Orchestrator re-run: 35/35. The developer reports test_global_toolset 80/80, test_html_markdown 13/13, test_dedup_content 15/15, and check-freeze PASS (65 entries).
- Reader grep: only `tier_rubric_text()` reads the rubric (it cuts the span by the two headings, still in place). Nothing parses the cell text.
- cycle_id re-grep: nothing writes it into an entry; it appears only as the run id. The lint names it as the place for cycle provenance.
- Plan correction: the rubric headings are lower case (`### tier rubric`), and the span is now about lines 107-143.

## Step 11 — manual evidence
Written by the developer, 2026-11-19. No test (Trivial stakes: yes). Nothing committed. Tests: `test_standalone.py` 35/35 passed (step 5's old-path scan passes); `test_global_toolset.py` 80/80 passed. No `tests/skills/*/cases.json` opened; `templates/CLAUDE.md.tmpl` untouched.

Lines added, per doc (quoted; "read" = against steps 1-3: folder `wiki/best-practices/{framework,local}/`; the toolset README replaced on refresh; user files never added, changed or removed; read order wiki local, then toolset local, then the framework doc):
- `CLAUDE.md` (framework-docs bullet): "A user's own changes never go in these docs: they go in `wiki/best-practices/local/` (the toolset's, or a wiki's own), and `seed/best-practices-local/README.md` is the one text that says how; each doc's "Local changes" line says in what order they are read". Seed bullet: "and the README that starts each `wiki/best-practices/local/` folder, in a new wiki and in the toolset (`seed/best-practices-local/`)". Read: right folder, both places, points to the README and the line, copies neither.
- `INSTALL-INVENTORY.md`: A4: "A user's own changes go in a `wiki/best-practices/local/` folder (the toolset's, or a wiki's own) instead; its README (`seed/best-practices-local/README.md`, section C) says how, and each doc's "Local changes" line says in what order the files are read." New section C row for `seed/best-practices-local/README.md` (rendered into every new wiki whatever `--project-folder` says; copied to the toolset as a listed framework file, replaced when it differs, counted toward stale; every other file in a `local/` folder never added, changed or removed). Taxonomy paragraph and section E: "`sessions/` and `best-practices/local/` always" and "`taxonomy_for()` appends both". Section G tree: `wiki/best-practices/local/` line, and "never edited by hand, except for the user's own files in `wiki/best-practices/local/`". Update mechanism: "the README in `wiki/best-practices/local/`". Read: matches step 2 (listed, replaced, counted) and step 3 (all nine answer pairs).
- `CHANGELOG.md`: new top entry `## 2026-11-19` (Why / What / Migration). Migration: "Existing wikis and other projects keep the old layout until task #248 retrofits them by hand". Older entries untouched. No re-run claim.
- `seed/how-to/_FRAMEWORK_MANAGED.md`: new section "Your own changes to the framework docs": "Your changes to them go in the toolset's `wiki/best-practices/local/`, where a refresh replaces only the README and never touches your files." Read: steps 1-2.
- `seed/global-toolset-README.md`: tree line `wiki/best-practices/local/ <- your own changes to those docs; its README says how it works`; "The one exception is `wiki/best-practices/local/`: a refresh replaces only its README and never adds, changes or removes any other file there."
- `wiki-seed/user-guide.md`: the "framework-managed" rule now ends "or put your own change in a `best-practices/local/` folder"; tree line `best-practices/local/`; a paragraph under The framework contracts: the wiki's own folder for that wiki, the toolset's for every wiki on the machine, a new wiki starts with the folder and README, each doc opens with a "Local changes" line. Read: order (wiki then toolset) is stated by pointing to the line, not copied.
- `skills/new-wiki/SKILL.md`: tree line `best-practices/local/ <- always: README only`; plan summary `Folders:` gains `wiki/best-practices/local/`; "Both halves are opt-in" note now says `sessions/` and `best-practices/local/` are created. `skills/new-wiki/wiki-seed/new-wiki.md`: "Whatever you choose for the two halves, a new wiki also gets `best-practices/local/` with one README in it". Nothing about a re-run.

One-source check (Grep over the edited docs, case-insensitive, for the README's and the Decision 3 line's phrases: "do not edit this README", "replaced on update", "Read them after this doc", "where they differ, the wiki's local file wins", "name a file after the framework doc", "When unsure which, ask the user", "put your changes in files beside"): No matches found. Grep for `project/best-practices/framework` over CLAUDE.md, INSTALL-INVENTORY.md, seed/, wiki-seed/user-guide.md, skills/new-wiki/: 0 occurrences.

Plan inconsistencies / left: (1) `wiki-seed/install.md:63` and `wiki-seed/new-wiki.md:18` (the "Input / Output" paragraph) still say `sessions/` is the one folder always created; outside step 11's list, listed not edited (the new-wiki page's next paragraph now says the rest). (2) CHANGELOG.md is 276 KB: read lines 1-60 only, the edit sits at the top. (3) The SKILL.md plan-summary `Folders:` line and tree changed the skill's visible output, so step 17's suite sees it. (4) The plan says the evidence goes to checkpoints.md; it is here, as for earlier steps.

## Step 11 — orchestrator follow-up
- Fixed the two stale "only `sessions/` is created" lines the developer listed: `wiki-seed/install.md:63` and `skills/new-wiki/wiki-seed/new-wiki.md:18` now name `best-practices/local/` too.
- Departure: the developer read `CHANGELOG.md` lines 1-60 only (276 KB; the edit is at the top), not the whole file.

## Step 12 — 2026-11-19, green
- `templates/CLAUDE.md.tmpl` precedence entry 1 gains one sentence: a project's own changes go in `wiki/best-practices/local/<doc name>`, never in the doc; read it after the framework doc (the doc's "Local changes" line says in what order). 5 new tests in test_standalone render the template through Phase B. Orchestrator re-run: 40/40. The developer reports test_local_folder 16/16, test_global_toolset 80/80, check-freeze PASS (70 entries).

## Step 13 — listing
Listing pass only, 2026-11-19. Nothing in project-notebooks was edited. Scripts and output live in the session scratchpad `...\scratchpad\step13\`: `list_links.py`, `listing.json`, `listing.md`, `repoint.py` (prepared, dry-run only).
- Counts (agentic-design, every file): 1043 items. 109 auto-repointable in 76 files (28 with an anchor, all mapped to existing headings; 0 headings to add); 81 for Mark (8 live, 73 in machine files); 9 owned by step 15; 3 unrecognised (`wiki/.obsidian/workspace.json`); 4 mentions that are not links; 837 items in 109 record files skipped.
- Plan's 128 links in 84 files: measured under `wiki/` with the plan's pattern, 130 occurrences on 127 lines in 83 files. Count of every doc-name form is 133 items in 84 files (126 links, 7 mentions).
- Dry run of `repoint.py`: 76 files, 109 links would change, 0 problems; every proposed target and anchor resolves.

## Step 14 — manual evidence
Written by the developer, 2026-11-19. No test (Trivial stakes: yes). Nothing committed. Script and output: session scratchpad `...\scratchpad\step14\step14.py` (modes `list`, `apply`, `resolve`); the apply step re-checked each file's hash against the listing and would have skipped a changed one (none did).

Listing (whole `notebooks/llm-wiki-bootstrap/` folder, hits of `global-toolset/wiki/project/best-practices/framework/`): 25 lines in 16 files, by class:
- live page, link (edited): 17 lines in 11 files (19 links; two lines hold two links)
- design-rebuild (`_inbox/design-rebuild/**`, left): 3 lines in 3 files (`final/50-quality-and-promotion.md:55`, `quality/documented.md:60`, `quality/living.md:43`; all prose)
- root `_INDEX.md` (listed, indexer rebuilds): 3 lines (614, 626, 665), all links
- live page, prose not a link (left): 1 (`wiki/project/architecture/50-quality-and-promotion.md:66`, architecture prose, the finish step's wiki record)
- sessions (left): 1 (`wiki/sessions/main/237-decisions-for-mark.md:139`)
- card #248: 0 hits (the card does not carry the full path string); other/unclassified: 0.
Before 25 lines; after 8 (3 design-rebuild, 3 root `_INDEX.md`, 1 prose, 1 sessions). Zero live links to the old path remain.

Files changed (11, all under `notebooks/llm-wiki-bootstrap/wiki/`, links only): project/architecture/00-system-overview.md (1), 20-ingesting-a-source.md (2), 50-quality-and-promotion.md (2); project/best-practices/memory-architecture-where-we-stand.md (1), wiki-authoring-where-we-stand.md (2); project/decisions/architecture-decisions-2026-04-10.md (1, the step 8 page, line 30 now), code-changes-summary-in-wiki-working-files-in-raw-2026-09-14.md (1), duplicates-retired-not-deleted-dedup-normalised-2026-09-14.md (1), icarus-integration-plan-2026-05-21.md (5), pages-declare-themselves-standalone-no-built-in-list-2026-09-24.md (2); project/troubleshooting/research-cycle-failures-we-hit-2026-04-to-10.md (1). 19 links repointed.

Resolve (path arithmetic onto `notebooks/global-toolset/wiki/best-practices/framework/<doc>`, doc checked in `framework-docs/`, anchor checked against that doc's headings): `links 19 dead 0`. Docs hit: wiki-authoring (7), wiki-frontmatter (7, one with `#tier-rubric`, heading `### tier rubric` exists), memory-signals (3), cycle-step-return-format (1), no others. No anchor into `#review-cadence`.

Listed, not edited: the 3 root `_INDEX.md` lines; the prose line in 50-quality-and-promotion.md:66 and the 3 design-rebuild lines (finish step's record / records); the session journal line.

Plan inconsistencies: (1) the plan says to classify card #248 hits; there are none. (2) Step 8's note said the architecture-decisions page line ~26 links the old path; it is line 30 after the step 8 edits. (3) The plan's `manual: step 14` says evidence goes to `checkpoints.md`; it is here, as for earlier steps.

## Step 13 — applied
2026-11-19, after Mark's 23:12Z answer (Discord, verbatim: "Agreed. LLM-WIKI might point adn AgentiucDEsign, but Agentic_Degsign does NOT poiunt at LKLM wiki. If its important, it goes in Agentic-Desgign"). The 8 for-Mark live links (7 pages) were added to the auto class: link targets only, text unchanged. Listing re-run fresh after step 8's commit; the counts did not move.
- Applied by `repoint.py --apply`: 117 links in 80 files (109 earlier auto + 8 approved). Skipped files: 0 (no hash change, no assertion failure, no JSON problem). Scripts and the file list are in the session scratchpad `...\scratchpad\step13\` (`changed_files.txt` lists the 80 paths).
- Resolve run (`resolve13.py`, every changed link, path exists and anchor is a heading): `resolved 117 changed links in 80 files (28 with anchors): 0 dead`. (A first run printed 3 "NOT APPLIED" on memory-architecture-best-practices.md lines 73, 134, 330: the check script looked at the original column on lines holding two links, whose second column moves after the first edit; the apply was right and the fixed check finds all.)
- Before / after, links from agentic-design `wiki/` into the toolset's framework docs: before 126 links (117 repointed + 9 step-15 class); after 9, all in the step-15 class (8 in `project/best-practices/README.md`, 1 own-folder link `HOME.md:66`). The plan pattern `framework-docs|best-practices/framework` under `wiki/`: 130 occurrences before, 15 after (the 9 step-15 links plus mentions and the workspace entries, none an edited class).
- Left unedited: 73 items in 8 machine files (`_INDEX.md`, `_config/drift-watch.md`, `_inbox/claims-index.json` and its two `.bak-*`, three `_inbox/done` files); 3 Obsidian `lastOpenFiles` entries; 4 mentions that are not links; 9 step-15 links; 837 items in 109 record files. Link text that still names the old file stays (28 links). Not mine, modified in the working tree: `notebooks/agentic-design/.obsidian/workspace.json`, `_inbox/reports/lint-report.md`.
- Nothing committed.

## Step 15 — manual evidence
Written by the developer, 2026-11-19. No test (Trivial stakes: yes). Nothing committed; `git rm` staged the one removal. All paths under `C:\github.com\project-notebooks\notebooks\agentic-design\`.

- Best-practices README (`wiki/project/best-practices/README.md`, read whole, rewritten in its own style): the 5 `framework/...` list links (old lines 22-26), the 3 Related links (52-54) and the framework section, its "don't edit" paragraph and the framework-vs-reference table (old 40-48, which only contrasted the removed folder) are gone. Added a "Wiki best practices" section and one Related line, both linking `../../research/wiki/wiki-best-practices.md`. Opening sentence changed from "Two kinds of documents" to say the wiki practice lives in research. Grep of the file for `llm-wiki-bootstrap|global-toolset`: 0.
- `wiki/HOME.md:66`: the table row for `project/best-practices/framework/` became `[research/wiki/](./research/wiki/wiki-best-practices.md)` with the text "Wiki best practices: the hub, the three practice pages and the lessons section" (the old text named the removed folder and the icarus plan). No other HOME edit.
- Folder `wiki/project/best-practices/framework/` held only `_INDEX.md` (Glob); removed with `git -C C:/github.com/project-notebooks rm -r` (staged `D`).
- Lessons sentences fixed (4): `wiki-best-practices-authoring.md:21`, `-context-loading.md:21`, `-frontmatter-and-tiers.md:21` ("which is being written" -> "which holds the lessons"); `wiki-best-practices.md:37` ("That section is being written; until it exists the link above has nothing to open." -> "That section holds the lessons."). Grep for `being written|nothing to open` over the folder afterwards: see resolve below, 0 left.
- Index runs: `wiki-index-per-folder.py --topic agentic-design --dry-run`, then for real: "Scanned 13 folders; regenerated 4; indexed 1707 entries total" (project/best-practices, research/implementation, research/wiki, lessons-from-llm-wiki). `wiki-index.py --topic agentic-design` (root): "Files: 1725 Folders: 14".
  Changed files from the indexers: `_INDEX.md` (root; the diff is large, 650 insertions / 612 deletions ignoring EOL, because the tooling list also moved with other sessions' ingests since 2026-11-13; the step-relevant hunks: `project/best-practices/framework/` and `architecture-decisions.md` lines dropped, `research/implementation/` 33 -> 32 files, `research/wiki/` and `lessons-from-llm-wiki/` added), `wiki/project/best-practices/_INDEX.md` (8 lines), `wiki/research/implementation/_INDEX.md` (13 lines), new `wiki/research/wiki/_INDEX.md` (lists the hub and the three pages), new `wiki/research/wiki/lessons-from-llm-wiki/_INDEX.md` (lists its README).
- Gap: the generated `research/wiki/_INDEX.md` lists the 4 pages but not the lessons section (the indexer does not recurse into subfolders and the file is "do not hand-edit"); the section has its own `_INDEX.md`, the root `_INDEX.md` lists it, and the hub links it.
- Resolve (`scratchpad/resolve15.py`, path-exists for every relative link, anchors stripped) over the four pages, lessons README, best-practices README and HOME: 37+24+13+22+8+7+36 = 147 links, 0 dead.
- `icarus-integration-plan` in any `_INDEX.md` under agentic-design: 0 files (its only lister was the removed framework index).
- Grep of agentic-design `wiki/*.md` for `global-toolset/wiki|best-practices/framework|framework-docs`: 3 lines, none a link into the toolset: `obsidian-as-the-wiki-reader.md:95,96` (link TEXT only; the targets are the research/wiki practice pages) and `research/long-term/calboreanu-context-engineering-practitioner-methodology.md:79` (prose naming `../../project/best-practices/framework/wiki-authoring-best-practices.md` inside backticks, not a link). Links into the toolset framework docs: 0. (Also 2 hits in `wiki/.obsidian/workspace.json`, not mine.)
- Left, listed: the calboreanu line-79 prose names the removed path; the two link texts in `obsidian-as-the-wiki-reader.md` name old file names (same as the 28 texts step 13 left). `.obsidian/workspace.json` and `_inbox/reports/lint-report.md` show modified; not mine.

## Step 16 — manual evidence
Written by the developer, 2026-11-19. No test (Trivial stakes: yes). Nothing committed. All paths under `C:\github.com\project-notebooks\notebooks\llm-wiki-bootstrap\wiki\project\decisions\`.

Convention found (read first): the frontmatter doc's `superseded_by` row and "On retirement" bullet: retire with `status: superseded` plus `superseded_by: <path>`, never delete; the successor names the retired entry back by link or slug (lint, 2026-10-14). The notebook's own example is `project/components/read-guard-hook-2026-09-18.md` (`status: superseded`, `superseded_by: ../architecture/90-safety-guards-and-hooks.md`, no other marker). So a convention exists; the step did not stop.

Changed lines:
- `wiki-building-practice-master-in-agentic-design-copied-into-llm-wiki-2026-11-13.md`: frontmatter gains `status: superseded` and `superseded_by: ./wiki-practice-lives-in-agentic-design-llm-wiki-holds-the-build-and-links-to-it-2026-11-19.md`; one line under the H1: "Superseded 2026-11-19 by [<successor title>](<successor>). Points 1, 2, 3 and 5 below are reversed there." Nothing else touched.
- NEW `wiki-practice-lives-in-agentic-design-llm-wiki-holds-the-build-and-links-to-it-2026-11-19.md`: `category: decision`, `tier: self`, date 2026-11-19, `source_url: internal://synthesis/...` (no session id to cite), no `origin` (not invented). Sections TL;DR, What, Related. What bullets: who holds what, framework docs link their practice page, no copy and no drift check, user changes in `best-practices/local/`, the layout, the architecture-decisions record moved here with the flow, agentic-design never links to llm-wiki; Mark's words quoted from checkpoints.md. Links: `./architecture-decisions-2026-04-10.md` (exists), `../../../../agentic-design/wiki/research/wiki/wiki-best-practices.md` (depth checked, file exists), `../../tasks/243-framework-docs-master-in-agentic-design-copied.md` (exists), the superseded page (named back in TL;DR and Related), the 2026-10-05 decision. It says the code-change record is added when the change is finished. No Backlinks block (the tool writes it).
- `global-toolset-one-notebook-for-every-tooling-doc-2026-10-05.md`: one bullet added first under "Caveats / open questions": "Layout moved by #243: now `wiki/best-practices/framework/` ([decision](./wiki-practice-lives-in-agentic-design-llm-wiki-holds-the-build-and-links-to-it-2026-11-19.md))." Not superseded. The page's body line 29 still says the old path (history; the note sits beside it).

Lint: `uv run --project C:/Users/mark/.claude/wiki-scripts python C:/Users/mark/.claude/wiki-scripts/wiki-lint-mechanical.py --topic llm-wiki-bootstrap`. Retirement links: no such entry=0, successor does not name it back=0. Broken links 19, none in the three files (the rest name the not-yet-installed toolset path). No orphan, frontmatter, body or tier finding names them. Findings that DO name them: (1) "Backlink blocks out of step", the 2026-11-13 and 2026-10-05 pages and the new page are listed as missing backlinks (also the moved architecture-decisions page, from step 8); (2) the 2026-10-05 page in Code drift (`describes: scripts/_install_tooling.py@273ddfb`, changed since, 22 commits), existing before this step. Not fixed: the only fix for (1) is `wiki-reciprocate-backlinks.py --topic llm-wiki-bootstrap`; its dry run shows it would rewrite 9 pages, 5 of them other sessions' (`code-changes/2026-11-19-246-...`, `decisions/left-undone-write-check-...`, `troubleshooting/byte-comparing-test-...`, `do-code-change-edit-gate-...`, `test-copying-scripts-...`), so it was not run; hand-editing inside the BACKLINKS-AUTO markers is forbidden. It is one command for the finish step or the cycle. (2) is a describes-drift prompt, not a defect of this step.
Side effect: the lint rewrote `notebooks/llm-wiki-bootstrap/_inbox/reports/lint-report.md`; not mine, not to be committed with this step.

## Step 4b - 2026-11-19, green
- `wiki-map-compile.py` `CONTAINER_FOLDERS` gains `best-practices` (one line). 5 new tests in test_local_folder (21/21). Red before the change: the note test and the README test failed (19/21); the other three are regression guards frozen green with bite shown by transient mutations, reverted. Name review: two over-claims fixed and re-frozen (name-review.md). check-freeze PASS (75 entries).
- Compiler: `process` walks a container folder with rglob, so `best-practices/local/` becomes its own section `best-practices/local/` (entries, tier-sorted). Folder README: `collect_folder_entries` globs every *.md except `_INDEX.md`, so a README with a `title` is listed as an entry like any note, and `folder_purpose` takes its first non-heading paragraph as the folder purpose line (rebasing links). The shipped local README gets both, exactly as the same file does in research/active/. A folder with no titled note gets no section; a wiki with no best-practices folder compiles as before.
- Other suites: test_cycle_script_fixes 44/44 (holds the only map-compile contract check), test_search_mode 82/82, test_global_toolset 80/80, test_standalone 40/40.
- Left: the comment above the constant still reads "Container folders (research/, project/)"; no pre-commit config in the repo.

## Step 7 follow-up — federation lesson
Written by the developer, 2026-11-19. No test (Trivial stakes: yes). Nothing committed. Mark's reason is quoted in `checkpoints.md` (23:20Z). All paths under `C:\github.com\project-notebooks\notebooks\`.

- New: `agentic-design\wiki\research\wiki\lessons-from-llm-wiki\skills-over-single-purpose-agents.md` (tier self, `internal://` source, TL;DR, Related with 3 links; practice, what was built per the 2026-10-30 note, Mark's quote attributed 2026-11-19, what the practice page now says; no link to llm-wiki).
- Edited: lessons `README.md` (TL;DR reworded, lesson listed under "The lessons", "Open" now says none, one Related line added); `wiki-best-practices-authoring.md` (one paragraph after the federation section's last bullet: the lesson revises the practice toward well-defined skills any agent can pick up and role agents using several skills; old reasons kept); `llm-wiki-bootstrap\wiki\project\decisions\architecture-decisions-2026-04-10.md` (one line after Decision 2's status note: Mark's reason, quoted, linked to the lesson page; relative depth `../../../../agentic-design/...`, file exists).
- Lint (`wiki-lint-mechanical.py --topic agentic-design`): Broken links 0, Orphan pages 0, spec enforcement 0. Only findings naming the new page or README are backlink-block "out of step" lines (missing links), cleared by the backlink rebuild, not run here. No body-check finding names them.
- `wiki-index-per-folder.py --topic agentic-design`: "Scanned 13 folders; regenerated 1; indexed 1708 entries total"; only `lessons-from-llm-wiki/_INDEX.md` rewritten (now 2 entries).

## Step 17 — /new-wiki cases, red then green, PENDING rows
- Cases and check branch from `eval-case-writer`, saved unchanged after Mark's "proceed": `local-readme-project-none`, `local-readme-project-default-stubs` (kind `scaffold-local`) in `tests/skills/new-wiki/cases.json`; the `scaffold-local` branch in `check.py` after `drive-ask`.
- Paid run 1, `--red-green 7b66e2a` (`20261119-223534-red-green-…`, $3.18): NOT red then green. The none case passed on the old copy on both models: the sessions ran `<bootstrap_source>/scripts/new-wiki.py` (live clone), not the export's. The stubs case was refused by the auto-mode classifier on Phase B on both models.
- manual: free red proof, old export vs working-tree `new-wiki.py --phase B` (`WIKI_TOOLING_DRY_RUN=1 WIKI_GIT_HOOKS_DRY_RUN=1`, scratch vault): old none → no README, old stubs → no README; new none → README, new stubs → README; all exit 0.
- Paid run 2 on Mark's "ok please run" (`20261119-224512`, $0.28): stubs case PASS on Sonnet and Opus.
- Baselines merged per case (11 → 13 per model, older entries unchanged). PENDING rows: new-wiki, the grouped path-correction row, wiki-lint + wiki-search. Card #252 (backlog) for the harness gap.
- Full suite: trigger applies (`_wiki_config.py`, search helper); told Mark $40-90, not recommended.

## Mutation pass (by hand)
Written by the developer, 2026-11-20. `prove_tests_bite.py` mutates only `src/**/*.py` and runs pytest; this repo's code is in `scripts/` and its tests are standalone scripts, so the real script cannot run here (as in runs 240 and 246).
- Real script, `--check --base 7b66e2a92fc2cfa3892050f143bd35fe0e6bd40d`, its last lines: `no mutation report: run the pass on the change (or record each trivial-stakes file with --exempt)`; `tests-bite layer: COULD-NOT-RUN against 7b66e2a9... (0 changed source file(s)); report .artifacts/python-mutation.json`; `VERDICT: COULD-NOT-RUN`.
- Stand-in: `hand-mutation.py.txt` / `hand-mutation-result.json` in this folder. One bug planted at a time in a scratch copy of the repo (never the repo), on the lines `git diff 7b66e2a HEAD -- scripts/` added or edited in `_install_tooling.py`, `_wiki_config.py`, `new-wiki.py`, `wiki-map-compile.py`, `wiki-qmd-query.py`, `wiki-update.py`. Tests: `test_global_toolset`, `test_local_folder`, `test_search_mode`, `test_standalone`, then `test_refresh_prunes`, `test_not_checked`, `test_install_incomplete`, `test_install_manifest`, `test_tooling_state_seam` (the other files that import the changed functions); a mutant is killed when any exits non-zero or does not end `N/N passed`. All nine files were green unmutated first; canary M0 (not a changed line) killed.
- Counts: 92 mutants (M0 canary + 91 on changed lines). First pass: 80 killed, 12 survived. After the new tests: 89 killed, 3 survived, all three recorded equivalent. Every changed code line carries at least one mutant except the `from functools import partial` and the two import lines (a mutant there fails at import, so it is trivially killed).
- The 12 first-pass survivors:
  - M20 (`if True` for the `not in files` filter) and M22 (`if True else []` for the `is_dir()` guard) in `toolset_status`: equivalent. `files` holds only new-layout paths, so the filter is true for every old .md; `Path.glob` on a missing folder yields nothing, so the guard only skips an empty scan.
  - M29 / M30 (`_guarded`'s reason drops the error class / the message): behaviour wrong (the reason is the one text a person reads). Killed by new `test_failed_reason_reads_error_class_colon_message`.
  - M47 (`old_docs.rmdir()` unguarded): wrong, a held folder would stop the refresh. Killed by `test_unremovable_old_folder_is_listed_failed_not_raised` (patches `Path.rmdir` to raise PermissionError for that folder).
  - M53 (INCOMPLETE line prints a count of 0): killed by `test_install_summary_counts_the_failed_operations`.
  - M64 / M65 (phase_docs failure line printed as a success line / count 0): killed by `test_phase_docs_failure_line_is_a_warning_with_the_count`.
  - M73 / M74 / M75 (`folder_notes` row for `best-practices/local` dropped / key altered / text emptied): the existing test only checked the line's prefix. Killed by `test_phase_b_readme_local_line_carries_its_note`.
  - M79 (README rendered with `{}` instead of the scaffold variables): equivalent for the shipped README, which has no `{{` placeholder (frozen `test_shipped_local_readme_has_no_template_placeholder`). A claim for the reviewer: a README given a placeholder later would need a test then.
- Tests added (all green on the code, red on the mutant in the scratch copy, which the re-run in `hand-mutation-result.json` shows): 4 in `tests/scripts/test_global_toolset.py` (80 -> 84), 1 in `tests/scripts/test_local_folder.py` (21 -> 22). Frozen with `check-freeze.py freeze --step mutation --green-reason "<the mutants it kills>"` (they pass on the code, so a green reason, not a red command). Three were re-frozen once with an unfrozen reason: an edit had dropped the space in the module-level `ROOT = Path(...)` they load, restored, test bodies unchanged.
- Final: test_global_toolset 84/84, test_local_folder 22/22, test_search_mode 82/82, test_standalone 40/40. check-freeze: `check-freeze: exit 0 - PASS: every frozen test matches, or changed with a reason`. No `.pre-commit-config.yaml` in the repo. No production file edited.
- Does not establish: the mutants are hand-chosen operators, not an engine's full set; a mutant run stopped at the first test file that failed, so per-file kill counts are not recorded; the three equivalents are recorded claims; `tests/skills/` (paid model runs) was not part of the pass; the scratch copy omitted `tests/skills` and `.git`, so tests needing them were not exercised.

## Fix round 1
Written by the developer, 2026-11-20. Nothing committed. Production edits were stashed for the freeze so each new test's red was recorded for real, then restored.
- standards-1 / risk-1 / spec-7: `scripts/wiki-upgrade.py` (after `print_summary`), `scripts/new-wiki.py` `phase_tooling` and `phase_b` (`--install-global-if-missing`) now return 1 when `summary["toolset"]["failed"]` is non-empty, printing one error line after the FAILED lines. Phase B stops before the project folder is created, the pre-change outcome (an `InstallIncomplete` returned 1 there). New tests in test_global_toolset: `test_wiki_upgrade_exits_1_when_a_toolset_write_failed`, `test_new_wiki_tooling_mode_exits_1_when_a_toolset_write_failed`, `test_scaffold_stops_when_the_global_install_it_runs_failed_a_toolset_write` (red: exit 0 / 0 / 0 with a project created; green after). CHANGELOG 2026-11-19 "What" bullet names the three paths. `install-wiki.ps1` (`exit $LASTEXITCODE`, `$exit`) and `install-wiki.sh` (`exit $?`, `$EXIT`) pass the code through; not edited. Scope: `scripts/wiki-upgrade.py` added to plan.md `## Scope` and a checkpoints.md line (the edit gate refused it otherwise).
- standards-2 / standards-9: `_skip()` in test_global_toolset prints `SKIP <test>: <reason>` and records no check; used in the root case and the three non-Windows exits. The four tests re-frozen with an unfrozen reason.
- standards-3: `PRACTICE_PAGE_ROOT` deleted from test_standalone (deleted, not used; the table's expected paths are typed out on purpose).
- standards-7 / spec-2 / risk-4: `"best-practices/local"` added to `MERGED_TAXONOMY`. New test `test_filing_into_best_practices_local_is_accepted_in_a_wiki_that_lacks_the_folder` in test_local_folder (red: validate_folder returned the new-top-folder error; green after).
- standards-5/6, standards-12 part: comment lines in `wiki-map-compile.py`, `_wiki_config.py` (SCAFFOLD_TAXONOMY value unchanged), `_install_tooling.py`, the `phase_docs` docstring, and `# B1 — mkdir + git init` restored. No test (comments).
- standards-4: the `not in files` clause dropped from `toolset_status`'s old-docs scan (M20/M22 equivalents; the `is_dir()` guard is kept as an `if`); test_global_toolset stays green.
- Counts: test_global_toolset 87/87, test_local_folder 23/23, test_standalone 40/40, test_install_incomplete 25/25, test_install_manifest 21/21, test_refresh_prunes 11/11, test_not_checked 23/23, test_tooling_state_seam 23/23. check-freeze: `check-freeze: exit 0 - PASS: every frozen test matches, or changed with a reason` (84 entries, 164 earlier).
