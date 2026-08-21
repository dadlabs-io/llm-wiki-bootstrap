# Installing on a fresh machine

You already have this framework installed (you're reading this from inside an installed project). But if you (or someone you're helping) wants to install it elsewhere:

## One-command quick start

```powershell
# Windows (PowerShell)
git clone https://github.com/dadlabs-io/llm-wiki-bootstrap.git ~/llm-wiki-bootstrap
cd ~/llm-wiki-bootstrap
.\install-wiki.ps1 -TargetFolder C:\github.com\my-new-project
```

```bash
# Mac / Linux
git clone https://github.com/dadlabs-io/llm-wiki-bootstrap.git ~/llm-wiki-bootstrap
cd ~/llm-wiki-bootstrap
./install-wiki.sh --target-folder ~/proj/my-new-project
```

That single command:
1. Installs `/new-wiki` globally at `~/.claude/skills/new-wiki/` (if not already there)
2. Asks 3 conversational questions (project type, name, description)
3. Scaffolds the new project (skills, scripts, llm-wiki/, CLAUDE.md, etc.)
4. (Development projects) Installs the agentmemory MCP server and wires it
5. (Optional) Walks through Google Drive OAuth if `-DriveEnabled yes`

## Two-step alternative

If you want the global install first, then create projects separately:

```powershell
# One time per machine
.\install-wiki.ps1

# Restart Claude Code, then in any project folder:
> /new-wiki
```

`/new-wiki` is a conversational skill — it'll ask all 6 questions (tool, type, name, description, target, Drive prefs) and scaffold the project.

## What gets installed where

**Globally (per machine):**
- `~/.claude/skills/new-wiki/` — the creator skill
- `~/.claude/wiki-config.json` — records where the bootstrap clone lives

**Per project (when you scaffold one):**
- `<project>/.claude/skills/` — 14 skills
- `<project>/.claude/wiki-scripts/` — 15 Python helpers
- `<project>/.claude/wiki-templates/` — templates
- `<project>/.claude/wiki-config.json` — per-project config (vault_root, wiki_topic)
- `<project>/.claude/settings.json` — agentmemory MCP wiring (dev only)
- `<project>/llm-wiki/{README, how-to/, best-practices/, wiki/}/`
- `<project>/CLAUDE.md`, `README.md`, `.gitignore`

For Cursor users: `.cursor/` replaces `.claude/`, and `.cursor/rules/*.mdc` are generated from the SKILL.md files so Cursor's agent picks them up natively.

## Prerequisites

- Python 3.10+
- Git
- Node.js (only if you'll use development projects with agentmemory)

## Updating

```powershell
cd ~/llm-wiki-bootstrap
git pull
.\install-wiki.ps1 -RefreshOnly      # refreshes the global /new-wiki skill
```

To refresh an existing per-project install with newer skills/scripts:
```
/new-wiki --sync                  # re-runs Phase B against the current target with --force
```

## Troubleshooting

- **`gh` / `git clone` fails with auth** — repo is public now, no auth needed; check your network
- **`npx` not found** — install Node.js; the dev path needs it for agentmemory
- **Drive OAuth fails** — see `how-to/drive-setup.md`
- **`/new-wiki` doesn't trigger in Claude Code** — restart Claude Code after install so it picks up the new global skill
