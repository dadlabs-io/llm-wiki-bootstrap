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

## Preflight — before the first search

**Search mode (2026-10-02, task #63).** Each machine is set to one of two modes (`search_mode` in `~/.claude/wiki-config.json`; the installer sets it from the GPU check and never switches it on its own). Before the first search of a session run `uv run --project {{WIKI_SCRIPTS_DIR}} python {{WIKI_SCRIPTS_DIR}}/wiki-qmd-query.py --preflight`; it names the mode.

- **keyword** — a machine with no GPU. The helper runs qmd's keyword index (no model, under a second) with the same scoping and filtering, and says so on its status line. That index returns only entries holding every word, so the helper searches the query's key words together and in every pair and fuses them by rank (task #64: on 8 real searches this found 57 of the full search's top 10, against 25 for the query as typed). Never run `qmd query`, `qmd vsearch` or `qmd embed` on it: each loads a model, which runs on the CPU and takes every core (on 2026-10-02 one full search on the CPU used ~9,900 CPU-seconds and hung the laptop). Matches are by word, not meaning: if a search comes back thin, rephrase with the words an entry would use. Tell the user once that this machine searches by keyword only. Once it has a GPU: `wiki-qmd-query.py --set-mode full` (refused while the GPU check fails), then `qmd embed` once.
- **full** — the GPU search below. The preflight runs the GPU check (CUDA, or Metal on a Mac).

**GPU check on a full machine (2026-09-12).** `qmd query` runs three bundled models in-process through node-llama-cpp. Without a CUDA runtime it falls back to Vulkan, where token generation never returns on this laptop (every never-seen query hung at 100% CPU on all cores; CPU-only was minutes per query). The preflight's check is the same as:

```bash
(cd "$(npm root -g)/@tobilu/qmd" && npx --no-install node-llama-cpp inspect gpu) | grep -E "^(CUDA|Metal):"   # must print `CUDA: available` (or `Metal: available`)
```

If it fails on a full machine, **stop and report it** — do not fall back to `qmd search`, a cloud model, or CPU mode and carry on, and do not switch the machine to keyword to get past it (that is the user's call, for a machine with no GPU). The known fix is the CUDA 13.2 runtime (`winget install --id Nvidia.CUDA --version 13.2 --exact --override "-s cudart_13.2 cublas_13.2"`; node-llama-cpp's prebuilt binary needs 13.1+), and a shell opened before that install lacks the CUDA PATH until restarted. Run the full search through `wiki-qmd-query.py` (below): it applies the 120-second timeout (killing the whole process tree, so no orphaned search holds the GPU), and it holds one of three GPU slots: qmd 2.8.3 sizes its model pools from the weight files, and three concurrent searches fit the 8 GB GPU (peak 7.7 of 8.2 GB, tested 2026-09-14; on qmd 2.1.0 a third failed with "Failed to create any rerank context", so the limit was two) — a fourth caller waits for a slot. `wiki-qmd-query.py --preflight` runs this same GPU check and warns when qmd is older than 2.8.3 (upgrade with `npm i -g @tobilu/qmd@latest`, or set `WIKI_QMD_SLOTS=2`). Everyone — the session and parallel ingest workers alike — uses the full search; there is no keyword fallback (user decision 2026-09-13). If batches get slow, `wiki-qmd-query.py --stats` shows how long searches waited for a slot; the remedy is fewer parallel workers.

## Three search modes

On a keyword machine only the first command runs, and it runs keyword search; the semantic row is not available there.

| Mode | Command | When to use |
|---|---|---|
| **Hybrid + rerank** (recommended) | `uv run --project {{WIKI_SCRIPTS_DIR}} python {{WIKI_SCRIPTS_DIR}}/wiki-qmd-query.py "<query>"` | Best quality. Combines keyword + semantic + reranking with qmd's bundled models on the GPU (on a keyword machine: keyword only, no model). Use by default — after the preflight above; the helper adds the timeout and the GPU slot. It searches the current project's notebook by default; `--notebook <name>` picks another, `--all-notebooks` searches every one — use that when the user asks for everything or the question is plainly about another notebook, and say which was searched. `-k` results (default 30); `-C` the most candidates the reranker may score (default 120 — qmd's pool tops out near 100, so it never cuts; the helper's status line shows how many were reranked). `_MAP`/`_INDEX` are dropped from results. Other `qmd query` options pass through (`--json`, `--min-score`). On a full machine it then lists up to 20 entries only the word-pair keyword search found, under `## Also found by keyword search` (in `--json`, rows marked `"found_by": "keyword"`; the ranked rows are `"full"`): not reranked, so weigh them below the ranked results and open one before relying on it; `--keyword-extra 0` leaves them out. |
| **Keyword only** | `qmd search "<query>"` | Fast, no LLM. Good for exact terms, file names, specific phrases. |
| **Semantic only** | `qmd vsearch "<query>"` | When you're searching by concept, not specific words ("how do agents handle stale knowledge"). Full machines only: it loads the embedding model. |

## What to ask the user (only if not provided)

1. **Query** — what to search for (natural language works — qmd searches by meaning)
2. Optional: `-k N` results returned (default 30)

## Run

```bash
# Recommended — the helper (run the preflight first; on a full machine it adds the timeout and a GPU slot)
uv run --project {{WIKI_SCRIPTS_DIR}} python {{WIKI_SCRIPTS_DIR}}/wiki-qmd-query.py "context engineering for agents"

# How long searches have been waiting for a GPU slot (is a batch slower?)
uv run --project {{WIKI_SCRIPTS_DIR}} python {{WIKI_SCRIPTS_DIR}}/wiki-qmd-query.py --stats

# Did C ever cut the reranker's pool? (sampled titles; exit 1 = C reached, raise it; /wiki-cycle --full runs it)
uv run --project {{WIKI_SCRIPTS_DIR}} python {{WIKI_SCRIPTS_DIR}}/wiki-qmd-query.py --depth-check --notebook <name>

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
2a. **Cite only what you opened (added 2026-09-16).** A hit proves an entry exists, not what it says: the snippet is a fragment picked for similarity to the *query*, and the entry may qualify it, attribute it to a source it rejects, or be superseded by the entry below it. Rely on or quote an entry only after reading it; otherwise offer it as an unread pointer ("there's an entry on X I haven't opened"). Contract: `{{TOOLSET_DIR}}/wiki/project/best-practices/framework/tiered-context-loading.md`.
3. If zero results on `qmd search`, try the full search (`wiki-qmd-query.py`, adds semantic matching on a full machine) or rephrase the query
4. For browsing what exists, use `/wiki` slash command to show the INDEX
5. **File the answer, or let it go (added 2026-09-08).** Once the question is answered, decide whether the answer is worth keeping. File-worthy: a comparison the user is likely to revisit; a connection between entries the wiki did not already state; a synthesis across three or more entries; an answer to a gap the wiki could not fill (that one is a `concept-gaps` candidate). Not file-worthy: a plain lookup, a question about wiki structure, a one-off. If file-worthy, ask **once**: "This looks worth keeping — file it as a `project/` entry?" On yes, write the answer to `<topic>/_inbox/temp/<slug>.md` in the entry shape (TL;DR, body, a `## Related` section linking the entries you read) and file it with `wiki-update.py --tier self --no-raw --folder project/<category> --ingested-by claude-code`; if the session will end with `/wrap-up` anyway, hand the answer to that instead. Why: a good answer that stays in the chat is knowledge the wiki paid to derive and then lost (Karpathy's gist names this; the nanzhipro bootstrap skill makes it a step — agentic-design `research/long-term/`).

## Truth-status rerank (optional; the search spec's surface 1)

When entries carry `verified:` (frontmatter or `_signals/<slug>.json` sidecar), sort qmd's results by truth-status bucket before showing them — `verified` above `unverified`, `temporal` and `contradicted` below, `rolled_back` excluded unless asked for:

```bash
qmd search "<query>" --json | uv run --project {{WIKI_SCRIPTS_DIR}} python {{WIKI_SCRIPTS_DIR}}/wiki-search-rerank.py
qmd search "<query>" --json | uv run --project {{WIKI_SCRIPTS_DIR}} python {{WIKI_SCRIPTS_DIR}}/wiki-search-rerank.py --surface-contradicted   # audit the disagreements
qmd search "<query>" --json | uv run --project {{WIKI_SCRIPTS_DIR}} python {{WIKI_SCRIPTS_DIR}}/wiki-search-rerank.py --include-rolled-back    # "what did we used to believe"
```

Contract: `{{TOOLSET_DIR}}/wiki/project/best-practices/framework/wiki-search-bucket-rerank-spec.md`. Entries with no `verified` field all land in the same bucket, so on a wiki that has not started verifying the order is unchanged.

## Maintenance

Every promotion re-indexes the search itself (`wiki-promote.py`, so `/wiki-promote`, `/wrap-up` and `/wiki-cycle` do), and `/wiki-cycle` re-indexes before its workers search. An entry filed straight into `wiki/` (direct mode) waits for the next of those. If search seems stale, re-index by hand:
```bash
uv run --project {{WIKI_SCRIPTS_DIR}} python {{WIKI_SCRIPTS_DIR}}/wiki-qmd-query.py --reindex   # qmd update, then qmd embed on a full machine only
```

The collection is configured at: `<vault>/<topic>/wiki/` — the path that was used at install time.

## Don't

- Don't use the old `wiki-search.py` grep script — it's been replaced by qmd
- Don't read every matched file unprompted — show snippets first, ask which to drill into
- Don't answer from snippets — an unopened entry is a pointer, never a source
- Don't run `qmd query`, `qmd vsearch` or `qmd embed` on a keyword machine, even to compare: they load a model and hang it on the CPU
