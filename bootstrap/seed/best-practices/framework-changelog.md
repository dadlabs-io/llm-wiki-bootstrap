# Framework Changelog

**Purpose**: History of changes to the shared workflow framework (personas, workflows, rules, best-practices). This is NOT a project changelog — it tracks changes that affect all projects using workflows-core.
**Status**: Active
**Tags**: #process, #framework

> If a workflow pattern, persona definition, or rule looks different from what you remember,
> check here first. Changes are listed newest-first with migration notes where needed.

---

## 2026-09-08

### Frontmatter loadability is a gate (intake pass, item: agent-builder handoff of 2026-09-06)
- **Four shipped artifacts had unparseable or truncated frontmatter**: `wrap-up`, `wiki-rollback` and the `wiki-ingester` agent carried an unquoted `description:` containing `: ` (a YAML loader drops *every* field, so the skill was listed by its H1 and only ran when typed by name); `wiki-report`'s description contained ` #2` and was silently cut there, losing all its trigger phrases. All four are now double-quoted.
- **New shared check** `_entry_checks.check_frontmatter_loadable()` on the RAW block: ERROR `frontmatter-unquoted-scalar` (`: ` in a plain top-level scalar), ERROR `frontmatter-reserved-indicator`, WARNING `description-comment-truncates` (` #`), ERROR `frontmatter-yaml-parse` (PyYAML, when present). Same rule names as the agent-builder's `lint-artifact.py`.
- **Installer refuses** a `SKILL.md` / `AGENT.md` that fails it (`_install_tooling.py`; the previous installed copy stays; `new-wiki.py --mode tooling` exits 1). Proven against known-bad fixtures and a deliberately broken package copy.
- **Lint**: the "Unquoted YAML Values" section becomes "Frontmatter Loadability" and runs the shared check (the old check read the *parsed* title after quotes were stripped, so it flagged correctly quoted titles and never saw the broken descriptions); new section over the **installed** `~/.claude/skills/*/SKILL.md` + `~/.claude/agents/*.md`; new **Search Index Coverage (qmd)** section — indexed file count vs `.md` files on disk, "not a collection", empty index, or qmd absent (Taskesen's silent-drop point; on Windows the check falls back to Git Bash because npm's `qmd.cmd` shim execs `/bin/sh`).
- **`/wiki-search`**: "Route the question first" (lookup → search; holistic / cross-entry → `/wiki-claims` or `/wiki-lint --full`; browsing → `/wiki`) and a **file-the-answer** step (offer once to keep a durable answer as a `project/` entry). From Taskesen (via the agent-builder) and the nanzhipro Karpathy-bootstrap skill (agentic-design `research/long-term/`, ingested 2026-09-08).
- **Process**: the agent-builder's three-phase research-to-framework update process adopted as a pattern in the llm-wiki-bootstrap notebook (`project/patterns/`), with a per-pass intake log (`project/intake-log-llm-wiki-2026-09.md`). This pass's frontmatter fix went out immediately as a recorded hotfix exception to "roll out last".
- **Migration**: re-run `install-wiki.ps1` (tooling mode) to pick up the four fixed descriptions and the new lint; the next `/wiki-lint` on any wiki shows the installed-skill and qmd-coverage sections. Roadmap gains three follow-ups: a concept-table hub page, `framework-version` on scaffolded files + a re-scaffold diff, qmd collection registration at scaffold time.

