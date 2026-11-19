# Plan — 243-framework-docs-master

Classification: vertical slice. Steps 1 to 3 are the code increments (each can be tried: the toolset layout, the toolset `local/` file, the new-wiki scaffold). Step 4 is the one sweep of the old path's name. Steps 5 to 13 are information steps (docs and notebook pages), ordered so the practice pages exist before any framework doc links to them. Not a wide refactor: no shared interface changes. The install (`-RefreshOnly`, `--mode status` current) and the wiki record are the finish step's, not plan steps.

Revised after the red-team and Mark's plan-confirmation answers (2026-11-19), steps rewritten in place; the history is in `checkpoints.md`.

## Problem Statement
The six framework docs mix how a wiki should be built (practice) with how llm-wiki is built. Mark settled on 2026-11-19: agentic-design holds the practice, llm-wiki holds what it has built and links to the practice. A user's own tweaks need a place that install and update never overwrite. Mark also moved the layout: `best-practices/` sits beside `project/` and `research/`, not inside `project/`.

## Solution
- Layout everywhere in llm-wiki wikis and the global toolset: `wiki/best-practices/framework/` (the six framework docs, toolset only) and `wiki/best-practices/local/`.
- `local/README.md` is a framework file: it says "do not edit this README; put your changes in files beside it". Install, `--phase docs` and every Phase B run replace it when it differs from the shipped text and create it when missing. Every other file in `local/` is the user's: never added, changed or removed, and outside the remove scan.
- The global install writes the framework docs to the toolset's `wiki/best-practices/framework/`, and removes the old `wiki/project/best-practices/framework/*.md` so nothing is in two places.
- Every skill, agent, template, wiki-seed page, test and script that names the old toolset path moves to the new one.
- Each of the six framework docs gets a "Local changes" line and a real relative link to its agentic-design practice page (or says none). The frontmatter doc gets the two tier rules, the new repository-tier cell and three field fixes. Docs that describe framework docs say where a user's changes go.
- Notebooks (information only): three practice pages in agentic-design, a `lessons-from-llm-wiki/` section, the architecture-decisions record moved into the llm-wiki-bootstrap notebook with the flow at its top, the 128 agentic-design links repointed to the practice pages, the hub README and index, and the 2026-11-13 decision marked superseded.
- Nothing copies from, or compares against, agentic-design (Exclusions). Existing wikis with the old layout are retrofitted later by a new card; the finish step notes it.

