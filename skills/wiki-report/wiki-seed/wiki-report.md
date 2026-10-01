---
title: "wiki-report — skill"
type: how-to
artifact: skill
name: wiki-report
installed_by: install-wiki
date: 2026-07-31
---

# wiki-report — skill

A single-page morning report on the state of the wiki: what changed, what's queued, what needs attention, and what to do next. It exists so review can be a batch activity — you read one page and give direction, instead of approving each ingested item one at a time. It never changes a wiki entry: the only files it writes are its own report and, when run on its own, the lint report that its mechanical lint pass refreshes.

**Trigger:** */wiki-report* — also "morning report", "wiki status", "what changed in the wiki", "show me the wiki health". Takes an optional topic, `--since <date>` (default: the last seven days), and `--brief` for counts and recommendations only.

**Input / Output:** Run as part of a full cycle, it assembles the report from the per-step JSON files that cycle's steps wrote, rather than re-running any of them. Run on its own, it gathers its own data: recent commits, entry counts, a fast mechanical lint, the sizes of the pending, proposed, and discovered queues, and the entries whose `review_after` date has passed. The report covers what changed, the pending work, what needs attention (overdue entries, contradictions from the latest claims report, lint counts, open concept gaps), and a best-practices gap analysis: practices a recent entry recommends that the project does not follow yet (NEW), components documented as built that have drifted (DRIFT), and better approaches the wiki now documents (UPGRADE). It writes a markdown report plus a JSON aggregate under `_inbox/reports/<date>/<cycle-id>/` (`_inbox/` sits beside `wiki/` at the notebook root), and prints the report inline — it is meant to be read, not filed and forgotten.

**When it skips itself:** it never runs the expensive semantic lint; it cites the latest existing report instead. With no claims report yet it says so and suggests [`wiki-claims`](./wiki-claims.md). Status pages a wiki does not have (a cycle overview, a getting-started status table) are skipped.

**Works with:** [`wiki-cycle`](./wiki-cycle.md) invokes it as the cycle's last step before the commit and supplies the per-step JSONs. It summarizes output from [`wiki-lint`](./wiki-lint.md) for health counts, [`wiki-refresh`](./wiki-refresh.md) for stale entries, [`wiki-claims`](./wiki-claims.md) for contradictions, [`wiki-discover`](./wiki-discover.md) for candidate decisions, [`wiki-list`](./wiki-list.md) for the pending queue, and [`wiki-promote`](./wiki-promote.md) for entries awaiting approval.

**Note:** The report ends with at most five concrete recommendations and stops there — it is a review checkpoint, not an automation trigger, so it never acts on what it finds.
