#!/usr/bin/env python3
"""Checks for the `synthesis` scope of scripts/wiki-cycle-scope.py (task #176). Never shipped.

    python tests/scripts/test_synthesis_scope.py    # exit 0 = every check passed

Mark, 2026-10-19: agentic-design's best practices had not taken in 107 research entries,
because synthesis ran only in `--full` and the six cycles since 10-12 were `--ingest-only`.
Synthesis now runs in every cycle that ingests, over the research entries promoted since the
last synthesis the user answered. A synthesis nobody could answer (`awaiting_approval`) does
not move the cut-off, so its entries come round again.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[2] / "scripts" / "wiki-cycle-scope.py"
results: list[tuple[bool, str]] = []


def check(name: str, ok: bool, detail: object = ""):
    results.append((bool(ok), name + (f"  [{detail}]" if not ok and detail != "" else "")))


def entry(title: str, extra: str = "") -> str:
    return (f"---\ntitle: \"{title}\"\ndate: 2026-09-01\ntier: 3\nconfidence: medium\nlast_reviewed: 2026-09-01\n"
            f"review_after: 2026-11-01\ntags: [a, b, c]\n{extra}---\n\n# {title}\n\n## TL;DR\n\nBody.\n")


with tempfile.TemporaryDirectory() as td:
    tmp = Path(td)
    nb = tmp / "notebooks" / "t"
    res = nb / "wiki" / "research" / "tooling"
    bp = nb / "wiki" / "project" / "best-practices"
    for d in (res, bp, nb / "wiki" / "project" / "decisions", nb / "_inbox" / "proposed"):
        d.mkdir(parents=True)
    (tmp / "linked-notebooks.json").write_text(json.dumps({"notebooks": {"t": {"root": "notebooks/t"}}}),
                                               encoding="utf-8")
    proj = tmp / "project"
    (proj / ".claude").mkdir(parents=True)
    (proj / ".claude" / "wiki-config.json").write_text(json.dumps(
        {"notebook": "t", "registry": (tmp / "linked-notebooks.json").as_posix()}), encoding="utf-8")

    def git(*a, date=None):
        env = {**os.environ}
        if date:
            env.update(GIT_AUTHOR_DATE=date, GIT_COMMITTER_DATE=date)
        return subprocess.run(["git", "-C", str(tmp), *a], capture_output=True, text=True, env=env, check=True)

    def run(*a):
        return subprocess.run([sys.executable, str(SCRIPT), "--topic", "t", *a], cwd=proj, capture_output=True,
                              text=True, encoding="utf-8", env={**os.environ, "PYTHONIOENCODING": "utf-8"})

    def synth(day: str, status: str):
        rf = nb / "_inbox" / "reports" / day / f"{day}-01"
        rf.mkdir(parents=True, exist_ok=True)
        (rf / "synthesis.json").write_text(json.dumps({"step": "synthesis", "status": status,
                                                       "timestamp": f"{day}T12:00:00-04:00"}), encoding="utf-8")

    git("init", "-q")
    git("config", "user.name", "t")
    git("config", "user.email", "t@example.com")
    (res / "r-old.md").write_text(entry("r-old"), encoding="utf-8")
    (bp / "skills-best-practices.md").write_text(entry("Skills"), encoding="utf-8")
    (bp / "README.md").write_text("# readme\n", encoding="utf-8")
    git("add", "-A")
    git("commit", "-qm", "old", date="2026-09-01T10:00:00-04:00")
    synth("2026-09-10", "completed")
    git("add", "-A")
    git("commit", "-qm", "synth", date="2026-09-10T12:00:00-04:00")
    (res / "r-new.md").write_text(entry("r-new"), encoding="utf-8")
    (res / "r-retired.md").write_text(entry("r-retired", "superseded_by: r-new.md\n"), encoding="utf-8")
    (nb / "wiki" / "project" / "decisions" / "d.md").write_text(entry("d"), encoding="utf-8")
    git("add", "-A")
    git("commit", "-qm", "new", date="2026-09-15T09:00:00-04:00")
    (nb / "_inbox" / "proposed" / "staged.md").write_text(entry("staged"), encoding="utf-8")
    rf = nb / "_inbox" / "reports" / "2026-09-24" / "2026-09-24-01"

    def scope():
        f = rf / "synthesis-scope.txt"
        return [l for l in f.read_text(encoding="utf-8").splitlines() if l and not l.startswith("#")] if f.is_file() else None

    p = run("synthesis", "--run-folder", str(rf))
    s = scope()
    check("exit 0", p.returncode == 0, p.stderr[-300:])
    check("only the research entry promoted since the last synthesis",
          s == ["wiki/research/tooling/r-new.md"], s)
    check("prints the count and the cut-off", "synthesis scope: 1" in p.stdout and "2026-09-10T12:00:00-04:00" in p.stdout,
          p.stdout)

    synth("2026-09-20", "awaiting_approval")
    p = run("synthesis", "--run-folder", str(rf))
    check("a synthesis nobody answered does not move the cut-off", scope() == ["wiki/research/tooling/r-new.md"]
          and "2026-09-10T12:00:00-04:00" in p.stdout, (scope(), p.stdout))

    synth("2026-09-21", "completed")
    p = run("synthesis", "--run-folder", str(rf))
    check("an answered synthesis after them empties the scope", scope() == [], (scope(), p.stdout))

    p = run("synthesis", "--run-folder", str(rf), "--all")
    check("--all: every live research entry, never a retired one or a project page",
          scope() == ["wiki/research/tooling/r-new.md", "wiki/research/tooling/r-old.md"], scope())

    for f in (nb / "_inbox" / "reports").rglob("synthesis.json"):
        f.unlink()
    p = run("synthesis", "--run-folder", str(rf))
    check("no earlier synthesis: every live research entry, and says so",
          len(scope() or []) == 2 and "no earlier synthesis" in p.stdout, p.stdout)

    (bp / "skills-best-practices.md").unlink()
    p = run("synthesis", "--run-folder", str(rf))
    check("no best-practices pages: an empty scope that says why, exit 0",
          p.returncode == 0 and scope() == [] and "no best-practices pages" in p.stdout, p.stdout)
    f = rf / "synthesis-scope.txt"
    check("an empty scope is never a zero-byte file", f.is_file() and f.stat().st_size > 0)

failed = [n for ok, n in results if not ok]
for ok, n in results:
    print(("PASS " if ok else "FAIL ") + n)
print(f"\n{len(results) - len(failed)}/{len(results)} passed")
sys.exit(1 if failed else 0)
