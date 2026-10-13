"""wiki-discover test suite: sandbox, prompts and checks for run_skill_test.py (task #16, 2026-10-12).

A throwaway registry with one notebook, `skilltest-discover`, copied fresh for each case from
fixtures/seed-notebook/ (its wiki entries are what discovery dedups against; a search index of
its own, built once per model in setup, so the real index is never touched).

Each case names, from fixtures/:
- `feeds`: a file in fixtures/feeds/, written as the notebook's _config/feeds.md (omit it for a
  notebook with no feeds page);
- `saved`: a folder in fixtures/saved/ holding saved feed files and an index.json mapping each
  feeds.md Feed value to its file. wiki-feeds.py reads them through $WIKI_FEEDS_FROM_DIR instead
  of the network; a Feed value the index does not map fails like a dead feed;
- `say`: the user's line; `answers` (optional): what the user answers when the skill pauses for
  review (the session cannot reply, so it is given up front).
Web-search sources (Feed `—`) use the live WebSearch tool.

The checks read what the session left behind and its tool calls, never its reasoning.
"""

from __future__ import annotations

import datetime
import json
import os
import re
import shutil
import stat
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
NOTEBOOK = "skilltest-discover"
ALLOWED_TOOLS = [
    "Read", "Write", "Edit", "Glob", "Grep", "WebSearch",
    "Bash(python:*)", "Bash(python3:*)", "Bash(uv:*)", "Bash(node:*)", "Bash(qmd:*)",
    "Bash(cd:*)", "Bash(ls:*)", "Bash(cat:*)", "Bash(grep:*)", "Bash(head:*)", "Bash(tail:*)",
    "Bash(wc:*)", "Bash(find:*)", "Bash(sort:*)", "Bash(echo:*)", "Bash(pwd:*)", "Bash(sed:*)",
    "Bash(mkdir:*)", "Bash(mv:*)", "Bash(date:*)",
]


def _rmtree(path: Path) -> None:
    def onexc(func, target, exc):
        try:
            os.chmod(target, stat.S_IWRITE)
            func(target)
        except OSError:
            pass
    if path.exists():
        shutil.rmtree(path, onexc=onexc)


def _qmd() -> list[str]:
    shim = shutil.which("qmd")
    if not shim:
        raise SystemExit("qmd not found on PATH")
    entry = Path(shim).resolve().parent / "node_modules" / "@tobilu" / "qmd" / "dist" / "cli" / "qmd.js"
    node = shutil.which("node")
    return [node, str(entry)] if entry.exists() and node else [shim]


def _qmd_index_file(index: str) -> Path:
    return Path.home() / ".cache" / "qmd" / f"{index}.sqlite"


def prepare_fixtures(repo: Path, refresh: bool = False) -> list[dict]:
    return []  # every feed, article and entry is written for the test


def setup(model: str, sandbox: Path, repo: Path) -> dict:
    _rmtree(sandbox)
    nb = sandbox / "notebooks" / NOTEBOOK
    shutil.copytree(HERE / "fixtures" / "seed-notebook", nb)
    registry = sandbox / "linked-notebooks.json"
    registry.write_text(json.dumps({"notebooks": {NOTEBOOK: {"root": f"notebooks/{NOTEBOOK}"}}}, indent=2),
                        encoding="utf-8")
    project = sandbox / "project"
    cfg = json.dumps({"tool": "claude-code", "project_name": NOTEBOOK, "notebook": NOTEBOOK, "persona": "main",
                      "registry": registry.as_posix()}, indent=2)
    for d in (project, sandbox):
        (d / ".claude").mkdir(parents=True, exist_ok=True)
        (d / ".claude" / "wiki-config.json").write_text(cfg, encoding="utf-8")
    index = f"skilltest-discover-{model}-{sandbox.parent.name}"
    _qmd_index_file(index).unlink(missing_ok=True)
    for args in (["collection", "add", str(nb / "wiki")], ["embed"]):
        subprocess.run([*_qmd(), "--index", index, *args], capture_output=True, text=True,
                       encoding="utf-8", errors="replace", timeout=600)
    saved = sandbox / "saved-feeds"
    return {"sandbox": sandbox, "project": project, "notebook": nb, "registry": registry, "saved": saved,
            "skill_dir": sandbox / "skill" / "wiki-discover", "index": index, "scripts": repo / "scripts",
            "env": {"WIKI_QMD_INDEX": index, "WIKI_FEEDS_FROM_DIR": saved.as_posix(), "PYTHONIOENCODING": "utf-8"}}


