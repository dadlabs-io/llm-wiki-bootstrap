---
name: wiki-discover
description: Discover new content for a topic wiki by searching trusted feeds, deduping against existing entries, and queuing candidates for human review.
---

> **⚙️ Internal skill.** This is invoked by `/wiki-cycle` (the orchestrator) — users normally don't call it directly. Public-facing commands are `/wiki-cycle`, `/wiki-update`, `/wiki-search`, `/wiki-init`. This skill is documented + callable for programmatic use.

# /wiki-discover

Search trusted sources for new content relevant to a topic wiki. Dedupes against existing entries, queues candidates to `_inbox/discovered/`, and generates a review checklist.

## Usage

```
/wiki-discover                          # configured default topic, all feeds
/wiki-discover <topic>                  # specific topic
/wiki-discover <topic> --voices         # trusted voices only (blogs, YouTube)
/wiki-discover <topic> --academic       # arxiv/papers only
/wiki-discover <topic> --repos          # GitHub repos only
/wiki-discover <topic> --feed "<name>"  # single feed by author/source name (substring match against feeds.md row)
/wiki-discover <topic> --query "custom search terms"   # ad-hoc query instead of feeds
/wiki-discover <topic> --gaps           # search specifically for concept-gaps entries

# Combine with --backfill <YYYY-MM-DD> to push coverage backward, e.g.:
/wiki-discover agentic-design --feed "Boris Cherny" --backfill 2026-01-01
```

## What You Must Do When Invoked

### Step 1 — Load the feeds config

Read `llm-wiki/wiki/_config/feeds.md`. This file defines:
- Trusted authors/blogs with URLs, tiers, and keywords
- YouTube channels to check
- GitHub repos to watch
- Academic search queries
- Vendor/platform blogs
- Community sources (lower trust, human-approve only)

If the feeds config doesn't exist for the topic, tell the user and offer to create one from the topic-template (shipped with llm-wiki).

### Step 2 — Determine which feeds to search

**Default ordering: staleness-first.** Sort all eligible feeds by `To` ascending (oldest-queried first; `To = —` / never-queried sorts earliest). Take the top 6 per the per-run cap. Over ~6 runs every feed cycles through, with the feeds that have the longest coverage gap always getting priority.

**Common bug**: agents have repeatedly mis-sorted `To = —` as "exclude" rather than "earliest". Cycle 2026-05-06-01's discover agent skipped 11 never-queried feeds (Cole Medin, agentmemory, OpenClaw, Letta, Mem0, Graphiti, qmd, n8n, KDnuggets, AnalyticsVidhya, HN, DEV Community) in favor of feeds with `To: 2026-04-23` already populated. **`—` MUST sort to position 0** (highest priority). When in doubt, take the never-queried feeds first explicitly.

Based on the flags:
- No flag → search ALL feed categories, staleness-ordered, cap at 6
- `--voices` → Blogs & Newsletters + YouTube Channels only, staleness-ordered
- `--academic` → Academic / ArXiv only, staleness-ordered
- `--repos` → GitHub Repos & Projects only, staleness-ordered
- `--feed "<name>"` → **single feed only** by case-insensitive substring match against the feed's first column (Author / Creator / Project / Query / Vendor / Source). E.g., `--feed "Boris Cherny"` matches the YouTube row "Boris Cherny" but not the Blog row "Hamel Husain". If the substring matches multiple rows, fail with a list and ask user to disambiguate. Cap-of-6 ignored — explicit single-feed runs are deliberate.
- `--query "..."` → skip feeds, run this custom query via WebSearch (does NOT update feeds.md `To` columns — ad-hoc only)
- `--gaps` → read `concept-gaps-things-mentioned-not-yet-covered.md`, search for each P1-P3 gap
- `--all-feeds` → override the 6-cap; search every feed (expensive, only for bootstrap/catch-up)

