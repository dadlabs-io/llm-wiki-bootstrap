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

The backlog (Mark, 2026-10-01): one `### Backlog` section, always last (after
Unassigned), whose table carries an Owner column, so a task set aside keeps its
owner. `backlog <N>` moves a task there, `unbacklog <N>` sends it back to its
owner's section. "Backlog" is never an owner name.

A short overview, details apart (Mark's design, 2026-10-04: rows had grown to 3-4 lines and the list
scrolled across two screens): a row's Task is at most 70 characters and its Next at most 60, and
`add` / `set` / `done` refuse a longer one (exit 2). The rest goes in `--details`, kept in a
`## Task details` section right under the block, one `### #N: <task>` entry per task. `show` prints
the overview only; `show --details` adds the details; `show <N>` prints one task with its details.
A row already longer than the limits is kept as it is until an edit touches that cell.

Usage:
  python wiki-tasks.py [show [<N>] [--details]]
  python wiki-tasks.py init [--owners "Mark,main,Unassigned"]
  python wiki-tasks.py add "<task>" [--owner <section>] [--status "to do"] [--next "<text>"] [--details "<text>"] [--backlog]
  python wiki-tasks.py set <N> [--task ...] [--status ...] [--next ...] [--owner ...] [--details ...]
  python wiki-tasks.py done <N> [--next "<text>"] [--details "<text>"]
  python wiki-tasks.py backlog <N>
  python wiki-tasks.py unbacklog <N> [--owner <section>]
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
PLACEHOLDER_OWNER = "User"
UNASSIGNED = "Unassigned"
BACKLOG = "Backlog"
DETAILS_HEADING = "## Task details"
DETAIL_RE = re.compile(r"^###\s+#(\d+):")
TASK_MAX, NEXT_MAX = 70, 60  # characters, the overview's two text cells (Mark, 2026-10-04)
TABLE_HEAD = ["| # | Task | Status | Next / waiting on |", "|---|---|---|---|"]
BACKLOG_HEAD = ["| # | Task | Owner | Status | Next / waiting on |", "|---|---|---|---|---|"]
INTRO = ("Every task, one line each, by owner. A number is never reused. \"waiting\" is a status: the task "
         "stays with its owner. A task leaves this list only when the user says so; a finished one is marked "
         "`done` and the session asks before removing it. A task's details go in Task details below, under its number.")
OLD_INTRO = INTRO.replace("A task's details go in Task details below, under its number.",
                          "Notes on a task go below, keyed by its number.")


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


def is_backlog(s: dict) -> bool:
    return s["name"].lower() == BACKLOG.lower()


