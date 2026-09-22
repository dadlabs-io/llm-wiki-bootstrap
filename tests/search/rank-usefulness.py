#!/usr/bin/env python3
"""
rank-usefulness.py — is `-k 20` the right cut, or should it be 40?

The depth check (`wiki-qmd-query.py --depth-check`) answers a different question:
it compares candidate limits (C vs 2C) and counts entries the deeper run surfaced
at all. That measures recall INTO the reranker. Nothing has ever measured whether
the results the reranker ranks 21-40 are worth showing — `-k 20` was chosen on
2026-09-13 from the shape of the scores (they plateau after about rank 3), not
from anyone judging the entries.

This script measures it, on real queries:

  1. Take N distinct queries from the search log (~/.cache/wiki-qmd/searches.jsonl),
     which is every search this framework has run. Synthetic skill-test queries and
     the depth check's own queries are excluded.
  2. Re-run each at -k 40 through the normal wrapper, so scope, sizing, machine-file
     and superseded filtering are exactly what a real search does.
  3. Ask a model to judge each returned entry against the query as `useful`,
     `redundant` (says what another entry already said) or `noise`.
     The entries are SHUFFLED and labelled before judging, so the judge never sees
     the rank — otherwise it would simply agree with the ranking.
  4. Report the useful rate for ranks 1-20 against ranks 21-40, and how often a
     query had anything useful below rank 20 at all.

Read the result like this: if ranks 21-40 are almost all redundant or noise, k=20
is right and now has evidence. If a few queries per twenty turn up something
genuinely useful down there, that argues for a larger k — which costs no GPU time,
since the reranker has already scored every candidate, only the reading agent's
attention.

Usage (from the repo root):
  python tests/search/rank-usefulness.py --dry-run          # plan + cost estimate, no spend
  python tests/search/rank-usefulness.py                    # 20 queries, sonnet
  python tests/search/rank-usefulness.py --queries 40 --model opus
  python tests/search/rank-usefulness.py --scope agentic-design --seed 7

Results land in tests/search/.results/<stamp>/ (report.md + judgments.json); nothing
here ships with the framework.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import re
import shutil
import statistics
import subprocess
import sys
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
WRAPPER = REPO / "bootstrap" / "scripts" / "wiki-qmd-query.py"
LOG = Path(os.environ.get("WIKI_QMD_SLOT_DIR") or Path.home() / ".cache" / "wiki-qmd") / "searches.jsonl"
SKIP_CALLERS = ("depth-check", "rank-usefulness")
EXCERPT_CHARS = 700
VERDICTS = ("useful", "redundant", "noise")


def claude_exe() -> str:
    """The claude program itself (npm's .cmd shim mangles multi-line input on Windows)."""
    found = shutil.which("claude")
    if found and found.lower().endswith((".cmd", ".bat")):
        exe = Path(found).parent / "node_modules" / "@anthropic-ai" / "claude-code" / "bin" / "claude.exe"
        if exe.is_file():
            return str(exe)
    return found or "claude"


def is_junk(q: str) -> bool:
    """Skip what is not a real question: a flag that leaked into the logged text, a
    path, or an entry title (the link-gap and dedup passes search titles verbatim,
    which asks "find this exact entry", not "what do we know about X")."""
    low = q.lower()
    if "--" in q or low.endswith(".md") or low.startswith(("#", "-", "qmd://")):
        return True
    return any(t.startswith(low[:60]) for t in known_titles())


_TITLES: set[str] | None = None


def known_titles() -> set[str]:
    """Entry titles across the vault, lowercased, for the junk filter."""
    global _TITLES
    if _TITLES is None:
        _TITLES = set()
        try:
            sys.path.insert(0, str(REPO / "bootstrap" / "scripts"))
            from _wiki_config import load_registry  # noqa: PLC0415
            reg, reg_path = load_registry()
            for entry in (reg or {}).get("notebooks", {}).values():
                root = entry.get("root") if isinstance(entry, dict) else entry
                wiki = (Path(reg_path).parent / str(root) / "wiki") if root else None
                if not wiki or not wiki.is_dir():
                    continue
                for f in wiki.rglob("*.md"):
                    try:
                        head = f.read_text(encoding="utf-8", errors="replace")[:600]
                    except OSError:
                        continue
                    m = re.search(r'^title:\s*"?(.+?)"?\s*$', head, re.M)
                    if m:
                        _TITLES.add(m.group(1).strip().lower())
        except Exception:  # noqa: BLE001 - the filter is a convenience, never a blocker
            pass
    return _TITLES


def load_queries(scope: str | None, n: int, seed: int) -> list[dict]:
    """Distinct real queries from the search log, newest first, sampled deterministically."""
    if not LOG.is_file():
        sys.exit(f"no search log at {LOG} — run some searches first")
    rows = []
    for line in LOG.read_text(encoding="utf-8", errors="replace").splitlines():
        try:
            r = json.loads(line)
        except json.JSONDecodeError:
            continue
        if r.get("outcome") != "ok" or not r.get("query"):
            continue
        caller = str(r.get("caller", ""))
        if caller in SKIP_CALLERS or caller.startswith("skilltest"):
            continue  # synthetic test queries are not real questions
        if scope and r.get("scope") != scope:
            continue
        rows.append(r)
    seen, distinct = set(), []
    for r in reversed(rows):  # newest first
        q = r["query"].strip()
        if q.lower() in seen or len(q) < 8:
            continue
        if is_junk(q):
            continue
        seen.add(q.lower())
        distinct.append({"query": q, "scope": r.get("scope"), "ts": r.get("ts")})
    if not distinct:
        sys.exit("no usable queries in the log for that scope")
    random.Random(seed).shuffle(distinct)
    return distinct[:n]


def search(query: str, scope: str | None, k: int, timeout: int) -> list[dict]:
    """One real search through the wrapper, as any session would run it."""
    cmd = [sys.executable, str(WRAPPER), "--caller", "rank-usefulness", "-k", str(k), "--json"]
    if scope and scope != "all notebooks":
        cmd += ["--notebook", scope]
    elif scope == "all notebooks":
        cmd += ["--all-notebooks"]
    cmd.append(query)
    p = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace",
                       timeout=timeout, env={**os.environ, "PYTHONIOENCODING": "utf-8"})
    if p.returncode != 0:
        return []
    try:
        return json.loads(p.stdout)
    except json.JSONDecodeError:
        return []


