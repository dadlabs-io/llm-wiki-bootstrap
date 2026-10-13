"""task-list test suite: sandbox, prompts and checks for run_skill_test.py.

Every case starts from a fresh copy of its seed cards folder (prompt() writes it
just before the session starts), so no case depends on another's leftovers or order.
The seeds under fixtures/ are written for the tests. Each check reads the cards and
ORDER.md with its own small parser and compares them with the seed. The task.md
list and its cases went with task #90 (2026-10-12): every project is on cards.
"""

from __future__ import annotations

import json
import re
import shutil
from pathlib import Path

HERE = Path(__file__).resolve().parent
NOTEBOOK = "skilltest-tasks"
PERSONA = "main"


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
    if tasks_dir.exists():  # a project has a list exactly when wiki/tasks/ORDER.md exists: never leave one behind
        shutil.rmtree(tasks_dir)
    if ctx["task_md"].exists():
        ctx["task_md"].unlink()
    if case.get("tasks_seed"):  # the seed folder becomes wiki/tasks/; with no seed the project has no list yet
        shutil.copytree(HERE / "fixtures" / case["tasks_seed"], tasks_dir)
    if case.get("pointer"):  # a leftover task.md beside the cards: a pointer
        shutil.copy2(HERE / "fixtures" / case["pointer"], ctx["task_md"])
    return HEADER.format(skill=ctx["skill_dir"].as_posix(), notebook=NOTEBOOK, nb=ctx["notebook"].as_posix(),
                         sandbox=ctx["sandbox"].as_posix()) + case["say"]


# ---- card projects (tasks/ORDER.md): checks read the files only, with their own small parser ----
CARD_KINDS = ("card-top", "card-done-named")
CARD_REQUIRED = ("id", "title", "owner", "list", "status", "created", "updated")
CARD_LISTS = ("current", "backlog", "done")
CARD_STATUSES = ("ready", "doing", "waiting", "done")
# the user said a task is done: it is removed without a question. Only base forms count as asking, so "I removed it" is fine
BASE_REMOVAL = re.compile(r"\b(remove|delete)\b|take (it|that|this|them) off|drop it|clear it|off the (task )?list", re.I)
OFFER_WORDS = ("let me know", "tell me", "say the word", "if you want", "if you'd like", "would you like",
               "shall i", "should i", "want me to")


def _asks_removal(raw: str) -> bool:
    """True when one sentence is a question or an open offer about removing the task."""
    for m in re.finditer(r"[^.!?\n]+[.!?]?", raw):
        s = m.group().strip()
        if BASE_REMOVAL.search(s) and (s.endswith("?") or any(o in s.lower() for o in OFFER_WORDS)):
            return True
    return False


def _log_dates(body: str):
    """The dates of the bullet lines under **Log**, or None when the card has no such heading."""
    m = re.search(r"^\*\*Log\*\*:?\s*$", body, re.M)
    if not m:
        return None
    return re.findall(r"^-\s+(\d{4}-\d{2}-\d{2}):\s*\S", body[m.end():], re.M)


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

    if kind == "card-done-named":  # the user said it is done: done, off ORDER.md, the card file kept
        from datetime import date
        add(f"task {target} marked done", t_now.get("status") == "done", t_now)
        add(f"task {target} moved to list: done", t_now.get("list") == "done", t_now)
        add(f"task {target} no longer in ORDER.md", target not in order, order)
        want_order = [i for i in s_order if i != target]
        add("ORDER.md holds the other cards in their old order", order == want_order, order)
        add(f"task {target}: its card file is kept", tname in cards, sorted(cards))
        s_fields = s_cards[tname][0]
        keep = {k for k in s_fields if k not in ("status", "next", "waiting_on", "updated", "list")}
        add(f"task {target}: its other fields unchanged", all(t_now.get(k) == s_fields[k] for k in keep), t_now)
        add("no other card changed", not untouched({target}, {"updated"}), untouched({target}, {"updated"}))
        body = cards[tname][1] if tname in cards else ""
        dates = _log_dates(body)
        add(f"task {target}: a Log line dated today under **Log**",
            dates is not None and date.today().isoformat() in dates, dates if dates is not None else "no **Log**")
        add(f"task {target}: its earlier Log line kept", "- 2026-10-08: sections 1 and 2 written." in body)
        add("reply does not ask whether to remove it", not _asks_removal(run["text"]), run["text"][-300:])
        add("reply names the task, not just its number", all(w in run["text"].lower() for w in case["words"]),
            case["words"])
        return res

    raise ValueError(f"unknown card case kind: {case['id']}")


