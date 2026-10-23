#!/usr/bin/env python3
"""Checks for the task stack (one card per task, tasks/ORDER.md). Never shipped.

    uv run python tests/scripts/test_task_cards.py    # exit 0 = every check passed

agent-builder's design (its task 173, agreed with Mark 2026-10-10): each task is a card,
tasks/<id>-<slug>.md (YAML fields, then the body); ORDER.md lists the current cards' ids in
working order with the next-id counter; NOW is the first card there not done. `check` runs six
rules, and every write that would add a breach is refused.

Task #90 (2026-10-12, every notebook on cards): cards are the only layout. The task.md list, its
`migrate` and `init`, and the --file / --persona flags are gone; the first `add` in a project with
no tasks/ORDER.md starts it on cards; a project that still keeps a task.md list is refused, never
written past (Mark: nothing gets lost).
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "wiki-tasks.py"

# the stack the checks below start from (task #89's test made it by migrating a task.md)
SEED_CARDS = {
    5: ("swap-the-embedding-model", {"title": "Swap the embedding model", "owner": "main", "list": "backlog",
                                     "status": "ready", "next": "only if measured"}, ""),
    11: ("decide-how-personas-work", {"title": "Decide how personas work", "owner": "Mark", "list": "backlog",
                                      "status": "ready", "next": "thinking it over"}, ""),
    12: ("label-the-search-questions", {"title": "Label the search questions", "owner": "Mark", "list": "current",
                                        "status": "ready", "next": "a few days"}, "Fifty questions on the labelling page."),
    20: ("build-the-stack-cards-order", {"title": 'Build "the stack": cards + ORDER', "owner": "main",
                                         "list": "current", "status": "doing", "next": "questions first"},
         "The spec is the intake note.\nSecond line of details."),
    21: ("clean-the-tds-links", {"title": "Clean the TDS links", "owner": "main", "list": "current",
                                 "status": "waiting", "waiting_on": "Mark's yes"}, ""),
    22: ("finished-thing", {"title": "Finished thing", "owner": "main", "list": "current", "status": "done",
                            "next": "remove? (your call)"}, ""),
}
SEED_ORDER = [20, 12, 21, 22]

TASK_MD_LIST = """## At a glance

<!-- wiki-tasks next-id: 3 -->

### main

