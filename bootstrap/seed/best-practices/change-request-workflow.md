# Change Request Workflow

**Purpose**: End-to-end process for creating, reviewing, and implementing Change Requests (CRs).
**Status**: 🟢 Active
**Tags**: #process, #standards

---

## Overview

Change Requests bundle related backlog items into architectural initiatives. ARCH owns the CR through implementation.

### ASCII Flow

```text
  PM [Phase 1]       ARCH [Phase 2]      DEV [Phase 3]      ARCH [Phase 4]      PM [Phase 5]
  (Creation)         (Review/Plan)       (Implementation)   (Verification)      (Closure)
      |                  |                   |                  |                  |
      |  1. Create CR    |                   |                  |                  |
      | ────────────────►|                   |                  |                  |
      |                  |  2. Approve/Plan  |                  |                  |
      |                  | ─────────────────►|                  |                  |
      |                  |                   |  3. Build work   |                  |
      |                  |  4. Finish work   |◄─────────────────|                  |
      |                  | ◄─────────────────|                  |                  |
      |                  |                   |                  |  5. Verified     |
      |                  | ────────────────────────────────────►|                  |
      |                  |                   |                  |  6. Close CR     |
      | ◄───────────────────────────────────────────────────────| ────────────────►|
      |                  |                   |                  |                  |
```