def teardown(ctx: dict) -> None:
    _rmtree(ctx["sandbox"])
    _qmd_index_file(ctx["index"]).unlink(missing_ok=True)


def snapshot(ctx: dict) -> dict:
    nb = ctx["notebook"]
    if not nb.exists():
        return {}
    return {p.relative_to(nb).as_posix(): (p.stat().st_size, p.stat().st_mtime_ns) for p in nb.rglob("*") if p.is_file()}


HEADER = """You are running an automated test of the wiki-discover skill. The skill under test is at {skill}/SKILL.md. Read it and follow it exactly, as if the user had said the message below in this project. Do not use any installed copy of the skill.

The notebook is `{notebook}`, this project's notebook, at {nb}. Its search index is named `{index}`: the search helper picks that up by itself (pass it no `--index`). Run scripts as the skill writes them, `uv run --project <scripts dir> python <path> ...`, with no environment-variable prefix, and write only inside {sandbox}. The user cannot reply while this runs: where the skill says to wait for the user, take the answers given below as already spoken; where it says to ask something with no answer given, ask it in your final message and stop there.

{answers}The user said: """


def prompt(case: dict, ctx: dict) -> str:
    nb, saved = ctx["notebook"], ctx["saved"]
    _rmtree(nb)
    shutil.copytree(HERE / "fixtures" / "seed-notebook", nb)
    if case.get("feeds"):
        (nb / "_config").mkdir(parents=True, exist_ok=True)
        shutil.copy2(HERE / "fixtures" / "feeds" / case["feeds"], nb / "_config" / "feeds.md")
    _rmtree(saved)
    if case.get("saved"):
        shutil.copytree(HERE / "fixtures" / "saved" / case["saved"], saved)
    else:
        saved.mkdir(parents=True)
        (saved / "index.json").write_text("{}", encoding="utf-8")
    ctx["before_case"] = snapshot(ctx)
    answers = f"When the skill pauses for the user's review, the user answers: {case['answers']}\n\n" if case.get("answers") else ""
    return HEADER.format(skill=ctx["skill_dir"].as_posix(), notebook=NOTEBOOK, nb=nb.as_posix(), index=ctx["index"],
                         sandbox=ctx["sandbox"].as_posix(), answers=answers) + case["say"]


ITEMS = {  # id: (slug in the link, keyword in the title, full title)
    "w1": ("long-term-memory-store-for-coding-agents", "memory store", "Designing a long-term memory store for coding agents"),
    "w2": ("chunking-strategies-retrieval-evals", "chunking", "Chunking strategies that survive retrieval evals"),
    "w3": ("episodic-memory-from-trajectories", "trajectories", "Summarising agent trajectories into episodic memory"),
    "w4": ("hnsw-parameters-measured", "hnsw", "Vector index tuning: HNSW parameters measured on 2M documents"),
    "w5": ("reranking-trick-halved-rag-latency", "reranking", "Show: a reranking trick that halved my RAG latency"),
    "w6": ("five-memory-libraries-recall", "libraries", "Benchmark: five agent memory libraries compared on recall"),
    "h1": ("hybrid-retrieval-for-agents", "hybrid", "Hybrid Search Is Back: BM25 Meets Embeddings in Agent Memory"),
    "o1": ("lisbon-campus-move", "lisbon", "Our office move to the new Lisbon campus"),
    "l1": ("top-10-ai-tools-2026", "top 10", "Top 10 AI tools every developer must try in 2026"),
}
FEED_ROWS = {  # row token -> old To, in the judge/approve feeds pages
    "vellum engineering": "2026-08-15", "agent commons": "2026-09-01",
}
WEB_SOURCES = {  # token -> old To ("—" = never checked); the six stalest are searched
    "alderwick": "—", "brightmoor": "—", "calloway": "2026-03-02", "dunmore": "2026-04-10",
    "eastgate": "2026-05-20", "fennimore": "2026-07-01", "garrowby": "2026-08-15", "hollis": "2026-09-30",
}
STALEST_SIX = {"alderwick", "brightmoor", "calloway", "dunmore", "eastgate", "fennimore"}
CHECKLIST_NAME = re.compile(r"^\d{4}-\d{2}-\d{2}-discovery\.md$")


