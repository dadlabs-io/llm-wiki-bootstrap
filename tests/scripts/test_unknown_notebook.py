#!/usr/bin/env python3
"""A notebook name the registry does not know is refused, never created (task #88). Never shipped.

    python tests/scripts/test_unknown_notebook.py    # exit 0 = every check passed

The wiki-cycle suite, 2026-10-06 (run 20261006-154949, Sonnet drive-files): a session ran the Drive step
from a folder inside the suite's sandbox, which sits inside llm-wiki-bootstrap. Walking up for a project
config found this repo's own, whose notebook resolves into the real project-notebooks, and the sandbox's
notebook name `cycletest`, unknown to the real registry, was joined onto it: the Drive step created
project-notebooks/notebooks/cycletest/. A notebook named on the command line that is neither in the
registry nor an existing folder now stops the script with exit 2, naming the registry it read.
"""
from __future__ import annotations

import io
import json
import contextlib
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))
import _wiki_config as wc  # noqa: E402

results: list[tuple[bool, str]] = []


def check(name: str, ok: bool, detail: object = ""):
    results.append((bool(ok), name + (f"  [{detail}]" if not ok and detail != "" else "")))


def refused(fn, *a, **kw):
    err = io.StringIO()
    try:
        with contextlib.redirect_stderr(err):
            fn(*a, **kw)
    except SystemExit as e:
        return e.code, err.getvalue()
    return None, err.getvalue()


with tempfile.TemporaryDirectory() as td:
    tmp = Path(td)
    notebooks = tmp / "notebooks"
    (notebooks / "real" / "wiki").mkdir(parents=True)
    (notebooks / "legacy" / "wiki").mkdir(parents=True)        # a folder no registry lists
    (tmp / "linked-notebooks.json").write_text(json.dumps({"notebooks": {"real": {"root": "notebooks/real"}}}),
                                               encoding="utf-8")
    proj = tmp / "project"
    (proj / ".claude").mkdir(parents=True)
    (proj / ".claude" / "wiki-config.json").write_text(json.dumps(
        {"notebook": "real", "registry": (tmp / "linked-notebooks.json").as_posix()}), encoding="utf-8")
    deep = proj / "sandbox" / "inner"                            # a folder whose nearest config is the project's
    deep.mkdir(parents=True)

    check("a registered notebook resolves", wc.topic_root("real", cwd=deep) == str(notebooks / "real"))
    check("an existing unregistered folder still resolves (legacy)", wc.topic_root("legacy", cwd=deep)
          == str(notebooks / "legacy"))
    for fn, label in ((wc.topic_root, "topic_root"), (wc.resolve_vault_topic, "resolve_vault_topic"),
                      (wc.wiki_dir, "wiki_dir")):
        code, err = refused(fn, "ghost", cwd=deep)
        check(f"{label}: an unknown notebook is refused (exit 2)", code == 2, (code, err))
        check(f"{label}: ... naming the notebook and the registry it read",
              "ghost" in err and "linked-notebooks.json" in err, err)
    check("nothing was created", not (notebooks / "ghost").exists())
    check("an explicit --vault is the legacy join, never refused",
          wc.resolve_vault_topic("ghost", vault=str(tmp / "v"), cwd=deep) == (str(tmp / "v"), "ghost"))

    p = subprocess.run([sys.executable, str(SCRIPTS / "wiki-list-add.py"), "--topic", "ghost",
                        "--source", "https://example.org/a"], cwd=deep, capture_output=True, text=True,
                       encoding="utf-8", errors="replace", timeout=120)
    check("wiki-list-add.py --topic ghost: exit 2, nothing created",
          p.returncode == 2 and not (notebooks / "ghost").exists(), (p.returncode, (p.stderr or p.stdout)[-300:]))
    p = subprocess.run([sys.executable, str(SCRIPTS / "wiki-list-add.py"), "--topic", "real",
                        "--source", "https://example.org/a"], cwd=deep, capture_output=True, text=True,
                       encoding="utf-8", errors="replace", timeout=120)
    check("wiki-list-add.py --topic real still queues", p.returncode == 0
          and any((notebooks / "real" / "_inbox" / "pending").glob("*.md")), (p.returncode, (p.stderr or p.stdout)[-300:]))

failed = [n for ok, n in results if not ok]
for ok, n in results:
    print(("PASS " if ok else "FAIL ") + n)
print(f"\n{len(results) - len(failed)}/{len(results)} passed")
sys.exit(1 if failed else 0)
