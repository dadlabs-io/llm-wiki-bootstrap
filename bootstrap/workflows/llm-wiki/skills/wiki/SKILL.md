---
name: wiki
description: Show this project's wiki INDEX (folder tree + curated file list with summaries). Use when the user says "show me the wiki", "what's in the wiki", "list wiki topics", or wants to browse what's been captured.
---

> **⚙️ Internal skill.** This is invoked by `/wiki-cycle` (the orchestrator) — users normally don't call it directly. Public-facing commands are `/wiki-cycle`, `/wiki-update`, `/wiki-search`, `/wiki-init`. This skill is documented + callable for programmatic use.

Display this project's wiki `_INDEX.md`. In per-project installs there is one wiki per project, rooted at `llm-wiki/wiki/`.

## Behavior

### Default: show this project's wiki
1. Read `llm-wiki/wiki/_INDEX.md` (relative to project root, i.e., the CWD when Claude Code was started)
2. Display it to the user as-is — it's already formatted for reading
3. Offer to read any specific file in the index if they want to drill in
4. If `_INDEX.md` is missing or stale (modified before any `wiki/` file), regenerate it first:
   ```bash
   python .claude/wiki-scripts/wiki-index-per-folder.py --vault llm-wiki/wiki
   ```

### If the user wants to regenerate the index
```bash
python .claude/wiki-scripts/wiki-index-per-folder.py --vault llm-wiki/wiki
```

For the top-level orientation map (`_MAP.md`, always-loaded in CLAUDE.md):
```bash
python .claude/wiki-scripts/wiki-map-compile.py --topic <project-slug> --vault llm-wiki/wiki
```

### Multi-wiki note (v2 feature, not in v1)

The v1 install model is **one wiki per project**, located at `llm-wiki/wiki/`. Multi-wiki-per-project support is deferred to v2 — if/when that ships, this skill grows a `--topic <name>` arg to disambiguate.

## Key paths (per-project install)

- Wiki content: `llm-wiki/wiki/`
- Index script: `.claude/wiki-scripts/wiki-index-per-folder.py`
- MAP script: `.claude/wiki-scripts/wiki-map-compile.py`
- Per-folder INDEX: `llm-wiki/wiki/<folder>/_INDEX.md`
- Top-level MAP: `llm-wiki/wiki/_MAP.md`

## Don't

- Don't summarize the INDEX — show it. The whole point is that it's already a curated, scannable view
- Don't auto-regenerate unless asked or unless the file is missing/stale
- Don't conflate this with `/wiki-search` — `/wiki` is for browsing, `/wiki-search` is for finding
- Don't assume a shared `vault` exists. Each project's wiki lives inside the project at `llm-wiki/wiki/`.
