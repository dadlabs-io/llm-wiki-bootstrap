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

Required discovery, in order. **ALL FIVE are mandatory — you must ask the user for each, even when you can plausibly default. Showing a default is fine; silently using the default is not. Every question gets explicit user confirmation.**

**Use the `AskUserQuestion` tool with selectable options — do NOT ask the user via plain-text questions.** The tool's UI gives the user clear pre-built choices (radio buttons for type/drive, an "Other" escape hatch for free text, recommended-option highlighting). Plain-text Q&A loses that, makes the user retype the same answers every cycle, and is harder to scan.

AskUserQuestion caps at 4 questions per call, so split into two rounds:
- **Round 1 (4 questions)**: target folder, project type, project name (with default), drive ingest
- **Round 2 (1 question)**: description (with default `"Wiki for <name>"`)

For each question, supply 2–4 **concrete, fully-resolved options** — never strategies, meta-instructions, or placeholders like `<slug>` or "use the folder leaf name as the slug". If you don't have a concrete value yet, resolve one BEFORE building the picker:

- **Before building the picker, pick a working slug.** If the user gave a name in their message, slugify it. If they didn't, use `new-project` as the working slug and let them override via "Other". Never show `<slug>`, `<name>`, or `<new-project>` as literal placeholders in option labels — those leak through to the installer and break paths.
- Use `(Recommended)` suffix on the suggested default so it's selectable in one click.

Examples (assume the working slug is `test-project`):
- Target folder: `C:\github.com\test-project` (Recommended) / `~/proj/test-project` / Other (free text)
- Project type: `Research` / `Development (Recommended for code projects)` — never default; let user pick
- Project name (slug): `test-project` (Recommended) / Other (type a different slug)
- Drive: `No (Recommended)` / `Yes`
- Description (Round 2): default **must include the project type**. For development → `Development wiki for test-project` (Recommended). For research → `Research wiki for test-project` (Recommended). Plus one alternate (e.g. plain `Wiki for test-project`) and `Other (type your own)`.

Round 2 (description) **must still fire even when the user accepted all Round-1 defaults**. Always show the description picker — never silently use the default. The default's wording always reflects the project type chosen in Round 1.

1. **Target folder** — where the new project goes (e.g., `C:\github.com\my-project`). If they gave it in their message, confirm by repeating it back.
2. **Project type** — `research` or `development`. This is the most important call and the easiest to guess wrong. Ask explicitly: "Is this a research project (curating external content) or a development project (building code)?" Never default.
3. **Project name** — slugified (lowercase, dashes). Propose a default from the target folder leaf, but **always show it and ask the user to confirm or override**. Do NOT silently use the default.
4. **Description** — one-liner. Propose a default of `"Wiki for <name>"`, but **always show it and ask the user to confirm or override**. Do NOT silently use the default or leave it empty. A non-empty description is also required to avoid argument-bridge bugs when invoking the installer (see TOOL CHOICE below).
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

**TOOL CHOICE — important on Windows**:
- Invoke `install-wiki.ps1` via the **PowerShell tool**. Do NOT use the Bash tool to call `powershell.exe ./install-wiki.ps1 ...`. Bash → PowerShell argument bridging eats empty quoted strings — `-ProjectDescription ""` collapses, and the *next* flag becomes the description value, which causes a cascade of parse errors and exit 2.
- If the PowerShell tool gets denied by an auto-classifier, **ask the user to run the command themselves** in their terminal. Don't fall back to Bash → PowerShell.
- Always pass a non-empty `-ProjectDescription` (default to `"Wiki for <name>"` if the user didn't provide one) so the bridge problem can't bite even if someone disregards the above.

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
