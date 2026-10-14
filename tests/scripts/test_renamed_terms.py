#!/usr/bin/env python3
"""Checks for task #132: the renamed-terms table and the retirement-link check. Never shipped.

    python tests/scripts/test_renamed_terms.py    # exit 0 = every check passed

From the Ruflo deep dive (2026-10-13): their ADR lint found 22 supersede breaks in 366
records, and a renamed term lingers in old pages unless something names it. The lint now
reads `<notebook>/_config/renamed-terms.md` (one row per old name) and flags an old name
left in our own pages (tier self or under project/, decision entries excepted; code,
quotes, link targets and frontmatter not read), and checks that a `superseded_by` names a
real entry that names the retired one back.
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
SCRIPTS = ROOT / "scripts"

results: list[tuple[bool, str]] = []


def check(name: str, ok: bool, detail: object = ""):
    results.append((bool(ok), name + (f"  [{detail}]" if not ok and detail != "" else "")))


def page(title: str, body: str, tier: str = "self", extra: str = "") -> str:
    return (f"---\ntitle: \"{title}\"\ndate: 2026-09-01\ntier: {tier}\nconfidence: high\n"
            f"tags: [x, y, z]\n{extra}---\n\n# {title}\n\n{body}\n")


TABLE = """---
title: Renamed terms
---
| Old name | New name | Since | Note |
|---|---|---|---|
| upd-docs | wrap-up | 2026-09-15 | retired |
| `intake-other` | intake/main | 2026-09-24 | |
| intake-misc | intake/main | 2026-09-24 | a second old name for the same new one |
"""


def run_lint(table: str | None):
    td = tempfile.TemporaryDirectory()
    tmp = Path(td.name)
    nb = tmp / "notebooks" / "t"
    w = nb / "wiki"
    for d in ("project/patterns", "project/decisions", "research/x"):
        (w / d).mkdir(parents=True)
    (nb / "_inbox" / "reports").mkdir(parents=True)
    if table is not None:
        (nb / "_config").mkdir()
        (nb / "_config" / "renamed-terms.md").write_text(table, encoding="utf-8")
    (tmp / "linked-notebooks.json").write_text(json.dumps({"notebooks": {"t": {"root": "notebooks/t"}}}),
                                               encoding="utf-8")
    proj = tmp / "project"
    (proj / ".claude").mkdir(parents=True)
    (proj / ".claude" / "wiki-config.json").write_text(json.dumps(
        {"notebook": "t", "registry": (tmp / "linked-notebooks.json").as_posix()}), encoding="utf-8")

    pat = w / "project" / "patterns"
    (pat / "own.md").write_text(page("Own", "\n".join([
        "Run /upd-docs at the end.",                  # hit (slash form)
        "The UPD-DOCS step is gone.",                 # hit (any case)
        "Files go to intake-other.",                  # hit (backticked in the table)
        "See intake-misc too.",                       # hit (second old name, same new one)
        "Not upd-docs-v2, a longer name.",            # no hit (hyphen after)
        "Inline `upd-docs` is code, still a name.",    # hit (inline code is read)
        "> upd-docs quoted from a source",            # no hit
        "[the page](upd-docs.md) link target",        # no hit
        "```", "upd-docs in a fence", "```",          # no hit
    ]), extra="aliases: upd-docs\n"), encoding="utf-8")
    (w / "project" / "decisions" / "d.md").write_text(page("D", "We retired upd-docs."), encoding="utf-8")
    (w / "research" / "x" / "src.md").write_text(page("Src", "The author runs upd-docs.", tier="3"),
                                                 encoding="utf-8")
    (w / "research" / "x" / "mine.md").write_text(page("Mine", "Our note on upd-docs."), encoding="utf-8")
    (pat / "old.md").write_text(page("Old", "upd-docs everywhere",
                                     extra="superseded_by: new.md\nstatus: superseded\n"), encoding="utf-8")

    # retirement links
    (pat / "new.md").write_text(page("New", "Replaces [old](old.md)."), encoding="utf-8")
    (pat / "gone.md").write_text(page("Gone", "x", extra="superseded_by: missing.md\n"), encoding="utf-8")
    (pat / "paren.md").write_text(page("Paren", "x", extra='superseded_by: "(none yet - pending)"\n'),
                                  encoding="utf-8")
    (pat / "silent.md").write_text(page("Silent", "x", extra="superseded_by: quiet\n"), encoding="utf-8")
    (w / "research" / "x" / "quiet.md").write_text(page("Quiet", "never names its predecessor"),
                                                   encoding="utf-8")

    run = nb / "_inbox" / "reports" / "r"
    env = {**os.environ, "PYTHONIOENCODING": "utf-8"}
    p = subprocess.run([sys.executable, str(SCRIPTS / "wiki-lint-mechanical.py"), "--topic", "t",
                        "--cycle-id", "c1", "--run-folder", str(run)],
                       cwd=proj, capture_output=True, text=True, encoding="utf-8", env=env)
    report = (nb / "_inbox" / "reports" / "lint-report.md")
    text = report.read_text(encoding="utf-8") if report.is_file() else ""
    jp = run / "lint-mechanical.json"
    summary = (json.loads(jp.read_text(encoding="utf-8")) if jp.is_file() else {}).get("summary") or {}
    td.cleanup()
    return p, text, summary


def section(text: str, word: str) -> str:
    m = re.search(rf"^## [^\n]*{word}[^\n]*$(.*?)(?=^## |\Z)", text, re.MULTILINE | re.DOTALL)
    return m.group(1) if m else ""


p, text, summary = run_lint(TABLE)
check("lint exits 0 (warn-only)", p.returncode == 0, p.stderr[-300:])
rt = section(text, "Renamed Terms")
hits = re.findall(r"^- `([^`]+)`", rt, re.MULTILINE)
check("own page: the slash form, any case, a backticked table cell and a second old name and inline code are flagged",
      [h for h in hits if h.startswith("project/patterns/own.md:")]
      == [f"project/patterns/own.md:{n}" for n in (12, 13, 14, 15, 17)], hits)
check("a longer name, a quote, a link target, a fence and frontmatter are not flagged",
      not any(h.startswith("project/patterns/own.md:") and int(h.rsplit(":", 1)[1]) in (7, 16, 18, 19, 21)
              for h in hits), hits)
check("each hit names the new name", '"upd-docs" → use "wrap-up"' in rt and '→ use "intake/main"' in rt, rt[:400])
check("a decision entry is not checked", not any(h.startswith("project/decisions/") for h in hits), hits)
check("a research entry from a source is not checked", not any(h.startswith("research/x/src.md") for h in hits), hits)
check("a research entry of our own (tier self) is checked", any(h.startswith("research/x/mine.md") for h in hits), hits)
check("a retired entry is not checked", not any(h.startswith("project/patterns/old.md") for h in hits), hits)
check("the summary counts the hits", summary.get("renamed_terms_left") == len(hits) == 6, (summary, hits))
check("the header counts the hits", "**Renamed terms left**: 6" in text, text[:900])

rl = section(text, "Retirement Links")
check("a successor that names the retired entry back is clean", "patterns/old.md`" not in rl, rl)
check("a superseded_by naming no entry is flagged", "gone.md` — `superseded_by: missing.md`: no such entry" in rl, rl)
check("a parenthetical superseded_by is flagged as not a path", "paren.md` — " in rl and "not a path" in rl, rl)
check("a bare slug resolves anywhere in the wiki; a successor that never names it back is flagged",
      "silent.md` — its successor `research/x/quiet.md` does not name it back" in rl, rl)
check("summary counts the retirement findings",
      summary.get("supersede_bad_target") == 2 and summary.get("supersede_no_backlink") == 1, summary)

p, text, summary = run_lint(None)
check("no table: the section says not checked", "Not checked: this notebook has no" in section(text, "Renamed Terms"))
check("no table: header says so", "(no renamed-terms table)" in text)
p, text, summary = run_lint("| Old name | New name |\n|---|---|\n")
check("an empty table: the section says it has no rows", "has no rows" in section(text, "Renamed Terms"))

failed = [n for ok, n in results if not ok]
for ok, n in results:
    print(("PASS " if ok else "FAIL ") + n)
print(f"\n{len(results) - len(failed)}/{len(results)} passed")
sys.exit(1 if failed else 0)
