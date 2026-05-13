# /wiki-search — hybrid search across this project's wiki

Search `llm-wiki/wiki/` (and `llm-wiki/best-practices/` if enabled) using BM25 + vector similarity + LLM rerank.

## Usage

```
/wiki-search "your query"
```

Returns a ranked list of relevant entries with snippets. Use natural language — no special syntax needed.

## How the ranking works

1. **BM25** over title + body — fast lexical match
2. **Vector similarity** over chunked entries — semantic match
3. **LLM rerank** of the top N — fine-grained relevance

Each entry's final score combines all three. Tier 1-2 entries get a small boost; tier 4 entries get a small penalty (you can disable this in config).

## When to use it

- Before writing a new entry — see if it overlaps with existing content (contradictions are OK, duplicates aren't)
- During coding — "have we decided how to handle X?" → search prior decisions
- Researching a topic — start broad, then drill into specific entries

## Don't

- Don't substitute search for reading — search gets you to the right entries, but the full entry text is where the actual content is
- Don't rely on search to find unindexed work — `wiki/_inbox/proposed/` isn't searched by default (it's staging, not yet promoted)
- Don't expect grep-like exact matches — use `qmd query "<terms>"` from a terminal if you need that

## Direct CLI alternative

```
qmd query "your terms"
```

Same backend, no LLM rerank — faster for known-string lookups.
