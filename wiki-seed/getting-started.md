---
title: "Getting started — llm-wiki"
type: how-to
pack: llm-wiki
installed_by: install-wiki
date: 2026-09-08
---

# Getting started

You just ran `/new-wiki` and have a fresh project. Here's the first hour.

## What you have

- `<project>/CLAUDE.md` — agent's first-read document; imports the wiki README, the command reference (`how-to/llm-wiki/commands.md`) and the wiki MAP
- a startup hook (installed with the global tooling): at startup and after `/clear` it lists this project's resume files (`sessions/active-context.md`, `sessions/<persona>/handoff.md`, `task.md`) for the session to read. A fresh project has none yet — the first `/wrap-up` writes them
- `<project>/.claude/wiki-config.json` — points at the global skills and scripts in `~/.claude/` (a bundled install has its own copy under `<project>/.claude/` instead)
- the wiki root (`<project>/llm-wiki/` or a notebook in your vault) — `wiki/` with the folders you chose (`project/`, `research/`, always `sessions/`), plus the seeded `how-to/` usage docs, and with `research/` the trusted-sources page `_config/feeds.md`

## First actions

### 1. Restart Claude Code (only if the tooling was just installed)

If `/new-wiki` had to install the global tooling during the scaffold (it says so, and the summary carries `needs_restart: true`), restart Claude Code so the other `/wiki-*` skills appear. A project pointed at an already-installed set needs no restart.

### 2. Add your first wiki entry

If you have a **`project/` folder** (what you build):
- Start coding
- At end of session, run `/wrap-up` — it shows the entries it would file; say `go`
- They stage in `_inbox/proposed/` (at the wiki root, beside `wiki/`), and `/wrap-up` offers to promote them on the spot
- Anything you hold back, promote later with `/wiki-promote --review`

If you have a **`research/` folder** (what you ingest):
- Find a useful article
- Run `/wiki-update https://example.com/article` — with an empty `research/` it proposes the first subfolder and creates it
- If you enabled Drive ingest, drop URLs into Google Drive (`__FOR CLAUDE/<project-slug>/`) and batch-process with `/wiki-cycle`
- List the blogs, YouTube channels and repos you trust in `_config/feeds.md` (beside `wiki/`; `/new-wiki` created it empty unless you named some), or ask the agent to add them; `/wiki-discover` (or `/wiki-cycle`) searches them for new material

Chose neither? You have a plain notes notebook: `/wrap-up` still keeps `sessions/`; create `project/` or `research/` whenever you want the other flows.

### 3. Configure your CLAUDE.md

Open `<project>/CLAUDE.md`. Fill in the **Conventions** section with whatever you currently know about the project — naming, testing, file layout, anti-patterns. This is the agent's constitution; bad CLAUDE.md = bad agent behavior.

Keep the Conventions section short. CLAUDE.md is a shortcut, not a manual. Use `@imports` to pull in detail when needed.

## Common gotchas

- **Where the skills live**: in `~/.claude/skills/` and `~/.claude/wiki-scripts/` (global, shared by every project), or under `<project>/.claude/` for a bundled install. Don't hand-edit either — they get overwritten on refresh. Edit the bootstrap source instead.
- **Search hangs or pegs the CPU**: qmd's full search runs local models and needs a GPU: the CUDA runtime on an NVIDIA machine (see the optional GPU step on the [install](./install.md) page), or Metal on a Mac. The installer records each machine's search mode; a machine with no GPU is set to `keyword` and searches qmd's keyword index only, with no model, so it never hangs (same page). On a `full` machine `/wiki-search` checks the GPU before its first search and stops rather than falling back, and ingest (`/wiki-update`, `/wiki-cycle`) stops too. `uv run --project ~/.claude/wiki-scripts python ~/.claude/wiki-scripts/wiki-qmd-query.py --preflight` says which mode this machine is in.
- **Drive OAuth**: if you opted into Drive ingest and the OAuth flow failed, see [`drive-setup`](./drive-setup.md).
- **Multiple projects on one machine**: they share the one global tooling; each project's `.claude/wiki-config.json` says which wiki it uses, so nothing conflicts. The Drive OAuth token is shared too (good — sign in once).

## Next reading

- [`wiki-update`](./skills/wiki-update.md) — adding a single URL
- [`wiki-cycle`](./skills/wiki-cycle.md) — full ingest pipeline
- [`wrap-up`](./skills/wrap-up.md) — end-of-session distillation
- [`wiki-search`](./skills/wiki-search.md) — hybrid BM25 + vector + LLM rerank search
