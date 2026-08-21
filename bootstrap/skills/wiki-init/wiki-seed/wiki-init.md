---
title: "wiki-init — skill"
type: how-to
artifact: skill
name: wiki-init
installed_by: install-wiki
date: 2026-07-31
---

# wiki-init — skill

Creates the wiki itself: the folder structure under `llm-wiki/wiki/<topic>/` and a templated README describing what the wiki is for. It normally runs automatically when a project is first scaffolded, so you rarely invoke it by hand — the reasons to do so are adding a wiki to a project that never got one, or rebuilding a scaffold that was damaged. It takes a topic slug and a one-or-two-sentence description, and refuses to overwrite a topic that already exists.

**Trigger:** */wiki-init*, or natural phrasings like "wiki init", "create a new wiki", "init wiki".

**Input / Output:** Consumes a topic slug (lowercase, hyphenated — defaults to the project slug), a description of the wiki's scope (read from `.claude/wiki-config.json` if you don't supply one), and an optional vault path that defaults to `llm-wiki/wiki`. Produces the topic folder at `llm-wiki/wiki/<topic>/` with its scaffold files, including a README whose description field is filled in and whose "In scope / Out of scope" sections are left as placeholders for you.

**Works with:** [`wiki`](./wiki.md) browses the structure this creates. Once the scaffold exists, the two ways to start filling it are [`wiki-update`](./wiki-update.md) for ingesting external sources and [`wrap-up`](./wrap-up.md) at the end of a working session.

**Note:** Editing the README's "In scope / Out of scope" sections is deliberately left to you — deciding what belongs in a wiki is a human call, and a good description is specific enough that you can later tell what is off-topic.
