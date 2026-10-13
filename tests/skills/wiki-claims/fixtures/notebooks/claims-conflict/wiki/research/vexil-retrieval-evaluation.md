---
title: "Vexil retrieval evaluation, 2026 run"
date: 2026-09-03
source_url: "https://example.com/vexil-retrieval-evaluation"
tier: 2
confidence: medium
tags: [vexil, retrieval, evaluation]
---

# Vexil retrieval evaluation, 2026 run

## TL;DR
Vexil, a vector memory store for coding agents, reached 71.4% recall@10 on MemBench in our evaluation of version 2.0 with its default configuration. It beat a plain BM25 index by 19.4 points.

## Setup
We ran Vexil 2.0 with default settings on the MemBench 10k-document split. Each of the 500 queries was run once. Recall@10 is the share of queries whose gold document appears in the top ten results.

## Results
Vexil reached 71.4% recall@10 on MemBench. The BM25 baseline scored 52.0% on the same split. Median query latency was 38 ms.

## Caveats
This is a single run without a confidence interval. We did not tune any index parameter.
