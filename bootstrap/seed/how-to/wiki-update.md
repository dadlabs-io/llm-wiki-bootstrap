# /wiki-update — add a single URL to the wiki

For ad-hoc additions. One URL = fetch + render + stage right now. Multiple URLs = queue them to `_inbox/pending/` for the next `/wiki-cycle` to process.

## Usage

```
/wiki-update https://example.com/article
```

The skill fetches the page, extracts content (handles articles, PDFs via `wiki-fetch-pdf.py`, YouTube via `wiki-fetch-youtube.py`), renders a wiki entry, scores it on tier/relevance, and stages it at `llm-wiki/wiki/_inbox/proposed/<slug>.md`.

You review the proposed entry, then `/wiki-promote --review` to move it into `wiki/<folder>/`.

## Tier scoring

The script evaluates each URL against the project's tier definitions:

- **tier 1** — peer-reviewed / primary research (papers, official specs)
- **tier 2** — vendor / official docs
- **tier 3** — expert / first-hand practitioner (well-known author, deep dive)
- **tier 4** — community / blog / X post / Reddit
- **tier self** — our own synthesis (rarely set automatically)

Tier 4 items get a stricter relevance check — if they don't clear the bar, they're rejected with a content-grounded reason (not a title-pattern guess).

## Don't

- Don't run `/wiki-update` and then immediately promote without reviewing — the score isn't a substitute for human review
- Don't bypass the staging area to write directly into `wiki/<folder>/` — that breaks `_MAP.md` regen and the backlinks pass
- Don't add the same URL twice expecting different results — the script dedupes against `_inbox/pending/`, `_inbox/proposed/`, `wiki/`, and `_inbox/done/`

## Batching

For multiple URLs:
```
/wiki-update https://a.com https://b.com https://c.com
```
Two-URL+ is treated as a queue: each URL goes to `_inbox/pending/` for `/wiki-cycle --ingest-only` (or full `/wiki-cycle`) to drain.

Or drop links into the Drive folder (`__FOR CLAUDE/<project-slug>/`) and let `/wiki-cycle` pick them up.
