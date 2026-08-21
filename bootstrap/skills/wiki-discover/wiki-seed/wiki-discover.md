---
title: "wiki-discover — skill"
type: how-to
artifact: skill
name: wiki-discover
installed_by: install-wiki
date: 2026-07-31
---

# wiki-discover — skill

Finds new material worth adding to your wiki without you having to go looking for it. It searches the sources you have declared trustworthy, discards anything the wiki already covers, and hands you a checklist of candidates to approve or reject. Nothing is ingested automatically — discovery only proposes.

**Trigger:** */wiki-discover* — also "discover new content", "search the trusted feeds", "find candidates for the wiki". Flags narrow the search: `--voices` for blogs and YouTube, `--academic`, `--repos`, `--feed "<name>"` for a single source, `--query "..."` for an ad-hoc search, and `--gaps` to hunt specifically for known concept gaps.

**Input / Output:** Reads `_config/feeds.md`, which lists your trusted authors, YouTube channels, GitHub repos, academic queries, and vendor blogs along with each feed's covered date range. Produces a dated checklist at `_inbox/discovered/<date>-discovery.md` grouping candidates by HIGH and MEDIUM relevance with a one-line reason each, plus a three-section decisions log — Queued, Skipped, Deferred — recording why every URL was or wasn't taken. Approved candidates are queued to `_inbox/pending/`, and each searched feed's last-queried date is advanced so the next run picks up where this one stopped.

**Works with:** approved candidates go onto the queue managed by [`wiki-list`](./wiki-list.md), which later hands them to [`wiki-update`](./wiki-update.md) for ingestion. [`wiki-cycle`](./wiki-cycle.md) runs discovery as its first step, and [`wiki-report`](./wiki-report.md) surfaces the decisions log so you can see what was rejected and why.

**Note:** A run caps at six feeds, chosen oldest-queried-first, so successive runs cycle through all your sources rather than repeatedly hitting the same few. Zero results for a feed is a normal outcome, not a failure — it means nothing new since the last check.
