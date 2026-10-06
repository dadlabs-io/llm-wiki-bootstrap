#!/usr/bin/env python3
"""
question-set.py — a labelled set of real search questions, to measure the search (task #82).

Every search change so far was judged by a model (rank-usefulness.py) or by the
shape of the scores. This builds a fixed yardstick instead: about 50 real
questions from the search log, each labelled by the user with the entries that
answer it, so any later change (k, C, --keyword-extra, a qmd upgrade, an
embedding swap, keyword mode) can be scored against the same answers. It also
answers task #64's open question: are the keyword-only finds useful, not just
different?

  draft     Sample the questions from the search log (stratified by who asked:
            ingest workers, discovery, triage, interactive sessions), run each
            through the normal wrapper at the default settings (-k 30 plus the
            up-to-20 keyword-only finds), and save every result as the pool the
            user labels: question-set/pool.json, plus question-set/page-data.json
            (each question's candidates shuffled, with no rank and no hint of
            which search found them) for the labelling page.
  import    Turn the labelling page's saved rows into question-set/labels.json.
  measure   Score a configuration against the labels: recall at 10 and at k of
            the ranked results, the reciprocal rank of the first answer, and how
            many answers only the keyword finds reached. --from-pool scores the
            pool's own run without searching again; otherwise each question is
            searched again with the settings given.

Pooling caveat: only entries in the pool were labelled. A later configuration
that returns an entry outside it is reported as "unjudged" per question; it
counts as not an answer until it is labelled.

Usage (from the repo root):
  uv run python tests/search/question-set.py draft --dry-run
  uv run python tests/search/question-set.py draft
  uv run python tests/search/question-set.py import <rows.json>
  uv run python tests/search/question-set.py measure --from-pool
  uv run python tests/search/question-set.py measure -k 30 --keyword-extra 0
  uv run python tests/search/question-set.py measure --mode keyword

Nothing here ships with the framework.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import os
import random
import re
import statistics
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
WRAPPER = REPO / "scripts" / "wiki-qmd-query.py"
SET_DIR = HERE / "question-set"
POOL, PAGE_DATA, LABELS = SET_DIR / "pool.json", SET_DIR / "page-data.json", SET_DIR / "labels.json"
CALLER = "question-set"
DEFAULT_MIX = "wiki-ingester=30,discover=10,triage=5,session=5"
SUMMARY_CHARS = 260

_spec = importlib.util.spec_from_file_location("rank_usefulness", HERE / "rank-usefulness.py")
ru = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(ru)


def parse_mix(text: str) -> dict[str, int]:
    out = {}
    for part in text.split(","):
        name, _, n = part.partition("=")
        out[name.strip()] = int(n)
    return out


def sample(scope: str, mix: dict[str, int], seed: int) -> list[dict]:
    """The questions: rank-usefulness's loader (real, distinct, junk-filtered, shuffled), then quotas per caller."""
    pool = ru.load_queries(scope, 10**6, seed)
    picked, short = [], {}
    for caller, n in mix.items():
        rows = [q for q in pool if q.get("caller") == caller][:n]
        picked += rows
        if len(rows) < n:
            short[caller] = (len(rows), n)
    for caller, (got, want) in short.items():
        print(f"note: only {got} usable {caller} questions (wanted {want})")
    return picked


def search(query: str, scope: str, k: int, keyword_extra: int, C: int | None, mode: str | None,
           timeout: int) -> list[dict] | None:
    cmd = [sys.executable, str(WRAPPER), "--caller", CALLER, "--notebook", scope, "-k", str(k),
           "--keyword-extra", str(keyword_extra), "--json"]
    if C:
        cmd += ["-C", str(C)]
    env = {**os.environ, "PYTHONIOENCODING": "utf-8"}
    if mode:
        env["WIKI_SEARCH_MODE"] = mode
    p = subprocess.run(cmd + [query], capture_output=True, text=True, encoding="utf-8", errors="replace",
                       timeout=timeout, env=env)
    if p.returncode != 0:
        print(f"  search failed (exit {p.returncode}): {query[:60]!r}: {(p.stderr or '').strip()[-200:]}")
        return None
    try:
        return json.loads(p.stdout)
    except json.JSONDecodeError:
        return None


