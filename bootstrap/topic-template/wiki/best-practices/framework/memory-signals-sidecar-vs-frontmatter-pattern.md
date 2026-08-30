---
title: Memory Signals — Sidecar vs Frontmatter Pattern
date: 2026-05-07
source_url: internal://synthesis/2026-05-07-memory-signals-sidecar-pattern
raw_path: (none — self-authored)
ingested_by: claude-code
tier: self
confidence: high
framework-contract: true
framework-version: 2
last_reviewed: 2026-05-25
review_after: 2026-08-25
tags: [memory-signals, recall-count, last-accessed, ebbinghaus, sidecar-pattern, frontmatter, decay, qmd, principle-3, self-authored, icarus-schema, truth-status, verify, rollback]
---

# Memory Signals — Sidecar vs Frontmatter Pattern

Our canonical position on **where** access-frequency signals (recall_count, last_accessed) should live in a markdown-first knowledge wiki, and **who** writes them. Synthesised 2026-05-07 from a research brief covering 9 production memory frameworks plus 2 reference implementations.

This entry operationalises memory-architecture-best-practices.md Principle 3 *(agentic-design :: wiki/project/best-practices/memory-architecture-best-practices.md)* ("Memory signals — make forgetting measurable"). The principle says every memory entry should have at least `recall_count`, `last_accessed`, and `confidence`. We have `confidence` (frontmatter, author-driven). This doc covers the other two.

## TL;DR

- **Sidecar JSON, never frontmatter.** Per-entry signals live at `<topic>/_signals/<entry-slug>.json`, owned by the search layer (`qmd`). Frontmatter stays author-driven.
- **The retrieval layer is the writer.** Every production reference impl that actually ships recall_count tracks it inside the search code path — not as a separate hook, not as a periodic batch. `recall_memory()` does the cosine search, applies the score, then writes back the increment.
- **Strength's role in ranking is contested — both-sides-stay applies.** YourMemory ranks similarity-pure and uses strength only for a 24h prune job (their docs: multiplying by strength "would penalise old-but-valid"). Oblivion DOES let strength affect ranking — *"neglected clusters become less prominent in retrieval ranking"* (§2.2) — at L1 cluster granularity, plus a separate uncertainty signal `u_t(c)` gates the read-path. Two production wins, two different mechanisms. The granularity (per-entry vs per-cluster) may be what makes both work. Naked recall_count without an Ebbinghaus-shape decay doesn't move benchmarks regardless — compute strength either way.

## Why frontmatter is the wrong place

Markdown-first knowledge wikis hit one specific blocker: **every read would dirty the file**. With ~500 entries and dozens of retrievals per session, frontmatter-mutation-on-read produces a flood of micro-commits with no semantic value, and breaks the "git history reflects intent" rule.

Three concrete signals that this is the wrong design:

1. **Karpathy's original `llm-wiki.md` gist** defines frontmatter as `title, confidence, last_ingested, sources, content_hash, stale` — pointedly **no access counters**. He hit the git-noise problem early and avoided it.
2. **danvega/karpathy-wiki** (Spring AI implementation) writes a `wiki/log.md` append-only audit on every `ingest`, `compile`, `query`, `lint` operation. The *operations* are journaled, not the *entries*. Same shape: external log, untouched documents.
3. **Anthropic skills + AGENTS.md** track none of this — those are author-curated config, not memory entries. The convention extends: human-authored markdown stays human-authored.

The git-noise problem is not theoretical. Every production markdown-first system in the survey either (a) doesn't track signals at all, (b) writes to an append-only log, or (c) batch-applies updates from a log on a schedule. None mutate frontmatter on every read.

## Why a database column isn't an option for us

Production memory frameworks that ship retrieval signals (YourMemory, Oblivion, agentmemory, smixs/agent-memory-skill) all put `recall_count INTEGER` and `last_accessed_at TIMESTAMP` in the same row as the embedding — DuckDB, SQLite, or pgvector.

