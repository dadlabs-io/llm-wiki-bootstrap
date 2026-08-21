---
title: "project/ — cross-agent semantic memory (internal)"
date: 2026-05-25
source_url: internal://framework/project-readme
ingested_by: claude-code
tier: self
confidence: high
last_reviewed: 2026-05-25
review_after: 2027-05-25
raw_path: (none — self-authored)
tags: [readme, folder-marker, four-layer-model, project, semantic-internal, self-authored]
---

# `project/` — cross-agent semantic memory (internal)

**Cognitive analogue**: semantic memory (internal — "what I know about THIS thing").
**Frame**: "what I know about the codebase / process / system we're building."
**Owner**: cross-agent. All personas read and write here; this is the shared durable knowledge layer.

This is the **project** layer of the four-layer memory model (icarus integration plan §6). See [sessions/README.md](../sessions/README.md) for the full four-layer table.

## Subfolder convention

```
project/
├── components/         architectural components / modules / services
├── decisions/          ADRs and load-bearing decisions with rationale
├── architecture/       system maps, data flows, deployment topologies
├── patterns/           reusable patterns we've adopted (or rejected)
├── troubleshooting/    bug post-mortems, debugging guides, fix recipes
└── best-practices/     project-specific conventions (coding, testing, comms)
    └── framework/      meta-framework docs (icarus plan, lint spec, etc.)
```

## The project-vs-research line — PROVENANCE, not topic

Both `project/` and `research/` are semantic memory; both are durable; both cross-agent. The discriminator is **provenance**:

- **`project/`** = "we authored this, it describes us." Decisions, components, patterns we settled on, bugs we traced. Load-bearing claim is about the codebase or process we're building.
- **`research/`** = "we ingested this, it describes the world." Papers, vendor blogs, library writeups, comparisons. Load-bearing claim is about something external.

**Synthesis docs that draw on research to inform a decision** (like the icarus integration plan) live in **`project/best-practices/framework/`** because the load-bearing claim is what *we* decided, even though they cite research throughout. Cite via cross-references; don't duplicate the research entry in project/.

## What goes here

- Decisions: `project/decisions/0042-pick-mem0.md` (cite `research/active/mem0-chhikara-et-al.md` for the why)
- Components: `project/components/dashboard.md` (the spec / interface / known-issues for a component we own)
- Architecture: `project/architecture/system-map.md`, `project/architecture/data-flow-receipts.md`
- Patterns: `project/patterns/eav-schema.md`, `project/patterns/circuit-breaker-for-llm-calls.md`
- Troubleshooting: `project/troubleshooting/openclaw-auth-symlink-wipe.md`
- Best-practices: `project/best-practices/communication.md`, `project/best-practices/database-conventions.md`
- Framework (meta): `project/best-practices/framework/icarus-integration-plan.md`

## What does NOT go here

- **Per-session episodic** (what happened when I tried X) → `sessions/`
- **External-sourced research** → `research/`
- **Raw source files** (papers, blog HTML, transcripts) → `<topic>/raw/`

## Cross-references are bidirectional and load-bearing

A `project/decisions/0042-pick-mem0.md` cites `research/active/mem0-chhikara-et-al.md` ("we picked this because of these benchmarks") and the research entry's BACKLINKS-AUTO surfaces the project decision so anyone reading the mem0 entry sees "workflows-core picked this — see decision #42."

This is exactly why all four layers live under one `wiki/` tree — uniform link semantics across `qmd`, `/wiki-search`, BACKLINKS-AUTO, and reciprocate-backlinks.

## Briefing-rule signal

An agent starting a development task pulls `sessions/<own-persona>/` + `project/` by default — that's "everything I know about this project we're building, plus my own episodic context." Research is loaded only if the task explicitly cites it. Better signal-to-noise than the old single-folder approach.

## Related

- [icarus-integration-plan.md §6](./best-practices/framework/icarus-integration-plan.md) — the four-layer model spec
- [sessions/README.md](../sessions/README.md) — the "episodic memory" peer
- [research/README.md](../research/README.md) — the "external semantic memory" peer
