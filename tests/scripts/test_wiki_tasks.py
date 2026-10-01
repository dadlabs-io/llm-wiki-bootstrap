#!/usr/bin/env python3
"""Checks for task #59: the task list's Backlog section. Never shipped.

    python tests/scripts/test_wiki_tasks.py    # exit 0 = every check passed

agent-builder (skill suggestion, 2026-10-01): Mark asked to move parked tasks to a
backlog, and /task-list knew only owner sections, so a "Backlog" owner was made and
each task lost its real owner. Mark's shape (2026-10-01): one `### Backlog` section,
always last (after Unassigned), whose table carries an Owner column; `backlog <N>`
moves a task there keeping its owner, `unbacklog <N>` sends it back.
"""
from __future__ import annotations

import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "wiki-tasks.py"

results: list[tuple[bool, str]] = []


def check(name: str, ok: bool, detail: object = ""):
    results.append((bool(ok), name + (f"  [{detail}]" if not ok and detail != "" else "")))


BASE = """## At a glance

<!-- wiki-tasks next-id: 10 -->
Intro line.

### Mark

| # | Task | Status | Next / waiting on |
|---|---|---|---|
| 3 | Rotate the keys | parked | yours |
| 4 | Pick bot names | to do | |

### main

| # | Task | Status | Next / waiting on |
|---|---|---|---|
| 5 | Discovery pass | to do | soon |

### Unassigned

| # | Task | Status | Next / waiting on |
|---|---|---|---|
| 6 | A loose idea | parked | |

## NOW
Something.

## QUEUE
3. Notes on the keys.
"""

# agent-builder's list as it stands: a Backlog "owner" with 4-cell rows, placed before Unassigned
LEGACY = """## At a glance

<!-- wiki-tasks next-id: 20 -->
Intro.

### Mark

| # | Task | Status | Next / waiting on |
|---|---|---|---|
| 11 | Decide personas | to do | |

### Backlog

| # | Task | Status | Next / waiting on |
|---|---|---|---|
| 14 | Rotate the keys | parked | yours |
| 17 | Re-check the plugin | waiting | 2026-11-01 |

### Unassigned

| # | Task | Status | Next / waiting on |
|---|---|---|---|

## NOW
x
"""


def run(f: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(SCRIPT), *args, "--file", str(f)], capture_output=True, text=True,
                          encoding="utf-8", env={**os.environ, "PYTHONIOENCODING": "utf-8"})


def sections(text: str) -> list[str]:
    block = text.split("## NOW")[0]
    return [ln[4:].strip() for ln in block.splitlines() if ln.startswith("### ")]


def section_body(text: str, name: str) -> str:
    block = text.split("## NOW")[0]
    parts = block.split(f"### {name}\n")
    if len(parts) < 2:
        return ""
    return parts[1].split("\n### ")[0]


def fresh(td: Path, text: str, name: str = "task.md") -> Path:
    f = td / name
    f.write_text(text, encoding="utf-8")
    return f


