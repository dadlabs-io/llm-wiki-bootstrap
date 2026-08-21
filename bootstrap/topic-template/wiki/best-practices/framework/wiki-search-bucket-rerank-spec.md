---
title: "Wiki Search — Bucket-Aware Retrieval Sort Spec"
date: 2026-05-25
source_url: internal://synthesis/2026-05-25-wiki-search-bucket-rerank-spec
ingested_by: claude-code
tier: self
confidence: high
framework-contract: true
framework-version: 1
last_reviewed: 2026-05-25
review_after: 2026-08-25
raw_path: (none — self-authored)
tags: [best-practices, framework, search, retrieval, icarus-schema, truth-status, qmd, self-authored]
---

# Wiki Search — Bucket-Aware Retrieval Sort Spec

Implementation contract for §3 of [icarus-integration-plan.md](./icarus-integration-plan.md). Defines the sort-key semantics that any wiki-search surface (qmd wrapper, `/wiki-search` skill, future native search layer) must honor when truth-status fields are present.

## TL;DR

Add a **truth-status bucket** to the existing relevance score. Default sort changes from `score DESC` to `(bucket, score) DESC`. Verified entries always outrank unverified at the same score; contradicted entries always sink below unverified; rolled-back entries are excluded by default.

Two opt-in flags relax the default:
- `--include-rolled-back` — surface entries marked `verified: rolled_back` (default: exclude). Use case: "show me what we used to believe."
- `--surface-contradicted` — *prefer* `verified: contradicted` entries instead of sinking them. Use case: explicit audit of tensions. (Refinement identified in cycle 2026-05-24-01 from BeliefMem + Rashomon Memory.)

## Bucket function

```python
def truth_bucket(entry) -> int | None:
    """Return rank bucket from verified status, or None to exclude from retrieval.

    Higher bucket = ranked higher at any given relevance score.
    None = excluded from result set entirely.
    """
    verified = read_verified(entry)  # frontmatter, fall back to sidecar
    if verified == "verified":
        return 4
    if verified == "unverified" or verified is None:
        return 3
    if verified == "temporal":
        return 2  # was correct as-of-a-past-date but no longer current (cycle 2026-05-24-01)
    if verified == "contradicted":
        return 1
    if verified == "rolled_back":
        return None  # excluded by default; --include-rolled-back overrides
    # Unknown value: treat as unverified (don't fail-closed)
    return 3
```

The TEMPORAL bucket (2) sits below `unverified` because temporal-stale-but-not-wrong content is still slightly less useful than fresh-unverified content at the same relevance score (the unverified entry might be currently correct; the temporal one is known-stale). It sits above `contradicted` because temporal is "was right at the time", contradicted is "we now know it was wrong even then."

Read order: prefer the frontmatter `verified:` field (no I/O beyond the entry); fall back to the sidecar `verified` field if frontmatter is unset. If neither is set, treat as `unverified` (bucket 2).

## Sort key

Default:

```
sorted(candidates, key=lambda e: (truth_bucket(e), score(e)), reverse=True)
```

Where `candidates` excludes any entry whose bucket is `None` (i.e., `rolled_back`).

With `--include-rolled-back`: keep entries with `verified: rolled_back` in the candidate set and assign them bucket `0` (below `contradicted`). Still ordered last unless their score is dramatically higher than other candidates.

With `--surface-contradicted`: invert the bucket for `contradicted` entries — assign them bucket `5` (above `verified`). Use case: "I'm explicitly looking for the disagreements." All other bucket values unchanged. Mutually compatible with `--include-rolled-back`.

## Tie-breaking

Within a single bucket, sort by `score` descending (as today). Within the same `(bucket, score)` tuple, tie-break by `last_reviewed` descending (more recently re-verified entries win).

## Where this gets applied

Three implementation surfaces, in priority order:

1. **Post-filter wrapper around qmd** (cheapest — ship first). A small `wiki-search-rerank.py` that takes qmd's JSON output, reads each candidate's `verified` field, applies the bucket function, and re-sorts. No qmd modification needed. Documented as the v1 implementation path.

2. **`/wiki-search` skill** consumes the rerank wrapper by default. Adds `--include-rolled-back` and `--surface-contradicted` flags to the skill's CLI. Backward compatible: callers that don't pass either flag get the new default sort.

3. **Native bucket-aware search layer** (eventually). If we ever build our own search to replace qmd, the bucket is a first-class field at index time, not a post-filter. Avoids the wrapper round-trip.

## Reranker contract (v1 — post-filter wrapper)

```
Usage:
    wiki-search-rerank.py <qmd-json-stdin> [--include-rolled-back] [--surface-contradicted]

Input (stdin): qmd's JSON output. Expected shape:
    {
      "query": "...",
      "results": [
        {"path": "wiki/active/foo.md", "score": 0.82, "snippet": "..."},
        ...
      ]
    }

Output (stdout): same shape, with `results` re-sorted by (bucket, score) DESC and
filtered per the flags. Adds a `bucket` field to each result for transparency.
```

Failure modes:
- If a candidate path doesn't exist on disk → drop with WARN to stderr (don't crash)
- If a candidate has no `verified` field anywhere → bucket = 2 (unverified default)
- If qmd's JSON doesn't have a `results` array → pass-through unchanged

## Why this isn't built yet

qmd is an external tool (we don't own its source). The bucket-rerank can ship as either:
- (a) post-filter wrapper that adds latency proportional to result-set size (cheap; 50-200ms for a 100-candidate set)
- (b) qmd plugin if its plugin API surfaces this (would need to check qmd's plugin spec)
- (c) native search layer if we ever build one (long-term)

V1 should ship as (a). It unblocks every consumer immediately and the latency is bounded by candidate count, not corpus size.

## Migration story

- Existing entries have no `verified:` field → all default to bucket `2` (unverified) → ranking changes for these are **zero** (everything's in the same bucket, sort falls back to score-only).
- New entries created post-icarus-§1 may carry `verified:` → those get bucketed normally.
- `/wiki-verify` flow (icarus §5) is what populates `verified: verified` on existing entries — no batch migration needed.

So the default-sort change is **safe to deploy** before any entries actually carry truth-status fields. The bucket function returns 2 for unset, and the sort degenerates to today's behavior. Adoption is incremental.

## Related

- [icarus-integration-plan.md §3](./icarus-integration-plan.md#3-recall--retrieval--new-sort-key) — the plan section this spec realizes
- [memory-signals-sidecar-vs-frontmatter-pattern.md](./memory-signals-sidecar-vs-frontmatter-pattern.md) — sidecar that holds the authoritative `verified` value when frontmatter is stale
- [wiki-frontmatter-best-practices.md](./wiki-frontmatter-best-practices.md) — the optional `verified:` field on the entry itself

## Open question

Should the `/wiki-search` skill always apply the bucket sort by default once we ship it, or should it stay an opt-in flag for the first cycle to avoid surprise? Lean: opt-in for the first 7 days (`--bucket-sort` to enable), then flip to default-on with `--no-bucket-sort` as the escape hatch. Same training-wheel pattern as the human checkpoints in /wiki-cycle.
