---
name: wiki-search
description: "Search a topic wiki using qmd (hybrid BM25/vector + LLM reranking). Use when the user asks \"what does the wiki say about X\", \"search the wiki for Y\", \"find Z in the wiki\", or wants to look up something in a curated knowledge base. LOOKUP questions only. A holistic question (\"what have we decided about X across entries\", \"is our position on X consistent\", \"what contradicts what\") wants the aggregate pass in /wiki-claims or /wiki-lint --full, not a retriever. After answering, offers once to file a durable answer back into the wiki. Replaces the old grep-based wiki-search.py."
last_reviewed: 2026-09-08
review_after: 2026-12-08
reviewed_for_model: claude-fable-5-1
---

Search a topic wiki using qmd — hybrid BM25 keyword + vector similarity + LLM reranking. Finds entries by meaning, not just exact keywords.

## Route the question first (added 2026-09-08)

A retriever optimises **local** relevance. It answers "which entries mention X?" well and answers "is our thinking on X coherent?" with a plausible local answer that misses the rest. Pick the tool by the shape of the question before running anything:

| The question is... | Use | Why |
|---|---|---|
| **Lookup** — "what does the wiki say about X", "do we have anything on Y", "find the entry about Z" | this skill | one or a few entries answer it |
| **Holistic / cross-entry** — "what have we decided about X across entries", "is our position on X consistent", "what contradicts what", "summarise everything we hold on X" | `/wiki-claims` (claims + contradictions) or `/wiki-lint --full` (semantic pass) | needs analyze → summarize → aggregate over many entries, not top-k retrieval |
| **Browsing** — "what's in the wiki", "show me the topics" | `/wiki` | the INDEX, not a query |

If a holistic question arrives here anyway, say which tool it wants and offer to run it. Do not answer it from the top five hits. (Source: Taskesen's lookup-vs-holistic distinction, agentic-design `research/orchestration/`, handed over by the agent-builder session 2026-09-06.)

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
5. **File the answer, or let it go (added 2026-09-08).** Once the question is answered, decide whether the answer is worth keeping. File-worthy: a comparison the user is likely to revisit; a connection between entries the wiki did not already state; a synthesis across three or more entries; an answer to a gap the wiki could not fill (that one is a `concept-gaps` candidate). Not file-worthy: a plain lookup, a question about wiki structure, a one-off. If file-worthy, ask **once**: "This looks worth keeping — file it as a `project/` entry?" On yes, write the answer to `<topic>/_inbox/temp/<slug>.md` in the entry shape (TL;DR, body, a `## Related` section linking the entries you read) and file it with `wiki-update.py --tier self --no-raw --folder project/<category> --ingested-by claude-code`; if the session will end with `/wrap-up` anyway, hand the answer to that instead. Why: a good answer that stays in the chat is knowledge the wiki paid to derive and then lost (Karpathy's gist names this; the nanzhipro bootstrap skill makes it a step — agentic-design `research/long-term/`).

## Truth-status rerank (optional; the search spec's surface 1)

When entries carry `verified:` (frontmatter or `_signals/<slug>.json` sidecar), sort qmd's results by truth-status bucket before showing them — `verified` above `unverified`, `temporal` and `contradicted` below, `rolled_back` excluded unless asked for:

```bash
qmd search "<query>" --json | python {{WIKI_SCRIPTS_DIR}}/wiki-search-rerank.py
qmd search "<query>" --json | python {{WIKI_SCRIPTS_DIR}}/wiki-search-rerank.py --surface-contradicted   # audit the disagreements
qmd search "<query>" --json | python {{WIKI_SCRIPTS_DIR}}/wiki-search-rerank.py --include-rolled-back    # "what did we used to believe"
```

Contract: `project/best-practices/framework/wiki-search-bucket-rerank-spec.md` in every project wiki. Entries with no `verified` field all land in the same bucket, so on a wiki that has not started verifying the order is unchanged.

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
