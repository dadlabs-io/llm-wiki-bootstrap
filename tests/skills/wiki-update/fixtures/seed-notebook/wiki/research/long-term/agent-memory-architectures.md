---
title: "Agent memory architectures"
date: 2026-01-11
source_url: "internal://skilltest/seed/agent-memory-architectures"
ingested_by: skilltest-fixture
tier: self
confidence: medium
last_reviewed: 2026-01-11
review_after: 2026-04-11
tags: [agent-memory, agents, retrieval]
---

# Agent memory architectures

## TL;DR

Agents keep memory at three levels: the context window (working memory), notes kept for the current task or session, and a long-term store searched when needed. Most designs differ in how the long-term store is written and searched.

## The three levels

- **Working memory**: whatever is in the context window now.
- **Session notes**: a scratchpad or handoff file the agent writes and rereads.
- **Long-term store**: documents, facts or past episodes, found by keyword or vector search.

## Trade-offs

Writing everything down makes the store noisy; writing too little loses what mattered. Search quality decides whether a stored memory is ever found again.

## Related in this wiki

- [Context engineering basics](../best-practices/context-engineering-basics.md): memory is one of the inputs context engineering chooses between.
- [LLM agent planning and tools](../best-practices/llm-agent-planning-and-tools.md): the agent loop decides when to read and write memory.
