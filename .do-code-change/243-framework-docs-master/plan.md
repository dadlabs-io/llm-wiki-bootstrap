# Plan — 243-framework-docs-master

Classification: vertical slice. Steps 1 and 2 are the code increments (each a user can try); steps 3 to 11 are information steps (docs and notebook pages), ordered so the practice pages exist before any framework doc links to them. Not a wide refactor: no shared interface changes. The install and the wiki record are the finish step's, not plan steps.

## Problem Statement
The six framework docs mix how a wiki should be built (practice) with how llm-wiki is built. Mark settled on 2026-11-19: agentic-design holds the practice, llm-wiki holds what it has built and links to the practice. A user's own tweaks need a place that install and update never overwrite.

## Solution
- Code: a `local/` folder with one README, created in the global toolset by the global install (never overwritten, never counted as stale) and in each new wiki by the `/new-wiki` scaffold. One shared helper creates it, from one shipped README text.
- Docs: each of the six framework docs gets a "Local changes" line and a real relative link to its agentic-design practice page (or says none). The frontmatter doc gets the two tier rules, the repository-tier cell and three field fixes. Every doc that describes framework docs says where a user's changes go.
- Notebooks (information only): three practice pages in agentic-design, a `lessons-from-llm-wiki/` section, the architecture-decisions record moved into the llm-wiki-bootstrap notebook with the flow at its top, the 128 agentic-design links repointed to the practice pages, the hub README, and the 2026-11-13 decision marked superseded.
- Nothing copies from, or compares against, agentic-design (Exclusions).

