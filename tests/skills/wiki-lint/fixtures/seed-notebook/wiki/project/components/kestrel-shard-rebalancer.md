---
title: "Kestrel shard rebalancer"
date: 2026-08-20
source_url: "internal://session/seed"
ingested_by: claude-code
tier: self
confidence: high
last_reviewed: 2026-08-20
review_after: 2026-11-18
tags: [kestrel, component, rebalancer]
---

# Kestrel shard rebalancer

## TL;DR
The shard rebalancer decides which dispatcher owns which shard, and announces moves.

## What
It holds the shard map, moves a shard when a dispatcher is slow or gone, and announces each
move on the control topic. A move is announced before it takes effect, never after.

## Why
One owner of the shard map means one place to reason about split brain.

## Related
- [Kestrel delivery guarantees](../architecture/kestrel-delivery-guarantees.md)

