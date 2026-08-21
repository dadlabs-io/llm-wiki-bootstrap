# Persona Workflow Best Practices

**Purpose**: AI persona collaboration protocols, territory mapping, and handoff procedures.
**Status**: 🟢 Active
**Tags**: #process, #standards

This document defines how different AI personas (DEV, ARCH, QA, PM) interact, share territory, and handle handoffs to ensure consistency and prevent architectural drift.

## 🎭 Persona Territory Map

| Persona | Primary Territory | Workflow Artifacts |
|---------|------------------|-------------------|
| **DEV** | `unity-code/` | `short-term/_personas/dev/task.md`, `<task>-implementation-plan.md`, `<task>-working-notes.md` |
| **ARCH**| `memory-bank/long-term/` | `short-term/_personas/arch/task.md`, Design docs, system-map.md |
| **PM**  | `_personas/`, `.agent/workflows/` | `short-term/_personas/pm/task.md`, Persona definitions, workflows |
| **CR**  | `.agent/workflows/CR/` | `short-term/_personas/cr/task.md`, Fix lists, release notes |
| **QA**  | `memory-bank/short-term/` (Test) | `short-term/_personas/qa/task.md`, Test plans, checklists |
| **DEPLOY** | `memory-bank/long-term/deployment/` | `short-term/_personas/deploy/task.md`, Release checklists, store guides |

---

## Persona Protocol

> [!CRITICAL]
> **STRICT SIGN-OFF ENFORCEMENT:**
> You **MUST** sign off every single message with your active persona tag (e.g., `[DEV]`, `[ARCH]`, `[PM]`).
> **FAILURE TO SIGN OFF IS A CRITICAL ERROR.**
> If you do not sign off, the user cannot trust which context you are operating in.
> Treat the sign-off as the **checksum** of your response. If the tag is missing, the response is invalid.

### Active Personas
- **Architect (`[ARCH]`)**: High-level design, system coherence, long-term memory management.
- **Product Manager (`[PM]`)**: User requirements, feature definition, prioritization.
- **Developer (`[DEV]`)**: Implementation, bug fixing, detailed coding tasks.
- **Code Reviewer (`[CR]`)**: Fetch findings, triage, close fix lists, archive.
- **QA (`[QA]`)**: Verification, testing scenarios, quality assurance.
- **Deployment Manager (`[DEPLOY]`)**: Release pipeline, app store submission, rollout monitoring.

### Switching Personas
When switching to a core role (DEV or ARCH), it is often better to use a "blank slate" persona instance (switching to the persona after a fresh context load) to ensure they have no lingering bias or outdated session knowledge, strictly following the definitions and the latest Memory Bank state.

---

## 🤝 Handoff Protocols

### ARCH ➔ DEV (The Vision)
1. **ARCH** creates a design doc (e.g., `long-term/concepts/feature-analysis.md`).
2. **DEV** reads the design doc and creates a `<task>-implementation-plan.md`.
3. **User** signs off on the implementation plan.

### DEV ➔ ARCH (The Reconciliation)
1. **DEV** completes the task and updates `<task>-implementation-plan.md` with the final results.
2. **DEV** MUST maintain `<task>-working-notes.md` documenting "why" decisions were made and "what was backed out" (e.g., "Used Dictionary instead of List because of lookup performance and order stability").
3. **ARCH** reads the implementation plan and working notes.
4. **ARCH** updates the long-term documentation and `system-map.md` to reflect the new reality.
5. **ARCH** archives the implementation plan.

---

## 📝 Working Notes: The "Why" and "Failed Attempts"

It is critical that the **DEV** persona maintains working notes. 
- **Goal**: Prevent repeating mistakes in 6 months when someone asks, "Why didn't we use a List here?"
- **Content**:
    - Rationale for specific data structures or patterns.
    - Alternatives considered and why they were rejected.
    - Documentation of "back-outs" (approaches tried and abandoned).

---

## 🔄 Active Context Ownership

### Shared Dashboard (Human-Facing)

`sessions/active-context.md` is the **human dashboard** — a cross-persona status overview. Each persona updates **ONLY their section** during the `/wrap-up` workflow (Step 0.5).

- **DEV**: `short-term/_personas/dev/task.md`, status, and active implementation plan link.
- **ARCH**: `short-term/_personas/arch/task.md`, status, and system map health.
- **PM**: `short-term/_personas/pm/task.md`, status, and workflow health.
- **QA**: `short-term/_personas/qa/task.md`, status, and testing progress.

### Per-Agent Active Context (Agent-Facing)

Each agent instance creates its own folder under `_personas/` with an `active-context.md`:

```
_personas/
  persona-manager.md          ← shared template (from bootstrap)
  dev-csharp-unity.md         ← shared template (from bootstrap)
  _agent-template/            ← reference template for new agents
    active-context.md
  my-agent-name/              ← agent instance (runtime, NOT from bootstrap)
    active-context.md         ← "what am I working on right now?"
```

**Rules:**
- **Persona definitions** (`.md` files at root) = shared templates from bootstrap, synced
- **Agent instance folders** (subdirectories) = runtime state, project-specific, never synced
- The agent's `active-context.md` is their personal resume file — read it first on session start
- Use `_personas/_agent-template/active-context.md` as a starting point

## 📂 Persona Subfolders

To prevent "Checklist Collision" and maintain a clear individual context, each persona uses a subfolder in `memory-bank/short-term/_personas/`:
- **Path**: `memory-bank/short-term/_personas/[persona-name]/`
- **Primary file**: `task.md` (Role-specific session tracking).
- **Rationale**: This allows personas to maintain their own "working brain" without polluting the root `short-term/` or overwriting other roles' checklists.


---

## 🧼 Context Isolation

When switching to a core role (DEV or ARCH), it is often better to use a "blank slate" persona instance (switching to the persona after a fresh context load) to ensure they have no lingering bias or outdated session knowledge, strictly following the definitions and the latest Memory Bank state.
