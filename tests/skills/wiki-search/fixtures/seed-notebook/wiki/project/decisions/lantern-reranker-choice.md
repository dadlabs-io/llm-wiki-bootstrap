---
title: "Lantern reranker choice"
date: 2026-05-06
source_url: "internal://skilltest/seed/lantern-reranker-choice"
ingested_by: skilltest-fixture
tier: self
confidence: high
last_reviewed: 2026-05-06
review_after: 2026-08-04
tags: [lantern, reranker, retrieval, decision]
---

# Lantern reranker choice

## TL;DR

Lantern reranks the top 50 candidates with a locally hosted cross-encoder, `lantern-rerank-small`, instead of a hosted rerank API. Measured p95 rerank time: 180 ms for 50 candidates.

## Why

- Documents must not leave the network, which rules out the hosted API.
- The hosted API was faster (90 ms) and slightly better on the team's test queries (+2 points), but the local model's 180 ms was judged acceptable.

## Related

- [Lantern query latency budget](../architecture/lantern-query-latency-budget.md)
- [Lantern chunking](../components/lantern-chunking.md)