with tempfile.TemporaryDirectory() as tmp:
    td = Path(tmp)

    # backlog <N>: moves the task, keeps its owner, number, status and next
    f = fresh(td, BASE)
    p = run(f, "backlog", "3")
    t = f.read_text(encoding="utf-8")
    check("backlog 3 exits 0", p.returncode == 0, p.stderr.strip())
    check("the Backlog section is last, after Unassigned", sections(t) == ["Mark", "main", "Unassigned", "Backlog"],
          sections(t))
    bl = section_body(t, "Backlog")
    check("the Backlog table has an Owner column", "| # | Task | Owner | Status | Next / waiting on |" in bl, bl)
    check("task 3 is in the backlog with its owner, status and next kept",
          "| 3 | Rotate the keys | Mark | parked | yours |" in bl, bl)
    check("task 3 has left Mark's section", "| 3 |" not in section_body(t, "Mark"), section_body(t, "Mark"))
    check("the printed line names the owner and the backlog", "owner: Mark" in p.stdout and "backlog" in p.stdout,
          p.stdout.strip())
    check("the rest of the file is untouched", "## QUEUE\n3. Notes on the keys." in t)
    check("the next-id marker is unchanged", "<!-- wiki-tasks next-id: 10 -->" in t)

    # a second task from another owner
    run(f, "backlog", "5")
    t = f.read_text(encoding="utf-8")
    check("a main task keeps main as its owner", "| 5 | Discovery pass | main | to do | soon |" in section_body(t, "Backlog"),
          section_body(t, "Backlog"))

    # backlog on a task already there: refused
    p = run(f, "backlog", "3")
    check("backlog on a task already in the backlog exits 2", p.returncode == 2, p.stdout + p.stderr)

    # set on a backlog row: --owner changes the Owner cell, the row stays in the backlog
    p = run(f, "set", "5", "--owner", "Mark", "--next", "later")
    t = f.read_text(encoding="utf-8")
    check("set --owner on a backlog row exits 0", p.returncode == 0, p.stderr.strip())
    check("set --owner changes the Owner cell and stays in the backlog",
          "| 5 | Discovery pass | Mark | to do | later |" in section_body(t, "Backlog"), section_body(t, "Backlog"))
    check("set --owner on a backlog row creates no new section",
          sections(t) == ["Mark", "main", "Unassigned", "Backlog"], sections(t))

    # unbacklog <N>: back to its owner's section, in the 4-column table
    p = run(f, "unbacklog", "3")
    t = f.read_text(encoding="utf-8")
    check("unbacklog 3 exits 0", p.returncode == 0, p.stderr.strip())
    check("task 3 is back in Mark's section", "| 3 | Rotate the keys | parked | yours |" in section_body(t, "Mark"),
          section_body(t, "Mark"))
    check("task 3 has left the backlog", "| 3 |" not in section_body(t, "Backlog"))

    p = run(f, "unbacklog", "4")
    check("unbacklog on a task not in the backlog exits 2", p.returncode == 2, p.stdout + p.stderr)

    # unbacklog to an owner whose section is gone: recreated among the owners, before Unassigned
    f = fresh(td, BASE)
    run(f, "backlog", "5")
    t = f.read_text(encoding="utf-8")
    check("main's section is kept (now empty) after its only task left", "main" in sections(t), sections(t))
    f.write_text(t.replace("### main\n\n| # | Task | Status | Next / waiting on |\n|---|---|---|---|\n\n", ""),
                 encoding="utf-8")
    check("(setup) main's section removed", "main" not in sections(f.read_text(encoding="utf-8")))
    p = run(f, "unbacklog", "5")
    t = f.read_text(encoding="utf-8")
    check("unbacklog recreates the owner's section before Unassigned and Backlog",
          sections(t) == ["Mark", "main", "Unassigned", "Backlog"], sections(t))
    check("task 5 is in main's recreated section", "| 5 | Discovery pass | to do | soon |" in section_body(t, "main"),
          section_body(t, "main"))

    # done and remove work on a backlog row
    f = fresh(td, BASE)
    run(f, "backlog", "3")
    p = run(f, "done", "3", "--next", "rotated")
    t = f.read_text(encoding="utf-8")
    check("done on a backlog row keeps it in the backlog, marked done",
          p.returncode == 0 and "| 3 | Rotate the keys | Mark | done | rotated |" in section_body(t, "Backlog"),
          section_body(t, "Backlog"))
    p = run(f, "remove", "3", "--confirmed")
    t = f.read_text(encoding="utf-8")
    check("remove --confirmed takes a backlog row off the list", p.returncode == 0 and "| 3 |" not in t, p.stderr)

    # add --backlog: straight into the backlog, with the owner given
    f = fresh(td, BASE)
    p = run(f, "add", "Swap the embedding model", "--owner", "main", "--status", "parked", "--backlog")
    t = f.read_text(encoding="utf-8")
    check("add --backlog exits 0", p.returncode == 0, p.stderr.strip())
    check("add --backlog files the task in the backlog with its owner",
          "| 10 | Swap the embedding model | main | parked |  |" in section_body(t, "Backlog"), section_body(t, "Backlog"))
    p = run(f, "add", "Another", "--owner", "main")
    check("a number in the backlog is never reused", "#11 " in p.stdout, p.stdout.strip())

    # Backlog is not an owner
    f = fresh(td, BASE)
    for args in (("add", "x", "--owner", "Backlog"), ("set", "4", "--owner", "backlog"),
                 ("init", "--owners", "Mark,Backlog")):
        p = run(fresh(td, "" if args[0] == "init" else BASE, "o.md"), *args)
        check(f"--owner Backlog is refused ({args[0]})", p.returncode == 2, p.stdout + p.stderr)

    # a new owner section still lands before Unassigned (and before Backlog)
    f = fresh(td, BASE)
    run(f, "backlog", "6")
    run(f, "add", "Ask the architect", "--owner", "architect")
    t = f.read_text(encoding="utf-8")
    check("a new owner section goes before Unassigned and Backlog",
          sections(t) == ["Mark", "main", "architect", "Unassigned", "Backlog"], sections(t))
    check("an Unassigned task in the backlog keeps Unassigned as owner",
          "| 6 | A loose idea | Unassigned | parked |  |" in section_body(t, "Backlog"), section_body(t, "Backlog"))

    # agent-builder's list today: a 4-column Backlog before Unassigned
    f = fresh(td, LEGACY)
    p = run(f, "show")
    check("the legacy Backlog section shows its tasks", p.returncode == 0 and "| 14 | Rotate the keys |" in p.stdout,
          p.stdout + p.stderr)
    p = run(f, "set", "14", "--owner", "Mark")
    t = f.read_text(encoding="utf-8")
    check("set --owner fills a legacy backlog row's owner, row kept",
          p.returncode == 0 and "| 14 | Rotate the keys | Mark | parked | yours |" in section_body(t, "Backlog"),
          section_body(t, "Backlog"))
    check("the legacy list is rewritten with Backlog last", sections(t) == ["Mark", "Unassigned", "Backlog"],
          sections(t))
    check("a legacy row with no owner yet has an empty Owner cell",
          "| 17 | Re-check the plugin |  | waiting | 2026-11-01 |" in section_body(t, "Backlog"),
          section_body(t, "Backlog"))
    p = run(f, "unbacklog", "17")
    check("unbacklog with no owner recorded exits 2 and says to give one",
          p.returncode == 2 and "--owner" in p.stderr, p.stdout + p.stderr)
    p = run(f, "unbacklog", "17", "--owner", "agent-builder")
    t = f.read_text(encoding="utf-8")
    check("unbacklog --owner sends it to the named owner",
          p.returncode == 0 and "| 17 | Re-check the plugin | waiting | 2026-11-01 |" in section_body(t, "agent-builder"),
          section_body(t, "agent-builder"))

    # without a backlog nothing changes: a set leaves the layout exactly as before
    f = fresh(td, BASE)
    run(f, "set", "4", "--next", "")
    check("a list with no backlog gets no Backlog section", "Backlog" not in f.read_text(encoding="utf-8"))

failed = [n for ok, n in results if not ok]
for ok, n in results:
    print(("PASS " if ok else "FAIL ") + n)
print(f"\n{len(results) - len(failed)}/{len(results)} passed")
sys.exit(1 if failed else 0)
