# llm-wiki-bootstrap

Install the LLM-wiki framework on a fresh machine. Ships /new-wiki, /wrap-up, /wiki-cycle, /wiki-search, /wiki-update, and the supporting scripts + templates + seed content. After install, you scaffold per-project with `/new-wiki` inside any project folder.

**Version:** `2026-05-14`
**Source repo:** [dadlabs-io/workflows-core](https://github.com/dadlabs-io/workflows-core) (this package is generated from `bootstrap/workflows/llm-wiki/`)

## Install model

- **One-time per machine**: `install-wiki.ps1` (or `.sh`) puts the `/new-wiki` creator skill in `~/.claude/skills/` and records this package's path as `bootstrap_source` in `~/.claude/wiki-config.json`.
- **Per-project, conversational**: `/new-wiki` inside any project folder asks tool (claude-code/cursor), type (research/development), Drive prefs, etc., then scaffolds:
  - `<project>/.claude/skills/` (all 13 skills, per-project)
  - `<project>/.claude/wiki-scripts/`, `wiki-templates/`
  - `<project>/llm-wiki/{README, how-to/, best-practices/, wiki/}/`
  - `<project>/CLAUDE.md`, `README.md`, `.gitignore`

This means: skills + scripts live PER PROJECT (not globally). Updates to one project don't affect others.

## Quick start — one command

```powershell
git clone https://github.com/dadlabs-io/llm-wiki-bootstrap.git ~/llm-wiki-bootstrap
cd ~/llm-wiki-bootstrap

# Install + scaffold a new project in one shot (interactive prompts):
.\install-wiki.ps1 -TargetFolder C:\github.com\my-new-project
```

Mac / Linux:
```bash
git clone https://github.com/dadlabs-io/llm-wiki-bootstrap.git ~/llm-wiki-bootstrap
cd ~/llm-wiki-bootstrap
./install-wiki.sh --target-folder ~/proj/my-new-project
```

Requires: Python 3.10+, Git, Node.js (only if you'll use development projects with agentmemory).

After install, restart Claude Code so it picks up the new skills, then `cd <target-folder>` and start coding.

## Modes

### A. Global-only install (defer project scaffold to later)

```powershell
.\install-wiki.ps1                              # just installs /new-wiki globally
```

Then later, in any project folder:
```
claude
> /new-wiki
```

The conversational `/new-wiki` asks the same questions and scaffolds.

### B. One-shot install + scaffold (the quick start above)

```powershell
.\install-wiki.ps1 -TargetFolder <path>             # interactive prompts
.\install-wiki.ps1 -TargetFolder <path> `
    -ProjectType development -ProjectName myproj `
    -ProjectDescription "..." -DriveEnabled yes    # fully scripted, no prompts
```

`install-wiki.sh` accepts equivalent `--target-folder`, `--project-type`, `--project-name`, `--project-description`, `--drive-enabled`, `--drive-parent-folder`, `--tool` flags.

### C. Existing install — refresh skills from current bootstrap

```powershell
.\install-wiki.ps1 -RefreshOnly                # idempotent re-copy
```

Or from inside Claude Code: `/new-wiki --sync` does the same.

## What you get per project

```
<target>/
├── .claude/skills/         (or .cursor/skills/)  ← 14 skills
├── .claude/wiki-scripts/                          ← 15 scripts
├── .claude/wiki-templates/
├── .claude/wiki-config.json
├── .claude/settings.json                          ← agentmemory MCP (dev only)
├── llm-wiki/
│   ├── README.md
│   ├── how-to/                                    ← 6 usage docs
│   ├── best-practices/                            ← 17 dev best practices
│   └── wiki/                                      ← your project's research/dev entries
├── CLAUDE.md
├── README.md
└── .gitignore
```

For each session afterward: `/wrap-up` at the end (dev projects) or `/wiki-cycle` for research projects.

## What ships in `bootstrap/workflows/llm-wiki/`

| Folder | What |
|---|---|
| `skills/` | 13 slash-command skills (`new-wiki`, `wrap-up`, `wiki-cycle`, `wiki-update`, `wiki-search`, `wiki-init`, plus internal `wiki-*` helpers) |
| `scripts/` | 14 Python helpers (`new-wiki.py`, `wiki-init.py`, `wiki-fetch-drive-folder.py`, `wiki-cycle` step scripts, etc.) |
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
/new-wiki --sync   # rebuilds <project>/.claude/skills/ etc. from current bootstrap
```

## Source of truth

This repo is a release artifact built from [dadlabs-io/workflows-core](https://github.com/dadlabs-io/workflows-core)'s `bootstrap/workflows/llm-wiki/` tree. To contribute changes, send PRs against the source repo; the maintainer rebuilds + republishes this repo on each release.