# ---- session-finished and reorder cases on a card project (2026-10-11 rules); reads the files and the reply only ----
CARD_KINDS_SELF = ("card-reorder", "card-done-self")
SELF_REMOVAL_PHRASES = ("remov", "delet", "take it off", "off the list", "drop it", "clear it")
SELF_OFFER_PHRASES = ("let me know", "tell me", "say the word", "if you want", "if you'd like", "would you like",
                      "shall i", "should i", "want me to")


def _offers_removal_self(reply: str) -> bool:
    """The reply offers to take the finished task off the list, as a question or as an open offer."""
    low = reply.lower()
    return any(w in low for w in SELF_REMOVAL_PHRASES) and ("?" in reply or any(w in low for w in SELF_OFFER_PHRASES))


def _reply_names_self(reply: str, pattern: str) -> bool:
    return bool(re.search(pattern, reply, re.I))


def check_cards_self(case: dict, before: dict, after: dict, run: dict, ctx: dict) -> list[dict]:
    from datetime import date
    today = date.today().isoformat()
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
    target, kind, reply = case["task"], case["kind"], run["text"]

    def file_of(cs, i):
        return next((n for n in cs if int(n.split("-")[0]) == i), None)

    def fields_of(cs, i):
        n = file_of(cs, i)
        return cs[n][0] if n else {}

    def changed_cards(skip):  # cards other than `skip` whose fields or body differ in any way from the seed
        return sorted(int(n.split("-")[0]) for n in s_cards
                      if int(n.split("-")[0]) not in skip and n in cards and cards[n] != s_cards[n])

    rel_task_md = ctx["task_md"].relative_to(nb).as_posix()
    touched = sorted(k for k in set(before) | set(after)
                     if k != rel_task_md and not k.startswith("wiki/tasks/") and before.get(k) != after.get(k))
    add("ORDER.md still there", has_order)
    add("same card files, none added, renamed or deleted", sorted(cards) == sorted(s_cards) and others == s_others,
        sorted(set(cards) ^ set(s_cards)) or others)
    add("the six rules hold", not _card_rules(cards, order, next_id), _card_rules(cards, order, next_id))
    add("nothing else in the notebook touched", not touched, touched)
    t_now, s_fields = fields_of(cards, target), fields_of(s_cards, target)
    s_ids = [int(n.split("-")[0]) for n in s_cards]

    if kind == "card-reorder":
        want = case["order_after"]
        add(f"ORDER.md is {want}", order == want, order)
        add("a pure reorder: every card keeps the status it had",
            {i: fields_of(cards, i).get("status") for i in s_ids} == {i: fields_of(s_cards, i).get("status") for i in s_ids},
            {i: fields_of(cards, i).get("status") for i in s_ids})
        add("a pure reorder: every card keeps the list it was on",
            {i: fields_of(cards, i).get("list") for i in s_ids} == {i: fields_of(s_cards, i).get("list") for i in s_ids})
        add(f"the moved card's updated date is today ({today})", t_now.get("updated") == today, t_now.get("updated"))
        add(f"task {target}: only updated differs from the seed",
            all(t_now.get(k) == s_fields.get(k) for k in s_fields if k != "updated"), t_now)
        add("no other card changed at all", not changed_cards({target}), changed_cards({target}))
        add("task.md not recreated (a card project has none)", not ctx["task_md"].exists())
        add("the reply names the moved task by its words", _reply_names_self(reply, case["names"]), reply[-300:])
        return res

    if kind == "card-done-self":  # the session finished it; the user has not said it is done
        add(f"task {target} marked done", t_now.get("status") == "done", t_now)
        add(f"task {target} stays on the current list (nothing removed)", t_now.get("list") == "current", t_now)
        add(f"ORDER.md unchanged ({s_order}): the finished card keeps its position", order == s_order, order)
        keep = {k for k in s_fields if k not in ("status", "next", "waiting_on", "updated")}
        add(f"task {target}: its other fields unchanged", all(t_now.get(k) == s_fields[k] for k in keep), t_now)
        add("no other card changed at all", not changed_cards({target}), changed_cards({target}))
        add("the reply says what was done, naming the task by its words",
            _reply_names_self(reply, case["names"]), reply[-300:])
        add("the reply asks whether to remove it", _offers_removal_self(reply), reply[-300:])
        tm = ctx["task_md"]
        tt = tm.read_text(encoding="utf-8") if tm.is_file() else ""
        titles = [f.get("title", "").lower() for f, _ in cards.values()]
        pointer_only = (not re.search(r"(?m)^\s*(?:#{1,6}\s*|\*\*)?(?:NOW|QUEUE)\b", tt)
                        and not re.search(r"(?m)^\s*\|\s*\d+\s*\|", tt)
                        and not any(t and t in tt.lower() for t in titles))
        add("a leftover task.md is only a pointer (no NOW/QUEUE, no task rows, no task titles)",
            (not tm.is_file()) or pointer_only, tt[:200])
        return res

    raise ValueError(f"unknown card case kind: {case['id']}")


