---
title: "Transformer attention overview"
date: 2026-01-13
source_url: "internal://skilltest/seed/transformer-attention-overview"
ingested_by: skilltest-fixture
tier: self
confidence: medium
last_reviewed: 2026-01-13
review_after: 2026-04-13
tags: [transformers, attention, language-models]
---

# Transformer attention overview

## TL;DR

A transformer processes a sequence by letting every position attend to every other: each token builds a query, compares it with the keys of the others, and takes a weighted mix of their values. Stacking these attention layers with feed-forward layers is the architecture behind today's language models.

## The mechanism

Attention weights come from the similarity of a query with each key, scaled and normalised. Several attention "heads" run side by side, each free to track a different relation. Because attention itself ignores order, position information is added to the inputs.

## Why it replaced recurrence

Recurrent networks read a sequence one step at a time; attention looks at all positions at once, which trains much faster on parallel hardware and handles long-range links more easily.

## Related in this wiki

- [Neural network fundamentals](../tooling/neural-network-fundamentals.md): the layers, weights and training that attention is built from.
- [Prompt caching notes](../tooling/prompt-caching-notes.md): caching reuses the keys and values attention computes for a repeated prefix.
