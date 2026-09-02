---
title: "wiki-lint — skill"
type: how-to
artifact: skill
name: wiki-lint
installed_by: install-wiki
date: 2026-07-31
---

# wiki-lint — skill

A health check on the wiki, available at two depths. The default pass is a fast deterministic script that catches mechanical rot: links pointing at files that no longer exist, pages nothing links to, half-finished TODO text, missing frontmatter. The `--full` pass goes further — the agent reads every entry and looks for the problems a script cannot see, such as two entries contradicting each other. Both modes report only.

**Trigger:** */wiki-lint* — also "lint the wiki", "wiki health check", "check the wiki for issues". For the deep pass: */wiki-lint --full*, "semantic lint", "find contradictions", "find missing connections in the wiki".

**Input / Output:** Reads the entries under `wiki/`. The mechanical mode prints a summary and saves it to `_inbox/reports/lint-report.md`, covering broken links, orphan pages, stale pending/TODO phrases, missing `title` and `date` frontmatter, and missing or invalid `tier` values. The full mode additionally writes `_inbox/reports/<agent>-semantic-lint-<date>.md`, evaluating every entry against six criteria — contradictions, missing cross-references, thin coverage, concept gaps, tier accuracy, and a catch-all — plus a drift-watch section for entries you have flagged as needing a deep comparison against a named canonical source.

**Works with:** [`wiki-cycle`](./wiki-cycle.md) runs both passes as cycle steps, and [`wiki-report`](./wiki-report.md) pulls the lint counts into its summary. [`wiki-promote`](./wiki-promote.md) re-runs the mechanical pass after promoting entries, to confirm the move left no broken links.

**Note:** The full mode reads every file in the wiki, so it costs real time and tokens — that is why it is not the default. Findings are never auto-applied: you approve the fixes, then the mechanical pass re-runs to verify nothing new broke.
