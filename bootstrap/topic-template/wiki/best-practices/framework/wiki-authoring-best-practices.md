---
title: LLM Wiki Authoring — Best Practices
date: 2026-04-18
source_url: internal://synthesis/2026-04-18-wiki-authoring-best-practices
raw_path: (none — self-authored)
ingested_by: claude-code
tier: self
confidence: high
framework-contract: true
framework-version: 3
last_reviewed: 2026-09-08
review_after: 2026-12-08
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

## The operational principles

(Heading deliberately uncounted — see principle 9's "never write a count you could point at": a heading that counts its own list makes every addition an edit in two places.)

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

**Duplicate carve-out (added 2026-08-05 in agentic-design; narrow, exact-identity only — user decision).** Both-sides-stay does not apply to true duplicates: the exact same URL ingested twice, or the exact same article republished verbatim (or near-verbatim) at a different URL/site (mirror, syndication, cross-post). Those get **moved out of the live wiki into `_inbox/archived-duplicates/`** (not destroyed — a safer default while this carve-out is new), with inbound links redirected to the surviving entry — "we don't need to ingest the same feed 25 times." This is an **identity** test, not a similarity test: **any** actual difference in content — a correction, an update, new details, or the same story reported with different framing — does NOT qualify. Differences get handled by editing the existing entry or adding a `revises:` pointer on the newer one, never by removal from the live wiki. The bar is deliberately narrow so a future agent can't extend it to "overlapping" or "merely similar" entries. Enforcement: `wiki-list-add.py` and the Drive fetcher dedup on canonical URL at queue time (mechanical); the verbatim-republish case is prose-only — a content-hash check is the missing control.

### 5. Claim-level extraction with 4-way classification

**Not described in any external source at our granularity.** workflows-core innovation, validated by `/wiki-claims` skill.

Every factual assertion in every entry is classified as one of:
- **direct-quote** — verbatim from source, in blockquotes
- **sourced** — paraphrased but cleanly attributed
- **synthesis** — our conclusion drawn from multiple sources
- **inference** — our own assertion, unsourced (highest drift risk)

Claims are indexed in `_inbox/claims-index-*.json` for cross-entry comparison. This makes contradiction detection precise (sentence-level, not page-level) and makes drift visible (every `inference` claim is a candidate for future verification).

**Read before you reject (added 2026-08-01; observed doctrine since 2026-04-29).** No title-pattern rejections, no URL-pattern guesses, no domain-quality heuristic as a standalone basis for skipping. The user has already curated at queue-add time; the ingest agent's job is to render the item, not re-litigate whether it belongs. **Every queued item is fully fetched and read before any tier / cluster / skip decision, and every rejection is content-grounded: a quoted passage from the fetched source plus the slug of the existing entry it overlaps.** The rule was added after a cycle agent rejected 22 of 26 user-curated URLs on title patterns alone — the drop rate was the tell. The rule also lives in the `wiki-update` skill and the `wiki-ingester` agent (their operational home); this section is the doctrinal record. Enforcement: prose, plus the ingester's receipt row (a rejection without a quoted passage is a visible defect).

**Auto-captioned sources: check before you blockquote (added 2026-08-13).** The `direct-quote` class asserts *verbatim from source*. When the source text came from automatic speech recognition — YouTube auto-captions, a `yt-dlp`-fetched `.vtt`, any podcast transcript — verbatim-from-the-transcript and verbatim-from-the-speaker are not the same claim, and ASR fails **systematically** on exactly the vocabulary these wikis are made of: "Claude Code" arrives as "Cloud Code" or "Quad Code", `CLAUDE.md` as "quadmd", "CloudMD", "clawed MD". Preserving those inside `>` marks puts a fabricated quotation behind the wiki's strongest truth signal — principle 3's anti-poisoning guarantee defeated from the inside.

**The rule**: before any ASR-derived passage is placed inside a blockquote, scan the transcript for systematic mishearings of the entry's own key terms and correct each to the intended word, disambiguated by context. Disclose the correction **once**, in a dated transcription note near the top of the entry, rather than annotating every instance. If a passage cannot be disambiguated with confidence, it is `sourced`, not `direct-quote`: paraphrase it and drop the blockquote. (Worked example: the Boris Cherny / Y Combinator entry in agentic-design `research/tooling/`. Added after cycle 2026-08-04-01 found roughly twenty uncorrected ASR corruptions inside verbatim blocks across two entries.) Enforcement: prose; the `wiki-update` YouTube flow states it as a required step.

### 6. Two human checkpoints in any autonomous loop

**Stricter than any external pattern in the batch.** The spectrum from the sources:
- Asel: fully autonomous 700-change AutoResearch runs (no checkpoints).
- rohitg00: event-driven automation, human stays in the loop for curation.
- **workflows-core**: two human checkpoints (URL approval + entry approval) as non-negotiable.

Rationale: **silent poisoning risk** (Mem0 warning, Asel L2) + source-quality blindness justify the conservatism. The wiki is load-bearing for downstream decisions; a bad ingest that survives review can pollute months of work.

Don't soften this. The right move when automation wants to push further is to make the checkpoints *faster*, not remove them.

### 7. Source quality tiers in frontmatter — tier 4 never auto-ingests

The 4-tier rubric is defined in ONE place — the tier table in [wiki-frontmatter-best-practices.md](./wiki-frontmatter-best-practices.md#tier-rubric) — and is not restated here (restatement rule, 2026-08-01: a paraphrase cannot be lint-checked and ages independently; until 2026-09-08 this section carried its own four-bullet version that had drifted from the table). Orientation only: tier 1 is primary / peer-reviewed / source code, tier 4 is community and unsourced material, and **tier 4 never auto-ingests**.

rohitg00 has a quality threshold; Huber has a gold-set. **No external source implements the full tier rubric or tier-4-hard-block.** Ours is stricter.

Enforce in `/wiki-update` eval gate and `/wiki-list process`. When a source fails tier evaluation, drop to `_inbox/proposed/` for human review, never direct to `wiki/`.

### 8. Distinguish synthesis from direct claims in prose

- Blockquotes for direct quotes (always) — and for ASR-derived text, only after principle 5's transcription check
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

**Never write a count you could point at (added 2026-08-13).** A number derived from the corpus itself — entry counts, folder counts, "the `wiki-*` family is N skills" — is a dependency like any other, but one with no `review_after`, no `raw_path`, and no lint rule behind it. It rots the moment the next cycle runs, and nothing announces the rot. **Point at the live artifact instead of freezing the number**: `_MAP.md` for entry and folder counts, a folder's `_INDEX.md` for its contents, the install manifest (`_install_tooling.py`) for how many skills and scripts ship, a named verify-command for anything a script can recount. Where a frozen number is genuinely load-bearing — a snapshot you are *arguing from* rather than merely reporting — keep it, but stamp it as a dated snapshot in the same sentence, so a reader can tell a measurement from a fact. Cycle 2026-08-04-01 in agentic-design found seven such counts across four project docs, every one stale by roughly an order of magnitude and every one invisible to mechanical lint. The rule reaches section headings that count their own contents ("The ten operational principles") — a frozen count that makes growing the list an edit in two places. Enforcement: prose; `_entry_checks.py` warns on numeric claims in prose outside a blockquote, which catches the external-figure case below but not a bare integer.

**Volatile external figures carry an as-of date, or they don't ship (added 2026-08-13).** Star counts, download counts, version numbers, tool/endpoint counts and repo-size figures are true only at the moment of fetch, and the corpus proves they drift: the same cycle found one project's star count in four mutually inconsistent forms across four entries, the newest figure *below* the oldest, and three entries dated the same day citing three different star counts for one repository. **The rule**: any point-in-time external figure is written with the date it was true — "49k stars (as of 2026-07-08)" — or it is left out. Two supports already exist: the `temporal` value of `verified`, for an entry whose whole body is a snapshot that was correct as-of-a-past-date; and a `snapshot_date:` + `frozen: true` frontmatter pattern for a comparison deliberately kept frozen and superseded by a sibling rather than edited in place. **And never put a volatile number in a title or slug** — it cannot be corrected without breaking every inbound link. A number you didn't measure and can't re-derive needs a date; a number you *could* re-derive needs a pointer.

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

### 11. Every hard rule is a hybrid artifact — prose paired with a mechanical check

A rule that exists only as prose in a SKILL.md or a best-practices doc is enforced only by the drafting agent's goodwill, and an agent scoring its own draft against that prose is circular. The 2026-08-13 lint retrofit measured the result: *"everything the lint script checks is clean; everything it doesn't check has decayed."* So every **must** / **never** gets a paired deterministic check — a lint rule, a script guard, a refusal at write time, a hook, a tool omission — or an explicit note that it is prose-only and why.

- **The pattern**: the prose biases the agent; the check makes violations unfileable. Huk calls the pair a *hybrid artifact* — `boundaries.md` for the model, `semgrep-rule.yml` for CI ("Context as Code", O'Reilly Radar, 2026-06-03; in agentic-design under `research/best-practices/`).
- **In this framework**: `_entry_checks.py` is one module used by both `wiki-update.py` (refuse to file) and `wiki-lint-mechanical.py` (backlog view), so the gate and the lint cannot disagree. The agent's eval self-score covers only the judgment dimensions (extraction fidelity, synthesis value) and is advisory, never the gate.
- **When adding a rule**: state its enforcement mechanism next to it. `prose` is allowed, with a reason. A doc that says "the lint should catch this" describes a gap, not a control.
- **Corollary — governance artifacts are code**: skill and agent definitions carry `last_reviewed` / `review_after` / `reviewed_for_model` and are scanned by `/wiki-refresh`. A stale rule enforced strictly is context debt.
- **Corollary — a governance artifact must load before it can govern (2026-09-08)**: a `SKILL.md` whose YAML frontmatter does not parse is dropped whole by the loader — it appears under its H1 and never triggers by description. Four shipped skills were in that state for weeks with no prose rule able to catch it. The installer now refuses to install an artifact whose frontmatter fails `check_frontmatter_loadable()`, and the lint runs the same check over entries and the installed copies. The rule "quote any value containing `: ` or ` #`" is therefore a hybrid artifact; before that date it was prose only, and it failed.

## Implementation status — what we do now vs what the principles say

**Purpose**: one-stop view of principle-vs-reality, so gaps are visible at a glance and we know where to look when we want to improve. Update this section when state changes; don't let it drift.

Legend: ✅ implemented and enforced · ⚠️ partial / policy not fully automated · ❌ aspirational, not built

**Snapshot note (counts are point-in-time):** the absolute entry counts in this table — principle 9's "134/148 entries compliant", and the "22 entries retrofitted 2026-04-10" under principles 5 and 8 — are a snapshot **as of 2026-04-10** from the first wiki this framework ran. Any wiki has since grown past them (see its `_MAP.md` for the live count); the ✅/⚠️/❌ marks reflect current capability, only the frozen counts are historical.

| # | Principle | Status | Evidence / gap |
|---|---|---|---|
| 1 | Compile, don't retrieve | ✅ | Wiki is plain markdown (no RAG DB). Confirmed by folder layout at `<notebook-root>/wiki/`. |
| 2 | LLM writes, human reads | ✅ | User queues URLs via `/wiki-list add` (or drops them in Drive) → agent compiles via `/wiki-update`. |
| 3 | Raw sources immutable | ✅ | `raw/` folder preserved at wiki root. No rewrite pattern; re-fetches create new timestamped files. |
| 4 | Both-sides-stay (contradiction preservation) | ✅ | Policy baked in. `/wiki-claims` surfaces contradictions; both entries kept. |
| 5 | Claim-level 4-way classification | ✅ | `/wiki-claims` skill implemented. 22 entries retrofitted 2026-04-10. New ingests classify at author time. |
| 6 | Two human checkpoints | ✅ | URL approval gate (`/wiki-list add` / Drive fetch → `_inbox/pending/`, confirmed at `/wiki-cycle` Step 1.5) + entry approval gate (`_inbox/proposed/` → `/wiki-promote --review` → `wiki/`). Non-negotiable. |
| 7 | Source tier-4 hard block | ✅ | Eval gate in `/wiki-update` step 5 (added 2026-04-13). Failing-tier entries drop to `_inbox/proposed/` for human review. |
| 8 | Synthesis vs direct claims distinguished in prose | ⚠️ | Retrofit done 2026-04-10 for 22 entries. Convention baked into `wiki-update` SKILL.md, but enforcement across new ingests relies on author discipline — not mechanically checked by lint. |
| 9 | Dependency tracking (`last_reviewed` / `review_after` / `confidence`) | ⚠️ | Lifecycle fields are required by the spec and lint-checked (missing `last_reviewed` / `review_after` is a lint finding). `raw_path` is **in the frontmatter schema and enforced** by `wiki-lint-mechanical.py` (missing / phantom `raw_path` checks). Remaining gap: the frozen "134/148 compliant" figure above is a 2026-04 snapshot; the live compliance number is the lint's, per wiki. |
| 10 | Federation of specialists (`/wiki-*` skills) | ✅ | Every skill in the install manifest (`TRAVEL_SKILLS` in `_install_tooling.py` — point there, not at a count here) ships as a Claude Code skill at `~/.claude/skills/`, plus the `wiki-ingester` agent. `rollback` + `verify` implement the truth-status lifecycle the sibling specs depend on. |
| 11 | Hard rules are hybrid artifacts (prose + check) | ⚠️ | 2026-09-02: rubric's structural rules moved into `_entry_checks.py` (gate + lint); skill frontmatter carries lifecycle fields. 2026-09-08: frontmatter loadability is an install-time gate + lint check. Still prose-only: the claim-classification convention (principle 5), the duplicate carve-out's verbatim-republish case (principle 4), the frozen-count rule (principle 9), and most SKILL.md "don't" bullets — each needs an enforcement note or a check. |

### Explicit gaps (punch list — where improvement lives)

1. ~~**L5 self-improvement loop not built**~~ **— resolved 2026-08-01.** The L5 read/write loop **is** built: `/wiki-cycle` closes it, with Step 6.5 (best-practices synthesis) as the write path from `research/` into canon and `cycle-step-return-format.md` §Synthesis as its contract. Per this doc's own gloss (*"read/write loop over L1-L4"*) and Asel's definition, L5 denotes a **closed loop, not an unattended one** — and by principle 6 the loop is human-gated permanently and by choice. **The two real remaining gaps are narrower**: (a) no scheduler — the loop runs when a human starts it; (b) the parallel-dispatch step is execution-context-dependent (in-process teammates cannot use the documented background-agent recipe).
2. ~~**`raw_path` frontmatter field not enforced**~~ **✅ RESOLVED** — `raw_path` is in the frontmatter schema and enforced by `wiki-lint-mechanical.py` (missing / phantom `raw_path` checks); lint verifies raw-source integrity.
3. **Entries missing `last_reviewed` / `review_after`** (principle 9 compliance gap). The "14 entries" figure was a 2026-04-16 snapshot and is not a live number; the lint's "missing lifecycle fields" counter is. Track the per-wiki backlog in that wiki's task dashboard (`sessions/<persona>/task.md`), not here.
4. **Synthesis-vs-direct-claim prose distinction only partly verified** (principle 8 enforcement gap). Partially closed 2026-09-02: `_entry_checks.py` flags numeric claims in prose outside a blockquote (gate + lint). Assertion-level detection for non-numeric claims is still not built.
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

## The org-scale boundary — single-markdown context stores hit a ceiling

**Added 2026-06-09 (agentic-design); carried into the framework copy 2026-09-08.** This doc's whole stance — a git-tracked markdown wiki, searched with `qmd` — mirrors the memory-architecture doc's "one real contradiction" *(agentic-design :: wiki/project/best-practices/memory-architecture-best-practices.md)*: markdown-as-memory wins at single-user-to-small-team scope, and a database becomes necessary at enterprise multi-tenant scale. A 2026 vendor wave names the *other side* of that boundary explicitly.

Single-markdown / `AGENTS.md`-style context stores hit a ceiling at **org scale (on the order of a thousand repos)**: one shared file (or one git wiki) can't serve hundreds of teams, each with their own conventions, without becoming either too generic or too large to load. A vendor category — **"Context Lake" / shared org-level context store** — has emerged to name this layer (Port's Context Lake, LangSmith Context Hub, the open-source `ktx` context-layer warehouse, Unabyss's MCP-native context layer; all filed in agentic-design `research/`). `ktx` independently reinvents this framework's flag-contradictions-for-human mechanic — external validation of principle 4's both-sides-stay-with-human-review instinct.

**Where this framework sits**: single-user-to-small-team, git-wiki + qmd is sufficient; the org-scale shared-context-store layer is **not** something it builds or needs — boundary noted for when a project scales past it. Same scope logic as the file-based-ceiling contradiction: both sides are right in their scope.

## The lineage — Vannevar Bush's Memex (1945)

> *"Consider a future device for individual use, which is a sort of mechanized private file and library. [...] Any given book of his library can thus be called up and consulted with far greater facility than if it were taken from a shelf. [...] The first idea, however, to be drawn from the analogy concerns selection. Selection by association, rather than by indexing."* — Vannevar Bush, "As We May Think"

Bush couldn't solve **who does the maintenance**. The Memex requires someone to encode the associative trails, and humans don't have the patience. **LLMs solve the maintenance problem.** Karpathy's pattern is Memex at scale — the associative trails are the wiki's cross-references, and the LLM writes them on ingest.

Every workflows-core wiki entry is a Memex trail made durable.

## The 5-layer stack (Asel) — how we map

Asel's 5-layer self-improving AI stack maps onto workflows-core:
- **L1 Knowledge** (static markdown + search) → `wiki/research/long-term/`
- **L2 Memory** (active context) → `wiki/sessions/` (journals + working-memory dashboards) + `wiki/research/active/`
- **L3 Context** (session habits, CLAUDE.md) → `CLAUDE.md` + the always-loaded `_MAP.md` import
- **L4 Skills** (reusable routines) → `~/.claude/skills/` (the `memory-bank/` and `bootstrap/workflows/` trees named here previously are legacy)
- **L5 Self-improvement** (read/write loop over L1-L4) → `/wiki-cycle` — read path Steps 1–4, write path Steps 6–6.5, human-gated per principle 6

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

These aren't "borrowed from the literature." They emerged from our own cycles. The failure-modes pre-mortem *(agentic-design :: wiki/project/architecture/research-agent-failure-modes-pre-mortem.md)* lists the failure modes that go beyond any single external source (the count lives there, not here) — silent poisoning is the one shared concern; the others (100-article cliff, topic bleed, source-quality blindness, silent integration-script drift, etc.) are ours.

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
