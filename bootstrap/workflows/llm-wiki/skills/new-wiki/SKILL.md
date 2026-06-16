---
name: new-wiki
description: Scaffold a new project with the LLM-wiki framework. Asks tool (claude-code/cursor), name, target folder, and Drive ingest preferences (NO project-type question — every project gets one merged wiki that does both research ingest and project-knowledge capture). Sets up per-project .claude/skills + llm-wiki/ folder with notes, best-practices, and the project's wiki (research/* + project/* + sessions/). Use when the user says "new project", "create a new wiki", "install a new wiki", "set up a new wiki", "bootstrap a project", "start a new project", or types "/new-wiki".
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
│   ├── wiki/                          ← this project's entries (merged taxonomy)
│   │   ├── research/{active,long-term,tooling,best-practices,implementation,skills,orchestration,interesting-docs}/
│   │   ├── project/{components,decisions,architecture,patterns,troubleshooting,best-practices}/
│   │   └── sessions/                  ← per-persona episodic logs
│   └── raw/sessions/                  ← session transcripts
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
Q2: name? (if not given)
Q3: description? (if not given)
Q4: target folder? (default C:\github.com\<name>)
Q5: skills install? (global [default] | bundled)  — see below
Q6: wiki content location? (separate vault [default] | inside project)  — see below
Q7: Drive ingest? (yes/no) — if yes: parent folder name (default __FOR CLAUDE)
   ↓
