---
title: "User guide — llm-wiki"
type: how-to
pack: llm-wiki
installed_by: install-wiki
date: 2026-09-25
---

# llm-wiki — user guide

> ⚠️ **Framework-managed file.** This is shipped by the LLM-wiki installer and may be overwritten when you refresh the framework. **Don't hand-edit.** To customize, see the wiki root's `README.md` → "Framework-managed folders".

The one page to read to know how this system works: what it is, the commands you type, how an entry gets into the wiki, what the research cycle does, and where everything lives. The other pages in this folder go deeper: [`commands.md`](./commands.md) is the full command reference, [`getting-started.md`](./getting-started.md) your first hour, and `skills/<name>.md` one page per skill.

## What llm-wiki is

A knowledge wiki that an AI agent maintains for a project, built from two kinds of material:

- **What you build** (`wiki/project/`): decisions, patterns, bugs and architecture from your own working sessions, written by `/wrap-up` at the end of each one.
- **What you read** (`wiki/research/`): articles, papers, videos, repositories and posts, ingested from their full text by `/wiki-update` and `/wiki-cycle`, with a raw copy of every source kept beside the wiki.

It is plain Markdown under git. Every entry carries the same frontmatter (tier, confidence, dates, source), a mechanical gate refuses an entry that is missing its structure, nothing an agent writes counts as verified until a person says so, and a hybrid search reads the whole thing back when a question comes up.

## The commands you type

| Command | What it does |
|---|---|
| `/new-wiki` | Start a project: checks the tooling, asks a few questions, scaffolds the wiki. |
| `/wiki-update <url>` | Ingest one source now: fetch it in full, write the entry, file it (`--staged` to review it first). Two or more URLs are queued for the cycle instead. |
| `/wiki-cycle` | The research cycle: gather, triage, ingest, check, lint, report. `--full` adds the deeper passes. |
| `/wiki-search "<query>"` | Hybrid search (keyword + meaning + reranking) across the wiki. |
| `/wrap-up` | End of a session: the journal, the resume files, and the session's durable entries, staged and offered for promotion. |
| `/task-list` | The project's task list; plain speech works too ("add a task …", "mark 3 done"). |
| `/wiki-promote` | Review staged entries and move the ones you approve into `wiki/`. |
| `/wiki-verify` | Mark an entry verified. Entries never certify themselves. |
| `/wiki-rollback` | Walk an entry back to its last verified version. |

The rest (`/wiki-discover`, `/wiki-triage`, `/wiki-lint`, `/wiki-claims`, `/wiki-refresh`, `/wiki-report`, `/wiki-list`, `/wiki`, `/wiki-init`) are steps the cycle runs for you; you can call any of them directly. [`commands.md`](./commands.md) lists them all.

## How an entry gets into the wiki

1. **Written from the full source.** The agent reads the whole article, transcript, PDF or repository, saves it verbatim to `raw/`, and writes an entry: a TL;DR, the body, a Related section linking other entries, a footer naming the source.
2. **Gated by a script.** Before anything is written, `wiki-update.py` checks the draft mechanically. It refuses to file an entry with no TL;DR, fewer than two Related links, or its sections out of order; the agent fixes the draft and tries again. It warns on the rest: fewer than three tags, a short entry not tagged `stub`, a figure paraphrased instead of quoted, a `>` quote not found word for word in the raw.
3. **Staged or filed.** A single `/wiki-update` files straight into `wiki/` unless you ask for `--staged`. A cycle batch and `/wrap-up`'s entries wait in `_inbox/proposed/` until you approve them with `/wiki-promote` (or accept wrap-up's offer).
4. **Checked, when the source is long.** An entry written from a long video transcript is read against that transcript by a second agent, the `wiki-checker`, before it can be promoted.
5. **Linked in.** Promotion resolves the links, adds a backlink to every page the entry links to, and regenerates the indexes and the map.
6. **Verified by a person.** An entry starts `unverified`; `/wiki-verify` records who checked it and when.

## The research cycle

