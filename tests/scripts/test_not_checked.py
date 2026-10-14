#!/usr/bin/env python3
"""Checks for task #133: no check reports clean when it checked nothing. Never shipped.

    python tests/scripts/test_not_checked.py    # exit 0 = every check passed

From the Ruflo deep dive (2026-10-13; here, #38/#39's depth check was a green that could not fail):
a run that inspected zero items says NOT checked and exits 3, never "None" or "ok". Covered: the
mechanical lint (no entries; the search index missing, not a collection or empty), the task check
(no cards), claims corroboration (no claims), the feeds check (a page with no sources), the search
preflight (the probe search finds nothing), and the tooling status (nothing to compare against; the
installed scripts not running).
"""
from __future__ import annotations

import contextlib
import importlib.util
import io
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(SCRIPTS))
from _fake_qmd import fake_qmd_env  # noqa: E402

results: list[tuple[bool, str]] = []


def check(name: str, ok: bool, detail: object = ""):
    results.append((bool(ok), name + (f"  [{detail}]" if not ok and detail != "" else "")))


def notebook(tmp: Path, pages: dict[str, str]) -> tuple[Path, Path, Path]:
    nb = tmp / "notebooks" / "t"
    w = nb / "wiki"
    w.mkdir(parents=True)
    (nb / "_inbox" / "reports").mkdir(parents=True)
    for rel, body in pages.items():
        (w / rel).parent.mkdir(parents=True, exist_ok=True)
        (w / rel).write_text(body, encoding="utf-8")
    (tmp / "linked-notebooks.json").write_text(json.dumps({"notebooks": {"t": {"root": "notebooks/t"}}}),
                                               encoding="utf-8")
    proj = tmp / "project"
    (proj / ".claude").mkdir(parents=True)
    (proj / ".claude" / "wiki-config.json").write_text(json.dumps(
        {"notebook": "t", "registry": (tmp / "linked-notebooks.json").as_posix()}), encoding="utf-8")
    return nb, w, proj


PAGE = "---\ntitle: A\ndate: 2026-09-01\ntier: self\nconfidence: high\ntags: [x, y, z]\n---\n\n# A\n\nBody.\n"


def lint(proj: Path, env: dict, *extra: str):
    return subprocess.run([sys.executable, str(SCRIPTS / "wiki-lint-mechanical.py"), "--topic", "t", *extra],
                          cwd=proj, capture_output=True, text=True, encoding="utf-8", env=env)


base_env = {**os.environ, "PYTHONIOENCODING": "utf-8"}

# ── the lint ─────────────────────────────────────────────────────────────────
with tempfile.TemporaryDirectory() as td:
    tmp = Path(td)
    nb, w, proj = notebook(tmp, {})
    p = lint(proj, fake_qmd_env(tmp / "bin", w, n=0, env=base_env))
    report = (nb / "_inbox" / "reports" / "lint-report.md").read_text(encoding="utf-8")
    check("no entries: exit 3", p.returncode == 3, (p.returncode, p.stderr[-200:]))
    check("no entries: the report opens with NOT FULLY CHECKED and says 0 entries",
          "**⚠️ NOT FULLY CHECKED**" in report.split("**Generated**")[0] and "0 entries scanned" in report, report[:400])
    check("no entries: an empty index (0 files) is named too", "EMPTY, 0 files indexed" in report, report[:500])

with tempfile.TemporaryDirectory() as td:
    tmp = Path(td)
    nb, w, proj = notebook(tmp, {"research/a.md": PAGE})
    p = lint(proj, fake_qmd_env(tmp / "bin", w, env=base_env))
    report = (nb / "_inbox" / "reports" / "lint-report.md").read_text(encoding="utf-8")
    check("entries and an index that holds them: exit 0, no banner", p.returncode == 0 and "NOT FULLY CHECKED" not in report,
          (p.returncode, report[:300]))
    p = lint(proj, fake_qmd_env(tmp / "bin2", tmp / "elsewhere", n=5, env=base_env))
    report = (nb / "_inbox" / "reports" / "lint-report.md").read_text(encoding="utf-8")
    check("wiki not a qmd collection: exit 3, named at the top", p.returncode == 3
          and "not a qmd collection" in report.split("**Generated**")[0], (p.returncode, report[:400]))
    no_qmd = {**base_env, "PATH": os.pathsep.join(d for d in base_env["PATH"].split(os.pathsep)
                                                  if not (Path(d) / "qmd").exists() and not (Path(d) / "qmd.cmd").exists())}
    p = lint(proj, no_qmd)
    report = (nb / "_inbox" / "reports" / "lint-report.md").read_text(encoding="utf-8")
    check("qmd not on PATH: exit 3, named at the top", p.returncode == 3 and "not on PATH" in report.split("**Generated**")[0],
          (p.returncode, report[:400]))
    run = nb / "_inbox" / "reports" / "r"
    p = lint(proj, no_qmd, "--cycle-id", "c1", "--run-folder", str(run))
    d = json.loads((run / "lint-mechanical.json").read_text(encoding="utf-8"))
    check("cycle step: status partial, with the not_checked list",
          d.get("status") == "partial" and any("not on PATH" in r for r in d.get("not_checked", [])), d.get("not_checked"))
    p = lint(proj, no_qmd, "--strict")
    check("--strict with nothing failing still exits 3 when a part checked nothing", p.returncode == 3, p.returncode)

