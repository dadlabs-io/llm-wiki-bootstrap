---
name: wrap-up
description: Crystallize the current session's work into the project wiki. ALWAYS updates a running per-session journal at wiki/sessions/<persona>/<YYYY-MM>/ (upserted every wrap-up so the "what we did" record builds as you go), AND extracts durable knowledge — components built, decisions made, patterns established, bugs investigated — staged to _inbox/proposed/ for review then promoted to wiki/project/<category>/. For ingesting EXTERNAL sources (URLs/papers/videos) use /wiki-update instead. Use when the user says "wrap up", "wrap-up", "/wrap-up", "wrap this session", "document what we did", "crystallize this session", "save this work".
---

# /wrap-up

End-of-session distillation. Read the conversation + recent file changes, identify durable work product, file wiki entries that capture the *why* and the *what* — not the conversation transcript.

## What this is FOR

A development project (codebase you're building) where session work produces durable artifacts: a new component, an architectural decision, a debugging insight, a pattern that should be remembered. `/wrap-up` is what turns "we just spent 2 hours figuring out X" into a wiki entry that next-session-you (or a teammate) can read in 60 seconds.

## What this is NOT for

- **Research projects** — use `/wiki-update` or `/wiki-cycle` instead. Those ingest *external* content. `/wrap-up` distills *internal* work.
- **Transcript dumps** — don't paste the chat into a wiki. The wiki entry is a *distilled* artifact: what was decided, what was built, what was learned. The transcript is raw material; the entry is the synthesis.
- **Trivial fixes** — typo-fix, single-line edit, dependency bump. Don't wiki it.
- **In-flight thinking** — if a decision is still half-baked, don't wrap up yet. Wait until it's actually settled, or capture it as a "decision in flight" with explicit `confidence: low` and a `review_after` flag.

## Required context

| Field | How to get it |
|---|---|
| Project name (matches a wiki topic in the vault) | From CWD: read the project's `CLAUDE.md` for the topic reference. Fall back to asking the user. |
| Vault root | From `<cwd>/.claude/wiki-config.json` (`vault_root`) or `~/.claude/wiki-config.json`. Fall back to the topic's `CLAUDE.md` import path. |

There is **no project-type gate** (the research/development split was removed 2026-06-15 — every project's wiki does both). `/wrap-up` is for capturing *our own* work into `project/` + the session journal; `/wiki-update` is for ingesting *external* sources into `research/`. If a `/wrap-up` session turns out to be pure research with no durable project work, still write the session-journal entry (Step 0), then point the user at `/wiki-update` for the source itself.

## The flow

### Step 0 — Update the session journal (ALWAYS — every `/wrap-up`)

This runs on **every** wrap-up, before anything else, so the "what we did" record builds up *as you go* instead of being reconstructed once at the end. One journal entry **per session**, upserted.

**Path**: `<vault>/<project>/wiki/sessions/<persona>/<YYYY-MM>/<YYYY-MM-DD>-<session-id>.md`
- `persona` — the active persona if the project uses them (read from `active-context.md` / the user's sign-off tag); otherwise default to `main`.
- `session-id` — a stable id for THIS Claude Code session. Use the session UUID from the transcript path if available; else a `<YYYY-MM-DD>-<short-slug>` derived on the first wrap-up. The point is that repeat wrap-ups in the same session resolve to the SAME file.

**Upsert logic**:
1. Resolve today's `<YYYY-MM>` folder under `sessions/<persona>/`. Glob it and look for an entry whose frontmatter `session_id:` matches the current session. (If you created it earlier this conversation, you already know the path.)
2. **If it exists** → append a new dated block under `## Updates` with what's happened *since the last wrap-up* (don't rewrite earlier blocks — append). Refresh the `**Next:**` line.
3. **If it doesn't** → create it with the frontmatter + skeleton below, seeding `**Goal:**` and the first update block.

This entry goes **directly** to `wiki/sessions/` (NOT staged in `_inbox/proposed/`) — it's our own running log, not a curated artifact needing review.

```yaml
---
title: "Session <YYYY-MM-DD> — <persona>"
date: <YYYY-MM-DD>
session_id: <id>
persona: <persona>
type: session-journal
ingested_by: claude-code
tier: self
confidence: high
last_reviewed: <YYYY-MM-DD>
review_after: <YYYY-MM-DD+90>
tags: [<project-name>, session-journal, <persona>]
---

# Session <YYYY-MM-DD> — <persona>

**Goal:** <one line — what this session is trying to achieve; edit if it shifts>
**Next:** <the single most important next action; refreshed every wrap-up>

## Updates

### Update <N> — <YYYY-MM-DD HH:MM if known, else just the sequence> — <short summary>
- **Did:** <what happened since the last wrap-up>
- **Decisions:** <any; link the project/decisions/ entries filed below>
- **Files:** <key paths touched>
- **Open:** <anything unresolved>
```

(For `HH:MM`, run `date '+%H:%M'` if you need a real clock — the model doesn't have one otherwise. If unavailable, just use the sequence number `Update 1`, `Update 2`, …)

The journal is the chronological "what we did"; the `project/` entries below (Steps 1-3) are the distilled durable knowledge extracted from it. Both, every wrap-up.

### Step 1 — Scan the session for durable work

Look at: the conversation in this session, files modified, recent commits, any session scratchpad at `<vault>/<project>/_inbox/sessions/<session-id>/`.

**Gracefully handle empty / brand-new repos.** `git log` exits 128 ("does not have any commits yet") on a freshly-scaffolded project, and `git diff HEAD~N` won't have anchors to compare against. Don't treat those as failures — they're the most common first-wrap-up state. Fall back to:
- `git status --short` (works on a zero-commit repo) for the file list
- `git diff --no-index /dev/null <file>` if you need diff content for a never-committed file
- Or just read the files directly via the Read tool and synthesize from the conversation context — the conversation is the primary source anyway; git is supplementary.

If you see "does not have any commits yet" or "fatal: ambiguous argument 'HEAD'" — treat as "everything is new", not as an error.

Identify candidates by category. Each candidate gets ONE row in a proposal table.

| Category | What it captures | Example |
|---|---|---|
| **Component** | A new module, class, function, or system part — what it does, how it fits | "New `OAuthTokenCache` class — handles scope mismatch via re-auth, caches at `~/.config/<app>/token.json`" |
| **Decision** | A choice between alternatives with the *why* preserved (ADR-style) | "Chose `BooleanOptionalAction` default-True over `store_true` for `--move-handled` because…" |
| **Architecture** | A system-level structural rule that constrains future work | "Vault stays in workflows-core, projects link via `~/.claude/wiki-config.json`" |
| **Pattern** | A reusable approach the project will follow elsewhere | "URL-dedup at the producer (queue-add) prevents stale-requeue at the consumer" |
| **Troubleshooting** | A bug or issue + root cause + fix (so future-you doesn't re-debug it) | "OAuth pop-up every scan = cached token scope < requested scope; force full-scope re-auth once" |

### Step 2 — Present the proposal table

Show the user:

```
I see the following durable work from this session:

| # | Category | Proposed title | Target folder |
|---|---|---|---|
| 1 | troubleshooting | OAuth re-prompt on every Drive scan — root cause + fix | wiki/project/troubleshooting/ |
| 2 | decision | --move-handled default-ON for wiki-fetch-drive-folder | wiki/project/decisions/ |
| 3 | pattern | URL-dedup at producer (wiki-list-add) — defense-in-depth against stale-requeue | wiki/project/patterns/ |

**Bulk accept (default):** `go` / `all` / `keep all` / `roll them up` — files every proposed entry as-is.
**Bulk reject:** `none` / `drop all` / `skip` — files nothing.
**Per-item override:** `1 keep, 2 drop, 3 reframe to <new title>` — escape hatch for surgical control.

Show the bulk-accept option first so a one-word `go` is the obvious path. Per-item syntax is the escape hatch, not the default.
```

Wait for explicit confirmation. The user MUST get to veto before any wiki entry is filed — but a one-word `go` is a valid veto-not-exercised.

### Step 3 — File each kept candidate to `_inbox/proposed/`

Same staging discipline as `/wiki-update` — entries go to `<vault>/<project>/_inbox/proposed/<slug>.md`, NOT directly to `wiki/`. Promotion via `/wiki-promote` moves each to its target folder `wiki/project/<category>/` (components, decisions, architecture, patterns, troubleshooting). The metadata sidecar records `target_folder: project/<category>`.

Each entry has:

```yaml
---
title: "<descriptive title>"
date: <YYYY-MM-DD>
source_url: "internal://session/<session-id-or-date>"
raw_path: "raw/sessions/<YYYY-MM-DD>-<session-slug>.md"   # OR "(none — self-authored)"
ingested_by: claude-code
origin: wrap-up      # who filed this entry: wrap-up | inline | wiki-update
tier: self
confidence: <high|medium|low>
last_reviewed: <YYYY-MM-DD>
review_after: <YYYY-MM-DD+90>
category: <component|decision|architecture|pattern|troubleshooting>
tags: [<project-name>, <category>, <topic-tags>]
---
```

Body has these sections (skip any that don't apply):

1. **TL;DR** — 1-2 sentence summary
2. **What** — the durable artifact (component description, decision text, pattern definition, bug root cause)
3. **Why** — the rationale, including what was considered and rejected
4. **How** — code references, file paths, commit hashes
5. **Caveats / open questions** — anything still uncertain
6. **Related** — links to other wiki entries this connects to

### Step 4 — Optional: write a session-transcript snapshot to `raw/sessions/`

If the session is substantively rich (multi-hour, multi-component, or contains reasoning that would be hard to re-derive), write a markdown snapshot to `<vault>/<project>/raw/sessions/<YYYY-MM-DD>-<session-slug>.md` capturing:

- Date + session ID
- Files touched (from `git diff --name-only`)
- The 1-paragraph "what we did" summary
- Key passages from the conversation (NOT the full transcript) — just the load-bearing bits

This is the **raw-is-sacred** anchor: each session-derived wiki entry references this snapshot in its `raw_path`, so deletion at the wiki layer is always reversible.

If the session is light (single fix, one decision), set `raw_path: "(none — self-authored)"` and skip the snapshot.

### Step 5 — Summary report

Show the user:

```
Wrapped up:
  Session journal updated: wiki/sessions/main/2026-05/2026-05-12-<session-id>.md  (Update 3)
  3 entries staged to _inbox/proposed/ (→ wiki/project/<category>/ on promote):
  - troubleshooting/oauth-re-prompt-root-cause-2026-05-12.md
  - decisions/move-handled-default-on-2026-05-12.md
  - patterns/url-dedup-at-producer-2026-05-12.md

Raw snapshot: raw/sessions/2026-05-12-drive-cleanup-session.md
Next: run /wiki-promote --review to approve & promote the project entries.
```

## Slug naming

Same convention as wiki-update entries: `<descriptive-short-slug>-<YYYY-MM-DD>.md`. The date matters — wiki entries are session-anchored.

For categories that should be ADR-style (Architecture Decision Records), prefix with the next available number: `0042-decision-slug-2026-05-12.md`.

## Tier and confidence

- **tier: self** — always. These are first-person work product, not external sources.
- **confidence**:
  - `high` — settled decision, working code, validated pattern
  - `medium` — provisional design, working but not yet stress-tested
  - `low` — in-flight thinking, needs revisit. Set a near `review_after` (~14 days).

## When to NOT wrap up

If the user types `/wrap-up` but the session was:

- **Pure research / ingest work** — say so, suggest `/wiki-update` or `/wiki-cycle`.
- **Pure exploration with no settled output** — say so, suggest waiting until something concrete emerges.
- **A failed direction** — wrap up the *learning* (troubleshooting entry: "we tried X, it didn't work because Y") but be explicit that nothing was built.

Never silently file empty / thin entries. Better to say "nothing here merits a wiki entry yet" than to clutter the wiki.

## Cross-link to the wider system

- Reciprocate-backlinks runs automatically after entries are filed (same as wiki-update).
- Per-folder `_INDEX.md` regenerates.
- `_MAP.md` regenerates if root-level entries were added.

## Don't

- Don't auto-file without the user's explicit confirmation of the proposal table.
- Don't write the conversation transcript into the wiki — distill, don't dump.
- Don't promote directly to `wiki/` — always stage in `_inbox/proposed/` and let the user promote via `/wiki-promote`.
- Don't run `/wrap-up` on the agentic-design topic — that's research; use `/wiki-update` instead.
- Don't write to `~/.claude/projects/*/memory/MEMORY.md` (that's auto-memory's job, different layer). `/wrap-up` writes to the project wiki.

## After install

When this skill ships as part of `/new-wiki`'s standard bundle (Phase A), it lives at `~/.claude/skills/wrap-up/SKILL.md` globally. Project-local overrides at `<project>/.claude/skills/wrap-up/SKILL.md` if a project needs different folder taxonomy.

## Source

Authored 2026-05-12 in workflows-core during the session that designed the install pattern. Validated by dog-fooding on workflows-core itself before being part of the `/new-wiki` bundle.
