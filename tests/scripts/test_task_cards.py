#!/usr/bin/env python3
"""Checks for task #89: the task stack (one card per task, tasks/ORDER.md). Never shipped.

    uv run python tests/scripts/test_task_cards.py    # exit 0 = every check passed

agent-builder's design (its task 173, agreed with Mark 2026-10-10): a project whose wiki has
tasks/ORDER.md keeps each task as a card, tasks/<id>-<slug>.md (YAML fields, then the body);
ORDER.md lists the current cards' ids in working order with the next-id counter; NOW is the
first card there not done. `migrate` turns task.md into cards (each live task's row, Task
details and QUEUE note moved whole; the rest archived unchanged; task.md a pointer). `check`
runs six rules, and every write that would add a breach is refused.
"""
from __future__ import annotations

import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "wiki-tasks.py"

TASK_MD = """## At a glance

<!-- wiki-tasks next-id: 30 -->
Intro line.

### Mark

| # | Task | Status | Next / waiting on |
|---|---|---|---|
| 11 | Decide how personas work | parked | thinking it over |
| 12 | Label the search questions | to do | a few days |

### main

| # | Task | Status | Next / waiting on |
|---|---|---|---|
| 20 | Build "the stack": cards + ORDER | doing | questions first |
| 21 | Clean the TDS links | waiting | Mark's yes |
| 22 | Finished thing | done | remove? (your call) |

### Unassigned

| # | Task | Status | Next / waiting on |
|---|---|---|---|

### Backlog

| # | Task | Owner | Status | Next / waiting on |
|---|---|---|---|---|
| 5 | Swap the embedding model | main | parked | only if measured |

## Task details

### #12: Label the search questions

Fifty questions on the labelling page.

### #20: Build "the stack": cards + ORDER

The spec is the intake note.
Second line of details.

### #9: An old removed task

Orphan details stay in the archive.

## NOW
2026-10-06: the last session's summary.

Earlier — 2026-10-05: an older summary.

## QUEUE
20. **The stack's long note.** It spans
    two lines, indented.
19. (CLOSED) A closed task's note.
5. **Embedding swap note.**

### Parked (optional)
- A parked idea in prose.
"""

results: list[tuple[bool, str]] = []


def check(name: str, ok: bool, detail: object = ""):
    results.append((bool(ok), name + (f"  [{detail}]" if not ok and detail != "" else "")))


def run(f: Path, tasks: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(SCRIPT), *args, "--file", str(f), "--tasks-dir", str(tasks)],
                          capture_output=True, text=True, encoding="utf-8", env={**os.environ, "PYTHONIOENCODING": "utf-8"})


def card(tasks: Path, n: int) -> tuple[dict, str, Path]:
    p = next(tasks.glob(f"{n}-*.md"))
    text = p.read_text(encoding="utf-8")
    fm = text.split("---\n")[1]
    return yaml.safe_load(fm), text.split("---\n", 2)[2], p


def order(tasks: Path) -> list[int]:
    return [int(m.group(1)) for ln in (tasks / "ORDER.md").read_text(encoding="utf-8").splitlines()
            if (m := re.match(r"^- (\d+)\b", ln))]


def snapshot(d: Path) -> dict:
    return {p.relative_to(d).as_posix(): p.read_text(encoding="utf-8") for p in sorted(d.rglob("*.md"))}


def setup(td: Path) -> tuple[Path, Path]:
    wiki = td / "wiki"
    (wiki / "sessions" / "main").mkdir(parents=True, exist_ok=True)
    f = wiki / "sessions" / "main" / "task.md"
    f.write_text(TASK_MD, encoding="utf-8")
    return f, wiki / "tasks"


