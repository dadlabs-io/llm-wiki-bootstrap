#!/usr/bin/env python3
"""
wiki-qmd-query.py — run qmd's full search (`qmd query`) safely from many
processes at once, scoped to the notebook, and log how long each search waited
and ran.

Why (tested 2026-09-13 on an 8 GB RTX 4070 Laptop GPU): each `qmd query`
process loads its models onto the GPU. On qmd 2.1.0 two concurrent searches
fit and a third failed fast with "Failed to create any rerank context"; qmd
2.8.3 sizes its embedding pool from the weight file, and three fit (peak
7.7 of 8.2 GB, three runs, 2026-09-14) — so the default is three slots, and
--preflight warns on a qmd older than 2.8.3. The user's decision on 2026-09-13: every search is the FULL search, never a keyword
downgrade — when the GPU is full, searches wait their turn, and if that makes
batches too slow, run fewer workers.

A machine with no GPU (task #63, 2026-10-02): the models fall back to the CPU and
take every core — one full search on the CPU used ~9,900 CPU-seconds and hung the
laptop without finishing. So each machine has a search mode in
~/.claude/wiki-config.json (`search_mode`): `full`, the GPU search above, or
`keyword`, where this helper runs qmd's keyword index (`qmd search`, no model) with
the same scoping and filtering, and never `qmd query`, `vsearch` or `embed`.

The word-pair keyword search (task #64): qmd's keyword index returns only entries
holding every word, so a long query loses its best entries to one rare word. Every
machine therefore searches the query's key words together and in every pair (up to
8 key words: 29 tiny searches, run in parallel) and fuses them by rank. A keyword
machine shows that list's top k. A full machine shows the full search's own top k
first, then up to --keyword-extra (default 20) entries only the keyword search found,
under a heading in text output and as `"found_by": "keyword"` in JSON (every full
result there carries `"found_by": "full"`); they are never reranked or mixed into the
full search's order. On 8 real queries the word-pair search found 57 of the full
search's top 10 in its top 30 (the query as typed: 25), and 34 of its own top-10
entries were ones the full search never returned. The installer sets the mode from the GPU check (CUDA, or Metal
on a Mac; Vulkan is the backend that hung) and never switches a machine on its own;
`--set-mode full` switches once a GPU is there and refuses while the check fails.
Keyword mode is a setting, not a fallback: on a `full` machine a GPU failure is
still a stop-and-report.

Depth, named for what it is:
  -k  results returned after reranking (default 30; qmd's own flag is -n).
      Measured 2026-09-22 (tests/search/rank-usefulness.py, 18 real queries judged
      blind): ranks 21-30 are as dense in useful entries as 11-20 (33% vs 31%), and
      in 3 of 18 queries the single BEST entry sat at rank 27-29. Ranks 31-40 are
      thinner (25%) and never held the best entry, so 30, not 40. Costs no GPU time
      (the reranker has already scored every candidate) - about 180 tokens a result
      in the reading session, so 20 -> 30 is ~1,800 tokens.
  -C  the most candidates the reranker may score (default 120). It is a ceiling,
      not a depth: qmd fetches every keyword and vector list with a hard-coded
      20 (store.js hybridQuery), fuses them, and reranks one chunk per fused
      document, so the pool is at most 20 x the number of lists (5 when the
      query expands: about 100). Measured 2026-09-23 with -C 500: 77 candidates
      in agentic-design (1,211 files), 36 in agent-builder, 39 in llm-wiki. The
      8%-of-files sizing used until then (40-200) never bound, and its floor of
      40 was the only part that ever cut. 120 sits above every measured pool, so
      it changes nothing today and cannot start cutting as a notebook grows
      unless the lists themselves grow. Every search logs qmd's own count of
      candidates reranked; --stats and --depth-check report it against C.

What it does:
  - searches the current project's notebook by default (from the nearest
    .claude/wiki-config.json); --notebook <name> picks another,
    --all-notebooks searches every indexed one
  - holds one of N GPU slots (default 3) for the whole search — an OS file
    lock released when the process ends; a caller with no free slot waits
  - runs `qmd query` under a timeout that kills the whole process tree
  - GPU full or a transient CUDA fault: back off and retry; after the last
    retry exit 75 — stop and report; NEVER a fallback to `qmd search`
  - drops the machine files (_MAP.md, _INDEX.md) from text and --json results;
    they are orientation pages, never a link target
  - logs one JSON line per call to <slot-dir>/searches.jsonl, including how many
    candidates qmd reranked; --stats sums it
  - --depth-check: searches sampled entry titles from a notebook and reports how
    many candidates qmd reranked against C. Exit 1 when any search reached C (C
    may have cut the pool: raise it); exit 2 when no search could be measured.
    (Until 2026-09-23 it compared C with 2C, which always reported "0 missed"
    because neither ever bound.)

Usage:
  python wiki-qmd-query.py "tiered context loading"          # this project's notebook
  python wiki-qmd-query.py --notebook agentic-design "term"  # one notebook
  python wiki-qmd-query.py --all-notebooks "term"            # every notebook
  python wiki-qmd-query.py "term" -k 40 -C 200               # explicit depth
  python wiki-qmd-query.py --preflight                       # the machine's mode; on full, the GPU check + qmd version
  python wiki-qmd-query.py --set-mode full                   # switch this machine (full needs the GPU check to pass)
  python wiki-qmd-query.py --stats                           # wait/run summary
  python wiki-qmd-query.py --depth-check --notebook agentic-design

Exit codes: qmd's own code on a completed search (0 = ok); 2 = preflight
failed or usage error; 75 = GPU busy after every retry; 124 = timed out.
--depth-check: 0 = C never reached, 1 = C reached, 2 = nothing measured (always,
on a keyword machine: there is no reranker).

Environment: WIKI_QMD_K, WIKI_QMD_C (other values instead of the defaults),
WIKI_QMD_SLOTS (default 3; 2 on a qmd older than 2.8.3), WIKI_QMD_SLOT_DIR (default ~/.cache/wiki-qmd),
WIKI_QMD_BIN (the qmd executable; default: node + qmd's dist/cli/qmd.js),
WIKI_QMD_INDEX (a named qmd index; default: qmd's own default index),
WIKI_SEARCH_MODE (full | keyword, instead of the machine's setting).
"""

