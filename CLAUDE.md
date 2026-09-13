# CLAUDE.md — llm-wiki-bootstrap

You're reading this from inside the llm-wiki-bootstrap repo (probably because the user opened this folder in Claude Code or Cursor).

## Resuming — where we left off (do this on startup)

Active persona: **main** (`sessions/<persona>/` is per persona; an installed role agent such as developer or
architect reads its own folder).

After this file and auto-memory load, before the first reply, read in order, each **if present** (`<notebook>` is
`C:\github.com\project-notebooks
otebooks\llm-wiki-bootstrap`, this repo's own notebook per `.claude/wiki-config.json`):
1. `<notebook>/wiki/sessions/active-context.md` — cross-persona resume pointer
2. `<notebook>/wiki/sessions/<persona>/handoff.md`, then `task.md` — goal, state, pending; NOW and QUEUE
3. Project status doc, if this project keeps one: (none yet — e.g. `project/roadmap.md`)

If `handoff.md` is missing (no wrap-up yet): read the newest journal under `sessions/<persona>/<YYYY-MM>/` if any,
else treat the project as new. Journals otherwise stay on demand.
Open the first reply, whatever the user said, with one paragraph on where we left off and what is next. A project
with a Discord bot does its channel catch-up after this read.

## What this repo is

The LLM-wiki framework installer. Ships:

- The `/new-wiki` creator skill (installs globally so the user can scaffold projects from anywhere)
- The per-project skills (`wiki-update`, `wiki-cycle`, `wrap-up`, `wiki-search`, `wiki-promote`, etc.) — the list is `TRAVEL_SKILLS` in `bootstrap/scripts/_install_tooling.py`; don't restate the count here (it was wrong twice)
- The Python helper scripts (vault management, lint, indexing, Drive ingest) — `TRAVEL_SCRIPTS` in the same file — including `_entry_checks.py`, the shared mechanical gate used by `wiki-update.py` (refuse-to-file), `wiki-lint-mechanical.py` (backlog view) and, since 2026-09-08, `_install_tooling.py` (refuse to install a skill or agent whose frontmatter does not parse)
- The six framework-contract docs (`bootstrap/topic-template/wiki/best-practices/framework/`, `framework-contract: true`, `framework-version`) — the gold copies; `new-wiki.py` lands them at every project's `wiki/project/best-practices/framework/` at scaffold time and on `--phase docs`, replacing a drifted project copy and naming it (2026-09-08)
- Templates for `CLAUDE.md`, `README.md`, `.gitignore` in research/development variants
- Seed content for the per-project `llm-wiki/` folder (the how-to marker + 17 curated best-practices; the how-to pages themselves are the pack docs below, since 2026-09-08)
- Pack usage docs (wiki-seed): one page per skill (`skills/<name>/wiki-seed/`, each carrying its full
  walkthrough), one per agent, the pack overview plus getting-started / commands / install / drive-setup
  (`bootstrap/wiki-seed/`), assembled into each project's `llm-wiki/how-to/llm-wiki/` on install
- `install-wiki.ps1` (Windows) and `install-wiki.sh` (Mac/Linux) — the installer entry points

## What the user probably wants

The user almost certainly wants one of three things:

### 1. Set up the framework + scaffold a new project (one shot)

Most common case. The interview is the same one `/new-wiki` runs — read
`bootstrap/skills/new-wiki/SKILL.md` for the contract; this is the summary.

**Step 0 — state check, before any question.** Run `python bootstrap/scripts/new-wiki.py --mode status`
(PowerShell tool on Windows). It writes nothing and reports the global tooling as `installed`, `stale`,
`partial` or `missing`. Installed or stale → the project will use it and nothing is re-copied (a stale set is
named in the plan summary with `-RefreshOnly` as the fix, never refreshed here). Partial or missing → the
scaffold installs it once (the installer wrapper passes `--install-global-if-missing`) — say so in the plan.
Never ask "global or bundled" when the state is installed or stale; that reinstall-every-time question is
what the 2026-09-09 rewrite removed.

**Use the `AskUserQuestion` tool with selectable options — do NOT ask via plain text.** Concrete,
fully-resolved options only (never `<slug>` placeholders); `(Recommended)` on the default; don't add an
`Other` option, the tool provides it. The name is asked first because everything else is built from it.

- **Round 1 (2 questions)**: project name (slug — slugify what the user said, `new-project` if nothing);
  review gate (`Yes — review before filing and publishing (Recommended)` / `No — automatic`).
- **Round 2 (4 questions, built from the slug)**: description (`Wiki for <slug> (Recommended)` + one plain
  alternate); **project folder?** (`Yes, with the default stubs (Recommended)` / `Yes, empty` / `No`);
  **research folder?** (the same three); where the wiki lives (`Notebook in the vault —
  C:\github.com\project-notebooks\notebooks\<slug> (Recommended)` / `Inside the project —
  C:\github.com\<slug>\llm-wiki`).
- **Round 3 (only when needed)**: skills — only when the state is partial or missing (`Install the global
  tooling now and use it (Recommended)` / `Bundle into this project`); Drive — only when
  `~/.claude/wiki-config.json` has `drive.enabled: true`.

Not asked, shown in the plan summary for override: the tool (`cursor` if a `.cursor/` folder is present,
else `claude-code`), the target folder (`C:\github.com\<slug>`, or the cwd when its leaf name equals
the slug), the skills line, the Drive line. Show the plan (with the folder tree the answers produce) and
wait for "yes" / "go" / "create".

Once confirmed, run:

**Windows:**
```powershell
.\install-wiki.ps1 -TargetFolder C:\github.com\<slug> `
    -ProjectName <slug> -ProjectDescription "<one-liner>" `
    -ProjectFolder <stubs|empty|none> -ResearchFolder <stubs|empty|none> `
    -VaultRoot C:\github.com\project-notebooks\notebooks `
    -Registry C:\github.com\project-notebooks\linked-notebooks.json `   # omit both for an in-project wiki
    -DriveEnabled <yes|no>
```

**Mac/Linux:**
```bash
./install-wiki.sh --target-folder ~/proj/<slug> \
    --project-name <slug> --project-description "<one-liner>" \
    --project-folder <stubs|empty|none> --research-folder <stubs|empty|none> \
    --vault-root ~/proj/project-notebooks/notebooks \
    --registry ~/proj/project-notebooks/linked-notebooks.json \
    --drive-enabled <yes|no>
```

(The review gate is a Phase B flag pair — `--confirm-before-create` / `--confirm-before-promote` — the
wrappers don't expose; for a non-default gate call `python bootstrap/scripts/new-wiki.py --phase B ...`
directly with the flag list in the skill. Both default to `true`.)

Pass every value the user gave you — don't drop into the PowerShell `Read-Host` fallback if you can avoid it (it works, but it bypasses your role as the conversational layer).

**TOOL CHOICE — important on Windows**:
- Invoke `install-wiki.ps1` via the **PowerShell tool**. Do NOT use the Bash tool to call `powershell.exe ./install-wiki.ps1 ...`. Bash → PowerShell argument bridging eats empty quoted strings — `-ProjectDescription ""` collapses, and the *next* flag becomes the description value, which causes a cascade of parse errors and exit 2.
- If the PowerShell tool gets denied by an auto-classifier, **ask the user to run the command themselves** in their terminal. Don't fall back to Bash → PowerShell.
- Always pass a non-empty `-ProjectDescription` (default to `"Wiki for <name>"` if the user didn't provide one) so the bridge problem can't bite even if someone disregards the above.

This installs the `/new-wiki` skill globally (and the rest of the tooling if it was missing) AND scaffolds the target project. After it completes, `/new-wiki` is available from any Claude Code session on this machine.

### 2. Just the global install (no project yet)

If they want the global install without scaffolding a project right now:

```powershell
.\install-wiki.ps1
```

After this, they can `cd` to any future project folder and say "/new-wiki" or "create a new wiki" in Claude Code, and the skill walks them through scaffolding.

### 3. Refresh the global skill from a `git pull`

```powershell
.\install-wiki.ps1 -RefreshOnly
```

Idempotent re-copy of the `/new-wiki` skill from this repo to `~/.claude/skills/new-wiki/`.

## How to read the rest of this repo

- `README.md` — the user-facing install README (what someone reads when they land on the GitHub page)
- `V2_ROADMAP.md` — deferred V2 ideas (wiki-agent, multi-wiki, antigravity adapter, etc.)
- `bootstrap/skills/` — every skill that ships
- `bootstrap/agents/` — agent definitions that ship (→ `~/.claude/agents/`; `TRAVEL_AGENTS`
  manifest in `_install_tooling.py`). First: `wiki-ingester`, the spawnable batch-ingest worker
  `/wiki-cycle` delegates to (added 2026-08-20)
- `bootstrap/scripts/` — Python helpers behind the skills
- `bootstrap/seed/` — content that lands in each per-project `llm-wiki/` folder
- `bootstrap/wiki-seed/` + `skills/<name>/wiki-seed/` — pack usage docs
  (standard wiki-seed convention, shared with the agent-factory): `wiki-seed/llm-wiki.md` is
  the pack entry page, each skill carries its own one-page usage doc; `new-wiki.py` assembles
  them into `<target>/llm-wiki/how-to/llm-wiki/{,skills/,agents/}` on install (Phase B) and on
  `--phase docs` (refresh an existing project's pack docs only; `--check` reports without writing). Distinct from `seed/` (the
  broader project scaffold) — one name per mechanism.
  **Requirement (2026-09-08, shared with the agent-factory): every skill under `bootstrap/skills/`
  and every agent under `bootstrap/agents/` ships `wiki-seed/<name>.md`, and the pack page
  `wiki-seed/llm-wiki.md` lists it.** Adding a skill or agent means four files: the artifact, its
  `wiki-seed/` page (what it does, trigger, inputs/outputs, when it skips itself — written for a
  developer who has never seen this repo, no paths into it), its row in `INSTALL-INVENTORY.md`, and
  its row in the pack page. `new-wiki.py` (`seed_pack_docs`) warns by name for every shipped skill or
  agent without a page — an artifact without one is installed undocumented.
- `bootstrap/templates/` — `CLAUDE.md`, `README.md`, `.gitignore` templates

## Conventions (when editing the scripts)

- **After any change that lands in a notebook** (a framework-contract doc, a `wiki-seed/` page, the how-to
  root marker, a skill or script), the standing procedure (SOP, 2026-09-08) is: `python bootstrap/scripts/new-wiki.py --phase docs --check --all-notebooks` (from this repo; the registry comes from `.claude/wiki-config.json`) → review every REPLACE line → the same command without `--check` → `.\install-wiki.ps1 -RefreshOnly`.
  `--check` writes nothing and exits 1 when any notebook would change; a REPLACE at the *same*
  `framework-version` is a project-local edit the refresh will lose — read it before refreshing. One
  command, nine notebooks, a summary line each; never the hand loop.
- **Date/time** — single rule, helpers in `scripts/_wiki_config.py`:
  - **Date labels** (calendar day a human organizes by — cycle ids, report folders, `date:`/`last_reviewed:`/`review_after:` frontmatter) → **local** date, `today_label()`. Never `datetime.now(timezone.utc)` for a date label (it rolls a night-time run to tomorrow's UTC day).
  - **Timestamps** (a precise instant — `created`, `*_at`, run stamps) → `now_stamp()`: **local time with an explicit UTC offset** (tz-aware ISO-8601, e.g. `2026-06-17T00:05:07-04:00`). Never a naive `.isoformat()` — the zone must always be labelled.

## Don't

- Don't edit `bootstrap/` files unless the user explicitly wants to modify the framework. This is a release package — changes here will be overwritten on the next build from workflows-core.
- Don't try to run the per-project skills (`/wiki-update`, `/wrap-up`, etc.) inside this repo — those are for installed projects, not for the bootstrap itself.
- Don't push changes to this repo on the user's behalf without explicit instruction — it's published.

## If the user asks for help

Point them at:
- `README.md` for the install overview
- `bootstrap/wiki-seed/commands.md` for the per-command reference
- `bootstrap/wiki-seed/getting-started.md` for the first-hour walkthrough

Or just walk them through running `install-wiki.ps1` with the right flags.

## Source

This file is the agent-onboarding doc for llm-wiki-bootstrap. **`llm-wiki-bootstrap` is the gold
copy** — edit directly here. (Historical note: this repo was originally generated from
`workflows-core/bootstrap/` by `scripts/build-wiki-package.py`; that pipeline
has been retired and changes now land here directly — see `git log` for the active commit
history. The build pipeline's `manifest.json` was deleted 2026-09-08 — nothing read it, and the
install manifests in `_install_tooling.py` are the live lists; `README.md` and
`bootstrap/INSTALL-INVENTORY.md` were corrected the same day.)

## Discord channel (this project's bot)

Bot `llm-wiki`; plugin state `~/.claude/channels/discord-llm-wiki/` (set by `DISCORD_STATE_DIR` in
`.claude/settings.local.json` — not the plugin default `~/.claude/channels/discord/`, which is agent-builder's, so
when running `/discord:access` here read and write `access.json` and `approved/` under this folder); launch
`claude --channels plugin:discord@claude-plugins-official` from this folder; the shared channel is `#agent-chat`
(id 1548480711298777199). Setup, bot ids and traps: the `add-project-to-discord` skill (installed globally) and
its seed page. Rules, identical for every project bot:
- Answer only messages that @mention this bot; ignore the rest silently, in the channel and the terminal.
- **Always @mention the bot you address**, as the raw `<@user_id>` (the `discord` block per notebook in
  `C:\github.com\project-notebooks\linked-notebooks.json`), never `@name`: an untagged post reaches nobody. End an
  exchange by tagging it and saying "no reply needed"; the plugin's rate cap (10 bot deliveries per channel per
  10 min) guards against loops.
- Reply with the verdict and where the detail lives (terminal, wiki path); post an interim line on anything over
  a few minutes; say in the channel when a permission prompt is waiting at the keyboard. The full write-up goes
  to the terminal and the wiki as usual.
- After the Resuming read, fetch the recent `#agent-chat` messages and act on any unanswered mention of this bot
  (the plugin does not replay history). When an intake handoff is resolved (Resolution section appended, note
  moved to `_inbox/done/`), post one tagged line back to the sending bot.
