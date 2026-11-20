# 2026-11-20 243-framework-docs-master — framework docs move to wiki/best-practices/framework, user changes go in best-practices/local

## TL;DR
The global install now writes the six framework docs to the toolset's `wiki/best-practices/framework/` and removes the old `wiki/project/best-practices/framework/` copy. A `wiki/best-practices/local/` folder, with one shipped README, sits in the toolset and in every new wiki for the user's own changes, and each framework doc opens with a "Local changes" line and a link to the agentic-design practice page it follows. This settles Mark's 2026-11-19 design: agentic-design holds how a wiki should be built, llm-wiki holds how it is built and links to it, and nothing copies or compares between them. Full path, 4 review rounds and 3 verify rounds; verify PASS, merged into main (fast-forward) on Mark's "Merge please".

## What changed
- 1. The global install writes the framework docs to `wiki/best-practices/framework/` in the toolset and removes the old copy
- 2. The toolset carries `wiki/best-practices/local/README.md` as a framework file, and the user's files beside it are left alone
- 3. A new wiki gets `wiki/best-practices/local/README.md`, for every `--project-folder` answer
- 4. `/wiki-search` finds notes in `best-practices/` and `best-practices/local/`, and lint treats files in `local/` as entries
- 4b. `_MAP.md` lists notes in `best-practices/` (the framework docs aside, which a wiki never holds)
- 5. Every shipped file that names the old toolset framework path names the new one
- 6. The agentic-design hub and three practice pages exist in `wiki/research/wiki/`, with the flow described and the two new tier rules in the frontmatter page
- 7. The lessons section exists in `wiki/research/wiki/lessons-from-llm-wiki/`, with the first pass from the seven decisions
- 8. The architecture-decisions record lives in the llm-wiki-bootstrap notebook
- 9. Each of the six framework docs opens with the "Local changes" line and a practice link, with `framework-version` bumped
- 10. The frontmatter doc carries the two tier rules, the new repository-tier cell and the three field fixes
- 11. Every doc that describes framework docs and user edits says where a user's changes go
- 12. `templates/CLAUDE.md.tmpl` tells every new project's agents where a project's own changes to a framework doc go
- 13. The 128 agentic-design links into the framework docs point at the practice pages
- 14. The llm-wiki-bootstrap notebook's live pages no longer link the old toolset path
- 15. The agentic-design hub pointer and indexes are right, and the stale framework folder is gone
- 16. The 2026-11-13 decision is marked superseded, and the 2026-10-05 decision gets a layout note
- 17. `/new-wiki`'s changed behaviour passes new cases red then green on both models, and the other skills' changes are logged

New tags: `framework-docs` (tooling), `global-toolset` (tooling).

## Why: decisions and exclusions
All settled with Mark on 2026-11-19 (terminal, then his Discord DM); his words are in `checkpoints.md`. Each is a decision, with the alternative turned down.

1. The practice side in agentic-design: a new topic folder `wiki/research/wiki/` holding a hub `wiki-best-practices.md` (overview, the flow, links to the three pages, the lessons section, the existing wiki research entries and the memory page) and three practice pages `wiki-best-practices-authoring.md`, `wiki-best-practices-frontmatter-and-tiers.md`, `wiki-best-practices-context-loading.md`, extracted from the practice text of today's docs with our build specifics left out: (a) wiki authoring (principles, compile-not-retrieve, scoring, contradictions, checkpoints); (b) frontmatter and source tiers (the tier rubric with the two new tier rules, the field principles); (c) context loading and memory signals. The practice reasons in the architecture-decisions page are folded in where not already stated. The two mechanism docs (cycle step format, rerank spec) get no practice page. The pages describe the flow of Decision 2 so it is clear there. agentic-design's empty `project/best-practices/framework/` is removed; its other `project/` pages stay. Turned down: one single page; writing the pages fresh from research; `project/best-practices/` (Mark: agentic-design is research, not project).

2. The architecture-decisions page moves whole to the llm-wiki-bootstrap notebook `project/decisions/` as our decision record: not a framework doc, not shipped, no local file. The flow (agentic-design says how to build; llm-wiki builds and records why; a decision that departs from the practice sends the lesson and its reason back to agentic-design) is written at the top of the record and in the agentic-design practice pages. First pass now: while extracting the practice pages, the seven decisions are compared with them; each departure becomes a lesson (Decision 5). No automated conflict detection. The 19 live pages that mention it are repointed to the record's new place (agentic-design pages to the practice pages, Decision 5); records are left; the 3 machine files are listed for Mark before any edit. Turned down: a seventh framework doc.

