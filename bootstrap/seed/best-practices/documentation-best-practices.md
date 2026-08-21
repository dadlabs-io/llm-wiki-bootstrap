# Documentation Best Practices

**Purpose**: Standards for documentation structure, directory organization, and writing conventions.
**Status**: 🟢 Active
**Tags**: #process, #standards

---

## 🏗️ Structure Strategy

### The Maps (Indexing)
Every folder MUST have a `_README.md` that acts as a Table of Contents (named with underscore to sort to top).
- **Root**: `memory-bank/system-map.md` (Global Context)
- **Deep**: `long-term/components/hints/_README.md` (Local Context)
- **Goal**: You should be able to navigate the entire library by clicking links, without searching.

### The Folders
- **`short-term/`**: Active work (context, task lists, implementation plans).
- **`long-term/`**: Permanent reference (decisions, architecture, rules).
    - **`concepts/`**: "How it works" (Architecture, Algorithms).
    - **`components/`**: "What it is" (Modules, Systems).
    - **`best-practices/`**: "How to do it" (Rules, Guides).
- **`archive/`**: Completed plans and old logs.
- **`reading-lists/`**: Contextual groupings of files.
    - Used to quickly load relevant context for a specific task (e.g., `hint-system-reading-list.json` might include architecture, UI, and C# files).
    - Think of these as "Context Playlists."

---

## 📝 Writing Standards

### 1. Title & Header
Every file starts with a clear H1 and metadata block.
```markdown
# [Title]

**Purpose**: One line summary of why this file exists.
**Status**: 🟢 Active / 🟡 Draft / 🔴 Deprecated
**Tags**: #keyword, #system
```

### 2. Linking
- **Internal Links**: Use relative paths or `memory-bank/` root paths.
- **Code Links**: Use absolute file URIs: `[GameManager.cs](file:///c:/path/to/script.cs)`.

### 3. Conciseness (The "No Wall of Text" Rule)
- Use tables for structured data.
- Use lists for steps.
- Use Mermaid diagrams for logic flows.
- If a file exceeds 500 lines, consider splitting it.

---

## 🔄 Maintenance Rituals

### The "Librarian's Check" (Weekly)
1. Are there orphans in `planning/`? -> Move to `long-term/`.
2. Are `active-context.md` tasks stale? -> status update.
3. Is `system-map.md` still accurate?

### Handoff Protocol (DEV -> ARCH)
1. **DEV**: Documents changes in `short-term/implementation_plan.md`.
2. **ARCH**: Extract insights -> Update `long-term/` docs.
3. **ARCH**: Archive the plan -> `archive/implementation-plans/`.
    - **CRITICAL**: Ensure the plan captures *what failed* ("Negative Knowledge").
    - If a path was abandoned, document **WHY** before archiving.
    - Future us needs to know: "We tried X, it broke Y, so we did Z."

---

## 🏷️ Tagging System (Future)
Standard tags to use in headers:
- `#architecture`
- `#database`
- `#ui`
- `#hints`
- `#solver`
- `#process`
