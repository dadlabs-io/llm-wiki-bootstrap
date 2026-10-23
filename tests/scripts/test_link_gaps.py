#!/usr/bin/env python3
"""Checks for task #201: wiki-link-gaps.py, the link-gap pass as a standing tool (suggest a review sheet of
Related-link candidates for thin and recently filed entries; apply only the pairs the user ticked). Never shipped.

    uv run python tests/scripts/test_link_gaps.py    # exit 0 = every check passed

The search is replaced through WIKI_LINK_GAPS_SEARCH_FROM (a JSON file: target path -> result rows), so no
GPU or qmd index is needed. Everything runs in a temporary notebook and registry.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "wiki-link-gaps.py"
td = tempfile.TemporaryDirectory()
BASE = Path(td.name)
NB = BASE / "vault" / "notebooks" / "gapnb"
W = NB / "wiki"

results: list[tuple[bool, str]] = []


def check(name: str, ok: bool, detail: object = ""):
    results.append((bool(ok), name + (f"  [{detail}]" if not ok and detail != "" else "")))


def entry(rel: str, title: str, date: str, related: list[str] = (), extra_fm: str = "", heading: str = "Related") -> Path:
    p = W / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    links = "\n".join(f"- [{Path(r).stem}]({os.path.relpath(W / r, p.parent).replace(os.sep, '/')})" for r in related)
    p.write_text(f'---\ntitle: "{title}"\ndate: {date}\nsource_url: "https://example.com/{p.stem}"\n'
                 f"ingested_by: claude-code\ntier: 2\nconfidence: medium\ntags: [a, b, c]\n{extra_fm}---\n\n"
                 f"# {title}\n\n## TL;DR\n\n{title} explained in one line.\n\n## Body\n\nText.\n\n"
                 f"## {heading}\n\n{links}\n", encoding="utf-8")
    return p


# a: thin (no links); b: two links (not thin); c: one link, to a (thin); d: filed recently, two links
entry("research/active/a-memory-tiers.md", "Memory tiers", "2026-09-01")
entry("research/active/b-context-windows.md", "Context windows", "2026-09-01",
      ["research/active/c-retrieval.md", "research/active/d-new-paper.md"])
entry("research/active/c-retrieval.md", "Retrieval", "2026-09-01", ["research/active/a-memory-tiers.md"])
entry("research/active/d-new-paper.md", "New paper", "2026-10-20",
      ["research/active/b-context-windows.md", "research/active/c-retrieval.md"], heading="See also")
# e: two links, old: never a target, but a fair candidate for c (nothing links c and e yet)
entry("research/active/e-tool-use.md", "Tool use", "2026-09-01",
      ["research/active/a-memory-tiers.md", "research/active/b-context-windows.md"])
# never targets or candidates
(W / "sessions" / "main").mkdir(parents=True)
(W / "sessions" / "main" / "handoff.md").write_text("# handoff\n", encoding="utf-8")
(W / "HOME.md").write_text("---\ntitle: Home\n---\n# Home\n", encoding="utf-8")
entry("project/best-practices/framework/spec.md", "Spec", "2026-09-01", extra_fm="framework-contract: true\n")

reg = BASE / "vault" / "linked-notebooks.json"
reg.write_text(json.dumps({"notebooks": {"gapnb": {"root": "notebooks/gapnb"}}}), encoding="utf-8")
proj = BASE / "proj"
(proj / ".claude").mkdir(parents=True)
(proj / ".claude" / "wiki-config.json").write_text(json.dumps({"notebook": "gapnb", "registry": str(reg)}),
                                                   encoding="utf-8")


def row(rel: str, score: float, title: str = "") -> dict:
    return {"file": f"qmd://gapnb/wiki/{rel}", "score": score, "title": title or Path(rel).stem}


search = {
    "research/active/a-memory-tiers.md": [
        row("research/active/a-memory-tiers.md", 0.99),           # itself
        row("research/active/b-context-windows.md", 0.81, "Context windows"),
        row("research/active/c-retrieval.md", 0.70),             # already linked (c -> a): skip
        row("sessions/main/handoff.md", 0.95),                    # a session page: never
        row("HOME.md", 0.90),                                     # HOME: never
        row("project/best-practices/framework/spec.md", 0.88),    # a framework doc: never
        row("research/active/d-new-paper.md", 0.30),              # below the score floor
        {**row("research/active/d-new-paper.md", 0.0), "found_by": "keyword"},
    ],
    "research/active/c-retrieval.md": [row("research/active/d-new-paper.md", 0.66, "New paper"),  # d links c: skip
                                       row("research/active/e-tool-use.md", 0.62, "Tool use")],
    "research/active/d-new-paper.md": [row("research/active/a-memory-tiers.md", 0.77, "Memory tiers")],
}
sf = BASE / "search.json"
sf.write_text(json.dumps(search), encoding="utf-8")
ENV = {**os.environ, "WIKI_LINK_GAPS_SEARCH_FROM": str(sf), "PYTHONIOENCODING": "utf-8"}


def run(*args, env=None):
    return subprocess.run([sys.executable, str(SCRIPT), *args], capture_output=True, text=True, encoding="utf-8",
                          cwd=proj, env=env or ENV)


check("the script exists", SCRIPT.is_file(), SCRIPT)
sheet = NB / "_inbox" / "reports" / "sheet.md"
p = run("suggest", "--topic", "gapnb", "--since", "2026-10-15", "--out", str(sheet))
check("suggest exits 0", p.returncode == 0, p.stdout[-300:] + p.stderr[-300:])
text = sheet.read_text(encoding="utf-8") if sheet.is_file() else ""
lines = [ln for ln in text.splitlines() if ln.startswith("- [ ] ")]
check("the sheet is written", bool(text), sheet)
check("thin entry a gets the related candidate b",
      any("a-memory-tiers.md" in ln and "b-context-windows.md" in ln for ln in lines), lines)
check("a pair already linked one way is not suggested (a/c)",
      not any("a-memory-tiers.md" in ln and "c-retrieval.md" in ln for ln in lines), lines)
check("session pages, HOME and framework docs are never candidates",
      not any(x in text for x in ("handoff.md", "HOME.md", "spec.md")), text[:400])
check("candidates below the score floor are left out", not any("(0.30)" in ln for ln in lines), lines)
check("thin entry c is a target (one curated link)", any(ln.split(" -> ")[0].endswith("c-retrieval.md")
                                                         for ln in lines), lines)
check("an entry filed since --since is a target though not thin (d, under See also)",
      any(ln.split(" -> ")[0].endswith("d-new-paper.md") for ln in lines), lines)
check("an entry neither thin nor recent is not a target (b)",
      not any(ln.split(" -> ")[0].endswith("b-context-windows.md") for ln in lines), lines)
check("each pair appears once (d -> a and a -> d are one pair)",
      len({frozenset(ln.split(" (")[0][6:].split(" -> ")) for ln in lines}) == len(lines), lines)
check("the sheet says nothing is applied until ticked", "[x]" in text and "apply" in text.lower(), text[:300])
check("suggest writes no entry", "b-context-windows" not in (W / "research/active/a-memory-tiers.md").read_text(encoding="utf-8"))

# tick a/b only, then apply
ab = next((ln for ln in lines if "a-memory-tiers.md" in ln and "b-context-windows.md" in ln), None)
sheet.parent.mkdir(parents=True, exist_ok=True)
sheet.write_text(text.replace(ab, ab.replace("- [ ] ", "- [x] ", 1)) if ab else text, encoding="utf-8")
p = run("apply", "--topic", "gapnb", "--sheet", str(sheet), "--dry-run")
check("apply --dry-run writes nothing", p.returncode == 0 and "b-context-windows" not in
      (W / "research/active/a-memory-tiers.md").read_text(encoding="utf-8"), p.stdout[-300:] + p.stderr[-300:])
p = run("apply", "--topic", "gapnb", "--sheet", str(sheet))
a_txt = (W / "research/active/a-memory-tiers.md").read_text(encoding="utf-8")
b_txt = (W / "research/active/b-context-windows.md").read_text(encoding="utf-8")
check("apply exits 0", p.returncode == 0, p.stdout[-300:] + p.stderr[-300:])
check("the ticked pair is linked a -> b, in the Related section", "(b-context-windows.md)" in a_txt
      and a_txt.index("(b-context-windows.md)") > a_txt.index("## Related"), a_txt[-300:])
check("and b -> a", "(a-memory-tiers.md)" in b_txt, b_txt[-300:])
check("an unticked pair is not applied", "e-tool-use" not in (W / "research/active/c-retrieval.md").read_text(encoding="utf-8"))
p = run("apply", "--topic", "gapnb", "--sheet", "_inbox/reports/sheet.md")
check("a sheet path relative to the notebook is found (the sheet's own apply line)", p.returncode == 0,
      p.stdout[-200:] + p.stderr[-200:])
check("apply twice adds nothing twice", (W / "research/active/a-memory-tiers.md").read_text(encoding="utf-8")
      .count("(b-context-windows.md)") == 1, p.stdout[-200:])

# nothing checked never reads as clean: every search failing exits 3
bad = BASE / "bad.json"
bad.write_text(json.dumps({"_fail": True}), encoding="utf-8")
p = run("suggest", "--topic", "gapnb", "--out", str(BASE / "s2.md"), env={**ENV, "WIKI_LINK_GAPS_SEARCH_FROM": str(bad)})
check("every search failed: exit 3, NOT checked", p.returncode == 3 and "not checked" in (p.stdout + p.stderr).lower(),
      (p.returncode, p.stdout[-200:]))

sys.stdout.reconfigure(encoding="utf-8")
failed = [n for ok, n in results if not ok]
for ok, n in results:
    print(("PASS " if ok else "FAIL ") + n)
print(f"\n{len(results) - len(failed)}/{len(results)} passed")
sys.exit(1 if failed else 0)
