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

**Input / Output:** what you said, and the list in `wiki/sessions/<persona>/task.md` (the persona comes from the project's `.claude/wiki-config.json`, default `main`). It shows the list (the short rows; with details when you ask, or one task's details by its number), or changes one row and replies with that row. The block and the Task details section sit above the file's `## NOW` and `## QUEUE`. The script refuses a row longer than the limits, so the agent puts the rest in the task's details; a row written before the limits stays as it is until it is next edited.

**Two rules:**
- **A number is never reused.** The script picks each new number above every number already in the file, including QUEUE's, and records the next free one in a comment in the block.
- **A task leaves the list only on your word.** "Delete task 4" removes it. A finished task is marked `done`, and the session asks whether to remove it. It never removes a task on its own, and the script refuses to unless the session passes a confirmation flag.

Statuses are `to do`, `doing`, `waiting`, `parked` and `done`. "Waiting" keeps the task with its owner; the last column says what it is waiting on.

**Works with:** [`wrap-up`](./wrap-up.md) keeps the list current at the end of a session: it marks the session's finished tasks done (and asks before removing any), adds the tasks it took on or left for you, and moves statuses that changed. The SessionStart hook points each new session at the same `task.md`, so the list is in view from the first reply.

**When it skips itself:** it needs a wiki project. Outside one, the script says no wiki was found and nothing is written. In a project whose `task.md` has no At a glance block yet, the first task you add creates it; your existing NOW and QUEUE stay as they are.
