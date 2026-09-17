---
title: "How long Kestrel keeps an undelivered message"
date: 2026-08-20
source_url: "internal://session/seed"
ingested_by: claude-code
tier: self
confidence: high
last_reviewed: 2026-08-20
review_after: 2026-11-18
tags: [kestrel, decision, retention]
---

# How long Kestrel keeps an undelivered message

## TL;DR
Undelivered messages are kept for **7 days**, then dropped.

## What
The holding tier keeps an undelivered message for **7 days**. After that it is dropped and
counted in the `kestrel_dropped_total` metric.

## Why
Seven days keeps the holding tier inside one disk. A longer window was considered and
rejected on cost.

## Related
- [Kestrel delivery guarantees](../architecture/kestrel-delivery-guarantees.md)

