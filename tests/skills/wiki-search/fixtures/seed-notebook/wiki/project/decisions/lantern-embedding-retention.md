---
title: "Lantern embedding retention in the vector store"
date: 2026-03-02
source_url: "internal://skilltest/seed/lantern-embedding-retention"
ingested_by: skilltest-fixture
tier: self
confidence: high
last_reviewed: 2026-03-20
review_after: 2026-06-18
tags: [lantern, vector-store, retention, decision]
---

# Lantern embedding retention in the vector store

## Proposal (2026-03-02): keep embeddings in the vector store for 30 days

Lantern keeps document embeddings in the vector store for 30 days, then deletes them. How long we keep embeddings decides how much the vector store costs: 30 days of embeddings fits in the current instance, and anything older is rarely searched. The proposal was to keep embeddings for 30 days and re-embed a document when someone opens it after that.

- Storage at 30 days of embeddings: about 40 GB.
- Re-embedding an old document on open: about 2 seconds.

## Review (2026-03-12)

Search logs showed that a third of the useful hits are on documents older than a month: quarterly reports and incident reviews are searched long after they are written. Re-embedding them on open would make those searches miss, because a document that is not embedded cannot be found in the first place.

## Decision (2026-03-20)

The 30-day proposal was rejected. The retention window is **90 days**, and documents tagged `reference` are never expired. The vector store moved to the larger instance to hold it (about 120 GB).

## Related

- [Lantern ingest batch size](../components/lantern-ingest-batch-size.md)
- [Lantern chunking](../components/lantern-chunking.md)
