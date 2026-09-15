---
title: "Installing on a fresh machine — llm-wiki"
type: how-to
pack: llm-wiki
installed_by: install-wiki
date: 2026-09-09
---

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
1. Records where this clone lives and installs `/new-wiki` globally at `~/.claude/skills/new-wiki/`
2. Installs the rest of the global tooling (every wiki skill, script and agent) **only if it is missing or partial** — an installed set is left alone, never re-copied
3. Asks for anything not passed (name, description) and scaffolds the project (`llm-wiki/`, `CLAUDE.md`, config); `-ProjectFolder` / `-ResearchFolder` (`stubs` | `empty` | `none`, default `stubs`) choose the wiki's two halves. The wiki goes inside the project as `llm-wiki/` unless you pass `-VaultRoot` (and `-Registry`) to make it a notebook in your notebooks vault, which is what `/new-wiki` recommends
4. (Optional) Walks through Google Drive OAuth if `-DriveEnabled yes`

## Two-step alternative

If you want the global install first, then create projects separately:

```powershell
# One time per machine
.\install-wiki.ps1

# Restart Claude Code, then in any project folder:
> /new-wiki
```

`/new-wiki` is a conversational skill. It checks the global tooling first (use it as is; install it once if missing; never re-copy), then asks two rounds of questions — name and review gate; description, a `project/` folder (with stubs, empty, or none), a `research/` folder (the same three), and where the wiki lives — shows the plan, and scaffolds on your go.

## What gets installed where

**Globally (per machine):**
- `~/.claude/skills/` — every wiki skill
- `~/.claude/wiki-scripts/` — the Python helpers behind them
- `~/.claude/agents/` — the `wiki-ingester` agent, with its model config and reading list
- `~/.claude/settings.json` — a SessionStart hook that lists a wiki project's resume files at startup and after `/clear` (the file is backed up first; other settings are left alone)
- `~/.claude/wiki-config.json` — records where the bootstrap clone lives

**Per project (when you scaffold one):**
- `<project>/.claude/wiki-config.json` — per-project config: which tooling it uses, where the wiki is, the two folder answers
- `<project>/CLAUDE.md`, `README.md`, `.gitignore`
- the wiki root — `<project>/llm-wiki/` or a registered notebook in your notebooks vault — with `README`, `how-to/`, `wiki/` (the folders you chose; `sessions/` always) and `raw/sessions/`
- only with `-SkillsInstall bundled`: `<project>/.claude/skills/`, `wiki-scripts/`, `wiki-templates/` (a private copy of the tooling)

For Cursor users (Windows installer only; the Mac/Linux installer does not support Cursor yet): `.cursor/` replaces `.claude/`, the skills are always bundled, and `.cursor/rules/*.mdc` are generated from the SKILL.md files so Cursor's agent picks them up natively.

## Prerequisites

- Python 3.10+
- Git
- Node.js + `qmd` 2.8.3 or newer (`npm i -g @tobilu/qmd@latest`) for wiki search
- Only for Google Drive ingest: `pip install google-api-python-client google-auth-oauthlib`

### Optional: a GPU runtime for `qmd query` (search)

Wiki search runs on [qmd](https://github.com/tobi/qmd) 2.8.3 or newer (`npm i -g @tobilu/qmd@latest`), which bundles three small models and runs them on the machine through node-llama-cpp. Keyword search (`qmd search`) needs no model. The hybrid mode the skills use by default (`qmd query`) does, and it needs a GPU backend: on a Windows machine with an NVIDIA GPU install the CUDA runtime once, at machine level (not per project):

```powershell
winget install --id Nvidia.CUDA --version 13.2 --exact --accept-package-agreements --accept-source-agreements --override "-s cudart_13.2 cublas_13.2"
```

That installs only the runtime library and cuBLAS (no compiler, no driver; CUDA 13.1 or newer is what node-llama-cpp's prebuilt binary needs). Open a new terminal afterwards, then verify from qmd's package folder:

```bash
(cd "$(npm root -g)/@tobilu/qmd" && npx --no-install node-llama-cpp inspect gpu) | grep -E "^CUDA:"   # must print: CUDA: available
```

Without it node-llama-cpp falls back to Vulkan, where token generation can hang indefinitely at 100% CPU (seen 2026-09-12 on an RTX 4070 + Intel iGPU laptop). The `/wiki-search` skill runs this check before the first query and stops if it fails; it does not fall back. On a machine with no NVIDIA GPU, use `qmd search`.

**Upgrading from an older qmd (2.1 → 2.8).** After `npm i -g @tobilu/qmd@latest`, run `qmd doctor` once before anything else. Its first check migrates the old embeddings to 2.8's fingerprint; until then `qmd status` shows nearly every file as needing embedding, and re-embedding would redo them all for nothing. `qmd status` now also reports orphaned chunks, the vectors of old file versions that 2.1 never pruned: `qmd cleanup` removes them. Then `qmd embed` for any files genuinely pending. On 2.8.3 an 8 GB GPU runs three full searches at once, which is the search helper's default; on an older qmd set `WIKI_QMD_SLOTS=2`.

## Updating

```powershell
cd ~/llm-wiki-bootstrap
git pull
.\install-wiki.ps1                   # refreshes every wiki skill, script and agent, and the hook
```

The plain run is the refresh (press Enter at its two prompts, or run it non-interactively).
`-RefreshOnly` is still accepted for old scripts but does nothing extra. `wiki-upgrade.py` does the
same refresh; from inside Claude Code, `/new-wiki --sync` refreshes only the global `/new-wiki`
skill. None of these touches a project. To refresh a project's framework-managed docs (the `how-to/llm-wiki/` pages and the six
framework-contract docs), from the bootstrap clone:
```
python bootstrap/scripts/new-wiki.py --phase docs --check --target-folder <project>   # preview, writes nothing
python bootstrap/scripts/new-wiki.py --phase docs --target-folder <project>           # refresh
```
A bundled install (skills copied into the project) refreshes them by re-running the scaffold
against the same folder with `--force`.

## Troubleshooting

- **`gh` / `git clone` fails with auth** — repo is public now, no auth needed; check your network
- **`/new-wiki` says the global tooling is missing or partial** — run `.\install-wiki.ps1` (no flags) once, or let the skill install it; `python <clone>/bootstrap/scripts/new-wiki.py --mode status` shows what is installed, stale or missing
- **Drive OAuth fails** — see [`drive-setup`](./drive-setup.md)
- **`/new-wiki` doesn't trigger in Claude Code** — restart Claude Code after install so it picks up the new global skill
