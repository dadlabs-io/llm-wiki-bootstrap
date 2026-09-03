---
name: wiki-search
description: Search a topic wiki using qmd (hybrid BM25/vector + LLM reranking). Use when the user asks "what does the wiki say about X", "search the wiki for Y", "find Z in the wiki", or wants to look up something in a curated knowledge base. Replaces the old grep-based wiki-search.py.
last_reviewed: 2026-09-02
review_after: 2026-12-02
reviewed_for_model: claude-fable-5-1
---

Search a topic wiki using qmd — hybrid BM25 keyword + vector similarity + LLM reranking. Finds entries by meaning, not just exact keywords.

## Three search modes

| Mode | Command | When to use |
|---|---|---|
| **Hybrid + rerank** (recommended) | `qmd query "<query>"` | Best quality. Combines keyword + semantic + reranking. Use by default. |
| **Keyword only** | `qmd search "<query>"` | Fast, no LLM. Good for exact terms, file names, specific phrases. |
| **Semantic only** | `qmd vsearch "<query>"` | When you're searching by concept, not specific words ("how do agents handle stale knowledge"). |

## What to ask the user (only if not provided)

1. **Query** — what to search for (natural language works — qmd searches by meaning)
2. Optional: `--top N` to limit results (default shows top matches)

## Run

```bash
# Recommended — hybrid search
qmd query "context engineering for agents"

# Keyword search (fast, no LLM)
qmd search "silent poisoning mem0"

# Semantic search (meaning-based)
qmd vsearch "how should we handle stale knowledge"

# Get a specific file
qmd get "qmd://wiki/path/to/file.md"

# List all files in the collection
qmd ls
```

## After running

1. Show the results to the user (file paths + scores + snippets)
2. If results look promising, **offer to read one of the matched files** with the Read tool for full context
3. If zero results on `qmd search`, try `qmd query` (adds semantic matching) or rephrase the query
4. For browsing what exists, use `/wiki` slash command to show the INDEX

## Maintenance

If new entries are added and search seems stale, re-index:
```bash
qmd update
qmd embed
```

The collection is configured at: `<vault>/<topic>/wiki/` — the path that was used at install time.

## Don't

- Don't use the old `wiki-search.py` grep script — it's been replaced by qmd
- Don't read every matched file unprompted — show snippets first, ask which to drill into
- Don't forget to run `qmd update && qmd embed` after batch ingestion
