---
title: "task-list — skill"
type: how-to
artifact: skill
name: task-list
installed_by: install-wiki
date: 2026-09-15
---

# task-list — skill

The project's task list, kept where every session, every bot and you can see it: an **At a glance** block at the top of the session's `task.md` in the wiki. There is one table per owner (you, each persona or bot working in the project, and Unassigned), with one row per task: a number, the task in one plain line, a status, and the next step or what it is waiting on. The list is plain Markdown, and a small script makes every edit, so it works in any harness and you can read it in any editor.

**Trigger:** */task-list*, or plain speech: "add a task …", "put X on the list", "delete task 4", "mark 2 done", "task 3 is waiting on Y", "move 5 to agent-builder", "what's on my list", "what's left". This is not Claude Code's own `/tasks`, which shows background jobs.

**Input / Output:** what you said, and the list in `wiki/sessions/<persona>/task.md` (the persona comes from the project's `.claude/wiki-config.json`, default `main`). It shows the list, or changes one row and replies with that row. The block sits above the file's `## NOW` and `## QUEUE`. Longer notes on a task go in QUEUE as a numbered item with the task's number.

**Two rules:**
- **A number is never reused.** The script picks each new number above every number already in the file, including QUEUE's, and records the next free one in a comment in the block.
- **A task leaves the list only on your word.** "Delete task 4" removes it. A finished task is marked `done`, and the session asks whether to remove it. It never removes a task on its own, and the script refuses to unless the session passes a confirmation flag.

Statuses are `to do`, `doing`, `waiting`, `parked` and `done`. "Waiting" keeps the task with its owner; the last column says what it is waiting on.

**Works with:** [`wrap-up`](./wrap-up.md) keeps the list current at the end of a session: it marks the session's finished tasks done (and asks before removing any), adds the tasks it took on or left for you, and moves statuses that changed. The SessionStart hook points each new session at the same `task.md`, so the list is in view from the first reply.

**When it skips itself:** it needs a wiki project. Outside one, the script says no wiki was found and nothing is written. In a project whose `task.md` has no At a glance block yet, the first task you add creates it; your existing NOW and QUEUE stay as they are.
