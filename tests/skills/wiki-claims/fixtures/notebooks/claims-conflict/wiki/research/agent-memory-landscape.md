---
title: "Agent memory landscape, autumn 2026"
date: 2026-09-12
source_url: "https://example.com/agent-memory-landscape"
tier: 3
confidence: medium
tags: [memory, retrieval, comparison]
---

# Agent memory landscape, autumn 2026

## TL;DR
Four memory stores are in common use for coding agents. On the MemBench 10k-document split, Ember leads with 62.5% recall@10, ahead of Vexil.

## Scores
Vexil 2.0 with default settings scores 58.2% recall@10 on the MemBench 10k-document split. Ember scores 62.5% under the same conditions. The BM25 baseline scores 52.0%.

## Practical notes
Ember needs a GPU for indexing, while Vexil indexes on CPU. Teams that already run a vector database often start with that instead of adopting a dedicated store.
