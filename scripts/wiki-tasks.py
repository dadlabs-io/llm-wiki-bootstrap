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
  python wiki-tasks.py set <N> [--task ...] [--status ...] [--next ...] [--owner ...] [--details ... | --append-details ...]
  python wiki-tasks.py done <N> [--next "<text>"] [--details "<text>" | --append-details "<text>"]
`set` / `done` --details writes a task's details only when it has none; on a task that has some it is
refused (exit 2, nothing written) unless --replace-details is passed (task #101). --append-details adds
a paragraph and keeps the rest.
  python wiki-tasks.py backlog <N>
  python wiki-tasks.py unbacklog <N> [--owner <section>]
  python wiki-tasks.py remove <N> --confirmed
Every command takes --file <task.md> (default: sessions/<persona>/task.md in the
project's wiki), --persona <name> (default: the project config's "persona", else
main) and --cwd <dir>. `add`, `set` and `done` create the block when it is missing.

Prints the row it changed and `task_file=<path>`. Exit 0 ok; 2 bad input, an
unknown task number, no wiki, or remove without --confirmed; 3 show found no block.

Cards (task #89, agent-builder's task-stack design, 2026-10-10): a project whose wiki has
tasks/ORDER.md keeps one card per task in tasks/<id>-<slug>.md instead (_task_cards.py).
The same commands then work on the cards, prints `tasks_dir=<path>`, and adds:
  python wiki-tasks.py check                         # the six rules; exit 1 on a breach
  python wiki-tasks.py order <N> --top|--bottom|--before <M>|--after <M>
  python wiki-tasks.py log <N> "<what happened>"     # a dated line in the card's **Log**
  add/set also take --priority P1|P2|P3, --tags "a,b", --waiting-on "<text>", --link <target>
`migrate [--dry-run] [--now <N>]` turns this persona's task.md into cards (it is what
switches a project on): each live task's row, Task details and numbered QUEUE note move
whole into its card, the rest of task.md goes unchanged to tasks/archive/task-md-<YYYY-MM>.md,
and task.md becomes a two-line pointer. --tasks-dir <dir> names the cards folder (tests).
Exit 1 also means `check` found a breach.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _task_cards as tc  # noqa: E402
from _atomic_io import atomic_write_text  # noqa: E402
from _wiki_config import today_label  # noqa: E402

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
         "stays with its owner. A task leaves this list only when the user says so: a task the user calls done is "
         "removed, and one the session finished is marked `done` until the user agrees to remove it. "
         "A task's details go in Task details below, under its number.")
# the standard intros of earlier versions, brought up to date on the next write
_ASKS = ("Every task, one line each, by owner. A number is never reused. \"waiting\" is a status: the task "
         "stays with its owner. A task leaves this list only when the user says so; a finished one is marked "
         "`done` and the session asks before removing it. ")
OLD_INTROS = {_ASKS + "Notes on a task go below, keyed by its number.",  # before the details section
              _ASKS + "A task's details go in Task details below, under its number."}  # before 2026-10-11's done rule


UserError = tc.UserError  # one error type for both layouts


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
                            f"--replace-details replaces them, `log {n} \"<text>\"` records a dated note (cards)")
        return _detail_lines(text)
    if extra is not None:
        add = _detail_lines(extra)
        if not add:
            raise UserError("--append-details is empty")
        return current + ([""] if current else []) + add
    return None


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
        if intro in OLD_INTROS:
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


# ---------- cards (tasks/ORDER.md present) ----------

def card_line(c: "tc.Card") -> str:
    nxt = f"waiting on: {c.get('waiting_on')}" if c.get("status") == "waiting" else c.get("next")
    return f"#{c.id} | {c.get('title')} | {c.get('status')} | {nxt} | owner: {c.get('owner')}, list: {c.get('list')}"


def _apply(c: "tc.Card", stack: "tc.Stack", args) -> None:
    """The field flags of add / set onto one card."""
    if getattr(args, "task", None) is not None and args.cmd == "set":
        c.fields["title"] = _short(args.task, TASK_MAX, "the task")
    if getattr(args, "status", None) is not None:
        word = " ".join(str(args.status).lower().split())
        if word == "parked":  # task.md's "park 5": on cards that is the backlog
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


def cards_main(args, stack: "tc.Stack") -> int:
    today = today_label()
    where = f"tasks_dir={stack.dir}"
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
    if args.cmd in ("init", "migrate"):
        raise UserError(f"this project is already on cards ({stack.order_path} exists)")

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
        elif args.cmd == "log":
            if not args.text.strip():
                raise UserError("the log text is empty")
            c.add_log(f"{today}: {' '.join(args.text.split())}")
            changed = f"logged on #{c.id}: {today}: {' '.join(args.text.split())}"
        else:
            raise UserError(f"{args.cmd} does not apply to cards")
    stack.touch(c, today)
    stack.save(before)
    print(changed)
    print(where)
    return 0


