---
title: "Trimming tool results before reuse"
date: 2026-09-15
source_url: "internal://skilltest/seed/trimming-tool-results-before-reuse"
ingested_by: skilltest-fixture
tier: self
confidence: medium
last_reviewed: 2026-09-15
review_after: 2026-12-15
tags: [agents, tools, context-engineering]
---

# Trimming tool results before reuse

## TL;DR

Long tool results crowd the context and are re-sent on every later turn. Trim a large result to what the next step needs and keep the full output on disk with a pointer the agent can follow.

## What it covers

- **Trimming**: cut a result to the fields or lines the task needs before it enters the context.
- **Pointers**: store the whole output in a file and give the model its path.
- **Cost**: a single forty-kilobyte log kept in context is paid for again on every following turn.

## Why it matters

Agents that pass every tool result through whole spend most of their context on output they never use again. Trimming with a pointer keeps the detail reachable without carrying it.