## Implementation Decisions
- Constants live in `_wiki_config.py` beside the existing one: `TOOLSET_FRAMEWORK_DOCS` becomes `wiki/best-practices/framework`; new `TOOLSET_LOCAL_DIR` = `wiki/best-practices/local`; new `TOOLSET_OLD_FRAMEWORK_DOCS` = `wiki/project/best-practices/framework` (read only by the remove scan). `wiki-update.py:1264` builds the toolset path by hand from parts: it is migrated to `TOOLSET_FRAMEWORK_DOCS` (uses: the constant, `_wiki_config.py`).
- The README source is one shipped file, `seed/best-practices-local/README.md`. `toolset_files()` lists it at `TOOLSET_LOCAL_DIR / README.md`, so `toolset_status()` adds, replaces and counts it toward stale like a framework doc. The existing add/replace/remove dict carries it, and the dry-run early return in `seed_toolset` (`_install_tooling.py:225-226`) already reports it, because the dict is built before the return.
- A per-file guard in `seed_toolset` (round-2 fix 4): each write (`mkdir`, `copyfile`) and each `unlink` / `rmdir` is wrapped on its own. A failure (a plain file where `local/` should be, a held file on Windows) is caught, recorded in a new `failed` list of `{path, reason}` in the returned dict, and the loop goes on with the next file. `failed` is set only on a real run (a dry run has none), never feeds `state`, and never changes what `toolset_status` returns. `phase_docs` prints each as `FAILED <path>: <reason>` and returns exit 1 when any exist; the global install prints them the same way and says the refresh is incomplete. `new function _guarded(op, path, failed)`, `searched for: try/except OSError, exist_ok in _install_tooling.py, found no per-file guard`.
- Callers of the dict `seed_toolset` returns (to be listed again by the implementer in step 1's hand-back): `phase_docs` in `new-wiki.py` (prints add, replace, remove and now `failed`; the check path reads `toolset_status` only) and the `--mode status` toolset report (`_install_tooling.py:~1191-1203`, stale when add, replace or remove is non-empty; it does not read `failed`). Both already treat a non-empty add or replace as "something to refresh", which is the intended meaning for the README.
- The remove scan is extended only as far as `TOOLSET_OLD_FRAMEWORK_DOCS/*.md` (files not in the package's list); after unlinking, the emptied `framework` folder is removed with `rmdir` (never its parents, never a folder holding a non-`.md` file or subfolder). The scan never looks inside `local/`.
- Scaffold: Phase B writes `seed/best-practices-local/README.md` to `<wiki>/best-practices/local/README.md` on every run, by comparing bytes: write when the file is missing or its bytes differ, leave it when equal. `_copy_tree` is NOT used: it skips a destination whose mtime is at or after the source's (`new-wiki.py:316-318`), so an edited README would never be restored (round-2 fix 1a). `new function write_if_bytes_differ(src, dst, dry_run)` in `_install_tooling.py`, `searched for: _copy_tree, shutil.copyfile, _render_template, found none that compares bytes before writing`; the toolset side already compares bytes inside `toolset_status`, so it does not call it. The folder is created for every `--project-folder` value (`none` too). `folder_notes`/`WIKI_FOLDERS` list `best-practices`.
- pending Mark: item 1b (a Phase B re-run also re-renders `README.md`, `HOME.md`, `_MAP.md`, and the new `best-practices` entry changes the rendered README: state it, or render those only for a new wiki). Step 3's retrofit bullet below waits on it.
- pending Mark: item 2 (about eight project CLAUDE.md files rendered from the template still name the old path as the frontmatter-spec authority, `templates/CLAUDE.md.tmpl:94,164`; and the toolset refresh removes the old copy: remove now, keep the old copy until the retrofit card, or put the CLAUDE.md line fix on the retrofit card). Step 1's removal bullet waits on it.
- pending Mark: item 6/7 (whether user files in `best-practices/local/` are exempt from the entry checks in `wiki-lint-mechanical.py:189-195`, and whether search indexes the folder, `wiki-qmd-query.py:773`). Step 3's lint bullet covers the README only.
- Practice pages in agentic-design stay in that notebook's existing `wiki/project/best-practices/framework/` folder (see Decisions needed), named `wiki-authoring-practice.md`, `wiki-frontmatter-and-source-tiers-practice.md`, `context-loading-and-memory-signals-practice.md`.
- Which practice page each doc links to: wiki-authoring → authoring page; wiki-frontmatter → frontmatter page; tiered-context-loading and memory-signals → context page; cycle-step-return-format → authoring page (its checkpoints idea); wiki-search-bucket-rerank-spec → none (the doc says "Practice page: none"; no link to it among the 128).
- Link depth at the new layout: a framework doc sits in `global-toolset/wiki/best-practices/framework/`, so `notebooks/` is four `../` up. The practice link is `../../../../agentic-design/wiki/project/best-practices/framework/<page>.md`. The existing wiki-authoring line-221 link `../../../../../llm-wiki-bootstrap/wiki/...` becomes `../../../../llm-wiki-bootstrap/wiki/...` in the same edit; the implementer checks every other relative link in the six docs at the new depth (the sibling `./<doc>.md` links are unchanged).
- The "Local changes" line is Decision 3's wording, with the path moved: "`best-practices/local/<this doc's name>` in the wiki you are working in, then the toolset's `local/<this doc's name>`, hold this install's own changes. Read them after this doc; where they differ, the wiki's local file wins, then the toolset's, then this doc." Directly under the frontmatter. No script or skill reads it.
- The shipped `local/README.md` carries valid frontmatter (title, date, tags, tier, `framework-contract: true`, `framework-version: 1`) so the mechanical lint finds nothing in it. It states: this folder is for your own changes; this README is a framework file and is replaced on update, so do not edit it; name a file after the framework doc it changes.
- Frontmatter-doc rows are written from the code, not the card. Verified in this run: `wiki-update.py:830` writes `status: proposed`; `wiki-promote.py:173-185,471-473` strips it at promotion. `origin`: no script writes it; `templates/CLAUDE.md.tmpl:94` tells agents to stamp `origin: inline`. `cycle_id`: no script or skill text found writing it into an entry (`wiki-lint-mechanical.py:1260` only names it as the place for cycle provenance). The implementer re-greps `cycle_id` over `scripts/`, `skills/`, `templates/`, `agents/` and writes the row to say what it finds; it does not invent a writer.
- Version bumps (once each, in step 8): cycle-step-return-format 9→10, memory-signals 3→4, tiered-context-loading 3→4, wiki-authoring 16→17, wiki-frontmatter 19→20, rerank spec 2→3. Step 9 does not bump again.
- `templates/CLAUDE.md.tmpl` needs a `local/` mention: one line in its precedence list (line ~164, the framework-contract docs entry) saying a project's own changes to a framework doc go in `wiki/best-practices/local/<doc name>`, read after it. Its two framework-path mentions (lines 94, 164) move in step 4. The `project/best-practices/` line (36, 51) is the project's own conventions and stays.
- Not the framework path, unchanged: `scripts/_cycle_common.py:158` and `tests/skills/wiki-cycle/check.py:1124` read the project's own `wiki/project/best-practices/` canon pages. Stated so the sweep does not rewrite them.
- The moved architecture-decisions page (step 7): `git mv` to the llm-wiki-bootstrap notebook's `wiki/project/decisions/`; the frontmatter is rewritten to that notebook's decision-page convention (the implementer reads a sibling decision page first), keeping `tier: self` and the original date and adding the flow at the top; `## Related` links are rewritten as relative links valid from the new place (a link from llm-wiki to an agentic-design practice page is intended; the reverse is not); the auto Backlinks block is emptied between its markers, its entries pointed at agentic-design pages that Decision 5 repoints away, and the notebook's backlink tool rebuilds it; nothing in it is hand-written.
- The `architecture-decisions` mentions, 83 files and 180 occurrences (counted this run over `project-notebooks/notebooks`), by class, with Mark's Choice 2:
  - left as records: 30 files under agentic-design `_inbox/archive/**`; 24 under `_inbox/reports/**`; 2 claims-index backups (`claims-index.json.bak-2026-08-02`, `.bak-2026-08-13`); 4 llm-wiki session journals and `sessions/main/231-split-plan.md`; total 60;
  - machine files, listed for Mark before any edit: 3 (`_inbox/claims-index.json`, `_signals/architecture-decisions.json`, `_config/drift-watch.md`);
  - live pages repointed: 14 in agentic-design (3 under `architecture/`, 9 under `research/`, `research/implementation/_INDEX.md`, the notebook's root `_INDEX.md`), 3 llm-wiki pages (two decision records, one troubleshooting page) and 2 llm-wiki task cards (231, 243); total 19;
  - the page itself, moved: 1. 60 + 3 + 19 + 1 = 83.
- `tests/search/question-set/pool.json` (3 `architecture-decisions` ids; framework-path ids too): out of scope. It is a frozen question set whose ids and the stored results (`tests/search/.results/`) describe the notebook as it was when it ran; editing the ids would make the baseline claim something no run saw. A later search run that misses the moved page is a search-test matter, not this change's.
- Old-path sites in this repository, from one search (`best-practices/framework`, excluding `.do-code-change/`, `.git`, `tests/search/`, `archive/`): 63 occurrences in 34 files, plus two code sites that build the path from parts (`_wiki_config.py:520`, `wiki-update.py:1264`). By class: 17 skill files (`new-wiki`, `wiki-claims`, `wiki-cycle` ×2, `wiki-discover` ×2, `wiki-lint` ×2, `wiki-refresh` ×2, `wiki-report`, `wiki-rollback`, `wiki-search`, `wiki-update` ×2, `wiki-verify`, `wrap-up` wiki-seed page); 1 agent file (`agents/wiki-ingester/wiki-ingester-reading-list.json`, 4 occurrences); 2 templates (`CLAUDE.md.tmpl`, `feeds.md.tmpl`); 1 seed file (`seed/global-toolset-README.md`); 2 wiki-seed pages (`user-guide.md` 9, `obsidian.md` 1); 1 framework doc (`wiki-frontmatter-best-practices.md`); 3 scripts by text (`_install_tooling.py`, `new-wiki.py`, `wiki-update.py`); 4 root docs (`CLAUDE.md`, `INSTALL-INVENTORY.md` ×4, `V2_ROADMAP.md`, `CHANGELOG.md` ×6); 3 test files (`test_global_toolset.py` ×2, `test_link_gaps.py` ×2 fixture, `tests/skills/PENDING.md` ×1). The CHANGELOG's six older entries are history and stay; step 10 adds the new entry. The implementer repeats the one search at the start of step 4 and lists any site this plan missed.

### Red-team fixes
- The shipped README carries valid frontmatter; step 3 lints a freshly scaffolded wiki and expects no finding from `best-practices/`.
- `--project-folder none` and the `project/` folder: moot, `best-practices/` is its own top-level folder.
- The `seed_toolset` dry-run early return: no helper to place; the README is a listed file, reported by the status dict built before the return; no new key; callers of the dict are listed above.
- Step 11's listing script handles `.obsidian/workspace.json`, directory-form links and `#anchor` suffixes (each anchor mapped to an existing heading in the target practice page, or the heading added, or the link listed for Mark), and re-reads each file just before writing it.
- The link invariant has real checks: a pure path-arithmetic test of the six links in step 8, plus a resolve run from the registered toolset root and a mechanical lint of one framework doc in a temp wiki, output quoted. `test_link_gaps.py` is no longer cited as the pin.
- `pool.json`: out of scope, with the reason above.
- Steps 5, 6, 7, 10, 12 and 13 each carry a `Failures:` line.

#### Red-team fixes, round 2 (plan errors only; choices wait for Mark)
- 1a: Phase B writes the local README by byte comparison (`write_if_bytes_differ`); `_copy_tree` is not used (it skips by mtime).
- 4: `seed_toolset` gets a per-file guard with a reported `failed` result; step 1's "no new function" and step 2's "does not raise" bullet are rewritten to match.
- 5: `V2_ROADMAP.md` is in step 4's sweep unconditionally; step 10's condition is dropped. Step 13 adds a one-line "layout moved by #243" note to the 2026-10-05 global-toolset decision. The requirements' "the 2026-10-05 decision still holds" line is wrong (that decision states the old path; only the 2026-11-13 one is superseded): the orchestrator corrects it in `requirements.md`, outside this plan's one file.
- 6: step 9 states the two tier rules land inside the `### Tier rubric` to `### Review cadence` span, with a test that `tier_rubric_text()` returns both.
- 7: `tests/skills/new-wiki/check.py` (lines 368-372, a guard on the old path) is in Scope and step 4's sweep, red then green per the repo's `tests/skills` rule.
- 3 (plan-error part): Scope and Out of Scope name the decision on live pages outside the lists (below).
- `templates/CLAUDE.md.tmpl`: one `local/` line, step 10.
- The moved page's frontmatter, `## Related` and Backlinks block: stated above, checked in step 7.
- Counts: 83 files / 180 occurrences, split by class above.
- Phase B over an existing wiki: now an intended retrofit path (Mark's Choice 3, refined): step 3 tests it.
- Steps 8 and 9's `Trivial stakes:` re-proposed (step 9 is `no`, since every ingest reads the rubric).

## Testing Decisions
Seams, agreed with the run's requirements (Mark, 2026-11-19, "the run's code and tests cover llm-wiki-bootstrap"):
- Seam A: `seed_toolset` / `toolset_status` / `toolset_files` on a temp toolset through `$WIKI_GLOBAL_CONFIG`, and `new-wiki.py --phase docs --check` as a subprocess, in `tests/scripts/test_global_toolset.py` (the existing harness).
- Seam B: `new-wiki.py` Phase B run into a temp target through `$WIKI_GLOBAL_CONFIG`; the implementer copies how an existing test runs Phase B (the files that grep `--project-folder` in `tests/scripts/`). New checks go in a new `tests/scripts/test_local_folder.py` if no existing file fits. The mechanical lint (`wiki-lint-mechanical.py`) runs on the scaffolded temp wiki.
- Seam C: the six docs read as text, and a scan of the shipped folders for the old path, in `tests/scripts/test_standalone.py` (it already reads `framework-docs/` and its `framework-version`).
- Seam D: `wiki-update.py`'s spec lookup, run against a temp toolset laid out at the new path (step 1).
- manual: step 5 — the three pages read against the six docs' practice text and the seven decisions; the notebook's mechanical lint run before step 5 and after step 12 shows no new error; the page paths listed in `checkpoints.md`
- manual: step 6 — the lessons README and each lesson page read against the seven decisions; one lesson per departure, or "no departure" per decision, listed in `checkpoints.md`
- manual: step 7 — before and after counts of `architecture-decisions` against the class split in Implementation Decisions (60 left, 3 listed for Mark, 19 repointed, 1 moved); the record opens with the flow; the old path is gone; the moved page's frontmatter, `## Related` and Backlinks block read against its rules
- manual: step 8 — a resolve script run over the six practice links from the registered toolset root (`C:\github.com\project-notebooks\notebooks\global-toolset\wiki\best-practices\framework\`), and a mechanical lint of one framework doc in a temp wiki; both outputs quoted in `checkpoints.md`
- manual: step 10 — each doc read against steps 1 to 3's tests (the folder name, the README is replaced, user files untouched, the order wiki then toolset then framework doc); the one-source rule: no doc copies the README text or the Decision 3 line beyond what the framework docs carry
- manual: step 11 — before and after counts of `framework-docs|best-practices/framework` in agentic-design `wiki/` (128 in 84 files before; zero toward the toolset after); a link-resolve script run over every changed link, anchors included; the list of links held for Mark's OK, in `checkpoints.md`
- manual: step 12 — the hub README and the folder `_INDEX.md` read: they list the three new pages and the lessons section, and no longer list `icarus-integration-plan.md`
- manual: step 13 — the 2026-11-13 decision file read: status superseded, pointing at this change's record
- Steps 8 and 9 are proved by tests for the form (the line, the link pattern and its depth, the rows, the versions). That every link resolves on this machine is the manual line above.

## Out of Scope
- Copying any agentic-design page into `framework-docs/`; a "master is agentic-design, do not edit" note; any drift check or refresh command comparing the two.
- Changing how skills and agents find the framework docs beyond the one path change (`{{TOOLSET_DIR}}` placeholder stays).
- Retrofitting existing wikis (old `project/best-practices/` layout): a new card, noted at finish; the owner fixes them by hand, or by a Phase B re-run (which adds `local/README.md` only).
- Moving agentic-design's own `project/best-practices/framework/` folder (Decisions needed).
- agent-builder and its notebook. The other agentic-design practice pages (memory architecture, CLAUDE.md authoring, corpus reviews, negative constraints).
- Other agentic-design links into llm-wiki outside the framework docs.
- Machine files, archives, reports, session journals: not edited (only listed).
- Live notebook pages outside the lists, and the consumers of the old path in about eight project CLAUDE.md files and rpg-strategist's project skills: not edited by this plan until Mark answers items 2 and 3 (Scope, above; rpg-strategist is out regardless).
- `tests/search/question-set/pool.json` and `tests/search/.results/` (reason in Implementation Decisions).
- `scripts/_cycle_common.py` and `tests/skills/wiki-cycle/check.py`: they read the project's own canon folder, not the framework path.
- The 231 status, component and 00-95 pages, beyond repointing the architecture-decisions mentions.
- Splitting into separate changes: the code and the notebooks share the docs' practice links and Mark settled one run (Decision 4).

## Scope
Repository (llm-wiki-bootstrap):
- `scripts/_install_tooling.py`
- `scripts/_wiki_config.py`
- `scripts/new-wiki.py`
- `scripts/wiki-update.py`
- `seed/**`
- `framework-docs/**`
- `skills/**` (only the lines naming the framework path, plus the new-wiki skill's docs)
- `agents/wiki-ingester/**` (the reading list)
- `templates/**`
- `wiki-seed/**`
- `tests/scripts/**`
- `tests/skills/PENDING.md`
- `tests/skills/new-wiki/check.py` (its guard at lines 368-372 names the old path)
- `CLAUDE.md`
- `INSTALL-INVENTORY.md`
- `V2_ROADMAP.md`
- `CHANGELOG.md`
- `.claude/do-code-change.json` (an orchestrator config change on Mark's instruction, a signed `budget` entry; no plan step or test of its own)

Notebooks (committed in `C:\github.com\project-notebooks` by explicit path; not in this repository's diff):
- `notebooks/agentic-design/wiki/project/best-practices/**`
- `notebooks/agentic-design/wiki/project/lessons-from-llm-wiki/**`
- `notebooks/agentic-design/wiki/**` (the link repoints; every file the step 11 list names)
- `notebooks/agentic-design/_INDEX.md`
- `notebooks/agentic-design/wiki/research/implementation/architecture-decisions.md` (moved out)
- `notebooks/llm-wiki-bootstrap/wiki/project/decisions/**`
- `notebooks/llm-wiki-bootstrap/wiki/project/troubleshooting/research-cycle-failures-we-hit-2026-04-to-10.md`
- `notebooks/llm-wiki-bootstrap/wiki/tasks/231-separate-best-practices-from-llm-wiki.md`
- `notebooks/llm-wiki-bootstrap/wiki/tasks/243-framework-docs-master-in-agentic-design-copied.md`
- The three machine files are not in scope until Mark answers; any other file the step 7 search names is listed in `checkpoints.md` before it is edited.
- pending Mark: item 3. Live notebook pages outside the lists above that link the old toolset path (the red-team found 37 matches in 25 files outside agentic-design, among them llm-wiki-bootstrap `project/architecture/00-system-overview.md`, `20-ingesting-a-source.md`, `50-quality-and-promotion.md`, `best-practices/wiki-authoring-where-we-stand.md`, `memory-architecture-where-we-stand.md`, several decisions; cottage-build, soundboard-app and spotify-app files): widen the repoint to them, or list them for a later card. Until Mark answers, none is edited and none is in Scope. `agent-builder-bootstrap/CLAUDE.md` stays out either way (Exclusions): listed, not edited.

## Invariants
- A refresh still replaces a hand-edited listed file, removes a retired pack page and leaves another pack's folder alone — pinned by the existing checks in `tests/scripts/test_global_toolset.py` ("the hand edit replaced", "the retired page removed", "another pack's folder untouched", "current again"), which stay green.
- `toolset_status` ignores line endings — pinned by the existing "differing only in line endings" check.
- `--phase docs --check` exits 0 when current and 1 when a listed page is missing, and writes nothing — pinned by the existing checks at the end of `test_global_toolset.py`, plus steps 1 and 2's `Failures:`.
- A user's own file in `local/` is never added, changed or removed by a refresh or a Phase B re-run — step 2's and step 3's `Expected:` bullets.
- A user's CLAUDE.md, README and `.gitignore` are never overwritten by the scaffold (`skip_if_exists`). Whether an existing test pins it is unknown: the implementer searches `tests/scripts/` first; if none does, step 3's `Failures:` writes one (a Phase B run over an existing CLAUDE.md keeps it).
- Skills and agents still find the docs through `{{TOOLSET_DIR}}`, now at the new path — pinned by the existing "install-skill fills {{TOOLSET_DIR}}" and "the ingester's reading list names the toolset's spec" checks, updated to the new path in step 1.
- The six practice links resolve from the registered toolset root, and one framework doc lints clean in a temp wiki — step 8's `manual:` evidence (resolve run, lint output, both quoted) and its path-arithmetic test.
- Nothing in `scripts/` reads or names the agentic-design notebook (the Exclusions) — a grep for `agentic-design` over `scripts/` finds no new hit; the output is quoted in step 1's hand-back.
- `framework-contract: true` pages stay exempt from body checks — the existing exemption at `_entry_checks.py:229`, unchanged (no code change there); step 3's lint of a scaffolded wiki holding the README covers it.

## Decisions needed
pending Mark (asked; his answer is awaited, step 5's layout holds until then): 1. Where the new practice pages live in agentic-design.
   - Recommended: the notebook's existing `wiki/project/best-practices/framework/` folder (its hub README and 128 links already sit under `project/best-practices/`; this run does not move agentic-design's own layout). Risk: agentic-design's layout then differs from llm-wiki's new `wiki/best-practices/`.
   - Alternative: a new top-level `wiki/best-practices/framework/` in agentic-design, matching llm-wiki. Risk: a second best-practices folder beside the existing one until a later move; the hub and the 128 repoints would point at the new folder, and the old one would hold the older pages.
   - [ ] recommended   [ ] alternative

## Steps

1. The global install writes the framework docs to `wiki/best-practices/framework/` in the toolset and removes the old copy — done when the new and updated checks in `tests/scripts/test_global_toolset.py` pass (seam A) and the spec-lookup check passes (seam D).
   uses: `TOOLSET_FRAMEWORK_DOCS` and `toolset_files` / `toolset_status` / `seed_toolset`; `wiki-update.py:1264` migrated to the constant; new function `_guarded`, searched for: try/except OSError in `_install_tooling.py`, found no per-file guard (Implementation Decisions).
   - Expected: on an empty temp toolset `seed_toolset` writes the six docs at `wiki/best-practices/framework/<name>`; `toolset_status` is `current`; nothing is written under `wiki/project/`.
   - pending Mark: item 2 (whether the old copy is removed now); the next bullet is written for "remove now", the recommended-by-the-plan route.
   - Expected: a toolset holding the old `wiki/project/best-practices/framework/<six docs>.md`: `toolset_status` is `stale`, `remove` names those six, a refresh deletes them and the emptied `framework` folder, and `current` follows; `wiki/project/best-practices/` and anything else in it is untouched.
   - Expected: `--phase docs --check` exits 1 naming the old files as REMOVE, writes nothing; a plain `--phase docs` clears it.
   - Expected: `wiki-update.py`'s spec lookup finds `wiki-frontmatter-best-practices.md` in a temp toolset at the new path, and still falls back to `framework-docs/` beside the scripts when the toolset has none (the existing behaviour).
   - Failures: a held file (an open handle on Windows, or a read-only file) in the old folder, so `unlink` raises → that file is named in `failed`, the other removals and all copies still run, and `phase_docs` exits 1 printing `FAILED <path>: <reason>`; a dry run lists no `failed`. The old folder also holds a non-`.md` file or a subfolder → the `.md` files are removed, that item stays and the folder is not removed, and no error is raised. A toolset with the docs only at the old path and no registry entry → the refresh still adds the new and removes the old. `phase_docs --check` never removes anything.
   - Invariant: the existing replace, remove, other-pack and line-ending checks stay green. The two existing checks that name the old framework path (`test_global_toolset.py:74,117`) are updated to the new one.
   - Speed: none (no table, view or index; one more folder listed per refresh).
   Trivial stakes: no

2. The toolset carries `wiki/best-practices/local/README.md` as a framework file, and the user's files beside it are left alone — done when the new checks in `tests/scripts/test_global_toolset.py` pass (seam A).
   uses: `toolset_files()` (the file is listed there), `TOOLSET_LOCAL_DIR`, step 1's `_guarded`; adds the shipped `seed/best-practices-local/README.md`.
   - Expected: on an empty temp toolset a refresh creates `local/README.md` with the shipped text's bytes; the status was `add` for it before and `current` after.
   - Expected: the README edited, or an older shipped text → `toolset_status` is `stale` with it in `replace`; a refresh restores the shipped bytes; `--phase docs --check` exits 1 before and 0 after.
   - Expected: the README deleted → `add` names it; a refresh creates it again.
   - Expected: a user file `local/my-notes.md` and a user subfolder: a refresh and a second refresh leave their bytes and names unchanged, `remove` never lists them, and the status stays `current` with them there.
   - Expected: a dry run reports the README as `would be added` or `replaced` (from the status dict) and writes nothing.
   - Failures: `local` exists as a plain file where the folder should be → the refresh does not raise; the README is listed in `failed` with the reason, every other file is still refreshed, and `phase_docs` exits 1 printing it. The README held open on Windows when it is to be replaced → the same `failed` entry, the rest done. The README source missing from the package → `toolset_status` skips it as it skips any listed file with no source (the existing `src.is_file()` filter), no error.
   - Invariant: the existing refresh, remove and other-pack checks stay green.
   - Speed: none (no table, view or index; one more listed file).
   Trivial stakes: no

3. The `/new-wiki` scaffold and every Phase B run write `wiki/best-practices/local/README.md` — done when the new Phase B checks pass (seam B).
   uses: new function `write_if_bytes_differ` (Implementation Decisions); not `_copy_tree`, which skips by mtime.
   - Expected: Phase B into a temp target creates the README under the new wiki, with the shipped text's bytes, for `--project-folder stubs`, `empty` and `none`; the folder `best-practices` appears in the wiki's README/`WIKI_FOLDERS` list.
   - Expected: the mechanical lint over the freshly scaffolded wiki reports no finding from `best-practices/`.
   - Expected: the README edited with a newer mtime than the shipped file, then Phase B run again → the shipped bytes are back (this is the case `_copy_tree` would miss); a user file `local/my-notes.md` is unchanged.
   - Expected (retrofit path): a Phase B re-run into a temp wiki that already has a populated `project/` and no `best-practices/` → `best-practices/local/README.md` is added and every `project/` file is unchanged. pending Mark: item 1b (whether the re-run also re-renders `README.md`, `HOME.md`, `_MAP.md`; the tree-diff bullet is worded once he answers: "only the README added", or "the README added and these three re-rendered").
   - Expected: `--dry-run` prints `WOULD ...` for the folder and writes nothing.
   - Failures: the README source missing from the package → the scaffold stops with a named error and a non-zero exit, and creates no `best-practices/` folder. A target that already has a CLAUDE.md → kept, bytes unchanged (the invariant). A hard-coded list of top-level wiki folders somewhere in `scripts/` (the implementer greps `"research"` with `"project"`) that rejects `best-practices/` → fixed or listed in the hand-back; a lint or index run that treats the folder as an error fails this step.
   - Invariant: `_MAP.md`, `README.md` and `HOME.md` are still rendered — pinned by an existing test if one exists, else a check here.
   Trivial stakes: no

4. Every shipped file that names the old toolset framework path names the new one — done when the new scan check in `tests/scripts/test_standalone.py` passes (seam C: no file under `skills/`, `agents/`, `templates/`, `seed/`, `wiki-seed/`, `framework-docs/`, `scripts/`, `CLAUDE.md`, `INSTALL-INVENTORY.md` or `V2_ROADMAP.md` contains `project/best-practices/framework` or a path built from `"project"`, `"best-practices"`, `"framework"` parts), the existing path checks pass, and `tests/skills/new-wiki/check.py` passes with its guard (lines 368-372, "no docs copied into the wiki") pointed at the new `wiki/best-practices/framework` (red then green per the repo's `tests/skills` rule: the check is first shown to fail on a wiki holding a copy at the new path, then to pass).
   blocked by: 1.
   - `V2_ROADMAP.md` (line 56) is in this sweep unconditionally.
   - Expected: the sites listed in Implementation Decisions (63 occurrences in 34 files by the one search, plus the two by-parts sites) are rewritten to `wiki/best-practices/framework` with `{{TOOLSET_DIR}}` kept; the CHANGELOG's older entries and `tests/search/` are not touched; the project-canon mentions (`_cycle_common.py:158`, `tests/skills/wiki-cycle/check.py:1124`, `templates/CLAUDE.md.tmpl` lines 36 and 51) are not touched.
   - Failures: a site the plan missed (the repeated search finds more) → rewritten and listed in the hand-back; a rewritten skill whose frontmatter no longer parses → the install's frontmatter check (`_install_tooling.py`'s refuse-to-install) fails, so the implementer runs it on the changed skills and quotes the result; `tests/skills/PENDING.md` mentioning the path as a record of a past finding → left, named in the hand-back.
   - Invariant: skills still find the docs through `{{TOOLSET_DIR}}`, pinned by the updated "install-skill fills {{TOOLSET_DIR}}" and reading-list checks.
   Trivial stakes: no

5. Three practice pages exist in agentic-design, with the flow described and the two new tier rules in the frontmatter page — done when the evidence under `manual: step 5` is in `checkpoints.md` (no test: information pages).
   - pending Mark: Decisions needed 1 (the folder these pages are written in). Nothing in this step is written until he answers; the file names stay as in Implementation Decisions.
   - Read the notebook's own conventions first (frontmatter spec, `_INDEX.md` per folder, lint) and note them in `checkpoints.md`.
   - Extract the practice text from the six docs (principles, compile-not-retrieve, scoring, contradictions, checkpoints; the tier rubric and field principles; context loading and memory signals) with our build specifics left out; fold in the practice reasons of the seven decisions where not stated. Write the flow (agentic-design says how; llm-wiki builds and records why; a departure sends a lesson back) in each page.
   - The frontmatter page carries both tier rules: an official vendor post with something checkable behind it (code, docs, a public benchmark) is tier 2, one that is pitch alone is tier 4; repositories: "read at least the README and sanity-check the main code (not all of a big repo); if unsure check size or that main functions work; else ask Mark".
   - No link to llm-wiki from any of the three pages.
   - Failures: a page that fails the notebook's mechanical lint → fixed before the step ends; a practice idea that cannot be stated without our build detail → left out of the page and listed in `checkpoints.md`, never written as llm-wiki detail; a link to llm-wiki found by grep → removed.
   Trivial stakes: yes — information pages in a notebook; no repository code a test could catch.

6. The lessons section exists, with the first pass from the seven decisions — done when the evidence under `manual: step 6` is in `checkpoints.md`.
   blocked by: 5.
   - `lessons-from-llm-wiki/README.md` states the flow and lists the lessons; one page per departure of a decision from the practice pages; a decision with no departure is named in the README as "no departure". A practice page changed by a lesson links to it. No link to llm-wiki.
   - Failures: a departure whose reason the decision record does not give → not written as a lesson; listed for Mark in `checkpoints.md`. A lesson page that fails the notebook's lint → fixed before the step ends.
   Trivial stakes: yes — information pages in a notebook; no repository code a test could catch.

7. The architecture-decisions record lives in the llm-wiki-bootstrap notebook — done when the evidence under `manual: step 7` is in `checkpoints.md`.
   blocked by: 6.
   - `git mv` of the whole page to `wiki/project/decisions/` in that notebook; the flow written at its top; its frontmatter, `## Related` and Backlinks block handled as stated in Implementation Decisions; it stays not shipped and has no local file. The 19 live pages are repointed to its new place; the 60 record files are left; the 3 machine files are listed for Mark and not edited.
   - Failures: a mention in a file outside the listed globs → listed in `checkpoints.md`, not edited. A target path that already exists in `decisions/` → stop, nothing overwritten. A live page whose link target after the repoint does not exist (the resolve script finds it) → fixed before the step ends. A session journal or archived report found edited by the step → reverted and reported.
   Trivial stakes: yes — a move and link repoint in notebooks; no repository code a test could catch.

8. Each of the six framework docs opens with the "Local changes" line and a practice link, with `framework-version` bumped — done when the new checks in `tests/scripts/test_standalone.py` pass (seam C), with the version floors updated to the new numbers.
   blocked by: 4, 5.
   - Expected: for each doc, the line directly under the frontmatter reads the Implementation Decisions wording and names `best-practices/local/<its own file name>`; a `Practice page:` line follows with a relative link of the form `../../../../agentic-design/wiki/project/best-practices/framework/<page>.md` (rerank spec: "Practice page: none"); the version is at least the bumped number (10, 4, 4, 17, 20, 3).
   - Expected: path arithmetic: each link joined onto `notebooks/global-toolset/wiki/best-practices/framework` and normalised equals `notebooks/agentic-design/wiki/project/best-practices/framework/<page>.md`; the wiki-authoring link to llm-wiki-bootstrap, at the new depth, normalises to `notebooks/llm-wiki-bootstrap/wiki/...`.
   - Failures: a doc whose local line names another doc's file → the check fails; a `Practice page:` link at the old depth (five `../`) → fails; a doc still at its old version → fails.
   - Invariant: the existing floors for `cycle-step-return-format` (3) and the frontmatter doc (13) in `test_standalone.py` are raised to 10 and 20 and pass.
   Trivial stakes: yes — doc text and version numbers only; no Python line (a wrong link depth is caught by the path-arithmetic test, not by mutation).

9. The frontmatter doc carries the two tier rules, the new repository-tier cell and the three field fixes — done when the new checks in `tests/scripts/test_standalone.py` pass (seam C).
   blocked by: 5, 8.
   - Expected: `wiki-update.py`'s `tier_rubric_text()` returns only the span from `### Tier rubric` to `### Review cadence` (doc lines 103-138 today), so the two tier rules and the repository cell are written inside that span, never after it. A new check in `test_standalone.py` calls `tier_rubric_text()` (or reads the same span from the doc) and asserts that both the vendor-post rule and the new repository sentence are in it, and that the old cell text is not.
   - Expected: the doc has the vendor-post tier rule (checkable → tier 2, pitch alone → tier 4); the repository cell holds the new sentence and no longer contains "code read beyond the README"; a `status` row names `proposed` and says `wiki-promote` strips it; the `origin` row says who writes it (the agent stamps it per the CLAUDE.md template; no script writes it) and keeps the four values; the `cycle_id` row says what the re-grep found.
   - Failures: a row naming `status: proposed` while `wiki-promote.py` no longer strips it → the plan's own assumption; the implementer greps first and reports a mismatch instead of writing the row. Anything in `scripts/` or the skills that matches the old repository-cell text or parses the rubric rather than quoting it (the implementer runs `grep -n "tier" scripts/wiki-update.py` and checks the references at `wiki-update.py:754` and `:1256-1264`) → listed and the step does not proceed until the reader is checked against the new text.
   Trivial stakes: no — `wiki-update.py` and every ingest read this doc as the tier rubric, so the new rules change what ingest does.

10. Every doc that describes framework docs and user edits says where a user's changes go — done when the evidence under `manual: step 10` is in `checkpoints.md`.
    blocked by: 1, 2, 3.
    - Docs: `CLAUDE.md`, `INSTALL-INVENTORY.md` (also a row for the new `seed/best-practices-local/` file), `CHANGELOG.md` (the new entry; older entries stay), `seed/how-to/_FRAMEWORK_MANAGED.md`, `wiki-seed/user-guide.md`, `seed/global-toolset-README.md`, the `/new-wiki` skill's wiki-seed page and SKILL.md where the scaffold change needs a line, and `templates/CLAUDE.md.tmpl` (the one precedence-list line). Each points to the one source (the `local/README.md` text, the line atop each framework doc) and copies none of it. The CHANGELOG entry also notes that existing wikis keep the old layout until a new card retrofits them.
    - Failures: a doc that copies the README text or the Decision 3 line → reworded to a pointer. A doc that still tells a user to edit a framework doc in place, or names the old path → fails step 4's scan or the read in the evidence. `INSTALL-INVENTORY.md` without a row for the new seed file → the step is not done.
    Trivial stakes: yes — doc wording only; step 4's scan test catches an old path. The template line is read by agents of every new project, so the requester may prefer `no` for that one file.

11. The 128 agentic-design links into the framework docs point at the practice pages — done when the evidence under `manual: step 11` is in `checkpoints.md`.
    blocked by: 5.
    - A scratch script (in the session scratchpad, never in the repository) first lists every link without editing: file, line, target doc, idea, form (file link, directory-form link such as `HOME.md:66` and `README.md:44`, the `.obsidian/workspace.json` entries at lines 190 and 214), and any `#anchor` with the heading it should map to. Links to wiki-authoring, frontmatter, tiered-context-loading and memory-signals go to the page covering that doc, with each anchor mapped to a heading that exists in that page (the heading is added to the page if the idea belongs there, else the link is listed). Links to the two mechanism docs, and any link that seems to need llm-wiki, are listed for Mark's OK and not edited until he answers. The script re-reads each file just before writing it (other sessions write in project-notebooks), and edits only files under `notebooks/agentic-design/`.
    - Failures: an anchor with no heading in the practice page → the heading is added or the link is listed; never left dead and never pointed at llm-wiki. A file that changed since the listing → skipped and re-listed, never overwritten. A link form the script does not recognise → listed, not edited. `.obsidian/workspace.json` entries → edited only if the file parses as JSON after the edit, else listed.
    Trivial stakes: no — a script rewrites links in about 84 files, and a wrong rewrite is only caught by the resolve run.

12. The best-practices hub and the framework folder's index list the new pages — done when the evidence under `manual: step 12` is in `checkpoints.md`.
    blocked by: 5, 6.
    - `README.md` hub lines 22-26, 44, 52-54 rewritten to list the practice pages and the lessons section; the folder's `_INDEX.md` drops `icarus-integration-plan.md` and lists the three pages.
    - Failures: a hub or index entry whose target does not exist (the resolve script finds it) → fixed before the step ends. A hub line that still names a toolset framework doc as a source → fails the read.
    Trivial stakes: yes — index and hub text in a notebook; no repository code a test could catch.

13. The 2026-11-13 decision is marked superseded — done when the evidence under `manual: step 13` is in `checkpoints.md`.
    blocked by: 7.
    - `wiki/project/decisions/wiki-building-practice-master-in-agentic-design-copied-into-llm-wiki-2026-11-13.md` in the llm-wiki-bootstrap notebook gets status superseded and a link to this change's record; the notebook's own supersede convention is read first. The wiki change-record and the task card are the finish step's.
    - Also: the 2026-10-05 decision `global-toolset-one-notebook-for-every-tooling-doc-2026-10-05.md` (it states the framework docs live at `wiki/project/best-practices/framework/`, which this change reverses) gets a one-line note "layout moved by #243: now `wiki/best-practices/framework/`", pointing at this change's record. It is not superseded: its other points (one toolset, no per-project copies) still hold. Whether to mark it superseded instead is Mark's call at confirmation. `requirements.md`'s Fact that this decision "still holds" is corrected by the orchestrator.
    - Failures: the notebook has no supersede convention for decisions → the step stops and the question goes to `checkpoints.md`; the decision file is not edited by guess.
    Trivial stakes: yes — one status line in a notebook; no repository code a test could catch.
