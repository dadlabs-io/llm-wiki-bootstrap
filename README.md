# llm-wiki-bootstrap

Install the LLM-wiki framework on a fresh machine. Ships the wiki skills (`/new-wiki`,
`/wrap-up`, `/wiki-cycle`, `/wiki-search`, `/wiki-update` and the rest of the pack), the
`wiki-ingester` agent, the Python helper scripts, the templates and the seed content.
After install, scaffold a per-project wiki with `/new-wiki`.

**Install llm-wiki-bootstrap (this repo) first, then
[agent-builder-bootstrap](https://github.com/dadlabs-io/agent-builder-bootstrap).**
Agent-builder's skills depend on the wiki skills this repo installs: its do-code-change
workflow, for one, uses `writing-skill-suggestions` from here.

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

[uv](https://docs.astral.sh/uv/) and Git. Every wiki script runs in its own uv environment, built beside the scripts from this repo's `uv.lock` (the Google, PDF, YouTube, YAML and MarkItDown libraries come with it), and uv fetches the pinned Python when the machine has none. The installer asks before installing uv when it is missing. No Node.js required for the global install.

### Optional: a GPU runtime for `qmd query` (search)

Wiki search runs on [qmd](https://github.com/tobi/qmd) 2.8.3 or newer (`npm i -g @tobilu/qmd@latest`), which bundles three small models and runs them on the machine through node-llama-cpp. Keyword search (`qmd search`) needs no model. The hybrid mode the skills use by default (`qmd query`) does, and it needs a GPU backend: on a Windows machine with an NVIDIA GPU install the CUDA runtime once, at machine level (not per project):

```powershell
winget install --id Nvidia.CUDA --version 13.2 --exact --accept-package-agreements --accept-source-agreements --override "-s cudart_13.2 cublas_13.2"
```

That installs only the runtime library and cuBLAS (no compiler, no driver; CUDA 13.1 or newer is what node-llama-cpp's prebuilt binary needs). Open a new terminal afterwards, then verify from qmd's package folder:

```bash
(cd "$(npm root -g)/@tobilu/qmd" && npx --no-install node-llama-cpp inspect gpu) | grep -E "^(CUDA|Metal):"   # must print: CUDA: available (or Metal: available)
```

Without it node-llama-cpp falls back to Vulkan, where token generation can hang indefinitely at 100% CPU (seen 2026-09-12 on an RTX 4070 + Intel iGPU laptop). A Mac uses Metal, with nothing to install.

**A machine with no GPU searches by keyword only.** The installer runs the GPU check once and records the machine's search mode in `~/.claude/wiki-config.json`: `full` when CUDA or Metal is available, `keyword` otherwise. On a keyword machine every wiki search runs qmd's keyword index (`qmd search`: no model, well under a second; the helper searches the key words together and in every pair, since that index needs every word to match), and the wiki, `/wrap-up`, the task list and ingest all work as usual. What it gives up is matching by meaning and the reranking: related entries are found by shared words only. Never run `qmd query`, `qmd vsearch` or `qmd embed` there: with no GPU the models run on the CPU and take every core (on 2026-10-02 one full search on a laptop's CPU used about 9,900 CPU-seconds and hung it without finishing). Index upkeep is `qmd update` alone. When the machine gets a GPU, install its runtime (above), run `uv run --project ~/.claude/wiki-scripts python ~/.claude/wiki-scripts/wiki-qmd-query.py --set-mode full` (it refuses while the GPU check fails), then `qmd embed` once to build the meaning index; an install refresh says so when a keyword machine has a GPU available. On a `full` machine nothing changes: `/wiki-search` runs the GPU check before its first search and stops if it fails, never falling back.

**Upgrading from an older qmd (2.1 → 2.8).** After `npm i -g @tobilu/qmd@latest`, run `qmd doctor` once before anything else. Its first check migrates the old embeddings to 2.8's fingerprint; until then `qmd status` shows nearly every file as needing embedding, and re-embedding would redo them all for nothing. `qmd status` now also reports orphaned chunks, the vectors of old file versions that 2.1 never pruned: `qmd cleanup` removes them. Then `qmd embed` for any files genuinely pending. On 2.8.3 an 8 GB GPU runs three full searches at once, which is `wiki-qmd-query.py`'s default; on an older qmd set `WIKI_QMD_SLOTS=2`.

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

No flags needed. Installs all wiki skills to `~/.claude/skills/`, all wiki
scripts to `~/.claude/wiki-scripts/` (with their uv environment, `.venv`, beside them), and the wiki
agents to `~/.claude/agents/`. Idempotent.

Restart Claude Code after install so it picks up the new skills.

### What gets installed globally

| Skill | When to use |
|---|---|
| `/new-wiki` | One-time per project: scaffold a wiki, `CLAUDE.md`, `.gitignore` |
| `/wrap-up` | End of every dev session: write journal, capture next steps |
| `/wiki-update` | File a durable decision or finding to the wiki |
| `/wiki-search` | Search wiki entries before starting work |
| `/wiki-cycle` | Research projects: search → read → capture loop |

Those are the five you will use daily. The rest of the pack installs with them — `/wiki`,
`/wiki-lint`, `/wiki-promote`, `/wiki-refresh`, `/wiki-report`, `/wiki-claims`, `/wiki-verify`,
`/wiki-rollback`, `/wiki-discover`, `/wiki-list`, `/wiki-triage`, `/task-list` — and every one has a usage page in
`wiki-seed/` (also copied into each project's `how-to/llm-wiki/`). The install manifests
are `TRAVEL_SKILLS`, `TRAVEL_SCRIPTS` and `TRAVEL_AGENTS` in `scripts/_install_tooling.py`.

| Agent | What it's for |
|---|---|
| `wiki-ingester` | Spawnable subagent for batch ingestion — `/wiki-cycle` (or any session) delegates queue drains / multi-URL batches to it; each source is read in full and staged for review |

### Set up a project wiki

After the global install, open any project folder in Claude Code and run:

```
/new-wiki
```

It checks the global tooling first (uses it as is; installs it once if missing; never
re-copies an installed set), then asks two rounds of questions — name and review gate; description,
a `project/` folder (with stubs, empty, or none), a `research/` folder (the same three), and where
the wiki lives — and scaffolds:

```
<project>/
├── .claude/wiki-config.json ← points at the global skills + scripts (no per-project copy)
├── llm-wiki/
│   ├── README.md
│   ├── how-to/              ← usage docs, one folder per installed package (llm-wiki/ is the framework's)
│   ├── wiki/                ← your project's entries: research/, project/ (with the framework-contract docs), sessions/
│   └── raw/sessions/        ← session snapshots
├── CLAUDE.md
├── README.md
└── .gitignore
```

Two variants. `--skills-install bundled` (and every Cursor install) copies the skills, scripts
and templates into the project's `.claude/` (or `.cursor/`) instead of using the global ones. A
target that sits inside a notebooks vault (a folder with a `linked-notebooks.json` registry above
it) is scaffolded flat at the notebook root — `wiki/`, `raw/`, `_inbox/` as direct children, no
`llm-wiki/` level — and registered there.

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
| `-RefreshOnly` | Re-copy skills + scripts + agents from this clone (after `git pull`) |
| `-Tool cursor` | Global install to `~/.cursor/` instead (Windows only) |
| `-TargetFolder <path>` | Global install + scaffold a project at `<path>` (the full tooling is installed only if missing or partial) |
| `-ProjectName`, `-ProjectDescription` | Skip interactive prompts |
| `-ProjectFolder`, `-ResearchFolder` | `stubs` (default) / `empty` / `none` — the wiki's two halves |
| `-VaultRoot <dir>`, `-Registry <linked-notebooks.json>` | Put the wiki in a notebooks vault and register it there, instead of `<project>/llm-wiki/` |
| `-SkillsInstall bundled` | Copy skills + scripts into the project instead of using the global ones |
| `-DriveEnabled yes` | Enable Google Drive sync for wiki content |

## Updating

```powershell
cd C:\github.com\llm-wiki-bootstrap
git pull
.\install-wiki.ps1 -RefreshOnly   # idempotent — re-copies skills + scripts + agents
```

From inside Claude Code, `/new-wiki --sync` refreshes only the global `/new-wiki` skill from
the recorded bootstrap source; the installer (or `wiki-upgrade.py`) refreshes everything.
Neither touches a project. `uv run python scripts/new-wiki.py --mode status` says whether a
refresh is due (installed / stale / partial / missing, with the differing files named). To bring a project's framework-managed
docs (its `how-to/llm-wiki/` pages and the six framework-contract docs) up to date:

```
uv run python scripts/new-wiki.py --phase docs --check --target-folder <project>   # preview
uv run python scripts/new-wiki.py --phase docs --target-folder <project>           # refresh
```

`--all-notebooks` does either for every notebook in a registry. A bundled install refreshes its
project-local skills by re-running the scaffold against the same folder with `--force`.

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
