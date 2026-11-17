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
    INTERIM_LAST = ("Not counted yet: leftovers of steps that ran (lint findings, dropped sources, "
                    "entries not linted, claimed or synthesised)")

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
              p.returncode == 0 and lines[:1] == ["Left undone: 3 queue(s)"], (p.returncode, p.stderr[-300:], lines))
        check("left_undone_counts_review_dates: past review_after counts 2 (the quoted date too), today and the future not",
              f"- Past review_after: 2 — {PAST_NOT_RUN}" in lines, lines)
        check("left_undone_counts_review_dates: no review_after counts 1, a task card and a session page not",
              "- No review_after: 1 — refresh cannot see an entry with no review_after; add the date "
              "(the lint lists them under Missing lifecycle fields)" in lines, lines)
        check("left_undone_counts_review_dates: a review_after that is not a date counts 1",
              "- review_after not a date: 1 — refresh cannot read it; correct the date "
              "(the lint lists them under Dates not in ISO form)" in lines, lines)
        check("left_undone_counts_review_dates: exactly three queue lines, and the interim line last, not a queue",
              len([l for l in lines if l.startswith("- ")]) == 3 and lines[-1:] == [INTERIM_LAST], lines)
        rel = "_inbox/reports/2026-06-15/2026-06-15-01/left-undone.txt"
        check("left_undone_counts_review_dates: only left-undone.txt is new, nothing else changed, no scope file",
              set(after) - set(before) == {rel} and all(after.get(k) == v for k, v in before.items())
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
              and lines[:1] == ["Left undone: 3 queue(s)"], lines)
        # a mode that cannot be read: no scratchpad, two lines that disagree
        for label, kw in (("no scratchpad", {}), ("two lines naming different modes", {"cycle": "--full", "mode": "--quick"})):
            _, p, lines = unclear_run("lu3", **kw)
            check(f"left_undone_names_what_it_cannot_check: {label} keeps the count, the other lines and adds the Mode line",
                  "- Past review_after: 2, not checked (cannot read the mode from scratchpad.md)" in lines
                  and none_line in lines and f"- {no_mode}" in lines and lines[:1] == ["Left undone: 3 queue(s)"], lines)
        # no mode token at all, an empty run folder, nothing else to count: the header is never "nothing"
        clean = mknb("lu4")
        page(clean, "wiki/research/x/future.md", "2026-12-01")
        _, p, lines = unclear_run("lu4", cycle="see the notes")
        check("left_undone_names_what_it_cannot_check: no mode token and nothing else gives one queue, never nothing",
              lines[:2] == ["Left undone: 1 queue(s)", f"- {no_mode}"], lines)
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
              and lines[:1] == [f"Left undone: {len([l for l in lines if l.startswith('- ')])} queue(s)"], (p.stderr[-200:], lines))
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
              p.returncode == 0 and lines == ["Left undone: 2 queue(s)", OWN_NO_INGEST, OTHERS, INTERIM_LAST],
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
              p.returncode == 0 and lines == ["Left undone: 1 queue(s)", no_triage, INTERIM_LAST], (p.stderr[-300:], lines))
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
        none = ["Left undone (disk-state queues): none", INTERIM_LAST]
        p, lines = step3_run("lu8", cycle="--lint-only", setting="false")
        check("left_undone_counts_staged_entries: with confirm_before_promote false the two staged entries are one queue line",
              p.returncode == 0 and lines == ["Left undone: 1 queue(s)", "- Staged entries: 2 — staged before this run, "
                                              "or held by the checker; /wiki-promote", INTERIM_LAST],
              (p.stderr[-300:], lines))
        p, lines = step3_run("lu8", cycle="--lint-only", setting="true")
        check("left_undone_counts_staged_entries: with confirm_before_promote true Needs you has them, so no line",
              lines == none, lines)
        p, lines = step3_run("lu8", cycle="--lint-only")
        check("left_undone_counts_staged_entries: with no promote-setting.txt the count is kept and not checked is said",
              lines == ["Left undone: 1 queue(s)", "- Staged entries: 2, not checked (no promote-setting.txt: whether "
                                                   "they wait for you is not known)", INTERIM_LAST], lines)
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
                  "Left undone: 1 queue(s)", "- Discovery checklists: 1 — still in _inbox/discovered/ (discovery files a "
                  "processed one in _inbox/done/); whether it was reviewed is not recorded", INTERIM_LAST],
              (p.stderr[-300:], lines))
        mknb("lu9b")
        p, lines = step3_run("lu9b", cycle="--lint-only")
        check("left_undone_counts_discovery_checklists: no _inbox/discovered/ adds nothing",
              lines == ["Left undone (disk-state queues): none", INTERIM_LAST], lines)
    left_undone_counts_discovery_checklists()

    def left_undone_falls_back_to_one_bucket_on_an_unparseable_intake_readme():
        root = mknb("lu10")
        intake = root / "_inbox" / "intake"
        intake.mkdir(parents=True)
        (intake / "README.md").write_text("---\nbuckets: [unclosed\n---\n\n# Intake\n", encoding="utf-8")
        lu_tickets(intake / "main", "m", 2)
        p, lines = step3_run("lu10", cycle="--lint-only")
        check("left_undone_falls_back_to_one_bucket_on_an_unparseable_intake_readme: exit 0 and the main bucket is this session's",
              p.returncode == 0 and lines == ["Left undone: 1 queue(s)", OWN_NO_INGEST, INTERIM_LAST],
              (p.returncode, p.stderr[-300:], lines))
    left_undone_falls_back_to_one_bucket_on_an_unparseable_intake_readme()

    def left_undone_docstring_names_the_unsupported_working_folder():
        import ast
        doc = ast.get_docstring(ast.parse(SCRIPT.read_text(encoding="utf-8"))) or ""
        check("left_undone_docstring_names_the_unsupported_working_folder: the docstring says a working folder whose "
              ".claude/wiki-config.json names another notebook is not supported",
              "names another notebook" in doc and "not a supported case" in doc, doc[doc.find("`left-undone`"):][:700])
    left_undone_docstring_names_the_unsupported_working_folder()

failed =[n for ok, n in results if not ok]
for ok, n in results:
    print(("PASS " if ok else "FAIL ") + n)
print(f"\n{len(results) - len(failed)}/{len(results)} passed")
sys.exit(1 if failed else 0)
