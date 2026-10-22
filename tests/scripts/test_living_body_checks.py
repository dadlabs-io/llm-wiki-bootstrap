#!/usr/bin/env python3
"""Checks for two body-check exemptions in scripts/_entry_checks.py (task #187, found checking
investment-agent's design rebuild 2026-10-20). Never shipped.

    python tests/scripts/test_living_body_checks.py   # exit 0 = every check passed

1. A forward pointer on a `>` line that opens with a bold label and a link to a wiki page
   ("> **Current design:** [60 Members](../architecture/60-members.md) (2026-10-20). ...") is our
   own note, not source text: the quote check must not compare it with the raw.
2. A `kind: living` page states how our own system works now; its figures (timeouts, sizes) are
   not claims from an outside source, so the numbers-in-prose rule does not apply to it.
Everything else stays checked: a real quote on such a page, numbers on any other page.
"""
from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[2] / "scripts"
sys.path.insert(0, str(SCRIPTS))
import _entry_checks as ec  # noqa: E402

results: list[tuple[bool, str]] = []


def check(name: str, ok: bool):
    results.append((ok, name))


RAW = "The committee roster is read from the house clerk's XML feed once a day and stored as dated intervals."
BANNER = ("> **Current design:** [70 Committees](../architecture/70-committees.md) (2026-10-20). "
          "The raw intervals, the three answers and the old commands it describes are history.\n")
BODY = "## TL;DR\n\nHow committees are ingested.\n\n## Related\n\n- [a](a.md)\n- [b](b.md)\n"


def quote_warnings(body: str, raw: str | None, **kw) -> list[str]:
    return [w for w in ec.check_entry_body(body, tags=["a", "b", "c"], raw_text=raw, **kw)["warnings"]
            if "quoted fragment" in w]


def number_warnings(body: str, **kw) -> list[str]:
    return [w for w in ec.check_entry_body(body, tags=["a", "b", "c"], **kw)["warnings"] if "numeric claim" in w]


# ── 1. the forward-pointer banner ───────────────────────────────────────────
check("banner: a bold-label pointer to a wiki page is not checked against the raw",
      quote_warnings(BANNER + "\n" + BODY, RAW) == [])
check("banner: a real misquote on the same page is still reported",
      any("not found" in w for w in quote_warnings(
          BANNER + "\n" + BODY + '\n> "the roster is scraped from the senate website every hour"\n', RAW)))
check("banner: a correct quote on the same page stays clean",
      quote_warnings(BANNER + "\n" + BODY + '\n> "read from the house clerk\'s XML feed once a day"\n', RAW) == [])
check("bold label with no wiki link is still a quote to check",
      any("not found" in w for w in quote_warnings(
          '> **Speaker:** "the roster is scraped from the senate website every hour"\n\n' + BODY, RAW)))

# ── 2. figures on a living page ─────────────────────────────────────────────
FIGURES = BODY + "\nA failed upload is retried for 120 seconds; chunks are 8 MB; the per-request timeout is 30 seconds.\n"
check("living: kind living skips the numbers-in-prose warning", number_warnings(FIGURES, kind="living") == [])
check("living: the same figures on a page with no kind still warn", bool(number_warnings(FIGURES)))
check("living: the same figures on a history page still warn", bool(number_warnings(FIGURES, kind="history")))
_fm = "---\ntitle: Upload sync\nkind: living\ntier: self\ntags: [a, b, c]\n---\n\n"
check("living: check_entry_text reads kind from the frontmatter",
      not any("numeric claim" in w for w in ec.check_entry_text(_fm + FIGURES)["warnings"]))

# ── the lint, end to end ────────────────────────────────────────────────────
with tempfile.TemporaryDirectory() as td:
    td = Path(td)
    nb = td / "vault" / "nb"
    arch, dec = nb / "wiki" / "project" / "architecture", nb / "wiki" / "project" / "decisions"
    arch.mkdir(parents=True)
    dec.mkdir(parents=True)
    (nb / "raw").mkdir()
    (nb / "raw" / "committees.md").write_text(RAW, encoding="utf-8")
    (arch / "70-committees.md").write_text(
        "---\ntitle: 70 Committees\ndate: 2026-10-20\nkind: living\ntier: self\nconfidence: high\n"
        "tags: [a, b, c]\nlast_reviewed: 2026-10-20\nreview_after: 2027-01-18\n---\n\n" + FIGURES, encoding="utf-8")
    (dec / "committee-ingest-2026-09-24.md").write_text(
        "---\ntitle: Committee ingest\ndate: 2026-09-24\nkind: history\ntier: self\nconfidence: high\n"
        "raw_path: raw/committees.md\ntags: [a, b, c]\nlast_reviewed: 2026-09-24\nreview_after: 2026-12-23\n---\n\n"
        + BANNER + "\n" + BODY + "\n[70](../architecture/70-committees.md)\n", encoding="utf-8")
    p = subprocess.run([sys.executable, str(SCRIPTS / "wiki-lint-mechanical.py"), "--vault", str(td / "vault"),
                        "--topic", "nb"], capture_output=True, text=True, encoding="utf-8", timeout=120)
    lines = p.stdout.splitlines()
    check("lint: no numeric warning on the living page",
          not any("70-committees.md" in l and "numeric claim" in l for l in lines))
    check("lint: no quote warning on the history page's banner",
          not any("committee-ingest" in l and "quoted fragment" in l for l in lines))

failed = [n for ok, n in results if not ok]
for ok, n in results:
    print(("PASS " if ok else "FAIL ") + n)
print(f"\n{len(results) - len(failed)}/{len(results)} passed")
sys.exit(1 if failed else 0)
