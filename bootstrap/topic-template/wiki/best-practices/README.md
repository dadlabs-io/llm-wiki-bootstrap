---
title: "best-practices/ — folder purpose"
date: 2026-01-01
source_url: internal://template/best-practices-readme
ingested_by: claude-code
tier: self
confidence: high
last_reviewed: 2026-01-01
review_after: 2027-01-01
tags: [folder-readme, best-practices, navigation]
---

# best-practices/

Two kinds of documents live here. The split is deliberate.

## `framework/` — shipped contracts (don't edit)

Documents tagged `framework-contract: true` + `framework-version: N` in frontmatter. These are the **contracts llm-wiki enforces**. Scripts and skills hard-depend on their schemas:

- [`framework/wiki-frontmatter-best-practices.md`](./framework/wiki-frontmatter-best-practices.md) — canonical frontmatter schema (audit script validates against this)
- [`framework/wiki-authoring-best-practices.md`](./framework/wiki-authoring-best-practices.md) — entry body structure rules
- [`framework/cycle-step-return-format.md`](./framework/cycle-step-return-format.md) — orchestrator ↔ step-skill JSON contract
- [`framework/tiered-context-loading.md`](./framework/tiered-context-loading.md) — how agents consult the wiki

**Don't hand-edit these.** They ship with the framework. Updates arrive via framework upgrades; the installer compares `framework-version` to decide what's stale. If you need to customize, fork — you've diverged from the shipping framework, and updates won't auto-merge.

## Top level — reference patterns (free to edit)

Your ingested author patterns and external conventions live here (NOT shipped — these you accumulate as you ingest). Examples of what you might put here:
- Author-specific style guides
- External best-practice posts on your topic
- Your own synthesized conventions

Not contracts — we don't enforce these. Keep them, rewrite them, customize for your vault, whatever.

## How to tell them apart

| Check | Framework contract | Reference pattern |
|---|---|---|
| Location | `best-practices/framework/` | `best-practices/` |
| Frontmatter | `framework-contract: true` + `framework-version: N` | no framework flags |
| Edit? | No — fork if you need to diverge | Yes — customize at will |
| Updates | Via installer (diff against shipped version) | Your problem |
