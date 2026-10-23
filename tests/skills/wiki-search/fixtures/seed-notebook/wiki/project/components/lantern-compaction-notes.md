---
title: "Lantern compaction notes"
date: 2026-03-02
source_url: "internal://skilltest/seed/lantern-compaction-notes"
ingested_by: skilltest-fixture
tier: self
confidence: medium
last_reviewed: 2026-03-02
review_after: 2026-06-02
tags: [lantern, compaction, storage]
---

# Lantern compaction notes

## TL;DR

Lantern compacts its segment files every Sunday night, merging small segments into larger ones so reads touch fewer files.

## What

- Compaction runs after the weekly on-call hand-over checklist is done.
- Segments below 64 MB are merged first.

## Limits

A snapshot shard may not exceed 37 GB; a larger shard is split in two before it is written out.

## Related

- [Lantern chunking](lantern-chunking.md)
