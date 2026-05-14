---
title: Framework-managed folder — do not hand-edit
date: 2026-05-14
ingested_by: install-wiki
tier: self
confidence: high
---

# ⚠️ This folder is framework-managed

Everything in `llm-wiki/how-to/` (this folder) is shipped by the LLM-wiki framework on install. It will be **overwritten** on the next refresh (`install-wiki.ps1 -RefreshOnly` or `/new-wiki --sync`) to pick up the latest framework docs.

## Don't hand-edit files here

If you edit one of these how-to docs in place, your changes are at risk every time the framework is updated.

## Customizing — where your edits belong

If you want a project-specific how-to doc, put it under `llm-wiki/wiki/`:

```
llm-wiki/wiki/how-to/<your-doc>.md
```

That folder is YOUR content, not framework-managed. It survives every refresh and is the right place for:

- Project-specific workflows that don't fit the generic how-to docs
- Internal team conventions that supplement the shipped docs
- Notes that reference your specific repo / codebase

## Customizing — overriding a shipped doc

If a shipped doc (e.g., `how-to/wrap-up.md`) doesn't match how YOUR team works, copy it:

```
cp llm-wiki/how-to/wrap-up.md llm-wiki/wiki/how-to/wrap-up.md
```

Then edit the copy. The shipped version stays at `llm-wiki/how-to/wrap-up.md` (untouched, framework canon); your override lives at `llm-wiki/wiki/how-to/wrap-up.md` and survives refreshes.

In the override, add a "Why this diverges" section at the top so future-you remembers what was customized.

## V2 plan

A future version of the framework will support proper user-override layering — the framework looks for `wiki/how-to/<name>.md` first and falls back to `how-to/<name>.md`, so overrides are first-class. Until then, the copy-elsewhere pattern above is the workaround.

## See also

- `llm-wiki/README.md` — the per-project README explains the framework-managed vs user-content split in detail
- `V2_ROADMAP.md` in the llm-wiki-bootstrap source — tracks the override-layering work
