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

**Trigger:** */wiki-search "<query>"*, plus natural phrasings like "what does the wiki say about X", "search the wiki for Y", or "find Z in the wiki". It is for **lookup** questions. A holistic question ("what have we decided about X across entries", "is our position on X consistent", "what contradicts what") is routed to [`wiki-claims`](./wiki-claims.md) or [`wiki-lint`](./wiki-lint.md) `--full` instead, because a retriever answers a whole-wiki question with a plausible local answer.

**Input / Output:** consumes a natural-language query and an optional `--top N` result limit. Produces ranked matches with file paths, scores, and snippets, shown to you first rather than read in bulk — the skill then offers to open a specific match for full context. Three modes are available: `qmd query` for the recommended hybrid search with reranking, `qmd search` for fast keyword-only lookups of exact terms or filenames, and `qmd vsearch` for purely conceptual searches. `qmd get` retrieves one file and `qmd ls` lists everything in the collection. After the answer, the skill decides whether it is worth keeping (a comparison you will revisit, a connection the wiki did not state, a synthesis across several entries, a gap it could not fill) and, if so, asks once whether to file it as a `project/` entry so the answer compounds instead of staying in the chat.

If results look stale after a batch of new entries, re-index with `qmd update` followed by `qmd embed`. The mechanical lint now reports the collection's indexed file count against the files on disk, so a stale or missing index shows up there too.

**Works with:** [`wiki`](./wiki.md) is the better choice for browsing rather than searching — it shows the wiki's INDEX. [`wiki-update`](./wiki-update.md) leans on this search during ingestion to find the existing entries a new source should cross-link to, which is also why re-indexing matters after a large ingest. [`wiki-claims`](./wiki-claims.md) and [`wiki-lint`](./wiki-lint.md) take the cross-entry questions this skill routes away.

**Note:** this replaced an older grep-based `wiki-search.py`; the script is gone and qmd is the only search path.

## Full walkthrough

Search `wiki/` (and `llm-wiki/best-practices/` if enabled) using BM25 + vector similarity + LLM rerank.

### Usage

```
/wiki-search "your query"
```

Returns a ranked list of relevant entries with snippets. Use natural language — no special syntax needed.

### How the ranking works

1. **BM25** over title + body — fast lexical match
2. **Vector similarity** over chunked entries — semantic match
3. **LLM rerank** of the top N — fine-grained relevance

Each entry's final score combines all three. Tier 1-2 entries get a small boost; tier 4 entries get a small penalty (you can disable this in config).

### When to use it

- Before writing a new entry — see if it overlaps with existing content (contradictions are OK, duplicates aren't)
- During coding — "have we decided how to handle X?" → search prior decisions
- Researching a topic — start broad, then drill into specific entries

### Don't

- Don't substitute search for reading — search gets you to the right entries, but the full entry text is where the actual content is
- Don't rely on search to find unindexed work — `wiki/_inbox/proposed/` isn't searched by default (it's staging, not yet promoted)
- Don't expect grep-like exact matches — use `qmd query "<terms>"` from a terminal if you need that

### Direct CLI alternative

```
qmd query "your terms"
```

Same backend, no LLM rerank — faster for known-string lookups.

