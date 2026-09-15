"""wiki-update test suite: fixtures, sandbox, prompts and checks for run_skill_test.py.

The cached sources (an article, a YouTube transcript, a PDF, an X post) are fetched
live from the URLs in cases.json the first time, or with --refresh-fixtures, and kept
in ~/.cache/llm-wiki-skilltest/wiki-update/ — third-party text never enters the repo.
The seed notebook and the input samples under fixtures/ are written for the tests.
"""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
NOTEBOOK = "skilltest"
CACHE = Path(os.environ.get("SKILLTEST_CACHE") or Path.home() / ".cache" / "llm-wiki-skilltest" / "wiki-update")
MACHINE_FILES = {"_index.md", "_map.md", "index.md", "map.md", "readme.md"}
REQUIRED_FM = ("title", "date", "source_url", "ingested_by", "tier", "confidence",
               "last_reviewed", "review_after", "tags")


def _suite() -> dict:
    return json.loads((HERE / "cases.json").read_text(encoding="utf-8"))


def _scripts(repo: Path) -> Path:
    return repo / "bootstrap" / "scripts"


def _qmd() -> list[str]:
    shim = shutil.which("qmd")
    if not shim:
        raise SystemExit("qmd not found on PATH")
    entry = Path(shim).resolve().parent / "node_modules" / "@tobilu" / "qmd" / "dist" / "cli" / "qmd.js"
    node = shutil.which("node")
    return [node, str(entry)] if entry.exists() and node else [shim]


def _qmd_index_file(index: str) -> Path:
    return Path.home() / ".cache" / "qmd" / f"{index}.sqlite"


# ---------- fixtures ----------

def prepare_fixtures(repo: Path, refresh: bool = False) -> list[dict]:
    """Fetch each fixture source with its real fetcher into the cache (the live check)."""
    scripts = _scripts(repo)
    CACHE.mkdir(parents=True, exist_ok=True)
    report = []
    for sid, src in _suite()["sources"].items():
        cached, meta = CACHE / f"{sid}.md", CACHE / f"{sid}.json"
        if cached.is_file() and meta.is_file() and not refresh:
            report.append({"source": sid, "status": "cached", "bytes": cached.stat().st_size})
            continue
        vault = CACHE / "_fetch"
        shutil.rmtree(vault, ignore_errors=True)
        (vault / "fx" / "wiki").mkdir(parents=True)
        py = sys.executable
        cmd = {
            "page": [py, scripts / "wiki-update.py", "--topic", "fx", "--vault", vault,
                     "--source", src["url"], "--fetch-only"],
            "youtube": [py, scripts / "wiki-fetch-youtube.py", "--topic", "fx", "--vault", vault,
                        "--url", src["url"], "--ingested-by", "skilltest"],
            "pdf": [py, scripts / "wiki-fetch-pdf.py", "--topic", "fx", "--vault", vault,
                    "--source", src["url"], "--ingested-by", "skilltest"],
            "tweet": [shutil.which("node") or "node", scripts / "wiki-fetch-tweet.js", "--topic", "fx",
                      "--vault", vault, "--url", src["url"], "--ingested-by", "skilltest"],
        }[src["fetcher"]]
        try:
            p = subprocess.run([str(c) for c in cmd], capture_output=True, text=True, encoding="utf-8",
                               errors="replace", timeout=300, env={**os.environ, "PYTHONIOENCODING": "utf-8"})
            out, err, rc = p.stdout, p.stderr, p.returncode
        except subprocess.TimeoutExpired:
            out, err, rc = "", "timed out after 300 s", 1
        m = re.search(r"^raw_path=(.+)$", out, re.M)
        raw = Path(m.group(1).strip()) if m else None
        if rc == 0 and raw and raw.is_file() and raw.stat().st_size > 1024:
            shutil.copy2(raw, cached)
            meta.write_text(json.dumps({"url": src["url"], "fetcher": src["fetcher"], "raw_name": raw.name}),
                            encoding="utf-8")
            report.append({"source": sid, "status": "fetched", "bytes": cached.stat().st_size})
        else:
            report.append({"source": sid, "status": "FETCH FAILED", "detail": (err or out)[-300:]})
        shutil.rmtree(vault, ignore_errors=True)
    return report


# ---------- sandbox ----------

