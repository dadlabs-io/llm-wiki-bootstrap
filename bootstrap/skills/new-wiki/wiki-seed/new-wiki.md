---
title: "new-wiki — skill"
type: how-to
artifact: skill
name: new-wiki
installed_by: install-wiki
date: 2026-07-31
---

# new-wiki — skill

Scaffolds a new project with the whole framework wired up. It walks you through a short interview and then builds the folder layout, installs the skills and helper scripts, seeds the documentation, and writes the config that ties it together — so a fresh project can ingest research and capture its own decisions from the first session. Every project gets the same merged wiki; there is no research-versus-development choice to make.

**Trigger:** */new-wiki [name]*, plus natural phrasings like "new project", "set up a new wiki", or "bootstrap a project".

**Input / Output:** consumes your answers to the interview — which tool (Claude Code or Cursor), project name and one-line description, target folder, whether skills install globally or bundle into the project, whether the wiki content lives in a separate vault or inside the project, whether to ingest from a Google Drive folder, and whether new entries need your review before being filed and published. Produces the project folder with a git repo, a `.claude/` (or `.cursor/`) directory holding the skills, scripts, templates and `wiki-config.json`, and an `llm-wiki/` tree containing the README, seeded `how-to/` and `best-practices/` docs, the wiki itself (`research/`, `project/`, `sessions/`), and `raw/sessions/`. It also renders a `CLAUDE.md`, `README.md`, and `.gitignore`, and walks you through Google Drive OAuth if you asked for Drive ingest. The Cursor variant additionally generates `.cursor/rules/*.mdc` so Cursor's agent picks the skills up on its own.

The review-gate answer sets two independent settings — one for whether candidate entries are proposed to you before filing, one for whether staged entries are promoted without asking. Either can be flipped later.

**Works with:** the project it creates is ready for [`wiki-update`](./wiki-update.md) and [`wiki-cycle`](./wiki-cycle.md) to bring research in, [`wrap-up`](./wrap-up.md) to capture session work, and [`wiki-search`](./wiki-search.md) to look any of it back up.

**Note:** this needs the one-time machine install (`install-wiki.ps1` on Windows, `install-wiki.sh` on Mac and Linux) to have run first — that is what records where the bootstrap source lives. Re-run `/new-wiki --sync` after pulling updates to refresh the global skill.