`/wiki-cycle` runs the research half end to end. A quick run (the default):

```
gather ──► your review ──► triage ──► ingest ──► checker ──► lint + links ──► report ──► commit
(Drive,    (approve the    (one owner  (up to 4    (long        (backlinks,
 feeds)     queue)          per source) workers,    transcripts) indexes, map)
                                        staged)
```

`--full` adds a semantic lint of what is new, fixes, promotion of the staged entries, contradiction hunting across claims, a synthesis of the new research against your best-practices pages, and a scan for stale entries. Run it weekly, or after a big batch.

You have **two checkpoints**: after discovery, the run pauses on what it wants to queue (a tier-4 source is never approved for you); and the next morning, `/wiki-report` summarises the run and `/wiki-promote --review` walks what it staged. Changes to your best-practices pages are applied only with your approval.

| Mode | Runs |
|---|---|
| _(none)_ / `--quick` | The quick run above. |
| `--full` | Everything, including synthesis. "Full means full." |
| `--ingest-only` | Triage and ingest what is already queued; no gathering. |
| `--discover-only` | Gather and write the checklist, then stop. |
| `--prompt-for-urls` | You paste URLs; they are ingested. |
| `--lint-only [--semantic]` | The mechanical lint (plus the semantic pass). |
| `--claims-only` · `--refresh-only` · `--report-only` | One step on its own. |

Modifiers: `<notebook>` (another registered notebook), `--direct` (file into `wiki/` instead of staging), `--no-confirm-discovery` (no pause, for unattended runs), `--resume <cycle_id>`, `--since <hours>`, `--all-topics`, `--lint-all`. The [`wiki-cycle`](./skills/wiki-cycle.md) page has each step and when it skips itself.

## Common workflows

**"I just read something worth keeping."**
```
/wiki-update https://example.com/article
```

**"I collected links all day."** Paste them all into one `/wiki-update` (they are queued), drop them in your Drive folder if Drive ingest is on, then:
```
/wiki-cycle --ingest-only
```

**"Weekly deep pass."**
```
/wiki-cycle --full
```

**"What does the wiki say about X?"**
```
/wiki-search "<terms>"
```

