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

**Input / Output:** consumes the current conversation, changed files, and recent commits. Produces three things every run: a per-session journal entry at `wiki/sessions/<persona>/<YYYY-MM>/`, upserted so repeat wrap-ups in one session append to the same file; refreshed working-memory dashboards at `wiki/sessions/<persona>/handoff.md` and `wiki/sessions/active-context.md`, and the task cards in `wiki/tasks/`; durable entries (component, decision, pattern, troubleshooting) staged to `_inbox/proposed/` (at the notebook root, beside `wiki/`) with a `<slug>.proposed_metadata.json` sidecar naming their target folder under `wiki/project/`. For a substantial session it also writes a snapshot to `raw/sessions/`, which the entries cite as their `raw_path`; a light session skips the snapshot and leaves `raw_path` out. And it revises in place the living design pages (`wiki/project/architecture/`) that the session's change made out of date.

Two per-notebook settings control how much it asks: `confirm_before_create` gates the proposal table of candidate entries, and `confirm_before_promote` gates whether staged entries get promoted inline at the end of the run (the same setting decides promotion in `/wiki-update` and `/wiki-cycle`). Both default to asking. A third, `wrap_up_commit`, chooses whether it commits and pushes at the end (below).

**Works with:** [`wiki-promote`](./wiki-promote.md) finishes the job — wrap-up stages entries and offers to promote them immediately, and anything you decline stays in `_inbox/proposed/` for a later `/wiki-promote --review`. [`wiki-update`](./wiki-update.md) is the counterpart for external sources into `research/`; if a session turns out to be pure ingest, wrap-up still writes the journal and dashboards, then points you there for the source. [`task-list`](./task-list.md) owns the task cards (`wiki/tasks/`, worked in the order `tasks/ORDER.md` sets); wrap-up keeps them current: finished tasks marked done, new ones added, statuses that moved changed, and one dated line in the Log of each card the session worked on. A task you said was done comes off the list; one the session finished itself stays, and wrap-up asks whether to remove it.

**Docs check:** when the session changed something a README or a usage page describes (a command, skill, script, flag, setting or file name), the wrap-up searches those docs for each changed name, reads every passage that names one, and checks it against the change. A claim that is no longer true is fixed in place (and committed with the rest of the session's work); one it cannot fix, such as another project's page or a question only you can answer, is quoted in the handoff's WAITING ON YOU list, which does not make the wrap-up incomplete. Only what the session changed is checked. The summary gives one line, `Docs check: <n> passages read in <m> docs; <k> fixed, <j> left for you`, or says nothing a doc describes changed; it never reports a check it did not run.

**Cost:** every summary carries the session's running cost so far, `Cost: $N so far this session`, read by a script from the running total your status line saves (Claude Code's own API-price estimate; on a subscription a comparison figure, not a bill). With no total available it says the cost was not checked, never a guess (2026-10-22).

**Living pages (2026-10-19):** a decision or troubleshooting note says why something changed; a living page in `wiki/project/architecture/` says how that part works now. Filing only the note leaves the page wrong, which is how design pages went stale in every notebook. So for each change the session made, the wrap-up finds the living page that covers that part (by its `describes:` path, title or contents), reads it, and edits it in place: it corrects what the change made untrue, adds what is new, moves a fixed gap out of Known gaps, links the session's note under History, and sets `last_reviewed` to today. When the page pins its code (`describes: <path>@<commit>`), the pin moves to that path's latest commit (or to the bare path while the code is still uncommitted), so the lint's code-drift warning clears once the page is current. Each page it means to revise is a row in the proposal table, so you can drop it. A page it cannot settle (the code's behaviour now is unclear) is left unedited and named in WAITING ON YOU. Then a final check (2026-10-22) runs the lint's two staleness checks, "Design Pages Behind Their Notes" and "Code Drift", over the living pages, so a page the session missed, or one an earlier session left behind, is caught before the wrap-up ends: each one flagged is revised then or named in WAITING ON YOU with the reason. A notebook with no living pages skips this. The summary says `Living pages: <n> revised (<pages>), <m> left for you; final check flagged <k>, <what happened to each>`.

