---
title: "wiki-search — skill"
type: how-to
artifact: skill
name: wiki-search
installed_by: install-wiki
date: 2026-07-31
---

# wiki-search — skill

Looks things up in your wiki by meaning, not just by matching words. It runs on qmd, which combines BM25 keyword search with vector similarity and an LLM reranking pass, so a question phrased in plain English finds the right entry even when it shares no vocabulary with it. Use it whenever you want to know whether the wiki already covers something before you go research it again.

**Trigger:** */wiki-search "<query>"*, plus natural phrasings like "what does the wiki say about X", "search the wiki for Y", or "find Z in the wiki".

**Input / Output:** consumes a natural-language query and an optional `--top N` result limit. Produces ranked matches with file paths, scores, and snippets, shown to you first rather than read in bulk — the skill then offers to open a specific match for full context. Three modes are available: `qmd query` for the recommended hybrid search with reranking, `qmd search` for fast keyword-only lookups of exact terms or filenames, and `qmd vsearch` for purely conceptual searches. `qmd get` retrieves one file and `qmd ls` lists everything in the collection.

If results look stale after a batch of new entries, re-index with `qmd update` followed by `qmd embed`.

**Works with:** [`wiki`](./wiki.md) is the better choice for browsing rather than searching — it shows the wiki's INDEX. [`wiki-update`](./wiki-update.md) leans on this search during ingestion to find the existing entries a new source should cross-link to, which is also why re-indexing matters after a large ingest.

**Note:** this replaced an older grep-based `wiki-search.py`; the script is gone and qmd is the only search path.

Full walkthrough: [`../../wiki-search.md`](../../wiki-search.md)