# ---- details are never lost by accident (task #101, 2026-10-12) ----
def _hand_edits(run: dict) -> list[str]:
    """Write/Edit-style calls aimed at a card or task.md: the list is edited only through wiki-tasks.py."""
    bad = []
    for c in run.get("tool_calls", []):
        if c.get("name") in ("Write", "Edit", "MultiEdit", "NotebookEdit"):
            inp = c.get("input") or {}
            p = str(inp.get("file_path") or inp.get("path") or inp.get("notebook_path") or "").replace("\\", "/")
            if "/wiki/tasks/" in p or p.endswith("/task.md"):
                bad.append(f"{c['name']} {p}")
    return bad


def check_card_details(case: dict, before: dict, after: dict, run: dict, ctx: dict) -> list[dict]:
    """The shared rows for a card whose details are added to or replaced (used by card-details-add and
    card-details-replace, which drop and replace its line-based loss check and its Write/Edit-only check)."""
    res = []

    def add(name, ok, detail=""):
        res.append({"name": name, "ok": bool(ok), "detail": str(detail)[:300]})

    def norm(s):
        return " ".join(s.split())

    r = run["result"]
    add("session completed", r.get("subtype") == "success" and not r.get("is_error"),
        r.get("subtype") or run.get("stderr_tail") or "no result event")
    denials = r.get("permission_denials") or []
    add("no permission denials", not denials, [d.get("tool_name") if isinstance(d, dict) else d for d in denials])

    nb = ctx["notebook"]
    tasks = nb / "wiki" / "tasks"
    seed = HERE / "fixtures" / case["tasks_seed"]
    s_cards, s_order, s_next, s_others, _ = _card_state(seed)
    cards, order, next_id, others, has_order = _card_state(tasks)
    target = case["task"]
    tname = next(n for n in s_cards if int(n.split("-")[0]) == target)

    rel_task_md = ctx["task_md"].relative_to(nb).as_posix()
    touched = sorted(k for k in set(before) | set(after)
                     if k != rel_task_md and not k.startswith("wiki/tasks/") and before.get(k) != after.get(k))
    add("ORDER.md still there", has_order)
    add("same card files, none added, renamed or deleted", sorted(cards) == sorted(s_cards) and others == s_others,
        sorted(set(cards) ^ set(s_cards)) or others)
    add("the six rules hold", not _card_rules(cards, order, next_id), _card_rules(cards, order, next_id))
    add("task.md not recreated (a card project has none)", not ctx["task_md"].exists())
    add("nothing else in the notebook touched", not touched, touched)
    order_now = (tasks / "ORDER.md").read_text(encoding="utf-8") if has_order else ""
    add("ORDER.md unchanged", order_now.replace("\r\n", "\n") == (seed / "ORDER.md").read_text(encoding="utf-8").replace("\r\n", "\n"),
        order_now[:200])
    changed = sorted(int(n.split("-")[0]) for n in s_cards if n != tname and n in cards and cards[n] != s_cards[n])
    add("no other card changed at all", not changed, changed)

    s_f, s_body = s_cards[tname]
    f, body = cards.get(tname, ({}, ""))
    add(f"task {target}: id, title, owner, list and created unchanged",
        all(f.get(k) == s_f.get(k) for k in ("id", "title", "owner", "list", "created")), f)
    nbody = norm(body)
    lost = [ln for ln in (norm(x) for x in s_body.splitlines()) if ln and ln not in nbody]
    add(f"task {target}: every line of the existing details (and Log) is still in the card", not lost, lost)
    for w in case["new_words"]:
        add(f"task {target}: the new text ('{w}') is in the card, in the details or the Log", w.lower() in body.lower(),
            body[-200:])
    add("the card file was edited only through the script (no Write/Edit on it)", not _hand_edits(run), _hand_edits(run))
    return res


