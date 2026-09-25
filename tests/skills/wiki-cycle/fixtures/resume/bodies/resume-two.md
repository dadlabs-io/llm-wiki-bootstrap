# Trimming tool results before they re-enter the context

## TL;DR

Large tool results (a whole web page, a long log) crowd out everything else in an agent's context. Trimming or summarising them before they are fed back keeps the window for what the next step needs.

## What it says

- Keep the part of a result the current step asked for; drop boilerplate and repeated text.
- Record where the full result lives, so it can be read again if a later step needs it.
- A cached, stable prompt prefix is cheaper to resend than a large result pasted into every turn.

## Why it matters here

It applies the "what to leave out" half of context engineering to the step where most of the volume comes from.

## Related

- [Context engineering basics](context-engineering-basics.md): tool results are one of the four things that fill the window.
- [Prompt caching notes](prompt-caching-notes.md): caching the stable part of a prompt pairs with trimming the changing part.