def excerpt(result: dict) -> str:
    """What the judge reads: the entry's TL;DR if it has one, else its best chunk."""
    path = re.match(r"qmd://(.+?\.md)", str(result.get("file", "")).replace("\\", "/"))
    text = ""
    if path:
        try:
            text = Path(path.group(1)).read_text(encoding="utf-8", errors="replace")
        except OSError:
            text = ""
    if text:
        body = text.split("---", 2)[-1] if text.startswith("---") else text
        m = re.search(r"##\s*TL;DR\s*\n+(.+?)(?=\n##\s|\Z)", body, re.S | re.I)
        if m:
            return " ".join(m.group(1).split())[:EXCERPT_CHARS]
        return " ".join(body.split())[:EXCERPT_CHARS]
    return " ".join(str(result.get("bestChunk") or result.get("body") or "").split())[:EXCERPT_CHARS]


JUDGE_PROMPT = """You are judging search results from a personal knowledge wiki, for a retrieval
evaluation. Answer with JSON only — no preamble, no code fence.

The person searched for:

    {query}

Below are {n} wiki entries the search returned, in random order. For EACH entry, decide what it
would be worth to someone who asked that question and is about to read entries to answer it:

- "useful"    — it helps answer the question, and says something the other entries do not
- "redundant" — it is on topic, but another entry here already covers the same ground (name that
                entry's label in "duplicate_of")
- "noise"     — it does not help answer this question

Judge each entry on its own merits. The order tells you nothing: it is deliberately shuffled.

Entries:

{entries}

Reply with exactly this JSON shape:

{{"best": "<label of the single most useful entry for this question>",
 "judgments": [{{"label": "E1", "verdict": "useful", "duplicate_of": null, "why": "<8 words>"}}]}}
"""


