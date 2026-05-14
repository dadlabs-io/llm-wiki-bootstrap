# CLAUDE.md — llm-wiki-bootstrap

You're reading this from inside the llm-wiki-bootstrap repo (probably because the user opened this folder in Claude Code or Cursor).

## What this repo is

The LLM-wiki framework installer. Ships:

- The `/new-wiki` creator skill (installs globally so the user can scaffold projects from anywhere)
- 14 per-project skills (`wiki-update`, `wiki-cycle`, `wrap-up`, `wiki-search`, `wiki-promote`, etc.)
- 15 Python helper scripts (vault management, lint, indexing, Drive ingest)
- Templates for `CLAUDE.md`, `README.md`, `.gitignore` in research/development variants
- Seed content for the per-project `llm-wiki/` folder (how-to docs + 17 curated best-practices)
- `install-wiki.ps1` (Windows) and `install-wiki.sh` (Mac/Linux) — the installer entry points

## What the user probably wants

The user almost certainly wants one of three things:

### 1. Set up the framework + scaffold a new project (one shot)

Most common case.

**STOP — ask the user explicitly for each of these BEFORE running anything. Do NOT guess from the folder name or other context. The user's answer is the source of truth.**

Required discovery, in order:

1. **Target folder** — where the new project goes (e.g., `C:\github.com\my-project`). If they gave it in their message, confirm by repeating it back.
2. **Project type** — `research` or `development`. This is the most important call and the easiest to guess wrong. Ask explicitly: "Is this a research project (curating external content) or a development project (building code)?" Never default.
3. **Project name** — defaults to the target folder leaf, slugified. Show the proposed default and let them override.
4. **Description** — one-liner. Optional; if they don't have one, leave empty.
5. **Drive ingest** — yes/no. Defaults to no. Ask only if it might apply.

Once you have all the answers, run:

**Windows:**
```powershell
.\install-wiki.ps1 -TargetFolder C:\github.com\<their-new-project> `
    -ProjectType <research|development> -ProjectName <slug> `
    -ProjectDescription "<one-liner>" -DriveEnabled <yes|no>
```

**Mac/Linux:**
```bash
./install-wiki.sh --target-folder ~/proj/<their-new-project> \
    --project-type <research|development> --project-name <slug> \
    --project-description "<one-liner>" --drive-enabled <yes|no>
```

Pass every value the user gave you — don't drop into the PowerShell `Read-Host` fallback if you can avoid it (it works, but it bypasses your role as the conversational layer).

This installs the `/new-wiki` skill globally AND scaffolds the target project. After it completes, `/new-wiki` is available from any Claude Code session on this machine.

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
- `bootstrap/workflows/llm-wiki/skills/` — every skill that ships
- `bootstrap/workflows/llm-wiki/scripts/` — Python helpers behind the skills
- `bootstrap/workflows/llm-wiki/seed/` — content that lands in each per-project `llm-wiki/` folder
- `bootstrap/workflows/llm-wiki/templates/` — `CLAUDE.md`, `README.md`, `.gitignore` templates

## Don't

- Don't edit `bootstrap/workflows/llm-wiki/` files unless the user explicitly wants to modify the framework. This is a release package — changes here will be overwritten on the next build from workflows-core.
- Don't try to run the per-project skills (`/wiki-update`, `/wrap-up`, etc.) inside this repo — those are for installed projects, not for the bootstrap itself.
- Don't push changes to this repo on the user's behalf without explicit instruction — it's published.

## If the user asks for help

Point them at:
- `README.md` for the install overview
- `bootstrap/workflows/llm-wiki/seed/how-to/commands.md` for the per-command reference
- `bootstrap/workflows/llm-wiki/seed/how-to/getting-started.md` for the first-hour walkthrough

Or just walk them through running `install-wiki.ps1` with the right flags.

## Source

This file is the agent-onboarding doc for llm-wiki-bootstrap. Built from `workflows-core/bootstrap/workflows/llm-wiki/CLAUDE.md` by `scripts/build-wiki-package.py`. Don't hand-edit the copy in the package — edit the source in workflows-core.
