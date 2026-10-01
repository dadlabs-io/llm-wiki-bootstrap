#!/usr/bin/env python3
"""Every shipped script that prints non-ASCII writes UTF-8 (task #61). Never shipped.

    python tests/scripts/test_utf8_output.py    # exit 0 = every check passed

Piped on Windows, Python's stdout is cp1252, which has no "→", "✓" or "—"; a
script that prints one crashes with UnicodeEncodeError, as wiki-upgrade.py did
partway through an install on 2026-10-01. The fix is the stream reconfigure at
the top of main(). This test finds every shipped command (scripts/*.py and
skills/*/scripts/*.py, not the _ helpers) whose print or write calls carry a
non-ASCII character and requires that line, so a new script cannot bring the
crash back. Then one real run: install-skill.py --dry-run under cp1252.
"""
from __future__ import annotations

import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parents[2]
results: list[tuple[bool, str]] = []


def check(name: str, ok: bool, detail: object = ""):
    results.append((bool(ok), name + (f"  [{detail}]" if not ok and detail != "" else "")))


PRINTS = re.compile(r"\b(print|_info|_ok|_warn|_err|_log|write)\(.*[^\x00-\x7f]")
RECONFIGURE = re.compile(r"reconfigure\(\s*encoding\s*=\s*[\"']utf-8[\"']")
commands = sorted(p for p in [*(ROOT / "scripts").glob("*.py"), *(ROOT / "skills").glob("*/scripts/*.py")]
                  if not p.name.startswith("_"))
check("found the shipped commands", len(commands) > 20, len(commands))
for p in commands:
    text = p.read_text(encoding="utf-8")
    if any(PRINTS.search(ln) for ln in text.splitlines()):
        check(f"{p.relative_to(ROOT).as_posix()} prints non-ASCII and writes UTF-8", bool(RECONFIGURE.search(text)))

# a real run: install-skill.py's dry run prints "→", with the output piped as cp1252
env = {k: v for k, v in os.environ.items() if k not in ("PYTHONIOENCODING", "PYTHONUTF8")}
env["PYTHONIOENCODING"] = "cp1252"
with tempfile.TemporaryDirectory() as tmp:
    r = subprocess.run([sys.executable, str(ROOT / "scripts" / "install-skill.py"), "--skill", "wiki", "--dry-run",
                        "--skills-dest", str(Path(tmp) / "skills"), "--scripts-dir", str(Path(tmp) / "ws")],
                       capture_output=True, env=env)
out = r.stdout.decode("utf-8", "replace")
err = r.stderr.decode("utf-8", "replace")
check("install-skill.py --dry-run under cp1252 exits 0", r.returncode == 0, err.strip().splitlines()[-1:])
check("install-skill.py writes the arrow as UTF-8", "→" in out, out[-200:])

failed = [n for ok, n in results if not ok]
for ok, n in results:
    print(("PASS " if ok else "FAIL ") + n)
print(f"\n{len(results) - len(failed)}/{len(results)} passed")
sys.exit(1 if failed else 0)
