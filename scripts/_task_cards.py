#!/usr/bin/env python3
"""
_task_cards.py — the task stack: one card per task, an order file (task #89, agent-builder's
design 2026-10-10, agreed with Mark; agent-builder-bootstrap was the pilot). Every project's
task list since 2026-10-12 (task #90 removed the older sessions/<persona>/task.md list).

A project has a list when its wiki has `tasks/ORDER.md` (detection, never a setting): the first
`wiki-tasks.py add` creates it.

  wiki/tasks/<id>-<slug>.md   one card: YAML fields, then the body (details, a **Steps**
                              checklist, a dated **Log**), any length. Found by its `<id>-`
                              prefix; the slug is a label, never renamed.
  wiki/tasks/ORDER.md         `<!-- next-id: N -->`, then one `- <id> <title>` line per
                              `list: current` card, in working order. The id is the key; the
                              title is refreshed from the card whenever the script writes.
  wiki/tasks/archive/         (in projects that moved from task.md) that list's history, which
                              nothing reads.

NOW is the first card in ORDER.md whose status is not done. A card is never deleted, so a
number is never reused: `list: done` is the user's word that it is finished with.

The six rules (`check`; every write is refused if it adds a breach, a hand edit is caught by
`check`):
  1. every `list: current` card is in ORDER.md exactly once, and no other card is
  2. every id in ORDER.md has a card
  3. no two cards share an id, and a card's file name starts with its own id
  4. the required fields are present, and list and status use their fixed words
  5. `waiting_on` is filled exactly when status is waiting
  6. next-id is above every card's id
"""

from __future__ import annotations

import datetime as _dt
import re
from pathlib import Path

import yaml

from _atomic_io import atomic_write_text

ORDER_NAME = "ORDER.md"
FIELDS = ("id", "title", "owner", "list", "status", "next", "waiting_on", "priority", "tags", "created",
          "updated", "links")
REQUIRED = ("id", "title", "owner", "list", "status", "created", "updated")
LISTS = ("current", "backlog", "done")
STATUSES = ("ready", "doing", "waiting", "done")
PRIORITIES = ("P1", "P2", "P3")
BACKLOG = "Backlog"
NEXT_ID_RE = re.compile(r"<!--\s*next-id:\s*(\d+)\s*-->")
ORDER_LINE_RE = re.compile(r"^\s*-\s+(\d+)\b")
CARD_ID_RE = re.compile(r"^(\d+)-")
SECTION_MARKS = ("**Steps**", "**Log**")


class UserError(Exception):
    pass


def tasks_dir_of(wiki: Path) -> Path:
    return Path(wiki) / "tasks"


def is_on(tasks_dir: Path) -> bool:
    """A project is on cards exactly when tasks/ORDER.md exists."""
    return (Path(tasks_dir) / ORDER_NAME).is_file()


