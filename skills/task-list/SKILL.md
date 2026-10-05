---
name: task-list
description: "Keeps the project's task list, the At a glance block at the top of sessions/<persona>/task.md in the wiki: one table per owner (the user, each persona or bot, Unassigned), then a Backlog table that keeps each set-aside task's owner, one short row per task (a number that is never reused, the task, a status: to do / doing / waiting / parked / done, and what it waits on), with each task's longer details kept apart. Shows the list (the short rows; the details on request), adds a task, changes a task's status, owner or next step, moves one to the backlog and back, marks one done, and removes one only when the user says so. Use when the user types /task-list, or says 'add a task', 'new task', 'put X on the list', 'delete task 4', 'remove task 4', 'mark 2 done', 'task 3 is done', 'task 3 is waiting on Y', 'move task 5 to <owner>', 'move 5 to the backlog', 'take 5 off the backlog', 'what's on my list', 'show my tasks', 'what's left', 'show my tasks with details', 'details on 25'. Not Claude Code's /tasks (background jobs), and not a session's own scratch to-do list."
last_reviewed: 2026-10-01
review_after: 2026-12-30
reviewed_for_model: claude-opus-5-5
---

# /task-list — the project's task list

The list is the **At a glance** block at the top of `<wiki>/sessions/<persona>/task.md`, above `## NOW` and
`## QUEUE`. It is plain Markdown, so the user, every session and every bot can read it:

```
### Mark
| # | Task | Status | Next / waiting on |
|---|---|---|---|
| 14 | Rotate the API keys | to do | yours |
```

One `###` section per owner: the user (by name), each persona or bot working in the project, and Unassigned.
Last comes `### Backlog`, for tasks set aside: its table has an Owner column, so a task keeps its owner while it
waits there. `Backlog` is never an owner name; the script refuses it as `--owner`.

**Every edit goes through the script, never by hand**: it keeps the numbering, the escaping and the layout.

```bash
uv run --project {{WIKI_SCRIPTS_DIR}} python {{WIKI_SCRIPTS_DIR}}/wiki-tasks.py show [<N>] [--details]
uv run --project {{WIKI_SCRIPTS_DIR}} python {{WIKI_SCRIPTS_DIR}}/wiki-tasks.py add "<short task>" --owner <section> [--status <s>] [--next "<short>"] [--details "<the rest>"] [--backlog]
uv run --project {{WIKI_SCRIPTS_DIR}} python {{WIKI_SCRIPTS_DIR}}/wiki-tasks.py set <N> [--status <s>] [--next "<short>"] [--owner <section>] [--task "<short>"] [--details "<the rest>"]
uv run --project {{WIKI_SCRIPTS_DIR}} python {{WIKI_SCRIPTS_DIR}}/wiki-tasks.py done <N> [--next "<short>"] [--details "<the rest>"]
uv run --project {{WIKI_SCRIPTS_DIR}} python {{WIKI_SCRIPTS_DIR}}/wiki-tasks.py backlog <N>
uv run --project {{WIKI_SCRIPTS_DIR}} python {{WIKI_SCRIPTS_DIR}}/wiki-tasks.py unbacklog <N> [--owner <section>]
uv run --project {{WIKI_SCRIPTS_DIR}} python {{WIKI_SCRIPTS_DIR}}/wiki-tasks.py remove <N> --confirmed
```

**Short rows, details apart** (Mark, 2026-10-04): the table is a checklist read at a glance, so a row's Task is at
most 70 characters and its Next at most 60, and the script refuses a longer one (exit 2). Everything else about a
task (the why, the steps, file names, the evidence) goes in `--details`, any length: the script keeps it under
`## Task details`, right below the table, as `### #N: <task>`. `set --details` replaces a task's details
(`--details ""` clears them); `remove` drops them with the task. `show` prints the table only; `show --details`
adds every task's details; `show <N>` prints one task with its details. A row written before the limits stays as
it is until you edit that cell; when you do, shorten it and move the rest into `--details` on the same call.

