---
name: wiki-init
description: Create a new topic wiki — scaffolds the folder structure and templated README. Conversational discovery if the user doesn't provide all the details. Use when the user says "wiki init", "create a new wiki", "start a new research topic", "make a new wiki for X", "set up a wiki for Y", "init wiki", "new wiki".
---

Create a new topic wiki via conversational discovery if needed, then call wiki-init.py.

## Required fields

| Field | Required | Default | How to get it |
|---|---|---|---|
| `topic` | ✅ yes | none — must come from user | If not given, ask or propose based on conversation |
| `description` | ✅ yes | none — must come from user | If not given, ask or propose based on conversation |
| `vault` | optional | `/shared/openclaw/vault/wikis` (host: `docker/shared/openclaw/vault/wikis/`) | Use default unless user overrides |

## Conversational discovery flow

If the user types `/wiki-init` with NO args, OR with just a vague intent ("I want a wiki for X"):

1. **Have a brief conversation** to understand what the topic is FOR. What kind of content goes in it? What's it NOT for?

2. **Propose all three fields** in this format, clearly:

   ```
   I'd create:
     Vault:       docker/shared/openclaw/vault/wikis/
     Topic:       <slugified-name>
     Full path:   docker/shared/openclaw/vault/wikis/<slugified-name>/
     Description: <one-line scope>

   Confirm? (or tell me what to change)
   ```

3. **Wait for confirmation** before running. Don't proceed without explicit "yes" / "go" / "create".

4. If the user pushes back on any field, adjust and re-propose.

## When the user gave full args

If the user says `/wiki-init my-topic "scope here"`, just confirm briefly and run:

```
Creating: docker/shared/openclaw/vault/wikis/my-topic/
Description: scope here
Confirm? (or just say go)
```

## Topic naming guidance

- Slug-style: lowercase, hyphens, no spaces
- Specific over generic: `agentic-design` > `ai`
- Long-running: name a research area, not a task
- Examples of good topic names: `agentic-design`, `canadian-tax-law`, `home-network`, `unity-game-dev`, `claude-code-skills`, `memory-systems`

## Description guidance

A 1-2 sentence answer to "what is this wiki for?" — should be specific enough that future-you can decide what's on/off topic.

Examples:
- ❌ "AI stuff"
- ✅ "AI agent design patterns, Claude Code, memory architectures, context engineering — the meta-work of building agents"
- ❌ "Canada"
- ✅ "Canadian personal income tax rules, CRA forms, deduction categories, business expense rules"

## Run the script

```bash
python bootstrap/docker-setup/openclaw/agents-training/main/skills/research-wiki/wiki-init.py \
  --topic <slugified-topic> \
  --description "<scope>" \
  --vault docker/shared/openclaw/vault/wikis
```

## After creation

1. Show the user the topic root path
2. Tell them to edit the topic README's "In scope / Out of scope" sections (it's a placeholder)
3. Suggest first add: `/wiki-update` or `/wiki-list add <url>`

## Don't

- Don't create a topic without explicit user confirmation when discovering conversationally
- Don't create a topic with a generic name without asking ("ai", "research", "stuff")
- Don't overwrite an existing topic — wiki-init.py already errors out, but check first if you can
- Don't fill in the README's scope sections automatically — that's a human decision

## Key paths

- wiki-init.py: `bootstrap/docker-setup/openclaw/agents-training/main/skills/research-wiki/wiki-init.py`
- Default vault: `docker/shared/openclaw/vault/wikis/`
