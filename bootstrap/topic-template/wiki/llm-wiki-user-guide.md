---
title: "llm-wiki — User Guide"
date: 2026-04-24
source_url: internal://session/2026-04-24-llm-wiki-user-guide
ingested_by: claude-code
tier: self
confidence: high
framework-contract: true
framework-version: 1
last_reviewed: 2026-04-24
review_after: 2026-07-24
tags: [framework-contract, user-guide, getting-started, reference, commands, workflow]
---

# llm-wiki — User Guide

The single doc to read if you want to know how to use this system. What it is, the 4 commands you actually type, what each phase of the cycle does, common workflows, and the 5-layer stack at a glance.

## What llm-wiki is

A self-improving knowledge wiki for any topic. Built from canonical sources (peer-reviewed papers, vendor primary docs, first-party creator material) with a dedupe + human-review loop. Markdown-based, AI-maintained, git-versioned. The framework is content-agnostic: drop your topic in, define your trusted feeds, and the cycle handles discovery → ingest → integration → self-assessment → reporting.

## The 4 user-facing commands

This is the entire surface you type day-to-day. Everything else is internal.

| Command | When to use |
|---|---|
| **`/wiki-cycle [flags]`** | Universal orchestrator. 90% of wiki work goes through this. Default = quick cycle (discover → ingest → lint → backlinks → INDEX/MAP regen → report). |
| **`/wiki-update <url(s)>`** | Ad-hoc ingest. Single URL = fetch + file immediately. Multiple URLs = batch-queue to `_inbox/pending/` (drain later via `/wiki-cycle --ingest-only`). |
| **`/wiki-search <query>`** | Read the wiki via qmd hybrid BM25 + vector + LLM-rerank. |
| **`/wiki-init <topic>`** | One-time: scaffold a new topic wiki. |

Other slash-commands (`/wiki-discover`, `/wiki-lint`, `/wiki-claims`, `/wiki-refresh`, `/wiki-report`, `/wiki-list`, `/wiki-promote`, `/wiki`) are **internal**. They exist as scripts + SKILL.md for programmatic invocation but are normally invoked by `/wiki-cycle` rather than typed by you.

## The cycle in one diagram

```
[ Discover ] → [ Filter ] → [ Human review #1 ]
     ↓                            ↓
     │                       (approve URLs)
     │                            ↓
     │                       [ Ingest ] → [ Integrate ] → [ Self-assess ]
     │                                                          ↓
     │                                                  [ Human review #2 ]
     │                                                          ↓
     │                                                  (approve entries,
     │                                                   resolve contradictions)
     │                                                          ↓
     └──────────────────────────────────────── feeds back to Discover ───┘
```

Two human checkpoints per cycle. Everything else is automated.

## The 8 phases (what `/wiki-cycle` actually does)

