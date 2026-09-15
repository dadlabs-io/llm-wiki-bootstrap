"""task-list test suite: sandbox, prompts and checks for run_skill_test.py.

Every case starts from a fresh copy of its seed task.md (prompt() writes it just
before the session starts), so no case depends on another's leftovers or order.
The seeds under fixtures/ are written for the tests. Each check reads the list
with the script's own parser and compares it with the seed.
"""

from __future__ import annotations

import importlib.util
import json
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
            "skill_dir": sandbox / "skill" / "task-list", "scripts": repo / "bootstrap" / "scripts",
            "env": {"PYTHONIOENCODING": "utf-8"}}


def teardown(ctx: dict) -> None:
    shutil.rmtree(ctx["sandbox"], ignore_errors=True)


def snapshot(ctx: dict) -> dict:
    nb = ctx["notebook"]
    return {p.relative_to(nb).as_posix(): (p.stat().st_size, p.stat().st_mtime_ns)
            for p in nb.rglob("*") if p.is_file()}


HEADER = """You are running an automated test of the task-list skill. The skill under test is at {skill}/SKILL.md. Read it and follow it exactly, as if the user had said the message below in this project. Do not use any installed copy of the skill.

The project's wiki is the notebook `{notebook}` at {nb}; this session's persona is `main`. Write only inside {sandbox}. Run scripts as `python <path> ...`, with no environment-variable prefix. The user cannot answer while this runs: where the skill says to ask the user something, ask it in your final reply and stop there, without acting on an answer you do not have.

The user said: """


def prompt(case: dict, ctx: dict) -> str:
    shutil.copy2(HERE / "fixtures" / case.get("seed", DEFAULT_SEED), ctx["task_md"])  # a fresh list per case
    return HEADER.format(skill=ctx["skill_dir"].as_posix(), notebook=NOTEBOOK, nb=ctx["notebook"].as_posix(),
                         sandbox=ctx["sandbox"].as_posix()) + case["say"]


def check(case: dict, before: dict, after: dict, run: dict, ctx: dict) -> list[dict]:
    mod = _tasks(ctx["scripts"])
    res = []

    def add(name, ok, detail=""):
        res.append({"name": name, "ok": bool(ok), "detail": str(detail)[:300]})

    def board(text):
        b = mod.Board(text)
        m = mod.MARKER_RE.search(text)
        return b, {r["id"]: {**r, "owner": s["name"]} for s in b.sections for r in s["rows"]}, \
            (int(m.group(1)) if m else None)

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

    raise ValueError(f"unknown case kind: {case['id']}")
