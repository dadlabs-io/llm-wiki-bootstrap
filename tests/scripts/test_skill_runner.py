#!/usr/bin/env python3
"""Checks for task #134: the skill test runner's red-then-green mode and fixed report shape. Never shipped.

    python tests/scripts/test_skill_runner.py    # exit 0 = every check passed

From the Ruflo deep dive (2026-10-13): a new case proves a change only if it fails on the old skill
and passes on the new; a run that checked nothing never reads clean; a switched-off case carries an
expiry date; and every write-up states what it was compared with, n, cost and what it does not show.
No model is called: run_case is replaced by a stand-in session.
"""
from __future__ import annotations

import importlib.util
import subprocess
import sys
import tempfile
import types
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("rst", ROOT / "tests" / "skills" / "run_skill_test.py")
rst = importlib.util.module_from_spec(spec)
spec.loader.exec_module(rst)

results: list[tuple[bool, str]] = []


def check(name: str, ok: bool, detail: object = ""):
    results.append((bool(ok), name + (f"  [{detail}]" if not ok and detail != "" else "")))


TODAY = "2026-10-14"

# ── switched off, with a date ────────────────────────────────────────────────
check("off_until after today: off", rst.is_off({"off_until": "2026-11-01"}, TODAY))
check("off_until today or earlier: back on", not rst.is_off({"off_until": "2026-10-14"}, TODAY)
      and not rst.is_off({"off_until": "2026-10-01"}, TODAY))
check("a rule's older in_suite False with no date: off", rst.is_off({"in_suite": False}, TODAY))
check("an off_until on a rule overrides in_suite False once it passes",
      not rst.is_off({"in_suite": False, "off_until": "2026-10-01"}, TODAY))

cases = [{"id": "a"}, {"id": "b", "tags": ["complex"]}, {"id": "c", "off_until": "2026-12-01", "off_reason": "flaky"},
         {"id": "d", "off_until": "2026-10-01"}]
sel, off, skipped = rst.select_cases(cases, None, None, TODAY)
check("default: plain and back-on cases run", [c["id"] for c in sel] == ["a", "d"], [c["id"] for c in sel])
check("default: complex not selected", [c["id"] for c in skipped] == ["b"], [c["id"] for c in skipped])
check("default: a switched-off case is listed apart", [c["id"] for c in off] == ["c"], [c["id"] for c in off])
sel, off, skipped = rst.select_cases(cases, ["c"], None, TODAY)
check("--cases runs a switched-off case by name", [c["id"] for c in sel] == ["c"] and not off)
sel, off, skipped = rst.select_cases(cases, ["nope"], None, TODAY)
check("--cases naming nothing selects zero cases", sel == [])

# ── red then green ───────────────────────────────────────────────────────────
P = lambda ok: {"passed": ok, "checks": [{"name": "x", "ok": ok, "detail": ""}], "cost_usd": 1.0, "wall_s": 60,  # noqa: E731
                "turns": 3}
old = {"sonnet": {"k1": P(False), "k2": P(True), "k3": P(False)}}
new = {"sonnet": {"k1": P(True), "k2": P(True), "k3": P(False), "k4": P(True)}}
v = rst.red_green(old, new)
check("failed on old, passed on new: red-green", v[("k1", "sonnet")] == "red-green", v)
check("passed on old too: green-green", v[("k2", "sonnet")] == "green-green", v)
check("fails on new: new-fails", v[("k3", "sonnet")] == "new-fails", v)
check("no old run: missing", v[("k4", "sonnet")] == "missing", v)

