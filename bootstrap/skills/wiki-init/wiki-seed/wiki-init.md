---
title: "wiki-init — skill"
type: how-to
artifact: skill
name: wiki-init
installed_by: install-wiki
date: 2026-07-31
---

# wiki-init — skill

Scaffolds a notebook folder by hand: `<vault>/<topic>/`, with the wiki inside it and the working folders beside it. [`new-wiki`](./new-wiki.md) does not use it (new projects get their wiki from `/new-wiki`'s own scaffold), so reach for this only to create a notebook folder outside that flow. It takes a topic slug and a one-or-two-sentence description, shows you the plan to confirm, and refuses to overwrite a topic that already exists.

**Trigger:** */wiki-init*, or "wiki init", "init wiki". "Create a new wiki" usually means `/new-wiki`; name this skill if you want it.

**Input / Output:** Consumes a topic slug (lowercase, hyphenated; the skill suggests the project slug), a description of the wiki's scope (the skill offers the project description from `.claude/wiki-config.json` if you give none), and an optional vault, the folder that holds notebook folders, which defaults to the project's registered notebooks vault, else the current folder. Produces `<vault>/<topic>/` containing:
- `wiki/` with the default `project/` and `research/` subfolders, `sessions/`, a HOME page and a user guide
- `raw/`, `answers/`, and `_inbox/` (pending, done, failed, reports, archive)
- `_config/feeds.md` for discovery sources, and a first `_INDEX.md`
- a README whose Scope section is filled from your description

**Works with:** [`wiki`](./wiki.md) browses what it creates. To start filling it, use [`wiki-update`](./wiki-update.md) for external sources and [`wrap-up`](./wrap-up.md) at the end of a working session.

**Note:** Sharpen the README's Scope section by hand. Deciding what belongs in a wiki is a human call, and a good description is specific enough that you can later tell what is off-topic. This scaffold puts the framework-contract docs at `wiki/best-practices/framework/`; projects made by `/new-wiki` keep them at `wiki/project/best-practices/framework/`.
