---
title: "Lantern snapshot schedule"
date: 2026-03-05
source_url: "internal://skilltest/seed/lantern-snapshot-schedule"
ingested_by: skilltest-fixture
tier: self
confidence: medium
last_reviewed: 2026-03-05
review_after: 2026-06-05
tags: [lantern, snapshot, operations]
---

# Lantern snapshot schedule

## TL;DR

Lantern takes a snapshot of the whole index every night at 02:00 and keeps the last 14 snapshots. A snapshot is written to the cold store and checked once it lands.

## What

- The snapshot job is paused while a compaction is running.
- A snapshot that fails its check is taken again the next night.
- Snapshot size depends on the index and is reported after each run.

## Related

- [Lantern on-call](lantern-on-call.md)
