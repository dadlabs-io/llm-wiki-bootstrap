---
title: "Kestrel dispatcher"
date: 2026-08-20
source_url: "internal://session/seed"
ingested_by: claude-code
tier: self
confidence: high
last_reviewed: 2026-08-20
review_after: 2026-11-18
tags: [kestrel, component, dispatcher]
---

# Kestrel dispatcher

## TL;DR
The dispatcher pulls from the holding tier and hands messages to consumers.

## What
The dispatcher asks the shard rebalancer which shards it owns before every pull, and
re-asks whenever the shard rebalancer announces a move. If the shard rebalancer is
unreachable the dispatcher keeps its last assignment and logs a warning. Nothing else in
Kestrel talks to the shard rebalancer directly.

## Why
Keeping the dispatcher ignorant of the rebalancing algorithm means the algorithm can change
without redeploying it.

## Related
- [Kestrel delivery guarantees](../architecture/kestrel-delivery-guarantees.md)