def entry_id(file_field: str) -> str:
    """qmd://C:\\...\\<notebook>\\wiki/research/x.md -> wiki/research/x.md (stable across machines)."""
    path = str(file_field).replace("qmd://", "").replace("\\", "/")
    i = path.find("/wiki/")
    return path[i + 1:] if i >= 0 else path


def summary(file_field: str) -> str:
    text = ru.excerpt({"file": file_field})
    return text[:SUMMARY_CHARS] + ("…" if len(text) > SUMMARY_CHARS else "")


def as_candidates(results: list[dict]) -> list[dict]:
    out, seen, full_rank, kw_pos = [], set(), 0, 0
    for r in results:
        cid = entry_id(r.get("file", ""))
        if cid in seen:
            continue
        seen.add(cid)
        found_by = r.get("found_by") or "full"
        if found_by == "full":
            full_rank += 1
        else:
            kw_pos += 1
        out.append({"id": cid, "title": str(r.get("title") or cid)[:160], "summary": summary(r.get("file", "")),
                    "found_by": found_by, "full_rank": full_rank if found_by == "full" else None,
                    "keyword_pos": kw_pos if found_by != "full" else None})
    return out


def write_page_data(pool: dict, seed: int) -> None:
    """What the labelling page shows: candidates shuffled, no rank, no source of the find."""
    qs = []
    for i, q in enumerate(pool["questions"]):
        cands = [{"id": c["id"], "title": c["title"], "summary": c["summary"]} for c in q["candidates"]]
        random.Random(seed * 1000 + i).shuffle(cands)
        qs.append({"id": q["id"], "query": q["query"], "caller": q["caller"], "candidates": cands})
    PAGE_DATA.write_text(json.dumps({"scope": pool["scope"], "questions": qs}, ensure_ascii=False, indent=1),
                         encoding="utf-8")


def cmd_draft(args) -> int:
    mix = parse_mix(args.mix)
    questions = sample(args.scope, mix, args.seed)
    print(f"{len(questions)} questions from {args.scope} ({args.mix}), seed {args.seed}")
    if args.dry_run:
        for q in questions:
            print(f"  [{q['caller']}] {q['query'][:110]}")
        return 0
    SET_DIR.mkdir(exist_ok=True)
    prior = None
    if args.fill:  # search again only the sampled questions the pool is missing (a timed-out search)
        prior = json.loads(POOL.read_text(encoding="utf-8"))
        have = {q["query"] for q in prior["questions"]}
        questions = [q for q in questions if q["query"] not in have]
        print(f"filling {len(questions)} missing questions")

    def run(q):
        return search(q["query"], args.scope, args.k, args.keyword_extra, None, None, args.timeout)

    with ThreadPoolExecutor(max_workers=args.workers) as ex:
        results = list(ex.map(run, questions))
    out = prior["questions"] if prior else []
    for i, (q, res) in enumerate(zip(questions, results), 1):
        if not res:
            print(f"  skipped (no results): {q['query'][:70]!r}")
            continue
        cands = as_candidates(res)
        out.append({"id": f"q{len(out) + 1:02d}", "query": q["query"], "caller": q["caller"],
                    "logged_at": q.get("ts"), "candidates": cands})
        print(f"[{i}/{len(questions)}] {len(cands)} candidates  {q['query'][:70]!r}")
    pool = {"created": prior["created"] if prior else datetime.now().astimezone().isoformat(timespec="seconds"),
            "scope": args.scope,
            "seed": args.seed, "mix": args.mix,
            "config": {"k": args.k, "keyword_extra": args.keyword_extra, "C": "default"},
            "questions": out}
    POOL.write_text(json.dumps(pool, ensure_ascii=False, indent=1), encoding="utf-8")
    write_page_data(pool, args.seed)
    n = sum(len(q["candidates"]) for q in out)
    print(f"pool: {len(out)} questions, {n} candidates -> {POOL.relative_to(REPO)}; page data -> "
          f"{PAGE_DATA.relative_to(REPO)}")
    return 0


def cmd_page(args) -> int:
    pool = json.loads(POOL.read_text(encoding="utf-8"))
    write_page_data(pool, pool["seed"])
    print(f"page data -> {PAGE_DATA.relative_to(REPO)}")
    return 0


