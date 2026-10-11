---
title: "Tool output handling"
date: 2026-01-20
source_url: "internal://skilltest/seed/tool-output-handling"
ingested_by: skilltest-fixture
tier: self
confidence: medium
last_reviewed: 2026-01-20
review_after: 2026-04-20
tags: [context-engineering, agents, tools]
---

# Tool output handling

## TL;DR

What a tool returns is the cheapest place to save context. Tool result trimming, cutting a result down to what the next step needs before the agent sees it, keeps a long run from filling the window with hits nobody reads.

## What to do

- Return a few ranked results, not every match.
- Shorten each result to the part that answers the question.
- Say how much was left out, so the agent can ask for more.

## Related in this wiki

- [Context engineering basics](context-engineering-basics.md): tool results are one of the inputs context engineering chooses between.
- [LLM agent planning and tools](llm-agent-planning-and-tools.md): the agent loop decides which tool to call next.