That's the right call **if** your knowledge layer is already a database. Ours isn't. Our wiki is plain markdown by design (the [compile-don't-retrieve](./wiki-authoring-best-practices.md) principle), and our search layer (`qmd`) builds an index *over* the markdown rather than replacing it. Adding a primary database for signals would invert the architecture.

The markdown-equivalent of a DB column is a sidecar file. The closest analogue:

```
<topic>/wiki/active/foo.md            ← entry (author-owned, git-tracked)
<topic>/_signals/foo.json             ← signals (qmd-owned, git-tracked but low-noise)
<topic>/raw/2026-05-07-foo.md         ← raw source (immutable WAL)
```

One sidecar JSON per entry means file-level diffs stay small and parallel-merge-safe. Whether it's git-tracked or git-ignored is a follow-up call (see "open question" below).

## What the signals contain

Two signal classes share one sidecar file. The schema is **additive**: recency-class fields (existing) and truth-status fields (added per icarus §2) coexist; nothing should be split across files. The two classes are owned by different writers and updated on different events, but they belong together because retrieval ranking needs both at the same instant.

```jsonc
{
  "slug": "foo",

  // ── Recency-class signals (qmd-owned; updated on every retrieval) ─────────
  "recall_count": 12,
  "first_accessed": "2026-04-12T09:14:31",
  "last_accessed": "2026-05-07T16:22:08",
  "queries": [
    {"q": "memory signals decay", "ts": "2026-05-07T16:22:08", "rank": 1},
    {"q": "ebbinghaus curve wiki", "ts": "2026-05-04T11:09:55", "rank": 3}
  ],
  "strength": 0.847,
  "strength_computed_at": "2026-05-07T03:00:00",

  // ── Truth-status signals (verify-owned; mutated only on verify / rollback / contradiction events) ──
  "verified": "verified",
  "verified_at": "2026-05-08T10:14:00",
  "verified_by": "human",
  "contradicted_by": [
    "../active/newer-revising-entry-2026.md"
  ],
  "rolled_back_at": null
}
```

**Recency-class fields** (existing — `qmd`-owned):
- `recall_count`, `last_accessed` — incremented by `qmd` on every retrieval where this entry is in the returned set.
- `first_accessed` — written once on first hit. Lets us age-bucket the wiki ("never-retrieved at 90 days = archive candidate").
- `queries` — bounded ring buffer (last 50). Useful for "what queries surface this entry?" introspection. Optional; if storage cost is a concern, drop.
- `strength` — composite score derived from `recall_count`, `last_accessed`, age, and a per-content-type decay rate. Computed by a separate batch job, not on every retrieval.
- `strength_computed_at` — when the batch last ran. If older than 7 days, lint flags the sidecar as stale.

**Truth-status fields** (icarus §2 — written by `/wiki-verify`, `/wiki-rollback`, and contradiction-marking events; mirrored from frontmatter on initial write):
- `verified` — enum mirror of the frontmatter `verified:` field (`unverified` | `verified` | `contradicted` | `rolled_back`). Lives in the sidecar so retrieval / verification can update it without touching the entry file itself (no git-noise per the same rule that motivates the sidecar pattern in the first place).
- `verified_at` — ISO timestamp when `/wiki-verify` ran. Null until verified.
- `verified_by` — `human` | `agent` | `tool`. Who certified the entry. (Tool means a sandboxed test or static analyzer; agent means an LLM judge; human means an editorial signoff. Aardvark-style PoC validation = `tool`.)
- `contradicted_by` — **array** (not single value). A single entry can be contradicted by multiple later entries (one for each specific claim that gets revised). Each item is a relative path to the contradicting entry. Empty array = no contradictions.
- `rolled_back_at` — ISO timestamp when the rollback walk marked this entry `rolled_back`. Null until rolled back. Set only via `/wiki-rollback`, never hand-set.

### Why these go in the sidecar, not frontmatter

The same "every read would dirty the file" argument that motivated the recency sidecar applies to truth-status:
- A `/wiki-verify` operation should not require a frontmatter edit if the entry's content didn't change — the human just looked at evidence and signed off. Sidecar-only update keeps git history clean.
- Multi-contradiction tracking (`contradicted_by` array) doesn't fit YAML frontmatter naturally; sidecar JSON handles arrays cleanly.
- A rollback walk touches many sidecars in one operation. If those were frontmatter edits, each rollback would be a many-file commit; sidecar-only writes batch cleanly.

### Frontmatter mirror semantics

Frontmatter still carries `verified:` for **discoverability** (so qmd / lint can read it without opening the sidecar) but the sidecar is the **authoritative** writer for the four lifecycle events (verify, contradict, rollback, mirror-on-create). Reconciliation rule: **sidecar wins** on conflict; frontmatter is the cached snapshot. Lint flags drift (frontmatter `verified:` ≠ sidecar `verified:`).

### Mirror-on-create

When an entry is first written, the sidecar's `verified` is set from the frontmatter (typically `unverified`), `verified_at` and `rolled_back_at` are `null`, `verified_by` is unset, and `contradicted_by` is an empty array. Subsequent verify / rollback / contradiction-marking events mutate the sidecar; if mirror-back-to-frontmatter is enabled (an open question), the frontmatter `verified:` field is updated on a debounced batch (e.g., per `/wiki-cycle`).

## The decay formula — and the ranking-vs-pruning split

The strength formula itself is well-established (Ebbinghaus + recall multiplier):

```
strength = importance × e^(−λ_eff × active_days) × (1 + recall_count × k)

where  λ_eff = base_λ × (1 − importance × 0.8)   ← important memories decay slower
       active_days = elapsed days where user was active (vacations don't count)
       k = 0.2 (YourMemory)
       base_λ varies by content type — see below
```

YourMemory's `base_λ` values: `fact=0.16, strategy=0.10, assumption=0.20, failure=0.35`. Architecture decisions decay slow; ephemeral failure logs decay fast. (The same per-content-type-decay logic is what the confidence-scoring *(agentic-design :: wiki/research/active/confidence-scoring-ebbinghaus-forgetting-curve-for-wiki-lifecycle.md)* entry calls Level 4.)

**The contested question — strength's role in ranking — has two opposing production answers. Both ship. Both win. Both-sides-stay applies.** (Updated 2026-05-11 after re-reading the Oblivion paper raw; earlier framing on 2026-05-07 incorrectly described Oblivion as also excluding strength from ranking.)

| System | Strength's effect on ranking | Strength's effect on storage | Granularity |
|---|---|---|---|
| **YourMemory** *(agentic-design :: wiki/research/active/yourmemory-ebbinghaus-decay-recall-count-implementation-2026.md)* | **NONE** — `0.4 × bm25_norm + 0.6 × cosine` (similarity-pure). Their BENCHMARKS.md: *"multiplying cosine by strength would penalise old-but-valid memories below newer irrelevant ones."* | 24h prune job at strength threshold 0.05 | Per-entry |
| **Oblivion** *(agentic-design :: wiki/research/long-term/oblivion-decay-driven-activation-arxiv-2604-00131.md)* | **YES** — §2.2: *"neglected ones see R_t(c) decline, making their memories less prominent in retrieval ranking."* Plus uncertainty `u_t(c)` separately gates the read-path (whether to retrieve at all). | Eviction during curation, *"yet never deleted, preserving reactivatability when future interactions reinforce them"* | Per L1 cluster |

The benchmark wins:
- **YourMemory** (similarity-pure ranking, decay-only-prunes): 59% Recall@5 vs Zep Cloud 28% (+31pp absolute, 2.1× relative) on LoCoMo-10.
- **Oblivion** (retention affects cluster prominence in ranking + drives eviction): +3.90% LongMemEval, +36.97% GoodAILTM, with −72% tokens / −68% cost vs FullCTX on GoodAILTM 32K (GPT-4.1-mini). Retention function: `R_t(c) = exp(−n_t(c) / S_t(c))` where `S_t(c) = (U_t(c) + F_t(c) + ε) · T` (T=10 sweet spot).

**Why both can be right.** The granularity difference is probably what saves both. YourMemory operates per-entry, where "old-but-valid" is a sharp risk — penalising one entry's score directly suppresses it. Oblivion operates per L1 cluster (aggregate of many entries), where retention-affects-prominence dilutes individual-entry risk: a cluster doesn't disappear from ranking, it just drops in prominence proportional to its aggregate utility/recency signal. Different scales, different safe defaults.

**Implication for our design — two patterns are both defensible.** The decay batch writes `strength` to the sidecar regardless. The design call is whether qmd uses it for ranking:
- **Pattern A (YourMemory-like)**: qmd ignores strength in ranking; uses it only for prune-candidate / archive-flagging. Safer for per-entry granularity.
- **Pattern B (Oblivion-like)**: qmd multiplies cosine by a strength term in ranking, *plus* uses it for eviction. Would require clustering wiki entries first (out of scope for v1).
- **Hybrid (recommended for v1)**: ship Pattern A first (cheap, low-risk). Once we have a clustering layer (Oblivion-style L1 buckets over wiki entries), revisit Pattern B as an upgrade. The both-sides-stay framing means we don't pick one as canonical — we pick which to build first.

**Naked recall_count without an Ebbinghaus-shape decay doesn't move benchmarks regardless** — whatever you do with strength, compute it.

## Architecture: who writes, who reads

```
                                Author edits entry
                                       ↓
                              wiki/<folder>/foo.md            ← human-owned
                                       ↑              ↗
                            (no automatic mutation)  /
                                                    /
                                                   / strength batch reads:
                                                  /  - frontmatter (confidence, age)
                                                 /   - signals (recall_count, last_accessed)
                                                /
                                               /
qmd retrieval                              ↓
   ↓                                  /wiki-signals-decay
returns ranked entries                (nightly batch)
   ↓                                       ↓
qmd writes:                          writes strength
   - increment recall_count          back to signals.json
   - update last_accessed                  ↓
   - append query[]                  lint reads signals
   ↓                                       ↓
_signals/foo.json                    flag never-retrieved
   ← (qmd-owned, git-tracked)             entries (recall_count == 0
                                          AND age > 90d) for archive
                                          review
```

Three actors, three responsibilities:

| Actor | Writes | Reads |
|---|---|---|
| Human author / `/wiki-update` | frontmatter, body; **mirror-on-create initializes sidecar truth-status block** | (everything) |
| `qmd` retrieval layer | `_signals/<slug>.json` (recall_count++, last_accessed, queries[]) | both |
| `/wiki-signals-decay` batch | `strength`, `strength_computed_at` in signals | frontmatter + signals |
| **`/wiki-verify`** | sidecar truth-status block (`verified`, `verified_at`, `verified_by`); validates no-self-certification invariant | frontmatter + sidecar |
| **`/wiki-rollback`** | sidecar `verified: rolled_back` + `rolled_back_at` on intermediate entries; writes a NEW `type: rollback` entry pointing at the verified ancestor | frontmatter + sidecar; walks `revises:` chain |
| **Contradiction marker** (manual or agent-driven) | sidecar `verified: contradicted` + appends to `contradicted_by[]` array | frontmatter + sidecar |
| `/wiki-lint` | nothing — read-only | both; reports drift between frontmatter `verified:` and sidecar `verified` |

This separation is the load-bearing decision. It mirrors the provider-vs-manager split *(agentic-design :: wiki/project/best-practices/memory-architecture-best-practices.md)* — the entry is the provider (the durable substrate); qmd + the decay batch are the managers (the code that moves information).

## Downstream uses (in order of payoff)

1. **Decay-weighted ranking.** `qmd` returns top-K by `score`, not raw cosine similarity. This is the benchmark-winning use. **Highest priority.**
2. **Auto-pruning / forgetting-candidate selection.** `/wiki-signals-decay` flags entries below strength 0.05 as archive candidates. Per memory-architecture-best-practices.md Principle 2 *(agentic-design :: wiki/project/best-practices/memory-architecture-best-practices.md)*, candidates move to `wiki/archive/`, not deletion (still searchable, de-emphasised in ranking).
3. **Lint flags for never-retrieved entries.** `/wiki-lint` flags `recall_count == 0 AND age > 90d` as "is this paying its keep?" Cheap, mechanical.
4. **Heatmaps for human review.** Per MemGuard *(agentic-design :: wiki/research/tooling/memguard-memory-validation-sidecar-mem0-letta-zep-2026.md)*: frequently-retrieved-but-stale = highest truth-decay risk. The signals + `last_reviewed` cross-product surfaces these.

## Open questions (defer to design phase)

1. **Git-tracked or git-ignored?** Tracking gives audit + cross-machine sync, but adds noise. Ignoring is cleaner but loses portability. Lean: track, but in a separate dir with `.gitattributes` to suppress noise in diffs.
2. **Queries[] retention.** Last 50 vs last 10 vs none. Lean: last 10 by default, configurable.
3. **What gets a sidecar?** Every entry, or only retrieved entries (lazy creation)? Lean: lazy creation — sidecar appears on first retrieval, never proactively.
4. **Migration vs greenfield.** No existing signals to migrate; start clean.
5. **Strength batch cadence.** Nightly is sufficient given our query volume; could be weekly. Whatever the lint flagging allows.
6. **Mirror-back-to-frontmatter on/off?** When the sidecar's `verified` flips (verify/rollback/contradict), should we ALSO update the frontmatter `verified:` for discoverability? Lean: yes-but-debounced via `/wiki-cycle` so the per-event sidecar write stays clean, and the frontmatter mirror is a batched cycle-time pass. Tradeoff: small commit on cycle vs no commit at all.
7. **Lazy-create the truth-status block?** Recency block is lazy (first retrieval creates). Truth-status block could be either eager (created at promote time) or lazy (created on first verify/rollback event). Lean: eager — created at promote-time with `verified: unverified`, `verified_at: null`, `contradicted_by: []`, so the schema is uniform and lint can detect missing blocks reliably.

## What this isn't (boundary conditions)

- **Not truth decay.** "Is this fact still correct?" is the `last_reviewed` / `review_after` axis (human-driven). MemGuard separates this clearly. Both axes matter independently.
- **Not author intent.** `confidence: high|medium|low` stays in frontmatter and stays author-driven. Signals don't override author judgement; they augment it.
- **Not search-result caching.** Sidecar is for persistent signals; query result caches live elsewhere.
- **Not a database replacement.** If we ever migrate the wiki to a DB, signals collapse into a column on the entry row and the sidecar pattern is retired.

## Where this differs from production frameworks

Most named frameworks (Mem0, Letta, Graphiti, Honcho, LangMem, MemoRizz) do not actually ship per-entry retrieval signals — `created_at` / `updated_at` only. The exceptions (YourMemory, Oblivion, agentmemory, smixs) all use a database column adjacent to the embedding. Our sidecar pattern is the markdown-first equivalent of that column.

This puts us **ahead of canonical practitioner shipping reality**, not behind it. The doctrine (Richmond Alake's MemoRizz writeup) calls for recall_count + last_accessed but the library doesn't implement it. We're filling a gap the doctrine names but the production tools don't.

## Implementation roadmap

Following the confidence-scoring spectrum *(agentic-design :: wiki/research/active/confidence-scoring-ebbinghaus-forgetting-curve-for-wiki-lifecycle.md)* (Levels 1-4):

| Level | What | Status |
|---|---|---|
| 1 | Manual `confidence: high\|medium\|low` in frontmatter | ✅ Built |
| 2 | This doc — sidecar schema + qmd-as-writer integration | ⏳ Designed (this doc), not built |
| 3 | `/wiki-signals-decay` batch — strength composite computation | ⏳ Designed (this doc), not built |
| 4 | Per-content-type decay rates, query-introspection dashboards | ⏳ Aspirational |

Level 2 is the load-bearing build: it wires qmd to write signals on retrieval. Without it, Levels 3-4 have no input data. Estimate: ~1 day of qmd work + sidecar schema validation + a small lint addition. The benchmark wins ride on getting Level 2 right.

## Source entries

Production reference impls:
- YourMemory — Ebbinghaus Decay + recall_count Reference Implementation (+16pp Recall vs Mem0) *(agentic-design :: wiki/research/active/yourmemory-ebbinghaus-decay-recall-count-implementation-2026.md)* — the production-shipping reference; this entry's most direct prior art
- Oblivion — Decay-Driven Activation (+3.9pp LongMemEval, +36.97pp GoodAILTM) *(agentic-design :: wiki/research/long-term/oblivion-decay-driven-activation-arxiv-2604-00131.md)* — academic/empirical backing

Wiki framework + adjacent:
- Memory Architecture Best Practices *(agentic-design :: wiki/project/best-practices/memory-architecture-best-practices.md)* — Principle 3 (this doc operationalises it), Principle 2 (no-deletion / archive-not-delete)
- Confidence Scoring + Ebbinghaus Forgetting Curve for Wiki Lifecycle *(agentic-design :: wiki/research/active/confidence-scoring-ebbinghaus-forgetting-curve-for-wiki-lifecycle.md)* — the level-spectrum framing
- MemGuard — Open-Source Memory Validation Sidecar *(agentic-design :: wiki/research/tooling/memguard-memory-validation-sidecar-mem0-letta-zep-2026.md)* — the truth-decay axis (complementary, not overlap)
- [Wiki Authoring Best Practices](./wiki-authoring-best-practices.md) — Principle 9 (build-artifact dependency tracking) — sidecar pattern extends this

Production-systems-that-deliberately-don't:
- Mem0 *(agentic-design :: wiki/research/active/mem0ai-mem0-intelligent-memory-layer-for-ai-agents.md)* — ADD-only, no signals
- Letta / MemGPT *(agentic-design :: wiki/research/active/letta-ai-letta-formerly-memgpt-stateful-agents-with-os-tiered-memory.md)* — block versioning, no per-block read counter
- Zep / Graphiti *(agentic-design :: wiki/research/active/getzep-graphiti-temporal-context-graphs-for-ai-agents.md)* — bi-temporal validity windows for truth decay, not access decay

## Related

- [Wiki Frontmatter Best Practices](./wiki-frontmatter-best-practices.md) — frontmatter contract that this doc says to *not* extend with signals
- [Cycle Step Return Format](./cycle-step-return-format.md) — the sidecar JSON convention this doc inherits

---

**Source**: research brief at `memory-bank/short-term/memory-signals-research-brief-2026-05-07.md` (synthesised from 9 production framework analyses + YourMemory + Oblivion).

<!-- BACKLINKS-AUTO START -->

## Backlinks (auto-maintained)

_Other entries linking to this one. Managed by `wiki-reciprocate-backlinks.py`; do not hand-edit within the BACKLINKS-AUTO markers._

- auto-memory — Zero-Dependency Recall Layer for GitHub Copilot CLI *(agentic-design :: wiki/research/tooling/auto-memory-zero-dependency-recall-layer-for-github-copilot-cli.md)*
- Codex Chronicle — Screen-Aware Ambient Memory for Codex Mac *(agentic-design :: wiki/research/tooling/codex-chronicle-screen-aware-ambient-memory.md)*
- MemAlign — Building Better LLM Judges From Human Feedback With Scalable Memory (Databricks 2026-02-03) *(agentic-design :: wiki/research/tooling/databricks-memalign-llm-judges-memory-2026.md)*
- Honcho — Plastic Labs' Dialectic User Modeling for Stateful Agents *(agentic-design :: wiki/research/tooling/honcho-plastic-labs-dialectic-user-modeling.md)*
- Icarus Integration Plan — Concrete Changes to Adopt Icarus's Schema + Patterns *(agentic-design :: wiki/project/best-practices/framework/icarus-integration-plan.md)*
- Mem0 Memory Plugin for OpenClaw — Persistent Memory in 30 Seconds (Deshraj Yadav, Mem0, 2026-02-06) *(agentic-design :: wiki/research/tooling/mem0-openclaw-plugin-yadav-2026.md)*
- MemGuard — Open-Source Memory Validation Sidecar for Mem0/Letta/Zep (5-Strategy Trust Scoring) *(agentic-design :: wiki/research/tooling/memguard-memory-validation-sidecar-mem0-letta-zep-2026.md)*
- MemoRizz — Richmond Alake's Memory-Layer Library for AI Agents *(agentic-design :: wiki/research/tooling/memorizz-richmond-alake-memory-layer-library.md)*
- Agent Memory Architecture — Best Practices *(agentic-design :: wiki/project/best-practices/memory-architecture-best-practices.md)*
- OpenClaw 2026.4.10 — Active Memory Plugin (Memory Sub-Agent for Ongoing Chats) *(agentic-design :: wiki/research/tooling/openclaw-2026-4-10-active-memory-plugin.md)*
- SMFS (Supermemory) — Agent Memory Exposed as a Filesystem with Semantic grep *(agentic-design :: wiki/research/tooling/smfs-supermemory-agent-memory-exposed-as-a-filesystem-with-semantic-grep.md)*
- Vision — Iterative Self-Improving Research Cycle *(agentic-design :: wiki/project/architecture/vision-nightly-self-improving-research-cycle.md)*
- [Wiki Frontmatter — Best Practices & Canonical Field Reference](../../best-practices/framework/wiki-frontmatter-best-practices.md)
- YourMemory — Ebbinghaus Decay + recall_count Reference Implementation (+16pp Recall vs Mem0 on LoCoMo) *(agentic-design :: wiki/research/active/yourmemory-ebbinghaus-decay-recall-count-implementation-2026.md)*

<!-- BACKLINKS-AUTO END -->
