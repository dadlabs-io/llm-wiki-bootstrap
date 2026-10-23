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

**Input / Output:** consumes the pending queue, the URLs you dropped into the configured Google Drive folder, the emails under your Gmail wiki label, and the wiki as it stands. Produces new entries, staged in `_inbox/proposed/` and then promoted or left for you by the notebook's `confirm_before_promote` (below), and a run folder, `_inbox/reports/<date>/<cycle_id>/`: one JSON and markdown file per step, the scratchpad, the scope files, the checker's reports and the cycle report. Nothing else: the helper agents keep their working files in scratch folders outside the notebook, and any left over are deleted before the commit (2026-10-23). A `cycle_id` is `<YYYY-MM-DD>-<NN>`, which is also what `--resume` takes.

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
| Checker, when a transcript is long, a source is big, or the spot check picks an entry | ✓ | ✓ | ✓ | — | ✓ |
| Mechanical lint, backlinks, indexes, map | ✓ | ✓ | ✓ | — | ✓ |
| Semantic lint, fixes | — | ✓ | — | — | — |
| Promote, when `confirm_before_promote` is false | ✓ | ✓ | ✓ | — | ✓ |
| Hubs, when a hub page misses an entry carrying its tag | ✓ | ✓ | ✓ | — | ✓ |
| Claims, refresh | — | ✓ | — | — | — |
| Best-practices synthesis, when research entries reached the wiki since the last one | ✓ | ✓ | ✓ | — | ✓ |
| Report, one commit | ✓ | ✓ | ✓ | ✓ | ✓ |

`--lint-only` runs the mechanical lint (`--semantic` adds the semantic pass), `--claims-only` the claims step, `--refresh-only` the overdue scan, and `--report-only` rebuilds the report from the last run. Modifiers: `<notebook>` (another registered notebook), `--direct`, `--no-confirm-discovery` (no discovery pause, for unattended runs), `--since <hours>`, `--resume <cycle_id>`, `--all-topics`, and `--lint-all` (below).

## The steps you will notice

