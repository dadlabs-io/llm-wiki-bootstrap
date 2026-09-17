---
title: "Lantern chunking"
date: 2026-02-14
source_url: "internal://skilltest/seed/lantern-chunking"
ingested_by: skilltest-fixture
tier: self
confidence: medium
last_reviewed: 2026-02-14
review_after: 2026-05-15
tags: [lantern, chunking, ingest]
---

# Lantern chunking

## TL;DR

Lantern splits documents into chunks of 512 tokens with a 64-token overlap, and keeps tables whole even when a table is longer than one chunk.

## What

- Headings start a new chunk.
- A table is one chunk, however long; tables were the worst-searched content when they were split.

## Related

- [Lantern ingest batch size](lantern-ingest-batch-size.md)
- [Lantern reranker choice](../decisions/lantern-reranker-choice.md)
