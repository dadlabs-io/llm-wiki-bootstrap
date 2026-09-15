---
title: "wiki-update — skill"
type: how-to
artifact: skill
name: wiki-update
installed_by: install-wiki
date: 2026-07-31
---

# wiki-update — skill

Ingests one external source into the wiki. You hand it whatever you have (a link, a YouTube video, a PDF, an X post, a local file, or pasted text) and it picks the right fetcher, keeps the verbatim original under `raw/`, and writes a curated entry that is cross-linked into what the wiki already knows. Integration is the point: a summary that sits alone is half the value, so every entry links to related entries and says where the new source agrees with, extends or contradicts them.

**Trigger:** */wiki-update <source>*, plus phrasings like "add this to the wiki", "save this article", "wiki this" or "ingest this video". "Update the wiki" belongs to [`wiki-cycle`](./wiki-cycle.md).

**Input / Output:** one URL, file path, or block of pasted text. By default it files directly: the raw under `raw/`, the entry at `wiki/<folder>/<slug>.md` with full frontmatter (title, date, source URL, raw path, tier, confidence, review dates, tags), links added back from the related entries it found, and the index regenerated. With `--staged` the entry goes to `_inbox/proposed/` with a sidecar file instead, no other entry is touched, and [`wiki-promote`](./wiki-promote.md) finishes the integration later. Two or more URLs are not ingested: each is queued in `_inbox/pending/` for `/wiki-cycle --ingest-only`. With no source at all it stops and points you to [`wrap-up`](./wrap-up.md), which is for capturing the session's own work.

**When it skips itself:** a source already in the wiki (or already staged) is reported as a duplicate and not filed again, unless you say to force it. A community source (tier 4) is never ingested automatically; it needs your yes.

**Works with:** [`wiki-list`](./wiki-list.md) holds the queue that batch mode writes into, and [`wiki-cycle`](./wiki-cycle.md) drains that queue by running this flow across many sources, staged. [`wiki-search`](./wiki-search.md) is the search the flow uses to find the entries worth linking to. [`wiki-promote`](./wiki-promote.md) moves staged entries into the wiki.

## Full walkthrough

### Usage

```
/wiki-update https://example.com/article
/wiki-update https://example.com/article --staged     # stage it for review instead of filing it
/wiki-update https://a.com https://b.com              # two or more: queued for /wiki-cycle
```

### What happens, step by step

1. **Fetch the raw.** Ordinary web pages are fetched directly. YouTube videos get their transcript, PDFs are converted to text page by page, X posts come from the public syndication API, and pages that need JavaScript are rendered in a browser. A Medium member-only story is read through your own signed-in browser when the session is interactive. A raw that was already saved (handed over by a batch) skips this step.
2. **Read the raw in full.**
3. **Search the wiki** for three to five of the source's key terms, with the full search, scoped to this notebook.
4. **Write the entry**: a TL;DR, the body, the sources, and a Related section linking at least two existing entries. Numbers and quotations go in attributed `>` blockquotes, so they are never paraphrased.
5. **The gate.** The filing script checks the draft before writing anything; see below. The agent then scores what a script cannot and prints one line: `Scores: extraction fidelity N/5, synthesis value N/5`. The scores are advisory: the agent that wrote the draft never certifies it.
6. **Add links back** from the related entries to the new one (direct mode only).
7. **File it**, regenerate the index, and delete the temporary files.

### The gate (what "refused" means)

The filing script refuses to write an entry that has no `## TL;DR` section, a `## Related` section with fewer than two links to other wiki entries (for your own synthesis, tier `self`, this is only a warning), anything after its Source footer other than the automatic backlinks block, or frontmatter that would not parse. It warns, without refusing, on fewer than three tags, a thin entry not tagged `stub`, and numbers written in plain prose instead of a `>` blockquote. A refusal prints `Refusing to file` and writes nothing; the agent fixes the draft and files again, so the source is never lost. `--no-gate '<reason>'` is the audited override for the rare entry a rule is genuinely wrong for. [`wiki-lint`](./wiki-lint.md) runs the same checks over existing entries as a warn-only backlog.

### Direct or staged

| | Direct (the default) | `--staged` |
|---|---|---|
| Entry goes to | `wiki/<folder>/` | `_inbox/proposed/`, with a sidecar naming its folder |
| Links back from related entries | added now | added by `/wiki-promote` |
| Use it when | you are ingesting a source yourself | you ask for review first, or a batch runs unattended (`/wiki-cycle`'s workers) |

The agent never chooses staged mode on its own; you (or the calling workflow) ask for it.

### Tier and confidence

Tier is the source's quality, from `1` (primary or peer-reviewed) to `4` (community), or `self` for the wiki's own synthesis. Confidence is how reliable the entry is. The agent chooses both from the rubric in your notebook's frontmatter spec (`wiki/project/best-practices/framework/wiki-frontmatter-best-practices.md`), the one place they are defined; between two adjacent tiers it takes the lower. Tier 4 never auto-ingests.

### Duplicates

The filing script compares the source's URL, normalised (case, `www.`, trailing slash, tracking parameters), with every entry in `wiki/` and `_inbox/proposed/`, and skips a match. A later snapshot of a source that changed (a repository that grew, a new release) is filed with `--revises <slug>`: it records the earlier entry, checks that it exists, and lets the shared URL through. Entries written from a session (`internal://` URLs) are never treated as duplicates of each other. The queue (batch mode, Drive links) has its own duplicate check: it skips a URL already queued in `_inbox/pending/`, already processed in `_inbox/done/`, staged in `_inbox/proposed/`, or in `wiki/`.

### Don't

- Don't promote a staged entry without reading it: the agent's scores are not a review.
- Don't force past a duplicate unless the source really changed.
- Don't use it for session work ("save what we did"): that is `/wrap-up`.

### Batching

For several URLs:
```
/wiki-update https://a.com https://b.com https://c.com
```
Each URL goes to `_inbox/pending/` for `/wiki-cycle --ingest-only` (or a full `/wiki-cycle`) to drain. You can also drop links into the Drive folder (`__FOR CLAUDE/<project-slug>/`) and let `/wiki-cycle` pick them up.