def cmd_import(args) -> int:
    """Rows saved by the labelling page: a list of {question_id, relevant: [ids], done, note} docs."""
    raw = json.loads(Path(args.rows).read_text(encoding="utf-8"))
    rows = raw.get("documents") or raw.get("docs") or raw if isinstance(raw, dict) else raw
    if isinstance(rows, dict):
        rows = list(rows.values())
    pool = json.loads(POOL.read_text(encoding="utf-8"))
    known = {q["id"]: {c["id"] for c in q["candidates"]} for q in pool["questions"]}
    labels, bad = {}, []
    for row in rows:
        d = row.get("data", row)
        qid = d.get("question_id")
        if qid not in known:
            bad.append(f"unknown question {qid!r}")
            continue
        rel = [c for c in d.get("relevant", []) if c in known[qid]]
        if len(rel) != len(d.get("relevant", [])):
            bad.append(f"{qid}: {len(d.get('relevant', [])) - len(rel)} ids not in its pool")
        labels[qid] = {"relevant": sorted(rel), "done": bool(d.get("done")), "note": str(d.get("note") or ""),
                       "labelled_by": d.get("labelled_by")}
    LABELS.write_text(json.dumps(dict(sorted(labels.items())), ensure_ascii=False, indent=1), encoding="utf-8")
    done = sum(v["done"] for v in labels.values())
    print(f"labels: {len(labels)} questions ({done} marked done) -> {LABELS.relative_to(REPO)}")
    for b in bad:
        print(f"  warning: {b}")
    return 0


def score(ranked: list[str], extras: list[str], relevant: set[str], k: int) -> dict:
    first = next((i for i, cid in enumerate(ranked, 1) if cid in relevant), None)
    hit10 = len(relevant & set(ranked[:10]))
    hitk = len(relevant & set(ranked[:k]))
    kw_only = relevant & set(extras) - set(ranked[:k])
    seen = relevant & (set(ranked[:k]) | set(extras))
    return {"recall10": hit10 / len(relevant), "recallk": hitk / len(relevant),
            "recall_seen": len(seen) / len(relevant), "rr": 1 / first if first else 0.0,
            "kw_only": len(kw_only), "kw_extras": len(extras), "kw_relevant": len(relevant & set(extras))}


