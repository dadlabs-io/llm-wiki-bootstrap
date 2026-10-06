#!/usr/bin/env python3
"""Checks that a promotion writes the backlinks for what it promoted. Never shipped.

    python tests/scripts/test_promote_backlinks.py    # exit 0 = every check passed

wiki-promote.py moved entries, fixed their links and regenerated the indexes and map,
but never ran wiki-reciprocate-backlinks.py. A promoted entry links out to older ones,
and nothing linked back to it until a /wiki-cycle happened to run the backlink script,
so every /wrap-up left its new entries as orphans (found at the 2026-09-25 wrap-up:
five promoted, four orphans). The user's call (2026-09-25): the promote step runs the
backlink rebuild itself, so every path that promotes (/wrap-up, /wiki-promote,
/wiki-cycle) gets it.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "scripts"

results: list[tuple[bool, str]] = []


def check(name: str, ok: bool, detail: object = ""):
    results.append((bool(ok), name + (f"  [{detail}]" if not ok and detail != "" else "")))


def entry(title: str, related: list[str]) -> str:
    links = "\n".join(f"- [{r}]({r})" for r in related) or "- (none)"
    return (f'---\ntitle: "{title}"\ndate: 2026-09-25\ntier: self\nconfidence: high\n'
            f"tags: [t, test, backlinks]\n---\n\n# {title}\n\n## TL;DR\n\n{title}.\n\n## Related\n\n{links}\n")


QMD_ENV: dict[str, str] = {}


def run(args, cwd):
    return subprocess.run([sys.executable, str(SCRIPTS / "wiki-promote.py"), *args], cwd=cwd,
                          capture_output=True, text=True, encoding="utf-8",
                          env={**os.environ, "PYTHONIOENCODING": "utf-8", **QMD_ENV})


def fake_qmd(folder: Path) -> tuple[Path, Path]:
    """A stand-in for qmd that only logs its arguments, so the promotion's re-index (task #81 P1)
    is seen without touching the real index or loading a model."""
    log = folder / "qmd-calls.log"
    if os.name == "nt":
        exe = folder / "fake-qmd.cmd"
        exe.write_text(f'@echo off\r\necho %*>>"{log}"\r\necho Done! Embedded 0 chunks\r\n', encoding="utf-8")
    else:
        exe = folder / "fake-qmd"
        exe.write_text(f'#!/bin/sh\necho "$@" >> "{log}"\necho "Done! Embedded 0 chunks"\n', encoding="utf-8")
        exe.chmod(0o755)
    return exe, log


with tempfile.TemporaryDirectory() as td:
    tmp = Path(td)
    qmd_exe, qmd_log = fake_qmd(tmp)
    QMD_ENV.update({"WIKI_QMD_BIN": str(qmd_exe), "WIKI_SEARCH_MODE": "full",
                    "WIKI_QMD_SLOT_DIR": str(tmp / "slots")})
    nb = tmp / "notebooks" / "t"
    dec = nb / "wiki" / "project" / "decisions"
    dec.mkdir(parents=True)
    # two existing entries that already link to each other, so neither is an orphan
    (dec / "old-a.md").write_text(entry("Old A", ["old-b.md"]), encoding="utf-8")
    (dec / "old-b.md").write_text(entry("Old B", ["old-a.md"]), encoding="utf-8")
    # one staged entry that links to both
    prop = nb / "_inbox" / "proposed"
    prop.mkdir(parents=True)
    (prop / "new-c.md").write_text(entry("New C", ["old-a.md", "old-b.md"]), encoding="utf-8")
    (prop / "new-c.proposed_metadata.json").write_text(json.dumps(
        {"target_folder": "project/decisions", "title": "New C", "tier": "self"}), encoding="utf-8")
    (tmp / "linked-notebooks.json").write_text(json.dumps({"notebooks": {"t": {"root": "notebooks/t"}}}),
                                               encoding="utf-8")
    proj = tmp / "project"
    (proj / ".claude").mkdir(parents=True)
    (proj / ".claude" / "wiki-config.json").write_text(json.dumps(
        {"notebook": "t", "registry": (tmp / "linked-notebooks.json").as_posix()}), encoding="utf-8")

    p = run(["--topic", "t", "--auto"], proj)
    out = p.stdout + p.stderr
    check("--auto exits 0", p.returncode == 0, out[-400:])
    check("the entry moved to its target folder", (dec / "new-c.md").exists(), out[-300:])
    qmd_calls = [l.strip() for l in qmd_log.read_text(encoding="utf-8").splitlines()] if qmd_log.exists() else []
    check("the promotion re-indexes the search: qmd update, then qmd embed",
          [c.split()[0] for c in qmd_calls if c] == ["update", "embed"], (qmd_calls, out[-300:]))

    for old in ("old-a.md", "old-b.md"):
        text = (dec / old).read_text(encoding="utf-8")
        block = text.split("<!-- BACKLINKS-AUTO START -->", 1)[1] if "<!-- BACKLINKS-AUTO START -->" in text else ""
        check(f"{old} now carries a backlinks block", bool(block), text[-300:])
        check(f"{old}'s backlinks block links the promoted entry", "new-c.md" in block, block[:300])

    # the lint agrees: nothing is an orphan after the promotion
    lint = subprocess.run([sys.executable, str(SCRIPTS / "wiki-lint-mechanical.py"), "--topic", "t"], cwd=proj,
                          capture_output=True, text=True, encoding="utf-8",
                          env={**os.environ, "PYTHONIOENCODING": "utf-8"})
    lout = lint.stdout + lint.stderr
    orphan_line = next((l for l in lout.splitlines() if l.startswith("**Orphan pages**")), "")
    check("the lint finds 0 orphans after the promotion", orphan_line.endswith(": 0"), orphan_line or lout[-300:])

    # a dry run moves nothing and so rewrites no backlinks (promotion removed the empty proposed/)
    prop.mkdir(parents=True, exist_ok=True)
    (prop / "new-d.md").write_text(entry("New D", ["old-a.md"]), encoding="utf-8")
    (prop / "new-d.proposed_metadata.json").write_text(json.dumps(
        {"target_folder": "project/decisions", "title": "New D", "tier": "self"}), encoding="utf-8")
    before = (dec / "old-a.md").read_text(encoding="utf-8")
    p = run(["--topic", "t", "--auto", "--dry-run"], proj)
    check("--dry-run leaves the backlinks untouched", (dec / "old-a.md").read_text(encoding="utf-8") == before,
          (p.stdout + p.stderr)[-300:])
    after = [l for l in qmd_log.read_text(encoding="utf-8").splitlines() if l.strip()] if qmd_log.exists() else []
    check("--dry-run does not re-index", len(after) == len(qmd_calls), after)

failed = [n for ok, n in results if not ok]
for ok, n in results:
    print(("PASS " if ok else "FAIL ") + n)
print(f"\n{len(results) - len(failed)}/{len(results)} passed")
sys.exit(1 if failed else 0)
