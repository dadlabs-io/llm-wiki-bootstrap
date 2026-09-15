---
name: wiki
description: Show this project's wiki INDEX (folder tree + curated file list with summaries). Use when the user says "show me the wiki", "what's in the wiki", "list wiki topics", or wants to browse what's been captured.
last_reviewed: 2026-09-15
review_after: 2026-12-15
reviewed_for_model: claude-opus-5
---

> **Browsing skill.** You call it to see what the wiki holds. `/wiki-cycle` rebuilds the same indexes as part of its run but does not call this skill. For finding something specific, use `/wiki-search`.

> **Wiki resolution.** The scripts resolve the wiki through the registry (`<cwd>/.claude/wiki-config.json` → `notebook` + `registry` → `linked-notebooks.json`), so most projects' wiki is a notebook in the notebooks vault; a project scaffolded with the wiki inside it has `llm-wiki/` instead. Omit `--vault`; pass `--vault <vault_root>` only for a legacy in-project vault outside the registry.

Show this project's wiki index: `<notebook>/_INDEX.md`, the full list of entries at the notebook root (beside `wiki/`), which the filing script regenerates every time an entry is filed.

## Behavior

### Default: show this project's wiki
1. Resolve the notebook root from `.claude/wiki-config.json` (the registry notebook's root, or `llm-wiki/` inside the project) and read `<notebook>/_INDEX.md`
2. Display it to the user as-is — it's already formatted for reading
3. Offer to read any specific file in the index if they want to drill in
4. If `_INDEX.md` is missing or older than the newest file in `wiki/`, regenerate it first:
   ```bash
   python {{WIKI_SCRIPTS_DIR}}/wiki-index.py --topic <notebook>
   ```

### Other views
Per-folder indexes (`wiki/<folder>/_INDEX.md`; `sessions/` gets none, retired entries are left out):
```bash
python {{WIKI_SCRIPTS_DIR}}/wiki-index-per-folder.py --topic <notebook>
```

The top-level orientation map (`wiki/_MAP.md`, always loaded through CLAUDE.md):
```bash
python {{WIKI_SCRIPTS_DIR}}/wiki-map-compile.py --topic <notebook>
```

`--topic <name>` on any of these picks another registered notebook.

## Key paths

- Notebook root: from the registry, or `llm-wiki/` inside the project
- Full index: `<notebook>/_INDEX.md` (`wiki-index.py`)
- Per-folder INDEX: `<notebook>/wiki/<folder>/_INDEX.md` (`wiki-index-per-folder.py`)
- Top-level MAP: `<notebook>/wiki/_MAP.md` (`wiki-map-compile.py`)

## Don't

- Don't summarize the INDEX — show it. The whole point is that it's already a curated, scannable view
- Don't auto-regenerate unless asked or unless the file is missing/stale
- Don't conflate this with `/wiki-search` — `/wiki` is for browsing, `/wiki-search` is for finding
- Don't assume `llm-wiki/wiki/`: most projects' wiki is a notebook in the vault, found through the registry
