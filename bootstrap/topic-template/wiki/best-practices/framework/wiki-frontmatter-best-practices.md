---
title: "Wiki Frontmatter — Best Practices & Canonical Field Reference"
date: 2026-04-21
source_url: internal://synthesis/2026-04-21-wiki-frontmatter-best-practices
ingested_by: claude-code
tier: self
confidence: high
framework-contract: true
framework-version: 4
last_reviewed: 2026-09-08
review_after: 2026-12-08
tags: [best-practices, frontmatter, wiki, authoring, self-authored, canonical, spec, icarus-schema]
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
| `recall_count` | int | Reserved for future memory-signal tracking (principle 10 federation, memory architecture). Do not write manually yet. See [memory-signals-sidecar-vs-frontmatter-pattern.md](./memory-signals-sidecar-vs-frontmatter-pattern.md) — the sidecar pattern is the production-bound implementation route; this field is the frontmatter mirror for entries where the signal is editorially-set, not telemetry-derived. |
| `access_count` | int | Same as above — reserved. |

## Optional fields — truth-status and lineage (icarus schema)

Adopted from the icarus-memory-infra schema *(agentic-design :: wiki/research/active/icarus-memory-infra-esaradev-2026.md)* (MIT-licensed vocabulary lift; we do not take icarus as a runtime dependency — see icarus-integration-plan.md *(agentic-design :: wiki/project/best-practices/framework/icarus-integration-plan.md)* §1). These five fields layer truth-status and forward/backward lineage onto entries; they are **optional** at the schema level but have **write-time invariants** when used.

| Field | Type | Values / format | Purpose |
|---|---|---|---|
| `verified` | enum | `unverified` (default) \| `verified` \| `temporal` \| `contradicted` \| `rolled_back` | Truth-status. Default `unverified` when omitted. Production retrieval ranks `verified` highest, then `unverified`, then `temporal` (was correct as-of-a-past-date), then `contradicted` lowest, `rolled_back` excluded by default. The `temporal` value splits off "still correct but stale by date" from "was wrong" (cycle 2026-05-24-01 refinement, TDS Alexander 3-time-problems framing). |
| `revises` | slug | Relative path to the older entry this one revises | Backward lineage. Used by rollback walks to reach the verified ancestor. |
| `review_of` | slug | Relative path to the entry this one audits / re-evaluates | Forward lineage for `type: review` entries — the audited target. |
| `contradicted_by` | slug | Relative path to the newer entry that contradicts this one | Set on the older side of a contradiction pair. **Required iff `verified='contradicted'`.** |
| `synthesis_of` | list of slugs | Relative paths to the research entries this project entry distills | ACL lineage from project → research synthesis. When a `project/` entry draws claims from one or more `research/` entries, list them here so ACL-aware retrieval can detect distillation chains and propagate access constraints (e.g., NDA-bound, customer-private). Cycle 2026-05-24-01 refinement (Databricks Lakebase). |
| `type` | enum | `decision` \| `observation` \| `attempt` \| `rollback` \| `review` | Entry kind. Default: not set (treated as a regular entry). |

### Write-time invariants

These must be checked at write time (during ingest / promote / hand-edit), not retrieval time. The `wiki-lint-mechanical.py` script enforces them with `--strict` mode failing CI:

1. **No self-certification** — `verified: verified` cannot be set on the initial write of an entry. Only a separate verify step (e.g., `/wiki-verify <slug>`) can set it. This prevents an entry from asserting its own truth.
2. **Contradiction needs a target** — if `verified: contradicted`, then `contradicted_by:` must be present and must point at an existing entry.
3. **Rollback needs an ancestor** — if `type: rollback`, then `revises:` must be present and point at an existing entry (the verified ancestor it restores).
4. **Review needs a target** — if `type: review`, then `review_of:` must be present and point at an existing entry (the audited target).
5. **Reference integrity** — `revises`, `review_of`, `contradicted_by`, and every entry in `synthesis_of` (when present) must each resolve to a real file under `wiki/`.

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
| 1 | `1` | Peer-reviewed / primary — papers, official spec docs, source code |
| 2 | `2` | Established documentation — vendor/framework docs, official blog posts |
| 3 | `3` | Reputable expert / first-hand — founder posts, expert blogs, conf talks, journalism (KDnuggets, VentureBeat, Karpathy gists, Simon Willison, Hamel Husain, Lance Martin) |
| 4 | `4` | Community / blog / forum — Medium, Reddit, anonymous gists, an individual's repository — **never auto-ingest**, human review only |
| self | `self` | Self-authored synthesis, plans, specs, session notes |

When unsure between two adjacent tiers, prefer the LOWER tier (more conservative). Tiers 1–3 are auto-ingestible; tier 4 always queues for human approval.

