---
title: Framework-managed folder — do not hand-edit
date: 2026-05-14
ingested_by: install-wiki
tier: self
confidence: high
---

# ⚠️ This folder is framework-managed

Everything in `llm-wiki/best-practices/` (this folder) is shipped by the LLM-wiki framework on install. It will be **overwritten** on the next refresh (`install-wiki.ps1 -RefreshOnly` or `/new-wiki --sync`) to pick up the latest curated best-practices.

## Don't hand-edit files here

These files are curated software-development best practices that travel with every install — coding conventions, communication norms, documentation rules, logging guidance, testing approach, trust principles, etc. If you edit one in place, your changes get lost on the next refresh.

## Customizing — where your edits belong

If you want **project-specific** best practices, put them under `llm-wiki/wiki/best-practices/`:

```
llm-wiki/wiki/best-practices/<your-doc>.md
```

That folder is YOUR content, not framework-managed. It survives every refresh and is the right place for:

- Project-specific conventions (this codebase uses X pattern, we don't use Y, etc.)
- Team agreements (PR review rules, branching strategy)
- Anything that doesn't apply to all projects using the framework

## Customizing — overriding a shipped best-practice

If a shipped best-practice (e.g., `coding-best-practices.md`) doesn't match your project's conventions, copy it:

```
cp llm-wiki/best-practices/coding-best-practices.md llm-wiki/wiki/best-practices/coding-best-practices.md
```

Then edit the copy. The shipped version stays at `llm-wiki/best-practices/coding-best-practices.md` (untouched, framework canon); your override lives at `llm-wiki/wiki/best-practices/coding-best-practices.md` and survives refreshes.

In the override, add a "Why this diverges" section at the top so future-you remembers what was customized.

## V2 plan

A future version of the framework will support proper user-override layering — the framework looks for `wiki/best-practices/<name>.md` first and falls back to `best-practices/<name>.md`, so overrides are first-class. Until then, the copy-elsewhere pattern above is the workaround.

## See also

- `llm-wiki/README.md` — the per-project README explains the framework-managed vs user-content split in detail
- `V2_ROADMAP.md` in the llm-wiki-bootstrap source — tracks the override-layering work
