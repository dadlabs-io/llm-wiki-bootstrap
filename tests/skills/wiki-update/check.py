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
    return repo / "scripts"


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


# ---------- generated two-column PDF (written for the test; no binary is committed) ----------

PDF_QUOTE_START = "The team found that rewriting"
PDF_LEFT = [
    "Field notes on scratchpad memory in long-running agents",
    "Six agent teams took part in a spring trial of how an agent should keep its session notes while it "
    "works through a long task. Each team kept its usual model and its usual tools, and only the way the "
    "agent wrote and reread its scratchpad was changed.",
    "The team found that rewriting the scratchpad into a short summary after every tenth step, rather than "
    "appending to it after every step, cut the number of runs that repeated finished work by about a third "
    "across the six agent teams in the trial.",
    "Engineers on the smaller teams reported that the summary was easy to audit once the agent marked each "
    "line as done, open or dropped.",
]
PDF_RIGHT = [
    "Agents differ in how well they reread their own notes, and the trial recorded which lines of the "
    "scratchpad the agent actually used when it chose its next step.",
    "Notes written in the last few steps were reread most often by the agent, and moving older decisions "
    "into a long-term store that was searched on demand removed most of the clutter that the append-only "
    "scratchpad had built up.",
    "A second round of the trial is planned for the autumn, when the agents will work on longer tasks that "
    "span more than one session.",
]
PDF_LEFT_SENTENCE, PDF_RIGHT_SENTENCE = PDF_LEFT[2], PDF_RIGHT[1]


def _norm_ws(s: str) -> str:
    return re.sub(r"\s+", " ", s).strip()


def _pdf_text(s: str) -> str:
    return s.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def _write_two_column_pdf(path: Path) -> None:
    """A one-page, two-column PDF of the text above, drawn line by line at fixed x positions
    (left column x=72, right column x=320), so a layout-preserving extraction puts a row of
    each column on one output line."""
    import textwrap

    def column(paras: list[str], x: int) -> str:
        ops = [f"BT /F1 10 Tf 12 TL {x} 740 Td"]
        for para in paras:
            for line in textwrap.wrap(para, 38):
                ops.append(f"({_pdf_text(line)}) Tj T*")
            ops.append("T*")
        ops.append("ET")
        return "\n".join(ops)

    stream = (column(PDF_LEFT, 72) + "\n" + column(PDF_RIGHT, 320)).encode("ascii")
    objs = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 5 0 R "
        b"/Resources << /Font << /F1 4 0 R >> >> >>",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
        b"<< /Length %d >>\nstream\n" % len(stream) + stream + b"\nendstream",
    ]
    out = bytearray(b"%PDF-1.4\n")
    offsets = []
    for i, o in enumerate(objs, 1):
        offsets.append(len(out))
        out += b"%d 0 obj\n" % i + o + b"\nendobj\n"
    xref = len(out)
    out += b"xref\n0 %d\n" % (len(objs) + 1) + b"0000000000 65535 f \n"
    for off in offsets:
        out += b"%010d 00000 n \n" % off
    out += b"trailer\n<< /Size %d /Root 1 0 R >>\nstartxref\n%d\n%%%%EOF\n" % (len(objs) + 1, xref)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(bytes(out))


# staged-backlinks: entries that must NOT appear in suggested_backlinks, and the one that must
BACKLINK_DECOYS = [("conference-travel-checklist", "Conference travel checklist"),
                   ("auto-generated-glossary", "Auto-generated glossary"),
                   ("team-reading-list", "Reading list for new team members")]
BACKLINK_NEIGHBOUR = ("tool-output-handling", "Tool output handling")

# preview-ticket: the raw a paywalled page leaves behind, marked a preview by the page fetcher
PREVIEW_RAW_TEXT = """---
title: {title}
date: 2026-10-11
source_url: {url}
ingested_by: skilltest
paywall: "the page shows its first paragraphs only; the rest is for subscribers"
completeness: preview
---

# {title}

{teaser}

_Subscribe to keep reading._
"""
PREVIEW_SAID = re.compile(r"preview|paywall|partial|incomplete|teaser|truncat|not (the )?(full|whole|complete)|"
                          r"only (part|a (part|portion|fragment|piece|snippet)|the first)")


# ---------- prompts ----------

