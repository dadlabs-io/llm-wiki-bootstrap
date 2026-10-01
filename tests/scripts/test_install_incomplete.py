#!/usr/bin/env python3
"""Checks for task #61: an install that stops partway says so. Never shipped.

    python tests/scripts/test_install_incomplete.py    # exit 0 = every check passed

On 2026-10-01 wiki-upgrade.py crashed partway through an install (after the
scripts, before any skill) and left only a traceback: nothing said the skills were
still the old ones, and nothing was kept that a later session could read. The
user: notify when it crashes, in a way that "you would know what the error was"
when asked why and to fix it.

So: install_tooling() raises InstallIncomplete carrying what was done and the
full traceback; report_incomplete() writes a log a later session can read
(~/.cache/llm-wiki/install-errors/, $WIKI_INSTALL_LOG_DIR here) and prints one
"⚠️ INSTALL INCOMPLETE" line naming the stop, the error and the log. Every
install entry point (wiki-upgrade.py, new-wiki.py --mode tooling) uses it and
exits 1. Nothing here writes to the real ~/.claude or ~/.cache.
"""
from __future__ import annotations

import io
import os
import shutil
import subprocess
import sys
import tempfile
from contextlib import redirect_stdout
from pathlib import Path

for _stream in (sys.stdout, sys.stderr):  # the report names contain ⚠️; piped on Windows stdout is cp1252
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))
import _install_tooling as it  # noqa: E402

results: list[tuple[bool, str]] = []


def check(name: str, ok: bool, detail: object = ""):
    results.append((bool(ok), name + (f"  [{detail}]" if not ok and detail != "" else "")))


FAIL_AT = "wiki-search"
before_fail = it.TRAVEL_SKILLS[:it.TRAVEL_SKILLS.index(FAIL_AT)]
Incomplete = getattr(it, "InstallIncomplete", None)
check("_install_tooling has InstallIncomplete", Incomplete is not None)
check("_install_tooling has report_incomplete()", callable(getattr(it, "report_incomplete", None)))

with tempfile.TemporaryDirectory() as tmp:
    td = Path(tmp)
    real_loader = it.load_install_skill_fn

    def failing_loader(scripts_src):
        real = real_loader(scripts_src)

        def fn(**kw):
            if kw["skill"] == FAIL_AT:
                raise RuntimeError("disk full (test)")
            return real(**kw)
        return fn

    it.load_install_skill_fn = failing_loader
    caught = None
    try:
        with redirect_stdout(io.StringIO()):
            it.install_tooling(ROOT, skills_dest=td / "skills", scripts_dest=td / "wiki-scripts")
    except Exception as e:  # noqa: BLE001 — the test inspects whatever came out
        caught = e
    finally:
        it.load_install_skill_fn = real_loader

    check("a mid-install failure raises InstallIncomplete", Incomplete is not None and isinstance(caught, Incomplete),
          type(caught).__name__)
    if Incomplete is not None and isinstance(caught, Incomplete):
        p = caught.progress
        check("it records every script as copied", len(p["scripts"]) >= len(it.TRAVEL_SCRIPTS), len(p["scripts"]))
        check("it records the skills installed before the stop", p["skills"] == before_fail, p["skills"])
        check("it names where it stopped", caught.stopped_at == f"skill {FAIL_AT}", caught.stopped_at)
        check("it keeps the original error", isinstance(caught.error, RuntimeError) and "disk full" in str(caught.error))
        check("it keeps the full traceback", "Traceback" in caught.traceback_text and "disk full" in caught.traceback_text)

        out = io.StringIO()
        with redirect_stdout(out):
            log = it.report_incomplete(caught, command=["wiki-upgrade.py"], log_dir=td / "logs")
        line = [ln for ln in out.getvalue().splitlines() if ln.strip()][-1] if out.getvalue().strip() else ""
        check("the closing line starts ⚠️ INSTALL INCOMPLETE", line.startswith("⚠️ INSTALL INCOMPLETE"), line)
        check("the closing line names the stop and the error",
              f"skill {FAIL_AT}" in line and "RuntimeError: disk full (test)" in line, line)
        check("the closing line names the log", log is not None and str(log) in line, line)
        text = Path(log).read_text(encoding="utf-8") if log and Path(log).is_file() else ""
        check("the log is written", bool(text))
        check("the log has the traceback", "Traceback" in text and "disk full (test)" in text)
        check("the log says where it stopped", f"stopped at: skill {FAIL_AT}" in text)
        check("the log lists the skills not installed", all(s in text.split("not done:", 1)[-1]
                                                             for s in it.TRAVEL_SKILLS[len(before_fail):]))
        check("the log says how to finish", "-RefreshOnly" in text)

    # nothing done yet: a missing source is still the plain FileNotFoundError the callers already report
    (td / "empty").mkdir()
    try:
        it.install_tooling(td / "empty", skills_dest=td / "s2", scripts_dest=td / "w2")
        err = None
    except Exception as e:  # noqa: BLE001
        err = e
    check("a missing source stays a FileNotFoundError", type(err) is FileNotFoundError, type(err).__name__)

# end to end: both install commands, a throwaway copy of the source with one skill file corrupted
with tempfile.TemporaryDirectory() as tmp:
    td = Path(tmp)
    src = td / "src"
    for d in ("scripts", "skills", "agents"):
        shutil.copytree(ROOT / d, src / d, ignore=shutil.ignore_patterns("__pycache__"))
    bad = src / "skills" / "wiki" / "SKILL.md"
    bad.write_bytes(b"\xff\xfe\xfa not utf-8 " + bad.read_bytes())
    env = {k: v for k, v in os.environ.items() if k not in ("PYTHONIOENCODING", "PYTHONUTF8")}
    env["PYTHONIOENCODING"] = "cp1252"  # what a pipe gets on Windows
    for label, cmd in (("wiki-upgrade.py", [sys.executable, str(src / "scripts" / "wiki-upgrade.py"),
                                            "--dry-run", "--bootstrap-source", str(src)]),
                       ("new-wiki.py --mode tooling", [sys.executable, str(src / "scripts" / "new-wiki.py"),
                                                       "--mode", "tooling", "--dry-run", "--bootstrap-source", str(src)])):
        logs = td / f"logs-{label.split('.')[0]}"
        p = subprocess.run(cmd, capture_output=True, env={**env, "WIKI_INSTALL_LOG_DIR": str(logs)})
        out, err = p.stdout.decode("utf-8", "replace"), p.stderr.decode("utf-8", "replace")
        lines = [ln for ln in out.splitlines() if ln.strip()]
        check(f"{label}: exits 1", p.returncode == 1, p.returncode)
        check(f"{label}: ends on ⚠️ INSTALL INCOMPLETE naming the stop",
              bool(lines) and lines[-1].startswith("⚠️ INSTALL INCOMPLETE") and "skill wiki" in lines[-1],
              lines[-1:] or err[-200:])
        check(f"{label}: no raw traceback on screen", "Traceback" not in out + err, (out + err)[-200:])
        found = sorted(logs.glob("*.log")) if logs.is_dir() else []
        body = found[0].read_text(encoding="utf-8") if found else ""
        check(f"{label}: one log, with the real error", len(found) == 1 and "UnicodeDecodeError" in body
              and "Traceback" in body, [f.name for f in found])

failed = [n for ok, n in results if not ok]
for ok, n in results:
    print(("PASS " if ok else "FAIL ") + n)
print(f"\n{len(results) - len(failed)}/{len(results)} passed")
sys.exit(1 if failed else 0)
