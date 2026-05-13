# llm-wiki-bootstrap

Install the LLM-wiki framework on a fresh machine. Ships /new-project, /wrap-up, /wiki-cycle, /wiki-search, /wiki-update, and the supporting scripts + templates + seed content. After install, you scaffold per-project with `/new-project` inside any project folder.

**Version:** `2026-05-13`
**Source repo:** [dadlabs-io/workflows-core](https://github.com/dadlabs-io/workflows-core) (this package is generated from `bootstrap/workflows/llm-wiki/`)

## Install model

- **One-time per machine**: `install-wiki.ps1` (or `.sh`) puts the `/new-project` creator skill in `~/.claude/skills/` and records this package's path as `bootstrap_source` in `~/.claude/wiki-config.json`.
- **Per-project, conversational**: `/new-project` inside any project folder asks tool (claude-code/cursor), type (research/development), Drive prefs, etc., then scaffolds:
  - `<project>/.claude/skills/` (all 13 skills, per-project)
  - `<project>/.claude/wiki-scripts/`, `wiki-templates/`
  - `<project>/llm-wiki/{README, how-to/, best-practices/, wiki/}/`
  - `<project>/CLAUDE.md`, `README.md`, `.gitignore`

This means: skills + scripts live PER PROJECT (not globally). Updates to one project don't affect others.

## One-time machine install

### Windows (PowerShell)
```powershell
git clone https://github.com/dadlabs-io/llm-wiki-bootstrap.git ~/llm-wiki-bootstrap
cd ~/llm-wiki-bootstrap
.\install-wiki.ps1
```

### Mac / Linux (bash)
```bash
git clone https://github.com/dadlabs-io/llm-wiki-bootstrap.git ~/llm-wiki-bootstrap
cd ~/llm-wiki-bootstrap
./install-wiki.sh
```

Requires: Python 3.10+, Git, Node.js (only if you'll use development projects with agentmemory).

After install, restart Claude Code so it picks up the new global `/new-project` skill.

## Install options

```powershell
# Default: install /new-project globally, no Drive default
.\install-wiki.ps1

# Enable Drive ingest by default (will walk you through OAuth on first /new-project)
.\install-wiki.ps1 -DriveEnabled yes -DriveParentFolder "__FOR CLAUDE"
```

`install-wiki.sh` accepts equivalent `--drive-enabled` and `--drive-parent-folder` flags.

Tool choice (claude-code vs cursor) and project type (research vs development) are NOT picked at install — they're per-project, asked by `/new-project`.

## After install — scaffold a project

```
cd <your-project-folder>
claude       # or: cursor .
> /new-project
```

`/new-project` asks tool, project type, name, description, target, and Drive prefs. Then it creates the per-project layout and (for development projects) wires agentmemory.

For each session afterward: `/wrap-up` at the end (dev projects) or `/wiki-cycle` for research projects.

## What ships in `bootstrap/workflows/llm-wiki/`

| Folder | What |
|---|---|
| `skills/` | 13 slash-command skills (`new-project`, `wrap-up`, `wiki-cycle`, `wiki-update`, `wiki-search`, `wiki-init`, plus internal `wiki-*` helpers) |
| `scripts/` | 14 Python helpers (`new-project.py`, `wiki-init.py`, `wiki-fetch-drive-folder.py`, `wiki-cycle` step scripts, etc.) |
| `templates/` | Project-bootstrap templates (CLAUDE.md, README.md, .gitignore, research/development variants) |
| `seed/` | Per-project seed content: `llm-wiki-readme.md.tmpl`, `how-to/*.md` (getting-started + per-command docs), `best-practices/*.md` (curated dev best practices) |

## Updating

When you pull new versions of this repo:
```powershell
cd ~/llm-wiki-bootstrap
git pull
.\install-wiki.ps1     # idempotent re-run of Phase A
```

To sync an EXISTING per-project install with the latest bootstrap:
```
# Inside the project, with Claude Code running:
/new-project --sync   # rebuilds <project>/.claude/skills/ etc. from current bootstrap
```

## Source of truth

This repo is a release artifact built from [dadlabs-io/workflows-core](https://github.com/dadlabs-io/workflows-core)'s `bootstrap/workflows/llm-wiki/` tree. To contribute changes, send PRs against the source repo; the maintainer rebuilds + republishes this repo on each release.