| # | Task | Status | Next / waiting on |
|---|---|---|---|
| 1 | A task still kept in task.md | to do | |
"""

results: list[tuple[bool, str]] = []


def check(name: str, ok: bool, detail: object = ""):
    results.append((bool(ok), name + (f"  [{detail}]" if not ok and detail != "" else "")))


def run(tasks: Path, *args: str) -> subprocess.CompletedProcess:
    # from the temp folder, never this repo: a script that resolved the wiki from its working directory once
    # wrote these tests' tasks into the real notebook's task.md (2026-10-12, the pre-#90 script in the red run)
    return subprocess.run([sys.executable, str(SCRIPT), *args, "--tasks-dir", str(tasks)], cwd=tasks.parents[1],
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


def seed(tasks: Path) -> None:
    tasks.mkdir(parents=True, exist_ok=True)
    for n, (slug, fields, body) in SEED_CARDS.items():
        fm = {"id": n, **{k: "" for k in ("next", "waiting_on", "priority")}, **fields, "tags": [],
              "created": "2026-10-10", "updated": "2026-10-10", "links": []}
        text = "---\n" + yaml.safe_dump(fm, sort_keys=False, allow_unicode=True) + "---\n" + (f"\n{body}\n" if body else "")
        (tasks / f"{n}-{slug}.md").write_text(text, encoding="utf-8")
    titles = {n: f[1]["title"] for n, f in SEED_CARDS.items()}
    (tasks / "ORDER.md").write_text("<!-- next-id: 30 -->\n" + "".join(f"- {n} {titles[n]}\n" for n in SEED_ORDER),
                                    encoding="utf-8")


with tempfile.TemporaryDirectory() as tmp:
    td = Path(tmp)

    # --- a project with no tasks yet: show says so; the first add starts it on cards
    fresh = td / "fresh" / "wiki" / "tasks"
    (fresh.parent / "sessions" / "main").mkdir(parents=True)
    p = run(fresh, "show")
    check("no tasks yet: show exits 3 and says the first add starts the list",
          p.returncode == 3 and "add" in p.stdout and not fresh.exists(), (p.returncode, p.stdout))
    p = run(fresh, "add", "The first task", "--owner", "main")
    check("the first add creates tasks/ORDER.md and card 1", p.returncode == 0 and (fresh / "ORDER.md").is_file()
          and order(fresh) == [1] and card(fresh, 1)[0]["title"] == "The first task", (p.stdout, p.stderr))
    check("... with next-id 2", "<!-- next-id: 2 -->" in (fresh / "ORDER.md").read_text(encoding="utf-8"))
    check("... and no task.md written", not any((fresh.parent / "sessions").rglob("task.md")))
    p = run(fresh, "check")
    check("the new stack passes check", p.returncode == 0, p.stdout + p.stderr)

    # --- a project that still keeps its tasks in a task.md list is refused, nothing written
    old = td / "old" / "wiki"
    (old / "sessions" / "main").mkdir(parents=True)
    (old / "sessions" / "main" / "task.md").write_text(TASK_MD_LIST, encoding="utf-8")
    for args in (("add", "A new task"), ("show",), ("set", "1", "--next", "x")):
        p = run(old / "tasks", *args)
        check(f"a task.md list still in sessions/: `{args[0]}` refused (exit 2), naming the file",
              p.returncode == 2 and "task.md" in p.stderr, (p.returncode, p.stderr))
    check("... nothing written", not (old / "tasks").exists()
          and (old / "sessions" / "main" / "task.md").read_text(encoding="utf-8") == TASK_MD_LIST)
    ptr = td / "ptr" / "wiki"
    (ptr / "sessions" / "main").mkdir(parents=True)
    (ptr / "sessions" / "main" / "task.md").write_text("# Tasks moved to cards\n\nSee tasks/.\n", encoding="utf-8")
    p = run(ptr / "tasks", "add", "Fine beside a pointer")
    check("a task.md that is only a pointer does not block add", p.returncode == 0, p.stderr)

    # --- the task.md commands and flags are gone
    tasks = td / "a" / "wiki" / "tasks"
    seed(tasks)
    for args in (("migrate",), ("init",), ("show", "--file", "x.md"), ("show", "--persona", "arch")):
        p = run(tasks, *args)
        check(f"`{' '.join(args)}` is not a command or flag any more (exit 2)", p.returncode == 2, p.returncode)

    # --- check passes; show gives NOW first
    p = run(tasks, "check")
    check("check on the seeded stack: ok, exit 0", p.returncode == 0 and "ok" in p.stdout, p.stdout + p.stderr)
    p = run(tasks, "show")
    check("show: NOW is the first card not done, and prints tasks_dir=",
          p.returncode == 0 and "NOW: #20 " in p.stdout and "tasks_dir=" in p.stdout, p.stdout)
    check("show: the backlog is listed with owners", "| 5 | Swap the embedding model | main |" in p.stdout, p.stdout)
    p = run(tasks, "show", "20")
    check("show 20: the card in full", "The spec is the intake note." in p.stdout and "id: 20" in p.stdout, p.stdout)
    _, _, path20 = card(tasks, 20)

    # --- add: a new card, the next id, appended to ORDER.md; a "to do" status is ready
    p = run(tasks, "add", "Write the pilot notes", "--owner", "main", "--priority", "P2", "--tags", "pilot,docs")
    fm, _, _ = card(tasks, 30)
    check("add: card 30 with the given fields", p.returncode == 0 and fm["priority"] == "P2"
          and fm["tags"] == ["pilot", "docs"] and fm["status"] == "ready" and fm["list"] == "current", (p.stderr, fm))
    check("add: appended to ORDER.md, next-id 31", order(tasks)[-1] == 30
          and "<!-- next-id: 31 -->" in (tasks / "ORDER.md").read_text(encoding="utf-8"))
    p = run(tasks, "add", "Someday idea", "--owner", "Mark", "--backlog")
    fm, _, _ = card(tasks, 31)
    check("add --backlog: list backlog, not in ORDER.md", fm["list"] == "backlog" and 31 not in order(tasks), fm)
    p = run(tasks, "show", "--tag", "pilot")
    check("show --tag: only the tagged tasks", "| 30 |" in p.stdout and "| 20 |" not in p.stdout, p.stdout)
    p = run(tasks, "show", "--details")
    check("show --details: the details after the overview", "Fifty questions on the labelling page." in p.stdout
          and "NOW: #20 " in p.stdout, p.stdout)

    # --- the backlog lists each owner's cards doing, ready, then waiting (agent-builder's suggestion, 2026-10-23:
    # it listed them by number, so a waiting card sat above a ready one and order cannot move backlog cards)
    blog = td / "blog" / "wiki" / "tasks"
    seed(blog)
    run(blog, "add", "A later idea", "--owner", "main", "--backlog")
    run(blog, "set", "5", "--status", "waiting", "--waiting-on", "a measurement")
    p = run(blog, "show")
    rows = [ln for ln in p.stdout.split("### Backlog", 1)[-1].splitlines() if ln.startswith("| ") and "| main |" in ln]
    check("show: in the backlog a ready card is listed above a waiting one of the same owner",
          [r.split("|")[1].strip() for r in rows] == ["30", "5"], rows)

    # --- waiting and waiting_on (rule 5)
    p = run(tasks, "set", "12", "--status", "waiting", "--next", "Mark's labels")
    fm, _, _ = card(tasks, 12)
    check("set --status waiting --next Y: waiting_on Y", p.returncode == 0 and fm["waiting_on"] == "Mark's labels", fm)
    run(tasks, "set", "5", "--status", "waiting", "--waiting-on", "agent-builder's reply")
    p = run(tasks, "show", "--waiting")
    check("show --waiting: every waiting card with what it waits on, the backlog's too, and no other card",
          p.returncode == 0 and "| 12 |" in p.stdout and "Mark's labels" in p.stdout and "| 5 |" in p.stdout
          and "| backlog |" in p.stdout and "| 20 |" not in p.stdout, p.stdout)
    p = run(tasks, "show", "--waiting", "mark")
    check("show --waiting <who>: only the cards whose waiting_on names them (any case)",
          "| 12 |" in p.stdout and "| 5 |" not in p.stdout, p.stdout)
    run(tasks, "set", "5", "--status", "ready")
    p = run(tasks, "show", "--waiting", "the printer")
    check("show --waiting <who>, none: says so, exit 0", p.returncode == 0 and "no card is waiting on that" in p.stdout,
          p.stdout)
    p = run(tasks, "set", "12", "--status", "doing")
    fm, _, _ = card(tasks, 12)
    check("leaving waiting clears waiting_on", fm["status"] == "doing" and not fm.get("waiting_on"), fm)
    before = snapshot(tasks)
    p = run(tasks, "set", "12", "--status", "waiting")
    check("waiting with nothing to wait on is refused (rule 5), nothing written",
          p.returncode == 2 and "rule 5" in p.stderr and snapshot(tasks) == before, p.stderr)

    # --- done stays in ORDER.md; NOW moves on; remove takes it out, the card stays
    run(tasks, "done", "20", "--next", "built")
    p = run(tasks, "show")
    check("done 20: still in ORDER.md, NOW moves to the next open card, the done one is named",
          20 in order(tasks) and "NOW: #12 " in p.stdout and "remove: #20" in p.stdout, p.stdout)
    p = run(tasks, "remove", "20")
    check("remove without --confirmed: exit 2", p.returncode == 2, p.stderr)
    p = run(tasks, "remove", "20", "--confirmed")
    fm, _, _ = card(tasks, 20)
    check("remove --confirmed: list done, out of ORDER.md, card kept",
          p.returncode == 0 and fm["list"] == "done" and 20 not in order(tasks) and path20.exists(), (p.stderr, fm))

    # --- backlog / unbacklog / order / owner
    run(tasks, "backlog", "21")
    check("backlog 21: out of ORDER.md", 21 not in order(tasks) and card(tasks, 21)[0]["list"] == "backlog")
    run(tasks, "unbacklog", "21")
    check("unbacklog 21: back at the end of ORDER.md", order(tasks)[-1] == 21 and card(tasks, 21)[0]["list"] == "current")
    run(tasks, "order", "21", "--top")
    check("order --top", order(tasks)[0] == 21, order(tasks))
    run(tasks, "order", "30", "--before", "12")
    o = order(tasks)
    check("order --before", o.index(30) == o.index(12) - 1, o)
    p = run(tasks, "order", "31", "--top")
    check("order on a backlog card: exit 2", p.returncode == 2, p.stderr)
    p = run(tasks, "set", "30", "--status", "parked")
    check("set --status parked on cards: to the backlog", card(tasks, 30)[0]["list"] == "backlog"
          and 30 not in order(tasks), p.stdout + p.stderr)
    run(tasks, "set", "21", "--owner", "Mark")
    check("set --owner: the card's owner changes", card(tasks, 21)[0]["owner"] == "Mark")
    p = run(tasks, "set", "21", "--owner", "Backlog")
    check("Backlog is not an owner: exit 2", p.returncode == 2, p.stderr)

    # --- log, details, the slug
    run(tasks, "log", "12", "started labelling")
    run(tasks, "log", "12", "half done")
    _, body, _ = card(tasks, 12)
    check("log: a **Log** section with dated lines, in order",
          re.search(r"\*\*Log\*\*\n\n- \d{4}-\d{2}-\d{2}: started labelling\n- \d{4}-\d{2}-\d{2}: half done", body), body)
    # task #101 (agent-builder's card 197, 2026-10-12: a progress note sent with set --details replaced the
    # source and the steps written into the details)
    _, _, p12 = card(tasks, 12)
    before = p12.read_text(encoding="utf-8")
    p = run(tasks, "set", "12", "--details", "Done so far: half labelled.")
    check("set --details on a card with details is refused (exit 2), the card untouched, the options named",
          p.returncode == 2 and p12.read_text(encoding="utf-8") == before and "--append-details" in p.stderr
          and "log 12" in p.stderr, (p.returncode, p.stderr))
    p = run(tasks, "done", "12", "--details", "Finished.")
    check("done --details on a card with details is refused too, and the card is not marked done",
          p.returncode == 2 and p12.read_text(encoding="utf-8") == before, p.returncode)
    p = run(tasks, "set", "12", "--append-details", "Done so far: half labelled.")
    _, body, _ = card(tasks, 12)
    check("--append-details adds a paragraph after the details, before the Log, keeping both",
          p.returncode == 0 and re.search(r"Fifty questions[^\n]*\n(?:[^\n]+\n)*\nDone so far: half labelled\.\n\n\*\*Log\*\*",
                                          body) is not None and "half done" in body, body)
    run(tasks, "set", "12", "--details", "New details only.", "--replace-details")
    _, body, _ = card(tasks, 12)
    check("set --details --replace-details replaces the details and keeps the log",
          body.lstrip().startswith("New details only.") and "Fifty questions" not in body
          and "Done so far" not in body and "half done" in body, body)
    _, _, p12 = card(tasks, 12)
    run(tasks, "set", "12", "--task", "Label the fifty search questions")
    _, _, p12b = card(tasks, 12)
    check("set --task: the title changes, the file name never does", p12 == p12b
          and card(tasks, 12)[0]["title"] == "Label the fifty search questions")
    check("ORDER.md's title is refreshed from the card",
          "- 12 Label the fifty search questions" in (tasks / "ORDER.md").read_text(encoding="utf-8"))
    p = run(tasks, "add", "x" * 71)
    check("a task over 70 characters is refused (exit 2)", p.returncode == 2 and "70" in p.stderr, p.stderr)

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
        p_ = run(tasks, "check")
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
          lambda: card(tasks, 31)[2].write_text(card(tasks, 31)[2].read_text(encoding="utf-8")
                                                .replace("status: ready", "status: someday"), encoding="utf-8"), "rule 4")
    edits("a required field removed",
          lambda: card(tasks, 21)[2].write_text(re.sub(r"^owner:.*\n", "", card(tasks, 21)[2].read_text(encoding="utf-8"),
                                                       flags=re.M), encoding="utf-8"), "rule 4")
    edits("waiting_on filled on a card not waiting",
          lambda: card(tasks, 31)[2].write_text(card(tasks, 31)[2].read_text(encoding="utf-8")
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
    p = run(tasks, "set", "21", "--next", "unrelated edit")
    check("an unrelated write goes through beside an existing breach", p.returncode == 0, p.stderr)
    restore()

    # --- the SessionStart hook: ORDER.md and the NOW card, never task.md or other cards
    proj = td / "proj"
    wiki = proj / "llm-wiki" / "wiki"
    (proj / ".claude").mkdir(parents=True)
    (proj / ".claude" / "wiki-config.json").write_text(json.dumps({"vault_root": str(proj), "wiki_topic": "llm-wiki"}),
                                                       encoding="utf-8")
    (wiki / "sessions" / "main").mkdir(parents=True)
    (wiki / "sessions" / "main" / "handoff.md").write_text("GOAL: carry on\n", encoding="utf-8")
    (wiki / "sessions" / "main" / "task.md").write_text("# Tasks moved to cards\n", encoding="utf-8")
    hook = ROOT / "scripts" / "wiki-session-start.py"

    def context() -> str:
        p_ = subprocess.run([sys.executable, str(hook), "--cwd", str(proj)], capture_output=True, text=True,
                            encoding="utf-8")
        return json.loads(p_.stdout)["hookSpecificOutput"]["additionalContext"] if p_.stdout.strip() else ""

    ctx = context()
    check("hook, no cards yet: the handoff is listed, never task.md, and the first add is named",
          "handoff.md" in ctx and "task.md" not in ctx and not re.search(r"^\s+\d+\. .*ORDER\.md", ctx, re.M)
          and "no task cards yet" in ctx, ctx)
    ptasks = wiki / "tasks"
    seed(ptasks)
    run(ptasks, "order", "21", "--top")
    ctx = context()
    now_card = next(ptasks.glob("21-*.md"))
    check("hook, cards: lists ORDER.md and the NOW card", str(ptasks / "ORDER.md") in ctx and str(now_card) in ctx, ctx)
    check("hook, cards: no other card and no task.md", "20-build" not in ctx and "12-label" not in ctx
          and "task.md" not in ctx and "read only the NOW card" in ctx, ctx)
    for n in (21, 20, 12, 22):
        run(ptasks, "done", str(n))
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

    # --- card file names: cut at the last whole word within 50 characters (agent-builder's pilot)
    sys.path.insert(0, str(ROOT / "scripts"))
    import _task_cards as tcm
    long_title = "GitHub CI: run our tests in Actions, read results automatically"
    s = tcm.slugify(long_title)
    check("slug: a long title is cut at a whole word, not mid-word",
          len(s) <= 50 and long_title.lower().replace(":", "").replace(",", "").replace(" ", "-").startswith(s)
          and s == "github-ci-run-our-tests-in-actions-read-results", s)
    check("slug: a short title is kept whole", tcm.slugify("Decide the -C ceiling: 120 or 200")
          == "decide-the-c-ceiling-120-or-200")
    check("slug: one word longer than 50 is still cut at 50", len(tcm.slugify("x" * 70)) == 50)

failed = [n for ok, n in results if not ok]
for ok, n in results:
    print(("PASS " if ok else "FAIL ") + n)
print(f"\n{len(results) - len(failed)}/{len(results)} passed")
sys.exit(1 if failed else 0)
