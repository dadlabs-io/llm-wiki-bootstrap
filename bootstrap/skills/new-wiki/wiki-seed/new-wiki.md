---
title: "new-wiki — skill"
type: how-to
artifact: skill
name: new-wiki
installed_by: install-wiki
date: 2026-09-09
---

# new-wiki — skill

Scaffolds a new project with the whole framework wired up. It first checks what the machine already has, then walks you through a short interview and builds the folder layout, seeds the documentation, and writes the config that ties it together — so a fresh project can ingest research and capture its own decisions from the first session. Every project gets the same merged wiki; there is no research-versus-development choice to make, but each half of the wiki is opt-in.

**Trigger:** */new-wiki [name]*, plus natural phrasings like "new project", "set up a new wiki", or "bootstrap a project".

**Before it asks anything** it checks the global tooling (the wiki skills, helper scripts and agent in your home folder) against the bootstrap clone and reports one of four states: installed, stale, partial or missing. When the tooling is installed — even if a few files differ from the clone — the project simply uses it and nothing is re-copied; refreshing an installed set is a separate command. Only when the tooling is partial or missing does it ask whether to install it once now (and use it) or bundle a private copy into the project.

**Input / Output:** consumes your answers to a two-round interview — project name, then whether new entries need your review before being filed and published; then the description, whether you want a `project/` folder (what you build; with its default subfolders, empty, or not at all), whether you want a `research/` folder (what you ingest; the same three choices), and where the wiki content lives (a registered notebook in your notebooks vault, or inside the project). Drive ingest is asked only when Drive is already enabled on the machine. Everything else — the tool, the target folder, the skills line — is shown in a plan summary you confirm before anything runs, and any line can be changed by saying so. Produces the project folder (a new git repo, unless it already sits inside one) with a `.claude/wiki-config.json` (plus the skills and scripts themselves only in bundled mode), and the wiki root containing the README, the seeded `how-to/` usage docs, the wiki folders you chose (`sessions/` is always created), the framework-contract docs when `project/` exists, and `raw/sessions/`. It also renders a `CLAUDE.md`, `README.md`, and `.gitignore` for the project (an existing one is never overwritten), and walks you through Google Drive OAuth if you asked for Drive ingest. The Cursor variant always bundles and additionally generates `.cursor/rules/*.mdc` so Cursor's agent picks the skills up on its own.

The default `project/` stubs are components, decisions, architecture, patterns, troubleshooting and best-practices; the default `research/` stubs are active, long-term, tooling, best-practices and interesting-docs. An empty half gains subfolders as content arrives: `/wiki-update` proposes one on the first ingest, `/wrap-up` creates the category it files into. A wiki with neither half is a plain notes notebook.

The review-gate answer sets two independent settings — one for whether `/wrap-up` waits for your OK on its table of candidate entries before filing (the table is shown either way), one for whether staged entries are promoted without asking. Either can be flipped later.

**Works with:** the project it creates is ready for [`wiki-update`](./wiki-update.md) and [`wiki-cycle`](./wiki-cycle.md) to bring research in, [`wrap-up`](./wrap-up.md) to capture session work, and [`wiki-search`](./wiki-search.md) to look any of it back up.

**Note:** this needs the one-time machine install (`install-wiki.ps1` on Windows, `install-wiki.sh` on Mac and Linux) to have run first — that is what records where the bootstrap source lives. If the tooling was installed during the run, restart Claude Code before the other `/wiki-*` skills appear. A target folder that already holds other files needs `--force`, which still overwrites nothing you wrote. Re-run `/new-wiki --sync` after pulling updates to refresh this skill; `install-wiki.ps1 -RefreshOnly` refreshes the whole global tooling. To refresh only an existing project's usage docs and framework-contract docs, run `new-wiki.py --phase docs --target-folder <project>` (add `--check` to preview without writing).
