# /task-list on cards — the task stack

Read this when the project is on cards (its wiki has `tasks/ORDER.md`, and every `wiki-tasks.py` call ends with
`tasks_dir=<path>` instead of `task_file=`), and before moving a project onto cards. The same script and the same two rules apply; this file says only what
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
| "task 3 is done" | `done 3 --next "<what happened>"`, `log 3 "<what happened>"`, then `remove 3 --confirmed` (their word) |
| (you finished 3) | `done 3 --next "<what happened>"` and `log 3 "<what happened>"`: it stays in ORDER.md, above NOW, until the user says yes to removing it; ask |
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

Only on the user's word. Each live task's row, Task details and QUEUE note move whole into its card. Everything else in
task.md (NOW's history, closed notes) goes unchanged to `tasks/archive/task-md-<YYYY-MM>.md`, and task.md becomes a
pointer. The checklist (from agent-builder's pilot and this notebook's move, 2026-10-10):

1. **Add any task still only in the conversation, then commit task.md** by path. A task not yet written is the one
   lost in a move.
2. **`migrate --dry-run`, and show the user every line:** the card count (compare it with the At a glance rows), each
   card's list and status, the details and QUEUE-note line counts (a live task with a long QUEUE note and 0 lines
   means the note was missed), the ORDER.md it proposes, the archive's lines kept. Nothing is written.
3. **Choose NOW with the user.** The proposed ORDER.md takes the current tasks by owner table in file order, so the
   user's own table comes first. `--now <N>` puts N first; after the run, fix the rest with `order <N> --after <M>`.
4. **`migrate --now <N>`, then `check`, then commit `wiki/tasks/` and the task.md pointer** with a pathspec
   (`git commit -- <paths>`): another session's staged file must not ride along.
5. **Change the project's CLAUDE.md Resuming lines.** The startup hook switches by itself, but an existing project's
   CLAUDE.md still names task.md: it should read handoff.md, then ORDER.md and the NOW card, and no other card.
6. **Sweep what still describes task.md:** the project's auto-memory (`~/.claude/projects/<project>/memory/`), its
   CLAUDE.md, and any skill suggestion in its box about task.md's layout that the cards replace.
7. A persona's list moves on its own: a second persona's `sessions/<persona>/task.md` stays until it is migrated too
   (`--persona <name>`).