def setup(model: str, sandbox: Path, repo: Path) -> dict:
    sys.path.insert(0, str(_scripts(repo)))
    from _wiki_config import SCAFFOLD_TAXONOMY  # the folders a default /new-wiki creates

    if sandbox.exists():
        shutil.rmtree(sandbox)
    nb = sandbox / "notebooks" / NOTEBOOK
    shutil.copytree(HERE / "fixtures" / "seed-notebook", nb)
    for d in ["_inbox/proposed", "_inbox/pending", "_inbox/done", "_inbox/temp", "raw",
              *[f"wiki/{t}" for t in SCAFFOLD_TAXONOMY]]:
        (nb / d).mkdir(parents=True, exist_ok=True)
    fw = nb / "wiki" / "project" / "best-practices" / "framework"
    fw.mkdir(parents=True, exist_ok=True)
    for doc in (repo / "bootstrap" / "topic-template" / "wiki" / "best-practices" / "framework").glob("*.md"):
        shutil.copy2(doc, fw / doc.name)
    raw_names = {}
    for sid in _suite()["sources"]:
        meta = CACHE / f"{sid}.json"
        if meta.is_file():
            name = json.loads(meta.read_text(encoding="utf-8"))["raw_name"]
            shutil.copy2(CACHE / f"{sid}.md", nb / "raw" / name)
            raw_names[sid] = name
    shutil.copytree(HERE / "fixtures" / "inputs", sandbox / "inputs")

    registry = sandbox / "linked-notebooks.json"
    registry.write_text(json.dumps({"notebooks": {NOTEBOOK: {"root": f"notebooks/{NOTEBOOK}"}}}, indent=2),
                        encoding="utf-8")
    project = sandbox / "project"
    (project / ".claude").mkdir(parents=True)
    # The same config at the sandbox root too: a session that cd's into notebooks/
    # must still resolve the test registry. Without it the walk up reached this repo's
    # own .claude/wiki-config.json and the real registry, where `skilltest` does not
    # exist, and every search failed (Opus, xpost case, 2026-09-15).
    cfg = json.dumps({"tool": "claude-code", "project_name": "skilltest", "notebook": NOTEBOOK,
                      "registry": registry.as_posix()}, indent=2)
    (project / ".claude" / "wiki-config.json").write_text(cfg, encoding="utf-8")
    (sandbox / ".claude").mkdir(exist_ok=True)
    (sandbox / ".claude" / "wiki-config.json").write_text(cfg, encoding="utf-8")

    index = f"skilltest-{model}-{sandbox.parent.name}"  # one per run, so two runs never share an index
    _qmd_index_file(index).unlink(missing_ok=True)
    for args in (["collection", "add", str(nb / "wiki")], ["embed"]):
        subprocess.run([*_qmd(), "--index", index, *args], capture_output=True, text=True,
                       encoding="utf-8", errors="replace", timeout=600)
    return {"sandbox": sandbox, "project": project, "notebook": nb, "registry": registry,
            "skill_dir": sandbox / "skill" / "wiki-update", "index": index, "raw_names": raw_names,
            "scripts": _scripts(repo),
            "env": {"WIKI_QMD_INDEX": index, "WIKI_QMD_CALLER": f"skilltest-{model}-{sandbox.parent.name}", "PYTHONIOENCODING": "utf-8"}}


def teardown(ctx: dict) -> None:
    shutil.rmtree(ctx["sandbox"], ignore_errors=True)
    _qmd_index_file(ctx["index"]).unlink(missing_ok=True)


def snapshot(ctx: dict) -> dict:
    nb = ctx["notebook"]
    return {p.relative_to(nb).as_posix(): (p.stat().st_size, p.stat().st_mtime_ns)
            for p in nb.rglob("*") if p.is_file()}


# ---------- prompts ----------

HEADER = """You are running an automated test of the wiki-update skill. The skill under test is at {skill}/SKILL.md, with its reference files beside it. Read it and follow it exactly, as if the user had typed /wiki-update with the input below. Do not use any installed copy of the skill.

The notebook is `{notebook}`, this project's notebook, at {nb}. Write only inside {sandbox}. Run scripts as `python <path> ...` or `node <path> ...`, with no environment-variable prefix. The user started this run and will read your report, but cannot answer questions while it runs: where the skill says to confirm something with the user, make the reasonable choice and say what you chose.

"""


