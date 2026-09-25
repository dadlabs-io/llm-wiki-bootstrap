"""wiki-triage test suite: sandbox, prompts and checks for run_skill_test.py.

A throwaway registry: `research` (the shared notebook being triaged, no bot), `proj`
(this session's project, bot proj-bot) and `other` (bot other-bot). The session runs
from proj's folder, so buckets read by proj-bot are its own.

The shared config has four buckets: main (proj-bot), memory (proj-bot), agents
(other-bot), money (mark). The five sources are written for the test, as local files
queued with wiki-list-add.py, so nothing touches the network:
- vector-index-tuning -> memory; subagent-harness -> agents; side-hustles -> money;
- gpu-cluster-costs fits no bucket -> main; memory-for-subagents fits two -> main.
Items for another reader (agents, money) must carry a captured raw.
"""

from __future__ import annotations

import json
import os
import re
import shutil
import stat
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
NOTEBOOK = "research"
EXTRA_SKILLS = ["wiki-update"]
DISALLOWED_TOOLS = ["Skill"]

SHARED = """---
buckets:
  - folder: main
    purpose: Anything relevant that fits no other bucket, or fits two equally
    reader: proj-bot
  - folder: memory
    purpose: Agent memory, vector stores, retrieval and RAG
    reader: proj-bot
  - folder: agents
    purpose: Building agents, harnesses, subagents and orchestration
    reader: other-bot
  - folder: money
    purpose: Making money with AI (side hustles, digital products)
    reader: mark
---

# Intake buckets for the research notebook

Each source gets one bucket. Readers ingest their own buckets; mark reviews money himself.
"""
NO_MAIN = SHARED.replace("  - folder: main\n    purpose: Anything relevant that fits no other bucket, or fits two equally\n"
                         "    reader: proj-bot\n", "")


def _rmtree(path: Path) -> None:
    def onexc(func, target, exc):
        try:
            os.chmod(target, stat.S_IWRITE)
            func(target)
        except OSError:
            pass
    if path.exists():
        shutil.rmtree(path, onexc=onexc)


def prepare_fixtures(repo: Path, refresh: bool = False) -> list[dict]:
    return []  # every source is written for the test


def setup(model: str, sandbox: Path, repo: Path) -> dict:
    _rmtree(sandbox)
    reg = {"notebooks": {
        NOTEBOOK: {"root": f"notebooks/{NOTEBOOK}"},
        "proj": {"root": "notebooks/proj", "discord": {"bot_name": "proj-bot", "user_id": "111"}},
        "other": {"root": "notebooks/other", "discord": {"bot_name": "other-bot", "user_id": "222"}},
    }}
    sandbox.mkdir(parents=True)
    (sandbox / "linked-notebooks.json").write_text(json.dumps(reg, indent=2), encoding="utf-8")
    for n in ("proj", "other"):
        (sandbox / "notebooks" / n / "wiki").mkdir(parents=True)
    shutil.copytree(HERE / "fixtures" / "sources", sandbox / "sources")
    cfg = json.dumps({"tool": "claude-code", "project_name": "proj", "notebook": "proj", "persona": "main",
                      "registry": (sandbox / "linked-notebooks.json").as_posix()}, indent=2)
    project = sandbox / "project"
    for d in (project, sandbox):
        (d / ".claude").mkdir(parents=True, exist_ok=True)
        (d / ".claude" / "wiki-config.json").write_text(cfg, encoding="utf-8")
    return {"sandbox": sandbox, "project": project, "notebook": sandbox / "notebooks" / NOTEBOOK,
            "skill_dir": sandbox / "skill" / "wiki-triage", "scripts": repo / "bootstrap" / "scripts",
            "env": {"PYTHONIOENCODING": "utf-8"}}


def teardown(ctx: dict) -> None:
    _rmtree(ctx["sandbox"])


def snapshot(ctx: dict) -> dict:
    nb = ctx["notebook"]
    if not nb.exists():
        return {}
    return {p.relative_to(nb).as_posix(): (p.stat().st_size, p.stat().st_mtime_ns) for p in nb.rglob("*") if p.is_file()}


def _queue(ctx: dict, name: str) -> Path:
    src = (ctx["sandbox"] / "sources" / f"{name}.md").as_posix()
    p = subprocess.run([sys.executable, str(ctx["scripts"] / "wiki-list-add.py"), "--topic", NOTEBOOK,
                        "--source", src, "--added-by", "skilltest"], cwd=ctx["project"], capture_output=True,
                       text=True, encoding="utf-8", env={**os.environ, **ctx["env"]})
    m = re.search(r"^Queued:\s*(.+)$", p.stdout, re.M)
    if p.returncode != 0 or not m:
        raise RuntimeError(f"could not queue {name}: {p.stdout}{p.stderr}")
    return Path(m.group(1).strip())


