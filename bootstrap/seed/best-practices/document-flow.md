# Document Flow Between Personas

**Purpose**: How documents move between personas at each stage of work.  
**Status**: 🟢 Active  
**Tags**: #process, #standards

---

## Flow 1: Change Request (CR) Lifecycle

**Purpose**: New features or refactoring initiatives from backlog.

```
 PM              ARCH             DEV              ARCH             PM
 ─────           ─────            ─────            ─────            ─────
 Creates CR   →  Reviews       →  Implements    →  Verifies      →  Closes
                 Plans                              Updates docs
                 Decides                            Archives plan
```

| Phase | Who | Input Document | Action | Output Document | Moves To |
|-------|-----|---------------|--------|-----------------|----------|
| **1** | PM | Backlog items (BL-xxx) | Create CR | `CR-XXX-<name>.md` | `arch/incoming/` |
| **2** | ARCH | CR document | Review, plan | CR + Implementation Plan | `dev/incoming/` |
| **3** | DEV | CR + Impl Plan | Code changes | CR (with work notes) | `arch/incoming/` |
| **4** | ARCH | Completed CR | Verify, update docs | CR (verified) | `pm/incoming/` |
|       |      | Implementation Plan | Archive | → `archive/implementation-plans/` | — |
| **5** | PM | Verified CR | Close, update backlog | CR (closed) | `archive/change-requests/` |

**Workflow scripts**:
- [ARCH/process-change-request.md](.agent/workflows/ARCH/process-change-request.md)
- [DEV/process-outline.md](.agent/workflows/DEV/process-outline.md)
- [PM/process-change-request-completed.md](.agent/workflows/PM/process-change-request-completed.md)

---

## Flow 2: Code Review (PR) Lifecycle

**Purpose**: Fix findings from GitHub Pull Request reviews (e.g., CodeRabbit).

```
 CR (persona)     ARCH             DEV              ARCH             CR (persona)
 ─────            ─────            ─────            ─────            ─────
 Creates       →  Triages       →  Implements    →  Verifies      →  Closes
 fix-list         Creates           fixes            Updates          Archives
                  outline                            fix-list
```

| Phase | Who | Input Document | Action | Output Document | Moves To |
|-------|-----|---------------|--------|-----------------|----------|
| **1** | CR | PR findings | Create fix-list | `pr-X-fix-list.md` | `arch/incoming/` |
| **2** | ARCH | Fix-list | Triage, create outline | `pr-X-fix-outline.md` | `dev/incoming/` |
| **3** | DEV | Fix outline | Implement fixes | Outline (with notes) | `arch/incoming/` |
| **4** | ARCH | Completed outline | Verify, update fix-list | Fix-list (updated) | `cr/incoming/` |
|       |      | Fix outline | Archive | → `archive/code-reviews/` | — |
| **5** | CR | Verified fix-list | Distribute findings, close | Fix-list (closed) | `archive/code-reviews/` |

**Workflow scripts**:
- [ARCH/process-fix-list.md](.agent/workflows/ARCH/process-fix-list.md)
- [DEV/process-outline.md](.agent/workflows/DEV/process-outline.md)
- [ARCH/process-outline-completed.md](.agent/workflows/ARCH/process-outline-completed.md)
- [CR/process-fix-list-completed.md](.agent/workflows/CR/process-fix-list-completed.md)

---

## Flow 3: Development Workflow (Within a Single Persona)

**Purpose**: How any persona approaches code changes (used within Flows 1 & 2).

```
 Discussion → Planning → Documentation → Approval → Execution
    (NO CODE)   (NO CODE)    (NO CODE)     (NO CODE)    (CODE!)
```

| Phase | Document Created | Location |
|-------|-----------------|----------|
| Discussion | (none — analysis only) | — |
| Planning | (none — design only) | — |
| Documentation | `task.md` (checklist) | `memory-bank/short-term/task.md` |
|  | `<task>-implementation-plan.md` | `memory-bank/short-term/` |
| Approval | (user sign-off) | — |
| Execution | Code changes + updated docs | Source files |

**Reference**: [development-workflow.md](memory-bank/long-term/best-practices/development-workflow.md)

---

## Inbox Map

```
memory-bank/short-term/_personas/
├── arch/incoming/    ← Receives: CRs (from PM), fix-lists (from CR), outlines (from DEV)
├── dev/incoming/     ← Receives: CRs with plans (from ARCH), outlines (from ARCH)
├── pm/incoming/      ← Receives: Verified CRs (from ARCH)
└── cr/incoming/      ← Receives: Verified fix-lists (from ARCH)
```

---

## Archive Destinations

| Document Type | Archive Location |
|--------------|-----------------|
| Completed CRs | `memory-bank/archive/change-requests/` |
| Implementation Plans | `memory-bank/archive/implementation-plans/` |
| Fix Lists | `memory-bank/archive/code-reviews/` |
| Fix Outlines | `memory-bank/archive/code-reviews/` |

---

## Quick Reference: Who Owns What?

| Persona | Creates | Receives | Closes |
|---------|---------|----------|--------|
| **PM** | CRs (from backlog) | Verified CRs | CRs → archive |
| **ARCH** | Implementation Plans, Fix Outlines | CRs, Fix-lists, Completed outlines | Impl Plans → archive |
| **DEV** | Code changes, Work notes | CRs + Plans, Fix outlines | (returns docs to ARCH) |
| **CR** | Fix-lists (from PR reviews) | Verified fix-lists | Fix-lists → archive |

---

Last Updated: February 13, 2026
