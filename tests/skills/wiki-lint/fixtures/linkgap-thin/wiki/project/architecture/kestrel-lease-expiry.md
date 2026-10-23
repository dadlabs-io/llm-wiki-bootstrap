---
title: "Kestrel lease expiry"
date: 2026-10-20
source_url: "internal://session/seed"
ingested_by: claude-code
tier: self
confidence: high
last_reviewed: 2026-10-20
review_after: 2027-01-18
tags: [kestrel, architecture, lease]
---

# Kestrel lease expiry

## TL;DR
When a message's lease runs out without a renewal, Kestrel puts the message back for another consumer.

## What
Expiry is checked by the dispatcher on every pull. An expired message keeps its delivery count.

## Why
Counting deliveries across expiries keeps the at-least-once promise honest.

## Related
- [Kestrel delivery guarantees](kestrel-delivery-guarantees.md)
- [Kestrel dispatcher](../components/kestrel-dispatcher.md)
