#!/usr/bin/env python3
"""Checks for wiki-claims-corroborate.py (task #110, 2026-10-13): claims that agree raise each
other's corroboration, counted by independent source and weighted by tier. Never shipped.

    python tests/scripts/test_claims_corroborate.py    # exit 0 = every check passed
"""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "wiki-claims-corroborate.py"
results: list[tuple[bool, str]] = []


def check(name: str, ok: bool, detail: object = ""):
    results.append((bool(ok), name + (f"  [{detail}]" if not ok and detail != "" else "")))


def entry(nb: Path, rel: str, tier, url: str, confidence: str = "medium"):
    p = nb / "wiki" / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(f"---\ntitle: {rel}\ntier: {tier}\nconfidence: {confidence}\nsource_url: {url}\n---\n\n# {rel}\n",
                 encoding="utf-8")


def claim(i, rel, agrees=(), origin=None, text="Opus is best for coding"):
    c = {"id": f"claim-{i:04d}", "claim": text, "source_entry": rel, "classification": "sourced",
         "confidence": 0.8, "subject": "opus", "predicate": "rank", "object": "best for coding"}
    if agrees:
        c["agrees_with"] = [f"claim-{a:04d}" for a in agrees]
    if origin:
        c["origin"] = origin
    return c


def run(nb: Path, *extra) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(SCRIPT), "--index", str(nb / "_inbox" / "claims-index.json"), *extra],
                          capture_output=True, text=True, encoding="utf-8", cwd=nb)


