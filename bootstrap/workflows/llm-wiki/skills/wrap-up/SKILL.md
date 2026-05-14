---
name: wrap-up
description: Crystallize the current session's durable work into wiki entries for a development project. Identifies components built, decisions made, patterns established, bugs investigated, and files them to the project's wiki staging area for review and promotion. Use when the user says "wrap up", "wrap-up", "/wrap-up", "wrap this session", "document what we did", "crystallize this session", "save this work".
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
| Vault root | From `~/.claude/wiki-config.json` (`vault_root`). Fall back to the topic's `CLAUDE.md` import path. |
| Project type | From the wiki topic's `README.md` frontmatter (`project_type: development` vs `research`). |

If `project_type: research` — refuse and point user at `/wiki-update`.

## The flow

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
| 1 | troubleshooting | OAuth re-prompt on every Drive scan — root cause + fix | wiki/troubleshooting/ |
| 2 | decision | --move-handled default-ON for wiki-fetch-drive-folder | wiki/decisions/ |
| 3 | pattern | URL-dedup at producer (wiki-list-add) — defense-in-depth against stale-requeue | wiki/patterns/ |

**Bulk accept (default):** `go` / `all` / `keep all` / `roll them up` — files every proposed entry as-is.
**Bulk reject:** `none` / `drop all` / `skip` — files nothing.
**Per-item override:** `1 keep, 2 drop, 3 reframe to <new title>` — escape hatch for surgical control.

Show the bulk-accept option first so a one-word `go` is the obvious path. Per-item syntax is the escape hatch, not the default.
```

Wait for explicit confirmation. The user MUST get to veto before any wiki entry is filed — but a one-word `go` is a valid veto-not-exercised.

### Step 3 — File each kept candidate to `_inbox/proposed/`

Same staging discipline as `/wiki-update` — entries go to `<vault>/<project>/_inbox/proposed/<folder>/<slug>.md`, NOT directly to `wiki/`. Promotion happens via `/wiki-promote`.

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
project_type: development
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
  3 entries filed to _inbox/proposed/<project>/
  - troubleshooting/oauth-re-prompt-root-cause-2026-05-12.md
  - decisions/move-handled-default-on-2026-05-12.md
  - patterns/url-dedup-at-producer-2026-05-12.md

Raw snapshot: raw/sessions/2026-05-12-drive-cleanup-session.md
Next: run /wiki-promote --review to approve & promote.
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
