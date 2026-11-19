## Facts

The request
- user confirmed (task #243 card, Mark 2026-11-13): (1) the gold master of each wiki-building practice doc lives in agentic-design; (2) `framework-docs/` holds a copy, refreshed from the master whenever it changes, never edited in llm-wiki; (3) each copy opens with a note (master is agentic-design `<path>`; the doc evolves from our agentic-design research; if unsure, agentic-design has the latest; do not edit this copy); (4) a user-editable page beside each framework page that references it, never overwritten by install or update; (5) a check that flags a copy differing from its master. The architecture-decisions page is included: its seven decisions stay in agentic-design as practice and ship under this design; only our build notes move to llm-wiki. Change type: do-code-change.
- user confirmed (card Log, 2026-11-12): three content fixes for the masters once the location is settled: L101 (frontmatter spec: `status: proposed`, `origin`, `cycle_id`), a tier-rubric rule for official vendor posts, and a repository-tier rule that replaces "code read beyond the README".
- user confirmed (standing rule, Mark 2026-11-10/13, as given in the brief): agentic-design = how we SHOULD do things; the llm-wiki-bootstrap notebook = what we HAVE built. Wiki-building practice is both: kept in agentic-design, shipped with llm-wiki as framework documents, users able to tweak their copy separately so updates still bring new practice.

What earlier records say
- wiki `llm-wiki-bootstrap/wiki/project/decisions/wiki-building-practice-master-in-agentic-design-copied-into-llm-wiki-2026-11-13.md`: the same five points as the card, with the reason. Copying at install time from the agentic-design notebook was rejected: someone installing from GitHub has the repo but not our notebook. So the copy lives in the repo, refreshed when the master changes. Its caveat: "Not built yet (#243): which documents count as wiki-building practice beyond the six framework docs, the copy step's shape, where the user page lives and how the skills read both."
- wiki `llm-wiki-bootstrap/wiki/project/decisions/global-toolset-one-notebook-for-every-tooling-doc-2026-10-05.md`: the six docs are installed once into the global toolset at `wiki/project/best-practices/framework/`; no project carries a copy; Mark rejected "pointer pages per project" and search over the toolset. Reason given: copies drifted behind their source.
- wiki `llm-wiki-bootstrap/wiki/sessions/main/231-split-plan.md` (task 231): marks `research/implementation/architecture-decisions.md` as "moves" to llm-wiki `project/decisions`. Mark's answers D1-D6 of 2026-11-11 do not mention it. The 2026-11-13 decision above supersedes that verdict: the seven decisions stay in agentic-design.
- earlier change records: `.do-code-change/archive/2026-11-15-240-report-fallbacks` and `2026-11-18-240-loud-backlogs` cite `framework-docs/cycle-step-return-format.md` (`framework-version: 9`). Neither touches how the docs are stored or installed. No earlier change record settles where framework docs live.

What the code does today
- found in `framework-docs/`: six docs, each with `framework-contract: true` and a `framework-version` (cycle-step-return-format 9, memory-signals 3, tiered-context-loading 3, wiki-authoring 16, wiki-frontmatter 19, wiki-search-bucket-rerank-spec 2).
- found in `scripts/_install_tooling.py:150-164` (`toolset_files()`): every `framework-docs/*.md` maps to `wiki/project/best-practices/framework/<name>` in the global toolset.
- found in `scripts/_install_tooling.py:178-198` (`toolset_status()`): compares only files the package lists, ignoring line endings; "replace" means the toolset file differs from the package file. The "remove" scan covers only `how-to/llm-wiki/` (top level, `skills/`, `agents/`). So a page added beside the framework docs is neither replaced nor removed today, and does not make the toolset "stale".
- found in `scripts/_install_tooling.py:216-234` (`seed_toolset()`): copies files over the toolset's on every global install; step 7 of the install; `--mode status` reports `toolset` stale when add/replace/remove is non-empty (`:1191-1203`).
- found in `scripts/new-wiki.py:772-812` (`phase_docs`): `--phase docs` refreshes only the toolset; `--phase docs --check` prints add/replace/remove, writes nothing, exits 1 when anything would change. This compares the package against the toolset. It never reads agentic-design.
- found in `scripts/wiki-update.py:1262-1265`: finds the frontmatter spec in the toolset, else `framework-docs/` beside `scripts/`. `scripts/_entry_checks.py:229` exempts any page with `framework-contract: true` from body checks.
- found in skills, agents and templates: about 20 files name `{{TOOLSET_DIR}}/wiki/project/best-practices/framework/<doc>` (wiki-claims, wiki-discover, wiki-lint, wiki-refresh, wiki-report, wiki-rollback, wiki-search, wiki-update, wiki-verify, wiki-ingester reading list, `templates/CLAUDE.md.tmpl`, `templates/feeds.md.tmpl`, `wiki-seed/user-guide.md`, `wiki-seed/obsidian.md`, `seed/global-toolset-README.md`, three skill wiki-seed pages). All point at the toolset copy.
- found in tests: `tests/scripts/test_standalone.py:121-132` asserts `framework-version` floors for two docs; `tests/scripts/test_global_toolset.py:74,117` checks the toolset's framework path; `tests/scripts/test_link_gaps.py:58` uses a fixture framework doc. No test compares a copy to a master.
- found in `CLAUDE.md:26,172`, `INSTALL-INVENTORY.md:72-73,187,205-208`, `V2_ROADMAP.md:56`, `CHANGELOG.md`: these call `framework-docs/` "the gold copies" and say an in-place edit is lost on refresh. All of them describe the old direction.
- found in `seed/how-to/_FRAMEWORK_MANAGED.md` and `wiki-seed/user-guide.md:165`: the toolset is "framework-managed", "Don't hand-edit files here. An edit made here is lost on the next refresh." The marker's own precedent for a diverging page is the project's wiki, `wiki/project/patterns/<your-doc>.md`, "never touched by a refresh". This text is about `how-to/`; the user guide line says it of the toolset's `framework/` docs too.
- found in `scripts/new-wiki.py:1093-1121`: `skip_if_exists=True` is how Phase B keeps a user's CLAUDE.md, README and `.gitignore`. It is the existing "never overwrite" mechanism, for project files only. No existing install writes a user-editable page into the toolset.
- found: no existing check compares an llm-wiki file to an agentic-design file. Searched `scripts/` and `tests/` for the master/copy idea: nothing.

What agentic-design holds today
- found in agentic-design `wiki/project/best-practices/framework/`: only `_INDEX.md`, which lists `icarus-integration-plan.md`, a page that moved to llm-wiki on 2026-11-12 (CHANGELOG line 69). The index is stale. The six docs are NOT in agentic-design.
- found in agentic-design: 128 matches of `framework-docs|best-practices/framework` in 84 files under `wiki/` (`.obsidian/workspace.json` included). The sampled form is a relative path into the toolset, `../../../../global-toolset/wiki/project/best-practices/framework/<doc>.md` (README.md, research/long-term/*, others), plus a few `../../project/best-practices/framework/<doc>.md` paths that point into agentic-design's own, now empty, folder.
- found in agentic-design `project/best-practices/README.md:22-26,44,52-54`: lists the framework docs as a hub, says their location is `best-practices/framework/`.
- found in agentic-design `research/implementation/architecture-decisions.md` (read whole): seven decisions with rationale and alternatives. It carries our build notes inside: Decision 2 status note (2026-10-30, federation shipped as skills plus two agents), Decision 4 "(Satisfied...)", Decision 6 "(Restated 2026-10-13...)" and the 2026-08-02 refinement, Decision 7's qmd v2.8.3 / preflight / "no cloud fallback" text and "Previous state", plus links into the toolset's how-to pages. It is `tier: self`. 53 files across the notebooks mention `architecture-decisions` (agentic-design pages, `_inbox` reports, 8 llm-wiki pages).
- found in `framework-docs/wiki-frontmatter-best-practices.md:58,126` and `scripts/wiki-update.py:830`: the spec's `origin` row lists `inline, wrap-up, wiki-update, wiki-cycle`; `wiki-update.py` writes `status: proposed` (line 830). The spec has no `status: proposed` row. `templates/CLAUDE.md.tmpl:94` tells agents to stamp `origin: inline`, so "no script writes `origin`" is true of scripts only. The `wiki-promote.py` strip and `cycle_id` were taken from the card, not re-verified in this run.
- found in `framework-docs/wiki-frontmatter-best-practices.md:126`: the repository row says "its code read beyond the README", the cell the card replaces.

Rules that settle points
- follows from card (2) "never edited in llm-wiki" and the Log "Fix in the master": the three content fixes are made in the masters. They reach `framework-docs/` only through a refresh, never by hand-editing the copy.
- follows from card (2): `CLAUDE.md`, `INSTALL-INVENTORY.md`, `V2_ROADMAP.md`, `CHANGELOG.md` and the user guide stop calling `framework-docs/` the gold copy. The change updates every page that names the old direction (the wiki pattern "find every page naming a changed thing before docs are done").
- follows from card (4) "beside each framework page": the framework pages themselves stay installed at `wiki/project/best-practices/framework/` in the toolset, so the `{{TOOLSET_DIR}}/wiki/project/best-practices/framework/<doc>` links in skills and agents keep their form.
- follows from the 2026-11-13 decision "Copying at install time from the agentic-design notebook was rejected": the install and `--phase docs` copy from the repo's `framework-docs/`, never from agentic-design.
- follows from card (2) "refreshed from agentic-design whenever the master changes": the framework version number (`framework-version`) is set in the master and carried unchanged in the copy.
- follows from card (3): the note names the master's path, and says the doc evolves from agentic-design research, that agentic-design has the latest, and not to edit the copy.
- follows from card (4) "never overwritten by install or update": the install, `--phase docs` and any refresh create the user page only when it is absent and never rewrite or delete it.
- follows from the standing "code change means test change" practice (memory, Mark 2026-10-19): tests that assert the old direction are updated with the change, and the new refresh and check get their own tests.
- decided by the run under the brief's note that implementation detail is not asked: no Decision here about the check's code structure, which module holds it, or how the compare is written.

## Exclusions

- No copying from the agentic-design notebook at install time. The repo copy is what ships.
- No automatic trigger when a master changes. The copy is refreshed by a deliberate step.
- No change to how skills and agents find the framework docs (`{{TOOLSET_DIR}}` placeholder, the toolset path).
- No change to the content of the six docs beyond the three card fixes and the note. Other pending doc edits are not part of this.
- No change to agent-builder, its library or its notebook.
- No move of other agentic-design best-practice pages (memory architecture, CLAUDE.md authoring, the corpus reviews, negative constraints). They are general practice that llm-wiki does not ship.
- No change to the 231 split (status pages, component pages, 00-95 pages) except where the architecture-decisions build notes land.
- No new gate on a normal install or `--mode status`: a machine without the agentic-design notebook installs exactly as today.
- No rewrite of the research content in agentic-design that merely cites a framework doc, other than repointing its link to the master.

## Decisions

Ordered most important first. Decisions marked "depends on" come after the one they depend on.

1. Which docs count as wiki-building practice docs (decides the scope of everything below).
   - Recommended: all six. The 2026-11-13 decision treats "the six framework docs" as the starting set and its open question only asks for docs "beyond" them. One kind of framework doc keeps one edit rule, one note, one check.
   - Alternative: only the four practice docs (authoring, frontmatter, tiered context loading, memory signals). The cycle-step return format and the search rerank spec describe mechanisms we built ("what we HAVE"), so they would stay owned by llm-wiki, edited in the repo, outside this design.
   - Visible effect: with the alternative, two docs would keep the old "gold copy" rule and the user page and check cover four docs.

2. How the run splits across repositories. do-code-change does not attempt multi-repo coordination (from the brief). The masters, the 84 link repoints and the content fixes live in project-notebooks; the copy note, user page, refresh and check, docs and tests live in llm-wiki-bootstrap.
   - Recommended: the run's diff and its tests cover llm-wiki-bootstrap only. Moving the six masters into agentic-design, repointing the links, and the three content fixes are notebook edits, done as manual plan steps with their evidence recorded (script output, a link count before and after, a commit in project-notebooks), as the 2026-10-05 move did (157 links repointed by script). The refresh then runs once against the finished masters.
   - Alternative: do the notebook edits first by hand in a separate change, then run this one against masters that already exist. Or: let the run write into the notebooks too.

3. Where the user-editable page lives (card: "beside each framework page"). The toolset's own text says edits there are lost and sends divergence to the project wiki. This reverses that text for the `framework/` folder: `_FRAMEWORK_MANAGED.md`: "Don't hand-edit files here. An edit made here is lost on the next refresh." and `wiki-seed/user-guide.md:165`: "a local edit is overwritten. Ask for the change in the framework instead." It also sits near the 2026-10-05 rejection of "pointer pages per project". It is not a pointer: it holds the user's own changes.
   - Recommended: in the global toolset, next to each framework page in `wiki/project/best-practices/framework/`. This is one page per machine, as the framework pages are, and the card says "beside". The install creates it only if absent. The two texts above are corrected to say the framework pages are overwritten but the user page beside them is not.
   - Alternative: in each project's wiki, `wiki/project/best-practices/` (the marker's existing precedent). Per project, but then "beside" is not literal, and every `/new-wiki` project would need the page.

4. Where the masters live in agentic-design (depends on 1).
   - Recommended: the six at `project/best-practices/framework/<same file name>` in agentic-design (the folder exists, holding only a stale `_INDEX.md`, which the index tool regenerates). Same file names keep the note's path simple. The master path in the note is written in the existing form `agentic-design :: project/best-practices/framework/<doc>.md`.
   - Alternative: a differently named folder in agentic-design, or the docs next to the pages they relate to.

5. What happens to the ~84 agentic-design files that link into the toolset copy (depends on 4).
   - Recommended: repoint every such link to the master in agentic-design, by script, and update the best-practices `README.md` hub. If unsure, a reader of agentic-design should land on the master, as the note says.
   - Alternative: leave the links on the toolset copy (they still resolve), accepting that agentic-design pages cite a copy.

6. What a copy is and what "differs from its master" means.
   - Recommended: the copy is the master byte for byte (line endings ignored, as `toolset_status()` does today), except one note block inserted directly after the frontmatter, so the frontmatter stays first. The note text is the card's four statements in one short block quote, naming the master path. "Differs" means: copy with the note removed is not equal to the master. Frontmatter is compared too, so `framework-version` and `framework-contract` are part of what must match.
   - Alternative: compare body only, or compare only `framework-version`. Cheaper, but a body edit made in the copy by mistake would go unnoticed, which is the case the check exists for.
   - Visible: the exact note wording and its place appear at the top of every installed framework doc.

7. How a copy is refreshed from its master (depends on 4 and 6).
   - Recommended: a script command in the repo that reads the agentic-design root from the registry, writes each copy with the note, and reports what changed. It runs by hand after a master changes. The docs-change procedure in `CLAUDE.md` gains this step before `-RefreshOnly`.
   - Alternative: by hand (copy and paste the note), with the check as the only safeguard. Or a git hook in project-notebooks. Neither is recommended: by hand repeats the 2026-09-08 seeder-dropped-text kind of failure.

8. Where the check runs and what it does on drift (depends on 7).
   - Recommended: the same command with a check flag (no writes). It prints each drifted doc and exits 1. It runs where the agentic-design notebook exists; where it does not, it says "master not found, not checked" and exits 0, so a GitHub install never fails on it. It is not part of `--mode status`, install, or `--phase docs --check`. The docs-change procedure runs it before commit.
   - Alternative: run it inside `--mode status` or the lint (would make installs and status depend on the notebook), or as a pre-commit hook (blocks commits without the notebook).

9. The user page's name and first content (depends on 3).
   - Recommended: `<framework-doc-name>-local.md` beside the doc, for example `wiki-authoring-best-practices-local.md`. First content: a short title, one link to its framework page, and one line saying "Your changes go here. Install and update never overwrite this page; the framework page above is overwritten."
   - Alternative: a different suffix (for example `-my-changes`), or a single `LOCAL.md` for all six.
   - Visible: the file name appears in the toolset folder and in the docs.

10. Does any tool or skill read the user page (depends on 3 and 9)? The 2026-11-13 decision lists "how the skills read both" as open.
    - Recommended: no script and no skill reads it in this change. It is a page for people, and for agents a person points at it. A change that makes it a rule agents must follow is a separate request. The page links to its framework page; the framework page's note says the user page exists.
    - Alternative: skills and agents that load a framework doc also load its user page, with the user page winning on conflict. This adds behaviour to about 20 skill and agent files.

11. The architecture-decisions page: what moves to llm-wiki and whether it becomes a seventh framework doc.
    - Recommended: yes, a seventh doc, so the repo copy, note, user page and check apply to it. Its seven decisions with rationale and alternatives stay in the master. The build notes move to a new llm-wiki `project/decisions` page: the Decision 2 status note, Decision 4's "(Satisfied...)", Decision 6's "(Restated...)", Decision 7's qmd version, preflight and "no cloud fallback" text and "Previous state", and the links into our how-to pages. The master keeps a short pointer for each decision to that page. The card's exact reading of "build notes" is not stated, so this split is the assumption. This differs from the 231 plan, which said the whole page moves.
    - Alternative: the page stays in agentic-design as practice and is not copied (the card says "ship under this design", so this is not recommended). Or the whole page moves to llm-wiki, as the 231 plan proposed, which the 2026-11-13 decision overrides.
    - Includes: whether the seventh doc carries `framework-contract: true`. Recommended: yes, so it is handled like the others (the flag only exempts it from body checks, `_entry_checks.py:229`).

12. Where the architecture-decisions master sits in agentic-design (depends on 11).
    - Recommended: stay at `research/implementation/architecture-decisions.md`. 53 files already link there, so no repoint is needed. The note names that path.
    - Alternative: move it into `project/best-practices/framework/` beside the others, and repoint those links. One home for everything shipped, more link edits.

13. Whether the three content fixes are in this change (depends on 4).
    - Recommended: in this change, made in the masters before the first refresh, so the first copy already carries them and `framework-version` of the frontmatter spec rises once. The fixes are: add `status: proposed` (written by `wiki-update.py`, removed on promotion) and `cycle_id` to the spec and correct the `origin` row to say who writes it (the CLAUDE.md template stamps `inline`); the tier rule that an official vendor post with something checkable behind it (code, docs, a public benchmark) is tier 2 and one that is pitch alone is tier 4; the repository-tier cell reading "read at least the README and sanity-check the main code (not all of a big repo); if unsure check size or that main functions work; else ask Mark". The `wiki-promote.py` strip and `cycle_id` are checked against the code during the fix.
    - Alternative: a follow-up change after the move, so the move can be verified as a pure copy. The check then proves the move changed nothing.
    - Visible: the tier rules change what `/wiki-update` and the lint judge from the day it ships; tests that assert tier text (for example the skill-test baselines) may need a new case.
