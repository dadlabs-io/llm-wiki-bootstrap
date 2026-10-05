#!/usr/bin/env python3
"""Checks for the task list's short overview and its details (agent-builder's suggestion, Mark's design,
2026-10-04). Never shipped.

    uv run python tests/scripts/test_wiki_tasks_details.py    # exit 0 = every check passed

The At a glance rows grew to 3-4 lines each (one Task cell ~1,500 characters), so the list scrolled across two
screens. Mark's design: each task is a short overview row (Task at most 70 characters, Next at most 60) plus
details kept apart, in a `## Task details` section under the block (`### #N: <task>`). `show` prints the overview
only, `show --details` adds the details, `show <N>` prints one task with its details. `add` / `set` / `done`
refuse an overview cell over its limit (exit 2) and take `--details`. Rows already longer are left as they are
until an edit touches that cell.
"""
from __future__ import annotations

import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "wiki-tasks.py"
LONG_TASK = "A task written as a whole paragraph: " + "with every detail of what it involves and why " * 3
LONG_NEXT = "Next step written as a paragraph too, " + "naming every file and every condition " * 2

BASE = f"""## At a glance

<!-- wiki-tasks next-id: 10 -->
Intro line.

### Mark

| # | Task | Status | Next / waiting on |
|---|---|---|---|
| 3 | Rotate the keys | parked | yours |
| 4 | {LONG_TASK} | to do | {LONG_NEXT} |

### Unassigned

| # | Task | Status | Next / waiting on |
|---|---|---|---|

## NOW
Something.

## QUEUE
3. Notes on the keys.
"""

results: list[tuple[bool, str]] = []


def check(name: str, ok: bool, detail: object = ""):
    results.append((bool(ok), name + (f"  [{detail}]" if not ok and detail != "" else "")))


def run(f: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(SCRIPT), *args, "--file", str(f)], capture_output=True, text=True,
                          encoding="utf-8", env={**os.environ, "PYTHONIOENCODING": "utf-8"})


def fresh(td: Path, text: str = BASE) -> Path:
    f = td / "task.md"
    f.write_text(text, encoding="utf-8")
    return f


