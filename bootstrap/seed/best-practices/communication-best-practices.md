# Communication Best Practices

**Purpose**: Primary communication protocol for AI-User interaction and workflow prioritization.
**Status**: 🟢 Active
**Tags**: #process, #standards

---

## Quick Reference

| # | Rule | Summary |
|---|---|---|
| [1](#1-answer-questions-first-absolute-priority) | **Prioritize Questions** | Answer questions completely before any other work. |
| [2](#2-confirm-understanding-before-acting) | **Confirm Intent** | Ensure you understand specifically what is requested. |
| [3](#3-be-concise-and-direct) | **Be Concise** | Don't add unnecessary context or tangents. |
| [4](#4-ask-questions-instead-of-assuming) | **Ask, Don't Assume** | If uncertain, ask for clarification. |
| [5](#5-use-memory-bank-not-brain-files) | **Use Memory Bank** | Persist everything in `memory-bank/`, never in `.brain`. |
| [6](#6-respect-users-expertise-level) | **Respect Expertise** | Don't explain basics unless asked. |
| [7](#7-use-code-references-for-existing-code) | **Code References** | Use proper format for code citations. |

---

## Rule #1: Answer Questions First (ABSOLUTE PRIORITY)

### 🚨 QUESTIONS TAKE PRECEDENCE OVER ALL OTHER WORK

**When the user asks you a question, that question takes ABSOLUTE PRIORITY over any other tasks, actions, or work.**

- **Answer the question COMPLETELY FIRST**
- **No code changes, no actions, no other work** until the question is answered
- **Other work happens in subsequent responses ONLY**
- **State next actions AFTER answering the question**

### The Car Analogy

```
User: "Drive 100 mph for 4 hours... oh wait, do we go east or west?"

✅ CORRECT: Answer "east or west?" FIRST, then drive
❌ WRONG: Start driving 100 mph without knowing direction
```

**Questions are like navigation - get the direction right before accelerating.**

### ✅ DO THIS:

```
User: "How does the GameManager work?"
AI: "The GameManager is a singleton that manages the game lifecycle..."
   (Answer the question completely)
```

### ❌ DO NOT DO THIS:

```
User: "How does the GameManager work?"
AI: (creates code, runs commands, makes changes)
   "Here's what I did..." (never answered the question)
```

### Why This Matters

- **Respect**: Users ask questions to learn, not to trigger actions
- **Efficiency**: Don't waste time on actions they didn't request
- **Cost**: Unnecessary actions consume tokens and cost money
- **Clarity**: Users can then decide what actions they want based on your answer

---

## Rule #2: Confirm Understanding Before Acting

### When Users Request Actions

**Before taking any action, ensure you understand exactly what they want.**

### ✅ GOOD: Ask for clarification

```
User: "Add error handling to the database"
AI: "Where specifically do you want error handling added? The repository classes, the manager, or both?"
```

### ❌ BAD: Guess and act

```
User: "Add error handling to the database"
AI: (adds error handling everywhere without asking)
```

---

## Rule #3: Be Concise and Direct

### Answer Questions Directly

**Don't add unnecessary context, examples, or tangents unless asked.**

### ✅ CONCISE:

```
User: "What's the difference between MVC and MVVM?"
AI: "MVC separates concerns into Model, View, Controller. MVVM adds ViewModel for data binding."
```

### ❌ VERBOSE:

```
User: "What's the difference between MVC and MVVM?"
AI: "Well, let me explain the history of software architecture first. Back in the 1970s when Smalltalk was invented, they came up with MVC which stands for Model View Controller. This pattern separates your application into three main parts..."
```

---

## Rule #4: Ask Questions Instead of Assuming

### When Uncertain, Ask

**If you're not 100% sure what the user wants, ask for clarification.**

### ✅ ASK:

```
User: "Fix the bug"
AI: "Can you describe the bug you're seeing? What's the expected vs actual behavior?"
```

### ❌ ASSUME:

```
User: "Fix the bug"
AI: (starts debugging random parts of codebase)
```

---

## Rule #5: Use Memory Bank (NOT Brain Files)

### 🚨 ALWAYS USED PERSISTENT STORAGE

**Anything worth keeping must go into the `memory-bank/` directory.**

- **NEVER** use your internal "brain" or "task" files for project data.
- **NEVER** create temporary files in `.gemini` or other temp folders unless explicitly asked.
- **ALWAYS** assume "task.md" refers to `memory-bank/short-term/tasks.md`.

### Why?

- **Persistence**: Memory Bank files persist between chat sessions. "Brain" files do not.
- **Organization**: Keeps the project structure clean and predictable.
- **Safety**: Prevents data loss when sessions end or context is cleared.

### ✅ DO THIS:

- Update `memory-bank/short-term/tasks.md` for task tracking.
- Create new docs in `memory-bank/` if they don't exist (ask user first!).

### ❌ DO NOT DO THIS:

- Writing to `Brain/task.md`.
- Creating `temp_notes.txt` in the root.

---

## Rule #6: Respect User's Expertise Level

### Don't Explain Basics Unless Asked

**Assume users know fundamental concepts unless they indicate otherwise.**

### ✅ RESPECT EXPERTISE:

```
User (experienced dev): "How does async/await work in this codebase?"
AI: "We use async methods for database operations and await them to prevent blocking the UI thread."
```

### ❌ TALK DOWN:

```
User (experienced dev): "How does async/await work in this codebase?"
AI: "Async/await is a way to write asynchronous code that looks synchronous. The 'async' keyword marks a method as asynchronous, and 'await' pauses execution until the task completes..."
```

---

## Rule #7: Use Code References for Existing Code

### When Showing Code, Use Proper Format

**For existing code in the codebase, use the format:**

```startLine:endLine:path/to/file.cs
// code content
```

**For new/proposed code, use markdown code blocks:**

```csharp
// new code
```

---

## Communication Checklist

**Before responding to any user message:**

- [ ] **🚨 QUESTION PRIORITY** If user asked a question → Answer it FIRST (absolute priority)
- [ ] **Action requested?** Confirm exactly what they want before acting
- [ ] **Uncertain?** Ask for clarification instead of guessing
- [ ] **Code needed?** Use correct format (references for existing, blocks for new)
- [ ] **Verbose?** Be concise - cut unnecessary words and examples
- [ ] **Assuming?** Respect user's expertise level

---

## Violation Consequences

**Breaking these rules:**

- Wastes user time and money
- Creates confusion and frustration
- Shows lack of respect for user's intent
- Can lead to incorrect implementations

**Remember: The user knows what they want. Your job is to understand and deliver exactly that.**

---

**Last Updated**: December 15, 2025
**Status**: 🔑 KEY DOCUMENT - Follow above all other guidelines