# ── the task check ───────────────────────────────────────────────────────────
with tempfile.TemporaryDirectory() as td:
    tmp = Path(td)
    nb, w, proj = notebook(tmp, {"tasks/ORDER.md": "<!-- next-id: 1 -->\n"})
    p = subprocess.run([sys.executable, str(SCRIPTS / "wiki-tasks.py"), "check"], cwd=proj, capture_output=True,
                       text=True, encoding="utf-8", env=base_env)
    check("task check with no cards: exit 3, NOT checked", p.returncode == 3 and "NOT checked" in p.stdout,
          (p.returncode, p.stdout[-200:], p.stderr[-200:]))
    subprocess.run([sys.executable, str(SCRIPTS / "wiki-tasks.py"), "add", "First task", "--owner", "main"], cwd=proj,
                   capture_output=True, text=True, encoding="utf-8", env=base_env)
    p = subprocess.run([sys.executable, str(SCRIPTS / "wiki-tasks.py"), "check"], cwd=proj, capture_output=True,
                       text=True, encoding="utf-8", env=base_env)
    check("task check with a card: ok, and says how many it checked", p.returncode == 0 and "1 cards checked" in p.stdout,
          (p.returncode, p.stdout[-200:]))

# ── claims corroboration ─────────────────────────────────────────────────────
with tempfile.TemporaryDirectory() as td:
    tmp = Path(td)
    nb, w, proj = notebook(tmp, {"research/a.md": PAGE})
    (nb / "_inbox" / "claims-index.json").write_text(json.dumps({"claims": []}), encoding="utf-8")
    p = subprocess.run([sys.executable, str(SCRIPTS / "wiki-claims-corroborate.py")], cwd=proj, capture_output=True,
                       text=True, encoding="utf-8", env=base_env)
    check("corroboration on an index with no claims: exit 3, NOT checked", p.returncode == 3 and "NOT checked" in p.stderr,
          (p.returncode, p.stderr[-200:]))

# ── the feeds check ──────────────────────────────────────────────────────────
with tempfile.TemporaryDirectory() as td:
    tmp = Path(td)
    nb, w, proj = notebook(tmp, {})
    (nb / "_config").mkdir()
    (nb / "_config" / "feeds.md").write_text("---\ntitle: Trusted sources\n---\n\n| Name | URL | Feed | From | To |\n"
                                             "|---|---|---|---|---|\n", encoding="utf-8")
    p = subprocess.run([sys.executable, str(SCRIPTS / "wiki-feeds.py"), "--topic", "t", "check"], cwd=proj,
                       capture_output=True, text=True, encoding="utf-8", env=base_env)
    check("feeds check on a page with no sources: exit 3, NOT checked", p.returncode == 3 and "NOT checked" in p.stderr,
          (p.returncode, p.stdout[-200:], p.stderr[-200:]))

# ── the search preflight's probe ─────────────────────────────────────────────
spec = importlib.util.spec_from_file_location("wqq", SCRIPTS / "wiki-qmd-query.py")
q = importlib.util.module_from_spec(spec)
spec.loader.exec_module(q)
probes = []


def probe_with(rc, out, err=""):
    q.run_qmd = lambda argv, timeout: (probes.append(argv) or (rc, out, err))
    e = io.StringIO()
    with contextlib.redirect_stderr(e):
        code = q.probe_search()
    return code, e.getvalue()


code, err = probe_with(0, json.dumps([{"file": "qmd://x/a.md"}]))
check("probe: a search that returns a row passes", code == 0 and "probe search ok" in err, (code, err))
check("probe: it is a keyword search (no model)", probes and probes[-1][0] == "search", probes[-1:])
code, err = probe_with(0, "[]")
check("probe: no rows fails (exit 2) and says the index is empty or broken", code == 2 and "empty or broken" in err,
      (code, err))
code, err = probe_with(1, "", "boom: no such index")
check("probe: a failed search fails, quoting why", code == 2 and "boom" in err, (code, err))
code, err = probe_with(None, "", "")
check("probe: a timeout is NOT checked (exit 124)", code == 124 and "NOT checked" in err, (code, err))
os.environ["WIKI_SEARCH_MODE"] = "keyword"
q.run_qmd = lambda argv, timeout: (0, "[]", "")
e = io.StringIO()
with contextlib.redirect_stderr(e):
    code = q.preflight()
os.environ.pop("WIKI_SEARCH_MODE")
check("preflight on a keyword machine runs the probe too", code == 2 and "probe search" in e.getvalue(), (code, e.getvalue()))

# ── the tooling status ───────────────────────────────────────────────────────
import _install_tooling as it  # noqa: E402

with tempfile.TemporaryDirectory() as td:
    tmp = Path(td)
    empty_pkg = tmp / "pkg"
    (empty_pkg / "scripts").mkdir(parents=True)
    st = it.global_tooling_status(empty_pkg, skills_dest=tmp / "skills", scripts_dest=tmp / "scripts",
                                  agents_dest=tmp / "agents")
    check("status against a package with nothing in it: state not-checked, not current",
          st["state"] == "not-checked" and not st["current"] and not st["complete"]
          and set(st["not_checked"]) == {"skills", "scripts", "toolset docs"}, (st["state"], st["not_checked"]))
    check("format_tooling_status says NOT checked", "NOT checked" in it.format_tooling_status(st))
    check("toolset_status against an empty package: not-checked", it.toolset_status(empty_pkg, tmp / "ts")["state"]
          in ("not-checked",), it.toolset_status(empty_pkg, tmp / "ts")["state"])
    check("scripts_run on a folder with no environment: not ok, says why",
          it.scripts_run(tmp / "scripts").startswith("no python"), it.scripts_run(tmp / "scripts"))

st = it.global_tooling_status(ROOT)
check("status on this machine: the installed scripts run (runs ok)", st["runs"] in ("ok", None), st["runs"])

failed = [n for ok, n in results if not ok]
for ok, n in results:
    print(("PASS " if ok else "FAIL ") + n)
print(f"\n{len(results) - len(failed)}/{len(results)} passed")
sys.exit(1 if failed else 0)