def slugify(title: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", str(title).lower()).strip("-")
    if len(s) > 50:
        cut = s[:51]  # a hyphen at index 50 means the 50th character ends a whole word
        s = cut[:cut.rfind("-")] if "-" in cut else s[:50]  # the last whole word; one long word is cut at 50
    return s.rstrip("-") or "task"


def card_status(s: str) -> str:
    """A status word, `to do` read as ready. `parked` is not a status: the backlog is."""
    s = " ".join(str(s).lower().split())
    s = {"to do": "ready", "todo": "ready", "to-do": "ready"}.get(s, s)
    if s == "parked":
        raise UserError("`parked` is not a status on cards: `backlog <N>` sets a task aside (list: backlog)")
    if s not in STATUSES:
        raise UserError(f"status must be one of: {', '.join(STATUSES)} (got {s!r})")
    return s


def _yaml_value(v) -> str:
    if v is None or v == "":
        return ""
    if isinstance(v, (list, tuple)):
        return yaml.safe_dump(list(v), allow_unicode=True, default_flow_style=True, width=10**6).strip()
    out = yaml.safe_dump(v, allow_unicode=True, default_flow_style=True, width=10**6).strip()
    return out[:-4].strip() if out.endswith("\n...") else out


def _plain(v):
    """A loaded YAML value as the script keeps it: dates as 'YYYY-MM-DD' strings."""
    if isinstance(v, (_dt.date, _dt.datetime)):
        return v.strftime("%Y-%m-%d")
    return v


class Card:
    def __init__(self, path: Path, fields: dict, body: str, error: str = ""):
        self.path, self.fields, self.body, self.error = Path(path), fields, body, error

    @classmethod
    def load(cls, path: Path) -> "Card":
        text = Path(path).read_text(encoding="utf-8").replace("\r\n", "\n")
        if not text.startswith("---\n"):
            return cls(path, {}, text, "no YAML front matter")
        end = text.find("\n---\n", 4)
        if end == -1 and text.endswith("\n---"):
            end = len(text) - 4
        if end == -1:
            return cls(path, {}, text, "the front matter has no closing ---")
        try:
            data = yaml.safe_load(text[4:end]) or {}
        except yaml.YAMLError as e:
            return cls(path, {}, text, f"the front matter does not parse ({str(e).splitlines()[0]})")
        if not isinstance(data, dict):
            return cls(path, {}, text, "the front matter is not a set of fields")
        return cls(path, {k: _plain(v) for k, v in data.items()}, text[end + 5:].strip("\n"))

    @property
    def id(self):
        v = self.fields.get("id")
        return v if isinstance(v, int) else None

    def get(self, key: str, default=""):
        v = self.fields.get(key)
        return default if v is None else v

    def text(self) -> str:
        keys = list(FIELDS) + [k for k in self.fields if k not in FIELDS]
        lines = ["---"]
        for k in keys:
            v = self.fields.get(k)
            if k in ("tags", "links") and v is None:
                v = []
            val = _yaml_value(v)
            lines.append(f"{k}: {val}" if val != "" else f"{k}:")
        lines.append("---")
        body = self.body.strip("\n")
        return "\n".join(lines) + "\n" + (f"\n{body}\n" if body else "")

    # --- the body: details first, then the **Steps** / **Log** sections, kept as written
    def _split(self) -> tuple[list[str], list[str]]:
        lines = self.body.split("\n") if self.body else []
        cut = next((i for i, ln in enumerate(lines) if ln.strip() in SECTION_MARKS), len(lines))
        return lines[:cut], lines[cut:]

    def details_lines(self) -> list[str]:
        """The body's details: everything above **Steps** / **Log**."""
        return self._split()[0]

    def set_details(self, text: str) -> None:
        _, rest = self._split()
        details = [ln.rstrip() for ln in str(text).replace("\r\n", "\n").strip("\n").split("\n")] if text else []
        self.body = "\n".join(details + ([""] if details and rest else []) + rest).strip("\n")

    def add_log(self, line: str) -> None:
        lines = self.body.split("\n") if self.body else []
        entry = f"- {line}"
        i = next((k for k, ln in enumerate(lines) if ln.strip() == "**Log**"), None)
        if i is None:
            self.body = "\n".join(lines + ([""] if lines else []) + ["**Log**", "", entry]).strip("\n")
            return
        # the log's items: the `- ` lines (and their indented continuations) after the heading's blank line
        j = i + 1
        while j < len(lines) and not lines[j].strip():
            j += 1
        start = j
        while j < len(lines) and (lines[j].startswith("- ") or (j > start and lines[j].startswith("  "))):
            j += 1
        lines[j if j > start else i + 1:j if j > start else i + 1] = [entry] if j > start else ["", entry]
        self.body = "\n".join(lines).strip("\n")


class Stack:
    """wiki/tasks/: the cards and ORDER.md."""

    def __init__(self, tasks_dir: Path):
        self.dir = Path(tasks_dir)
        self.order_path = self.dir / ORDER_NAME
        self.cards: list[Card] = []
        if self.dir.is_dir():
            for p in sorted(self.dir.glob("*.md")):
                if p.name in (ORDER_NAME, "README.md"):
                    continue
                self.cards.append(Card.load(p))
        self.order: list[int] = []
        self.next_id = 0
        self.order_error = ""
        if self.order_path.is_file():
            for ln in self.order_path.read_text(encoding="utf-8").splitlines():
                m = NEXT_ID_RE.search(ln)
                if m:
                    self.next_id = int(m.group(1))
                    continue
                m = ORDER_LINE_RE.match(ln)
                if m:
                    self.order.append(int(m.group(1)))
        self.dirty: set[int] = set()

    # --- lookups
    def by_id(self) -> dict[int, Card]:
        out: dict[int, Card] = {}
        for c in self.cards:
            if c.id is not None and c.id not in out:
                out[c.id] = c
        return out

    def find(self, n: int) -> Card:
        c = self.by_id().get(n)
        if c is None:
            raise UserError(f"no card #{n} in {self.dir}")
        return c

    def now(self) -> Card | None:
        cards = self.by_id()
        for n in self.order:
            c = cards.get(n)
            if c is not None and c.get("status") != "done":
                return c
        return None

    def done_above_now(self) -> list[Card]:
        """Cards marked done but still in ORDER.md: finished, waiting for the user's word."""
        cards = self.by_id()
        return [cards[n] for n in self.order if n in cards and cards[n].get("status") == "done"]

    # --- the six rules
    def check(self) -> list[str]:
        errs: list[str] = []
        seen: dict[int, Path] = {}
        for c in self.cards:
            name = c.path.name
            if c.error:
                errs.append(f"rule 4: {name}: {c.error}")
                continue
            m = CARD_ID_RE.match(name)
            if c.id is None:
                errs.append(f"rule 4: {name}: `id` is missing or not a number")
            else:
                if c.id in seen:
                    errs.append(f"rule 3: id {c.id} is on two cards: {seen[c.id].name} and {name}")
                else:
                    seen[c.id] = c.path
                if not m or int(m.group(1)) != c.id:
                    errs.append(f"rule 3: {name}: the file name does not start with its id ({c.id}-)")
            for k in REQUIRED:
                if c.fields.get(k) in (None, ""):
                    errs.append(f"rule 4: {name}: `{k}` is missing")
            if c.fields.get("list") not in (None, "") and c.fields.get("list") not in LISTS:
                errs.append(f"rule 4: {name}: list {c.fields.get('list')!r} is not one of {', '.join(LISTS)}")
            if c.fields.get("status") not in (None, "") and c.fields.get("status") not in STATUSES:
                errs.append(f"rule 4: {name}: status {c.fields.get('status')!r} is not one of {', '.join(STATUSES)}")
            waiting = c.fields.get("status") == "waiting"
            filled = c.fields.get("waiting_on") not in (None, "")
            if waiting and not filled:
                errs.append(f"rule 5: {name}: status is waiting but `waiting_on` is empty")
            if filled and not waiting:
                errs.append(f"rule 5: {name}: `waiting_on` is filled but status is {c.fields.get('status')!r}")
        cards = self.by_id()
        counts: dict[int, int] = {}
        for n in self.order:
            counts[n] = counts.get(n, 0) + 1
        for n, k in counts.items():
            if k > 1:
                errs.append(f"rule 1: id {n} is in ORDER.md {k} times")
            if n not in cards:
                errs.append(f"rule 2: id {n} is in ORDER.md but has no card")
            elif cards[n].fields.get("list") != "current":
                errs.append(f"rule 1: id {n} is in ORDER.md but its list is {cards[n].fields.get('list')!r}")
        for n, c in cards.items():
            if c.fields.get("list") == "current" and n not in counts:
                errs.append(f"rule 1: {c.path.name} is list: current but not in ORDER.md")
        ids = [c.id for c in self.cards if c.id is not None]
        if ids and self.next_id <= max(ids):
            errs.append(f"rule 6: next-id {self.next_id} is not above the highest card id {max(ids)}")
        if not self.order_path.is_file():
            errs.append(f"rule 1: {self.order_path} does not exist")
        return errs

    # --- writing
    def order_text(self) -> str:
        cards = self.by_id()
        lines = [f"<!-- next-id: {self.next_id} -->"]
        for n in self.order:
            title = " ".join(str(cards[n].get("title")).split()) if n in cards else ""
            lines.append(f"- {n} {title}".rstrip())
        return "\n".join(lines) + "\n"

    def touch(self, c: Card, today: str) -> None:
        c.fields["updated"] = today
        if c.id is not None:
            self.dirty.add(c.id)

    def save(self, before: list[str]) -> None:
        """Write the touched cards and ORDER.md, refusing a state that adds a breach of the six rules."""
        new = [e for e in self.check() if e not in before]
        if new:
            raise UserError("refused: the change would break the task rules:\n  " + "\n  ".join(new))
        self.dir.mkdir(parents=True, exist_ok=True)
        for n in sorted(self.dirty):
            c = self.by_id()[n]
            atomic_write_text(c.path, c.text())
        atomic_write_text(self.order_path, self.order_text())

    def new_card(self, title: str, owner: str, today: str) -> Card:
        n = self.next_id
        c = Card(self.dir / f"{n}-{slugify(title)}.md",
                 {"id": n, "title": title, "owner": owner, "list": "current", "status": "ready", "next": "",
                  "waiting_on": "", "priority": "", "tags": [], "created": today, "updated": today, "links": []},
                 "")
        self.cards.append(c)
        self.next_id = n + 1
        self.dirty.add(n)
        return c

    def place(self, n: int, *, top=False, bottom=False, before: int | None = None, after: int | None = None) -> None:
        if n not in self.order:
            raise UserError(f"#{n} is not in ORDER.md (only list: current cards are ordered)")
        anchor = before if before is not None else after
        if anchor is not None:
            if anchor == n:
                raise UserError("a card cannot move relative to itself")
            if anchor not in self.order:
                raise UserError(f"#{anchor} is not in ORDER.md")
        self.order.remove(n)
        if top:
            self.order.insert(0, n)
        elif bottom:
            self.order.append(n)
        elif before is not None:
            self.order.insert(self.order.index(before), n)
        elif after is not None:
            self.order.insert(self.order.index(after) + 1, n)
        else:
            raise UserError("say where: --top, --bottom, --before <M> or --after <M>")


# --- showing
def _cell(text) -> str:
    return " ".join(str(text if text is not None else "").split()).replace("|", "\\|")


def _next_cell(c: Card) -> str:
    if c.get("status") == "waiting":
        return "waiting on: " + str(c.get("waiting_on"))
    return str(c.get("next"))


def render(stack: Stack, tag: str | None = None) -> list[str]:
    def keep(c: Card) -> bool:
        return tag is None or tag.lower() in [str(t).lower() for t in (c.get("tags") or [])]

    cards = stack.by_id()
    out: list[str] = []
    now = stack.now()
    for c in stack.done_above_now():
        out.append(f"Done, waiting for the user's word to remove: #{c.id} {c.get('title')}")
    out.append(f"NOW: #{now.id} {now.get('title')} ({now.get('status')}, owner {now.get('owner')})"
               if now else "NOW: nothing open in ORDER.md (ask the user what to work on)")
    out += ["", "### Order", "", "| # | Task | Owner | Status | P | Next / waiting on |", "|---|---|---|---|---|---|"]
    for n in stack.order:
        c = cards.get(n)
        if c is None or not keep(c):
            continue
        out.append(f"| {n} | {_cell(c.get('title'))} | {_cell(c.get('owner'))} | {c.get('status')} | "
                   f"{_cell(c.get('priority'))} | {_cell(_next_cell(c))} |")
    # each owner's cards doing, ready, then waiting: the backlog has no ORDER.md, so `order` cannot place them
    rank = {"doing": 0, "ready": 1, "waiting": 2}
    backlog = sorted((c for c in stack.cards if c.get("list") == "backlog" and c.id is not None and keep(c)),
                     key=lambda c: (str(c.get("owner")).lower(), rank.get(c.get("status"), 3), c.id))
    out += ["", f"### {BACKLOG}", "", "| # | Task | Owner | Status | P | Next / waiting on |",
            "|---|---|---|---|---|---|"]
    out += [f"| {c.id} | {_cell(c.get('title'))} | {_cell(c.get('owner'))} | {c.get('status')} | "
            f"{_cell(c.get('priority'))} | {_cell(_next_cell(c))} |" for c in backlog]
    return out