**Restatement rule (2026-08-01; template synced to v3 on 2026-09-02).** This table is the only place the tier rubric is defined, and the confidence scale below is the only place confidence is defined. Folder READMEs, `_INDEX` files, eval rubrics, skill definitions and entry bodies **link here; they do not restate it.** A paraphrase cannot be lint-checked, ages independently of the thing it paraphrases, and — where it also claims to be "the same as elsewhere" — actively deters verification. The same rule applies to any rule in this document. If a folder needs a rubric this table does not support, that is a gap to close here, not a local variant to publish there. (Why it matters: on 2026-09-02 the `wiki-update` skill's own paraphrase of the confidence scale had drifted from this table and an ingest had to guess which won. Precedence is now stated in the project CLAUDE.md: framework-contract docs first.)

### confidence scale

- `high` — claims are well-sourced, recently verified, from tier 1-2 sources
- `medium` — tier 3 source, older entry, or synthesis with some inference
- `low` — tier 4, speculative, or flagged for re-review

### review cadence (default `review_after` offset)

| Content type | Default offset |
|---|---|
| Peer-reviewed / primary (tier 1) | +12 months |
| Established documentation (tier 2) | +6 months |
| Reputable expert / first-hand (tier 3) | +6 months |
| Community / blog / forum (tier 4) | +3 months |
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

**Loadability (2026-09-08, `_entry_checks.check_frontmatter_loadable()`)** — checked on the RAW block, before any field check, because an unparseable block makes a YAML loader drop *every* field:
- a top-level plain (unquoted) value containing `: ` or ending in `:` — error `frontmatter-unquoted-scalar`
- a top-level plain value starting with a YAML indicator (`* & ! % @` or a backtick) — error `frontmatter-reserved-indicator`
- a top-level plain value containing ` #` — warning `description-comment-truncates` (YAML starts a comment; the value is silently cut)
- anything else PyYAML rejects, when PyYAML is installed — error `frontmatter-yaml-parse`
The same check runs over the installed `~/.claude/skills/*/SKILL.md` and `~/.claude/agents/*.md`, and the installer refuses to install a skill or agent that fails it (the loader would list the skill by its H1 and never trigger it by description — four shipped skills were in that state until this date). Fix: double-quote the value, escape inner `"`.

**Core schema checks:**
- All required fields present
- `date`, `last_reviewed`, `review_after` are valid ISO dates
- `tier` is `1`, `2`, `3`, `4`, or `self`
- `confidence` is one of the three enum values
- `raw_path` exists on disk (if present)
- `raw_path` is required iff `tier != self`
- `source_url` is either `http(s)://...` or `internal://...`
- `ingested_by` is one of the known values
- `tags` has length ≥ 3

**Body checks (2026-09-02, `_entry_checks.py`)** — the mechanical half of the eval rubric, shared verbatim between `wiki-update.py` (hard pre-write gate: refuses to file on an error unless `--no-gate '<reason>'`) and `wiki-lint-mechanical.py` (warn-only backlog view over existing entries):
- `## TL;DR` section present (a bold `**TL;DR**` lead also counts) — error
- `## Related …` section with ≥ 2 links to wiki entries — error (warning when `tier: self`)
- `tags` ≥ 3 — warning
- fewer than 30 non-blank body lines AND fewer than 300 words, with no `stub` tag — warning
- numeric claims in prose outside a `>` blockquote — warning (numbers are quoted and attributed, never paraphrased)
Exempt: wiki-root hub pages, `_`-prefixed system files, `framework-contract: true` docs, `type: rollback|review` entries.

**Icarus schema checks** (default WARN; `--strict` flips to error / non-zero exit):
- `verified` (when present) is one of `unverified` \| `verified` \| `temporal` \| `contradicted` \| `rolled_back`
- `type` (when present) is one of `decision` \| `observation` \| `attempt` \| `rollback` \| `review`
- `verified: verified` is NOT set on initial write (reject — only `/wiki-verify` can flip this)
- `verified: contradicted` requires `contradicted_by:` field present
- `type: rollback` requires `revises:` field present
- `type: review` requires `review_of:` field present
- `revises`, `review_of`, `contradicted_by`, and every entry in `synthesis_of` (when present) point at existing files under `wiki/`

Entries failing any check get listed in the next lint report for manual fix.

## Skill and agent definitions carry lifecycle fields too (2026-09-02; agents 2026-09-08)

The `SKILL.md` files that govern every ingest, and the `AGENT.md` of every shipped agent, are governance artifacts and decay like entries do. Each carries `last_reviewed`, `review_after` (3-month cadence, same as self-authored specs), and `reviewed_for_model` (the model id the procedure was last checked against — harness behaviour is model-relative). `/wiki-refresh` scans them alongside entries and lists overdue ones in its report. Claude Code ignores the extra keys; the Cursor rule converter reads only `description`. Their frontmatter is also subject to the loadability check above — a governance artifact that does not parse governs nothing. The six framework-contract docs carry `framework-version` in addition; a project copy whose version is behind the template's is stale, and `new-wiki.py --phase docs` replaces it.

## Related

The six framework-contract docs, of which this is one. They are installed together at `project/best-practices/framework/` in every project wiki by `new-wiki.py` and refreshed by `--phase docs`; this list is the hub so none of them is an orphan in a fresh wiki.

- [wiki-authoring-best-practices.md](./wiki-authoring-best-practices.md) — the operational principles this spec enforces (especially principles 9 and 11)
- [cycle-step-return-format.md](./cycle-step-return-format.md) — the orchestrator ↔ step-skill JSON contract
- [tiered-context-loading.md](./tiered-context-loading.md) — how agents load the wiki (map → folder index → entry) and say where they stopped
- [memory-signals-sidecar-vs-frontmatter-pattern.md](./memory-signals-sidecar-vs-frontmatter-pattern.md) — why access signals and truth-status events live in a sidecar, not here
- [wiki-search-bucket-rerank-spec.md](./wiki-search-bucket-rerank-spec.md) — how the optional `verified:` field sorts search results
