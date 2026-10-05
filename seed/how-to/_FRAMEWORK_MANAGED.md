---
title: "How-to folder — framework-managed, one folder per installed package"
type: how-to
pack: llm-wiki
installed_by: install-wiki
date: 2026-10-04
---

# ⚠️ This folder is framework-managed

`how-to/` in the global toolset (this folder) holds the usage docs of every package installed globally on this
machine, **one folder per package**:

```
how-to/
  _FRAMEWORK_MANAGED.md      ← this marker, the only file at the root
  llm-wiki/                  ← the LLM-wiki framework's own pack: llm-wiki.md (entry page),
                                getting-started.md, commands.md, user-guide.md, install.md, drive-setup.md,
                                skill-suggestions.md, skills/<name>.md, agents/<name>.md
  <other-package>/           ← every other pack you install (e.g. do-code-change/) — same shape
```

Each package's folder is written by that package's installer and **overwritten on its next refresh**. The
llm-wiki install (`install-wiki.ps1 -RefreshOnly`, or `new-wiki.py --phase docs` for the docs alone, with `--check`
to report first) keeps `llm-wiki/`; another pack's installer keeps its own folder. A refresh never removes
another package's folder. Until 2026-10-04 every project wiki carried its own copy of these folders; they live
only here now.

## Don't hand-edit files here

An edit made here is lost on the next refresh. Change the page in its package's source (for llm-wiki, the
llm-wiki-bootstrap repo: `wiki-seed/`, or `<skill>/wiki-seed/`) and refresh.

## Project-specific how-to docs

They belong in the project's own wiki, e.g. `wiki/project/patterns/<your-doc>.md`: that is the project's content,
never touched by a refresh. To diverge from a shipped page for one project, write the project's version there and
say at its top why it diverges.