3. How the local changes are found: each framework doc opens with a line naming its local files and the order: "Local changes: `best-practices/local/<this doc's name>` in the wiki you are working in, then the toolset's `local/<this doc's name>`, hold this install's own changes. Read them after this doc; where they differ, the wiki's local file wins, then the toolset's, then this doc." No skill or script code reads the local files. Turned down: a mention in the install docs only; every skill loading the local file.

4. Repositories: the run's code and tests cover llm-wiki-bootstrap. The run also writes the notebook pages (agentic-design practice pages, lessons section, link repoints, README hub; the llm-wiki-bootstrap notebook's decision record and the superseded 2026-11-13 decision) as plan steps with no tests, each a `manual:` step with its evidence, committed in project-notebooks by explicit path. The practice pages are written before the framework docs get their practice links. Turned down: a separate notebook task first.

5. agentic-design does not link to llm-wiki. Every agentic-design link into the framework docs (128 links in 84 files) is repointed to the practice page covering that idea; where a page needs more than the idea, the idea is written into the practice page, not our build detail. Any link that seems to need llm-wiki is listed for Mark's OK, never decided silently. New: an agentic-design section `wiki/research/wiki/lessons-from-llm-wiki/` (a README stating the flow, one page per lesson); a practice page changed by a lesson links to the lesson; it starts with what the seven decisions turn up. The `project/best-practices/README.md` hub points at the new hub. llm-wiki-bootstrap's own CLAUDE.md and its notebook's live pages naming the old toolset path are repointed in this run (journals and archived reports left as records); other projects' files are card #248. Other agentic-design links into llm-wiki are out of this change. Turned down: repoint none; repoint all regardless.

6. Each llm-wiki framework doc names the agentic-design practice page it follows with a real relative link (Mark: "That's what we use everywhere else"); dead for a GitHub install without agentic-design, accepted. Turned down: a plain-text `agentic-design :: <path>` line.

