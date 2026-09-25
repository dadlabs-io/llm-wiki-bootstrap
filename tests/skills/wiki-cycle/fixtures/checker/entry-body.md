# Keeping an agent's context small: eight techniques

## TL;DR

A conference talk walks through eight techniques for keeping an agent's context window small, from trimming tool results to capping tool output. Together they cut token use by 70% on long tasks.

## The techniques

1. Trim tool results before they go back into the window.
2. Summarise old turns once a conversation passes a budget.
3. Retrieve instead of paste: search for the notes a step needs.
4. Keep a stable prompt prefix so caching makes it cheap.
5. Split work across sub-agents, each with a narrow brief.
6. Write a short handoff file at the end of a session.
7. Prune memories nobody has read in a month.
8. Cap each tool's output at a fixed size and say where the full result lives.

> "keep the part the step asked for and drop the rest" — the speaker

## Related

- [Context engineering basics](context-engineering-basics.md): these techniques are the "what to leave out" half of context engineering.
- [Prompt caching notes](prompt-caching-notes.md): technique 4 depends on caching a stable prefix.
