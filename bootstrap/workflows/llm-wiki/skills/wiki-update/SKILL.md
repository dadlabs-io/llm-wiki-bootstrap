---
name: wiki-update
description: Update a topic wiki with new content. Auto-detects what to do based on what the user gives. URL → fetch + file. YouTube URL → fetch transcript + synthesize summary + file. Local file → file. Pasted text → file. Nothing → synthesize from current session (git log + handoff). Use when the user says "update the wiki", "add this to the wiki", "save this article", "wiki this", "wiki update", "save what we did to the wiki", "ingest this video", "add this YouTube video to the wiki". Replaces the old /wiki-add command.
---

Update (add) content to a topic wiki. The user shouldn't have to think about what type of source they have — figure it out from what they give you.

## Frontmatter — authoritative reference

Every entry's YAML frontmatter MUST conform to the canonical spec at `<vault>/<topic>/wiki/best-practices/framework/wiki-frontmatter-best-practices.md`. That doc is the single source of truth for required fields, tier rubric, review cadence, and `raw_path` handling. When in doubt, read it — do not invent new fields or drop required ones.

Required on every entry: `title`, `date`, `source_url`, `ingested_by`, `tier`, `confidence`, `last_reviewed`, `review_after`, `tags`. Plus `raw_path` for external ingests (omit for self-authored with `tier: self`).

## Dispatch table — figure out what to do

| User gave you... | Do this |
|---|---|
| **Exactly one URL** (any kind) | Immediate ingest — fetch, synthesize, file as a wiki entry |
| **Multiple URLs** (>1, separated by spaces, newlines, list syntax) | Batch-queue mode — call `wiki-list-add.py` for each; print "queued N items; run `/wiki-cycle --ingest-only` to drain" |
| YouTube URL (single) | YouTube flow — fetch transcript + synthesize + file |
| Local file path (single) | File flow — call wiki-update.py with --source PATH |
| Pasted text | Text flow — write to a temp file, then call wiki-update.py with --source TEMP |
| Nothing (just `/wiki-update`) | Session flow — synthesize from git log + handoff.md |

### Multi-URL detection

The user might paste URLs as:
- Space-separated: `https://a.com https://b.com https://c.com`
- Newline-separated (inside a code block or not)
- Bulleted list: `- https://a.com\n- https://b.com`
- Tuple/array syntax: `[(url1), (url2), ...]` — strip punctuation, extract URLs

Any pattern with 2+ URLs → batch-queue mode. Use a simple regex like `https?://\S+` to extract them.

### Flags to override auto-detect

- `--now <url>` — force immediate-ingest mode even on a list (ingest first item, warn about others)
- `--queue <url(s)>` — force batch-queue mode even on a single URL (skip immediate ingest; just append to pending)

## Universal pre-checks

1. **Topic** — default = the topic configured in your harness if not specified. Confirm with user if ambiguous.
2. **Folder** — concept folder under `wiki/`. List existing first:
   ```bash
   ls llm-wiki/wiki/
   ```
   If none fit, propose a new folder name based on content.
