---
title: "wiki-report — skill"
type: how-to
artifact: skill
name: wiki-report
installed_by: install-wiki
date: 2026-07-31
---

# wiki-report — skill

A single-page morning report on the state of the wiki: what changed, what's queued, what needs attention, and what to do next. It exists so review can be a batch activity — you read one page and give direction, instead of approving each ingested item one at a time. Everything it does is read-only.

**Trigger:** */wiki-report* — also "morning report", "wiki status", "what changed in the wiki", "show me the wiki health". Takes an optional topic, `--since <date>` (default: the last seven days), and `--brief` for counts and recommendations only.

**Input / Output:** Run as part of a full cycle, it assembles the report from the per-step JSON files that cycle's steps wrote, rather than re-running any of them. Run on its own, it gathers its own data: recent commits, entry counts, a fast mechanical lint, and the sizes of the pending, proposed, and discovered queues. It writes a markdown report plus a JSON aggregate under `_inbox/reports/<date>/<cycle-id>/`, and prints the report inline — it is meant to be read, not filed and forgotten.

**Works with:** [`wiki-cycle`](./wiki-cycle.md) invokes it as the final step and supplies the per-step JSONs. It summarizes output from [`wiki-lint`](./wiki-lint.md) for health counts, [`wiki-refresh`](./wiki-refresh.md) for stale entries, [`wiki-claims`](./wiki-claims.md) for contradictions, [`wiki-discover`](./wiki-discover.md) for candidate decisions, [`wiki-list`](./wiki-list.md) for the pending queue, and [`wiki-promote`](./wiki-promote.md) for entries awaiting approval.

**Note:** The report ends with at most five concrete recommendations and stops there — it is a review checkpoint, not an automation trigger, so it never acts on what it finds.
