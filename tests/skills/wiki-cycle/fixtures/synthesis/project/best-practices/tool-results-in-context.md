---
title: "Tool results in context"
date: 2026-01-12
source_url: "internal://skilltest/seed/tool-results-in-context"
ingested_by: skilltest-fixture
tier: self
confidence: medium
last_reviewed: 2026-01-12
review_after: 2027-01-12
tags: [agents, tools, context-engineering]
---

# Tool results in context

## TL;DR

Return the full output of every tool call to the model, so that nothing the tool produced is lost between turns.

## The practice

- Pass each tool result into the context unchanged.
- Do not summarise or cut a result before the model has seen all of it.

## Why it matters

A result the model never saw cannot be reasoned about, so the safest default is to keep every result whole.
