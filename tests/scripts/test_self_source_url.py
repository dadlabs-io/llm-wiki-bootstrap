#!/usr/bin/env python3
"""Checks that a self-authored entry filed from a local draft gets an internal:// source_url (task #177). Never
shipped.

    uv run python tests/scripts/test_self_source_url.py    # exit 0 = every check passed

wiki-update.py gave a page filed from a local file `source_url: file://<the draft's path>` when no --source-url was
passed. For our own pages (tier self) that is a temp file in _inbox/temp/, deleted once filed, so the field named a
file that no longer exists; the spec's form is `internal://synthesis/<date>-<slug>`. The lint's new source_url
check (2026-10-22) found 15 such pages in two notebooks, among them the improver's pass pages, which are filed with
the command `suggestions.py summary` prints. An explicit --source-url, and any external tier, are kept as given.
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import tempfile
from datetime import datetime
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[2] / "scripts"
results: list[tuple[bool, str]] = []


def check(name: str, ok: bool, detail: object = ""):
    results.append((bool(ok), name + (f"  [{detail}]" if not ok and detail != "" else "")))


with tempfile.TemporaryDirectory() as td:
    tmp = Path(td)
    nb = tmp / "notebooks" / "t"
    (nb / "wiki" / "project" / "decisions").mkdir(parents=True)
    (tmp / "linked-notebooks.json").write_text(json.dumps({"notebooks": {"t": {"root": "notebooks/t",
                                                                                "confirm_before_promote": False}}}),
                                               encoding="utf-8")
    proj = tmp / "project"
    (proj / ".claude").mkdir(parents=True)
    (proj / ".claude" / "wiki-config.json").write_text(json.dumps(
        {"notebook": "t", "registry": (tmp / "linked-notebooks.json").as_posix()}), encoding="utf-8")
    (nb / "_inbox" / "temp").mkdir(parents=True)
    env = {**os.environ, "PYTHONIOENCODING": "utf-8"}

    def file(title: str, *flags: str) -> dict:
        draft = nb / "_inbox" / "temp" / "draft.md"
        draft.write_text("## TL;DR\n\nWhat we decided.\n\n## Related\n\n- [a](a.md)\n- [b](b.md)\n", encoding="utf-8")
        p = subprocess.run([sys.executable, str(SCRIPTS / "wiki-update.py"), "--topic", "t", "--folder",
                            "project/decisions", "--source", str(draft), "--title", title, "--tags", "a,b,c",
                            "--confidence", "high", "--no-index", "--skip-integration", *flags],
                           cwd=proj, capture_output=True, text=True, encoding="utf-8", env=env, timeout=120)
        m = re.search(r"^wiki_path=(.+)$", p.stdout, re.M)
        text = Path(m.group(1).strip()).read_text(encoding="utf-8") if m else ""
        sm = re.search(r"^source_url:\s*(.+)$", text, re.M)
        return {"code": p.returncode, "source_url": sm.group(1).strip().strip("\"'") if sm else None,
                "out": (p.stdout + p.stderr)[-400:]}

    today = datetime.now().strftime("%Y-%m-%d")
    r = file("Our decision on caching", "--tier", "self", "--no-raw")
    check("a self page from a local draft: filed", r["code"] == 0, r["out"])
    check("... with source_url internal://synthesis/<today>-<slug>, never file://",
          r["source_url"] == f"internal://synthesis/{today}-our-decision-on-caching", r["source_url"])
    r = file("A second decision", "--tier", "self", "--no-raw", "--source-url", "internal://session/abc")
    check("an explicit --source-url is kept", r["source_url"] == "internal://session/abc", r["source_url"])
    r = file("A local article", "--tier", "3")
    check("an external tier from a local file keeps its file:// pointer (no URL to give)",
          (r["source_url"] or "").startswith("file://"), r["source_url"])

failed = [n for ok, n in results if not ok]
for ok, n in results:
    print(("PASS " if ok else "FAIL ") + n)
print(f"\n{len(results) - len(failed)}/{len(results)} passed")
sys.exit(1 if failed else 0)