**`--feed` is the right flag for backfill runs**, since backfill is per-feed by design (low-cadence creators benefit; high-cadence vendor blogs don't). Pair `--feed <name> --backfill <YYYY-MM-DD>` for targeted historical coverage extension.

### Step 3 — Search each feed with date-filtered queries

**Primary tool**: `mcp__Exa-ai__web_search_exa` — returns structured result objects (distinct `title`, `url`, `published`, `author` fields). Use this by default.

**Fallback**: `WebSearch` if Exa is unavailable.

**Date filtering (mandatory)** — every Exa call must include:
- `publishedAfter`: the feed's `To` date if set in feeds.md, else the feed's `From` date, else the global anchor `2026-03-14`
- `publishedBefore`: today

Rationale: each feed tracks its own covered range via `From` (earliest covered) and `To` (last queried). Normal discovery queries only content newer than `To`. Empty results mean "nothing new since last check" — a legitimate outcome, not a failure.

**Per feed**:

```
mcp__Exa-ai__web_search_exa:
  query: "<author name> <keywords>"
  publishedAfter: <feed.To || feed.From || "2026-03-14">
  publishedBefore: <today>
```

Batch related queries for efficiency (not for an arbitrary cap). Example: don't run "Simon Willison agents" and "Simon Willison Claude" separately — combine into one query.

**YouTube feeds**: search with `site:youtube.com` or use the channel URL pattern. For transcript fetching, the actual ingest (not discovery) uses `wiki-fetch-youtube.py` — discovery only finds URLs.

**Empty result is valid.** If `publishedAfter → now` returns zero candidates for a feed, record `0 new hits since <feed.To>` and move on. Do NOT auto-walk-back — the `--backfill` flag (below) is the deliberate mechanism for extending coverage backward.

**After a successful search** (even with zero hits): update the feed's `To` column in feeds.md to today's date. Next run's window starts from today forward.

**Backfill mode** (`--backfill <YYYY-MM-DD>`): queries `(target_date, feed.From)` range. On success, updates `feed.From = target_date` (pushes covered range backward). Use this when a low-cadence creator has valuable content before our current coverage starts (e.g., IndyDevDan's Feb/Mar videos before our 2026-03-14 anchor).

**Hard floor**: `publishedAfter` never goes before **2026-01-01**, even with `--backfill`. AI tooling pre-2026 is mostly superseded; anchor-style ingests of older material (Karpathy posts, MemGPT paper, etc.) should use `/wiki-update <url>` directly, not the discovery pipeline.

**Optional `--empty-fallback`**: if the initial window is empty, walk back one month and retry (capped by the 2026-01-01 floor). Off by default; useful for exploratory manual runs, never for automated cycles.

### Step 4 — Dedup against existing wiki

For each candidate URL/title found in search results:

1. **URL dedup**: check if the exact URL exists in any wiki entry's `source_url` frontmatter:
   ```bash
   grep -r "<url>" llm-wiki/wiki/ --include="*.md" -l
   ```

2. **Title/concept dedup**: search the wiki for the key concept:
   ```bash
   qmd query "<key terms from the candidate>"
   ```
   If qmd returns a 80%+ match, the concept is already covered — skip unless the new source adds substantial new information.

3. **Queue dedup**: check if the URL is already in `_inbox/pending/` or `_inbox/done/`:
   ```bash
   grep -r "<url>" llm-wiki/wiki/_inbox/ --include="*.md" -l
   ```

### Step 5 — Score and classify candidates

**CRITICAL — pairing rule**: each candidate is ONE SEARCH-RESULT OBJECT. The title and URL MUST come from the SAME result object. Never pair a title from result N with a URL from result M — this is the single most common bug (2026-04-16 cycle produced 3 of 4 queue URLs mislabeled because of this). If using Exa, walk the returned `results` array one object at a time. If using WebSearch, each result block is a single unit — don't cross fields.

For each candidate that passes dedup, extract fields from a single search-result object:

| Field | How to determine |
|---|---|
| **Title** | From the result's `title` field (Exa) or title line (WebSearch). NOT a reconstructed title. |
| **URL** | From the SAME result object's `url` field. NEVER from a different result. |
| **Tier** | From the feed config's default tier for this source |
| **Relevance** | HIGH (directly addresses a wiki concept or gap), MEDIUM (related to wiki topics), LOW (tangentially connected) |
| **Why** | One sentence: what slot does this fill in the wiki? |

**Pairing verification (mandatory before Step 6)**: for the first 2-3 candidates, confirm:
- Title keywords appear in the URL slug, OR
- URL domain matches the expected feed source (e.g., Simon Willison result URL contains `simonwillison.net`)

If a pairing looks wrong, re-examine the source search result. Do NOT queue mismatched pairs.

**Drop** any candidate with relevance LOW unless it's from a tier 1 source.

### Step 6 — Generate the discovery checklist

Write a markdown file to `_inbox/discovered/<date>-discovery.md`:

```markdown
# Discovery Queue — <date>

**Topic**: <topic>
**Feeds searched**: <count>
**Candidates found**: <count>
**After dedup**: <count>
**Queries used**: <list the WebSearch queries run>

## Candidates

### HIGH relevance

- [ ] [Title](url) — tier N — **Why**: fills the X slot
- [ ] [Title](url) — tier N — **Why**: updates our understanding of Y

### MEDIUM relevance

- [ ] [Title](url) — tier N — **Why**: related to Z
- [ ] [Title](url) — tier N — **Why**: new perspective on W

## Concept gaps searched (if --gaps flag)

| Gap | Priority | Found? | Candidate |
|---|---|---|---|
| A2A protocol | 3 | Yes/No | [link if found] |

## Decisions log

Every discovery run ends with this three-section ledger. Fill in progressively — each section uses the same columns so the morning report can consolidate them uniformly.

### Queued

| Priority | URL | Reason | Timestamp |
|---|---|---|---|
| P2 | https://... | Tier 1-2 primary source; fills X slot | 2026-04-23T18:45Z |

### Skipped

| Priority | URL | Reason | Timestamp |
|---|---|---|---|
| — | https://... | SEO listicle, no new technique | 2026-04-23T18:47Z |
| — | https://... | Already covered by `<existing-entry-slug>` | 2026-04-23T18:47Z |

### Deferred

| Priority | URL | Reason | Timestamp |
|---|---|---|---|
| P3 | https://... | URL returned SOURCE_NOT_AVAILABLE; retry next cycle | 2026-04-23T18:50Z |
```

**Why three sections instead of a single "Decision" column**: the morning report can point users directly at a section they care about ("what did we reject and why"). Easier to scan, easier to tweak — if a Skipped row should actually be queued, just move it into Queued and re-run ingestion.

### Return format (cycle contract)

When invoked inside `/wiki-cycle`, this skill writes `<run-folder>/discover.json` and `discover.md` per the [Cycle Step Return Format contract](./best-practices/framework/cycle-step-return-format.md).


### Step 7 — Queue approved candidates

After the user reviews the checklist (human review #1), queue the approved items:

```bash
python .claude/wiki-scripts/wiki-list-add.py \
  --topic <topic> --vault llm-wiki/wiki \
  --source "<url>" --title "<title>" --priority <1-5> --tags "<tags>" --added-by claude-code
```

Update the Decisions log's **Queued** table as each item is added, and the **Skipped** / **Deferred** tables as decisions are made elsewhere in the run.

Move the discovery checklist to `_inbox/done/` after processing — the Decisions log travels with the checklist so the morning report can reference it.

### Step 8 — Report

Print a summary:

```
Discovery complete for <topic>
  Feeds searched: N
  Candidates found: N (M after dedup)
  High relevance: N
  Medium relevance: N
  Skipped (already covered): N
  Checklist: _inbox/discovered/<date>-discovery.md
  
  Next: review the checklist, then run /wiki-list process to ingest approved items.
```

## After running

- Tell the user where the checklist is
- Tell them how many candidates to review
- Do NOT auto-ingest. Discovery queues. Ingestion is a separate step (`/wiki-update` or `/wiki-list process`).
- Do NOT run discovery again unless asked — one pass per session is enough

## Key paths

- Feeds config: `llm-wiki/wiki/_config/feeds.md`
- Discovery output: `llm-wiki/wiki/_inbox/discovered/`
- Pending queue: `llm-wiki/wiki/_inbox/pending/`
- Done queue: `llm-wiki/wiki/_inbox/done/`
- Concept gaps: `llm-wiki/wiki/concept-gaps-things-mentioned-not-yet-covered.md`
- wiki-list-add script: `.claude/wiki-scripts/wiki-list-add.py`

## Integration with the research cycle

This skill implements **Phase 1 (Discover) + Phase 2 (Filter)** of the research cycle documented in `wiki/implementation/research-cycle-setup.md`. The output (discovery checklist) is the input to **Phase 3 (Human review #1)**.

```
/wiki-discover  →  _inbox/discovered/<date>.md  →  human reviews  →  /wiki-list add  →  /wiki-update
     Phase 1+2          Phase 2 output               Phase 3            Phase 4 prep      Phase 4
```

## Don't

- Don't ingest during discovery — discovery queues, ingestion is separate
- Don't search more than 6 times per run — rate limits + context budget
- Don't include tier 4 candidates without explicit `(NEEDS HUMAN REVIEW)` label
- Don't skip dedup — the #1 cause of duplicate wiki entries is "I thought this was new"
- Don't search for topics outside the wiki's scope (check the topic README)
