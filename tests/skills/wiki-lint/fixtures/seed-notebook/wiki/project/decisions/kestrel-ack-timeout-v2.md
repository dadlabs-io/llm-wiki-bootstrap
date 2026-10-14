---
title: "Kestrel acknowledgement timeout (current)"
date: 2026-08-20
source_url: "internal://session/seed"
ingested_by: claude-code
tier: self
confidence: high
last_reviewed: 2026-08-20
review_after: 2026-11-18
tags: [kestrel, decision, ack]
---

# Kestrel acknowledgement timeout (current)

## TL;DR
A consumer has 10 seconds to acknowledge a message before it is redelivered.

## What
The acknowledgement timeout is 10 seconds. After that the message is handed to another consumer.

## Why
Measured handlers finish well inside ten seconds, and a shorter timeout recovers stuck consumers sooner.

## Related
- [Kestrel delivery guarantees](../architecture/kestrel-delivery-guarantees.md)

