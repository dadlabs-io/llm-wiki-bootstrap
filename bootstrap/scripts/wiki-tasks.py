#!/usr/bin/env python3
"""
wiki-tasks.py — the task list at the top of a wiki project's sessions/<persona>/task.md.

The "At a glance" block (the user's layout, 2026-09-15): one section per owner (the
user, each persona working in the project, Unassigned) and one row per task:

  | # | Task | Status | Next / waiting on |

A number is never reused: the block keeps the next free number in a marker comment,
and a new number is always above every number already in the file. "waiting" is a
status; the task stays with its owner. A task leaves the list only on the user's
word: `done` marks it and asks "remove? (your call)"; `remove` refuses without
--confirmed, which the skill passes only after the user said to remove it.

Usage:
  python wiki-tasks.py [show]
  python wiki-tasks.py init [--owners "Mark,main,Unassigned"]
  python wiki-tasks.py add "<task>" [--owner <section>] [--status "to do"] [--next "<text>"]
  python wiki-tasks.py set <N> [--task ...] [--status ...] [--next ...] [--owner ...]
  python wiki-tasks.py done <N> [--next "<text>"]
  python wiki-tasks.py remove <N> --confirmed
Every command takes --file <task.md> (default: sessions/<persona>/task.md in the
project's wiki), --persona <name> (default: the project config's "persona", else
main) and --cwd <dir>. `add`, `set` and `done` create the block when it is missing.

Prints the row it changed and `task_file=<path>`. Exit 0 ok; 2 bad input, an
unknown task number, no wiki, or remove without --confirmed; 3 show found no block.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _atomic_io import atomic_write_text  # noqa: E402

HEADING = "## At a glance"
MARKER_RE = re.compile(r"<!--\s*wiki-tasks\s+next-id:\s*(\d+)\s*-->")
STATUSES = ("to do", "doing", "waiting", "parked", "done")
DONE_NEXT = "remove? (your call)"
TABLE_HEAD = ["| # | Task | Status | Next / waiting on |", "|---|---|---|---|"]
INTRO = ("Every task, one line each, by owner. A number is never reused. \"waiting\" is a status: the task "
         "stays with its owner. A task leaves this list only when the user says so; a finished one is marked "
         "`done` and the session asks before removing it. Notes on a task go below, keyed by its number.")


class UserError(Exception):
    pass


def _cells(line: str) -> list[str]:
    parts = re.split(r"(?<!\\)\|", line.strip())
    return [p.strip().replace("\\|", "|") for p in parts[1:-1]]


def _cell(text: str) -> str:
    return " ".join(str(text).split()).replace("|", "\\|")


def _status(s: str) -> str:
    s = " ".join(str(s).lower().split())
    s = {"todo": "to do", "to-do": "to do"}.get(s, s)
    if s not in STATUSES:
        raise UserError(f"status must be one of: {', '.join(STATUSES)} (got {s!r})")
    return s


class Board:
    """The At a glance block of one task.md, parsed; the rest of the file kept as is."""

    def __init__(self, text: str):
        self.lines = text.splitlines()
        self.start = next((i for i, ln in enumerate(self.lines) if ln.strip() == HEADING), None)
        self.end = None
        self.intro: list[str] = []
        self.sections: list[dict] = []
        marker = 0
        if self.start is not None:
            self.end = next((i for i in range(self.start + 1, len(self.lines))
                             if self.lines[i].startswith("## ")), len(self.lines))
            cur = None
            for ln in self.lines[self.start + 1:self.end]:
                m = MARKER_RE.search(ln)
                if m:
                    marker = int(m.group(1))
                    continue
                if ln.startswith("### "):
                    cur = {"name": ln[4:].strip(), "rows": [], "extras": []}
                    self.sections.append(cur)
                    continue
                is_table = ln.lstrip().startswith("|")
                cells = _cells(ln) if is_table else []
                if cur is None:
                    if not is_table:
                        self.intro.append(ln)
                elif len(cells) == 4 and cells[0].isdigit():
                    cur["rows"].append({"id": int(cells[0]), "task": cells[1],
                                        "status": cells[2], "next": cells[3]})
                elif ln.strip() and not is_table:
                    cur["extras"].append(ln)
        # Above every number in the file: the block's own rows and the numbered QUEUE items
        # its notes are keyed by, so a new task never takes a number already in use.
        outside = self.lines if self.start is None else self.lines[:self.start] + self.lines[self.end:]
        used = [r["id"] for s in self.sections for r in s["rows"]]
        used += [int(m.group(1)) for ln in outside if (m := re.match(r"^(\d+)\.\s", ln))]
        self.next_id = max([marker, *[u + 1 for u in used], 1])

    @property
    def exists(self) -> bool:
        return self.start is not None

    def section(self, name: str, create: bool = False) -> dict:
        for s in self.sections:
            if s["name"].lower() == name.strip().lower():
                return s
        if not create:
            raise UserError(f"no owner section {name!r}; sections: {', '.join(s['name'] for s in self.sections)}")
        new = {"name": name.strip(), "rows": [], "extras": []}
        idx = next((i for i, s in enumerate(self.sections) if s["name"].lower() == "unassigned"), len(self.sections))
        self.sections.insert(idx, new)
        return new

    def find(self, n: int) -> tuple[dict, dict]:
        for s in self.sections:
            for r in s["rows"]:
                if r["id"] == n:
                    return s, r
        raise UserError(f"no task #{n} in the list")

    def block(self) -> list[str]:
        out = [HEADING, "", f"<!-- wiki-tasks next-id: {self.next_id} -->"]
        intro = "\n".join(self.intro).strip()
        out += [intro or INTRO, ""]
        for s in self.sections:
            s["rows"].sort(key=lambda r: r["status"] == "done")  # stable: done rows sink to the bottom
            out += [f"### {s['name']}", "", *TABLE_HEAD]
            out += [f"| {r['id']} | {_cell(r['task'])} | {r['status']} | {_cell(r['next'])} |" for r in s["rows"]]
            if s["extras"]:
                out += ["", *s["extras"]]
            out.append("")
        return out

    def text(self) -> str:
        if self.start is None:
            body = self.lines
            return "\n".join(self.block() + body) + "\n"
        return "\n".join(self.lines[:self.start] + self.block() + self.lines[self.end:]) + "\n"


def resolve(args) -> tuple[Path, str]:
    cwd = Path(args.cwd) if args.cwd else Path.cwd()
    if args.file:
        return Path(args.file), (args.persona or "main").strip().lower()
    try:
        from _wiki_config import load_config, wiki_dir
        cfg = load_config(cwd=cwd)
        wiki = Path(wiki_dir(cwd=cwd))
    except Exception as e:  # noqa: BLE001 — any resolution failure is the same answer to the user
        raise UserError(f"no wiki found from {cwd} ({e}); pass --file <task.md>") from e
    if not wiki.is_dir():
        raise UserError(f"no wiki found from {cwd} (looked for {wiki}); pass --file <task.md>")
    persona = (args.persona or cfg.get("persona") or "main").strip().lower()
    return wiki / "sessions" / persona / "task.md", persona


def init_board(board: Board, owners: list[str]) -> None:
    for o in owners:
        board.section(o, create=True)
    if board.start is None and not board.lines:
        board.lines = ["## NOW", "Awaiting next task", "", "## QUEUE", ""]


def row_line(s: dict, r: dict) -> str:
    return f"#{r['id']} | {r['task']} | {r['status']} | {r['next']} | owner: {s['name']}"


def main(argv: list[str]) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--file")
    common.add_argument("--persona")
    common.add_argument("--cwd")
    ap = argparse.ArgumentParser(description="The At a glance task list in sessions/<persona>/task.md.")
    sub = ap.add_subparsers(dest="cmd")
    sub.add_parser("show", parents=[common])
    p = sub.add_parser("init", parents=[common])
    p.add_argument("--owners", help="comma-separated owner sections (default: User,<persona>,Unassigned)")
    p = sub.add_parser("add", parents=[common])
    p.add_argument("task")
    p.add_argument("--owner", default="Unassigned")
    p.add_argument("--status", default="to do")
    p.add_argument("--next", default="")
    p = sub.add_parser("set", parents=[common])
    p.add_argument("n", type=int)
    p.add_argument("--task")
    p.add_argument("--status")
    p.add_argument("--next")
    p.add_argument("--owner")
    p = sub.add_parser("done", parents=[common])
    p.add_argument("n", type=int)
    p.add_argument("--next")
    p = sub.add_parser("remove", parents=[common])
    p.add_argument("n", type=int)
    p.add_argument("--confirmed", action="store_true", help="the user said to remove this task")
    if not argv or argv[0].startswith("-"):
        argv = ["show", *argv]
    args = ap.parse_args(argv)

    try:
        path, persona = resolve(args)
        board = Board(path.read_text(encoding="utf-8") if path.is_file() else "")
        default_owners = ["User", persona, "Unassigned"]

        if args.cmd == "show":
            if not board.exists:
                print(f"no At a glance block in {path} yet — `init` creates one (add/set/done do too)")
                print(f"task_file={path}")
                return 3
            print("\n".join(board.block()).rstrip())
            print(f"task_file={path}")
            return 0

        if args.cmd == "init":
            if board.exists:
                print(f"{path} already has an At a glance block; nothing changed")
                print(f"task_file={path}")
                return 0
            owners = [o.strip() for o in (args.owners or ",".join(default_owners)).split(",") if o.strip()]
            init_board(board, owners)
            changed = "created the At a glance block: " + ", ".join(s["name"] for s in board.sections)
        else:
            if not board.exists:
                init_board(board, default_owners)
            if args.cmd == "add":
                if not args.task.strip():
                    raise UserError("the task text is empty")
                r = {"id": board.next_id, "task": args.task.strip(), "status": _status(args.status),
                     "next": args.next.strip()}
                if r["status"] == "done" and not r["next"]:
                    r["next"] = DONE_NEXT
                s = board.section(args.owner, create=True)
                s["rows"].append(r)
                board.next_id += 1
                changed = "added " + row_line(s, r)
            elif args.cmd in ("set", "done"):
                s, r = board.find(args.n)
                if args.cmd == "done":
                    r["status"] = "done"
                    r["next"] = args.next.strip() if args.next else DONE_NEXT
                else:
                    if args.task is not None:
                        r["task"] = args.task.strip()
                    if args.status is not None:
                        r["status"] = _status(args.status)
                        if r["status"] == "done" and args.next is None:
                            r["next"] = DONE_NEXT
                    if args.next is not None:
                        r["next"] = args.next.strip()
                    if args.owner is not None and args.owner.strip().lower() != s["name"].lower():
                        s["rows"].remove(r)
                        s = board.section(args.owner, create=True)
                        s["rows"].append(r)
                changed = "updated " + row_line(s, r)
            else:  # remove
                s, r = board.find(args.n)
                if not args.confirmed:
                    raise UserError(f"#{args.n} is removed only on the user's word: ask them, then pass --confirmed")
                s["rows"].remove(r)
                changed = f"removed #{r['id']} ({r['task']}); its number is not reused"

        path.parent.mkdir(parents=True, exist_ok=True)
        atomic_write_text(path, board.text())
        print(changed)
        print(f"task_file={path}")
        return 0
    except UserError as e:
        print(f"error: {e}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