### Phase 2 cleanup pass, same day (every shipped artifact and every registered wiki re-checked against the framework)
- **Framework-contract docs reconciled in both directions.** Five of the six templates were overdue for review (one since July) and `tiered-context-loading.md` had shipped truncated mid-table since its first commit; the agentic-design copies had been completed and extended in August (duplicate carve-out, read-before-reject, ASR check, frozen-count and as-of-date rules, org-scale boundary, cycle steps 1.0/3.5/5.5/6.5, "say where you stopped", bucket-number fixes) and none of it had flowed back. The templates now carry all of it (authoring v3, frontmatter v4, cycle-step v2, tiered v2, memory-signals v3, search-spec v2) plus: the tier rubric is no longer restated in the authoring doc (link to the spec's table); the cycle contract's timestamp invariant says tz-aware local with offset, not UTC (it disagreed with the date/time convention and with `now_stamp()`); the memory-signals template lost a stale agentic-design backlink block and a retired `memory-bank/` source path; the search spec's status table says surface 1 shipped and surface 2 is opt-in.
- **Framework docs are now framework-managed everywhere.** `new-wiki.py` gains `seed_framework_docs()`: the six docs land at `wiki/project/best-practices/framework/` at scaffold time and on `--phase docs`, content-compared and replaced when different, each replaced file named. Before this, five of nine registered notebooks had no framework docs at all (the CLAUDE.md precedence rule pointed at a folder that did not exist) and the two that did had drifted both ways. `install.py`'s framework list corrected to six. All eight standard notebooks refreshed this pass.
- **Skills re-read against the contracts.** Every `--vault llm-wiki/wiki` example removed (it pointed registry notebooks at a non-existent folder) and replaced by a wiki-resolution note; the "public-facing commands" banner in eight skills now names `/wrap-up`, `/wiki-verify`, `/wiki-rollback`, `/new-wiki`; `wiki-refresh`'s review-cadence table (which disagreed with the spec on every row) and `wiki-lint`'s tier definitions replaced by links to the spec; `wiki-cycle`'s config section rewritten for the registry model and its semantic-lint row un-frozen; `wiki-verify` / `wiki-rollback` links to a non-existent `../topic-template/...` path fixed; `wiki-ingester`'s eval step lost its contradictory pre-split scoring sentence; `new-wiki`'s frozen skill/script counts point at the manifests; `wiki-report`'s agentic-design-specific reads made conditional. Lifecycle fields refreshed on all sixteen skills and added to the agent.
- **`wiki-search-rerank.py` ships.** It existed in `bootstrap/scripts/` but was not in `TRAVEL_SCRIPTS`; now installed, with an inventory row and a "Truth-status rerank" section in `/wiki-search` (opt-in pipe).
- **Accepted gap, recorded:** agentic-design has 208 pre-rubric entries with no `## TL;DR` and 72 with no `## Related`; that is a research-wiki content pass, warn-only by design, and is not part of this framework pass.

### Post-package queue, same evening (seeder follow-ups from the Phase 2 decision's caveats)
- **`new-wiki.py --phase docs --check`.** Review-first mode for a notebook owner: writes nothing, lists every framework-contract doc as unchanged / ADD / REPLACE with the `framework-version` on both sides and a unified diff of the body, names the pack pages a refresh would copy, and exits 1 when anything would change. A REPLACE at the same version means a project-local edit the refresh would lose; at a lower version, a stale copy. Run it per registered notebook after a framework change, then the refresh.
- **Bug fixed in the seeder's comparison.** Text appended *after* a doc's reciprocation backlink block was dropped from the comparison and silently deleted on refresh. It is now part of the compared body, so it shows in the `--check` diff and marks the doc REPLACE.
- **A wiki without the `project/` taxonomy is out of scope for the framework docs.** `--phase docs` names it and skips them instead of creating a folder the notebook has no use for; its pack usage docs still refresh. `maggies-computer-notes` (a beginner's Python notes wiki with its own folders) stays out of scope — decided 2026-09-08.
- All nine registered notebooks checked: eight match the framework; the ninth had one stale pack page (the `/wiki-search` usage page, edited after that notebook's morning refresh), now refreshed.
- **`--all-notebooks`, and the SOP.** `--phase docs` (check or refresh) runs over every notebook in the registry with a one-line summary per notebook and one exit code. The standing procedure after any change that lands in a notebook is now `--phase docs --check --all-notebooks` → review every REPLACE → the same without `--check` → `install-wiki.ps1 -RefreshOnly`; recorded in CLAUDE.md, the `/new-wiki` skill and the process pattern. It replaces the hand-written shell loop that had to be corrected twice in the session that built it.

## 2026-09-02

### Build-time governance pass (from "Context as Code", Huk, O'Reilly Radar — agentic-design `research/best-practices/`)
- **Mechanical eval gate**: new shared module `_entry_checks.py`. `wiki-update.py` now refuses to file an entry with no `## TL;DR` or with fewer than two wiki links in its `## Related` section (`--no-gate '<reason>'` overrides, and prints the reason); it warns on <3 tags, unmarked stubs, and numeric claims outside blockquotes. `wiki-lint-mechanical.py` runs the same checks over existing entries as a warn-only backlog view. The agent's rubric self-score now covers only extraction fidelity and synthesis value, and is advisory.
- **Precedence**: `CLAUDE.md` template gains a "When guidance conflicts" section (framework-contract docs > SKILL.md > CLAUDE.md/how-to > memory; mechanical enforcement outranks prose). The `wiki-update` skill's restated tier/confidence definitions were replaced with a link to the frontmatter spec.
- **Lifecycle on skills**: every shipped `SKILL.md` carries `last_reviewed`, `review_after`, `reviewed_for_model`; `/wiki-refresh` Step 1b scans them.
- **Principle 11** added to the authoring best-practices: every hard rule is a hybrid artifact (prose + a paired mechanical check).
- **Migration**: existing wikis show a body-check backlog in the next `/wiki-lint` (warn-only, nothing fails). Re-run `install-wiki.ps1 -RefreshOnly` to pick up the new script and skills. Frontmatter spec template synced to v3 (restatement rule).

### Bugs fixed in the same pass
- Drive triage dedup missed HubSpot (`_hsenc`/`_hsmi`) and YouTube (`si`) tracking tokens and re-queued two ingested sources. `wiki-fetch-drive-folder.py` now strips those plus ad-click ids, collapses any YouTube URL form to `watch?v=<id>`, and checks canonical URLs against the target wiki's `source_url`s before queueing (`--requeue-known` to bypass); known items are reported and their Drive files archived.
- `wiki-update.py --raw-path raw/<file>.md` resolved against the shell cwd, not the topic root, producing a footer link into the wrong repo.
- `wiki-update.py`'s outbound-link resolver only examined links starting with `./` or `../`, so bare-slug links to entries in other folders shipped broken with `outbound_warnings=0`.

## 2026-02-07

### Per-Agent Active Context
- Each agent instance can now create `_personas/<agent-name>/active-context.md` as a personal resume file
- Template at `_personas/_agent-template/active-context.md`
- Shared dashboard `memory-bank/short-term/active-context.md` is unchanged
- **Migration**: No action required. Create your own agent folder under `_personas/` when ready.

### Best Practices Reading List
- Now includes all 12 best-practices documents
- Previously missing: `change-request-workflow.md`, `documentation-best-practices.md`
- **Migration**: Your reading list will be updated on next sync. No action required.

### Sync Tooling
- `check-sync.py` excludes project-specific reading lists and agent instance folders
- `setup-antigravity-workflow.ps1` supports new project scaffolding
- `setup-cursor-workflow.ps1` added (untested)
- **Migration**: Internal tooling only. No project-side changes needed.
