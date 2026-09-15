---
title: "Prompt caching notes"
date: 2026-01-15
source_url: "internal://skilltest/seed/prompt-caching-notes"
ingested_by: skilltest-fixture
tier: self
confidence: medium
last_reviewed: 2026-01-15
review_after: 2026-04-15
tags: [prompt-caching, language-models, cost]
---

# Prompt caching notes

## TL;DR

When many requests start with the same text (a system prompt, a long document), a provider can keep the model's intermediate state for that prefix and reuse it, so later requests with the same start are cheaper and faster. The saving depends on keeping the prefix identical.

## How it works

The model's attention layers compute keys and values for every token of the prompt. Caching stores them for a prefix; a later request that begins with exactly the same tokens skips recomputing them.

## Practical rules

- Put what never changes first and what changes last.
- A single changed character early in the prompt invalidates everything after it.
- Caches expire after a while, so the benefit is largest for bursts of similar requests.

## Related in this wiki

- [Transformer attention overview](../long-term/transformer-attention-overview.md): the keys and values being cached come from attention.
- [Context engineering basics](../best-practices/context-engineering-basics.md): ordering the context well is what makes caching pay.