**"I'm done for the day."**
```
/wrap-up
```
It files what the session decided and learned, updates the resume files the next session reads at startup, and (if the project's setting says so) commits and pushes.

## Where everything lives

A notebook (in a notebooks vault, or `<project>/llm-wiki/` for a wiki kept inside the project):

```
<notebook>/
├── README.md                     what this notebook covers
├── _INDEX.md                     generated: every entry, by folder
├── _config/feeds.md              the trusted sources discovery searches
├── _signals/<slug>.json          truth-status sidecars (/wiki-verify, /wiki-rollback)
├── how-to/                       framework-managed usage docs (this page)
├── raw/                          the sources, verbatim; append-only
├── _inbox/                       work in progress
│   ├── pending/                  queued sources; _pending-list.md is the view
│   ├── intake/<bucket>/          sources triaged to one reader; README.md lists the buckets
│   ├── done/                     ingested tickets; the ledger dedup reads (never prune)
│   ├── failed/                   tickets that failed, with the reason
│   ├── proposed/                 staged entries awaiting /wiki-promote   (only while it has some)
│   ├── rejected/                 entries declined at promotion           (only while it has some)
│   ├── discovered/               discovery checklists                    (only while it has some)
│   └── reports/                  every generated report; one folder per cycle run
└── wiki/
    ├── HOME.md                   the landing page
    ├── _MAP.md                   generated: the compressed map the agent always loads
    ├── project/                  what you build: decisions, patterns, bugs, architecture, …
    │   └── best-practices/framework/   the framework-contract docs
    ├── research/<folder>/        what you read, one folder per subject
    └── sessions/                 the agent's working memory
        ├── active-context.md     the resume pointer
        └── <persona>/            handoff.md, task.md, and <YYYY-MM>/ journals
```

A notebook has only the halves it was created with (`project/`, `research/`, or neither); the other can be added any time.

## Rules the layout keeps

- **`raw/` is append-only.** A raw file is never edited or deleted.
- **Links are written by bare file name** (`[x](some-entry.md)`); the scripts turn them into the right relative paths on promotion.
- **Generated files are never hand-edited:** `_INDEX.md`, `_MAP.md`, the per-folder `_INDEX.md` files, and the `BACKLINKS-AUTO` block at the end of an entry. A file starting with `_` is a view, not an item.
- **An empty `_inbox/` folder is removed.** `proposed/`, `rejected/` and `discovered/` exist only while they hold something, so the listing alone shows what awaits you.
- **A source waits in `pending/`, is triaged into an `intake/` bucket, and moves to `done/` once ingested.** `done/` is what stops a source being ingested twice.
- **A page nothing links to** is an orphan, unless its frontmatter declares `standalone: "<reason>"` (the landing page does).
- **`sessions/` is working memory, not curated content.** `/wrap-up` writes it; the lint and the indexes skip it, and search still finds it.
- **Framework-managed files** (`how-to/` and `project/best-practices/framework/`) are refreshed from the framework and a local edit is overwritten. Ask for the change in the framework instead.

## The ideas it is built on

llm-wiki follows Chappy Asel's [self-improving AI stack](https://x.com/chappyasel/status/2041166770472644721), five layers deep:

| Layer | What it is | Here |
|---|---|---|
| **L1 — Knowledge base** | Structured Markdown plus an index. | The entries, their frontmatter, `_INDEX.md`, the search. |
| **L2 — Agent memory** | Load a small map always, the detail on demand. | `_MAP.md` always loaded; per-folder `_INDEX.md` when needed; full entries through search. |
| **L3 — Context engineering** | Load just in time; search before reading. | The [tiered context loading](../../wiki/project/best-practices/framework/tiered-context-loading.md) contract. |
| **L4 — Agent systems** | Skills, routed. | The skills, with `/wiki-cycle` orchestrating the research half. |
| **L5 — Self-improvement** | A read-write loop that compounds. | The cycle, and `/wrap-up` feeding each session's lessons back in. |

## When you're stuck

- **What's in this wiki?** Read `wiki/_MAP.md` (short) or `_INDEX.md` (everything), or type `/wiki`.
- **How do I add something?** `/wiki-update <url>`.
- **How do I find something?** `/wiki-search "<terms>"`.
- **What broke?** `/wiki-cycle --lint-only`.
- **What contradicts what?** `/wiki-cycle --claims-only`.
- **Is anything out of date?** `/wiki-cycle --refresh-only`.
- **What did the last cycle do?** `/wiki-cycle --report-only`.
- **Where did we leave off?** `wiki/sessions/active-context.md`, then your persona's `handoff.md`.

Or ask the agent in plain English; it reads these pages when a question needs them.

## The framework contracts

In `wiki/project/best-practices/framework/`, refreshed with the framework:

- [Wiki frontmatter](../../wiki/project/best-practices/framework/wiki-frontmatter-best-practices.md): the metadata every entry carries.
- [Wiki authoring](../../wiki/project/best-practices/framework/wiki-authoring-best-practices.md): how an entry's body is laid out.
- [Tiered context loading](../../wiki/project/best-practices/framework/tiered-context-loading.md): how an agent consults the wiki.
- [Cycle step return format](../../wiki/project/best-practices/framework/cycle-step-return-format.md): what each cycle step writes.
- [Memory signals: sidecar vs frontmatter](../../wiki/project/best-practices/framework/memory-signals-sidecar-vs-frontmatter-pattern.md): where truth-status lives.
- [Search bucket rerank](../../wiki/project/best-practices/framework/wiki-search-bucket-rerank-spec.md): how search orders results by truth-status.

## Further reading

- [Karpathy — the LLM wiki pattern](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f): the pattern this builds on.
- [Chappy Asel — the self-improving AI stack](https://x.com/chappyasel/status/2041166770472644721): the five layers.
- [Chroma — context rot](https://research.trychroma.com/context-rot): why more tokens is not better recall.
