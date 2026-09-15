---
name: wiki-init
description: "Scaffold a notebook folder by hand (<vault>/<topic>/ with wiki/, raw/, _inbox/, _config/feeds.md and a README whose scope comes from the user's description). Use when the user says 'wiki init' or 'init wiki', or wants a wiki added to a project that has none. /new-wiki scaffolds whole projects itself and does not call this."
last_reviewed: 2026-09-08
review_after: 2026-12-08
reviewed_for_model: claude-fable-5-1
---

> **⚙️ Standalone skill.** `/new-wiki` does not call it (its Phase B builds the wiki folders itself). Use it to create a notebook folder by hand, for example to add a wiki to an existing project or a second topic.

> **Wiki resolution (2026-09-08).** The scripts resolve the wiki through the registry (`<cwd>/.claude/wiki-config.json` → `notebook` + `registry` → `linked-notebooks.json`). Omit `--vault`; pass `--vault <vault_root>` only for a legacy in-project vault or when running from outside the project. The `--vault llm-wiki/wiki` examples that used to appear here pointed registry notebooks at a folder that does not exist.

Create a notebook folder, `<vault>/<topic>/`, and write its scaffold files: `wiki/` (the stub folders plus `sessions/`), `raw/`, `answers/`, `_inbox/` (pending, done, failed, reports, archive), `_config/feeds.md`, the template's README and hub pages, and a first `_INDEX.md`.

## Required fields

| Field | Required | Default | How to get it |
|---|---|---|---|
| `topic` | ✅ yes | project slug | If not given, derive from the project folder name |
| `description` | ✅ yes | project description from config | Read `.claude/wiki-config.json` if not given |
| `vault` | optional | this project's registered vault, else `vault_root` in `.claude/wiki-config.json`, else the current folder | Use the default unless overriding |

## Default usage

```bash
python {{WIKI_SCRIPTS_DIR}}/wiki-init.py \
  --topic <project-slug> \
  --description "<scope>"
```

`/new-wiki` does not call this: `new-wiki.py` Phase B builds the wiki folders itself. `wiki-init.py` is the standalone scaffolder for a notebook folder created by hand.

## Standalone invocation

If you want to add a wiki to an existing project that doesn't have one, or rebuild the scaffold:

1. **Verify the script is installed**: `{{WIKI_SCRIPTS_DIR}}/wiki-init.py` ships with the global tooling install (or a bundled project install). If it is missing, run the tooling install (`install-wiki.ps1` / `./install-wiki.sh` with no flags); `/new-wiki --sync` refreshes only the `/new-wiki` skill and will not install it.

2. **Propose the plan**:
   ```
   I'd create:
     Project root: <cwd>
     Notebook:     <vault>/<slug>/
     Topic:        <slug>
     Description:  <one-line scope>

   Confirm? (or tell me what to change)
   ```

3. **Run after confirmation**:
   ```bash
   python {{WIKI_SCRIPTS_DIR}}/wiki-init.py \
     --topic <slug> \
     --description "<scope>"
   ```

## Topic naming guidance

- Slug-style: lowercase, hyphens, no spaces
- Usually the project slug; a second topic for a separate subject is fine
- Examples of good slugs: `agentic-design`, `dnd-combat-engine`, `canadian-tax-law`, `home-network`

## Description guidance

A 1-2 sentence answer to "what is this wiki for?" — specific enough that future-you can decide what's on/off topic. The description goes into the wiki's root README.

Examples:
- ❌ "AI stuff"
- ✅ "AI agent design patterns, Claude Code, memory architectures, context engineering — the meta-work of building agents"

## After creation

1. Show the user the notebook path: `<vault>/<topic>/`
2. Tell them the README's `## Scope` section was filled from their description, and to sharpen it by hand
3. Suggest first add: `/wiki-update <url>` (research) or `/wrap-up` at session-end (development)

## Don't

- Don't create a topic without explicit user confirmation when invoked standalone
- Don't overwrite an existing topic — wiki-init.py errors out; check first
- Don't invent the scope: it comes from the user's description, and only they can sharpen it

## Key paths

- wiki-init.py: `{{WIKI_SCRIPTS_DIR}}/wiki-init.py`
- Default vault: the project's registered vault, else the current folder
- Created notebook: `<vault>/<topic>/` (its framework-contract docs land at `wiki/best-practices/framework/`, the template's layout; `/new-wiki` puts them at `wiki/project/best-practices/framework/`)
