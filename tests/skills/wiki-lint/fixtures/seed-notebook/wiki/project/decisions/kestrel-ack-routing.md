---
title: "Where Kestrel acknowledgements go"
date: 2026-08-20
source_url: "internal://session/seed"
ingested_by: claude-code
tier: self
confidence: high
last_reviewed: 2026-08-20
review_after: 2026-11-18
tags: [kestrel, decision, ack]
---

# Where Kestrel acknowledgements go

## TL;DR
Acknowledgements go to the ack tracker, not to the producer.

## What
The courier sends every acknowledgement to the ack tracker. The producer is never told directly.

## Why
The producer may be gone by the time the acknowledgement arrives.

## Related
- [Kestrel delivery guarantees](../architecture/kestrel-delivery-guarantees.md)

