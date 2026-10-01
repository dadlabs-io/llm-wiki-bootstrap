---
title: "wiki-cycle — skill"
type: how-to
artifact: skill
name: wiki-cycle
installed_by: install-wiki
date: 2026-09-24
---

# wiki-cycle — skill

Runs a notebook's research pipeline end to end: gather new sources, give each one an owner, ingest this project's share, have a second reader check the long transcripts, lint the wiki, fix what broke, regenerate the indexes and map, and hand you a report. It is the universal interface: the other `wiki-*` maintenance skills are its steps, and you reach them through this command with the right flag. A scratchpad, updated after every step, lets an interrupted cycle resume instead of restarting.

**Trigger:** */wiki-cycle*, plus "run the cycle", "update the wiki", "full wiki update".

**Input / Output:** consumes the pending queue, the URLs you dropped into the configured Google Drive folder, and the wiki as it stands. Produces entries staged in `_inbox/proposed/` (`--direct` files straight into `wiki/`) and a run folder, `_inbox/reports/<date>/<cycle_id>/`: one JSON and markdown file per step, the scratchpad, the scope files, the checker's reports and the cycle report. A `cycle_id` is `<YYYY-MM-DD>-<NN>`, which is also what `--resume` takes.

## What each mode runs

| | quick (default) | `--full` | `--ingest-only` | `--discover-only` | `--prompt-for-urls` |
|---|---|---|---|---|---|
| Drive-fetch, when Drive is on | ✓ | ✓ | — | ✓ | — |
| Discover, then your review | ✓ | ✓ | — | ✓ (then stops) | — |
| Triage | ✓ | ✓ | ✓ | — | — (you chose them) |
| Browser capture, when needed | ✓ | ✓ | ✓ | — | ✓ |
| Ingest, then the staging check | ✓ | ✓ | ✓ | — | ✓ |
| Checker, when a transcript is long | ✓ | ✓ | ✓ | — | ✓ |
| Mechanical lint, backlinks, indexes, map | ✓ | ✓ | ✓ | — | ✓ |
| Semantic lint, fixes, promote | — | ✓ | — | — | — |
| Claims, synthesis, refresh | — | ✓ | — | — | — |
| Report, one commit | ✓ | ✓ | ✓ | ✓ | ✓ |

`--lint-only` runs the mechanical lint (`--semantic` adds the semantic pass), `--claims-only` the claims step, `--refresh-only` the overdue scan, and `--report-only` rebuilds the report from the last run. Modifiers: `<notebook>` (another registered notebook), `--direct`, `--no-confirm-discovery` (no discovery pause, for unattended runs), `--since <hours>`, `--resume <cycle_id>`, `--all-topics`, and `--lint-all` (below).

## The steps you will notice

- **Triage.** Every source waiting in `_inbox/pending/` gets one owner: [`wiki-triage`](./wiki-triage.md) moves it into the bucket whose purpose fits, `_inbox/intake/<folder>/`, and tells the other readers. The cycle then ingests the buckets this project reads, and only those. A notebook with no buckets file has one bucket, `main`, so everything is this project's.
- **Browser capture.** A login-gated page, or a site that refuses a direct fetch, is captured through your signed-in browser before any worker starts, since workers have no browser. A run without a browser leaves such an item in its bucket and says so.
- **Ingest.** [`wiki-ingester`](../agents/wiki-ingester.md) workers, up to four, each running the full [`wiki-update`](./wiki-update.md) flow with its gate. You may be asked which model to use (set in `~/.claude/agents/wiki-ingester-config.json`); a run that cannot ask uses the default and names it. When a batch has several YouTube videos, one worker fetches them one at a time, because parallel subtitle fetches hit YouTube's rate limit. The cycle writes the ingest step's record from the workers' receipts, then checks what they staged with the promote script, since a receipt is a claim.
- **The checker.** Every staged entry whose source is a YouTube transcript of 15 minutes or more is read against that transcript by [`wiki-checker`](../agents/wiki-checker.md), a second agent that never saw the writer's notes and cannot edit anything. It reports claims the transcript does not support, sections the entry skipped, and misquotes. An entry it flags is corrected before promotion or held for you with the report; it is never promoted as flagged. Every check is logged in `_inbox/reports/checker-log.jsonl`, so the pass rate by length shows over time whether the 15-minute line should move (`~/.claude/agents/wiki-checker-config.json`).
- **Semantic lint and claims read what is new.** A `--full` run's semantic lint covers the entries added or revised since the last one, plus this run's staged entries; claims cover the entries with no claims yet, or revised since the index was written. A script decides the scope and writes it to the run folder, and `--lint-all` reads everything instead. A background edit, such as a backlink block, never pulls an entry back in.

## Your two checkpoints

1. **After discovery**, the run pauses on what was queued, skipped and deferred; you say go or edit the list. A tier-4 source is never approved for you.
2. **The morning review**: `/wiki-report` summarises the run, and `/wiki-promote --review` walks each staged entry, including any the checker held, with its report beside it.

`--no-confirm-discovery` skips the first for an unattended run; entries still stage for the second. A `--full` run promotes its own staged entries (the ones the checker did not hold) before claims and synthesis, which read `wiki/`, and its synthesis changes to your best-practices pages are applied only with your approval; a run nobody is watching writes them as a proposal.

## Drive-fetch

If you enabled Drive ingest at `/new-wiki` time, the cycle starts by pulling URLs from `<parent-folder>/<project-slug>/` in your Drive. URLs are canonicalised (tracking parameters stripped, YouTube links collapsed to `watch?v=<id>`), and one already in the wiki or staged is reported as known, not queued. The rest are queued into `_inbox/pending/`, where triage picks them up. Handled Drive files move to `_completed/<cycle-id>/`; a file whose URL failed to queue stays for the next cycle.

## When steps skip themselves

- Drive-fetch, when Drive ingest is off for the project.
- Browser capture, when nothing in this project's buckets needs it; the checker, when no staged transcript is long enough.
- The link normaliser before the lint, unless entries were promoted during the cycle (`--direct` or `--full`).
- Semantic lint, in quick mode, and in `--full` if one ran in the last 24 hours.
- Refresh, outside `--full` and `--refresh-only`; it then covers overdue entries only.

## Don't

- Don't read the first report of a new install only after promoting: read it first.
- Don't run `--full` every cycle; weekly is enough.
- Don't pass `--direct` on an unattended run: staging exists so a person reviews overnight work.
