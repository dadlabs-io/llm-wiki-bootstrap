#!/usr/bin/env python3
"""wiki-claims-corroborate.py — score how well each claim is backed by sources that agree.

/wiki-claims compares claims by subject. Until 2026-10-13 it looked only for conflicts: seven
entries saying the same thing earned a claim nothing (task #110, Mark: "seven articles that say
Opus is best for coding rank higher than one"). The model now records agreement on the claims
themselves, and this script does the arithmetic:

- `agrees_with: [<claim id>, ...]` on a claim: another entry's claim that states the same fact.
  Agreement is symmetric and transitive here: linked claims form one group.
- `origin: "<url or name>"` on a claim: the original evidence it restates (a paper, a benchmark,
  a vendor dashboard, a person), when the entry is not that original itself.

For each group the script finds the independent sources behind it. Two claims are one source
when they share an origin, or, without one, the same source URL (`_source_identity.source_key`):
seven reposts of one benchmark count once (Mark: "the same person saying it seven times isn't as
strong as three different people"). Each source counts by the best tier among its entries'
frontmatter, weighted 1.0 / 0.6 / 0.3 / 0.1 for tiers 1-4 (Mark, 2026-10-13); a `self` entry
(our own synthesis) is listed but weighs 0. The sum is the group's score.

Every claim in a group gets a `corroboration` field: the group's claim ids, its sources (key,
entries, tier, weight and why claims were merged into it), `independent_sources`, `score`, and the
date. The merges are shown, never hidden: deciding that two claims share an original is a best
guess, and a wrong one should be visible and correctable. An entry's own `confidence` is never
changed; the script flags where the two disagree (an entry at high confidence whose claim has a
score under 0.3, or one at low confidence whose claim scores 1.0 or more from two or more
independent sources).

    wiki-claims-corroborate.py --topic <notebook>                    # score, write the index, print a summary
    wiki-claims-corroborate.py --topic <notebook> --dry-run          # print, write nothing
    wiki-claims-corroborate.py --topic <notebook> --report <file.md> # also write the report's section

Exit 0 on success (a summary JSON on stdout), 2 on bad input (no index, unparsable JSON).
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _wiki_config  # noqa: E402
from _atomic_io import atomic_write_text  # noqa: E402
from _source_identity import source_key  # noqa: E402

WEIGHTS = {"1": 1.0, "2": 0.6, "3": 0.3, "4": 0.1}
WELL = 1.0       # a group at or above this score, from two or more independent sources, is well corroborated
THIN = 0.3       # a high-confidence entry's claim under this is flagged


def _front(path: Path) -> dict:
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return {}
    m = re.match(r"\A---\s*\n(.*?)\n---", text, re.S)
    out = {}
    for line in (m.group(1).splitlines() if m else []):
        k, _, v = line.partition(":")
        if v and not line.startswith((" ", "-", "\t")):
            out[k.strip()] = v.strip().strip("\"'")
    return out


def _tier_out(t: str):
    """The tier as the frontmatter means it: a number for 1-4, the word for `self` (or what else is written)."""
    return int(t) if t.isdigit() else t


def _origin_key(origin: str) -> str:
    o = origin.strip()
    if re.match(r"https?://", o, re.I):
        return source_key(o)
    return "origin:" + re.sub(r"[^a-z0-9]+", " ", o.lower()).strip()


class _Union:
    def __init__(self):
        self.p: dict = {}

    def find(self, x):
        self.p.setdefault(x, x)
        while self.p[x] != x:
            self.p[x] = self.p[self.p[x]]
            x = self.p[x]
        return x

    def join(self, a, b):
        self.p[self.find(a)] = self.find(b)


def score(index: dict, wiki: Path, today: str) -> dict:
    claims = index.get("claims") or []
    by_id = {str(c.get("id")): c for c in claims if c.get("id")}
    entries: dict[str, dict] = {}

    def entry(rel: str) -> dict:
        if rel not in entries:
            fm = _front(wiki / rel)
            entries[rel] = {"tier": str(fm.get("tier", "")).strip(), "confidence": fm.get("confidence", ""),
                            "source_url": fm.get("source_url", ""), "found": bool(fm)}
        return entries[rel]

    groups = _Union()
    unknown = []
    for c in claims:
        cid = str(c.get("id", ""))
        for other in c.get("agrees_with") or []:
            if str(other) in by_id:
                groups.join(cid, str(other))
            else:
                unknown.append({"claim": cid, "agrees_with": str(other)})

    members: dict[str, list[dict]] = {}
    for c in claims:
        cid = str(c.get("id", ""))
        if cid in groups.p:
            members.setdefault(groups.find(cid), []).append(c)

    stats = {"groups": 0, "claims_corroborated": 0, "well_corroborated_groups": 0, "flags": [],
             "unknown_agrees_with": unknown, "entries_missing": []}
    in_group = set()
    for root, cs in members.items():
        if len({c.get("source_entry") for c in cs}) < 2:
            continue   # agreement inside one entry is not corroboration
        stats["groups"] += 1
        why: dict[str, set] = {}
        claim_key = {}
        for c in cs:
            e = entry(c.get("source_entry", ""))
            if not e["found"]:
                stats["entries_missing"].append(c.get("source_entry"))
            url = e["source_url"]
            url_key = source_key(url) if re.match(r"https?://", url or "", re.I) else "entry:" + str(c.get("source_entry"))
            if c.get("origin"):
                k = _origin_key(str(c["origin"]))
                why.setdefault(k, set()).add(f"same origin: {c['origin']}")
            else:
                k = url_key
                why.setdefault(k, set()).add("same source URL")
            claim_key[str(c.get("id"))] = k
        sources: dict[str, dict] = {}
        for c in cs:
            k = claim_key[str(c.get("id"))]
            e = entry(c.get("source_entry", ""))
            s = sources.setdefault(k, {"key": k, "entries": [], "claims": [], "tier": None, "weight": 0.0,
                                       "merged_because": sorted(why.get(k, set()))})
            if c.get("source_entry") not in s["entries"]:
                s["entries"].append(c.get("source_entry"))
            s["claims"].append(str(c.get("id")))
            w = WEIGHTS.get(e["tier"], 0.0)
            if w > s["weight"]:
                s["weight"], s["tier"] = w, _tier_out(e["tier"])
            elif s["tier"] is None:
                s["tier"] = _tier_out(e["tier"]) or "unknown"
        for s in sources.values():
            if len(s["claims"]) < 2:
                s["merged_because"] = []
        total = round(sum(s["weight"] for s in sources.values()), 2)
        independent = sum(1 for s in sources.values() if s["weight"] > 0)
        if total >= WELL and independent >= 2:
            stats["well_corroborated_groups"] += 1
        record = {"group": sorted(str(c.get("id")) for c in cs), "sources": list(sources.values()),
                  "independent_sources": independent, "score": total, "computed": today}
        for c in cs:
            c["corroboration"] = record
            in_group.add(str(c.get("id")))
            stats["claims_corroborated"] += 1
            conf = entry(c.get("source_entry", ""))["confidence"]
            if conf == "high" and total < THIN:
                stats["flags"].append({"claim": c.get("id"), "entry": c.get("source_entry"), "confidence": conf,
                                       "score": total, "why": "high-confidence entry, thinly corroborated"})
            elif conf == "low" and total >= WELL and independent >= 2:
                stats["flags"].append({"claim": c.get("id"), "entry": c.get("source_entry"), "confidence": conf,
                                       "score": total, "why": "low-confidence entry, well corroborated"})
    for c in claims:   # a claim that left its group loses the old record
        if "corroboration" in c and str(c.get("id")) not in in_group:
            del c["corroboration"]
    single_t4 = [c for c in claims if str(c.get("id")) not in in_group
                 and entry(c.get("source_entry", ""))["tier"] == "4"]
    stats["single_tier4_claims"] = len(single_t4)
    stats["index_claims"] = len(claims)
    stats["index_entries"] = len({c.get("source_entry") for c in claims if c.get("source_entry")})
    stats["entries_missing"] = sorted(set(filter(None, stats["entries_missing"])))
    return stats


def report_section(index: dict, stats: dict) -> str:
    claims = index.get("claims") or []
    seen, groups = set(), []
    for c in claims:
        r = c.get("corroboration")
        if r and tuple(r["group"]) not in seen:
            seen.add(tuple(r["group"]))
            groups.append((r, c))
    groups.sort(key=lambda g: -g[0]["score"])

    def cell(s):
        return str(s or "").replace("|", "/").replace("\n", " ")[:160]

    out = ["## Corroboration", "",
           f"{stats['groups']} groups of agreeing claims ({stats['claims_corroborated']} claims); "
           f"{stats['well_corroborated_groups']} well corroborated (score >= {WELL} from 2+ independent sources); "
           f"{stats['single_tier4_claims']} claims rest on a single tier-4 entry.", "",
           "| Score | Sources | Claim | Sources counted (merged because) |", "|---|---|---|---|"]
    for r, c in groups:
        srcs = "; ".join(f"T{s['tier']} {', '.join(s['entries'])}" + (f" ({'; '.join(s['merged_because'])})" if s["merged_because"] else "")
                         for s in r["sources"])
        out.append(f"| {r['score']} | {r['independent_sources']} | {cell(c.get('claim'))} | {srcs.replace("|", "/")} |")
    out += ["", "### Confidence and corroboration disagree", ""]
    out += [f"- {f['claim']} in {f['entry']}: confidence {f['confidence']}, score {f['score']} ({f['why']})"
            for f in stats["flags"]] or ["None."]
    return "\n".join(out) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--topic", help="notebook name (registry); default: this project's")
    ap.add_argument("--index", help="claims index path (default: <notebook>/_inbox/claims-index.json)")
    ap.add_argument("--report", help="also write the report's Corroboration section to this file")
    ap.add_argument("--dry-run", action="store_true", help="print the summary, write nothing")
    a = ap.parse_args()
    root = Path(_wiki_config.topic_root(a.topic))
    idx_path = Path(a.index) if a.index else root / "_inbox" / "claims-index.json"
    if not idx_path.is_file():
        print(f"error: no claims index at {idx_path}", file=sys.stderr)
        return 2
    try:
        index = json.loads(idx_path.read_text(encoding="utf-8"))
    except ValueError as e:
        print(f"error: {idx_path} is not JSON: {e}", file=sys.stderr)
        return 2
    if not (index.get("claims") or []):  # nothing to score never reads as a clean result (task #133)
        print(f"NOT checked: {idx_path} holds no claims, so nothing was corroborated", file=sys.stderr)
        return 3
    stats = score(index, root / "wiki", _wiki_config.today_label())
    if not a.dry_run:
        index["corroboration_computed"] = _wiki_config.now_stamp()
        atomic_write_text(idx_path, json.dumps(index, indent=2, ensure_ascii=False))
        if a.report:
            rp = Path(a.report)
            rp = rp if rp.is_absolute() else root / rp   # a relative path is the notebook's, whatever the cwd
            rp.parent.mkdir(parents=True, exist_ok=True)
            atomic_write_text(rp, report_section(index, stats))
    print(json.dumps({k: (v if not isinstance(v, list) else (v if k == "flags" else len(v))) for k, v in stats.items()},
                     indent=1, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
