---
title: "research/ — cross-agent semantic memory (external)"
date: 2026-05-25
source_url: internal://framework/research-readme
ingested_by: claude-code
tier: self
confidence: high
last_reviewed: 2026-05-25
review_after: 2027-05-25
raw_path: (none — self-authored)
tags: [readme, folder-marker, four-layer-model, research, semantic-external, self-authored]
---

# `research/` — cross-agent semantic memory (external)

**Cognitive analogue**: semantic memory (external — "what I learned from things I ingested").
**Frame**: "what I learned from papers / blog posts / vendor docs / GitHub repos."
**Owner**: cross-agent. All personas read here; ingest skills (`/wiki-update`, `/wiki-cycle`) write here.

This is the **research** layer of the four-layer memory model (icarus integration plan §6). See [sessions/README.md](../sessions/README.md) for the full four-layer table.

## Subfolder convention

```
research/
├── active/           current / evolving — recent papers, fast-moving frameworks, items where the field is still settling
├── long-term/        peer-reviewed / settled — foundational papers, mature frameworks
├── tooling/          specific tools / libraries / platforms
└── _inbox/
    └── proposed/     staging area for cycle-ingested entries pending promote-review
```

(Project may add others as needed: e.g., `research/orchestration/`, `research/implementation/`, `research/skills/`, `research/interesting-docs/`. The structure is uniform; the population is per-project.)

## What goes here

- ArXiv papers, peer-reviewed publications
- Vendor blog posts, engineering writeups
- GitHub repo descriptions / READMEs we've evaluated
- Comparison entries ("X vs Y vs Z" — landscape surveys)
- Community discussion (HN threads, Twitter threads with substance, conference talks)

## What does NOT go here

- **Our own decisions about what to build** → `project/decisions/`
- **Our own components / architecture** → `project/components/` / `project/architecture/`
- **Per-session episodic** → `sessions/`
- **Raw source files** → `<topic>/raw/`

## Provenance discriminator (vs `project/`)

Both `project/` and `research/` are semantic memory; both durable; both cross-agent. The line is **provenance**:

- **`research/`** = "we ingested this, it describes the world." Load-bearing claim is about something external.
- **`project/`** = "we authored this, it describes us." Load-bearing claim is about the codebase or process we're building.

Synthesis docs that draw on research to inform a project decision live in `project/`, not `research/`. (See [project/README.md](../project/README.md).)

## Lifecycle differences

`research/` entries get **superseded** when newer literature lands. The supersession is captured via the icarus `revises:` / `superseded_by:` schema (icarus integration plan §1). Project entries are anchored to live code and follow the code's lifecycle.

Mixing them in one folder made both lifecycles harder to reason about — that's the load-bearing reason the four-layer split exists.

## For research-only projects

If a project is entirely a research wiki (e.g., a curated knowledge base about a specific field), `project/` may be sparse or absent. The structure is uniform; the population is per-project. The icarus / Mem0 / OpenClaw kinds of vendor-knowledge wikis fit cleanly into `research/` alone.

## Briefing-rule signal

`research/` is NOT loaded by default at session start for development tasks. It's loaded only when:
- The current task explicitly cites a research entry
- A `project/decisions/` doc the agent is reading cross-references a research entry
- The user explicitly asks ("what does the wiki say about X?")

This is the load-bearing reason the four-layer model exists: better signal-to-noise on session start vs the old single-folder approach.

## Related

- [icarus-integration-plan.md §6](../project/best-practices/framework/icarus-integration-plan.md) — the four-layer model spec
- [sessions/README.md](../sessions/README.md) — the "episodic memory" peer
- [project/README.md](../project/README.md) — the "internal semantic memory" peer
