---
name: new-project
description: Bootstrap a brand-new project with the LLM-wiki framework. Asks research-vs-development, installs the global skills + scripts + templates the first time, optionally installs agentmemory (for development projects), then creates the per-project scaffold. Use when the user says "new project", "create-new-wiki", "/new-project", "set up a new wiki", "bootstrap a project", "start a new project".
---

# /new-project

The single command that turns "I want to start a new project" into a working setup. Handles both first-time-on-this-machine global install AND the per-project scaffold. Idempotent — safe to run repeatedly; skips steps that are already done.

## Flow at a glance

```
User: /new-project [name]
   ↓
Q1: which tool? (claude-code | cursor)
Q2: research or development?
Q3: name? (if not given)
Q4: description? (if not given)
Q5: target folder? (default C:\github.com\<name>)
Q6: ingest from Google Drive? (yes/no) — if yes: parent folder name (default __FOR CLAUDE)
   ↓
Phase A — Global install (skipped if already done)
   A1.  Detect what's installed (per tool)
   A2.  Copy skills (bootstrap → ~/.claude/skills/    for claude-code)
                  (bootstrap → .cursor/rules/         for cursor; per-project only)
   A3.  Copy scripts (bootstrap → ~/.claude/wiki-scripts/   for claude-code)
                    (bootstrap → <target>/.wiki/scripts/   for cursor)
   A4.  Copy templates (bootstrap → ~/.claude/wiki-templates/  for claude-code)
                      (bootstrap → <target>/.wiki/templates/  for cursor)
   A5.  Write ~/.claude/wiki-config.json  (claude-code)  OR
        Write <target>/.wiki/config.json  (cursor — per-project)
   A6.  (DEVELOPMENT ONLY) Install agentmemory
   A7.  (DEVELOPMENT ONLY) Wire agentmemory MCP into the right settings file
   A8.  (DEVELOPMENT ONLY) Tell user to restart Claude Code / reload Cursor
   ↓
Phase B — Per-project scaffold (always runs)
   B1.  mkdir <target> + git init
   B2.  /wiki-init <name> with --project-type <research|development>
   B3.  Write project CLAUDE.md / AGENTS.md from template
   B4.  Write project README.md from template
   B5.  Write project .gitignore from template
   B6.  Record drive_subfolder choice (project slug → __FOR CLAUDE/<slug>/ by default)
   B7.  Print ready-state with next-step commands
```

## Step-by-step contract

### Step 0 — Discovery

If the user typed `/new-project` with no args, conversationally find out (in order):

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

**Q3-5 — Name, description, target folder** (if not provided as args). Slugify the name.

**Q6 — Google Drive ingest** (optional but ask)
```
Do you want to ingest from a Google Drive folder?
  1. yes — I drop links into a Drive folder throughout the day
  2. no  — I'll add URLs manually with /wiki-update

Pick (1 or 2):
```

If yes:
```
Parent folder name in your Drive? (default: __FOR CLAUDE)
The script will look for: <parent>/<project-slug>/  (so this project: __FOR CLAUDE/<slug>/)
```

Show the proposed plan:

```
About to set up:
  Tool:               claude-code
  Project type:       development
  Name (slug):        dnd-combat-engine
  Description:        D&D 5e + Pathfinder monster combat engine
  Target folder:      C:\github.com\dnd-combat-engine
  Wiki topic:         <vault>/dnd-combat-engine/   (folders: components, decisions, architecture, patterns, troubleshooting)
  Drive ingest:       yes → __FOR CLAUDE/dnd-combat-engine/
  Global install:     <will run Phase A if not already done>
  agentmemory:        <will install if development + not already wired>

Confirm? (yes / no / change <field>)
```

Wait for explicit "yes" / "go" / "create" before proceeding.

#### Tool-specific notes

