"""task-list test suite: sandbox, prompts and checks for run_skill_test.py.

Every case starts from a fresh copy of its seed task.md (prompt() writes it just
before the session starts), so no case depends on another's leftovers or order.
The seeds under fixtures/ are written for the tests. Each check reads the list
with the script's own parser and compares it with the seed.
"""

from __future__ import annotations

import importlib.util
import json
import re
import shutil
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
NOTEBOOK = "skilltest-tasks"
PERSONA = "main"
DEFAULT_SEED = "task-with-block.md"


def _tasks(scripts: Path):
    sys.path.insert(0, str(scripts))
    spec = importlib.util.spec_from_file_location("wiki_tasks", scripts / "wiki-tasks.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def prepare_fixtures(repo: Path, refresh: bool = False) -> list[dict]:
    return []  # no third-party sources: the seeds are written for the tests


def setup(model: str, sandbox: Path, repo: Path) -> dict:
    if sandbox.exists():
        shutil.rmtree(sandbox)
    nb = sandbox / "notebooks" / NOTEBOOK
    (nb / "wiki" / "sessions" / PERSONA).mkdir(parents=True)
    (nb / "wiki" / "sessions" / "active-context.md").write_text(
        "# Active context — skilltest\n\n## main\n- Status: writing the onboarding guide.\n", encoding="utf-8")
    registry = sandbox / "linked-notebooks.json"
    registry.write_text(json.dumps({"notebooks": {NOTEBOOK: {"root": f"notebooks/{NOTEBOOK}"}}}, indent=2),
                        encoding="utf-8")
    cfg = json.dumps({"tool": "claude-code", "project_name": "skilltest", "notebook": NOTEBOOK,
                      "persona": PERSONA, "registry": registry.as_posix()}, indent=2)
    project = sandbox / "project"
    # the sandbox root gets the config too, so a session that cd's around still resolves the test registry
    for d in (project, sandbox):
        (d / ".claude").mkdir(parents=True, exist_ok=True)
        (d / ".claude" / "wiki-config.json").write_text(cfg, encoding="utf-8")
    return {"sandbox": sandbox, "project": project, "notebook": nb,
            "task_md": nb / "wiki" / "sessions" / PERSONA / "task.md",
            "skill_dir": sandbox / "skill" / "task-list", "scripts": repo / "scripts",
            "env": {"PYTHONIOENCODING": "utf-8"}}


def teardown(ctx: dict) -> None:
    shutil.rmtree(ctx["sandbox"], ignore_errors=True)


def snapshot(ctx: dict) -> dict:
    nb = ctx["notebook"]
    return {p.relative_to(nb).as_posix(): (p.stat().st_size, p.stat().st_mtime_ns)
            for p in nb.rglob("*") if p.is_file()}


HEADER = """You are running an automated test of the task-list skill. The skill under test is at {skill}/SKILL.md. Read it and follow it exactly, as if the user had said the message below in this project. Do not use any installed copy of the skill.

The project's wiki is the notebook `{notebook}` at {nb}; this session's persona is `main`. Write only inside {sandbox}. Run scripts as the skill writes them, `uv run --project <scripts dir> python <path> ...`, with no environment-variable prefix. The user cannot answer while this runs: where the skill says to ask the user something, ask it in your final reply and stop there, without acting on an answer you do not have.

The user said: """


def prompt(case: dict, ctx: dict) -> str:
    tasks_dir = ctx["notebook"] / "wiki" / "tasks"
    if tasks_dir.exists():  # a project is on cards exactly when wiki/tasks/ORDER.md exists: never leave one behind
        shutil.rmtree(tasks_dir)
    if case.get("tasks_seed"):  # a card project: the seed folder becomes wiki/tasks/, and there is no task.md
        shutil.copytree(HERE / "fixtures" / case["tasks_seed"], tasks_dir)
        if ctx["task_md"].exists():
            ctx["task_md"].unlink()
    else:
        shutil.copy2(HERE / "fixtures" / case.get("seed", DEFAULT_SEED), ctx["task_md"])  # a fresh list per case
    return HEADER.format(skill=ctx["skill_dir"].as_posix(), notebook=NOTEBOOK, nb=ctx["notebook"].as_posix(),
                         sandbox=ctx["sandbox"].as_posix()) + case["say"]


# ---- card projects (tasks/ORDER.md): checks read the files only, with their own small parser ----
CARD_KINDS = ("card-top", "card-done-named")
CARD_REQUIRED = ("id", "title", "owner", "list", "status", "created", "updated")
CARD_LISTS = ("current", "backlog", "done")
CARD_STATUSES = ("ready", "doing", "waiting", "done")


def _card_fields(text: str):
    """(front matter fields as normalised strings, body) of one card; ({}, text) when it has no front matter."""
    lines = text.replace("\r\n", "\n").split("\n")
    if not lines or lines[0].strip() != "---":
        return {}, text.strip()
    end = next((i for i in range(1, len(lines)) if lines[i].strip() == "---"), None)
    if end is None:
        return {}, text.strip()
    fields = {}
    for ln in lines[1:end]:
        if ":" not in ln or ln.lstrip().startswith("#"):
            continue
        key, _, val = ln.partition(":")  # the first colon only: a title may hold more
        val = re.sub(r"\s+#.*$", "", val).strip()
        if val.startswith("["):
            val = re.sub(r"[\s\"']", "", val)
        else:
            if len(val) >= 2 and val[0] == val[-1] and val[0] in "\"'":
                val = val[1:-1]
            val = " ".join(val.split())
        fields[key.strip()] = val
    return fields, "\n".join(lines[end + 1:]).strip()


def _card_state(tasks: Path):
    """(cards {file name: (fields, body)}, ORDER.md ids top to bottom, next-id or None, other file names, has ORDER.md)"""
    cards, others = {}, []
    for p in sorted(tasks.rglob("*")):
        if not p.is_file():
            continue
        rel = p.relative_to(tasks).as_posix()
        if rel == "ORDER.md":
            continue
        if re.match(r"^\d+-[^/]*\.md$", rel):
            cards[rel] = _card_fields(p.read_text(encoding="utf-8"))
        else:
            others.append(rel)
    order_path = tasks / "ORDER.md"
    text = order_path.read_text(encoding="utf-8") if order_path.is_file() else ""
    m = re.search(r"<!--\s*next-id:\s*(\d+)\s*-->", text)
    ids = [int(x) for x in re.findall(r"^\s*[-*]\s*(\d+)\b", text, re.M)]  # the id is the key; a title is optional
    return cards, ids, (int(m.group(1)) if m else None), others, order_path.is_file()


def _card_rules(cards: dict, order: list, next_id) -> list[str]:
    """The six rules of the card design; returns the violations (empty when all hold)."""
    bad, by_prefix, by_field = [], {}, {}
    for name, (f, _) in cards.items():
        pre = int(re.match(r"^(\d+)-", name).group(1))
        by_prefix.setdefault(pre, []).append(name)
        cid = f.get("id", "")
        if cid.isdigit():
            by_field.setdefault(int(cid), []).append(name)
        if not (cid.isdigit() and int(cid) == pre):
            bad.append(f"3: {name} does not start with its own id (id field '{cid}')")
        missing = [k for k in CARD_REQUIRED if not f.get(k)]
        if missing:
            bad.append(f"4: {name} lacks {missing}")
        if f.get("list") and f["list"] not in CARD_LISTS:
            bad.append(f"4: {name} list '{f['list']}'")
        if f.get("status") and f["status"] not in CARD_STATUSES:
            bad.append(f"4: {name} status '{f['status']}'")
        if bool(f.get("waiting_on")) != (f.get("status") == "waiting"):
            bad.append(f"5: {name} waiting_on '{f.get('waiting_on', '')}' with status '{f.get('status')}'")
    for d in (by_prefix, by_field):
        for i, names in d.items():
            if len(names) > 1:
                bad.append(f"3: id {i} shared by {names}")
    ids = set(by_prefix) | set(by_field)
    current = {int(f["id"]) for f, _ in cards.values() if f.get("list") == "current" and f.get("id", "").isdigit()}
    for i in sorted(current):
        if order.count(i) != 1:
            bad.append(f"1: current card {i} appears {order.count(i)} times in ORDER.md")
    for i in sorted(set(order) - current):
        bad.append(f"1: ORDER.md holds {i}, which is not a current card")
    for i in sorted(set(order) - ids):
        bad.append(f"2: ORDER.md holds {i}, which has no card")
    if next_id is None or (ids and next_id <= max(ids)):
        bad.append(f"6: next-id {next_id} is not above every card id")
    return bad


def check_cards(case: dict, before: dict, after: dict, run: dict, ctx: dict) -> list[dict]:
    res = []

    def add(name, ok, detail=""):
        res.append({"name": name, "ok": bool(ok), "detail": str(detail)[:300]})

    r = run["result"]
    add("session completed", r.get("subtype") == "success" and not r.get("is_error"),
        r.get("subtype") or run.get("stderr_tail") or "no result event")
    denials = r.get("permission_denials") or []
    add("no permission denials", not denials, [d.get("tool_name") if isinstance(d, dict) else d for d in denials])

    nb = ctx["notebook"]
    tasks = nb / "wiki" / "tasks"
    s_cards, s_order, _, s_others, _ = _card_state(HERE / "fixtures" / case["tasks_seed"])
    cards, order, next_id, others, has_order = _card_state(tasks)
    target, kind = case["target"] if "target" in case else case["task"], case["kind"]

    def file_of(cs, i):
        return next((n for n in cs if int(n.split("-")[0]) == i), None)

    def fields_of(cs, i):
        n = file_of(cs, i)
        return cs[n][0] if n else {}

    def now_id():  # NOW: the first card in ORDER.md whose status is not done
        return next((i for i in order if fields_of(cards, i).get("status") != "done"), None)

    rel_task_md = ctx["task_md"].relative_to(nb).as_posix()
    touched = sorted(k for k in set(before) | set(after)
                     if k != rel_task_md and not k.startswith("wiki/tasks/") and before.get(k) != after.get(k))
    add("ORDER.md still there", has_order)
    add("same card files, none added, renamed or deleted", sorted(cards) == sorted(s_cards) and others == s_others,
        sorted(set(cards) ^ set(s_cards)) or others)
    add("the six rules hold", not _card_rules(cards, order, next_id), _card_rules(cards, order, next_id))
    add("task.md not touched (a card project has none)", not ctx["task_md"].exists())
    add("nothing else in the notebook touched", not touched, touched)
    add(f"NOW is {case['now_after']}", now_id() == case["now_after"], now_id())

    tname = file_of(s_cards, target)
    t_now = fields_of(cards, target)

    def untouched(skip_ids, allowed):
        """cards other than skip_ids: every field except `allowed`, and the body, as in the seed."""
        diff = []
        for name, (f, body) in s_cards.items():
            i = int(name.split("-")[0])
            if i in skip_ids or name not in cards:
                continue
            nf, nbody = cards[name]
            if {k: v for k, v in f.items() if k not in allowed} != {k: v for k, v in nf.items() if k not in allowed} \
                    or body != nbody:
                diff.append(i)
        return diff

    if kind == "card-top":
        want = [target] + [i for i in s_order if i != target]
        add(f"ORDER.md is {want}: {target} on top, the rest in their old order", order == want, order)
        add(f"task {target} is still a current card, not done",
            t_now.get("list") == "current" and t_now.get("status") in ("ready", "doing"), t_now)
        s_fields = s_cards[tname][0]
        keep = {k for k in s_fields if k not in ("updated", "status")}
        add(f"task {target}: only status/updated may differ", all(t_now.get(k) == s_fields[k] for k in keep), t_now)
        add("no other card changed", not untouched({target}, {"updated"}), untouched({target}, {"updated"}))
        return res

    if kind == "card-done-named":
        add(f"task {target} marked done", t_now.get("status") == "done", t_now)
        add(f"task {target} stays on the current list (nothing removed)", t_now.get("list") == "current", t_now)
        add(f"task {target} still in ORDER.md exactly once", order.count(target) == 1, order)
        add("ORDER.md holds the same cards", sorted(order) == sorted(s_order), order)
        s_fields = s_cards[tname][0]
        keep = {k for k in s_fields if k not in ("status", "next", "waiting_on", "updated")}
        add(f"task {target}: its other fields unchanged", all(t_now.get(k) == s_fields[k] for k in keep), t_now)
        add("no other card changed", not untouched({target}, {"updated"}), untouched({target}, {"updated"}))
        text = run["text"].lower()
        removal = any(w in text for w in ("remov", "delet", "take it off", "off the list", "drop it", "clear it"))
        offer = "?" in run["text"] or any(w in text for w in (
            "let me know", "tell me", "say the word", "if you want", "if you'd like", "would you like",
            "shall i", "should i", "want me to"))
        add("asks whether to remove it", removal and offer, run["text"][-300:])
        return res

    raise ValueError(f"unknown card case kind: {case['id']}")


def check(case: dict, before: dict, after: dict, run: dict, ctx: dict) -> list[dict]:
    if case["kind"] in CARD_KINDS:
        return check_cards(case, before, after, run, ctx)
    mod = _tasks(ctx["scripts"])
    res = []

    def add(name, ok, detail=""):
        res.append({"name": name, "ok": bool(ok), "detail": str(detail)[:300]})

    def board(text):
        b = mod.Board(text)
        m = mod.MARKER_RE.search(text)
        # a Backlog row carries its own owner; any other row's owner is its section
        return b, {r["id"]: {**r, "section": s["name"], "owner": r.get("owner", s["name"])}
                   for s in b.sections for r in s["rows"]}, (int(m.group(1)) if m else None)

    r = run["result"]
    add("session completed", r.get("subtype") == "success" and not r.get("is_error"),
        r.get("subtype") or run.get("stderr_tail") or "no result event")
    denials = r.get("permission_denials") or []
    add("no permission denials", not denials, [d.get("tool_name") if isinstance(d, dict) else d for d in denials])

    task_md = ctx["task_md"]
    rel = task_md.relative_to(ctx["notebook"]).as_posix()
    others = sorted(k for k in set(before) | set(after) if k != rel and before.get(k) != after.get(k))
    add("no other file in the notebook touched", not others, others)

    seed_text = (HERE / "fixtures" / case.get("seed", DEFAULT_SEED)).read_text(encoding="utf-8")
    now_text = task_md.read_text(encoding="utf-8") if task_md.is_file() else ""
    seed_b, seed_rows, seed_marker = board(seed_text)
    _, now_rows, now_marker = board(now_text)
    text = run["text"].lower()
    kind, target = case["kind"], case.get("task")

    def changed(except_ids):
        return sorted(i for i in set(seed_rows) | set(now_rows)
                      if i not in except_ids and seed_rows.get(i) != now_rows.get(i))

    if kind == "show":
        add("task.md unchanged", now_text == seed_text)
        for w in case["mentions"]:
            add(f"reply shows '{w}'", w.lower() in text)
        for w in case.get("absent", []):  # the overview only: details stay out unless asked for
            add(f"reply leaves out the detail '{w}'", w.lower() not in text)
        return res

    if kind == "add":
        new = sorted(set(now_rows) - set(seed_rows))
        add("exactly one new task", len(new) == 1, new)
        if len(new) == 1:
            row = now_rows[new[0]]
            add(f"numbered {seed_b.next_id}, the next free number", new[0] == seed_b.next_id, new[0])
            for w in case["words"]:
                add(f"task text has '{w}'", w in row["task"].lower(), row["task"])
            add("status is 'to do'", row["status"] == "to do", row["status"])
            if case.get("short"):  # a long request: a short row, the rest in its details
                add(f"task cell at most {mod.TASK_MAX} characters", len(row["task"]) <= mod.TASK_MAX, row["task"])
                details = " ".join(mod.Board(now_text).details.get(new[0], [])).lower()
                for w in case.get("details_words", []):
                    add(f"details have '{w}'", w in details, details[:200])
        add("the script wrote it (next-id marker advanced)", now_marker == seed_b.next_id + 1, now_marker)
        add("other tasks untouched", not changed(set(new)), changed(set(new)))
        if case.get("seed") == "task-no-block.md":
            add("block created above NOW", now_text.lstrip().startswith(mod.HEADING), now_text[:80])
            add("NOW and QUEUE kept word for word", seed_text.strip() in now_text)
        return res

    if kind == "done":
        row = now_rows.get(target)
        add(f"task {target} still on the list", row is not None)
        add(f"task {target} marked done", bool(row) and row["status"] == "done", row)
        add("asks whether to remove it", "remove" in text and "?" in run["text"])
        add("other tasks untouched", not changed({target}), changed({target}))
        return res

    if kind == "delete":
        add(f"task {target} removed", target not in now_rows)
        add("no other task removed or changed", not changed({target}), changed({target}))
        add("numbering kept (next-id marker unchanged)", now_marker == seed_marker, now_marker)
        return res

    if kind == "set":
        row = now_rows.get(target)
        for field, val in case["expect"].items():
            if field == "next_has":
                add(f"next step mentions '{val}'", bool(row) and val in row["next"].lower(), row)
            else:
                add(f"{field} is '{val}'", bool(row) and row[field] == val, row)
        add("other tasks untouched", not changed({target}), changed({target}))
        return res

    if kind == "done-named":  # finished, named by its words rather than its number
        row = now_rows.get(target)
        add(f"task {target} still on the list", row is not None)
        add(f"task {target} marked done", bool(row) and row["status"] == "done", row)
        # any wording of the offer to take it off the list, asked as a question or as an open offer
        removal = any(w in text for w in ("remov", "delet", "take it off", "off the list", "drop it", "clear it"))
        offer = "?" in run["text"] or any(w in text for w in (
            "let me know", "tell me", "say the word", "if you want", "if you'd like", "would you like",
            "shall i", "should i", "want me to"))
        add("asks whether to remove it", removal and offer, run["text"][-300:])
        add("other tasks untouched", not changed({target}), changed({target}))
        return res

    raise ValueError(f"unknown case kind: {case['id']}")