# ---- details checks v2 (task #108, 2026-10-12): nothing already there is lost; word tokens, not lines ----
def _toks(s: str) -> list[str]:
    """Words only: whitespace, line breaks, punctuation and markdown markers are ignored."""
    return [t for t in (x.strip(".'-/_") for x in re.findall(r"[a-z0-9][a-z0-9'./_-]*", s.lower())) if t]


def _find_seq(hay: list, needle: list) -> int:
    """Index where `needle` occurs contiguously in `hay`, else -1 (an empty needle is at 0)."""
    n = len(needle)
    for i in range(len(hay) - n + 1):
        if hay[i:i + n] == needle:
            return i
    return -1 if n else 0


def _split_body(body: str):
    """(details part, Steps/Log part): the split is at the first **Steps** or **Log** heading."""
    m = re.search(r"^\*\*(Steps|Log)\*\*:?\s*$", body, re.M)
    return (body[:m.start()], body[m.start():]) if m else (body, "")


def _lost_lines(seed_text: str, now_text: str) -> list[str]:
    """Seed lines whose words are no longer, in order, in the new text (a pure reflow loses none)."""
    nt = _toks(now_text)
    return [ln.strip() for ln in seed_text.splitlines() if _toks(ln) and _find_seq(nt, _toks(ln)) < 0]


def _drop(res: list, *prefixes: str) -> list:
    return [r for r in res if not r["name"].startswith(prefixes)]


def check_card_details_add(case: dict, before: dict, after: dict, run: dict, ctx: dict) -> list[dict]:
    """A note or addition on a card that already has details: nothing lost (reflow allowed), new text landed."""
    target = case["task"]
    res = _drop(check_card_details(case, before, after, run, ctx),
                f"task {target}: every line of the existing details",
                "the card file was edited only through the script")

    def add(name, ok, detail=""):
        res.append({"name": name, "ok": bool(ok), "detail": str(detail)[:300]})

    s_cards = _card_state(HERE / "fixtures" / case["tasks_seed"])[0]
    cards = _card_state(ctx["notebook"] / "wiki" / "tasks")[0]
    tname = next(n for n in s_cards if int(n.split("-")[0]) == target)
    s_body, body = s_cards[tname][1], cards.get(tname, ({}, ""))[1]
    lost = _lost_lines(s_body, body)
    add(f"task {target}: every line of the existing details, Steps and Log is still there (reflow allowed)", not lost, lost)
    if case.get("lands_in") == "details":
        s_det, det = _split_body(s_body)[0], _split_body(body)[0]
        dt, st = _toks(det), _toks(s_det)
        i = _find_seq(dt, st)
        for w in case["new_words"]:
            add(f"the new text ('{w}') is after the old details, before Steps and Log",
                i >= 0 and _find_seq(dt[i + len(st):], _toks(w)) >= 0, det[-200:])
    return res


