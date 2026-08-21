---
title: "wiki — skill"
type: how-to
artifact: skill
name: wiki
installed_by: install-wiki
date: 2026-07-31
---

# wiki — skill

Shows your project's wiki index — the folder tree plus a curated file list with summaries — so you can see at a glance what has been captured without opening anything. It is the browsing entry point to the wiki that lives inside your project at `llm-wiki/wiki/`. The index is already formatted for reading, so this skill displays it as-is rather than summarizing it, and offers to open any file you want to drill into. If the index is missing or older than the entries it describes, it regenerates it first.

**Trigger:** */wiki*, or natural phrasings like "show me the wiki", "what's in the wiki", "list wiki topics".

**Input / Output:** Reads `llm-wiki/wiki/_INDEX.md` (and the per-folder `_INDEX.md` files beneath it) and prints it. When regeneration is requested or the index is stale, it rewrites `_INDEX.md`; it can also recompile the top-level orientation map `llm-wiki/wiki/_MAP.md`. It never edits wiki entries.

**Works with:** [`wiki-search`](./wiki-search.md) is the counterpart — this skill is for browsing, that one is for finding. [`wiki-init`](./wiki-init.md) creates the `llm-wiki/wiki/` structure this skill reads. [`wiki-cycle`](./wiki-cycle.md) invokes it as part of the orchestrated run, which is the usual way it gets called.

**Note:** The v1 install model is one wiki per project, rooted at `llm-wiki/wiki/` — there is no shared vault across projects, and no `--topic` argument to disambiguate between multiple wikis.
