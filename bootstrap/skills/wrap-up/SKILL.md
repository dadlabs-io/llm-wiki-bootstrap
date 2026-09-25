---
name: wrap-up
description: "Crystallize the current session's work into the project wiki AND refresh the working-memory dashboards. ALWAYS (1) upserts a running per-session journal at wiki/sessions/<persona>/<YYYY-MM>/ so the \"what we did\" record builds as you go, (2) refreshes the mutable working-memory dashboards — sessions/<persona>/handoff.md + task.md + sessions/active-context.md (the resume pointer; the memory-bank replacement), and (3) extracts durable knowledge — components/decisions/patterns/bugs — staged to _inbox/proposed/ then promoted to wiki/project/<category>/ (gated by two per-notebook booleans: `confirm_before_create` for Step 2's filing decision, `confirm_before_promote` for Step 6's promotion decision). With --auto-commit it commits the session's work at the end, with --auto-push it also pushes, and every wrap-up ends on one closing line (\"WRAP-UP COMPLETE: committed and pushed\" or what is left). This is the ONE session-close command — it absorbs the retired /upd-docs. For ingesting EXTERNAL sources (URLs/papers/videos) use /wiki-update instead. Use when the user says \"wrap up\", \"wrap-up\", \"/wrap-up\", \"wrap this session\", \"document what we did\", \"crystallize this session\", \"save this work\", \"save progress\", \"save state\", \"update docs\", \"upd-docs\", \"wrap up and commit\", \"wrap up and push\"."
last_reviewed: 2026-09-24
review_after: 2026-12-24
reviewed_for_model: claude-opus-5-5
---

# /wrap-up

End-of-session distillation. Read the conversation and the recent file changes, then write the *why* and the *what* — never the transcript. `/wrap-up` turns "we just spent two hours figuring out X" into an entry next-session-you can read in 60 seconds.

**This is for our own work.** External sources (URLs, papers, videos) belong to `/wiki-update` or `/wiki-cycle`. There is no project-type gate: every project's wiki does both. If a session turns out to be pure research, still write the journal (Step 0), then point the user at `/wiki-update` for the source itself.

**Don't wiki a typo fix, a one-line edit or a dependency bump**, and don't file half-baked thinking — either wait until it is settled, or file it with `confidence: low` and a near `review_after`.

**Flags:** `/wrap-up --auto-commit` commits the session's work when the wrap-up is done; `/wrap-up --auto-push` commits and pushes (Step 7). Without either, nothing new is committed beyond Step 6's promote commit, and nothing is pushed. Every wrap-up, with a flag or without, ends on one closing line (Step 7) saying whether it is safe to close the window.

## Required context

| Field | How to get it |
|---|---|
| Project / notebook name | `<cwd>/.claude/wiki-config.json` (`notebook`), else the project's `CLAUDE.md`, else ask. |
| Where the notebook lives | The registry named by that config (`registry` → `linked-notebooks.json`), else `~/.claude/wiki-config.json`. |
| `<persona>` | The config's `persona`, else the active persona in `active-context.md`, else `main`. Create the folder on demand — a new persona just works, there is no fixed list. |

**Two per-notebook booleans gate this skill**, both default `true`, both resolved the same way: the notebook's entry in the registry (`linked-notebooks.json`, where `/new-wiki` writes them) → the project's `wiki-config.json` → `true`.

- `confirm_before_create` — Step 2, before anything is filed.
- `confirm_before_promote` — Step 6, before anything is promoted.

To change either: edit the notebook's registry entry (or the project's `wiki-config.json`), or ask the user. A notebook still carrying the pre-2026-07-20 name `wrap_up_auto_promote` needs that key renamed to `confirm_before_promote` (`ask` → `true`, `true` → `false`).

## The flow

Steps 0 and 0.5 run on **every** wrap-up, and Step 7's closing line ends every one. Steps 1–6 depend on what the session produced; Step 7's commit and push depend on the flags.

### Step 0 — Update the session journal (ALWAYS)

One journal entry **per session**, upserted, so the record builds as you go instead of being reconstructed at the end.

