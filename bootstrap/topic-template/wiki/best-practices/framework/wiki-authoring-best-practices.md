---
title: LLM Wiki Authoring — Best Practices
date: 2026-04-18
source_url: internal://synthesis/2026-04-18-wiki-authoring-best-practices
ingested_by: claude-code
tier: self
confidence: high
framework-contract: true
framework-version: 1
last_reviewed: 2026-04-18
review_after: 2026-07-18
tags: [best-practices, wiki, knowledge-base, claim-extraction, contradiction-preservation, curation, self-authored, synthesis]
---

# LLM Wiki Authoring — Best Practices

Our canonical position on running a research wiki (like this one), synthesized from 7 external source entries + 3 self-authored docs + operational learnings from the 2026-04 cycles.

**Authority stack**:
- **Highest**: Karpathy's original gist (foundational pattern)
- **High** (production practitioners): rohitg00's LLM Wiki v2, Chappy Asel's 5-layer stack, lucasastorian's hosted MCP version
- **Medium**: SamurAIGPT's LLM Wiki Agent
- **Historical anchor**: Vannevar Bush's Memex (1945)
- **Operational**: self-authored synthesis (architecture decisions, vision docs, post-mortems)

---

## The foundational reframe — compile, don't retrieve

Karpathy's core insight:

> *"Obsidian is the IDE; the LLM is the programmer; the wiki is the codebase."* — Karpathy, LLM Wiki gist

Most LLM+document workflows are RAG: upload files, retrieve chunks at query time, regenerate an answer. **Every question starts from raw chaos.** Karpathy's pattern is the opposite: **the LLM reads your raw sources once, extracts the key information, and writes it into an interlinked wiki of markdown pages**. Future sessions read the wiki instead of re-deriving from scratch.

Asel validated this empirically: a 313-star markdown + keyword-search repo beat the previous best AI-search pipeline at **91% vs 86%** on the benchmark. For bounded topics, structure beats search.

**Foundational principle**: compile, don't retrieve. The wiki is a **compounding artifact**, not a cache.

## The ten operational principles

### 1. Compile, don't retrieve, for bounded topics