def cmd_measure(args) -> int:
    pool = json.loads(POOL.read_text(encoding="utf-8"))
    if not LABELS.is_file():
        sys.exit("no labels yet: label the questions, then run `import`")
    labels = json.loads(LABELS.read_text(encoding="utf-8"))
    qs = [q for q in pool["questions"] if labels.get(q["id"], {}).get("done")]
    k = args.k or pool["config"]["k"]
    if args.from_pool:
        runs = {q["id"]: ([c["id"] for c in q["candidates"] if c["found_by"] == "full"],
                          [c["id"] for c in q["candidates"] if c["found_by"] != "full"]) for q in qs}
        label = f"the pool's own run (k={pool['config']['k']}, keyword-extra {pool['config']['keyword_extra']})"
    else:
        extra = pool["config"]["keyword_extra"] if args.keyword_extra is None else args.keyword_extra

        def run(q):
            res = search(q["query"], pool["scope"], k, extra, args.C, args.mode, args.timeout) or []
            ids = [entry_id(r.get("file", "")) for r in res]
            fb = [r.get("found_by") or "full" for r in res]
            return ([i for i, f in zip(ids, fb) if f == "full"], [i for i, f in zip(ids, fb) if f != "full"])

        with ThreadPoolExecutor(max_workers=args.workers) as ex:
            runs = dict(zip([q["id"] for q in qs], ex.map(run, qs)))
        label = (f"k={k}, keyword-extra {extra}, C={args.C or 'default'}, mode {args.mode or 'machine default'}")
    rows, empty, unjudged = [], [], 0
    pooled = {q["id"]: {c["id"] for c in q["candidates"]} for q in qs}
    for q in qs:
        rel = set(labels[q["id"]]["relevant"])
        ranked, extras = runs[q["id"]]
        new = [c for c in ranked[:k] + extras if c not in pooled[q["id"]]]
        unjudged += len(new)
        if not rel:
            empty.append(q)
            continue
        rows.append({"id": q["id"], "query": q["query"], "caller": q["caller"], "relevant": len(rel),
                     "unjudged": len(new), **score(ranked, extras, rel, k)})
    if not rows:
        sys.exit("no labelled question has an answer yet")
    mean = lambda key: statistics.mean(r[key] for r in rows)  # noqa: E731
    kw_extras = sum(r["kw_extras"] for r in rows)
    lines = [f"# Search measured against the labelled questions — {label}", "",
             f"{len(rows)} questions with at least one answer ({sum(r['relevant'] for r in rows)} answers in all); "
             f"{len(empty)} labelled with none; {len(pool['questions']) - len(qs)} not labelled yet.", "",
             "| Measure | Value |", "|---|---|",
             f"| Recall in the top 10 | {mean('recall10'):.0%} |",
             f"| Recall in the top {k} | {mean('recallk'):.0%} |",
             f"| Recall in all a session sees (top {k} + keyword finds) | {mean('recall_seen'):.0%} |",
             f"| Mean reciprocal rank of the first answer | {mean('rr'):.2f} |",
             f"| Answers only the keyword finds reached | {sum(r['kw_only'] for r in rows)} "
             f"(in {sum(1 for r in rows if r['kw_only'])} questions) |",
             f"| Keyword finds that were answers | {sum(r['kw_relevant'] for r in rows)} of {kw_extras}"
             f" ({sum(r['kw_relevant'] for r in rows) / kw_extras:.0%}) |" if kw_extras else
             "| Keyword finds | none in this run |",
             f"| Results outside the labelled pool (unjudged) | {unjudged} |", "",
             "## Per question", "", "| Q | Asked by | Answers | R@10 | R@k | RR | Keyword-only | Unjudged | Question |",
             "|---|---|---|---|---|---|---|---|---|"]
    for r in rows:
        lines.append(f"| {r['id']} | {r['caller']} | {r['relevant']} | {r['recall10']:.0%} | {r['recallk']:.0%} | "
                     f"{r['rr']:.2f} | {r['kw_only']} | {r['unjudged']} | {r['query'][:80]} |")
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    out = HERE / ".results" / f"{stamp}-question-set"
    out.mkdir(parents=True, exist_ok=True)
    (out / "report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    (out / "results.json").write_text(json.dumps({"config": label, "rows": rows}, indent=1), encoding="utf-8")
    print("\n".join(lines[:15]))
    print(f"report: {out / 'report.md'}")
    return 0


def main() -> int:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0],
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    d = sub.add_parser("draft", help="sample the questions and build the pool to label")
    d.add_argument("--scope", default="agentic-design")
    d.add_argument("--mix", default=DEFAULT_MIX, help=f"questions per caller (default {DEFAULT_MIX})")
    d.add_argument("--seed", type=int, default=1)
    d.add_argument("-k", type=int, default=30)
    d.add_argument("--keyword-extra", type=int, default=20)
    d.add_argument("--workers", type=int, default=3, help="searches at once (the wrapper has 3 GPU slots)")
    d.add_argument("--timeout", type=int, default=600)
    d.add_argument("--dry-run", action="store_true", help="list the questions, search nothing")
    d.add_argument("--fill", action="store_true", help="keep pool.json; search only the sampled questions it lacks")
    sub.add_parser("page", help="rewrite page-data.json from pool.json (no searches)")
    i = sub.add_parser("import", help="labels from the labelling page's saved rows")
    i.add_argument("rows")
    m = sub.add_parser("measure", help="score a configuration against the labels")
    m.add_argument("--from-pool", action="store_true", help="score the pool's own run, no new searches")
    m.add_argument("-k", type=int)
    m.add_argument("-C", type=int)
    m.add_argument("--keyword-extra", type=int)
    m.add_argument("--mode", choices=("full", "keyword"))
    m.add_argument("--workers", type=int, default=3)
    m.add_argument("--timeout", type=int, default=600)
    args = ap.parse_args()
    return {"draft": cmd_draft, "page": cmd_page, "import": cmd_import, "measure": cmd_measure}[args.cmd](args)


if __name__ == "__main__":
    raise SystemExit(main())