- **Triage.** Every source waiting in `_inbox/pending/` gets one owner: [`wiki-triage`](./wiki-triage.md) moves it into the bucket whose purpose fits, `_inbox/intake/<folder>/`, and tells the other readers. The cycle then ingests the buckets this project reads, and only those. A notebook with no buckets file has one bucket, `main`, so everything is this project's.
- **Save as PDF.** Instagram posts and reels, Threads, LinkedIn, Notion and Medium are fetched headless on this machine (an Instagram post's caption, every slide image, and each slide's text where Instagram recognised any; a reel's speech transcribed locally with Whisper). A page no fetcher can get (a paywall or member wall, a login, or a site that blocks the fetcher) is never copied out of your browser and never fetched another way: it stays in its bucket, and the report lists it under **Save as PDF** with its link. The report gives the folder to save it into as a full path you can paste into Chrome's Save dialog (usually `...\_inbox\intake\llm-wiki\`; any intake folder or your Drive folder works too). Open the page in Chrome, Print → Save as PDF into that folder, and the next cycle attaches each PDF to the ticket waiting for it, matched by its title, keeping the article's URL, and files it with its full text. A PDF it cannot match, or that fits two tickets equally, is listed for you rather than guessed.
- **Ingest.** The search index is brought up to date first, so the workers' searches see everything filed since it was last built (every promotion also does this). Then [`wiki-ingester`](../agents/wiki-ingester.md) workers, up to four, each running the full [`wiki-update`](./wiki-update.md) flow with its gate. Their model is set in `~/.claude/agents/wiki-ingester-config.json` and used without asking (since 2026-10-22; say so if you want to pick it for a run), and the cycle's record names it. Long transcripts (as long as the checker's 15-minute line or longer) go to Opus workers and everything else to that model: in a blind comparison on five talks (2026-10-14) Opus's drafts needed about 40% fewer fixes and skipped no part of a talk. When a batch has several YouTube videos, one worker fetches them one at a time, because parallel subtitle fetches hit YouTube's rate limit. If YouTube refuses the subtitles anyway (HTTP 429), the fetcher transcribes the talk's audio locally with Whisper instead (2026-10-15: the limit held for days across three cycles, while the audio download was never limited). An item that still could not be fetched for a reason that may clear stays in its bucket marked for retry, and the cycle puts one card on the task list of that bucket's reader naming each one, so it is not forgotten when the next cycle is another project's. A raw too big for one worker (`wiki-raw-parts.py` says it does not fit: a whole repository, a book) is never filed from part of it: the cycle splits it along its headings, sends one reader per part, then has an Opus worker file the entry from the readers' reports (2026-10-17). The cycle writes the ingest step's record from the workers' receipts, then checks what they staged with the promote script, since a receipt is a claim.
- **The checker.** Every staged entry whose source is a transcript of 15 minutes or more (YouTube captions, or a Whisper transcript of a podcast, reel or video), whose source is 60 KB or more (a long PDF, a whole repository; since 2026-10-23), or that the 1-in-10 spot check of the rest picks, is read against that source by [`wiki-checker`](../agents/wiki-checker.md), a second agent that never saw the writer's notes and cannot edit anything. It reports claims the transcript does not support, sections the entry skipped, misquotes, and passages vaguer than the transcript where its specifics matter. An entry it flags is corrected before promotion or held for you with the report; it is never promoted as flagged. Every check is logged in `_inbox/reports/checker-log.jsonl`, so the pass rate by length shows over time whether the 15-minute line should move (`~/.claude/agents/wiki-checker-config.json`).
- **Hubs.** A hub page gathers one topic from across folders (agentic-design's Obsidian hub) and names the tag it collects with `hub_tag` in its frontmatter. After promotion, every entry carrying that tag that the hub does not link yet gets one line on it, under the heading that fits, written from the entry's TL;DR; the hub's other lines are never reordered or rewritten, and the report names the lines added (2026-10-23).
- **Semantic lint and claims read what is new.** A `--full` run's semantic lint covers the entries added or revised since the last one, plus this run's staged entries; claims cover the entries with no claims yet, or revised since the index was written. A script decides the scope and writes it to the run folder, and `--lint-all` reads everything instead. A background edit, such as a backlink block, never pulls an entry back in.
- **Best-practices synthesis, in every cycle that ingests.** Helpers read the research entries that reached the wiki since the last synthesis you answered (promoted between cycles counts) against your best-practices pages, and propose confirmations, dated watch-notes or doctrine changes; nothing changes those pages without your approval. A run nobody can answer leaves its proposal in the report, and those entries come round again next cycle. (Until 2026-10-19 synthesis ran only in `--full`, and six ingest-only cycles left agentic-design's best practices 107 entries behind.)
- **Cost.** The report's header says what the run cost: the session's running total (Claude Code's own estimate at API prices, subagents included; on a subscription plan a figure for comparing runs, not a bill) at the start and at the end, and the difference. The total comes from a file the status line writes, `~/.claude/session-cost/<session_id>.json` with `session_id`, `cwd` and `total_cost_usd` (the status line receives these from Claude Code); without that file the report says the cost was not checked.
- **Helper models.** The semantic lint and fix agents of a `--full` run, and the synthesis agents of any run, run on Sonnet, set per step in `helper-models.json` beside the skill (`semantic_lint`, `lint_fixes`, `synthesis`). A blind comparison on a real notebook found Sonnet as good as Opus there for under half the cost; its lint reports more findings that turn out wrong, and your approval before any fix is where those are dropped. Change a value to `opus` to switch a step back. Every run starts by printing the model of each kind of helper, read from these files and the ingester's and checker's own, and spawns from that list; a file it cannot read is named in the report. (Before this, a cycle asked to read the files often skipped them and used the agent's own default, which would have hidden a change to a setting.)

## Your two checkpoints

1. **After discovery and email**, the run pauses on what it found. The session has marked every find *recommend* or *skip*, with a reason; you say "approve recommended", or adjust first ("also 14", "drop 7"). A tier-4 source is never approved for you.
2. **The morning review**: `/wiki-report` summarises the run, and `/wiki-promote --review` walks each staged entry, including any the checker held, with its report beside it. The report's last section, **⚠️ Needs you**, lists everything waiting on you (entries to promote, held entries, pages to save as PDF, items left for retry and the card each went to, Drive files left, emails not yet approved, fixes to approve), so you can read it from the bottom.

`--no-confirm-discovery` skips the first for discovery on an unattended run (tiers 1–3 are queued, tier 4 waits); entries still stage for the second. Email always waits for you: an unattended run lists its candidates and recommendations in the report and leaves the emails in the label. **Whether new entries are promoted is the notebook's `confirm_before_promote`**, the same setting [`wrap-up`](./wrap-up.md) and [`wiki-update`](./wiki-update.md) follow, printed at the start of every run: `true` (the default) → nothing is promoted, in any mode, watched or not; the entries wait for your `/wiki-promote`, and claims and synthesis leave them out until then. `false` → every mode that ingests promotes the entries the checker did not hold, in one promotion run so the notebook is rebuilt once, before claims and synthesis, which read `wiki/`. (Until 2026-10-19 the cycle ignored the setting: `--full` always promoted, every other mode never did.) Synthesis changes to your best-practices pages, in any mode, are applied only with your approval; a run nobody is watching writes them as a proposal.

## Drive-fetch

If you enabled Drive ingest at `/new-wiki` time, the cycle starts by pulling URLs from `<parent-folder>/<project-slug>/` in your Drive. URLs are canonicalised (tracking parameters stripped, YouTube links collapsed to `watch?v=<id>`), and one already in the wiki or staged is reported as known, not queued. The rest are queued into `_inbox/pending/`, where triage picks them up. A file that is itself the source (a PDF, a Word, PowerPoint or Excel file, Google Slides or Sheets, an EPUB, an Outlook message, an image) is saved into `raw/` and queued with it. Handled Drive files move to `_completed/<cycle-id>/`; a file whose URL failed to queue stays for the next cycle. A file the cycle cannot read (a note with no link, an audio memo) stays in Drive, and the report names it.

## Email-fetch

With `email.enabled: true` in the project's `.claude/wiki-config.json`, the cycle reads every email under your Gmail label (`email.label`, default `...wiki-inbox`). Newsletters are not hand-picked the way Drive links are, so nothing is queued straight away: every article link becomes a numbered candidate, with tracking redirects followed (Towards Data Science's tracker too, which answers with a page rather than a redirect), tracking parameters stripped, and footer, account, app-store, social-profile, author and tag links dropped. A tracking link that cannot be followed, a rate limit included, is listed with its reason rather than offered; it is never worked around. A full-text newsletter, an email that is itself the article, is one candidate, and if it is approved its text is saved as the raw, so its ingest never fetches it again. Links already in the wiki or the queue are listed as known. When a batch runs past about a hundred candidates, the judging is split across helpers, each given whole emails, and every candidate still needs a decision before anything is queued. After your review, approved candidates are queued and every fetched email moves to the done label (`email.done_label`, default `...wiki-inbox/read`); an email never leaves the label before its links are decided. The first run needs a one-time Gmail sign-in in your browser; [drive-setup](../drive-setup.md) has the steps.

## When steps skip themselves

- Drive-fetch, when Drive ingest is off for the project; email-fetch, when email is off.
- The Save as PDF list, when every page in this project's buckets could be fetched; the checker, when no staged entry is a long transcript or a big source and the spot check picks none.
- The link normaliser before the lint, unless `--direct` filed entries during the cycle (a promotion fixes its own entries' links).
- Semantic lint, in quick mode, and in `--full` if one ran in the last 24 hours.
- Refresh, outside `--full` and `--refresh-only`; it then covers overdue entries only.

## Don't

- Don't read the first report of a new install only after promoting: read it first.
- Don't run `--full` every cycle; weekly is enough.
- Don't pass `--direct` on an unattended run: it files entries before the checker reads them and overrides the notebook's `confirm_before_promote`.