- **claude-code**: globals at `~/.claude/skills/`, `~/.claude/wiki-scripts/`, `~/.claude/wiki-templates/`. Config at `~/.claude/wiki-config.json`. MCP wiring in `~/.claude/settings.json`.
- **cursor**: no global-skills concept. Skills + scripts + templates land in `<target>/.wiki/` per-project (Cursor doesn't share `~/.claude/`). MCP wiring in `<target>/.cursor/mcp.json`. The `adapters/cursor/` folder in workflows-core is the canonical translation point — if it's not built yet, the script surfaces a clear "Cursor adapter incomplete" warning and falls back to writing per-project copies of the CC skills (which Cursor users can invoke manually until `.mdc` rule generation is wired).

### Step 1 — Phase A (global install)

Run the helper script with the right phase flag:

```bash
python ~/.claude/wiki-scripts/new-project.py --phase A \
  --tool <claude-code|cursor> \
  --project-type <research|development> \
  --bootstrap-source "$BOOTSTRAP_SOURCE" \
  --drive-enabled <yes|no> \
  --drive-parent-folder "__FOR CLAUDE"
```

If `~/.claude/wiki-scripts/new-project.py` doesn't exist yet (very first run on this machine), use the in-repo path: `bootstrap/workflows/llm-wiki/scripts/new-project.py`.

The script:
1. Reads `~/.claude/wiki-config.json` if it exists; otherwise treats this as first-time
2. Copies `bootstrap/.../skills/` → `~/.claude/skills/` (overwriting only files where bootstrap is newer)
3. Copies `bootstrap/.../scripts/` → `~/.claude/wiki-scripts/`
4. Copies `bootstrap/.../templates/` → `~/.claude/wiki-templates/`
5. Writes/updates `~/.claude/wiki-config.json` with vault root + bootstrap source path
6. If `--project-type development`: also installs agentmemory via `npx @agentmemory/agentmemory` and merges its MCP entry into `~/.claude/settings.json`

If anything in Phase A required new MCP wiring or a fresh agentmemory install: print a clear "RESTART CLAUDE CODE" notice and STOP. The per-project scaffold (Phase B) runs in the same script call only if no restart was needed.

#### Drive OAuth walkthrough (Phase A, only if `--drive-enabled yes`)

If the user opted into Drive ingest, Phase A checks for a cached OAuth token at `~/.config/wiki-cycle/drive-token.json`:

- **Token cached with `https://www.googleapis.com/auth/drive` scope**: nothing to do — auth is good.
- **Token cached with wrong scope (e.g., `drive.readonly`)**: stale token is deleted, OAuth flow re-runs.
- **No token**: helper runs `wiki-fetch-drive-folder.py` in probe mode, which triggers the OAuth flow:
  1. A browser window opens at `accounts.google.com`
  2. User signs in with the Google account that holds the `__FOR CLAUDE` folder
  3. User approves the "See, edit, create, and delete all of your Google Drive files" scope (full `drive`, not `drive.readonly` — `--move-handled` defaults on, which requires write)
  4. Token caches to `~/.config/wiki-cycle/drive-token.json`

If `~/.config/wiki-cycle/client_secrets.json` is missing, the helper surfaces clear instructions to create OAuth credentials at https://console.cloud.google.com/apis/credentials (Desktop application type) and download the JSON to that path. The skill should pass this guidance through to the user verbatim.

### Step 2 — Phase B (per-project scaffold)

Run the helper again with phase B:

```bash
python ~/.claude/wiki-scripts/new-project.py --phase B \
  --tool <claude-code|cursor> \
  --project-name <slug> \
  --project-description "<desc>" \
  --project-type <research|development> \
  --target-folder <path> \
  --drive-subfolder <slug>   # defaults to project slug; pass empty if drive disabled
```

The script:
1. Creates the project folder + runs `git init`
2. Invokes the global `wiki-init` script with `--project-type` so it gets the right folder taxonomy
3. Renders the project CLAUDE.md template (with `@imports` pointing at the vault MAP)
4. Renders README.md and .gitignore from templates
5. Returns a JSON summary

Print the ready-state report:

```
✅ Project ready.

Project codebase:    C:\github.com\dnd-combat-engine\
Wiki topic:          <vault>/dnd-combat-engine/
Wiki folders:        components, decisions, architecture, patterns, troubleshooting
Global skills:       installed at ~/.claude/skills/
agentmemory:         installed and wired
CLAUDE.md:           written, @imports the wiki MAP

Next steps:
  1. cd C:\github.com\dnd-combat-engine
  2. claude   (or start a Claude Code session here)
  3. Start coding. /wrap-up at session-end to crystallize the session into wiki entries.
  4. /wiki-search   to look up prior decisions/components as your wiki grows.
```

### Step 3 — Don't

- Don't proceed without explicit confirmation at the discovery step.
- Don't run Phase A every time — check `~/.claude/wiki-config.json` for already-installed status.
- Don't auto-install agentmemory on research projects.
- Don't write to an existing target folder unless the user explicitly says it's okay (`--force` flag).
- Don't proceed silently if agentmemory's `npx` install hangs or fails — surface the error.
- Don't promise a Claude-Code-restart will happen automatically — instruct the user, they restart.

## State detection (for the idempotency)

Before running Phase A, the helper checks:

| Check | Method | Skip Phase A if all true |
|---|---|---|
| `~/.claude/wiki-config.json` exists | filesystem | + |
| `~/.claude/skills/wiki-init/SKILL.md` exists | filesystem | + |
| `~/.claude/wiki-scripts/wiki-init.py` exists | filesystem | + |
| `~/.claude/wiki-templates/CLAUDE.md.research.tmpl` exists | filesystem | + |
| If development project: agentmemory MCP entry in `~/.claude/settings.json` | grep | + |
| If development project: agentmemory server reachable | HTTP probe | + |

If any check fails → run that sub-step of Phase A. Don't blindly skip the whole phase.

## Update mode

`/new-project --sync` (no other args) runs only Phase A in update mode:
- Diffs each bootstrap source against installed copy
- Asks user to confirm overwrites
- Bumps `install_version` in wiki-config.json

This is how you propagate skill / script / template changes to the global install after you've edited them in `bootstrap/`.

## Dry-run mode

`/new-project --dry-run` prints what would happen without writing anything. Useful for sanity-checking before the real run.

## Required: the bootstrap-source path

The skill needs to know where workflows-core lives so it can find the bootstrap directory. Three ways to discover it:

1. **From config**: `~/.claude/wiki-config.json` → `bootstrap_source` field
2. **From CWD**: if user is currently inside workflows-core, derive it from git rev-parse --show-toplevel
3. **From arg**: `/new-project --bootstrap-source <path>`

If none can be determined → ask the user.

## Source

Authored 2026-05-12 alongside `/wrap-up` and the INSTALL-INVENTORY doc. Companion skill that orchestrates the global install + per-project scaffold.