7. The local folders: `wiki/best-practices/local/` (beside `wiki/best-practices/framework/`) holding one README (what the folder is, that it is for the user's own changes, to name a file after the framework doc it changes; it has frontmatter that passes lint); no starter file per doc. Written (a) in every new wiki by the `/new-wiki` scaffold when it creates the wiki, whatever `--project-folder` says, and (b) in the global toolset by the global install. In the toolset the README is ours: install and `--phase docs` replace it when it differs. Every other file in `local/` is the user's: never added, changed or removed. In a wiki, those files are entries: linted as entries and searched (`/wiki-search` covers `best-practices/`); the toolset's `local/` is, like the rest of the toolset, hidden from lint and search (`10-install-and-setup.md:217`). Phase B re-run behaviour is unchanged (Mark: "Drop the re run"). Existing wikis are retrofitted by hand on card #248. Turned down: `<name>-local.md` beside each doc; a starter file per doc; `project/best-practices/local/`; `_config/local/`; skipping `local/` notes in lint or search; changing what a Phase B re-run writes.

Size: full (open design pieces; install, `--mode status` and about 20 skills use what changes). Branch: `features/243-framework-docs-master`, created after the clarify notes are committed on main (Mark: "Let's do branch. Although we should commit everything we have here first before we branch").

- No copy of any agentic-design page into `framework-docs/`, and no copy step.
- No "master is agentic-design, do not edit this copy" note on the framework docs.
- No check, in any command, that compares llm-wiki docs with agentic-design pages.
- No change to how skills and agents find the toolset (`{{TOOLSET_DIR}}` placeholder); only the path under it changes.
- No change to agent-builder, its library or its notebook.
- No retrofit of existing wikis or other projects' files (card #248), except llm-wiki-bootstrap's own CLAUDE.md and its notebook's live pages.
- No move of the other agentic-design practice pages (memory architecture, CLAUDE.md authoring, corpus reviews, negative constraints).
- No change to the 231 status, component and 00-95 pages beyond link-only repoints (the architecture-decisions move, and the old toolset path per Mark's Choice B); prose that names the old path is the finish step's wiki record.
- No change to Phase B re-run behaviour (Mark: "Drop the re run"); the scaffold is for creating a wiki.
- No new gate on a normal install or `--mode status`: a machine without the agentic-design notebook installs exactly as today.
- The field fixes are not added to agentic-design: they describe our build.

## What the review found
- standards-1 [important]: `CHANGELOG.md` (2026-11-19 entry, "What" bullet) with `scripts/wiki-upgrade.py:68-69` and `scripts/new-wiki.py:510-514` — G4: a failed write on the global refresh path prints FA... — addressed
- standards-2 [important]: `tests/scripts/test_global_toolset.py:459` — T4: a skipped case records a PASS. Quote: `check("unwritable README: skipped, root writes through a read-only file (nothing proved h... — addressed
- standards-3 [important]: `tests/scripts/test_standalone.py:170` — R26: new constant nothing uses. Quote: `PRACTICE_PAGE_ROOT = "notebooks/agentic-design/wiki/research/wiki/"`; grep finds only the defini... — addressed
- standards-4 [suggestion]: `scripts/_install_tooling.py:200` — S15: the clause can never be false, so it is dead logic. Quote: `if TOOLSET_OLD_FRAMEWORK_DOCS / p.name not in files] if old_docs.is_dir() el... — addressed
- standards-5 [suggestion]: `scripts/wiki-map-compile.py:375` — C2: stale comment beside the changed line 378. Quote: `# Container folders (research/, project/) hold subfolders instead of direct` beside `C... — addressed
- standards-6 [suggestion]: `scripts/_wiki_config.py:103` — C2: the comment no longer matches what the scaffold creates. Quote: `# What a default scaffold creates: both halves with stubs, plus sessions/.`... — addressed
- standards-7 [suggestion]: `scripts/_wiki_config.py:112` — S7: the folder list is kept in two places and the diff updated one. Quote: `MERGED_TAXONOMY = (RESEARCH_TAXONOMY + LEGACY_RESEARCH_TAXONOMY + PRO... — addressed
- standards-8 [suggestion]: S2: duplicated test code added in this diff: `def _run(fn):` with the same body at `tests/scripts/test_global_toolset.py:561`, `tests/scripts/test_local_folder.py:418`, `tests/s... — open
- standards-9 [suggestion]: `tests/scripts/test_global_toolset.py:166`, `:189`, `:203` — T4: `if sys.platform != "win32": ... return` records no check on other platforms, so the check count differs by OS a... — addressed
- standards-10 [suggestion]: `scripts/_install_tooling.py:222` — N7: `def _guarded(op, path, failed: list) -> bool:` appends to its `failed` argument and the name does not say so. Fix: rename to say it reco... — open
- standards-11 [suggestion]: `tests/skills/new-wiki/check.py:372` — R15: `add("local/README.md names the framework docs", bool(re.search(r"framework", body, re.I)))` passes on the bare word. Fix: match the... — open
- standards-12 [nit]: Tail, grouped by root cause: C2 at `scripts/_install_tooling.py:145` and the `phase_docs` docstring at `scripts/new-wiki.py:773-775` (neither lists the local README the same fun... — open
- spec-1 [important]: `.do-code-change/243-framework-docs-master/checkpoints.md:92` — step 17's red-then-green is not met for `local-readme-project-none`, which passed on the old copy on both models,... — addressed
- spec-2 [suggestion]: `scripts/wiki-update.py:710` — `--folder best-practices/local` is refused in any wiki that lacks `wiki/best-practices/`. Intent: "folder guards ... that rejects or mishandles be... — open
- spec-3 [suggestion]: `tests/skills/new-wiki/check.py:391` — the shared scaffold guard still names the old path, so it cannot fail. Intent: "its path moves to `wiki/best-practices/framework` because... — open
- spec-4 [nit]: `scripts/wiki-map-compile.py:375` — comment not updated after `best-practices` joined the set (plan step 4b); line 378 is `CONTAINER_FOLDERS = {"research", "project", "best-prac... — addressed
- spec-5 [nit]: `scripts/_wiki_config.py:103` — the SCAFFOLD_TAXONOMY comment is stale (leftover 2): "What a default scaffold creates: both halves with stubs, plus sessions/." while `taxonomy_f... — addressed
- spec-6 [nit]: `.do-code-change/243-framework-docs-master/plan.md:188` — the expected `wiki_folders` entry in `.claude/wiki-config.json` is not met. Intent: "`best-practices` is in the wiki's... — open
- spec-7 [nit]: `CHANGELOG.md`, 2026-11-19 entry, "What" bullet — "finishes the rest and exits 1" holds for `--phase docs` only. Intent: "`phase_docs` exits 1 with `FAILED <path>: <reason>`; th... — addressed
- risk-1 [important]: [important, needs-a-human] `scripts/new-wiki.py:510-514` (and `:911-916`), `scripts/wiki-upgrade.py:68-69` — a global refresh whose toolset write or remove failed still exits 0.... — addressed
- risk-2 [suggestion]: [suggestion, needs-a-human] `scripts/_install_tooling.py:198-200` and `:254-256` — the remove scan follows whatever `root / wiki/project/best-practices/framework` resolves to. N... — open
- risk-3 [suggestion]: `framework-docs/wiki-frontmatter-best-practices.md` (vendor-post paragraph and the tier 2 row) — ingest behaviour changes with an undefined test. Quote: "An official vendor post... — open
- risk-4 [suggestion]: `scripts/wiki-update.py:680-681` (validate_folder Case 1: "top segment already exists on disk … safe regardless of taxonomy") — every new wiki now has `wiki/best-practices/` (`_... — open
- standards-13 [suggestion]: S2 `scripts/_wiki_config.py:114` and `:136`: `"best-practices/local"` is now written in `MERGED_TAXONOMY` and again in `taxonomy_for()` (`folders.append("best-practices/local")`... — open
- standards-14 [suggestion]: PY9 `tests/scripts/test_global_toolset.py:635-638`: the scaffold test discards stderr and asserts only `code == 1 and not target.exists()`. Traced against `phase_b` (new-wiki.py... — addressed
- standards-15 [suggestion]: R14 `tests/scripts/test_global_toolset.py:575` (`sys.modules[module_name] = mod`) and `tests/scripts/test_local_folder.py:420`: modules are loaded under fixed names and register... — open
- standards-16 [suggestion]: T4 `tests/scripts/test_global_toolset.py:172-174, 196-198, 211-213, 469-471`: the `_skip` cases record no check, so off Windows (and as root) the held-file and read-only behavio... — open
- standards-17 [nit]: `scripts/new-wiki.py:779-780`: the reflowed `phase_docs` docstring leaves a short line ("global-toolset notebook. No project wiki") before "carries a copy any more". Fix: reflow... — addressed
- spec-8 [suggestion]: `scripts/new-wiki.py:920`: the scaffold's failure message says "fix and re-run", but a re-run only warns and goes on. Intent: CHANGELOG.md:16 "a scaffold's `--install-global-if-... — addressed
- spec-9 [nit]: `CHANGELOG.md:16`: "A refresh that cannot write or remove one file now lists it as `FAILED`, finishes the rest and exits 1" holds only for toolset files; `_install_tooling.py:64... — addressed
- spec-10 [nit]: `plan.md:23`: step 1 says the global install "prints them the same way and says the refresh is incomplete", with no exit code and no scaffold stop; the fix round added both (`ch... — open
- risk-5 [important]: `scripts/new-wiki.py:925`: a re-run after a failed toolset write warns and proceeds instead of stopping or refreshing. `global_tooling_status` reports the toolset as stale, not... — addressed
- risk-6 [suggestion]: `scripts/_wiki_config.py:114` with `scripts/wiki-promote.py:109-112`: `MERGED_TAXONOMY` gaining `best-practices/local` makes a bare `local` leaf auto-prefix to `best-practices/l... — open
- risk-7 [suggestion]: `scripts/_install_tooling.py:199-201`: the old-docs scan lists every `*.md` under `wiki/project/best-practices/framework` for removal with no name check. The removed `not in fil... — open
- risk-8 [suggestion]: `scripts/wiki-upgrade.py:68-72`: a sibling of the fix's toolset check, outside its hunk and outside what the brief named. It tests only `toolset.failed`, not `frontmatter_failed... — addressed
- standards-18 [suggestion]: S2 `scripts/new-wiki.py:920-922` and `:931-933`: the remedy text "`install-wiki.ps1 -RefreshOnly` (or `new-wiki.py --phase docs` ...)" is written out twice in the diff, and the... — open
- standards-19 [suggestion]: S2/S7 `scripts/new-wiki.py:515` and `scripts/wiki-upgrade.py:74`: `"the global toolset refresh is incomplete (see the FAILED lines above) — fix and re-run"` keeps the vague word... — open
- standards-20 [nit]: S1 `scripts/new-wiki.py:927`: `differs` reads like a flag but holds stale item names. Fix: `stale_names`. — open
- standards-21 [nit]: `scripts/new-wiki.py:929` says "toolset docs" where `scripts/_install_tooling.py:1279` says "global toolset docs": one state, two names. Fix: pick one. — open
- standards-22 [nit]: C3-adjacent `scripts/new-wiki.py:780`: the docstring reflow leaves the short line "    A global install (`--mode tooling`," before the next. Fix: rewrap the paragraph. — open
- standards-23 [nit]: T1 `tests/scripts/test_global_toolset.py:602-612`: the new wiki-upgrade test checks only `code == 1`, not the new stderr text. Fix: also assert the "refused" message, as the sca... — open
- spec-11 [suggestion]: `scripts/new-wiki.py:920-922`: the failed-write message says "free the file named there", but the FAILED line names the file being written, not the blocker. Intent: plan.md line... — open
- spec-12 [suggestion]: `scripts/new-wiki.py:927-933`: when the stale cause is only the uv environment, `differs` is empty and the warning names nothing. Intent: CLAUDE.md Step 0, "a stale set is named... — open
- spec-13 [nit]: `scripts/new-wiki.py:920-922`, `:931-933`, `:514-516`, `:916-918`, `:819-821`, `scripts/wiki-upgrade.py:73-76`: sibling "fix and re-run" messages name no repair path as phase_b'... — open
- spec-14 [nit]: `install-wiki.ps1:120` (`[switch]$RefreshOnly`) and `install-wiki.sh:66,85` (`REFRESH_ONLY`) are parsed but never read (Grep: no other use), so the repair `install-wiki.ps1 -Ref... — open
- standards-24 [suggestion]: `tests/scripts/test_local_folder.py:25` (C3 / Python): the removed `# noqa: E402` leaves `import _wiki_config as wc` with no recorded reason for sitting after the `sys.path.inse... — open
- standards-25 [nit]: `tests/scripts/test_search_mode.py:323` (G4): `gpu = lambda: ("cuda", "CUDA: available")  # noqa: E731` (and `:324`) is a suppression in a file this window edited. It predates t... — open
- spec-15 [important]: `.do-code-change/243-framework-docs-master/plan.md:189` — the clause "`.claude/wiki-config.json`'s `wiki_folders` keeps only the interview's two answers (`project`, `research`)"... — addressed
- spec-16 [suggestion]: `plan.md:26` — still says `taxonomy_for`'s one caller "`new-wiki.py:1016` ... also feeds `wiki_folders_md` ... and `.claude/wiki-config.json`'s `wiki_folders`", which contradict... — open
- spec-17 [suggestion]: `plan.md:32` — "so the mechanical lint finds nothing in it" contradicts plan.md:190 and checkpoints.md:83 (the lint does draw findings on the new README, the same as HOME.md). F... — open
- spec-18 [suggestion]: `plan.md` step 17 (lines 297, 303, 306) — the literal done criterion ("every case 'red then green' on Sonnet and Opus"; "a case that passes on the old copy: not counted as proof... — open
- spec-19 [nit]: `plan.md:49` — red-team history "step 3 lints a freshly scaffolded wiki and expects no finding from `best-practices/`" is superseded by line 190. Fix: mark it superseded. — open

## What was verified
- tests: PASS — four named suites exit 0 ("91/91 passed", "23/23 passed", "40/40 passed", "82/82 passed"); rest of `tests/scripts/` 61 files exit 0 with 0 FAIL lines, `test_fetch_repo.py` exit 1 "11/27 passed" (16 FAIL lines), the same count and failures as at the fixed point in rounds 1 and 2
- diff-contains-fix: PASS — every file the plan's steps name is in `git diff 7b66e2a… --stat` (55 files, 2001 insertions, 103 deletions), nothing untracked or uncommitted, notebook repository clean
- findings-addressed: PASS — review-ledger.py exit 0, "review-ledger: met - no open blocking item, every verdict current (7 closed, 45 non-blocking), 4 round(s)" / "review-ledger: exit 0 - met"
- frozen-tests: PASS — check-freeze.py exit 0, "frozen-tests layer: PASS — 86 entries checked (+ 164 from earlier changes), all match or unfrozen with a reason (7 retired: deleted on purpose) (118 frozen green, each with its reason)" / "check-freeze: exit 0 - PASS: every frozen test matches, or changed with a reason"
- coverage: PASS — every plan step's done criterion maps to an `existing` test or a `manual:` line in plan.md's Testing Decisions; row 3c is now `manual: step 3` (plan.md:79); step 17 is manual and met only under Mark's recorded ruling (spec-18 open, non-blocking)
- bar-unmoved: PASS — floor-guard.py exit 0, "floor-guard: exit 0 - clean: no move lowers the bar"
- in-scope: PASS — scope-guard.py exit 0, "scope-guard: exit 0 - PASS: every touched file is inside the declared scope"
- tests-bite: off — on demand by project setting (Mark, 2026-11-20), prove_tests_bite.py `--check` exit 4, "tests-bite layer: OFF - mutation testing is on demand in this project (.claude/do-code-change.json: decided by Mark, 2026-11-20); no pass runs with each change (exit 4)" / "VERDICT: OFF"

VERDICT: PASS

## Working files
Unchanged copies in the notebook's raw folder; the same files are archived in the code repository at `.do-code-change/archive/2026-11-20-243-framework-docs-master/`.

- [budget.json](../../../raw/code-changes/2026-11-20-243-framework-docs-master/budget.json)
- [checkpoints.md](../../../raw/code-changes/2026-11-20-243-framework-docs-master/checkpoints.md)
- [doubt-log.md](../../../raw/code-changes/2026-11-20-243-framework-docs-master/doubt-log.md)
- [hand-mutation-result.json](../../../raw/code-changes/2026-11-20-243-framework-docs-master/hand-mutation-result.json)
- [hand-mutation.py.txt](../../../raw/code-changes/2026-11-20-243-framework-docs-master/hand-mutation.py.txt)
- [implement-log.md](../../../raw/code-changes/2026-11-20-243-framework-docs-master/implement-log.md)
- [name-review.md](../../../raw/code-changes/2026-11-20-243-framework-docs-master/name-review.md)
- [parked.md](../../../raw/code-changes/2026-11-20-243-framework-docs-master/parked.md)
- [plan-red-team-round-1.md](../../../raw/code-changes/2026-11-20-243-framework-docs-master/plan-red-team-round-1.md)
- [plan-red-team-round-2.md](../../../raw/code-changes/2026-11-20-243-framework-docs-master/plan-red-team-round-2.md)
- [plan-red-team.md](../../../raw/code-changes/2026-11-20-243-framework-docs-master/plan-red-team.md)
- [plan.md](../../../raw/code-changes/2026-11-20-243-framework-docs-master/plan.md)
- [readonly-red-team.json](../../../raw/code-changes/2026-11-20-243-framework-docs-master/readonly-red-team.json)
- [readonly-review.json](../../../raw/code-changes/2026-11-20-243-framework-docs-master/readonly-review.json)
- [requirements.md](../../../raw/code-changes/2026-11-20-243-framework-docs-master/requirements.md)
- [review-findings.md](../../../raw/code-changes/2026-11-20-243-framework-docs-master/review-findings.md)
- [review-ledger.json](../../../raw/code-changes/2026-11-20-243-framework-docs-master/review-ledger.json)
- [review-report-round-1.md](../../../raw/code-changes/2026-11-20-243-framework-docs-master/review-report-round-1.md)
- [review-report-round-2.md](../../../raw/code-changes/2026-11-20-243-framework-docs-master/review-report-round-2.md)
- [review-report-round-3.md](../../../raw/code-changes/2026-11-20-243-framework-docs-master/review-report-round-3.md)
- [review-report-round-4.md](../../../raw/code-changes/2026-11-20-243-framework-docs-master/review-report-round-4.md)
- [round2-changed.txt](../../../raw/code-changes/2026-11-20-243-framework-docs-master/round2-changed.txt)
- [round3-changed.txt](../../../raw/code-changes/2026-11-20-243-framework-docs-master/round3-changed.txt)
- [run.json](../../../raw/code-changes/2026-11-20-243-framework-docs-master/run.json)
- [scope-baseline.json](../../../raw/code-changes/2026-11-20-243-framework-docs-master/scope-baseline.json)
- [test-freeze.json](../../../raw/code-changes/2026-11-20-243-framework-docs-master/test-freeze.json)
- [verification-result.md](../../../raw/code-changes/2026-11-20-243-framework-docs-master/verification-result.md)

## Related
- [code-changes/ — the folder and its tags](README.md)
- Previous change: [2026-11-19 246-240-follow-ups](2026-11-19-246-240-follow-ups-three-open-findings-of-the-240-backlog-change-clos.md)
- Decision implemented: [Wiki practice lives in agentic-design; llm-wiki holds the build and links to it](../decisions/wiki-practice-lives-in-agentic-design-llm-wiki-holds-the-build-and-links-to-it-2026-11-19.md)
- Decision made during the run: [Mutation testing on demand for llm-wiki-bootstrap](../decisions/mutation-testing-on-demand-for-llm-wiki-bootstrap-2026-11-20.md)
- Moved by this change: [architecture-decisions](../decisions/architecture-decisions-2026-04-10.md)
