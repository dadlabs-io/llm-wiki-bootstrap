#!/usr/bin/env python3
"""
wiki-tasks.py — the project's task list: one card per task in the wiki's tasks/ folder (_task_cards.py).

The task stack (agent-builder's design, its task 173, agreed with Mark 2026-10-10; every notebook moved onto it
by 2026-10-12, when the task.md list and its migration were removed, task #90):

  wiki/tasks/<id>-<slug>.md   one card: YAML fields, then the details, an optional **Steps** checklist and a
                              dated **Log**
  wiki/tasks/ORDER.md         the next free id, then the current cards in working order; NOW is the first
                              card there not done

A number is never reused: a removed card stays, marked `list: done`. A task leaves the list only on the user's
word: `done` marks it and asks "remove? (your call)"; `remove` refuses without --confirmed, which the skill
passes only after the user said to remove it. A task set aside goes to the backlog (`list: backlog`) and keeps
its owner; "Backlog" is never an owner name.

A short overview, details apart (Mark's design, 2026-10-04): a task's title is at most 70 characters and its
next step at most 60, refused when longer (exit 2); the rest goes in --details, the card's body. --details on a
card that already has details is refused (exit 2, nothing written) unless --replace-details is passed (task
#101); --append-details adds a paragraph and keeps the rest; `log` records a dated note.

The first `add` in a project with no tasks/ORDER.md starts its list. A project that still keeps an "At a glance"
list in a sessions/<persona>/task.md is refused (exit 2): that list predates the cards, and writing beside it
would leave it behind unseen (Mark, 2026-10-12: nothing gets lost). Its tasks are moved by hand, or with an
llm-wiki release before task #90, which still had `migrate`.

Usage:
  python wiki-tasks.py [show [<N>] [--details] [--tag <tag>]]
  python wiki-tasks.py add "<task>" [--owner <owner>] [--status ready] [--next "<text>"] [--details "<text>"] [--backlog]
  python wiki-tasks.py set <N> [--task ...] [--status ...] [--next ...] [--owner ...] [--details ... | --append-details ...]
  python wiki-tasks.py done <N> [--next "<text>"] [--details "<text>" | --append-details "<text>"]
  python wiki-tasks.py backlog <N> | unbacklog <N> [--owner <owner>]
  python wiki-tasks.py order <N> --top|--bottom|--before <M>|--after <M>
  python wiki-tasks.py log <N> "<what happened>"
  python wiki-tasks.py remove <N> --confirmed
  python wiki-tasks.py check                         # the six rules; exit 1 on a breach
add/set also take --priority P1|P2|P3, --tags "a,b", --waiting-on "<text>", --link <target>.
Every command takes --cwd <dir> (resolve the wiki from there) and --tasks-dir <dir> (the cards folder itself;
tests). Statuses: ready, doing, waiting, done ("to do" reads as ready; "parked" moves the task to the backlog).

Prints the line it changed and `tasks_dir=<path>`. Exit 0 ok; 1 `check` found a breach; 2 bad input, an
unknown task number, no wiki, a task.md list still in place, or remove without --confirmed; 3 `show` with no
tasks yet.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _task_cards as tc  # noqa: E402
from _wiki_config import today_label  # noqa: E402

DONE_NEXT = "remove? (your call)"
OLD_LIST_HEADING = "## At a glance"  # the task.md list removed in task #90; still recognised, to refuse
TASK_MAX, NEXT_MAX = 70, 60  # characters, the overview's two text cells (Mark, 2026-10-04)

UserError = tc.UserError


def _short(text: str, limit: int, what: str) -> str:
    """The overview keeps each text cell short; the rest belongs in --details."""
    text = " ".join(str(text).split())
    if len(text) > limit:
        raise UserError(f"{what} is {len(text)} characters; the overview keeps it to {limit}. Shorten it and "
                        f"put the rest in --details")
    return text


def _detail_lines(text: str) -> list[str]:
    lines = [ln.rstrip() for ln in str(text).replace("\r\n", "\n").split("\n")]
    while lines and not lines[0].strip():
        lines.pop(0)
    while lines and not lines[-1].strip():
        lines.pop()
    return lines


def new_details(n: int, current: list[str], args) -> list[str] | None:
    """The task's details after set / done, or None when they stay as they are. --details on a task that
    already has details is refused without --replace-details (task #101: agent-builder's progress note
    replaced a card's source and steps, 2026-10-12); --append-details adds a paragraph and keeps the rest."""
    text = getattr(args, "details", None)
    extra = getattr(args, "append_details", None)
    replace = getattr(args, "replace_details", False)
    if text is not None and extra is not None:
        raise UserError("pass --details (with --replace-details) or --append-details, not both")
    if replace and text is None:
        raise UserError("--replace-details goes with --details \"<the new text>\" (\"\" clears them)")
    current = _detail_lines("\n".join(current))
    if text is not None:
        if current and not replace:
            first = " ".join(next(ln for ln in current if ln.strip()).split())
            first = first if len(first) <= 80 else first[:77] + "..."
            raise UserError(f"#{n} already has details ({len(current)} lines, starting \"{first}\"); nothing "
                            f"written. --append-details \"<text>\" adds to them, --details \"<text>\" "
                            f"--replace-details replaces them, `log {n} \"<text>\"` records a dated note")
        return _detail_lines(text)
    if extra is not None:
        add = _detail_lines(extra)
        if not add:
            raise UserError("--append-details is empty")
        return current + ([""] if current else []) + add
    return None


def _owner(name: str) -> str:
    if name.strip().lower() == tc.BACKLOG.lower():
        raise UserError(f"{tc.BACKLOG!r} is not an owner: use `backlog <N>` to set a task aside, keeping its owner")
    return name.strip()


def resolve(args) -> Path:
    """The cards folder: --tasks-dir, else the project wiki's tasks/."""
    if args.tasks_dir:
        return Path(args.tasks_dir)
    cwd = Path(args.cwd) if args.cwd else Path.cwd()
    try:
        from _wiki_config import wiki_dir
        wiki = Path(wiki_dir(cwd=cwd))
    except Exception as e:  # noqa: BLE001 — any resolution failure is the same answer to the user
        raise UserError(f"no wiki found from {cwd} ({e}); run it from the project, or pass --cwd") from e
    if not wiki.is_dir():
        raise UserError(f"no wiki found from {cwd} (looked for {wiki}); run it from the project, or pass --cwd")
    return tc.tasks_dir_of(wiki)


def old_lists(tasks_dir: Path) -> list[Path]:
    """sessions/<persona>/task.md files that still hold a task list (beside a wiki not yet on cards)."""
    sessions = tasks_dir.parent / "sessions"
    out = []
    for p in sorted(sessions.glob("*/task.md")) if sessions.is_dir() else []:
        try:
            if any(ln.strip() == OLD_LIST_HEADING for ln in p.read_text(encoding="utf-8").splitlines()):
                out.append(p)
        except (OSError, UnicodeDecodeError):
            continue
    return out


def card_line(c: "tc.Card") -> str:
    nxt = f"waiting on: {c.get('waiting_on')}" if c.get("status") == "waiting" else c.get("next")
    return f"#{c.id} | {c.get('title')} | {c.get('status')} | {nxt} | owner: {c.get('owner')}, list: {c.get('list')}"


def _apply(c: "tc.Card", stack: "tc.Stack", args) -> None:
    """The field flags of add / set onto one card."""
    if getattr(args, "task", None) is not None and args.cmd == "set":
        c.fields["title"] = _short(args.task, TASK_MAX, "the task")
    if getattr(args, "status", None) is not None:
        word = " ".join(str(args.status).lower().split())
        if word == "parked":  # "park 5" sets a task aside: the backlog
            c.fields["list"], c.fields["status"] = "backlog", "ready"
            if c.id in stack.order:
                stack.order.remove(c.id)
        else:
            c.fields["status"] = tc.card_status(word)
    waiting = c.get("status") == "waiting"
    if getattr(args, "waiting_on", None) is not None:
        c.fields["waiting_on"] = " ".join(args.waiting_on.split())
    if getattr(args, "next", None) is not None:
        text = _short(args.next, NEXT_MAX, "next")
        if waiting and getattr(args, "waiting_on", None) is None and args.status is not None:
            c.fields["waiting_on"] = text  # "set 3 --status waiting --next Y": Y is what it waits on
        else:
            c.fields["next"] = text
    if not waiting:
        c.fields["waiting_on"] = ""
    if getattr(args, "owner", None) is not None and args.cmd == "set":
        c.fields["owner"] = _owner(args.owner)
    if getattr(args, "priority", None) is not None:
        p = args.priority.strip().upper()
        if p and p not in tc.PRIORITIES:
            raise UserError(f"priority must be one of {', '.join(tc.PRIORITIES)} (or \"\" to clear it)")
        c.fields["priority"] = p
    if getattr(args, "tags", None) is not None:
        c.fields["tags"] = [t.strip() for t in args.tags.split(",") if t.strip()]
    if getattr(args, "link", None):
        links = list(c.get("links") or [])
        c.fields["links"] = links + [ln for ln in args.link if ln not in links]
    details = new_details(c.id, c.details_lines(), args)
    if details is not None:
        c.set_details("\n".join(details))


def run_command(args, stack: "tc.Stack") -> int:
    today = today_label()
    where = f"tasks_dir={stack.dir}"
    if not tc.is_on(stack.dir):
        if args.cmd != "add":
            print(f"no tasks yet in {stack.dir}: the first `add` starts the list")
            print(where)
            return 3 if args.cmd == "show" else 2
        stack.next_id = max(stack.next_id, 1)
    if args.cmd == "show":
        if args.n is not None:
            print(stack.find(args.n).path.read_text(encoding="utf-8").rstrip())
        else:
            lines = tc.render(stack, args.tag)
            if args.details:
                cards = stack.by_id()
                for n in stack.order:
                    if n in cards and cards[n].body.strip():
                        lines += ["", f"### #{n}: {cards[n].get('title')}", "", cards[n].body.strip()]
            print("\n".join(lines))
        print(where)
        return 0
    if args.cmd == "check":
        errs = stack.check()
        print("\n".join(errs) if errs else "ok: the six task rules hold")
        print(where)
        return 1 if errs else 0

    before = stack.check()
    if args.cmd == "add":
        if not args.task.strip():
            raise UserError("the task text is empty")
        c = stack.new_card(_short(args.task, TASK_MAX, "the task"), _owner(args.owner), today)
        stack.order.append(c.id)
        _apply(c, stack, args)
        if args.backlog and c.get("list") == "current":
            c.fields["list"] = "backlog"
            stack.order.remove(c.id)
        if c.get("status") == "done" and not c.get("next"):
            c.fields["next"] = DONE_NEXT
        changed = "added " + card_line(c)
    else:
        c = stack.find(args.n)
        if args.cmd == "set":
            _apply(c, stack, args)
            changed = "updated " + card_line(c)
        elif args.cmd == "done":
            details = new_details(c.id, c.details_lines(), args)
            c.fields["status"], c.fields["waiting_on"] = "done", ""
            c.fields["next"] = _short(args.next, NEXT_MAX, "next") if args.next else DONE_NEXT
            if details is not None:
                c.set_details("\n".join(details))
            changed = "updated " + card_line(c)
        elif args.cmd == "backlog":
            if c.get("list") == "backlog":
                raise UserError(f"#{args.n} is already in the backlog (owner: {c.get('owner')})")
            c.fields["list"] = "backlog"
            if c.id in stack.order:
                stack.order.remove(c.id)
            changed = "moved to the backlog " + card_line(c)
        elif args.cmd == "unbacklog":
            if c.get("list") != "backlog":
                raise UserError(f"#{args.n} is not in the backlog (list: {c.get('list')})")
            c.fields["list"] = "current"
            if args.owner:
                c.fields["owner"] = _owner(args.owner)
            stack.order.append(c.id)
            changed = "back from the backlog " + card_line(c)
        elif args.cmd == "remove":
            if not args.confirmed:
                raise UserError(f"#{args.n} is removed only on the user's word: ask them, then pass --confirmed")
            if c.get("list") == "done":
                raise UserError(f"#{args.n} was already removed from the list")
            c.fields["list"] = "done"
            if c.id in stack.order:
                stack.order.remove(c.id)
            changed = f"removed #{c.id} ({c.get('title')}) from the list; its card stays, list: done"
        elif args.cmd == "order":
            stack.place(c.id, top=args.top, bottom=args.bottom, before=args.before, after=args.after)
            changed = f"#{c.id} is now {stack.order.index(c.id) + 1} of {len(stack.order)} in ORDER.md"
        else:  # log
            if not args.text.strip():
                raise UserError("the log text is empty")
            c.add_log(f"{today}: {' '.join(args.text.split())}")
            changed = f"logged on #{c.id}: {today}: {' '.join(args.text.split())}"
    stack.touch(c, today)
    stack.save(before)
    print(changed)
    print(where)
    return 0


def main(argv: list[str]) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--cwd")
    common.add_argument("--tasks-dir", help="the cards folder (default: the wiki's tasks/)")
    fields = argparse.ArgumentParser(add_help=False)
    fields.add_argument("--priority")
    fields.add_argument("--tags", help="comma-separated; replaces the card's tags")
    fields.add_argument("--waiting-on")
    fields.add_argument("--link", action="append", help="a link to keep on the card (repeatable)")
    ap = argparse.ArgumentParser(description="The project's task cards: wiki/tasks/ and tasks/ORDER.md.")
    sub = ap.add_subparsers(dest="cmd")
    p = sub.add_parser("show", parents=[common])
    p.add_argument("n", type=int, nargs="?", help="one task, with its details")
    p.add_argument("--details", action="store_true", help="the overview, then every task's details")
    p.add_argument("--tag", help="just the tasks with this tag")
    sub.add_parser("check", parents=[common])
    p = sub.add_parser("order", parents=[common])
    p.add_argument("n", type=int)
    p.add_argument("--top", action="store_true")
    p.add_argument("--bottom", action="store_true")
    p.add_argument("--before", type=int)
    p.add_argument("--after", type=int)
    p = sub.add_parser("log", parents=[common])
    p.add_argument("n", type=int)
    p.add_argument("text")
    p = sub.add_parser("add", parents=[common, fields])
    p.add_argument("task")
    p.add_argument("--owner", default="Unassigned")
    p.add_argument("--status", default="ready")
    p.add_argument("--next", default="")
    p.add_argument("--details", help="the task's details (any length), the card's body")
    p.add_argument("--backlog", action="store_true", help="file it straight into the backlog, keeping --owner")
    edits = argparse.ArgumentParser(add_help=False)  # set / done: a task's details
    edits.add_argument("--details", help="the task's details, when it has none; replacing existing ones "
                                         "needs --replace-details")
    edits.add_argument("--append-details", help="add a paragraph to the task's details, keeping what is there")
    edits.add_argument("--replace-details", action="store_true",
                       help="with --details: replace the existing details (\"\" clears them)")
    p = sub.add_parser("set", parents=[common, fields, edits])
    p.add_argument("n", type=int)
    p.add_argument("--task")
    p.add_argument("--status")
    p.add_argument("--next")
    p.add_argument("--owner")
    p = sub.add_parser("done", parents=[common, edits])
    p.add_argument("n", type=int)
    p.add_argument("--next")
    p = sub.add_parser("backlog", parents=[common])
    p.add_argument("n", type=int)
    p = sub.add_parser("unbacklog", parents=[common])
    p.add_argument("n", type=int)
    p.add_argument("--owner", help="a new owner as it comes back (default: the one it kept)")
    p = sub.add_parser("remove", parents=[common])
    p.add_argument("n", type=int)
    p.add_argument("--confirmed", action="store_true", help="the user said to remove this task")
    if not argv or argv[0].startswith("-"):
        argv = ["show", *argv]
    args = ap.parse_args(argv)

    try:
        tasks_dir = resolve(args)
        if not tc.is_on(tasks_dir):
            left = old_lists(tasks_dir)
            if left:
                raise UserError(f"{', '.join(str(p) for p in left)} still holds a task list (\"{OLD_LIST_HEADING}\"), "
                                f"from before task cards; nothing written. Move its tasks onto cards first (by hand, "
                                f"or with an llm-wiki release before 2026-10-12, which has `migrate`), so none is lost")
        return run_command(args, tc.Stack(tasks_dir))
    except UserError as e:
        print(f"error: {e}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
