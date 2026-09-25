#!/usr/bin/env python3
"""Are the backlinks wiki-update.py suggests worth having? A blind judgment, not shipped.

Task #53 (task #42, finding 8). Since 2026-09-24 a staged entry's `suggested_backlinks`
keep a single-word match only when the two entries share MIN_SHARED_TAGS tags. This
measures what that rule removes and what it keeps, on real entries:

    python tests/backlinks/judge_backlinks.py build --notebook agentic-design --entries 12 --out <dir>
        -> <dir>/pairs.json (shuffled, no bucket shown) and <dir>/key.json (the buckets)
    (a judge — a sub-agent given only pairs.json — writes <dir>/verdicts.json:
     [{"id": "p001", "related": true|false, "reason": "..."}])
    python tests/backlinks/judge_backlinks.py score --out <dir>

Each pair is (the new entry, an existing entry the old rule would have asked to link
back to it). "removed" = suggested before, dropped by the rule; "kept" = suggested
before and after; "new" = only suggested after the rule (it moved up into a freed slot).

Decision rule, set before the first run (2026-09-24, task #53): build option (b) — keep
a single-word match that the entry's own search ranks highly — if >= 10 of the 79
removed pairs of the first sample (about 1 in 8) are judged related. Separately, flag
the rule if fewer than half of the pairs it suggests (kept + new) are related.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import random
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
SCRIPTS = REPO / "bootstrap" / "scripts"
sys.path.insert(0, str(SCRIPTS))


def _wiki_update():
    spec = importlib.util.spec_from_file_location("wiki_update", SCRIPTS / "wiki-update.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _summary(path: Path) -> tuple[str, str]:
    """(title, TL;DR or the opening of the body), capped for the judge."""
    text = path.read_text(encoding="utf-8", errors="replace")
    m = re.search(r'^title:\s*"?(.*?)"?\s*$', text, re.M)
    title = m.group(1) if m else path.stem
    body = re.sub(r"\A---\n.*?\n---\n", "", text, flags=re.S)
    m = re.search(r"^##\s*TL;DR\s*\n+(.*?)(?=\n##\s|\Z)", body, re.M | re.S)
    gist = (m.group(1) if m else re.sub(r"^#.*$", "", body, flags=re.M)).strip()
    return title, re.sub(r"\s+", " ", gist)[:900]


def build(args) -> int:
    from _wiki_config import wiki_dir
    wu = _wiki_update()
    wiki = Path(wiki_dir(args.notebook))
    entries = sorted((p for p in wiki.rglob("*.md") if "/research/" in p.as_posix() and not p.name.startswith("_")),
                     key=lambda p: p.stat().st_mtime, reverse=True)[:args.entries]
    rows = []
    for e in entries:
        title, _ = _summary(e)
        inbound = wu.find_inbound_candidates(e, wiki, title)
        rule = wu.MIN_SHARED_TAGS
        wu.MIN_SHARED_TAGS = 0
        old = [p for p, _, _ in wu._curate_backlink_candidates(inbound, wiki, max_n=8, entry_path=e)]
        wu.MIN_SHARED_TAGS = rule
        new = [p for p, _, _ in wu._curate_backlink_candidates(inbound, wiki, max_n=8, entry_path=e)]
        for p in dict.fromkeys(old + new):
            bucket = "kept" if p in old and p in new else ("removed" if p in old else "new")
            rows.append((e, p, bucket))
    random.Random(args.seed).shuffle(rows)
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    pairs, key = [], {}
    for i, (e, p, bucket) in enumerate(rows, 1):
        pid = f"p{i:03d}"
        (nt, ng), (tt, tg) = _summary(e), _summary(p)
        pairs.append({"id": pid, "new_entry": {"title": nt, "gist": ng}, "existing_entry": {"title": tt, "gist": tg}})
        key[pid] = {"bucket": bucket, "new_entry": e.relative_to(wiki).as_posix(),
                    "existing_entry": p.relative_to(wiki).as_posix()}
    (out / "pairs.json").write_text(json.dumps(pairs, indent=1, ensure_ascii=False), encoding="utf-8")
    (out / "key.json").write_text(json.dumps(key, indent=1, ensure_ascii=False), encoding="utf-8")
    counts = {b: sum(1 for v in key.values() if v["bucket"] == b) for b in ("removed", "kept", "new")}
    print(f"{len(pairs)} pairs from {len(entries)} entries: {counts} -> {out}")
    return 0


def score(args) -> int:
    out = Path(args.out)
    key = json.loads((out / "key.json").read_text(encoding="utf-8"))
    verdicts = {v["id"]: v for v in json.loads((out / "verdicts.json").read_text(encoding="utf-8"))}
    missing = sorted(set(key) - set(verdicts))
    if missing:
        print(f"no verdict for {len(missing)} pairs: {missing[:10]}")
        return 2
    lines = []
    for b in ("removed", "kept", "new"):
        ids = [i for i, v in key.items() if v["bucket"] == b]
        yes = [i for i in ids if verdicts[i]["related"]]
        lines.append(f"{b:8} {len(yes):3} of {len(ids):3} judged related ({100 * len(yes) / max(len(ids), 1):.0f}%)")
    suggested = [i for i, v in key.items() if v["bucket"] in ("kept", "new")]
    removed = [i for i, v in key.items() if v["bucket"] == "removed"]
    rel_removed = sum(verdicts[i]["related"] for i in removed)
    rel_suggested = sum(verdicts[i]["related"] for i in suggested)
    lines.append("")
    lines.append(f"rule 1 (build option b if >= 1 in 8 removed are related): {rel_removed}/{len(removed)} -> "
                 + ("BUILD (b)" if removed and rel_removed * 8 >= len(removed) else "keep the rule as is"))
    lines.append(f"rule 2 (flag if < half of what it suggests is related): {rel_suggested}/{len(suggested)} -> "
                 + ("FLAG" if suggested and rel_suggested * 2 < len(suggested) else "ok"))
    lines.append("")
    lines.append("removed but judged related:")
    for i in removed:
        if verdicts[i]["related"]:
            lines.append(f"  {key[i]['new_entry']}  <-  {key[i]['existing_entry']}  ({verdicts[i].get('reason', '')[:120]})")
    report = "\n".join(lines)
    (out / "score.md").write_text(report + "\n", encoding="utf-8")
    print(report)
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    b = sub.add_parser("build")
    b.add_argument("--notebook", required=True)
    b.add_argument("--entries", type=int, default=12, help="the N most recently changed research entries")
    b.add_argument("--seed", type=int, default=24)
    b.add_argument("--out", required=True)
    s = sub.add_parser("score")
    s.add_argument("--out", required=True)
    args = ap.parse_args()
    return build(args) if args.cmd == "build" else score(args)


if __name__ == "__main__":
    sys.exit(main())
