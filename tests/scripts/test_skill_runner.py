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

# ── with and without the skill (--ablation, #226 A1) ─────────────────────────
with tempfile.TemporaryDirectory() as td:
    fake_repo = Path(td) / "repo"
    (fake_repo / "skills" / "s").mkdir(parents=True)
    (fake_repo / "skills" / "s" / "SKILL.md").write_text(
        '---\nname: s\ndescription: "Does the s thing. Use when asked for s."\n---\n\n# s\n\nSECRET STEP: run s.py\n',
        encoding="utf-8")
    (fake_repo / "skills" / "s" / "reference.md").write_text("more SECRET STEP", encoding="utf-8")
    dest = rst.render_without("s", None, Path(td) / "out" / "s", fake_repo)
    stub = (dest / "SKILL.md").read_text(encoding="utf-8")
    check("without: the stub keeps the name and description", "name: s" in stub
          and 'description: "Does the s thing. Use when asked for s."' in stub, stub)
    check("without: the stub has none of the skill's instructions", "SECRET STEP" not in stub, stub)
    check("without: the skill's other files are withheld", sorted(p.name for p in dest.iterdir()) == ["SKILL.md"],
          sorted(p.name for p in dest.iterdir()))

with tempfile.TemporaryDirectory() as td:
    rst.build_toolset(Path(td), ROOT, without="wiki-lint")
    pages = {p.name for p in Path(td).rglob("*.md")}
    check("without: the skill's own usage page is left out of the toolset", "wiki-lint.md" not in pages)
    check("without: other skills' usage pages stay", "wiki-search.md" in pages, sorted(pages)[:10])

call = lambda name, **inp: {"name": name, "input": inp}  # noqa: E731
esc = rst.escapes({"tool_calls": [
    call("Read", file_path="C:/Users/x/.claude/skills/s/SKILL.md"),
    call("Bash", command=r"cat C:\Users\x\.claude\skills\s\reference.md"),
    call("Glob", pattern="~/.claude/skills/s/*"),
    call("Skill", skill="s"),
    call("Read", file_path="C:/github.com/project-notebooks/notebooks/global-toolset/how-to/llm-wiki/skills/s.md"),
    call("Read", file_path="C:/Users/x/.claude/skills/s-two/SKILL.md"),
    call("Read", file_path="C:/sandbox/skill/s/SKILL.md"),
    call("Skill", skill="other")]}, "s")
check("escape: the installed copy, either slash, and ~ are caught", len([e for e in esc if "skills" in e and "Skill:" not in e]) >= 3, esc)
check("escape: the Skill tool loading the skill is caught", any(e.startswith("Skill:") for e in esc), esc)
check("escape: the real toolset's usage page is caught", any("global-toolset" in e for e in esc), esc)
check("escape: another skill, the sandbox stub and another Skill call are not", len(esc) == 5, esc)

R = lambda ok, names=("x",), escaped=(): {"passed": ok, "checks": [{"name": n, "ok": ok, "detail": ""} for n in names],  # noqa: E731
                                          "cost_usd": 1.0, "wall_s": 60, "turns": 3, "escaped": list(escaped), "permission_denials": []}
abl_cases = [{"id": "p1"}, {"id": "p2"}, {"id": "neg", "should_trigger": False}]
w = {"sonnet": {"p1": R(True), "p2": R(True), "neg": R(True)}}
wo = {"sonnet": {"p1": R(False), "p2": R(True), "neg": R(True)}}
a = rst.ablation(w, wo, abl_cases)
check("ablation: a case passing only with the skill has delta +1", a["rows"][("p1", "sonnet")]["delta"] == 1, a["rows"])
check("ablation: a case passing in both arms has delta 0", a["rows"][("p2", "sonnet")]["delta"] == 0, a["rows"])
check("ablation: a should-not-trigger case is not a positive", a["positives"] == 2, a["positives"])
check("ablation: a check true in both arms on every run is flagged no signal",
      ("p2", "x") in a["weak"] and ("p1", "x") not in a["weak"], a["weak"])