## Implementation Decisions
- The README text lives once, as one shipped file under `seed/`. Toolset install and scaffold both write that file's bytes. `uses: copy-if-absent pattern like skip_if_exists in new-wiki.py (project files only)`; `new function seed_local_readme(pkg, dest_wiki_root, dry_run), searched for: skip_if_exists, _render_template, seed_toolset, found none that creates one file only when absent`. It lives in `_install_tooling.py` beside `seed_toolset`, and the scaffold imports it from there (new-wiki.py already imports from that file). Only one place needs it twice, so no migrate step: the two callers are both new.
- `toolset_files()` does NOT list the local README. So `toolset_status()` never adds, replaces or removes it, and the toolset is never stale because of it. `seed_toolset()` calls `seed_local_readme` after the file copy, and returns a new key `local` with `created` or `kept`. A dry run writes nothing and reports `would create` or `kept`.
- `--phase docs` goes through `seed_toolset`, so it creates the stub too. `--phase docs --check` stays read-only and its exit code is unchanged by the stub.
- The scaffold creates `wiki/project/best-practices/local/README.md` in every new wiki, also with `--project-folder none` (Mark: "create those folders as part of seating a new wiki"). It uses the same helper, so a second Phase B run keeps an edited README.
- Practice pages in agentic-design `wiki/project/best-practices/framework/`: `wiki-authoring-practice.md`, `wiki-frontmatter-and-source-tiers-practice.md`, `context-loading-and-memory-signals-practice.md`.
- Which practice page each doc links to: wiki-authoring → authoring page; wiki-frontmatter → frontmatter page; tiered-context-loading and memory-signals → context page; cycle-step-return-format → authoring page (its checkpoints idea); wiki-search-bucket-rerank-spec → none (no practice page covers search ranking; the doc says "Practice page: none"). The link form from the toolset folder: `../../../../../agentic-design/wiki/project/best-practices/framework/<page>.md`.
- The "Local changes" line is Decision 3's wording, word for word, with `<this doc's name>` filled in per doc. It sits directly under the frontmatter. No script or skill reads it.
- Frontmatter rows are written from the code, not the card. Verified in this run: `wiki-update.py:830` writes `status: proposed`; `wiki-promote.py:173-185,471-473` strips it at promotion. `origin`: no script writes it; `templates/CLAUDE.md.tmpl:94` tells agents to stamp `origin: inline`. `cycle_id`: no script or skill text found writing it into an entry (`wiki-lint-mechanical.py:1260` only names it as the place for cycle provenance). The implementer re-greps `cycle_id` across `scripts/`, `skills/`, `templates/`, `agents/` and writes the row to say what it finds (a field nothing writes is documented as "free-form, set by hand"); it does not invent a writer.
- Version bumps (once each, in step 6): cycle-step-return-format 9→10, memory-signals 3→4, tiered-context-loading 3→4, wiki-authoring 16→17, wiki-frontmatter 19→20, rerank spec 2→3. Step 7 does not bump again.
- agentic-design's own conventions (frontmatter spec, `_INDEX.md` per folder, the notebook's lint) are read from the notebook at the start of step 3, and every page written in steps 3, 4 and 10 follows them.
- Notebook commits: in `C:\github.com\project-notebooks`, by explicit path, never `git add -A` (other sessions write there). The orchestrator commits; the plan steps only write.

## Testing Decisions
Seams, agreed with the run's requirements (Mark, 2026-11-19, "the run's code and tests cover llm-wiki-bootstrap"):
- Seam A: `_install_tooling.seed_toolset` / `toolset_status` / `seed_local_readme` on a temp toolset through `$WIKI_GLOBAL_CONFIG`, in `tests/scripts/test_global_toolset.py` (the existing harness).
- Seam B: `new-wiki.py` Phase B run into a temp target through `$WIKI_GLOBAL_CONFIG`; the implementer copies how an existing test runs Phase B (the files that grep `--project-folder` in `tests/scripts/`). New checks go in a new `tests/scripts/test_local_folder.py` if no existing file fits.
- Seam C: the six docs read as text in `tests/scripts/test_standalone.py` (it already reads `framework-docs/` and its `framework-version`).
- manual: step 3 — the three pages read against the six docs' practice text and the seven decisions; the notebook's mechanical lint run before step 3 and after step 10 shows no new error; the page paths listed in `checkpoints.md`
- manual: step 4 — the lessons README and each lesson page read against the seven decisions; one lesson per departure, or the sentence "no departure" per decision, listed in `checkpoints.md`
- manual: step 5 — before and after counts of `architecture-decisions` mentions outside agentic-design (53 files at the start); the record opens with the flow; the old path is gone
- manual: step 8 — each doc read against steps 1 and 2's tests (the folder name, "never overwritten", the order wiki, toolset, framework doc); the one-source rule: no doc copies the README text or the Decision 3 line beyond what the framework docs carry
- manual: step 9 — before and after counts of `framework-docs|best-practices/framework` in agentic-design `wiki/` (128 in 84 files before; zero toward the toolset after); a link-resolve script run over every changed link; the list of links held for Mark's OK, in `checkpoints.md`
- manual: step 10 — the hub README and the folder `_INDEX.md` read: they list the three new pages and the lessons section, and no longer list `icarus-integration-plan.md`
- manual: step 11 — the 2026-11-13 decision file read: status superseded, pointing at this change's record
- Steps 6 and 7 are proved by tests for the form (the line, the link pattern, the rows, the versions). That every link resolves on this machine is manual: `manual: step 6 — a resolve script over the six links, output quoted in checkpoints.md`.

## Out of Scope
- Copying any agentic-design page into `framework-docs/`; a "master is agentic-design, do not edit" note; any drift check or refresh command comparing the two.
- Changing how skills and agents find the framework docs (`{{TOOLSET_DIR}}` paths stay).
- agent-builder and its notebook. The other agentic-design practice pages (memory architecture, CLAUDE.md authoring, corpus reviews, negative constraints).
- Other agentic-design links into llm-wiki outside the framework docs.
- Creating `local/` in existing wikis (added by hand when needed).
- The 231 status, component and 00-95 pages, beyond repointing the architecture-decisions mentions.
- Look-alikes outside Scope: none found for the create-if-absent write.
- Splitting into separate changes: the code and the notebooks share the docs' practice links and Mark settled one run (Decision 4), so no split is proposed.

## Scope
Repository (llm-wiki-bootstrap):
- `scripts/_install_tooling.py`
- `scripts/new-wiki.py`
- `seed/**`
- `framework-docs/**`
- `tests/scripts/**`
- `wiki-seed/**`
- `skills/new-wiki/**`
- `CLAUDE.md`
- `INSTALL-INVENTORY.md`
- `V2_ROADMAP.md`
- `CHANGELOG.md`
- `.claude/do-code-change.json` (an orchestrator config change on Mark's instruction, a signed `budget` entry; no plan step or test of its own)

Notebooks (committed in `C:\github.com\project-notebooks` by explicit path; not in this repository's diff):
- `notebooks/agentic-design/wiki/project/best-practices/**`
- `notebooks/agentic-design/wiki/project/lessons-from-llm-wiki/**`
- `notebooks/agentic-design/wiki/**` (the link repoints; every file the step 9 list names)
- `notebooks/agentic-design/wiki/research/implementation/architecture-decisions.md` (moved out)
- `notebooks/llm-wiki-bootstrap/wiki/project/decisions/**`
- `notebooks/llm-wiki-bootstrap/wiki/**` (the mentions of `architecture-decisions` to repoint)
- Any other notebook file the step 5 search names for `architecture-decisions`: listed in `checkpoints.md` before it is edited.

## Invariants
- A refresh still replaces a hand-edited listed file, removes a retired pack page and leaves another pack's folder alone, and the framework docs stay overwritten on install — pinned by the existing checks in `tests/scripts/test_global_toolset.py` ("the hand edit replaced", "the retired page removed", "another pack's folder untouched", "current again"), which must stay green.
- `toolset_status` ignores line endings — pinned by the existing "differing only in line endings" check.
- `--phase docs --check` exits 0 when current and 1 when a listed page is missing, and writes nothing — pinned by the existing checks at the end of `test_global_toolset.py`, plus step 1's `Failures:` for the stub.
- A user's CLAUDE.md, README and `.gitignore` are never overwritten by the scaffold (`skip_if_exists`). Whether an existing test pins this is unknown: the implementer searches `tests/scripts/` first; if none does, step 2's `Failures:` bullet writes one (a Phase B run over an existing CLAUDE.md keeps it).
- Skills and agents still name `{{TOOLSET_DIR}}/wiki/project/best-practices/framework/<doc>` — pinned by the existing "the ingester's reading list names the toolset's spec" and "install-skill fills {{TOOLSET_DIR}}" checks.
- `framework-contract: true` pages stay exempt from body checks, and the new relative link in a framework doc is not a lint error — pinned by `test_link_gaps.py` (its framework-doc fixture) staying green; the implementer also runs the mechanical lint on one doc in a temp wiki and quotes it.
- Nothing in `scripts/` reads or names the agentic-design notebook (the Exclusions) — checked by a grep for `agentic-design` over `scripts/` that finds no new hit; the output is quoted in step 1's hand-back.
- The toolset stub is never counted as stale: step 1's `Expected:` bullet.

## Decisions needed
none

## Steps

1. The global install puts a `local/` stub in the global toolset — done when the new checks in `tests/scripts/test_global_toolset.py` pass (seam A).
   uses: `seed_toolset`, `toolset_status` (`_install_tooling.py`); new function `seed_local_readme`, searched for: `skip_if_exists`, `_render_template`, found none that creates one file only when absent. Also adds the one shared README text under `seed/`.
   - Expected: on an empty temp toolset, `seed_toolset` creates `wiki/project/best-practices/local/README.md` with the shipped text's bytes, and returns `local: created`. `toolset_status` for that toolset is `current` (the README is not in add, replace or remove).
   - Expected: the toolset holds an extra user file `local/my-notes.md`: `toolset_status` is `current`, `remove` lists nothing from `local/`, and a refresh leaves the file's bytes alone.
   - Expected: the README deleted from an otherwise current toolset: `toolset_status` is still `current` and `--phase docs --check` exits 0; a plain `--phase docs` run then creates it again.
   - Expected: dry run on an empty toolset writes nothing and reports `would create`.
   - Failures: the README already exists with edited content → after a refresh its bytes are unchanged and `local` says `kept` (nothing overwritten, not removed). The toolset has `local/` holding only a user file and no README → the README is created and the user file is untouched. `local` exists as a plain file where the folder should be → the refresh does not raise and reports `kept`, nothing written (the framework docs are still refreshed).
   - Invariant: the existing refresh, remove and other-pack checks stay green.
   - Speed: none (no table, view or index; a file existence check per install).
   Trivial stakes: no

2. The `/new-wiki` scaffold creates `wiki/project/best-practices/local/README.md` in each new wiki — done when the new Phase B checks pass (seam B).
   uses: `seed_local_readme` from step 1.
   - Expected: Phase B into a temp target creates the README under the new wiki, with the same bytes as the shipped text, for `--project-folder stubs`, `empty` and `none`.
   - Expected: `--dry-run` prints `WOULD ...` for the folder and writes nothing.
   - Failures: a second Phase B run over a wiki whose README the user edited → bytes unchanged. A target that already has a CLAUDE.md → kept (the invariant). The README source file missing from the package → the scaffold stops with a named error and exit non-zero, and does not write a half-seeded `local/` (an empty folder counts as written: nothing is created).
   - Invariant: the three existing scaffold files (`_MAP.md`, `README.md`, `HOME.md`) are still rendered — pinned by an existing test if one exists, else a check here.
   Trivial stakes: no

3. Three practice pages exist in agentic-design, with the flow described and the two new tier rules in the frontmatter page — done when the evidence under `manual: step 3` is in `checkpoints.md` (no test: information pages).
   blocked by: none (starts after steps 1 and 2 so the code is proved first; no content dependency).
   - Read the notebook's own conventions first (frontmatter spec, `_INDEX.md`, lint) and note them in `checkpoints.md`.
   - Extract the practice text from the six docs (principles, compile-not-retrieve, scoring, contradictions, checkpoints; the tier rubric and field principles; context loading and memory signals) with our build specifics left out; fold in the practice reasons of the seven decisions where not stated. Write the flow (agentic-design says how; llm-wiki builds and records why; a departure sends a lesson back) in each page.
   - The frontmatter page carries both tier rules: official vendor post with something checkable (code, docs, public benchmark) is tier 2, pitch alone is tier 4; repositories: "read at least the README and sanity-check the main code (not all of a big repo); if unsure check size or that main functions work; else ask Mark".
   - No link to llm-wiki from any of the three pages.
   Trivial stakes: yes — information pages in a notebook; no code line a test could catch.

4. The lessons section exists, with the first pass from the seven decisions — done when the evidence under `manual: step 4` is in `checkpoints.md`.
   blocked by: 3.
   - `lessons-from-llm-wiki/README.md` states the flow and lists the lessons; one page per departure of a decision from the practice pages; a decision with no departure is named in the README as "no departure". A practice page changed by a lesson links to it. No link to llm-wiki.
   Trivial stakes: yes — information pages in a notebook; no code line a test could catch.

5. The architecture-decisions record lives in the llm-wiki-bootstrap notebook — done when the evidence under `manual: step 5` is in `checkpoints.md`.
   blocked by: 4.
   - `git mv` of the whole page to `wiki/project/decisions/` in that notebook; the flow written at its top; it stays not shipped and has no local file. The 53 mentions are repointed to the new place, except agentic-design pages, which follow step 9. A mention in a file outside the two notebooks' listed globs is listed in `checkpoints.md` before it is touched.
   Trivial stakes: yes — a move and link repoint in notebooks; no code line a test could catch.

6. Each of the six framework docs opens with the "Local changes" line and a practice link, with `framework-version` bumped — done when the new checks in `tests/scripts/test_standalone.py` pass (seam C), with the version floors updated to the new numbers.
   blocked by: 3 (the pages must exist for the links to resolve).
   - Expected: for each doc, the line directly under the frontmatter reads Decision 3's wording and names `project/best-practices/local/<its own file name>`; a `Practice page:` line follows with a relative link of the form in Implementation Decisions (rerank spec: the words "Practice page: none"); the version is at least the bumped number (10, 4, 4, 17, 20, 3).
   - Failures: a doc whose local line names another doc's file → the check fails; a `Practice page:` link not starting with `../../../../../agentic-design/wiki/project/best-practices/framework/` → fails; a doc still at its old version → fails.
   - Invariant: the existing floors for `cycle-step-return-format` (3) and the frontmatter doc (13) in `test_standalone.py` are raised to 10 and 20; they must still pass.
   - manual (also under Testing Decisions): the six links resolved on this machine.
   Trivial stakes: yes — doc text and version numbers only; no Python line.

7. The frontmatter doc carries the two tier rules, the new repository-tier cell and the three field fixes — done when the new checks in `tests/scripts/test_standalone.py` pass (seam C).
   blocked by: 3, 6.
   - Expected: the doc has the vendor-post tier rule (checkable → tier 2, pitch alone → tier 4); the repository cell holds the new sentence and no longer contains "code read beyond the README"; a `status` row names `proposed` and says `wiki-promote` strips it; the `origin` row says who writes it (the agent stamps it per the CLAUDE.md template; no script writes it) and keeps the four values; the `cycle_id` row says what the re-grep found.
   - Failures: a row naming `status: proposed` while `wiki-promote.py` no longer strips it → this is the plan's own assumption; the implementer greps first and reports a mismatch instead of writing the row.
   Trivial stakes: yes — doc text only; no Python line.

8. Every doc that describes framework docs and user edits says where a user's changes go — done when the evidence under `manual: step 8` is in `checkpoints.md`.
   blocked by: 1, 2.
   - Docs: `CLAUDE.md`, `INSTALL-INVENTORY.md` (also a row for the new `seed/` file), `V2_ROADMAP.md` only if the line at 56 still reads as wrong, `CHANGELOG.md`, `seed/how-to/_FRAMEWORK_MANAGED.md`, `wiki-seed/user-guide.md`, `seed/global-toolset-README.md`, the `/new-wiki` skill's wiki-seed page and SKILL.md if the scaffold change needs a line. Each points to the one source (the `local/README.md` text, the Line atop each framework doc) and copies no text from it. Skill or script text is not edited otherwise.
   Trivial stakes: yes — doc wording only; no Python line.

9. The 128 agentic-design links into the framework docs point at the practice pages — done when the evidence under `manual: step 9` is in `checkpoints.md`.
   blocked by: 3.
   - A scratch script (kept in the session scratchpad, never in the repository) first lists every link (file, line, target doc, idea) without editing. Links to wiki-authoring, frontmatter, tiered-context-loading and memory-signals go to the page covering that doc; links to the two mechanism docs, and any link that seems to need llm-wiki, are listed for Mark's OK and not edited until he answers. Then it rewrites the rest, including the form that points into agentic-design's own empty folder.
   - Failures: a link whose practice page lacks the idea → the idea is added to the practice page (not our build detail) or the link is listed for Mark; never left dead and never pointed at llm-wiki.
   Trivial stakes: yes — link repoints in notebooks by script; no repository code.

10. The best-practices hub and the framework folder's index list the new pages — done when the evidence under `manual: step 10` is in `checkpoints.md`.
    blocked by: 3, 4.
    - `README.md` hub lines 22-26, 44, 52-54 rewritten to list the practice pages and the lessons section; the folder's `_INDEX.md` drops `icarus-integration-plan.md` and lists the three pages.
    Trivial stakes: yes — index and hub text in a notebook; no code line a test could catch.

11. The 2026-11-13 decision is marked superseded — done when the evidence under `manual: step 11` is in `checkpoints.md`.
    blocked by: 5.
    - `wiki/project/decisions/wiki-building-practice-master-in-agentic-design-copied-into-llm-wiki-2026-11-13.md` in the llm-wiki-bootstrap notebook gets status superseded and a link to this change's record; the wiki's own supersede convention is read first. The wiki change-record and card are the finish step's.
    Trivial stakes: yes — one status line in a notebook; no code line a test could catch.
