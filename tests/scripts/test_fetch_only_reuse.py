#!/usr/bin/env python3
"""Checks for task #106 (improver pass 2026-10-12-mixed P3): `--fetch-only` reuses the raw it already has.

    uv run python tests/scripts/test_fetch_only_reuse.py    # exit 0 = every check passed

Before: `wiki-update.py --fetch-only` on a URL already fetched into raw/ wrote a second raw with a
`-2` suffix; a worker that re-ran it by accident left an unreferenced duplicate (cycle 2026-10-11-01,
worker 2). Now a raw whose `source_url` is the same source (compared by `source_key`) is reused when no
entry cites it, and reported as a duplicate when one does; `--refetch` writes a new copy on purpose.
A local web server plays the page, so no check touches the network.
"""
from __future__ import annotations

import http.server
import os
import subprocess
import sys
import tempfile
import threading
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "scripts"

results: list[tuple[bool, str]] = []


def check(name: str, ok: bool, detail: object = ""):
    results.append((bool(ok), name + (f"  [{detail}]" if not ok and detail != "" else "")))


PAGE = ("<html><head><title>Honcho v3.3.0 release notes</title></head><body><h1>Honcho v3.3.0</h1>"
        + "".join(f"<p>Paragraph {i}: the memory service now keeps a session summary per peer.</p>" for i in range(30))
        + "</body></html>").encode("utf-8")


class Handler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):  # noqa: N802
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(PAGE)))
        self.end_headers()
        self.wfile.write(PAGE)

    def log_message(self, *a):
        pass


server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Handler)
threading.Thread(target=server.serve_forever, daemon=True).start()
URL = f"http://127.0.0.1:{server.server_port}/blog/honcho-v3-3-0"
ENV = dict(os.environ, NO_PROXY="127.0.0.1,localhost", no_proxy="127.0.0.1,localhost")


def fetch(vault: Path, url: str, *extra: str) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(SCRIPTS / "wiki-update.py"), "--vault", str(vault), "--topic", "nb",
                           "--source", url, "--fetch-only", *extra], capture_output=True, text=True,
                          encoding="utf-8", env=ENV, timeout=180)


def raws(vault: Path) -> list[str]:
    d = vault / "nb" / "raw"
    return sorted(p.name for p in d.iterdir()) if d.is_dir() else []


def printed(p: subprocess.CompletedProcess, key: str) -> str:
    for line in p.stdout.splitlines():
        if line.startswith(key + "="):
            return line.split("=", 1)[1].strip()
    return ""


with tempfile.TemporaryDirectory() as td:
    vault = Path(td)
    (vault / "nb" / "wiki" / "research").mkdir(parents=True)

    p1 = fetch(vault, URL)
    first = raws(vault)
    check("first fetch: exit 0 and one raw", p1.returncode == 0 and len(first) == 1, (p1.returncode, first, p1.stderr[-300:]))
    rp1 = printed(p1, "raw_path")

    p2 = fetch(vault, URL)
    check("second fetch: exit 0", p2.returncode == 0, p2.stderr[-300:])
    check("second fetch: no new raw (no -2 copy)", raws(vault) == first, raws(vault))
    check("second fetch: prints the existing raw_path", printed(p2, "raw_path") == rp1, (printed(p2, "raw_path"), rp1))
    check("second fetch: says it reused an earlier fetch", "reused" in p2.stdout.lower(), p2.stdout[-400:])

    p3 = fetch(vault, URL + "?utm_source=newsletter&ref=feed")
    check("tracking tags: the same source, still no new raw", p3.returncode == 0 and raws(vault) == first, raws(vault))
    check("tracking tags: prints the existing raw_path", printed(p3, "raw_path") == rp1, printed(p3, "raw_path"))

    p4 = fetch(vault, URL, "--refetch")
    after = raws(vault)
    check("--refetch: exit 0 and a new copy written", p4.returncode == 0 and len(after) == 2, (p4.returncode, after, p4.stderr[-300:]))
    check("--refetch: prints the new raw, not the old", printed(p4, "raw_path") not in ("", rp1), printed(p4, "raw_path"))

with tempfile.TemporaryDirectory() as td:
    vault = Path(td)
    (vault / "nb" / "wiki" / "research").mkdir(parents=True)
    p1 = fetch(vault, URL)
    first = raws(vault)
    raw_name = first[0] if first else "missing.md"
    entry = vault / "nb" / "wiki" / "research" / "honcho-v3-3-0.md"
    entry.write_text(f"---\ntitle: Honcho v3.3.0\nsource_url: {URL}\nraw_path: raw/{raw_name}\n---\n\n## TL;DR\n\nx\n",
                     encoding="utf-8")
    p2 = fetch(vault, URL)
    check("cited: no new raw", raws(vault) == first, raws(vault))
    check("cited: reported as a duplicate of the entry",
          "duplicate_of=" in p2.stdout and "honcho-v3-3-0.md" in printed(p2, "duplicate_of"), p2.stdout[-400:])

server.shutdown()
failed = [n for ok, n in results if not ok]
for ok, n in results:
    print(("PASS " if ok else "FAIL ") + n)
print(f"\n{len(results) - len(failed)}/{len(results)} passed")
sys.exit(1 if failed else 0)
