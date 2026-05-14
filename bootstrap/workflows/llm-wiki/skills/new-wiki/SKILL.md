---
name: new-wiki
description: Scaffold a new project with the LLM-wiki framework. Asks tool (claude-code/cursor), project type (research/development), name, target folder, and Drive ingest preferences. Sets up per-project .claude/skills + llm-wiki/ folder with notes, best-practices, and the project's wiki. For development projects, also wires agentmemory MCP. Use when the user says "new project", "create a new wiki", "install a new wiki", "set up a new wiki", "bootstrap a project", "start a new project", or types "/new-wiki".
---

# /new-wiki

Conversational scaffold for a new project. Everything is per-project — the only global thing is this skill itself (lives at `~/.claude/skills/new-wiki/` so you can invoke it from anywhere).

## Layout this skill creates

```
<target>/                              ← user's project folder (e.g., C:\github.com\dnd-project)
├── .claude/                           ← claude-code tool config (per-project)
│   ├── skills/                        ← 13 skills (wiki-cycle, wiki-update, wrap-up, etc.)
│   ├── wiki-scripts/                  ← 14 Python helpers
│   ├── wiki-templates/                ← project-bootstrap templates
│   ├── wiki-config.json
│   └── settings.json                  ← agentmemory MCP wiring (dev projects only)
├── llm-wiki/                          ← human-readable wiki content
│   ├── README.md                      ← how to use the framework in this project
│   ├── how-to/                        ← seeded usage docs
│   ├── best-practices/                ← seeded software-dev best practices
│   ├── wiki/                          ← this project's research/dev entries
│   │   └── {active,long-term,...}/    ← (research)  or  {components,decisions,...}/  (development)
│   └── raw/sessions/                  ← session transcripts (dev only)
├── CLAUDE.md                          ← imports llm-wiki/README.md and wiki/_MAP.md
├── README.md                          ← project README
└── .gitignore
```

