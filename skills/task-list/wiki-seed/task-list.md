---
title: "task-list — skill"
type: how-to
artifact: skill
name: task-list
installed_by: install-wiki
date: 2026-09-15
---

# task-list — skill

The project's task list, kept in the wiki where every session, every bot and you can see it, as a stack of **task cards**: one file per task in `wiki/tasks/`, each with its fields at the top (owner, status, the next step or what it waits on, priority, tags) and below them its details, an optional checklist of steps, and a dated log. Beside them, `tasks/ORDER.md` lists the current tasks in the order you'll work on them. **NOW** is the first one there not yet done, and a session starts by reading only that card, not the whole list. Tasks set aside go to the **backlog**, keeping their owner, and come back to the order when you bring them back. The cards are plain Markdown, and a small script makes every change to their fields and to the order, so it works in any harness and you can read it in any editor. (agent-builder's design, 2026-10-10; every project moved onto cards by 2026-10-12, when the older `task.md` list was retired.)

**Trigger:** */task-list*, or plain speech: "add a task …", "put X on the list", "delete task 4", "mark 2 done", "task 3 is waiting on Y", "move 5 to agent-builder", "move 5 to the backlog", "take 5 off the backlog", "put 5 first", "do 5 after 3", "note on 12: …", "what's NOW", "what's on my list", "what's left", "show my tasks with details", "details on 25". This is not Claude Code's own `/tasks`, which shows background jobs.

**Input / Output:** what you said, and the cards in the project wiki's `tasks/` folder. It shows the list (NOW, then the current tasks in order, then the backlog by owner; one card in full when you name it), or makes one change and replies with the one line the script printed for it. A task's title is at most 70 characters and its next step at most 60; anything longer goes in the card's details.

**Two rules:**
- **A number is never reused.** The script picks each new number from a counter in `ORDER.md`. A removed task's card stays, marked done, so its number stays taken.
- **A task leaves the list only on your word.** "Delete task 4" removes it. So does "task 4 is done": your saying so is the word, so the session marks it done and removes it without asking. A task the session finished itself is marked done and stays in the order, above NOW; the session tells you what was done and asks whether to remove it, so you can check nothing was missed. It never removes a task on its own, and the script refuses to unless the session passes a confirmation flag.

**Naming a task:** by its number, or by its words ("I've finished the build-scripts cleanup"). When the words match exactly one task, the session uses that task without asking you to confirm it; when two could match, or none does, it asks which one you mean. It never guesses a number.

**Moving a task** to another owner changes only its owner: its status and next step stay as they were unless you say otherwise. **Reordering** ("put 5 first", "do 5 after 3") changes only `ORDER.md`. While a session works a task, it moves that card to the top and marks it doing, so NOW always shows the real work; a task left waiting goes below it.

**A task's details are added to, never overwritten by accident.** "Add to 25's details: …" appends a paragraph and keeps what is there. Writing new details over a card that already has some is refused, with nothing changed, unless you ask for them to be replaced ("replace 25's details with …"). A progress note goes in the card's dated log ("note on 12: …"). (Since 2026-10-12: a progress note once replaced a card's source and steps.)

Statuses are `ready`, `doing`, `waiting` and `done` ("to do" reads as ready; "park 5" moves it to the backlog). "Waiting" keeps the task with its owner and names what it waits on.

**Editing a card by hand** is fine for its body: the details, ticking a step, adding one. The fields and `ORDER.md` go through the script. A check covers six rules (every current task in `ORDER.md` exactly once and nothing else, every listed number has a card, numbers unique and matching their file names, required fields set with their fixed words, a waiting task names what it waits on, the counter above every number); the script refuses any change that would break one, and after a hand edit the session runs the check.

**Works with:** [`wrap-up`](./wrap-up.md) keeps the cards current at the end of a session: it marks the session's finished tasks done (and asks before removing any it finished itself), adds the tasks it took on or left for you, and moves statuses that changed. The SessionStart hook points each new session at `ORDER.md` and the NOW card, so the work is in view from the first reply.

**When it skips itself:** it needs a wiki project. Outside one, the script says no wiki was found and nothing is written. In a project with no `tasks/ORDER.md` yet, the first task you add starts the list. A project that still keeps an old "At a glance" list in a `task.md` is refused, with nothing written, so that list is never left behind unseen; its tasks are moved onto cards first.
