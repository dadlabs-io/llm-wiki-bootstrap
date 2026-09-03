# Framework Changelog

**Purpose**: History of changes to the shared workflow framework (personas, workflows, rules, best-practices). This is NOT a project changelog — it tracks changes that affect all projects using workflows-core.
**Status**: Active
**Tags**: #process, #framework

> If a workflow pattern, persona definition, or rule looks different from what you remember,
> check here first. Changes are listed newest-first with migration notes where needed.

---

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
