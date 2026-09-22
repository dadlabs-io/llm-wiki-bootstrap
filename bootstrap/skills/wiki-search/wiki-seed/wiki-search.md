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

**Input / Output:** consumes a natural-language query, plus an optional `-k N` (results returned, default 30). It searches the current project's notebook unless you name another (`--notebook <name>`) or ask for all of them (`--all-notebooks`), and it leaves `_MAP` and `_INDEX` pages out of the results. Produces ranked matches with file paths, scores, and snippets, shown to you first rather than read in bulk — the skill then offers to open a specific match for full context. Three modes are available: the recommended hybrid search with reranking, run through the `wiki-qmd-query.py` helper (it wraps `qmd query` with a timeout and a GPU slot), `qmd search` for fast keyword-only lookups of exact terms or filenames, and `qmd vsearch` for purely conceptual searches. `qmd query` runs qmd's bundled models on the GPU and needs the CUDA runtime: the skill's preflight (`wiki-qmd-query.py --preflight`) checks for it first, and a missing runtime or a timed-out query is reported and fixed, never worked around (on 2026-09-12 the Vulkan fallback hung every fresh query at 100% CPU until CUDA 13.2 was installed). `qmd get` retrieves one file and `qmd ls` lists everything in the collection. After the answer, the skill decides whether it is worth keeping (a comparison you will revisit, a connection the wiki did not state, a synthesis across several entries, a gap it could not fill) and, if so, asks once whether to file it as a `project/` entry so the answer compounds instead of staying in the chat.

If results look stale after a batch of new entries, re-index with `qmd update` followed by `qmd embed`. The mechanical lint now reports the collection's indexed file count against the files on disk, so a stale or missing index shows up there too.

**Works with:** [`wiki`](./wiki.md) is the better choice for browsing rather than searching — it shows the wiki's INDEX. [`wiki-update`](./wiki-update.md) leans on this search during ingestion to find the existing entries a new source should cross-link to, which is also why re-indexing matters after a large ingest. [`wiki-claims`](./wiki-claims.md) and [`wiki-lint`](./wiki-lint.md) take the cross-entry questions this skill routes away.

**Note:** this replaced an older grep-based `wiki-search.py`; the script is gone and qmd is the only search path.

## Full walkthrough

Search `wiki/` using BM25 + vector similarity + LLM rerank.

### Usage

```
/wiki-search "your query"
```

Returns a ranked list of relevant entries with snippets. Use natural language — no special syntax needed.

### How the ranking works

1. **BM25** over title + body — fast lexical match
2. **Vector similarity** over chunked entries — semantic match
3. **LLM rerank** of the top candidates (`-C`, sized to about 8% of the notebook's files, between 40 and 200) — fine-grained relevance

Each entry's final score combines all three. Optionally, results can be re-sorted by verification status (`verified` first, `contradicted` lower, `rolled_back` hidden unless asked for) with the `wiki-search-rerank.py` helper; entries with no `verified` field keep qmd's order.

### When to use it

- Before writing a new entry — see if it overlaps with existing content (contradictions are OK, duplicates aren't)
- During coding — "have we decided how to handle X?" → search prior decisions
- Researching a topic — start broad, then drill into specific entries

### Don't

- Don't substitute search for reading — search gets you to the right entries, but the full entry text is where the actual content is
- Don't expect staged entries in results — `_inbox/proposed/` sits beside `wiki/`, and only `wiki/` is indexed
- Don't expect grep-like exact matches — use `qmd search "<terms>"` from a terminal if you need that
- Don't call `qmd query` directly — go through `wiki-qmd-query.py`, which runs three searches on the GPU at once by default (two on qmd older than 2.8.3) and queues the rest; everyone, the session and parallel workers alike, uses the full search, and `--stats` shows how long searches waited (the fix for a slow batch is fewer workers, never keyword search)

### Direct CLI alternative

```
qmd search "your terms"
```

Keyword-only, no model at all — fastest for known-string lookups.