```
┌─────────────────────────────────────────────────────────────────┐
│                    CHANGE REQUEST FLOW                          │
│                                                                  │
│      PM ──────► ARCH ──────► DEV ──────► ARCH ──────► PM        │
│    (create)   (review)    (build)    (verify)    (close)        │
│                                                                  │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│   Phase 1        Phase 2       Phase 3       Phase 4    Phase 5 │
│   ────────       ────────      ────────      ────────   ─────── │
│   PM creates     ARCH          DEV           ARCH       PM      │
│   CR from        reviews,      implements    verifies   updates │
│   backlog        plans         from plan     & returns  backlog │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Document ID Registries

| Prefix | Sequence | Description |
|--------|----------|-------------|
| **CR** | CR-001, CR-002, ... | Change Requests — bundles related work into architectural initiatives (sequential, 3 digits) |
| **PR** | PR-8, PR-9, ... | Pull Request reviews — matches GitHub PR number |
| **BL** | BL-001, BL-002, ... | Backlog Items — individual work items (sequential, 3 digits) |
| **FT** | FT-001, FT-002, ... | Feature tickets — feature implementation tracking |
| **RV** | RV-001, RV-002, ... | Code Review tickets — PR/code review tracking |

---

## Personas & Responsibilities

| Persona | Role | Owns CR During |
|---------|------|----------------|
| **PM** | Creates CRs from backlog, closes when done | Phase 1, Phase 5 |
| **ARCH** | Reviews, plans, routes to DEV, verifies completion | Phase 2, Phase 4 |
| **DEV** | Implements from plan | Phase 3 |

---

## Phase 1: CR Creation (PM)

1. **Identify related backlog items** (BL-xxx) that should be done together
2. **Create CR document** in ARCH inbox:
   ```
   memory-bank/short-term/_personas/arch/incoming/CR-XXX-<name>.md
   ```
3. **Include**:
   - Overview of the goal
   - Links to related BL items with summaries
   - Questions for ARCH
   - Suggested approach (optional)

---

## Phase 2: Architectural Review (ARCH)

1. **Pick up CR** from `arch/incoming/`
2. **Review & analyze**:
   - Understand scope and dependencies
   - Check affected codebase areas
   - Consider alternatives
3. **Answer questions** in the CR
4. **Make decision**:
   - `✅ Approved` — Create Implementation Plan, route to DEV
   - `❌ Rejected` — Return to PM with rationale
   - `⏸️ Deferred` — Return to PM with conditions
5. **If approved**: Move CR to `dev/incoming/`

---

## Phase 3: Implementation (DEV)

1. **Pick up CR** from `dev/incoming/`
2. **Follow Implementation Plan** step-by-step
3. **Update CR** with completed work notes
4. **Return CR** to `arch/incoming/` for verification

---

## Phase 4: Verification (ARCH)

1. **Pick up completed CR** from `arch/incoming/`
2. **Verify implementation** matches plan
3. **Update documentation** if needed
4. **Move CR** to `pm/incoming/`

---

## Phase 5: Closure (PM)

1. **Pick up CR** from `pm/incoming/`
2. **Update backlog**:
   - Mark related BL items complete
   - Update CR status to Complete
3. **Archive CR** to `archive/change-requests/`

---

## Folder Structure

```
memory-bank/short-term/_personas/
├── arch/incoming/     ← CRs from PM (Phase 2) or returning from DEV (Phase 4)
├── dev/incoming/      ← Approved CRs with Implementation Plans (Phase 3)
└── pm/incoming/       ← Verified CRs returning for closure (Phase 5)
```

## Document Naming Convention

### Pattern

```
{ID}-{description}-{document-kind}.md
```

| Part | Description | Examples |
|------|-------------|---------|
| **ID** | Parent CR or PR number | `CR-004`, `PR-8` |
| **ID (sub-plan)** | Dot notation for child plans | `CR-004.1`, `CR-004.3` |
| **Description** | Kebab-case short name | `color-settings-ui`, `save-themes-to-db` |
| **Document Kind** | Spelled-out type suffix | `change-request`, `implementation-plan`, `fix-list`, `outline`, `walkthrough` |

### Document Kinds

| Kind Suffix | Who Creates | When |
|-------------|-------------|------|
| `-change-request` | PM | Phase 1 — bundling backlog items |
| `-implementation-plan` | ARCH | Phase 2 — after CR review |
| `-outline` | ARCH | Code review triage — quick fixes |
| `-fix-list` | CR persona | After PR review (e.g., CodeRabbit) |
| `-walkthrough` | Any | Post-completion summary |

### Examples

**CR Flow**:
```
CR-004-color-settings-ui-change-request.md          ← PM creates
CR-004-color-settings-ui-implementation-plan.md      ← ARCH creates (main plan)
CR-004.1-theme-db-implementation-plan.md             ← ARCH creates (sub-plan)
```

**PR Flow**:
```
PR-8-coderabbit-fix-list.md                          ← CR persona creates
PR-8-coderabbit-outline.md                           ← ARCH creates
PR-8-coderabbit-walkthrough.md                       ← Any persona creates
```

**Backlog items** (no document-kind suffix — only one doc type):
```
BL-011-color-settings-ui.md
```

> **ID Registries**: See [Document ID Registries](#document-id-registries) at the top of this document.

### Archive Naming

Add date prefix when archiving: `YYYY-MM-DD-{original-filename}.md`

```
archive/implementation-plans/2026-02-08-CR-004-color-settings-ui-implementation-plan.md
archive/code-reviews/2026-02-08-PR-8-coderabbit-fix-list.md
```

### Document Hierarchy

```
CR-004                                        ← PM creates
├── CR-004-...-implementation-plan             ← ARCH creates
│   ├── CR-004.1-...-implementation-plan       ← ARCH creates (sub-plan)
│   └── CR-004.2-...-implementation-plan       ← ARCH creates (sub-plan)
└── (code changes)                             ← DEV implements

PR-8                                          ← GitHub (external)
├── PR-8-...-fix-list                          ← CR persona creates
├── PR-8-...-outline                           ← ARCH creates
└── PR-8-...-walkthrough                       ← Any persona creates
```

---

## Related Workflows

- [ARCH/process-change-request.md](file:///.agent/workflows/ARCH/process-change-request.md)
- [PM/process-change-request-completed.md](file:///.agent/workflows/PM/process-change-request-completed.md)
- [DEV/process-outline.md](file:///.agent/workflows/DEV/process-outline.md)
- [document-flow.md](memory-bank/long-term/best-practices/document-flow.md)

---

Last Updated: February 8, 2026

