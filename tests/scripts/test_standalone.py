#!/usr/bin/env python3
"""Checks for task #54: a page declares itself standalone. Never shipped.

    python tests/scripts/test_standalone.py    # exit 0 = every check passed

Until 2026-09-24 the mechanical lint listed every page with no inbound link as an
orphan, and the cycle contract called a run clean at `orphans <= 1`, an allowance
for the wiki's HOME page. The user's rule (2026-09-24): one mechanism, no built-in
list. A page whose frontmatter carries `standalone: "<reason>"` is left off the
orphan list and listed apart with its reason; the allowance goes. A `standalone:`
with no reason (blank, `true`, `yes`) is not honoured: the page stays an orphan and
the report says why.
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
FRAMEWORK = ROOT / "bootstrap" / "topic-template" / "wiki" / "best-practices" / "framework"

results: list[tuple[bool, str]] = []


def check(name: str, ok: bool, detail: object = ""):
    results.append((bool(ok), name + (f"  [{detail}]" if not ok and detail != "" else "")))


def page(title: str, body: str, extra: str = "") -> str:
    return (f"---\ntitle: \"{title}\"\ndate: 2026-09-01\ntier: self\nconfidence: high\n"
            f"tags: [x, y, z]\n{extra}---\n\n# {title}\n\n{body}\n")


def frontmatter(text: str) -> dict:
    m = re.match(r"^---\s*\n(.*?)\n---\s*\n", text, re.DOTALL)
    if not m:
        return {}
    try:
        import yaml
        return yaml.safe_load(m.group(1)) or {}
    except ImportError:
        return {k.strip(): v.strip().strip("\"'") for k, _, v in
                (l.partition(":") for l in m.group(1).splitlines() if ":" in l)}


def version(path: Path) -> int:
    return int(frontmatter(path.read_text(encoding="utf-8")).get("framework-version", 0))


# ── the lint ─────────────────────────────────────────────────────────────────
with tempfile.TemporaryDirectory() as td:
    tmp = Path(td)
    nb = tmp / "notebooks" / "t"
    w = nb / "wiki"
    (w / "research").mkdir(parents=True)
    (nb / "_inbox" / "reports").mkdir(parents=True)
    (tmp / "linked-notebooks.json").write_text(json.dumps({"notebooks": {"t": {"root": "notebooks/t"}}}),
                                               encoding="utf-8")
    proj = tmp / "project"
    (proj / ".claude").mkdir(parents=True)
    (proj / ".claude" / "wiki-config.json").write_text(json.dumps(
        {"notebook": "t", "registry": (tmp / "linked-notebooks.json").as_posix()}), encoding="utf-8")

    (w / "HOME.md").write_text(page("Home", "- [A](research/a.md)",
                                    'standalone: "the landing page: reading starts here"\n'), encoding="utf-8")
    (w / "research" / "a.md").write_text(page("A", "- [B](b.md)\n- [Linked](linked.md)"), encoding="utf-8")
    (w / "research" / "b.md").write_text(page("B", "- [A](a.md)"), encoding="utf-8")
    (w / "research" / "orphan.md").write_text(page("Orphan", "nothing links here"), encoding="utf-8")
    (w / "research" / "blank.md").write_text(page("Blank", "no reason", 'standalone: ""\n'), encoding="utf-8")
    (w / "research" / "bare-true.md").write_text(page("Bare", "no reason", "standalone: true\n"), encoding="utf-8")
    (w / "research" / "linked.md").write_text(page("Linked", "has a link in", 'standalone: "a hub"\n'),
                                              encoding="utf-8")

    run = nb / "_inbox" / "reports" / "2026-09-24" / "2026-09-24-01"
    env = {**os.environ, "PYTHONIOENCODING": "utf-8"}
    p = subprocess.run([sys.executable, str(SCRIPTS / "wiki-lint-mechanical.py"), "--topic", "t",
                        "--cycle-id", "2026-09-24-01", "--run-folder", str(run)],
                       cwd=proj, capture_output=True, text=True, encoding="utf-8", env=env)
    check("lint exits 0", p.returncode == 0, p.stderr[-300:])
    jp = run / "lint-mechanical.json"
    d = json.loads(jp.read_text(encoding="utf-8")) if jp.is_file() else {}
    orphans = sorted(d.get("orphans") or [])
    check("a page with no inbound link and no `standalone:` is an orphan", "research/orphan.md" in orphans, orphans)
    check("HOME.md with a reason is not an orphan", "HOME.md" not in orphans, orphans)
    check("a blank `standalone:` is not honoured", "research/blank.md" in orphans, orphans)
    check("`standalone: true` (no reason) is not honoured", "research/bare-true.md" in orphans, orphans)
    check("the orphan count is the three", (d.get("summary") or {}).get("orphans") == 3, d.get("summary"))
    sa = d.get("standalone")
    check("JSON lists the standalone pages apart, with the reason",
          sa == [{"file": "HOME.md", "reason": "the landing page: reading starts here"}], sa)
    check("summary counts the standalone pages", (d.get("summary") or {}).get("standalone") == 1, d.get("summary"))
    check("a standalone page that has inbound links is in neither list",
          "research/linked.md" not in orphans and all(s.get("file") != "research/linked.md" for s in sa or []), sa)

    report = (nb / "_inbox" / "reports" / "lint-report.md")
    text = report.read_text(encoding="utf-8") if report.is_file() else ""
    m = re.search(r"^## [^\n]*Standalone[^\n]*$(.*?)(?=^## )", text, re.MULTILINE | re.DOTALL)
    check("the report has a Standalone section", bool(m), text[:300])
    sec = m.group(1) if m else ""
    check("the section names HOME.md with its reason",
          "HOME.md" in sec and "the landing page: reading starts here" in sec, sec[:300])
    check("the report header counts standalone pages", "**Standalone pages**: 1" in text, text[:600])
    om = re.search(r"^## [^\n]*Orphan[^\n]*$(.*?)(?=^## )", text, re.MULTILINE | re.DOTALL)
    osec = om.group(1) if om else ""
    check("the orphan section says a reason-less `standalone:` is not honoured",
          bool(re.search(r"blank\.md[^\n]*standalone[^\n]*reason", osec))
          and bool(re.search(r"bare-true\.md[^\n]*standalone[^\n]*reason", osec)),
          osec[:400])
    check("the orphan section tells how to declare a page standalone", "standalone:" in osec, osec[:400])

# ── the docs ─────────────────────────────────────────────────────────────────
csf = FRAMEWORK / "cycle-step-return-format.md"
ctext = csf.read_text(encoding="utf-8")
check("the cycle contract drops the `orphans <= 1` allowance", "orphans <= 1" not in ctext)
check("the cycle contract: a clean run has no orphans",
      "summary.orphans == 0" in ctext, [l for l in ctext.splitlines() if "clean run" in l])
check("the cycle contract names the standalone array", "standalone: [{file, reason}]" in ctext)
check("cycle-step-return-format framework-version bumped to 3", version(csf) == 3, version(csf))

fm = FRAMEWORK / "wiki-frontmatter-best-practices.md"
ftext = fm.read_text(encoding="utf-8")
check("the frontmatter spec has a `standalone` optional-field row", "| `standalone` |" in ftext)
check("wiki-frontmatter-best-practices framework-version bumped to 13", version(fm) == 13, version(fm))

for home in (ROOT / "bootstrap" / "seed" / "wiki" / "HOME.md.tmpl",):
    reason = str(frontmatter(home.read_text(encoding="utf-8")).get("standalone") or "")
    check(f"{home.relative_to(ROOT).as_posix()} declares itself standalone with a reason",
          reason.strip().lower() not in {"", "true", "yes"}, reason)

failed = [n for ok, n in results if not ok]
for ok, n in results:
    print(("PASS " if ok else "FAIL ") + n)
print(f"\n{len(results) - len(failed)}/{len(results)} passed")
sys.exit(1 if failed else 0)
