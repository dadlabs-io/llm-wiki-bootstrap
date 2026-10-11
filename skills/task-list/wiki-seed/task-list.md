---
title: "task-list — skill"
type: how-to
artifact: skill
name: task-list
installed_by: install-wiki
date: 2026-09-15
---

# task-list — skill

The project's task list, kept where every session, every bot and you can see it: an **At a glance** block at the top of the session's `task.md` in the wiki. There is one table per owner (you, each persona or bot working in the project, and Unassigned), with one short row per task: a number, the task (at most 70 characters), a status, and the next step or what it is waiting on (at most 60). A task's longer details (the why, the steps, the evidence) are kept apart, in a Task details section right under the tables, so the list reads as a quick checklist. Last comes a **Backlog** table for tasks set aside; it has an Owner column, so a task keeps its owner while it waits there, and goes back to that owner's table when you bring it back. The list is plain Markdown, and a small script makes every edit, so it works in any harness and you can read it in any editor.

**Trigger:** */task-list*, or plain speech: "add a task …", "put X on the list", "delete task 4", "mark 2 done", "task 3 is waiting on Y", "move 5 to agent-builder", "move 5 to the backlog", "take 5 off the backlog", "what's on my list", "what's left", "show my tasks with details", "details on 25". This is not Claude Code's own `/tasks`, which shows background jobs.

**Input / Output:** what you said, and the list in `wiki/sessions/<persona>/task.md` (the persona comes from the project's `.claude/wiki-config.json`, default `main`). It shows the list (the short rows; with details when you ask, or one task's details by its number), or changes one row and replies with the one line the script printed for it (number, task, status, owner). The block and the Task details section sit above the file's `## NOW` and `## QUEUE`. The script refuses a row longer than the limits, so the agent puts the rest in the task's details; a row written before the limits stays as it is until it is next edited.

**Two rules:**
- **A number is never reused.** The script picks each new number above every number already in the file, including QUEUE's, and records the next free one in a comment in the block.
- **A task leaves the list only on your word.** "Delete task 4" removes it. A finished task is marked `done`, and the session asks whether to remove it. It never removes a task on its own, and the script refuses to unless the session passes a confirmation flag.

**Naming a task:** by its number, or by its words ("I've finished the build-scripts cleanup"). When the words match exactly one task, the session uses that task without asking you to confirm it; when two could match, or none does, it asks which one you mean. It never guesses a number.

**Moving a task** to another owner changes only its owner: its status and next step stay as they were unless you say otherwise.

Statuses are `to do`, `doing`, `waiting`, `parked` and `done`. "Waiting" keeps the task with its owner; the last column says what it is waiting on.

**Works with:** [`wrap-up`](./wrap-up.md) keeps the list current at the end of a session: it marks the session's finished tasks done (and asks before removing any), adds the tasks it took on or left for you, and moves statuses that changed. The SessionStart hook points each new session at the same `task.md`, so the list is in view from the first reply.

**Task cards (since 2026-10-10; agent-builder-bootstrap and llm-wiki-bootstrap so far):** a project can keep its tasks as a stack of cards instead: one file per task in `wiki/tasks/`, each with its fields at the top and its details, steps and a dated log below, plus `tasks/ORDER.md`, which lists the current tasks in the order you'll work on them. NOW is the first one there not yet done, and a session starts by reading only that card, not the whole list. The same requests work on cards. You can also reorder ("put 5 first", "do 5 after 3"), add a dated note to a card ("note on 12: …"), tag tasks and show one tag's tasks, and give a task a priority. A check covers six rules (each current task listed in ORDER.md exactly once, numbers unique and never reused, required fields set), and the script refuses any change that would break one. A project switches over when you say so: a dry run shows each card it would write, then the move carries each task's row, details and notes into its card whole, and keeps the rest of the old `task.md` in an archive. Every other project stays on `task.md`.

**Moving a project onto cards** (what the first two moves taught; say "move this project onto cards"):
1. Add any task that is still only in the conversation, and commit `task.md`.
2. The session runs a dry run and shows you every line: how many cards (compare with your rows), each card's list and status, how many lines of details and notes each carries (a long note showing 0 lines means it was missed), the proposed order, and what goes to the archive. Nothing is written yet.
3. Choose which task comes first. The proposed order follows the owner tables, so your own table comes first; the rest can be reordered after the move.
4. The move, then the six-rule check, then a commit of only this notebook's `tasks/` folder and `task.md`.
5. The project's `CLAUDE.md` Resuming lines are changed to read the order file and the NOW card instead of `task.md`. The startup hook switches by itself; an existing `CLAUDE.md` does not.
6. Anything else that still describes `task.md` is swept: the project's saved memories, its `CLAUDE.md`, and any unsent skill suggestion about `task.md`'s layout.
7. Each persona's list moves on its own: a second persona's `task.md` stays until it is moved too.

**When it skips itself:** it needs a wiki project. Outside one, the script says no wiki was found and nothing is written. In a project whose `task.md` has no At a glance block yet, the first task you add creates it; your existing NOW and QUEUE stay as they are.