check("ablation: fewer than four positives is flagged", a["below_floor"] is True, a)
wo_esc = {"sonnet": {"p1": R(False, escaped=["Skill: s"]), "p2": R(True), "neg": R(True)}}
a2 = rst.ablation(w, wo_esc, abl_cases)
check("ablation: an escaped without-run voids that row's delta", a2["rows"][("p1", "sonnet")]["delta"] is None
      and a2["void"] == [("p1", "sonnet")], a2)

args = types.SimpleNamespace(skill="no-such-skill", skill_ref=None, effort=None, red_green=None, ablation=True, today=TODAY)
h3 = "\n".join(rst.report_header(args, ["sonnet"], abl_cases, w, {"without": wo, "ablation": a}))
check("ablation header: compared with the without-skill arm", "without the skill" in h3, h3[:300])
check("ablation header: n counts both arms", "with and without the skill: 6 session(s)" in h3, h3)
check("ablation header: cost counts both arms", "$6.00 in all" in h3, h3)
check("ablation header: the four-positive floor is named", "below the four" in h3, h3)
h4 = "\n".join(rst.report_header(args, ["sonnet"], abl_cases, w, {"without": wo_esc, "ablation": a2}))
check("ablation header: a void row is named", "void" in h4 and "p1 (sonnet)" in h4, h4)
with tempfile.TemporaryDirectory() as td:
    rep = rst.write_report(Path(td), args, ["sonnet"], abl_cases, w, [], {"without": wo, "ablation": a}).read_text(encoding="utf-8")
    check("ablation report: the with/without table with each case's delta",
          "## With and without the skill" in rep and "| p1 | with PASS · without FAIL · delta +1 |" in rep, rep[:1500])
    check("ablation report: positives counted per arm", "positives passed 2/2 with the skill vs 1/2 without" in rep, rep)
    check("ablation report: the no-signal checks listed", "- p2: x" in rep, rep)

with tempfile.TemporaryDirectory() as td:
    tmp = Path(td)
    seen = {}
    fake = types.SimpleNamespace(
        setup=lambda model, sandbox, repo: {"sandbox": sandbox, "project": sandbox, "skill_dir": sandbox / "skill" / "s"},
        snapshot=lambda ctx: {}, check=lambda case, b, a, run, ctx: [{"name": "x", "ok": True, "detail": ""}],
        teardown=lambda ctx: None)
    (tmp / "sandbox-m-without").mkdir()
    saved = rst.run_case, rst.render_skill, rst.render_without, rst.build_toolset
    rst.run_case = lambda case, model, ctx, check, out, tools, timeout: {
        "result": {"num_turns": 1, "total_cost_usd": 0.0}, "wall_s": 1.0, "tool_errors": 0, "stderr_tail": "",
        "tool_calls": [{"name": "Skill", "input": {"skill": "s"}}], "text": ""}
    rst.render_skill = lambda *a, **k: seen.setdefault("rendered", []).append(a[0])
    rst.render_without = lambda *a, **k: seen.setdefault("stub", []).append(a[0])
    rst.build_toolset = lambda *a, **k: seen.setdefault("toolset_without", k.get("without"))
    args = types.SimpleNamespace(skill="s", skill_ref=None, effort=None, timeout=10, keep=True, today=TODAY)
    try:
        out = rst.run_model("m", [{"id": "z"}], args, fake, tmp, [], without=True)
    finally:
        rst.run_case, rst.render_skill, rst.render_without, rst.build_toolset = saved
    check("run_model without: the skill is stubbed, not rendered", seen.get("stub") == ["s"] and not seen.get("rendered"), seen)
    check("run_model without: the toolset leaves its page out", seen.get("toolset_without") == "s", seen)
    check("run_model without: the run records its escapes", out["z"]["escaped"] == ["Skill: s"], out["z"])

p = subprocess.run([sys.executable, str(ROOT / "tests" / "skills" / "run_skill_test.py"), "wiki-lint", "--ablation",
                    "--red-green", "HEAD"], capture_output=True, text=True, cwd=ROOT)
check("--ablation with --red-green is refused (exit 2)", p.returncode == 2 and "--ablation" in p.stderr, (p.returncode, p.stderr[-200:]))

failed = [n for ok, n in results if not ok]
for ok, n in results:
    print(("PASS " if ok else "FAIL ") + n)
print(f"\n{len(results) - len(failed)}/{len(results)} passed")
sys.exit(1 if failed else 0)
