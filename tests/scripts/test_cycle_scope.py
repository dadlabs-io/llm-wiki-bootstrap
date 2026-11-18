#!/usr/bin/env python3
"""Checks for scripts/wiki-cycle-scope.py (task #42: C1 scope, C3 checker). Never shipped.

    python tests/scripts/test_cycle_scope.py    # exit 0 = every check passed

A throwaway notebook in its own git repo, with commit dates set explicitly:
old entries committed 2026-09-01, a semantic lint on 2026-09-10, then on 2026-09-15 one
new entry, one entry re-reviewed (last_reviewed bumped) and one entry that only got a
machine edit (a backlink block). The scope must take the first two and not the third.
"""
from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

SCRIPT = Path(os.environ.get("WIKI_SCOPE_SCRIPT") or
              Path(__file__).resolve().parents[2] / "scripts" / "wiki-cycle-scope.py")
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
    check("claims with no index: every entry, not the staged one (task #184)",
          len(scope("claims-scope.txt") or []) == 4 and "no claims index" in p.stdout,
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
    # task #184 (Mark's OK, 2026-10-19): an entry still staged at the claims step waits for the user or was held by
    # the checker, so its claims wait until it is promoted
    check("claims: a staged entry is not in scope", c is not None and "_inbox/proposed/staged-e.md" not in c, c)

    # ── checker ──
    def raw(name, kind, secs):
        (nb / "raw" / name).write_text(f"---\ntype: {kind}\nduration_seconds: {secs}\n---\n\ntext\n", encoding="utf-8")
    raw("long.md", "youtube-transcript", 20 * 60)
    raw("short.md", "youtube-transcript", 10 * 60)
    raw("article.md", "article", 99 * 60)
    raw("whisper.md", "media-transcript", 1802)  # wiki-transcribe.py's raw (task #105: cycle 2026-10-11-01 missed one)
    (nb / "_inbox" / "proposed" / "whisper-i.md").write_text(entry("whisper-i", "2026-09-24", raw="raw/whisper.md"), encoding="utf-8")
    (nb / "_inbox" / "proposed" / "short-f.md").write_text(entry("short-f", "2026-09-24", raw="raw/short.md"), encoding="utf-8")
    (nb / "_inbox" / "proposed" / "article-g.md").write_text(entry("article-g", "2026-09-24", raw="raw/article.md"), encoding="utf-8")
    (nb / "_inbox" / "proposed" / "noraw-h.md").write_text(entry("noraw-h", "2026-09-24"), encoding="utf-8")
    p = run("checker", "--run-folder", str(run_folder), "--min-minutes", "15", "--sample-every", "0", "--min-raw-kb", "0")
    k = scope("checker-scope.txt") or []
    check("checker: exit 0", p.returncode == 0, p.stderr[-300:])
    check("checker: only the 20-minute YouTube and the 30-minute Whisper transcript at 15",
          sorted(l.split("\t")[0] for l in k) == ["_inbox/proposed/staged-e.md", "_inbox/proposed/whisper-i.md"], k)
    rows = {l.split("\t")[0]: l.split("\t")[1:] for l in k}
    check("checker: its raw and minutes recorded", rows.get("_inbox/proposed/staged-e.md") == ["raw/long.md", "20"], k)
    check("checker #105: a Whisper transcript's raw and minutes recorded",
          rows.get("_inbox/proposed/whisper-i.md") == ["raw/whisper.md", "30"], k)
    p = run("checker", "--run-folder", str(run_folder), "--min-minutes", "5", "--sample-every", "0", "--min-raw-kb", "0")
    k = scope("checker-scope.txt") or []
    check("checker at 5 minutes: every transcript, never the article (a page, Mark 2026-10-12) or a raw-less entry",
          sorted(l.split("\t")[0] for l in k) == ["_inbox/proposed/short-f.md", "_inbox/proposed/staged-e.md",
                                                   "_inbox/proposed/whisper-i.md"], k)

    p = run("checker", "--run-folder", str(run_folder), "--min-minutes", "999", "--sample-every", "0", "--min-raw-kb", "0")
    f = run_folder / "checker-scope.txt"
    check("checker with nothing in scope: the file is not zero bytes (a header line)",
          f.is_file() and f.stat().st_size > 0 and scope("checker-scope.txt") == [], f.read_text(encoding="utf-8") if f.is_file() else "missing")


    # ── checker beyond transcripts (task #202, Mark 2026-10-23): a big raw (min_raw_kb) and a spot check of 1 in N ──
    (nb / "raw" / "big.md").write_text("---\ntype: repo\n---\n\n" + "word " * 14000, encoding="utf-8")  # ~70 KB
    (nb / "_inbox" / "proposed" / "big-j.md").write_text(entry("big-j", "2026-09-24", raw="raw/big.md"), encoding="utf-8")
    p = run("checker", "--run-folder", str(run_folder), "--min-minutes", "15", "--min-raw-kb", "60", "--sample-every", "0")
    k = scope("checker-scope.txt") or []
    rows = {l.split(chr(9))[0]: l.split(chr(9))[1:] for l in k}
    check("checker #202: a raw of 60+ KB is checked, its minutes '-', its size printed as the reason",
          rows.get("_inbox/proposed/big-j.md") == ["raw/big.md", "-"]
          and any("big-j.md" in l and "KB)" in l for l in p.stdout.splitlines()), (k, p.stdout))
    check("checker #202: a transcript keeps its columns and the printed reason says transcript",
          rows.get("_inbox/proposed/staged-e.md") == ["raw/long.md", "20"]
          and any("staged-e.md" in l and "(transcript of 20 minutes)" in l for l in p.stdout.splitlines()), p.stdout)
    check("checker #202: a small article is not picked without the spot check", "_inbox/proposed/article-g.md" not in rows, k)
    p = run("checker", "--run-folder", str(run_folder), "--min-minutes", "15", "--min-raw-kb", "60", "--sample-every", "1")
    k = scope("checker-scope.txt") or []
    rows = {l.split(chr(9))[0]: l.split(chr(9))[1:] for l in k}
    check("checker #202: the spot check (1 in 1) takes every other entry with a raw, printed as a spot check",
          "_inbox/proposed/article-g.md" in rows and "_inbox/proposed/short-f.md" in rows
          and any("article-g.md" in l and "spot check, 1 in 1" in l for l in p.stdout.splitlines()), (k, p.stdout))
    check("checker #202: an entry with no raw is never picked", "_inbox/proposed/noraw-h.md" not in rows, k)
    first = sorted(k)
    run("checker", "--run-folder", str(run_folder), "--min-minutes", "15", "--min-raw-kb", "60", "--sample-every", "3")
    once = sorted(scope("checker-scope.txt") or [])
    run("checker", "--run-folder", str(run_folder), "--min-minutes", "15", "--min-raw-kb", "60", "--sample-every", "3")
    check("checker #202: the spot check picks the same entries every time (a resumed run agrees)",
          once == sorted(scope("checker-scope.txt") or []), once)
    run("checker", "--run-folder", str(run_folder), "--min-minutes", "15", "--min-raw-kb", "60", "--sample-every", "1000")
    check("checker #202: a sparser spot check picks fewer", len(scope("checker-scope.txt") or []) < len(first), first)
    (nb / "_inbox" / "proposed" / "big-j.md").unlink()

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
    # 2026-10-15, task #151: the fourth list, vague passages, is counted and alone makes a fix
    rep.write_text(json.dumps({"source_minutes": 25, "model": "opus", "vague_passages": [{"x": 1}, {"x": 2}, {"x": 3}]}),
                   encoding="utf-8")
    run("checker-log", "--run-folder", str(run_folder), "--entry", "vague", "--report", str(rep))
    rows = [json.loads(l) for l in log.read_text(encoding="utf-8").splitlines()]
    check("checker-log: vague passages counted, and with no other finding the verdict is fix",
          len(rows) == 3 and rows[2].get("vague_passages") == 3 and rows[2]["verdict"] == "fix", rows[-1:])

    # ── models (task #99: the cycle spawns from the setting files, not from a default it assumes) ──
    cfg = tmp / "cfg"
    cfg.mkdir()
    (cfg / "ing.json").write_text(json.dumps({"model_default": "haiku", "confirm_model_each_run": True}), encoding="utf-8")
    (cfg / "chk.json").write_text(json.dumps({"model_default": "fable"}), encoding="utf-8")
    (cfg / "help.json").write_text(json.dumps({"semantic_lint": "opus", "lint_fixes": "sonnet"}), encoding="utf-8")

    def models(**paths):
        args = ["models", "--run-folder", str(run_folder)]
        for k in ("ingester", "checker", "helpers"):
            args += [f"--{k}", str(paths.get(k, cfg / "none.json"))]
        p = run(*args)
        f = run_folder / "models.json"
        return p, (json.loads(f.read_text(encoding="utf-8")) if f.is_file() else {})

    p, m = models(ingester=cfg / "ing.json", checker=cfg / "chk.json", helpers=cfg / "help.json")
    r = m.get("roles", {})
    check("models: exit 0", p.returncode == 0, p.stderr[-300:])
    check("models: each role from its file, a non-default value kept",
          [r.get(k, {}).get("model") for k in ("ingest_workers", "checker", "semantic_lint", "lint_fixes")]
          == ["haiku", "fable", "opus", "sonnet"], r)
    check("models: a role the helpers file leaves out falls back, and says so",
          r.get("synthesis", {}).get("model") == "sonnet" and r.get("synthesis", {}).get("from") == "fallback", r)
    check("models: the ask-each-run flag is printed", "ingest workers: haiku (ask the user" in p.stdout, p.stdout)
    check("models: no problem with every file present", m.get("problems") == [], m.get("problems"))
    p, m = models(ingester=cfg / "ing.json", checker=cfg / "chk.json")
    check("models: a missing file is named as a warning, its roles on the fallback",
          "warning:" in p.stdout and "none.json: missing" in p.stdout
          and m["roles"]["semantic_lint"]["model"] == "sonnet" and len(m["problems"]) == 1, p.stdout)
    (cfg / "bad.json").write_text('{"model_default": "opus",}', encoding="utf-8")
    p, m = models(ingester=cfg / "bad.json", checker=cfg / "chk.json", helpers=cfg / "help.json")
    check("models: an unreadable file is named, never a crash",
          p.returncode == 0 and "bad.json: unreadable" in p.stdout and m["roles"]["ingest_workers"]["model"] == "sonnet",
          p.stdout + p.stderr[-200:])

    # ── writer by raw size (task #239, Mark 2026-11-09: Sonnet writes a raw under 10 KB, Opus one of 10 KB or more) ──
    (cfg / "ing-size.json").write_text(json.dumps({"model_default": "sonnet", "large_raw_kb": 10,
                                                   "large_raw_model": "opus"}), encoding="utf-8")
    p, m = models(ingester=cfg / "ing-size.json", checker=cfg / "chk.json", helpers=cfg / "help.json")
    w = m.get("roles", {}).get("ingest_workers", {})
    check("models #239: the size line is recorded and printed",
          w.get("large_raw_kb") == 10 and w.get("large_raw_model") == "opus"
          and "ingest workers: sonnet; opus for a raw of 10 KB or more" in p.stdout, (w, p.stdout))
    p, m = models(ingester=cfg / "ing.json", checker=cfg / "chk.json", helpers=cfg / "help.json")
    w = m.get("roles", {}).get("ingest_workers", {})
    check("models #239: a file without the size line falls back to 10 KB and opus",
          w.get("large_raw_kb") == 10 and w.get("large_raw_model") == "opus", w)
    (nb / "raw" / "small.md").write_text("x" * (9 * 1024), encoding="utf-8")
    (nb / "raw" / "edge.md").write_text("x" * (10 * 1024), encoding="utf-8")
    p = run("writer", "--ingester", str(cfg / "ing-size.json"), str(nb / "raw" / "small.md"), str(nb / "raw" / "edge.md"),
            str(nb / "raw" / "missing.md"))
    rows = {Path(l.split("\t")[0]).name: l.split("\t")[1:] for l in p.stdout.splitlines() if "\t" in l}
    check("writer #239: a 9 KB raw goes to the default model", rows.get("small.md") == ["9", "sonnet"], p.stdout)
    check("writer #239: a raw of exactly 10 KB goes to opus", rows.get("edge.md") == ["10", "opus"], p.stdout)
    check("writer #239: a missing raw is named and the exit is 1",
          p.returncode == 1 and "missing.md" in (p.stdout + p.stderr), (p.returncode, p.stdout, p.stderr))

    # ── cost (task #138: the status line's session total at the start and end of a run) ──
    sc = tmp / "session-cost"
    sc.mkdir()

    def cost(mark, folder=run_folder):
        return subprocess.run([sys.executable, str(SCRIPT), "--topic", "t", "cost", "--run-folder", str(folder),
                               "--mark", mark], cwd=proj, capture_output=True, text=True, encoding="utf-8",
                              env={**os.environ, "PYTHONIOENCODING": "utf-8", "WIKI_SESSION_COST_DIR": str(sc)})

    def session(sid, cwd, usd, updated):
        (sc / f"{sid}.json").write_text(json.dumps({"session_id": sid, "cwd": str(cwd), "total_cost_usd": usd,
                                                    "updated": updated}), encoding="utf-8")

    p = cost("start")
    check("cost: no session file is NOT checked (exit 3), never a zero",
          p.returncode == 3 and "NOT checked" in p.stdout
          and json.loads((run_folder / "cost.json").read_text(encoding="utf-8"))["status"] == "not_checked", p.stdout)
    session("other", tmp / "elsewhere", 50.0, "2026-10-14T23:00:00Z")
    session("old", proj, 10.0, "2026-10-14T20:00:00Z")
    session("this", proj, 12.5, "2026-10-14T22:00:00Z")
    p = cost("start")
    rec = json.loads((run_folder / "cost.json").read_text(encoding="utf-8"))
    check("cost start: the newest session in this folder, not another folder's",
          p.returncode == 0 and rec.get("session_id") == "this" and rec.get("start_usd") == 12.5, (p.stdout, rec))
    session("this", proj, 20.25, "2026-10-14T23:30:00Z")
    session("newer", proj, 99.0, "2026-10-14T23:31:00Z")
    p = cost("end")
    rec = json.loads((run_folder / "cost.json").read_text(encoding="utf-8"))
    check("cost end: the start's session is read again (not a newer one), the difference recorded",
          p.returncode == 0 and rec.get("run_usd") == 7.75 and rec.get("status") == "completed"
          and "$7.75" in (run_folder / "cost.md").read_text(encoding="utf-8"), (p.stdout, rec))
    p = cost("end", folder=tmp / "fresh-run")
    check("cost end with no start mark: NOT checked", p.returncode == 3 and "no start mark" in p.stdout, p.stdout)

    # ── session-cost (task #182 row 34: /wrap-up's cost line, the session's running total, no run folder) ──
    def session_cost(*a):
        return subprocess.run([sys.executable, str(SCRIPT), "--topic", "t", "session-cost", *a], cwd=proj,
                              capture_output=True, text=True, encoding="utf-8",
                              env={**os.environ, "PYTHONIOENCODING": "utf-8", "WIKI_SESSION_COST_DIR": str(sc)})
    p = session_cost("--session-id", "this")
    check("session-cost: the named session's running total, said to be an estimate",
          p.returncode == 0 and "$20.25" in p.stdout and "estimate" in p.stdout, (p.returncode, p.stdout, p.stderr[-200:]))
    p = session_cost()
    check("session-cost with no id: the newest session in this folder", p.returncode == 0 and "$99.00" in p.stdout, p.stdout)
    p = session_cost("--session-id", "nobody")
    check("session-cost for a session with no file: NOT checked (exit 3), never a zero",
          p.returncode == 3 and "NOT checked" in p.stdout and "$0" not in p.stdout, p.stdout)

    # ── unfinished (task #240, lesson #10): Step 0 names an earlier run folder that has no report ──
    reports = nb / "_inbox" / "reports"
    cur = reports / "2026-11-20" / "2026-11-20-01"

    def mkrun(cid, scratch=None, report=False):
        d = reports / cid[:10] / cid
        d.mkdir(parents=True, exist_ok=True)
        (d / "semantic-scope.txt").write_text("# a step file\n", encoding="utf-8")
        if scratch is not None:
            (d / "scratchpad.md").write_text(
                f"# Cycle Run — {cid[:10]}\n\n**Status**: {scratch}\n**Cycle**: {cid}\n\n## Decisions log\n"
                "- 2026-10-01T10:00:00-04:00 — started\n", encoding="utf-8")
        if report:
            (d / f"{cid}-run-cycle-report.md").write_text("# report\n", encoding="utf-8")
        return d

    mkrun("2026-10-01-01")                                # steps run by hand: no scratchpad, no report
    mkrun("2026-10-02-01", scratch="in_progress")
    mkrun("2026-10-03-01", scratch="completed", report=True)
    mkrun("2026-10-04-01", scratch="interrupted")
    (reports / "2026-10-05" / "checker").mkdir(parents=True)
    (reports / "2026-10-05" / "checker" / "x.json").write_text("{}", encoding="utf-8")
    mkrun("2026-11-20-01")                                # the current run: no report yet, never named

    def unfinished_names_runs_without_report():
        p = run("unfinished", "--run-folder", str(cur))
        lines = [l for l in p.stdout.splitlines() if l.startswith("unfinished: ")]
        ids = [l.split()[1] for l in lines]
        by = dict(zip(ids, lines))
        # the first two are the lint run and the run folder the sections above used: no report either
        check("unfinished_names_runs_without_report: exit 0, exactly the four unfinished folders, oldest first",
              p.returncode == 0 and ids == ["2026-09-10-01", "2026-09-24-01", "2026-10-01-01", "2026-10-02-01"],
              (p.returncode, p.stdout, p.stderr[-200:]))
        check("unfinished_names_runs_without_report: a folder with no scratchpad says so",
              "no scratchpad" in by.get("2026-10-01-01", ""), by)
        check("unfinished_names_runs_without_report: an in_progress scratchpad says so",
              "scratchpad says in_progress" in by.get("2026-10-02-01", ""), by)
        check("unfinished_names_runs_without_report: each line gives the close-out",
              bool(ids) and all(f'wiki-cycle-scope.py --topic t unfinished --mark-interrupted {i} --reason "' in by[i]
                                for i in ids), by)
        # Mark's ruling: resume only for a folder with a scratchpad; nothing in one without can be resumed
        check("unfinished_names_runs_without_report: resume is offered for the in_progress folder only",
              bool(ids) and all((f"/wiki-cycle t --resume {i}" in by[i]) == (i == "2026-10-02-01") for i in ids), by)
        f = cur / "unfinished-runs.txt"
        rows = ([l.split("\t") for l in f.read_text(encoding="utf-8").splitlines() if l and not l.startswith("#")]
                if f.is_file() else None)
        check("unfinished_names_runs_without_report: unfinished-runs.txt lists each folder and its why",
              rows is not None and [r[0] for r in rows] == ids
              and all(len(r) == 2 for r in rows) and "no scratchpad" in rows[2][1] and "in_progress" in rows[3][1],
              (rows, p.stdout))
    unfinished_names_runs_without_report()

    def unfinished_none_case():
        for cid in ("2026-09-10-01", "2026-09-24-01", "2026-10-01-01", "2026-10-02-01"):
            (reports / cid[:10] / cid / f"{cid}-run-cycle-report.md").write_text("# report\n", encoding="utf-8")
        p = run("unfinished", "--run-folder", str(cur))
        f = cur / "unfinished-runs.txt"
        text = f.read_text(encoding="utf-8") if f.is_file() else ""
        check("unfinished_none_case: the one line 'unfinished: none', exit 0",
              p.returncode == 0 and p.stdout.strip() == "unfinished: none", (p.returncode, p.stdout, p.stderr[-200:]))
        check("unfinished_none_case: the file holds only its header line, not zero bytes",
              len(text.splitlines()) == 1 and text.startswith("#"), repr(text))
    unfinished_none_case()

    def unfinished_skips_a_folder_filed_under_another_date():
        # a run id is filed under its own date; a folder elsewhere is one the close-out would refuse, so it is not listed
        misfiled = reports / "2026-10-14" / "2026-10-15-01"
        misfiled.mkdir(parents=True)
        p = run("unfinished", "--run-folder", str(cur))
        shutil.rmtree(misfiled.parent)
        check("unfinished_skips_a_folder_filed_under_another_date: not named, the listing stays 'unfinished: none'",
              p.returncode == 0 and p.stdout.strip() == "unfinished: none", (p.returncode, p.stdout, p.stderr[-200:]))
    unfinished_skips_a_folder_filed_under_another_date()

    def unfinished_skips_a_file_named_like_a_run():
        # only a folder is a run; a stray file with a run id's name has no report to look for
        stray = reports / "2026-10-16" / "2026-10-16-01"
        stray.parent.mkdir(parents=True)
        stray.write_text("not a run folder\n", encoding="utf-8")
        p = run("unfinished", "--run-folder", str(cur))
        shutil.rmtree(stray.parent)
        check("unfinished_skips_a_file_named_like_a_run: not named, the listing stays 'unfinished: none'",
              p.returncode == 0 and p.stdout.strip() == "unfinished: none", (p.returncode, p.stdout, p.stderr[-200:]))
    unfinished_skips_a_file_named_like_a_run()

    def unfinished_without_a_reports_folder():
        away = nb / "_inbox" / "reports-away"
        reports.rename(away)
        elsewhere = tmp / "rf-no-reports"
        p = run("unfinished", "--run-folder", str(elsewhere))
        made = reports.exists()
        wrote = sorted(x.name for x in elsewhere.iterdir()) if elsewhere.is_dir() else None
        if made:
            shutil.rmtree(reports)    # whatever the script made, so the real folder can come back
        away.rename(reports)
        check("unfinished_without_a_reports_folder: exit 0 and 'unfinished: none'",
              p.returncode == 0 and p.stdout.strip() == "unfinished: none", (p.returncode, p.stdout, p.stderr[-200:]))
        check("unfinished_without_a_reports_folder: nothing created outside the run folder",
              not made and wrote == ["unfinished-runs.txt"], (made, wrote))
    unfinished_without_a_reports_folder()

    def mark_interrupted_closes_a_scratchpad_run():
        d = mkrun("2026-10-06-01", scratch="in_progress")
        before = run("unfinished", "--run-folder", str(cur))
        p = run("unfinished", "--mark-interrupted", "2026-10-06-01", "--reason", "died at ingest")
        pad = (d / "scratchpad.md").read_text(encoding="utf-8")
        head, _, log = pad.partition("## Decisions log")
        after = run("unfinished", "--run-folder", str(cur))
        check("mark_interrupted_closes_a_scratchpad_run: the folder was named before, exit 0 now",
              "unfinished: 2026-10-06-01 " in before.stdout and p.returncode == 0, (before.stdout, p.returncode, p.stderr[-200:]))
        check("mark_interrupted_closes_a_scratchpad_run: the Status line says interrupted, in_progress is gone",
              "**Status**: interrupted" in head and "in_progress" not in pad, pad)
        check("mark_interrupted_closes_a_scratchpad_run: the reason is appended under the Decisions log, the old line kept",
              any(l.startswith("- ") and l.endswith("— marked interrupted: died at ingest") for l in log.splitlines())
              and "- 2026-10-01T10:00:00-04:00 — started" in log, pad)
        check("mark_interrupted_closes_a_scratchpad_run: the next unfinished run leaves it out",
              "2026-10-06-01" not in after.stdout, after.stdout)
    mark_interrupted_closes_a_scratchpad_run()

    def mark_interrupted_puts_the_reason_inside_the_log_section():
        # a real scratchpad's Decisions log is followed by "## Unresolved for next run" (skills/wiki-cycle/reference.md)
        d = mkrun("2026-10-07-02", scratch="in_progress")
        pad = d / "scratchpad.md"
        pad.write_text(pad.read_text(encoding="utf-8") + "\n## Unresolved for next run\n- the checker report\n",
                       encoding="utf-8")
        p = run("unfinished", "--mark-interrupted", "2026-10-07-02", "--reason", "laptop closed")
        lines = pad.read_text(encoding="utf-8").splitlines()
        at = next((i for i, l in enumerate(lines) if l.endswith("marked interrupted: laptop closed")), -1)
        log = lines.index("## Decisions log")
        nxt = lines.index("## Unresolved for next run")
        check("mark_interrupted_puts_the_reason_inside_the_log_section: the line sits between the log heading and the next section",
              p.returncode == 0 and log < at < nxt, (p.returncode, p.stderr[-200:], lines))
        check("mark_interrupted_puts_the_reason_inside_the_log_section: the next section keeps its own line",
              lines[nxt + 1:] == ["- the checker report"], lines)
    mark_interrupted_puts_the_reason_inside_the_log_section()

    def mark_interrupted_writes_a_scratchpad_for_a_run_with_none():
        d = mkrun("2026-10-08-01")
        p = run("unfinished", "--mark-interrupted", "2026-10-08-01", "--reason", "run by hand, never reported")
        pad = d / "scratchpad.md"
        lines = pad.read_text(encoding="utf-8").splitlines() if pad.is_file() else []
        after = run("unfinished", "--run-folder", str(cur))
        check("mark_interrupted_writes_a_scratchpad_for_a_run_with_none: exit 0, a scratchpad with the title and the status",
              p.returncode == 0 and lines[:1] == ["# Cycle Run — 2026-10-08"] and "**Status**: interrupted" in lines,
              (p.returncode, p.stderr[-200:], lines))
        check("mark_interrupted_writes_a_scratchpad_for_a_run_with_none: the reason sits under a Decisions log heading",
              "## Decisions log" in lines and lines[-1].endswith("— marked interrupted: run by hand, never reported")
              and lines.index("## Decisions log") < len(lines) - 1, lines)
        check("mark_interrupted_writes_a_scratchpad_for_a_run_with_none: the next unfinished run leaves it out",
              "2026-10-08-01" not in after.stdout, after.stdout)
    mark_interrupted_writes_a_scratchpad_for_a_run_with_none()

    def mark_interrupted_adds_the_log_heading_when_missing():
        d = mkrun("2026-10-09-01")
        pad = d / "scratchpad.md"
        pad.write_text("# Cycle Run — 2026-10-09\n\n**Status**: in_progress\n", encoding="utf-8")
        p = run("unfinished", "--mark-interrupted", "2026-10-09-01", "--reason", "no log yet")
        lines = pad.read_text(encoding="utf-8").splitlines()
        check("mark_interrupted_adds_the_log_heading_when_missing: exit 0, status closed, heading added with the reason below it",
              p.returncode == 0 and "**Status**: interrupted" in lines and "## Decisions log" in lines
              and lines[-1].endswith("— marked interrupted: no log yet")
              and lines.index("## Decisions log") == len(lines) - 2, (p.returncode, p.stderr[-200:], lines))
    mark_interrupted_adds_the_log_heading_when_missing()

    def mark_interrupted_adds_no_second_heading_when_the_log_heading_ends_the_file():
        d = mkrun("2026-10-13-01")
        pad = d / "scratchpad.md"
        pad.write_bytes(b"# Cycle Run - 2026-10-13\n\n**Status**: in_progress\n\n## Decisions log")
        p = run("unfinished", "--mark-interrupted", "2026-10-13-01", "--reason", "heading last, no newline")
        lines = pad.read_text(encoding="utf-8").splitlines()
        check("mark_interrupted_adds_no_second_heading_when_the_log_heading_ends_the_file: exit 0, one heading, "
              "the reason on the line below it",
              p.returncode == 0 and lines.count("## Decisions log") == 1
              and lines[-1].endswith("— marked interrupted: heading last, no newline")
              and lines.index("## Decisions log") == len(lines) - 2, (p.returncode, p.stderr[-200:], lines))
    mark_interrupted_adds_no_second_heading_when_the_log_heading_ends_the_file()

    def tree(root):
        return {p.relative_to(root).as_posix(): (p.read_bytes() if p.is_file() else None) for p in root.rglob("*")}

    def mark_interrupted_refuses_an_unknown_run():
        before = tree(nb)
        for bad in ("2026-12-31-01", "not-a-run", "../../../wiki"):
            p = run("unfinished", "--mark-interrupted", bad, "--reason", "x")
            check(f"mark_interrupted_refuses_an_unknown_run: {bad!r} exits 2 and the error names it",
                  p.returncode == 2 and bad in p.stderr, (p.returncode, p.stdout, p.stderr[-300:]))
        check("mark_interrupted_refuses_an_unknown_run: nothing in the notebook was written",
              tree(nb) == before, sorted(set(tree(nb).items()) ^ set(before.items()), key=str)[:5])
    mark_interrupted_refuses_an_unknown_run()

    def mark_interrupted_needs_a_reason():
        mkrun("2026-10-10-01", scratch="in_progress")
        before = tree(nb)
        p = run("unfinished", "--mark-interrupted", "2026-10-10-01")
        check("mark_interrupted_needs_a_reason: exit 2 and the error names --reason",
              p.returncode == 2 and "needs --reason" in p.stderr, (p.returncode, p.stdout, p.stderr[-300:]))
        check("mark_interrupted_needs_a_reason: nothing in the notebook was written", tree(nb) == before,
              sorted(set(tree(nb).items()) ^ set(before.items()), key=str)[:5])
    mark_interrupted_needs_a_reason()

    def unfinished_needs_a_flag():
        before = tree(nb)
        p = run("unfinished")
        check("unfinished_needs_a_flag: neither flag exits 2 and the error says to give one, not both and not neither",
              p.returncode == 2 and "not both and not neither" in p.stderr,
              (p.returncode, p.stdout, p.stderr[-300:]))
        check("unfinished_needs_a_flag: nothing in the notebook was written", tree(nb) == before,
              sorted(set(tree(nb).items()) ^ set(before.items()), key=str)[:5])
    unfinished_needs_a_flag()

    def mark_interrupted_refuses_a_run_folder_beside_it():
        mkrun("2026-10-12-01", scratch="in_progress")
        before = tree(nb)
        p = run("unfinished", "--run-folder", str(cur), "--mark-interrupted", "2026-10-12-01", "--reason", "x")
        check("mark_interrupted_refuses_a_run_folder_beside_it: both flags exit 2 and the error says not both and not neither",
              p.returncode == 2 and "not both and not neither" in p.stderr,
              (p.returncode, p.stdout, p.stderr[-300:]))
        check("mark_interrupted_refuses_a_run_folder_beside_it: nothing in the notebook was written",
              tree(nb) == before, sorted(set(tree(nb).items()) ^ set(before.items()), key=str)[:5])
    mark_interrupted_refuses_a_run_folder_beside_it()

    def mark_interrupted_closes_a_scratchpad_with_no_status_line():
        d = mkrun("2026-10-11-01")
        (d / "scratchpad.md").write_text("# Cycle Run — 2026-10-11\n\n## Decisions log\n- started\n", encoding="utf-8")
        p = run("unfinished", "--mark-interrupted", "2026-10-11-01", "--reason", "no status written")
        after = run("unfinished", "--run-folder", str(cur))
        check("mark_interrupted_closes_a_scratchpad_with_no_status_line: exit 0 and the next unfinished run leaves it out",
              p.returncode == 0 and "2026-10-11-01" not in after.stdout, (p.returncode, p.stderr[-200:], after.stdout))
        sp = (d / "scratchpad.md").read_text(encoding="utf-8")
        check("mark_interrupted_closes_a_scratchpad_with_no_status_line: the scratchpad gains a Status line saying "
              "interrupted, and the reason under the Decisions log",
              "**Status**: interrupted" in sp and "no status written" in sp.split("## Decisions log", 1)[-1], sp)
    mark_interrupted_closes_a_scratchpad_with_no_status_line()

    def unfinished_offers_resume_or_close_as_one_choice():
        mkrun("2026-10-18-01", scratch="in_progress")
        p = run("unfinished", "--run-folder", str(cur))
        line = next((l for l in p.stdout.splitlines() if l.startswith("unfinished: 2026-10-18-01 ")), "")
        check("unfinished_offers_resume_or_close_as_one_choice: the printed line offers the resume or else the close-out",
              line == "unfinished: 2026-10-18-01 (scratchpad says in_progress) — resume: /wiki-cycle t --resume "
                      '2026-10-18-01; or close it: wiki-cycle-scope.py --topic t unfinished --mark-interrupted '
                      '2026-10-18-01 --reason "<why>"', p.stdout)
    unfinished_offers_resume_or_close_as_one_choice()

    def mark_interrupted_prints_what_it_closed():
        mkrun("2026-10-17-01", scratch="in_progress")
        p = run("unfinished", "--mark-interrupted", "2026-10-17-01", "--reason", "said so")
        check("mark_interrupted_prints_what_it_closed: stdout names the run and the reason",
              p.returncode == 0 and p.stdout.strip() == "unfinished: 2026-10-17-01 marked interrupted: said so",
              (p.returncode, p.stdout, p.stderr[-200:]))
    mark_interrupted_prints_what_it_closed()

    def unfinished_offers_only_the_close_out_without_a_scratchpad():
        mkrun("2026-10-19-01")
        p = run("unfinished", "--run-folder", str(cur))
        line = next((l for l in p.stdout.splitlines() if l.startswith("unfinished: 2026-10-19-01 ")), "")
        check("unfinished_offers_only_the_close_out_without_a_scratchpad: the printed line is the close-out alone",
              line == "unfinished: 2026-10-19-01 (no scratchpad) — close it: wiki-cycle-scope.py --topic t unfinished "
                      '--mark-interrupted 2026-10-19-01 --reason "<why>"', p.stdout)
    unfinished_offers_only_the_close_out_without_a_scratchpad()

    def mark_interrupted_rewrites_the_first_status_line_only():
        # the listing reads the first Status line; a later one (a quoted note in the log) is the user's text
        d = mkrun("2026-10-20-01", scratch="in_progress")
        pad = d / "scratchpad.md"
        pad.write_text(pad.read_text(encoding="utf-8") + "**Status**: completed (copied from an old run)\n",
                       encoding="utf-8")
        p = run("unfinished", "--mark-interrupted", "2026-10-20-01", "--reason", "two status lines")
        lines = pad.read_text(encoding="utf-8").splitlines()
        status = [l for l in lines if l.startswith("**Status**:")]
        check("mark_interrupted_rewrites_the_first_status_line_only: the later Status line is kept as written",
              p.returncode == 0 and status == ["**Status**: interrupted",
                                               "**Status**: completed (copied from an old run)"],
              (p.returncode, p.stderr[-200:], lines))
    mark_interrupted_rewrites_the_first_status_line_only()

    # ── left-undone (task #240, lesson #9, step 1): what a cycle leaves undone, written by the script ──
    TODAY = "2026-06-15"

    def mknb(name):
        root = tmp / "notebooks" / name
        (root / "wiki" / "research" / "x").mkdir(parents=True)
        reg = json.loads((tmp / "linked-notebooks.json").read_text(encoding="utf-8"))
        reg["notebooks"][name] = {"root": f"notebooks/{name}"}
        (tmp / "linked-notebooks.json").write_text(json.dumps(reg), encoding="utf-8")
        return root

    def run_on(topic, *a):
        return subprocess.run([sys.executable, str(SCRIPT), "--topic", topic, *a], cwd=proj, capture_output=True,
                              text=True, encoding="utf-8", env={**os.environ, "PYTHONIOENCODING": "utf-8"})

    def page(root, rel, review=None):
        f = root / rel
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text("---\ntitle: \"x\"\ndate: 2026-01-01\ntier: 3\nlast_reviewed: 2026-01-01\n"
                     + (f"review_after: {review}\n" if review is not None else "") + "tags: [a]\n---\n\n# x\n",
                     encoding="utf-8")

    def lu_run(root, cid, cycle=None, mode=None, files=()):
        """A run folder with a scratchpad: `cycle` is the text in parentheses on the **Cycle** line, `mode` the
        `- Mode:` line; `files` are (name, status) step results."""
        rf = root / "_inbox" / "reports" / cid[:10] / cid
        rf.mkdir(parents=True, exist_ok=True)
        pad = ["# Cycle Run", "", "**Status**: in_progress"]
        if cycle is not None:
            pad.append(f"**Cycle**: {cid} ({cycle})")
        if mode is not None:
            pad.append(f"- Mode: {mode}")
        if cycle is not None or mode is not None:
            (rf / "scratchpad.md").write_text("\n".join(pad) + "\n", encoding="utf-8")
        for name, status in files:
            (rf / name).write_text(json.dumps({"status": status}), encoding="utf-8")
        return rf

    def lu(topic, rf, *extra):
        p = run_on(topic, "left-undone", "--run-folder", str(rf), "--today", TODAY, *extra)
        f = rf / "left-undone.txt"
        return p, (f.read_text(encoding="utf-8").splitlines() if f.is_file() else [])

    PAST_NOT_RUN = "this mode does not run refresh; /wiki-cycle --refresh-only lists them"
    PAST_RAN = "refresh ran; this count is from the dates now (refreshing them is your call: /wiki-refresh)"
    LINT_NONE = "- Lint findings: not checked (the mechanical lint left no lint-mechanical.json)"

    def left_undone_counts_review_dates():
        root = mknb("lu1")
        page(root, "wiki/research/x/past-a.md", "2026-01-01")
        page(root, "wiki/research/x/past-q.md", '"2026-02-01"')
        page(root, "wiki/research/x/due-today.md", TODAY)
        page(root, "wiki/research/x/future.md", "2026-12-01")
        page(root, "wiki/research/x/none-a.md")
        page(root, "wiki/research/x/bad-a.md", "soon")
        page(root, "wiki/tasks/card.md")
        page(root, "wiki/sessions/journal.md")
        (root / "wiki" / "_MAP.md").write_text("# map\n", encoding="utf-8")
        (root / "wiki" / "README.md").write_text("# readme\n", encoding="utf-8")
        rf = lu_run(root, "2026-06-15-01", cycle="--lint-only")
        before = tree(root)
        p, lines = lu("lu1", rf)
        after = tree(root)
        check("left_undone_counts_review_dates: exit 0 and the header counts the three queue lines",
              p.returncode == 0 and lines[:1] == ["Left undone: 6 queue(s)"], (p.returncode, p.stderr[-300:], lines))
        check("left_undone_counts_review_dates: past review_after counts 2 (the quoted date too), today and the future not",
              f"- Past review_after: 2 — {PAST_NOT_RUN}" in lines, lines)
        check("left_undone_counts_review_dates: no review_after counts 1, a task card and a session page not",
              "- No review_after: 1 — refresh cannot see an entry with no review_after; add the date "
              "(the lint lists them under Missing lifecycle fields)" in lines, lines)
        check("left_undone_counts_review_dates: a review_after that is not a date counts 1",
              "- review_after not a date: 1 — refresh cannot read it; correct the date "
              "(the lint lists them under Dates not in ISO form)" in lines, lines)
        check("left_undone_counts_review_dates: exactly six queue lines, the last of them a queue line",
              len([l for l in lines if l.startswith("- ")]) == 6 and lines[-1].startswith("- "), lines)
        rel = "_inbox/reports/2026-06-15/2026-06-15-01/left-undone.txt"
        check("left_undone_counts_review_dates: only left-undone.txt and its events file are new, nothing else changed, no scope file",
              set(after) - set(before) == {rel, rel.replace("left-undone.txt", "left-undone-events.txt")}
              and all(after.get(k) == v for k, v in before.items())
              and not [k for k in after if k.endswith("-scope.txt")], sorted(set(after) ^ set(before)))
        rf = lu_run(root, "2026-06-15-02", cycle="--full", files=[("refresh.json", "completed")])
        p, lines = lu("lu1", rf)
        check("left_undone_counts_review_dates: a --full run with a completed refresh.json says refresh ran",
              f"- Past review_after: 2 — {PAST_RAN}" in lines, (p.stderr[-300:], lines))
    left_undone_counts_review_dates()

    mode_runs = [0]

    def mode_of(cycle=None, mode=None):
        """(mode, modifiers) the command reports for a scratchpad with these two lines, as it prints them."""
        mode_runs[0] += 1
        rf = lu_run(mknb_once("lu2"), f"2026-06-16-{mode_runs[0]:02d}", cycle=cycle, mode=mode)
        p = run_on("lu2", "left-undone", "--run-folder", str(rf), "--today", TODAY)
        m = re.search(r"; mode (\S+); modifiers (\S+) ->", p.stdout)
        return (m.group(1), m.group(2)) if m else (p.stdout + p.stderr[-200:], "")

    def mknb_once(name):
        return tmp / "notebooks" / name if (tmp / "notebooks" / name).is_dir() else mknb(name)

    def left_undone_reads_the_mode():
        texts = [("--full", "full"), ("--ingest-only, staged; this session's bucket drained", "ingest-only"),
                 ("--prompt-for-urls (17 URLs…), staged", "prompt-for-urls"),
                 ('quick (ingest pass; the user asked for "a full ingest"…)', "quick"),
                 ("--quick (default)", "quick"), ("full", "full"), ("lint-only", "lint-only"),
                 ("`--full`", "full"), ("--lint-only --semantic", "lint-only-semantic"),
                 ("--discover-only", "discover-only"), ("--report-only", "report-only"),
                 ("--refresh-only", "refresh-only"), ("--claims-only", "claims-only")]
        for text, want in texts:
            got = mode_of(cycle=text)
            check(f"left_undone_reads_the_mode: {text!r} on the Cycle line reads {want}", got == (want, "none"), got)
            got = mode_of(mode=text)
            check(f"left_undone_reads_the_mode: {text!r} on the Mode line alone reads {want}",
                  got == (want, "none"), got)
        got = mode_of(cycle="--lint-only", mode="--lint-only --semantic")
        check("left_undone_reads_the_mode: --semantic on the Mode line makes a --lint-only Cycle line semantic",
              got == ("lint-only-semantic", "none"), got)
        got = mode_of(cycle="--full --semantic")
        check("left_undone_reads_the_mode: --semantic changes no other mode", got == ("full", "none"), got)
        got = mode_of(cycle="--full, --no-confirm-discovery")
        check("left_undone_reads_the_mode: a modifier on the Cycle line is reported",
              got == ("full", "--no-confirm-discovery"), got)
        got = mode_of(cycle="--full", mode="--full --lint-all")
        check("left_undone_reads_the_mode: a modifier only on the Mode line is reported",
              got == ("full", "--lint-all"), got)
        got = mode_of(cycle="--quick, --since 6, --direct, --lint-all, --no-confirm-discovery")
        check("left_undone_reads_the_mode: the four modifiers together, sorted, whatever else is written",
              got == ("quick", "--direct,--lint-all,--no-confirm-discovery,--since"), got)
    left_undone_reads_the_mode()

    unclear_runs = [0]

    def unclear_run(topic, cycle=None, mode=None, files=()):
        unclear_runs[0] += 1
        rf = lu_run(tmp / "notebooks" / topic, f"2026-06-17-{unclear_runs[0]:02d}", cycle=cycle, mode=mode, files=files)
        return (rf, *lu(topic, rf))

    def left_undone_names_what_it_cannot_check():
        root = mknb("lu3")
        page(root, "wiki/research/x/past-a.md", "2026-01-01")
        page(root, "wiki/research/x/past-b.md", "2026-02-01")
        page(root, "wiki/research/x/none-a.md")
        page(root, "wiki/research/x/future.md", "2026-12-01")
        none_line = ("- No review_after: 1 — refresh cannot see an entry with no review_after; add the date "
                     "(the lint lists them under Missing lifecycle fields)")
        no_mode = "Mode: not checked (cannot read the mode from scratchpad.md); steps that left no file are not known"
        # the third state: a mode that runs refresh, whose result is missing or not completed
        _, p, lines = unclear_run("lu3", cycle="--full")
        check("left_undone_names_what_it_cannot_check: --full with no refresh.json keeps the count and says so",
              "- Past review_after: 2, not checked (refresh left no refresh.json)" in lines
              and not [l for l in lines if l.startswith("- Past review_after: 2 —")], (p.stderr[-200:], lines))
        _, p, lines = unclear_run("lu3", cycle="--full", files=[("refresh.json", "partial")])
        check("left_undone_names_what_it_cannot_check: a partial refresh.json keeps the count and says it ended partial",
              "- Past review_after: 2, not checked (the refresh ended partial)" in lines, lines)
        # a mode the run folder contradicts: the counts stay, the mode-dependent line says so, the Mode line is added
        _, p, lines = unclear_run("lu3", cycle="--quick", files=[("refresh.json", "completed")])
        why = "the mode in scratchpad.md is quick but the run folder holds refresh.json"
        check("left_undone_names_what_it_cannot_check: a mismatch keeps the count on the refresh line only",
              f"- Past review_after: 2, not checked ({why})" in lines and none_line in lines, lines)
        check("left_undone_names_what_it_cannot_check: a mismatch adds the Mode line and the header counts all three",
              f"- Mode: not checked ({why}); steps that left no file are not known" in lines
              and lines[:1] == ["Left undone: 5 queue(s)"], lines)
        # a mode that cannot be read: no scratchpad, two lines that disagree
        for label, kw in (("no scratchpad", {}), ("two lines naming different modes", {"cycle": "--full", "mode": "--quick"})):
            _, p, lines = unclear_run("lu3", **kw)
            check(f"left_undone_names_what_it_cannot_check: {label} keeps the count, the other lines and adds the Mode line",
                  "- Past review_after: 2, not checked (cannot read the mode from scratchpad.md)" in lines
                  and none_line in lines and f"- {no_mode}" in lines and lines[:1] == ["Left undone: 5 queue(s)"], lines)
        # no mode token at all, an empty run folder, nothing else to count: the header is never "nothing"
        clean = mknb("lu4")
        page(clean, "wiki/research/x/future.md", "2026-12-01")
        _, p, lines = unclear_run("lu4", cycle="see the notes")
        check("left_undone_names_what_it_cannot_check: no mode token and nothing else gives one queue, never nothing",
              lines[:4] == ["Left undone: 3 queue(s)",
                            "- Not semantically linted: 1, not checked (cannot read the mode from scratchpad.md)",
                            "- No claims, or revised since the index: 1, not checked (cannot read the mode from scratchpad.md)",
                            f"- {no_mode}"], lines)
        # step files that are not steps never contradict a mode
        _, p, lines = unclear_run("lu3", cycle="--quick", files=[(n, "completed") for n in (
            "models.json", "cost.json", "email-review.json")])
        check("left_undone_names_what_it_cannot_check: models.json, cost.json and email-review.json are not steps",
              not [l for l in lines if l.startswith("- Mode:")]
              and "- Past review_after: 2 — this mode does not run refresh; /wiki-cycle --refresh-only lists them" in lines, lines)
        # the cross-check covers each named step file
        every = ["refresh.json", "lint-semantic.json", "claims.json", "synthesis.json", "update.json", "triage.json",
                 "discover.json", "lint-mechanical.json"]
        for mode, name in (("quick", "refresh.json"), ("quick", "lint-semantic.json"), ("quick", "claims.json"),
                           ("refresh-only", "synthesis.json"), ("refresh-only", "update.json"),
                           ("refresh-only", "triage.json"), ("prompt-for-urls", "triage.json"),
                           ("ingest-only", "discover.json"), ("discover-only", "lint-mechanical.json")):
            _, p, lines = unclear_run("lu3", cycle=f"--{mode}", files=[(name, "completed")])
            check(f"left_undone_names_what_it_cannot_check: --{mode} with {name} is a contradiction",
                  any(l.startswith(f"- Mode: not checked (the mode in scratchpad.md is {mode} but the run folder "
                                   f"holds {name})") for l in lines), lines)
        for mode, names in (("full", every), ("lint-only", ["lint-mechanical.json"]),
                            ("lint-only-semantic", ["lint-semantic.json", "lint-mechanical.json"]),
                            ("prompt-for-urls", ["update.json", "synthesis.json", "lint-mechanical.json"]),
                            ("claims-only", ["claims.json"]), ("discover-only", ["discover.json"])):
            cyc = "--lint-only --semantic" if mode == "lint-only-semantic" else f"--{mode}"
            _, p, lines = unclear_run("lu3", cycle=cyc, files=[(n, "completed") for n in names])
            check(f"left_undone_names_what_it_cannot_check: --{mode} with the steps it runs is no contradiction",
                  not [l for l in lines if l.startswith("- Mode:")], lines)
        # --report-only: the second line names the last run, which is never a report-only run or an unreported one
        for cid, cyc, report in (("2026-06-14-01", "--full", True), ("2026-06-14-02", "--report-only", True),
                                 ("2026-06-14-03", "--full", False), ("2026-06-16-01", "--full", True)):
            rf = lu_run(root, cid, cycle=cyc)
            if report:
                (rf / f"{cid}-run-cycle-report.md").write_text("# report\n", encoding="utf-8")
        rf = lu_run(root, "2026-06-15-09", cycle="--report-only")
        p, lines = lu("lu3", rf)
        check("left_undone_names_what_it_cannot_check: --report-only names the last full run on its second line, uncounted",
              lines[1:2] == ["Disk-state queues are counted now; event lines are from the last run (2026-06-14-01)"]
              and lines[:1] == ["Left undone: 5 queue(s)"], (p.stderr[-200:], lines))
        rf = lu_run(clean, "2026-06-15-09", cycle="--report-only")
        p, lines = lu("lu4", rf)
        check("left_undone_names_what_it_cannot_check: --report-only with no earlier report says there is none",
              lines[1:2] == ["Disk-state queues are counted now; event lines are from the last run "
                             "(none: no earlier run with a report)"], lines)
        _, p, lines = unclear_run("lu3", cycle="--full", files=[("refresh.json", "completed")])
        check("left_undone_names_what_it_cannot_check: a run that is not --report-only has no such line",
              not [l for l in lines if l.startswith("Disk-state queues")], lines)
    left_undone_names_what_it_cannot_check()

    def left_undone_refuses_bad_input():
        root = tmp / "notebooks" / "lu1"
        rf = lu_run(root, "2026-06-18-01", cycle="--lint-only")
        for bad in ("2026-13-40", "20260101", "tomorrow"):
            p = run_on("lu1", "left-undone", "--run-folder", str(rf), "--today", bad)
            check(f"left_undone_refuses_bad_input: --today {bad} exits 2, names --today and writes no file",
                  p.returncode == 2 and "--today" in p.stderr and not (rf / "left-undone.txt").exists(),
                  (p.returncode, p.stderr[-200:]))
        gone = root / "_inbox" / "reports" / "2026-06-18" / "2026-06-18-02"
        p = run_on("lu1", "left-undone", "--run-folder", str(gone), "--today", TODAY)
        check("left_undone_refuses_bad_input: a run folder that is not there exits 2, names it and creates nothing",
              p.returncode == 2 and "2026-06-18-02" in p.stderr and not gone.exists(), (p.returncode, p.stderr[-200:]))
        (tmp / "notebooks" / "lu5").mkdir()
        reg = json.loads((tmp / "linked-notebooks.json").read_text(encoding="utf-8"))
        reg["notebooks"]["lu5"] = {"root": "notebooks/lu5"}
        (tmp / "linked-notebooks.json").write_text(json.dumps(reg), encoding="utf-8")
        p = run_on("lu5", "left-undone", "--run-folder", str(rf), "--today", TODAY)
        check("left_undone_refuses_bad_input: a notebook with no wiki/ exits 2 and writes no file",
              p.returncode == 2 and "no wiki" in p.stderr and not (rf / "left-undone.txt").exists(),
              (p.returncode, p.stderr[-200:]))
    left_undone_refuses_bad_input()

    def left_undone_mode_table_matches_skill():
        import importlib.util
        spec = importlib.util.spec_from_file_location("wiki_cycle_scope_under_test", SCRIPT)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        script_table = {step: set(modes) for step, modes in getattr(mod, "STEP_MODES", {}).items()}
        skill = Path(__file__).resolve().parents[2] / "skills" / "wiki-cycle" / "SKILL.md"
        skill_text = skill.read_text(encoding="utf-8")
        # each row of the skill's five-mode table, and the script's steps it covers
        rows = (("1 Discover", ("discover",)), ("1.7 Triage", ("triage",)), ("2 Ingest", ("ingest",)),
                ("3 Integration scripts", ("lint",)), ("4 Semantic lint", ("semantic", "fix")),
                ("6 Claims", ("claims", "refresh")), ("6.5 Best-practices", ("synthesis",)))

        def skill_runs(text):
            lines = text.splitlines()
            start = next((i for i, l in enumerate(lines) if l.startswith("| Step | quick |")), None)
            if start is None:
                return [], {}
            table = []
            for l in lines[start:]:
                if not l.startswith("|"):
                    break
                table.append([c.strip() for c in l.strip().strip("|").split("|")])
            modes = [c.removeprefix("--") for c in table[0][1:]]
            runs = {}
            for prefix, steps in rows:
                row = next((r for r in table if r[0].startswith(prefix)), None)
                for step in steps:
                    runs[step] = {m for m, cell in zip(modes, row[1:], strict=True) if cell.startswith("✓")} if row else set()
            return modes, runs

        def drift(table, text):
            modes, runs = skill_runs(text)
            return [f"{step}: script {sorted(table.get(step, set()) & set(modes))} skill {sorted(want)}"
                    for step, want in runs.items() if table.get(step, set()) & set(modes) != want]

        modes, runs = skill_runs(skill_text)
        check("left_undone_mode_table_matches_skill: the skill's table has the five modes and all nine steps",
              modes == ["quick", "full", "ingest-only", "discover-only", "prompt-for-urls"] and len(runs) == 9
              and all(runs[s] for s in runs), (modes, runs))
        check("left_undone_mode_table_matches_skill: the script's table agrees with it for those five modes",
              drift(script_table, skill_text) == [], drift(script_table, skill_text))
        flipped = skill_text.replace("| 6 Claims, 7 refresh | — |", "| 6 Claims, 7 refresh | ✓ |", 1)
        check("left_undone_mode_table_matches_skill: a cell flipped in the skill's table is drift",
              flipped != skill_text and len(drift(script_table, flipped)) == 2, drift(script_table, flipped))
        moved = {**script_table, "triage": script_table.get("triage", set()) | {"discover-only"}}
        check("left_undone_mode_table_matches_skill: a step moved in the script's table is drift, and named",
              [d.split(":")[0] for d in drift(moved, skill_text)] == ["triage"], drift(moved, skill_text))
    left_undone_mode_table_matches_skill()

    def left_undone_reads_a_quoted_mode_before_punctuation():
        for text, want in (("`--full`.", "full"), ("'quick':", "quick"), ('"--lint-only" `--semantic`!', "lint-only-semantic")):
            got = mode_of(cycle=text)
            check(f"left_undone_reads_a_quoted_mode_before_punctuation: {text!r} on the Cycle line reads {want}",
                  got == (want, "none"), got)
            got = mode_of(mode=text)
            check(f"left_undone_reads_a_quoted_mode_before_punctuation: {text!r} on the Mode line reads {want}",
                  got == (want, "none"), got)
    left_undone_reads_a_quoted_mode_before_punctuation()

    # ── left-undone step 3: tickets in buckets, pending, staged entries and discovery checklists ──
    step3_runs = [0]

    def step3_run(topic, cycle=None, files=(), setting=None):
        """A fresh run folder on notebook `topic` (cycle id from a counter), its left-undone lines."""
        step3_runs[0] += 1
        rf = lu_run(tmp / "notebooks" / topic, f"2026-06-18-{step3_runs[0]:02d}", cycle=cycle, files=files)
        if setting is not None:
            (rf / "promote-setting.txt").write_text(f"confirm_before_promote: {setting}\nfrom: test\n", encoding="utf-8")
        p, lines = lu(topic, rf)
        return p, lines

    def lu_tickets(folder, tag, n):
        folder.mkdir(parents=True, exist_ok=True)
        for i in range(n):
            (folder / f"{tag}-{i}.md").write_text(f"---\nsource: https://x.test/{tag}/{i}\n---\n\n# t\n", encoding="utf-8")

    NO_MODE = "cannot read the mode from scratchpad.md"
    OWN_NO_INGEST = "- Tickets in this session's bucket main: 2 — this mode does not ingest; /wiki-cycle --ingest-only"
    OWN_RAN = ("- Tickets in this session's bucket main: 2 — left in the bucket after ingest: dropped, failed, "
               "deferred or not reached")
    OTHERS = "- Other readers' buckets, still to process: other 4, money 15"

    def left_undone_counts_bucket_tickets():
        root = mknb("lu6")
        intake = root / "_inbox" / "intake"
        intake.mkdir(parents=True)
        (intake / "README.md").write_text(
            "---\nbuckets:\n  - folder: main\n    purpose: Anything\n    reader: t\n  - folder: other\n"
            "    purpose: Agents\n    reader: other-bot\n  - folder: money\n    purpose: Money\n    reader: mark\n"
            "  - folder: ghost\n    purpose: No folder on disk\n    reader: other-bot\n---\n\n# Intake\n", encoding="utf-8")
        lu_tickets(intake / "main", "m", 2)
        lu_tickets(intake / "other", "o", 4)
        lu_tickets(intake / "money", "k", 15)
        (intake / "other" / "handoff-note.md").write_text("# a note, no source line\n", encoding="utf-8")
        (intake / "other" / "README.md").write_text("---\nsource: https://x.test/readme\n---\n", encoding="utf-8")
        p, lines = step3_run("lu6", cycle="--lint-only")
        check("left_undone_counts_bucket_tickets: --lint-only names this session's bucket once and the others once, "
              "and counts both in the header",
              p.returncode == 0 and lines == ["Left undone: 3 queue(s)", LINT_NONE, OWN_NO_INGEST, OTHERS],
              (p.stderr[-300:], lines))
        p, lines = step3_run("lu6", cycle="--full")
        check("left_undone_counts_bucket_tickets: --full gives the ran reason on this session's bucket, the others unchanged",
              OWN_RAN in lines and OTHERS in lines, lines)
        p, lines = step3_run("lu6")
        check("left_undone_counts_bucket_tickets: an unreadable mode keeps the count and says so, the other readers' line unchanged",
              f"- Tickets in this session's bucket main: 2, not checked ({NO_MODE})" in lines and OTHERS in lines,
              lines)
    left_undone_counts_bucket_tickets()

    def left_undone_counts_pending_tickets():
        root = mknb("lu7")
        pend = root / "_inbox" / "pending"
        lu_tickets(pend, "p", 2)
        (pend / "p-nosource.md").write_text("---\nadded_by: test\n---\n\n# a ticket the dequeue counts too\n", encoding="utf-8")
        (pend / "_held.md").write_text("---\nsource: https://x.test/held\n---\n", encoding="utf-8")
        (pend / "README.md").write_text("# pending\n", encoding="utf-8")
        head = "- Tickets in _inbox/pending/: 3"
        no_triage = f"{head} — this mode does not triage; /wiki-cycle --ingest-only gives each an owner"
        late = f"{head} — not triaged: arrived after triage, or triage did not complete"
        p, lines = step3_run("lu7", cycle="--lint-only")
        check("left_undone_counts_pending_tickets: --lint-only counts the three (one with no source:) and says it does not triage",
              p.returncode == 0 and lines == ["Left undone: 2 queue(s)", LINT_NONE, no_triage],
              (p.stderr[-300:], lines))
        p, lines = step3_run("lu7", cycle="--prompt-for-urls")
        check("left_undone_counts_pending_tickets: a mode that ingests and does not triage says it does not triage",
              no_triage in lines, lines)
        p, lines = step3_run("lu7", cycle="--full")
        check("left_undone_counts_pending_tickets: --full says they arrived after triage or triage did not complete",
              late in lines, lines)
        p, lines = step3_run("lu7", cycle="--full", files=[("triage.json", "completed")])
        check("left_undone_counts_pending_tickets: a completed triage.json changes nothing on the line",
              late in lines, lines)
        p, lines = step3_run("lu7")
        check("left_undone_counts_pending_tickets: an unreadable mode keeps the count and says so",
              f"{head}, not checked ({NO_MODE})" in lines, lines)
    left_undone_counts_pending_tickets()

    def left_undone_counts_staged_entries():
        root = mknb("lu8")
        prop = root / "_inbox" / "proposed"
        prop.mkdir(parents=True)
        for name in ("s1.md", "s2.md", "_x.md", "README.md"):
            (prop / name).write_text("---\ntitle: s\n---\n", encoding="utf-8")
        (prop / "s1.proposed_metadata.json").write_text("{}", encoding="utf-8")
        none = ["Left undone: 1 queue(s)", LINT_NONE]
        p, lines = step3_run("lu8", cycle="--lint-only", setting="false")
        check("left_undone_counts_staged_entries: with confirm_before_promote false the two staged entries are one queue line",
              p.returncode == 0 and lines == ["Left undone: 2 queue(s)", LINT_NONE, "- Staged entries: 2 — staged before "
                                              "this run, or held by the checker; /wiki-promote"],
              (p.stderr[-300:], lines))
        p, lines = step3_run("lu8", cycle="--lint-only", setting="true")
        check("left_undone_counts_staged_entries: with confirm_before_promote true Needs you has them, so no line",
              lines == none, lines)
        p, lines = step3_run("lu8", cycle="--lint-only")
        check("left_undone_counts_staged_entries: with no promote-setting.txt the count is kept and not checked is said",
              lines == ["Left undone: 2 queue(s)", LINT_NONE, "- Staged entries: 2, not checked (no promote-setting.txt: "
                                                              "whether they wait for you is not known)"], lines)
        mknb("lu8b")
        p, lines = step3_run("lu8b", cycle="--lint-only", setting="false")
        check("left_undone_counts_staged_entries: no staged entries add nothing, with the setting false or absent",
              lines == none and step3_run("lu8b", cycle="--lint-only")[1] == none, lines)
    left_undone_counts_staged_entries()

    def left_undone_counts_discovery_checklists():
        root = mknb("lu9")
        disc = root / "_inbox" / "discovered"
        disc.mkdir(parents=True)
        for name in ("2026-06-14-discovery.md", "README.md", "_old.md"):
            (disc / name).write_text("# Discovery\n\n- [ ] **1.** [T](https://x.test/t) — tier 2\n", encoding="utf-8")
        p, lines = step3_run("lu9", cycle="--lint-only")
        check("left_undone_counts_discovery_checklists: one checklist is one queue line, a README and a _-file are not counted",
              p.returncode == 0 and lines == [
                  "Left undone: 2 queue(s)", LINT_NONE, "- Discovery checklists: 1 — still in _inbox/discovered/ "
                  "(discovery files a processed one in _inbox/done/); whether it was reviewed is not recorded"],
              (p.stderr[-300:], lines))
        mknb("lu9b")
        p, lines = step3_run("lu9b", cycle="--lint-only")
        check("left_undone_counts_discovery_checklists: no _inbox/discovered/ adds nothing",
              lines == ["Left undone: 1 queue(s)", LINT_NONE], lines)
    left_undone_counts_discovery_checklists()

    def left_undone_falls_back_to_one_bucket_on_an_unparseable_intake_readme():
        root = mknb("lu10")
        intake = root / "_inbox" / "intake"
        intake.mkdir(parents=True)
        (intake / "README.md").write_text("---\nbuckets: [unclosed\n---\n\n# Intake\n", encoding="utf-8")
        lu_tickets(intake / "main", "m", 2)
        p, lines = step3_run("lu10", cycle="--lint-only")
        check("left_undone_falls_back_to_one_bucket_on_an_unparseable_intake_readme: exit 0 and the main bucket is this session's",
              p.returncode == 0 and lines == ["Left undone: 2 queue(s)", LINT_NONE, OWN_NO_INGEST],
              (p.returncode, p.stderr[-300:], lines))
    left_undone_falls_back_to_one_bucket_on_an_unparseable_intake_readme()

    def left_undone_docstring_names_the_unsupported_working_folder():
        import ast
        doc = ast.get_docstring(ast.parse(SCRIPT.read_text(encoding="utf-8"))) or ""
        check("left_undone_docstring_names_the_unsupported_working_folder: the docstring says a working folder whose "
              ".claude/wiki-config.json names another notebook is not supported",
              "names another notebook" in doc and "not a supported case" in doc, doc[doc.find("`left-undone`"):][:700])
    left_undone_docstring_names_the_unsupported_working_folder()

    def left_undone_session_buckets_lets_an_unexpected_error_surface():
        import importlib.util
        spec = importlib.util.spec_from_file_location("wiki_cycle_scope_session_buckets", SCRIPT)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)

        class Raises:
            def __init__(self, exc):
                self.exc = exc

            def buckets(self, nb):
                raise self.exc

            def me(self):
                return "me"

        for exc in (OSError("disk gone"), RuntimeError("bug in buckets")):
            try:
                got = mod.session_buckets(Raises(exc), tmp)
            except type(exc):
                got = "raised"
            check(f"left_undone_session_buckets_lets_an_unexpected_error_surface: a {type(exc).__name__} from buckets() "
                  "is raised, not counted as the main bucket", got == "raised", got)
        root = mknb("lu10b")
        intake = root / "_inbox" / "intake"
        intake.mkdir(parents=True)
        tri = mod._triage()
        for label, front in (("a YAML syntax error", "buckets: [unclosed"), ("buckets that is not a list", "buckets: 5"),
                             ("a top-level list", "- a"), ("a bucket that is not a mapping", "buckets: [a]")):
            (intake / "README.md").write_text(f"---\n{front}\n---\n\n# Intake\n", encoding="utf-8")
            got = [b["folder"] for b in mod.session_buckets(tri, root)]
            check(f"left_undone_session_buckets_lets_an_unexpected_error_surface: {label} in the intake README reads as "
                  "the one-bucket default", got == ["main"], got)
    left_undone_session_buckets_lets_an_unexpected_error_surface()

    # ── left-undone step 4: newest_step, the one walk over the run folders' step results ──
    def newest_step_returns_the_newest_matching_result():
        import importlib.util
        spec = importlib.util.spec_from_file_location("wiki_cycle_scope_newest_step", SCRIPT)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        root = mknb("ns1")

        def put(day, text):
            d = root / "_inbox" / "reports" / day / f"{day}-01"
            d.mkdir(parents=True)
            (d / "lint-semantic.json").write_text(text, encoding="utf-8")
            return d

        done = put("2026-10-02", json.dumps({"status": "completed", "timestamp": "2026-10-02T09:00:00-04:00"}))
        put("2026-10-04", json.dumps({"timestamp": "2026-10-04T09:00:00-04:00"}))
        part = put("2026-10-05", json.dumps({"status": "partial", "timestamp": "2026-10-05T09:00:00-04:00"}))
        put("2026-10-06", "{not json")
        put("2026-10-07", json.dumps({"status": "completed"}))
        put("2026-10-09", json.dumps({"status": "completed", "timestamp": "2026-10-01T08:00:00-04:00"}))

        def got(*a, at=root, **k):
            try:
                r = mod.newest_step(at, "lint-semantic.json", *a, **k)
            except NotImplementedError as e:
                return f"NotImplementedError {e}"
            return None if r is None else (r[0].isoformat(), r[1].name)

        check("newest_step_returns_the_newest_matching_result: with no filter the newest timestamp wins, whatever its "
              "status, and a later folder name, a file that does not parse and one with no timestamp do not",
              got() == ("2026-10-05T09:00:00-04:00", "2026-10-05-01"), got())
        check("newest_step_returns_the_newest_matching_result: status completed leaves out the partial and the one with no status",
              got("completed") == ("2026-10-02T09:00:00-04:00", "2026-10-02-01"), got("completed"))
        check("newest_step_returns_the_newest_matching_result: skip leaves out one run folder, and a result with no status "
              "is still found when no status is asked for",
              got(skip=part) == ("2026-10-04T09:00:00-04:00", "2026-10-04-01"), got(skip=part))
        check("newest_step_returns_the_newest_matching_result: status and skip together fall back to the next older completed one",
              got("completed", skip=done) == ("2026-10-01T08:00:00-04:00", "2026-10-09-01"), got("completed", skip=done))
        bare = mknb("ns2")
        check("newest_step_returns_the_newest_matching_result: a notebook with no run folders gives None",
              got(at=bare) is None, got(at=bare))
    newest_step_returns_the_newest_matching_result()

    # ── left-undone step 4: entries not linted, without claims, not synthesised (the covered-set rule) ──
    D0, D1, D2, D3 = "2026-10-01", "2026-10-02", "2026-10-03", "2026-10-04"
    SEM, CLM, SYN = "- Not semantically linted: ", "- No claims, or revised since the index: ", "- Not yet synthesised: "
    SEM_OFF = "this mode does not run the semantic lint; /wiki-cycle --lint-only --semantic or --full"
    SEM_RAN = ("the semantic lint ran and did not read them (lint-semantic.md); an entry re-reviewed later on the "
               "lint's own day is not counted")
    CLM_OFF = "this mode does not run claims; /wiki-cycle --claims-only or --full"
    CLM_RAN = ("the claims step ran and did not read them (claims.md); an entry re-reviewed later on that day "
               "is not counted")
    SYN_OFF = "this mode does not synthesise (only modes that ingest do); /wiki-cycle --ingest-only"
    SYN_RAN = "synthesis ran and did not read them (synthesis.md)"
    s4_runs = [0]

    def s4_stamp(day):
        return f"{day}T12:00:00-04:00"

    def s4_entry(root, rel, reviewed, extra=""):
        f = root / rel
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text(f"---\ntitle: \"x\"\ndate: 2026-01-01\ntier: 3\nlast_reviewed: {reviewed}\nreview_after: 2099-01-01\n"
                     f"tags: [a]\n{extra}---\n\n# x\n", encoding="utf-8")

    def s4_commit(day):
        git("add", "-A")
        git("commit", "-q", "--allow-empty", "-m", "s4", date=f"{day}T10:00:00-04:00")

    def s4_step(rf, name, status, stamp=None, scope=None, text=None):
        """A step result in a run folder (`stamp` its timestamp; `text` its raw content) and, with `scope`
        (file name, paths), the scope file that step read."""
        rec = {"status": status, **({"timestamp": stamp} if stamp else {})}
        (rf / name).write_text(text if text is not None else json.dumps(rec), encoding="utf-8")
        if scope:
            (rf / scope[0]).write_text(f"# {scope[0]}: {len(scope[1])} (test)\n" + "".join(p + "\n" for p in scope[1]),
                                       encoding="utf-8")

    def s4_lu(topic, cycle, steps=()):
        """(process, left-undone lines, (files new, files changed)) for a fresh run folder with these step results."""
        s4_runs[0] += 1
        root = tmp / "notebooks" / topic
        rf = lu_run(root, f"{D3}-{s4_runs[0]:02d}", cycle=cycle)
        for step in steps:
            s4_step(rf, **step)
        before = tree(root)
        p, lines = lu(topic, rf)
        after = tree(root)
        shutil.rmtree(rf)     # a scenario's run folder would be an earlier run (and a cut-off) for the next one
        return p, lines, ([k for k in after if k not in before], [k for k, v in before.items() if after.get(k) != v])

    def s4_line(lines, prefix):
        return next((l for l in lines if l.startswith(prefix)), None)

    def s4_sem_history(name):
        """old-a and old-b committed D0, a completed lint on D1 that read both, then new-d added (untracked) and
        old-a re-reviewed on D2: the harness's own history, in a notebook of its own."""
        root = mknb(name)
        s4_entry(root, "wiki/research/x/old-a.md", D0)
        s4_entry(root, "wiki/research/x/old-b.md", D0)
        s4_commit(D0)
        hist = root / "_inbox" / "reports" / D1 / f"{D1}-01"
        hist.mkdir(parents=True)
        s4_step(hist, "lint-semantic.json", "completed", s4_stamp(D1),
                ("semantic-scope.txt", ["wiki/research/x/old-a.md", "wiki/research/x/old-b.md"]))
        s4_entry(root, "wiki/research/x/new-d.md", D2)
        s4_entry(root, "wiki/research/x/old-a.md", D2)
        return root

    def s4_lint(day, paths, status="completed"):
        return [dict(name="lint-semantic.json", status=status, stamp=s4_stamp(day), scope=("semantic-scope.txt", paths))]

    def left_undone_counts_entries_not_linted():
        from datetime import datetime, timedelta
        both = ["wiki/research/x/old-a.md", "wiki/research/x/old-b.md"]
        new_d = "wiki/research/x/new-d.md"
        s4_sem_history("s4a")
        p, lines, (new, edited) = s4_lu("s4a", "--lint-only")
        check("left_undone_counts_entries_not_linted: --lint-only counts the entry added and the one re-reviewed since "
              "the last lint, gives the does-not-run reason and a header of the line count (never nothing)",
              p.returncode == 0 and f"{SEM}2 — {SEM_OFF}" in lines and lines[:1] == ["Left undone: 4 queue(s)"]
              and lines[-1].startswith("- "), (p.stderr[-300:], lines))
        check("left_undone_counts_entries_not_linted: only left-undone.txt and its events file are new, nothing changed, no scope file written",
              sorted(k.rsplit("/", 1)[-1] for k in new) == ["left-undone-events.txt", "left-undone.txt"] and edited == [],
              (new, edited))
        p, lines, _ = s4_lu("s4a", "--full")
        check("left_undone_counts_entries_not_linted: --full with no lint-semantic.json keeps the count and says the lint left none",
              f"{SEM}2, not checked (the semantic lint left no lint-semantic.json)" in lines, lines)
        p, lines, _ = s4_lu("s4a", "--full", s4_lint(D3, both + [new_d]))
        check("left_undone_counts_entries_not_linted: this run's completed lint and a scope file listing both: no line",
              s4_line(lines, SEM) is None, lines)
        p, lines, _ = s4_lu("s4a", "--full", s4_lint(D3, both))
        check("left_undone_counts_entries_not_linted: a lint that did not read the new entry counts it, with the ran reason",
              f"{SEM}1 — {SEM_RAN}" in lines, lines)
        p, lines, _ = s4_lu("s4a", "--full", s4_lint(D3, both + [new_d], status="partial"))
        check("left_undone_counts_entries_not_linted: a partial lint with a 3-entry scope file is not subtracted, the line says not checked",
              f"{SEM}2, not checked (the semantic lint ended partial; what it covered is unknown)" in lines
              and lines[:1] != ["Left undone: nothing"], lines)
        p, lines, _ = s4_lu("s4a", "--full", [dict(name="lint-semantic.json", status="completed", text="{not json")])
        check("left_undone_counts_entries_not_linted: a lint-semantic.json that does not parse is not checked, no crash",
              p.returncode == 0 and f"{SEM}2, not checked (lint-semantic.json unreadable)" in lines, (p.stderr[-300:], lines))
        p, lines, _ = s4_lu("s4a", "--full", [dict(name="lint-semantic.json", status="completed", stamp=s4_stamp(D3))])
        check("left_undone_counts_entries_not_linted: a completed lint with no scope file is not checked, the count kept",
              f"{SEM}1, not checked (no semantic-scope.txt in the run folder)" in lines, lines)
        p, lines, _ = s4_lu("s4a", None)
        check("left_undone_counts_entries_not_linted: a mode that cannot be read keeps the count and says so",
              f"{SEM}2, not checked (cannot read the mode from scratchpad.md)" in lines, lines)
        # the labelled under-count: a step compares days
        root = mknb("s4b")
        for nm, rev in (("same-in", D2), ("same-out", D2), ("after-in", D3)):
            s4_entry(root, f"wiki/research/x/{nm}.md", rev)
        s4_commit(D0)
        p, lines, _ = s4_lu("s4b", "--full", s4_lint(D2, [f"wiki/research/x/{n}.md" for n in ("same-in", "same-out", "after-in")]))
        check("left_undone_counts_entries_not_linted: read and re-reviewed on the lint's own day is not counted, one "
              "re-reviewed on a later day is, whatever the scope file says",
              f"{SEM}1 — {SEM_RAN}" in lines, lines)
        p, lines, _ = s4_lu("s4b", "--full", s4_lint(D2, [f"wiki/research/x/{n}.md" for n in ("same-in", "after-in")]))
        check("left_undone_counts_entries_not_linted: re-reviewed on the lint's day and not in the scope file is counted",
              f"{SEM}2 — {SEM_RAN}" in lines, lines)
        # a staged entry linted and then promoted is bridged by its stem; a task card is never counted
        root = mknb("s4c")
        s4_entry(root, "wiki/research/x/old-a.md", D0)
        s4_commit(D0)
        s4_entry(root, "wiki/research/x/promo.md", D1)
        s4_entry(root, "wiki/tasks/card.md", D1)
        p, lines, _ = s4_lu("s4c", "--full", s4_lint(D2, ["wiki/research/x/old-a.md", "_inbox/proposed/promo.md"]))
        check("left_undone_counts_entries_not_linted: a staged entry linted then promoted is not counted, nor is a task card",
              s4_line(lines, SEM) is None, lines)
        root = mknb("s4d")
        s4_entry(root, "wiki/research/x/old-a.md", D0)
        s4_commit(D0)
        s4_entry(root, "wiki/research/x/dup.md", D1)
        s4_entry(root, "wiki/research/y/dup.md", D1)
        p, lines, _ = s4_lu("s4d", "--full", s4_lint(D2, ["wiki/research/x/old-a.md", "_inbox/proposed/dup.md"]))
        check("left_undone_counts_entries_not_linted: a name present twice under wiki/ is not bridged, both are counted",
              f"{SEM}2 — {SEM_RAN}" in lines, lines)
        # the lint skipped because one ran within 24 hours (cycle Step 4)
        root = mknb("s4e")
        s4_entry(root, "wiki/research/x/old-a.md", D0)
        s4_commit(D0)
        now = datetime.now().astimezone()
        prior = f"{now.strftime('%Y-%m-%d')}-01"
        hist = root / "_inbox" / "reports" / prior[:10] / prior
        hist.mkdir(parents=True)
        s4_step(hist, "lint-semantic.json", "completed", (now - timedelta(hours=1)).isoformat(),
                ("semantic-scope.txt", ["wiki/research/x/old-a.md"]))
        s4_entry(root, "wiki/research/x/new-e.md", D1)
        p, lines, _ = s4_lu("s4e", "--full")
        check("left_undone_counts_entries_not_linted: no lint in a mode that runs it, one under 24 hours old: says it was skipped",
              f"{SEM}1 — the semantic lint was skipped: one ran within 24 hours ({prior})" in lines, lines)
    left_undone_counts_entries_not_linted()

    def s4_claims_nb(name, index_day, index_recopy=None):
        """old-a, old-b, old-c committed D0; an index of old-a and old-b committed `index_day`; new-d added and old-a
        re-reviewed D2. With `index_recopy` they are committed D2 and the index is written again on that day (a
        claims step that found no claims in old-c and new-d)."""
        root = mknb(name)
        for nm in ("old-a", "old-b", "old-c"):
            s4_entry(root, f"wiki/research/x/{nm}.md", D0)
        s4_commit(D0)
        idx = root / "_inbox" / "claims-index.json"
        idx.parent.mkdir(parents=True, exist_ok=True)
        idx.write_text(json.dumps({"generated": index_day, "claims": [
            {"source_entry": "research/x/old-a.md"}, {"source_entry": "research/x/old-b.md"}]}), encoding="utf-8")
        s4_commit(index_day)
        s4_entry(root, "wiki/research/x/new-d.md", D2)
        s4_entry(root, "wiki/research/x/old-a.md", D2)
        s4_entry(root, "wiki/tasks/card.md", D2)
        if index_recopy:
            s4_commit(D2)
            idx.write_text(json.dumps({"generated": index_recopy, "claims": [
                {"source_entry": "research/x/old-a.md"}, {"source_entry": "research/x/old-b.md"}]}), encoding="utf-8")
            s4_commit(index_recopy)
        return root

    def s4_claims(paths, status="completed"):
        return [dict(name="claims.json", status=status, stamp=s4_stamp(D3), scope=("claims-scope.txt", paths))]

    def left_undone_counts_entries_without_claims():
        old_c, new_d = "wiki/research/x/old-c.md", "wiki/research/x/new-d.md"
        root = mknb("s4f")
        for nm in ("old-a", "old-b", "old-c"):
            s4_entry(root, f"wiki/research/x/{nm}.md", D0)
        s4_entry(root, "wiki/tasks/card.md", D0)
        p, lines, (new, edited) = s4_lu("s4f", "--lint-only")
        check("left_undone_counts_entries_without_claims: with no claims index every entry is counted, a task card is not, "
              "with the does-not-run reason, and no scope file is written",
              p.returncode == 0 and f"{CLM}3 — {CLM_OFF}" in lines
              and sorted(k.rsplit("/", 1)[-1] for k in new) == ["left-undone-events.txt", "left-undone.txt"]
              and edited == [], (p.stderr[-300:], lines, new))
        s4_claims_nb("s4g", D1)
        p, lines, _ = s4_lu("s4g", "--lint-only")
        check("left_undone_counts_entries_without_claims: with an index only the unindexed and the revised entries are counted",
              f"{CLM}3 — {CLM_OFF}" in lines, lines)
        p, lines, _ = s4_lu("s4g", "--full")
        check("left_undone_counts_entries_without_claims: --full with no claims.json keeps the count and says the step left none",
              f"{CLM}3, not checked (the claims step left no claims.json)" in lines, lines)
        p, lines, _ = s4_lu("s4g", "--full", s4_claims([old_c, new_d], status="partial"))
        check("left_undone_counts_entries_without_claims: a partial claims step is not subtracted, the line says not checked",
              f"{CLM}3, not checked (the claims step ended partial; what it covered is unknown)" in lines, lines)
        p, lines, _ = s4_lu("s4g", "--full", [dict(name="claims.json", status="completed", text="{not json")])
        check("left_undone_counts_entries_without_claims: a claims.json that does not parse is not checked, no crash",
              p.returncode == 0 and f"{CLM}3, not checked (claims.json unreadable)" in lines, (p.stderr[-300:], lines))
        p, lines, _ = s4_lu("s4g", "--full", [dict(name="claims.json", status="completed", stamp=s4_stamp(D3))])
        check("left_undone_counts_entries_without_claims: a completed claims step with no scope file is not checked, the count kept",
              f"{CLM}3, not checked (no claims-scope.txt in the run folder)" in lines, lines)
        s4_claims_nb("s4h", D1, index_recopy=D3)
        p, lines, _ = s4_lu("s4h", "--full", s4_claims([old_c, new_d]))
        check("left_undone_counts_entries_without_claims: entries the claims step read and found no claims in are not counted",
              s4_line(lines, CLM) is None, lines)
        p, lines, _ = s4_lu("s4h", "--full", s4_claims([old_c]))
        check("left_undone_counts_entries_without_claims: one the step did not read is counted, with the ran reason",
              f"{CLM}1 — {CLM_RAN}" in lines, lines)
    left_undone_counts_entries_without_claims()

    def s4_synth_nb(name, canon=True):
        """A best-practices page, research entry r-old committed D0 and read by a synthesis completed D1; then r-new
        and a superseded r-super added (untracked) on D2."""
        root = mknb(name)
        if canon:
            s4_entry(root, "wiki/project/best-practices/bp.md", D0)
        s4_entry(root, "wiki/research/x/r-old.md", D0)
        s4_commit(D0)
        hist = root / "_inbox" / "reports" / D1 / f"{D1}-01"
        hist.mkdir(parents=True)
        s4_step(hist, "synthesis.json", "completed", s4_stamp(D1), ("synthesis-scope.txt", ["wiki/research/x/r-old.md"]))
        s4_entry(root, "wiki/research/x/r-new.md", D2)
        s4_entry(root, "wiki/research/x/r-super.md", D2, "superseded_by: r-new\n")
        return root

    def s4_synth(paths, status="completed"):
        return [dict(name="synthesis.json", status=status, stamp=s4_stamp(D3), scope=("synthesis-scope.txt", paths))]

    def left_undone_counts_entries_not_synthesised():
        r_old, r_new = "wiki/research/x/r-old.md", "wiki/research/x/r-new.md"
        s4_synth_nb("s4i")
        p, lines, (new, edited) = s4_lu("s4i", "--lint-only")
        check("left_undone_counts_entries_not_synthesised: the research entries added since the last synthesis are counted, "
              "a superseded one is not, with the does-not-run reason and no scope file written",
              p.returncode == 0 and f"{SYN}1 — {SYN_OFF}" in lines
              and sorted(k.rsplit("/", 1)[-1] for k in new) == ["left-undone-events.txt", "left-undone.txt"]
              and edited == [], (p.stderr[-300:], lines, new))
        p, lines, _ = s4_lu("s4i", "--ingest-only", s4_synth([r_new]))
        check("left_undone_counts_entries_not_synthesised: this run's completed synthesis and a scope file listing the new "
              "entry: no line", s4_line(lines, SYN) is None, lines)
        p, lines, _ = s4_lu("s4i", "--ingest-only", s4_synth([r_old]))
        check("left_undone_counts_entries_not_synthesised: a synthesis that did not read the new entry counts it, with the ran reason",
              f"{SYN}1 — {SYN_RAN}" in lines, lines)
        p, lines, _ = s4_lu("s4i", "--ingest-only", s4_synth([r_new], status="awaiting_approval"))
        check("left_undone_counts_entries_not_synthesised: a synthesis awaiting approval adds no line (Needs you has it)",
              s4_line(lines, SYN) is None, lines)
        p, lines, _ = s4_lu("s4i", "--ingest-only")
        check("left_undone_counts_entries_not_synthesised: a mode that synthesises, no synthesis.json: not checked, count kept",
              f"{SYN}1, not checked (synthesis left no synthesis.json)" in lines, lines)
        p, lines, _ = s4_lu("s4i", "--ingest-only", s4_synth([r_new], status="partial"))
        check("left_undone_counts_entries_not_synthesised: a partial synthesis is not subtracted, the line says not checked",
              f"{SYN}1, not checked (synthesis ended partial; what it covered is unknown)" in lines, lines)
        p, lines, _ = s4_lu("s4i", "--ingest-only", [dict(name="synthesis.json", status="completed", text="{not json")])
        check("left_undone_counts_entries_not_synthesised: a synthesis.json that does not parse is not checked, no crash",
              p.returncode == 0 and f"{SYN}1, not checked (synthesis.json unreadable)" in lines, (p.stderr[-300:], lines))
        p, lines, _ = s4_lu("s4i", "--ingest-only", [dict(name="synthesis.json", status="completed", stamp=s4_stamp(D3))])
        check("left_undone_counts_entries_not_synthesised: a completed synthesis with no scope file is not checked, count kept",
              f"{SYN}1, not checked (no synthesis-scope.txt in the run folder)" in lines, lines)
        s4_synth_nb("s4j", canon=False)
        p, lines, _ = s4_lu("s4j", "--lint-only")
        check("left_undone_counts_entries_not_synthesised: with no best-practices page there is nothing to synthesise into, no line",
              s4_line(lines, SYN) is None, lines)
    left_undone_counts_entries_not_synthesised()

    # ── left-undone step 5: lint findings, semantic findings, the fixes record, earlier runs' findings ──
    S5_LINT, S5_EARLY, S5_LATE = "2026-10-04T12:00:00-04:00", "2026-10-04T10:00:00-04:00", "2026-10-04T14:00:00-04:00"
    S5_KINDS = {"files_scanned": 9, "broken_links": 2, "orphans": 0, "unquoted_yaml": 1, "standalone": 3,
                "backlink_blocks_out_of_step": 4}
    NO_FIX = "no fix step in this mode"
    STILL = "still present after the cycle Step 5 fixes (not approved, declined, or no fix step covers this kind)"
    GUARD = "- Lint findings: not checked (the lint predates cycle Step 5; re-run the mechanical lint)"
    SEMF = "- Semantic findings: "
    S5_WAY = "the findings are in lint-semantic.md and no later cycle step shows them again"
    NO_USABLE = f"{SEMF}not checked (lint-semantic.json has no usable findings list)"

    def s5_file(name, content):
        return dict(name=name, status="", text=content if isinstance(content, str) else json.dumps(content))

    def s5_lint(summary=S5_KINDS, status="completed", not_checked=(), stamp=S5_LINT):
        return s5_file("lint-mechanical.json", {"status": status, "timestamp": stamp, "not_checked": list(not_checked),
                                                "summary": summary})

    def s5_fixes(applied="", declined="", at=S5_EARLY):
        return s5_file("lint-fixes.txt", f"applied: {applied}\ndeclined: {declined}\nat: {at}\n")

    def s5_findings(n):
        return [{"file": f"wiki/research/x/f{i}.md", "category": "drift", "severity": "high", "detail": f"detail {i}",
                 "evidence": "e", "suggested_fix": "s", "agent": "a"} for i in range(1, n + 1)]

    def s5_sem_rec(n, status="completed", not_checked=(), stamp=S5_LINT):
        return {"status": status, "timestamp": stamp, "not_checked": list(not_checked), "summary": {"findings": n},
                "findings": s5_findings(n)}

    def s5_sem(n, status="completed", not_checked=(), stamp=S5_LINT):
        return s5_file("lint-semantic.json", s5_sem_rec(n, status, not_checked, stamp))

    def left_undone_names_lint_findings():
        s5a = mknb("s5a")
        p, lines, (new, edited) = s4_lu("s5a", "--lint-only", [s5_lint()])
        check("left_undone_names_lint_findings: a lint of 2 broken links and 1 unquoted yaml gives those two lines and "
              "none for files_scanned, standalone, backlink_blocks_out_of_step or the zero kind, in a mode with no fix step",
              p.returncode == 0 and lines == ["Left undone: 2 queue(s)", f"- Lint broken links: 2 — {NO_FIX}",
                                              f"- Lint unquoted yaml: 1 — {NO_FIX}"], (p.stderr[-300:], lines))
        check("left_undone_names_lint_findings: only left-undone.txt and its events file are new and nothing changed",
              sorted(k.rsplit("/", 1)[-1] for k in new) == ["left-undone-events.txt", "left-undone.txt"] and edited == [],
              (new, edited))
        p, lines, _ = s4_lu("s5a", "--full", [s5_lint(), s5_fixes()])
        check("left_undone_names_lint_findings: --full with a fixes record and a lint stamped after it says each kind is "
              "still present after the Step 5 fixes",
              f"- Lint broken links: 2 — {STILL}" in lines and f"- Lint unquoted yaml: 1 — {STILL}" in lines, lines)
        p, lines, _ = s4_lu("s5a", "--full", [s5_lint()])
        check("left_undone_names_lint_findings: --full with no lint-fixes.txt keeps the counts and says the fix step left none",
              "- Lint broken links: 2, not checked (the fix step left no lint-fixes.txt)" in lines
              and "- Lint unquoted yaml: 1, not checked (the fix step left no lint-fixes.txt)" in lines, lines)
        p, lines, _ = s4_lu("s5a", "--full", [s5_lint(), s5_fixes(at=S5_LATE)])
        check("left_undone_names_lint_findings: a fixes record with zero ids and a lint stamped before it gives one guard "
              "line and no counts",
              GUARD in lines and not [l for l in lines if l.startswith("- Lint broken") or l.startswith("- Lint unquoted")],
              lines)
        p, lines, _ = s4_lu("s5a", "--full", [s5_lint(), s5_fixes(at="not a time")])
        check("left_undone_names_lint_findings: a fixes record whose at: cannot be read cannot prove the lint is later, so the guard fires",
              GUARD in lines, lines)
        p, lines, _ = s4_lu("s5a", "--lint-only", [s5_lint(), s5_fixes(at=S5_LATE)])
        check("left_undone_names_lint_findings: the guard fires whenever lint-fixes.txt exists, in any mode",
              GUARD in lines, lines)
        p, lines, _ = s4_lu("s5a", "--lint-only", [s5_lint({"files_scanned": 4, "broken_links": 2}, status="partial",
                                                           not_checked=["no entries", "qmd is not on PATH"])])
        check("left_undone_names_lint_findings: a partial lint gives one not-checked line per part, no counts, never nothing",
              "- Lint: not checked — no entries" in lines and "- Lint: not checked — qmd is not on PATH" in lines
              and not [l for l in lines if l.startswith("- Lint broken")] and lines[:1] == ["Left undone: 2 queue(s)"], lines)
        p, lines, _ = s4_lu("s5a", "--lint-only", [s5_lint({"files_scanned": 4, "broken_links": 0}, status="partial",
                                                           not_checked=["no entries"])])
        check("left_undone_names_lint_findings: a partial lint with all-zero counts still names what it did not check",
              "- Lint: not checked — no entries" in lines, lines)
        p, lines, _ = s4_lu("s5a", "--lint-only")
        check("left_undone_names_lint_findings: a mode that lints and left no lint-mechanical.json: not checked",
              "- Lint findings: not checked (the mechanical lint left no lint-mechanical.json)" in lines, lines)
        p, lines, _ = s4_lu("s5a", "--discover-only")
        check("left_undone_names_lint_findings: a mode that does not lint says no lint ran this cycle",
              "- Lint findings: not checked (no lint ran this cycle; /wiki-cycle --lint-only)" in lines, lines)
        p, lines, _ = s4_lu("s5a", None)
        check("left_undone_names_lint_findings: an unknown mode with no lint adds no lint line (the Mode line covers it)",
              not [l for l in lines if l.startswith("- Lint")] and lines[:1] == ["Left undone: 1 queue(s)"], lines)
        p, lines, _ = s4_lu("s5a", None, [s5_lint()])
        check("left_undone_names_lint_findings: an unknown mode with a lint keeps the counts and says not checked",
              "- Lint broken links: 2, not checked (cannot read the mode from scratchpad.md)" in lines, lines)
        p, lines, _ = s4_lu("s5a", "--lint-only", [s5_lint({"files_scanned": 9, "broken_links": 0, "standalone": 3})])
        check("left_undone_names_lint_findings: a completed lint of all zeros adds no lint line",
              not [l for l in lines if l.startswith("- Lint")], lines)
        p, lines, _ = s4_lu("s5a", "--lint-only", [s5_file("lint-mechanical.json", "{not json")])
        check("left_undone_names_lint_findings: a lint-mechanical.json that does not parse is not checked, no crash",
              p.returncode == 0 and "- Lint findings: not checked (lint-mechanical.json unreadable)" in lines,
              (p.stderr[-300:], lines))
        p, lines, _ = s4_lu("s5a", "--lint-only", [s5_lint(status="failed")])
        check("left_undone_names_lint_findings: a lint that ended failed is not checked",
              "- Lint findings: not checked (the mechanical lint ended failed)" in lines, lines)
    left_undone_names_lint_findings()

    def left_undone_does_not_read_a_lint_with_no_summary_as_clean():
        mknb("s5a2")
        for what, summary in (("no summary key", None), ("a summary that is not an object", [1, 2])):
            rec = {"status": "completed", "timestamp": S5_LINT, "not_checked": []}
            if summary is not None:
                rec["summary"] = summary
            p, lines, _ = s4_lu("s5a2", "--lint-only", [s5_file("lint-mechanical.json", rec)])
            check(f"left_undone_does_not_read_a_lint_with_no_summary_as_clean: a completed lint with {what} reads not "
                  "checked, never clean",
                  p.returncode == 0 and "- Lint findings: not checked (lint-mechanical.json has no usable summary)" in lines,
                  (p.returncode, p.stderr[-200:], lines))
    left_undone_does_not_read_a_lint_with_no_summary_as_clean()

    def lint_fixes_prints_the_numbered_findings():
        root = mknb("s5b0")
        rf = lu_run(root, "2026-10-05-05", cycle="--full")
        finds = s5_findings(5)
        finds[0]["detail"] = "abcdefghij" * 15
        finds[1]["detail"] = "line one\nline two"
        (rf / "lint-semantic.json").write_text(json.dumps({**s5_sem_rec(5), "findings": finds}), encoding="utf-8")
        bare = lu_run(root, "2026-10-05-06", cycle="--full")
        before = tree(root)
        p = run_on("s5b0", "lint-fixes", "--run-folder", str(rf), "--show")
        want = [f"1. [drift] wiki/research/x/f1.md — {'abcdefghij' * 10}", "2. [drift] wiki/research/x/f2.md — line one line two"] \
            + [f"{i}. [drift] wiki/research/x/f{i}.md — detail {i}" for i in (3, 4, 5)]
        check("lint_fixes_prints_the_numbered_findings: --show prints one numbered line per finding, 100 characters of "
              "detail at most, a newline in it flattened, and records nothing",
              p.returncode == 0 and p.stdout.splitlines() == want and tree(root) == before, (p.returncode, p.stdout, p.stderr[-200:]))
        p = run_on("s5b0", "lint-fixes", "--run-folder", str(bare), "--show")
        check("lint_fixes_prints_the_numbered_findings: --show with no lint-semantic.json says so and exits 0",
              p.returncode == 0 and "no lint-semantic.json" in p.stdout, (p.returncode, p.stdout))
    lint_fixes_prints_the_numbered_findings()

    def lint_fixes_writes_the_fixes_record():
        root = mknb("s5b")
        rf = lu_run(root, "2026-10-05-01", cycle="--full")
        (rf / "lint-semantic.json").write_text(json.dumps(s5_sem_rec(5)), encoding="utf-8")

        def lf(*a, folder=rf):
            return run_on("s5b", "lint-fixes", "--run-folder", str(folder), *a)
        before = tree(root)
        p = lf("--applied", "2,1,1", "--declined", "3")
        txt = (rf / "lint-fixes.txt").read_text(encoding="utf-8").splitlines() if (rf / "lint-fixes.txt").is_file() else []
        from datetime import datetime
        at = None
        try:
            at = datetime.fromisoformat(txt[2][len("at: "):]) if len(txt) == 3 and txt[2].startswith("at: ") else None
        except ValueError:
            pass
        after = tree(root)
        check("lint_fixes_writes_the_fixes_record: --applied and --declined write the ids sorted and once each, "
              "with a tz-aware at: stamp, in lint-fixes.txt, and nothing else is new",
              p.returncode == 0 and txt[:2] == ["applied: 1,2", "declined: 3"] and at is not None and at.tzinfo is not None
              and [k.rsplit("/", 1)[-1] for k in after if k not in before] == ["lint-fixes.txt"]
              and [k for k, v in before.items() if after.get(k) != v] == [], (p.returncode, p.stderr[-200:], txt))
        (rf / "lint-fixes.txt").unlink(missing_ok=True)
        p = lf()
        txt = (rf / "lint-fixes.txt").read_text(encoding="utf-8").splitlines() if (rf / "lint-fixes.txt").is_file() else []
        check("lint_fixes_writes_the_fixes_record: no ids at all writes two empty lists and the stamp",
              p.returncode == 0 and txt[:2] == ["applied:", "declined:"] and len(txt) == 3, (p.returncode, txt))
        bare = lu_run(root, "2026-10-05-02", cycle="--full")
        p = lf(folder=bare)
        txt = (bare / "lint-fixes.txt").read_text(encoding="utf-8").splitlines() if (bare / "lint-fixes.txt").is_file() else []
        check("lint_fixes_writes_the_fixes_record: with no lint-semantic.json it writes empty lists and exits 0",
              p.returncode == 0 and txt[:2] == ["applied:", "declined:"], (p.returncode, p.stderr[-200:], txt))
    lint_fixes_writes_the_fixes_record()

    def lint_fixes_refuses_ids_it_cannot_place():
        root = mknb("s5c0")
        rf = lu_run(root, "2026-10-05-03", cycle="--full")
        (rf / "lint-semantic.json").write_text(json.dumps(s5_sem_rec(5)), encoding="utf-8")
        bare = lu_run(root, "2026-10-05-04", cycle="--full")
        p = run_on("s5c0", "lint-fixes", "--run-folder", str(rf), "--applied", "5", "--declined", "1")
        check("lint_fixes_refuses_ids_it_cannot_place: control: ids inside 1..5 and in one list each are accepted",
              p.returncode == 0 and (rf / "lint-fixes.txt").is_file(), (p.returncode, p.stderr[-200:]))
        (rf / "lint-fixes.txt").unlink(missing_ok=True)
        cases = [("an id of 0", rf, ["--applied", "0"]), ("an id past the list", rf, ["--declined", "6"]),
                 ("a non-numeric id", rf, ["--applied", "1,x"]), ("a negative id", rf, ["--declined", "-1"]),
                 ("an id in both lists", rf, ["--applied", "1,2", "--declined", "2"]),
                 ("--show with ids", rf, ["--show", "--applied", "1"]),
                 ("an id with no lint-semantic.json", bare, ["--applied", "1"])]
        for what, folder, extra in cases:
            p = run_on("s5c0", "lint-fixes", "--run-folder", str(folder), *extra)
            check(f"lint_fixes_refuses_ids_it_cannot_place: {what} exits 2, says why and writes no lint-fixes.txt",
                  p.returncode == 2 and p.stderr.strip() != "" and not (folder / "lint-fixes.txt").exists(),
                  (p.returncode, p.stderr[-200:]))
        p = run_on("s5c0", "lint-fixes", "--run-folder", str(root / "nowhere"), "--applied", "1")
        check("lint_fixes_refuses_ids_it_cannot_place: a run folder that is not there exits 2 and creates nothing",
              p.returncode == 2 and not (root / "nowhere").exists(), (p.returncode, p.stderr[-200:]))
    lint_fixes_refuses_ids_it_cannot_place()

    def left_undone_counts_semantic_findings():
        mknb("s5c")
        p, lines, _ = s4_lu("s5c", "--full", [s5_sem(5), s5_fixes("1,2", "3")])
        rid = f"{D3}-{s4_runs[0]:02d}"
        check("left_undone_counts_semantic_findings: --full, 5 findings, 2 applied and 1 declined: 2 awaiting, with the "
              "truthful way out naming this run",
              f"{SEMF}2 — awaiting your approval; the findings are in lint-semantic.md (run {rid}); no later cycle step "
              "shows them again" in lines, lines)
        p, lines, _ = s4_lu("s5c", "--lint-only --semantic", [s5_sem(5)])
        check("left_undone_counts_semantic_findings: --lint-only --semantic counts all 5 with no fix step in this mode",
              f"{SEMF}5 — {NO_FIX}; {S5_WAY}" in lines, lines)
        p, lines, _ = s4_lu("s5c", "--full", [s5_sem(5)])
        check("left_undone_counts_semantic_findings: --full with 5 findings and no lint-fixes.txt keeps the count and says "
              "applied and declined were not recorded",
              f"{SEMF}5, not checked (the fix step left no lint-fixes.txt: applied and declined were not recorded)" in lines,
              lines)
        p, lines, _ = s4_lu("s5c", "--full", [s5_sem(0), s5_fixes()])
        none_empty = not [l for l in lines if l.startswith(SEMF)]
        p, lines, _ = s4_lu("s5c", "--full", [s5_sem(5), s5_fixes("1,2,3", "4,5,9")])
        check("left_undone_counts_semantic_findings: 0 findings, or a record covering every finding (one id beyond the "
              "list too), gives no line and never a negative count",
              none_empty and not [l for l in lines if l.startswith(SEMF)], lines)
        p, lines, _ = s4_lu("s5c", "--full", [s5_sem(5, status="partial"), s5_fixes("1", "")])
        check("left_undone_counts_semantic_findings: a partial semantic lint with a usable list prints the figure the "
              "complete line would print, with not checked",
              f"{SEMF}4, not checked (the semantic lint ended partial)" in lines, lines)
        p, lines, _ = s4_lu("s5c", "--full", [s5_sem(5, status="partial")])
        check("left_undone_counts_semantic_findings: a partial lint with no fixes record prints all 5, with not checked",
              f"{SEMF}5, not checked (the semantic lint ended partial)" in lines, lines)
        p, lines, _ = s4_lu("s5c", "--full", [s5_sem(5, not_checked=["two entries unread", "no scope"]), s5_fixes()])
        check("left_undone_counts_semantic_findings: a top-level not_checked of 2 gives one parts-not-checked line",
              "- Semantic lint, parts not checked: 2 — two entries unread; no scope" in lines, lines)
        bad = {"status": "completed", "timestamp": S5_LINT, "summary": {"findings": 5}}
        for what, rec in (("no findings key", bad), ("a findings value that is not a list", {**bad, "findings": "x"}),
                          ("a length that disagrees with summary.findings", {**s5_sem_rec(5), "summary": {"findings": 4}})):
            p, lines, _ = s4_lu("s5c", "--full", [s5_file("lint-semantic.json", rec), s5_fixes()])
            check(f"left_undone_counts_semantic_findings: {what} reads not checked, never zero", NO_USABLE in lines, lines)
        p, lines, _ = s4_lu("s5c", "--full", [s5_file("lint-semantic.json", "{not json")])
        check("left_undone_counts_semantic_findings: a lint-semantic.json that does not parse is not checked, no crash",
              p.returncode == 0 and f"{SEMF}not checked (lint-semantic.json unreadable)" in lines, (p.stderr[-300:], lines))
        p, lines, _ = s4_lu("s5c", "--full")
        p2, lines2, _ = s4_lu("s5c", "--lint-only")
        check("left_undone_counts_semantic_findings: a mode that runs the lint and left no lint-semantic.json says so; one "
              "that does not run it adds no line",
              f"{SEMF}not checked (the semantic lint left no lint-semantic.json)" in lines
              and not [l for l in lines2 if l.startswith(SEMF)], (lines, lines2))
        p, lines, _ = s4_lu("s5c", "--full", [s5_sem(5), s5_file("lint-fixes.txt", "garbage\n")])
        check("left_undone_counts_semantic_findings: a lint-fixes.txt with no applied and declined lines is unreadable",
              f"{SEMF}5, not checked (lint-fixes.txt unreadable)" in lines, lines)
        p, lines, _ = s4_lu("s5c", None, [s5_sem(5), s5_fixes("1", "")])
        check("left_undone_counts_semantic_findings: an unknown mode keeps the figure and says not checked",
              f"{SEMF}4, not checked (cannot read the mode from scratchpad.md)" in lines, lines)
    left_undone_counts_semantic_findings()

    def s5_hist(root, day, nth, n, status="completed", note=None):
        """An earlier run folder holding a semantic lint of `n` findings (and, with `note` = (applied, declined), its
        fixes record); returns the run id."""
        d = root / "_inbox" / "reports" / day / f"{day}-{nth:02d}"
        d.mkdir(parents=True)
        (d / "lint-semantic.json").write_text(json.dumps(s5_sem_rec(n, status, stamp=f"{day}T09:00:00-04:00")),
                                              encoding="utf-8")
        if note is not None:
            (d / "lint-fixes.txt").write_text(f"applied: {note[0]}\ndeclined: {note[1]}\nat: {day}T10:00:00-04:00\n",
                                              encoding="utf-8")
        return d.name

    def left_undone_names_semantic_findings_from_earlier_runs():
        import ast
        root = mknb("s5d")
        l0 = s5_hist(root, "2026-09-20", 1, 0, note=("", ""))
        l1 = s5_hist(root, "2026-09-21", 1, 5, note=("1,2", "3"))
        part = s5_hist(root, "2026-09-22", 1, 5, status="partial")
        l2 = s5_hist(root, "2026-09-22", 2, 3)
        l3 = s5_hist(root, "2026-09-23", 1, 2)
        l4 = s5_hist(root, "2026-09-24", 1, 0, note=("", ""))
        SUP = (f"- Semantic findings from {l1}: 2, superseded by a newer lint; no longer shown in full; the findings are "
               f"in lint-semantic.md (run {l1}); no later cycle step shows them again")
        COLL = "- 2 earlier lints recorded no applied or declined findings; no longer shown in full"

        def old_lines(lines):
            return [l for l in lines if l.startswith("- Semantic findings from ") or "earlier lint" in l]
        p, lines, _ = s4_lu("s5d", "--ingest-only")
        check("left_undone_names_semantic_findings_from_earlier_runs: an older lint with unresolved findings gets a "
              "superseded line though the newest lint found nothing, the two older ones with no fixes record collapse into "
              "one line, and an empty list, the newest and a partial lint add nothing",
              old_lines(lines) == [SUP, COLL] and not [l for l in lines if part in l or l0 in l or l4 in l],
              old_lines(lines))
        check("left_undone_names_semantic_findings_from_earlier_runs: the header counts those lines",
              lines[:1] == ["Left undone: 4 queue(s)"], lines[:1])
        p, lines, _ = s4_lu("s5d", "--full", [s5_sem(1), s5_fixes("1", "")])
        check("left_undone_names_semantic_findings_from_earlier_runs: a --full run whose own lint is the newest still "
              "prints the older lints' lines", old_lines(lines) == [SUP, COLL], old_lines(lines))
        p, lines, _ = s4_lu("s5d", "--lint-only --semantic", [s5_sem(5)])
        check("left_undone_names_semantic_findings_from_earlier_runs: so does a --lint-only --semantic run, beside its own line",
              old_lines(lines) == [SUP, COLL] and f"{SEMF}5 — {NO_FIX}; {S5_WAY}" in lines, lines)
        doc = ast.get_docstring(ast.parse(SCRIPT.read_text(encoding="utf-8"))) or ""
        check("left_undone_names_semantic_findings_from_earlier_runs: the docstring says only completed lints are read, "
              "so an older partial lint is not",
              "only completed lints are read" in doc and "partial" in doc[doc.find("only completed lints are read") - 300:][:600],
              doc[doc.find("only completed lints"):][:200])
        one = mknb("s5e")
        x = s5_hist(one, "2026-09-21", 1, 5, note=("1,2", "3"))
        p, lines, _ = s4_lu("s5e", "--ingest-only")
        check("left_undone_names_semantic_findings_from_earlier_runs: a run with no lint of its own names the newest lint's "
              "unresolved findings, with where they are and that fixes made by hand are not seen",
              f"- Semantic findings from {x}: 2 — awaiting your approval; the findings are in lint-semantic.md (run {x}); "
              "no later cycle step shows them again; fixes made by hand since are not seen" in lines, lines)
        none = mknb("s5f")
        y = s5_hist(none, "2026-09-21", 1, 4)
        p, lines, _ = s4_lu("s5f", "--ingest-only")
        check("left_undone_names_semantic_findings_from_earlier_runs: an earlier lint with no fixes record is not checked, count kept",
              f"- Semantic findings from {y}: 4, not checked (that run recorded no applied or declined findings)" in lines,
              lines)
        un = mknb("s5g")
        z = "2026-09-21-01"
        d = un / "_inbox" / "reports" / "2026-09-21" / z
        d.mkdir(parents=True)
        (d / "lint-semantic.json").write_text(json.dumps({"status": "completed", "timestamp": "2026-09-21T09:00:00-04:00"}),
                                              encoding="utf-8")
        p, lines, _ = s4_lu("s5g", "--ingest-only")
        check("left_undone_names_semantic_findings_from_earlier_runs: an earlier lint with no usable findings list is not checked",
              f"- Semantic findings from {z}: not checked (lint-semantic.json has no usable findings list)" in lines, lines)
        done = mknb("s5h")
        s5_hist(done, "2026-09-21", 1, 5, note=("1,2,3", "4,5"))
        p, lines, _ = s4_lu("s5h", "--ingest-only")
        check("left_undone_names_semantic_findings_from_earlier_runs: an earlier lint every finding of which was answered adds nothing",
              old_lines(lines) == [], lines)
    left_undone_names_semantic_findings_from_earlier_runs()

    # ── left-undone step 6: sources, tier-4 deferrals, --report-only's copy of the last run, no interim form ──
    s6_runs = [0]

    def s6_run(topic, cycle, files=(), cid=None, report=False):
        """A fresh run folder (`cid`, else the next id of a counter) on notebook `topic` holding `files` (name, JSON
        object or raw text); (run folder, process, left-undone lines)."""
        s6_runs[0] += 1
        cid = cid or f"2026-10-06-{s6_runs[0]:02d}"
        rf = lu_run(tmp / "notebooks" / topic, cid, cycle=cycle)
        for name, content in files:
            (rf / name).write_text(content if isinstance(content, str) else json.dumps(content), encoding="utf-8")
        if report:
            (rf / f"{cid}-run-cycle-report.md").write_text("# report\n", encoding="utf-8")
        p, lines = lu(topic, rf)
        return rf, p, lines

    def s6_update(**lists):
        return {"status": "completed", "skipped": [], "deferred": [], "errors": [], **lists}

    def left_undone_names_each_source_the_run_left():
        root = mknb("s6a")
        intake = root / "_inbox" / "intake" / "main"
        intake.mkdir(parents=True)
        (intake / "held.md").write_text("---\nsource: https://x.test/held\nretry: slow (2026-10-05, cycle x)\n---\n",
                                        encoding="utf-8")
        (intake / "pdf.md").write_text("---\nsource: https://x.test/pdf\nsave_as_pdf: paywall\n---\n", encoding="utf-8")
        (intake / "plain.md").write_text("---\nsource: https://x.test/plain\n---\n", encoding="utf-8")
        upd = s6_update(skipped=[{"url": "https://x.test/skip", "reason": "thin content"}, {"slug": "a-slug", "reason": "dup"},
                                 {"url": "https://x.test/noreason"}],
                        deferred=[{"url": "https://x.test/def", "reason": "429"}, {"url": "https://x.test/held", "reason": "slow"},
                                  {"url": "https://x.test/pdf", "reason": "paywall"}, {"url": "https://x.test/plain", "reason": "429"}],
                        errors=[{"code": "E1", "message": "boom", "item": "https://x.test/err"}])
        dis = s6_update(skipped=[{"url": "https://x.test/low", "reason": "LOW relevance"},
                                 {"url": "https://x.test/cov", "reason": "already covered by x"}])
        rf, p, lines = s6_run("s6a", "--quick", [("update.json", upd), ("discover.json", dis)])
        want = ["- Source https://x.test/skip: skipped — thin content", "- Source a-slug: skipped — dup",
                "- Source https://x.test/noreason: skipped — (no reason recorded)",
                "- Source https://x.test/def: deferred — 429", "- Source https://x.test/plain: deferred — 429",
                "- Source https://x.test/err: failed — boom", "- Source https://x.test/low: skipped — LOW relevance"]
        got = [l for l in lines if l.startswith("- Source")]
        check("left_undone_names_each_source_the_run_left: each skipped, deferred and failed source is a line "
              "with its reason as the file holds it, the discovery drop 'already covered' and the two sources whose ticket "
              "carries retry: or save_as_pdf: left out", sorted(got) == sorted(want), got)
        n = len([l for l in lines if l.startswith("- ")])
        check("left_undone_names_each_source_the_run_left: the header counts them",
              lines[:1] == ["Left undone: 9 queue(s)"] and n == 9, (lines[:1], n))
        ev = rf / "left-undone-events.txt"
        events = ev.read_text(encoding="utf-8").splitlines() if ev.is_file() else []
        check("left_undone_names_each_source_the_run_left: the events file holds the same source lines under a # header",
              events[:1] and events[0].startswith("#") and [l for l in events if l.startswith("- Source")] == got, events)
        _, p, lines = s6_run("s6a", "--ingest-only")
        check("left_undone_names_each_source_the_run_left: a mode that ingests and left no update.json is not checked",
              "- Sources: not checked (ingest left no update.json)" in lines, lines)
        _, p, lines = s6_run("s6a", "--quick", [("update.json", s6_update())])
        check("left_undone_names_each_source_the_run_left: a mode that discovers and left no discover.json is not checked",
              "- Sources: not checked (discovery left no discover.json)" in lines
              and not [l for l in lines if "update.json" in l], lines)
        _, p, lines = s6_run("s6a", "--lint-only")
        check("left_undone_names_each_source_the_run_left: a mode that neither ingests nor discovers adds no source line",
              not [l for l in lines if l.startswith(("- Source", "- Tier-4"))], lines)
        _, p, lines = s6_run("s6a", "--quick", [("update.json", "{not json"), ("discover.json", s6_update())])
        check("left_undone_names_each_source_the_run_left: an update.json that does not parse is not checked, no crash",
              p.returncode == 0 and "- Sources: not checked (update.json unreadable)" in lines, (p.stderr[-300:], lines))
        _, p, lines = s6_run("s6a", None, [("update.json", upd)])
        check("left_undone_names_each_source_the_run_left: an unknown mode with no discover.json adds no 'left no' line (the Mode line says it)",
              not [l for l in lines if l.startswith("- Sources")] and "- Source https://x.test/skip: skipped — thin content" in lines,
              lines)
    left_undone_names_each_source_the_run_left()

    T4 = "- Source https://x.test/t4a: deferred — tier 4: needs your review (--no-confirm-discovery)"
    CHECKLIST = ("# Discovery 2026-10-06\n\n- [ ] **1.** [A](https://x.test/t4a) — tier 4 — **Why**: new (NEEDS HUMAN REVIEW)\n"
                 "- [ ] **2.** [B](https://x.test/t3) — tier 3 — **Why**: (NEEDS HUMAN REVIEW) not tier 4\n"
                 "- [x] **3.** [C](https://x.test/t4done) — tier 4 — **Why**: ticked\n"
                 "- [ ] **4.** [D](https://x.test/t4held) — tier 4 — **Why**: already queued\n")

    def s6_tier_nb(name, where="done", text=CHECKLIST):
        root = mknb(name)
        if where:
            (root / "_inbox" / where).mkdir(parents=True, exist_ok=True)
            (root / "_inbox" / where / "2026-10-06-discovery.md").write_text(text, encoding="utf-8")
        pend = root / "_inbox" / "pending"
        pend.mkdir(parents=True, exist_ok=True)
        (pend / "held.md").write_text("---\nsource: https://x.test/t4held\n---\n", encoding="utf-8")
        return root

    def left_undone_names_deferred_tier_4_sources():
        dis = [("discover.json", s6_update()), ("update.json", s6_update())]
        s6_tier_nb("s6b")
        _, p, lines = s6_run("s6b", "--quick, --no-confirm-discovery", dis)
        got = [l for l in lines if l.startswith(("- Source", "- Tier-4"))]
        check("left_undone_names_deferred_tier_4_sources: with discover.json and the flag, a checklist in _inbox/done/ gives "
              "one line for the unticked tier-4 candidate not held anywhere, none for tier 3, a ticked one or a held one",
              got == [T4], (p.stderr[-300:], got))
        s6_tier_nb("s6c", where="discovered")
        _, p, lines = s6_run("s6c", "--quick, --no-confirm-discovery", dis)
        check("left_undone_names_deferred_tier_4_sources: the same checklist in _inbox/discovered/ gives the same line",
              [l for l in lines if l.startswith(("- Source", "- Tier-4"))] == [T4], lines)
        _, p, lines = s6_run("s6c", "--quick", dis)
        check("left_undone_names_deferred_tier_4_sources: no --no-confirm-discovery in the scratchpad adds no tier-4 line (the stated silent miss)",
              not [l for l in lines if l.startswith(("- Source", "- Tier-4"))], lines)
        _, p, lines = s6_run("s6c", "--ingest-only, --no-confirm-discovery", [("update.json", s6_update())])
        check("left_undone_names_deferred_tier_4_sources: a run with no discover.json adds no tier-4 line, whatever an earlier run left",
              not [l for l in lines if l.startswith(("- Source", "- Tier-4"))], lines)
        s6_tier_nb("s6d", where=None)
        _, p, lines = s6_run("s6d", "--quick, --no-confirm-discovery", dis)
        check("left_undone_names_deferred_tier_4_sources: no checklist in either folder is not checked, with the date",
              "- Tier-4 sources: not checked (no discovery checklist for 2026-10-06)" in lines, lines)
        s6_tier_nb("s6e2", text="- [ ] **1.** [T](https://x.test/t2) — tier 2 — **Why**: z\n")
        _, p, lines = s6_run("s6e2", "--quick, --no-confirm-discovery", dis)
        check("left_undone_names_deferred_tier_4_sources: a checklist with no tier-4 candidate adds no line",
              not [l for l in lines if l.startswith(("- Source", "- Tier-4"))], lines)
    left_undone_names_deferred_tier_4_sources()

    def left_undone_repeats_the_last_runs_events_when_only_reporting():
        root = mknb("s6f")
        page(root, "wiki/research/x/none-a.md")
        a, p, lines = s6_run("s6f", "--quick", [("update.json", s6_update(skipped=[{"url": "https://x.test/skip",
                                                                                   "reason": "thin content"}])),
                                                ("discover.json", s6_update())], cid="2026-10-07-01", report=True)
        s6_run("s6f", "--full", cid="2026-10-07-02")
        b, p, lines_b = s6_run("s6f", "--report-only", cid="2026-10-07-03", report=True)
        c, p, lines_c = s6_run("s6f", "--report-only", cid="2026-10-07-04")
        src = "- Source https://x.test/skip: skipped — thin content"
        ev = a / "left-undone-events.txt"
        a_events = ev.read_text(encoding="utf-8").splitlines() if ev.is_file() else []
        check("left_undone_repeats_the_last_runs_events_when_only_reporting: the events file of a run that is not "
              "--report-only holds its event lines under a # header",
              a_events[:1] and a_events[0].startswith("#") and src in a_events, a_events)
        check("left_undone_repeats_the_last_runs_events_when_only_reporting: a --report-only run copies them with "
              "(from <id>), counts them in the header, and skips an unreported run",
              lines_b[1:2] == ["Disk-state queues are counted now; event lines are from the last run (2026-10-07-01)"]
              and f"{src} (from 2026-10-07-01)" in lines_b
              and lines_b[:1] == ["Left undone: 5 queue(s)"], lines_b)
        check("left_undone_repeats_the_last_runs_events_when_only_reporting: its own run says no lint ran and counts "
              "the disk-state queues fresh",
              not [l for l in lines_b if l.startswith("- Lint findings: not checked (no lint ran")]
              and any(l.startswith("- No review_after: 1 —") for l in lines_b), lines_b)
        check("left_undone_repeats_the_last_runs_events_when_only_reporting: a --report-only run writes no events file, "
              "and another report-only run after it still cites the last full run",
              not (b / "left-undone-events.txt").exists() and not (c / "left-undone-events.txt").exists()
              and f"{src} (from 2026-10-07-01)" in lines_c, (sorted(p.name for p in b.iterdir()), lines_c))
        mknb("s6g")
        _, p, lines = s6_run("s6g", "--report-only", cid="2026-10-08-02")
        check("left_undone_repeats_the_last_runs_events_when_only_reporting: no earlier run with a report is not checked",
              "- Events of the last run: not checked (no earlier run with a report)" in lines, lines)
        s6_run("s6g", "--full", cid="2026-10-09-01", report=True)
        (tmp / "notebooks" / "s6g" / "_inbox" / "reports" / "2026-10-09" / "2026-10-09-01" / "left-undone-events.txt").unlink(missing_ok=True)
        _, p, lines = s6_run("s6g", "--report-only", cid="2026-10-09-02")
        check("left_undone_repeats_the_last_runs_events_when_only_reporting: a last run with no events file is not checked",
              "- Events of the last run: not checked (that run left no left-undone-events.txt)" in lines
              and lines[:1] == ["Left undone: 1 queue(s)"], lines)
    left_undone_repeats_the_last_runs_events_when_only_reporting()

    def left_undone_drops_the_interim_form():
        mknb("s6h")
        _, p, lines = s6_run("s6h", "--lint-only", [("lint-mechanical.json", {"status": "completed", "timestamp": S5_LINT,
                                                                             "not_checked": [], "summary": {"files_scanned": 1}})])
        check("left_undone_drops_the_interim_form: a run with nothing counted is exactly Left undone: nothing",
              p.returncode == 0 and lines == ["Left undone: nothing"], (p.stderr[-300:], lines))
        page(tmp / "notebooks" / "s6h", "wiki/research/x/none-a.md")
        _, p, lines = s6_run("s6h", "--lint-only")
        check("left_undone_drops_the_interim_form: with queues the header counts them and no Not counted yet line or "
              "disk-state header is written",
              lines[0].startswith("Left undone: ") and lines[0].endswith(" queue(s)") and lines[-1].startswith("- ")
              and not [l for l in lines if l.startswith(("Not counted yet", "Left undone (disk-state"))], lines)
    left_undone_drops_the_interim_form()

    def left_undone_reads_nothing_after_a_fully_answered_full_run():
        root = mknb("s6i")
        for rel, day in (("old-a", D0), ("old-b", D0), ("claimless", D0), ("promoted", D1), ("reviewed-late", D1)):
            s4_entry(root, f"wiki/research/x/{rel}.md", day)
        s4_entry(root, "wiki/project/best-practices/bp.md", D0)
        page(root, "wiki/tasks/card.md")
        s4_commit(D0)
        (root / "_inbox").mkdir(exist_ok=True)
        (root / "_inbox" / "claims-index.json").write_text(json.dumps({"claims": [
            {"source_entry": f"research/x/{n}.md"} for n in ("old-a", "old-b", "promoted", "reviewed-late")]
            + [{"source_entry": "project/best-practices/bp.md"}]}), encoding="utf-8")
        s4_commit(D1)
        rf = lu_run(root, "2026-10-10-01", cycle="--full")
        x = "wiki/research/x/"
        for name, rec, scope in (
                ("lint-semantic.json", s5_sem_rec(2, stamp=s4_stamp(D1)),
                 ("semantic-scope.txt", [x + "reviewed-late.md", "_inbox/proposed/promoted.md"])),
                ("claims.json", {"status": "completed", "timestamp": s4_stamp(D1)},
                 ("claims-scope.txt", [x + "claimless.md", x + "promoted.md", x + "reviewed-late.md"])),
                ("synthesis.json", {"status": "completed", "timestamp": s4_stamp(D1)}, ("synthesis-scope.txt", [])),
                ("refresh.json", {"status": "completed", "timestamp": s4_stamp(D1)}, None),
                ("triage.json", {"status": "completed", "timestamp": s4_stamp(D1)}, None),
                ("update.json", s6_update(), None), ("discover.json", s6_update(), None),
                ("lint-mechanical.json", {"status": "completed", "timestamp": S5_LINT, "not_checked": [],
                                          "summary": {"files_scanned": 7, "broken_links": 0, "standalone": 1}}, None)):
            s4_step(rf, name, "completed", text=json.dumps(rec), scope=scope)
        (rf / "lint-fixes.txt").write_text(f"applied: 1\ndeclined: 2\nat: {S5_EARLY}\n", encoding="utf-8")
        (rf / "promote-setting.txt").write_text("confirm_before_promote: true\nfrom: test\n", encoding="utf-8")
        p, lines = lu("s6i", rf)
        check("left_undone_reads_nothing_after_a_fully_answered_full_run: every step completed with its scope file, a staged "
              "entry linted then promoted, an entry re-reviewed on the lint's day, a task card, a claim-less entry, every "
              "finding accounted for and a lint after the fixes: the file is Left undone: nothing",
              p.returncode == 0 and lines == ["Left undone: nothing"], (p.stderr[-300:], lines))
        (rf / "refresh.json").unlink()
        p, lines = lu("s6i", rf)
        check("left_undone_reads_nothing_after_a_fully_answered_full_run: the same run with refresh.json removed gives the "
              "third state on the past-due line and is not nothing",
              "- Past review_after: 0, not checked (refresh left no refresh.json)" in lines
              and lines[:1] == ["Left undone: 1 queue(s)"], lines)
    left_undone_reads_nothing_after_a_fully_answered_full_run()

    def left_undone_names_an_older_lint_with_no_usable_findings_list():
        root = mknb("s6j")
        old = "2026-09-21-01"
        d = root / "_inbox" / "reports" / "2026-09-21" / old
        d.mkdir(parents=True)
        (d / "lint-semantic.json").write_text(json.dumps({"status": "completed", "timestamp": "2026-09-21T09:00:00-04:00"}),
                                              encoding="utf-8")
        s5_hist(root, "2026-09-22", 1, 0, note=("", ""))
        p, lines, _ = s4_lu("s6j", "--ingest-only")
        check("left_undone_names_an_older_lint_with_no_usable_findings_list: an older completed lint whose findings list "
              "cannot be trusted is not checked, never silent, and the header counts the line",
              f"- Semantic findings from {old}: not checked (lint-semantic.json has no usable findings list)" in lines
              and lines[:1] == ["Left undone: 3 queue(s)"], lines)
    left_undone_names_an_older_lint_with_no_usable_findings_list()

    # ── hand mutation pass (task #240): tests that kill the real survivors ──
    def left_undone_reads_a_step_result_with_no_status_as_unknown():
        mknb("mut1")
        rec = {"timestamp": S5_LINT, "not_checked": [], "summary": {"files_scanned": 4, "broken_links": 2}}
        p, lines, _ = s4_lu("mut1", "--lint-only", [s5_file("lint-mechanical.json", rec)])
        check("left_undone_reads_a_step_result_with_no_status_as_unknown: a lint result with no status field reads "
              "ended unknown, never completed",
              "- Lint findings: not checked (the mechanical lint ended unknown)" in lines
              and not [l for l in lines if l.startswith("- Lint broken")], (p.stderr[-200:], lines))
    left_undone_reads_a_step_result_with_no_status_as_unknown()

    def left_undone_bridges_a_promoted_stem_only_from_inbox_proposed():
        root = mknb("mut2")
        s4_entry(root, "wiki/research/x/old-a.md", D0)
        s4_commit(D0)
        s4_entry(root, "wiki/research/x/promo.md", D1)
        p, lines, _ = s4_lu("mut2", "--full", s4_lint(D2, ["wiki/research/x/old-a.md", "_inbox/done/promo.md"]))
        check("left_undone_bridges_a_promoted_stem_only_from_inbox_proposed: a scope file naming the stem under "
              "_inbox/done/ does not cover the live entry",
              f"{SEM}1 — {SEM_RAN}" in lines, (p.stderr[-200:], lines))
    left_undone_bridges_a_promoted_stem_only_from_inbox_proposed()

    def left_undone_reads_a_fixes_record_missing_one_line_as_unreadable():
        mknb("mut3")
        for what, text in (("no declined line", f"applied: 1\nat: {S5_EARLY}\n"),
                           ("no applied line", f"declined: 1\nat: {S5_EARLY}\n")):
            p, lines, _ = s4_lu("mut3", "--full", [s5_sem(3), s5_file("lint-fixes.txt", text)])
            check(f"left_undone_reads_a_fixes_record_missing_one_line_as_unreadable: a record with {what} counts all "
                  "3 findings as not checked",
                  f"{SEMF}3, not checked (lint-fixes.txt unreadable)" in lines, (p.stderr[-200:], lines))
    left_undone_reads_a_fixes_record_missing_one_line_as_unreadable()

    def left_undone_names_a_partial_lint_that_lists_no_reason():
        mknb("mut4")
        p, lines, _ = s4_lu("mut4", "--lint-only", [s5_lint({"files_scanned": 4, "broken_links": 2}, status="partial")])
        check("left_undone_names_a_partial_lint_that_lists_no_reason: a partial lint with an empty not_checked list "
              "reads ended partial, never nothing",
              "- Lint findings: not checked (the mechanical lint ended partial)" in lines, (p.stderr[-200:], lines))
        p, lines, _ = s4_lu("mut4", "--lint-only", [s5_lint({"files_scanned": 4, "broken_links": 2}, not_checked=["stale"])])
        check("left_undone_names_a_partial_lint_that_lists_no_reason: a completed lint that lists a reason still gives "
              "its counts",
              f"- Lint broken links: 2 — {NO_FIX}" in lines and "- Lint: not checked — stale" not in lines,
              (p.stderr[-200:], lines))
    left_undone_names_a_partial_lint_that_lists_no_reason()

    def lint_fixes_skips_an_empty_id_between_commas():
        root = mknb("mut5")
        rf = lu_run(root, "2026-10-06-01", cycle="--full")
        (rf / "lint-semantic.json").write_text(json.dumps(s5_sem_rec(5)), encoding="utf-8")
        p = run_on("mut5", "lint-fixes", "--run-folder", str(rf), "--applied", "1,,2", "--declined", ",3")
        txt = (rf / "lint-fixes.txt").read_text(encoding="utf-8").splitlines() if (rf / "lint-fixes.txt").is_file() else []
        check("lint_fixes_skips_an_empty_id_between_commas: 1,,2 and ,3 read as the ids 1, 2 and 3",
              p.returncode == 0 and txt[:2] == ["applied: 1,2", "declined: 3"], (p.returncode, p.stderr[-200:], txt))
    lint_fixes_skips_an_empty_id_between_commas()

    def semantic_scope_takes_its_cut_off_from_an_earlier_run_only():
        root = mknb("mut6")
        earlier = lu_run(root, "2026-10-04-01", cycle="--full")
        (earlier / "lint-semantic.json").write_text(json.dumps({"status": "completed", "timestamp": S5_LINT}), encoding="utf-8")
        own = lu_run(root, "2026-10-06-01", cycle="--full")
        (own / "lint-semantic.json").write_text(json.dumps({"status": "completed", "timestamp": S5_LATE}), encoding="utf-8")
        p = run_on("mut6", "semantic", "--run-folder", str(own))
        check("semantic_scope_takes_its_cut_off_from_an_earlier_run_only: a lint result already in this run's folder is "
              "not the cut-off, the earlier run's is",
              p.returncode == 0 and f"since {S5_LINT} " in p.stdout and S5_LATE not in p.stdout, (p.returncode, p.stdout))
    semantic_scope_takes_its_cut_off_from_an_earlier_run_only()

failed =[n for ok, n in results if not ok]
for ok, n in results:
    print(("PASS " if ok else "FAIL ") + n)
print(f"\n{len(results) - len(failed)}/{len(results)} passed")
sys.exit(1 if failed else 0)
