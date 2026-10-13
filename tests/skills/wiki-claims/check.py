"""wiki-claims test suite: sandbox, prompts and checks for run_skill_test.py (task #16, 2026-10-12).

A throwaway registry with one notebook, `skilltest-claims`. For each case the notebook is rebuilt
from fixtures/notebooks/<case "notebook">/ (its `wiki/` entries carry the planted claims; an
optional `_inbox/claims-index.json` for a run that appends to an existing index). The skill reads
and writes files only: no search index is needed.

Each case names:
- `notebook`: a folder in fixtures/notebooks/ copied as the notebook root;
- `say`: the user's line; `answers` (optional): what the user answers if the skill asks.

The checks read what the session left behind and its tool calls, never its reasoning.
"""

from __future__ import annotations

import json
import os
import re
import shutil
import stat
from pathlib import Path

HERE = Path(__file__).resolve().parent
NOTEBOOK = "skilltest-claims"
ALLOWED_TOOLS = [
    "Read", "Write", "Edit", "Glob", "Grep",
    "Bash(python:*)", "Bash(python3:*)", "Bash(uv:*)",
    "Bash(cd:*)", "Bash(ls:*)", "Bash(cat:*)", "Bash(grep:*)", "Bash(head:*)", "Bash(tail:*)",
    "Bash(wc:*)", "Bash(find:*)", "Bash(sort:*)", "Bash(echo:*)", "Bash(pwd:*)", "Bash(sed:*)",
    "Bash(mkdir:*)", "Bash(date:*)",
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


def prepare_fixtures(repo: Path, refresh: bool = False) -> list[dict]:
    return []  # every entry is written for the test


def setup(model: str, sandbox: Path, repo: Path) -> dict:
    _rmtree(sandbox)
    nb = sandbox / "notebooks" / NOTEBOOK
    nb.mkdir(parents=True)
    registry = sandbox / "linked-notebooks.json"
    registry.write_text(json.dumps({"notebooks": {NOTEBOOK: {"root": f"notebooks/{NOTEBOOK}"}}}, indent=2),
                        encoding="utf-8")
    project = sandbox / "project"
    cfg = json.dumps({"tool": "claude-code", "project_name": NOTEBOOK, "notebook": NOTEBOOK, "persona": "main",
                      "registry": registry.as_posix()}, indent=2)
    for d in (project, sandbox):
        (d / ".claude").mkdir(parents=True, exist_ok=True)
        (d / ".claude" / "wiki-config.json").write_text(cfg, encoding="utf-8")
    return {"sandbox": sandbox, "project": project, "notebook": nb, "registry": registry,
            "skill_dir": sandbox / "skill" / "wiki-claims", "scripts": repo / "scripts",
            "env": {"PYTHONIOENCODING": "utf-8"}}


def teardown(ctx: dict) -> None:
    _rmtree(ctx["sandbox"])


def snapshot(ctx: dict) -> dict:
    nb = ctx["notebook"]
    if not nb.exists():
        return {}
    return {p.relative_to(nb).as_posix(): (p.stat().st_size, p.stat().st_mtime_ns) for p in nb.rglob("*") if p.is_file()}


HEADER = """You are running an automated test of the wiki-claims skill. The skill under test is at {skill}/SKILL.md. Read it and follow it exactly, as if the user had said the message below in this project. Do not use any installed copy of any skill.

The notebook is `{notebook}`, this project's notebook, at {nb}. Run scripts as the skill writes them, `uv run --project <scripts dir> python <path> ...`, with no environment-variable prefix, and write only inside {sandbox}. The user cannot reply while this runs: where the skill says to ask the user something, take the answer given below if there is one; with none given, ask it in your final message and stop there, without acting on an answer you do not have.

{answers}The user said: """


def prompt(case: dict, ctx: dict) -> str:
    nb = ctx["notebook"]
    _rmtree(nb)
    shutil.copytree(HERE / "fixtures" / "notebooks" / case["notebook"], nb)
    ctx["before_case"] = snapshot(ctx)
    answers = f"When the skill asks the user, the user answers: {case['answers']}\n\n" if case.get("answers") else ""
    return HEADER.format(skill=ctx["skill_dir"].as_posix(), notebook=NOTEBOOK, nb=nb.as_posix(),
                         sandbox=ctx["sandbox"].as_posix(), answers=answers) + case["say"]


SEVERITIES = ("high", "medium", "low")
LABELS = {"direct-quote", "sourced", "synthesis", "inference"}
REPORT_NAME = re.compile(r"^claims-report-\d{4}-\d{2}-\d{2}\.md$")
INDEX_KEY = "_inbox/claims-index.json"

CASES = {  # kind: the fixture notebook, the entries a finding must name, and a regex for the planted subject or figures
    "conflict": {"nb": "claims-conflict", "entries": ["vexil-retrieval-evaluation", "agent-memory-landscape"],
                 "token": r"membench|71\.4|58\.2"},
    "stale": {"nb": "claims-stale", "entries": ["gleam-toolkit-overview", "gleam-release-notes-2026-09"],
              "token": r"exporter|\b2\.1\b|\b3\.0\b|\b12\b|\b15\b"},
    "drift": {"nb": "claims-drift", "entries": ["citation-guard-evaluation"],
              "token": r"eliminat|\b31\b|reduc|hallucinat|18\.2|12\.6"},
    "framing": {"nb": "claims-framing", "entries": ["loomdb-failover-results", "loomdb-operations-notes"],
                "token": r"write-ahead|replay|\b2 s|two seconds|2-second|about 2"},
    "corroborate-repost": {"nb": "claims-corroborate-repost",
                           "entries": ["quillbench-paper", "reel-marlin-quillbench"],
                           "token": r"quillbench|63\.8"},
    "corroborate-disagree": {"nb": "claims-corroborate-disagree",
                             "entries": ["harbor-cache-field-notes", "spindle-queue-throughput-page"],
                             "token": r"15 minutes|120"},
}
STALE_WORDS = re.compile(r"stale|outdat|out[\s-]of[\s-]date|supersed|obsolete|no longer|\bolder?\b", re.I)
DRIFT_WORDS = re.compile(r"intra[\s_-]*entry|drift|overstat|exaggerat|overclaim|inconsisten|does not match|doesn't match", re.I)
CONFLICT_WORDS = re.compile(r"direct[\s_-]*conflict", re.I)


def _final(run: dict) -> str:
    return str(run["result"].get("result") or (run["texts"][-1] if run["texts"] else ""))


def _title(path: Path) -> str:
    m = re.search(r'^title:\s*"?(.*?)"?\s*$', path.read_text(encoding="utf-8"), re.M)
    return m.group(1).lower() if m else ""


def _aliases(nbname: str, stem: str) -> list[str]:
    """The ways a report can name an entry: its file stem, the stem with spaces, its frontmatter title."""
    out = [stem.lower(), stem.lower().replace("-", " ")]
    for p in (HERE / "fixtures" / "notebooks" / nbname / "wiki").rglob(f"{stem}.md"):
        if _title(p):
            out.append(_title(p))
    return out


def _all_entries(nbname: str) -> dict[str, list[str]]:
    root = HERE / "fixtures" / "notebooks" / nbname / "wiki"
    return {p.stem: _aliases(nbname, p.stem) for p in sorted(root.rglob("*.md"))}


def _keys(o) -> set[str]:
    if isinstance(o, dict):
        return {str(k).lower() for k in o} | {k for v in o.values() for k in _keys(v)}
    if isinstance(o, list):
        return {k for v in o for k in _keys(v)}
    return set()


def _strings(o) -> list[str]:
    if isinstance(o, str):
        return [o]
    if isinstance(o, dict):
        return [s for v in o.values() for s in _strings(v)]
    if isinstance(o, list):
        return [s for v in o for s in _strings(v)]
    return []


def _claims(data) -> list[dict]:
    """The claim records: dicts in lists under a key named like 'claims' (never inside a contradictions record);
    failing that, the largest list of dicts that all carry a subject."""
    groups: list[tuple[str, list[dict]]] = []

    def visit(o, path=""):
        if isinstance(o, list):
            items = [i for i in o if isinstance(i, dict)]
            if items and len(items) == len(o):
                groups.append((path, items))
            for v in o:
                visit(v, path)
        elif isinstance(o, dict):
            for k, v in o.items():
                visit(v, f"{path}/{str(k).lower()}")
    visit(data)
    named = [i for p, items in groups if "claim" in p.rsplit("/", 1)[-1] and "contradict" not in p for i in items]
    if named:
        return named
    withsubj = [items for _, items in groups if all("subject" in _keys(i) for i in items)]
    return max(withsubj, key=len, default=[])


def _heading_level(line: str) -> int:
    s = line.strip()
    m = re.match(r"^(#{1,6})\s+\S", s)
    if m:
        return len(m.group(1))
    return 7 if re.match(r"^\*\*[^*]+\*\*:?\s*$", s) else 0


def _sev_words(text: str) -> set[str]:
    return {m.lower() for m in re.findall(r"(?i)\b(high|medium|low)\b", text)}


def _heading_severity(lines: list[str], i: int) -> set[str]:
    """The severity of the group heading a line sits under (a heading naming exactly one severity, with no
    same-or-shallower heading of another kind between it and the line)."""
    seen = 99
    for j in range(i, -1, -1):
        lv = _heading_level(lines[j])
        if not lv:
            continue
        w = _sev_words(lines[j])
        if len(w) == 1 and lv < seen:
            return w
        if not w or len(w) > 1:
            seen = min(seen, lv)
    return set()


def _windows(lines: list[str], groups: list[list[str]], token: str, radius: int = 4) -> list[dict]:
    """Every window of lines, centred on a line that names one of the entries, in which each entry is named and the
    planted subject or figures appear: a finding that touches those entries. `wide` is every severity word in the
    window or its group heading; `narrow` only those on lines that name an entry or carry the subject, else the
    group heading's."""
    out = []
    flat = [a for g in groups for a in g]
    for i, line in enumerate(lines):
        if not any(a in line.lower() for a in flat):
            continue
        lo, hi = max(0, i - radius), min(len(lines), i + radius + 1)
        block = lines[lo:hi]
        text = "\n".join(block).lower()
        if not (all(any(a in text for a in g) for g in groups) and re.search(token, text, re.I)):
            continue
        own = [l for l in block if any(a in l.lower() for a in flat) or re.search(token, l, re.I)]
        narrow = set().union(*[_sev_words(l) for l in own]) if own else set()
        out.append({"text": text, "wide": _sev_words(text) | _heading_severity(lines, i),
                    "narrow": narrow or _heading_severity(lines, i)})
    return out


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

    spec = CASES.get(case.get("kind"))
    if not spec:
        raise ValueError(f"unknown case kind: {case['id']} ({case.get('kind')})")
    nb = ctx["notebook"]
    bc = ctx["before_case"]
    now = snapshot(ctx)
    entries = _all_entries(spec["nb"])

    # requirement 7: flagged, never resolved: no wiki entry added, removed or changed
    bad = sorted(k for k in set(bc) | set(now) if k.startswith("wiki/") and bc.get(k) != now.get(k))
    add("no file under wiki/ added, removed or changed", not bad, bad)

    # requirement 4: the index, beside wiki/
    claims: list[dict] = []
    add("claims index exists at _inbox/claims-index.json", INDEX_KEY in now)
    if INDEX_KEY in now:
        try:
            data = json.loads((nb / INDEX_KEY).read_text(encoding="utf-8"))
        except (ValueError, OSError) as e:
            add("claims index parses as JSON", False, e)
            data = None
        if data is not None:
            add("claims index parses as JSON", True)
            claims = _claims(data)
            add("index holds claims (at least 6 for this notebook)", len(claims) >= 6, len(claims))
            no_label = [i for i, c in enumerate(claims)
                        if not any(re.sub(r"[\s_]+", "-", s.strip().lower()) in LABELS for s in _strings(c))]
            add("every claim carries one of the four classifications", claims and not no_label, no_label[:10])
            no_spo = [i for i, c in enumerate(claims) if not {"subject", "predicate", "object"} <= _keys(c)]
            add("every claim carries subject, predicate and object", claims and not no_spo, no_spo[:10])
            joined = [" ".join(_strings(c)).lower() for c in claims]
            no_src = [i for i, t in enumerate(joined) if not any(a in t for al in entries.values() for a in al)]
            add("every claim names its source entry", claims and not no_src, no_src[:10])
            silent = [stem for stem, al in entries.items() if not any(a in t for t in joined for a in al)]
            add("every entry has at least one claim (a full run scans them all)", claims and not silent, silent)

    # requirement 6: the report
    reports = sorted(k for k in now if k.startswith("_inbox/reports/") and REPORT_NAME.match(k.rsplit("/", 1)[-1]))
    add("one report at _inbox/reports/claims-report-<date>.md", len(reports) >= 1, reports)
    lines: list[str] = []
    if reports:
        rtext = (nb / reports[-1]).read_text(encoding="utf-8", errors="replace")
        lines = rtext.splitlines()

        def has_number(n: int) -> bool:
            return bool(re.search(rf"(?<![\d.]){n}(?!\d)", rtext))

        add("report states how many entries were scanned", has_number(len(entries)), f"expected {len(entries)}")
        add("report states how many claims the index holds", bool(claims) and has_number(len(claims)),
            f"index has {len(claims)}")
        add("report counts contradictions by severity (names high, medium or low)", bool(_sev_words(rtext)))
        add("report lists the inference claims", bool(re.search(r"inference", rtext, re.I)))

    final = _final(run)
    add("final summary names the report and the index",
        bool(re.search(r"claims-report", final, re.I)) and bool(re.search(r"claims-index", final, re.I)), final[-200:])

    # the planted problem
    groups = [_aliases(spec["nb"], stem) for stem in spec["entries"]]
    found = _windows(lines, groups, spec["token"]) if lines else []
    kind = case["kind"]
    if kind.startswith("corroborate-"):
        import sys
        sys.path.insert(0, str(HERE.parent))
        import _trajectory

        def walk(o, key):
            if isinstance(o, dict):
                for k, v in o.items():
                    if str(k).lower() == key:
                        return v
                for v in o.values():
                    r2 = walk(v, key)
                    if r2 is not None:
                        return r2
            elif isinstance(o, list):
                for v in o:
                    r2 = walk(v, key)
                    if r2 is not None:
                        return r2
            return None

        def rec(c):
            v = walk(c, "corroboration")
            return v if isinstance(v, dict) else None

        def num(r, key):
            v = r.get(key) if isinstance(r, dict) else None
            if isinstance(v, bool):
                return None
            try:
                return float(v)
            except (TypeError, ValueError):
                return None

        def vals(c):
            r = rec(c)
            return (num(r, "independent_sources"), num(r, "score")) if r else (None, None)

        def about(stem, token):
            out = []
            for c in claims:
                t = " ".join(_strings(c))
                if any(a in t.lower() for a in entries[stem]) and re.search(token, t, re.I):
                    out.append(c)
            return out

        def scalars(o) -> set[str]:
            if isinstance(o, dict):
                return {s for v in o.values() for s in scalars(v)}
            if isinstance(o, list):
                return {s for v in o for s in scalars(v)}
            return {str(o)}

        def norm(l):
            return re.sub(r"\s+", " ", l.strip().lower())

        # ---- the record's shape (task #110: group, sources[key, entries, claims, tier, weight, merged_because],
        # independent_sources, score, computed); every claim in a group carries the same record
        REC_KEYS = {"group", "sources", "independent_sources", "score", "computed"}
        SRC_KEYS = {"key", "entries", "claims", "tier", "weight", "merged_because"}
        WEIGHT = {1: 1.0, 2: 0.6, 3: 0.3, 4: 0.1}
        REASON = re.compile(r"^(same origin: .+|same source URL)$")

        def shape_problems(r):
            if not isinstance(r, dict) or not REC_KEYS <= set(r):
                return ["record keys"]
            if not isinstance(r["sources"], list) or not r["sources"]:
                return ["sources list"]
            bad = []
            for s in r["sources"]:
                if not isinstance(s, dict) or not SRC_KEYS <= set(s):
                    bad.append("source keys")
                    continue
                mb = s["merged_because"]
                if not isinstance(mb, list) or not all(isinstance(x, str) and REASON.match(x) for x in mb):
                    bad.append(f"merged_because {mb!r}")
                n = len(s["claims"]) if isinstance(s["claims"], list) else s["claims"]
                if n == 1 and mb != []:
                    bad.append("merged_because not empty for a one-claim source")
                if s["tier"] in WEIGHT and num(s, "weight") is not None and abs(num(s, "weight") - WEIGHT[s["tier"]]) > 0.001:
                    bad.append(f"weight {s['weight']} for tier {s['tier']}")
                if s["tier"] == "self" and num(s, "weight") not in (None, 0.0):
                    bad.append(f"self source weighs {s['weight']}")
            return bad

        recs = [(c, rec(c)) for c in claims if rec(c)]
        shape = [p for _, r in recs for p in shape_problems(r)]
        add("every corroboration record has the fixed keys, and every source item its keys and a well-formed merged_because",
            bool(recs) and not shape, shape[:4])
        by_group: dict[str, set[str]] = {}
        for _, r in recs:
            by_group.setdefault(str(r.get("group")), set()).add(json.dumps(r, sort_keys=True))
        add("every claim in a group carries the same record", bool(recs) and all(len(v) == 1 for v in by_group.values()),
            [g for g, v in by_group.items() if len(v) > 1][:5])

        # ---- the script wrote the record, from the run's tool calls (a refused call never counts)
        ss = _trajectory.steps(run)
        shell = ("Bash", "PowerShell")
        ran = [s for s in ss if s.name in shell and re.search(r"wiki-claims-corroborate\.py", s.text)
               and not re.search(r"--dry-run", s.text)]
        add("the session ran wiki-claims-corroborate.py, not as a dry run", bool(ran), len(ran))

        def wrote_record(s):
            t = s.text.lower()
            if "corroboration" not in t:
                return False
            if s.name in ("Write", "Edit", "MultiEdit"):
                return bool(re.search(r"file_path=\S*claims-index\.json", s.text))
            if s.name in shell:
                return "claims-index" in t and "wiki-claims-corroborate" not in t and "claims-report" not in t
            return False

        hand = [s.text[:150] for s in ss if wrote_record(s)]
        add("the session never wrote a corroboration key into the index itself", not hand, hand[:2])

        # ---- the report's Corroboration section, fixed layout
        sec: list[str] = []
        for i, l in enumerate(lines):
            if l.strip() == "## Corroboration":
                for m in lines[i + 1:]:
                    if 0 < _heading_level(m) <= 2:
                        break
                    sec.append(m)
                break
        sec_text = "\n".join(sec).lower()
        add("the report has a '## Corroboration' section with content", bool(sec_text.strip()), f"{len(sec)} lines")

        groups_n = len(by_group)
        well = len({g for g, v in by_group.items()
                    for r in [json.loads(next(iter(v)))]
                    if (num(r, "independent_sources") or 0) >= 2 and (num(r, "score") or 0) >= 1.0})

        def entry_tier(c):
            se = walk(c, "source_entry")
            stems = [Path(str(se)).stem] if isinstance(se, str) and se else []
            if not stems or stems[0] not in entries:
                t = " ".join(_strings(c)).lower()
                stems = [st for st, al in entries.items() if any(a in t for a in al)][:1]
            for st in stems:
                for p in (HERE / "fixtures" / "notebooks" / spec["nb"] / "wiki").rglob(f"{st}.md"):
                    m = re.search(r"^tier:\s*\"?(\w+)", p.read_text(encoding="utf-8"), re.M)
                    return m.group(1) if m else None
            return None

        single4 = sum(1 for c in claims if not rec(c) and entry_tier(c) == "4")
        SUMMARY = re.compile(r"^(\d+) groups? of agreeing claims \((\d+) claims?\); (\d+) well corroborated "
                             r"\(score >= 1\.0 from 2\+ independent sources\); (\d+) claims? rests? on a single tier-4 entry\.$")
        sm = next((m for m in (SUMMARY.match(l.strip()) for l in sec) if m), None)
        add("the section opens with the summary line in the fixed wording", bool(sm), sec[:3])
        add("the summary line's group and claim counts match the index's records",
            bool(sm) and bool(recs) and (int(sm.group(1)), int(sm.group(2))) == (groups_n, len(recs)),
            f"line {sm.groups() if sm else None}, index {(groups_n, len(recs))}")
        add("the summary line's well-corroborated count matches the index's records",
            bool(sm) and bool(recs) and int(sm.group(3)) == well, f"line {sm.group(3) if sm else None}, index {well}")
        add("the summary line's single-tier-4-entry count matches the index's records",
            bool(sm) and bool(recs) and int(sm.group(4)) == single4, f"line {sm.group(4) if sm else None}, index {single4}")

        hi = next((i for i, l in enumerate(sec) if norm(l) == "| score | sources | claim | sources counted (merged because) |"), None)
        rows: list[list[str]] = []
        if hi is not None and hi + 1 < len(sec) and re.match(r"^\s*\|[\s:|-]+\|\s*$", sec[hi + 1]):
            for l in sec[hi + 2:]:
                if not l.strip().startswith("|"):
                    break
                rows.append([x.strip() for x in l.strip().strip("|").split("|")])
        add("the section has the table header '| Score | Sources | Claim | Sources counted (merged because) |'", hi is not None)
        add("the table has one row per group in the index", bool(recs) and len(rows) == groups_n, f"{len(rows)} rows, {groups_n} groups")

        if kind == "corroborate-repost":
            paper = "quillbench-paper"
            reposts = ["reel-marlin-quillbench", "carousel-marlin-quillbench",
                       "story-marlin-quillbench", "repost-marlin-quillbench"]
            tok = spec["token"]
            pv = [vals(c) for c in about(paper, tok)]
            add("the paper's figure claim has a corroboration record: independent_sources 1, score 1.0",
                any(i == 1 and s is not None and abs(s - 1.0) < 0.01 for i, s in pv), pv)
            fig = [c for c in claims if re.search(tok, " ".join(_strings(c)), re.I) and rec(c)]
            over = [vals(c) for c in fig if (vals(c)[0] or 0) > 1 or (vals(c)[1] or 0) > 1.01]
            add("no claim stating the figure is credited with more than one independent source or a score above 1.0",
                bool(fig) and not over, over[:5])
            missing = [r for r in reposts if not any(rec(c) for c in about(r, tok))]
            add("each of the four reposts' figure claims carries a corroboration record", not missing, missing)

            def merged_source(r):
                for s in r.get("sources") or []:
                    if not isinstance(s, dict) or not isinstance(s.get("entries"), list):
                        continue
                    ent = " ".join(str(e) for e in s["entries"]).lower()
                    if all(any(a in ent for a in entries[x]) for x in [paper] + reposts):
                        return s
                return None
            ms = [merged_source(rec(c)) for c in about(paper, tok) if rec(c)]
            ms = [m for m in ms if m]
            add("one source item holds the paper and all four reposts, at tier 1 and weight 1.0 (the best tier among them)",
                any(m.get("tier") == 1 and num(m, "weight") is not None and abs(num(m, "weight") - 1.0) < 0.01 for m in ms),
                [(m.get("tier"), m.get("weight")) for m in ms])
            add("that merged source lists why it was merged (merged_because, not empty)",
                any(isinstance(m.get("merged_because"), list) and m["merged_because"] for m in ms),
                [m.get("merged_because") for m in ms])
            row = next((r for r in rows if len(r) >= 4
                        and all(any(a in r[3].lower() for a in entries[x]) for x in [paper] + reposts)), None)
            add("the table's row for that group lists the paper and the four reposts in its last column", row is not None, rows[:3])
            add("that row shows 1 source and score 1.0",
                bool(row) and re.fullmatch(r"1", row[1]) is not None and abs(float(re.sub(r"[^\d.]", "", row[0]) or -1) - 1.0) < 0.01,
                row)
            add("that row's last column gives the merge reason ('same origin' or 'same source URL')",
                bool(row) and bool(re.search(r"same origin|same source URL", row[3])), row)
        else:
            a_stem, c_stem = "harbor-cache-field-notes", "spindle-queue-throughput-page"
            b_stems = ["harbor-cache-docs-walkthrough", "harbor-ops-review-2026"]
            ht = r"15 minutes|fifteen|\b15\b|idle|expire|evict"
            ct = r"120,?000|120k|messages per second|msgs/sec|throughput"
            hv = [vals(c) for s in [a_stem] + b_stems for c in about(s, ht)]
            add("the Harbor idle-timeout claims carry corroboration with 2 or more independent sources and score 1.0 or more",
                any(i is not None and i >= 2 and s is not None and s >= 1.0 for i, s in hv), hv[:6])
            cv = [vals(c) for c in about(c_stem, ct)]
            add("the Spindle throughput claim carries corroboration with independent_sources 1 and score under 0.3",
                any(i == 1 and s is not None and s < 0.3 for i, s in cv), cv[:6])

            sub: list[str] = []
            for i, l in enumerate(sec):
                if norm(l) == "### confidence and corroboration disagree":
                    for m in sec[i + 1:]:
                        if 0 < _heading_level(m) <= 3:
                            break
                        sub.append(m.strip())
                    break
            sub = [l for l in sub if l]
            add("the section has '### Confidence and corroboration disagree'", bool(sub) or any(
                norm(l) == "### confidence and corroboration disagree" for l in sec), len(sub))
            FLAG = re.compile(r"^- (\S+) in (\S+): confidence (high|low), score (\d+(?:\.\d+)?) \((.+)\)$")
            flags = [FLAG.match(l) for l in sub]
            add("every line under it is a flag in the form '- <claim id> in <entry path>: confidence <high|low>, score <n> (<why>)'",
                bool(sub) and all(flags) and "None." not in sub, sub[:4])

            def flag_for(stem, conf, claim_list):
                for m in flags:
                    if m and stem in m.group(2).lower() and m.group(3) == conf:
                        ids = {i for c in claim_list for i in scalars(c)}
                        sc = [vals(c)[1] for c in claim_list if m.group(1) in scalars(c)]
                        if m.group(1) in ids and any(s is not None and abs(s - float(m.group(4))) < 0.05 for s in sc):
                            return True
                return False
            add("a flag names a Harbor field-notes claim in that entry, confidence low, with the score its record carries",
                flag_for(a_stem, "low", about(a_stem, ".")))
            add("a flag names a Spindle throughput claim in that entry, confidence high, with the score its record carries",
                flag_for(c_stem, "high", about(c_stem, ".")))

            fm = {}
            for stem in (a_stem, c_stem):
                hits = list((nb / "wiki").rglob(f"{stem}.md"))
                m = re.search(r"^confidence:\s*(\w+)", hits[0].read_text(encoding="utf-8"), re.M) if hits else None
                fm[stem] = m.group(1) if m else None
            add("the two flagged entries keep their confidence in frontmatter",
                fm == {a_stem: "low", c_stem: "high"}, fm)
            wrong = []
            for m in flags:
                if m:
                    hits = list((nb / "wiki").rglob(f"{Path(m.group(2).strip('`')).stem}.md"))
                    f = re.search(r"^confidence:\s*(\w+)", hits[0].read_text(encoding="utf-8"), re.M) if hits else None
                    if f and f.group(1) != m.group(3):
                        wrong.append((m.group(2), m.group(3), f.group(1)))
            add("every flag states the confidence its entry actually carries", not wrong, wrong[:3])
        return res
    if kind == "framing":
        high = [w for w in found if "high" in w["narrow"]]
        add("same fact, different emphasis is not reported as a high-severity contradiction", not high,
            f"{len(high)} high-severity finding(s) naming both entries")
        return res

    names = " and ".join(spec["entries"])
    add(f"a contradiction names {names} and the planted subject", bool(found), "no finding in the report")
    if kind == "conflict":
        add("the conflict is typed direct_conflict", any(CONFLICT_WORDS.search(w["text"]) for w in found))
        add("the conflict has severity high", any("high" in w["wide"] for w in found),
            [sorted(w["wide"]) for w in found][:3])
    elif kind == "stale":
        add("the older entry's release and count are flagged as stale or superseded",
            any(STALE_WORDS.search(w["text"]) for w in found))
    elif kind == "drift":
        add("flagged as drift inside that one entry (TL;DR against body)",
            any(DRIFT_WORDS.search(w["text"]) for w in found))
    return res
