"""wiki-search test suite: fixtures, sandbox, prompts and checks for run_skill_test.py.

The seed notebook describes Lantern, a made-up service, so no answer can come from
what a model already knows. One entry is a snippet trap: its opening section is a
rejected 30-day proposal, and the 90-day decision comes at the end, so a model that
answers from the search snippet answers wrong (the old skill did, Sonnet, 2026-09-17).

The rule under test (step 2a, "cite only what you opened"): an answer may state a fact
from an entry only after opening it. Each seed entry has facts found only in it
(ENTRY_FACTS); stating one without having opened that entry fails, unless the answer
marks it as unread. A table of search hits names entries without
relying on them, so names alone are not checked. An entry counts as opened when a
Read, or a cat/head/sed/qmd get, named its file.
"""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
NOTEBOOK = "skilltest"
ALLOWED_TOOLS = [
    "Read", "Glob", "Grep",
    "Bash(python:*)", "Bash(python3:*)", "Bash(node:*)", "Bash(npx:*)", "Bash(npm:*)", "Bash(qmd:*)",
    "Bash(cd:*)", "Bash(ls:*)", "Bash(cat:*)", "Bash(grep:*)", "Bash(head:*)", "Bash(tail:*)",
    "Bash(wc:*)", "Bash(find:*)", "Bash(sort:*)", "Bash(echo:*)", "Bash(pwd:*)", "Bash(sed:*)",
]
SEARCH_LOG = Path(os.environ.get("WIKI_QMD_SLOT_DIR") or Path.home() / ".cache" / "wiki-qmd") / "searches.jsonl"
NOT_READ = re.compile(r"not (yet )?(opened|read)|haven'?t (opened|read)|didn'?t (open|read)|unread|unopened|"
                      r"without (opening|reading)|pointer", re.I)
ENTRY_FACTS = {
    "lantern-embedding-retention": r"(?<!\d)(30|90)\s*-?\s*days?\b|120\s*gb",
    "lantern-ingest-batch-size": r"batch(es)? of (250|100)\b|(?<!\d)250 documents|14\s*gb",
    "lantern-chunking": r"(?<!\d)512(?!\d)|64-token|(?<!\d)64 tokens?",
    "lantern-reranker-choice": r"(?<!\d)180\s*ms|lantern-rerank-small|(?<!\d)90\s*ms",
    "lantern-query-latency-budget": r"1\.2\s*s(ec|econds)?\b|(?<!\d)400\s*ms|(?<!\d)250\s*ms",
    "lantern-on-call": r"monday|four engineers",
}
SAYS_NO_ANSWER = re.compile(
    r"no (\w+ )?(entry|entries|information|mention|record|answer)|nothing (in|about|on)|"
    r"not (in|covered|documented|recorded|mentioned)|"
    r"(doesn'?t|does not)( appear to| seem to)? (cover|contain|say|mention|document|have|include)|"
    r"(couldn'?t|could not|did not|didn'?t) find|don'?t have|no (rpo|disaster)", re.I)


def _suite() -> dict:
    return json.loads((HERE / "cases.json").read_text(encoding="utf-8"))


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
    return []  # every fixture is written for the test and lives in fixtures/


def setup(model: str, sandbox: Path, repo: Path) -> dict:
    if sandbox.exists():
        shutil.rmtree(sandbox)
    nb = sandbox / "notebooks" / NOTEBOOK
    shutil.copytree(HERE / "fixtures" / "seed-notebook", nb)
    (nb / "_inbox" / "temp").mkdir(parents=True, exist_ok=True)
    registry = sandbox / "linked-notebooks.json"
    registry.write_text(json.dumps({"notebooks": {NOTEBOOK: {"root": f"notebooks/{NOTEBOOK}"}}}, indent=2),
                        encoding="utf-8")
    project = sandbox / "project"
    (project / ".claude").mkdir(parents=True)
    cfg = json.dumps({"tool": "claude-code", "project_name": "skilltest", "notebook": NOTEBOOK,
                      "registry": registry.as_posix()}, indent=2)
    (project / ".claude" / "wiki-config.json").write_text(cfg, encoding="utf-8")
    (sandbox / ".claude").mkdir(exist_ok=True)
    (sandbox / ".claude" / "wiki-config.json").write_text(cfg, encoding="utf-8")
    index = f"skilltest-search-{model}-{sandbox.parent.name}"
    _qmd_index_file(index).unlink(missing_ok=True)
    for args in (["collection", "add", str(nb / "wiki")], ["embed"]):
        subprocess.run([*_qmd(), "--index", index, *args], capture_output=True, text=True,
                       encoding="utf-8", errors="replace", timeout=600)
    return {"sandbox": sandbox, "project": project, "notebook": nb, "registry": registry,
            "skill_dir": sandbox / "skill" / "wiki-search", "index": index,
            "scripts": repo / "bootstrap" / "scripts",
            "env": {"WIKI_QMD_INDEX": index, "WIKI_QMD_CALLER": f"skilltest-search-{model}-{sandbox.parent.name}",
                    "PYTHONIOENCODING": "utf-8"}}


def teardown(ctx: dict) -> None:
    shutil.rmtree(ctx["sandbox"], ignore_errors=True)
    _qmd_index_file(ctx["index"]).unlink(missing_ok=True)


def snapshot(ctx: dict) -> dict:
    nb = ctx["notebook"]
    return {p.relative_to(nb).as_posix(): (p.stat().st_size, p.stat().st_mtime_ns)
            for p in nb.rglob("*") if p.is_file()}


