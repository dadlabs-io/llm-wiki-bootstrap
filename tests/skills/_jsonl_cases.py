"""Shared checker for suites whose cases came from agent-builder's eval format (2026-09-30).

The skill-suggestions skills moved here from agent-builder's library with their eval cases.
Those cases are kept word for word in each suite's cases.json (one object per case: `prompt`,
`setup.files`, `setup.git`, `setup.fixture_dir`, `should_trigger`, `expect`, `questions`,
`judge`), and this module runs them through our runner (run_skill_test.py). What carries over
and what does not:

- `expect.files_exist` / `files_absent` / `file_contains` / `regex` (on the session's reply) /
  `commands` (run in the case's project folder, exit code compared): checked as written.
- `expect.forbidden_calls` on the Skill tool: our runner never loads a skill through the Skill
  tool (the suite blocks it, so an installed copy can never answer), so "the skill was not
  invoked" is checked as "the session did not run the skill's script and did not open its
  SKILL.md". The files_absent/regex checks beside it carry the rest.
- `questions`: answered YES or NO by a judge model (Sonnet) from the session's reply,
  compared with `expect`.
- `judge` (the free-text rubric) and the without-skill ablation runs are not ported: our
  standard is a baseline per model with the skill, and every rubric's testable parts are
  already in `expect` and `questions`.

Each case gets a fresh project folder built from its own setup, so no case depends on another.
"""

from __future__ import annotations

import glob
import json
import os
import re
import shutil
import stat
import subprocess
from pathlib import Path

ALLOWED_TOOLS = ["Read", "Write", "Edit", "Glob", "Grep", "Bash(python:*)", "Bash(python3:*)", "Bash(uv:*)", "Bash(git:*)",
                 "Bash(ls:*)", "Bash(cat:*)", "Bash(cd:*)", "Bash(find:*)", "Bash(pwd:*)"]
DISALLOWED_TOOLS = ["Skill"]
JUDGE_MODEL = "sonnet"  # Haiku misread a clear "not proposed again" as YES (run 20260930-195308)

HEADER = """You are working in a project at {project}. One skill is available to you in this session: `{skill}`, at {skill_dir}/SKILL.md (its scripts are in that folder). Its description: "{description}" When the request below is one the skill's description covers, read the SKILL.md in full and follow it exactly; when it is not, do not use the skill. Do not use any installed copy of a skill. Write only inside {project}. The user cannot reply while this runs.

{prompt}"""


def _rmtree(path: Path) -> None:
    def onexc(func, target, exc):
        try:
            os.chmod(target, stat.S_IWRITE)
            func(target)
        except OSError:
            pass
    shutil.rmtree(path, onexc=onexc)


def _git(cwd: Path, *args: str) -> str:
    return subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True, timeout=60).stdout


def make_setup(skill: str, here: Path):
    def setup(model: str, sandbox: Path, repo: Path) -> dict:
        if sandbox.exists():
            _rmtree(sandbox)
        project = sandbox / "project"
        project.mkdir(parents=True)
        return {"sandbox": sandbox, "project": project, "skill": skill, "here": here,
                "skill_dir": sandbox / "skill" / skill, "env": {"PYTHONIOENCODING": "utf-8"}}
    return setup


def prepare_fixtures(repo: Path, refresh: bool = False) -> list:
    return []  # every fixture is written for the test and committed beside the cases


def teardown(ctx: dict) -> None:
    try:
        _rmtree(ctx["sandbox"])
    except OSError:
        pass


def snapshot(ctx: dict) -> dict:
    p = ctx["project"]
    return {f.relative_to(p).as_posix(): f.stat().st_size for f in p.rglob("*")
            if f.is_file() and ".git" not in f.parts}


def _reset_project(case: dict, ctx: dict) -> None:
    project = ctx["project"]
    for child in list(project.iterdir()):
        _rmtree(child) if child.is_dir() else child.unlink()
    setup = case.get("setup") or {}
    fixture = setup.get("fixture_dir")
    if fixture:
        src = ctx["here"] / fixture
        shutil.copytree(src, project, dirs_exist_ok=True)
    for rel, body in (setup.get("files") or {}).items():
        out = project / rel
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(body, encoding="utf-8", newline="\n")
    if setup.get("git"):
        _git(project, "init", "-q")
        _git(project, "config", "user.email", "test@example.invalid")
        _git(project, "config", "user.name", "Skill Test")
        _git(project, "config", "core.autocrlf", "false")  # line endings never read as a change (Windows)
        _git(project, "config", "core.longpaths", "true")  # a deep sandbox path must not make `git add` skip files
        _git(project, "add", "-A")  # the library's files staged, as agent-builder's runner does