HEADER = """You are running an automated test of the wiki-triage skill. The skill under test is at {skill}/SKILL.md; the wiki-update skill it refers to is at {skills}/wiki-update/. Read the skill and follow it exactly, as if the user had said the message below in this project. Do not use any installed copy of any skill; the Skill tool is not available.

This project's notebook is `proj`; the notebook the user means is `{notebook}`, at {nb}. Run scripts as `python <path> ...`, with no environment-variable prefix, and write only inside {sandbox}. This session has no Discord channel. The user cannot reply while this runs: where the skill says to ask or tell someone, say it in your final message.

The user said: """


def prompt(case: dict, ctx: dict) -> str:
    nb = ctx["notebook"]
    _rmtree(nb)
    for d in ("wiki", "raw", "_inbox/pending", "_inbox/done"):
        (nb / d).mkdir(parents=True, exist_ok=True)
    (nb / "wiki" / "README.md").write_text("# research\n\nA shared research notebook (test).\n", encoding="utf-8")
    intake = nb / "_inbox" / "intake"
    if case["config"] in ("shared", "no-main"):
        intake.mkdir(parents=True)
        (intake / "README.md").write_text(SHARED if case["config"] == "shared" else NO_MAIN, encoding="utf-8")
    ctx["tickets"] = {}
    for name in case.get("pending", []):
        ctx["tickets"][name] = _queue(ctx, name).name
    for name, folder in (case.get("dropped") or {}).items():
        t = _queue(ctx, name)
        (intake / folder).mkdir(parents=True, exist_ok=True)
        t.rename(intake / folder / t.name)
        ctx["tickets"][name] = t.name
    ctx["before_case"] = snapshot(ctx)
    return HEADER.format(skill=ctx["skill_dir"].as_posix(), skills=ctx["skill_dir"].parent.as_posix(),
                         notebook=NOTEBOOK, nb=nb.as_posix(), sandbox=ctx["sandbox"].as_posix()) + case["say"]


def _where(nb: Path, ticket: str) -> str:
    if (nb / "_inbox" / "pending" / ticket).is_file():
        return "pending"
    hits = list((nb / "_inbox" / "intake").glob(f"*/{ticket}")) if (nb / "_inbox" / "intake").is_dir() else []
    return hits[0].parent.name if len(hits) == 1 else ("missing" if not hits else "several")


def _front(path: Path) -> dict:
    m = re.match(r"\A---\s*\n(.*?)\n---", path.read_text(encoding="utf-8", errors="replace"), re.S)
    return dict(l.split(":", 1) for l in (m.group(1).splitlines() if m else []) if ":" in l)


def check(case: dict, before: dict, after: dict, run: dict, ctx: dict) -> list[dict]:
    res: list[dict] = []

    def add(name, ok, detail=""):
        res.append({"name": name, "ok": bool(ok), "detail": str(detail)[:300]})

    r = run["result"]
    add("session completed", r.get("subtype") == "success" and not r.get("is_error"),
        r.get("subtype") or run.get("stderr_tail") or "no result event")
    errs = run.get("error_texts") or {}
    other = [d for d in (r.get("permission_denials") or []) if not (isinstance(d, dict) and (
        d.get("tool_name") == "Skill" or "read-guard:" in str(errs.get(d.get("tool_use_id"), ""))))]
    add("no permission denials (read-guard and the blocked Skill tool counted apart)", not other,
        [d.get("tool_name") if isinstance(d, dict) else d for d in other])

    nb, text = ctx["notebook"], run["text"].lower()
    now = snapshot(ctx)
    new = sorted(set(now) - set(ctx["before_case"]))
    for name, want in case["expect"].items():
        got = _where(nb, ctx["tickets"][name])
        add(f"{name} -> {want}", got == want, got)

    entries = [k for k in new if (k.startswith("wiki/") or k.startswith("_inbox/proposed/")) and k.endswith(".md")]
    add("nothing ingested or staged", not entries, entries)
    rk = "_inbox/intake/README.md"
    add("intake README untouched", now.get(rk) == ctx["before_case"].get(rk))
    log = nb / "_inbox" / "intake" / "triage-log.md"
    rows = [l for l in log.read_text(encoding="utf-8").splitlines() if l.startswith("| ") and not l.startswith("| Date")] \
        if log.is_file() else []
    moved = [n for n, w in case["expect"].items() if w != "pending" and n not in (case.get("dropped") or {})]
    add("one triage-log row per routed item", len(rows) == len(moved), f"{len(rows)} rows for {len(moved)} items")

    if case["id"] == "shared-five":
        for name in ("subagent-harness", "side-hustles"):
            t = nb / "_inbox" / "intake" / case["expect"][name] / ctx["tickets"][name]
            rp = _front(t).get("raw_path", "").strip() if t.is_file() else ""
            add(f"{name}: raw captured for its other reader", bool(rp) and (nb / rp).is_file(), rp or "no raw_path")
        add("report names other-bot's items for telling", "other-bot" in text or "<@222>" in text)
        add("report points the user at the money bucket", "money" in text)
    if case["id"] == "user-drop":
        add("says there was nothing to triage", bool(re.search(r"nothing|empty|no (item|ticket|source)", text)))
    if case["id"] == "bad-config":
        add("stops on the config problem and names it", "main" in text and bool(
            re.search(r"problem|missing|no .main|catch-all", text)))
    return res
