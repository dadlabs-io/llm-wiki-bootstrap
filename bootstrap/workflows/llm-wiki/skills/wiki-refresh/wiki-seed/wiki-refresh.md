---
title: "wiki-refresh — skill"
type: how-to
artifact: skill
name: wiki-refresh
installed_by: install-wiki
date: 2026-07-31
---

# wiki-refresh — skill

The maintenance counterpart to discovery: instead of asking what's new, it asks what's gone stale. It scans the lifecycle metadata on every entry and flags the ones past their review date, the ones marked low-confidence, the community-sourced ones nobody has corroborated, and the heavily-linked ones that are quietly aging. It reports and suggests; it does not rewrite your wiki.

**Trigger:** */wiki-refresh* — also "check for stale entries", "what needs updating", "decay scan". Narrow the scan with `--overdue-only`, `--low-confidence`, `--high-value` (entries with five or more inbound links), `--tier <N>`, or `--dry-run`.

**Input / Output:** Reads the frontmatter of every entry under `wiki/` — `date`, `last_reviewed`, `review_after`, `tier`, `confidence`, `source_url` — plus a count of inbound links. Writes `_inbox/reports/refresh-report-<date>.md`, grouping flagged entries into overdue, low confidence, unverified community sources, high-value aging, and sources that may have changed, each row carrying a suggested action. If you confirm a batch is still accurate, it updates `last_reviewed` and recalculates `review_after` on a per-tier interval, from six months for papers down to two months for community sources.

**Works with:** [`wiki-report`](./wiki-report.md) draws its stale-entries section from this scan, and [`wiki-cycle`](./wiki-cycle.md) runs it as a cycle step so every run spends part of its budget maintaining old entries rather than only chasing new ones. Entries whose source has changed substantially go back through [`wiki-update`](./wiki-update.md) for re-synthesis.

**Note:** "Overdue" means the scheduled review hasn't happened, not that the entry is wrong. Nothing is deleted or rewritten without your say-so, and the scan deliberately skips raw source files and `sessions/`, which carry no review lifecycle.
