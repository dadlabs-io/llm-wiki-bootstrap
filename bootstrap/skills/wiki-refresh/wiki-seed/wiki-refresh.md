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

**Trigger:** */wiki-refresh* — also "check for stale entries", "what needs updating", "decay scan". Narrow the scan with `--overdue-only`, `--low-confidence` (entries marked low or medium), `--high-value` (entries with five or more inbound links), `--tier <N>`, or `--dry-run` (report only, no offer to fix).

**Input / Output:** Reads the frontmatter of every entry under `wiki/` — `date`, `last_reviewed`, `review_after`, `tier`, `confidence`, `source_url` — plus a count of inbound links. It also reads the installed skill definitions, which carry the same review dates plus the model they were last reviewed for. Writes `_inbox/reports/refresh-report-<date>.md` (the `_inbox/` beside `wiki/`), grouping flagged entries into overdue, low confidence, unverified community sources, high-value aging, and sources that may have changed, each row carrying a suggested action, plus a Skills section listing each skill as overdue, model drift, unstamped or ok. If you confirm a batch is still accurate, it updates `last_reviewed` and recalculates `review_after` from the review cadence in your notebook's frontmatter spec (`wiki/project/best-practices/framework/wiki-frontmatter-best-practices.md`), the one place the offsets are defined.

**Works with:** [`wiki-cycle`](./wiki-cycle.md) runs it, for overdue entries only, in `--full` and `--refresh-only`; otherwise the intended rhythm is one pass a month. [`wiki-report`](./wiki-report.md) draws its stale-entries section from this scan inside a cycle (standalone it checks `review_after` dates itself). Entries whose source has changed substantially go back through [`wiki-update`](./wiki-update.md) for re-synthesis.

**Note:** "Overdue" means the scheduled review hasn't happened, not that the entry is wrong. Nothing is deleted or rewritten, and no source is re-fetched, without your say-so. Skill files are only reported, never edited; a skill is re-reviewed where it is maintained. The scan skips raw source files and `sessions/`, which carry no review lifecycle.
