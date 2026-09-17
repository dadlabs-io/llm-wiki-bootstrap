---
title: "Kestrel delivery guarantees"
date: 2026-08-20
source_url: "internal://session/seed"
ingested_by: claude-code
tier: self
confidence: high
last_reviewed: 2026-08-20
review_after: 2026-11-18
tags: [kestrel, architecture, delivery]
---

# Kestrel delivery guarantees

## TL;DR
Kestrel delivers at least once, keeps undelivered messages for **14 days**, and offers
three delivery modes.

## What
Every message is retried until acknowledged, so a consumer must be idempotent. Undelivered
messages sit in the holding tier for **14 days** before they are dropped; the operator is
paged at day 10. Kestrel offers three delivery modes: `immediate`, `batched` and `deferred`.

## Why
At-least-once is what the storage layer can promise without a two-phase commit. Fourteen
days covers a long weekend plus a full working week of investigation.

## Related
- [Kestrel dispatcher](../components/kestrel-dispatcher.md)