from __future__ import annotations

import argparse
import itertools
import json
import os
import re
import shutil
import statistics
import subprocess
import sys
import time
from pathlib import Path
from typing import NamedTuple

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _wiki_config import load_config, now_stamp, wiki_dir, search_mode, set_search_mode  # noqa: E402
from _entry_checks import split_frontmatter, is_superseded  # noqa: E402

DEFAULT_K = int(os.environ.get("WIKI_QMD_K", "30"))
DEFAULT_C = int(os.environ.get("WIKI_QMD_C", "120"))
RERANKED_RE = re.compile(r"Reranking (\d+) chunks")  # qmd's stderr progress line: one chunk per candidate
ANSI_RE = re.compile(r"\x1b\[[0-9;]*m")
MACHINE_FILES = {"_map.md", "map.md", "_index.md", "index.md"}  # qmd shows _MAP.md as map.md
EXTRA_FOR_FILTER = 15  # ask qmd for more so dropped machine files do not shorten k (an INDEX-heavy
                       # query in agentic-design dropped 11 on 2026-09-13; k itself costs no GPU time)

# GPU trouble worth a back-off and retry (never a keyword fallback): the GPU is full, or a
# transient CUDA fault — seen 2026-09-13 as "ggml-cuda.cu:98: CUDA error" on a search after the
# GPU had been idle; the retry 10 s later succeeded.
GPU_FULL_MARKERS = (
    "Failed to create any rerank context",
    "Failed to create context",
    "ErrorOutOfDeviceMemory",
    "out of memory",
    "cudaMalloc",
    "CUDA error",
)
EXIT_USAGE, EXIT_GPU_BUSY, EXIT_TIMEOUT = 2, 75, 124
QMD_MIN_VERSION = (2, 8, 3)  # the three-slot default assumes 2.8.3's embed-pool sizing (qmd #799)
# The GPU backends a full search may run on. Vulkan is not one: on 2026-09-12 qmd's token generation
# hung under it at 100% CPU on every core (the laptop's CUDA runtime was missing).
GPU_BACKENDS = ("CUDA", "Metal")
GPU_CHECK_TIMEOUT = 60  # seconds; node-llama-cpp's inspect lists backends and loads no model

# The word-pair keyword search (task #64, 2026-10-02). qmd's keyword index returns only entries that
# hold EVERY word of a search, so one rare word in a long query drops the best entries ("Microsoft Agent
# Framework agent and workflow channels" matched 19 files, none of them the Microsoft Agent Framework
# entries, which lack "channels"). Searching the key words together and in every pair, fused by
# reciprocal rank, found 57 of the full search's top 10 in its top 30 on 8 real queries, against 25 for
# the query as typed, and as many as qmd's keyword + vector search without the reranker (58). It also
# found entries the full search never returns (34 of its top-10 entries were outside the full search's
# 30), so a full machine shows up to KEYWORD_EXTRA of those after its own results.
KEYWORD_MAX_TERMS = 8        # 8 key words = the whole + 28 pairs, run in parallel
KEYWORD_PER_LIST = 20        # results per keyword search, as qmd fetches per list
KEYWORD_EXTRA = int(os.environ.get("WIKI_QMD_KEYWORD_EXTRA", "20"))
KEYWORD_WORKERS = 8
STOPWORDS = {"a", "an", "and", "the", "of", "for", "to", "in", "on", "over", "vs", "with", "from", "by", "or",
             "not", "is", "are", "how", "what", "which", "do", "does", "at", "as", "about", "into"}
# qmd options that take a value; the rest of the passed-through arguments are the query's words
VALUE_OPTIONS = {"-c", "--collection", "--min-score", "-n", "--index", "--format", "-C", "--candidate-limit"}
FORMAT_FLAGS = {"--json", "--files", "--csv", "--md", "--xml", "--full", "--explain", "--line-numbers"}


def slot_dir() -> Path:
    d = Path(os.environ.get("WIKI_QMD_SLOT_DIR") or Path.home() / ".cache" / "wiki-qmd")
    d.mkdir(parents=True, exist_ok=True)
    return d