**Skill suggestions:** when a skill got in the way during a session, a session may leave a short note in the notebook's suggestion box, `_inbox/skill-suggestions/`. What a note is, how one is written, and what the skill's owner does with it after collecting it are on the [skill-suggestions page](../skill-suggestions.md). This page covers only wrap-up's part: putting each note to you and sending it on. Every wrap-up lists what is in the box and works out whose skill each one is from where its usage page sits in the global toolset's `how-to/` folder (these pages): a page under `how-to/llm-wiki/` is llm-wiki's, a page in any other pack is agent-builder's. A note about a skill whose owner keeps its notebook here (llm-wiki's own notebook, say, and a note about `/wrap-up`) is already home: the wrap-up files it in `_inbox/skill-suggestions/received/` for the owner's next improver pass and tells you, without asking. For every other note it asks you, file by file: send it to that owner, keep it for later, or drop it. You can send one somewhere else, and when it can't tell whose skill it is, it says so and asks you. It doesn't wait for your answer: the rest of the wrap-up goes on, and anything you haven't answered is shown again next time. A sent suggestion lives only with its owner: the wrap-up adds a `Sent` line, leaves the file in the box for the owner to collect, and posts one tagged line to that project's bot. Until the owner collects it, later wrap-ups list it as waiting for pickup and don't ask again. A dropped one gets your decision added and moves to `archive/`, and a kept one stays as it is. Apart from filing a note that is already home, nothing is sent, dropped or moved without your word, even in a notebook where the rest of the wrap-up runs without asking.

**Note:** if you only want the fast dashboard refresh without filing anything, run `/wrap-up` and answer `none` at the proposal table — the journal and dashboards still update.

**Commit and push when it's done:** `/wrap-up --auto-commit` commits the session's work at the end, and `/wrap-up --auto-push` commits and pushes it, so you can close the window. It commits only the files the session changed in the project's repository (never everything that happens to be uncommitted: anything else is left alone and named), and only the notebook's own folder in the notebook's repository; one commit each, or one in all when the wiki lives inside the project. It pushes only a branch that already tracks a remote, and never forces: a push that fails is reported and left to you. To make that the default for a project, set `wrap_up_commit` in the notebook's registry entry (or the project's `wiki-config.json`): `none` (the default, commit nothing), `commit` (as `--auto-commit`), or `push` (as `--auto-push`). It is one setting with three values rather than two switches, because pushing always includes committing. A flag you type still wins for that wrap-up, so `/wrap-up --auto-commit` in a `push` project commits without pushing, and the report says which one decided. Every wrap-up ends on one line saying where things stand: `✅ WRAP-UP COMPLETE: committed and pushed ✅`, `committed, not pushed`, `nothing committed` (nothing asked for), or `⚠️ WRAP-UP INCOMPLETE: <what's left> ⚠️`. A wrap-up still waiting for your answer at the proposal table has not reached that line.

## Full walkthrough

The single session-close command. It writes all three memory tiers under `sessions/` plus the durable layer, and (since 2026-07-06) absorbs the retired `/upd-docs`:

1. **Episodic journal** (always) — upserts `wiki/sessions/<persona>/<YYYY-MM>/<date>-<sid>.md`, the append-only "what we did" log.
2. **Working-memory dashboards** (always, Step 0.5) — refreshes the mutable resume pointer: `wiki/sessions/<persona>/handoff.md` (overwrite; its last section is always **⚠️ WAITING ON YOU**, what needs your decision or action, or "Nothing blocking."), your section of `wiki/sessions/active-context.md` (created on the first wrap-up if the project has none — nothing else seeds it), and the task cards (`wiki/tasks/`, through `/task-list`'s script, each worked card's Log gaining a line). These are the memory-bank replacement — a wrap-up never leaves them stale, and after the first wrap-up they exist for the SessionStart hook to point the next session at (the Resuming section in CLAUDE.md is the fallback where no hook is installed). A session that ends without a wrap-up leaves them describing the one before; the hook notices (the previous session's transcript ran on 30 minutes or more after `handoff.md` was written) and says so at the next startup, so the recap does not resume from them unawares (2026-10-22).
3. **Durable knowledge** (optional) — distills components/decisions/patterns/bugs, staged to `_inbox/proposed/` (beside `wiki/`) then promoted to `wiki/project/<category>/`.

If you only want the fast working-memory refresh, run `/wrap-up` and answer `none` at the proposal table — the journal + dashboards still update, nothing gets staged.

### When to run

- At end of a development session, before clearing context
- Especially after any session that made a decision, built a component, or hit a non-trivial bug
- For a trivial session (a typo fix) there is nothing to distill: answer `none` at the proposal table and the journal and dashboards still update

### What it does

1. Reads the current conversation, changed files and recent commits (a repo with no commits yet is fine), plus any session scratchpad
2. Sorts durable work into five categories: Component / Decision / Living page / Pattern / Troubleshooting
   - and checks the README and usage pages against what the session changed (see Docs check above)
3. Shows a proposal table of distilled entries
4. With the default setting, waits for your answer — `go` (file all), `none` (file nothing), or per-item keep / drop / reframe; with `confirm_before_create: false` it prints the table and files without waiting
5. Revises each kept living page in place and runs the final living-page check (see Living pages above), then stages each kept entry as `_inbox/proposed/<slug>.md` (beside `wiki/`, not inside it) with a `<slug>.proposed_metadata.json` sidecar naming its target folder; the entry carries `tier: self`, `origin: wrap-up` and `category:` frontmatter (fields defined in the frontmatter spec ([wiki-frontmatter-best-practices.md](../../../wiki/project/best-practices/framework/wiki-frontmatter-best-practices.md), in the global toolset))
6. For a substantial session, writes a snapshot (summary, files touched, key passages — not the full transcript) to `raw/sessions/<date>-<slug>.md`, which each entry cites as its `raw_path`; a light session skips the snapshot and leaves `raw_path` out
7. Offers to promote the staged entries right away (see Promoting below)
8. Lists any skill suggestions in `_inbox/skill-suggestions/` and names each one's owner; files the ones whose owner keeps its notebook here, and asks you about the rest: send, keep or drop (see Skill suggestions above)

### Categories

| Category | When |
|---|---|
| **Component** | Built or significantly changed a module/class/system |
| **Decision** | Picked an approach with non-obvious tradeoffs (ADR-style) |
| **Living page** | How a part works now changed: its page in `wiki/project/architecture/` is revised in place, never a new entry beside it |
| **Pattern** | Reusable approach that should apply elsewhere |
| **Troubleshooting** | Bug + root cause + fix — so we don't re-debug it |

Anything that fits none of the five is raised with you rather than forced into one.

### Don't

- Don't paste raw transcripts into wiki entries — the snapshot goes to `raw/sessions/`, not `wiki/`
- Don't set `confirm_before_promote: false` unless you want staged entries promoted without being asked — with the default, wrap-up asks first; the agent drafts, you edit
- Don't expect entries from a session with no settled output — wrap-up says "nothing here merits a wiki entry yet" rather than filing thin ones (the journal and dashboards still update)

### Promoting

Right after staging, wrap-up offers to promote: `yes` (all), `no`, or numbers (`1 3`). With `confirm_before_promote: false` it promotes everything without asking. Promoted entries move to `wiki/project/<category>/`, links to them are added to the related entries, `_INDEX.md` and `_MAP.md` are rebuilt, and the notebook's changes are committed (only its own paths; pushed only with `--auto-push` or `wrap_up_commit: push`). After a clean all-yes or all-no it offers once to save that answer as the notebook's setting. Entries you decline stay in `_inbox/proposed/` for later:

```
/wiki-promote --review
```