def judge(query: str, items: list[dict], model: str, timeout: int) -> dict:
    """One model call per query; returns {label: {verdict, duplicate_of, why}}."""
    entries = "\n\n".join(f"[{it['label']}] {it['title']}\n{it['excerpt']}" for it in items)
    prompt = JUDGE_PROMPT.format(query=query, n=len(items), entries=entries)
    env = {k: v for k, v in os.environ.items() if k != "ANTHROPIC_API_KEY"}
    cmd = [claude_exe(), "-p", "--model", model, "--output-format", "json"]
    p = subprocess.run(cmd, input=prompt, capture_output=True, text=True, encoding="utf-8",
                       errors="replace", timeout=timeout, env=env)
    out, best, cost = {}, None, 0.0
    try:
        envelope = json.loads(p.stdout)
        cost = float(envelope.get("total_cost_usd") or 0.0)
        text = envelope.get("result") or ""
        m = re.search(r"\{.*\}", text, re.S)
        parsed = json.loads(m.group(0))
        best = parsed.get("best")
        for j in parsed["judgments"]:
            v = str(j.get("verdict", "")).lower()
            if v in VERDICTS:
                out[str(j.get("label"))] = {"verdict": v, "duplicate_of": j.get("duplicate_of"),
                                            "why": str(j.get("why", ""))[:120]}
    except (json.JSONDecodeError, AttributeError, KeyError, TypeError, ValueError):
        pass
    return {"verdicts": out, "best": best, "cost_usd": cost, "stderr": (p.stderr or "")[-300:]}


