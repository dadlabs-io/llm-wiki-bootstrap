#!/usr/bin/env python3
"""Checks that an entry the wiki-checker flagged is never promoted until it is corrected (task #178 row 8). Never
shipped.

    uv run python tests/scripts/test_checker_hold.py    # exit 0 = every check passed

The checker decision (2026-09-24) says a flagged entry is "never promoted as flagged", but until 2026-10-22 the hold
rested only on the orchestrator leaving that slug out of the promote call: wiki-promote.py knew nothing of the
checker, and `/wiki-promote --review` could not show the verdict. Now `wiki-cycle-scope.py checker-log` writes the
verdict into the staged entry's sidecar, `checker-corrected` marks it corrected after the fix, and the promote
script holds an uncorrected `fix` like a bad sidecar (HELD, exit 4; `--check` exit 1). No network: qmd is a stand-in.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[2] / "scripts"
results: list[tuple[bool, str]] = []


def check(name: str, ok: bool, detail: object = ""):
    results.append((bool(ok), name + (f"  [{detail}]" if not ok and detail != "" else "")))


def entry(title: str) -> str:
    return (f'---\ntitle: "{title}"\ndate: 2026-10-22\ntier: 3\nconfidence: medium\ntags: [t, test, checker]\n'
            f"status: proposed\n---\n\n# {title}\n\n## TL;DR\n\n{title}.\n\n## Related\n\n- [Old A](old-a.md)\n")


with tempfile.TemporaryDirectory() as td:
    tmp = Path(td)
    log = tmp / "qmd-calls.log"
    if os.name == "nt":
        qmd = tmp / "fake-qmd.cmd"
        qmd.write_text(f'@echo off\r\necho %*>>"{log}"\r\necho Done! Embedded 0 chunks\r\n', encoding="utf-8")
    else:
        qmd = tmp / "fake-qmd"
        qmd.write_text(f'#!/bin/sh\necho "$@" >> "{log}"\necho "Done! Embedded 0 chunks"\n', encoding="utf-8")
        qmd.chmod(0o755)
    env = {**os.environ, "PYTHONIOENCODING": "utf-8", "WIKI_QMD_BIN": str(qmd), "WIKI_SEARCH_MODE": "full",
           "WIKI_QMD_SLOT_DIR": str(tmp / "slots")}
    nb = tmp / "notebooks" / "t"
    dec = nb / "wiki" / "research" / "tooling"
    dec.mkdir(parents=True)
    (dec / "old-a.md").write_text(entry("Old A").replace("status: proposed\n", ""), encoding="utf-8")
    prop = nb / "_inbox" / "proposed"
    prop.mkdir(parents=True)
    for slug in ("flagged", "clean"):
        (prop / f"{slug}.md").write_text(entry(slug), encoding="utf-8")
        (prop / f"{slug}.proposed_metadata.json").write_text(json.dumps(
            {"target_folder": "research/tooling", "title": slug, "tier": "3"}), encoding="utf-8")
    (tmp / "linked-notebooks.json").write_text(json.dumps({"notebooks": {"t": {"root": "notebooks/t"}}}),
                                               encoding="utf-8")
    proj = tmp / "project"
    (proj / ".claude").mkdir(parents=True)
    (proj / ".claude" / "wiki-config.json").write_text(json.dumps(
        {"notebook": "t", "registry": (tmp / "linked-notebooks.json").as_posix()}), encoding="utf-8")
    rf = nb / "_inbox" / "reports" / "2026-10-22" / "2026-10-22-01"
    rf.mkdir(parents=True)

    def scope(*a):
        return subprocess.run([sys.executable, str(SCRIPTS / "wiki-cycle-scope.py"), "--topic", "t", *a], cwd=proj,
                              capture_output=True, text=True, encoding="utf-8", env=env, timeout=60)

    def promote(*a, stdin=None):
        return subprocess.run([sys.executable, str(SCRIPTS / "wiki-promote.py"), "--topic", "t", *a], cwd=proj,
                              capture_output=True, text=True, encoding="utf-8", env=env, timeout=120, input=stdin)

    def sidecar(slug):
        f = prop / f"{slug}.proposed_metadata.json"
        return json.loads(f.read_text(encoding="utf-8")) if f.is_file() else {}

    fix_rep, pass_rep = tmp / "flagged.json", tmp / "clean.json"
    fix_rep.write_text(json.dumps({"source_minutes": 20, "model": "opus",
                                   "unsupported_claims": [{"claim": "x"}]}), encoding="utf-8")
    pass_rep.write_text(json.dumps({"source_minutes": 25, "model": "opus"}), encoding="utf-8")

    # 1. checker-log writes the verdict into the staged entry's sidecar
    p = scope("checker-log", "--run-folder", str(rf), "--entry", "flagged", "--report", str(fix_rep))
    sc = sidecar("flagged").get("checker") or {}
    check("checker-log: exit 0", p.returncode == 0, p.stderr[-300:])
    check("checker-log: the sidecar carries the fix verdict, its report and corrected: false",
          sc.get("verdict") == "fix" and sc.get("corrected") is False and sc.get("report") == str(fix_rep), sc)
    scope("checker-log", "--run-folder", str(rf), "--entry", "clean", "--report", str(pass_rep))
    check("checker-log: a pass is recorded too", (sidecar("clean").get("checker") or {}).get("verdict") == "pass",
          sidecar("clean"))

    # 2. an uncorrected fix is held: --check names it, a promote leaves it staged (exit 4), the pass goes through
    p = promote("--check")
    out = p.stdout + p.stderr
    check("--check: exit 1, the flagged entry named with the checker's report",
          p.returncode == 1 and "flagged.md" in out and "checker" in out and str(fix_rep) in out, out[-500:])
    p = promote("--auto")
    out = p.stdout + p.stderr
    check("--auto: exit 4 (held)", p.returncode == 4, out[-500:])
    check("... the flagged entry stays staged", (prop / "flagged.md").is_file() and not (dec / "flagged.md").exists(),
          out[-300:])
    check("... the entry the checker passed is promoted", (dec / "clean.md").is_file(), out[-300:])
    check("... the held line says how to release it (checker-corrected)", "checker-corrected" in out, out[-500:])

    # 3. checker-corrected marks it; then it promotes, and --review shows the verdict first
    p = scope("checker-corrected", "--entry", "flagged")
    sc = sidecar("flagged").get("checker") or {}
    check("checker-corrected: exit 0, corrected: true with the time", p.returncode == 0 and sc.get("corrected") is True
          and sc.get("corrected_at"), (p.stdout + p.stderr)[-300:])
    p = promote("--check")
    check("--check after the correction: exit 0", p.returncode == 0, (p.stdout + p.stderr)[-400:])
    p = promote("--review", stdin="s\n")
    check("--review shows the checker's verdict and that it was corrected",
          "Checker: fix" in p.stdout and "corrected" in p.stdout.split("Checker: fix", 1)[-1][:80], p.stdout[-500:])
    p = scope("checker-corrected", "--entry", "no-such-entry")
    check("checker-corrected on an entry that is not staged: exit 2, named", p.returncode == 2
          and "no-such-entry" in p.stderr, (p.returncode, p.stderr[-300:]))

failed = [n for ok, n in results if not ok]
for ok, n in results:
    print(("PASS " if ok else "FAIL ") + n)
print(f"\n{len(results) - len(failed)}/{len(results)} passed")
sys.exit(1 if failed else 0)