def _today() -> str:
    return datetime.date.today().isoformat()


def _heading(line: str) -> bool:
    return bool(re.match(r"^\s*#{1,6}\s+\S", line))


def _level(line: str) -> int:
    return len(line.strip()) - len(line.strip().lstrip("#"))


def _skipped_heading(line: str) -> bool:
    return bool(re.match(r"^\s*#{1,6}\s+.*skipped", line, re.I)
                or re.match(r"^\s*\*\*[^*]*skipped[^*]*\*\*\s*$", line, re.I))


def _parse(text: str) -> dict:
    """Split a checklist into its lines, the listed part (the Candidates, before the Decisions log and
    before any top-level Skipped section) and every Skipped section wherever it sits, including a
    subsection of the Decisions log."""
    body = re.sub(r"\A---[ \t]*\n.*?\n---[ \t]*\n", "", text, flags=re.S)
    lines = body.splitlines()
    dec = next((i for i, l in enumerate(lines) if _heading(l) and re.search(r"decision", l, re.I)), None)
    heads = [i for i, l in enumerate(lines) if _skipped_heading(l)]
    spans = []
    for i in heads:
        lv = _level(lines[i]) if _heading(lines[i]) else 7  # a bold-only line ends at any heading
        end = len(lines)
        for j in range(i + 1, len(lines)):
            if dec is not None and i < dec and j == dec:
                end = j
                break
            if _heading(lines[j]) and _level(lines[j]) <= lv:
                end = j
                break
        spans.append((i + 1, end))
    cuts = ([dec] if dec is not None else []) + [i for i in heads if dec is None or i < dec]
    return {"lines": lines, "dec": dec, "heads": heads, "main": (0, min(cuts) if cuts else len(lines)),
            "skipped_spans": spans}


def _hits(lines: list[str], span: tuple[int, int], slug: str) -> list[int]:
    return [i for i in range(*span) if slug in lines[i].lower()]


def _hits_multi(lines: list[str], spans: list[tuple[int, int]], slug: str) -> list[int]:
    return sorted({i for sp in spans for i in _hits(lines, sp, slug)})


def _leading_number(lines: list[str], i: int):
    for j in range(i, max(i - 3, -1), -1):
        s = re.sub(r"https?://\S+", "", lines[j])
        # a task-list box, empty or ticked, reads the same: "- [ ] **1.**" and "- [x] **1.**"
        s = re.sub(r"^(\s*[-*+>|]*\s*)\[[ xX]\]\s*", r"\1", s)
        m = re.match(r"^[\W_]*?(\d{1,3})(?!\d)(?=[\s.)\]|:*]|$)", s)
        if m:
            return int(m.group(1))
    return None


def _checklist_files(nb: Path, folder: str) -> list[Path]:
    d = nb / "_inbox" / folder
    return sorted(p for p in d.glob("*") if p.is_file() and CHECKLIST_NAME.match(p.name)) if d.is_dir() else []


def _row(feeds_text: str, token: str) -> str:
    return next((l.lower() for l in feeds_text.splitlines() if token in l.lower() and "|" in l), "")


def _final(run: dict) -> str:
    return str(run["result"].get("result") or (run["texts"][-1] if run["texts"] else ""))


def _web_searches(run: dict) -> list[str]:
    return [json.dumps(c.get("input") or {}, ensure_ascii=False).lower()
            for c in run["tool_calls"] if c.get("name") == "WebSearch"]


