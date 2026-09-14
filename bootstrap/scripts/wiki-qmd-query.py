#!/usr/bin/env python3
"""
wiki-qmd-query.py — run qmd's full search (`qmd query`) safely from many
processes at once, sized to the notebook, and log how long each search waited
and ran.

Why (tested 2026-09-13 on an 8 GB RTX 4070 Laptop GPU): each `qmd query`
process loads ~2 GB of models onto the GPU. Two concurrent searches fit;
a third fails fast with "Failed to create any rerank context". The user's
decision the same night: every search is the FULL search, never a keyword
downgrade — when the GPU is full, searches wait their turn, and if that makes
batches too slow, run fewer workers.

Depth, named for what it is:
  -k  results returned after reranking (default 20; qmd's own flag is -n)
  -C  candidates the reranker scores; an entry outside the top C is never
      seen. Default: sized to the collection searched — 8% of its files,
      rounded up to 10, never below 40 or above 200 (1,211 files -> 100).
      A depth test on 2026-09-13 found C=40 missed canonical entries in a
      1,211-file notebook that C=100 ranked in its top 10, for ~2 s more.

What it does:
  - searches the current project's notebook by default (from the nearest
    .claude/wiki-config.json); --notebook <name> picks another,
    --all-notebooks searches every indexed one
  - holds one of N GPU slots (default 2) for the whole search — an OS file
    lock released when the process ends; a caller with no free slot waits
  - runs `qmd query` under a timeout that kills the whole process tree
  - GPU full or a transient CUDA fault: back off and retry; after the last
    retry exit 75 — stop and report; NEVER a fallback to `qmd search`
  - drops the machine files (_MAP.md, _INDEX.md) from text and --json results;
    they are orientation pages, never a link target
  - logs one JSON line per call to <slot-dir>/searches.jsonl; --stats sums it
  - --depth-check: samples entry titles from a notebook, searches each at C
    and 2C, and reports entries 2C ranks in its top k that C never returned —
    run it as notebooks grow; a rising count means the 8% rule needs raising

Usage:
  python wiki-qmd-query.py "tiered context loading"          # this project's notebook
  python wiki-qmd-query.py --notebook agentic-design "term"  # one notebook
  python wiki-qmd-query.py --all-notebooks "term"            # every notebook
  python wiki-qmd-query.py "term" -k 40 -C 100               # explicit depth
  python wiki-qmd-query.py --preflight                       # CUDA check only
  python wiki-qmd-query.py --stats                           # wait/run summary
  python wiki-qmd-query.py --depth-check --notebook agentic-design

Exit codes: qmd's own code on a completed search (0 = ok); 2 = preflight
failed or usage error; 75 = GPU busy after every retry; 124 = timed out.

Environment: WIKI_QMD_K, WIKI_QMD_C (fixed values instead of the defaults),
WIKI_QMD_SLOTS (default 2), WIKI_QMD_SLOT_DIR (default ~/.cache/wiki-qmd),
WIKI_QMD_BIN (the qmd executable; default: node + qmd's dist/cli/qmd.js).
"""

from __future__ import annotations

import argparse
import json
import math
import os
import re
import shutil
import statistics
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _wiki_config import load_config, now_stamp, wiki_dir  # noqa: E402

