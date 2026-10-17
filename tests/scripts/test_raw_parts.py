#!/usr/bin/env python3
"""Checks for wiki-raw-parts.py, the splitter for raws too big for one reader. Never shipped.

    python tests/scripts/test_raw_parts.py    # exit 0 = every check passed

Task #163 idea A (2026-10-17): a raw too big for one worker is read in parts, one helper per
part. The parts must cover every line exactly once, in order, each within the size budget, and
follow the raw's headings where it has them, so the split is the same every run and auditable.
"""
from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "wiki-raw-parts.py"
spec = importlib.util.spec_from_file_location("raw_parts", SCRIPT)
rp = importlib.util.module_from_spec(spec)
spec.loader.exec_module(rp)

results: list[tuple[bool, str]] = []


def check(name: str, ok: bool, detail: object = ""):
    results.append((bool(ok), name + (f"  [{detail}]" if not ok and detail != "" else "")))


def covered(parts, n):
    return rp.check_coverage(parts, n) == []


tmp = Path(tempfile.mkdtemp(prefix="raw-parts-test-"))


def run(*args, env=None):
    p = subprocess.run([sys.executable, str(SCRIPT), *args], capture_output=True, env=env)
    return p.returncode, p.stdout.decode("utf-8", "replace"), p.stderr.decode("utf-8", "replace")


# 1. a small raw: one part, fits one worker
small = tmp / "small.md"
small.write_text("# Title\n\nSome text.\n\n## Section\n\nMore text.\n", encoding="utf-8")
code, out, err = run(str(small))
check("small raw exits 0", code == 0, err)
check("small raw is one part", "parts=1" in out, out)
check("small raw fits one worker", "fits_one_worker=yes" in out, out)

# 2. headings: whole sections joined up to the budget, a part starts at a heading
sec = "x" * 396 + "\n"            # 100 tokens a line
body = "".join(f"## Chapter {k}\n" + sec * 30 for k in range(10))   # ~3,000 tokens a chapter
lines = body.splitlines(keepends=True)
parts = rp.split(lines, max_tokens=7_000)
check("headings: every line covered once, in order", covered(parts, len(lines)), rp.check_coverage(parts, len(lines)))
check("headings: no part over the budget", all(p["tokens"] <= 7_000 for p in parts), [p["tokens"] for p in parts])
check("headings: chapters joined two to a part", len(parts) == 5, len(parts))
check("headings: each part starts at a heading", all(p["starts_with"].startswith("## Chapter") for p in parts),
      [p["starts_with"] for p in parts])
check("headings: split kind is heading", {p["split"] for p in parts} == {"heading"}, {p["split"] for p in parts})

# 3. one huge section with no headings (a transcript): windows, ending at blank lines
para = sec * 5 + "\n"             # 500 tokens + a blank line
trans = para * 100                # ~50,000 tokens, no headings
lines = trans.splitlines(keepends=True)
parts = rp.split(lines, max_tokens=8_000)
check("no headings: covered", covered(parts, len(lines)), rp.check_coverage(parts, len(lines)))
check("no headings: no part over the budget", all(p["tokens"] <= 8_000 for p in parts), [p["tokens"] for p in parts])
check("no headings: windows", {p["split"] for p in parts} == {"window"}, {p["split"] for p in parts})
check("no headings: every window but the last ends on a blank line",
      all(not lines[p["end_line"] - 1].strip() for p in parts[:-1]), [lines[p["end_line"] - 1][:10] for p in parts])
check("no headings: more than one part", len(parts) >= 6, len(parts))

# 4. no blank lines at all: windows cut at line ends, still covered and within budget
dense = sec * 400                 # 40,000 tokens, no blank line
lines = dense.splitlines(keepends=True)
parts = rp.split(lines, max_tokens=5_000)
check("no blank lines: covered", covered(parts, len(lines)), rp.check_coverage(parts, len(lines)))
check("no blank lines: within budget", all(p["tokens"] <= 5_000 for p in parts), [p["tokens"] for p in parts])

# 5. a single line bigger than a part: kept whole, flagged
huge = "short\n" + "y" * 40_000 + "\n" + "short\n"
lines = huge.splitlines(keepends=True)
parts = rp.split(lines, max_tokens=5_000)
check("oversized line: covered", covered(parts, len(lines)), rp.check_coverage(parts, len(lines)))
check("oversized line: flagged", any(p["split"] == "oversized" for p in parts), [p["split"] for p in parts])
f = tmp / "huge.md"
f.write_text(huge, encoding="utf-8")
code, out, _ = run(str(f), "--max-tokens", "5000")
check("oversized line: named in the printed index", "OVERSIZED" in out, out)

# 6. a mix: a big chapter between small ones; small ones still join, the big one is windowed
mixed = "## A\n" + sec * 10 + "## B\n" + (sec * 5 + "\n") * 30 + "## C\n" + sec * 10 + "## D\n" + sec * 10
lines = mixed.splitlines(keepends=True)
parts = rp.split(lines, max_tokens=4_000)
check("mixed: covered", covered(parts, len(lines)), rp.check_coverage(parts, len(lines)))
check("mixed: within budget", all(p["tokens"] <= 4_000 for p in parts), [p["tokens"] for p in parts])
check("mixed: C and D joined after B's windows", parts[-1]["starts_with"].startswith("## C"), [p["starts_with"] for p in parts])

# 7. the whole-raw verdict and JSON output
big = tmp / "big.md"
big.write_text(trans, encoding="utf-8")
code, out, err = run(str(big), "--json", "--fit-tokens", "20000", "--max-tokens", "8000")
data = json.loads(out) if code == 0 else {}
check("--json exits 0 and parses", code == 0 and "parts" in data, err)
check("--json: too big for one worker", data.get("fits_one_worker") is False, data.get("fits_one_worker"))
check("--json: parts cover every line", data and rp.check_coverage(data["parts"], data["lines"]) == [], data.get("lines"))
code, out, _ = run(str(big), "--fit-tokens", "100000")
check("same raw under a higher limit fits", "fits_one_worker=yes" in out, out[:200])

# 8. CRLF line ends, an empty file, a missing file, cp1252 pipes
crlf = tmp / "crlf.md"
crlf.write_bytes(b"# T\r\n\r\ntext\r\n## U\r\nmore\r\n")
code, out, _ = run(str(crlf))
check("CRLF raw: lines counted right", code == 0 and "lines=5" in out, out)
empty = tmp / "empty.md"
empty.write_text("", encoding="utf-8")
code, out, _ = run(str(empty))
check("empty raw: exits 0 with no parts", code == 0 and "parts=0" in out and "fits_one_worker=yes" in out, out)
code, _, err = run(str(tmp / "nope.md"))
check("missing raw: exit 2", code == 2 and "no such file" in err, (code, err))
code, _, err = run(str(small), "--max-tokens", "0")
check("zero budget: exit 2", code == 2, (code, err))
env = {k: v for k, v in os.environ.items() if k not in ("PYTHONIOENCODING", "PYTHONUTF8")}
env["PYTHONIOENCODING"] = "cp1252"
uni = tmp / "uni.md"
uni.write_text("# Café → naïve\n\ntext\n", encoding="utf-8")
code, out, err = run(str(uni), env=env)
check("cp1252 pipe: no crash on non-ASCII headings and the tokens sign",code == 0 and "Traceback" not in err, err[-200:])

failed = [n for ok, n in results if not ok]
for ok, n in results:
    print(("PASS " if ok else "FAIL ") + n)
print(f"\n{len(results) - len(failed)}/{len(results)} passed")
sys.exit(1 if failed else 0)
