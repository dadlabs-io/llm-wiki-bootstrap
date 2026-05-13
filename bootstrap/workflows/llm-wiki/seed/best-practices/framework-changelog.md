# Framework Changelog

**Purpose**: History of changes to the shared workflow framework (personas, workflows, rules, best-practices). This is NOT a project changelog — it tracks changes that affect all projects using workflows-core.
**Status**: Active
**Tags**: #process, #framework

> If a workflow pattern, persona definition, or rule looks different from what you remember,
> check here first. Changes are listed newest-first with migration notes where needed.

---

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