def prompt(case: dict, ctx: dict) -> str:
    _reset_project(case, ctx)
    fm = (ctx["skill_dir"] / "SKILL.md").read_text(encoding="utf-8").split("---")[1]
    m = re.search(r'^description:\s*"?(.*?)"?\s*$', fm, re.M)
    return HEADER.format(project=ctx["project"].as_posix(), skill=ctx["skill"], description=m.group(1) if m else "",
                         skill_dir=ctx["skill_dir"].as_posix(), prompt=case["prompt"])


def _claude_exe() -> str:
    found = shutil.which("claude")
    if found and found.lower().endswith((".cmd", ".bat")):
        exe = Path(found).parent / "node_modules" / "@anthropic-ai" / "claude-code" / "bin" / "claude.exe"
        if exe.is_file():
            return str(exe)
    return found or "claude"


def _judge(question: str, reply: str) -> tuple[bool | None, str]:
    """The majority of up to three judge calls (stops once two agree). One call alone flipped: on the same
    reply it said NO once and YES twice (2026-10-04, replay-freeze-step-label)."""
    votes, raws = [], []
    for _ in range(3):
        v, raw = _judge_once(question, reply)
        votes.append(v)
        raws.append(raw)
        for answer in (True, False):
            if votes.count(answer) >= 2:
                return answer, " / ".join(raws)
    return None, " / ".join(raws)


def _judge_once(question: str, reply: str) -> tuple[bool | None, str]:
    """YES/NO from a small model reading only the session's reply; None when it gave neither."""
    ask =("Below is the final reply an AI assistant gave in a session, then a question about it. "
           "Answer with exactly one word, YES or NO.\n\n<reply>\n" + reply[-12000:] +
           "\n</reply>\n\nQuestion: " + question)
    env = {k: v for k, v in os.environ.items() if k != "ANTHROPIC_API_KEY"}
    try:
        p = subprocess.run([_claude_exe(), "-p", "--model", JUDGE_MODEL, "--output-format", "text"], input=ask,
                           capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=180, env=env)
    except subprocess.TimeoutExpired:
        return None, "judge timed out"
    out = (p.stdout or "").strip().upper()
    m = re.search(r"\b(YES|NO)\b", out)
    return (m.group(1) == "YES") if m else None, out[:80]


def _used_skill(run: dict, ctx: dict) -> list[str]:
    """Calls that show the session used the skill: read its SKILL.md or ran a script from its folder."""
    hits = []
    skill_dir = ctx["skill_dir"].as_posix().lower()
    for c in run["tool_calls"]:
        blob = json.dumps(c.get("input") or {}).replace("\\\\", "/").lower()
        if skill_dir in blob:  # only the rendered skill's folder: the results path also carries the skill's name
            hits.append(f"{c.get('name')}: {blob[:120]}")
    return hits


def check(case: dict, before: dict, after: dict, run: dict, ctx: dict) -> list[dict]:
    res: list[dict] = []
    project = ctx["project"]
    exp = case.get("expect") or {}
    text = run["text"]

    def add(name, ok, detail=""):
        res.append({"name": name, "ok": bool(ok), "detail": str(detail)[:300]})

    r = run["result"]
    add("session completed", r.get("subtype") == "success" and not r.get("is_error"),
        r.get("subtype") or run.get("stderr_tail") or "no result event")

    used = _used_skill(run, ctx)
    if case.get("should_trigger") is False:
        add("the skill is not used (SKILL.md not opened, no script run)", not used, used[:3])
    else:
        add("the skill is used (SKILL.md read or its script run)", bool(used), "no call touched the skill")

    for rel in exp.get("files_exist", []):
        add(f"exists: {rel}", (project / rel).exists())
    for rel in exp.get("files_absent", []):
        add(f"absent: {rel}", not (project / rel).exists())
    for rel, needles in (exp.get("file_contains") or {}).items():
        f = project / rel
        body = f.read_text(encoding="utf-8", errors="replace") if f.is_file() else ""
        missing = [n for n in needles if n not in body]
        add(f"{rel} contains {len(needles)} expected text(s)", f.is_file() and not missing, missing or "file missing")
    for i, pattern in enumerate(exp.get("regex", []), 1):
        add(f"reply matches pattern {i}: {pattern[:60]}", re.search(pattern, text) is not None)
    for i, c in enumerate(exp.get("commands", []), 1):
        p = subprocess.run(c["cmd"], shell=True, cwd=project, capture_output=True, text=True,
                           encoding="utf-8", errors="replace", timeout=120)
        add(f"command {i} exits {c.get('exit', 0)}", p.returncode == c.get("exit", 0),
            ((p.stdout or "") + (p.stderr or "")).strip()[-250:])
    for q in case.get("questions", []):
        verdict, raw = _judge(q["q"], text)
        add(f"judge: {q['q'][:90]} -> {'YES' if q['expect'] else 'NO'}", verdict is q["expect"], raw)
    return res
