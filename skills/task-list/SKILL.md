---
name: task-list
description: "Keeps the project's task list, a stack of task cards in the wiki: one card per task in wiki/tasks/ (its fields: owner, status ready / doing / waiting / done, the next step or what it waits on, priority, tags; then its details, an optional Steps checklist and a dated Log), and tasks/ORDER.md, the current tasks in working order, where NOW is the first card not done. A set-aside task goes to the backlog and keeps its owner; a number is never reused. Shows the list (NOW, the order, the backlog; one card in full on request), adds a task, changes a task's status, owner or next step, reorders ('put 5 first', 'do 5 after 3'), adds a dated note to a card ('note on 12: …'), moves one to the backlog and back, marks one done, and removes one only when the user says so. Use when the user types /task-list, or says 'add a task', 'new task', 'put X on the list', 'delete task 4', 'remove task 4', 'mark 2 done', 'task 3 is done', 'task 3 is waiting on Y', 'move task 5 to <owner>', 'move 5 to the backlog', 'take 5 off the backlog', 'put 5 first', 'note on 12: …', 'what's NOW', 'what's on my list', 'show my tasks', 'what's left', 'show my tasks with details', 'details on 25', 'what's waiting', 'what's waiting on me'. Not Claude Code's /tasks (background jobs), and not a session's own scratch to-do list."
last_reviewed: 2026-10-12
review_after: 2027-01-10
reviewed_for_model: claude-opus-5-5
---

# /task-list — the project's task stack

