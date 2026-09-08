---
title: "Tiered Context Loading — How Agents Consult the Wiki"
date: 2026-04-24
source_url: internal://session/2026-04-24-tiered-context-loading
ingested_by: claude-code
tier: self
confidence: high
framework-contract: true
framework-version: 2
last_reviewed: 2026-09-08
review_after: 2026-12-08
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
│   └── NO → answer from tier-1/tier-2 only — AND say so in the answer
│            ("from the map/INDEX; I did not open the entries")
│
└── After reading: if new claims/concepts surface, check `concept-gaps-things-mentioned-not-yet-covered.md`
```

## Structural conventions inside an entry

Within a single entry, the same 3-tier idea applies:

| Within-entry tier | Section | Read first? |
|---|---|---|
| abstract | `## TL;DR` (~100 tokens) | Always |
| overview | Body sections between TL;DR and Related | Only if TL;DR doesn't answer the question |
| drill-down | `## Related` + backlinked/cross-referenced entries | Only when the overview doesn't answer and a specific linked entry needs pulling in — follow one link at a time, not the whole section |

This mirrors the top-level pattern recursively: an entry's `## Related` section is itself a tier-2-style index into further tier-3 reads, so an agent drilling down from one entry to another is doing the same abstract→overview→full-content walk one level deeper.

**Completion note (2026-08-05; carried into the framework template 2026-09-08)**: this document was truncated mid-table from the moment it was first authored (2026-04-24, `workflows-core@0900bd5c` — its own commit message reads "L3 is ~90% complete"). It was never finished, not corrupted later. The drill-down row and the closing sections were written on 2026-08-05 in the agentic-design copy, following the structure and voice of the two finished rows above and the sibling framework docs' closing pattern, and the framework's gold copy shipped the truncated version for another month until the 2026-09-08 reconciliation pass.

## Say where you stopped (added 2026-08-13)

The tiers above decide *what to load*. They do not, on their own, say anything about the answer that comes out — and an answer built from `_MAP.md` and a folder `_INDEX.md` is a different epistemic object from one built by reading the entries. **When an agent answers without drilling to tier 3, it says so.** One clause is enough: "from the map and the `active/` index; I did not open the entries." The same applies when a drill-down was attempted and came back thin — name the gap rather than smoothing over it.

The rule is borrowed from a context compiler for coding agents, which reaches the same three-tier shape from a different direction — full source / signatures-and-docstrings skeleton / *excluded entirely*, the third tier being what a flat repo map lacks — and states the discipline that makes such a scheme safe:

> "an incomplete map with explicit warnings is far more useful than a complete map that is secretly wrong." — Alexander, TDS *(agentic-design :: wiki/research/, the context-compiler entry)*

Its worked case is a resolver that cannot see `getattr`-dispatched handlers: rather than guessing, it emits `MISSED (as expected)` and names where static analysis stopped, so an agent tracing a bug "does not get a correct handler by luck or a wrong handler delivered with false confidence." Tiered loading has exactly the same failure surface — a tier-2 read is a lossy projection of the entries, and an answer built from it is indistinguishable, at the point of use, from one built by reading them. This is the loading-side instance of the disclosure discipline already in the canon: `not_found` as a first-class output and the abstention gate (memory-architecture best practices, Principle 9 *(agentic-design :: wiki/project/best-practices/memory-architecture-best-practices.md)*), and the synthesis-vs-direct-claim distinction ([wiki-authoring principle 8](./wiki-authoring-best-practices.md)).

The external source is worth reading for its architecture and not for its numbers: its prompt-reduction figures are measured only against a naive full-repo dump, and it runs no task-quality evaluation at all — see the entry's own caveat.

## Related

- [Wiki Frontmatter Best Practices](./wiki-frontmatter-best-practices.md) — sibling framework contract
- [Cycle Step Return Format](./cycle-step-return-format.md) — sibling framework contract
- [Wiki Authoring Best Practices](./wiki-authoring-best-practices.md) — principle 8 (synthesis vs direct claims), which "say where you stopped" extends to the loading side