HEADER = """You are running an automated test of the wiki-search skill. The skill under test is at {skill}/SKILL.md. Read it and follow it exactly, as if the user had typed /wiki-search with the question below. Do not use any installed copy of the skill.

The notebook is `{notebook}`, this project's notebook, at {nb}. Its search index is named `{index}`: the search helper picks that up by itself (pass it no `--index`); pass `--index {index}` only to a `qmd` command you run directly. Run scripts as `python <path> ...`, with no environment-variable prefix. Do not write, edit or create any file. The user wants the answer to their question and will read your final message, but cannot reply while this runs: where the skill says to offer something or ask the user, say in your final message what you would offer or ask.

The user's question: """


def prompt(case: dict, ctx: dict) -> str:
    return HEADER.format(skill=ctx["skill_dir"].as_posix(), notebook=NOTEBOOK, nb=ctx["notebook"].as_posix(),
                         index=ctx["index"]) + case["question"]


def _logged_searches(caller) -> list[dict]:
    if not caller or not SEARCH_LOG.is_file():
        return []
    out = []
    for line in SEARCH_LOG.read_text(encoding="utf-8", errors="replace").splitlines():
        try:
            r = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(r, dict) and r.get("caller") == caller:
            out.append(r)
    return out


def _opened(run: dict) -> set:
    text = []
    for c in run["tool_calls"]:
        inp = c["input"]
        if c["name"] == "Read":
            text.append(str(inp.get("file_path", "")))
        elif c["name"] == "Bash":
            cmd = str(inp.get("command", ""))
            if re.search(r"\b(cat|head|tail|sed|type|more|less)\b|\bget\b", cmd):
                text.append(cmd)
    return set(re.findall(r"([a-z0-9-]+)\.md", "\n".join(text)))


def _final_answer(run: dict) -> str:
    return str(run["result"].get("result") or (run["texts"][-1] if run["texts"] else ""))


def check(case: dict, before: dict, after: dict, run: dict, ctx: dict) -> list[dict]:
    res = []

    def add(name, ok, detail=""):
        res.append({"name": name, "ok": bool(ok), "detail": str(detail)[:300]})

    r = run["result"]
    add("session completed", r.get("subtype") == "success" and not r.get("is_error"),
        r.get("subtype") or run.get("stderr_tail") or "no result event")
    denials = r.get("permission_denials") or []
    add("no permission denials", not denials, [d.get("tool_name") if isinstance(d, dict) else d for d in denials])
    changed = sorted(k for k in set(before) | set(after) if before.get(k) != after.get(k))
    add("nothing written to the notebook", not changed, changed)

    answer = _final_answer(run)
    low = answer.lower()
    kind = case["kind"]

    if kind == "holistic":
        add("routes to /wiki-claims or /wiki-lint --full", "wiki-claims" in low or "wiki-lint" in low)
        return res

    searches = [s for s in _logged_searches(run.get("caller")) if s.get("outcome") == "ok"]
    # a session may pass its own --caller, which hides its searches from the log's tag
    helper_calls = [str(c["input"].get("command", "")) for c in run["tool_calls"] if c["name"] == "Bash"
                    and "wiki-qmd-query.py" in str(c["input"].get("command", ""))
                    and not re.search(r"--(help|preflight|stats|depth-check)\b", str(c["input"].get("command", "")))]
    add("searched with the full search helper", searches or helper_calls,
        f"{len(searches)} logged, {len(helper_calls)} helper calls")
    add("no search outside this notebook",
        not any(re.search(r"--all-notebooks|--notebook\s+(?!skilltest\b)", c) for c in helper_calls)
        and all(NOTEBOOK in str(s.get("scope", "")) for s in searches), [s.get("scope") for s in searches])

    opened = _opened(run)
    unflagged = []
    for slug, pat in ENTRY_FACTS.items():
        if slug in opened:
            continue
        spots = [m.start() for m in re.finditer(pat, answer, re.I)]
        if spots and not any(NOT_READ.search(answer[max(0, i - 250): i + 250]) for i in spots):
            unflagged.append(f"{slug}: {answer[spots[0]:spots[0] + 40]!r}")
    add("states facts only from opened entries (others marked as not read)", not unflagged, unflagged)

    if kind == "gap":
        add("says the wiki does not answer it", SAYS_NO_ANSWER.search(answer), answer[:200])
        add("invents no RPO figure",
            not re.search(r"\brpo\b[^.\n]{0,60}\b\d+\s*(s|sec|seconds|min|minutes|h|hours)\b", low),
            re.findall(r"\brpo\b[^.\n]{0,60}", low)[:2])
        return res

    for slug in case["must_open"]:
        add(f"opened {slug}", slug in opened, sorted(opened))
    for fact in case["answer_has"]:
        add(f"answer states {fact}", re.search(rf"(?<![\d.]){re.escape(fact)}(?![\d.])", answer), answer[:200])
    if case["id"] == "snippet-trap-retention":
        add("does not give 30 days as the answer",
            not re.search(r"\b30\s*days?\b", low)
            or re.search(r"reject|propos|superseded|revis|original|not 30|instead of 30", low), answer[:200])
    if kind == "compare":
        add("offers to file the answer", re.search(r"\bfil(e|ing)\b|worth keeping|project/", low), answer[-300:])
    return res
