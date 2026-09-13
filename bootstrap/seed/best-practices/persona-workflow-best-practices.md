# Persona Workflow Best Practices

**Purpose**: AI persona collaboration protocols, territory mapping, and handoff procedures.
**Status**: 🟢 Active
**Tags**: #process, #standards

This document defines how different AI personas (DEV, ARCH, QA, PM) interact, share territory, and handle handoffs to ensure consistency and prevent architectural drift.

## 🎭 Persona Territory Map

| Persona | Primary Territory | Workflow Artifacts |
|---------|------------------|-------------------|
| **DEV** | the code tree | `sessions/dev/task.md`, `<task>-implementation-plan.md`, `<task>-working-notes.md` |
| **ARCH**| `project/architecture/`, `project/decisions/` | `sessions/arch/task.md`, Design docs, system map |
| **PM**  | persona definitions, workflows | `sessions/pm/task.md`, Persona definitions, workflows |
| **CR**  | change-request workflow | `sessions/cr/task.md`, Fix lists, release notes |
| **QA**  | test plans | `sessions/qa/task.md`, Test plans, checklists |
| **DEPLOY** | deployment docs | `sessions/deploy/task.md`, Release checklists, store guides |

Every persona's working files live under `sessions/<persona>/` in the wiki: `handoff.md` (resume dump), `task.md` (NOW / QUEUE) and the dated journals. `/wrap-up` Step 0.5 writes the first two; the Resuming step in CLAUDE.md reads them on startup.

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

- **DEV**: `sessions/dev/task.md`, status, and active implementation plan link.
- **ARCH**: `sessions/arch/task.md`, status, and system map health.
- **PM**: `sessions/pm/task.md`, status, and workflow health.
- **QA**: `sessions/qa/task.md`, status, and testing progress.

### Per-Persona Resume Files (Agent-Facing)

Each persona has its own folder under `sessions/` in the wiki, created on demand by the first `/wrap-up` — there is no fixed list and no template file to copy:

```
sessions/
  active-context.md           ← shared dashboard, one section per persona
  main/                       ← the default persona
    handoff.md                ← full resume dump (overwritten every wrap-up)
    task.md                   ← NOW / QUEUE (updated in place)
    2026-09/                  ← dated session journals (append-only)
  arch/                       ← any other persona: same three things
```

**Rules:**
- `handoff.md` is the persona's resume file — the Resuming step in CLAUDE.md reads it first on session start, before the first reply
- `/wrap-up` Step 0.5 writes `handoff.md` and `task.md` and updates the persona's section of `active-context.md`; a wrap-up never leaves them stale
- Before the first wrap-up none of them exist; a cold start then reads the newest journal if any, else treats the project as new
- A persona's folder is runtime state, project-specific, never copied from the bootstrap

## 📂 Persona Subfolders

To prevent "Checklist Collision" and maintain a clear individual context, each persona uses its own subfolder of `sessions/`:
- **Path**: `sessions/<persona>/`
- **Primary files**: `task.md` (role-specific NOW / QUEUE) and `handoff.md` (resume dump).
- **Rationale**: This allows personas to maintain their own "working brain" without overwriting other roles' checklists; the shared `sessions/active-context.md` is the only file every persona touches, and only its own section.


---

## 🧼 Context Isolation

When switching to a core role (DEV or ARCH), it is often better to use a "blank slate" persona instance (switching to the persona after a fresh context load) to ensure they have no lingering bias or outdated session knowledge, strictly following the definitions and the latest Memory Bank state.
