# /task-list on cards — the task stack

Read this when the project is on cards: its wiki has `tasks/ORDER.md`, and every `wiki-tasks.py` call ends with
`tasks_dir=<path>` instead of `task_file=`. The same script and the same two rules apply; this file says only what
is different. (agent-builder's design, 2026-10-10, agreed with Mark; agent-builder-bootstrap is the first project on
cards.)

## The layout

- **A card per task:** `wiki/tasks/<id>-<slug>.md`. YAML fields on top (`id`, `title`, `owner`, `list`, `status`,
  `next`, `waiting_on`, `priority`, `tags`, `created`, `updated`, `links`), then the body: the details, an optional
  `**Steps**` checklist (`- [ ] A2. Short title (details)`), and a dated `**Log**`. The slug is a label: never rename
  a card, and look it up by its number.
- **`tasks/ORDER.md`:** `<!-- next-id: N -->`, then one `- <id> <title>` line per current task, in working order.
- **NOW** is the first card in ORDER.md whose status is not done. A done card above it is finished and waiting for
  the user's word: name it and ask whether to remove it.
- `list` is `current` (in ORDER.md), `backlog` (set aside, keeps its owner) or `done` (the user said to remove it;
  the card stays, so its number is never reused). `status` is `ready`, `doing`, `waiting` or `done`. There is no
  `parked`: that is the backlog.

## From what the user said

Everything in SKILL.md's table works the same, with these differences:

| The user says | Run |
|---|---|
| "park 5" | `backlog 5` (`set 5 --status parked` does the same) |
| "task 3 is waiting on Y" | `set 3 --status waiting --next "Y"`: Y becomes `waiting_on`. A wait with nothing named is refused |
| "task 3 is done" | `done 3 --next "<what happened>"`: it stays in ORDER.md until the user says to remove it; then ask |
| "remove task 4" | `remove 4 --confirmed`: `list: done`, out of ORDER.md; the card stays |
| "do 5 next", "put 5 first", "5 after 3" | `order 5 --top`, `order 5 --after 3` (`--before`, `--bottom`) |
| "make 5 a P1", "tag 5 pilot" | `set 5 --priority P1`, `set 5 --tags "pilot"` (replaces the tags) |
| "show me the pilot items" | `show --tag pilot` |
| "note on 12: …" | `log 12 "<the note>"` (a dated line in the card's Log) |
| "what's NOW", "what am I on" | `show`: its first line is NOW |

`show` prints NOW, then the ORDER.md tasks in order, then the backlog by owner; `show <N>` prints the card in full.

## Editing a card

- **Fields and ORDER.md only through the script.** It refuses any write that would break one of the six rules
  (exit 2, the rule named).
- **The body may be edited by hand**: the details, ticking a step (`- [ ]` → `- [x]`), adding a step. After a hand
  edit, run `wiki-tasks.py check`. Exit 1 lists each rule broken; fix it, then check again.
- The six rules: every current card is in ORDER.md once and nothing else is; every id in ORDER.md has a card; ids
  are unique and match the file name; the required fields are set, with list and status in their fixed words;
  `waiting_on` is filled exactly when the status is waiting; next-id is above every id.

## Moving a project onto cards

Only on the user's word. `migrate --dry-run` lists each card it would write (with its details and its numbered QUEUE
note), the ORDER.md it would write and the archive. Show the user, then run `migrate --now <N>`, where N is the
task to put first. Each live task's row, Task details and QUEUE note move whole into its card. Everything else in
task.md (NOW's history, closed notes) goes unchanged to `tasks/archive/task-md-<YYYY-MM>.md`, and task.md becomes a
pointer. Afterwards, the startup hook lists ORDER.md and the NOW card instead of task.md.