def _owner(name: str) -> str:
    if name.strip().lower() == BACKLOG.lower():
        raise UserError(f"{BACKLOG!r} is not an owner: use `backlog <N>` to set a task aside, keeping its owner")
    return name.strip()


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
                elif is_backlog(cur) and len(cells) == 5 and cells[0].isdigit():
                    cur["rows"].append({"id": int(cells[0]), "task": cells[1], "owner": cells[2],
                                        "status": cells[3], "next": cells[4]})
                elif len(cells) == 4 and cells[0].isdigit():
                    # a 4-column row in a Backlog section predates the Owner column: owner not known yet
                    row = {"id": int(cells[0]), "task": cells[1], "status": cells[2], "next": cells[3]}
                    if is_backlog(cur):
                        row["owner"] = ""
                    cur["rows"].append(row)
                elif ln.strip() and not is_table:
                    cur["extras"].append(ln)
        # The details section (any position in the file): one `### #N: <task>` entry per task.
        self.details: dict[int, list[str]] = {}
        self.d_start = next((i for i, ln in enumerate(self.lines) if ln.strip() == DETAILS_HEADING), None)
        self.d_end = None
        if self.d_start is not None:
            self.d_end = next((i for i in range(self.d_start + 1, len(self.lines))
                               if self.lines[i].startswith("## ")), len(self.lines))
            cur_id = None
            for ln in self.lines[self.d_start + 1:self.d_end]:
                m = DETAIL_RE.match(ln)
                if m:
                    cur_id = int(m.group(1))
                    self.details[cur_id] = []
                elif cur_id is not None:
                    self.details[cur_id].append(ln)
            self.details = {k: _detail_lines("\n".join(v)) for k, v in self.details.items()}
        # Above every number in the file: the block's own rows, the details' numbers and the numbered
        # QUEUE items older notes are keyed by, so a new task never takes a number already in use.
        outside = [ln for i, ln in enumerate(self.lines) if not self._in_block(i)]
        used = [r["id"] for s in self.sections for r in s["rows"]] + list(self.details)
        used += [int(m.group(1)) for ln in outside if (m := re.match(r"^(\d+)\.\s", ln))]
        self.next_id = max([marker, *[u + 1 for u in used], 1])

    def _in_block(self, i: int) -> bool:
        """Line i belongs to the At a glance block or to the details section."""
        return ((self.start is not None and self.start <= i < self.end)
                or (self.d_start is not None and self.d_start <= i < self.d_end))

    def details_block(self) -> list[str]:
        titles = {r["id"]: r["task"] for s in self.sections for r in s["rows"]}
        kept = sorted(n for n, body in self.details.items() if n in titles and body)
        if not kept:
            return []
        out = [DETAILS_HEADING, ""]
        for n in kept:
            out += [f"### #{n}: {' '.join(titles[n].split())}", "", *self.details[n], ""]
        return out

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
        last = (UNASSIGNED.lower(), BACKLOG.lower())
        idx = next((i for i, s in enumerate(self.sections) if s["name"].lower() in last), len(self.sections))
        self.sections.insert(idx, new)
        return new

    def backlog(self) -> dict:
        for s in self.sections:
            if is_backlog(s):
                return s
        new = {"name": BACKLOG, "rows": [], "extras": []}
        self.sections.append(new)
        return new

    def find(self, n: int) -> tuple[dict, dict]:
        for s in self.sections:
            for r in s["rows"]:
                if r["id"] == n:
                    return s, r
        raise UserError(f"no task #{n} in the list")

    def block(self) -> list[str]:
        # an empty "User" section is the placeholder the first version created; drop it
        self.sections = [s for s in self.sections if s["rows"] or s["extras"] or s["name"] != PLACEHOLDER_OWNER]
        # the owners in their own order, then Unassigned, then the Backlog last (Mark, 2026-10-01)
        rank = {UNASSIGNED.lower(): 1, BACKLOG.lower(): 2}
        self.sections.sort(key=lambda s: rank.get(s["name"].lower(), 0))
        out = [HEADING, "", f"<!-- wiki-tasks next-id: {self.next_id} -->"]
        intro = "\n".join(self.intro).strip()
        if intro == OLD_INTRO:  # the standard intro from before the details section: brought up to date
            intro = INTRO
        out += [intro or INTRO, ""]
        for s in self.sections:
            s["rows"].sort(key=lambda r: r["status"] == "done")  # stable: done rows sink to the bottom
            if is_backlog(s):
                out += [f"### {s['name']}", "", *BACKLOG_HEAD]
                out += [f"| {r['id']} | {_cell(r['task'])} | {_cell(r['owner'])} | {r['status']} | {_cell(r['next'])} |"
                        for r in s["rows"]]
            else:
                out += [f"### {s['name']}", "", *TABLE_HEAD]
                out += [f"| {r['id']} | {_cell(r['task'])} | {r['status']} | {_cell(r['next'])} |" for r in s["rows"]]
            if s["extras"]:
                out += ["", *s["extras"]]
            out.append("")
        return out

    def text(self) -> str:
        head = self.block() + self.details_block()
        if self.start is None:
            body = [ln for i, ln in enumerate(self.lines) if not self._in_block(i)]
            return "\n".join(head + body) + "\n"
        before = [ln for i, ln in enumerate(self.lines[:self.start]) if not self._in_block(i)]
        after = [ln for i, ln in enumerate(self.lines[self.end:], start=self.end) if not self._in_block(i)]
        return "\n".join(before + head + after) + "\n"


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
    if is_backlog(s):
        return f"#{r['id']} | {r['task']} | {r['status']} | {r['next']} | owner: {r['owner'] or '(none yet)'}, in the backlog"
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
    p = sub.add_parser("show", parents=[common])
    p.add_argument("n", type=int, nargs="?", help="one task, with its details")
    p.add_argument("--details", action="store_true", help="the overview, then every task's details")
    p = sub.add_parser("init", parents=[common])
    p.add_argument("--owners", help="comma-separated owner sections (default: User,<persona>,Unassigned)")
    p = sub.add_parser("add", parents=[common])
    p.add_argument("task")
    p.add_argument("--owner", default="Unassigned")
    p.add_argument("--status", default="to do")
    p.add_argument("--next", default="")
    p.add_argument("--details", help="the task's details (any length), kept under Task details")
    p.add_argument("--backlog", action="store_true", help="file it straight into the backlog, keeping --owner")
    p = sub.add_parser("set", parents=[common])
    p.add_argument("n", type=int)
    p.add_argument("--task")
    p.add_argument("--status")
    p.add_argument("--next")
    p.add_argument("--owner")
    p.add_argument("--details", help="replace the task's details (\"\" clears them)")
    p = sub.add_parser("done", parents=[common])
    p.add_argument("n", type=int)
    p.add_argument("--next")
    p.add_argument("--details", help="replace the task's details")
    p = sub.add_parser("backlog", parents=[common])
    p.add_argument("n", type=int)
    p = sub.add_parser("unbacklog", parents=[common])
    p.add_argument("n", type=int)
    p.add_argument("--owner", help="the section to return it to (default: the owner the backlog recorded)")
    p = sub.add_parser("remove", parents=[common])
    p.add_argument("n", type=int)
    p.add_argument("--confirmed", action="store_true", help="the user said to remove this task")
    if not argv or argv[0].startswith("-"):
        argv = ["show", *argv]
    args = ap.parse_args(argv)

    try:
        path, persona = resolve(args)
        board = Board(path.read_text(encoding="utf-8") if path.is_file() else "")
        # No placeholder section for the user: theirs is created, under their name, by the first task
        # given to them (investment-agent, 2026-09-15: a first `add --owner main` left an empty "User"
        # section beside the "Mark" one made next).
        default_owners = [persona, "Unassigned"]

        if args.cmd == "show":
            if not board.exists:
                print(f"no At a glance block in {path} yet — `init` creates one (add/set/done do too)")
                print(f"task_file={path}")
                return 3
            if args.n is not None:
                s, r = board.find(args.n)
                print(row_line(s, r))
                body = board.details.get(args.n)
                print("\n".join(["", *body]) if body else "(no details)")
            else:
                print("\n".join(board.block() + (board.details_block() if args.details else [])).rstrip())
            print(f"task_file={path}")
            return 0

        if args.cmd == "init":
            if board.exists:
                print(f"{path} already has an At a glance block; nothing changed")
                print(f"task_file={path}")
                return 0
            owners = [_owner(o) for o in (args.owners or ",".join(default_owners)).split(",") if o.strip()]
            init_board(board, owners)
            changed = "created the At a glance block: " + ", ".join(s["name"] for s in board.sections)
        else:
            if not board.exists:
                init_board(board, default_owners)
            if args.cmd == "add":
                if not args.task.strip():
                    raise UserError("the task text is empty")
                r = {"id": board.next_id, "task": _short(args.task, TASK_MAX, "the task"),
                     "status": _status(args.status), "next": _short(args.next, NEXT_MAX, "next")}
                if args.details:
                    board.details[r["id"]] = _detail_lines(args.details)
                if r["status"] == "done" and not r["next"]:
                    r["next"] = DONE_NEXT
                owner = _owner(args.owner)
                if args.backlog:
                    existing = next((o for o in board.sections if o["name"].lower() == owner.lower()), None)
                    r["owner"] = existing["name"] if existing else owner
                    s = board.backlog()
                else:
                    s = board.section(owner, create=True)
                s["rows"].append(r)
                board.next_id += 1
                changed = "added " + row_line(s, r)
            elif args.cmd == "backlog":
                s, r = board.find(args.n)
                if is_backlog(s):
                    raise UserError(f"#{args.n} is already in the backlog (owner: {r['owner'] or 'none yet'})")
                s["rows"].remove(r)
                r["owner"] = s["name"]
                s = board.backlog()
                s["rows"].append(r)
                changed = "moved to the backlog " + row_line(s, r)
            elif args.cmd == "unbacklog":
                s, r = board.find(args.n)
                if not is_backlog(s):
                    raise UserError(f"#{args.n} is not in the backlog (it is in {s['name']}'s section)")
                owner = _owner(args.owner) if args.owner else r["owner"]
                if not owner:
                    raise UserError(f"#{args.n} has no owner recorded in the backlog: pass --owner <section>")
                s["rows"].remove(r)
                del r["owner"]
                s = board.section(owner, create=True)
                s["rows"].append(r)
                changed = "back from the backlog " + row_line(s, r)
            elif args.cmd in ("set", "done"):
                s, r = board.find(args.n)
                if args.details is not None:
                    board.details[args.n] = _detail_lines(args.details)
                if args.cmd == "done":
                    r["status"] = "done"
                    r["next"] = _short(args.next, NEXT_MAX, "next") if args.next else DONE_NEXT
                else:
                    if args.task is not None:
                        r["task"] = _short(args.task, TASK_MAX, "the task")
                    if args.status is not None:
                        r["status"] = _status(args.status)
                        if r["status"] == "done" and args.next is None:
                            r["next"] = DONE_NEXT
                    if args.next is not None:
                        r["next"] = _short(args.next, NEXT_MAX, "next")
                    if args.owner is not None:
                        owner = _owner(args.owner)
                        if is_backlog(s):  # a backlog row keeps its place; only its Owner cell changes
                            existing = next((o for o in board.sections if o["name"].lower() == owner.lower()), None)
                            r["owner"] = existing["name"] if existing else owner
                        elif owner.lower() != s["name"].lower():
                            s["rows"].remove(r)
                            s = board.section(owner, create=True)
                            s["rows"].append(r)
                changed = "updated " + row_line(s, r)
            else:  # remove
                s, r = board.find(args.n)
                if not args.confirmed:
                    raise UserError(f"#{args.n} is removed only on the user's word: ask them, then pass --confirmed")
                s["rows"].remove(r)
                board.details.pop(r["id"], None)
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
