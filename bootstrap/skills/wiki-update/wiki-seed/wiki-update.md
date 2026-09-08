---
title: "wiki-update — skill"
type: how-to
artifact: skill
name: wiki-update
installed_by: install-wiki
date: 2026-07-31
---

# wiki-update — skill

Ingests an external source into the wiki's `research/` layer. You hand it whatever you have — a link, a YouTube video, a PDF, a local file, or pasted text — and it works out the right fetcher, saves the verbatim original, and writes a curated summary that is cross-linked into what the wiki already knows. Integration is the point: a summary that sits alone is half the value, so every entry links to related entries and notes where the new source agrees with, extends, or contradicts them.

**Trigger:** */wiki-update <source>*, plus natural phrasings like "add this to the wiki", "save this article", "wiki this", or "ingest this video".

**Input / Output:** consumes exactly one URL, file path, or block of pasted text. Produces a verbatim raw capture under `raw/` and a curated entry at `wiki/<folder>/<slug>.md` with full frontmatter (title, date, source_url, raw_path, tier, confidence, review dates, tags), plus regenerated indexes and backlinks added to the related entries it found. With `--staged` the entry lands in `_inbox/proposed/` alongside a `<slug>.proposed_metadata.json` sidecar instead, leaving existing entries untouched until promotion. Hand it two or more URLs and it switches to batch-queue mode, queueing each for later draining rather than ingesting inline.

Before filing, the script itself runs a deterministic gate over the draft — a TL;DR, a Related section with at least two wiki links, enough tags, stub marking on thin entries, numbers quoted rather than paraphrased — and refuses to file on a hard failure (an explicit `--no-gate` with a reason is the only way past it). The agent then scores only the two judgment dimensions a script cannot decide, extraction fidelity and synthesis value, and that self-score is advisory: the agent that wrote the draft is never the thing that certifies it. The same body checks run in `wiki-lint` over every existing entry so the backlog stays visible.

**Works with:** [`wrap-up`](./wrap-up.md) is the counterpart for internal session work — run `/wiki-update` with no source and it redirects there. [`wiki-list`](./wiki-list.md) holds the queue that batch mode writes into, and [`wiki-cycle`](./wiki-cycle.md) drains that queue by running this flow across many sources at once. [`wiki-promote`](./wiki-promote.md) moves staged entries into the wiki and wires their backlinks. [`wiki-search`](./wiki-search.md) is what the synthesis step uses to find the existing entries worth linking to.

## Full walkthrough

For ad-hoc additions. One URL = fetch + render + stage right now. Multiple URLs = queue them to `_inbox/pending/` for the next `/wiki-cycle` to process.

### Usage

```
/wiki-update https://example.com/article
```

The skill fetches the page, extracts content (handles articles, PDFs via `wiki-fetch-pdf.py`, YouTube via `wiki-fetch-youtube.py`), renders a wiki entry, scores it on tier/relevance, and stages it at `llm-wiki/wiki/_inbox/proposed/<slug>.md`.

### The gate (what "refused" means)

Since 2026-09-02 the filing script checks the drafted entry **before** it writes anything. Two rules are hard: the entry must have a `## TL;DR` section, and a `## Related` section linking to at least two other wiki entries. Three are soft: three or more tags, a `stub` tag on genuinely thin entries, and numbers that sit in an attributed `>` blockquote rather than loose prose. A hard failure means the script prints `Refusing to file`, writes nothing, and hands the draft back — the agent adds the missing section and files again. The source is never lost or skipped; it just cannot land half-finished. `--no-gate '<reason>'` is the audited override for the rare entry where a rule is genuinely wrong for it. The agent's own quality score covers only the two things a script cannot judge, faithfulness to the source and whether the summary adds insight, and that score is advisory. `/wiki-lint` runs the same checks over existing entries as a warn-only backlog view.

You review the proposed entry, then `/wiki-promote --review` to move it into `wiki/<folder>/`.

### Tier scoring

The script evaluates each URL against the project's tier definitions:

- **tier 1** — peer-reviewed / primary research (papers, official specs)
- **tier 2** — vendor / official docs
- **tier 3** — expert / first-hand practitioner (well-known author, deep dive)
- **tier 4** — community / blog / X post / Reddit
- **tier self** — our own synthesis (rarely set automatically)

Tier 4 items get a stricter relevance check — if they don't clear the bar, they're rejected with a content-grounded reason (not a title-pattern guess).

### Don't

- Don't run `/wiki-update` and then immediately promote without reviewing — the score isn't a substitute for human review
- Don't bypass the staging area to write directly into `wiki/<folder>/` — that breaks `_MAP.md` regen and the backlinks pass
- Don't add the same URL twice expecting different results — the script dedupes against `_inbox/pending/`, `_inbox/proposed/`, `wiki/`, and `_inbox/done/`; Drive-fetched links are compared by canonical URL (tracking params stripped, YouTube collapsed to `watch?v=<id>`) so a newsletter link no longer re-queues an ingested article

### Batching

For multiple URLs:
```
/wiki-update https://a.com https://b.com https://c.com
```
Two-URL+ is treated as a queue: each URL goes to `_inbox/pending/` for `/wiki-cycle --ingest-only` (or full `/wiki-cycle`) to drain.

Or drop links into the Drive folder (`__FOR CLAUDE/<project-slug>/`) and let `/wiki-cycle` pick them up.

