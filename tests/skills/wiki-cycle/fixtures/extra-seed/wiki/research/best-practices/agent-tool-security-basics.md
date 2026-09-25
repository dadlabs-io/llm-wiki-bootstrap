---
title: "Agent tool security basics"
date: 2026-01-12
source_url: "internal://skilltest/seed/agent-tool-security-basics"
ingested_by: skilltest-fixture
tier: self
confidence: medium
last_reviewed: 2026-01-12
review_after: 2026-04-12
tags: [agents, security, prompt-injection, tools]
---

# Agent tool security basics

## TL;DR

An agent that can call tools can be steered by any text it reads. Instructions hidden in a web page, an email or a file can make it misuse the tools it holds, so what an agent may read and what it may do have to be decided together.

## What it covers

- **Prompt injection**: text from an untrusted source that the model treats as an instruction.
- **Tool scope**: the fewer tools an agent holds, the less an injected instruction can do.
- **Data exposure**: an agent that can read private data and also send data out can leak it.

## Why it matters

The model cannot reliably tell the user's instructions from instructions that arrive inside content. Guarding the tools is more dependable than hoping the model ignores the injected text.

## Related in this wiki

- [LLM agent planning and tools](llm-agent-planning-and-tools.md): the tools an agent plans with are the tools an injection can misuse.
- [Context engineering basics](context-engineering-basics.md): untrusted material enters an agent through its context.
