---
title: "wiki — skill"
type: how-to
artifact: skill
name: wiki
installed_by: install-wiki
date: 2026-07-31
---

# wiki — skill

Shows your project's wiki index — the folder tree plus a curated file list with summaries — so you can see at a glance what has been captured without opening anything. It is the browsing entry point to the project's wiki, wherever it lives: a notebook in your notebooks vault (the default layout) or `llm-wiki/wiki/` inside the project. The index is already formatted for reading, so this skill displays it as-is rather than summarizing it, and offers to open any file you want to drill into. If the index is missing or older than the entries it describes, it regenerates it first.

**Trigger:** */wiki*, or natural phrasings like "show me the wiki", "what's in the wiki", "list wiki topics".

**Input / Output:** Reads the wiki's top-level `_INDEX.md` (and the per-folder `_INDEX.md` files beneath it) and prints it. When you ask for a refresh, or an index is missing or stale, it regenerates the per-folder `_INDEX.md` files (`sessions/` gets none, and retired entries are left out); it can also recompile the top-level orientation map, `_MAP.md`. It never edits wiki entries.

**Works with:** [`wiki-search`](./wiki-search.md) is the counterpart — this skill is for browsing, that one is for finding. [`new-wiki`](./new-wiki.md) creates the wiki this skill reads. [`wiki-cycle`](./wiki-cycle.md) rebuilds the same indexes as part of its run; you call this skill directly when you want to browse.
