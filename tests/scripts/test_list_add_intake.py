"""wiki-list-add.py's duplicate check also reads the intake buckets (task #109 (e), 2026-10-12).

Since /wiki-triage (2026-09-24) a queued ticket moves out of _inbox/pending/ into _inbox/intake/<bucket>/ until
its reader ingests it, but the queue's duplicate check read only pending/, proposed/, wiki/ and done/. So a source
already triaged into a bucket could be queued a second time. wiki-dequeue.py already reads the buckets (2026-10-03).

Run: uv run python tests/scripts/test_list_add_intake.py   (exit 0 = every check passed)
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[2] / "scripts"
results: list[tuple[str, bool, str]] = []


def check(name: str, ok: bool, detail: object = "") -> None:
    results.append((name, bool(ok), str(detail)))


with tempfile.TemporaryDirectory() as td:
    tmp = Path(td)
    nb = tmp / "notebooks" / "t"
    (nb / "wiki").mkdir(parents=True)
    (nb / "_inbox" / "pending").mkdir(parents=True)
    bucket = nb / "_inbox" / "intake" / "main"
    bucket.mkdir(parents=True)
    (nb / "_inbox" / "intake" / "README.md").write_text(
        "---\nbuckets:\n  - folder: main\n    purpose: everything\n    reader: t\n---\n# intake\n", encoding="utf-8")
    (bucket / "README.md").write_text("# main bucket\n\nSee https://example.com/not-a-ticket for nothing.\n", encoding="utf-8")
    (bucket / "3-a-post.md").write_text(
        "---\nsource: https://x.com/someone/status/1886192184808149383\npriority: 3\n---\n\n# a post\n", encoding="utf-8")
    (tmp / "linked-notebooks.json").write_text(json.dumps({"notebooks": {"t": {"root": "notebooks/t"}}}), encoding="utf-8")
    proj = tmp / "project"
    (proj / ".claude").mkdir(parents=True)
    (proj / ".claude" / "wiki-config.json").write_text(json.dumps(
        {"notebook": "t", "registry": (tmp / "linked-notebooks.json").as_posix()}), encoding="utf-8")
    env = {**os.environ, "PYTHONIOENCODING": "utf-8", "HOME": str(tmp), "USERPROFILE": str(tmp)}

    def run(*a: str) -> subprocess.CompletedProcess:
        return subprocess.run([sys.executable, str(SCRIPTS / "wiki-list-add.py"), *a], cwd=proj,
                              capture_output=True, text=True, encoding="utf-8", env=env)

    def queued() -> list[str]:
        return sorted(x.name for x in (nb / "_inbox" / "pending").glob("*.md") if not x.name.startswith("_"))

    p = run("--topic", "t", "--source", "https://twitter.com/someone/status/1886192184808149383?s=20")
    check("a source already triaged into a bucket (another link form) is not queued again",
          p.returncode == 0 and not queued(), (p.stdout + p.stderr)[-300:])
    check("the report names the bucket it was found in",
          "intake/main/" in p.stdout and "3-a-post.md" in p.stdout, p.stdout[-300:])
    p = run("--topic", "t", "--source", "https://example.com/not-a-ticket")
    check("a link that only appears in a bucket's README (no source: line) is still queued",
          p.returncode == 0 and len(queued()) == 1, (p.stdout + p.stderr)[-300:])
    p = run("--topic", "t", "--source", "https://www.youtube.com/watch?v=9bZkp7q19f0")
    check("a new source is queued", p.returncode == 0 and len(queued()) == 2, (p.stdout + p.stderr)[-300:])

for name, ok, detail in results:
    print(f"{'PASS' if ok else 'FAIL'}  {name}" + (f"  [{detail}]" if not ok and detail else ""))
passed = sum(ok for _, ok, _ in results)
print(f"\n{passed}/{len(results)} checks passed")
sys.exit(0 if passed == len(results) else 1)
