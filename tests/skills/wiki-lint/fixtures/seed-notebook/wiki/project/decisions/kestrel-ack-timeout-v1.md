---
title: "Kestrel acknowledgement timeout (first version)"
date: 2026-08-20
source_url: "internal://session/seed"
ingested_by: claude-code
tier: self
confidence: high
last_reviewed: 2026-08-20
review_after: 2026-11-18
tags: [kestrel, decision, ack]
superseded_by: kestrel-ack-timeout-v2.md
---

# Kestrel acknowledgement timeout (first version)

## TL;DR
A consumer has 30 seconds to acknowledge a message before it is redelivered.

## What
The acknowledgement timeout is 30 seconds. After that the message is handed to another consumer.

## Why
Thirty seconds was the longest handler anyone expected.

## Related
- [Kestrel delivery guarantees](../architecture/kestrel-delivery-guarantees.md)