3. **Title** — let the script auto-detect, override only if obviously wrong.
4. **Always pass `--ingested-by claude-code`** (when called from this slash command).
5. **Always pass `--tier <1|2|3|4|self>`** and **`--confidence <high|medium|low>`**.

   **Confidence** measures how reliable OUR entry is (not the source — that's tier):
   - `high` = primary source directly fetched + content verified or corroborated by other entries
   - `medium` = single good source fetched, or describes plans/decisions
   - `low` = synthesized from secondary references, source not fetched, or very thin. Tag with `stub` in tags.

   **Tier** — pick the source quality tier:
   - `1` = peer-reviewed / primary (papers, official spec docs, source code)
   - `2` = established documentation (vendor docs, framework docs, official blog posts)
   - `3` = reputable expert / first-hand (founder posts, expert blogs, conf talks, journalism — KDnuggets, VentureBeat, Karpathy gists, Simon Willison, Hamel Husain, Lance Martin)
   - `4` = community / blog / forum (Medium, Reddit, anonymous gists)
   - `self` = self-authored (our own design docs, syntheses, decisions — pair with `--no-raw`)
   When unsure between two adjacent tiers, prefer the LOWER tier (more conservative). Tier 4 sources should never auto-ingest in the future nightly cycle — they queue for human approval. Tiers 1-3 are auto-ingestible.

## Staging mode (`--staged`)

By default, `/wiki-update` files entries **directly to `wiki/`** and updates backlinks immediately. This is the fast path for manual sessions where you're reviewing output in real-time.

With `--staged`, the entry goes to **`_inbox/proposed/`** instead. No backlinks are added, no existing entries are modified. The entry sits there until promoted via `/wiki-promote`. This is the safe path for automated/batch runs where no human is watching.

| Mode | Entry goes to | Backlinks | When to use |
|---|---|---|---|
| Default (direct) | `wiki/<folder>/` | Added immediately | Manual sessions, you're reviewing |
| `--staged` | `_inbox/proposed/` | Deferred until promotion | Automated runs, batch ingestion, uncertain quality |

**When the user says `--staged`**: follow steps 1-4 as normal, then skip steps 5-6 (backlinks), and in step 7 file to `_inbox/proposed/` instead of `wiki/`. Add `status: proposed` to frontmatter. Save a `_proposed_metadata.json` alongside the entry with: target folder, inbound candidates list, suggested backlinks — so `/wiki-promote` knows what to do later.

**When the user doesn't say `--staged`**: follow the full 8-step flow below (current behavior, unchanged).

## CRITICAL: integrate, don't isolate

**Every ingestion is more than fetch + summarize + file.** A summary that sits alone in the wiki is half the value. The Karpathy pattern is **integration**: every new entry should weave into the existing wiki, updating related entries, adding cross-links, noting where the new source contradicts or extends prior claims.

**The full ingestion flow has 8 steps** (direct mode — default):

1. **Fetch raw** via `wiki-update.py --fetch-only` (or `wiki-fetch-youtube.py` for YouTube). Get the verbatim raw saved to `<topic>/raw/`.
2. **Read the raw file** to understand what's actually in the source.
3. **Search the wiki** for related concepts using `qmd query`. Extract 3-5 key terms from the source and search each. qmd uses hybrid BM25 + vector search, so it finds entries by meaning, not just exact keywords.
4. **Synthesize the curated summary** with explicit cross-links to those existing entries in a "Related in this wiki" section. Don't just summarize in isolation — mention where this new source agrees/disagrees/extends what's already in the wiki. **Use `wiki-update.py --slug-for --title "<other entry title>" --topic <topic> --folder <folder>` to look up the canonical slug of any entry you want to link to** — don't guess slugs from titles. (Guessing is the bug that caused 39 broken links in the 2026-04-08 batch ingest.)
5. **Eval gate — score against the rubric** (see `wiki/implementation/eval-rubric.md`). Before filing, evaluate your synthesis against 5 dimensions (1-5 each):

   | Dimension | What to check |
   |---|---|
   | Extraction fidelity | Every claim attributed? Numbers sourced? No hallucinated context? |
   | Cross-link quality | 3+ relevant cross-links? Bidirectional? |
   | Synthesis value | TL;DR tells you something the title doesn't? Positions source in landscape? |
   | Structural completeness | TL;DR, blockquotes with attribution, Related section, clean headings? |
   | Metadata accuracy | All frontmatter fields present? Tier justified? Confidence reflects certainty? |

   **Pass**: average >= 3.0 AND no dimension scores 1.
   **Fail**: average < 3.0 OR any dimension = 1.

   If **pass**: print the scores and continue to step 6.
   If **fail**: print the scores, flag which dimensions failed, and ask the user: "Entry scores below threshold — fix issues and re-score, or file anyway?"

   This step takes 10 seconds. It's the quality gate that prevents silent poisoning (pre-mortem failure mode #7).

6. **Identify which existing entries should be updated** to add a backlink to the new entry. (Usually the "Related" section of the layer concept page that this source belongs to, plus any entries that the new source explicitly addresses.) **Skip this step if `--staged`.**
7. **Update those existing entries** via Edit — add the new entry to their Related sections. **Skip this step if `--staged`.**
8. **File the new curated entry** via `wiki-update.py`:
   - **Direct mode (default)**: file to `wiki/<folder>/` as before.
   - **Staged mode (`--staged`)**: file to `_inbox/proposed/` instead. Add `status: proposed` to frontmatter. Write a `_proposed_metadata.json` next to the entry containing `{"target_folder": "<folder>", "inbound_candidates": [...], "suggested_backlinks": [...]}` so `/wiki-promote` can finish the integration later.
   The script will print:
   - `wiki_path=<path>` — the canonical path of the new entry
   - `wiki_slug=<slug>` — the canonical slug
   - `outbound_fixed=N` — broken slug links auto-rewritten in your synthesis (review the output to see which)
   - `outbound_warnings=N` — broken slug links the script couldn't unambiguously resolve (you must fix manually)
   - `inbound_candidates=N` — files that mention this entry's topic but don't link to it yet. **In direct mode**: read the listed candidates and add backlinks where appropriate. **In staged mode**: save to metadata file for later.
9. **If processing from queue**: move the `.queue` file from `_inbox/pending/` to `_inbox/done/` and regen the pending-list view.

## Looking up slugs ahead of time (`--slug-for` mode)

Before writing cross-references in your synthesis, look up the canonical slug for each entry you want to link to:

```bash
python .claude/wiki-scripts/wiki-update.py \
  --topic <topic> --vault llm-wiki/wiki \
  --slug-for --title "Karpathy's LLM Wiki Pattern" --folder long-term
```

Output:
```
slug=karpathy-s-llm-wiki-pattern
path=<vault>/<topic>/wiki/long-term/karpathy-s-llm-wiki-pattern.md
```

Use that exact slug in your cross-reference markdown links. **Never guess slugs from titles** — slugify rules are deterministic but not visually obvious (apostrophes become `-s-`, em-dashes get stripped, collisions get `-2`/`-3` suffixes).

## URL flow (non-YouTube) — full integration

### Step 1: Fetch raw
```bash
python .claude/wiki-scripts/wiki-update.py \
  --topic <topic> --vault llm-wiki/wiki \
  --source <url> --fetch-only
```
Capture the `raw_path=...` line from the output.

### Step 2: Read the raw file using the Read tool

### Step 3: Search the wiki for related concepts
For each of 3-5 key terms from the source:
```bash
qmd query "<term>"
```
qmd returns ranked results with file paths and snippets. List the existing entries that come back.

### Step 4: Write the curated summary
Write to `<topic>/_inbox/temp/<slug>.md` with sections:
- TL;DR
- Body sections covering the actual content
- "Why this is in the wiki" (1-2 sentences on what slot it fills)
- "Sources" section separating External (the source material) from Internal (our session/synthesis)
- "Related in this wiki" with markdown links to the existing entries you found in Step 3 (use relative paths from the target folder)

**Synthesis vs direct claims convention** (MANDATORY):
- Use `> blockquotes` for direct quotes from the source material — verbatim text with attribution
- Use plain prose for YOUR synthesis, connections, and inferences
- When citing a specific number (benchmark score, percentage, token count), always blockquote it from the source and name the source. NEVER paraphrase numbers — they drift across entries when paraphrased.
- This distinction prevents silent poisoning (pre-mortem failure mode #7)

**Do NOT include a Source/Raw footer** in your temp file. The script adds its own canonical footer — including one in your synthesis creates duplicates.

**Minimum entry quality floor** (even for P5 items):
- TL;DR (1-2 sentences minimum)
- At least one substantive body section explaining why this matters
- "Related in this wiki" with at least 2 cross-links
- Entries under 30 lines should be explicitly marked as stubs: add `stub: true` to tags

### Step 5: Update related existing entries (MANDATORY, not optional)
For each existing entry that should mention the new one, use Edit to add it to their "Related in this wiki" section. The script's `inbound_candidates` output tells you which files to update — **act on ALL candidates**, not just the obvious ones. Bidirectional linking is what makes the wiki compound.

After a batch of 5+ ingests, also update the relevant **hub page** (e.g., `active/the-active-memory-layer.md` if you added active-layer entries) to list the new entries. Hub pages going stale is the #1 cause of the wiki feeling outdated.

### Step 6: File the curated entry
```bash
python .claude/wiki-scripts/wiki-update.py \
  --topic <topic> --folder <folder> \
  --source <synth file from step 4> \
  --source-url <original url> \
  --raw-path <raw path from step 1> \
  --vault llm-wiki/wiki \
  --ingested-by claude-code \
  --tier <1|2|3|4|self> \
  --confidence <high|medium|low> \
  --title "<title>" --tags "<tags>"
```

The script handles:
- Filing curated copy at `<topic>/wiki/<folder>/<slug>.md`
- Frontmatter (title, date, source_url, raw_path, ingested_by, tags)
- Footer with visible source + raw links
- INDEX regeneration

### Step 7: If from queue, move .queue file
```bash
mv <topic>/_inbox/pending/<file>.md <topic>/_inbox/done/
python .../wiki-list-render.py --topic <topic> --vault ...
```

### Step 8: Clean up the temp file
After `wiki-update.py` succeeds, `rm` the synthesis temp file in `<topic>/_inbox/temp/`. **Always do this on success** — temp files accumulate otherwise. Skip on failure (the temp file may need manual recovery).

```bash
rm <topic>/_inbox/temp/<slug>.md
```

## URL host dispatch — when to use which fetcher

**Before fetching, look at the URL host and pick the right fetcher:**

| Host pattern | Fetcher | Why |
|---|---|---|
| `youtube.com`, `youtu.be` | `wiki-fetch-youtube.py` (yt-dlp in container) | YouTube needs transcript extraction, not page scraping |
| **PDF URL** (`*.pdf`, `arxiv.org/pdf/*`) or local `.pdf` file | `wiki-fetch-pdf.py` (pdftotext + pypdf in container) | Hybrid extraction with quality-based fallback |
| `x.com`, `twitter.com` | `wiki-fetch-page.js` (Playwright in container) | Fully JS-rendered, urllib gets "JavaScript is not available" |
| `medium.com`, `*.medium.com` | `wiki-fetch-page.js` | Heavy JS, paywall walls |
| `threads.net`, `instagram.com`, `bsky.app` | `wiki-fetch-page.js` | All SPA-rendered |
| `linkedin.com` | `wiki-fetch-page.js` | Auth gates, JS-rendered |
| `notion.so` (public pages) | `wiki-fetch-page.js` | JS-rendered |
| `gist.github.com/<user>/<id>` | `wiki-update.py --fetch-only` (URL rewrite to raw) | Auto-rewritten by wiki-update.py |
| `github.com/<user>/<repo>` (bare repo) | `wiki-update.py --fetch-only` (URL rewrite to README raw) | Auto-rewritten by wiki-update.py |
| `github.com/<user>/<repo>/blob/<branch>/<file>` | `wiki-update.py --fetch-only` (URL rewrite to raw) | Auto-rewritten by wiki-update.py |
| Anything else (blogs, docs, plain HTML) | `wiki-update.py --fetch-only` (urllib) | Default — works for non-JS pages |

**When in doubt, try urllib first (`wiki-update.py --fetch-only`), check the raw — if it's < 1KB or contains "JavaScript is not available" / "enable JavaScript" / mostly chrome navigation, switch to playwright.**

## Playwright flow (JS-rendered pages)

For X.com, Twitter, Medium, Threads, etc. The fetch happens inside the openclaw container where Playwright + Chromium are installed. Three steps (same shape as YouTube):

### Step 1 — Fetch via Playwright in container

```bash
MSYS_NO_PATHCONV=1 docker exec openclaw bash -c 'cd /home/node && node /home/node/.openclaw/agents-training/main/skills/research-wiki/wiki-fetch-page.js --topic <topic> --url <url> --vault llm-wiki/wiki --ingested-by claude-code'
```

The script prints `raw_path=<path>` — capture it. Note the `MSYS_NO_PATHCONV=1` is needed on Git Bash for Windows (prevents path mangling). On Linux/Mac it's a harmless no-op.

### Step 2 — Read the raw page and synthesize a curated summary

Read the raw file via Read tool. Note: Playwright captures EVERYTHING including site chrome (login banners, "Don't miss what's happening", trending sidebars, etc.). Skip the chrome and focus on the actual post/article content.

Length philosophy: same as YouTube — quality over word count.

### Step 3 — File the curated entry

Same as the URL flow Step 6:
```bash
python .claude/wiki-scripts/wiki-update.py \
  --topic <topic> --folder <folder> \
  --source <synth file> \
  --source-url <original url> \
  --raw-path <raw path from step 1> \
  --vault llm-wiki/wiki \
  --ingested-by claude-code \
  --title "<title>" --tags "<tags>"
```

## PDF flow (URL or local file)

PDFs need text extraction first, then agent synthesis on top. Three steps, same shape as YouTube + Playwright.

### Step 1 — Extract via Docker exec

```bash
MSYS_NO_PATHCONV=1 docker exec openclaw python3 \
  /home/node/.openclaw/agents-training/main/skills/research-wiki/wiki-fetch-pdf.py \
  --topic <topic> \
  --source <url-or-local-pdf-path> \
  --vault llm-wiki/wiki \
  --ingested-by claude-code
```

The script:
- Downloads the PDF if `--source` is a URL (or uses the local file directly)
- Extracts text per page via hybrid pipeline: `pdftotext` (primary) → `pypdf` (fallback) → optional tesseract OCR (only if installed)
- Saves to `<topic>/raw/<date>-<slug>.md` with frontmatter (source_url, pdf_pages, extraction stats)
- Copies the source PDF alongside as `<date>-<slug>.pdf`
- Prints `raw_path=<path>` for capture

### Step 2 — Read raw, synthesize curated summary
Same as YouTube/Playwright flows.

### Step 3 — File curated entry
Same `wiki-update.py --source <synth> --source-url <orig> --raw-path <raw>` invocation.

## YouTube flow

YouTube videos need a verbatim transcript saved first, then the agent synthesizes a curated summary on top. Three steps:

### Step 1 — Fetch transcript via Docker exec

yt-dlp lives in the openclaw container. Run from there:

```bash
docker exec openclaw python3 \
  /home/node/.openclaw/agents-training/main/skills/research-wiki/wiki-fetch-youtube.py \
  --topic <topic> \
  --url <youtube-url> \
  --ingested-by claude-code
```

The script will print `raw_path=<path>` on success — capture it. The transcript is now saved at that path under `raw/`.

### Step 2 — Read the transcript and synthesize a curated summary

Read the raw transcript file (from host: `llm-wiki/raw/<file>`). Then write a curated markdown summary that captures what's actually important:

- **TL;DR** (1-2 sentences — what is this video about, why does it matter)
- **Key insights** (the actually substantive claims, numbers, frameworks, ideas)
- **Notable quotes** (verbatim snippets worth keeping)
- **When to watch this** (what question does watching this answer)
- **Related** (link to other wiki entries on the same topic)

**Length philosophy**: quality over word count. A 1-hour video might condense to 100 words if it has one good idea. A 3-minute video might need a full breakdown if it's dense. Don't artificially cap at 500 words. Don't pad to 500 either. The raw transcript stays in `raw/` for anything you didn't capture — we can always go back.

Write the summary to a temp file (e.g. `/tmp/wiki-yt-{slug}.md`).

### Step 3 — File the summary as a curated wiki entry

```bash
python .claude/wiki-scripts/wiki-update.py \
  --topic <topic> \
  --folder <folder> \
  --source /tmp/wiki-yt-<slug>.md \
  --source-url <youtube-url> \
  --raw-path <raw_path-from-step-1> \
  --vault llm-wiki/wiki \
  --ingested-by claude-code \
  --title "<video title>" \
  --tags "youtube,<other tags>"
```

`--source-url` ensures the YouTube URL stays in frontmatter (otherwise the temp file path would be the source). `--raw-path` adds the link to the verbatim transcript so you can always drill back.

After this, the curated summary is in `wiki/<folder>/`, the verbatim transcript is in `raw/`, both are linked in frontmatter and the rendered footer.

## File / pasted text flow

Same as URL flow, just pass a local path as `--source`. For pasted text, write it to `_inbox/pending/<slug>.md` first then use that as the source (or `/tmp/<slug>.md` if you don't want it in the queue).

## Session flow (no source)

1. Read these in parallel:
   - `git log --oneline -20`
   - `git diff --stat HEAD~5..HEAD`
   - `memory-bank/short-term/_personas/{persona}/handoff.md`
   - `memory-bank/short-term/_personas/{persona}/completed.md` (recent entries)
   - `git status --porcelain`
2. If handoff is stale, suggest running `/upd-docs` first.
3. Decide topic + folder ((decide based on the entry's content and your wiki's folder taxonomy).
4. **Synthesize a markdown file** capturing what was learned this session — not what was done, but what *insights* compounded. See "Length philosophy" above. Skip if nothing rises to the bar.
5. File via wiki-update.py with `--source` as the temp summary file. No `--source-url`. Pass `--ingested-by claude-code`.

## After running

Tell the user:
- Where it was filed
- Any dedup hit
- Updated INDEX path
- Stop. Don't ingest more sources unless asked.

## Don't

- Don't ingest off-topic content — check the topic README
- Don't fabricate session work — only synthesize what actually happened
- Don't include secrets (API keys, tokens, passwords) in summaries
- Don't pad summaries to hit a word count
- Don't ingest if dedup found a match unless the user explicitly says "force" or "anyway"
- Don't run `/wiki-update` blindly when the user just typed a URL — confirm topic + folder if not obvious

## Key paths

- Wikis vault: `llm-wiki/wiki/`
- wiki-update.py: `.claude/wiki-scripts/wiki-update.py`
- wiki-fetch-youtube.py: `.claude/wiki-scripts/wiki-fetch-youtube.py`
- Topic README (scope rules): `llm-wiki/wiki/README.md`


## Cycle contract

When invoked inside `/wiki-cycle`, this skill writes `<run-folder>/<step>.json` and `<step>.md` per the [Cycle Step Return Format contract](./best-practices/framework/cycle-step-return-format.md) — that doc defines the shape, counters, and queued/skipped/deferred semantics for this step.
