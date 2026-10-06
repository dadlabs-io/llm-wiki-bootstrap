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

**Input / Output:** consumes the pending queue, the URLs you dropped into the configured Google Drive folder, the emails under your Gmail wiki label, and the wiki as it stands. Produces entries staged in `_inbox/proposed/` (`--direct` files straight into `wiki/`) and a run folder, `_inbox/reports/<date>/<cycle_id>/`: one JSON and markdown file per step, the scratchpad, the scope files, the checker's reports and the cycle report. A `cycle_id` is `<YYYY-MM-DD>-<NN>`, which is also what `--resume` takes.

## What each mode runs

| | quick (default) | `--full` | `--ingest-only` | `--discover-only` | `--prompt-for-urls` |
|---|---|---|---|---|---|
| Drive-fetch, when Drive is on | ✓ | ✓ | — | ✓ | — |
| Discover | ✓ | ✓ | — | ✓ | — |
| Email-fetch, when email is on | ✓ | ✓ | — | ✓ | — |
| Your review of discovery's and email's finds | ✓ | ✓ | — | ✓ (then stops) | — |
| Triage | ✓ | ✓ | ✓ | — | — (you chose them) |
| Pages no fetcher can get, when there are any | ✓ | ✓ | ✓ | — | ✓ |
| Ingest, then the staging check | ✓ | ✓ | ✓ | — | ✓ |
| Checker, when a transcript is long | ✓ | ✓ | ✓ | — | ✓ |
| Mechanical lint, backlinks, indexes, map | ✓ | ✓ | ✓ | — | ✓ |
| Semantic lint, fixes, promote | — | ✓ | — | — | — |
| Claims, synthesis, refresh | — | ✓ | — | — | — |
| Report, one commit | ✓ | ✓ | ✓ | ✓ | ✓ |

`--lint-only` runs the mechanical lint (`--semantic` adds the semantic pass), `--claims-only` the claims step, `--refresh-only` the overdue scan, and `--report-only` rebuilds the report from the last run. Modifiers: `<notebook>` (another registered notebook), `--direct`, `--no-confirm-discovery` (no discovery pause, for unattended runs), `--since <hours>`, `--resume <cycle_id>`, `--all-topics`, and `--lint-all` (below).

## The steps you will notice

