---
title: "Kestrel lease renewal"
date: 2026-10-20
source_url: "internal://session/seed"
ingested_by: claude-code
tier: self
confidence: high
last_reviewed: 2026-10-20
review_after: 2027-01-18
tags: [kestrel, component, lease]
---

# Kestrel lease renewal

## TL;DR
A consumer renews its lease on a message before the lease expires, or the message returns to the queue.

## What
The consumer sends a renewal at half the lease length. A missed renewal lets the lease expire.

## Why
Short leases free stuck messages quickly without a separate reaper.

## Related
- [Kestrel dispatcher](kestrel-dispatcher.md)
