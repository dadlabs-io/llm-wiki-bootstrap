---
title: "Wiki Frontmatter — Best Practices & Canonical Field Reference"
date: 2026-04-21
source_url: internal://synthesis/2026-04-21-wiki-frontmatter-best-practices
ingested_by: claude-code
tier: self
confidence: high
framework-contract: true
framework-version: 1
last_reviewed: 2026-04-21
review_after: 2026-10-21
tags: [best-practices, frontmatter, wiki, authoring, self-authored, canonical, spec]
---

# Wiki Frontmatter — Best Practices & Canonical Field Reference

Single source of truth for what every entry's YAML frontmatter must contain. Enforces principle 9 (dependency tracking) from [wiki-authoring-best-practices.md](./wiki-authoring-best-practices.md). Any deviation from this spec is a gap to close, not a new pattern to accept.

**Scope**: applies to all markdown entries under `wiki/` in any topic. Does **not** apply to `_inbox/`, `_config/`, `raw/`, `answers/`, `README.md`, or `_INDEX.md`.

---

## Required fields (every entry)

| Field | Type | Values / format |
|---|---|---|
| `title` | string | Human-readable title. Quote if it contains `:` or `"` or special YAML chars. |
| `date` | ISO date | `YYYY-MM-DD` — the date the entry was authored / first compiled. Immutable after creation. |
| `source_url` | URL or `internal://...` | Canonical pointer to origin. See [source_url conventions](#source_url-conventions) below. |
| `ingested_by` | enum | One of: `claude-code`, `clawd`, `cli`, `human`. Who compiled the entry. |
| `tier` | int or literal `self` | `1`, `2`, `3`, `4` for external sources (see [tier rubric](#tier-rubric)); literal `self` for self-authored synthesis. |
| `confidence` | enum | `high`, `medium`, `low`. Author's confidence in the entry's claims. |
| `last_reviewed` | ISO date | `YYYY-MM-DD` of the last human or agent re-read. Update when content is verified. |
| `review_after` | ISO date | `YYYY-MM-DD` when the entry should be re-checked. See [review cadence](#review-cadence). |
| `tags` | list | At least 3 tags. Inline `[a, b, c]` or block list form both accepted. |

## Conditional field — `raw_path`

**Required** for entries that compile from an ingested raw source (external URL, paper, video, repo). Points to the immutable raw file under `raw/`.

**Omit** for self-authored synthesis entries (tier `self`). Those have `source_url: internal://...` and no raw artifact.

| Case | `raw_path` | Example |
|---|---|---|
| External ingest (URL, paper, video) | Required | `raw_path: raw/2026-04-08-llm-wiki.md` |
| Self-authored synthesis | Omit (do not write `null`) | — |
| Re-fetched / poisoned raw | Point at newer file; preserve older under a `.poisoned-*` suffix per principle 3 | `raw_path: raw/2026-04-21-foo-clean.txt` |

Path is relative to the topic root (the folder containing `_INDEX.md`), **not** the wiki root. Always starts with `raw/`.

## Optional fields

| Field | Purpose | When to include |
|---|---|---|
| `aliases` | list | Alternate titles for search — include when the entry covers something known by multiple names. |
| `origin` | enum | One of: `inline`, `wrap-up`, `wiki-update`, `wiki-cycle`. Which skill/path filed this entry. Useful at `/wiki-promote --review` time to spot whether the agent filed it during the session (inline) or batched at session end (wrap-up). Default if omitted: `wiki-update`. |
| `superseded_by` | relative path | When an entry is retired in favor of another, point to the successor. Keep both entries per both-sides-stay (principle 4). |
| `recall_count` | int | Reserved for future memory-signal tracking (principle 10 federation, memory architecture). Do not write manually yet. |
| `access_count` | int | Same as above — reserved. |

---

## Value conventions

### source_url conventions

- **External URL**: full `https://...` URL of the canonical source.
- **Self-authored synthesis**: `internal://synthesis/<YYYY-MM-DD>-<slug>`
- **Self-authored session doc**: `internal://session/<YYYY-MM-DD>-<slug>`
- **Self-authored plan / implementation**: `internal://plan/<YYYY-MM-DD>-<slug>`
- **Self-authored spec** (this doc): `internal://synthesis/<YYYY-MM-DD>-<slug>`

### tier rubric

From [wiki-authoring-best-practices.md principle 7](./wiki-authoring-best-practices.md):

| Tier | Value | Source type |
|---|---|---|
| 1 | `1` | Primary research, peer-reviewed papers, official docs from authoritative sources |
| 2 | `2` | Practitioner primary (direct quotes, talks by creators, first-party engineering writeups) |
| 3 | `3` | Well-sourced commentary (established blogs, secondary analysis with citations) |
| 4 | `4` | Opinion pieces, marketing content, unsourced claims — **never auto-ingest**, human review only |
| self | `self` | Self-authored synthesis, plans, specs, session notes |

### confidence scale

- `high` — claims are well-sourced, recently verified, from tier 1-2 sources
- `medium` — tier 3 source, older entry, or synthesis with some inference
- `low` — tier 4, speculative, or flagged for re-review

### review cadence (default `review_after` offset)

| Content type | Default offset |
|---|---|
| Peer-reviewed paper (tier 1) | +12 months |
| Practitioner primary (tier 2) | +6 months |
| Blog / commentary (tier 3) | +6 months |
| Marketing / opinion (tier 4) | +3 months |
| Self-authored best-practices / spec | +3 months |
| Self-authored session note / plan | +1 month |

Author can override — these are defaults, not hard rules. Shorter cadence is fine for fast-moving topics.

---

## Examples

### External ingest (tier 1 — peer-reviewed paper)

```yaml
---
title: A-MEM — Agentic Memory for LLM Agents (Xu et al., 2025)
date: 2026-04-11
source_url: https://arxiv.org/abs/2502.12110
raw_path: raw/2026-04-13-2502-12110-a-mem-agentic-memory-for-llm-agents.md
ingested_by: claude-code
tier: 1
confidence: high
last_reviewed: 2026-04-11
review_after: 2027-04-11
tags: [a-mem, memory, arxiv, agentic, peer-reviewed, zettelkasten, neurips]
---
```

### External ingest (tier 2 — practitioner video)

```yaml
---
title: "Architecting Agent Memory — Richmond Alake, MongoDB"
date: 2026-04-18
source_url: https://www.youtube.com/watch?v=W2HVdB4Jbjs
raw_path: raw/richmond-architecting-W2HVdB4Jbjs-clean.txt
ingested_by: claude-code
tier: 2
confidence: high
last_reviewed: 2026-04-18
review_after: 2026-10-18
tags: [agent-memory, mongodb, richmond-alake, memorizz, ai-engineer, video]
---
```

### Self-authored synthesis

```yaml
---
title: LLM Wiki Authoring — Best Practices
date: 2026-04-18
source_url: internal://synthesis/2026-04-18-wiki-authoring-best-practices
ingested_by: claude-code
tier: self
confidence: high
last_reviewed: 2026-04-18
review_after: 2026-07-18
tags: [best-practices, wiki, knowledge-base, self-authored, synthesis]
---
```

Note: no `raw_path`.

### Self-authored implementation plan

```yaml
---
title: "agentmemory Setup — Session Memory Implementation Plan"
date: 2026-04-10
source_url: internal://plan/2026-04-10-agentmemory-setup
ingested_by: claude-code
tier: self
confidence: medium
last_reviewed: 2026-04-10
review_after: 2026-05-10
tags: [implementation, agentmemory, session-memory, mcp, self-authored]
---
```

---

## When to update frontmatter

- **On creation**: fill all required fields. Non-negotiable.
- **On re-read / verification**: bump `last_reviewed` to today's date; push `review_after` forward by the default offset for that content type.
- **On content edit**: bump `last_reviewed` if the edit reflects new verification; leave untouched if it's a typo fix or cross-ref update.
- **On raw source re-fetch**: update `raw_path` to point at the new file; preserve the old raw under `.poisoned-<date>` suffix per principle 3 (immutability).
- **On retirement**: add `superseded_by: <path>`; do not delete the entry (principle 4 both-sides-stay + memory principle "no deletion, only forgetting").

## Lint enforcement

Mechanical checks `/wiki-lint` performs (or should perform):

- All required fields present
- `date`, `last_reviewed`, `review_after` are valid ISO dates
- `tier` is `1`, `2`, `3`, `4`, or `self`
- `confidence` is one of the three enum values
- `raw_path` exists on disk (if present)
- `raw_path` is required iff `tier != self`
- `source_url` is either `http(s)://...` or `internal://...`
- `ingested_by` is one of the known values
- `tags` has length ≥ 3

Entries failing any check get listed in the next lint report for manual fix.

## Related

- [wiki-authoring-best-practices.md](./wiki-authoring-best-practices.md) — the 10 principles this spec enforces (especially principle 9)