HEADER = """You are running an automated test of the wiki-update skill. The skill under test is at {skill}/SKILL.md, with its reference files beside it. Read it and follow it exactly, as if the user had typed /wiki-update with the input below. Do not use any installed copy of the skill.

The notebook is `{notebook}`, this project's notebook, at {nb}. Write only inside {sandbox}. Run scripts as the skill writes them (`uv run --project <scripts dir> python <path> ...` or `node <path> ...`), with no environment-variable prefix, from {sandbox} or a folder inside it, never from inside the scripts' own repository (its config would point them at the real notebooks). The user started this run and will read your report, but cannot answer questions while it runs: where the skill says to confirm something with the user, make the reasonable choice and say what you chose.

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
    if kind == "save-list":
        # Seed the notebook the question is asked in with three routed tickets in the intake bucket,
        # in the shapes wiki-list-add.py and wiki-triage.py route write: one marked in its frontmatter
        # (save_as_pdf), one marked only by a triage-log row (matched to it by the ticket's source URL),
        # one unmarked. The cases share a sandbox, so the pending and intake folders are emptied first
        # and an earlier case's tickets cannot join the list.
        nb = ctx["notebook"]
        for d in ("_inbox/pending", "_inbox/intake"):
            shutil.rmtree(nb / d, ignore_errors=True)
        (nb / "_inbox" / "pending").mkdir(parents=True, exist_ok=True)
        folder = nb / "_inbox" / "intake" / "main"
        folder.mkdir(parents=True, exist_ok=True)
        rows = []
        for t in case["tickets"]:
            mark = t.get("mark") or ""
            stamp = f"{t['created']}T09:00:00-04:00"
            lines = ["---"]
            if mark.startswith("frontmatter:"):
                lines.append(f"save_as_pdf: {mark.split(':', 1)[1]}")
            lines += [f"source: {t['url']}", "folder:", f"title: {t['title']}", "priority: 3",
                      f"added_at: {stamp}", "added_by: claude-code", "---", "",
                      f"# {t['title']}", "",
                      f"**Source**: <{t['url']}>", "",
                      f"_Queued by `claude-code` at {stamp}, priority 3._", "",
                      "_Awaiting processing. Will be moved to `_inbox/done/` when ingested._", ""]
            (folder / t["file"]).write_text("\n".join(lines), encoding="utf-8")
            if mark.startswith("log:"):
                rows.append(f"| {t['created']} | {t['url']} | main | "
                            f"save as PDF: {mark.split(':', 1)[1]} (a members-only thread) | nb |")
        log = ["# Triage log", "",
               "One row per call, newest last. `/wiki-triage` reads the recent rows as precedents; "
               "a correction by the user is a row like any other.", "",
               "| Date | Item | Folder | Reason | By |", "|---|---|---|---|---|", *rows, ""]
        (nb / "_inbox" / "intake" / "triage-log.md").write_text("\n".join(log), encoding="utf-8")
        return head + f'The user asks: "{case["question"]}"'
    if kind == "preview-ticket":
        # A raw the page fetcher marked a preview (a paywalled page) and an intake ticket whose raw_path
        # names it; the user says to file the ticket. Only this case's own two files are (re)written.
        nb = ctx["notebook"]
        raw = nb / "raw" / case["raw_file"]
        raw.parent.mkdir(parents=True, exist_ok=True)
        raw.write_text(PREVIEW_RAW_TEXT.format(title=case["title"], url=case["url"], teaser=case["teaser"]),
                       encoding="utf-8")
        folder = nb / "_inbox" / "intake" / "main"
        folder.mkdir(parents=True, exist_ok=True)
        stamp = "2026-10-11T09:00:00-04:00"
        ticket = folder / case["ticket_file"]
        ticket.write_text("\n".join([
            "---", f"source: {case['url']}", "folder:", f"title: {case['title']}", "priority: 3",
            f"added_at: {stamp}", "added_by: claude-code", f"raw_path: raw/{case['raw_file']}", "---", "",
            f"# {case['title']}", "", f"**Source**: <{case['url']}>", "",
            f"_Queued by `claude-code` at {stamp}, priority 3._", "",
            "_Awaiting processing. Will be moved to `_inbox/done/` when ingested._", ""]), encoding="utf-8")
        return head + f'The user says: "File this intake ticket: {ticket.as_posix()}"'
    if kind == "x-article-ticket":
        # The scenario is a page handed over directly that has no ticket yet. The cases share a sandbox, so
        # an earlier case may already have routed a ticket for this URL: remove only the tickets whose
        # source is this page, from pending and from every intake bucket (the triage log is left alone).
        nb = ctx["notebook"]
        for sub in ("_inbox/pending", "_inbox/intake"):
            root = nb / sub
            for p in sorted(root.rglob("*.md")) if root.is_dir() else []:
                if p.name == "triage-log.md":
                    continue
                t = p.read_text(encoding="utf-8", errors="replace")
                if re.search(r"^source:.*" + re.escape(case["status_id"]), t, re.M):
                    p.unlink()
        return head + f"The user's input: {case['url']}"
    if kind == "rubric-ingest":
        # seeded-raw: a raw already saved for a URL is handed over (the duplicate check is the first command on it).
        # local-file: a handed-over file the session fetches with --fetch-only. Only this case's raw is (re)written.
        if inp == "seeded-raw":
            raw = ctx["notebook"] / "raw" / case["raw_file"]
            raw.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(HERE / "fixtures" / "raws" / case["file"], raw)
            return head + (f"The user handed over a source that was already fetched: its raw is "
                           f"{raw.as_posix()}, the saved original of {case['url']}. "
                           f"File it with --source-url {case['url']} --raw-path raw/{case['raw_file']}.{staged}")
        return head + f"The user's input: the local file {(ctx['sandbox'] / 'inputs' / case['file']).as_posix()}{staged}"
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
    if inp == "generated-pdf":
        pdf = ctx["sandbox"] / "inputs" / case["file"]
        _write_two_column_pdf(pdf)
        return head + (f"The user's input: the local file {pdf.as_posix()}{staged} "
                       f"The user asks that the entry quote, word for word as a `>` blockquote, the sentence of "
                       f"the paper that begins \"{PDF_QUOTE_START}\".")
    raise ValueError(f"unknown case shape: {case['id']}")


# ---------- checks ----------

def _is_entry(rel: str) -> bool:
    name = rel.rsplit("/", 1)[-1].lower()
    if not rel.endswith(".md") or name in MACHINE_FILES:
        return False
    if rel.startswith("_inbox/proposed/"):
        return True
    return rel.startswith("wiki/") and not rel.startswith("wiki/sessions/")


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
    # the machine's global read-guard hook refusing a partial read is not harness friction:
    # the session recovers by reading the document whole (counted apart, as in wrap-up and wiki-cycle)
    errs = run.get("error_texts") or {}
    denials = [d for d in (r.get("permission_denials") or [])
               if not (isinstance(d, dict) and "read-guard:" in str(errs.get(d.get("tool_use_id"), "")))]
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

    if kind == "pdf-columns":
        add("exactly one new entry, in _inbox/proposed/",
            len(entries) == 1 and entries[0].startswith("_inbox/proposed/"), entries)
        if len(entries) != 1:
            return res
        path = nb / entries[0]
        entry_text = path.read_text(encoding="utf-8")
        fm, body = split_frontmatter(entry_text)
        add("filed by wiki-update.py (its Source footer and frontmatter)",
            bool(fm.get("ingested_by")) and "**Source**" in entry_text)
        rp = str(fm.get("raw_path", "")).strip().strip('"').strip("'")
        raw_file = nb / rp if rp else None
        raw_ok = bool(raw_file) and raw_file.is_file()
        add("raw captured and named in raw_path", raw_ok, rp)
        raw_text = raw_file.read_text(encoding="utf-8", errors="replace") if raw_ok else ""
        raw_n = _norm_ws(raw_text)
        # requirement 1: a sentence running over several lines of one column is whole in the raw
        add("raw holds the left-column multi-line sentence whole", _norm_ws(PDF_LEFT_SENTENCE) in raw_n,
            PDF_LEFT_SENTENCE[:60])
        add("raw holds the right-column multi-line sentence whole", _norm_ws(PDF_RIGHT_SENTENCE) in raw_n,
            PDF_RIGHT_SENTENCE[:60])
        # ... and it got there without hand edits to the raw
        bash_cmds = [str(c["input"].get("command", "")) for c in run["tool_calls"] if c["name"] == "Bash"]
        hand = [str(c["input"].get("file_path", "")) for c in run["tool_calls"]
                if c["name"] in ("Write", "Edit", "NotebookEdit")
                and "/raw/" in str(c["input"].get("file_path", "")).replace("\\", "/")]
        hand += [b[:120] for b in bash_cmds
                 if re.search(r">>?\s*\S*raw/|sed\s+-i[^|;&\n]*raw/|tee\s[^|;&\n]*raw/", b)]
        add("raw not edited by hand", not hand, hand)
        # the quote: a `>` blockquote that holds the whole sentence word for word
        quoted = _norm_ws(" ".join(re.sub(r"^\s*(?:>\s*)+", "", ln) for ln in body.splitlines()
                                   if ln.lstrip().startswith(">")))
        add("entry quotes the whole multi-line sentence in a > blockquote",
            _norm_ws(PDF_LEFT_SENTENCE) in quoted, quoted[:120])
        g = check_entry_file(path)
        add("gate: no errors", not g.get("errors"), g.get("errors"))
        side = path.with_suffix(".proposed_metadata.json")
        add("sidecar written", side.is_file(), side.name)
        return res
    if kind == "staged-backlinks":
        add("exactly one new entry, in _inbox/proposed/",
            len(entries) == 1 and entries[0].startswith("_inbox/proposed/"), entries)
        if len(entries) != 1:
            return res
        path = nb / entries[0]
        fm, _body = split_frontmatter(path.read_text(encoding="utf-8"))
        tags = [str(t).strip().lower() for t in (fm.get("tags") or [])]
        need = ["needs-source-check", "stub", "2026", NOTEBOOK]
        add("premise: the entry carries the bookkeeping tags and the notebook tag the user asked for",
            all(t in tags for t in need), tags)
        side = path.with_suffix(".proposed_metadata.json")
        add("sidecar written", side.is_file(), side.name)
        try:
            data = json.loads(side.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            data = {}
        sb = data.get("suggested_backlinks") if isinstance(data, dict) else None
        add("sidecar has a suggested_backlinks list", isinstance(sb, list), type(sb).__name__)
        named = [json.dumps(i, ensure_ascii=False).lower() for i in (sb or [])]

        def hit(stem: str, title: str) -> list[str]:
            return [n for n in named if stem in n or title.lower() in n]

        # requirement 2: no entry whose only link to the new one is a bookkeeping tag, the notebook
        # tag, or a match inside its own frontmatter
        for stem, title in BACKLINK_DECOYS:
            add(f"not suggested: {stem}", not hit(stem, title), hit(stem, title))
        stem, title = BACKLINK_NEIGHBOUR
        add(f"still suggested: {stem} (shares real topic tags, mentions the subject in its body)",
            bool(hit(stem, title)), named)
        return res
    if kind == "x-article":
        # An X Article is a page no fetcher can get (fetchers.md): read the preview, delete that raw,
        # ask the user to save the page as PDF, never file an entry from the preview alone.
        # Every check here judges what the session left behind and said, so it is meaningful against
        # the skill before and after the change.
        add("no entry filed, staged or live (never from the preview alone)", not entries, entries)
        leftover = [k for k in new if k.startswith(("raw/", "_inbox/proposed/", "wiki/"))]
        add("nothing new left in raw/, wiki/ or _inbox/proposed/ (preview raw deleted; no page copied in)",
            not leftover, leftover)
        touched = [k for k in changed if k.startswith("wiki/") and _is_entry(k)]
        add("no existing entry edited", not touched, touched)
        say = text.replace("\\", "/")
        add("reply asks the user to save the page as PDF",
            bool(re.search(r"(save|export|print)\w*\b[^\n]{0,60}\bpdf\b|\bpdf\b[^\n]{0,60}(save|export)", say)))
        add("reply tells the user which page (status id or title)",
            case["status_id"] in say or case["title"].lower() in say)
        sb = ctx["sandbox"].as_posix().lower()
        alts = [sb] + (["/" + sb[0] + sb[2:]] if sb[1:3] == ":/" else [])
        add("reply names a full folder path inside the sandbox to save it to (path, see question 1)",
            any(a in say for a in alts))
        banned = ("archive.org", "archive.ph", "archive.is", "archive.today", "webcache.googleusercontent",
                  "r.jina.ai", "12ft.io", "wayback")
        used = sorted({b for c in run["tool_calls"] for b in banned if b in json.dumps(c.get("input", "")).lower()})
        add("no archive, cache or proxy route tried", not used, used)
        return res
    if kind == "x-post-photo":
        # An ordinary X post is still filed as before (staged). The photo check is meaningful only for
        # the new fetcher: the old one did not link photos at original size.
        add("exactly one new entry, in _inbox/proposed/",
            len(entries) == 1 and entries[0].startswith("_inbox/proposed/"), entries)
        if len(entries) != 1:
            return res
        path = nb / entries[0]
        entry_text = path.read_text(encoding="utf-8")
        fm, body = split_frontmatter(entry_text)
        add("filed by wiki-update.py (its Source footer and frontmatter)",
            bool(fm.get("ingested_by")) and "**Source**" in entry_text)
        missing = [f for f in REQUIRED_FM if not fm.get(f)]
        add("frontmatter complete", not missing, missing)
        add("source_url is the post", case["status_id"] in str(fm.get("source_url", "")), fm.get("source_url"))
        rp = str(fm.get("raw_path", "")).strip().strip('"').strip("'")
        raw_ok = bool(rp) and (nb / rp).is_file()
        add("raw captured and named in raw_path", raw_ok, rp)
        raw_text = (nb / rp).read_text(encoding="utf-8", errors="replace") if raw_ok else ""
        add("entry is about the post's subject", case["subject"] in entry_text.lower(), case["subject"])
        urls = re.findall(r"https://pbs\.twimg\.com/media/[^\s)\]\"'<>]+", raw_text)
        add("raw links its photo at original size, name=orig (new fetcher only)",
            bool(urls) and all("name=orig" in u for u in urls), urls[:3])
        g = check_entry_file(path)
        add("gate: no errors", not g.get("errors"), g.get("errors"))
        side = path.with_suffix(".proposed_metadata.json")
        add("sidecar written", side.is_file(), side.name)
        return res
    if kind == "x-article-ticket":
        # A page the user hands over that no fetcher can get gets a ticket on the save-as-PDF list:
        # no entry, no raw, the ticket in the intake bucket marked, the user told. These checks judge
        # what the session left behind and said; they hold against the skill before and after the change.
        sid = case["status_id"]
        add("no entry filed, staged or live (never from the preview alone)", not entries, entries)
        raws = [k for k in new if k.startswith("raw/")]
        add("no raw left in raw/ (preview deleted; no page copied in)", not raws, raws)
        found = []
        for sub in ("_inbox/intake", "_inbox/pending"):
            for p in sorted((nb / sub).rglob("*.md")) if (nb / sub).is_dir() else []:
                try:
                    tfm, _tb = split_frontmatter(p.read_text(encoding="utf-8", errors="replace"))
                except Exception:
                    continue
                if isinstance(tfm, dict) and sid in str(tfm.get("source") or tfm.get("source_url") or ""):
                    found.append((p.relative_to(nb).as_posix(), tfm))
        in_main = [f for f in found if f[0].startswith("_inbox/intake/main/")]
        add("a ticket for the page waits in _inbox/intake/main/", bool(in_main), [f[0] for f in found])
        add("no copy of the ticket left anywhere else (pending or another bucket)",
            len(found) == len(in_main), [f[0] for f in found])
        if in_main:
            tfm = in_main[0][1]
            why = str(tfm.get("save_as_pdf") or "").strip().strip('"').strip("'").lower()
            add("ticket marked save_as_pdf: paywall, login or blocked", why in ("paywall", "login", "blocked"), why)
            add("ticket has no raw_path (the page stays on the list)", not tfm.get("raw_path"), tfm.get("raw_path"))
        logrel = "_inbox/intake/triage-log.md"
        logtxt = (nb / logrel).read_text(encoding="utf-8", errors="replace").lower() if (nb / logrel).is_file() else ""
        add("triage log gained a 'save as PDF: <why>' row in this run",
            (logrel in new or logrel in changed) and bool(re.search(r"save as pdf: (paywall|login|blocked)", logtxt)),
            logrel)
        say = text.replace("\\", "/")
        add("reply asks the user to save the page as PDF",
            bool(re.search(r"(save|export|print)\w*\b[^\n]{0,60}\bpdf\b|\bpdf\b[^\n]{0,60}(save|export)", say)))
        add("reply tells the user which page (status id or title)",
            sid in say or case["title"].lower() in say)
        sb = (nb / "_inbox" / "intake" / "main").as_posix().lower()
        alts = [sb] + (["/" + sb[0] + sb[2:]] if sb[1:3] == ":/" else [])
        add("reply names the intake folder as a full path (<notebook>/_inbox/intake/main)",
            any(a in say for a in alts), alts[0])
        banned = ("archive.org", "archive.ph", "archive.is", "archive.today", "webcache.googleusercontent",
                  "r.jina.ai", "12ft.io", "wayback")
        used = sorted({b for c in run["tool_calls"] for b in banned if b in json.dumps(c.get("input", "")).lower()})
        add("no archive, cache or proxy route tried", not used, used)
        return res
    if kind == "save-list":
        # The question "what pages do I need to save as PDF?" is answered from the list: the two marked
        # pages with their links and the folder, the unmarked ticket not offered as a page to save,
        # nothing filed or moved.
        folder = nb / "_inbox" / "intake" / "main"
        seeded = {f"_inbox/intake/main/{t['file']}" for t in case["tickets"]} | {"_inbox/intake/triage-log.md"}
        stray = [k for k in new if k not in seeded and not k.startswith("_inbox/temp/")]
        add("nothing filed, fetched or queued (no new file beyond the seeded tickets)", not stray, stray)
        moved = []
        for t in case["tickets"]:
            p = folder / t["file"]
            if not p.is_file():
                moved.append(f"{t['file']}: gone from _inbox/intake/main/")
                continue
            tfm, _tb = split_frontmatter(p.read_text(encoding="utf-8", errors="replace"))
            mark = t.get("mark") or ""
            want = mark.split(":", 1)[1] if mark.startswith("frontmatter:") else ""
            got = str(tfm.get("save_as_pdf") or "").strip().strip('"').strip("'")
            if got != want or tfm.get("raw_path") or t["url"] not in str(tfm.get("source") or ""):
                moved.append(f"{t['file']}: save_as_pdf={got!r} raw_path={tfm.get('raw_path')!r}")
        add("all three tickets still in _inbox/intake/main/, marks and sources as seeded", not moved, moved)
        say = text.replace("\\", "/")
        lines = say.split("\n")
        negated = re.compile(r"\b(not|isn'?t|aren'?t|no|without|excluded?|left out|omit\w*|skip\w*|"
                             r"unmarked|ordinary|other)\b")
        for t in case["tickets"]:
            if t.get("mark"):
                add(f"reply lists the page: {t['title']} (its link)", t["url"].lower() in say, t["url"])
            else:
                # named only to say it is not on the list is allowed; offered as a page to save is not
                offered = []
                for i, ln in enumerate(lines):
                    if t["url"].lower() in ln or t["title"].lower() in ln:
                        near = (lines[i - 1] + " " if i else "") + ln
                        if not negated.search(near):
                            offered.append(ln.strip()[:120])
                add(f"reply does not offer the unmarked page as one to save: {t['title']}", not offered, offered)
        sb = folder.as_posix().lower()
        alts = [sb] + (["/" + sb[0] + sb[2:]] if sb[1:3] == ":/" else [])
        add("reply gives the folder to save into as a full path (<notebook>/_inbox/intake/main)",
            any(a in say for a in alts), alts[0])
        return res
    if kind == "preview-ticket":
        # A raw marked completeness: preview must never be filed as the whole source, and the agent never
        # passes --partial-source on its own judgement (only on the user's word, which this user did not give).
        # The seeded raw and ticket are new files in this case's snapshot diff, so they are excluded.
        seeded = {f"raw/{case['raw_file']}", f"_inbox/intake/main/{case['ticket_file']}"}
        filed = [k for k in new if k not in seeded and k.startswith(("wiki/", "_inbox/proposed/"))]
        add("no entry filed, staged or live (the raw holds only a preview)", not filed, filed)
        done = [k for k in new if k.startswith("_inbox/done/")]
        add("ticket not moved to _inbox/done/ (nothing was filed)", not done, done)
        bash = [str(c["input"].get("command", "")) for c in run["tool_calls"] if c["name"] == "Bash"]
        forced = [b[:160] for b in bash if re.search(r"(?s)wiki-update\.py.*?--partial-source", b)]
        add("--partial-source not passed on the agent's own judgement", not forced, forced)
        raw = nb / "raw" / case["raw_file"]
        marked = raw.is_file() and re.search(r"^completeness:\s*[\"']?(preview|summary)",
                                             raw.read_text(encoding="utf-8", errors="replace"), re.M)
        add("raw not edited to drop its preview mark (a deleted raw is allowed)", (not raw.is_file()) or bool(marked),
            raw.name)
        add("reply says the raw holds only a preview", bool(PREVIEW_SAID.search(text)))
        add("reply names the page (title or link)", case["title"].lower() in text or case["url"].lower() in text)
        return res
    if kind == "rubric-ingest":
        # Requirement (task #99): tier and confidence follow the tier rubric and confidence scale. Posts are
        # tiered by author and evidence, not by platform; an arXiv paper is tier 1, reviewed or not.
        # Checked on what the entry carries; the run rule checks that the rubric was in front of the session.
        where = "_inbox/proposed/" if case.get("mode") == "staged" else "wiki/"
        add(f"exactly one new entry, in {where}", len(entries) == 1 and entries[0].startswith(where), entries)
        if len(entries) != 1:
            return res
        path = nb / entries[0]
        entry_text = path.read_text(encoding="utf-8")
        fm, _body = split_frontmatter(entry_text)
        add("filed by wiki-update.py (its Source footer and frontmatter)",
            bool(fm.get("ingested_by")) and "**Source**" in entry_text)
        tier = str(fm.get("tier", "")).strip().strip('"').strip("'")
        add(f"tier is {case['tier']}", tier in case["tier"], tier)
        conf = str(fm.get("confidence", "")).strip().strip('"').strip("'").lower()
        add(f"confidence is one of {case['confidence']}", conf in case["confidence"], conf)
        if case.get("input") == "seeded-raw":
            add("source_url is the handed-over source", _norm_url(fm.get("source_url")) == _norm_url(case["url"]),
                fm.get("source_url"))
            add("raw_path names the handed-over raw",
                str(fm.get("raw_path", "")).strip().strip('"').strip("'").endswith(case["raw_file"]), fm.get("raw_path"))
        g = check_entry_file(path)
        add("gate: no errors", not g.get("errors"), g.get("errors"))
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
    # task #81 P3: a -k cut is the same breach as head (cycle 2026-10-05-04: workers ran -k 6)
    cut = [(r.get("query"), r.get("k")) for r in ok_searches if int(r.get("k") or 0) < 30]
    add("step 3: no search cut below k=30", ok_searches and not cut, cut)
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
        if case.get("fetcher"):  # the routing in fetchers.md: which script this host goes to
            add(f"step 1: fetched with {case['fetcher']}", any(case["fetcher"] in b for b in bash))
            add("step 1: no Docker", not any("docker" in b for b in bash))
            raw_text = (nb / rp).read_text(encoding="utf-8", errors="replace") if rp and (nb / rp).is_file() else ""
            if case.get("raw_has"):
                add(f"raw holds its {case['raw_has']} section", case["raw_has"] in raw_text, rp)
            if case.get("read_unrecognised_slides"):
                # fetchers.md, Instagram: read the image wherever Instagram recognised no text
                blind = re.findall(r"\(Instagram recognised no text[^\n]*\n\s*\nImage: \[[^\]]*?([^/\]]+\.jpg)\]",
                                   raw_text)
                unread = [img for img in blind if not any(x.replace("\\", "/").endswith(img) for x in reads)]
                add("read every slide image Instagram did not recognise", blind and not unread,
                    f"{len(blind)} unrecognised; unread {unread}")
            for word in case.get("misheard", []):
                # fetchers.md, YouTube (the same check for any transcript): no mis-heard term inside a quote. The
                # transcription note the rule asks for names the mishearing, often as a `>` callout: not a quote
                # (Opus, run 20261005-154329)
                quoted = [ln for ln in body.splitlines() if ln.lstrip().startswith(">") and word in ln.lower()
                          and "transcri" not in ln.lower()]
                add(f"no quote carries the mis-heard '{word}'", not quoted, quoted[:2])

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