Cursor variant: substitutes `.cursor/` for `.claude/`. Additionally generates `.cursor/rules/<skill-name>.mdc` files (Cursor's native rule format) from each SKILL.md so Cursor's agent picks them up automatically. `llm-wiki/` is identical to claude-code.

## Flow at a glance

```
User: /new-wiki [name]
   ↓
Q1: tool? (claude-code | cursor)
Q2: research or development?
Q3: name? (if not given)
Q4: description? (if not given)
Q5: target folder? (default C:\github.com\<name>)
Q6: Drive ingest? (yes/no) — if yes: parent folder name (default __FOR CLAUDE)
   ↓
Phase B — Per-project scaffold (Phase A already done by install-wiki.ps1)
   B1.  mkdir <target> + git init
   B2.  Copy 13 skills    → <target>/.claude/skills/   (or .cursor/skills/)
   B3.  Copy 14 scripts   → <target>/.claude/wiki-scripts/
   B4.  Copy templates    → <target>/.claude/wiki-templates/
   B5.  mkdir llm-wiki/ + seed how-to/, best-practices/
   B6.  Apply project-type folder taxonomy under llm-wiki/wiki/
   B7.  Render CLAUDE.md / README.md / .gitignore at <target>/
   B7.5 Render llm-wiki/README.md from seed template
   B8.  Write <target>/.claude/wiki-config.json
   B9.  Drive OAuth walkthrough (if --drive-enabled yes; uses global token cache)
   B10. agentmemory install + MCP wiring (development only)
   B11. Print ready-state + next steps
```

## Step-by-step contract

### Step 0 — Discovery (if args not provided)

Ask in this order:

**Q1 — Tool**
```
Which tool are you installing for?
  1. claude-code  — Anthropic's Claude Code CLI
  2. cursor       — Cursor IDE

Pick (1 or 2):
```

**Q2 — Project type**
```
What kind of project is this?
  1. research     — ingesting external content (articles, papers, videos) into a wiki
  2. development  — building code, capturing design decisions + components

Pick (1 or 2):
```

**Q3-5 — Name, description, target folder** (if not provided). Slugify the name.

**Q6 — Drive ingest** (skip if user previously configured globally)
```
Do you want to ingest from a Google Drive folder?
  1. yes — I drop links into a Drive folder throughout the day
  2. no  — I'll add URLs manually

Pick (1 or 2):
```

If yes:
```
Parent folder name in your Drive? (default: __FOR CLAUDE)
The script will look for: <parent>/<project-slug>/  (so this project: __FOR CLAUDE/<slug>/)
```

Show the proposed plan and wait for "yes" / "go" / "create" before proceeding.

### Step 1 — Run Phase B

The global Phase A install (which put this skill in `~/.claude/skills/`) also recorded `bootstrap_source` in `~/.claude/wiki-config.json`. Read that to find where the bootstrap source lives. Then:

```bash
python "<bootstrap_source>/bootstrap/workflows/llm-wiki/scripts/new-wiki.py" \
  --phase B \
  --tool <claude-code|cursor> \
  --project-name <slug> \
  --project-description "<desc>" \
  --project-type <research|development> \
  --target-folder <path> \
  --drive-enabled <yes|no> \
  --drive-subfolder <slug>
```

The script handles everything in the layout diagram above and returns a JSON summary on stdout.

### Step 2 — Read back the summary + post-install reminders

The JSON includes `needs_restart: true` if agentmemory was just installed. Surface that to the user — they need to restart Claude Code before /wrap-up etc. work.

**After printing the next-steps**, also give the user a tailored "you're ready" message based on project type:

#### Development project

Tell the user:
- `/wrap-up` at the end of every meaningful session — distills what you did into proposed wiki entries (components, decisions, architecture, patterns, troubleshooting). Without this, the session evaporates.
- `/wiki-promote --review` to approve those proposed entries into the wiki
- `/wiki-search "<query>"` to look up prior decisions / components
- `/wiki-update <url>` for external references (articles, docs, papers)
- agentmemory auto-loads recent session context — no action needed
- **Ask the agent in natural language** for help anytime: "what commands do I have", "how do I look up prior decisions", "show me the wiki"

#### Research project

Tell the user:
- Drop URLs into Google Drive (`<parent>/<project-slug>/`) throughout the day, OR
- `/wiki-update <url>` for ad-hoc one-offs
- `/wiki-cycle` once a day/week — discovers new sources, ingests the queue, lints, promotes
- Source quality tiers: T1 (peer-reviewed / primary), T2 (vendor/official docs), T3 (expert/practitioner), T4 (community/blog). Set with `--tier` on every ingest.
- `/wiki-search "<query>"` to look up prior research
- **Ask the agent in natural language** for help anytime: "how do I add a URL", "what's the discovery process", "show me the wiki"

#### Either type — universal closing

End with: "Read `llm-wiki/how-to/commands.md` for the full command reference, or `llm-wiki/how-to/getting-started.md` for the first-hour walkthrough. You can also ask me anything in plain English — I have these docs loaded as context."

### Step 3 — Don't

- Don't proceed without explicit confirmation at discovery
- Don't overwrite an existing project folder without `--force` unless user explicitly OKs it
- Don't auto-install agentmemory on research projects
- Don't promise the Claude-Code-restart will happen automatically — instruct the user, they restart
- Don't edit `<target>/.claude/skills/` manually — that's an installed copy; edit in `<bootstrap_source>/bootstrap/workflows/llm-wiki/skills/` and re-sync

## Drive OAuth walkthrough (Phase B, only if `--drive-enabled yes`)

The Drive token is **machine-global** (cached at `~/.config/wiki-cycle/drive-token.json`), not per-project. If you've already done OAuth on this machine for a previous project, Phase B reuses the cached token.

If the token isn't cached, Phase B triggers the OAuth flow:
1. A browser window opens at `accounts.google.com`
2. User signs in with the Google account that holds the Drive folder
3. User approves the "See, edit, create, and delete all of your Google Drive files" scope (full `drive`)
4. Token caches; next time, Phase B reuses it

If `~/.config/wiki-cycle/client_secrets.json` is missing, the helper prints instructions to create OAuth credentials at https://console.cloud.google.com/apis/credentials (Desktop application) and download the JSON to that path.

## Update mode

`/new-wiki --sync` re-runs Phase A — refreshes the global `/new-wiki` skill from the current `bootstrap_source`. Use after `git pull` on the llm-wiki-bootstrap clone.

To sync a per-project install with the current bootstrap (refresh the project's skills + scripts), re-run Phase B against the same target folder with `--force`.

## Required: the bootstrap-source path

`/new-wiki` reads `~/.claude/wiki-config.json` to find where the bootstrap source lives (recorded during Phase A by `install-wiki.ps1`).

If `~/.claude/wiki-config.json` is missing or doesn't have `bootstrap_source`, the user hasn't run the one-time machine install. Direct them to:

```
git clone https://github.com/dadlabs-io/llm-wiki-bootstrap ~/llm-wiki-bootstrap
cd ~/llm-wiki-bootstrap
.\install-wiki.ps1     # Windows
./install-wiki.sh      # Mac/Linux
```

After that one-time setup, `/new-wiki` works in any project folder.

## Source

Authored 2026-05-12, restructured 2026-05-13 for the per-project model. Companion skills: `/wrap-up` (end-of-session distillation, dev projects), `/wiki-cycle` (research-project orchestrator), `/wiki-search`, `/wiki-update`.