with tempfile.TemporaryDirectory() as td:
    tmp = Path(td)
    (tmp / ".claude").mkdir()
    reg = tmp / "linked-notebooks.json"
    reg.write_text(json.dumps({"notebooks": {"t": {"root": "nb"}}}), encoding="utf-8")
    (tmp / ".claude" / "wiki-config.json").write_text(json.dumps({"notebook": "t", "registry": reg.as_posix()}),
                                                      encoding="utf-8")
    nb = tmp / "nb"
    (nb / "_inbox").mkdir(parents=True)
    # group A: seven reels restating one benchmark (one origin) + nothing else -> one source
    for n in range(7):
        entry(nb, f"reel-{n}.md", 4, f"https://www.instagram.com/reel/r{n}/")
    # group B: three different tier-3 authors -> three sources
    for n in range(3):
        entry(nb, f"blog-{n}.md", 3, f"https://blog{n}.example.com/post")
    # group C: one tier-1 paper and one tier-4 reel restating it (origin = the paper URL) -> one source, tier 1
    entry(nb, "paper.md", 1, "https://arxiv.org/abs/2610.00001", confidence="low")
    entry(nb, "reel-paper.md", 4, "https://www.instagram.com/reel/rp/")
    # D: a high-confidence entry whose only agreement is a tier-4 repost of itself
    entry(nb, "vendor.md", 4, "https://vendor.example.com/a", confidence="high")
    entry(nb, "vendor-repost.md", 4, "https://www.instagram.com/reel/vr/")
    # E: our own synthesis agreeing with one tier-3 blog
    entry(nb, "ours.md", "self", "internal://synthesis/x")
    entry(nb, "blog-e.md", 3, "https://e.example.com/p")
    # F: a lone tier-4 claim, no agreement; G: two claims in one entry agreeing with each other
    entry(nb, "lone.md", 4, "https://lone.example.com/")
    entry(nb, "same.md", 2, "https://same.example.com/")
    cl = [claim(1 + n, f"reel-{n}.md", agrees=[1] if n else (), origin="LiveCodeBench leaderboard 2026-09") for n in range(7)]
    cl += [claim(10, "blog-0.md", agrees=[11, 12]), claim(11, "blog-1.md"), claim(12, "blog-2.md")]
    cl += [claim(20, "paper.md"), claim(21, "reel-paper.md", agrees=[20], origin="https://arxiv.org/abs/2610.00001v2")]
    cl += [claim(30, "vendor.md"), claim(31, "vendor-repost.md", agrees=[30], origin="https://vendor.example.com/a")]
    cl += [claim(40, "ours.md"), claim(41, "blog-e.md", agrees=[40])]
    cl += [claim(50, "lone.md"), claim(60, "same.md"), claim(61, "same.md", agrees=[60]),
           claim(70, "lone.md", agrees=[999])]
    cl.append({**claim(80, "blog-0.md"), "corroboration": {"group": ["claim-0080", "claim-0081"], "score": 9}})
    # H: a low-confidence entry agreeing with two independent tier-2 sources (score 1.2 + its own 0.1)
    entry(nb, "doubtful.md", 4, "https://doubt.example.com/", confidence="low")
    entry(nb, "t2-a.md", 2, "https://a2.example.com/")
    entry(nb, "t2-b.md", 2, "https://b2.example.com/")
    cl += [claim(90, "doubtful.md", agrees=[91, 92]), claim(91, "t2-a.md"), claim(92, "t2-b.md")]
    idx = nb / "_inbox" / "claims-index.json"
    idx.write_text(json.dumps({"claims": cl}), encoding="utf-8")

    p = run(nb, "--dry-run")
    check("dry run exits 0", p.returncode == 0, p.stderr)
    check("dry run writes nothing", "corroboration_computed" not in idx.read_text(encoding="utf-8"))

    rep = nb / "corr.md"
    p = run(nb, "--report", str(rep))
    check("run exits 0 and prints JSON", p.returncode == 0 and p.stdout.strip().startswith("{"), p.stderr)
    out = json.loads(p.stdout) if p.returncode == 0 else {}
    data = json.loads(idx.read_text(encoding="utf-8"))
    by = {c["id"]: c for c in data["claims"]}

    a = by["claim-0001"].get("corroboration", {})
    check("seven reposts of one origin: one independent source", a.get("independent_sources") == 1, a)
    check("seven tier-4 reposts score 0.1", a.get("score") == 0.1, a.get("score"))
    check("the merge is shown with its reason",
          any("same origin" in m for s in a.get("sources", []) for m in s.get("merged_because", [])), a.get("sources"))
    b = by["claim-0010"].get("corroboration", {})
    check("three different tier-3 sources: three sources, score 0.9",
          b.get("independent_sources") == 3 and b.get("score") == 0.9, b)
    check("every claim in a group carries the record", all("corroboration" in by[f"claim-{i:04d}"] for i in (10, 11, 12)))
    c = by["claim-0020"].get("corroboration", {})
    check("a repost citing the paper's URL merges with the paper (arXiv version ignored)",
          c.get("independent_sources") == 1 and len(c.get("sources", [])) == 1, c)
    check("the merged source counts at its best tier (1.0)", c.get("score") == 1.0, c.get("score"))
    check("three tier-3 sources do not outrank one tier-1 paper", b.get("score", 9) < c.get("score", 0))
    d = by["claim-0030"].get("corroboration", {})
    check("a repost of the same vendor page adds nothing (0.1)", d.get("score") == 0.1, d)
    e = by["claim-0040"].get("corroboration", {})
    check("our own synthesis is listed but weighs 0",
          e.get("independent_sources") == 1 and e.get("score") == 0.3
          and any(s.get("tier") == "self" and s.get("weight") == 0 for s in e.get("sources", [])), e)
    check("a lone claim gets no record", "corroboration" not in by["claim-0050"])
    check("agreement inside one entry is not corroboration",
          "corroboration" not in by["claim-0060"] and "corroboration" not in by["claim-0061"])
    check("a stale record on a claim with no group is removed", "corroboration" not in by["claim-0080"])
    check("an unknown agrees_with id is counted, not fatal", out.get("unknown_agrees_with") == 1, out)
    flags = {f["claim"]: f["why"] for f in out.get("flags", [])}
    check("high-confidence entry, thinly corroborated, is flagged", "claim-0030" in flags, flags)
    check("a low-confidence entry backed by one source (even tier 1) is not called well corroborated",
          "claim-0020" not in flags, flags)
    check("a low-confidence entry backed by two independent tier-2 sources is flagged", "claim-0090" in flags, flags)
    check("summary counts groups (A, B, C, D, E, H)", out.get("groups") == 6, out.get("groups"))
    check("summary counts claims resting on a single tier-4 entry (lone x2)", out.get("single_tier4_claims") == 2,
          out.get("single_tier4_claims"))
    check("the entry's own confidence is never changed",
          "confidence: low" in (nb / "wiki" / "paper.md").read_text(encoding="utf-8"))
    rtext = rep.read_text(encoding="utf-8") if rep.exists() else ""
    check("report section lists groups and the disagreements",
          "## Corroboration" in rtext and "Confidence and corroboration disagree" in rtext and "claim-0030" in rtext, rtext[:300])
    check("summary counts the index's claims and entries",
          out.get("index_claims") == len(cl) and out.get("index_entries") == len({c["source_entry"] for c in cl}), out)
    p3 = subprocess.run([sys.executable, str(SCRIPT), "--report", "_inbox/reports/rel.md"],
                        capture_output=True, text=True, encoding="utf-8", cwd=tmp)
    check("a relative --report lands in the notebook, not the cwd",
          p3.returncode == 0 and (nb / "_inbox" / "reports" / "rel.md").exists()
          and not (tmp / "_inbox" / "reports" / "rel.md").exists(), p3.stderr)
    p2 = run(nb)
    data2 = json.loads(idx.read_text(encoding="utf-8"))
    check("a second run gives the same records",
          [c.get("corroboration", {}).get("score") for c in data2["claims"]]
          == [c.get("corroboration", {}).get("score") for c in data["claims"]])
    bad = nb / "_inbox" / "bad.json"
    bad.write_text("{not json", encoding="utf-8")
    p = subprocess.run([sys.executable, str(SCRIPT), "--index", str(bad)], capture_output=True, text=True, cwd=nb)
    check("unparsable index: exit 2", p.returncode == 2, p.returncode)

failed = [n for ok, n in results if not ok]
for ok, n in results:
    print(("PASS " if ok else "FAIL ") + n)
print(f"\n{len(results) - len(failed)}/{len(results)} passed")
sys.exit(1 if failed else 0)