| # | Phase | What it does | Skill |
|---|---|---|---|
| 1 | Discover | Search trusted feeds (configured in `_config/feeds.md`) for new content within the date window. Staleness-first ordering: feeds with the oldest `To` date go first. | `/wiki-discover` (internal) |
| 2 | Filter | Dedupe candidates against existing wiki + pending queue. Drop low-tier-irrelevant. | (part of discover) |
| 3 | **Human review #1 (URLs)** | Orchestrator pauses, shows Queued/Skipped/Deferred tables. User approves before any fetching happens. | (interactive checkpoint) |
| 4 | Ingest | Fetch each approved URL, synthesize a wiki entry with proper frontmatter, file under appropriate folder (staged to `_inbox/proposed/` by default), save raw to `raw/`. **Before writing, the script runs a mechanical gate** (`_entry_checks.py`: TL;DR present, a Related section with 2+ wiki links, 3+ tags, thin entries tagged `stub`, numbers quoted not paraphrased) and refuses to file on a hard failure — the agent fixes the draft and retries; `--no-gate '<reason>'` is the audited override. The agent's own rubric score covers only extraction fidelity and synthesis value and is advisory, never the gate. Then **dequeue** every processed item from `_inbox/pending/` to `_inbox/done/`. Batch work is delegated to the `wiki-ingester` subagent (installed by this framework); before workers launch, you may be asked which model to use for the batch — the default lives in `~/.claude/agents/wiki-ingester-config.json`. | `wiki-ingester` agent running `/wiki-update` (internal), then `wiki-dequeue.py` |
| 5 | Integrate | **Normalize links** (resolve bare-slug / wrong-depth cross-links to correct relative paths) → **reciprocate backlinks** (every outbound `.md` link gets an inbound link in target's `BACKLINKS-AUTO` section) → regenerate per-folder _INDEX.md and the always-loaded _MAP.md. | scripts: `wiki-fix-links.py`, `wiki-reciprocate-backlinks.py`, `wiki-index-per-folder.py`, `wiki-map-compile.py` |
| 6 | Self-assess (mechanical) | Broken links, orphans, missing frontmatter, missing tier/confidence, `raw_path` integrity, icarus lineage invariants, and the same body checks the ingest gate uses (warn-only here, as a backlog view over existing entries). | `wiki-lint-mechanical.py` (+ `_entry_checks.py`) |
| 6 | Self-assess (semantic) | _`--full` only._ 4 parallel agents read each folder, find contradictions / missing cross-refs / thin coverage / concept gaps / tier issues. | `/wiki-lint --full` (internal) |
| 6b | Contradiction hunt | _`--full` only._ Claim-level extraction + cross-claim contradiction detection. | `/wiki-claims` (internal) |
| 7 | **Human review #2 (entries)** | Morning report — new entries to approve, contradictions to resolve, suggested next-night targets. | `/wiki-report` (internal call) |
| 8 | Schedule | Cron loop. _Currently manual; deliberate._ | (deferred) |

## `/wiki-cycle` mode flags

Pick one mode flag (default = quick); combine with modifiers as needed.

| Mode flag | What runs |
|---|---|
| _(none)_ — `--quick` default | Phases 1, 2, 3, 4, 5, 6 (mechanical), 7. ~5-10 min for ≤20 items. |
| `--full` | Above + 6 (semantic) + 6b (claims) + Refresh. ~30-40 min. Run weekly or after big batches. |
| `--lint-only` | Phase 6 (mechanical) only. Print report; done. Add `--semantic` for 4-agent semantic pass too. |
| `--discover-only` | Phase 1+2+3 only. Produces checklist; stops before ingest. |
| `--ingest-only` | Skip phases 1-3. Drain the pending queue + cleanup. |
| `--prompt-for-urls` | Pause; user pastes URLs; ingest them. No discovery. |
| `--report-only` | Regen morning report from last cycle's JSONs. No new work. |
| `--refresh-only` | Stale-entry scan (review_after dates). |
| `--claims-only` | Contradiction extraction only. |

| Modifier | Purpose |
|---|---|
| `<topic>` | Specific topic name. If omitted, the orchestrator falls back to whichever topic you've set as default in your harness config. |
| `--direct` | File entries to `wiki/` instead of `_inbox/proposed/` (skip the staging step) |
| `--resume <cycle_id>` | Pick up an interrupted cycle from its scratchpad |
| `--no-confirm-discovery` | Skip Phase 3 human checkpoint (for cron / headless runs) |
| `--since <hours>` | Discovery window override (default: 24h) |

## Common workflows

### "I just saw something interesting" — single-URL ingest
```
/wiki-update https://example.com/article
```
Fetches, synthesizes, files under the right folder. Done in 2-3 min.

### "I collected a bunch of links today" — batch queue
Paste:
```
/wiki-update
  https://a.com
  https://b.com
  https://c.com
  ...
```
All go to `_inbox/pending/`. When you're ready:
```
/wiki-cycle --ingest-only
```
Drains the queue + cleanup, ~5-10 min depending on count.

### "Weekly deep pass" — full cycle
```
/wiki-cycle --full
```
Discover → ingest → mechanical lint → 4-agent semantic lint → claims extraction → refresh scan → report. 30-40 min. Run once a week or after a big content drop.

### "Quick health check"
```
/wiki-cycle --lint-only
```
2-second mechanical pass: broken links, orphans, missing fields. Prints report; done.

### "Just scan for new content but don't ingest yet"
```
/wiki-cycle --discover-only
```
Searches feeds, produces per-bucket checklists in `_inbox/intake-<bucket>/` (or one combined checklist in `_inbox/discovered/` when the topic has no intake folders). You review, then later run `--ingest-only` to drain.

### "What does the wiki say about X"
```
/wiki-search "<terms>"
```
qmd hybrid retrieval. Finds entries, ranks them, summarizes.

## The 5-layer stack at a glance

llm-wiki is built around Chappy Asel's [self-improving AI stack](https://x.com/chappyasel/status/2041166770472644721). All five layers are framework concerns:

| Layer | What it is | How it shows up here |
|---|---|---|
| **L1 — Knowledge Bases** | Structured markdown + indexing. | Your wiki entries, frontmatter schema, qmd search, `wiki-index.py` regenerates `_INDEX.md`. |
| **L2 — Agent Memory (the map)** | 3-tier loading: always-loaded compressed root + per-folder maps + full entries. | `wiki/_MAP.md` (auto-loaded, ~2K tokens) + `<folder>/_INDEX.md` (~1-3K each, loaded as needed) + qmd for full-content retrieval. |
| **L3 — Context Engineering** | Just-in-time loading; additive-not-replacing discipline. | [`tiered-context-loading.md`](./best-practices/framework/tiered-context-loading.md) is the contract. |
| **L4 — Agent Systems** | Skill organization + multi-routing. | `/wiki-cycle` is the explicit batch orchestrator that handles event/file routing for our scale. Hooks/hierarchical skill grouping deferred until the wiki has 100+ skills. |
| **L5 — Self-Improvement** | Read/write loop that compounds. | The 8-phase cycle above — `/wiki-cycle` is the implementation. |

## Where everything lives

```
<vault>/<topic>/
├── README.md                        — topic scope; what's in scope, what's not
├── _config/
│   └── feeds.md                     — your trusted sources for discovery
├── _inbox/
│   ├── pending/                     — queued items waiting for ingest
│   │   └── _pending-list.md         — auto-rendered view of the queue (pending + failed); never hand-edit
│   ├── done/                        — items already ingested (machine ledger; the URL-dedup source — never prune casually)
│   ├── failed/                      — items that failed ingest, with .error sidecars
│   ├── proposed/                    — staged entries pending human approval (Phase 7) — CREATE-ON-DEMAND: exists only while items wait
│   ├── rejected/                    — entries declined at promote (audit trail) — create-on-demand
│   ├── intake-<bucket>/             — per-bucket discovery checklists (Phase 1 output), one owner per bucket; set up by hand per topic
│   ├── discovered/                  — legacy single combined checklist, used only when no intake-*/ folders exist — create-on-demand
│   ├── reports/                     — EVERY generated report: lint-report.md, <agent>-semantic-lint-<date>.md,
│   │   │                              claims-report-<date>.md, discovery-<date>.md, refresh-report-<date>.md
│   │   └── <date>/<cycle_id>/       — per-cycle artifacts (JSON + MD sidecars + final report)
│   └── archive/                     — hand-parked old reports/checklists you want out of the way but not deleted
├── raw/                             — verbatim source dumps (append-only; never edit)
└── wiki/
    ├── HOME.md                     — landing page
    ├── _MAP.md                       — auto-loaded compressed orientation (Asel L2 tier-1)
    ├── _INDEX.md                     — auto-generated comprehensive listing
    ├── concept-gaps-...md           — running tracker of mentioned-but-not-covered concepts
    ├── best-practices/
    │   ├── README.md                — explains the framework/ vs reference split
    │   ├── framework/               — shipped contracts (don't edit; framework-version'd)
    │   │   ├── llm-wiki-user-guide.md            ← you are here
    │   │   ├── wiki-frontmatter-best-practices.md
    │   │   ├── wiki-authoring-best-practices.md
    │   │   ├── cycle-step-return-format.md
    │   │   └── tiered-context-loading.md
    │   └── ...                      — reference patterns (free to edit, ingested from external authors)
    ├── sessions/                    — MEMORY layer (non-curated; exempt from the pipeline like _inbox/)
    │   ├── active-context.md        — cross-persona dashboard          (MUTABLE)
    │   └── <persona>/               — created on demand by the running persona (no fixed list)
    │       ├── task.md              — NOW + QUEUE                       (MUTABLE, overwrite)
    │       ├── handoff.md           — resume-here / survival dump       (MUTABLE, overwrite)
    │       ├── BACKLOG.md           — persona backlog                   (MUTABLE)
    │       ├── reading-list.json    — session-start context load
    │       ├── incoming/            — inter-persona handoff (CRs)
    │       └── <YYYY-MM>/<date>-<sid>.md  — episodic journals (APPEND; written by /wrap-up)
    └── <topic-folders>/             — your content; folder taxonomy is up to you
        └── <folder>/_INDEX.md        — auto-generated tier-2 maps
```

## File layout invariants

- `raw/` is **append-only**. Never edit or delete a raw file. The agent fetches; humans don't touch.
- `_inbox/proposed/` is **staging**. Human approves via `/wiki-promote` before entries reach `wiki/`.
- **Create-on-demand folders** (`proposed/`, `rejected/`, `discovered/`): they exist only while they hold items. Writers `mkdir -p` before writing; `/wiki-promote` removes `proposed/` and `rejected/` once empty. So a folder's *presence* in `_inbox/` is itself the signal that something awaits action — no need to open it to know.
- **Underscore-prefixed files are views, not items.** `_inbox/pending/_pending-list.md` is the auto-rendered queue view (pending + failed; done shows as a count only). Every queue reader (`wiki-list-add`, `wiki-list-process`, `wiki-list-render`, `wiki-dequeue`) skips `_`-prefixed files — any new queue reader must too.
- **All generated reports go under `_inbox/reports/`** (lint, semantic lint, claims, discovery stats, refresh, per-cycle runs). Nothing derived sits loose in `_inbox/`.
- **Queue lifecycle**: an item lives in `_inbox/pending/` until it's ingested, then moves to `_inbox/done/`. `/wiki-cycle` runs `wiki-dequeue.py` after ingest to do this automatically (it matches a pending item's `source:` URL against ingested entries in `wiki/` or `_inbox/proposed/`). If you ever see already-ingested items lingering in `pending/`, run `wiki-dequeue.py --topic <topic>` to reconcile — genuinely-unprocessed and unreadable-deferral items stay put.
- **Cross-links are authored by bare slug** — the markdown link target is just the bare filename (`some-entry.md`), no folder path; `wiki-fix-links.py` (run on promote / in the cycle's Integrate phase) resolves them to correct relative paths. If a promoted entry shows broken links, run `wiki-fix-links.py --topic <topic>` — it's deterministic and idempotent.
- `wiki/<folder>/_INDEX.md` and `wiki/_MAP.md` are **auto-regenerated**. Don't hand-edit; changes get overwritten.
- `BACKLINKS-AUTO` blocks inside any entry are **machine-managed**. Edit only outside the markers.
- **`sessions/` is the memory layer, not curated content.** It holds *working memory* (persona-root `task.md`/`handoff.md`/`BACKLOG.md`/`reading-list.json` + `active-context.md` — MUTABLE, overwrite-in-place) and *episodic memory* (dated `<YYYY-MM>/` journals — append-only). Both tiers are written by `/wrap-up` (the working-memory dashboards in its Step 0.5, the journal in Step 0; the old `/upd-docs` was folded in on 2026-07-06). The whole `sessions/` tree is **exempt from the curated pipeline** the same way `_inbox/` is — lint/map/index/reciprocate/refresh skip it — while qmd still indexes it so it stays searchable. Persona folders are created **on demand** (a new persona just makes its own folder); there is no fixed persona list. There is **no `completed.md`** — the completed record is the `/wrap-up` journals (searchable by `session_id`/`date`/`persona`).
- `best-practices/framework/*.md` are **framework contracts**. Don't edit unless you intend to fork the framework.

## When you're stuck

- **"What's in this wiki?"** → read `_MAP.md` (compressed) or `_INDEX.md` (comprehensive)
- **"How do I ingest something?"** → `/wiki-update <url>`
- **"How do I find something?"** → `/wiki-search "<terms>"`
- **"What broke?"** → `/wiki-cycle --lint-only`
- **"What contradicts what?"** → `/wiki-cycle --claims-only`
- **"Is anything stale?"** → `/wiki-cycle --refresh-only`
- **"What did I do recently?"** → `/wiki-cycle --report-only` (regen latest morning report)

## Related framework contracts

- [Wiki Frontmatter](./best-practices/framework/wiki-frontmatter-best-practices.md) — required entry metadata schema
- [Wiki Authoring](./best-practices/framework/wiki-authoring-best-practices.md) — entry body structure (TL;DR / body / Related) and principle 11: every hard rule is prose paired with a mechanical check
- [Cycle Step Return Format](./best-practices/framework/cycle-step-return-format.md) — orchestrator ↔ skill JSON contract
- [Tiered Context Loading](./best-practices/framework/tiered-context-loading.md) — how agents consult the wiki

## External references

- [Karpathy — LLM Wiki Pattern](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f) — the foundational pattern this builds on
- [Chappy Asel — The Self-Improving AI Stack (5 Layers Deep)](https://x.com/chappyasel/status/2041166770472644721) — the 5-layer framework
- [Chroma — Context Rot](https://research.trychroma.com/context-rot) — empirical basis for "more tokens ≠ better recall"
