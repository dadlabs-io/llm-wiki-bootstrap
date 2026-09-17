---
title: "Quill-bench: one engineer's Kestrel throughput write-up"
date: 2026-08-18
source_url: "https://example.invalid/kestrel"
raw_path: raw/tooling-source.md
ingested_by: claude-code
tier: 1
confidence: high
last_reviewed: 2026-08-18
review_after: 2026-11-18
tags: [kestrel, tooling, benchmark]
---

# Quill-bench: one engineer's Kestrel throughput write-up

## TL;DR
A personal blog post benchmarking Kestrel against Nimbus on a single laptop.

## What
The author ran Quill-bench against Kestrel and against Nimbus, reporting that Kestrel held
its throughput under a slow consumer while Nimbus did not. Nimbus is the author's own queue
and is not covered anywhere else in this wiki.

> Numbers are from one laptop, one run, no repetition.

## Why
It is the only side-by-side of Kestrel and Nimbus anyone has published.

## Related
- [Kestrel delivery guarantees](../../project/architecture/kestrel-delivery-guarantees.md)
- [Kestrel dispatcher](../../project/components/kestrel-dispatcher.md)

