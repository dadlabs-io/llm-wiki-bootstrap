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
              bool(ids) and all(f'unfinished --mark-interrupted {i} --reason "' in by[i] for i in ids), by)
        # Mark, 2026-11-13: resume only for a folder with a scratchpad; nothing in one without can be resumed
        check("unfinished_names_runs_without_report: resume is offered for the in_progress folder only",
              bool(ids) and all((f"/wiki-cycle --resume {i}" in by[i]) == (i == "2026-10-02-01") for i in ids), by)
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
              p.returncode == 2 and "--reason" in p.stderr, (p.returncode, p.stdout, p.stderr[-300:]))
        check("mark_interrupted_needs_a_reason: nothing in the notebook was written", tree(nb) == before,
              sorted(set(tree(nb).items()) ^ set(before.items()), key=str)[:5])
    mark_interrupted_needs_a_reason()

    def unfinished_needs_a_flag():
        before = tree(nb)
        p = run("unfinished")
        check("unfinished_needs_a_flag: neither flag exits 2 and the error names both",
              p.returncode == 2 and "--run-folder" in p.stderr and "--mark-interrupted" in p.stderr,
              (p.returncode, p.stdout, p.stderr[-300:]))
        check("unfinished_needs_a_flag: nothing in the notebook was written", tree(nb) == before,
              sorted(set(tree(nb).items()) ^ set(before.items()), key=str)[:5])
    unfinished_needs_a_flag()

    def mark_interrupted_refuses_a_run_folder_beside_it():
        mkrun("2026-10-12-01", scratch="in_progress")
        before = tree(nb)
        p = run("unfinished", "--run-folder", str(cur), "--mark-interrupted", "2026-10-12-01", "--reason", "x")
        check("mark_interrupted_refuses_a_run_folder_beside_it: both flags exit 2 and the error names both",
              p.returncode == 2 and "--run-folder" in p.stderr and "--mark-interrupted" in p.stderr,
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

failed =[n for ok, n in results if not ok]
for ok, n in results:
    print(("PASS " if ok else "FAIL ") + n)
print(f"\n{len(results) - len(failed)}/{len(results)} passed")
sys.exit(1 if failed else 0)