with tempfile.TemporaryDirectory() as td:
    td = Path(td)

    # --- the limits
    f = fresh(td)
    p = run(f, "add", "x" * 71, "--owner", "Mark")
    check("add: a Task over 70 characters is refused (exit 2), naming the limit and --details",
          p.returncode == 2 and "70" in p.stderr and "--details" in p.stderr, (p.returncode, p.stderr))
    check("add: nothing written when refused", f.read_text(encoding="utf-8") == BASE)
    p = run(f, "add", "Short task", "--owner", "Mark", "--next", "y" * 61)
    check("add: a Next over 60 characters is refused", p.returncode == 2 and "60" in p.stderr, p.stderr)
    p = run(f, "add", "t" * 70, "--owner", "Mark", "--next", "n" * 60)
    check("add: exactly 70 / 60 is accepted", p.returncode == 0, p.stderr)
    f = fresh(td)
    for args, what in ((("set", "3", "--task", "x" * 71), "set --task"), (("set", "3", "--next", "y" * 61), "set --next"),
                       (("done", "3", "--next", "y" * 61), "done --next")):
        p = run(f, *args)
        check(f"{what}: over the limit is refused", p.returncode == 2, (p.returncode, p.stderr))
    check("refused edits wrote nothing", f.read_text(encoding="utf-8") == BASE)

    # --- a row already longer is left alone until that cell is edited
    p = run(f, "set", "4", "--status", "doing")
    t = f.read_text(encoding="utf-8")
    check("an existing long row: a status change works and keeps its text",
          p.returncode == 0 and f"| 4 | {' '.join(LONG_TASK.split())} | doing |" in t, (p.returncode, p.stderr))

    # --- details: written under the block, before NOW; the rest of the file kept
    f = fresh(td)
    p = run(f, "add", "Write the release notes", "--owner", "Mark", "--next", "after the suite",
            "--details", "Cover the toolset move.\nName every changed command.")
    t = f.read_text(encoding="utf-8")
    check("add --details: ok", p.returncode == 0, p.stderr)
    i_block, i_det, i_now = t.find("## At a glance"), t.find("## Task details"), t.find("## NOW")
    check("a `## Task details` section sits between the block and NOW", -1 < i_block < i_det < i_now, (i_block, i_det, i_now))
    check("the task's heading is `### #10: <task>`", "### #10: Write the release notes" in t, t[i_det:i_now])
    check("both detail lines are kept", "Cover the toolset move." in t and "Name every changed command." in t)
    check("the overview row stays one short line",
          "| 10 | Write the release notes | to do | after the suite |" in t)
    check("NOW and QUEUE are untouched", t.endswith("## NOW\nSomething.\n\n## QUEUE\n3. Notes on the keys.\n"), t[-80:])

    # --- show: overview only by default, details on request, one task by number
    p = run(f, "show")
    check("show: the overview, without details", p.returncode == 0 and "| 10 | Write the release notes" in p.stdout
          and "Cover the toolset move." not in p.stdout and "## Task details" not in p.stdout, p.stdout[-300:])
    p = run(f, "show", "--details")
    check("show --details: the overview and the details", p.returncode == 0 and "| 10 |" in p.stdout
          and "Cover the toolset move." in p.stdout, p.stdout[-300:])
    p = run(f, "show", "10")
    check("show 10: that task's row and its details, no other task",
          p.returncode == 0 and "Write the release notes" in p.stdout and "Cover the toolset move." in p.stdout
          and "Rotate the keys" not in p.stdout, p.stdout)
    p = run(f, "show", "99")
    check("show <unknown N>: exit 2", p.returncode == 2, p.returncode)

    # --- set --details replaces; set --task renames the heading; done keeps the details
    run(f, "set", "10", "--details", "Only this now.")
    t = f.read_text(encoding="utf-8")
    check("set --details replaces the details", "Only this now." in t and "Cover the toolset move." not in t)
    run(f, "set", "10", "--task", "Write the 2026-10 release notes")
    t = f.read_text(encoding="utf-8")
    check("set --task renames the details heading", "### #10: Write the 2026-10 release notes" in t
          and "### #10: Write the release notes\n" not in t, t[t.find("## Task details"):][:200])
    run(f, "done", "10", "--next", "published")
    check("done keeps the details", "Only this now." in f.read_text(encoding="utf-8"))
    run(f, "set", "3", "--details", "Keys live in the vault.")
    t = f.read_text(encoding="utf-8")
    check("details are ordered by task number", t.find("### #3: ") < t.find("### #10: "), t[t.find("## Task details"):])

    # --- remove drops the task's details; an emptied section goes
    run(f, "remove", "10", "--confirmed")
    t = f.read_text(encoding="utf-8")
    check("remove drops that task's details", "### #10" not in t and "Only this now." not in t)
    run(f, "remove", "3", "--confirmed")
    t = f.read_text(encoding="utf-8")
    check("the section goes when its last details go", "## Task details" not in t, t)

    # --- the standard intro from before details is brought up to date on the next write
    old = ('Every task, one line each, by owner. A number is never reused. "waiting" is a status: the task stays with '
           'its owner. A task leaves this list only when the user says so; a finished one is marked `done` and the '
           'session asks before removing it. Notes on a task go below, keyed by its number.')
    f = fresh(td, BASE.replace("Intro line.", old))
    run(f, "set", "3", "--status", "doing")
    t = f.read_text(encoding="utf-8")
    check("the old standard intro is replaced by the new one", "Notes on a task go below" not in t
          and "A task's details go in Task details below" in t, t[:400])
    f = fresh(td)
    run(f, "set", "3", "--status", "doing")
    check("a project's own intro is kept", "Intro line." in f.read_text(encoding="utf-8"))

    # --- a number used only by a details heading is never reused
    f = fresh(td, BASE.replace("## NOW", "## Task details\n\n### #12: An old task\n\nIts notes.\n\n## NOW"))
    p = run(f, "add", "Next one", "--owner", "Mark")
    check("a new task's number is above a details heading's", "added #13 " in p.stdout, p.stdout)

failed = [n for ok, n in results if not ok]
for ok, n in results:
    print(("PASS " if ok else "FAIL ") + n)
print(f"\n{len(results) - len(failed)}/{len(results)} passed")
sys.exit(1 if failed else 0)
