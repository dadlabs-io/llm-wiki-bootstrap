# llm-wiki-bootstrap

Install the LLM-wiki framework on a fresh machine. Ships `/new-wiki`, `/wrap-up`,
`/wiki-cycle`, `/wiki-search`, `/wiki-update`, and the supporting scripts + templates
+ seed content. After install, scaffold a per-project wiki with `/new-wiki`.

**Install this first** — other tools (e.g.
[agent-builder-bootstrap](https://github.com/dadlabs-io/agent-builder-bootstrap))
depend on the wiki skills this puts in place.

**This repo is the gold copy** — maintained and committed to directly (see `git log` for history);
it is no longer generated from `workflows-core`.

---

## Works with

| | Tool | Install guide |
|:--:|:--|:--|
| [![Claude Code](https://img.shields.io/badge/Claude_Code-CC785C?logo=anthropic&logoColor=white&style=flat-square)](https://claude.ai/code) | **Claude Code** | [→ Claude Code install](#claude-code) |
| [![Cursor](https://img.shields.io/badge/Cursor-000000?logo=cursor&logoColor=white&style=flat-square)](https://cursor.sh) | **Cursor** | [→ Cursor install](#cursor) |

---

## Prerequisites

Python 3.10+, Git. No Node.js required for the global install.

---

<h2 id="claude-code">
  <img src="https://cdn.simpleicons.org/anthropic/CC785C" height="28" alt="Anthropic" valign="middle">
  &nbsp;Claude Code
</h2>

### Install globally

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

No flags needed. Installs all wiki skills to `~/.claude/skills/` and all wiki
scripts to `~/.claude/wiki-scripts/`. Idempotent.

Restart Claude Code after install so it picks up the new skills.

### What gets installed globally

| Skill | When to use |
|---|---|
| `/new-wiki` | One-time per project: scaffold a wiki, `CLAUDE.md`, `.gitignore` |
| `/wrap-up` | End of every dev session: write journal, capture next steps |
| `/wiki-update` | File a durable decision or finding to the wiki |
| `/wiki-search` | Search wiki entries before starting work |
| `/wiki-cycle` | Research projects: search → read → capture loop |

### Set up a project wiki

After the global install, open any project folder in Claude Code and run:

```
/new-wiki
```

It asks a few questions (project name, description, Drive prefs) and scaffolds:

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

---

<h2 id="cursor">
  <img src="https://cdn.simpleicons.org/cursor/000000" height="28" alt="Cursor" valign="middle">
  &nbsp;Cursor
</h2>

> **Windows only** for now — `install-wiki.ps1 -Tool cursor`. The `.sh` script
> does not yet support Cursor; Mac/Linux Cursor users should use the Claude Code
> install path (Cursor 2.4+ also scans `~/.claude/skills/` natively).

### Install globally (Windows)

```powershell
cd C:\github.com\llm-wiki-bootstrap
.\install-wiki.ps1 -Tool cursor
```

Installs wiki skills to `~/.cursor/skills/` and scripts to `~/.cursor/wiki-scripts/`.

Restart Cursor after install.

### Set up a project wiki

Open any project in Cursor and run:

```
/new-wiki
```

The same conversational flow runs; project files are scaffolded to
`<project>/.cursor/skills/` and `<project>/.cursor/wiki-scripts/`.

### Mac / Linux Cursor users

Run the standard Claude Code install (`./install-wiki.sh`). Cursor 2.4+ discovers
skills in `~/.claude/skills/` automatically, so the wiki skills are immediately
available in Cursor without a separate install step.

---

## Install options

| Flag | Effect |
|---|---|
| _(no flags)_ | Global tooling install — skills + scripts to `~/.claude/` |
| `-Tool cursor` | Global install to `~/.cursor/` instead (Windows only) |
| `-TargetFolder <path>` | Global install + scaffold a project at `<path>` |
| `-ProjectName`, `-ProjectDescription` | Skip interactive prompts |
| `-DriveEnabled yes` | Enable Google Drive sync for wiki content |

## Updating

```powershell
cd C:\github.com\llm-wiki-bootstrap
git pull
.\install-wiki.ps1          # idempotent — re-copies skills + scripts
```

Or from inside Claude Code: `/new-wiki --sync` rebuilds the project-local skills
from the current bootstrap source.

## Next step

With the wiki skills installed, set up the **agent factory**:

→ **[agent-builder-bootstrap](https://github.com/dadlabs-io/agent-builder-bootstrap)**
— adds the `agent-builder` agent + `build-agent`, `build-skill`, `promote-agent`
skills so you can scaffold and install Claude Code agents from any project.

## Source of truth

**This repo (`llm-wiki-bootstrap`) is the gold copy.** To contribute changes, send PRs directly
against this repo. (Historical note: it was originally generated from
[dadlabs-io/workflows-core](https://github.com/dadlabs-io/workflows-core)'s
`bootstrap/workflows/llm-wiki/` tree by a build script; that pipeline has been retired — changes
now land here directly, per the active commit history in `git log`.)
