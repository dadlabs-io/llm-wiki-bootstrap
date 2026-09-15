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

## CUDA preflight — before the first `qmd query`

**CUDA preflight (2026-09-12).** `qmd query` runs three bundled models in-process through node-llama-cpp. Without a CUDA runtime it falls back to Vulkan, where token generation never returns on this laptop (every never-seen query hung at 100% CPU on all cores; CPU-only was minutes per query). Before the first `qmd query` of a session run:

```bash
(cd "$(npm root -g)/@tobilu/qmd" && npx --no-install node-llama-cpp inspect gpu) | grep -E "^CUDA:"   # must print `CUDA: available`
```

If it prints anything else, **stop and report it** — do not fall back to `qmd search`, a cloud model, or CPU mode and carry on. The known fix is the CUDA 13.2 runtime (`winget install --id Nvidia.CUDA --version 13.2 --exact --override "-s cudart_13.2 cublas_13.2"`; node-llama-cpp's prebuilt binary needs 13.1+), and a shell opened before that install lacks the CUDA PATH until restarted. Run the full search through `wiki-qmd-query.py` (below): it applies the 120-second timeout (killing the whole process tree, so no orphaned search holds the GPU), and it holds one of three GPU slots: qmd 2.8.3 sizes its model pools from the weight files, and three concurrent searches fit the 8 GB GPU (peak 7.7 of 8.2 GB, tested 2026-09-14; on qmd 2.1.0 a third failed with "Failed to create any rerank context", so the limit was two) — a fourth caller waits for a slot. `wiki-qmd-query.py --preflight` runs this same CUDA check and warns when qmd is older than 2.8.3 (upgrade with `npm i -g @tobilu/qmd@latest`, or set `WIKI_QMD_SLOTS=2`). Everyone — the session and parallel ingest workers alike — uses the full search; there is no keyword fallback (user decision 2026-09-13). If batches get slow, `wiki-qmd-query.py --stats` shows how long searches waited for a slot; the remedy is fewer parallel workers.

## Three search modes

| Mode | Command | When to use |
|---|---|---|
| **Hybrid + rerank** (recommended) | `python {{WIKI_SCRIPTS_DIR}}/wiki-qmd-query.py "<query>"` | Best quality. Combines keyword + semantic + reranking with qmd's bundled models on the GPU. Use by default — after the CUDA preflight above; the helper adds the timeout and the GPU slot. It searches the current project's notebook by default; `--notebook <name>` picks another, `--all-notebooks` searches every one — use that when the user asks for everything or the question is plainly about another notebook, and say which was searched. `-k` results (default 20); `-C` candidates the reranker scores (default sized to what is searched: 8% of its files, 40–200). `_MAP`/`_INDEX` are dropped from results. Other `qmd query` options pass through (`--json`, `--min-score`). |
| **Keyword only** | `qmd search "<query>"` | Fast, no LLM. Good for exact terms, file names, specific phrases. |
| **Semantic only** | `qmd vsearch "<query>"` | When you're searching by concept, not specific words ("how do agents handle stale knowledge"). |

## What to ask the user (only if not provided)

1. **Query** — what to search for (natural language works — qmd searches by meaning)
2. Optional: `-k N` results returned (default 20)

## Run

```bash
# Recommended — hybrid search (run the CUDA preflight first; the helper adds the timeout and a GPU slot)
python {{WIKI_SCRIPTS_DIR}}/wiki-qmd-query.py "context engineering for agents"

# How long searches have been waiting for a GPU slot (is a batch slower?)
python {{WIKI_SCRIPTS_DIR}}/wiki-qmd-query.py --stats

# Is C still deep enough as a notebook grows? (C vs 2C on sampled titles; /wiki-cycle --full runs it)
python {{WIKI_SCRIPTS_DIR}}/wiki-qmd-query.py --depth-check --notebook <name>

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
3. If zero results on `qmd search`, try the full search (`wiki-qmd-query.py`, adds semantic matching) or rephrase the query
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
