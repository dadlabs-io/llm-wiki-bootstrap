---
title: "Migrating from Claude Code to Cursor — llm-wiki"
type: how-to
pack: llm-wiki
installed_by: install-wiki
date: 2026-10-24
---

# Migrating from Claude Code to Cursor

This page is for the person moving their work from Claude Code to Cursor, and for the Cursor agent that
opens one of their projects. It explains where everything lives today and what carries over by itself. It also
lists what has to be set up by hand, and what Cursor cannot do. To start, the person tells Cursor:
"read `<toolset>/how-to/llm-wiki/migrating-from-claude-to-cursor.md` in full and check this machine against it".

Nothing here deletes or moves anything in `~/.claude/`. Claude Code keeps working, so both tools can be
used side by side and the move can be undone.

What Cursor loads was checked against Cursor's docs (2026-10-24): skills, subagents, hooks, rules, MCP and
third-party hooks. Every line marked **check** is unproven; settle it on the machine (see
[Checking it works](#checking-it-works)) before relying on it.

## Where everything lives today

| What | Where | What it does |
|---|---|---|
| Skills | `~/.claude/skills/<name>/SKILL.md` (with reference files beside it) | Every wiki command (`/wrap-up`, `/wiki-update`, `/task-list`, …) and any other installed pack's skills |
| Agents | `~/.claude/agents/<name>.md` (+ `<name>-config.json`, `<name>-reading-list.json`) | Subagents a skill hands work to: `wiki-ingester` (batch ingest), `wiki-checker` (checks an entry against its raw) |
| Workflows | `~/.claude/workflows/<name>/WORKFLOW.md` | Multi-step procedures the session walks by hand, step by step |
| Scripts | `~/.claude/wiki-scripts/` with its own uv environment | The Python behind the skills, always run as `uv run --project ~/.claude/wiki-scripts python ~/.claude/wiki-scripts/<script>` |
| Hooks | `~/.claude/settings.json` → `hooks`; a project's `.claude/settings.json` | Startup resume list (`wiki-session-start.py`), read guard (`read-guard.py`), ingest-worker guard (`agent-guard.py`), plus any others the user added |
| Global rules | `~/.claude/CLAUDE.md` | The user's standing instructions for every project |
| Project rules | `<project>/CLAUDE.md` | The project's instructions, including its **Resuming** section (what to read at startup) |
| Project config | `<project>/.claude/wiki-config.json` | Which notebook is this project's wiki; the scripts read it |
| Machine config | `~/.claude/wiki-config.json` | Where the bootstrap clone lives, the notebook registry, the search mode |
| Notebooks | the notebooks vault (named by `registry` → `linked-notebooks.json`), or `<project>/llm-wiki/` | The wikis themselves: `wiki/`, `raw/`, `_inbox/`, `wiki/sessions/`, `wiki/tasks/` |
| Usage docs | the global toolset notebook, `how-to/<pack>/` | One page per skill and agent, this page included |
| Claude's own memory | `~/.claude/projects/<project-path-slug>/memory/` (`MEMORY.md` + one file per fact) | Lessons and preferences Claude Code saved per project |
| MCP servers | `~/.claude/settings.json` → `mcpServers`, or a project's `.mcp.json` | Extra tools (browsers, docs servers, …) |
| Claude-only extras | plugins, mods, the status line, channels (e.g. a Discord bot) | Live in `~/.claude/` and in `enabledPlugins` / `env` in `settings.json` |

The **wiki is plain files and the scripts are plain Python**. Neither depends on Claude Code, so both work
unchanged from Cursor. What needs attention is the layer around them: how the agent finds skills, rules,
hooks and memory.

## What carries over by itself

- **Skills.** Cursor loads skills from `~/.claude/skills/` and a project's `.claude/skills/` as well as its own
  folders. Every installed skill shows up under `/` in Agent chat, and the agent can also pick one by its
  description. Nothing to copy.
- **Agents.** Cursor loads subagents from `~/.claude/agents/` and a project's `.claude/agents/`. Its frontmatter
  knows `name`, `description`, `model` (default `inherit`), `readonly` and `is_background`. Claude-only fields
  such as `tools` are ignored, so a subagent gets every tool its parent has.
- **Scripts, qmd search, notebooks, the git pre-commit hook, uv.** They are machine-wide. The skills call
  them through the shell exactly as before.

## What needs setting up

1. **Turn on third-party configs.** In Cursor's settings, under Rules, Skills, Subagents, turn on "Include
   third-party Plugins, Skills, and other configs". This is what lets Cursor read the `~/.claude/` folders and
   hooks.
2. **Global rules.** Cursor does not read `~/.claude/CLAUDE.md`. Paste its content into Cursor's **User Rules**
   (Customize → Rules), or into an always-applied rule. Keep `~/.claude/CLAUDE.md` as the master copy and paste
   again when it changes.
3. **Project rules.** Cursor reads `AGENTS.md` (root and nested). Whether it also reads `CLAUDE.md` is
   **check**. The safe step: add an `AGENTS.md` at the project root whose only line is "Read `CLAUDE.md` in
   full before anything else; it is this project's instructions." That keeps one copy of the rules.
4. **Hooks** (**check**). With step 1 on, Cursor loads hooks from `~/.claude/settings.json`,
   `.claude/settings.json` and `.claude/settings.local.json`. It maps the events (`SessionStart` →
   `sessionStart`, `PreToolUse` → `preToolUse`, `Stop` → `stop`, `SubagentStop` → `subagentStop`) and the
   tool names (`Bash` → `Shell`, `Edit` → `Write`; `Glob` cannot be matched). Four things are unproven:
   - **Loading at all.** One user reported that Cursor never loaded Claude-format hooks while the same hook in
     `.cursor/hooks.json` worked.
   - **The `command` + `args` form.** The installer writes every hook this way; Cursor's own format is one
     command string.
   - **The startup context.** `wiki-session-start.py` hands back its startup checklist as Claude's
     `additionalContext`; Cursor's `sessionStart` takes `additional_context`, and it does not wait for the hook.
   - **The transcript.** The read guard and the "previous session ended without a wrap-up" note read Claude
     Code's transcript (`transcript_path`). Without it they do nothing.

   If the hooks do not run, write `~/.cursor/hooks.json` by hand (Cursor's format). Make the startup hook's
   job a rule instead: the project `CLAUDE.md`'s Resuming section already says "if no hook message is in your
   context, read the files yourself", and Cursor will follow it.
5. **MCP servers.** Cursor reads `~/.cursor/mcp.json` and a project's `.cursor/mcp.json`, not Claude's
   settings. Copy the servers that are wanted (same `mcpServers` shape: `command`, `args`, `env`, or `url`).
   **Never copy an API key** into the file. Use `${env:NAME}` and set the variable outside it.
6. **Claude's memory.** Cursor does not read `~/.claude/projects/*/memory/`. Two ways to carry it:
   - At the start of a session, ask the agent to read that project's `MEMORY.md` and every file it lists.
   - Move the lessons that matter into a project rule (`.cursor/rules/<name>.mdc`, `alwaysApply: true`).

   Lessons learned while working in Cursor go into Cursor's rules or the wiki, so nothing is lost when moving back.

## Reading the skills in Cursor

The skills are written for Claude Code and name its tools. In Cursor, read each name as its equivalent:

| A skill says | In Cursor |
|---|---|
| the `Agent` tool, spawn a subagent, `subagent_type` | the subagent (Task) tool; pick the subagent by name |
| a spawn-time `model` override (e.g. `wiki-ingester-config.json`'s `model_default`) | the subagent's `model` field or the model picker; a run that needs a strong model for long transcripts (the checker) gets one chosen by hand |
| `AskUserQuestion` (selectable options) | ask in chat, with the options as a numbered list and the recommended one marked |
| `Read` with no limit, read every page | read the whole file; still no partial reads |
| the `PowerShell` tool | the terminal; check which shell it runs before pasting PowerShell or Bash syntax |
| `Skill` tool, load the skill first | open `~/.claude/skills/<name>/SKILL.md` and read it in full, or invoke it with `/` |
| `ToolSearch`, deferred tools | not needed: Cursor's tools are always loaded |

## What does not work in Cursor

| Feature | Why | What to do |
|---|---|---|
| Skill test runs (`tests/skills/run_skill_test.py`) | They drive the `claude` command line headless, which bills Claude anyway | Run them from Claude Code when there are credits; build and script-test (`tests/scripts/`) in Cursor |
| `/wrap-up`'s cost line (`wiki-cycle-scope.py session-cost`) | Reads Claude Code's session records | The line says `Cost: not checked`, as designed |
| The task pane / band mod | A Claude Code mod | `/task-list` (or `wiki-tasks.py show`) prints the same list |
| Discord channels (a project bot in a shared channel) | A Claude Code plugin; bots cannot reach a Cursor session | Hand work over through notes in the intake folders, or keep the bot sessions on Claude Code |
| Status line, Claude Code plugins, artifacts | Claude Code features | None needed for the wiki |
| Workflows run by the `Workflow` tool | Claude Code only | A `WORKFLOW.md` walked by hand still works: read it in full and do its steps |

## Things to avoid

- **Don't run the old Cursor installer** (`install-wiki.ps1 -Tool cursor`). It turns every skill into a
  `.cursor/rules/*.mdc` copy. Cursor now reads `~/.claude/skills/` natively, so the copies would duplicate every
  skill and go stale at the next refresh.
- **Don't copy `~/.claude/skills/` into `~/.cursor/skills/`.** Two copies of one skill drift apart. Refreshes
  keep landing in `~/.claude/`, through the usual `install-wiki.ps1` from the bootstrap clone.
- **Don't edit an installed skill to read better in Cursor.** Fix the skill in the bootstrap repo and refresh,
  so Claude Code gets the same fix.
- **Don't let a key ride along.** `settings.json` and MCP configs can hold keys. Anything copied into a
  Cursor config uses `${env:NAME}`.

## Checking it works

The Cursor agent runs these in a wiki project and reports each one as works, doesn't work, or not checked:

1. `/` in Agent chat lists `wrap-up`, `task-list` and `wiki-search`.
2. `uv run --project ~/.claude/wiki-scripts python ~/.claude/wiki-scripts/wiki-tasks.py show` prints the
   project's task list.
3. A new chat in the project: did the startup hook's resume list arrive in context? If not, did the
   `AGENTS.md` → `CLAUDE.md` Resuming fallback get the agent to read the resume files on its own?
4. The read guard: ask the agent to read only the first 10 lines of a long `.md` file with a shell `head`.
   A working guard refuses. A guard that lets it through is not running.
5. `/wiki-search "<a topic the wiki covers>"` returns entries (on a GPU machine the CUDA check runs first).
6. The subagents list shows `wiki-ingester` and `wiki-checker`.
7. `/wrap-up` on a short session: the journal, handoff and task cards update. `Cost: not checked` is
   expected.

Record the results on the project's task list or in a troubleshooting entry, so the next session knows what
already holds.

## Going back

Nothing above changes `~/.claude/`. To return to Claude Code, open the project in it again. The wiki, the
task cards and the handoff are the same files, so it resumes where Cursor left off. Copy back anything worth
keeping from Cursor's rules (a lesson saved only there) into the global `CLAUDE.md` or the project wiki.
