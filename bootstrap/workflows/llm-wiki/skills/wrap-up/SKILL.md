---
name: wrap-up
description: Crystallize the current session's work into the project wiki AND refresh the working-memory dashboards. ALWAYS (1) upserts a running per-session journal at wiki/sessions/<persona>/<YYYY-MM>/ so the "what we did" record builds as you go, (2) refreshes the mutable working-memory dashboards — sessions/<persona>/handoff.md + task.md + sessions/active-context.md (the resume pointer; the memory-bank replacement), and (3) extracts durable knowledge — components/decisions/patterns/bugs — staged to _inbox/proposed/ then promoted to wiki/project/<category>/ (auto-promote configurable per-notebook via `wrap_up_auto_promote`). This is the ONE session-close command — it absorbs the retired /upd-docs. For ingesting EXTERNAL sources (URLs/papers/videos) use /wiki-update instead. Use when the user says "wrap up", "wrap-up", "/wrap-up", "wrap this session", "document what we did", "crystallize this session", "save this work", "save progress", "save state", "update docs", "upd-docs".
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
2. **If it exists** → append a new dated block under `## Updates` with what's happened *since the last wrap-up* (don't rewrite earlier blocks — append). Refresh the `**Next:**` line, keeping it self-sufficient per the skeleton (exact files to read + steps).
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
**Next:** <the single most important next action — MUST be self-sufficient for a COLD START (fresh,
non-resume session): name the exact files to READ (full paths) AND the concrete STEPS. Never just
"build X" — always "read A, B, C → then do 1, 2, 3" so the next session continues with ZERO
inference. Refreshed every wrap-up.>

## Updates

