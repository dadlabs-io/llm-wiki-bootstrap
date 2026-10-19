#!/usr/bin/env python3
"""Checks for task #171: design pages behind the notes that change them. Never shipped.

    python tests/scripts/test_design_drift.py    # exit 0 = every check passed

investment-agent, 2026-10-18: a month of decisions, change records and troubleshooting notes
was filed while its architecture pages and data map were never revised; promote only appended
backlinks to them. The lint now lists every design page (under project/architecture/ or
project/components/, or any page marked `keep_current: true`) that a newer decision, change or
troubleshooting note links to, or that links to one, newer meaning the note's `date` is after
the design page's `last_reviewed` (else its `date`).
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _fake_qmd import fake_qmd_env  # noqa: E402  the lint needs an indexed wiki (task #133)

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "scripts"

results: list[tuple[bool, str]] = []


def check(name: str, ok: bool, detail: object = ""):
    results.append((bool(ok), name + (f"  [{detail}]" if not ok and detail != "" else "")))


def page(title: str, body: str, date: str, reviewed: str | None = None, extra: str = "") -> str:
    lr = f"last_reviewed: {reviewed}\n" if reviewed else ""
    return (f"---\ntitle: \"{title}\"\ndate: {date}\n{lr}tier: self\nconfidence: high\n"
            f"tags: [x, y, z]\n{extra}---\n\n# {title}\n\n{body}\n")


def run_lint():
    td = tempfile.TemporaryDirectory()
    tmp = Path(td.name)
    nb = tmp / "notebooks" / "t"
    w = nb / "wiki"
    for d in ("project/architecture", "project/components", "project/decisions", "project/code-changes",
              "project/troubleshooting", "project/patterns"):
        (w / d).mkdir(parents=True)
    (nb / "_inbox" / "reports").mkdir(parents=True)
    (tmp / "linked-notebooks.json").write_text(json.dumps({"notebooks": {"t": {"root": "notebooks/t"}}}),
                                               encoding="utf-8")
    proj = tmp / "project"
    (proj / ".claude").mkdir(parents=True)
    (proj / ".claude" / "wiki-config.json").write_text(json.dumps(
        {"notebook": "t", "registry": (tmp / "linked-notebooks.json").as_posix()}), encoding="utf-8")

    a, c, d = w / "project" / "architecture", w / "project" / "components", w / "project" / "decisions"
    # A design page written 09-13 whose backlink block names two later decisions and one earlier one
    (a / "layers.md").write_text(page("Layers", "Three stages.\n\n## Related\n- [d1](../decisions/d-new.md)\n"
                                      "- [d2](../decisions/d-newer.md)\n- [d0](../decisions/d-old.md)\n",
                                      "2026-09-13"), encoding="utf-8")
    (d / "d-new.md").write_text(page("D new", "Four stages now.", "2026-09-25"), encoding="utf-8")
    (d / "d-newer.md").write_text(page("D newer", "Gold layer.", "2026-10-15"), encoding="utf-8")
    (d / "d-old.md").write_text(page("D old", "DuckDB.", "2026-09-10"), encoding="utf-8")
    # A note linking TO a design page (no link back) counts too
    (c / "store.md").write_text(page("Store", "Opens the store.", "2026-09-01", reviewed="2026-09-20"),
                                encoding="utf-8")
    (w / "project" / "code-changes" / "ch.md").write_text(page("Change", "Changed [store](../components/store.md).",
                                                          "2026-10-01"), encoding="utf-8")
    # A design page reviewed after its newest note is current
    (c / "fresh.md").write_text(page("Fresh", "See [t](../troubleshooting/tr.md).", "2026-09-01",
                                     reviewed="2026-10-16"), encoding="utf-8")
    (w / "project" / "troubleshooting" / "tr.md").write_text(page("Tr", "x", "2026-10-10"), encoding="utf-8")
    # A note on the same day as the review is not newer
    (c / "sameday.md").write_text(page("Same day", "See [d](../decisions/d-same.md).", "2026-10-02"),
                                  encoding="utf-8")
    (d / "d-same.md").write_text(page("D same", "x", "2026-10-02"), encoding="utf-8")
    # A page outside the design folders, marked keep_current, is checked
    (w / "data-map.md").write_text(page("Data map", "See [d](project/decisions/d-newer.md).", "2026-10-09",
                                        extra="keep_current: true\n"), encoding="utf-8")
    # A pattern page (not design, not marked) is not checked
    (w / "project" / "patterns" / "pat.md").write_text(page("Pat", "See [d](../decisions/d-newer.md).",
                                                            "2026-09-01"), encoding="utf-8")
    # A retired design page is not checked; a retired note does not count
    (a / "retired.md").write_text(page("Retired", "See [d](../decisions/d-newer.md).", "2026-09-01",
                                       extra="superseded_by: layers.md\n"), encoding="utf-8")
    (a / "solo.md").write_text(page("Solo", "See [d](../decisions/d-gone.md).", "2026-09-01"), encoding="utf-8")
    (d / "d-gone.md").write_text(page("D gone", "x", "2026-10-05", extra="superseded_by: d-newer.md\n"),
                                 encoding="utf-8")

    run = nb / "_inbox" / "reports" / "r"
    env = fake_qmd_env(tmp / "bin", w, env={**os.environ, "PYTHONIOENCODING": "utf-8"})
    p = subprocess.run([sys.executable, str(SCRIPTS / "wiki-lint-mechanical.py"), "--topic", "t",
                        "--cycle-id", "c1", "--run-folder", str(run)],
                       cwd=proj, capture_output=True, text=True, encoding="utf-8", env=env)
    report = nb / "_inbox" / "reports" / "lint-report.md"
    text = report.read_text(encoding="utf-8") if report.is_file() else ""
    jp = run / "lint-mechanical.json"
    summary = (json.loads(jp.read_text(encoding="utf-8")) if jp.is_file() else {}).get("summary") or {}
    td.cleanup()
    return p, text, summary


def section(text: str, word: str) -> str:
    m = re.search(rf"^## [^\n]*{word}[^\n]*$(.*?)(?=^## |\Z)", text, re.MULTILINE | re.DOTALL)
    return m.group(1) if m else ""


p, text, summary = run_lint()
check("lint exits 0 (warn-only)", p.returncode == 0, p.stderr[-300:])
sec = section(text, "Design Pages Behind")
check("the report has the section", bool(sec), text[-1500:])
listed = re.findall(r"^- `([^`]+)`", sec, re.MULTILINE)
check("exactly the stale design pages are listed",
      sorted(listed) == ["data-map.md", "project/architecture/layers.md", "project/components/store.md"], listed)
check("a design page names how many newer notes and its own date",
      re.search(r"layers\.md` — 2 newer notes since 2026-09-13", sec), sec)
check("the newer notes are named, newest first, the older one left out",
      re.search(r"d-newer\.md` \(2026-10-15\).*d-new\.md` \(2026-09-25\)", sec) and "d-old.md" not in sec, sec)
check("a note that links to the design page counts, measured from last_reviewed",
      re.search(r"store\.md` — 1 newer note since 2026-09-20", sec), sec)
check("a page reviewed after its newest note is not listed", "fresh.md" not in sec, sec)
check("a note dated the same day as the review is not newer", "sameday.md" not in sec, sec)
check("keep_current marks a page outside the design folders", "data-map.md` — 1 newer note since 2026-10-09" in sec, sec)
check("a pattern page is not checked", "pat.md" not in sec, sec)
check("a retired design page is not checked", "retired.md" not in sec, sec)
check("a retired note does not count", "solo.md" not in sec, sec)
check("the header counts them", "**Design pages behind their notes**: 3" in text, text[:1500])
check("the cycle summary counts them", summary.get("design_behind") == 3, summary)

failed = [n for ok, n in results if not ok]
for ok, n in results:
    print(("PASS " if ok else "FAIL ") + n)
print(f"\n{len(results) - len(failed)}/{len(results)} passed")
sys.exit(1 if failed else 0)
