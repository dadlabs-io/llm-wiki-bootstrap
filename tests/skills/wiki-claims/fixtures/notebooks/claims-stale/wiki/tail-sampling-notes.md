---
title: "Tail sampling notes"
date: 2026-07-15
source_url: "https://example.com/tail-sampling"
tier: 2
confidence: high
tags: [sampling, tracing, collector]
---

# Tail sampling notes

## TL;DR
Tail sampling keeps every trace that contains an error and 10% of the rest.

## How it works
The collector buffers each trace for 30 seconds before deciding whether to keep it. A trace that holds an error span is always kept.

## Cost
At our volume the 10% sample cut storage use by roughly 85%.
