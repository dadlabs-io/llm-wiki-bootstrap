---
name: wiki
description: Show a topic wiki INDEX (folder tree + curated file list with summaries). Use when the user says "show me the wiki", "what's in the wiki", "list wiki topics", or wants to browse what's been captured.
---

> **⚙️ Internal skill.** This is invoked by `/wiki-cycle` (the orchestrator) — users normally don't call it directly. Public-facing commands are `/wiki-cycle`, `/wiki-update`, `/wiki-search`, `/wiki-init`. This skill is documented + callable for programmatic use.

Display a topic wiki's _INDEX.md, or list all available topics.

## Behavior

### If the user gave a topic name
1. Read `docker/shared/openclaw/vault/wikis/<topic>/_INDEX.md`
2. Display it to the user as-is — it's already formatted for reading
3. Offer to read any specific file in the index if they want to drill in
4. If `_INDEX.md` is missing or stale (modified before any wiki/ file), regenerate it first:
   ```bash
   python bootstrap/docker-setup/openclaw/agents-training/main/skills/research-wiki/wiki-index.py \
     --topic <topic> \
     --vault docker/shared/openclaw/vault/wikis
   ```

### If the user did NOT give a topic name
1. List all topics:
   ```bash
   ls docker/shared/openclaw/vault/wikis/
   ```
2. For each topic, read its `README.md` first paragraph to give the user a one-line description
3. Ask which topic they want to view (if there's only one topic in the vault, use that; otherwise prompt)

### If the user wants to regenerate the index
```bash
python bootstrap/docker-setup/openclaw/agents-training/main/skills/research-wiki/wiki-index.py \
  --topic <topic> \
  --vault docker/shared/openclaw/vault/wikis
```

## Key paths

- Wikis vault: `docker/shared/openclaw/vault/wikis/`
- Wiki-index script: `bootstrap/docker-setup/openclaw/agents-training/main/skills/research-wiki/wiki-index.py`
- Per-topic INDEX: `docker/shared/openclaw/vault/wikis/<topic>/_INDEX.md`
- Per-topic README (scope): `docker/shared/openclaw/vault/wikis/<topic>/README.md`

## Don't

- Don't summarize the INDEX — show it. The whole point is that it's already a curated, scannable view
- Don't auto-regenerate unless asked or unless the file is missing/stale
- Don't conflate this with `/wiki-search` — `/wiki` is for browsing, `/wiki-search` is for finding
