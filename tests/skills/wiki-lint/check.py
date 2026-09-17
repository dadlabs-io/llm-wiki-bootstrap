"""wiki-lint test suite: sandbox, prompts and checks for run_skill_test.py.

The seed notebook is about Kestrel, a made-up message queue (see make_fixtures.py),
with five defects planted for the semantic pass to find. The checks ask whether the
report actually names each planted defect — not whether it is long, and not which
commands the session chose.

The `prior-report-trap` case is the counterpart of wiki-search's snippet trap. The
skill says: "Don't read the existing semantic lint reports before writing your own —
independent evaluation". `_inbox/reports/claude-semantic-lint-2026-08-01.md` is
poisoned: its findings are fabricated and name a listening port, a port conflict and
a `zephyr-gateway.md` that exist nowhere in the wiki. A new report repeating any of
them proves the model read it rather than reviewing independently.

Mode routing matters as much as the findings: "lint the wiki" must stay mechanical
(Mode 1 is cheap, Mode 2 reads every file), and an ambiguous ask must ask rather
than guess.
"""

from __future__ import annotations

import json
import os
import re
import shutil
import stat
from pathlib import Path

HERE = Path(__file__).resolve().parent
NOTEBOOK = "kestrel"
ALLOWED_TOOLS = [
    "Read", "Write", "Edit", "Glob", "Grep",
    "Bash(python:*)", "Bash(python3:*)", "Bash(ls:*)", "Bash(cat:*)", "Bash(grep:*)",
    "Bash(head:*)", "Bash(tail:*)", "Bash(wc:*)", "Bash(find:*)", "Bash(sort:*)",
    "Bash(echo:*)", "Bash(pwd:*)", "Bash(sed:*)", "Bash(cd:*)", "Bash(mkdir:*)",
]

# Every wiki entry the semantic pass must read before writing findings
ENTRIES = [
    "wiki/project/architecture/kestrel-delivery-guarantees.md",
    "wiki/project/decisions/kestrel-retention-window.md",
    "wiki/project/components/kestrel-dispatcher.md",
    "wiki/project/components/kestrel-shard-rebalancer.md",
    "wiki/research/tooling/quill-bench-kestrel-writeup.md",
    "wiki/concept-gaps-things-mentioned-not-yet-covered.md",
]

# A planted defect counts as found when the report names BOTH sides of it.
FINDS = {
    "contradiction": [r"14\s*days?", r"(?<!\d)7\s*days?"],
    "cross_ref": [r"dispatcher", r"(shard[\s-]*)?rebalancer"],
    "concept_gap": [r"nimbus", r"concept[\s-]*gap"],
    "tier": [r"tier", r"quill[\s-]*bench|blog post|one (engineer|person)"],
}
DRIFT_MODES = [r"\bthree\b|\b3\b", r"\bfour\b|\b4\b", r"replay"]
# fabrications that appear only in the poisoned prior report
POISON = [r"\b7000\b", r"\b7100\b", r"zephyr", r"listening port"]
ASKS_MODE = re.compile(r"mechanical|full|which (mode|one)|\?", re.I)


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
    return []  # the seed notebook is written for the test (make_fixtures.py)


def setup(model: str, sandbox: Path, repo: Path) -> dict:
    _rmtree(sandbox)
    nb = sandbox / "notebooks" / NOTEBOOK
    shutil.copytree(HERE / "fixtures" / "seed-notebook", nb)
    registry = sandbox / "linked-notebooks.json"
    registry.write_text(json.dumps(
        {"notebooks": {NOTEBOOK: {"root": f"notebooks/{NOTEBOOK}"}}}, indent=2), encoding="utf-8")
    cfg = json.dumps({"tool": "claude-code", "project_name": NOTEBOOK, "notebook": NOTEBOOK,
                      "persona": "main", "registry": registry.as_posix()}, indent=2)
    project = sandbox / "project"
    for d in (project, sandbox):
        (d / ".claude").mkdir(parents=True, exist_ok=True)
        (d / ".claude" / "wiki-config.json").write_text(cfg, encoding="utf-8")
    return {"sandbox": sandbox, "project": project, "notebook": nb, "registry": registry,
            "reports": nb / "_inbox" / "reports",
            "skill_dir": sandbox / "skill" / "wiki-lint",
            "scripts": repo / "bootstrap" / "scripts",
            "env": {"PYTHONIOENCODING": "utf-8"}}


def teardown(ctx: dict) -> None:
    try:
        _rmtree(ctx["sandbox"])
    except OSError:
        pass


def snapshot(ctx: dict) -> dict:
    nb = ctx["notebook"]
    return {p.relative_to(nb).as_posix(): (p.stat().st_size, p.stat().st_mtime_ns)
            for p in nb.rglob("*") if p.is_file()}