with tempfile.TemporaryDirectory() as tmp:
    td = Path(tmp)

    # --- task.md mode: the card-only commands and fields are refused
    f, tasks = setup(td / "a")
    for args in (("check",), ("order", "20", "--top"), ("log", "20", "x"), ("set", "20", "--priority", "P1")):
        p = run(f, tasks, *args)
        check(f"task.md list: `{' '.join(args)}` is refused (exit 2)", p.returncode == 2, (p.returncode, p.stderr))
    check("task.md list: nothing written by the refusals", f.read_text(encoding="utf-8") == TASK_MD
          and not tasks.exists())

    # --- migrate --dry-run writes nothing and says what would move
    p = run(f, tasks, "migrate", "--dry-run")
    check("migrate --dry-run exits 0", p.returncode == 0, p.stderr)
    check("dry run: nothing written", f.read_text(encoding="utf-8") == TASK_MD and not tasks.exists())
    check("dry run: lists every task and the check", all(f"card {n}-" in p.stdout for n in (5, 11, 12, 20, 21, 22))
          and "check: ok" in p.stdout and "dry run: nothing written" in p.stdout, p.stdout)
    check("dry run: names the QUEUE note it moves", "card 20-build-the-stack-cards-order.md" in p.stdout
          and "QUEUE note 2 lines" in p.stdout, p.stdout)

    # --- migrate for real, NOW's task first
    p = run(f, tasks, "migrate", "--now", "20")
    check("migrate exits 0", p.returncode == 0, p.stderr)
    check("ORDER.md: the current tasks in file order, --now first; backlog and parked out",
          order(tasks) == [20, 12, 21, 22], order(tasks))
    check("ORDER.md keeps next-id", "<!-- next-id: 30 -->" in (tasks / "ORDER.md").read_text(encoding="utf-8"))
    fm, body, path20 = card(tasks, 20)
    check("card 20: fields from its row", fm["title"] == 'Build "the stack": cards + ORDER' and fm["owner"] == "main"
          and fm["list"] == "current" and fm["status"] == "doing" and fm["next"] == "questions first", fm)
    check("card 20: the title with quotes and a colon round-trips through YAML", fm["title"].count('"') == 2)
    check("card 20: its Task details moved whole", "The spec is the intake note.\nSecond line of details." in body, body)
    check("card 20: its QUEUE note moved whole, indented line kept",
          "**From the old QUEUE**" in body and "20. **The stack's long note.** It spans\n    two lines, indented." in body,
          body)
    fm, _, _ = card(tasks, 11)
    check("card 11 (parked in Mark's section): list backlog, status ready, owner Mark",
          (fm["list"], fm["status"], fm["owner"]) == ("backlog", "ready", "Mark"), fm)
    fm, _, _ = card(tasks, 5)
    check("card 5 (Backlog row): list backlog, owner from the Owner column",
          (fm["list"], fm["status"], fm["owner"]) == ("backlog", "ready", "main"), fm)
    fm, _, _ = card(tasks, 21)
    check("card 21 (waiting): waiting_on from its Next cell", fm["status"] == "waiting"
          and fm["waiting_on"] == "Mark's yes" and not fm.get("next"), fm)
    fm, _, _ = card(tasks, 12)
    check("card 12: `to do` became ready", fm["status"] == "ready", fm)
    archive = next((tasks / "archive").glob("task-md-*.md")).read_text(encoding="utf-8")
    check("archive: NOW's history kept", "2026-10-06: the last session's summary." in archive
          and "Earlier — 2026-10-05" in archive, archive)
    check("archive: a closed task's QUEUE note and the Parked prose kept",
          "19. (CLOSED) A closed task's note." in archive and "- A parked idea in prose." in archive, archive)
    check("archive: an orphan details entry kept", "Orphan details stay in the archive." in archive, archive)
    check("archive: moved pieces are not duplicated", "The stack's long note" not in archive
          and "Second line of details." not in archive and "| 20 |" not in archive and "Embedding swap note" not in archive,
          archive)
    t = f.read_text(encoding="utf-8")
    check("task.md is now a short pointer to tasks/", len(t.strip().splitlines()) <= 3 and "tasks/ORDER.md" in t
          and "archive/task-md-" in t, t)

    # --- check passes; show gives NOW first
    p = run(f, tasks, "check")
    check("check after migrate: ok, exit 0", p.returncode == 0 and "ok" in p.stdout, p.stdout + p.stderr)
    p = run(f, tasks, "show")
    check("show: NOW is the first card not done, and prints tasks_dir=",
          p.returncode == 0 and "NOW: #20 " in p.stdout and "tasks_dir=" in p.stdout, p.stdout)
    check("show: the backlog is listed with owners", "| 5 | Swap the embedding model | main |" in p.stdout, p.stdout)
    p = run(f, tasks, "show", "20")
    check("show 20: the card in full", "The spec is the intake note." in p.stdout and "id: 20" in p.stdout, p.stdout)

    # --- add: a new card, the next id, appended to ORDER.md
    p = run(f, tasks, "add", "Write the pilot notes", "--owner", "main", "--priority", "P2", "--tags", "pilot,docs")
    fm, _, _ = card(tasks, 30)
    check("add: card 30 with the given fields", p.returncode == 0 and fm["priority"] == "P2"
          and fm["tags"] == ["pilot", "docs"] and fm["status"] == "ready" and fm["list"] == "current", (p.stderr, fm))
    check("add: appended to ORDER.md, next-id 31", order(tasks)[-1] == 30
          and "<!-- next-id: 31 -->" in (tasks / "ORDER.md").read_text(encoding="utf-8"))
    p = run(f, tasks, "add", "Someday idea", "--owner", "Mark", "--backlog")
    fm, _, _ = card(tasks, 31)
    check("add --backlog: list backlog, not in ORDER.md", fm["list"] == "backlog" and 31 not in order(tasks), fm)
    p = run(f, tasks, "show", "--tag", "pilot")
    check("show --tag: only the tagged tasks", "| 30 |" in p.stdout and "| 20 |" not in p.stdout, p.stdout)

    # --- waiting and waiting_on (rule 5)
    p = run(f, tasks, "set", "12", "--status", "waiting", "--next", "Mark's labels")
    fm, _, _ = card(tasks, 12)
    check("set --status waiting --next Y: waiting_on Y", p.returncode == 0 and fm["waiting_on"] == "Mark's labels", fm)
    p = run(f, tasks, "set", "12", "--status", "doing")
    fm, _, _ = card(tasks, 12)
    check("leaving waiting clears waiting_on", fm["status"] == "doing" and not fm.get("waiting_on"), fm)
    before = snapshot(tasks)
    p = run(f, tasks, "set", "12", "--status", "waiting")
    check("waiting with nothing to wait on is refused (rule 5), nothing written",
          p.returncode == 2 and "rule 5" in p.stderr and snapshot(tasks) == before, p.stderr)

    # --- done stays in ORDER.md; NOW moves on; remove takes it out, the card stays
    run(f, tasks, "done", "20", "--next", "built")
    p = run(f, tasks, "show")
    check("done 20: still in ORDER.md, NOW moves to the next open card, the done one is named",
          20 in order(tasks) and "NOW: #12 " in p.stdout and "remove: #20" in p.stdout, p.stdout)
    p = run(f, tasks, "remove", "20")
    check("remove without --confirmed: exit 2", p.returncode == 2, p.stderr)
    p = run(f, tasks, "remove", "20", "--confirmed")
    fm, _, _ = card(tasks, 20)
    check("remove --confirmed: list done, out of ORDER.md, card kept",
          p.returncode == 0 and fm["list"] == "done" and 20 not in order(tasks) and path20.exists(), (p.stderr, fm))

    # --- backlog / unbacklog / order
    run(f, tasks, "backlog", "21")
    check("backlog 21: out of ORDER.md", 21 not in order(tasks) and card(tasks, 21)[0]["list"] == "backlog")
    run(f, tasks, "unbacklog", "21")
    check("unbacklog 21: back at the end of ORDER.md", order(tasks)[-1] == 21 and card(tasks, 21)[0]["list"] == "current")
    run(f, tasks, "order", "21", "--top")
    check("order --top", order(tasks)[0] == 21, order(tasks))
    run(f, tasks, "order", "30", "--before", "12")
    o = order(tasks)
    check("order --before", o.index(30) == o.index(12) - 1, o)
    p = run(f, tasks, "order", "31", "--top")
    check("order on a backlog card: exit 2", p.returncode == 2, p.stderr)
    p = run(f, tasks, "set", "30", "--status", "parked")
    check("set --status parked on cards: to the backlog", card(tasks, 30)[0]["list"] == "backlog"
          and 30 not in order(tasks), p.stdout + p.stderr)

    # --- log, details, the slug
    run(f, tasks, "log", "12", "started labelling")
    run(f, tasks, "log", "12", "half done")
    _, body, _ = card(tasks, 12)
    check("log: a **Log** section with dated lines, in order",
          re.search(r"\*\*Log\*\*\n\n- \d{4}-\d{2}-\d{2}: started labelling\n- \d{4}-\d{2}-\d{2}: half done", body), body)
    run(f, tasks, "set", "12", "--details", "New details only.")
    _, body, _ = card(tasks, 12)
    check("set --details replaces the details and keeps the log", body.lstrip().startswith("New details only.")
          and "Fifty questions" not in body and "half done" in body, body)
    _, _, p12 = card(tasks, 12)
    run(f, tasks, "set", "12", "--task", "Label the fifty search questions")
    _, _, p12b = card(tasks, 12)
    check("set --task: the title changes, the file name never does", p12 == p12b
          and card(tasks, 12)[0]["title"] == "Label the fifty search questions")
    check("ORDER.md's title is refreshed from the card",
          "- 12 Label the fifty search questions" in (tasks / "ORDER.md").read_text(encoding="utf-8"))

    # --- check catches hand edits, rule by rule
    good = snapshot(tasks)

    def restore():
        for p_ in tasks.rglob("*.md"):
            p_.unlink()
        for rel, text in good.items():
            (tasks / rel).parent.mkdir(parents=True, exist_ok=True)
            (tasks / rel).write_text(text, encoding="utf-8")

    def edits(name: str, fn, rule: str):
        restore()
        fn()
        p_ = run(f, tasks, "check")
        check(f"check: {name} -> {rule}, exit 1", p_.returncode == 1 and rule in p_.stdout, p_.stdout + p_.stderr)

    o_path = tasks / "ORDER.md"
    edits("a current card's line deleted from ORDER.md",
          lambda: o_path.write_text(re.sub(r"^- 12 .*\n", "", o_path.read_text(encoding="utf-8"), flags=re.M),
                                    encoding="utf-8"), "rule 1")
    edits("an id in ORDER.md with no card", lambda: o_path.write_text(o_path.read_text(encoding="utf-8") + "- 99\n",
                                                                    encoding="utf-8"), "rule 2")
    edits("a backlog card listed in ORDER.md", lambda: o_path.write_text(o_path.read_text(encoding="utf-8") + "- 5\n",
                                                                        encoding="utf-8"), "rule 1")
    edits("two cards with one id", lambda: (tasks / "12-copy.md").write_text(card(tasks, 12)[2].read_text(encoding="utf-8"),
                                                                            encoding="utf-8"), "rule 3")
    edits("a file name that is not its id",
          lambda: card(tasks, 21)[2].rename(tasks / "77-wrong.md"), "rule 3")
    edits("a status outside the fixed words",
          lambda: card(tasks, 30)[2].write_text(card(tasks, 30)[2].read_text(encoding="utf-8")
                                                .replace("status: ready", "status: someday"), encoding="utf-8"), "rule 4")
    edits("a required field removed",
          lambda: card(tasks, 21)[2].write_text(re.sub(r"^owner:.*\n", "", card(tasks, 21)[2].read_text(encoding="utf-8"),
                                                       flags=re.M), encoding="utf-8"), "rule 4")
    edits("waiting_on filled on a card not waiting",
          lambda: card(tasks, 30)[2].write_text(card(tasks, 30)[2].read_text(encoding="utf-8")
                                                .replace("waiting_on:\n", "waiting_on: someone\n"), encoding="utf-8"),
          "rule 5")
    edits("next-id not above every id", lambda: o_path.write_text(o_path.read_text(encoding="utf-8")
                                                                  .replace("next-id: 32", "next-id: 25"),
                                                                  encoding="utf-8"), "rule 6")
    edits("front matter that does not parse",
          lambda: card(tasks, 21)[2].write_text("---\nid: [21\n---\nx\n", encoding="utf-8"), "rule 4")

    # --- a write never adds a breach, and a breach already there does not block an unrelated write
    restore()
    o_path.write_text(o_path.read_text(encoding="utf-8") + "- 99\n", encoding="utf-8")
    p = run(f, tasks, "set", "21", "--next", "unrelated edit")
    check("an unrelated write goes through beside an existing breach", p.returncode == 0, p.stderr)
    restore()
    p = run(f, tasks, "migrate")
    check("migrate on a project already on cards: exit 2", p.returncode == 2, p.stderr)

    # --- the SessionStart hook: on cards it lists ORDER.md and the NOW card, never task.md or other cards
    import json
    proj = td / "proj"
    wiki = proj / "llm-wiki" / "wiki"
    (proj / ".claude").mkdir(parents=True)
    (proj / ".claude" / "wiki-config.json").write_text(json.dumps({"vault_root": str(proj), "wiki_topic": "llm-wiki"}),
                                                       encoding="utf-8")
    (wiki / "sessions" / "main").mkdir(parents=True)
    (wiki / "sessions" / "main" / "handoff.md").write_text("GOAL: carry on\n", encoding="utf-8")
    (wiki / "sessions" / "main" / "task.md").write_text(TASK_MD, encoding="utf-8")
    hook = ROOT / "scripts" / "wiki-session-start.py"

    def context() -> str:
        p_ = subprocess.run([sys.executable, str(hook), "--cwd", str(proj)], capture_output=True, text=True,
                            encoding="utf-8")
        return json.loads(p_.stdout)["hookSpecificOutput"]["additionalContext"] if p_.stdout.strip() else ""

    ctx = context()
    check("hook, task.md project: lists task.md as before", "task.md" in ctx and "ORDER.md" not in ctx, ctx)
    ptasks = wiki / "tasks"
    run(wiki / "sessions" / "main" / "task.md", ptasks, "migrate", "--now", "21")
    ctx = context()
    now_card = next(ptasks.glob("21-*.md"))
    check("hook, cards: lists ORDER.md and the NOW card", str(ptasks / "ORDER.md") in ctx and str(now_card) in ctx, ctx)
    check("hook, cards: no other card and no task.md", "20-build" not in ctx and "12-label" not in ctx
          and "task.md" not in ctx and "read only the NOW card" in ctx, ctx)
    for n in (21, 20, 12, 22):
        run(wiki / "sessions" / "main" / "task.md", ptasks, "done", str(n))
    ctx = context()
    check("hook, cards, nothing open: no card listed, ask the user", "ask the user what to work on" in ctx
          and not re.search(r"\\tasks\\\d+-|/tasks/\d+-", ctx), ctx)

    # --- the lint: cards are not entries; a link into tasks/ resolves; the task check is reported
    entry = wiki / "project" / "decisions" / "decide-the-stack.md"
    entry.parent.mkdir(parents=True)
    entry.write_text('---\ntitle: "Decide the stack"\ndate: 2026-10-11\ntier: self\nconfidence: high\n---\n\n'
                     "See [the card](../../tasks/12-label-the-search-questions.md) and "
                     "[a gone card](../../tasks/99-gone.md).\n", encoding="utf-8")
    lint = ROOT / "scripts" / "wiki-lint-mechanical.py"

    def run_lint(*extra: str) -> subprocess.CompletedProcess:
        return subprocess.run([sys.executable, str(lint), "--topic", "llm-wiki", "--vault", str(proj), *extra],
                              capture_output=True, text=True, encoding="utf-8",
                              env={**os.environ, "PYTHONIOENCODING": "utf-8"})

    p = run_lint()
    out = p.stdout
    check("lint: the cards are not scanned as entries", "**Files scanned**: 1" in out, out[:600])
    check("lint: a link into tasks/ to a real card is not broken; a missing card is",
          "12-label-the-search-questions.md" not in out.split("## 🔗 Broken Links")[1].split("##")[0]
          and "99-gone.md" in out.split("## 🔗 Broken Links")[1].split("##")[0], out)
    check("lint: the task check is reported, clean", "**Task cards (`tasks/`)**: 0" in out, out[:900])
    o_path = ptasks / "ORDER.md"
    o_path.write_text(o_path.read_text(encoding="utf-8") + "- 98\n", encoding="utf-8")
    entry.write_text(entry.read_text(encoding="utf-8").replace(" and [a gone card](../../tasks/99-gone.md)", ""),
                     encoding="utf-8")
    p = run_lint("--strict")
    check("lint: a task breach is listed and fails --strict", p.returncode == 1 and "rule 2: id 98" in p.stdout,
          (p.returncode, p.stdout[-800:]))

    # --- search: the wrapper drops results under wiki/tasks/
    import importlib.util
    spec = importlib.util.spec_from_file_location("wqq", ROOT / "scripts" / "wiki-qmd-query.py")
    wqq = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(wqq)
    rows = json.dumps([{"file": "qmd://C:\\nb\\wiki/tasks/12-label.md"}, {"file": "qmd://C:\\nb\\wiki/tasks/ORDER.md"},
                       {"file": "qmd://C:\\nb\\wiki/project/decisions/x.md"}])
    kept, dropped = wqq.drop_machine_files(rows, "json", 30)
    check("search: card and ORDER.md results are dropped, an entry kept",
          dropped == 2 and "project/decisions/x.md" in kept and "tasks/" not in kept, kept)

failed = [n for ok, n in results if not ok]
for ok, n in results:
    print(("PASS " if ok else "FAIL ") + n)
print(f"\n{len(results) - len(failed)}/{len(results)} passed")
sys.exit(1 if failed else 0)
