# Discovery Feeds — <topic>

**Purpose**: Trusted sources for `/wiki-discover`. Each row defines a feed the discovery step queries for new content.

## How this file works

Each feed has:
- **URL/query** — what to search or fetch
- **Tier** — source quality (1 = peer-reviewed primary, 2 = vendor/official, 3 = expert first-party, 4 = community/blog, self = our synthesis)
- **From** — earliest date covered (hard floor: 2026-01-01)
- **To** — last date successfully queried (`—` = never queried)
- **Topics/Keywords** — search terms
- **Notes** — why trusted, what to watch for

Default `/wiki-discover` run: **staleness-first** — feeds with the oldest `To` get priority. Over ~6 runs every feed cycles through. Cap: 6 searches per run (override with `--all-feeds`).

---

## Example table (replace with your feeds)

### Blogs & Newsletters

| Author | URL / Search Pattern | Tier | From | To | Topics | Notes |
| --- | --- | --- | --- | --- | --- | --- |
| _(your author)_ | `example.com/blog` | 3 | 2026-01-01 | — | _(keywords)_ | _(why trusted)_ |

### GitHub Repos & Projects

| Project | URL | Tier | From | To | What to watch | Notes |
| --- | --- | --- | --- | --- | --- | --- |
| _(project)_ | `github.com/org/repo` | 2 | 2026-01-01 | — | Releases, breaking changes | _(context)_ |

### Academic / ArXiv

| Query | Frequency | Tier | From | To | Notes |
| --- | --- | --- | --- | --- | --- |
| `"your keywords" site:arxiv.org` | Monthly | 1 | 2026-01-01 | — | _(rationale)_ |

### YouTube Channels

| Creator | Channel | Tier | From | To | Topics | Notes |
| --- | --- | --- | --- | --- | --- | --- |

### Vendor / Platform Blogs

| Vendor | URL | Tier | From | To | Topics | Notes |
| --- | --- | --- | --- | --- | --- | --- |

### Community / Aggregators (tier 4 — human-review-only)

| Source | URL | Tier | From | To | Notes |
| --- | --- | --- | --- | --- | --- |

---

## Feed management rules

1. **Tier 1-3** can auto-queue to the discovery checklist (`_inbox/intake-<bucket>/`, or legacy `_inbox/discovered/`) after dedup.
2. **Tier 4** (community, Reddit, Hacker News, Medium, DEV) MUST go to human review before queuing.
3. **YouTube** fetches via `wiki-fetch-youtube.py` (transcripts).
4. **arXiv PDFs** fetch via `wiki-fetch-pdf.py`.
5. **JS-rendered pages** (X, Medium, Threads) fetch via Playwright.
6. **Dedup** runs against `qmd` and existing wiki before queuing.
7. **Hard floor**: `publishedAfter` never goes before 2026-01-01, even with `--backfill`.
