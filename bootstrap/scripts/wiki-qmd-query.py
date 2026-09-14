#!/usr/bin/env python3
"""
wiki-qmd-query.py — run qmd's full search (`qmd query`) safely from many
processes at once, and log how long each search waited and ran.

Why (tested 2026-09-13 on an 8 GB RTX 4070 Laptop GPU): each `qmd query`
process loads ~2 GB of models onto the GPU. Two concurrent searches fit;
a third fails fast with "Failed to create any rerank context". The user's
decision the same night: parallel ingest workers use the FULL search, never a
keyword downgrade — when the GPU is full, searches wait their turn, and if
that makes batches too slow, run fewer workers.

What it does:
  - holds one of N GPU slots (default 2) for the whole search — a lock file the
    OS releases when the process ends, so a crashed search never leaks a slot;
    a caller that finds no free slot waits for one
  - runs `qmd query <args>` under a timeout; on timeout the whole process tree
    is killed (on Windows qmd is a .cmd shim, so killing only the direct child
    would orphan the node process that holds the GPU)
  - if qmd still reports the GPU is full (another program on the GPU), releases
    the slot, backs off and retries; after the last retry it exits 75 — stop and
    report; it NEVER falls back to `qmd search`
  - passes qmd's stdout through unchanged (so `--json` output can be piped on)
    and prints one status line to stderr
  - appends one JSON line per call to <slot-dir>/searches.jsonl; `--stats`
    summarises it (how often callers waited, how long, failures)

Usage:
  python wiki-qmd-query.py "tiered context loading"            # like qmd query
  python wiki-qmd-query.py --caller wiki-ingester "term" -n 5  # extra args go to qmd
  python wiki-qmd-query.py --preflight                         # CUDA check only
  python wiki-qmd-query.py --stats                             # the wait/run summary

Exit codes: qmd's own code on a completed search (0 = ok); 2 = preflight failed
or usage error; 75 = GPU busy after every retry; 124 = timed out.

Environment: WIKI_QMD_SLOTS (default 2), WIKI_QMD_SLOT_DIR (default
~/.cache/wiki-qmd), WIKI_QMD_BIN (the qmd executable; default: qmd on PATH).
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import statistics
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _wiki_config import now_stamp  # noqa: E402

GPU_FULL_MARKERS = (
    "Failed to create any rerank context",
    "Failed to create context",
    "ErrorOutOfDeviceMemory",
    "out of memory",
    "cudaMalloc",
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


def gpu_full(text: str) -> bool:
    return any(m.lower() in text.lower() for m in GPU_FULL_MARKERS)


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
        runs = [r["run_s"] for r in done]
        print(f"run time (s): median {statistics.median(runs):.1f}  max {max(runs):.1f}")
        print(f"waited for a slot: {len(waited)} of {len(done)} ok searches"
              + (f"  (median wait {statistics.median(waited):.1f}s, max {max(waited):.1f}s)" if waited else ""))
        retried = sum(r.get("attempts", 1) > 1 for r in done)
        print(f"needed a GPU-busy retry: {retried}")
    by_caller: dict[str, int] = {}
    for r in rows:
        by_caller[r.get("caller", "?")] = by_caller.get(r.get("caller", "?"), 0) + 1
    print("by caller: " + ", ".join(f"{k} {v}" for k, v in sorted(by_caller.items())))
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0],
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--slots", type=int, default=int(os.environ.get("WIKI_QMD_SLOTS", "2")),
                    help="concurrent full searches allowed on the GPU (default 2, or $WIKI_QMD_SLOTS)")
    ap.add_argument("--timeout", type=float, default=120, help="seconds per qmd query (default 120)")
    ap.add_argument("--max-wait", type=float, default=900, help="max seconds to wait for a free slot (default 900)")
    ap.add_argument("--retries", type=int, default=3, help="GPU-busy retries after the first attempt (default 3)")
    ap.add_argument("--caller", default=os.environ.get("WIKI_QMD_CALLER", "session"),
                    help="who is searching, for the log (e.g. wiki-ingester, session)")
    ap.add_argument("--preflight", action="store_true", help="run the CUDA check only")
    ap.add_argument("--stats", action="store_true", help="summarise the search log")
    args, qmd_args = ap.parse_known_args()

    if args.stats:
        return stats()
    if args.preflight:
        return preflight()
    if not qmd_args:
        ap.error("give a query (and any qmd query options)")

    record = {"ts": now_stamp(), "pid": os.getpid(), "caller": args.caller,
              "query": " ".join(qmd_args)[:80], "slots": args.slots}
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
            print(f"[wiki-qmd-query] GPU full (another program on it?) — retry {attempt}/{args.retries} "
                  f"in {backoff:.0f}s", file=sys.stderr)
            time.sleep(backoff)
            total_wait += backoff
            backoff *= 2
            continue
        if rc != 0 and gpu_full(out + err):
            record.update(outcome="gpu-busy", waited_s=round(total_wait, 1), run_s=round(run_s, 1), attempts=attempt, rc=EXIT_GPU_BUSY)
            log_call(record)
            print(f"[wiki-qmd-query] GPU still full after {args.retries} retries — stop and report "
                  "(no keyword fallback; run fewer parallel workers)", file=sys.stderr)
            return EXIT_GPU_BUSY
        sys.stdout.write(out)
        if err.strip() and rc != 0:
            sys.stderr.write(err)
        record.update(outcome="ok" if rc == 0 else "error", waited_s=round(total_wait, 1),
                      run_s=round(run_s, 1), attempts=attempt, rc=rc)
        log_call(record)
        print(f"[wiki-qmd-query] full search {'ok' if rc == 0 else f'rc={rc}'} — waited {total_wait:.1f}s "
              f"for a GPU slot, ran {run_s:.1f}s, attempt {attempt}", file=sys.stderr)
        return rc
    return EXIT_GPU_BUSY  # unreachable


if __name__ == "__main__":
    raise SystemExit(main())
