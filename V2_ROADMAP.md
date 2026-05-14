# LLM-wiki framework — V2 roadmap

Deferred items captured during the V1 design pass. Not in V1 scope; revisit after V1 has run in anger on a few real projects.

## Big ideas

### 1. wiki-agent — turn the framework into an autonomous agent

Today the framework is a collection of skills + scripts that a human invokes (via `/new-wiki`, `/wrap-up`, `/wiki-cycle`, etc.). V2 vision: a long-running agent that owns the wiki for a project.

What it could do:
- Watch the project for code changes and proactively offer `/wrap-up` when a session is ending
- Run `/wiki-cycle` automatically on a schedule (overnight, weekly)
- Notice stale entries (`review_after` passed) and propose refresh PRs
- Watch the Drive folder for new files and trigger ingest
- Surface "you've mentioned X 3 times without an entry — should I create one?"
- Surface contradictions across entries as they accumulate

Requires:
- A long-running process (not just slash-command invocations)
- Scheduling / triggering primitives
- Permission to take some actions autonomously (move files, regen indexes) but not others (delete entries, push commits) — needs a clear authority model

Open question: hosted (Claude Agent SDK?) vs local background process vs Docker container? V1 model is install-on-host, but a V2 agent might warrant a different architecture.

### 2. Multi-wiki per project

V1: one wiki per project, at `<project>/llm-wiki/wiki/`. The user-facing `topic` is fixed as `"llm-wiki"`.

V2: support multiple named topics under one project. Useful for:
- A development project that ALSO tracks research (e.g., a game project that has both `dnd-engine-decisions` and `dnd-mechanics-research`)
- An ecosystem repo with multiple sub-projects each wanting their own wiki

Requires:
- `wiki-config.json` to record a list of topics
- `/new-wiki --add-topic <name>` mode
- Scripts to take `--topic` and respect which one (already supported, just not exposed in v1 UX)

### 3. Antigravity adapter

V1: claude-code + cursor.
V2: antigravity (the .GEMINI / .agent rules system that workflows-core itself uses).

The cursor adapter approach (convert SKILL.md → .mdc) is the pattern. Antigravity would generate `.GEMINI/rules/*.mdc` (or whatever the right format is) from the same source.

### 4. Public release polish

When the repo goes wide:
- A demo video / GIF showing the one-command install + first /wrap-up cycle
- A canonical "Getting started" doc at the README level (not just per-project)
- CI that runs `install-wiki.ps1` on a fresh Windows + macOS + Linux runner against a test project — catches platform regressions
- Issue templates that lead with "what did you run, what happened, what did you expect"

### 5. User-override layering for seed content

V1 ships `llm-wiki/how-to/` and `llm-wiki/best-practices/` as framework-managed folders. On every refresh, they get re-copied from the bootstrap source — so any user edits in place are lost.

The v1 workaround: put project-specific overrides at `llm-wiki/wiki/how-to/<name>.md` or `llm-wiki/wiki/best-practices/<name>.md`. That folder is user content (not framework-managed) and survives refreshes. `_FRAMEWORK_MANAGED.md` marker files in each seed folder make this explicit.

V2 should make the override mechanism first-class:
- Framework looks for `wiki/how-to/<name>.md` first, falls back to `how-to/<name>.md`
- Same for best-practices
- On refresh, framework checks for an override before overwriting (and warns the user if the shipped version has changed in ways the override might want)
- A `wiki-doctor` command that lists divergence (shipped vs override) and offers to merge specific changes

This becomes important once a few real users have customized their installs and want refresh updates without losing their edits.

### 6. agentmemory alternatives

V1: agentmemory (rohitg00) — chosen because local, no subscription, MCP-native.
V2: support pluggable memory backends:
- mem0 (cloud-hosted, has free tier)
- Letta (formerly MemGPT)
- Bring-your-own (a thin MCP shim spec)

Add a `--memory-backend` flag to `/new-wiki` for development projects.

### 6. Skill marketplace integration

agentskills.io (and similar registries) are emerging. V2: register the LLM-wiki skills there so users can `npx skills install llm-wiki/<skill-name>` for individual pieces.

This is the "ecosystem" plays — make the framework's components consumable independently.

### 7. Tag agentmemory sessions by actor

V1: all memories written by the agentmemory MCP server land in the same per-project store (`<project>/llm-wiki/raw/sessions/agentmemory.json`) with no actor metadata. Fine when one human + one agent are the only writers.

V2 should add an actor tag (user id, agent persona, subagent role) on every write so multi-user or multi-agent setups can:
- Filter "what did persona X remember"
- Detect when two actors disagree on the same fact
- Audit who wrote what during incident review

Requires either upstream agentmemory support for actor tags or a thin wrapper that prepends `actor: <id>` to each memory body before forwarding. Probably the wrapper path — upstream changes are slower.

## Smaller follow-ups

- **`/install-sync` command** — designed but not implemented. Diff bootstrap against installed copy, prompt to refresh.
- **Per-skill versioning** — wiki-config.json has a single `install_version`. Per-skill versions would let partial refreshes target specific skills.
- **Cross-OS path handling** — `new-wiki.py` has Windows-flavored paths in some print statements. Test on Mac/Linux for cosmetic issues.
- **agentmemory MCP package** verified on npm but not exercised end-to-end on a fresh machine. First real test will validate.
- **`/wiki-update` and `/wiki-promote` end-to-end with backlinks** — staging+promote tested with 0-backlink case; tested-but-not-stressed with the suggested_backlinks application path.
- **Drive OAuth on non-graphical sessions** — flow assumes the user has a browser; WSL / headless containers need a different path.

## Should this repo (llm-wiki-bootstrap) have its own wiki for tracking?

Per the 2026-05-14 design discussion: probably not yet. The `agentic-design` wiki (in workflows-core) already tracks the research that informs this framework. A separate `llm-wiki-bootstrap` wiki would mostly duplicate or fragment that. Reconsider after V1 has been in use for a few months — at that point there may be enough framework-specific operational knowledge to warrant a dedicated wiki, separate from the research wiki.

## Should the framework eventually be its own product?

Open. The current model is "shared as a public GitHub repo, install via git clone + install-wiki.ps1". That's a working distribution path. If usage takes off, options include:
- A first-class npm package: `npx create-llm-wiki-project`
- A pipx-installable Python package: `pipx install llm-wiki && llm-wiki new <project>`
- A web installer: `iwr -useb https://llm-wiki.dadlabs.io/install | iex`

All are V2+. V1 ships as-is.
