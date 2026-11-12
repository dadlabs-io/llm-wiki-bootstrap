---
title: "Reading the wiki in Obsidian — llm-wiki"
type: how-to
pack: llm-wiki
installed_by: install-wiki
date: 2026-11-12
---

# Reading the wiki in Obsidian

A notebook is plain Markdown files. The agent writes them (through `/wiki-update`, `/wiki-cycle`, `/wrap-up`
and `/wiki-promote`); a person reads them. Obsidian is a good reader for them: links, backlinks, tags and
frontmatter all work as they are, and nothing has to be converted.

## Opening a notebook

Open the notebook's folder as a vault: the folder that holds `wiki/`, `raw/`, `_inbox/` and `_config/`
(for a notebook in the vault, `<vault root>/<notebook>`; for an in-project wiki, `<project>/llm-wiki`).
Obsidian creates its own `.obsidian/` settings folder the first time; nothing needs setting up beforehand.

## The folder layout already suits Obsidian

The notebook's system files and folders start with `_`: `wiki/_MAP.md` and `wiki/_INDEX.md`, and beside
`wiki/` the folders `_inbox/` (queued, staged and report files), `_config/` and `_signals/`. They sort to the top
of the file explorer. To keep them out of search and the graph, add `_inbox/`, `_signals/` and `raw/` under
Settings → Files & Links → Excluded files.

## Plugins worth running

| Plugin | Why it helps |
|---|---|
| **Dataview** | Every entry's frontmatter (`tier`, `confidence`, `review_after`, `date`, `tags`) is queryable, so a page can list, say, every tier-1 entry due for review this week. Field meanings: the framework's frontmatter spec in the global toolset (`wiki/project/best-practices/framework/wiki-frontmatter-best-practices.md`) |
| **Obsidian Linter** | Keeps frontmatter consistent if you do edit a page by hand |
| **Tag Wrangler** | Shows tags used once and helps rename a tag everywhere |
| **Backlinks pane** (built in) | Shows live what each entry's `BACKLINKS-AUTO` block holds (that block is written by `wiki-reciprocate-backlinks.py` at each promotion and cycle) |
| **Graph view** (built in) | Shows clusters and loners: where a folder could split, or an entry has no links |

## What not to turn on

- **Automatic link updates on rename or move** (Settings → Files & Links). The framework moves and renames
  pages with its own scripts and rewrites links with `wiki-fix-links.py`; two tools rewriting the same links
  make duplicate fixes that lint then flags. Leave moves to the agent.
- **Note-merging plugins** (e.g. ones that suggest merging similar notes). Entries that disagree are kept
  side by side on purpose; merging them loses one side.

## A reading routine

1. Start at `wiki/HOME.md` or `wiki/_MAP.md` (the map lists every entry by folder).
2. `Ctrl+O` jumps to a page by name; search `#tag-name` to see everything with a tag.
3. Read in Obsidian, write through the agent. Corrections, new sources and moves go through the skills
   (`/wiki-update`, `/wiki-promote`, `/wrap-up`), so the checks, links, indexes and search index stay right.
   Whether a new entry lands in `wiki/` at once or waits in `_inbox/proposed/` for your yes follows the
   notebook's `confirm_before_promote` setting.
