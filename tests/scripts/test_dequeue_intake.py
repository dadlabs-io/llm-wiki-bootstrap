#!/usr/bin/env python3
"""Checks for wiki-dequeue.py after triage (found by the wiki-cycle suite, 2026-10-03):
an ingested source's ticket moves to _inbox/done/ from an intake bucket too, not only
from pending/. Never shipped.

    python tests/scripts/test_dequeue_intake.py    # exit 0 = every check passed

Since triage (2026-09-24) a ticket waits in `_inbox/intake/<bucket>/` by the time it is
ingested, and the dequeue read only `_inbox/pending/`, so ingested tickets stayed in
their buckets: Sonnet failed the "ticket in done/" check on both the old and the new
skill, and Opus passed only by moving the ticket by hand.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "wiki-dequeue.py"
results: list[tuple[bool, str]] = []


def check(name: str, ok: bool, detail: object = ""):
    results.append((bool(ok), name + (f"  [{detail}]" if not ok and detail != "" else "")))


def ticket(path: Path, url: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(f"---\nsource: {url}\npriority: 3\n---\n\n# x\n", encoding="utf-8")


with tempfile.TemporaryDirectory() as td:
    tmp = Path(td)
    nb = tmp / "notebooks" / "t"
    (nb / "wiki" / "research").mkdir(parents=True)
    (nb / "_inbox" / "proposed").mkdir(parents=True)
    (nb / "wiki" / "research" / "a.md").write_text("---\nsource_url: https://example.com/a\n---\n", encoding="utf-8")
    (nb / "_inbox" / "proposed" / "b.md").write_text("---\nsource_url: https://example.com/b\n---\n", encoding="utf-8")
    inbox = nb / "_inbox"
    ticket(inbox / "pending" / "3-a.md", "https://example.com/a")            # ingested, in pending
    ticket(inbox / "intake" / "main" / "3-b.md", "https://example.com/b")    # staged, in this session's bucket
    ticket(inbox / "intake" / "other" / "3-a2.md", "https://www.example.com/a/")  # ingested, another bucket
    ticket(inbox / "intake" / "main" / "3-c.md", "https://example.com/c")    # not ingested: stays
    ticket(inbox / "pending" / "3-d.md", "https://example.com/d")            # not ingested: stays
    (inbox / "intake" / "README.md").write_text("---\nbuckets: []\n---\n# Intake\n", encoding="utf-8")
    (inbox / "intake" / "triage-log.md").write_text("| Date | Item |\n", encoding="utf-8")
    (inbox / "intake" / "main" / "README.md").write_text("# main bucket\n", encoding="utf-8")
    (inbox / "intake" / "main" / "2026-09-30-handoff-note.md").write_text("# A handoff, no source line\n", encoding="utf-8")
    (tmp / "linked-notebooks.json").write_text(json.dumps({"notebooks": {"t": {"root": "notebooks/t"}}}), encoding="utf-8")
    proj = tmp / "project"
    (proj / ".claude").mkdir(parents=True)
    (proj / ".claude" / "wiki-config.json").write_text(json.dumps(
        {"notebook": "t", "registry": (tmp / "linked-notebooks.json").as_posix()}), encoding="utf-8")

    def run(*a):
        return subprocess.run([sys.executable, str(SCRIPT), "--topic", "t", *a], cwd=proj, capture_output=True,
                              text=True, encoding="utf-8", env={**os.environ, "PYTHONIOENCODING": "utf-8"})

    p = run("--dry-run", "--json")
    check("dry run exits 0", p.returncode == 0, p.stderr[-300:])
    check("dry run moves nothing", (inbox / "intake" / "main" / "3-b.md").exists() and (inbox / "pending" / "3-a.md").exists())
    p = run("--json")
    check("run exits 0", p.returncode == 0, p.stderr[-300:])
    done = sorted(x.name for x in (inbox / "done").glob("*.md"))
    check("the ingested tickets are in done/: pending, this bucket and another bucket",
          done == ["3-a.md", "3-a2.md", "3-b.md"], done)
    check("a ticket not yet ingested stays in its bucket", (inbox / "intake" / "main" / "3-c.md").exists())
    check("a ticket not yet ingested stays in pending", (inbox / "pending" / "3-d.md").exists())
    check("files without a source line are untouched",
          all(x.exists() for x in (inbox / "intake" / "README.md", inbox / "intake" / "triage-log.md",
                                   inbox / "intake" / "main" / "README.md",
                                   inbox / "intake" / "main" / "2026-09-30-handoff-note.md")))
    try:
        out = json.loads(p.stdout)
    except json.JSONDecodeError:
        out = {}
    check("the JSON summary counts 3 moved", out.get("moved") == 3, out)
    p = run()
    check("a second run moves nothing", p.returncode == 0 and "0 already-ingested" in p.stdout, p.stdout)
    # a notebook with no pending/ but an intake bucket still drains the bucket
    (inbox / "pending" / "3-d.md").unlink()
    (inbox / "pending").rmdir()
    ticket(inbox / "intake" / "main" / "3-e.md", "https://example.com/a")
    p = run()
    check("no pending/ folder: the buckets are still read", p.returncode == 0 and (inbox / "done" / "3-e.md").exists(),
          p.stdout + p.stderr)

failed = [n for ok, n in results if not ok]
for ok, n in results:
    print(("PASS " if ok else "FAIL ") + n)
print(f"\n{len(results) - len(failed)}/{len(results)} passed")
sys.exit(1 if failed else 0)