### Update <N> — <YYYY-MM-DD HH:MM if known, else just the sequence> — <short summary>
- **Did:** <what happened since the last wrap-up>
- **Decisions:** <any; link the project/decisions/ entries filed below>
- **Files:** <key paths touched>
- **Open:** <anything unresolved>
```

(For `HH:MM`, run `date '+%H:%M'` if you need a real clock — the model doesn't have one otherwise. If unavailable, just use the sequence number `Update 1`, `Update 2`, …)

The journal is the chronological "what we did"; the `project/` entries below (Steps 1-3) are the distilled durable knowledge extracted from it. Both, every wrap-up.

### Step 0.5 — Refresh the working-memory dashboards (ALWAYS — every `/wrap-up`)

Right after the journal, refresh the **working-memory** tier of `sessions/` — the mutable dashboards that answer "where do I resume." These are the direct replacement for the old `memory-bank/short-term/_personas/*` + `active-context.md`, so `/wrap-up` keeps them current on every run. (This work used to be a separate `/upd-docs` skill; it was folded in here so session-close is a single command — a wrap-up must never leave the resume pointer stale.)

All three are **overwrite-in-place**, written **directly** to `sessions/` (NOT staged in `_inbox/proposed/`), and exempt from the curated pipeline (lint/map/index/reciprocate/refresh skip `sessions/` like `_inbox/`; qmd still indexes it). Resolve `<persona>` (same as Step 0) and create the folder on demand — a new persona just works, there is no fixed list:

```bash
mkdir -p <wiki_dir>/sessions/<persona>
```

**(a) `sessions/<persona>/handoff.md` — OVERWRITE** with a full resume dump. This is survival insurance and the stable-path resume pointer: a cold-start session reads THIS (not the newest dated journal, which it would have to glob for) to know where to pick up.

```
HANDOFF — <PERSONA> — <DATE>
GOAL: [one sentence — what to do next]
WORK COMPLETED (this session): [what was done, file paths, key decisions]
CURRENT STATE: [what's running / broken / blocked]
PENDING: [planned-but-not-done, blockers]
KEY FILES: [path — role] (max 10)
CONTEXT FOR CONTINUATION: [what the next session needs; gotchas; references]
```

First person; workspace-relative paths; no secrets; it's a snapshot, not a log — overwrite.

**(b) `sessions/<persona>/task.md` — READ first, then update in place** (don't blind-overwrite):

```
## NOW
[Single thing being actively worked — or "Awaiting next task"]

## QUEUE
1. [Next priority]
2. [After that]
3. [Backlog]
```

Promote the next QUEUE item to NOW as work completes.

**(c) `sessions/active-context.md` — update ONLY your persona's lines** (Status / Recent / Next) in the cross-persona dashboard. Do NOT touch other personas' sections; do NOT rewrite the file. Skip if your section already describes what you're doing.

These restate the same `Goal` / `Next` / completed info you just wrote into the journal — but in the **stable-path** dashboards, so a fresh session finds the resume pointer without hunting through dated journals. There is **no `completed.md`** — the journal's work-completed record covers it; never create one.

**First-run note:** the very first `/wrap-up` after this was folded in (or for a brand-new persona) has to author `handoff.md` + `task.md` from scratch, so it writes a bit more than a normal incremental refresh. That's expected — subsequent runs just update in place.

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

Same staging discipline as `/wiki-update` — entries go to `<topic_root>/_inbox/proposed/<slug>.md`.
**`<topic_root>` is a SIBLING of `wiki/`, NOT nested inside it** — i.e.
`<topic_root>/_inbox/proposed/`, never `<topic_root>/wiki/_inbox/proposed/`. To resolve
`<topic_root>`: read `<cwd>/.claude/wiki-config.json` for `notebook` + `registry`; look up
`notebooks[<name>]` in the registry (`.root`, or `.vault_root` + `.topic`) — that resolved path
IS `<topic_root>` (the wiki itself lives one level down, at `<topic_root>/wiki/`). Get this wrong
and `/wiki-promote` reports "nothing in `_inbox/proposed/` to promote" even though the file exists
(it's looking one level up from where you put it).

Promotion via `/wiki-promote` moves each entry to its target folder `wiki/project/<category>/`
(components, decisions, architecture, patterns, troubleshooting) — **but only if you write the
sidecar in this step**. `wiki-promote.py` reads the target folder from a
`<slug>.proposed_metadata.json` sidecar next to the `.md` file, NOT from the `.md`'s own
frontmatter `category:` field — an entry staged without a sidecar silently promotes to the **wiki
root** instead of `project/<category>/`. Write both files:

```json
// <slug>.proposed_metadata.json — same folder as the .md, same slug stem
{
  "target_folder": "project/<category>",
  "title": "<same as the .md's title>",
  "tier": "self",
  "confidence": "<high|medium|low>",
  "inbound_candidates": [],
  "suggested_backlinks": [],
  "created": "<ISO-8601 local timestamp with UTC offset>"
}
```

(`inbound_candidates`/`suggested_backlinks` can stay empty arrays — `/wiki-update`'s ingest-time
mention-scan populates them for external sources; `/wrap-up` entries don't need it unless you've
already identified specific files to backlink.)

Each `.md` entry has:

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
  Working memory refreshed: sessions/main/{handoff,task}.md + active-context.md
  3 entries staged to _inbox/proposed/ (→ wiki/project/<category>/ on promote):
  - troubleshooting/oauth-re-prompt-root-cause-2026-05-12.md
  - decisions/move-handled-default-on-2026-05-12.md
  - patterns/url-dedup-at-producer-2026-05-12.md

Raw snapshot: raw/sessions/2026-05-12-drive-cleanup-session.md
```

Then go straight to Step 6 — don't end on "run /wiki-promote later"; offer to promote now.

### Step 6 — Offer to promote (inline)

Staging isn't the finish line — an entry in `_inbox/proposed/` does nothing until it's promoted into `wiki/`. The old two-step (`/wrap-up` then separately `/wiki-promote`) was easy to forget. So offer promotion right here.

**Mode** is `wrap_up_auto_promote`, a per-notebook setting. Resolve it in this order:
1. **Registry (canonical home)** — read `<cwd>/.claude/wiki-config.json` for `notebook` + `registry`, open the registry (`linked-notebooks.json`), find the notebook's entry; if it's an object with `wrap_up_auto_promote`, use that. (This is where `/new-wiki` writes it, so it travels with the notebook.)
2. **Project config fallback** — for a legacy in-project wiki with no registry, read `wrap_up_auto_promote` from `<cwd>/.claude/wiki-config.json` directly.
3. **Default** — `ask` if neither is set.

To CHANGE it: edit the notebook's entry in `linked-notebooks.json` (registry notebooks) or the project's `wiki-config.json` (in-project), or just ask the agent.

| `wrap_up_auto_promote` | Behaviour |
|---|---|
| `ask` (default / unset) | Show the prompt below and wait for the user. |
| `true` | Promote ALL staged entries inline automatically — no prompt. Report what moved. |
| `false` | Skip — leave entries staged, print the manual `/wiki-promote` pointer, done. |

**Skip Step 6 entirely if nothing was staged** (e.g. journal-only wrap-up).

**The prompt (`ask` mode):**

```
4 entries staged to _inbox/proposed/. Promote them now?
  1. reading-list-includes-mechanism-2026-06-20.md      → project/architecture/
  2. agents-library-pre-submodule-staging-2026-06-20.md → project/architecture/
  3. agent-to-mdc-py-component-2026-06-20.md            → project/components/
  4. msys2-spurious-root-file-2026-06-20.md             → project/troubleshooting/

Promote all now?  (yes / no / pick numbers e.g. "1 3")
```

- **yes / all** → promote every staged entry.
- **no** → leave them staged; print `Run /wiki-promote --review when you're ready.` Done.
- **pick numbers** (`1 3`) → promote only those; leave the rest in `_inbox/proposed/`.

**Promote mechanism — reuse the promote script, don't reimplement** move/sidecar/backlink logic:

- All: `python <wiki-scripts>/wiki-promote.py --auto`
- Subset: one call per pick — `python <wiki-scripts>/wiki-promote.py --slug <slug> --auto`

(`<wiki-scripts>` = `~/.claude/wiki-scripts` for global installs, or `<project>/.claude/wiki-scripts` if bundled. Read the path from `scripts_installed_at` in wiki-config.json, else default to `~/.claude/wiki-scripts`.) This moves each entry to its `target_folder`, wires backlinks, and regenerates `_INDEX.md` + `_MAP.md`.

**Then commit** the promoted result — **scope the add to the notebook path** so unrelated in-flight work isn't swept in (a `git add -A` here will bundle another session's uncommitted files):

```bash
git -C <notebook-repo> add <notebook-root>/        # NOT add -A
git -C <notebook-repo> commit -m "wiki(<notebook>): wrap-up <YYYY-MM-DD> — promote N session entries"
```

If the notebook repo has unrelated uncommitted changes, add only the wrapped/promoted paths. Don't push (that's the user's call).

**Offer to remember (`ask` mode only):** after a clean all-`yes` or all-`no`, offer ONCE:

> Make this the default for **<notebook>**? I can set `wrap_up_auto_promote: <true|false>` in `.claude/wiki-config.json` so future wrap-ups skip this prompt.

Only write the key if they say yes. Never set it silently.

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

## The three memory tiers this writes (`/upd-docs` is retired — folded in here)

`/wrap-up` is the single session-close command. It writes all of `sessions/` plus the durable layer:

| Tier | Files | Lifecycle | Step |
|---|---|---|---|
| **Working memory** | `sessions/<persona>/{handoff,task}.md` + `sessions/active-context.md` | MUTABLE — overwrite in place | Step 0.5 |
| **Episodic** | `sessions/<persona>/<YYYY-MM>/<date>-<sid>.md` (the journal) | APPEND — one entry per session | Step 0 |
| **Semantic (durable)** | `project/<category>/*` (staged → promoted) | curated, reviewed | Steps 1-6 |

The working-memory dashboards are the direct replacement for `memory-bank/short-term/_personas/*` + `active-context.md`. There used to be a separate `/upd-docs` skill for the working tier; it was **retired** and folded into Step 0.5 so a wrap-up always leaves the resume pointer fresh (a wrap-up that updated the journal but left `handoff.md` stale was the failure mode that motivated the merge). The journal's work-completed section IS the completed record — there is **no** `completed.md`.

If you just want the fast working-memory refresh without the durable-extraction proposal flow, that's fine: run `/wrap-up` and answer `none` at the proposal table (Step 2) — Steps 0 + 0.5 still run (journal + dashboards), and nothing gets staged.

## Cross-link to the wider system

- Reciprocate-backlinks runs automatically after entries are filed (same as wiki-update).
- Per-folder `_INDEX.md` regenerates.
- `_MAP.md` regenerates if root-level entries were added.

## Don't

- Don't auto-file without the user's explicit confirmation of the proposal table.
- Don't write the conversation transcript into the wiki — distill, don't dump.
- Don't SKIP staging — entries always land in `_inbox/proposed/` first (Step 3). Promotion happens only in Step 6, gated by the user's answer (`ask` mode) or an explicit `wrap_up_auto_promote: true` they configured. Never silently promote when the mode is `ask`.
- Don't run `/wrap-up` on the agentic-design topic — that's research; use `/wiki-update` instead.
- Don't write to `~/.claude/projects/*/memory/MEMORY.md` (that's auto-memory's job, different layer). `/wrap-up` writes to the project wiki.

## After install

When this skill ships as part of `/new-wiki`'s standard bundle (Phase A), it lives at `~/.claude/skills/wrap-up/SKILL.md` globally. Project-local overrides at `<project>/.claude/skills/wrap-up/SKILL.md` if a project needs different folder taxonomy.

## Source

Authored 2026-05-12 in workflows-core during the session that designed the install pattern. Validated by dog-fooding on workflows-core itself before being part of the `/new-wiki` bundle.