`backlog <N>` moves a task into the Backlog and records its owner; `unbacklog <N>` sends it back to that owner's
section (`--owner` names another, and is needed for an old backlog row with no owner recorded). On a backlog
row, `set --owner` changes the Owner cell and the task stays in the Backlog; `done` and `remove` work as anywhere.

Run it from the project folder: it finds the wiki and the persona from `.claude/wiki-config.json`,
walking up from the working directory, so a subfolder of the project works too. You do not need to pass a
path. Statuses are `to do`, `doing`, `waiting`, `parked` and `done`. `add`, `set` and `done` create the block
when the file has none. Record the outcome on the same call — `done <N> --next "<what happened>"` — rather
than a `set` after it.

Every command also takes, and rarely needs, `--persona <name>` (another persona's list, only when the user
names it), `--cwd <dir>` (resolve from there instead of the working directory — for a session started outside
the project) and `--file <task.md>` (an explicit file, which skips config resolution). There is an `init
[--owners "A,B,C"]` too, for an empty list with named sections; `add` creates the block on its own, so `init`
is only for setting the sections up front.

Exit 2 means bad input, an unknown number, no wiki found, or `remove` without `--confirmed`; exit 3 means
`show` found no block yet. Read the message and fix the call, don't retry blindly and don't fall back to
editing the file.

## The two rules

1. **A number is never reused.** The script picks it. Never renumber, and never re-add a removed task under
   its old number.
2. **A task leaves the list only on the user's word.**
   - When the user says to delete or remove task N, that is their word: run `remove <N> --confirmed`.
   - When a task is finished (the user says it is done, or you finished it this session), run
     `done <N> --next "<what happened>"`, then ask: "Task N is done. Remove it from the list?" Remove it
     only on a yes.
   - Never pass `--confirmed` on your own judgement.

"Waiting" is a status: the task stays with its owner, and `--next` says what it waits on.

## From what the user said

| The user says | Run |
|---|---|
| "/task-list", "what's on my list", "show my tasks", "what's left" | `show`, then give them the tables as printed |
| "show my tasks with details", "the full list", "details on 25", "what's behind task 25" | `show --details`, or `show 25` for one task |
| "add a task …", "put X on the list", "remind me to …" | `add "<X>"`, owner as below |
| "task 3 is done", "mark 3 done", "I finished …" | `done 3 --next "<what happened>"`, then ask whether to remove it |
| "delete task 4", "remove task 4", "drop 4" | `remove 4 --confirmed` |
| "task 3 is waiting on Y", "park 5", "I'm on 2 now" | `set 3 --status waiting --next "Y"`, `set 5 --status parked`, `set 2 --status doing` |
| "move 5 to agent-builder", "give 5 to me" | `set 5 --owner <section>` |
| "move 5 to the backlog", "backlog 5" | `backlog 5` |
| "take 5 off the backlog", "bring 5 back" | `unbacklog 5` |
| "add X to the backlog" | `add "<X>" --backlog`, owner as below |

- **Which task:** when the user names a task by its words, not its number, run `show`, find it, and use its
  number. If two tasks could match, or none does, ask. Never guess a number.
- **Owner of a new task:** the user's own section when it is theirs to do ("remind me to", "I need to"); this
  persona's section when this session will do it; the section of the bot they name; otherwise Unassigned. The
  user's section is named after them when you know their name. On a new block, pass it once:
  `add … --owner "<name>"`.
- Write the task as a short line a stranger could act on, and the next step as a few words. Anything longer is
  details: pass it as `--details` on the same call, never squeezed into the row.

After a change, reply with the one line the script printed (number, task, status, owner). Show the whole list
only when asked.

## Don't

- Don't edit the block by hand, renumber tasks, or re-sort them.
- Don't make an owner called Backlog (`set --owner Backlog`): that loses the task's owner. Use `backlog <N>`.
- Don't remove a task the user did not tell you to remove, even one marked done.
- Don't confuse it with Claude Code's `/tasks` (background jobs) or a session's own to-do checklist. This list
  lives in the wiki and outlives the session.
