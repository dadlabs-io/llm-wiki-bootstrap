#!/usr/bin/env python3
"""Checks for task #44: a folder declares itself with a README. Never shipped.

    python tests/scripts/test_folder_readme.py    # exit 0 = every check passed

wiki-promote.py warned "not a known taxonomy path" for every folder outside the
framework's global list, so agentic-design's research/agents (64 entries) and nine
other notebooks' own folders printed noise on every promotion. The user's rule
(2026-09-24): a folder that carries a README.md, which says what it is for, counts
as known; a folder with none still warns, since a typo'd folder the script creates
never gets one.
"""
from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "bootstrap" / "scripts"
sys.path.insert(0, str(SCRIPTS))

results: list[tuple[bool, str]] = []


def check(name: str, ok: bool, detail: object = ""):
    results.append((bool(ok), name + (f"  [{detail}]" if not ok and detail != "" else "")))


spec = importlib.util.spec_from_file_location("wiki_promote", SCRIPTS / "wiki-promote.py")
promote = importlib.util.module_from_spec(spec)
spec.loader.exec_module(promote)
norm = promote._normalize_target_folder

with tempfile.TemporaryDirectory() as td:
    wiki = Path(td) / "wiki"
    (wiki / "research" / "agents").mkdir(parents=True)
    (wiki / "research" / "agents" / "README.md").write_text("# agents\n\nBuilding agents.\n", encoding="utf-8")
    (wiki / "research" / "agnets").mkdir(parents=True)          # a typo folder: exists, no README
    (wiki / "research" / "agnets" / "one.md").write_text("# x\n", encoding="utf-8")

    try:
        f, w = norm("research/agents", wiki)
    except TypeError as e:
        f, w = None, f"TypeError: {e}"
    check("a folder with a README is known: no warning", (f, w) == ("research/agents", None), (f, w))
    try:
        f, w = norm("research/agnets", wiki)
    except TypeError as e:
        f, w = None, f"TypeError: {e}"
    check("an existing folder with no README still warns", f == "research/agnets" and bool(w), (f, w))
    check("the warning says to add a README (or check the spelling)", bool(w) and "README" in w, w)
    try:
        f, w = norm("research/nowhere", wiki)
    except TypeError as e:
        f, w = None, f"TypeError: {e}"
    check("a folder that does not exist warns", f == "research/nowhere" and bool(w), (f, w))
    f, w = norm("research/agents")
    check("without the wiki's path the old behaviour stands (warns)", f == "research/agents" and bool(w), (f, w))
    try:
        f, w = norm("research/tooling", wiki)
    except TypeError:
        f, w = norm("research/tooling")
    check("a folder on the global list needs no README", (f, w) == ("research/tooling", None), (f, w))
    try:
        f, w = norm("long-term", wiki)
    except TypeError:
        f, w = norm("long-term")
    check("a bare leaf is still auto-prefixed", f == "research/long-term" and "auto-prefixed" in (w or ""), (f, w))
    try:
        f, w = norm("project/decision", wiki)
    except TypeError:
        f, w = norm("project/decision")
    check("a singular name is still mapped", f == "project/decisions", (f, w))

# end to end: wiki-promote.py --check on a staged entry for each folder
with tempfile.TemporaryDirectory() as td:
    tmp = Path(td)
    nb = tmp / "notebooks" / "t"
    wiki = nb / "wiki"
    (wiki / "research" / "agents").mkdir(parents=True)
    (wiki / "research" / "agents" / "README.md").write_text("# agents\n", encoding="utf-8")
    (wiki / "research" / "vendors").mkdir(parents=True)          # no README
    prop = nb / "_inbox" / "proposed"
    prop.mkdir(parents=True)
    for slug, folder in (("with-readme", "research/agents"), ("without-readme", "research/vendors")):
        (prop / f"{slug}.md").write_text(f"---\ntitle: \"{slug}\"\ndate: 2026-09-24\ntier: 3\n---\n\n# {slug}\n",
                                         encoding="utf-8")
        (prop / f"{slug}.proposed_metadata.json").write_text(json.dumps({"target_folder": folder, "title": slug}),
                                                             encoding="utf-8")
    (tmp / "linked-notebooks.json").write_text(json.dumps({"notebooks": {"t": {"root": "notebooks/t"}}}), encoding="utf-8")
    proj = tmp / "project"
    (proj / ".claude").mkdir(parents=True)
    (proj / ".claude" / "wiki-config.json").write_text(json.dumps(
        {"notebook": "t", "registry": (tmp / "linked-notebooks.json").as_posix()}), encoding="utf-8")
    p = subprocess.run([sys.executable, str(SCRIPTS / "wiki-promote.py"), "--topic", "t", "--check"], cwd=proj,
                       capture_output=True, text=True, encoding="utf-8", env={**os.environ, "PYTHONIOENCODING": "utf-8"})
    out = p.stdout + p.stderr
    check("--check exits 0", p.returncode == 0, out[-300:])
    check("--check: no warning for the folder with a README",
          not any("with-readme" in l and "not a known" in l for l in out.splitlines()), out[-400:])
    check("--check: the folder without a README still warns",
          any("without-readme" in l and "not a known" in l for l in out.splitlines()), out[-400:])

failed = [n for ok, n in results if not ok]
for ok, n in results:
    print(("PASS " if ok else "FAIL ") + n)
print(f"\n{len(results) - len(failed)}/{len(results)} passed")
sys.exit(1 if failed else 0)