def check(case: dict, before: dict, after: dict, run: dict, ctx: dict) -> list[dict]:
    res: list[dict] = []

    def add(name, ok, detail=""):
        res.append({"name": name, "ok": bool(ok), "detail": str(detail)[:300]})

    r = run["result"]
    add("session completed", r.get("subtype") == "success" and not r.get("is_error"),
        r.get("subtype") or run.get("stderr_tail") or "no result event")
    errs = run.get("error_texts") or {}
    other = [d for d in (r.get("permission_denials") or [])
             if not (isinstance(d, dict) and "read-guard:" in str(errs.get(d.get("tool_use_id"), "")))]
    add("no permission denials (read-guard counted apart)", not other,
        [d.get("tool_name") if isinstance(d, dict) else d for d in other])

    nb = ctx["notebook"]
    bc = ctx["before_case"]
    now = snapshot(ctx)
    new = sorted(set(now) - set(bc))
    changed = sorted(k for k in now if k in bc and now[k] != bc[k])
    kind = case.get("kind")
    feeds_p = nb / "_config" / "feeds.md"
    feeds_text = feeds_p.read_text(encoding="utf-8", errors="replace") if feeds_p.is_file() else ""

    # nothing is ingested into the wiki: no wiki entry, raw or proposed file added or changed
    bad = [k for k in new + changed if k.startswith(("wiki/", "raw/", "_inbox/proposed/"))]
    add("nothing ingested (no wiki, raw or proposed file added or changed)", not bad, bad)
    pending_new = [k for k in new if k.startswith("_inbox/pending/")]

    if kind in ("judge", "approve"):
        folder, other_folder = ("discovered", "done") if kind == "judge" else ("done", "discovered")
        files = _checklist_files(nb, folder)
        add(f"one checklist at _inbox/{folder}/<date>-discovery.md", len(files) == 1, [p.name for p in files])
        add(f"no checklist left in _inbox/{other_folder}/", not _checklist_files(nb, other_folder),
            [p.name for p in _checklist_files(nb, other_folder)])
        if len(files) != 1:
            return res
        parsed = _parse(files[0].read_text(encoding="utf-8", errors="replace"))
        lines = parsed["lines"]
        spans = parsed["skipped_spans"]
        add("checklist has a Skipped section (before the Decisions log or inside it)", bool(spans))
        main = {k: _hits(lines, parsed["main"], v[0]) for k, v in ITEMS.items()}
        skipped = {k: _hits_multi(lines, spans, v[0]) for k, v in ITEMS.items()}
        listed = {k for k, v in main.items() if v}
        in_skipped = {k for k, v in skipped.items() if v}

        first = min([i for v in main.values() for i in v] or [len(lines)])
        pre = [l for l in lines[:first] if l.strip() and not _heading(l)]
        add("run stats at the top (a non-heading line with a number before the first item)",
            any(re.search(r"\d", l) for l in pre), pre[:3])

        required = ("w1", "w2", "w3", "w4") if kind == "judge" else ("w1", "w2", "w3", "w4", "w5", "w6")
        for k in required:
            add(f"{k} ({ITEMS[k][0]}) is on the numbered checklist", k in listed, "listed" if k in listed else "not listed")
        if kind == "judge":
            for k in ("w5", "w6"):
                add(f"{k} judged: listed or in Skipped", k in listed or k in in_skipped)
        for k in ("o1", "l1"):
            add(f"{k} ({ITEMS[k][0]}) is in Skipped, not on the checklist", k in in_skipped and k not in listed,
                f"listed={k in listed} skipped={k in in_skipped}")
            idx = skipped[k][0] if skipped[k] else None
            if idx is not None:
                s = re.sub(r"https?://\S+", "", lines[idx], flags=re.I)
                s = re.sub(re.escape(ITEMS[k][2]), "", s, flags=re.I)
                add(f"{k} has a reason on its Skipped line", len(re.findall(r"[A-Za-z]", s)) >= 5, lines[idx])
        add("h1 (already held, other link form) is not listed as new", "h1" not in listed)
        unjudged = [k for k in ITEMS if k != "h1" and k not in listed and k not in in_skipped]
        add("every item is on the checklist or in Skipped", not unjudged, unjudged)

        nums = {k: _leading_number(lines, v[0]) for k, v in main.items() if v}
        vals = list(nums.values())
        add("checklist items numbered 1..N across the whole checklist, no repeats",
            bool(vals) and None not in vals and sorted(vals) == list(range(1, len(vals) + 1)), nums)

        bad_pairs = []
        for k in listed | in_skipped:
            ok = False
            for i in main[k] + skipped[k]:
                own = ITEMS[k][1]
                ok = ok or any(own in lines[j].lower().replace("-", " ") for j in range(max(i - 2, 0), i + 1))
            if not ok:
                bad_pairs.append(k)
        add("each title sits with its own link (own title keyword within the link's line or two above)", not bad_pairs, bad_pairs)

        if kind == "judge":
            miss = []
            for k in ("w5", "w6"):  # the community feed is tier 4
                for i in main[k]:
                    near = lines[max(i - 2, 0): i + 3]
                    head = next((lines[j] for j in range(i, -1, -1) if _heading(lines[j])), "")
                    if not any("needs human review" in l.lower() for l in near + [head]):
                        miss.append(k)
            add("tier-4 items listed carry (NEEDS HUMAN REVIEW)", not miss, miss)

        dec = parsed["dec"]
        if dec is None:
            add("Decisions log is the last section", False, "no Decisions heading")
        else:
            lv = _level(lines[dec])
            later = [l for l in lines[dec + 1:] if _heading(l) and _level(l) <= lv]
            tail = "\n".join(lines[dec:]).lower()
            add("Decisions log is the last section", not later, later[:2])
            add("Decisions log names Queued, Skipped and Deferred",
                all(w in tail for w in ("queued", "skipped", "deferred")))

        for tok, old in FEED_ROWS.items():
            row = _row(feeds_text, tok)
            add(f"feeds.md: {tok} To is today", _today() in row and old not in row, row)

        if kind == "judge":
            add("nothing queued in _inbox/pending/", not pending_new, pending_new)
        else:
            texts = {k: (nb / k).read_text(encoding="utf-8", errors="replace").lower() for k in pending_new}
            add("one ticket per listed item", len(pending_new) == len(listed) and len(listed) > 0,
                f"{len(pending_new)} tickets for {len(listed)} listed items")
            per_ticket = {k: [i for i, v in ITEMS.items() if v[0] in t] for k, t in texts.items()}
            add("each ticket is for exactly one item", all(len(v) == 1 for v in per_ticket.values()), per_ticket)
            queued = {v[0] for v in per_ticket.values() if v}
            add("queued items are exactly the listed items", queued == listed, f"queued={sorted(queued)} listed={sorted(listed)}")
            add("nothing skipped or already held was queued", not (queued & (in_skipped | {"h1"})), sorted(queued & (in_skipped | {"h1"})))
        return res

    if kind == "staleness":
        calls = _web_searches(run)
        searched = {t for t in WEB_SOURCES if any(t in c for c in calls)}
        add("exactly the six stalest sources searched (never-checked first)", searched == STALEST_SIX,
            f"searched={sorted(searched)} calls={len(calls)}")
        add("the two freshest sources not searched", not (searched & {"garrowby", "hollis"}), sorted(searched & {"garrowby", "hollis"}))
        for tok, old in WEB_SOURCES.items():
            row = _row(feeds_text, tok)
            if tok in STALEST_SIX:
                add(f"{tok}: To is today after the search", _today() in row, row)
            else:
                add(f"{tok}: To unchanged (not searched)", old in row and _today() not in row, row)
        add("nothing queued", not pending_new, pending_new)
        return res

    if kind in ("missing", "norows"):
        add("searched nothing (no WebSearch call)", not _web_searches(run), len(_web_searches(run)))
        add("no checklist written", not _checklist_files(nb, "discovered") and not pending_new,
            [k for k in new if k.startswith("_inbox/")])
        final = _final(run)
        if kind == "missing":
            add("feeds.md not created without the user's say-so", not feeds_p.is_file())
            add("tells the user feeds.md is missing and offers to create it",
                bool(re.search(r"feeds\.md", run["text"], re.I)) and bool(re.search(r"creat|template", final, re.I)), final[-200:])
        else:
            add("feeds.md left as it was", now.get("_config/feeds.md") == bc.get("_config/feeds.md"))
            add("asks which sources to add (a question naming sources and a URL or link)",
                "?" in final and bool(re.search(r"source", final, re.I)) and bool(re.search(r"url|link|address|site|feed", final, re.I)),
                final[-200:])
        return res

    raise ValueError(f"unknown case kind: {case['id']} ({kind})")
