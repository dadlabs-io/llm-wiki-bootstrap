# Development Workflow

**Purpose**: Mandatory phase-based approach (Discussion -> Planning -> Execution) for making changes.
**Status**: 🟢 Active
**Tags**: #process, #standards

## Core Principle: Plan Before You Code

**Never make code changes during analysis or discussion.** The workflow is:

| Phase | Description | Code Changes? |
|-------|-------------|---------------|
| [1. Discussion](#phase-1) | Understand the problem | ❌ NO |
| [2. Planning](#phase-2) | Design the solution | ❌ NO |
| [3. Documentation](#phase-3) | Create task list & plan | ❌ NO |
| [4. Approval](#phase-4) | Get user sign-off | ❌ NO |
| [5. Execution](#phase-5) | Implement the plan | ✅ YES |

Skipping steps leads to broken code, derailed conversations, and wasted effort.

We need to stay at each step until it is successful and completed.
We may end up coming back to one of these phases too as if we go through our planning we find we need to discuss and analyze something different or as we start as we're going to approval we realize we missed something in our planning or as we're doing our coding we noticed that we have to change something

---

## The Development Workflow

<a name="phase-1"></a>
### Phase 1: Discussion & Analysis
**Goal:** Understand the problem completely before proposing solutions.

- **NO CODE CHANGES** during this phase
- Debug and analyze the issue
- Review relevant code and logs
- Ask clarifying questions
- Continue until the problem is fully understood

<a name="phase-2"></a>
### Phase 2: Planning
**Goal:** Design the solution before touching code.

- **NO CODE CHANGES** during this phase
- Identify all files that need to change
- Consider how changes integrate with existing code
- Think holistically about the entire project
- Identify dependencies and potential side effects

<a name="phase-3"></a>
### Phase 3: Documentation
**Goal:** Create written artifacts for tracking and review.

**Step 1: Create Task List**

Update `memory-bank/short-term/task.md`:
- Add new task with checklist items
- Break down into granular sub-tasks
- Present to user for review

**Step 2: Decide on Implementation Plan**

After task list is reviewed, explicitly ask:
> "Do you think we need an implementation plan for this?"

Include your recommendation:
- **Recommend YES** if: 3+ files, refactoring, new components, non-obvious changes
- **Recommend NO** if: single file, obvious fix, documentation only

**Step 3: Create Implementation Plan (if needed)**

Create/update `memory-bank/short-term/<task>-implementation-plan.md`:
- Goal description
- Files to modify/create/delete
- Specific changes per file
- Verification steps

<a name="phase-4"></a>
### Phase 4: Approval
**Goal:** Get explicit user approval before making changes.

- **NO CODE CHANGES** during this phase
- Use `notify_user` to request review of the implementation plan
- **Wait for explicit approval before proceeding**
- "Do it" or "Proceed" = approval
- Anything else = continue discussion

<a name="phase-5"></a>
### Phase 5: Execution
**Goal:** Implement the approved plan completely.

- **READ BEFORE WRITE**: Always read the full file content before applying edits to avoid duplication or context errors.
- **CODE CHANGES** during this phase!
- Make all changes needed for the feature to work
- Don't make partial changes that break the build
- Test compilation after changes
- Update documentation as needed

---

## Documentation Artifacts

### Where Files Live

| Artifact | Location | Purpose |
|----------|----------|---------|
| Active Tasks | `memory-bank/short-term/task.md` | Current work checklist |
| Implementation Plan | `memory-bank/short-term/<task>-implementation-plan.md` | Detailed plan for current task |
| Active Context | `memory-bank/short-term/active-context.md` | Session state summary |
| Archived Plans | `memory-bank/archive/` | Completed implementation plans |

### Implementation Plan Lifecycle

1. **Create** — When starting a non-trivial task
2. **Update** — As planning evolves through discussion
3. **Execute** — Once approved
4. **Archive** — After completion:
   - Move to `memory-bank/archive/implementation-plans/`
   - Rename with format: `YYYY-MM-DD-<brief-description>.md`
   - Example: `2025-12-24-validation-hint.md`

### When to Create an Implementation Plan

**Required for:**
- Any change touching 3+ files
- Refactoring or architecture changes
- New features or components
- Bug fixes with non-obvious solutions

**Not required for:**
- Single-line fixes
- Typo corrections
- Documentation-only updates
- Obvious refactoring (rename, move to helper)

---

## Key Rules

### DO:
- ✅ Ask clarifying questions before proposing solutions
- ✅ Create implementation plan for complex changes
- ✅ Wait for explicit approval before coding
- ✅ Complete the full implementation (don't leave it half-done)
- ✅ Update task.md to track progress

### DON'T:
- ❌ Make code changes during analysis/discussion
- ❌ Create new files/classes without approval
- ❌ Make partial changes that break the build
- ❌ Skip the planning phase because the fix seems "obvious"
- ❌ Assume silence means approval

### 🛡️ Pattern Verification (Critical)

Before modifying ANY shared, core, or model file (e.g., `AppConfig.cs`, `DataManager.cs`), you **MUST**:
1.  **Identify Consumers**: Find 2-3 existing usages of the class/method.
2.  **Verify Usage**: Check how they instantiate or populate the data.
3.  **Confirm Alignment**: Ensure your planned change aligns with these existing patterns.

**Example**:
> *Wrong*: "I need a cover set, so I'll add `ReasoningHouses` to `HintContextData`."
> *Right*: "I need a cover set. I see `X-Wing` uses `HouseIndices` for the Base Set and derives the Cover Set. I should follow that pattern instead of modifying the Model."

**Failure to do this leads to architectural drift and broken contracts.**

---

## Recovery from Mistakes

If code was changed prematurely:
1. **STOP** — Don't try to "fix" by making more changes
2. **Acknowledge** — Inform user of the mistake
3. **Wait** — Let user decide how to proceed (they may want to revert, continue, etc.)
4. **Don't compound the error** by making additional changes

---

## Summary

The difference between good and bad outcomes is simple:

| Good | Bad |
|------|-----|
| Full plan, full execution | Piecemeal changes |
| User approved the approach | Assumed it was fine |
| All 25 files updated cleanly | One rinky-dink change broke everything |
| Holistic thinking | Narrow focus |

**When in doubt: discuss more, plan more, code less.**
