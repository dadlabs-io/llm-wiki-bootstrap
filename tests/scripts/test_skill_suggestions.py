"""Harness for the skill-suggestions scripts (moved from agent-builder's library, 2026-09-30).

Each script carries its own self-test (skill-suggestion.py: floor 34; suggestions.py: floor 53),
which agent-builder ran as its quality gate. This harness keeps that gate at full strength here:
it runs both self-tests and requires every assertion to pass at no fewer than the floor, then
proves the self-tests bite by running them against sabotaged copies of the scripts, each of
which must fail.

Run: python tests/scripts/test_skill_suggestions.py   (exit 0 = every check passed)
"""

from __future__ import annotations

import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
WRITER = REPO / "skills/writing-skill-suggestions/scripts/skill-suggestion.py"
IMPROVER = REPO / "skills/improving-skills-from-suggestions/scripts/suggestions.py"
FLOORS = {WRITER: 34, IMPROVER: 53}

# One sabotage per script behaviour the self-test must catch: (label, script, old, new).
SABOTAGE = [
    ("writer: duplicates no longer refused", WRITER,
     'return a.get("Skill") == b.get("Skill") and a.get("Issue", "").lower() == b.get("Issue", "").lower()',
     "return False"),
    ("writer: line breaks kept in a field", WRITER, "def one_line(value: str) -> str:\n",
     "def one_line(value: str) -> str:\n    return value\n"),
    ("improver: missing fields never reported", IMPROVER,
     "def missing_fields(fields: Dict[str, str]) -> List[str]:\n",
     "def missing_fields(fields: Dict[str, str]) -> List[str]:\n    return []\n"),
    ("improver: a re-sent suggestion never recognised", IMPROVER,
     "def same_suggestion(a: Dict[str, str], b: Dict[str, str]) -> bool:\n",
     "def same_suggestion(a: Dict[str, str], b: Dict[str, str]) -> bool:\n    return False\n"),
]

results: list[tuple[str, bool, str]] = []


def check(name: str, ok: bool, detail: str = "") -> None:
    results.append((name, bool(ok), detail))


def self_test(script: Path, cwd: Path | None = None) -> tuple[int, int, str]:
    """Run a script's --self-test; return (exit code, assertions reported, output tail)."""
    proc = subprocess.run([sys.executable, str(script), "--self-test"], capture_output=True, text=True,
                          encoding="utf-8", errors="replace", timeout=300, cwd=cwd)
    out = (proc.stdout or "") + (proc.stderr or "")
    m = re.search(r"\((\d+) assertions", out)
    return proc.returncode, int(m.group(1)) if m else 0, out.strip()[-200:]


for script, floor in FLOORS.items():
    code, n, tail = self_test(script)
    check(f"{script.name}: self-test passes", code == 0, tail)
    check(f"{script.name}: at least {floor} assertions", n >= floor, f"{n} reported")

for label, script, old, new in SABOTAGE:
    src = script.read_text(encoding="utf-8")
    if src.count(old) != 1:
        check(f"sabotage applies: {label}", False, "anchor not found once; update the harness")
        continue
    with tempfile.TemporaryDirectory() as tmp:
        # keep the script's folder shape (the improver reads ../templates/)
        root = Path(tmp) / script.parent.parent.name
        shutil.copytree(script.parent.parent, root, ignore=shutil.ignore_patterns("__pycache__", "wiki-seed"))
        broken = root / "scripts" / script.name
        broken.write_text(src.replace(old, new), encoding="utf-8")
        code, _, tail = self_test(broken)
        check(f"self-test catches: {label}", code != 0, tail)

for name, ok, detail in results:
    print(f"{'PASS' if ok else 'FAIL'}  {name}" + (f"  [{detail}]" if not ok and detail else ""))
passed = sum(ok for _, ok, _ in results)
print(f"\n{passed}/{len(results)} checks passed")
sys.exit(0 if passed == len(results) else 1)
