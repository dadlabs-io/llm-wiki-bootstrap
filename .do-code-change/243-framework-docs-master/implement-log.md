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