# ---------- migrate: task.md -> cards ----------

QUEUE_ITEM_RE = re.compile(r"^(\d+)\.\s")


def _ranges(lines: list[str], heading: str, item_re: re.Pattern) -> dict[int, tuple[int, int]]:
    """id -> (start, end) of each numbered item under a `## ` heading, up to the next item or heading."""
    start = next((i for i, ln in enumerate(lines) if ln.strip() == heading), None)
    if start is None:
        return {}
    end = next((i for i in range(start + 1, len(lines)) if lines[i].startswith("## ")), len(lines))
    out: dict[int, tuple[int, int]] = {}
    cur, cur_start = None, None
    for i in range(start + 1, end + 1):
        ln = lines[i] if i < end else "## "
        m = item_re.match(ln)
        if m or ln.startswith("#"):
            if cur is not None and cur not in out:
                stop = i
                while stop > cur_start and not lines[stop - 1].strip():
                    stop -= 1
                out[cur] = (cur_start, stop)
            cur, cur_start = (int(m.group(1)), i) if m else (None, None)
    return out


def migrate(board: Board, task_path: Path, tasks_dir: Path, now_id: int | None, dry_run: bool) -> int:
    today = today_label()
    if not board.exists:
        raise UserError(f"{task_path} has no At a glance block: nothing to migrate")
    if tasks_dir.exists() and any(tasks_dir.glob("*.md")):
        raise UserError(f"{tasks_dir} already holds files; migrate only into an empty folder")
    archive = tasks_dir / tc.ARCHIVE_DIR / f"task-md-{today[:7]}.md"
    if archive.exists():
        raise UserError(f"{archive} already exists")
    lines = board.lines
    details_at = _ranges(lines, DETAILS_HEADING, DETAIL_RE)
    queue_at = _ranges(lines, "## QUEUE", QUEUE_ITEM_RE)

    stack = tc.Stack(tasks_dir)
    stack.virtual = True
    moved: set[int] = set()
    report = []
    for s in board.sections:  # file order
        for r in s["rows"]:
            word = r["status"].strip().lower()
            in_backlog = is_backlog(s) or word == "parked"
            status = "ready" if word in ("parked", "to do", "todo", "to-do") else word
            if status not in tc.STATUSES:
                raise UserError(f"#{r['id']}: status {r['status']!r} has no card status")
            owner = (r.get("owner") or UNASSIGNED) if is_backlog(s) else s["name"]
            body = list(board.details.get(r["id"], []))
            note = []
            if r["id"] in queue_at:
                a, b = queue_at[r["id"]]
                note = lines[a:b]
                body += ([""] if body else []) + ["**From the old QUEUE**", ""] + note
            c = tc.Card(tasks_dir / f"{r['id']}-{tc.slugify(r['task'])}.md",
                        {"id": r["id"], "title": " ".join(r["task"].split()), "owner": owner,
                         "list": "backlog" if in_backlog else "current", "status": status,
                         "next": "" if status == "waiting" else r["next"],
                         "waiting_on": (r["next"] or "not recorded in task.md") if status == "waiting" else "",
                         "priority": "", "tags": [], "created": today, "updated": today, "links": []},
                        "\n".join(body).strip("\n"))
            stack.cards.append(c)
            stack.dirty.add(r["id"])
            if not in_backlog:
                stack.order.append(r["id"])
            moved.add(r["id"])
            report.append(f"card {c.path.name} | list {c.get('list')} | status {status} | owner {owner} | "
                          f"details {len(board.details.get(r['id'], []))} lines | QUEUE note "
                          f"{f'{len(note)} lines' if note else 'none'}")
    if now_id is not None:
        if now_id not in stack.order:
            raise UserError(f"--now {now_id}: not a current task")
        stack.place(now_id, top=True)
    stack.next_id = board.next_id

    # the archive: task.md less the block and the pieces moved whole into cards
    drop = set(range(board.start, board.end))
    for n, (a, b) in list(details_at.items()) + list(queue_at.items()):
        if n in moved:
            drop.update(range(a, b))
    if board.d_start is not None and not any(
            lines[i].strip() for i in range(board.d_start + 1, board.d_end) if i not in drop):
        drop.update(range(board.d_start, board.d_end))
    kept, blank = [], False
    for i, ln in enumerate(lines):
        if i in drop:
            continue
        if not ln.strip():
            if blank or not kept:
                continue
            blank = True
        else:
            blank = False
        kept.append(ln)
    archive_text = (f"# task.md as it was on {today}, less the tasks moved to cards\n\n"
                    f"The live tasks went to `wiki/tasks/<id>-<slug>.md` on {today}: each one's row, Task details "
                    "and numbered QUEUE note, moved whole. Everything else of the old task.md is below, unchanged.\n\n"
                    + "\n".join(kept).rstrip() + "\n")
    rel = archive.relative_to(tasks_dir.parent).as_posix()
    pointer = (f"# Tasks moved to cards ({today})\n\n"
               f"Every task is a card in `tasks/`, `tasks/ORDER.md` is the working order, and this file's history "
               f"is in `{rel}`.\n")

    errs = stack.check()
    print("\n".join(report))
    print("ORDER.md: " + (", ".join(str(n) for n in stack.order) or "(empty)") + f"; next-id {stack.next_id}")
    print(f"archive: {archive} ({len(kept)} lines kept of {len(lines)})")
    print(f"task.md: becomes a two-line pointer to tasks/ ({task_path})")
    print("check: " + ("ok, the six task rules hold" if not errs else "\n  " + "\n  ".join(errs)))
    if errs:
        raise UserError("refused: the migrated cards would break the task rules (above)")
    if dry_run:
        print("dry run: nothing written")
    else:
        archive.parent.mkdir(parents=True, exist_ok=True)
        atomic_write_text(archive, archive_text)
        stack.save([])
        atomic_write_text(task_path, pointer)
        print(f"migrated {len(stack.cards)} tasks to cards")
    print(f"tasks_dir={tasks_dir}")
    return 0


