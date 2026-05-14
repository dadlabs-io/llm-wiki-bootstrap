---
name: wiki-init
description: Initialize the per-project wiki — scaffolds the folder structure and templated README. Use when the user says "wiki init", "create a new wiki", "init wiki". In v1 install model, each project has ONE wiki at llm-wiki/wiki/; this skill is run automatically by /new-wiki but can also be invoked directly.
---

> **⚙️ Internal skill.** Normally invoked by `/new-wiki` during per-project scaffold. Manual invocation is only useful if you want to add or rebuild a wiki layer in an existing project, or if you're (v2) adding a second wiki topic to a project.

Create the per-project wiki structure at `llm-wiki/wiki/<topic>/` and write its scaffold files.

## Required fields

| Field | Required | Default | How to get it |
|---|---|---|---|
| `topic` | ✅ yes | project slug | If not given, derive from the project folder name |
| `description` | ✅ yes | project description from config | Read `.claude/wiki-config.json` if not given |
| `vault` | optional | `llm-wiki/wiki` (relative to project root) | Use default unless overriding |

## Default usage (called by /new-wiki)

```bash
python .claude/wiki-scripts/wiki-init.py \
  --topic <project-slug> \
  --description "<scope>" \
  --vault llm-wiki/wiki
```

`new-wiki.py` Phase B calls this automatically with the right args. You usually don't run it by hand.

## Standalone invocation

If you want to add a wiki to an existing project that doesn't have one, or rebuild the scaffold:

1. **Verify project structure**: `<project>/.claude/wiki-scripts/wiki-init.py` should exist (created by `/new-wiki`). If not, run `/new-wiki --sync` first.

2. **Propose the plan**:
   ```
   I'd create:
     Project root: <cwd>
     Wiki root:    llm-wiki/wiki/
     Topic:        <slug>
     Description:  <one-line scope>

   Confirm? (or tell me what to change)
   ```

3. **Run after confirmation**:
   ```bash
   python .claude/wiki-scripts/wiki-init.py \
     --topic <slug> \
     --description "<scope>" \
     --vault llm-wiki/wiki
   ```

## Topic naming guidance

- Slug-style: lowercase, hyphens, no spaces
- For v1 (one wiki per project), topic = project slug
- Examples of good slugs: `agentic-design`, `dnd-combat-engine`, `canadian-tax-law`, `home-network`

## Description guidance

A 1-2 sentence answer to "what is this wiki for?" — specific enough that future-you can decide what's on/off topic. The description goes into the wiki's root README.

Examples:
- ❌ "AI stuff"
- ✅ "AI agent design patterns, Claude Code, memory architectures, context engineering — the meta-work of building agents"

## After creation

1. Show the user the topic root path: `llm-wiki/wiki/<topic>/`
2. Tell them to edit `llm-wiki/wiki/<topic>/README.md`'s "In scope / Out of scope" sections (placeholder)
3. Suggest first add: `/wiki-update <url>` (research) or `/wrap-up` at session-end (development)

## Don't

- Don't create a topic without explicit user confirmation when invoked standalone
- Don't overwrite an existing topic — wiki-init.py errors out; check first
- Don't fill in the README's scope sections automatically — that's a human decision

## Key paths (per-project install)

- wiki-init.py: `.claude/wiki-scripts/wiki-init.py`
- Default vault (per-project): `llm-wiki/wiki/`
- Created topic: `llm-wiki/wiki/<topic>/`