def prompt(case: dict, ctx: dict) -> str:
    head = HEADER.format(skill=ctx["skill_dir"].as_posix(), notebook=NOTEBOOK,
                         nb=ctx["notebook"].as_posix(), sandbox=ctx["sandbox"].as_posix())
    staged = " Use staged mode (--staged)." if case.get("mode") == "staged" else ""
    kind, inp = case["kind"], case.get("input")
    if kind == "redirect":
        return head + "The user typed /wiki-update with nothing after it."
    if kind == "queue":
        return head + "The user's input: " + " ".join(case["urls"])
    if kind == "dedup":
        return head + "The user's input: " + _suite()["sources"][case["source"]]["url"]
    if inp == "cached":
        url = _suite()["sources"][case["source"]]["url"]
        raw = ctx["raw_names"].get(case["source"], "<missing fixture>")
        return head + (f"The user handed over a source that was already fetched: its raw is "
                       f"{ctx['notebook'].as_posix()}/raw/{raw}, the saved original of {url}. "
                       f"File it with --source-url {url} --raw-path raw/{raw}.{staged}")
    if inp == "live":
        return head + f"The user's input: {case['url']}{staged}"
    if inp == "local-file":
        return head + f"The user's input: the local file {(ctx['sandbox'] / 'inputs' / case['file']).as_posix()}{staged}"
    if inp == "pasted":
        return head + f"The user pasted this text:{staged}\n\n{case['text']}"
    raise ValueError(f"unknown case shape: {case['id']}")


# ---------- checks ----------

def _is_entry(rel: str) -> bool:
    name = rel.rsplit("/", 1)[-1].lower()
    if not rel.endswith(".md") or name in MACHINE_FILES:
        return False
    if rel.startswith("_inbox/proposed/"):
        return True
    return rel.startswith("wiki/") and not rel.startswith("wiki/sessions/") and "/framework/" not in rel


def _norm_url(u) -> str:
    return str(u or "").strip().strip('"').strip("'").rstrip("/").lower().replace("://www.", "://")


def _related_links(body: str) -> list[str]:
    m = re.search(r"^##\s+Related[^\n]*\n(.*?)(?=^##\s|^---\s*$|^\*\*Source\*\*|\Z)", body, re.M | re.S)
    return re.findall(r"\]\(([^)#\s]+\.md)", m.group(1)) if m else []


SEARCH_LOG = Path(os.environ.get("WIKI_QMD_SLOT_DIR") or Path.home() / ".cache" / "wiki-qmd") / "searches.jsonl"


def _logged_searches(caller) -> list[dict]:
    """The search helper's log lines for one case (the runner tags each case's caller)."""
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


def _scores(text: str) -> dict:
    out = {}
    for key, pat in (("fidelity", r"fidelity[^0-9\n]{0,40}([1-5])"),
                     ("synthesis", r"synthesis value[^0-9\n]{0,40}([1-5])")):
        m = re.search(pat, text, re.I)
        out[key] = int(m.group(1)) if m else None
    return out


