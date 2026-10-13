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
