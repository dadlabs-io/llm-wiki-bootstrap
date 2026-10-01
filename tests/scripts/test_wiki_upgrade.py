#!/usr/bin/env python3
"""Checks for wiki-upgrade.py's output encoding. Never shipped.

    python tests/scripts/test_wiki_upgrade.py    # exit 0 = every check passed

Found 2026-10-01 (task #60's testing): with its output piped, Python on Windows
writes cp1252, which has no "→", and wiki-upgrade.py crashed with
UnicodeEncodeError on the first line that prints one. new-wiki.py, which the
installers run, switches its output to UTF-8 at startup; wiki-upgrade.py did
not. The test forces cp1252 through PYTHONIOENCODING so it fails the same way on
any machine, and runs --dry-run, which writes nothing.
"""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "wiki-upgrade.py"

results: list[tuple[bool, str]] = []


def check(name: str, ok: bool, detail: object = ""):
    results.append((bool(ok), name + (f"  [{detail}]" if not ok and detail != "" else "")))


env = {k: v for k, v in os.environ.items() if k not in ("PYTHONIOENCODING", "PYTHONUTF8")}
env["PYTHONIOENCODING"] = "cp1252"  # what a pipe gets on Windows
p = subprocess.run([sys.executable, str(SCRIPT), "--dry-run", "--bootstrap-source", str(ROOT)],
                   capture_output=True, env=env)
out = p.stdout.decode("utf-8", errors="replace")
err = p.stderr.decode("utf-8", errors="replace")
check("--dry-run with cp1252 piped output exits 0", p.returncode == 0, err.strip().splitlines()[-1:] if err else p.returncode)
check("no UnicodeEncodeError", "UnicodeEncodeError" not in err, err.strip().splitlines()[-1:])
check("the arrow is written as UTF-8", "→" in out, out[-200:])
check("the summary is printed to the end", "Global tooling install summary" in out and "skills would be installed" in out,
      out[-300:])

# an error path prints to stderr: still no crash with cp1252
p = subprocess.run([sys.executable, str(SCRIPT), "--tool", "cursor"], capture_output=True, env=env)
check("the cursor refusal exits 1 cleanly", p.returncode == 1 and b"Traceback" not in p.stderr,
      p.stderr.decode("utf-8", errors="replace")[-200:])

failed = [n for ok, n in results if not ok]
for ok, n in results:
    print(("PASS " if ok else "FAIL ") + n)
print(f"\n{len(results) - len(failed)}/{len(results)} passed")
sys.exit(1 if failed else 0)
