---
title: "wrap-up — skill"
type: how-to
artifact: skill
name: wrap-up
installed_by: install-wiki
date: 2026-07-31
---

# wrap-up — skill

The single session-close command. It turns "we just spent two hours figuring out X" into a record you (or a teammate) can read in sixty seconds: a running journal of what happened, refreshed dashboards that say where to resume, and distilled entries for the durable decisions, components, patterns, and bugs the session produced. It writes about *your own* work — external articles and videos belong to [`wiki-update`](./wiki-update.md). It deliberately distills rather than dumping: the transcript is raw material, the entry is the synthesis.

**Trigger:** */wrap-up*, plus natural phrasings like "wrap up this session", "document what we did", "save progress", or "save state".

**Input / Output:** consumes the current conversation, changed files, and recent commits. Produces three things every run: a per-session journal entry at `wiki/sessions/<persona>/<YYYY-MM>/`, upserted so repeat wrap-ups in one session append to the same file; refreshed working-memory dashboards at `sessions/<persona>/handoff.md`, `sessions/<persona>/task.md`, and `sessions/active-context.md`; and durable entries (component, decision, architecture, pattern, troubleshooting) staged to `_inbox/proposed/` with a `<slug>.proposed_metadata.json` sidecar naming their target folder under `wiki/project/`. Optionally it also writes a session snapshot to `raw/sessions/` so every derived entry stays traceable to its source.

Two per-notebook settings control how much it asks: `confirm_before_create` gates the proposal table of candidate entries, and `confirm_before_promote` gates whether staged entries get promoted inline at the end of the run. Both default to asking.

**Works with:** [`wiki-promote`](./wiki-promote.md) finishes the job — wrap-up stages entries and offers to promote them immediately, and anything you decline stays in `_inbox/proposed/` for a later `/wiki-promote --review`. [`wiki-update`](./wiki-update.md) is the counterpart for external sources into `research/`; wrap-up redirects there if a session turns out to be pure ingest. [`upd-docs`](./upd-docs.md) is retired and its dashboard refresh now happens here.

**Note:** if you only want the fast dashboard refresh without filing anything, run `/wrap-up` and answer `none` at the proposal table — the journal and dashboards still update.

## Full walkthrough

The single session-close command. It writes all three memory tiers under `sessions/` plus the durable layer, and (since 2026-07-06) absorbs the retired `/upd-docs`:

1. **Episodic journal** (always) — upserts `wiki/sessions/<persona>/<YYYY-MM>/<date>-<sid>.md`, the append-only "what we did" log.
2. **Working-memory dashboards** (always, Step 0.5) — refreshes the mutable resume pointer: `sessions/<persona>/handoff.md` (overwrite), `sessions/<persona>/task.md` (NOW/QUEUE, update in place), and your section of `sessions/active-context.md`. These are the memory-bank replacement — a wrap-up never leaves them stale.
3. **Durable knowledge** (optional) — distills components/decisions/patterns/bugs, staged to `wiki/_inbox/proposed/` then promoted to `wiki/project/<category>/`.

If you only want the fast working-memory refresh, run `/wrap-up` and answer `none` at the proposal table — the journal + dashboards still update, nothing gets staged.

### When to run

- At end of a development session, before clearing context
- Especially after any session that made a decision, built a component, or hit a non-trivial bug
- Skip for trivial sessions (single typo fix, etc.) — there's nothing worth distilling

### What it does

1. Reads the current conversation + git diff + scratchpad
2. Identifies categories: Component / Decision / Architecture / Pattern / Troubleshooting / (other)
3. Proposes a table of distilled entries
4. **Pauses for your veto** before filing anything — you can drop or rename rows
5. Stages each as `wiki/_inbox/proposed/<category>/<slug>.md` with `tier: self` and `category: <type>` frontmatter
6. Saves a session transcript snapshot at `raw/sessions/<date>-<slug>.md`

### Categories

| Category | When |
|---|---|
| **Component** | Built or significantly changed a module/class/system |
| **Decision** | Picked an approach with non-obvious tradeoffs (ADR-style) |
| **Architecture** | System-level structural rule was established or changed |
| **Pattern** | Reusable approach that should apply elsewhere |
| **Troubleshooting** | Bug + root cause + fix — so we don't re-debug it |

If something doesn't fit any category, surface it to the user — adding a new category is fine; jamming it into the wrong one isn't.

### Don't

- Don't paste raw transcripts into wiki entries — they go to `raw/sessions/`, not `wiki/`
- Don't promote `/wrap-up` output without review — the agent is a starting point, you're the editor
- Don't run `/wrap-up` on a session that hasn't changed anything — it'll either produce nothing or hallucinate fake structure

### After /wrap-up

```
/wiki-promote --review
```

Walks each proposed entry, lets you accept / edit / reject. Accepted entries move from `_inbox/proposed/` to `wiki/<category>/`. Backlinks regenerate; `_MAP.md` and `_INDEX.md` re-build.

### Source signal

`/wrap-up` writes a sidecar at `_signals/<slug>.json` per entry — records what the session looked like (token count, files touched, time spent) so future analysis can correlate session weight with output quality. This is Gap #1 in the framework (designed, partially implemented).

