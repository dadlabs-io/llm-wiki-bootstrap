# llm-wiki-bootstrap

Install the LLM-wiki framework on a fresh machine. Ships `/new-wiki`, `/wrap-up`,
`/wiki-cycle`, `/wiki-search`, `/wiki-update`, and the supporting scripts + templates
+ seed content.

**Install this first** — other tools (e.g. [agent-builder-bootstrap](https://github.com/dadlabs-io/agent-builder-bootstrap))
depend on the wiki skills this puts in place.

**Version:** `2026-05-14`
**Source repo:** [dadlabs-io/workflows-core](https://github.com/dadlabs-io/workflows-core)

## Quick start — global install (recommended first step)

```powershell
# Windows
git clone https://github.com/dadlabs-io/llm-wiki-bootstrap.git C:\github.com\llm-wiki-bootstrap
cd C:\github.com\llm-wiki-bootstrap
.\install-wiki.ps1
```

```bash
# Mac / Linux
git clone https://github.com/dadlabs-io/llm-wiki-bootstrap.git ~/llm-wiki-bootstrap
cd ~/llm-wiki-bootstrap
./install-wiki.sh
```

No flags needed. This puts all wiki skills into `~/.claude/skills/` and records
this package's path in `~/.claude/wiki-config.json`.

Restart Claude Code after install so it picks up the new skills.

**Requires:** Python 3.10+, Git.

## What you get globally

After install, these slash-commands are available in **every** Claude Code project:

| Skill | When to use |
|---|---|
| `/new-wiki` | One-time per project: scaffold a wiki + CLAUDE.md + .gitignore |
| `/wrap-up` | End of every dev session: write journal, capture next steps |
| `/wiki-update` | File a durable decision or finding to the wiki |
| `/wiki-search` | Search wiki entries before starting work |
| `/wiki-cycle` | Research projects: search → read → capture loop |

## Set up a project wiki

After the global install, open any project folder in Claude Code and run:

```
/new-wiki
```

It asks a few questions (project name, description, Drive preferences) and
scaffolds:

```
<project>/
├── .claude/skills/          ← all wiki skills, project-local copy
├── .claude/wiki-scripts/    ← Python helper scripts
├── .claude/wiki-templates/
├── .claude/wiki-config.json
├── llm-wiki/
│   ├── README.md
│   ├── how-to/              ← usage docs
│   ├── best-practices/      ← curated dev best practices
│   └── wiki/                ← your project's entries
├── CLAUDE.md
├── README.md
└── .gitignore
```

For each session afterward: `/wrap-up` at the end.

## Modes

### Global-only install (the quick start above)

```powershell
.\install-wiki.ps1           # or: .\install-wiki.ps1 -Mode tooling
```

Installs skills + scripts to `~/.claude/`. No project scaffold. Use `/new-wiki`
later when you're in a project.

### One-shot install + project scaffold

```powershell
.\install-wiki.ps1 -TargetFolder C:\github.com\my-new-project
# interactive prompts for project name / description

.\install-wiki.ps1 -TargetFolder C:\github.com\my-new-project `
    -ProjectName myproj -ProjectDescription "..." -DriveEnabled yes
# fully scripted, no prompts
```

Mac / Linux equivalent flags: `--target-folder`, `--project-name`,
`--project-description`, `--drive-enabled`, `--drive-parent-folder`, `--tool`.

### Refresh an existing install

```powershell
.\install-wiki.ps1           # idempotent re-run updates ~/.claude/skills/
```

Or from inside Claude Code: `/new-wiki --sync` rebuilds the project-local skills
from the current bootstrap source.

## Updating

```powershell
cd C:\github.com\llm-wiki-bootstrap   # or wherever you cloned it
git pull
.\install-wiki.ps1                    # idempotent re-install
```

## Next step

With the wiki skills installed, set up the **agent factory**:

→ [agent-builder-bootstrap](https://github.com/dadlabs-io/agent-builder-bootstrap)
— adds the `agent-builder` agent + `build-agent`, `build-skill`, `promote-agent`
skills so you can scaffold and install Claude Code agents from any project.

## Source of truth

This repo is a release artifact built from [dadlabs-io/workflows-core](https://github.com/dadlabs-io/workflows-core)'s
`bootstrap/workflows/llm-wiki/` tree. To contribute changes, send PRs against the
source repo; the maintainer rebuilds + republishes this repo on each release.