- **Triage.** Every source waiting in `_inbox/pending/` gets one owner: [`wiki-triage`](./wiki-triage.md) moves it into the bucket whose purpose fits, `_inbox/intake/<folder>/`, and tells the other readers. The cycle then ingests the buckets this project reads, and only those. A notebook with no buckets file has one bucket, `main`, so everything is this project's.
- **Save as PDF.** Instagram posts and reels, Threads, LinkedIn, Notion and Medium are fetched headless on this machine (an Instagram post's caption and every slide's text; a reel's speech transcribed locally with Whisper). A page no fetcher can get (a paywall or member wall, a login, or a site that blocks the fetcher) is never copied out of your browser and never fetched another way: it stays in its bucket, and the report lists it under **Save as PDF** with its link. The report gives the folder to save it into as a full path you can paste into Chrome's Save dialog (usually `...\_inbox\intake\llm-wiki\`; any intake folder or your Drive folder works too). Open the page in Chrome, Print → Save as PDF into that folder, and the next cycle attaches each PDF to the ticket waiting for it, matched by its title, keeping the article's URL, and files it with its full text. A PDF it cannot match, or that fits two tickets equally, is listed for you rather than guessed.
- **Ingest.** The search index is brought up to date first, so the workers' searches see everything filed since it was last built (every promotion also does this). Then [`wiki-ingester`](../agents/wiki-ingester.md) workers, up to four, each running the full [`wiki-update`](./wiki-update.md) flow with its gate. You may be asked which model to use (set in `~/.claude/agents/wiki-ingester-config.json`); a run that cannot ask uses the default and names it. When a batch has several YouTube videos, one worker fetches them one at a time, because parallel subtitle fetches hit YouTube's rate limit. The cycle writes the ingest step's record from the workers' receipts, then checks what they staged with the promote script, since a receipt is a claim.
- **The checker.** Every staged entry whose source is a YouTube transcript of 15 minutes or more is read against that transcript by [`wiki-checker`](../agents/wiki-checker.md), a second agent that never saw the writer's notes and cannot edit anything. It reports claims the transcript does not support, sections the entry skipped, and misquotes. An entry it flags is corrected before promotion or held for you with the report; it is never promoted as flagged. Every check is logged in `_inbox/reports/checker-log.jsonl`, so the pass rate by length shows over time whether the 15-minute line should move (`~/.claude/agents/wiki-checker-config.json`).
- **Semantic lint and claims read what is new.** A `--full` run's semantic lint covers the entries added or revised since the last one, plus this run's staged entries; claims cover the entries with no claims yet, or revised since the index was written. A script decides the scope and writes it to the run folder, and `--lint-all` reads everything instead. A background edit, such as a backlink block, never pulls an entry back in.

## Your two checkpoints

1. **After discovery and email**, the run pauses on what it found. The session has marked every find *recommend* or *skip*, with a reason; you say "approve recommended", or adjust first ("also 14", "drop 7"). A tier-4 source is never approved for you.
2. **The morning review**: `/wiki-report` summarises the run, and `/wiki-promote --review` walks each staged entry, including any the checker held, with its report beside it. The report's last section, **⚠️ Needs you**, lists everything waiting on you (entries to promote, held entries, pages to save as PDF, Drive files left, emails not yet approved, fixes to approve), so you can read it from the bottom.

`--no-confirm-discovery` skips the first for discovery on an unattended run (tiers 1–3 are queued, tier 4 waits); entries still stage for the second. Email always waits for you: an unattended run lists its candidates and recommendations in the report and leaves the emails in the label. A `--full` run promotes its own staged entries (the ones the checker did not hold) before claims and synthesis, which read `wiki/`, and its synthesis changes to your best-practices pages are applied only with your approval; a run nobody is watching writes them as a proposal.

## Drive-fetch

If you enabled Drive ingest at `/new-wiki` time, the cycle starts by pulling URLs from `<parent-folder>/<project-slug>/` in your Drive. URLs are canonicalised (tracking parameters stripped, YouTube links collapsed to `watch?v=<id>`), and one already in the wiki or staged is reported as known, not queued. The rest are queued into `_inbox/pending/`, where triage picks them up. A file that is itself the source (a PDF, a Word, PowerPoint or Excel file, Google Slides or Sheets, an EPUB, an Outlook message, an image) is saved into `raw/` and queued with it. Handled Drive files move to `_completed/<cycle-id>/`; a file whose URL failed to queue stays for the next cycle. A file the cycle cannot read (a note with no link, an audio memo) stays in Drive, and the report names it.

## Email-fetch

With `email.enabled: true` in the project's `.claude/wiki-config.json`, the cycle reads every email under your Gmail label (`email.label`, default `...wiki-inbox`). Newsletters are not hand-picked the way Drive links are, so nothing is queued straight away: every article link becomes a numbered candidate, with tracking redirects followed, tracking parameters stripped, and footer, account, app-store and social-profile links dropped. A full-text newsletter, an email that is itself the article, is one candidate, and if it is approved its text is saved as the raw, so its ingest never fetches it again. Links already in the wiki or the queue are listed as known. When a batch runs past about a hundred candidates, the judging is split across helpers, each given whole emails, and every candidate still needs a decision before anything is queued. After your review, approved candidates are queued and every fetched email moves to the done label (`email.done_label`, default `...wiki-inbox/read`); an email never leaves the label before its links are decided. The first run needs a one-time Gmail sign-in in your browser; [drive-setup](../drive-setup.md) has the steps.

## When steps skip themselves

- Drive-fetch, when Drive ingest is off for the project; email-fetch, when email is off.
- The Save as PDF list, when every page in this project's buckets could be fetched; the checker, when no staged transcript is long enough.
- The link normaliser before the lint, unless entries were promoted during the cycle (`--direct` or `--full`).
- Semantic lint, in quick mode, and in `--full` if one ran in the last 24 hours.
- Refresh, outside `--full` and `--refresh-only`; it then covers overdue entries only.

## Don't

- Don't read the first report of a new install only after promoting: read it first.
- Don't run `--full` every cycle; weekly is enough.
- Don't pass `--direct` on an unattended run: staging exists so a person reviews overnight work.