DEFAULT_K = int(os.environ.get("WIKI_QMD_K", "20"))
FIXED_C = int(os.environ["WIKI_QMD_C"]) if os.environ.get("WIKI_QMD_C") else None
C_RATIO, C_MIN, C_MAX = 0.08, 40, 200
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
    found next to the shim, which also keeps the process tree one level deep."""
    override = os.environ.get("WIKI_QMD_BIN")
    if override:
        return [override]
    shim = shutil.which("qmd")
    if not shim:
        print("[wiki-qmd-query] qmd not found on PATH (npm i -g @tobilu/qmd)", file=sys.stderr)
        sys.exit(EXIT_USAGE)
    entry = Path(shim).resolve().parent / "node_modules" / "@tobilu" / "qmd" / "dist" / "cli" / "qmd.js"
    node = shutil.which("node")
    if entry.exists() and node:
        return [node, str(entry)]
    return [shim]


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


def sized_c(files: int) -> int:
    """C from the size of what is searched: 8% of its files, rounded up to 10, in [40, 200]."""
    return min(C_MAX, max(C_MIN, math.ceil(files * C_RATIO / 10) * 10))


def gpu_full(text: str) -> bool:
    return any(m.lower() in text.lower() for m in GPU_FULL_MARKERS)


def result_file(first_line: str) -> str:
    """The file name in a text result's header line (qmd://<collection>/<path>.md[:N] #id)."""
    names = re.findall(r"([^/\\]+\.md)", first_line)
    return names[-1].lower() if names else ""


def drop_machine_files(out: str, fmt: str, k: int) -> tuple[str, int]:
    """Remove _MAP/_INDEX results and trim to k; returns (output, dropped count)."""
    if fmt == "json":
        try:
            rows = json.loads(out)
        except ValueError:
            return out, 0
        keep = [r for r in rows if Path(str(r.get("file", ""))).name.lower() not in MACHINE_FILES]
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
        keep = [b for b in blocks if result_file(b[0]) not in MACHINE_FILES]
        return "".join(head) + "".join("".join(b) for b in keep[:k]), len(blocks) - len(keep)
    return out, 0


def log_call(record: dict) -> None:
    try:
        with open(slot_dir() / "searches.jsonl", "a", encoding="utf-8") as f:
            f.write(json.dumps(record) + "\n")
    except OSError:
        pass  # logging never blocks a search


def preflight() -> int:
    """The /wiki-search CUDA check: node-llama-cpp must report CUDA available."""
    npm = shutil.which("npm")
    if not npm:
        print("[wiki-qmd-query] preflight: npm not found", file=sys.stderr)
        return EXIT_USAGE
    root = subprocess.run([npm, "root", "-g"], capture_output=True, text=True).stdout.strip()
    qdir = Path(root) / "@tobilu" / "qmd"
    npx = shutil.which("npx") or "npx"
    r = subprocess.run([npx, "--no-install", "node-llama-cpp", "inspect", "gpu"], cwd=qdir,
                       capture_output=True, text=True, encoding="utf-8", errors="replace")
    line = next((l.strip() for l in r.stdout.splitlines() if l.strip().startswith("CUDA:")), "")
    print(f"[wiki-qmd-query] preflight: {line or 'no CUDA line in node-llama-cpp output'}", file=sys.stderr)
    return 0 if "available" in line.lower() and "not" not in line.lower() else EXIT_USAGE


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
        for r in done:
            by_c.setdefault(r.get("C", "?"), []).append(r["run_s"])
        print("run time by C: " + ", ".join(f"C={c} median {statistics.median(v):.1f}s (n={len(v)})"
                                            for c, v in sorted(by_c.items(), key=lambda kv: str(kv[0]))))
        print(f"waited for a slot: {len(waited)} of {len(done)} ok searches"
              + (f"  (median wait {statistics.median(waited):.1f}s, max {max(waited):.1f}s)" if waited else ""))
        print(f"needed a GPU retry: {sum(r.get('attempts', 1) > 1 for r in done)}")
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


