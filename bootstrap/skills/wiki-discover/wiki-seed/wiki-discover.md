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

**Trigger:** runs as the first step of [`wiki-cycle`](./wiki-cycle.md) (or `/wiki-cycle --discover-only`); you can also type */wiki-discover*. It has no natural-language trigger phrases. Flags narrow the search: `--voices` for blogs and YouTube, `--academic`, `--repos`, `--feed "<name>"` for a single source, `--query "..."` for an ad-hoc search, `--gaps` to hunt for known concept gaps, `--all-feeds` to search every feed, and `--backfill <YYYY-MM-DD>` (with `--feed`) to extend a feed's coverage backwards.

**Input / Output:** Reads `_config/feeds.md` (beside `wiki/` in the notebook root), which lists your trusted authors, YouTube channels, GitHub repos, academic queries and vendor blogs, each with the date range already covered. Produces a dated checklist grouping candidates by HIGH and MEDIUM relevance with a one-line reason each.
There is one checklist, at `_inbox/discovered/<date>-discovery.md`, with the stats at the top and the decisions log (Queued, Skipped, Deferred, with the reason for every URL) as its last section; once processed it moves to `_inbox/done/`.

After each feed is searched (even with no hits) its last-queried date is set to today, so the next run starts from there; `--query` runs don't touch it, and `--backfill` moves the feed's start date back instead. Approved candidates are queued to `_inbox/pending/`, and [`wiki-triage`](./wiki-triage.md) gives each one an owner: discovery itself never decides who reads what.

**How it searches and filters:**
- Each feed is searched only for material newer than its last-queried date, and never before 2026-01-01, even with `--backfill`. The search tool is web search; results published before the window are dropped, and one whose date cannot be established is deferred.
- A candidate is a duplicate if its URL is already an entry's source, if a full search of this notebook finds the concept already covered, or if the URL is already in the pending or done queue.
- LOW-relevance candidates are dropped unless they come from a tier-1 source, and tier-4 candidates are labelled NEEDS HUMAN REVIEW. Tiers are defined in your notebook's frontmatter spec (`wiki/project/best-practices/framework/wiki-frontmatter-best-practices.md`).

**Works with:** approved candidates go onto the queue managed by [`wiki-list`](./wiki-list.md), from which they are ingested. [`wiki-report`](./wiki-report.md) lists the discovery checklists, so you can see what was rejected and why.

**When it stops or skips:** a run covers six feeds, oldest-queried first, so successive runs cycle through all your sources; `--feed` ignores the cap and `--all-feeds` lifts it. Zero results for a feed is a normal outcome — nothing new since the last check. With no `_config/feeds.md` it stops, says so and offers to create one from the template; a `--feed` name that matches several feeds lists them and asks which. It never ingests anything.
