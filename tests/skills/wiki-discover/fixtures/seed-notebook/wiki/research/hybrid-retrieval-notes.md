---
title: "Hybrid retrieval notes: combining keyword and vector search for agents"
date: 2026-09-09
source_url: "https://vellum-eng.example/posts/2026/hybrid-retrieval-for-agents"
tier: 2
confidence: medium
category: research
tags: [retrieval, hybrid-search, agent-memory]
---

# Hybrid retrieval notes

## TL;DR
Keyword (BM25) scoring and dense vectors fail on different queries, so agent memory stores that fuse both recall more than either alone.

## What
A short summary of one engineering post on fusing BM25 and embedding scores with reciprocal rank fusion.
