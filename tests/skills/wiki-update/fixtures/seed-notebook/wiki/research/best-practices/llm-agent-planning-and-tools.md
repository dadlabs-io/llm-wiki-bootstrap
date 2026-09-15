---
title: "LLM agent planning and tools"
date: 2026-01-12
source_url: "internal://skilltest/seed/llm-agent-planning-and-tools"
ingested_by: skilltest-fixture
tier: self
confidence: medium
last_reviewed: 2026-01-12
review_after: 2026-04-12
tags: [agents, planning, tool-use]
---

# LLM agent planning and tools

## TL;DR

An LLM agent is a loop: the model plans a step, calls a tool, reads the result and decides what to do next. Planning breaks a task into steps; tools let the model act and look things up instead of answering from its weights.

## Planning

Common patterns are decomposing a task into subgoals up front, reflecting on a failed step and revising the plan, and alternating short reasoning with an action (the reason-then-act loop).

## Tools

A tool is a function the model can call with arguments: a search, a calculator, a code runner, an API. Good tool descriptions say when to use the tool, not only what it does.

## Related in this wiki

- [Context engineering basics](context-engineering-basics.md): every tool result lands in the context window.
- [Agent memory architectures](../long-term/agent-memory-architectures.md): memory is how an agent carries what it learned between steps and sessions.
