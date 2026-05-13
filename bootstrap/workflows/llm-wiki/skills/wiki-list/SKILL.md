---
name: wiki-list
description: Manage the pending ingestion list for a topic wiki — add items, process the list, or show what's queued. Use when the user says "add to the wiki list", "queue this for the wiki", "process the wiki list", "drain the queue", "what's in the wiki list", "show wiki list", "wiki list add", "wiki list process". Producer/consumer split for low-friction capture (drop URLs throughout the day, batch process later).
---

> **⚙️ Internal skill.** This is invoked by `/wiki-cycle` (the orchestrator) — users normally don't call it directly. Public-facing commands are `/wiki-cycle`, `/wiki-update`, `/wiki-search`, `/wiki-init`. This skill is documented + callable for programmatic use.

Manage the wiki ingestion list. ONE command, behavior depends on the user's intent: add, process, or show.

## Three modes

| User intent | Subcommand | What happens |
|---|---|---|
| Add a URL/file/text to the list for later | `add` | Drops a `.queue` file in `<topic>/_inbox/pending/`. Fast, no fetching. |
| Process everything in the list | `process` | Drains the pending queue, runs wiki-update.py per item, moves to done/ or failed/, regens INDEX once at end. |
| Show what's in the list | `show` (default) | Lists the `.queue` files in pending/ with their source URL + target folder. |

Pick the mode from the user's words. If ambiguous, ask. Default to `show` if user just runs `/wiki-list` with no args.

## Mode 1: ADD (producer)

What to ask the user (only if not already provided):

1. **Topic** — default = the topic configured in your harness
2. **Source** — URL, file path, or pasted text
3. **Folder** — optional, can be filled in at process time
4. **Title** — optional
5. **Tags** — optional

Run:
```bash
python bootstrap/docker-setup/openclaw/agents-training/main/skills/research-wiki/wiki-list-add.py \
  --topic <topic> \
  --source <url-or-path> \
  --vault docker/shared/openclaw/vault/wikis \
  --added-by claude-code \
  [--folder <folder>] \
  [--title "<title>"] \
  [--tags "<tag1,tag2>"]
```

After: tell user the queue file path and total pending count. Suggest `/wiki-list process` when ready.

## Mode 2: PROCESS (consumer)

What to ask:
1. **Topic** — default = the topic configured in your harness
2. **--limit N** — optional, only process some
3. **Dry run first?** — recommended if pending has > 5 items

Dry run:
```bash
python bootstrap/docker-setup/openclaw/agents-training/main/skills/research-wiki/wiki-list-process.py \
  --topic <topic> \
  --vault docker/shared/openclaw/vault/wikis \
  --dry-run
```

Real run:
```bash
python bootstrap/docker-setup/openclaw/agents-training/main/skills/research-wiki/wiki-list-process.py \
  --topic <topic> \
  --vault docker/shared/openclaw/vault/wikis
```

The processor passes each item's `added_by` field through to wiki-update.py as `--ingested-by` so we know who originally captured it.

After: report success/fail counts. List failed items if any, point at `_inbox/failed/` for `.error` sidecars.

**Important caveat**: synthesis quality depends on which model is running this slash command. When called from Claude Code (here), Opus does the work. When called via ClawD on Discord, ClawD's main agent (likely a cheaper model) does it. For high-stakes summaries, run process here.

## Mode 3: SHOW (default)

Just list what's in the pending queue:
```bash
ls docker/shared/openclaw/vault/wikis/<topic>/_inbox/pending/
```

Then for each `.queue` file, cat it briefly to show the user:
- Source URL
- Target folder
- Added by (claude-code, clawd, cli)
- Added at

Format as a compact list. Tell the user the total count and remind them they can run `/wiki-list process` to drain it.

## Don't

- Don't process items as part of `add` mode — that defeats the producer/consumer split
- Don't queue items that don't fit the topic README's scope — suggest a different topic
- Don't bypass the queue and call wiki-update directly when the user said "queue" or "list" — they want async capture

## Key paths

- Pending queue: `docker/shared/openclaw/vault/wikis/<topic>/_inbox/pending/`
- Done: `docker/shared/openclaw/vault/wikis/<topic>/_inbox/done/`
- Failed: `docker/shared/openclaw/vault/wikis/<topic>/_inbox/failed/` (with `.error` sidecars)
- wiki-list-add.py / wiki-list-process.py: `bootstrap/docker-setup/openclaw/agents-training/main/skills/research-wiki/`
