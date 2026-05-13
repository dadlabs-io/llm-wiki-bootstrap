# llm-wiki-bootstrap

Install the LLM-wiki framework on a fresh machine. Ships /new-project, /wrap-up, /wiki-cycle, /wiki-search, /wiki-update, and the supporting scripts + templates to bootstrap a research or development project with structured per-project memory.

**Version:** `2026-05-13`
**Source repo:** [dadlabs-io/workflows-core](https://github.com/dadlabs-io/workflows-core) (this package is generated from `bootstrap/workflows/llm-wiki/`)

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

After install, restart Claude Code (or Cursor) so it picks up the new skills.

## Install options

```powershell
# Default: claude-code + research project + no Drive ingest
.\install-wiki.ps1

# Development project (installs agentmemory MCP server)
.\install-wiki.ps1 -ProjectType development

# Enable Google Drive ingest (will walk you through OAuth)
.\install-wiki.ps1 -DriveEnabled yes -DriveParentFolder "__FOR CLAUDE"

# Cursor instead of Claude Code (per-project install only)
.\install-wiki.ps1 -Tool cursor -TargetFolder C:\github.com\myproject
```

`install-wiki.sh` accepts equivalent `--tool`, `--project-type`, `--target-folder`, `--drive-enabled`, `--drive-parent-folder` flags.

## After install

In any new project folder:

```
claude   # or open in Cursor
> /new-project
```

`/new-project` will ask whether the project is research or development, set up the folder structure, configure agentmemory if needed, and wire your Drive folder for ingest.

For each session: `/wrap-up` at the end to crystallize work into wiki entries.

## What lives in `bootstrap/workflows/llm-wiki/`

| Folder | What |
|---|---|
| `skills/` | 13 slash-command skills (`new-project`, `wrap-up`, `wiki-cycle`, `wiki-update`, `wiki-search`, `wiki-init`, plus internal `wiki-*` helpers) |
| `scripts/` | Python helpers invoked by the skills (`new-project.py`, `wiki-init.py`, `wiki-fetch-drive-folder.py`, etc.) |
| `templates/` | Project-bootstrap templates (CLAUDE.md, README.md, .gitignore, research vs development variants) |

## Updating

After pulling new versions of this repo:
```powershell
.\install-wiki.ps1     # idempotent — re-runs Phase A, only updates changed files
```

Or from inside Claude Code: `/new-project --sync` does the same thing.

## Source of truth

This repo is a release artifact built from [dadlabs-io/workflows-core](https://github.com/dadlabs-io/workflows-core)'s `bootstrap/workflows/llm-wiki/` tree. To contribute changes, send PRs against the source repo; the maintainer rebuilds + republishes this repo on each release.
