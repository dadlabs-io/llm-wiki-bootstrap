---
name: upd-docs
description: Quick-save the current session's WORKING MEMORY (live task state + resume dump) into the wiki's sessions/ layer. Writes the running persona's task.md (NOW/QUEUE), handoff.md (resume-here), and the shared active-context.md — all MUTABLE, overwrite-in-place, exempt from the curated pipeline. Use at the end of a work session, when the user says "save progress", "upd-docs", "/upd-docs", "update docs", "save state", or when context is getting long. For crystallizing durable knowledge or the episodic session journal, use /wrap-up instead.
---

# /upd-docs — save working memory to `sessions/`

**Speed target: under 2 minutes.** A quick save, not an audit.

This writes the **working-memory** tier of the wiki's `sessions/` layer — the live dashboards that answer "what am I doing right now / where do I resume." It is the counterpart to `/wrap-up` (which writes the append-only episodic **journal** and extracts durable knowledge to `project/*`). Between them:

| | `/upd-docs` (this) | `/wrap-up` |
|---|---|---|
| Writes | `sessions/<persona>/{task,handoff}.md` + `sessions/active-context.md` | `sessions/<persona>/<YYYY-MM>/<date>-<sid>.md` (journal) + `project/*` extraction |
| Lifecycle | MUTABLE — overwrite in place | APPEND — one entry per session |
| Purpose | live working set + resume pointer | history + durable knowledge |

There is **no `completed.md`** — the completed record lives in the `/wrap-up` journals (each has `session_id`/`date`/`persona` frontmatter and a work-completed section, and is qmd-searchable). Don't create one.

## Step 0 — Resolve persona + path

- **Persona** = the persona you are running as (you know this — e.g. ARCH, DEV, PM). Lowercase it for the folder (`arch`, `dev`, `pm`). If genuinely unset, use `main`.
- **Wiki dir** resolves from the project's `.claude/wiki-config.json` (registry-aware), same as every other wiki skill. Base path = `<wiki_dir>/sessions/`.
- **Create the folder on demand** (a new persona just works):
  ```bash
  mkdir -p <wiki_dir>/sessions/<persona>
  ```
  No fixed persona list exists anywhere — you create your own folder the first time.

## Step 1 — HANDOFF (do this first — survival insurance)

**File:** `<wiki_dir>/sessions/<persona>/handoff.md` — **overwrite** with a full session dump. If context dies after this step, nothing is lost.

Gather: `git diff --stat HEAD~5..HEAD`, `git status --porcelain`. Then write:

```
HANDOFF — <PERSONA> — <DATE>
GOAL: [one sentence — what to do next]
WORK COMPLETED (this session): [what was done, file paths, key decisions]
CURRENT STATE: [what's running / broken / blocked]
PENDING: [planned-but-not-done, blockers]
KEY FILES: [path — role] (max 10)
CONTEXT FOR CONTINUATION: [what the next session needs; gotchas; references]
```
Rules: first person; workspace-relative paths; no secrets; overwrite (snapshot, not a log).

## Step 2 — TASK (quick save)

**File:** `<wiki_dir>/sessions/<persona>/task.md` — read it first, then update in place (don't blind-overwrite):

```
## NOW
[Single thing being actively worked — or "Awaiting next task"]

## QUEUE
1. [Next priority]
2. [After that]
3. [Backlog]
```
When a NOW item is done, it's captured by `/wrap-up`'s journal — just promote the next QUEUE item to NOW here.

## Step 3 — ACTIVE-CONTEXT (only if stale)

**File:** `<wiki_dir>/sessions/active-context.md` — the cross-persona dashboard. Read your persona's section; if it still describes what you're doing, skip. If not, update ONLY your persona's lines (Status / Recent / Next). Do NOT touch other personas' sections; do NOT rewrite the file. 5 seconds, not 5 minutes.

## What this does NOT do

- ❌ the episodic journal or `project/*` durable extraction → that's `/wrap-up`
- ❌ ingesting external sources → `/wiki-update`
- ❌ any curated-entry work (lint/map/backlinks) — `sessions/` is exempt from all of it

## Notes

- Everything written here is **mutable working memory** under `sessions/` — the pipeline (`wiki-lint-mechanical`, `wiki-map-compile`, `wiki-index-per-folder`, `wiki-reciprocate-backlinks`, `wiki-refresh`) treats `sessions/` like `_inbox/` and leaves it alone; qmd still indexes it so it's searchable.
- Persona folders and dashboard files are created lazily — never pre-scaffold a persona set.