# ── a case that produced no checks fails ─────────────────────────────────────
with tempfile.TemporaryDirectory() as td:
    tmp = Path(td)
    fake = types.SimpleNamespace(
        setup=lambda model, sandbox, repo: {"sandbox": sandbox, "project": sandbox, "skill_dir": sandbox / "skill" / "s"},
        snapshot=lambda ctx: {}, check=lambda case, b, a, run, ctx: [], teardown=lambda ctx: None)
    (tmp / "sandbox-m").mkdir()
    real_run_case, real_render, real_toolset = rst.run_case, rst.render_skill, rst.build_toolset
    rst.run_case = lambda case, model, ctx, check, out, tools, timeout: {
        "result": {"num_turns": 1, "total_cost_usd": 0.0}, "wall_s": 1.0, "tool_errors": 0, "stderr_tail": "",
        "tool_calls": [], "text": ""}
    rst.render_skill = lambda *a, **k: None
    rst.build_toolset = lambda *a, **k: None
    args = types.SimpleNamespace(skill="no-such-skill", skill_ref=None, effort=None, timeout=10, keep=True, today=TODAY)
    try:
        out = rst.run_model("m", [{"id": "z"}], args, fake, tmp, [])
    finally:
        rst.run_case, rst.render_skill, rst.build_toolset = real_run_case, real_render, real_toolset
    rec = out["z"]
    check("a case with no checks does not pass", rec["passed"] is False, rec)
    check("its one check says nothing was checked", rec["checks"][0]["name"] == "the case produced checks", rec["checks"])

# ── the four headings ────────────────────────────────────────────────────────
args = types.SimpleNamespace(skill="no-such-skill", skill_ref=None, effort=None, red_green=None, today=TODAY)
info = {"off": [cases[2]], "not_selected": [cases[1]], "not_covered": ["no case covers --partial-source"],
        "off_rules": [{"id": "read the raw before filing", "in_suite": False}], "back_on": [cases[3]]}
h = "\n".join(rst.report_header(args, ["sonnet"], [{"id": "k1"}, {"id": "k2"}], {"sonnet": {"k1": P(True), "k2": P(True)}}, info))
heads = [l for l in h.splitlines() if l.startswith("## ")]
check("the header has exactly the four headings, in order",
      heads == ["## Compared with", "## n", "## Cost", "## What this does not show"], heads)
check("compared with: says there is no baseline", "no baseline exists" in h, h[:300])
check("n: cases x models and sessions", "2 case(s) x 1 model(s)" in h and ": 2 session(s)" in h, h)
check("cost: the total", "$2.00 in all" in h, h)
check("does not show: one session each can be noise", "can be noise" in h)
check("does not show: cases not run", "Cases not run: b" in h, h)
check("does not show: a switched-off case with its date and reason", "c, until 2026-12-01 (flaky)" in h, h)
check("does not show: an undated switched-off rule asks for a date", "(no date: give it one)" in h, h)
check("does not show: a case back on", "Back on since 2026-10-01" in h, h)
check("does not show: the suite's own not_covered notes", "no case covers --partial-source" in h, h)

args.red_green = "HEAD~1"
info2 = {"old": old, "red_green": v}
h2 = "\n".join(rst.report_header(args, ["sonnet"], [{"id": "k1"}], new, info2))
check("red-green: compared with the old ref", "export of `HEAD~1`" in h2, h2[:300])
check("red-green: n counts both copies", "on the old copy and on the new: 7 session(s)" in h2, h2)
check("red-green: a case that passed on the old copy is named", "do not test this change: k2 (sonnet)" in h2, h2)

# ── export of an old ref ─────────────────────────────────────────────────────
with tempfile.TemporaryDirectory() as td:
    head = subprocess.run(["git", "-C", str(ROOT), "rev-parse", "--short", "HEAD"], capture_output=True, text=True).stdout.strip()
    out = rst.export_tree(head, Path(td) / "old")
    check("export_tree unpacks the ref's skills and scripts",
          (out / "scripts" / "wiki-lint-mechanical.py").is_file() and (out / "skills" / "wiki-lint" / "SKILL.md").is_file())

# ── zero cases exits non-zero ────────────────────────────────────────────────
p = subprocess.run([sys.executable, str(ROOT / "tests" / "skills" / "run_skill_test.py"), "wiki-lint", "--cases", "no-such-case"],
                   capture_output=True, text=True, cwd=ROOT)
check("a run that selects zero cases exits non-zero and says so",
      p.returncode != 0 and "zero cases" in (p.stderr + p.stdout), (p.returncode, p.stderr[-200:]))

failed = [n for ok, n in results if not ok]
for ok, n in results:
    print(("PASS " if ok else "FAIL ") + n)
print(f"\n{len(results) - len(failed)}/{len(results)} passed")
sys.exit(1 if failed else 0)