([source: Karpathy](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f), [Asel empirical](https://x.com/chappyasel/status/2041166770472644721))

RAG re-derives; compiled wikis compound. Every raw source you ingest should produce structured markdown that survives the next session. If your wiki is indistinguishable from a document pile with vector search on top, you're doing RAG, not wiki authoring.

### 2. LLM as writer, human as reader

Unanimous across Karpathy, rohitg00, SamurAIGPT, lucasastorian. **No source has the human drafting entries.** The human's role is direction (what topics matter, what questions to answer, what quality bar to enforce). The LLM does the bookkeeping — extraction, linking, summarization, cross-reference.

For workflows-core: user feeds URLs → `/wiki-update` compiles → user reviews at promotion. Never the other way around.

### 3. Raw sources are immutable — always append, never edit

Karpathy, lucasastorian, and our own three-layer rule all converge here. The `raw/` directory is a **write-ahead log**. Never rewrite a raw source. Never silently update an old ingest when you re-fetch.

Without this rule, **silent poisoning is undetectable** (Asel L2, Databricks). Every claim in the wiki must be traceable back to an immutable raw source; if the raw changes and nobody notices, claims get poisoned.

### 4. Both-sides-stay — preserve minority views

This is workflows-core's **signature policy** and goes beyond every external source:
- SamurAIGPT: flag contradictions at ingest (but doesn't say what to do).
- rohitg00: supersession — new wins, old preserved as stale (winner takes all).
- **workflows-core**: both entries stay, even 3-vs-7 minority views. Contradiction-preservation, not resolution.

Rationale: the minority view today may be right tomorrow. Auto-resolving contradictions lossy-compresses the evidence. Better to flag, disclose, and let the reader (human or agent) weigh.

### 5. Claim-level extraction with 4-way classification

**Not described in any external source at our granularity.** workflows-core innovation, validated by `/wiki-claims` skill.

Every factual assertion in every entry is classified as one of:
- **direct-quote** — verbatim from source, in blockquotes
- **sourced** — paraphrased but cleanly attributed
- **synthesis** — our conclusion drawn from multiple sources
- **inference** — our own assertion, unsourced (highest drift risk)

Claims are indexed in `_inbox/claims-index-*.json` for cross-entry comparison. This makes contradiction detection precise (sentence-level, not page-level) and makes drift visible (every `inference` claim is a candidate for future verification).

### 6. Two human checkpoints in any autonomous loop

**Stricter than any external pattern in the batch.** The spectrum from the sources:
- Asel: fully autonomous 700-change AutoResearch runs (no checkpoints).
- rohitg00: event-driven automation, human stays in the loop for curation.
- **workflows-core**: two human checkpoints (URL approval + entry approval) as non-negotiable.

Rationale: **silent poisoning risk** (Mem0 warning, Asel L2) + source-quality blindness justify the conservatism. The wiki is load-bearing for downstream decisions; a bad ingest that survives review can pollute months of work.

Don't soften this. The right move when automation wants to push further is to make the checkpoints *faster*, not remove them.

### 7. Source quality tiers in frontmatter — tier 4 never auto-ingests

4-tier rubric:
- **Tier 1**: Primary research, peer-reviewed papers, official docs from authoritative sources
- **Tier 2**: Practitioner primary (direct quotes, talks by creators, first-party engineering writeups)
- **Tier 3**: Well-sourced commentary (established blogs, secondary analysis with citations)
- **Tier 4**: Opinion pieces, marketing content, unsourced claims → **never auto-ingest**

rohitg00 has a quality threshold; Huber has a gold-set. **No external source implements the full tier rubric or tier-4-hard-block.** Ours is stricter.

Enforce in `/wiki-update` eval gate and `/wiki-list process`. When a source fails tier evaluation, drop to `_inbox/proposed/` for human review, never direct to `wiki/`.

### 8. Distinguish synthesis from direct claims in prose

- Blockquotes for direct quotes (always)
- Explicit **"Synthesis notes"** or **"Our reading"** sections for our interpretations
- `inference`-classified claims marked in prose, not hidden

This closes the hallucination-injection gap: a reader should be able to tell at a glance whether a sentence is "what the source said" vs "what we concluded from the source" vs "our opinion."

### 9. Wiki as build artifact with dependency tracking

Pages track their raw sources and last-compiled date. Frontmatter contract:
- `raw_path`: pointer to the immutable source
- `last_reviewed`: when a human last validated
- `review_after`: when to re-check (decay trigger)
- `confidence`: high / medium / low based on source and age

When a raw source gets an update, or `review_after` passes, the entry is flagged for recompilation. This makes the wiki **reproducible and auditable** — a property external wiki patterns don't describe at this level.

### 10. Federation of single-purpose agents, not a monolith

The full-wiki-cycle system is a federation:
- **Discovery** (`/wiki-discover`) — find candidate sources from feeds
- **Ingestion** (`/wiki-update`) — fetch, synthesize, file with eval gate
- **Linting** (`/wiki-lint`) — mechanical + semantic structural health
- **Claims extraction** (`/wiki-claims`) — pull every factual assertion into indexed form
- **Contradiction hunting** — cross-compare claims for conflicts
- **Refresh/decay** (`/wiki-refresh`) — surface stale entries via `review_after`
- **Promotion** (`/wiki-promote`) — human-gated move from `_inbox/proposed/` to `wiki/`
- **Orchestration** (`/wiki-cycle`) — sequenced runner over all of the above

Each agent is independently tunable. No monolith. If one piece fails, the others keep working.

## Implementation status — what we do now vs what the principles say

**Purpose**: one-stop view of principle-vs-reality, so gaps are visible at a glance and we know where to look when we want to improve. Update this section when state changes; don't let it drift.

Legend: ✅ implemented and enforced · ⚠️ partial / policy not fully automated · ❌ aspirational, not built

| # | Principle | Status | Evidence / gap |
|---|---|---|---|
| 1 | Compile, don't retrieve | ✅ | Wiki is plain markdown (no RAG DB). Confirmed by folder layout at `docker/shared/openclaw/vault/wikis/<topic>/wiki/`. |
| 2 | LLM writes, human reads | ✅ | User feeds URLs via `/wiki-add` → agent compiles via `/wiki-update`. |
| 3 | Raw sources immutable | ✅ | `raw/` folder preserved at wiki root. No rewrite pattern; re-fetches create new timestamped files. |
| 4 | Both-sides-stay (contradiction preservation) | ✅ | Policy baked in. `/wiki-claims` surfaces contradictions; both entries kept. |
| 5 | Claim-level 4-way classification | ✅ | `/wiki-claims` skill implemented. 22 entries retrofitted 2026-04-10. New ingests classify at author time. |
| 6 | Two human checkpoints | ✅ | URL approval gate (`/wiki-add` → `_inbox/pending/`) + entry approval gate (`_inbox/proposed/` → `/wiki-promote --review` → `wiki/`). Non-negotiable. |
| 7 | Source tier-4 hard block | ✅ | Eval gate in `/wiki-update` step 5 (added 2026-04-13). Failing-tier entries drop to `_inbox/proposed/` for human review. |
| 8 | Synthesis vs direct claims distinguished in prose | ⚠️ | Retrofit done 2026-04-10 for 22 entries. Convention baked into `wiki-update` SKILL.md, but enforcement across new ingests relies on author discipline — not mechanically checked by lint. |
| 9 | Dependency tracking (`last_reviewed` / `review_after` / `confidence`) | ⚠️ | 134/148 entries compliant. 14 entries missing lifecycle frontmatter (flagged by 2026-04-16 `/wiki-refresh` scan). `raw_path` pointer part of the principle 9 contract but **not yet in the frontmatter schema** — documented, not implemented. |
| 10 | Federation of specialists (`/wiki-*` skills) | ✅ | All 10 skills exist as Claude Code skills: discover, update, lint, claims, refresh, promote, cycle, search, list, init. |

### Explicit gaps (punch list — where improvement lives)

1. **L5 self-improvement loop not built** (principle 10 culminating goal + Asel L5 on line ~160). Design doc lives in your wiki if you choose to define one. Orchestrator code is a future deliverable.
2. **`raw_path` frontmatter field not enforced** (principle 9 contract gap). Entries link to raw sources via prose only; no machine-readable pointer. Lint can't verify raw-source integrity until this exists.
3. **14 entries missing `last_reviewed` / `review_after`** (principle 9 compliance gap). Tracked in `memory-bank/short-term/_personas/arch/task.md` queue item 9.
4. **Synthesis-vs-direct-claim prose distinction not mechanically verified** (principle 8 enforcement gap). `/wiki-lint` could add a rule that flags prose outside blockquotes / "Synthesis notes" sections that makes factual assertions — not built.
5. **Wiki-discover URL verification bug** (discovery correctness gap). 3 of 4 queue URLs mislabeled in 2026-04-16 cycle; worked around via host yt-dlp, root cause unfixed. Violates principle 3 (raw source integrity starts at discovery).
6. ~~**Mem0 "(per MemPalace third-party)" qualifier not applied** to 4+ entries~~ **✅ RESOLVED 2026-04-22** — sweep applied across all 5 entries (Mem0, Zep/Graphiti, Mastra, session-memory-comparison x2, the-active-memory-layer). Each benchmark claim now carries explicit MemPalace-third-party attribution. (Principle 5 precision gap.) Tracked in arch task queue item 7.

Every item here should either have a tracked task or a decision to accept the gap. No silent drift.

## The one real wiki contradiction — autonomy trajectory

**HIGH-severity contradiction** worth preserving:
- **Asel**: 700-change AutoResearch runs, fully autonomous.
- **rohitg00**: event-driven, human stays in the loop for curation.
- **workflows-core**: two human checkpoints, non-negotiable.

Three positions on the same spectrum, legitimately different. Our position is the most conservative. **We keep it.**

Note that the research frontier continues to push toward more autonomy. This is one to revisit annually — the silent-poisoning risk may soften as models get better at self-critique. Until then, the conservative default holds.

## The lineage — Vannevar Bush's Memex (1945)

> *"Consider a future device for individual use, which is a sort of mechanized private file and library. [...] Any given book of his library can thus be called up and consulted with far greater facility than if it were taken from a shelf. [...] The first idea, however, to be drawn from the analogy concerns selection. Selection by association, rather than by indexing."* — Vannevar Bush, "As We May Think"

Bush couldn't solve **who does the maintenance**. The Memex requires someone to encode the associative trails, and humans don't have the patience. **LLMs solve the maintenance problem.** Karpathy's pattern is Memex at scale — the associative trails are the wiki's cross-references, and the LLM writes them on ingest.

Every workflows-core wiki entry is a Memex trail made durable.

## The 5-layer stack (Asel) — how we map

Asel's 5-layer self-improving AI stack maps onto workflows-core:
- **L1 Knowledge** (static markdown + search) → `wiki/long-term/` + `memory-bank/long-term/`
- **L2 Memory** (active context) → `memory-bank/short-term/` + wiki `active/`
- **L3 Context** (session habits, CLAUDE.md) → `CLAUDE.md` + reading-lists
- **L4 Skills** (reusable routines) → `.claude/skills/` + `bootstrap/workflows/`
- **L5 Self-improvement** (read/write loop over L1-L4) → optional design doc in your wiki (target)

Our three-layer model collapses L1+L2+L3 but the correspondence is clean.

## What workflows-core has that external sources don't

Operational innovations identified as novel:
1. **Claim-level extraction with 4-way classification** (principle 5) — not documented externally
2. **Contradiction-preservation policy** (principle 4) — every external source picks a winner or resolves; we don't
3. **Two-human-gates orchestration** (principle 6) — stricter than any external autonomy model
4. **Source-quality tier-4 hard block** (principle 7) — stricter than any external rubric
5. **Reading-list protocol with recursive includes** — not documented externally
6. **Build-artifact dependency tracking** via `review_after` frontmatter contract (principle 9) — external sources don't describe this
7. **Federation of specialists** (principle 10) — external sources describe monoliths or specific components, not the federation

These aren't "borrowed from the literature." They emerged from our own cycles. The failure-modes pre-mortem lists 7 failure modes that go beyond any single external source — silent poisoning is the one shared concern; the others (100-article cliff, topic bleed, source-quality blindness, etc.) are ours.

## Cross-references to memory architecture

Memory principles directly shape wiki operations:
- **"No deletion, only forgetting"** → don't delete old entries; move to `archive/` with decay signals, still reachable via weighted qmd
- **Memory signals** (recall_count, last_accessed) → add to wiki frontmatter; the agent's access pattern drives the forgetting curve
- **Metacognition bottleneck** → `_INDEX.md` at wiki root is load-bearing, always-loaded
- **OS analogy** → `raw/` is WAL; `wiki/` is the paged-in view

See `memory-architecture-best-practices.md` (sibling reference pattern, if your wiki has it) for the full framing.

## Source entries

Primary — foundational:
- [Karpathy — LLM Wiki Pattern](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f) — compile-vs-retrieve framing
- [Vannevar Bush — Memex / As We May Think (1945)](https://www.theatlantic.com/magazine/archive/1945/07/as-we-may-think/303881/) — historical anchor

Primary — production practitioners:
- [rohitg00 — LLM Wiki v2 (Production Extensions)](https://github.com/rohitg00)
- [Chappy Asel — The Self-Improving AI Stack](https://x.com/chappyasel/status/2041166770472644721)
- [lucasastorian — Hosted LLM Wiki with MCP](https://github.com/lucasastorian)

Novel implementations:
- [SamurAIGPT — LLM Wiki Agent](https://github.com/SamurAIGPT/llm-wiki-agent)

Self-authored:

## Related

- [Wiki Frontmatter Best Practices](./wiki-frontmatter-best-practices.md) — canonical field reference that operationalizes principle 9 (dependency tracking)
- [yzhao062 — agent-style 21 Writing Rules](https://github.com/yzhao062/agent-style) — operational writing rules (Strunk-White + Orwell + Pinker + Gopen-Swan) that govern the prose *inside* wiki entries; complements the structural principles here