def main() -> int:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0],
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--queries", type=int, default=20, help="how many logged queries to test (default 20)")
    ap.add_argument("--k", type=int, default=40, help="results to fetch and judge per query (default 40)")
    ap.add_argument("--cut", type=int, default=20, help="the cut being tested: ranks above it are the question (default 20)")
    ap.add_argument("--model", default="sonnet", help="judge model (default sonnet)")
    ap.add_argument("--scope", default="agentic-design",
                    help="notebook to test, or 'any' for every logged scope (default agentic-design)")
    ap.add_argument("--seed", type=int, default=1, help="sampling seed, for a repeatable set")
    ap.add_argument("--timeout", type=int, default=300, help="seconds per search and per judgment")
    ap.add_argument("--dry-run", action="store_true", help="build everything, spend nothing")
    args = ap.parse_args()

    scope = None if args.scope == "any" else args.scope
    queries = load_queries(scope, args.queries, args.seed)
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    out_dir = HERE / ".results" / stamp
    print(f"rank-usefulness: {len(queries)} queries, k={args.k}, cut at {args.cut}, judge={args.model}"
          f"{' (DRY RUN)' if args.dry_run else ''}")

    rows, total_cost = [], 0.0
    for i, q in enumerate(queries, 1):
        results = search(q["query"], q["scope"], args.k, args.timeout)
        if len(results) <= args.cut:
            print(f"[{i}/{len(queries)}] {q['query'][:60]!r}: only {len(results)} results — skipped")
            continue
        items = []
        for rank, r in enumerate(results, 1):
            items.append({"rank": rank, "label": f"E{rank}", "title": str(r.get("title") or "")[:120],
                          "file": str(r.get("file") or ""), "score": r.get("score"),
                          "excerpt": excerpt(r)})
        shuffled = items[:]
        random.Random(args.seed + i).shuffle(shuffled)
        for pos, it in enumerate(shuffled, 1):  # relabel so the label cannot leak the rank
            it["label"] = f"E{pos}"
        if args.dry_run:
            chars = sum(len(it["excerpt"]) + len(it["title"]) for it in shuffled)
            rows.append({"query": q["query"], "results": len(results), "prompt_chars": chars})
            print(f"[{i}/{len(queries)}] {q['query'][:60]!r}: {len(results)} results, "
                  f"~{chars // 4:,} prompt tokens")
            continue
        j = judge(q["query"], shuffled, args.model, args.timeout)
        total_cost += j["cost_usd"]
        if not j["verdicts"]:  # one retry: an unparseable reply is the judge's slip, not a result
            print(f"[{i}/{len(queries)}] unparseable judgment - retrying once")
            j = judge(q["query"], shuffled, args.model, args.timeout)
            total_cost += j["cost_usd"]
        by_rank = {}
        for it in shuffled:
            v = j["verdicts"].get(it["label"])
            if v:
                by_rank[it["rank"]] = {**v, "title": it["title"], "file": it["file"], "score": it["score"]}
        top = [v for r, v in by_rank.items() if r <= args.cut]
        tail = [v for r, v in by_rank.items() if r > args.cut]
        useful_tail = [(r, v) for r, v in sorted(by_rank.items()) if r > args.cut and v["verdict"] == "useful"]
        best_rank = next((it["rank"] for it in shuffled if it["label"] == j.get("best")), None)
        rows.append({"query": q["query"], "scope": q["scope"], "results": len(results),
                     "best_rank": best_rank,
                     "judged": len(by_rank), "by_rank": by_rank,
                     "useful_top": sum(v["verdict"] == "useful" for v in top),
                     "useful_tail": sum(v["verdict"] == "useful" for v in tail),
                     "n_top": len(top), "n_tail": len(tail), "cost_usd": j["cost_usd"]})
        print(f"[{i}/{len(queries)}] {q['query'][:60]!r}: useful {rows[-1]['useful_top']}/{len(top)} "
              f"in 1-{args.cut}, {rows[-1]['useful_tail']}/{len(tail)} in {args.cut + 1}-{len(results)}"
              + (f"  <- {useful_tail[0][1]['title'][:50]} (#{useful_tail[0][0]})" if useful_tail else ""))

    if args.dry_run:
        chars = sum(r["prompt_chars"] for r in rows)
        print(f"\nwould judge {len(rows)} queries, ~{chars // 4:,} prompt tokens total "
              f"(~${chars / 4 / 1e6 * 3:.2f} on sonnet input rates, plus output)")
        return 0

    judged = [r for r in rows if r.get("judged")]
    if not judged:
        print("nothing judged — check the model output")
        return 1
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "judgments.json").write_text(json.dumps(rows, indent=2), encoding="utf-8")

    top_rate = sum(r["useful_top"] for r in judged) / max(1, sum(r["n_top"] for r in judged))
    tail_rate = sum(r["useful_tail"] for r in judged) / max(1, sum(r["n_tail"] for r in judged))
    with_tail = [r for r in judged if r["useful_tail"] > 0]
    best_known = [r for r in judged if r.get("best_rank")]
    best_below = [r for r in best_known if r["best_rank"] > args.cut]
    lines = [f"# Is the cut at {args.cut} right? ({len(judged)} real queries, k={args.k})", "",
             f"Run `{stamp}`, judge `{args.model}`, scope `{args.scope}`, seed {args.seed}.",
             f"Queries come from the search log; entries were shuffled before judging.", "",
             "| Band | Entries judged | Judged useful | Rate |", "|---|---|---|---|",
             f"| ranks 1-{args.cut} | {sum(r['n_top'] for r in judged)} | "
             f"{sum(r['useful_top'] for r in judged)} | {top_rate:.0%} |",
             f"| ranks {args.cut + 1}+ | {sum(r['n_tail'] for r in judged)} | "
             f"{sum(r['useful_tail'] for r in judged)} | {tail_rate:.0%} |", "",
             f"- **{len(with_tail)} of {len(judged)} queries** had at least one useful entry below "
             f"rank {args.cut} (median {statistics.median([r['useful_tail'] for r in judged]):.1f} per query).",
             f"- **The single best entry sat below rank {args.cut} in {len(best_below)} of "
             f"{len(best_known)} queries** - the sharper question, since a useful-but-not-best "
             f"entry in the tail costs little.",
             f"- Spend: ${total_cost:.2f}.", ""]
    if with_tail:
        lines += [f"## What was found below rank {args.cut}", ""]
        for r in with_tail:
            lines.append(f"**{r['query']}**")
            for rank, v in sorted(r["by_rank"].items()):
                if rank > args.cut and v["verdict"] == "useful":
                    lines.append(f"- #{rank} ({v['score']:.3f}) {v['title']} — {v['why']}")
            lines.append("")
    verdict = ("the cut looks right — the tail is mostly redundant or noise" if tail_rate < 0.1
               else "borderline — a useful entry turns up below the cut often enough to discuss"
               if tail_rate < 0.25 else "the cut looks too tight — raise k or show more on demand")
    lines += [f"**Read:** {verdict}.", ""]
    (out_dir / "report.md").write_text("\n".join(lines), encoding="utf-8")
    print(f"\nranks 1-{args.cut}: {top_rate:.0%} useful | ranks {args.cut + 1}+: {tail_rate:.0%} useful | "
          f"{len(with_tail)}/{len(judged)} queries had a useful tail entry | "
          f"best below the cut in {len(best_below)}/{len(best_known)} | ${total_cost:.2f}")
    print(f"report: {out_dir / 'report.md'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
