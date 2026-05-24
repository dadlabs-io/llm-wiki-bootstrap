---
title: "Cycle Step Return Format — Orchestrator ↔ Skill Contract"
date: 2026-04-24
source_url: internal://session/2026-04-24-cycle-step-return-format
ingested_by: claude-code
tier: self
confidence: high
framework-contract: true
framework-version: 1
last_reviewed: 2026-04-24
review_after: 2026-07-24
tags: [best-practice, architecture, orchestrator, wiki-cycle, schema, contract]
---

# Cycle Step Return Format

The contract between `/wiki-cycle` (orchestrator) and every step-skill it invokes (`/wiki-discover`, `/wiki-update`, `/wiki-lint`, `/wiki-refresh`, `/wiki-claims`). Any new step-skill joining the pipeline adheres to this format.

## Why this contract exists

The cycle is a pipeline of mixed Python scripts and AI-driven skills. Without a shared return format:

- The orchestrator has to parse freeform markdown per skill (fragile regex, breaks when a skill's author tweaks phrasing)
- Morning reports scrape multiple files in multiple formats
- "Tweak a decision and re-run" requires re-interpreting each skill's output structure

With a shared JSON schema + markdown sidecar:

- Orchestrator reads one structure, renders uniformly
- Humans edit the markdown for readability; JSON is auto-regenerated or served as machine-readable truth
- Mixed Python + AI skills emit the same shape — doesn't matter which emitted it
- Reports template cleanly, and if a skill's logic changes, the schema doesn't have to

## File layout per cycle run

Each cycle run lives in a dated, iteration-numbered subfolder under `_inbox/reports/`:

```
_inbox/reports/
└── 2026-04-24/
    └── 2026-04-24-01/
        ├── discover.json
        ├── discover.md
        ├── update.json
        ├── update.md
        ├── lint-mechanical.json
        ├── lint-mechanical.md
        ├── lint-semantic.json
        ├── lint-semantic.md
        ├── refresh.json
        ├── refresh.md
        ├── claims.json
        ├── claims.md
        ├── 2026-04-24-01-run-cycle-report.md      ← orchestrator-assembled final
        └── 2026-04-24-01-run-cycle-report.json    ← aggregated JSON (union of step JSONs)
```

The iteration number (`01`, `02`, ...) increments for same-day re-runs. The orchestrator scans the day's folder and picks the next available `NN`.

## Common skeleton (every step emits this)

```json
{
  "skill": "wiki-discover",
  "cycle_id": "2026-04-24-01",
  "step": "discover",
  "timestamp": "2026-04-24T18:45:00Z",
  "status": "completed",
  "summary": {
    "<step-specific-count>": <n>,
    "<step-specific-count>": <n>
  },
  "queued":   [ { "priority": 2, "url|slug|id": "...", "reason": "...", "timestamp": "..." } ],
  "skipped":  [ { "priority": null, "url|slug|id": "...", "reason": "...", "timestamp": "..." } ],
  "deferred": [ { "priority": 3, "url|slug|id": "...", "reason": "...", "timestamp": "..." } ],
  "notes": "optional free-form agent commentary",
  "errors": []
}
```

### Required fields

| Field | Type | Notes |
|---|---|---|
| `skill` | string | Full skill name (e.g. `wiki-discover`) |
| `cycle_id` | string | `<date>-<NN>` — assigned by orchestrator |
| `step` | string | Short step name (`discover`, `update`, `lint-mechanical`, etc.) |
| `timestamp` | ISO-8601 UTC | When the step completed |
| `status` | string | `completed`, `partial`, `failed` |
| `summary` | object | Step-specific counters — keep keys consistent per skill |
| `queued` | array | Items approved/produced by this step |
| `skipped` | array | Items intentionally skipped, with reason |
| `deferred` | array | Items blocked on recoverable error (retry next cycle) |
| `notes` | string | Free-form agent commentary; empty string if none |
| `errors` | array of `{code, message, item}` | Unexpected errors; blocks cycle if any — orchestrator surfaces |

## Per-skill specifics

### `/wiki-discover`

- `queued[].url` is the source URL; `priority` is 1-5
- `skipped[]` includes dedup hits (reason: "already covered by <slug>") and LOW-tier drops (reason: "LOW relevance, no tier-1 source")
- `deferred[]` includes fetch failures (reason: `"SOURCE_NOT_AVAILABLE"`, `"404"`, `"timeout"`)
- `summary` keys: `feeds_searched`, `candidates_raw`, `candidates_after_dedup`, `queries_run`

### `/wiki-update`

- `queued[].slug` is the new entry slug; `url` also included for trace; `reason` is a 1-line summary of what was ingested
- `skipped[].url` + reason (e.g., "thin content, no new technique", "already covered by <existing-slug>")
- `deferred[].url` + reason (fetch error, timeout, rate limit)
- `summary` keys: `items_attempted`, `items_ingested`, `items_skipped`, `items_deferred`

### `/wiki-lint` (mechanical)

- `queued[]` is empty (mechanical lint doesn't produce items)
- `skipped[]` is empty
- `deferred[]` is empty
- `summary` keys: `files_scanned`, `broken_links`, `orphans`, `stale_pending`, `missing_frontmatter`, `missing_tier`, `invalid_tier`, `missing_confidence`, `invalid_confidence`, `unquoted_yaml`
- The detailed findings live in sibling arrays: `broken_links: [{file, target, link_text}]`, `orphans: [file]`, etc.
- `status: "completed"` with `summary.broken_links == 0 && summary.orphans <= 1` is a clean run

### `/wiki-lint --full` (semantic)

- Four parallel agents run (active / long-term / tooling / orch+impl+bp+root). Orchestrator merges their outputs.
- `queued[]` is empty
- Findings live in: `contradictions[]`, `missing_cross_refs[]`, `thin_coverage[]`, `concept_gaps[]`, `tier_review[]`, `other[]`
- Each finding: `{ file, line, severity: "high|med|low", description, recommended_fix }`
- `summary` keys: counts per category, per folder

### `/wiki-refresh`

- `queued[]` = entries flagged for refresh (with `slug`, `reason: "review_after expired"` or `"confidence decayed"`)
- `skipped[]` = entries checked and still valid
- `deferred[]` = entries that couldn't be assessed (source 404, etc.)
- `summary` keys: `entries_scanned`, `flagged_for_refresh`, `still_valid`, `deferred`

### `/wiki-claims`

- `queued[]` = new contradictions detected
- `skipped[]` = entries checked, no contradictions
- `deferred[]` = entries not yet in the claims index
- Each `queued[]` item for **cross-entry** contradictions: `{ priority, slug_a, slug_b, claim_a, claim_b, severity, confidence, reason, timestamp }` — this is a relational record, not a URL, so `slug_a`/`slug_b` replace the single `url` field from the common skeleton
- Each `queued[]` item for **intra-entry** drift (TL;DR overstates body, stale counts, frontmatter vs content): `{ priority, slug, claim_a, claim_b, severity, confidence, reason, timestamp }` — same entry, two conflicting statements inside it. Validated 2026-04-24: intra-entry drift is the highest-yield category on first run.
- `summary` keys: `claims_extracted`, `contradictions_found`, `severity_high`, `severity_med`, `severity_low`, `intra_entry_drift`, `cross_entry_contradictions`
- **Scope includes both cross-entry AND intra-entry** — don't just compare across files. A TL;DR that overstates the body is a real contradiction worth flagging.

## Markdown sidecar format

Each step also writes `<step>.md` alongside `<step>.json`. The markdown is a human-rendered view of the same data. **The JSON is authoritative** — if the markdown and JSON diverge, the JSON wins.

The markdown sidecar always has three sections mirroring the JSON:

```markdown
# <Step name> — <cycle_id>

**Status**: completed | partial | failed
**Timestamp**: <iso-8601>
**Summary**: <one-line counter summary>

## Queued

| Priority | URL/Slug | Reason | Timestamp |
|---|---|---|---|
| P2 | ... | ... | ... |

## Skipped

| Priority | URL/Slug | Reason | Timestamp |
|---|---|---|---|
| — | ... | ... | ... |

## Deferred

| Priority | URL/Slug | Reason | Timestamp |
|---|---|---|---|
| P3 | ... | ... | ... |

## Notes

<free-form commentary>

## Errors

(empty unless status != completed)
```

## Tweaking decisions post-hoc

If the human reviews the morning report and disagrees with a decision (e.g., a Skipped URL should be Queued):

1. Edit the markdown — move the row from one section to another, update the Reason
2. Run `/wiki-cycle --reconcile <cycle_id>` — re-parses the markdown, regenerates the JSON, replays downstream steps (ingest fires on items now in Queued)
3. Alternatively: edit the JSON directly and regenerate the markdown with `/wiki-report --from-json <cycle_id>`

## Invariants

1. **Every step emits both JSON and MD** — never just one
2. **Timestamps are UTC ISO-8601** — no ambiguity
3. **`cycle_id` is assigned by the orchestrator**, not by individual skills — ensures uniqueness even on same-day re-runs
4. **Errors surface at the step level** — any non-empty `errors[]` flags the cycle as degraded but doesn't halt downstream steps that don't depend on this one
5. **The aggregated cycle report is build from the per-step JSONs** — never scrape markdown sidecars for the final report

## Related

- `/wiki-cycle` SKILL.md (in `.claude/skills/wiki-cycle/SKILL.md` at the repo root) — the orchestrator implementing this contract
- [Wiki frontmatter best practices](./wiki-frontmatter-best-practices.md) — companion contract (for entry-level metadata)