Phase B — Per-project scaffold (Phase A already done by install-wiki.ps1)
   B1.  mkdir <target> + git init
   B2.  Copy 13 skills    → <target>/.claude/skills/   (or .cursor/skills/)
   B3.  Copy 14 scripts   → <target>/.claude/wiki-scripts/
   B4.  Copy templates    → <target>/.claude/wiki-templates/
   B5.  mkdir llm-wiki/ + seed how-to/, best-practices/
   B6.  Apply the single merged folder taxonomy under llm-wiki/wiki/ (research/* + project/* + sessions/)
   B7.  Render CLAUDE.md / README.md / .gitignore at <target>/
   B7.5 Render llm-wiki/README.md from seed template
   B8.  Write <target>/.claude/wiki-config.json
   B9.  Drive OAuth walkthrough (if --drive-enabled yes; uses global token cache)
   B11. Print ready-state + next steps
```

> **No project-type question.** Every project gets the same merged wiki — it does both research ingest (`research/`) and project-knowledge capture (`project/`) at once. (The research/development split was removed 2026-06-15.)

## Step-by-step contract

### Step 0 — Discovery (REQUIRED — ALWAYS ASK, never guess)

**CRITICAL**: Never default values based on context (folder name, prior conversation, "reasonable guess"). Ask explicitly for every field below before running anything. The user's answer is the source of truth.

Ask in this order:

**Q1 — Tool**
```
Which tool are you installing for?
  1. claude-code  — Anthropic's Claude Code CLI
  2. cursor       — Cursor IDE

Pick (1 or 2):
```

> **(No project-type question — removed 2026-06-15.)** Every project gets the merged taxonomy that does both research ingest and project-knowledge capture. Skip straight to name.

**Q2 — Name (ALWAYS confirm)**
Even if you can infer it from the user's input or the folder name, **always show the proposed name and ask for confirmation**. Slugify (lowercase, dashes for non-alphanumerics, strip leading/trailing dashes).

```
Project name (slug): test-project
Press enter to accept, or type a different slug:
```

**Q4 — Description (ALWAYS ask, with a default)**
Always prompt, never skip. Default is `"Wiki for <name>"`. User hits enter to accept or types their own.

```
One-line description for the wiki: [default: Wiki for test-project]
Press enter to accept the default, or type your own:
```

**Q5 — Target folder** (if not provided). Default is `C:\github.com\<slug>` on Windows, `~/proj/<slug>` on macOS/Linux. Confirm before proceeding.

**Q6 — Skills install** (claude-code only; cursor always bundles)
```
How should the wiki skills + scripts be installed?
  1. global   — use the shared ~/.claude install (no per-project copy; recommended for personal use) [default]
  2. bundled  — copy skills+scripts into the project (self-contained + version-pinned; for distribution)

Pick (1 or 2) [1]:
```
→ passes `--skills-install global|bundled`. Global keeps the project to just `.claude/wiki-config.json` + content; the global skills/scripts handle everything, reading this project's config.

**Q7 — Wiki content location**
```
Where should the wiki CONTENT live?
  1. separate vault — keeps the wiki OUT of the code repo (recommended) [default]
                      default root: C:\github.com\project-notebooks  → content at <root>\<slug>\
  2. inside project — <target>\llm-wiki\  (self-contained code+wiki repo)

Pick (1 or 2) [1]:
```
→ if separate, confirm the vault root (default `C:\github.com\project-notebooks`) and pass `--vault-root <root>`. Content then lives at `<root>\<slug>\wiki\`; the project carries only the config pointing at it. If inside, omit `--vault-root`.

**Q8 — Drive ingest** (skip if user previously configured globally)
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

The global Phase A install (which put this skill in `~/.claude/skills/`) also recorded `bootstrap_source` in `~/.claude/wiki-config.json`. Read that to find where the bootstrap source lives.

**TOOL CHOICE — IMPORTANT**:
- **Windows**: invoke `python new-wiki.py ...` via the **PowerShell tool**, not the Bash tool. Bash → PowerShell argument bridging mangles empty quoted strings (e.g. `-ProjectDescription ""` collapses, so the next flag gets consumed as the description value, causing exit 2). If the PowerShell tool is denied by an auto-classifier, ask the user to run the command themselves in their terminal — do NOT fall back to `bash` → `powershell.exe ...`.
- **macOS/Linux**: use the Bash tool directly — no shell-bridge issues.

Then:

```bash
python "<bootstrap_source>/bootstrap/workflows/llm-wiki/scripts/new-wiki.py" \
  --phase B \
  --tool <claude-code|cursor> \
  --project-name <slug> \
  --project-description "<desc>" \
  --target-folder <path> \
  --skills-install <global|bundled> \
  --vault-root <root>   `# omit entirely for an in-project wiki` \
  --drive-enabled <yes|no> \
  --drive-subfolder <slug>
```

`--skills-install` defaults to `global`. Omit `--vault-root` for an in-project wiki (`<target>/llm-wiki/`); include it (e.g. `C:\github.com\project-notebooks`) to put content at `<root>/<slug>/`.

The script handles everything in the layout diagram above and returns a JSON summary on stdout.

### Step 2 — Read back the summary + post-install reminders

The JSON includes `needs_restart: true` if agentmemory was just installed. Surface that to the user — they need to restart Claude Code before /wrap-up etc. work.

**After printing the next-steps**, also give the user a tailored "you're ready" message based on project type:

#### Every project (single merged flow — does both)

Tell the user:
- **Ingest research**: drop URLs into Google Drive (`<parent>/<project-slug>/`) throughout the day OR `/wiki-update <url>` ad-hoc, then `/wiki-cycle` (daily/weekly) to discover → ingest → lint → promote. Source tiers T1 primary / T2 vendor / T3 expert / T4 community — set with `--tier`.
- **Capture project knowledge**: as you code/decide/debug, the agent files durable items (decisions, components, architecture, patterns, troubleshooting) to `llm-wiki/wiki/_inbox/proposed/` inline; run `/wrap-up` at session-end to catch the rest.
- `/wiki-promote --review` to approve proposed entries (research → `research/`, project knowledge → `project/`).
- `/wiki-search "<query>"` to look up prior research + decisions/components.
- **Ask the agent in natural language** anytime: "what commands do I have", "how do I add a URL", "show me the wiki".

#### Universal closing

End with: "Read `llm-wiki/how-to/commands.md` for the full command reference, or `llm-wiki/how-to/getting-started.md` for the first-hour walkthrough. You can also ask me anything in plain English — I have these docs loaded as context."

### Step 3 — Don't

- Don't proceed without explicit confirmation at discovery
- Don't overwrite an existing project folder without `--force` unless user explicitly OKs it
- Don't ask the user to pick a project type — that distinction was removed; every project gets the merged taxonomy
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
