#!/usr/bin/env python3
"""Checks for bootstrap/scripts/wiki-cycle-scope.py (task #42: C1 scope, C3 checker). Never shipped.

    python tests/scripts/test_cycle_scope.py    # exit 0 = every check passed

A throwaway notebook in its own git repo, with commit dates set explicitly:
old entries committed 2026-09-01, a semantic lint on 2026-09-10, then on 2026-09-15 one
new entry, one entry re-reviewed (last_reviewed bumped) and one entry that only got a
machine edit (a backlink block). The scope must take the first two and not the third.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

SCRIPT = Path(os.environ.get("WIKI_SCOPE_SCRIPT") or
              Path(__file__).resolve().parents[2] / "bootstrap" / "scripts" / "wiki-cycle-scope.py")
results: list[tuple[bool, str]] = []


def check(name: str, ok: bool, detail: object = ""):
    results.append((bool(ok), name + (f"  [{detail}]" if not ok and detail != "" else "")))


def entry(title: str, reviewed: str, extra: str = "", raw: str = "") -> str:
    return (f"---\ntitle: \"{title}\"\ndate: 2026-09-01\ntier: 3\nconfidence: medium\nlast_reviewed: {reviewed}\n"
            f"review_after: 2026-11-01\ntags: [a, b, c]\n" + (f"raw_path: {raw}\n" if raw else "") +
            f"---\n\n# {title}\n\n## TL;DR\n\nBody.\n{extra}")


with tempfile.TemporaryDirectory() as td:
    tmp = Path(td)
    nb = tmp / "notebooks" / "t"
    w = nb / "wiki" / "research" / "tooling"
    w.mkdir(parents=True)
    (nb / "_inbox" / "proposed").mkdir(parents=True)
    (nb / "raw").mkdir()
    (tmp / "linked-notebooks.json").write_text(json.dumps({"notebooks": {"t": {"root": "notebooks/t"}}}),
                                               encoding="utf-8")
    proj = tmp / "project"
    (proj / ".claude").mkdir(parents=True)
    (proj / ".claude" / "wiki-config.json").write_text(json.dumps(
        {"notebook": "t", "registry": (tmp / "linked-notebooks.json").as_posix()}), encoding="utf-8")

    def git(*a, date=None):
        env = {**os.environ}
        if date:
            env.update(GIT_AUTHOR_DATE=date, GIT_COMMITTER_DATE=date)
        return subprocess.run(["git", "-C", str(tmp), *a], capture_output=True, text=True, env=env, check=True)

    def run(*a):
        return subprocess.run([sys.executable, str(SCRIPT), "--topic", "t", *a], cwd=proj, capture_output=True,
                              text=True, encoding="utf-8", env={**os.environ, "PYTHONIOENCODING": "utf-8"})

    git("init", "-q")
    git("config", "user.name", "t")
    git("config", "user.email", "t@example.com")
    for n in ("old-a", "old-b", "old-c"):
        (w / f"{n}.md").write_text(entry(n, "2026-09-01"), encoding="utf-8")
    (nb / "wiki" / "_MAP.md").write_text("# map\n", encoding="utf-8")
    (nb / "wiki" / "README.md").write_text("# readme\n", encoding="utf-8")
    (nb / "wiki" / "sessions").mkdir()
    (nb / "wiki" / "sessions" / "journal.md").write_text("# j\n", encoding="utf-8")
    git("add", "-A")
    git("commit", "-qm", "old", date="2026-09-01T10:00:00-04:00")
    lint_run = nb / "_inbox" / "reports" / "2026-09-10" / "2026-09-10-01"
    lint_run.mkdir(parents=True)
    (lint_run / "lint-semantic.json").write_text(json.dumps({"timestamp": "2026-09-10T12:00:00-04:00"}),
                                                 encoding="utf-8")
    git("add", "-A")
    git("commit", "-qm", "lint", date="2026-09-10T12:00:00-04:00")
    (w / "new-d.md").write_text(entry("new-d", "2026-09-15"), encoding="utf-8")
    (w / "old-a.md").write_text(entry("old-a", "2026-09-15", "\nA real correction.\n"), encoding="utf-8")
    (w / "old-b.md").write_text(entry("old-b", "2026-09-01",
                                      "\n<!-- BACKLINKS-AUTO START -->\n- [x](x.md)\n<!-- BACKLINKS-AUTO END -->\n"),
                                encoding="utf-8")
    git("add", "-A")
    git("commit", "-qm", "new", date="2026-09-15T09:00:00-04:00")
    (nb / "_inbox" / "proposed" / "staged-e.md").write_text(entry("staged-e", "2026-09-24", raw="raw/long.md"),
                                                            encoding="utf-8")
    run_folder = nb / "_inbox" / "reports" / "2026-09-24" / "2026-09-24-01"

    def scope(name):
        f = run_folder / name
        return [l for l in f.read_text(encoding="utf-8").splitlines() if l and not l.startswith("#")] if f.is_file() else None

    # ── semantic ──
    p = run("semantic", "--run-folder", str(run_folder))
    s = scope("semantic-scope.txt")
    check("semantic: exit 0", p.returncode == 0, p.stderr[-300:])
    check("semantic: the new entry is in scope", s and "wiki/research/tooling/new-d.md" in s, s)
    check("semantic: the re-reviewed entry is in scope", s and "wiki/research/tooling/old-a.md" in s, s)
    check("semantic: a machine-only edit is not", s and "wiki/research/tooling/old-b.md" not in s, s)
    check("semantic: an untouched entry is not", s and "wiki/research/tooling/old-c.md" not in s, s)
    check("semantic: this run's staged entry is in scope", s and "_inbox/proposed/staged-e.md" in s, s)
    check("semantic: machine files, README and sessions/ never", s is not None and not any(
        x.endswith(("_MAP.md", "README.md")) or "/sessions/" in x for x in s), s)
    check("semantic: says the cut-off", "2026-09-10T12:00:00-04:00" in p.stdout, p.stdout)
    p = run("semantic", "--run-folder", str(run_folder), "--all")
    s = scope("semantic-scope.txt")
    check("semantic --all: every entry + staged (5)", s is not None and len(s) == 5, s)

    # the lint in this run's own folder is not a cut-off; with no earlier lint, every entry
    (lint_run / "lint-semantic.json").unlink()
    p = run("semantic", "--run-folder", str(run_folder))
    check("semantic with no earlier lint: every entry, and says so",
          len(scope("semantic-scope.txt") or []) == 5 and "no earlier semantic lint" in p.stdout, p.stdout)

    # ── claims ──
    p = run("claims", "--run-folder", str(run_folder))
    check("claims with no index: every entry", len(scope("claims-scope.txt") or []) == 5 and "no claims index" in p.stdout,
          p.stdout)
    idx = nb / "_inbox" / "claims-index.json"
    idx.write_text(json.dumps({"generated": "2026-08-01", "claims": [
        {"source_entry": "research/tooling/old-a.md"}, {"source_entry": "research/tooling/old-b.md"},
        {"source_entry": "research/tooling/old-c.md"}]}), encoding="utf-8")
    git("add", "-A")
    git("commit", "-qm", "index", date="2026-09-12T09:00:00-04:00")
    p = run("claims", "--run-folder", str(run_folder))
    c = scope("claims-scope.txt")
    check("claims: exit 0", p.returncode == 0, p.stderr[-300:])
    check("claims: the entry with no claims is in scope", c and "wiki/research/tooling/new-d.md" in c, c)
    check("claims: the entry revised after the index was written", c and "wiki/research/tooling/old-a.md" in c, c)
    check("claims: a machine-only edit is not", c and "wiki/research/tooling/old-b.md" not in c, c)
    check("claims: an indexed, untouched entry is not", c and "wiki/research/tooling/old-c.md" not in c, c)
    check("claims: the staged entry is in scope", c and "_inbox/proposed/staged-e.md" in c, c)

    # ── checker ──
    def raw(name, kind, secs):
        (nb / "raw" / name).write_text(f"---\ntype: {kind}\nduration_seconds: {secs}\n---\n\ntext\n", encoding="utf-8")
    raw("long.md", "youtube-transcript", 20 * 60)
    raw("short.md", "youtube-transcript", 10 * 60)
    raw("article.md", "article", 99 * 60)
    (nb / "_inbox" / "proposed" / "short-f.md").write_text(entry("short-f", "2026-09-24", raw="raw/short.md"), encoding="utf-8")
    (nb / "_inbox" / "proposed" / "article-g.md").write_text(entry("article-g", "2026-09-24", raw="raw/article.md"), encoding="utf-8")
    (nb / "_inbox" / "proposed" / "noraw-h.md").write_text(entry("noraw-h", "2026-09-24"), encoding="utf-8")
    p = run("checker", "--run-folder", str(run_folder), "--min-minutes", "15")
    k = scope("checker-scope.txt") or []
    check("checker: exit 0", p.returncode == 0, p.stderr[-300:])
    check("checker: only the 20-minute transcript at 15", [l.split("\t")[0] for l in k] == ["_inbox/proposed/staged-e.md"], k)
    check("checker: its raw and minutes recorded", k and k[0].split("\t")[1:] == ["raw/long.md", "20"], k)
    p = run("checker", "--run-folder", str(run_folder), "--min-minutes", "5")
    k = scope("checker-scope.txt") or []
    check("checker at 5 minutes: both transcripts, never the article or a raw-less entry",
          sorted(l.split("\t")[0] for l in k) == ["_inbox/proposed/short-f.md", "_inbox/proposed/staged-e.md"], k)

    p = run("checker", "--run-folder", str(run_folder), "--min-minutes", "999")
    f = run_folder / "checker-scope.txt"
    check("checker with nothing in scope: the file is not zero bytes (a header line)",
          f.is_file() and f.stat().st_size > 0 and scope("checker-scope.txt") == [], f.read_text(encoding="utf-8") if f.is_file() else "missing")

    # ── checker-log ──
    rep = tmp / "rep.json"
    rep.write_text(json.dumps({"source_minutes": 20, "model": "opus", "unsupported_claims": [{"x": 1}, {"x": 2}],
                               "skipped_sections": [{"x": 1}], "misquotes": []}), encoding="utf-8")
    p = run("checker-log", "--run-folder", str(run_folder), "--entry", "staged-e", "--report", str(rep))
    log = nb / "_inbox" / "reports" / "checker-log.jsonl"
    rows = [json.loads(l) for l in log.read_text(encoding="utf-8").splitlines()] if log.is_file() else []
    check("checker-log: one row with counts, minutes, model and a fix verdict",
          len(rows) == 1 and rows[0]["unsupported_claims"] == 2 and rows[0]["skipped_sections"] == 1
          and rows[0]["misquotes"] == 0 and rows[0]["source_minutes"] == 20 and rows[0]["model"] == "opus"
          and rows[0]["verdict"] == "fix" and rows[0]["cycle"] == "2026-09-24-01", rows)
    rep.write_text(json.dumps({"source_minutes": 30, "model": "opus"}), encoding="utf-8")
    run("checker-log", "--run-folder", str(run_folder), "--entry", "clean", "--report", str(rep))
    rows = [json.loads(l) for l in log.read_text(encoding="utf-8").splitlines()]
    check("checker-log: a report with no findings is a pass, appended", len(rows) == 2 and rows[1]["verdict"] == "pass", rows)

failed = [n for ok, n in results if not ok]
for ok, n in results:
    print(("PASS " if ok else "FAIL ") + n)
print(f"\n{len(results) - len(failed)}/{len(results)} passed")
sys.exit(1 if failed else 0)
