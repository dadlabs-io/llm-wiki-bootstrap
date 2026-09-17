---
title: "Lantern ingest batch size"
date: 2026-04-10
source_url: "internal://skilltest/seed/lantern-ingest-batch-size"
ingested_by: skilltest-fixture
tier: self
confidence: high
last_reviewed: 2026-04-10
review_after: 2026-07-09
tags: [lantern, ingest, batching, gpu]
---

# Lantern ingest batch size

## TL;DR

The Lantern ingest worker embeds documents in batches of 250. It was raised from 100 on 2026-04-10 after GPU memory tests.

## What

- One batch is 250 documents, embedded in a single GPU call.
- At 250, peak GPU memory is 14 GB of the worker's 24 GB; at 400 the worker ran out of memory on long PDFs.
- A batch that fails is retried once at half size (125), then the failing documents go to the dead-letter folder.

## Related

- [Lantern chunking](lantern-chunking.md)
- [Lantern embedding retention](../decisions/lantern-embedding-retention.md)
