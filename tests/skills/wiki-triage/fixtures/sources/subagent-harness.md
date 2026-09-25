# Building a coding-agent harness with parallel subagents

A walkthrough of an orchestrator that splits a task into subagents, gives each a narrow tool list and its own brief, and merges their reports. It covers how the harness writes each subagent's instructions, when it runs them in parallel, and how a reviewer agent checks their work before the orchestrator commits.
