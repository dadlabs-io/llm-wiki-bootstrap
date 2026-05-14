# Getting started

You just ran `/new-wiki` and have a fresh project. Here's the first hour.

## What you have

- `<project>/CLAUDE.md` — agent's first-read document; auto-imports `llm-wiki/README.md` and the wiki MAP
- `<project>/.claude/skills/` — 13 slash commands now available in Claude Code
- `<project>/.claude/wiki-scripts/` — Python helpers behind those skills
- `<project>/llm-wiki/wiki/` — empty taxonomy folders waiting for content
- `<project>/llm-wiki/best-practices/` — seeded reference docs
- (development) agentmemory MCP wired into Claude Code settings

## First actions

### 1. Restart Claude Code

If `/new-wiki` installed agentmemory (development projects), Claude Code needs a restart to pick up the new MCP server. After restart, agentmemory will auto-load recent session context.

### 2. Read `llm-wiki/best-practices/`

The seeded best-practices cover communication, coding, documentation, logging, testing, etc. Skim them once so you know what's there. Reference them in CLAUDE.md or in `wiki/` entries as you go.

### 3. Add your first wiki entry

For a **development project**:
- Start coding
- At end of session, run `/wrap-up`
- Review the proposed entries it generates (in `wiki/_inbox/proposed/`)
- Approve and promote with `/wiki-promote`

For a **research project**:
- Find a useful article
- Run `/wiki-update https://example.com/article`
- Or drop URLs into Google Drive (`__FOR CLAUDE/<project-slug>/`) and batch-process with `/wiki-cycle`

### 4. Configure your CLAUDE.md

Open `<project>/CLAUDE.md`. Fill in the **Conventions** section with whatever you currently know about the project — naming, testing, file layout, anti-patterns. This is the agent's constitution; bad CLAUDE.md = bad agent behavior.

Don't write more than ~120 lines. CLAUDE.md is a shortcut, not a manual. Use `@imports` to pull in detail when needed.

## Common gotchas

- **`/new-wiki` paths**: skills/scripts/templates live at `<project>/.claude/`. Don't hand-edit these — they get overwritten on re-install. Edit the bootstrap source instead.
- **agentmemory restart**: if `/wrap-up` says "agentmemory not reachable", Claude Code didn't restart after install. Restart and try again.
- **Drive OAuth**: if you opted into Drive ingest and the OAuth flow failed, see `how-to/drive-setup.md`.
- **Multiple projects on one machine**: each project has its own `.claude/skills/`. Skills don't conflict between projects. The Drive OAuth token IS shared globally (good — sign in once).

## Next reading

- `how-to/wiki-update.md` — adding a single URL
- `how-to/wiki-cycle.md` — full ingest pipeline
- `how-to/wrap-up.md` — end-of-session distillation
- `how-to/wiki-search.md` — hybrid BM25 + vector + LLM rerank search
