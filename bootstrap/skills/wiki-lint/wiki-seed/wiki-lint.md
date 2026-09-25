---
title: "wiki-lint — skill"
type: how-to
artifact: skill
name: wiki-lint
installed_by: install-wiki
date: 2026-07-31
---

# wiki-lint — skill

A health check on the wiki, available at two depths. The default pass is a fast deterministic script that catches mechanical rot: links pointing at files that no longer exist, pages nothing links to, half-finished TODO text, missing frontmatter. The `--full` pass goes further — the agent reads every entry and looks for the problems a script cannot see, such as two entries contradicting each other. Neither mode changes anything on its own; the full mode applies only the fixes you approve.

**Trigger:** */wiki-lint* — also "lint the wiki", "wiki health check", "check the wiki for issues". For the deep pass: */wiki-lint --full*, "semantic lint", "find contradictions", "find missing connections in the wiki".

**Input / Output:** Reads the entries under `wiki/` (not `sessions/` or the generated `_INDEX.md` / `_MAP.md`). The mechanical mode prints its report and saves it to `_inbox/reports/lint-report.md` (`_inbox/` sits beside `wiki/` at the notebook root). It covers:

- broken links, live `[[wikilink]]` syntax the link checker cannot follow, and orphan pages (a retired entry is not an orphan; a page meant to stand alone, such as the wiki's HOME, says so with `standalone: "<reason>"` in its frontmatter and is listed apart with that reason)
- stale pending/TODO phrases
- frontmatter: required fields; valid `tier`, `confidence` and `ingested_by` values; tags and lifecycle dates present (your notebook's frontmatter spec, `wiki/project/best-practices/framework/wiki-frontmatter-best-practices.md`, defines them all); and frontmatter that would not parse, checked on the entries and on the installed skill and agent files, since a skill whose frontmatter does not parse never triggers
- `raw_path` resolving to a real file or folder; a tier `self` entry has none and counts as self-authored
- code drift: a `project/` entry that names the code it describes (`describes: <path>` or `<path>@<commit>`) is listed when that code changed since the pinned commit or after the entry's `last_reviewed` day, including uncommitted edits. The path is relative to the project's repo, which a notebook names as `project_root` in the notebook registry; a wiki inside its project uses the project folder. A broken path, an unknown commit, or a notebook with no repo is listed too. It is a prompt to re-read the entry, not a failure: re-read, correct if needed, then bump `last_reviewed` and pin the current commit
- the truth-status and lineage fields (`verified`, `type`, `revises`, `contradicted_by`, and the like)
- search-index coverage: files the search index holds against `.md` files on disk
- the body checks shared with the ingest gate: a TL;DR, a Related section with at least two wiki links (a warning for tier `self`), the entry layout (body, then the Source/Raw footer, then the auto backlinks block), three or more tags, `stub` on thin entries, and numbers on `>` blockquote lines rather than in prose. Here they only warn: they show the backlog in existing entries, while the gate refuses a new entry that breaks a hard rule (TL;DR, Related, layout, or frontmatter that would not parse). Hub, system and framework-contract pages and retired entries are exempt.

The run exits 0. With `--strict` it exits 1 on broken links, an invalid truth-status or lineage field, or an out-of-range `ingested_by`.

The full mode runs the mechanical pass first, then additionally writes `_inbox/reports/<agent>-semantic-lint-<date>.md`, evaluating every entry against six criteria — contradictions, missing cross-references, thin coverage, concept gaps, tier accuracy, and a catch-all — plus a drift-watch section for entries you have flagged as needing a deep comparison against a named canonical source.

**Works with:** [`wiki-cycle`](./wiki-cycle.md) runs both passes as cycle steps, and [`wiki-report`](./wiki-report.md) pulls the lint counts into its summary. [`wiki-promote`](./wiki-promote.md) re-runs the mechanical pass after promoting entries, to confirm the move left no broken links.

**Note:** The full mode reads every file in the wiki, so it costs real time and tokens — that is why it is not the default. Findings are never auto-applied: you approve the fixes, then the mechanical pass re-runs to verify nothing new broke.
