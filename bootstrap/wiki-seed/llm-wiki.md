---
title: "llm-wiki — the skill pack"
type: how-to
pack: llm-wiki
installed_by: install-wiki
date: 2026-08-20
---

# llm-wiki — the skill pack

The LLM-wiki framework's skills: everything for capturing, ingesting, verifying, and maintaining
this project's durable knowledge in its wiki. The pack is **skills, two agents and one
startup hook** (no workflow): the skills are meant for **every** agent and session, which is why
they're normally installed to the **global** skills area (`~/.claude/skills/`) rather than
per-project — one install serves all your projects, and each project's `.claude/wiki-config.json`
points the shared skills at that project's own wiki. The agents (below) are the pack's two dedicated
subagents, installed to `~/.claude/agents/`: an ingest worker (2026-08-20) and a checker that
reads its work against the source (2026-09-24). The hook, added to
`~/.claude/settings.json`, lists a wiki project's resume files (`sessions/active-context.md`, then
`sessions/<persona>/handoff.md` and `task.md`) when a session starts and after `/clear`, so the
session picks up where the last one left off; outside a wiki project it prints nothing.

Every skill has its own page in the sibling `skills/` folder — linked below. For the guided
version of this list, see [`user-guide.md`](./user-guide.md) (the whole system on one page),
[`commands.md`](./commands.md) (the full command reference) and
[`getting-started.md`](./getting-started.md) (the first-hour walkthrough).

## Daily drivers

| Skill | One line |
|---|---|
| [`wrap-up`](./skills/wrap-up.md) | End of session: updates the session journal and the resume dashboards (handoff, task, active-context), stages durable entries, then offers to promote them |
| [`task-list`](./skills/task-list.md) | The project's task list at the top of `task.md`: one table per owner; add, mark done, remove only on your word. Plain speech works ("add a task …", "delete task 4") |
| [`wiki-update`](./skills/wiki-update.md) | Ingest one external source (URL, video, PDF, X post, file, pasted text) and file it directly into the wiki (`--staged` to stage it for review); two or more URLs are queued for `wiki-cycle` |
| [`wiki-search`](./skills/wiki-search.md) | Hybrid BM25 + vector + reranked search across the wiki |
| [`wiki-cycle`](./skills/wiki-cycle.md) | The full research cycle: discover → ingest → lint → fix → report |
| [`wiki-promote`](./skills/wiki-promote.md) | Review staged entries in `_inbox/proposed/` and move approved ones into the wiki |
| [`wiki`](./skills/wiki.md) | Show the wiki's INDEX — folder tree + curated file list |

## Capture & queueing

| Skill | One line |
|---|---|
| [`wiki-list`](./skills/wiki-list.md) | Pending-ingestion queue: drop URLs all day, batch-process later |
| [`wiki-discover`](./skills/wiki-discover.md) | Search trusted feeds for new content, dedupe, queue candidates |
| [`wiki-triage`](./skills/wiki-triage.md) | Give each queued source one owner: move it into the intake bucket whose purpose fits (`main` is the catch-all), capture the raw for other readers, log the call |

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
| [`wiki-ingester`](./agents/wiki-ingester.md) | Spawnable worker for **delegated batch ingestion**: `/wiki-cycle` (or any session) hands it a queue slice or URL list; it runs the full `wiki-update` flow per source — one at a time, each read in FULL (whole repos, full transcripts, all PDF pages) — stages results to `_inbox/proposed/`, and returns a compressed receipt. Its model is set in `~/.claude/agents/wiki-ingester-config.json` (`model_default` + `confirm_model_each_run`). For a single source you're watching live, just run `/wiki-update` inline instead. |
| [`wiki-checker`](./agents/wiki-checker.md) | A second reader for a staged entry: checks it against its raw source and reports unsupported claims, skipped sections and misquotes; it never edits anything. `/wiki-cycle` runs it on long transcripts (15 minutes or more by default) before promotion and holds back an entry it flags. Settings in `~/.claude/agents/wiki-checker-config.json`. |

## Setup & lifecycle

| Skill | One line |
|---|---|
| [`new-wiki`](./skills/new-wiki.md) | Scaffold a new project with the framework (wiki + skills + config), or add a wiki to an existing project or another notebook to the vault |

## How the pieces flow

Capture happens at the edges — [`wiki-list`](./skills/wiki-list.md) /
[`wiki-discover`](./skills/wiki-discover.md) queue sources, [`wiki-update`](./skills/wiki-update.md)
and [`wiki-cycle`](./skills/wiki-cycle.md) ingest them (usually into `research/`), and
[`wrap-up`](./skills/wrap-up.md) distills your own sessions into `project/` + `sessions/` entries.
Nothing self-certifies: `wrap-up` entries and `wiki-cycle` batches stage through `_inbox/proposed/`
for [`wiki-promote`](./skills/wiki-promote.md) (a single `wiki-update` files directly unless you
ask for `--staged`), an entry becomes verified only through
[`wiki-verify`](./skills/wiki-verify.md), and [`wiki-lint`](./skills/wiki-lint.md) /
[`wiki-refresh`](./skills/wiki-refresh.md) / [`wiki-report`](./skills/wiki-report.md) keep the
whole thing honest over time.
