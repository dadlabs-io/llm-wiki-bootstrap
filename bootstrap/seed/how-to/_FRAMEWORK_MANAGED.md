---
title: Framework-managed folder — do not hand-edit
date: 2026-05-14
ingested_by: install-wiki
tier: self
confidence: high
---
# ⚠️ This folder is framework-managed

`llm-wiki/how-to/` (this folder) is shipped and refreshed by the installed packs, and its layout is **one
folder per installed package** (2026-09-08):

```
how-to/
  _FRAMEWORK_MANAGED.md      ← this marker, the only file at the root
  llm-wiki/                  ← the LLM-wiki framework's own pack: llm-wiki.md (entry page),
                                getting-started.md, commands.md, install.md, drive-setup.md,
                                skills/<name>.md (one per skill), agents/<name>.md (one per agent)
  <other-package>/           ← every other pack you install (e.g. agent-builder/) — same shape
```

Each package's folder is written by that package's installer and **overwritten on its next refresh**
(`new-wiki.py --phase docs --target-folder <project>` refreshes `llm-wiki/`; re-running Phase B with
`--force` rewrites the whole framework tree; another pack's installer refreshes its own folder). A refresh
never removes another package's folder. `/new-wiki --sync` refreshes the global skills and never touches a
project.

Before 2026-09-08 the framework's pages sat flat at this root (`commands.md`, `getting-started.md`,
`install.md`, `drive-setup.md`, `wiki-cycle.md`, `wiki-search.md`, `wiki-update.md`, `wrap-up.md`,
`upd-docs.md`). They moved into `llm-wiki/` (the four skill guides folded into their skill pages). A project
created before then still carries the old root copies until `--phase docs --prune-retired` removes them.

## Don't hand-edit files here

If you edit one of these docs in place, your changes are at risk on the next refresh.

## Customizing — where your edits belong

Project-specific how-to docs go under `llm-wiki/wiki/`:

```
llm-wiki/wiki/how-to/<your-doc>.md
```

That folder is YOUR content, not framework-managed. It survives every refresh and is the right place for
project-specific workflows, team conventions that supplement the shipped docs, and notes that reference
your specific repo.

## Customizing — overriding a shipped doc

Copy the shipped page, e.g. `llm-wiki/how-to/llm-wiki/skills/wrap-up.md`, to
`llm-wiki/wiki/how-to/wrap-up.md` and edit the copy; add a "Why this diverges" section at the top. The
shipped version stays untouched as framework canon.

## V2 plan

A future version will layer overrides properly — the framework looks for `wiki/how-to/<name>.md` first and
falls back to the shipped page — so overrides are first-class. Until then, the copy-elsewhere pattern above
is the workaround.

## See also

- `llm-wiki/README.md` — the per-project README explains the framework-managed vs user-content split
- `V2_ROADMAP.md` in the llm-wiki-bootstrap source — tracks the override-layering work