def check(case: dict, before: dict, after: dict, run: dict, ctx: dict) -> list[dict]:
    sys.path.insert(0, str(ctx["scripts"]))
    from _entry_checks import check_entry_file, split_frontmatter

    nb, res = ctx["notebook"], []

    def add(name, ok, detail=""):
        res.append({"name": name, "ok": bool(ok), "detail": str(detail)[:300]})

    r = run["result"]
    add("session completed", r.get("subtype") == "success" and not r.get("is_error"),
        r.get("subtype") or run.get("stderr_tail")
        or "no result event: the session never started as a stream-json run (check the claude command line)")
    denials = r.get("permission_denials") or []
    add("no permission denials", not denials, [d.get("tool_name") if isinstance(d, dict) else d for d in denials])

    new = sorted(set(after) - set(before))
    changed = sorted(k for k in before if k in after and before[k] != after[k])
    entries = [k for k in new if _is_entry(k)]
    text = run["text"].lower()
    kind = case["kind"]

    if kind == "redirect":
        add("nothing written", not new and not changed, new + changed)
        add("points the user to /wrap-up", "/wrap-up" in text)
        return res
    if kind == "queue":
        pending = [k for k in new if k.startswith("_inbox/pending/") and not k.rsplit("/", 1)[-1].startswith("_")]
        add("both URLs queued in _inbox/pending/", len(pending) == 2, pending)
        add("no entry filed", not entries, entries)
        add("points the user to /wiki-cycle", "/wiki-cycle" in text)
        return res
    if kind == "dedup":
        add("no new entry", not entries, entries)
        add("reports the duplicate", any(w in text for w in ("dedup", "already in the wiki", "already exists",
                                                               "duplicate", "already filed", "already ingested")))
        return res

    # ---- an ingest ----
    staged = case.get("mode") == "staged"
    where = "_inbox/proposed/" if staged else "wiki/"
    add(f"exactly one new entry, in {where}", len(entries) == 1 and entries[0].startswith(where), entries)
    bash = [str(c["input"].get("command", "")) for c in run["tool_calls"] if c["name"] == "Bash"]
    reads = [str(c["input"].get("file_path", "")) for c in run["tool_calls"] if c["name"] == "Read"]
    # Steps are checked by what they leave behind, not by parsing commands. Searches
    # come from the search helper's own log (one line per search, tagged with this
    # case's caller): counting Bash commands missed Opus's `for` loops, which run
    # several searches in one command (the 2026-09-15 rerun counted 1 where the log
    # shows 5). Filing is proven by the entry itself (step 8 below), staged or direct
    # by where it landed.
    ok_searches = [r for r in _logged_searches(run.get("caller")) if r.get("outcome") == "ok"]
    off_notebook = [r.get("query") for r in ok_searches if NOTEBOOK not in str(r.get("scope", ""))]
    add("step 3: searched the wiki 3+ times (helper log)", len(ok_searches) >= 3, f"{len(ok_searches)} searches")
    add("step 3: every search in this notebook", ok_searches and not off_notebook, off_notebook)
    sc = _scores(run["text"])
    add("step 5: printed both judgment scores", None not in sc.values(), sc)
    add("step 5: both scores 3 or more", all(v is not None and v >= 3 for v in sc.values()), sc)
    if len(entries) != 1:
        return res

    path = nb / entries[0]
    entry_text = path.read_text(encoding="utf-8")
    fm, body = split_frontmatter(entry_text)
    add("step 8: filed by wiki-update.py (its Source footer and frontmatter)",
        bool(fm.get("ingested_by")) and "**Source**" in entry_text)
    missing = [f for f in REQUIRED_FM if not fm.get(f)]
    add("frontmatter complete", not missing, missing)
    tier = str(fm.get("tier", "")).strip().strip('"')
    add(f"tier in {case['tier']}", tier in case["tier"], tier)
    add("confidence is high/medium/low", str(fm.get("confidence", "")).strip('"') in ("high", "medium", "low"),
        fm.get("confidence"))
    tags = fm.get("tags") or []
    for t in case.get("expect_tags", []):
        add(f"tagged {t}", t in tags, tags)

    inp = case.get("input")
    if inp == "cached":
        url = _suite()["sources"][case["source"]]["url"]
        raw = ctx["raw_names"].get(case["source"], "")
        add("source_url is the source", _norm_url(fm.get("source_url")) == _norm_url(url), fm.get("source_url"))
        add("raw_path names the handed-over raw", str(fm.get("raw_path", "")).strip('"').endswith(raw),
            fm.get("raw_path"))
        add("step 2: read the raw", any(raw in x for x in reads + bash))
    elif inp == "live":
        rp = str(fm.get("raw_path", "")).strip('"')
        add("source_url is the source", _norm_url(fm.get("source_url")) == _norm_url(case["url"]),
            fm.get("source_url"))
        add("raw captured and named in raw_path", bool(rp) and (nb / rp).is_file(), rp)

    g = check_entry_file(path)
    add("gate: no errors", not g.get("errors"), g.get("errors"))
    known = {p.name for p in (nb / "wiki").rglob("*.md")}
    links = _related_links(body)
    real = [l for l in links if l.rsplit("/", 1)[-1] in known and l.rsplit("/", 1)[-1] != path.name]
    add("Related: 2+ links to real entries", len(real) >= 2, f"{len(real)} of {len(links)} resolve")

    if staged:
        side = path.with_suffix(".proposed_metadata.json")
        add("sidecar written", side.is_file(), side.name)
        p = subprocess.run([sys.executable, str(ctx["scripts"] / "wiki-promote.py"), "--topic", NOTEBOOK,
                            "--check", "--slug", path.stem], cwd=ctx["project"], capture_output=True, text=True,
                           encoding="utf-8", errors="replace", env={**os.environ, **ctx["env"]})
        add("wiki-promote --check passes", p.returncode == 0, (p.stdout + p.stderr)[-200:])
    else:
        back = [k for k in changed if k.startswith("wiki/") and _is_entry(k)
                and path.name in (nb / k).read_text(encoding="utf-8", errors="replace")]
        add("steps 6-7: existing entries link back", bool(back), back)
    # only what THIS case left: the cases share one sandbox, and one case's leftover
    # must not fail the next (run 4 blamed two cases for the pasted-text case's file)
    leftover = [k for k in new if k.startswith("_inbox/temp/")]
    add("temp files cleaned up", not leftover, leftover)
    return res