def depth_check(notebook: str, n: int, k: int) -> int:
    """Search n sampled titles at the sized C and at 2C; count the entries 2C ranks in its
    top k that C never returned. A rising count means C is too small for the notebook."""
    cols = collections()
    col = collection_for(notebook, cols)
    if col is None:
        print(f"[wiki-qmd-query] notebook '{notebook}' has no qmd collection", file=sys.stderr)
        return EXIT_USAGE
    c = FIXED_C or sized_c(cols[col])
    me = [sys.executable, str(Path(__file__).resolve()), "--caller", "depth-check", "--notebook", notebook]
    total, rows = 0, []
    print(f"depth check: {notebook} ({cols[col]} files) — C={c} vs C={2 * c}, top {k}")
    for q in sample_titles(notebook, n):
        got = {}
        for cc in (c, 2 * c):
            r = subprocess.run([*me, q, "-k", str(max(k, c)), "-C", str(cc), "--json"],
                               capture_output=True, text=True, encoding="utf-8", errors="replace")
            got[cc] = json.loads(r.stdout) if r.returncode == 0 else None
        if not got[c] or not got[2 * c]:
            print(f"  FAILED: {q[:70]}")
            continue
        seen = {x["file"] for x in got[c]}
        missed = [(i + 1, x) for i, x in enumerate(got[2 * c][:k]) if x["file"] not in seen]
        total += len(missed)
        rows.append(len(missed))
        print(f"  {len(missed):2} missed  {q[:70]}")
        for rank, x in missed:
            print(f"       #{rank:2} {x['score']:.2f}  {str(x.get('title', ''))[:70]}")
    mean = total / len(rows) if rows else 0
    verdict = ("C is enough" if mean < 0.5 else "borderline — watch it" if mean < 1.5
               else "raise C (the 8% rule) for this notebook")
    print(f"summary: {total} missed across {len(rows)} queries (mean {mean:.1f} per query) — {verdict}")
    try:
        with open(slot_dir() / "depth-checks.jsonl", "a", encoding="utf-8") as f:
            f.write(json.dumps({"ts": now_stamp(), "notebook": notebook, "files": cols[col], "C": c,
                                "k": k, "queries": len(rows), "missed": total, "mean": round(mean, 2)}) + "\n")
    except OSError:
        pass
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0],
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("-k", "-n", "--results", dest="k", type=int, default=DEFAULT_K,
                    help="results returned, the top k after reranking (default 20, or $WIKI_QMD_K; qmd's flag is -n)")
    ap.add_argument("-C", "--candidate-limit", dest="C", type=int, default=FIXED_C,
                    help="candidates the reranker scores (default: 8%% of the searched files, 40-200, "
                         "or $WIKI_QMD_C); an entry outside the top C never reaches the reranker")
    scope = ap.add_mutually_exclusive_group()
    scope.add_argument("--notebook", help="search this registry notebook (default: the current project's)")
    scope.add_argument("--all-notebooks", action="store_true", help="search every indexed notebook")
    ap.add_argument("--slots", type=int, default=int(os.environ.get("WIKI_QMD_SLOTS", "2")),
                    help="concurrent full searches allowed on the GPU (default 2, or $WIKI_QMD_SLOTS)")
    ap.add_argument("--timeout", type=float, default=120, help="seconds per qmd query (default 120)")
    ap.add_argument("--max-wait", type=float, default=900, help="max seconds to wait for a free slot (default 900)")
    ap.add_argument("--retries", type=int, default=3, help="GPU retries after the first attempt (default 3)")
    ap.add_argument("--caller", default=os.environ.get("WIKI_QMD_CALLER", "session"),
                    help="who is searching, for the log (e.g. wiki-ingester, session)")
    ap.add_argument("--preflight", action="store_true", help="run the CUDA check only")
    ap.add_argument("--stats", action="store_true", help="summarise the search log")
    ap.add_argument("--depth-check", action="store_true",
                    help="sample titles from --notebook (or the project's) and compare C with 2C")
    ap.add_argument("--queries", type=int, default=6, help="titles to sample for --depth-check (default 6)")
    args, qmd_args = ap.parse_known_args()

    if args.stats:
        return stats()
    if args.preflight:
        return preflight()

    notebook = args.notebook
    if not notebook and not args.all_notebooks:
        notebook = load_config().get("notebook")  # the current project's notebook, if any
    if args.depth_check:
        if not notebook:
            ap.error("--depth-check needs --notebook (no project notebook found from this folder)")
        return depth_check(notebook, args.queries, args.k)
    if not qmd_args:
        ap.error("give a query (and any qmd query options)")

    query_text = " ".join(qmd_args)[:80]
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
    else:
        files = sum(cols.values())
    c = args.C or sized_c(files)
    if args.k > c:
        print(f"[wiki-qmd-query] note: k={args.k} is larger than C={c}; the reranker only scores "
              f"the top {c} candidates", file=sys.stderr)
    fmt = ("json" if "--json" in qmd_args
           else "other" if any(f in qmd_args for f in ("--files", "--csv", "--md", "--xml")) else "text")
    ask_k = args.k + (EXTRA_FOR_FILTER if fmt != "other" else 0)
    qmd_args = [*qmd_args, "-n", str(ask_k), "-C", str(c)]

    record = {"ts": now_stamp(), "pid": os.getpid(), "caller": args.caller, "query": query_text,
              "slots": args.slots, "k": args.k, "C": c, "C_sized": args.C is None,
              "files": files, "scope": scope_note}
    total_wait = 0.0
    backoff = 10.0
    for attempt in range(1, args.retries + 2):
        slot, waited = acquire_slot(args.slots, args.max_wait - total_wait)
        total_wait += waited
        if slot is None:
            record.update(outcome="gpu-busy", waited_s=round(total_wait, 1), run_s=0, attempts=attempt, rc=EXIT_GPU_BUSY)
            log_call(record)
            print(f"[wiki-qmd-query] no GPU slot free after {total_wait:.0f}s — stop and report "
                  "(no keyword fallback; run fewer parallel workers)", file=sys.stderr)
            return EXIT_GPU_BUSY
        t0 = time.monotonic()
        try:
            rc, out, err = run_qmd(["query", *qmd_args], args.timeout)
        finally:
            slot.release()
        run_s = time.monotonic() - t0
        if rc is None:
            record.update(outcome="timeout", waited_s=round(total_wait, 1), run_s=round(run_s, 1), attempts=attempt, rc=EXIT_TIMEOUT)
            log_call(record)
            print(f"[wiki-qmd-query] qmd query timed out after {args.timeout:.0f}s (process tree killed) — "
                  "stop and report; run the --preflight CUDA check", file=sys.stderr)
            return EXIT_TIMEOUT
        if rc != 0 and gpu_full(out + err) and attempt <= args.retries:
            print(f"[wiki-qmd-query] GPU error (full, or a transient CUDA fault) — retry {attempt}/{args.retries} "
                  f"in {backoff:.0f}s", file=sys.stderr)
            time.sleep(backoff)
            total_wait += backoff
            backoff *= 2
            continue
        if rc != 0 and gpu_full(out + err):
            record.update(outcome="gpu-busy", waited_s=round(total_wait, 1), run_s=round(run_s, 1), attempts=attempt, rc=EXIT_GPU_BUSY)
            log_call(record)
            print(f"[wiki-qmd-query] GPU still failing after {args.retries} retries — stop and report "
                  "(no keyword fallback; run fewer parallel workers)", file=sys.stderr)
            return EXIT_GPU_BUSY
        dropped = 0
        if rc == 0:
            out, dropped = drop_machine_files(out, fmt, args.k)
        sys.stdout.write(out)
        if err.strip() and rc != 0:
            sys.stderr.write(err)
        record.update(outcome="ok" if rc == 0 else "error", waited_s=round(total_wait, 1),
                      run_s=round(run_s, 1), attempts=attempt, rc=rc, machine_files_dropped=dropped)
        log_call(record)
        print(f"[wiki-qmd-query] full search {'ok' if rc == 0 else f'rc={rc}'} — {scope_note}, k={args.k}, "
              f"C={c}{' (sized)' if args.C is None else ''}; waited {total_wait:.1f}s for a GPU slot, "
              f"ran {run_s:.1f}s, attempt {attempt}", file=sys.stderr)
        return rc
    return EXIT_GPU_BUSY  # unreachable


if __name__ == "__main__":
    raise SystemExit(main())