def check_card_details_replace(case: dict, before: dict, after: dict, run: dict, ctx: dict) -> list[dict]:
    """The user asked to replace a card's details: old details gone, new in, Steps, Log and fields kept."""
    target = case["task"]
    res = _drop(check_card_details(dict(case, new_words=[]), before, after, run, ctx),
                f"task {target}: every line of the existing details",
                "the card file was edited only through the script")

    def add(name, ok, detail=""):
        res.append({"name": name, "ok": bool(ok), "detail": str(detail)[:300]})

    s_cards = _card_state(HERE / "fixtures" / case["tasks_seed"])[0]
    cards = _card_state(ctx["notebook"] / "wiki" / "tasks")[0]
    tname = next(n for n in s_cards if int(n.split("-")[0]) == target)
    s_f, s_body = s_cards[tname]
    f, body = cards.get(tname, ({}, ""))
    s_det, s_tail = _split_body(s_body)
    det, tail = _split_body(body)
    dt = _toks(det)
    add(f"task {target} had details and a Steps/Log part to keep (seed)", bool(_toks(s_det)) and bool(_toks(s_tail)))
    for w in case["old_words"]:
        add(f"task {target}: old details text '{w}' is gone", _find_seq(dt, _toks(w)) < 0, det[:200])
    for w in case["new_words"]:
        add(f"task {target}: new details text '{w}' is in the details, before Steps and Log",
            _find_seq(dt, _toks(w)) >= 0, det[:200])
    lost = _lost_lines(s_tail, tail)
    add(f"task {target}: Steps and Log kept", not lost, lost)
    add(f"task {target}: every field except updated unchanged",
        {k: v for k, v in f.items() if k != "updated"} == {k: v for k, v in s_f.items() if k != "updated"}, f)
    return res


# ---- gaps on cards (show, add, first add, delete, waiting, backlog, owner, old list); reads files and the reply ----
CARD_KINDS_MORE = ("card-show", "card-add", "card-first", "card-delete", "card-waiting",
                   "card-backlog", "card-owner", "card-old-list")
OLD_LIST_WORDS = re.compile(r"at a glance|task\.md|\b(old|existing|legacy|previous|leftover|earlier)\b[^.\n]{0,30}\blist\b", re.I)


