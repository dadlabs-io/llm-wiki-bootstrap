# Archived: the seeded best-practices folder (retired 2026-09-13)

These pages used to be copied into every new project's wiki root as `best-practices/` by
`/new-wiki`. They are kept here for reference and are **never shipped**: nothing under `archive/`
is installed or refreshed.

## Why they were retired

They are the memory-bank-era documents (December 2025 – February 2026, written for the sudoku app)
that came along when the package was first built. Each one has been replaced or belongs to one
project:

| Page | Replaced by |
|---|---|
| `change-request-workflow`, `document-flow` | the **do-code-change** workflow (requirements → plan → red-team → implement → review → verify → commit, with the product-manager / architect / developer / code-reviewer agents; artifacts in `.do-code-change/<slug>/`); cross-project handoffs use `_inbox/intake-<project>/` → `_inbox/done/` |
| `development-workflow` | do-code-change's clarify and plan stages and its human checkpoints; task tracking in `sessions/<persona>/task.md` |
| `persona-workflow-best-practices` | the role agents plus `sessions/<persona>/` (handoff, task, journals) kept by `/wrap-up` |
| `documentation-best-practices` | the wiki's framework-contract docs (authoring, frontmatter) and the generated `_MAP.md` / `_INDEX.md` |
| `opencode-best-practices` | nothing — OpenCode is not in use |
| `coding`, `database`, `logging`, `user-settings`, `specialized/unity`, `specialized/ui` | sudoku-app project knowledge (C# / Unity), not framework doctrine |
| `communication`, `trust` | covered by the user's CLAUDE.md rules |
| `_README`, `_FRAMEWORK_MANAGED` | the folder's own index and marker |

The framework changelog that lived in the same folder moved to `CHANGELOG.md` at the repo root.
Existing copies in the agent-builder-bootstrap and investment-agent notebooks, rpg-strategist and
equal-experts were removed the same day (each checked first: no project-local edits).

Project conventions now belong in each wiki's `wiki/project/best-practices/`, which is the
project's own content.
