---
title: "Context engineering basics"
date: 2026-01-10
source_url: "internal://skilltest/seed/context-engineering-basics"
ingested_by: skilltest-fixture
tier: self
confidence: medium
last_reviewed: 2026-01-10
review_after: 2026-04-10
tags: [context-engineering, agents, prompting]
---

# Context engineering basics

## TL;DR

Context engineering is choosing what goes into a model's context window for each step of a task: instructions, retrieved material, tool results and memory. The window is finite, so the work is deciding what to leave out as much as what to put in.

## What it covers

- **Instructions**: short, specific, and not repeated in several places.
- **Retrieved material**: only what the current step needs, found by search rather than pasted wholesale.
- **Tool results**: trimmed before they are fed back, so one large result does not crowd out everything else.
- **Memory**: notes kept outside the window and read back when relevant.

## Why it matters

A model given too little context guesses; one given too much loses the important parts among the rest. Long-running agents make this worse, because every step adds to the pile.

## Related in this wiki

- [Agent memory architectures](../long-term/agent-memory-architectures.md): memory is the part of context that outlives a single session.
- [LLM agent planning and tools](llm-agent-planning-and-tools.md): planning and tool use decide what an agent needs in context at each step.
- [Prompt caching notes](../tooling/prompt-caching-notes.md): caching makes a stable prefix of the context cheaper to resend.