def check_cards_more(case: dict, before: dict, after: dict, run: dict, ctx: dict) -> list[dict]:
    res = []

    def add(name, ok, detail=""):
        res.append({"name": name, "ok": bool(ok), "detail": str(detail)[:300]})

    r, reply, kind = run["result"], run["text"], case["kind"]
    add("session completed", r.get("subtype") == "success" and not r.get("is_error"),
        r.get("subtype") or run.get("stderr_tail") or "no result event")
    denials = r.get("permission_denials") or []
    add("no permission denials", not denials, [d.get("tool_name") if isinstance(d, dict) else d for d in denials])

    nb = ctx["notebook"]
    tasks = nb / "wiki" / "tasks"
    rel_task_md = ctx["task_md"].relative_to(nb).as_posix()
    touched = sorted(k for k in set(before) | set(after)
                     if k != rel_task_md and not k.startswith("wiki/tasks/") and before.get(k) != after.get(k))
    add("nothing else in the notebook touched", not touched, touched)

    if kind == "card-old-list":  # an old "At a glance" task.md and no cards: refused, nothing written, the user told
        seed_text = (HERE / "fixtures" / case["pointer"]).read_text(encoding="utf-8").replace("\r\n", "\n")
        tm = ctx["task_md"]
        now_text = tm.read_text(encoding="utf-8").replace("\r\n", "\n") if tm.is_file() else None
        made = sorted(p.relative_to(tasks).as_posix() for p in tasks.rglob("*") if p.is_file()) if tasks.exists() else []
        add("nothing created under wiki/tasks/ (no ORDER.md, no card)", not made, made)
        add("the old task.md is unchanged", now_text == seed_text, (now_text or "missing")[:200])
        add("the reply tells the user an old list is in the way", bool(OLD_LIST_WORDS.search(reply)), reply[-300:])
        return res

    seed = case.get("tasks_seed")
    if seed:
        s_cards, s_order, s_next, s_others, _ = _card_state(HERE / "fixtures" / seed)
        s_order_text = (HERE / "fixtures" / seed / "ORDER.md").read_text(encoding="utf-8").replace("\r\n", "\n")
    else:
        s_cards, s_order, s_next, s_others, s_order_text = {}, [], None, [], ""
    cards, order, next_id, others, has_order = _card_state(tasks)
    order_text = (tasks / "ORDER.md").read_text(encoding="utf-8").replace("\r\n", "\n") if has_order else ""
    add("ORDER.md there", has_order)
    add("the six rules hold", not _card_rules(cards, order, next_id), _card_rules(cards, order, next_id))
    add("task.md not created (a card project has none)", not ctx["task_md"].exists())

    def file_of(cs, i):
        return next((n for n in cs if int(n.split("-")[0]) == i), None)

    def others_same(skip):  # every seed card except `skip` is exactly as seeded, fields and body
        return sorted(int(n.split("-")[0]) for n in s_cards
                      if int(n.split("-")[0]) != skip and cards.get(n) != s_cards[n])

    if kind == "card-show":  # read-only: cards and ORDER.md as seeded; details only when asked
        add("nothing written: cards, ORDER.md and counter as seeded",
            cards == s_cards and others == s_others and order_text == s_order_text and next_id == s_next)
        rt = _toks(reply)
        low = reply.lower()
        if case.get("order_words"):
            pos = [(m.start() if (m := re.search(w, low)) else -1) for w in case["order_words"]]
            add("the reply mentions every current task", all(p >= 0 for p in pos), pos)
            add("the current tasks come in ORDER.md order", all(p >= 0 for p in pos) and pos == sorted(pos), pos)
        for w in case.get("backlog_words", []):
            add("the reply mentions the backlog task", bool(re.search(w, low)), reply[-300:])
        for ph in case.get("hidden", []):
            add(f"details not shown ('{ph}')", _find_seq(rt, _toks(ph)) < 0, reply[:200])
        for ph in case.get("shown", []):
            add(f"details shown ('{ph}')", _find_seq(rt, _toks(ph)) >= 0, reply[:200])
        return res

    if kind in ("card-add", "card-first"):
        new_id = case.get("new_id", 1)
        new = [n for n in cards if n not in s_cards]
        nname = file_of(cards, new_id)
        add("exactly one new card file, with the next id", len(new) == 1 and nname in new, sorted(new))
        add("every earlier card is exactly as seeded", not others_same(None), others_same(None))
        f, body = cards.get(nname, ({}, "")) if nname else ({}, "")
        add("the new card is on the current list, status ready", f.get("list") == "current" and f.get("status") == "ready", f)
        add(f"ORDER.md is the old order with {new_id} last", order == s_order + [new_id], order)
        add(f"next-id advanced to {new_id + 1}", next_id == new_id + 1, next_id)
        add("title is at most 70 characters and not empty", 0 < len(f.get("title", "")) <= 70, f.get("title"))
        add("next is at most 60 characters", len(f.get("next", "")) <= 60, f.get("next"))
        add("the title carries the task's subject", bool(re.search(case["title_re"], f.get("title", ""), re.I)), f.get("title"))
        bt = _toks(body)
        for w in case.get("body_words", []):
            add(f"the long remainder's word '{w}' landed in the card's details", w in bt, body[:200])
        return res

    target = case["task"]
    tname = file_of(s_cards, target)
    s_f, s_body = s_cards[tname]
    f, body = cards.get(tname, ({}, ""))
    add(f"task {target}: its card file is kept", tname in cards, sorted(cards))
    add("no card added or removed", sorted(cards) == sorted(s_cards) and others == s_others, sorted(set(cards) ^ set(s_cards)))
    add("no other card changed at all", not others_same(target), others_same(target))
    add(f"task {target}: nothing in its details, Steps or Log lost", not _lost_lines(s_body, body), _lost_lines(s_body, body))

    def same_but(*skip):
        keys = set(s_f) | set(f)
        return all(f.get(k) == s_f.get(k) for k in keys if k not in skip + ("updated",))

    if kind == "card-delete":  # the user's word: done, off ORDER.md, card kept, no removal question
        add(f"task {target}: list is done", f.get("list") == "done", f)
        add(f"task {target} no longer in ORDER.md, the rest in their old order",
            order == [i for i in s_order if i != target], order)
        add("the counter did not go back", next_id is not None and s_next is not None and next_id >= s_next, next_id)
        add(f"task {target}: id, title, owner and created unchanged",
            all(f.get(k) == s_f.get(k) for k in ("id", "title", "owner", "created")), f)
        add("reply does not ask whether to remove it", not _asks_removal(reply), reply[-300:])
        return res

    if kind == "card-waiting":
        wt = _toks(f.get("waiting_on", ""))
        add(f"task {target}: status waiting", f.get("status") == "waiting", f)
        for w in case["waiting_words"]:
            add(f"task {target}: waiting_on names what it waits on ('{w}')", w in wt, f.get("waiting_on"))
        add(f"task {target}: owner and list unchanged", f.get("owner") == s_f.get("owner") and f.get("list") == s_f.get("list"), f)
        add(f"task {target} is still in ORDER.md, once, and the others in their old order",
            order.count(target) == 1 and [i for i in order if i != target] == [i for i in s_order if i != target], order)
        add(f"task {target}: id, title, priority, tags, created unchanged",
            all(f.get(k) == s_f.get(k) for k in ("id", "title", "priority", "tags", "created")), f)
        return res

    if kind == "card-backlog":
        to = case["to"]
        add(f"task {target}: list is {to}", f.get("list") == to, f)
        add(f"task {target}: owner kept ({s_f.get('owner')})", f.get("owner") == s_f.get("owner"), f)
        add(f"task {target}: id, title, created unchanged", all(f.get(k) == s_f.get(k) for k in ("id", "title", "created")), f)
        rest = [i for i in order if i != target]
        add("the other tasks keep their old order", rest == [i for i in s_order if i != target], order)
        if to == "backlog":
            add(f"task {target} is out of ORDER.md", target not in order, order)
        else:
            add(f"task {target} is back in ORDER.md exactly once", order.count(target) == 1, order)
        return res

    if kind == "card-owner":  # only the owner changes
        add(f"task {target}: owner is {case['owner']}", f.get("owner", "").lower() == case["owner"].lower(), f)
        add(f"task {target}: every field except owner (and updated) as seeded: status, next, waiting_on, list",
            same_but("owner"), f)
        add("ORDER.md unchanged: the position is kept", order_text == s_order_text, order)
        add(f"task {target}: details unchanged", body == s_body, body[:200])
        return res

    raise ValueError(f"unknown card case kind: {case['id']}")


def check(case: dict, before: dict, after: dict, run: dict, ctx: dict) -> list[dict]:
    if case["kind"] == "card-details-add":
        return check_card_details_add(case, before, after, run, ctx)
    if case["kind"] == "card-details-replace":
        return check_card_details_replace(case, before, after, run, ctx)
    if case["kind"] in CARD_KINDS:
        return check_cards(case, before, after, run, ctx)
    if case["kind"] in CARD_KINDS_SELF:
        return check_cards_self(case, before, after, run, ctx)
    if case["kind"] in CARD_KINDS_MORE:
        return check_cards_more(case, before, after, run, ctx)
    raise ValueError(f"unknown case kind: {case['id']} ({case['kind']})")
