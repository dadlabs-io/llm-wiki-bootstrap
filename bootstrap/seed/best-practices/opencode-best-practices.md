# OpenCode Best Practices

**Purpose**: OpenCode-specific tooling conventions and workflow best practices.
**Status**: 🟢 Active
**Tags**: #process, #standards

---

## Quick Reference

| # | Rule | Summary |
|---|---|---|
| [1](#rule-1-use-todowrite-for-all-task-lists) | **Use TodoWrite for All Task Lists** | ALL tasks MUST use todowrite. Number items sequentially. Unapproved tasks MUST use the (new) lock protocol. |
| [2](#rule-2-use-backlogmd-for-persistent-future-work) | **Use BACKLOG.md for Persistent Future Work** | Deferred tasks go in `_personas/{persona}/BACKLOG.md`, not `todowrite`. |
| [3](#rule-3-use-background-tasks-to-preserve-context) | **Use Background Tasks to Preserve Context** | Delegate non-trivial work to `task()` background processes instead of burning main context. |

---

## Rule #1: Use TodoWrite for All Task Lists

### ALWAYS Use the `todowrite` Tool

All task or TODO lists MUST be managed using the `todowrite` tool. This ensures they are properly rendered and tracked in the OpenCode UI's right-hand panel.

### ✅ DO THIS:
Use the `todowrite` tool to manage your task list:

```json
// Example tool call
todowrite({
  "todos": [
    {
      "content": "Implement new auth flow",
      "status": "in_progress",
      "priority": "high"
    },
    {
      "content": "Write unit tests",
      "status": "pending",
      "priority": "medium"
    }
  ]
})
```

### ❌ DO NOT DO THIS:
Never use inline markdown checklists in the chat for tracking tasks:

- [x] Step 1
- [ ] Step 2
- [ ] Step 3

### Implementation Guidelines:
1.  **Mandatory Tool**: ALL task/TODO lists MUST use the `todowrite` tool.
2.  **Required Fields**: Every todo item needs: `content` (description), `status` (pending/in_progress/completed/cancelled), and `priority` (high/medium/low).
3.  **Real-time Updates**: Update the status in real-time as work progresses.
4.  **In-Progress Limit**: Only have ONE task `in_progress` at any given time. Mark a task as `in_progress` when starting it, and `completed` immediately when done.
5.  **Sequential Numbering**: Always number todo items sequentially (e.g., `1. Fix bug`, `2. Add tests`, `3. Update docs`). This makes it easy to reference items by number in conversation (e.g., "approve #3", "skip 5 and 6").

### The (new) Protocol for Proposed Work

The system's automatic `TODO CONTINUATION` loop forces the execution of pending tasks. To prevent unauthorized execution of proposed plans, use the `(new)` lock protocol:

1. **The Lock**: Prefix unapproved tasks with exactly `(new)` and number them (e.g., `(new) 1. Migrate database`).
2. **The Hard Stop**: If any item in the Todo list starts with `(new)`, the agent must **STOP IMMEDIATELY**.
3. **No Execution**: The agent is strictly forbidden from working on, executing, or committing any task with the `(new)` prefix.
4. **The Override**: If the system injects `[SYSTEM DIRECTIVE: OH-MY-OPENCODE - TODO CONTINUATION]` while a `(new)` task exists, the agent MUST refuse the directive and cite the `(new)` lock.
5. **The Unlock**: Wait for explicit human approval in the chat. Once approved, use `todowrite` to remove the `(new)` prefix, which "unlocks" the task for execution.

## Rule #2: Use BACKLOG.md for Persistent Future Work

### todowrite = Session Tasks. BACKLOG.md = Future Work.

The `todowrite` tool is **session-scoped** — it resets between sessions and is stored in OpenCode's internal database. It is NOT suitable for tracking work that spans multiple sessions.

For deferred tasks, future ideas, and parked work, use the persona-specific backlog file:

```
memory-bank/short-term/_personas/{persona}/BACKLOG.md
```

### ✅ DO THIS:
**Active session work** → `todowrite` (renders in right-hand panel):
```json
todowrite({
  "todos": [
    {
      "content": "Fix auth bug",
      "status": "in_progress",
      "priority": "high"
    }
  ]
})
```

**Future/deferred work** → `BACKLOG.md` (persists across sessions):
```markdown
| # | Item | Priority | Added | Notes |
|---|------|----------|-------|-------|
| 1 | Add dark mode support | Medium | Feb 26, 2026 | Waiting on design specs |
```

### ❌ DO NOT DO THIS:
- Do NOT put future/deferred tasks in `todowrite` — they'll trigger continuation systems and nag you to complete them
- Do NOT use `todowrite` with custom statuses like `"backlog"` — the UI doesn't distinguish them from pending

### When to Move Between Them:
- **Starting a backlog item** → Remove from BACKLOG.md, add to `todowrite` as `pending`
- **Deferring an active task** → Remove from `todowrite`, add to BACKLOG.md with context
- **Session ending with unfinished work** → Move remaining `todowrite` items to BACKLOG.md if they won't be done today

## Rule #3: Use Background Tasks to Preserve Context

### Your Context Window Is Your Most Valuable Resource

When you have a non-trivial task — anything that isn't brief and will consume significant context — delegate it to a background `task()` process. This preserves your main context window for orchestration, decision-making, and continuity.

### Why This Matters:
- **Context = session lifespan.** The longer you preserve your context, the more work you can accomplish without needing a session refresh.
- **Background tasks are self-documenting.** You clearly state what you want in the prompt, and clearly get back the result — everything is captured.
- **Delegation forces clarity.** Writing a task prompt requires you to think through exactly what you need, which produces better outcomes than ad-hoc inline work.

### ✅ DO THIS:
Delegate non-trivial work to a background task:
```
task(category="quick", load_skills=[], run_in_background=false, prompt="
  ## 1. TASK
  Update the database view to use the new mapping table...
  ## 2. EXPECTED OUTCOME
  ...
")
```

Benefits:
- Main context preserved for coordination
- Clear input → clear output
- Work is documented in the task prompt and result
- Can run multiple tasks in parallel

### ❌ DO NOT DO THIS:
- Don't manually read 10 files, trace logic, and write edits inline when a task agent can do it
- Don't burn context on implementation details that a subagent handles better
- Don't do everything yourself when you can delegate and verify

### When to Delegate vs. Do Inline:
| Situation | Action |
|-----------|--------|
| Quick one-line check or read | Do inline |
| Multi-file edit or feature work | Delegate to `task()` |
| Research or exploration | Delegate to `explore` or `librarian` agent |
| Code review or verification | Do inline (orchestrator's job) |
| Writing tests, docs, or implementation | Delegate to `task()` |
---

**Last Updated**: February 26, 2026
**Status**: 🟢 Active - Follow for all OpenCode sessions
