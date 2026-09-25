#!/usr/bin/env python3
"""Checks for task #46: the stale-"pending" lint flags our own stale notes, not a
source's words. Never shipped.

    python tests/scripts/test_stale_pending.py    # exit 0 = every check passed

The check exists to catch our own notes that went stale ("pending ingestion",
"not yet built", a TODO) once the thing got done. It scanned every line of every
file, frontmatter included, with `to-?do[- :]` among its phrases, so on 2026-09-24
agentic-design showed 34 hits and about one was ours to check: "Nothing to Do With"
in link titles, "to-do list" in articles about to-do lists, a tag, a raw_path, and
the Noyan entry's "she has not yet built", the speaker's own plan (agent-builder,
2026-09-23). Rules now: workflow phrases (pending ingestion, awaiting fetch,
awaiting playwright, todo after ingest) count in every entry; build phrases
("not yet built", an uppercase TODO marker) only in our own entries (tier self);
frontmatter, `>` quotes, fenced and inline code and link targets are never read.
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "bootstrap" / "scripts"

results: list[tuple[bool, str]] = []


def check(name: str, ok: bool, detail: object = ""):
    results.append((bool(ok), name + (f"  [{detail}]" if not ok and detail != "" else "")))


def entry(title: str, tier: str, body: str, tags: str = "x, y, z") -> str:
    return (f"---\ntitle: \"{title}\"\ndate: 2026-09-01\ntier: {tier}\nconfidence: medium\n"
            f"tags: [{tags}]\n---\n\n# {title}\n\n{body}\n")


PAGES = {
    # our own entries (tier self): every kind of stale note is flagged
    "project/own-not-built.md": ("self", "The retry fetcher is not yet built.", True),
    "project/own-todo.md": ("self", "TODO: add the sequence diagram.", True),
    "project/own-awaiting.md": ("self", "The companion paper is awaiting fetch.", True),
    "project/own-todo-prose.md": ("self", "ALL task/TODO lists MUST use the todowrite tool.", False),
    # a source's words, in a research entry (tier 3): build phrases are the source's plans
    "research/source-not-built.md": ("3", "She names two forward directions she has not yet built: guidance and training.", False),
    "research/source-todo-list.md": ("3", "The agent writes a to-do list first, then works through the TODO items.", False),
    # our workflow notes inside a research entry still count
    "research/workflow-note.md": ("3", "Related: the companion talk (pending ingestion).", True),
    # never read: link titles and targets, quotes, code, frontmatter
    "research/link-title.md": ("3", "- [Obsidian's Best Features Have Nothing to Do With Note-Taking](x.md)", False),
    "project/own-link-target.md": ("self", "See [the notes](../raw/2026-09-23-todo-after-ingest-list.md).", False),
    "project/own-quote.md": ("self", "> The feature is not yet built, the author said.", False),
    "project/own-code.md": ("self", "Run `grep TODO` to list them.\n\n```\n# TODO: not yet built\n```", False),
}
TAGGED = ("project/own-tags.md", "self", "Clean body.", "todo-md, todo, pending-ingestion")

with tempfile.TemporaryDirectory() as td:
    tmp = Path(td)
    nb = tmp / "notebooks" / "t"
    w = nb / "wiki"
    (nb / "_inbox" / "reports").mkdir(parents=True)
    for rel, (tier, body, _flag) in PAGES.items():
        (w / rel).parent.mkdir(parents=True, exist_ok=True)
        (w / rel).write_text(entry(Path(rel).stem, tier, body), encoding="utf-8")
    (w / TAGGED[0]).write_text(entry("own-tags", TAGGED[1], TAGGED[2], TAGGED[3]), encoding="utf-8")
    (tmp / "linked-notebooks.json").write_text(json.dumps({"notebooks": {"t": {"root": "notebooks/t"}}}), encoding="utf-8")
    proj = tmp / "project"
    (proj / ".claude").mkdir(parents=True)
    (proj / ".claude" / "wiki-config.json").write_text(json.dumps(
        {"notebook": "t", "registry": (tmp / "linked-notebooks.json").as_posix()}), encoding="utf-8")
    p = subprocess.run([sys.executable, str(SCRIPTS / "wiki-lint-mechanical.py"), "--topic", "t"], cwd=proj,
                       capture_output=True, text=True, encoding="utf-8", env={**os.environ, "PYTHONIOENCODING": "utf-8"})
    check("lint exits 0", p.returncode == 0, p.stderr[-300:])
    text = (nb / "_inbox" / "reports" / "lint-report.md").read_text(encoding="utf-8")
    m = re.search(r"^## [^\n]*Stale 'Pending'[^\n]*$(.*?)(?=^## )", text, re.MULTILINE | re.DOTALL)
    sec = m.group(1) if m else ""
    flagged = set(re.findall(r"^- `([^`:]+):\d+`", sec, re.MULTILINE))
    for rel, (tier, _body, want) in PAGES.items():
        got = rel in flagged
        check(f"{rel}: {'flagged' if want else 'not flagged'}", got == want, sorted(flagged))
    check("frontmatter (tags) is never read", TAGGED[0] not in flagged, sorted(flagged))
    n = len([f for f, (_t, _b, want) in PAGES.items() if want])
    check(f"the header counts the {n} real stale notes",
          f"**Stale 'pending' mentions**: {n}" in text, re.findall(r"\*\*Stale 'pending' mentions\*\*: \d+", text))
    lines = re.findall(r"^- `project/own-todo\.md:(\d+)`", sec, re.MULTILINE)
    check("the reported line number is the file's own line", lines == ["11"], lines)

failed = [n for ok, n in results if not ok]
for ok, n in results:
    print(("PASS " if ok else "FAIL ") + n)
print(f"\n{len(results) - len(failed)}/{len(results)} passed")
sys.exit(1 if failed else 0)