The list is a folder of cards in the wiki, plain Markdown, so the user, every session and every bot can read it
(agent-builder's design, agreed with Mark 2026-10-10):

- **A card per task:** `<wiki>/tasks/<id>-<slug>.md`. YAML fields on top (`id`, `title`, `owner`, `list`, `status`,
  `next`, `waiting_on`, `priority`, `tags`, `created`, `updated`, `links`), then the body: the details, an optional
  `**Steps**` checklist (`- [ ] A2. Short title (details)`), and a dated `**Log**`. The slug is a label: never rename
  a card, and find it by its number.
- **`tasks/ORDER.md`:** `<!-- next-id: N -->`, then one `- <id> <title>` line per current task, in working order.
- **NOW** is the first card in ORDER.md whose status is not done. A done card above it is finished and waiting for
  the user's word: name it and ask whether to remove it.
- `list` is `current` (in ORDER.md), `backlog` (set aside, keeps its owner) or `done` (the user said to remove it;
  the card stays, so its number is never reused). `status` is `ready`, `doing`, `waiting` or `done` ("to do" reads
  as ready; "parked" moves the task to the backlog). `Backlog` is never an owner name; the script refuses it.

**Fields and ORDER.md change only through the script**: it keeps the numbering and refuses any write that would
break one of the six rules (exit 2, the rule named). The body may be edited by hand (the details, ticking a step,
adding one); after a hand edit run `check`, and fix what it lists (exit 1) until it passes (exit 3 means it found no cards to check).

```bash
uv run --project {{WIKI_SCRIPTS_DIR}} python {{WIKI_SCRIPTS_DIR}}/wiki-tasks.py show [<N>] [--details] [--tag <tag>] [--waiting [<who>]]
uv run --project {{WIKI_SCRIPTS_DIR}} python {{WIKI_SCRIPTS_DIR}}/wiki-tasks.py add "<short task>" --owner <owner> [--status <s>] [--next "<short>"] [--details "<the rest>"] [--backlog]
uv run --project {{WIKI_SCRIPTS_DIR}} python {{WIKI_SCRIPTS_DIR}}/wiki-tasks.py set <N> [--status <s>] [--next "<short>"] [--owner <owner>] [--task "<short>"] [--append-details "<more>"]
uv run --project {{WIKI_SCRIPTS_DIR}} python {{WIKI_SCRIPTS_DIR}}/wiki-tasks.py done <N> [--next "<short>"] [--append-details "<more>"]
uv run --project {{WIKI_SCRIPTS_DIR}} python {{WIKI_SCRIPTS_DIR}}/wiki-tasks.py order <N> --top|--bottom|--before <M>|--after <M>
uv run --project {{WIKI_SCRIPTS_DIR}} python {{WIKI_SCRIPTS_DIR}}/wiki-tasks.py log <N> "<what happened>"
uv run --project {{WIKI_SCRIPTS_DIR}} python {{WIKI_SCRIPTS_DIR}}/wiki-tasks.py backlog <N>
uv run --project {{WIKI_SCRIPTS_DIR}} python {{WIKI_SCRIPTS_DIR}}/wiki-tasks.py unbacklog <N> [--owner <owner>]
uv run --project {{WIKI_SCRIPTS_DIR}} python {{WIKI_SCRIPTS_DIR}}/wiki-tasks.py remove <N> --confirmed
uv run --project {{WIKI_SCRIPTS_DIR}} python {{WIKI_SCRIPTS_DIR}}/wiki-tasks.py check
```

`add` and `set` also take `--priority P1|P2|P3`, `--tags "a,b"` (replaces the tags), `--waiting-on "<text>"` and
`--link <target>`. Run it from the project folder: it finds the wiki from `.claude/wiki-config.json`, walking up
from the working directory; `--cwd <dir>` resolves from elsewhere. Every call ends with `tasks_dir=<path>`. The
first `add` in a project with no `tasks/ORDER.md` starts the list.

**Short fields, details apart** (Mark, 2026-10-04): a title is at most 70 characters and `next` at most 60; a
longer one is refused (exit 2). Everything else (the why, the steps, file names, the evidence) goes in `--details`,
the card's body. `--append-details` adds a paragraph and keeps what is there. `--details` on a card that already has
details is refused (exit 2, nothing written; task #101, a progress note once wiped a card's steps); replace them
only when the user asks, with `--details "<new>" --replace-details`. Progress goes in the Log: `log <N> "<note>"`.

`show` prints NOW, then the ORDER.md tasks in order, then the backlog by owner; `show <N>` prints the card in full;
`show --waiting` lists every waiting card (current and backlog) with what it waits on, and `show --waiting <who>` only
those whose `waiting_on` names them;
`show --details` adds every current card's body.

Exit 2 means bad input, an unknown number, no wiki found, or `remove` without `--confirmed`; exit 3 means `show`
found no tasks yet. Read the message and fix the call, don't retry blindly and don't fall back to editing fields
by hand. One exit 2 is not a bad call: a project with no `tasks/ORDER.md` whose `sessions/<persona>/task.md` still
holds an old `## At a glance` list is refused, nothing written, so that list is never left behind. Tell the user,
show them its tasks, and on their word add each one as a card (its details with it) before the new task; that
old file is theirs to delete.

## The two rules

1. **A number is never reused.** The script picks it. Never renumber, and never re-add a removed task under
   its old number.
2. **A task leaves the list only on the user's word.** (Mark, 2026-10-11: "if I say it's done then it's done
   so we can remove it. If you say it's done, I need to be informed so I can decide if it is actually done.")
   - When the user says to delete or remove task N, that is their word: run `remove <N> --confirmed`.
   - When the user says task N is done, that is their word too: `done <N> --next "<what happened>"`,
     `log <N> "<what happened>"`, then `remove <N> --confirmed`, without asking.
   - When you finished a task yourself, run `done <N> --next "<what happened>"` and `log <N> "<what happened>"`:
     it stays in ORDER.md, above NOW. Tell the user what was done and ask: "Task N is done. Remove it from the
     list?" They may find something missed. Remove it only on a yes.
   - Never pass `--confirmed` on your own judgement.

"Waiting" is a status: the task keeps its owner, and `waiting_on` says what it waits on (a wait with nothing named
is refused).

## From what the user said

| The user says | Run |
|---|---|
| "/task-list", "what's on my list", "show my tasks", "what's left", "what's NOW" | `show`, then give them the list as printed (its first line is NOW) |
| "show my tasks with details", "details on 25", "what's behind task 25" | `show --details`, or `show 25` for one card |
| "what's waiting", "what's waiting on me", "what's waiting on agent-builder" | `show --waiting`, or `show --waiting <name>` |
| "add a task …", "put X on the list", "remind me to …" | `add "<X>"`, owner as below |
| "task 3 is done", "mark 3 done", "I finished …" | `done 3 --next "<what happened>"`, `log 3 "<what happened>"`, then `remove 3 --confirmed` (their word) |
| "delete task 4", "remove task 4", "drop 4" | `remove 4 --confirmed`: `list: done`, out of ORDER.md; the card stays |
| "task 3 is waiting on Y" | `set 3 --status waiting --next "Y"`: Y becomes `waiting_on` |
| "I'm on 2 now", "do 5 next", "put 5 first", "5 after 3" | `set 2 --status doing` + `order 2 --top`; `order 5 --top`; `order 5 --after 3` (`--before`, `--bottom`) |
| "move 5 to agent-builder", "give 5 to me" | `set 5 --owner <owner>` |
| "park 5", "move 5 to the backlog" | `backlog 5` |
| "take 5 off the backlog", "bring 5 back" | `unbacklog 5` |
| "add X to the backlog" | `add "<X>" --backlog`, owner as below |
| "make 5 a P1", "tag 5 pilot", "show me the pilot items" | `set 5 --priority P1`, `set 5 --tags "pilot"`, `show --tag pilot` |
| "note on 12: …", progress on 12 | `log 12 "<the note>"` |
| "add to 25's details: …" | `set 25 --append-details "<…>"` |
| "replace 25's details with …" | `set 25 --details "<…>" --replace-details` |

- **Which task:** when the user names a task by its words, not its number, run `show`, find it, and use its
  number. If two tasks could match, or none does, ask. Never guess a number.
- **Owner of a new task:** the user's own name when it is theirs to do ("remind me to", "I need to"); this
  persona's name when this session will do it; the bot they name; otherwise Unassigned.
- Write the task as a short line a stranger could act on, and the next step as a few words. Anything longer is
  details: pass it as `--details` on the same call.
- **While working a task, keep its card current:** starting it, `set <N> --status doing` and `order <N> --top`, so
  NOW is the real work; a task left waiting goes below the one being worked (`order <N> --after <M>`).

After a change, reply with the one line the script printed. Show the whole list only when asked.

## Don't

- Don't edit a card's fields or ORDER.md by hand, renumber, or rename a card.
- Don't make an owner called Backlog: that loses the task's owner. Use `backlog <N>`.
- Don't remove a task you marked done yourself until the user says yes.
- Don't confuse it with Claude Code's `/tasks` (background jobs) or a session's own to-do checklist. This list
  lives in the wiki and outlives the session.
