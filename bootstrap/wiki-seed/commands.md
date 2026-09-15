---
title: "Commands reference — llm-wiki"
type: how-to
pack: llm-wiki
installed_by: install-wiki
date: 2026-09-08
---

# Commands reference — every slash command

> ⚠️ **Framework-managed file.** This is shipped by the LLM-wiki installer and may be overwritten when you refresh the framework. **Don't hand-edit.** To customize, see the wiki root's `README.md` → "Framework-managed folders".

Canonical reference for the LLM-wiki framework. Each command works inside Claude Code (or Cursor, via the .mdc rules) once the framework is installed for this project.

## The user-facing commands (these are the only ones you'll typically type)

| Command | When to use it |
|---|---|
| `/new-wiki` | Scaffold a new project. Checks the global tooling, then asks name, review gate, description, `project/` folder, `research/` folder, where the wiki lives. Only needed to **start** a project. |
| `/wiki-update <url>` | Add one external reference (article, paper, video) to the wiki right now |
| `/wiki-cycle` | Batch ingest — discover, ingest (staged for your review), lint, backlinks and indexes, morning report, commit. `--full` adds semantic lint, claims, synthesis and refresh, and promotes. The daily/weekly command for `research/`. |
| `/wiki-search "<query>"` | Hybrid BM25 + vector + LLM-reranked search across your wiki |
| `/wrap-up` | End of session: updates the session journal and resume dashboards, proposes durable entries (you confirm), stages them, and offers to promote them. |
| `/task-list` | The project's task list (top of `task.md`): show it, add a task, mark one done, remove one only on your word. Plain speech works as well: "add a task …", "delete task 4", "what's on my list". |
| `/wiki-promote` | Walk staged entries in `_inbox/proposed/` and accept/reject each one |
| `/wiki-verify` | Mark an entry verified — entries never self-certify |
| `/wiki-rollback` | Roll an entry back to its verified ancestor |
| `/wiki-init` | Manually scaffold the wiki folder (rarely needed — `/new-wiki` does it for you) |

## The internal commands (invoked by other commands, you usually don't type these)

These are listed for completeness. `/wiki-cycle` invokes them in order; you can also call them directly when debugging.

| Command | What it does |
|---|---|
| `/wiki-discover` | Search the notebook's trusted feeds (`_config/feeds.md`) for new content, dedupe, queue candidates for your review |
| `/wiki-list` | Manage the `_inbox/pending/` queue |
| `/wiki-lint` | Mechanical lint (broken links, orphans, frontmatter, and the body checks that mirror the ingest gate — TL;DR, Related links, tags, stubs, unquoted numbers) and optionally semantic lint |
| `/wiki-claims` | Extract claims from entries, find contradictions |
| `/wiki-refresh` | Scan for stale entries (`review_after` date passed) |
| `/wiki-report` | Generate the morning report from a cycle run |
| `/wiki` | Browse the wiki — show the current `_INDEX.md` |

## Daily rhythm

**For the `project/` half (what you build):**
1. Start a session — at startup and after `/clear` the SessionStart hook lists the resume files (`sessions/active-context.md`, then `sessions/<persona>/handoff.md` and `task.md`, each if present) and the session reads them before its first reply; the Resuming section in CLAUDE.md is the fallback where no hook is installed; the `_MAP.md` is always-loaded via CLAUDE.md
2. Code + decide + investigate
3. `/wrap-up` at end — distills the session
4. Accept wrap-up's promote offer, or run `/wiki-promote --review` later for anything left staged

**For the `research/` half (what you ingest):**
1. If Drive ingest is enabled, drop URLs into Drive (`__FOR CLAUDE/<project-slug>/`) throughout the day
2. Or `/wiki-update <url>` for one-offs
3. `/wiki-cycle` once a day/week — discovers, ingests, lints; then `/wiki-promote --review` for what it staged
4. `/wiki-search "<query>"` whenever you need to look something up

## See also (deeper docs per command)

- [`getting-started`](./getting-started.md) — your first hour with a freshly-scaffolded project
- [`wiki-update`](./skills/wiki-update.md) — `/wiki-update` in depth (direct vs staged, the gate, dedup)
- [`wiki-cycle`](./skills/wiki-cycle.md) — `/wiki-cycle` orchestrator + mode flags
- [`wrap-up`](./skills/wrap-up.md) — `/wrap-up` categories + safety
- [`task-list`](./skills/task-list.md) — `/task-list`: the owner tables, the two rules, what it runs for each phrase
- [`wiki-search`](./skills/wiki-search.md) — `/wiki-search` ranking model
- [`drive-setup`](./drive-setup.md) — Google Drive OAuth one-time setup
- [`install`](./install.md) — installing the framework on a fresh machine

## Where to ask the agent for help

You can always ask in plain English. The agent has this file loaded (CLAUDE.md imports it) and reads the other pages in this folder when a question needs them. Try things like:

- "How do I add a single URL to the wiki?"
- "Show me what's in the wiki"
- "What's the difference between `/wiki-cycle` and `/wiki-update`?"
- "How do I look up prior decisions?"

The agent will route to the right command + walk you through it.
