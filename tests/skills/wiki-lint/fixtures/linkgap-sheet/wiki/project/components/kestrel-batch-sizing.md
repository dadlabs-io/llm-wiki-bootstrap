---
title: "Kestrel batch sizing"
date: 2026-10-20
source_url: "internal://session/seed"
ingested_by: claude-code
tier: self
confidence: high
last_reviewed: 2026-10-20
review_after: 2027-01-18
tags: [kestrel, component, batching]
---

# Kestrel batch sizing

## TL;DR
Producers batch up to 64 messages per write; the broker caps a batch at 256 KB.

## What
Batches are split at the cap and sent as separate writes.

## Why
A cap bounds the memory one slow write can pin.

## Related
- [Kestrel delivery guarantees](../architecture/kestrel-delivery-guarantees.md)
- [Kestrel dispatcher](kestrel-dispatcher.md)
