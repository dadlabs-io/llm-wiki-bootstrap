# Commands reference — every slash command

Canonical reference for the LLM-wiki framework. Each command works inside Claude Code (or Cursor, via the .mdc rules) once the framework is installed for this project.

## The user-facing commands (these are the only ones you'll typically type)

| Command | When to use it |
|---|---|
| `/new-project` | Scaffold a new project. Asks tool, type, name, target, Drive prefs. Only needed to **start** a project. |
| `/wiki-update <url>` | Add one external reference (article, paper, video) to the wiki right now |
| `/wiki-cycle` | Full ingest pipeline — discover, batch-ingest, lint, promote, commit. For research projects, the daily/weekly command. |
| `/wiki-search "<query>"` | Hybrid BM25 + vector + LLM-reranked search across your wiki |
| `/wrap-up` | End-of-session distillation (development projects). Reads conversation + git diff, proposes wiki entries, stages them for your review. |
| `/wiki-promote` | Walk staged entries in `_inbox/proposed/` and accept/reject each one |
| `/wiki-init` | Manually scaffold the wiki folder (rarely needed — `/new-project` does it for you) |

## The internal commands (invoked by other commands, you usually don't type these)

These are listed for completeness. `/wiki-cycle` invokes them in order; you can also call them directly when debugging.

| Command | What it does |
|---|---|
| `/wiki-discover` | Find new candidate URLs from RSS feeds + Drive folder |
| `/wiki-list` | Manage the `_inbox/pending/` queue |
| `/wiki-lint` | Mechanical lint (broken links, orphans, stale frontmatter) and optionally semantic lint |
| `/wiki-claims` | Extract claims from entries, find contradictions |
| `/wiki-refresh` | Scan for stale entries (`review_after` date passed) |
| `/wiki-report` | Generate the morning report from a cycle run |
| `/wiki` | Browse the wiki — show the current `_INDEX.md` |

## Daily rhythm

**For development projects:**
1. Start a session — agentmemory auto-loads recent context, the `_MAP.md` is always-loaded via CLAUDE.md
2. Code + decide + investigate
3. `/wrap-up` at end — distills the session
4. `/wiki-promote --review` to accept the proposed entries

**For research projects:**
1. Drop URLs into Drive (`__FOR CLAUDE/<project-slug>/`) throughout the day
2. Or `/wiki-update <url>` for one-offs
3. `/wiki-cycle` once a day/week — discovers, ingests, lints, promotes
4. `/wiki-search "<query>"` whenever you need to look something up

## See also (deeper docs per command)

- `how-to/getting-started.md` — your first hour with a freshly-scaffolded project
- `how-to/wiki-update.md` — `/wiki-update` in depth (staging, tier rules)
- `how-to/wiki-cycle.md` — `/wiki-cycle` orchestrator + mode flags
- `how-to/wrap-up.md` — `/wrap-up` categories + safety
- `how-to/wiki-search.md` — `/wiki-search` ranking model
- `how-to/drive-setup.md` — Google Drive OAuth one-time setup
- `how-to/install.md` — installing the framework on a fresh machine

## Where to ask the agent for help

You can always ask in plain English. The agent has this file (and the rest of `llm-wiki/how-to/`) loaded as context for the project. Try things like:

- "How do I add a single URL to the wiki?"
- "Show me what's in the wiki"
- "What's the difference between `/wiki-cycle` and `/wiki-update`?"
- "How do I look up prior decisions?"

The agent will route to the right command + walk you through it.
