---
title: "Lantern query latency budget"
date: 2026-04-22
source_url: "internal://skilltest/seed/lantern-query-latency-budget"
ingested_by: skilltest-fixture
tier: self
confidence: high
last_reviewed: 2026-04-22
review_after: 2026-07-21
tags: [lantern, latency, architecture, slo]
---

# Lantern query latency budget

## TL;DR

A Lantern search must answer within 1.2 seconds at p95. The budget is split: 400 ms for retrieval, 250 ms for reranking, and the rest for fetching snippets and rendering.

## What

- The 250 ms reranking allowance assumes 50 candidates.
- A stage that goes over its share pages the owning team, even when the total stays under 1.2 seconds.

## Related

- [Lantern reranker choice](../decisions/lantern-reranker-choice.md)
- [Lantern on-call](../architecture/lantern-on-call.md)