def main(argv: list[str]) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--file")
    common.add_argument("--persona")
    common.add_argument("--cwd")
    common.add_argument("--tasks-dir", help="the cards folder (default: the wiki's tasks/)")
    fields = argparse.ArgumentParser(add_help=False)  # card fields; refused on a task.md list
    fields.add_argument("--priority")
    fields.add_argument("--tags", help="comma-separated; replaces the card's tags")
    fields.add_argument("--waiting-on")
    fields.add_argument("--link", action="append", help="a link to keep on the card (repeatable)")
    ap = argparse.ArgumentParser(description="The At a glance task list in sessions/<persona>/task.md.")
    sub = ap.add_subparsers(dest="cmd")
    p = sub.add_parser("show", parents=[common])
    p.add_argument("n", type=int, nargs="?", help="one task, with its details")
    p.add_argument("--details", action="store_true", help="the overview, then every task's details")
    p.add_argument("--tag", help="cards only: just the tasks with this tag")
    p = sub.add_parser("init", parents=[common])
    p.add_argument("--owners", help="comma-separated owner sections (default: User,<persona>,Unassigned)")
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
    p = sub.add_parser("migrate", parents=[common])
    p.add_argument("--dry-run", action="store_true", help="list what would move; write nothing")
    p.add_argument("--now", type=int, help="the task to put first in ORDER.md")
    p = sub.add_parser("add", parents=[common, fields])
    p.add_argument("task")
    p.add_argument("--owner", default="Unassigned")
    p.add_argument("--status", default="to do")
    p.add_argument("--next", default="")
    p.add_argument("--details", help="the task's details (any length), kept under Task details")
    p.add_argument("--backlog", action="store_true", help="file it straight into the backlog, keeping --owner")
    edits =argparse.ArgumentParser(add_help=False)  # set / done: a task's details
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
    p.add_argument("--owner", help="the section to return it to (default: the owner the backlog recorded)")
    p = sub.add_parser("remove", parents=[common])
    p.add_argument("n", type=int)
    p.add_argument("--confirmed", action="store_true", help="the user said to remove this task")
    if not argv or argv[0].startswith("-"):
        argv = ["show", *argv]
    args = ap.parse_args(argv)

    try:
        path, persona = resolve(args)
        # a wiki's tasks/ sits beside sessions/: <wiki>/sessions/<persona>/task.md -> <wiki>/tasks
        tasks_dir = (Path(args.tasks_dir) if args.tasks_dir
                     else None if args.file else tc.tasks_dir_of(path.parent.parent.parent))
        if tasks_dir is not None and tc.is_on(tasks_dir):
            return cards_main(args, tc.Stack(tasks_dir))
        if args.cmd in ("check", "order", "log"):
            raise UserError(f"`{args.cmd}` works on cards; this project keeps its tasks in {path}")
        if args.cmd in ("add", "set") and any(getattr(args, k, None) is not None
                                              for k in ("priority", "tags", "waiting_on", "link")):
            raise UserError(f"--priority, --tags, --waiting-on and --link are card fields; {path} has none")
        board = Board(path.read_text(encoding="utf-8") if path.is_file() else "")
        if args.cmd == "migrate":
            if tasks_dir is None:
                raise UserError("migrate needs the cards folder: run it from the project, or pass --tasks-dir")
            return migrate(board, path, tasks_dir, args.now, args.dry_run)
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
                details = new_details(args.n, board.details.get(args.n, []), args)
                if details is not None:
                    board.details[args.n] = details
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
