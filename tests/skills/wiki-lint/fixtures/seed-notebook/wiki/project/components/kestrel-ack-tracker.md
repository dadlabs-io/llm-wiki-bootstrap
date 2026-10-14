---
title: "Kestrel ack tracker"
date: 2026-08-20
source_url: "internal://session/seed"
ingested_by: claude-code
tier: self
confidence: high
last_reviewed: 2026-08-20
review_after: 2026-11-18
tags: [kestrel, component, ack]
---

# Kestrel ack tracker

## TL;DR
The ack tracker records every acknowledgement and clears the message from the holding tier.

## What
The ack tracker records each acknowledgement the courier sends back and then clears that message from the holding tier.

## Why
A single place that sees acknowledgements keeps redelivery decisions in one spot.

## Related
- [Kestrel dispatcher](kestrel-dispatcher.md)

