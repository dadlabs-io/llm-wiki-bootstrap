---
title: "sessions/ — per-agent episodic memory"
date: 2026-05-25
source_url: internal://framework/sessions-readme
ingested_by: claude-code
tier: self
confidence: high
last_reviewed: 2026-05-25
review_after: 2027-05-25
raw_path: (none — self-authored)
tags: [readme, folder-marker, four-layer-model, sessions, episodic, self-authored]
---

# `sessions/` — per-agent episodic memory

**Cognitive analogue**: episodic memory.
**Frame**: "what happened when I tried X last Thursday."
**Owner**: per-agent (or per-persona). Each agent / persona writes its own session-by-session log here.

This is the **sessions** layer of the four-layer memory model (icarus integration plan §6). The four layers map 1:1 to classical cognitive memory types:

| Layer | Cognitive science term | Frame | Filesystem location |
|---|---|---|---|
| **Working memory** | Working memory (literal) | What's in context right now | Agent's conversation context — no on-disk location |
| **Sessions** ← _you are here_ | Episodic memory | "What happened when I tried X last Thursday" | `<topic>/wiki/sessions/<persona-or-agent-id>/YYYY-MM/<session-id>.md` |
| **Project** | Semantic memory (internal) | "What I know about THIS thing we're building" | `<topic>/wiki/project/` |
| **Research** | Semantic memory (external) | "What I learned from things we ingested" | `<topic>/wiki/research/` |

## Convention

```
sessions/
└── <persona-or-agent-id>/        e.g. arch/, dev/, pm/, claude-code/, codex/
    └── YYYY-MM/                  e.g. 2026-05/
        └── <session-id>.md       short slug or ISO datetime
```

Each session file is **immutable once written** (per the no-deletion-only-forgetting principle). The session captures what happened in one bounded conversation: what was attempted, what worked, what didn't, what the next agent should know.

## What goes here

- Session handoff docs (the per-persona handoff.md / task.md / completed.md content that used to live in `memory-bank/short-term/_personas/<persona>/`)
- Wrap-up notes from `/wrap-up` skill — durable observations from a single session worth preserving
- Attempted-but-not-completed work that future sessions should know about
- "Failed attempts and why" — episodic counter-evidence that prevents future agents from re-trying the same dead-end

## What does NOT go here

- **Cross-agent durable knowledge about the codebase** → `project/` (components, decisions, architecture, patterns, troubleshooting)
- **External research** (papers, blog posts, vendor docs) → `research/`
- **Current-session scratch** → agent's working memory (no disk persistence)

## Briefing-rule signal

Per the four-layer model: an agent starting a development task pulls `sessions/` + `project/` by default, and only touches `research/` if the task explicitly references it. The folder split makes "what to load on session start" structurally clear instead of needing per-persona reading-list curation.

## Privacy

`sessions/` may contain per-persona context (the agent's own notes about its own struggles). Privacy is enforced at the **briefing-rules layer**, not by tree separation — every agent can see every other agent's sessions if explicitly asked, but the default briefing only loads the current agent's own session log.

## Related

- [icarus-integration-plan.md §6](../best-practices/framework/icarus-integration-plan.md) — the four-layer model spec
- [project/README.md](../project/README.md) — the "internal semantic memory" peer
- [research/README.md](../research/README.md) — the "external semantic memory" peer