**Path**: `<topic_root>/wiki/sessions/<persona>/<YYYY-MM>/<YYYY-MM-DD>-<session-id>.md`, where `session-id` is this session's UUID from the transcript path, else a `<YYYY-MM-DD>-<short-slug>` you derive on the first wrap-up. The point is that repeat wrap-ups in one session resolve to the SAME file.

1. Glob today's `<YYYY-MM>` folder for an entry whose frontmatter `session_id:` matches this session.
2. **Found** → append a new dated block under `## Updates` with what happened *since the last wrap-up*. Never rewrite an earlier block. Refresh `**Next:**`.
3. **Not found** → create it from the skeleton, seeding `**Goal:**` and the first update block.

This goes **directly** to `wiki/sessions/` — never staged in `_inbox/proposed/`. It is our own running log, not a curated artifact.

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
**Next:** <the single most important next action, self-sufficient for a COLD START: the exact
files to READ (full paths) AND the concrete STEPS. Never just "build X" — always "read A, B, C →
then do 1, 2, 3", so the next session continues with ZERO inference. Refreshed every wrap-up.>

## Updates

### Update <N> — <HH:MM if known, else just the sequence> — <short summary>
- **Did:** <what happened since the last wrap-up>
- **Decisions:** <any; link the project/decisions/ entries filed below>
- **Files:** <key paths touched>
- **Open:** <anything unresolved>
```

(`date '+%H:%M'` if you want a real clock — you have none otherwise. Otherwise just `Update 1`, `Update 2`, …)

### Step 0.5 — Refresh the working-memory dashboards (ALWAYS)

The three mutable dashboards that answer "where do I resume". All are written **directly** to `sessions/` (never staged) and are exempt from the curated pipeline — lint, map, index, reciprocate and refresh skip `sessions/` like `_inbox/`; qmd still indexes it. `mkdir -p <wiki>/sessions/<persona>` as needed.

A wrap-up must never leave the resume pointer stale: a fresh session reads these, not the dated journals, which it would have to glob for.

**(a) `sessions/<persona>/handoff.md` — OVERWRITE.** A full resume dump: first person, workspace-relative paths, no secrets. A snapshot, not a log.

```
HANDOFF — <PERSONA> — <DATE>
GOAL: [one sentence — what to do next]
WORK COMPLETED (this session): [what was done, file paths, key decisions]
CURRENT STATE: [what's running / broken / blocked]
PENDING: [planned-but-not-done, blockers]
KEY FILES: [path — role] (max 10)
CONTEXT FOR CONTINUATION: [what the next session needs; gotchas; references]
```

**(b) `sessions/<persona>/task.md` — READ first, then update in place.** Never blind-overwrite.

```
## NOW
[Single thing being actively worked — or "Awaiting next task"]

## QUEUE
1. [Next priority]
2. [After that]
3. [Backlog]
```

Promote the next QUEUE item to NOW as work completes.

**When `task.md` starts with `## At a glance`** (the `/task-list` block, above NOW), keep it current **through the script, never by hand**: `wiki-tasks.py done <N> --next "<what happened>"` for each task finished this session, `add "<task>" --owner <section>` for work taken on or left for the user, `set <N> --status <s> --next "<text>"` where one moved.

```bash
python {{WIKI_SCRIPTS_DIR}}/wiki-tasks.py done <N> --next "<what happened>"
```

**Never `remove`.** A task leaves the list only on the user's word. Name every task you marked done in Step 5's summary and ask there whether to remove them — the ask belongs in the report you are already writing, not left to memory. A `task.md` without the block is left without one.

**(c) `sessions/active-context.md` — update ONLY your persona's lines** (Status / Recent / Next) in this cross-persona dashboard. Do NOT touch another persona's section; do NOT rewrite the file. Skip only if your section already describes what you are doing.

**Create it if missing.** Nothing else seeds this file, and a cold start's resume read looks at it first, so the first wrap-up of a project writes it: a title (`# Active context — <project>`), a line saying each persona edits only its own section, then `## <persona>` with Status / Recent / Next. A missing file is never a reason to skip (c).

There is **no `completed.md`** — the journal's work-completed record covers it. Never create one.

(The first wrap-up for a project or a new persona authors all three from scratch, so it writes more than a later incremental refresh. That is expected.)

### Step 1 — Scan the session for durable work

Look at the conversation, the files modified, recent commits, and any scratchpad at `<topic_root>/_inbox/sessions/<session-id>/`.

**A brand-new repo is normal, not a failure.** `git log` exits 128 on a repo with no commits and `git diff HEAD~N` has no anchor — the most common first-wrap-up state. Fall back to `git status --short`, or just read the files. The conversation is the primary source anyway; git is supplementary. "does not have any commits yet" or "fatal: ambiguous argument 'HEAD'" means "everything is new".

One row per candidate, by category:

| Category | What it captures |
|---|---|
| **Component** | A new module, class, function or system part — what it does, how it fits |
| **Decision** | A choice between alternatives with the *why* preserved (ADR-style) |
| **Architecture** | A system-level structural rule that constrains future work |
| **Pattern** | A reusable approach the project will follow elsewhere |
| **Troubleshooting** | A bug + root cause + fix, so future-you doesn't re-debug it |

### Step 2 — Present the proposal table

```
I see the following durable work from this session:

| # | Category | Proposed title | Target folder |
|---|---|---|---|
| 1 | troubleshooting | OAuth re-prompt on every Drive scan — root cause + fix | wiki/project/troubleshooting/ |
| 2 | decision | --move-handled default-ON for wiki-fetch-drive-folder | wiki/project/decisions/ |

**Bulk accept (default):** `go` / `all` / `keep all` / `roll them up`
**Bulk reject:** `none` / `drop all` / `skip`
**Per-item override:** `1 keep, 2 drop, 3 reframe to <new title>`
```

Show bulk-accept first, so a one-word `go` is the obvious path; per-item is the escape hatch, not the default.

- **`confirm_before_create: true`** — wait for an explicit answer. The user MUST get to veto before anything is filed; a one-word `go` is a veto not exercised.
- **`confirm_before_create: false`** — still print the table (you always see what was filed, even unattended), but don't wait: treat every candidate as kept and go to Step 3.

### Step 3 — File each kept candidate to `_inbox/proposed/`

Same staging discipline as `/wiki-update`: entries go to `<topic_root>/_inbox/proposed/<slug>.md`.

**`<topic_root>` is a SIBLING of `wiki/`, not nested inside it.** Resolve it from the registry entry (`.root`, or `.vault_root` + `.topic`); the wiki itself is one level down at `<topic_root>/wiki/`. Get this wrong and `/wiki-promote` reports "nothing to promote" while the file sits there.

**Write the sidecar or the entry will not promote.** `wiki-promote.py` reads the target folder from the sidecar, NOT from the `.md`'s `category:` field; an entry staged without a readable sidecar naming a `target_folder` is **held back** (`HELD`, exit 4).

```json
// <slug>.proposed_metadata.json — same folder, same slug stem
{
  "target_folder": "project/components",
  "title": "<same as the .md's title>",
  "tier": "self",
  "confidence": "<high|medium|low>",
  "inbound_candidates": [],
  "suggested_backlinks": [],
  "created": "<ISO-8601 local timestamp with UTC offset>"
}
```

**`target_folder` is `project/` followed by the plural folder name** — `project/components`, `project/decisions`, `project/architecture`, `project/patterns`, `project/troubleshooting`. Never the bare folder name, and never the singular `category:` word. (Three entries landed in phantom `project/component/` folders that way; the script maps singular → plural since 2026-09-13, but write the real name.) The two array fields can stay empty: `/wiki-update` fills them for external sources.

```yaml
---
title: "<descriptive title>"
date: <YYYY-MM-DD>
source_url: "internal://session/<session-id-or-date>"
raw_path: "raw/sessions/<YYYY-MM-DD>-<session-slug>.md"   # only when Step 4 saved a snapshot; otherwise omit the line
ingested_by: claude-code
origin: wrap-up
tier: self
confidence: <high|medium|low>
last_reviewed: <YYYY-MM-DD>
review_after: <YYYY-MM-DD+90>
category: <component|decision|architecture|pattern|troubleshooting>
tags: [<project-name>, <category>, <topic-tags>]
---
```

Body, skipping any section that doesn't apply: **TL;DR** (1–2 sentences) → **What** (the durable artifact) → **Why** (the rationale, including what was rejected) → **How** (paths, commits) → **Caveats / open questions** → **Related** (links to other entries).

### Step 4 — Optional: a session snapshot in `raw/sessions/`

If the session was substantively rich (multi-hour, multi-component, or reasoning that would be hard to re-derive), write `<topic_root>/raw/sessions/<YYYY-MM-DD>-<session-slug>.md`: date and session id, files touched, the one-paragraph "what we did", and the load-bearing passages — not the full transcript. Each entry then points at it via `raw_path`, so deletion at the wiki layer stays reversible.

If the session was light, skip it and **omit `raw_path`** — `tier: self` already says the entry is self-authored.

### Step 5 — Summary report

```
Wrapped up:
  Session journal updated: wiki/sessions/main/2026-05/2026-05-12-<session-id>.md  (Update 3)
  Working memory refreshed: sessions/main/{handoff,task}.md + active-context.md
  Task list: #1 done, #4 added — remove the done one? (your call)
  3 entries staged to _inbox/proposed/ (→ wiki/project/<category>/ on promote):
  - troubleshooting/oauth-re-prompt-root-cause-2026-05-12.md
  - decisions/move-handled-default-on-2026-05-12.md

Raw snapshot: raw/sessions/2026-05-12-drive-cleanup-session.md
```

Include the task-list line whenever the list has an At a glance block: it is where the "remove the done ones?" question gets asked. Then go straight to Step 6 — never end on "run /wiki-promote later".

### Step 6 — Offer to promote (inline)

An entry in `_inbox/proposed/` does nothing until it is promoted, and the old two-step was easy to forget. **Skip this step entirely if nothing was staged.**

| `confirm_before_promote` | Behaviour |
|---|---|
| `true` (default) | Show the prompt and wait. |
| `false` | Promote all staged entries inline, no prompt. Report what moved. |

```
4 entries staged to _inbox/proposed/. Promote them now?
  1. reading-list-includes-mechanism-2026-06-20.md      → project/architecture/
  2. agent-to-mdc-py-component-2026-06-20.md            → project/components/

Promote all now?  (yes / no / pick numbers e.g. "1 3")
```

- **yes / all** → promote everything.
- **no** → leave them staged; print `Run /wiki-promote --review when you're ready.` Done.
- **pick numbers** → promote only those; leave the rest staged.

**Reuse the promote script — never reimplement move, sidecar or backlink logic.** It also wires backlinks and regenerates `_INDEX.md` and `_MAP.md`.

```bash
python <wiki-scripts>/wiki-promote.py --auto              # all
python <wiki-scripts>/wiki-promote.py --slug <slug> --auto # one per pick
```

(`<wiki-scripts>` comes from `scripts_installed_at` in wiki-config.json, else `~/.claude/wiki-scripts`.)

**Then commit, scoping the add to the notebook path** so another session's in-flight work isn't swept in:

```bash
git -C <notebook-repo> add <notebook-root>/        # NOT add -A
git -C <notebook-repo> commit -m "wiki(<notebook>): wrap-up <YYYY-MM-DD> — promote N session entries"
```

If the notebook repo has unrelated uncommitted changes, add only the paths you wrapped. Don't push — that's the user's call. **With `--auto-commit` or `--auto-push`, skip this commit**: Step 7 makes one commit per repository that covers it.

**Offer to remember (`true` mode only):** after a clean all-`yes` or all-`no`, offer ONCE to set `confirm_before_promote` for this notebook so future wrap-ups skip the prompt. Only write the key if they say yes; never set it silently.

### Step 7 — Commit, push, and the closing line (ALWAYS ends the wrap-up)

Items 1–4 run **only with `--auto-commit` or `--auto-push`**; item 5, the closing line, ends **every** wrap-up (2026-09-24, the user's ask: "so the window can be closed"). Run it after Step 6, whether or not anything was staged.

1. **Sweep strays first**: `git status --short` in each repository below; delete any zero-byte or junk file a shell redirect left (named `output`, `#`, `${...}`, a stray word). Never delete a real file.
2. **The project's repository** (the git root of the project folder): add **only the paths this session changed**, the ones the conversation and Step 1 named, by explicit path. Never `git add -A` or `git add .`. A changed or untracked file the session did not touch is left alone and named in the report. Commit: `wrap-up <YYYY-MM-DD>: <one-line summary of the session>`. Skip this repository if the session changed nothing in it.
3. **The notebook's repository** (the git root of the notebook folder): `git add <notebook-root>/` only, since other sessions may have work in the same repository, then commit: `wiki(<notebook>): wrap-up <YYYY-MM-DD> — <what was filed>`. When the wiki lives inside the project (`<project>/llm-wiki/`), this is the same repository: make one commit covering both.
4. **Push, only with `--auto-push`**, each repository that got a commit: `git push`, on its current branch, only when that branch already tracks a remote (`git rev-parse --abbrev-ref --symbolic-full-name @{u}` succeeds). **Never force, never set up a remote, never pull or rebase to make a push go through.** A push that fails (rejected, no upstream, auth) is reported with git's message and left to the user.
5. **The closing line: the LAST line of the reply, on every wrap-up**, exactly one of:
   - `✅ WRAP-UP COMPLETE: committed and pushed ✅` (`--auto-push`, every commit pushed)
   - `✅ WRAP-UP COMPLETE: committed, not pushed ✅` (`--auto-commit`)
   - `✅ WRAP-UP COMPLETE: nothing committed ✅` (no flag; Step 6's promote commit, if any, is named above it)
   - `⚠️ WRAP-UP INCOMPLETE: <what is left, e.g. "push rejected in <repo>"> ⚠️` (a commit or push failed, or the user still has to answer something)

   Nothing follows it. A wrap-up that stops to wait for an answer (Step 2's table, Step 6's prompt) has not reached Step 7 and prints no closing line.

## Slugs, tier and confidence

- **Slug**: `<descriptive-short-slug>-<YYYY-MM-DD>.md`, same as wiki-update — entries are session-anchored. ADR-style categories take the next number first: `0042-decision-slug-2026-05-12.md`.
- **tier**: always `self`. This is first-person work product.
- **confidence**: `high` settled decision, working code, validated pattern · `medium` provisional, not stress-tested · `low` in-flight, with a near `review_after` (~14 days).

## When to NOT wrap up

- **Pure research / ingest** — say so, point at `/wiki-update` or `/wiki-cycle`. Write the journal anyway.
- **Pure exploration with no settled output** — say so, suggest waiting for something concrete.
- **A failed direction** — wrap up the *learning* as troubleshooting ("we tried X, it didn't work because Y"), and be explicit that nothing was built.

Never silently file thin or empty entries. "Nothing here merits a wiki entry yet" is the better answer.

For just the fast working-memory refresh: run `/wrap-up` and answer `none` at Step 2 — Steps 0 and 0.5 still run, and nothing is staged.

## Don't

- Don't auto-file without the user's confirmation of the proposal table, unless `confirm_before_create: false` is configured for the notebook.
- Don't write the conversation transcript into the wiki — distill, don't dump.
- Don't skip staging. Entries land in `_inbox/proposed/` first; promotion happens only in Step 6, on the user's answer or an explicit `confirm_before_promote: false`. Never silently promote when the mode is `true`.
- Don't run `/wrap-up` on a research notebook such as agentic-design — use `/wiki-update`.
- Don't write to `~/.claude/projects/*/memory/MEMORY.md` — that is auto-memory, a different layer. `/wrap-up` writes to the project wiki.
- Don't commit without `--auto-commit` / `--auto-push` beyond Step 6's promote commit, don't push without `--auto-push`, and never force-push or `git add -A`.
