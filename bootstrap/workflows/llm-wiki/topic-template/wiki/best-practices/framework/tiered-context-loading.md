---
title: "Tiered Context Loading — How Agents Consult the Wiki"
date: 2026-04-24
source_url: internal://session/2026-04-24-tiered-context-loading
ingested_by: claude-code
tier: self
confidence: high
framework-contract: true
framework-version: 1
last_reviewed: 2026-04-24
review_after: 2026-07-24
tags: [framework-contract, best-practice, context-engineering, L3, tiered-loading, agent-guidance]
---

# Tiered Context Loading

The convention any agent follows when pulling context from this wiki. Implements Chappy Asel's L3 (Context Engineering) — *"Three-tier loading pattern: abstracts → overviews → full content only on demand. Load minimum context at the lowest resolution; drill down only when needed."*

## Why this contract exists

Without a loading policy, agents either:
- **Read too much**: pull entire folders or the full INDEX into context, triggering context rot (Chroma: recall drops as tokens rise)
- **Read too little**: skim _MAP.md only, miss relevant entries, hallucinate gaps
- **Read wrong**: grep a keyword, find 5 matches, read only one, miss the canonical entry

The tiered convention gives a deterministic "what to load, in what order, based on what you're doing."

## The three tiers

| Tier | Artifact | Token cost | When to load |
|---|---|---|---|
| **Tier 1 — Always-loaded map** | `wiki/_MAP.md` | ~2K | Every session. Loaded via CLAUDE.md `@` import; agents never need to explicitly fetch it. Provides folder purposes + top entries per folder + pointers to hubs (HOME.md plus any hub pages your wiki defines). |
| **Tier 2 — Per-folder INDEX** | `wiki/<folder>/_INDEX.md` | ~1-3K each | When the agent is working in a specific area (e.g., responding to a query about memory → load `active/_INDEX.md` + `long-term/_INDEX.md`). Scannable per-folder map with every entry's title + tier + TL;DR. |
| **Tier 3 — Full entry content** | `wiki/<folder>/<slug>.md` | Variable | When the agent needs specific claims, quotes, or detail. Reach via (a) qmd search for concept/keyword, (b) direct read of a known slug, (c) following a link from an INDEX or another entry. |

## Decision tree for agents

```
Agent receives a prompt/question touching the wiki
│
├── Is _MAP.md already in context? (YES — loaded via CLAUDE.md @import)
│     └── Scan MAP for relevant folder(s)
│
├── Does the prompt touch a specific folder/area?
│   ├── YES → load that folder's _INDEX.md (tier-2)
│   │         Scan for relevant entry titles + TL;DRs
│   │
│   └── NO / multiple areas → stay at tier-1 (MAP) for now
│
├── Does the prompt need specific facts, quotes, benchmarks, or cross-claims?
│   ├── YES → load relevant full entries (tier-3)
│   │         Prefer qmd search over grep for conceptual lookup
│   │         Prefer direct read when slug is known
│   │
│   └── NO → answer from tier-1/tier-2 only
│
└── After reading: if new claims/concepts surface, check `concept-gaps-things-mentioned-not-yet-covered.md`
```

## Structural conventions inside an entry

Within a single entry, the same 3-tier idea applies:

| Within-entry tier | Section | Read first? |
|---|---|---|
| abstract | `## TL;DR` (~100 tokens) | Always |
| overview | Body sections between TL;DR and Related | Only if TL;DR doesn't answer the question |
| drill-down | `## Related` + `
