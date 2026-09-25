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

**Input / Output:** consumes the current conversation, changed files, and recent commits. Produces three things every run: a per-session journal entry at `wiki/sessions/<persona>/<YYYY-MM>/`, upserted so repeat wrap-ups in one session append to the same file; refreshed working-memory dashboards at `wiki/sessions/<persona>/handoff.md`, `wiki/sessions/<persona>/task.md`, and `wiki/sessions/active-context.md`; and durable entries (component, decision, architecture, pattern, troubleshooting) staged to `_inbox/proposed/` (at the notebook root, beside `wiki/`) with a `<slug>.proposed_metadata.json` sidecar naming their target folder under `wiki/project/`. For a substantial session it also writes a snapshot to `raw/sessions/`, which the entries cite as their `raw_path`; a light session skips the snapshot and leaves `raw_path` out.

Two per-notebook settings control how much it asks: `confirm_before_create` gates the proposal table of candidate entries, and `confirm_before_promote` gates whether staged entries get promoted inline at the end of the run. Both default to asking.

**Works with:** [`wiki-promote`](./wiki-promote.md) finishes the job — wrap-up stages entries and offers to promote them immediately, and anything you decline stays in `_inbox/proposed/` for a later `/wiki-promote --review`. [`wiki-update`](./wiki-update.md) is the counterpart for external sources into `research/`; if a session turns out to be pure ingest, wrap-up still writes the journal and dashboards, then points you there for the source. [`task-list`](./task-list.md) owns the At a glance task list at the top of `task.md`; when a project has one, wrap-up keeps it current (finished tasks marked done, new ones added) and asks before removing any.

**Note:** if you only want the fast dashboard refresh without filing anything, run `/wrap-up` and answer `none` at the proposal table — the journal and dashboards still update.

**Commit and push when it's done:** `/wrap-up --auto-commit` commits the session's work at the end, and `/wrap-up --auto-push` commits and pushes it, so you can close the window. It commits only the files the session changed in the project's repository (never everything that happens to be uncommitted: anything else is left alone and named), and only the notebook's own folder in the notebook's repository; one commit each, or one in all when the wiki lives inside the project. It pushes only a branch that already tracks a remote, and never forces: a push that fails is reported and left to you. Every wrap-up ends on one line saying where things stand: `✅ WRAP-UP COMPLETE: committed and pushed ✅`, `committed, not pushed`, `nothing committed` (no flag), or `⚠️ WRAP-UP INCOMPLETE: <what's left> ⚠️`. A wrap-up still waiting for your answer at the proposal table has not reached that line.

## Full walkthrough

The single session-close command. It writes all three memory tiers under `sessions/` plus the durable layer, and (since 2026-07-06) absorbs the retired `/upd-docs`:

1. **Episodic journal** (always) — upserts `wiki/sessions/<persona>/<YYYY-MM>/<date>-<sid>.md`, the append-only "what we did" log.
2. **Working-memory dashboards** (always, Step 0.5) — refreshes the mutable resume pointer: `wiki/sessions/<persona>/handoff.md` (overwrite), `wiki/sessions/<persona>/task.md` (NOW/QUEUE, update in place), and your section of `wiki/sessions/active-context.md` (created on the first wrap-up if the project has none — nothing else seeds it). These are the memory-bank replacement — a wrap-up never leaves them stale, and after the first wrap-up all three exist for the SessionStart hook to point the next session at (the Resuming section in CLAUDE.md is the fallback where no hook is installed).
3. **Durable knowledge** (optional) — distills components/decisions/patterns/bugs, staged to `_inbox/proposed/` (beside `wiki/`) then promoted to `wiki/project/<category>/`.

If you only want the fast working-memory refresh, run `/wrap-up` and answer `none` at the proposal table — the journal + dashboards still update, nothing gets staged.

### When to run

- At end of a development session, before clearing context
- Especially after any session that made a decision, built a component, or hit a non-trivial bug
- For a trivial session (a typo fix) there is nothing to distill: answer `none` at the proposal table and the journal and dashboards still update

### What it does

1. Reads the current conversation, changed files and recent commits (a repo with no commits yet is fine), plus any session scratchpad
2. Sorts durable work into five categories: Component / Decision / Architecture / Pattern / Troubleshooting
3. Shows a proposal table of distilled entries
4. With the default setting, waits for your answer — `go` (file all), `none` (file nothing), or per-item keep / drop / reframe; with `confirm_before_create: false` it prints the table and files without waiting
5. Stages each kept entry as `_inbox/proposed/<slug>.md` (beside `wiki/`, not inside it) with a `<slug>.proposed_metadata.json` sidecar naming its target folder; the entry carries `tier: self`, `origin: wrap-up` and `category:` frontmatter (fields defined in your notebook's frontmatter spec, `wiki/project/best-practices/framework/wiki-frontmatter-best-practices.md`)
6. For a substantial session, writes a snapshot (summary, files touched, key passages — not the full transcript) to `raw/sessions/<date>-<slug>.md`, which each entry cites as its `raw_path`; a light session skips the snapshot and leaves `raw_path` out
7. Offers to promote the staged entries right away (see Promoting below)

### Categories

| Category | When |
|---|---|
| **Component** | Built or significantly changed a module/class/system |
| **Decision** | Picked an approach with non-obvious tradeoffs (ADR-style) |
| **Architecture** | System-level structural rule was established or changed |
| **Pattern** | Reusable approach that should apply elsewhere |
| **Troubleshooting** | Bug + root cause + fix — so we don't re-debug it |

Anything that fits none of the five is raised with you rather than forced into one.

### Don't

- Don't paste raw transcripts into wiki entries — the snapshot goes to `raw/sessions/`, not `wiki/`
- Don't set `confirm_before_promote: false` unless you want staged entries promoted without being asked — with the default, wrap-up asks first; the agent drafts, you edit
- Don't expect entries from a session with no settled output — wrap-up says "nothing here merits a wiki entry yet" rather than filing thin ones (the journal and dashboards still update)

### Promoting

Right after staging, wrap-up offers to promote: `yes` (all), `no`, or numbers (`1 3`). With `confirm_before_promote: false` it promotes everything without asking. Promoted entries move to `wiki/project/<category>/`, links to them are added to the related entries, `_INDEX.md` and `_MAP.md` are rebuilt, and the notebook's changes are committed (only its own paths; pushed only with `--auto-push`). After a clean all-yes or all-no it offers once to save that answer as the notebook's setting. Entries you decline stay in `_inbox/proposed/` for later:

```
/wiki-promote --review
```