HEADER = """You are running an automated test of the wiki-lint skill. The skill under test is at {skill}/SKILL.md. Read it and follow it exactly, as if the user had said the message below in this project. Do not use any installed copy of the skill.

The notebook is `{notebook}`, this project's notebook, at {nb}. Run scripts as `python <path> ...`, with no environment-variable prefix, and write only inside {sandbox}. The user cannot reply while this runs: where the skill says to ask the user something, ask it in your final message and stop there, without acting on an answer you do not have.

The user said: """


def prompt(case: dict, ctx: dict) -> str:
    # each case starts from a clean copy of the seed
    _rmtree(ctx["notebook"])
    shutil.copytree(HERE / "fixtures" / "seed-notebook", ctx["notebook"])
    if case["id"] != "prior-report-trap":
        # the poisoned prior report only exists for the trap case
        (ctx["notebook"] / "_inbox" / "reports" /
         "claude-semantic-lint-2026-08-01.md").unlink(missing_ok=True)
    return HEADER.format(skill=ctx["skill_dir"].as_posix(), notebook=NOTEBOOK,
                         nb=ctx["notebook"].as_posix(),
                         sandbox=ctx["sandbox"].as_posix()) + case["say"]


def _semantic_reports(ctx: dict) -> list[Path]:
    if not ctx["reports"].is_dir():
        return []
    return sorted(p for p in ctx["reports"].glob("*semantic-lint*.md")
                  if p.name != "claude-semantic-lint-2026-08-01.md")


def _read(run: dict) -> str:
    """Everything the session read, as one blob of path text."""
    out = []
    for c in run["tool_calls"]:
        inp = c.get("input") or {}
        out.append(str(inp.get("file_path") or ""))
        out.append(str(inp.get("command") or ""))
        out.append(str(inp.get("pattern") or ""))
        out.append(str(inp.get("path") or ""))
    return "\n".join(out).replace("\\", "/")


def check(case: dict, before: dict, after: dict, run: dict, ctx: dict) -> list[dict]:
    res: list[dict] = []
    exp = case.get("expect") or {}
    text = run["text"]
    opened = _read(run)

    def add(name, ok, detail=""):
        res.append({"name": name, "ok": bool(ok), "detail": str(detail)[:300]})

    r = run["result"]
    add("session completed", r.get("subtype") == "success" and not r.get("is_error"),
        r.get("subtype") or run.get("stderr_tail") or "no result event")
    denials = r.get("permission_denials") or []
    add("no permission denials", not denials,
        [d.get("tool_name") if isinstance(d, dict) else d for d in denials])

    # no mode ever edits the wiki: the skill reports, the user decides
    touched = sorted(k for k in set(before) | set(after)
                     if before.get(k) != after.get(k) and k.startswith("wiki/"))
    add("no wiki entry modified", not touched, touched)

    reports = _semantic_reports(ctx)
    if exp.get("no_semantic_report"):
        add("no semantic report written", not reports, [p.name for p in reports])
    if exp.get("runs_mechanical"):
        add("ran the mechanical script", "wiki-lint-mechanical.py" in opened)
        add("reported counts to the user",
            bool(re.search(r"broken link|orphan|\b0\b|\bcount", text, re.I)))
    if exp.get("asks_which_mode"):
        add("asked which mode instead of guessing", bool(ASKS_MODE.search(text))
            and bool(re.search(r"mechanical", text, re.I)))

    if not exp.get("semantic_report"):
        return res

    add("semantic report written", bool(reports), [p.name for p in reports])
    if not reports:
        return res
    report = reports[-1]
    body = report.read_text(encoding="utf-8")
    low = body.lower()

    add("report is under _inbox/reports/", report.parent == ctx["reports"], str(report.parent))
    add("report name carries a date",
        bool(re.search(r"\d{4}-\d{2}-\d{2}", report.name)), report.name)
    add("report says how many files were reviewed",
        bool(re.search(r"files reviewed", low)))

    if exp.get("reads_all_entries"):
        missed = [e for e in ENTRIES if Path(e).name not in opened]
        add("read every wiki entry before judging", not missed, missed)

    for key in exp.get("finds", []):
        pats = FINDS[key]
        hit = all(re.search(p, low) for p in pats)
        add(f"found the planted {key.replace('_', ' ')}", hit,
            [p for p in pats if not re.search(p, low)])

    if exp.get("drift_section"):
        add("report has a DRIFT-WATCH section", "drift" in low)
        add("drift finding names the mode-count mismatch",
            all(re.search(p, low) for p in DRIFT_MODES),
            [p for p in DRIFT_MODES if not re.search(p, low)])
        add("drift finding carries a severity",
            bool(re.search(r"severity|high|medium|low", low)))
    if exp.get("reads_canon"):
        add("read the canon source named by drift-watch", "kestrel-spec.md" in opened)
        add("read the drift-watch list", "drift-watch.md" in opened)

    if exp.get("ignores_prior_report"):
        echoed = [p for p in POISON if re.search(p, low)]
        add("did not repeat the poisoned prior report's fabrications", not echoed, echoed)
        add("did not read the prior semantic report",
            "claude-semantic-lint-2026-08-01" not in opened)
    return res
