---
title: "global-toolset — every global tooling doc, once"
type: readme
standalone: "the toolset notebook's entry page"
---

# global-toolset

One notebook for the docs of the tooling installed globally on this machine (`~/.claude/`): how to use each
skill, agent and workflow, and the framework-contract docs the skills follow. Every project uses the same
tooling, so its docs live here once instead of being copied into every project's wiki.

```
global-toolset/
  README.md                          ← this page
  how-to/
    _FRAMEWORK_MANAGED.md            ← how the folder is kept
    llm-wiki/                        ← the LLM-wiki pack: llm-wiki.md (start here), commands.md, getting-started.md,
                                        user-guide.md, install.md, drive-setup.md, skill-suggestions.md,
                                        skills/<name>.md, agents/<name>.md
    <other pack>/                    ← each other installed pack (agent-builder's packs), written by its own installer
  wiki/project/best-practices/framework/   ← the six framework-contract docs (frontmatter spec, authoring
                                              principles, cycle step contract, …)
```

## How it is kept

- **Installed, not edited.** The llm-wiki install (`install-wiki.ps1`, `-RefreshOnly`, `new-wiki.py --mode tooling`)
  creates this notebook, registers it as `global-toolset` in `linked-notebooks.json`, and makes `how-to/llm-wiki/`,
  the marker, this README and the framework docs match the llm-wiki-bootstrap source.
  `new-wiki.py --phase docs` refreshes only these docs (`--check` reports first). A change made here by hand is
  lost on the next refresh: change the source in its library instead.
- **Each pack writes only its own folder.** Another pack's installer keeps its `how-to/<pack>/`; none removes another's.
- **Not searched.** `/wiki-search` searches a project's own wiki; the installed skills read these pages by path.
- **Projects keep their own work.** A project's decisions, sessions, code-change records and suggestion box stay in
  that project's wiki. Each project's `CLAUDE.md` imports `how-to/llm-wiki/commands.md` from here.
