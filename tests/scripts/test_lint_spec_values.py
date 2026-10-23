#!/usr/bin/env python3
"""Checks that the lint enforces what the frontmatter spec says it does (task #177 row 5). Never shipped.

    uv run python tests/scripts/test_lint_spec_values.py    # exit 0 = every check passed

The spec's "Lint enforcement" list promised checks no code made: `date`, `last_reviewed` and `review_after` are ISO
dates; `source_url` is `http(s)://` or `internal://`; `source_url` and `ingested_by` are present (the lint required
only `title` and `date`); and `verified: verified` is never set on an entry's own write, only by /wiki-verify,
whose record is the entry's `_signals/<slug>.json` (wiki-verify's own skill said "nothing mechanical enforces
this"). All four are warn-only in the Spec Enforcement section, as the other spec checks there are.
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

SCRIPTS = Path(__file__).resolve().parents[2] / "scripts"
results: list[tuple[bool, str]] = []


def check(name: str, ok: bool, detail: object = ""):
    results.append((bool(ok), name + (f"  [{detail}]" if not ok and detail != "" else "")))


GOOD = {"title": '"Good"', "date": "2026-10-01", "source_url": "https://example.com/a", "ingested_by": "claude-code",
        "tier": "3", "confidence": "medium", "last_reviewed": "2026-10-01", "review_after": "2026-12-01",
        "tags": "[x, y, z]", "raw_path": "raw/a.md"}


def page(name: str, **changes) -> str:
    fm = {**GOOD, "title": f'"{name}"', **changes}
    lines = [f"{k}: {v}" for k, v in fm.items() if v is not None]
    return "---\n" + "\n".join(lines) + f"\n---\n\n# {name}\n\n## TL;DR\n\nText.\n"


with tempfile.TemporaryDirectory() as td:
    tmp = Path(td)
    nb = tmp / "notebooks" / "t"
    w = nb / "wiki" / "research"
    w.mkdir(parents=True)
    (nb / "raw").mkdir()
    (nb / "raw" / "a.md").write_text("raw\n", encoding="utf-8")
    (nb / "_inbox" / "reports").mkdir(parents=True)
    (tmp / "linked-notebooks.json").write_text(json.dumps({"notebooks": {"t": {"root": "notebooks/t"}}}),
                                               encoding="utf-8")
    proj = tmp / "project"
    (proj / ".claude").mkdir(parents=True)
    (proj / ".claude" / "wiki-config.json").write_text(json.dumps(
        {"notebook": "t", "registry": (tmp / "linked-notebooks.json").as_posix()}), encoding="utf-8")

    (w / "good.md").write_text(page("Good"), encoding="utf-8")
    (w / "internal.md").write_text(page("Internal", source_url="internal://session/2026-10-01-x", raw_path=None,
                                        tier="self"), encoding="utf-8")
    (w / "bad-date.md").write_text(page("Bad date", date="2026-13-45", review_after="next month"), encoding="utf-8")
    (w / "bad-url.md").write_text(page("Bad url", source_url="www.example.com/a"), encoding="utf-8")
    (w / "no-source.md").write_text(page("No source", source_url=None, ingested_by=None), encoding="utf-8")
    (w / "self-certified.md").write_text(page("Self certified", verified="verified"), encoding="utf-8")
    (w / "verified-ok.md").write_text(page("Verified ok", verified="verified"), encoding="utf-8")
    (nb / "_signals").mkdir()
    (nb / "_signals" / "verified-ok.json").write_text(json.dumps(
        {"slug": "verified-ok", "verified": "verified", "verified_by": "human", "verified_at": "2026-10-02T10:00:00-04:00"}),
        encoding="utf-8")

    env = fake_qmd_env(tmp / "bin", nb / "wiki", env={**os.environ, "PYTHONIOENCODING": "utf-8"})
    p = subprocess.run([sys.executable, str(SCRIPTS / "wiki-lint-mechanical.py"), "--topic", "t"],
                       cwd=proj, capture_output=True, text=True, encoding="utf-8", env=env)
    check("lint exits 0 (warn-only)", p.returncode == 0, (p.returncode, p.stderr[-300:]))
    report = nb / "_inbox" / "reports" / "lint-report.md"
    text = report.read_text(encoding="utf-8") if report.is_file() else ""
    m = re.search(r"^## [^\n]*Spec Enforcement[^\n]*$(.*?)(?=^## )", text, re.MULTILINE | re.DOTALL)
    sec = m.group(1) if m else ""
    check("the report has its Spec Enforcement section", bool(sec), text[:300])

    def listed(heading: str) -> str:
        mm = re.search(rf"^### {heading}[^\n]*$(.*?)(?=^###|\Z)", sec, re.MULTILINE | re.DOTALL)
        return mm.group(1) if mm else ""

    dates = listed("Dates not in ISO form")
    check("a date that is not a calendar date is listed, by field and value",
          "bad-date.md" in dates and "date" in dates and "2026-13-45" in dates, dates[:300])
    check("... and a review_after that is not a date", "next month" in dates, dates[:300])
    urls = listed("`source_url` not")
    check("a source_url that is neither http(s):// nor internal:// is listed", "bad-url.md" in urls, urls[:300])
    check("... an internal:// one is not", "internal.md" not in urls, urls[:300])
    missing = listed("Missing `source_url`")
    check("a page with no source_url and no ingested_by is listed with both",
          "no-source.md" in missing and "source_url" in missing and "ingested_by" in missing, missing[:300])
    selfc = listed("`verified: verified` with no verify record")
    check("verified: verified with no /wiki-verify record is listed", "self-certified.md" in selfc, selfc[:300])
    check("... one with the record in _signals/ is not", "verified-ok.md" not in selfc, selfc[:300])
    clean = [n for n in ("good.md", "internal.md") if n in sec]
    check("the clean pages appear nowhere in the section", not clean, clean)
    check("the report header counts them (dates by wrong value: two on one page)",
          bool(re.search(r"\*\*Spec enforcement[^\n]*dates not ISO=2[^\n]*"
                                                          r"source_url form=1[^\n]*self-certified=1", text)),
          [l for l in text.splitlines() if l.startswith("**Spec enforcement")])

failed = [n for ok, n in results if not ok]
for ok, n in results:
    print(("PASS " if ok else "FAIL ") + n)
print(f"\n{len(results) - len(failed)}/{len(results)} passed")
sys.exit(1 if failed else 0)
