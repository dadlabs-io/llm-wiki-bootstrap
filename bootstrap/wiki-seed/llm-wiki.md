---
title: "llm-wiki — the skill pack"
type: how-to
pack: llm-wiki
installed_by: install-wiki
date: 2026-08-20
---

# llm-wiki — the skill pack

The LLM-wiki framework's skills: everything for capturing, ingesting, verifying, and maintaining
this project's durable knowledge in its wiki. The pack is **skills plus one worker agent** (no
workflow): the skills are meant for **every** agent and session, which is why they're normally
installed to the **global** skills area (`~/.claude/skills/`) rather than per-project — one
install serves all your projects, and each project's `.claude/wiki-config.json` points the
shared skills at that project's own wiki. The agent (below) is the pack's one dedicated
subagent, installed to `~/.claude/agents/` (added 2026-08-20).

Every skill has its own page in the sibling `skills/` folder — linked below. For the guided
version of this list, see [`../commands.md`](../commands.md) (the full command reference) and
[`../getting-started.md`](../getting-started.md) (the first-hour walkthrough).

## Daily drivers

| Skill | One line |
|---|---|
| [`wrap-up`](./skills/wrap-up.md) | End-of-session distillation: conversation + git diff → staged wiki entries + journals |
| [`wiki-update`](./skills/wiki-update.md) | Ingest one external source (URL, video, file, pasted text) into `research/` |
| [`wiki-search`](./skills/wiki-search.md) | Hybrid BM25 + vector + reranked search across the wiki |
| [`wiki-cycle`](./skills/wiki-cycle.md) | The full research cycle: discover → ingest → lint → fix → report |
| [`wiki-promote`](./skills/wiki-promote.md) | Review staged entries in `_inbox/proposed/` and move approved ones into the wiki |
| [`wiki`](./skills/wiki.md) | Show the wiki's INDEX — folder tree + curated file list |

## Capture & queueing

| Skill | One line |
|---|---|
| [`wiki-list`](./skills/wiki-list.md) | Pending-ingestion queue: drop URLs all day, batch-process later |
| [`wiki-discover`](./skills/wiki-discover.md) | Search trusted feeds for new content, dedupe, queue candidates |

## Health & truth maintenance

| Skill | One line |
|---|---|
| [`wiki-lint`](./skills/wiki-lint.md) | Health check: mechanical pass (links, frontmatter) or full semantic pass |
| [`wiki-refresh`](./skills/wiki-refresh.md) | Staleness scan: review_after dates, confidence decay, source freshness |
| [`wiki-report`](./skills/wiki-report.md) | Morning report: health, recent changes, pending items, contradictions |
| [`wiki-claims`](./skills/wiki-claims.md) | Extract + classify factual claims, flag contradictions between entries |
| [`wiki-verify`](./skills/wiki-verify.md) | Flip an entry unverified → verified (entries can never self-certify) |
| [`wiki-rollback`](./skills/wiki-rollback.md) | Roll an entry back to its verified ancestor along the `revises:` chain |

## Agents

| Agent | One line |
|---|---|
| `wiki-ingester` | Spawnable worker for **delegated batch ingestion**: `/wiki-cycle` (or any session) hands it a queue slice or URL list; it runs the full `wiki-update` flow per source — one at a time, each read in FULL (whole repos, full transcripts, all PDF pages) — stages results to `_inbox/proposed/`, and returns a compressed receipt. Its model is set in `~/.claude/agents/wiki-ingester-config.json` (`model_default` + `confirm_model_each_run`). For a single source you're watching live, just run `/wiki-update` inline instead. |

## Setup & lifecycle

| Skill | One line |
|---|---|
| [`new-wiki`](./skills/new-wiki.md) | Scaffold a new project with the framework (wiki + skills + config) |
| [`wiki-init`](./skills/wiki-init.md) | Scaffold just the wiki folder structure (run by new-wiki; rarely direct) |
| [`upd-docs`](./skills/upd-docs.md) | RETIRED — folded into `wrap-up`; kept as a redirect |

## How the pieces flow

Capture happens at the edges — [`wiki-list`](./skills/wiki-list.md) /
[`wiki-discover`](./skills/wiki-discover.md) queue sources, [`wiki-update`](./skills/wiki-update.md)
and [`wiki-cycle`](./skills/wiki-cycle.md) ingest them into `research/`, and
[`wrap-up`](./skills/wrap-up.md) distills your own sessions into `project/` + `sessions/` entries.
Nothing self-certifies: new entries stage through `_inbox/proposed/` and
[`wiki-promote`](./skills/wiki-promote.md), truth-status flips only via
[`wiki-verify`](./skills/wiki-verify.md), and [`wiki-lint`](./skills/wiki-lint.md) /
[`wiki-refresh`](./skills/wiki-refresh.md) / [`wiki-report`](./skills/wiki-report.md) keep the
whole thing honest over time.