class Slot:
    """One of N exclusive GPU slots, held as an OS lock on a small file.
    The OS drops the lock when the handle closes or the process dies."""

    def __init__(self, path: Path):
        self.path = path
        self.fh = None

    def try_acquire(self) -> bool:
        fh = open(self.path, "a+b")
        try:
            if os.name == "nt":
                import msvcrt
                fh.seek(0)
                msvcrt.locking(fh.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl
                fcntl.flock(fh.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError:
            fh.close()
            return False
        self.fh = fh
        return True

    def release(self) -> None:
        if self.fh is None:
            return
        try:
            if os.name == "nt":
                import msvcrt
                self.fh.seek(0)
                msvcrt.locking(self.fh.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                import fcntl
                fcntl.flock(self.fh.fileno(), fcntl.LOCK_UN)
        finally:
            self.fh.close()
            self.fh = None


def acquire_slot(n_slots: int, max_wait: float) -> tuple[Slot | None, float]:
    """Wait for any free slot; returns (slot, seconds waited) or (None, waited)."""
    d = slot_dir()
    start = time.monotonic()
    announced = False
    while True:
        for i in range(1, n_slots + 1):
            slot = Slot(d / f"slot-{i}.lock")
            if slot.try_acquire():
                return slot, time.monotonic() - start
        waited = time.monotonic() - start
        if waited >= max_wait:
            return None, waited
        if not announced:
            print(f"[wiki-qmd-query] all {n_slots} GPU slots busy — waiting for one", file=sys.stderr)
            announced = True
        time.sleep(1.0)


def kill_tree(proc: subprocess.Popen) -> None:
    if os.name == "nt":
        subprocess.run(["taskkill", "/T", "/F", "/PID", str(proc.pid)],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    else:
        import signal
        try:
            os.killpg(proc.pid, signal.SIGKILL)
        except OSError:
            proc.kill()
    try:
        proc.wait(timeout=10)
    except subprocess.TimeoutExpired:
        pass


def qmd_cmd() -> list[str]:
    """The command that starts qmd. npm's Windows shim (qmd.CMD) hands off to
    /bin/sh, which exists only inside Git Bash, so launched from Python it fails
    with "The system cannot find the path specified". qmd's own bin/qmd script
    just runs `node <pkg>/dist/cli/qmd.js`; do that directly when the package is
    found next to the shim, which also keeps the process tree one level deep.
    $WIKI_QMD_INDEX selects a named qmd index (qmd's --index); the skill test
    baseline (tests/skills/) keeps its sandbox notebook in its own index."""
    index = os.environ.get("WIKI_QMD_INDEX")
    extra = ["--index", index] if index else []
    override = os.environ.get("WIKI_QMD_BIN")
    if override:
        return [override, *extra]
    shim = shutil.which("qmd")
    if not shim:
        print("[wiki-qmd-query] qmd not found on PATH (npm i -g @tobilu/qmd)", file=sys.stderr)
        sys.exit(EXIT_USAGE)
    entry = Path(shim).resolve().parent / "node_modules" / "@tobilu" / "qmd" / "dist" / "cli" / "qmd.js"
    node = shutil.which("node")
    if entry.exists() and node:
        return [node, str(entry), *extra]
    return [shim, *extra]


def run_qmd(argv: list[str], timeout: float) -> tuple[int | None, str, str]:
    """Run qmd; returns (returncode or None on timeout, stdout, stderr)."""
    kwargs = {"stdout": subprocess.PIPE, "stderr": subprocess.PIPE,
              "text": True, "encoding": "utf-8", "errors": "replace"}
    if os.name != "nt":
        kwargs["start_new_session"] = True
    proc = subprocess.Popen([*qmd_cmd(), *argv], **kwargs)
    try:
        out, err = proc.communicate(timeout=timeout)
        return proc.returncode, out, err
    except subprocess.TimeoutExpired:
        kill_tree(proc)
        return None, "", ""


REINDEX_TIMEOUT = float(os.environ.get("WIKI_QMD_REINDEX_TIMEOUT", "3600"))


def reindex(mode: str, n_slots: int, max_wait: float) -> int:
    """Bring qmd's index up to date: `qmd update` (new and changed files), then on a full
    machine `qmd embed` (vectors for the new chunks) while holding every GPU slot, so no
    search loads a model beside it. A keyword machine never embeds. Run by wiki-promote.py
    after each promotion and by /wiki-cycle before its workers search (task #81 P1: no
    step did, and cycle 2026-10-05-02's workers searched an index 12 days stale)."""
    rc, out, err = run_qmd(["update"], REINDEX_TIMEOUT)
    if rc is None:
        print(f"[wiki-qmd-query] reindex: qmd update timed out after {REINDEX_TIMEOUT:.0f}s", file=sys.stderr)
        return EXIT_TIMEOUT
    if rc != 0:
        print(f"[wiki-qmd-query] reindex: qmd update failed (exit {rc}): {(err or out).strip()[-300:]}",
              file=sys.stderr)
        return 1
    if mode == "keyword":
        print("[wiki-qmd-query] reindex: qmd update done; keyword machine, no embed", file=sys.stderr)
        print("reindex=updated")
        return 0
    held: list[Slot] = []
    start = time.monotonic()
    try:
        while len(held) < n_slots:
            slot, _ = acquire_slot(n_slots, max(0.0, max_wait - (time.monotonic() - start)))
            if slot is None:
                print(f"[wiki-qmd-query] reindex: could not hold all {n_slots} GPU slots within "
                      f"{max_wait:.0f}s; index updated, not embedded", file=sys.stderr)
                return EXIT_GPU_BUSY
            held.append(slot)
        rc, out, err = run_qmd(["embed"], REINDEX_TIMEOUT)
    finally:
        for slot in held:
            slot.release()
    if rc is None:
        print(f"[wiki-qmd-query] reindex: qmd embed timed out after {REINDEX_TIMEOUT:.0f}s", file=sys.stderr)
        return EXIT_TIMEOUT
    lines = [ANSI_RE.sub("", l).strip() for l in (out + "\n" + err).splitlines()]
    last = next((l for l in reversed(lines) if l and "█" not in l), "")
    if rc != 0:
        print(f"[wiki-qmd-query] reindex: qmd embed failed (exit {rc}): {last[-300:]}", file=sys.stderr)
        return 1
    print(f"[wiki-qmd-query] reindex: qmd update and embed done. {last}", file=sys.stderr)
    print("reindex=embedded")
    return 0


def collections() -> dict[str, int]:
    """qmd's collections as {name: file count}. qmd names a collection by the folder
    it indexes (e.g. C:\\...\\notebooks\\agentic-design\\wiki)."""
    out = subprocess.run([*qmd_cmd(), "collection", "list"], capture_output=True,
                         text=True, encoding="utf-8", errors="replace").stdout
    found: dict[str, int] = {}
    name = None
    for line in out.splitlines():
        m = re.match(r"^(\S.*?) \(qmd://", line)
        if m:
            name = m.group(1)
            continue
        f = re.search(r"Files:\s+(\d+)", line)
        if f and name:
            found[name] = int(f.group(1))
            name = None
    return found


def norm(p: str) -> str:
    return p.replace("\\", "/").rstrip("/").lower()


def collection_for(notebook: str, cols: dict[str, int]) -> str | None:
    target = norm(str(Path(wiki_dir(notebook)).resolve()))
    return next((c for c in cols if norm(c) == target), None)


def gpu_full(text: str) -> bool:
    return any(m.lower() in text.lower() for m in GPU_FULL_MARKERS)


def reranked_count(err: str) -> int | None:
    """Candidates qmd reranked, from its stderr progress line; None when it printed none
    (no candidates, or a qmd whose output changed — never read as zero)."""
    m = RERANKED_RE.search(ANSI_RE.sub("", err or ""))
    return int(m.group(1)) if m else None


class SearchRun(NamedTuple):
    outcome: str  # ok | error | timeout | no-slot | gpu-failing
    rc: int | None
    out: str
    err: str
    waited_s: float
    run_s: float
    attempts: int


def run_search(qmd_argv: list[str], n_slots: int, timeout: float, max_wait: float,
               retries: int) -> SearchRun:
    """One `qmd query` holding a GPU slot, retried with back-off on GPU trouble."""
    total_wait, backoff = 0.0, 10.0
    for attempt in range(1, retries + 2):
        slot, waited = acquire_slot(n_slots, max_wait - total_wait)
        total_wait += waited
        if slot is None:
            return SearchRun("no-slot", None, "", "", total_wait, 0.0, attempt)
        t0 = time.monotonic()
        try:
            rc, out, err = run_qmd(["query", *qmd_argv], timeout)
        finally:
            slot.release()
        run_s = time.monotonic() - t0
        if rc is None:
            return SearchRun("timeout", None, "", "", total_wait, run_s, attempt)
        if rc != 0 and gpu_full(out + err):
            if attempt <= retries:
                print(f"[wiki-qmd-query] GPU error (full, or a transient CUDA fault) — retry {attempt}/{retries} "
                      f"in {backoff:.0f}s", file=sys.stderr)
                time.sleep(backoff)
                total_wait += backoff
                backoff *= 2
                continue
            return SearchRun("gpu-failing", rc, out, err, total_wait, run_s, attempt)
        return SearchRun("ok" if rc == 0 else "error", rc, out, err, total_wait, run_s, attempt)
    raise AssertionError("unreachable")


def split_query(qmd_args: list[str]) -> tuple[str, list[str]]:
    """(the query's words, the qmd options) from the arguments passed through to qmd."""
    words, opts, i = [], [], 0
    while i < len(qmd_args):
        a = qmd_args[i]
        if a.startswith("-") and len(a) > 1:
            opts.append(a)
            if a in VALUE_OPTIONS and i + 1 < len(qmd_args):
                opts.append(qmd_args[i + 1])
                i += 1
        else:
            words.append(a)
        i += 1
    return " ".join(words), opts


def key_terms(query: str) -> list[str]:
    """The query's key words, in order: stop words and repeats dropped, at most KEYWORD_MAX_TERMS."""
    seen, terms = set(), []
    for w in re.findall(r"[^\W_][\w.+'-]*", query):
        w = w.rstrip(".'-")
        if w.lower() in STOPWORDS or w.lower() in seen:
            continue
        seen.add(w.lower())
        terms.append(w)
    return terms[:KEYWORD_MAX_TERMS]


def keyword_queries(query: str) -> list[str]:
    """The keyword searches for one query: its key words together, then every pair of them."""
    terms = key_terms(query)
    if not terms:
        return [query]
    qs = [" ".join(terms)]
    if len(terms) > 2:
        qs += [f"{a} {b}" for a, b in itertools.combinations(terms, 2)]
    return qs


def row_key(file: str) -> str:
    """A result's file, comparable across qmd's JSON and text output."""
    m = re.match(r"(qmd://.+?\.md)", str(file).replace("\\", "/"), re.I)
    return (m.group(1) if m else str(file).replace("\\", "/")).lower()


def keyword_options(opts: list[str]) -> list[str]:
    """The passed-through options a keyword search keeps: scope and score filters, not output or depth."""
    keep, i = [], 0
    while i < len(opts):
        a = opts[i]
        takes_value = a in VALUE_OPTIONS and i + 1 < len(opts)
        if a not in FORMAT_FLAGS and a not in ("-n", "-C", "--candidate-limit", "--format"):
            keep += opts[i:i + 2] if takes_value else [a]
        i += 2 if takes_value else 1
    return keep


def keyword_rows(query: str, opts: list[str], timeout: float) -> tuple[list[dict] | None, int, bool]:
    """The word-pair keyword search: every search in keyword_queries(), in parallel, fused by
    reciprocal rank (each row keeps the fields from its best-ranked appearance). No model.
    Returns (rows or None when every search failed, searches run, any timed out)."""
    from concurrent.futures import ThreadPoolExecutor
    qs = keyword_queries(query)
    keep = keyword_options(opts)

    def one(q: str):
        rc, out, _ = run_qmd(["search", q, *keep, "-n", str(KEYWORD_PER_LIST), "--json"], timeout)
        if rc is None:
            return "timeout"
        if rc != 0:
            return None
        kept, _ = drop_machine_files(out, "json", KEYWORD_PER_LIST)
        try:
            return json.loads(kept)
        except ValueError:
            return None

    with ThreadPoolExecutor(max_workers=KEYWORD_WORKERS) as ex:
        lists = list(ex.map(one, qs))
    timed_out = any(lst == "timeout" for lst in lists)
    good = [lst for lst in lists if isinstance(lst, list)]
    if not good:
        return None, len(qs), timed_out
    score: dict[str, float] = {}
    best: dict[str, tuple[int, dict]] = {}
    for lst in good:
        for rank, row in enumerate(lst, 1):
            k = row_key(row.get("file", ""))
            score[k] = score.get(k, 0.0) + 1.0 / (60 + rank)
            if k not in best or rank < best[k][0]:
                best[k] = (rank, row)
    return [best[k][1] for k in sorted(score, key=lambda k: -score[k])], len(qs), timed_out


def render_text(rows: list[dict]) -> str:
    """Rows in qmd's own text layout: the qmd:// line, Title, Score, then the snippet."""
    out = []
    for r in rows:
        s = r.get("score")
        pct = f"{round(float(s) * 100)}%" if isinstance(s, (int, float)) else "?"
        out.append(f"{r.get('file', '')}:{r.get('line', '')} {r.get('docid', '')}\nTitle: {r.get('title', '')}\n"
                   f"Score:  {pct}\n\n{str(r.get('snippet') or '').rstrip()}\n\n")
    return "\n".join(out)


def run_keyword(qmd_argv: list[str], timeout: float) -> SearchRun:
    """One `qmd search`: qmd's keyword index, no model. Used on a keyword machine only for the
    output formats the word-pair search does not render (--files, --csv, --md, --xml)."""
    t0 = time.monotonic()
    rc, out, err = run_qmd(["search", *qmd_argv], timeout)
    run_s = time.monotonic() - t0
    if rc is None:
        return SearchRun("timeout", None, "", "", 0.0, run_s, 1)
    return SearchRun("ok" if rc == 0 else "error", rc, out, err, 0.0, run_s, 1)


def result_file(first_line: str) -> str:
    """The file name in a text result's header line (qmd://<collection>/<path>.md[:N] #id)."""
    names = re.findall(r"([^/\\]+\.md)", first_line)
    return names[-1].lower() if names else ""


def retired(qmd_file: str) -> bool:
    """A result whose entry is retired (`superseded_by`, frontmatter spec): its
    successor is the answer. qmd names a file qmd://<collection path>/<path>.md."""
    m = re.match(r"qmd://(.+?\.md)", qmd_file.replace("\\", "/"))
    if not m:
        return False
    try:
        head = Path(m.group(1)).read_text(encoding="utf-8", errors="replace")[:3000]
    except OSError:
        return False
    return is_superseded(split_frontmatter(head)[0])


def drop_machine_files(out: str, fmt: str, k: int) -> tuple[str, int]:
    """Remove _MAP/_INDEX results and retired entries (2026-09-14), then trim to
    k; returns (output, dropped count)."""
    if fmt == "json":
        try:
            rows = json.loads(out)
        except ValueError:
            return out, 0
        keep = [r for r in rows if Path(str(r.get("file", ""))).name.lower() not in MACHINE_FILES
                and not retired(str(r.get("file", "")))]
        return json.dumps(keep[:k], indent=2) + "\n", len(rows) - len(keep)
    if fmt == "text":
        lines = out.splitlines(keepends=True)
        head, blocks, cur = [], [], None
        for line in lines:
            if line.startswith("qmd://"):
                cur = [line]
                blocks.append(cur)
            elif cur is None:
                head.append(line)
            else:
                cur.append(line)
        keep = [b for b in blocks if result_file(b[0]) not in MACHINE_FILES and not retired(b[0])]
        return "".join(head) + "".join("".join(b) for b in keep[:k]), len(blocks) - len(keep)
    return out, 0


def log_call(record: dict) -> None:
    try:
        with open(slot_dir() / "searches.jsonl", "a", encoding="utf-8") as f:
            f.write(json.dumps(record) + "\n")
    except OSError:
        pass  # logging never blocks a search


def parse_qmd_version(text: str) -> tuple[int, ...] | None:
    """'qmd 2.8.3 (facd35e)' -> (2, 8, 3); None when the text holds no version."""
    m = re.search(r"(\d+)\.(\d+)\.(\d+)", text or "")
    return tuple(int(g) for g in m.groups()) if m else None


def qmd_version_text() -> str:
    try:
        return subprocess.run([*qmd_cmd(), "--version"], capture_output=True, text=True,
                              encoding="utf-8", errors="replace", timeout=30).stdout.strip()
    except (OSError, subprocess.TimeoutExpired):
        return ""


def parse_gpu_inspect(text: str) -> str | None:
    """'cuda' or 'metal' when node-llama-cpp's `inspect gpu` reports that backend available
    ("CUDA: available"), else None. Vulkan alone is None (see GPU_BACKENDS)."""
    for line in (text or "").splitlines():
        name, _, state = line.strip().partition(":")
        if name in GPU_BACKENDS and state.strip().lower().startswith("available"):
            return name.lower()
    return None


def gpu_backend() -> tuple[str | None, str]:
    """(backend, detail): the GPU a full search would run on ('cuda' or 'metal'), or None and
    why not. Runs node-llama-cpp's `inspect gpu` from qmd's package folder; loads no model."""
    npm = shutil.which("npm")
    if not npm:
        return None, "npm not found"
    root = subprocess.run([npm, "root", "-g"], capture_output=True, text=True).stdout.strip()
    qdir = Path(root) / "@tobilu" / "qmd"
    if not qdir.is_dir():
        return None, f"qmd is not installed ({qdir})"
    kwargs = {"cwd": qdir, "stdout": subprocess.PIPE, "stderr": subprocess.PIPE,
              "text": True, "encoding": "utf-8", "errors": "replace"}
    if os.name != "nt":
        kwargs["start_new_session"] = True
    proc = subprocess.Popen([shutil.which("npx") or "npx", "--no-install", "node-llama-cpp", "inspect", "gpu"],
                            **kwargs)
    try:
        out, _ = proc.communicate(timeout=GPU_CHECK_TIMEOUT)
    except subprocess.TimeoutExpired:
        kill_tree(proc)
        return None, f"the GPU check did not answer in {GPU_CHECK_TIMEOUT}s"
    found = [l.strip() for l in out.splitlines() if l.strip().split(":")[0] in (*GPU_BACKENDS, "Vulkan")]
    return parse_gpu_inspect(out), "; ".join(found) or "no GPU lines in node-llama-cpp's output"


def preflight() -> int:
    """Says the machine's search mode. On a full machine, the /wiki-search GPU check:
    node-llama-cpp must report CUDA or Metal available. Also reports qmd's version;
    older than QMD_MIN_VERSION is a warning, not a failure — it still searches, but
    the three-slot default assumes 2.8.3, so on an older qmd a third concurrent
    search fails and retries. A keyword machine runs no GPU check: it never loads a
    model."""
    mode = search_mode()
    want = ".".join(map(str, QMD_MIN_VERSION))
    text = qmd_version_text()
    ver = parse_qmd_version(text)
    if ver is None:
        print(f"[wiki-qmd-query] preflight: qmd version unknown ({text or 'no output'})", file=sys.stderr)
    elif ver < QMD_MIN_VERSION and mode == "full":
        print(f"[wiki-qmd-query] preflight: WARNING qmd {'.'.join(map(str, ver))} is older than {want} — "
              "upgrade (npm i -g @tobilu/qmd@latest, then qmd doctor) or set WIKI_QMD_SLOTS=2",
              file=sys.stderr)
    else:
        print(f"[wiki-qmd-query] preflight: qmd {'.'.join(map(str, ver))}", file=sys.stderr)
    if mode == "keyword":
        print("[wiki-qmd-query] preflight: search mode keyword — this machine runs qmd's keyword search "
              "only (no model, so no GPU check); switch with --set-mode full once it has a GPU", file=sys.stderr)
        return 0
    backend, detail = gpu_backend()
    print(f"[wiki-qmd-query] preflight: search mode full; GPU check: {detail}", file=sys.stderr)
    if not backend:
        print("[wiki-qmd-query] preflight: no CUDA or Metal GPU — stop and report. On a machine with no GPU, "
              "`--set-mode keyword` makes search keyword-only", file=sys.stderr)
        return EXIT_USAGE
    return 0


def set_mode(mode: str) -> int:
    """Switch this machine's search mode. `full` only when the GPU check passes."""
    backend = None
    if mode == "full":
        backend, detail = gpu_backend()
        if not backend:
            print(f"[wiki-qmd-query] not switched: the GPU check fails ({detail}). The full search needs "
                  f"CUDA (an NVIDIA GPU with the CUDA runtime; see the install page) or Metal (a Mac). "
                  f"This machine stays {search_mode()}.", file=sys.stderr)
            return EXIT_USAGE
    path = set_search_mode(mode)
    if mode == "full":
        print(f"search mode: full (GPU: {backend}), written to {path}. Next, once: `qmd embed` — it builds the "
              "meaning index a keyword machine never built; until then the full search has no meaning matches.")
    else:
        print(f"search mode: keyword, written to {path}. Searches now run qmd's keyword index only; "
              "no model loads. Skip `qmd embed` on this machine (`qmd update` keeps the index current).")
    return 0


def stats() -> int:
    p = slot_dir() / "searches.jsonl"
    if not p.exists():
        print("no searches logged yet")
        return 0
    rows = [json.loads(l) for l in p.read_text(encoding="utf-8").splitlines() if l.strip()]
    done = [r for r in rows if r.get("outcome") == "ok"]
    waited = [r["waited_s"] for r in done if r.get("waited_s", 0) >= 1]
    print(f"searches logged: {len(rows)}  ok: {len(done)}  "
          f"gpu-busy: {sum(r.get('outcome') == 'gpu-busy' for r in rows)}  "
          f"timeout: {sum(r.get('outcome') == 'timeout' for r in rows)}  "
          f"error: {sum(r.get('outcome') == 'error' for r in rows)}")
    if done:
        by_c: dict[object, list] = {}
        for r in done:  # a keyword search has no C: listed apart
            by_c.setdefault(r.get("C", "?") if r.get("mode", "full") == "full" else "keyword", []).append(r["run_s"])
        print("run time by C: " + ", ".join(f"{c if c == 'keyword' else f'C={c}'} median {statistics.median(v):.1f}s (n={len(v)})"
                                            for c, v in sorted(by_c.items(), key=lambda kv: str(kv[0]))))
        print(f"waited for a slot: {len(waited)} of {len(done)} ok searches"
              + (f"  (median wait {statistics.median(waited):.1f}s, max {max(waited):.1f}s)" if waited else ""))
        print(f"needed a GPU retry: {sum(r.get('attempts', 1) > 1 for r in done)}")
        # --depth-check keeps its own verdict (and may force a small C on purpose), so leave it out
        measured = [r for r in done if isinstance(r.get("reranked"), int) and r.get("caller") != "depth-check"]
        if measured:
            counts = [r["reranked"] for r in measured]
            reached = [r for r in measured if r["reranked"] >= r.get("C", 0)]
            print(f"candidates reranked: median {statistics.median(counts):.0f}, max {max(counts)} "
                  f"(n={len(measured)}); reached C in {len(reached)}"
                  + (" — C may have cut those pools: raise C" if reached else ""))
    by_caller: dict[str, int] = {}
    for r in rows:
        by_caller[r.get("caller", "?")] = by_caller.get(r.get("caller", "?"), 0) + 1
    print("by caller: " + ", ".join(f"{k} {v}" for k, v in sorted(by_caller.items())))
    return 0


def sample_titles(notebook: str, n: int) -> list[str]:
    """n entry titles spread evenly across a notebook's research/ and project/ entries."""
    root = Path(wiki_dir(notebook))
    files = sorted(p for half in ("research", "project") for p in (root / half).rglob("*.md")
                   if p.name.lower() not in MACHINE_FILES | {"readme.md"})
    titles = []
    for p in files[:: max(1, len(files) // n)][:n]:
        m = re.search(r'^title:\s*"?(.+?)"?\s*$', p.read_text(encoding="utf-8", errors="replace"), re.M)
        if m:
            titles.append(re.sub(r"\s*\([^)]*\)\s*$", "", m.group(1))[:90])
    return titles


def depth_check(notebook: str, n: int, c: int, n_slots: int, timeout: float, max_wait: float,
                retries: int) -> int:
    """Search n sampled titles and read how many candidates qmd reranked. C can only cut when
    that count reaches C, so the count against C is the measurement: exit 1 when any search
    reached C, exit 2 when no search could be measured (never a green over nothing)."""
    cols = collections()
    col = collection_for(notebook, cols)
    if col is None:
        print(f"[wiki-qmd-query] notebook '{notebook}' has no qmd collection", file=sys.stderr)
        return EXIT_USAGE
    print(f"depth check: {notebook} ({cols[col]} files) — candidates reranked against C={c}")
    counts, failed = [], 0
    for q in sample_titles(notebook, n):
        run = run_search([q, "-c", col, "-n", "1", "-C", str(c), "--json"], n_slots, timeout, max_wait, retries)
        got = reranked_count(run.err) if run.outcome == "ok" else None
        log_call({"ts": now_stamp(), "pid": os.getpid(), "caller": "depth-check", "query": q[:80],
                  "slots": n_slots, "k": 1, "C": c, "files": cols[col], "scope": notebook,
                  "outcome": run.outcome, "waited_s": round(run.waited_s, 1), "run_s": round(run.run_s, 1),
                  "attempts": run.attempts, "rc": run.rc, "reranked": got})
        if got is None:
            failed += 1
            print(f"  not measured ({run.outcome}): {q[:70]}")
            continue
        counts.append(got)
        print(f"  {got:3} of {c}{'  REACHED C' if got >= c else ''}  {q[:70]}")
    reached = sum(x >= c for x in counts)
    if not counts:
        print(f"summary: not checked — none of {failed} searches reported a reranked count")
        code = EXIT_USAGE
    else:
        verdict = (f"C was reached in {reached} — it may have cut those pools; raise C" if reached
                   else f"C never reached (headroom {c - max(counts)})")
        print(f"summary: {len(counts)} measured, {failed} not; reranked median "
              f"{statistics.median(counts):.0f}, max {max(counts)} — {verdict}")
        code = 1 if reached else 0
    try:
        with open(slot_dir() / "depth-checks.jsonl", "a", encoding="utf-8") as f:
            f.write(json.dumps({"ts": now_stamp(), "notebook": notebook, "files": cols[col], "C": c,
                                "measured": len(counts), "not_measured": failed,
                                "reranked_max": max(counts) if counts else None, "reached_C": reached}) + "\n")
    except OSError:
        pass
    return code


def main() -> int:
    # Redirected to a file on Windows, stdout/stderr default to cp1252, which cannot encode what qmd
    # returns (→, ≥, CJK in titles and snippets): the write raised UnicodeEncodeError and the search
    # exited 1 (17 of 39 discovery searches, cycle 2026-09-14-01). qmd's output is UTF-8; say so.
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0],
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("-k", "-n", "--results", dest="k", type=int, default=DEFAULT_K,
                    help="results returned, the top k after reranking (default 30, or $WIKI_QMD_K; qmd's flag is -n)")
    ap.add_argument("-C", "--candidate-limit", dest="C", type=int, default=DEFAULT_C,
                    help="the most candidates the reranker may score (default 120, or $WIKI_QMD_C); "
                         "qmd's pool is about 100 at most, so the default never cuts")
    scope = ap.add_mutually_exclusive_group()
    scope.add_argument("--notebook", help="search this registry notebook (default: the current project's)")
    scope.add_argument("--all-notebooks", action="store_true", help="search every indexed notebook")
    ap.add_argument("--slots", type=int, default=int(os.environ.get("WIKI_QMD_SLOTS", "3")),
                    help="concurrent full searches allowed on the GPU (default 3, or $WIKI_QMD_SLOTS; "
                         "set 2 on a qmd older than 2.8.3)")
    ap.add_argument("--timeout", type=float, default=120, help="seconds per qmd query (default 120)")
    ap.add_argument("--max-wait", type=float, default=900, help="max seconds to wait for a free slot (default 900)")
    ap.add_argument("--retries", type=int, default=3, help="GPU retries after the first attempt (default 3)")
    ap.add_argument("--caller", default=os.environ.get("WIKI_QMD_CALLER", "session"),
                    help="who is searching, for the log (e.g. wiki-ingester, session)")
    ap.add_argument("--preflight", action="store_true",
                    help="say the machine's search mode; on full, run the GPU check (and report the qmd version)")
    ap.add_argument("--set-mode", choices=("full", "keyword"),
                    help="switch this machine's search mode (full needs the GPU check to pass)")
    ap.add_argument("--stats", action="store_true", help="summarise the search log")
    ap.add_argument("--reindex", action="store_true",
                    help="bring the index up to date: qmd update, then qmd embed holding every GPU slot "
                         "(a keyword machine only updates); run after promoting and before ingest workers search")
    ap.add_argument("--depth-check", action="store_true",
                    help="search sampled titles from --notebook (or the project's) and report the "
                         "candidates reranked against C; exit 1 if any search reached C")
    ap.add_argument("--queries", type=int, default=6, help="titles to sample for --depth-check (default 6)")
    ap.add_argument("--keyword-extra", type=int, default=KEYWORD_EXTRA,
                    help="on a full machine, show up to N entries only the word-pair keyword search found, "
                         "after the full search's results (default 20, or $WIKI_QMD_KEYWORD_EXTRA; 0 = none)")
    args, qmd_args = ap.parse_known_args()

    if args.stats:
        return stats()
    if args.preflight:
        return preflight()
    if args.set_mode:
        return set_mode(args.set_mode)
    if args.reindex:
        return reindex(search_mode(), args.slots, args.max_wait)

    mode = search_mode()
    notebook = args.notebook
    if not notebook and not args.all_notebooks:
        notebook = load_config().get("notebook")  # the current project's notebook, if any
    if args.depth_check:
        if mode == "keyword":
            print("[wiki-qmd-query] depth check: not measured — this machine is set to keyword search, "
                  "which has no reranker", file=sys.stderr)
            return EXIT_USAGE
        if not notebook:
            ap.error("--depth-check needs --notebook (no project notebook found from this folder)")
        return depth_check(notebook, args.queries, args.C, args.slots, args.timeout, args.max_wait, args.retries)
    if not qmd_args:
        ap.error("give a query (and any qmd query options)")

    query_words, passed_opts = split_query(qmd_args)
    query_text = query_words[:80]
    cols = collections()
    scope_note = "all notebooks"
    if notebook:
        col = collection_for(notebook, cols)
        if col is None:
            print(f"[wiki-qmd-query] notebook '{notebook}' has no qmd collection "
                  f"(expected {Path(wiki_dir(notebook)).resolve()}) — add it: "
                  f"qmd collection add \"<that path>\", then qmd update && qmd embed", file=sys.stderr)
            return EXIT_USAGE
        files, scope_note = cols[col], notebook
        qmd_args = [*qmd_args, "-c", col]
        passed_opts = [*passed_opts, "-c", col]
    else:
        files = sum(cols.values())
    c = args.C
    if args.k > c and mode == "full":
        print(f"[wiki-qmd-query] note: k={args.k} is larger than C={c}; the reranker only scores "
              f"the top {c} candidates", file=sys.stderr)
    fmt = ("json" if "--json" in qmd_args
           else "other" if any(f in qmd_args for f in ("--files", "--csv", "--md", "--xml")) else "text")
    ask_k = args.k + (EXTRA_FOR_FILTER if fmt != "other" else 0)
    qmd_args = [*qmd_args, "-n", str(ask_k)] + (["-C", str(c)] if mode == "full" else [])

    record = {"ts": now_stamp(), "pid": os.getpid(), "caller": args.caller, "query": query_text, "mode": mode,
              "slots": args.slots, "k": args.k, "C": c, "files": files, "scope": scope_note}
    if mode == "keyword" and fmt != "other":
        # a keyword machine: the word-pair keyword search, no model
        t0 = time.monotonic()
        rows, n_searches, timed_out = keyword_rows(query_words, passed_opts, args.timeout)
        run_s = round(time.monotonic() - t0, 1)
        record.update(waited_s=0.0, run_s=run_s, attempts=1, keyword_searches=n_searches, reranked=None)
        if rows is None:
            record.update(outcome="timeout" if timed_out else "error", rc=EXIT_TIMEOUT if timed_out else 1)
            log_call(record)
            print(f"[wiki-qmd-query] keyword search failed — all {n_searches} qmd searches "
                  f"{'timed out' if timed_out else 'failed'}; stop and report", file=sys.stderr)
            return EXIT_TIMEOUT if timed_out else 1
        rows = rows[:args.k]
        sys.stdout.write(json.dumps(rows, indent=2, ensure_ascii=False) + "\n" if fmt == "json" else render_text(rows))
        record.update(outcome="ok", rc=0)
        log_call(record)
        print(f"[wiki-qmd-query] keyword search ok — {scope_note}, k={args.k}, {len(rows)} results from "
              f"{n_searches} keyword searches (the key words together and in pairs); this machine is set to "
              f"keyword (no GPU: no meaning matches, no reranking); ran {run_s:.1f}s", file=sys.stderr)
        return 0
    if mode == "keyword":
        run = run_keyword(qmd_args, args.timeout)
    else:
        run = run_search(qmd_args, args.slots, args.timeout, args.max_wait, args.retries)
    timing = dict(waited_s=round(run.waited_s, 1), run_s=round(run.run_s, 1), attempts=run.attempts)
    if run.outcome in ("no-slot", "gpu-failing"):
        record.update(outcome="gpu-busy", rc=EXIT_GPU_BUSY, **timing)
        log_call(record)
        why = (f"no GPU slot free after {run.waited_s:.0f}s" if run.outcome == "no-slot"
               else f"GPU still failing after {args.retries} retries")
        print(f"[wiki-qmd-query] {why} — stop and report (no keyword fallback; run fewer parallel workers)",
              file=sys.stderr)
        return EXIT_GPU_BUSY
    if run.outcome == "timeout":
        record.update(outcome="timeout", rc=EXIT_TIMEOUT, **timing)
        log_call(record)
        print(f"[wiki-qmd-query] qmd {'search' if mode == 'keyword' else 'query'} timed out after "
              f"{args.timeout:.0f}s (process tree killed) — stop and report"
              + ("" if mode == "keyword" else "; run the --preflight GPU check"), file=sys.stderr)
        return EXIT_TIMEOUT
    out, dropped = drop_machine_files(run.out, fmt, args.k) if run.rc == 0 else (run.out, 0)
    # a full machine also runs the word-pair keyword search and shows what only it found, after the
    # full search's own results (task #64): never reranked, never mixed into the full search's order
    extra_note = ""
    if mode == "full" and run.rc == 0 and fmt != "other" and args.keyword_extra > 0:
        t0 = time.monotonic()
        rows, n_searches, _ = keyword_rows(query_words, passed_opts, args.timeout)
        kw_s = time.monotonic() - t0
        if rows is None:
            extra_note = f"; keyword search unavailable ({n_searches} searches failed)"
        else:
            if fmt == "json":
                try:
                    full_rows = json.loads(out)
                except ValueError:
                    full_rows = None
            if fmt == "json" and full_rows is not None:
                seen = {row_key(r.get("file", "")) for r in full_rows}
                extras = [r for r in rows if row_key(r.get("file", "")) not in seen][:args.keyword_extra]
                out = json.dumps([{**r, "found_by": "full"} for r in full_rows]
                                 + [{**r, "found_by": "keyword"} for r in extras], indent=2, ensure_ascii=False) + "\n"
            elif fmt == "text":
                seen = {row_key(m) for m in re.findall(r"^(qmd://.+?\.md)", out, re.M)}
                extras = [r for r in rows if row_key(r.get("file", "")) not in seen][:args.keyword_extra]
                if extras:
                    out = (out.rstrip("\n") + f"\n\n## Also found by keyword search ({len(extras)}: not in the full "
                           "search's results above, not reranked)\n\n" + render_text(extras))
            else:
                extras = []
            record.update(keyword_extra=len(extras), keyword_searches=n_searches)
            extra_note = f"; +{len(extras)} found only by keyword search ({n_searches} keyword searches, {kw_s:.1f}s)"
    sys.stdout.write(out)
    if run.err.strip() and run.rc != 0:
        sys.stderr.write(run.err)
    reranked = reranked_count(run.err) if mode == "full" else None
    record.update(outcome=run.outcome, rc=run.rc, machine_files_dropped=dropped, reranked=reranked, **timing)
    log_call(record)
    status = "ok" if run.rc == 0 else f"rc={run.rc}"
    if mode == "keyword":
        print(f"[wiki-qmd-query] keyword search {status} — {scope_note}, k={args.k}; this machine is set to "
              f"keyword (no GPU: no meaning matches, no reranking); ran {run.run_s:.1f}s", file=sys.stderr)
        return run.rc
    pool = "" if reranked is None else f", reranked {reranked}{' (reached C — raise C)' if reranked >= c else ''}"
    print(f"[wiki-qmd-query] full search {status} — {scope_note}, k={args.k}, "
          f"C={c}{pool}; waited {run.waited_s:.1f}s for a GPU slot, ran {run.run_s:.1f}s, attempt {run.attempts}"
          f"{extra_note}", file=sys.stderr)
    return run.rc


if __name__ == "__main__":
    raise SystemExit(main())
