#!/usr/bin/env python3
"""Checks for scripts/wiki-triage.py, the mechanical half of /wiki-triage
(task #42 section T). Never shipped.

    python tests/scripts/test_wiki_triage.py    # exit 0 = every check passed

A throwaway registry holds a shared research notebook (`research`, no bot) and two
projects with bots (`proj` -> proj-bot, `other` -> other-bot). The session runs from
proj's folder, so it reads as proj-bot.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

SCRIPT = Path(os.environ.get("WIKI_TRIAGE_SCRIPT") or
              Path(__file__).resolve().parents[2] / "scripts" / "wiki-triage.py")
results: list[tuple[bool, str]] = []


def check(name: str, ok: bool, detail: object = ""):
    results.append((bool(ok), name + (f"  [{detail}]" if not ok and detail != "" else "")))


README = """---
buckets:
  - folder: main
    purpose: Anything relevant that fits no other bucket
    reader: proj-bot
  - folder: proj
    purpose: Memory and retrieval
    reader: proj-bot
  - folder: other
    purpose: Building agents
    reader: other-bot
  - folder: money
    purpose: "Making money with AI: side hustles"
    reader: mark
---

# Intake

How triage uses this file.
"""


def ticket(url: str) -> str:
    return (f"---\nsource: {url}\nfolder:\npriority: 3\nadded_at: 2026-09-24T10:00:00-04:00\nadded_by: test\n---\n\n"
            f"# {url}\n\n**Source**: <{url}>\n")


with tempfile.TemporaryDirectory() as td:
    tmp = Path(td)
    reg = {"notebooks": {
        "research": {"root": "notebooks/research"},
        "proj": {"root": "notebooks/proj", "discord": {"bot_name": "proj-bot", "user_id": "111"}},
        "other": {"root": "notebooks/other", "discord": {"bot_name": "other-bot", "user_id": "222"}},
    }}
    (tmp / "linked-notebooks.json").write_text(json.dumps(reg), encoding="utf-8")
    for n in ("research", "proj", "other"):
        (tmp / "notebooks" / n / "wiki").mkdir(parents=True)
    rs = tmp / "notebooks" / "research"
    (rs / "_inbox" / "pending").mkdir(parents=True)
    (rs / "raw").mkdir()
    proj = tmp / "project"
    (proj / ".claude").mkdir(parents=True)
    (proj / ".claude" / "wiki-config.json").write_text(json.dumps(
        {"notebook": "proj", "registry": (tmp / "linked-notebooks.json").as_posix()}), encoding="utf-8")

    def run(*args: str) -> subprocess.CompletedProcess:
        return subprocess.run([sys.executable, str(SCRIPT), *args], cwd=proj, capture_output=True, text=True,
                              encoding="utf-8", env={**os.environ, "PYTHONIOENCODING": "utf-8"})

    # ── no README: one bucket, main, read by this session ──
    p = run("--topic", "research", "buckets")
    check("no config: exit 0", p.returncode == 0, p.stderr[-200:])
    check("no config: one bucket, main", "- main:" in p.stdout and p.stdout.count("\n- ") == 1, p.stdout)
    check("no config: main is read by this session (proj-bot)", "reads as: proj-bot" in p.stdout
          and "this session" in p.stdout, p.stdout)
    p = run("--topic", "research", "check")
    check("no config: check passes", p.returncode == 0, p.stdout)

    # ── the README config ──
    intake = rs / "_inbox" / "intake"
    intake.mkdir(parents=True)
    (intake / "README.md").write_text(README, encoding="utf-8")
    p = run("--topic", "research", "buckets")
    out = p.stdout
    check("config: four buckets listed", out.count("\n- ") == 4, out)
    check("config: a purpose with a colon survives", "Making money with AI: side hustles" in out, out)
    check("config: other-bot's bucket names its Discord id", "<@222>" in out, out)
    check("config: mark's bucket is the user's", "the user" in out, out)
    check("config: proj-bot's buckets are this session's", out.count("[reader: this session]") == 2, out)
    p = run("--topic", "research", "check")
    check("config: check passes", p.returncode == 0, p.stdout)

    # ── check catches a broken config ──
    bad = README.replace("folder: main", "folder: Main Stuff").replace("reader: other-bot", "reader: nobody")
    (intake / "README.md").write_text(bad, encoding="utf-8")
    p = run("--topic", "research", "check")
    check("bad config: check exits 1", p.returncode == 1, p.stdout)
    check("bad config: names the missing main", "no 'main' bucket" in p.stdout, p.stdout)
    check("bad config: names the bad folder name", "not a plain lower-case name" in p.stdout, p.stdout)
    check("bad config: names the unknown reader", "reader 'nobody'" in p.stdout, p.stdout)
    (intake / "README.md").write_text(README, encoding="utf-8")

    # ── pending ──
    pend = rs / "_inbox" / "pending"
    for i, url in enumerate(("https://example.com/a", "https://example.com/b", "https://example.com/c"), 1):
        (pend / f"3-2026-09-24-10000{i}-t{i}.md").write_text(ticket(url), encoding="utf-8")
    (pend / "_pending.md").write_text("# view\n", encoding="utf-8")
    p = run("--topic", "research", "pending")
    check("pending: three tickets, the _ view skipped", p.stdout.startswith("3 ticket(s)") and "_pending" not in p.stdout,
          p.stdout)

    # ── route: refusals leave everything in place ──
    p = run("--topic", "research", "route", "3-2026-09-24-100001-t1.md", "--to", "nowhere", "--reason", "x")
    check("route to a non-bucket: exit 2", p.returncode == 2, p.returncode)
    check("route to a non-bucket: ticket still pending", (pend / "3-2026-09-24-100001-t1.md").is_file())
    p = run("--topic", "research", "route", "3-2026-09-24-100001-t1.md", "--to", "other", "--reason", "  ")
    check("route with a blank reason: exit 2", p.returncode == 2, p.returncode)
    p = run("--topic", "research", "route", "3-2026-09-24-100001-t1.md", "--to", "other", "--reason", "x",
            "--raw", "raw/missing.md")
    check("route with a raw that does not exist: exit 2", p.returncode == 2, p.returncode)
    check("no log written by a refused route", not (intake / "triage-log.md").exists())

    # ── route: a move with a raw ──
    (rs / "raw" / "a.md").write_text("the raw", encoding="utf-8")
    p = run("--topic", "research", "route", "3-2026-09-24-100001-t1.md", "--to", "other",
            "--reason", "agent building | a harness", "--raw", "raw/a.md")
    moved = intake / "other" / "3-2026-09-24-100001-t1.md"
    check("route: exit 0", p.returncode == 0, p.stderr[-200:])
    check("route: ticket moved into intake/other/", moved.is_file() and not (pend / moved.name).exists())
    mt = moved.read_text(encoding="utf-8") if moved.is_file() else ""
    check("route: raw_path recorded in the ticket's frontmatter", mt.startswith("---\nraw_path: raw/a.md\n"), mt[:80])
    check("route: the rest of the ticket kept", "source: https://example.com/a" in mt and "**Source**" in mt, mt)
    check("route: says the reader", "reader: other-bot" in p.stdout, p.stdout)
    log = (intake / "triage-log.md").read_text(encoding="utf-8") if (intake / "triage-log.md").is_file() else ""
    check("route: log row with item, folder, escaped reason, decider",
          "| https://example.com/a | other | agent building \\| a harness | proj-bot |" in log, log[-300:])

    # ── route: to this session's own bucket, then main; a second route of a moved ticket fails ──
    p = run("--topic", "research", "route", "3-2026-09-24-100002-t2.md", "--to", "proj", "--reason", "memory")
    check("route to this session's bucket: says so", p.returncode == 0 and "this session" in p.stdout, p.stdout)
    p = run("--topic", "research", "route", "3-2026-09-24-100003-t3.md", "--to", "main", "--reason", "fits two",
            "--by", "mark")
    lg = intake / "triage-log.md"
    check("route to main with --by: logged as mark", p.returncode == 0 and lg.is_file()
          and "| main | fits two | mark |" in lg.read_text(encoding="utf-8"), p.stdout)
    # a wrong call is fixed by routing again: a bare name is found in its bucket (task #111)
    p = run("--topic", "research", "route", "3-2026-09-24-100001-t1.md", "--to", "main", "--reason", "again")
    check("re-route of a bucket ticket by its bare name: exit 0, moved other -> main",
          p.returncode == 0 and (intake / "main" / "3-2026-09-24-100001-t1.md").is_file()
          and not moved.exists(), (p.returncode, p.stderr[-200:]))
    p = run("--topic", "research", "route", "3-2026-09-24-100009-none.md", "--to", "main", "--reason", "x")
    check("route of a ticket that is nowhere: exit 2", p.returncode == 2, p.returncode)
    check("pending holds only the view file now", [x.name for x in pend.iterdir()] == ["_pending.md"],
          [x.name for x in pend.iterdir()])

    # ── log ──
    p = run("--topic", "research", "log", "--last", "2")
    check("log: four calls (the re-route is one), the last two shown",
          p.stdout.startswith("4 call(s); the last 2:") and "example.com/b" not in p.stdout
          and "example.com/c" in p.stdout and "| main | again |" in p.stdout, p.stdout)

    # ── save as PDF: route marks the ticket, save-list lists what the user must save (task #96, Mark) ──
    p = run("--topic", "research", "save-list")
    check("save-list with nothing waiting: exit 0, says so", p.returncode == 0 and "nothing" in p.stdout.lower(),
          (p.returncode, p.stdout, p.stderr[-200:]))
    titled = ticket("https://x.com/AndrewYNg/status/2090840747738374568").replace(
        "folder:\n", "folder:\ntitle: Andrew Ng - AI Engineering Skills Map\n")
    (pend / "3-2026-10-11-100004-t4.md").write_text(titled, encoding="utf-8")
    (pend / "3-2026-10-11-100005-t5.md").write_text(ticket("https://medium.com/@a/paywalled-story"), encoding="utf-8")
    (pend / "3-2026-10-11-100006-t6.md").write_text(ticket("https://example.com/ordinary"), encoding="utf-8")
    p = run("--topic", "research", "route", "3-2026-10-11-100004-t4.md", "--to", "main", "--reason", "an X Article",
            "--save-as-pdf", "login")
    t4 = intake / "main" / "3-2026-10-11-100004-t4.md"
    t4_text = t4.read_text(encoding="utf-8") if t4.is_file() else ""
    check("route --save-as-pdf: exit 0", p.returncode == 0, p.stderr[-200:])
    check("route --save-as-pdf: the ticket itself is marked save_as_pdf: login", "\nsave_as_pdf: login\n" in t4_text,
          t4_text[:200])
    lg_text = (intake / "triage-log.md").read_text(encoding="utf-8")
    check("route --save-as-pdf: the log reason says save as PDF", "save as PDF: login" in lg_text, lg_text[-200:])
    p = run("--topic", "research", "route", "3-2026-10-11-100005-t5.md", "--to", "other", "--reason", "x",
            "--save-as-pdf", "because")
    check("route --save-as-pdf with an unknown reason: exit 2, ticket still pending",
          p.returncode == 2 and (pend / "3-2026-10-11-100005-t5.md").is_file(), p.returncode)
    # an older ticket: marked only by its log reason, the way routes were written before the flag
    p = run("--topic", "research", "route", "3-2026-10-11-100005-t5.md", "--to", "other",
            "--reason", "save as PDF: paywall (member-only)")
    p = run("--topic", "research", "route", "3-2026-10-11-100006-t6.md", "--to", "proj", "--reason", "memory")
    p = run("--topic", "research", "save-list")
    out = p.stdout
    check("save-list: exit 0", p.returncode == 0, p.stderr[-200:])
    check("save-list: counts the two pages waiting", out.startswith("2 page(s)"), out[:120])
    check("save-list: the marked ticket, by its title and link",
          "Andrew Ng - AI Engineering Skills Map" in out and "https://x.com/AndrewYNg/status/2090840747738374568" in out, out)
    check("save-list: the older ticket marked only in the log", "https://medium.com/@a/paywalled-story" in out, out)
    check("save-list: each one's reason", "login" in out and "paywall" in out, out)
    check("save-list: the full folder path to save each into", str(intake / "main") in out and str(intake / "other") in out,
          out)
    check("save-list: an ordinary ticket waiting for ingest is not listed", "example.com/ordinary" not in out, out)
    check("save-list: a ticket routed with a raw is not listed", "example.com/a\n" not in out and "example.com/a " not in out,
          out)
    # once the user's PDF is attached (raw_path set), the page leaves the list
    t4.write_text(t4_text.replace("---\n", "---\nraw_path: raw/andrew.md\n", 1), encoding="utf-8")
    p = run("--topic", "research", "save-list")
    check("save-list: a page whose PDF is attached leaves the list",
          p.stdout.startswith("1 page(s)") and "AndrewYNg" not in p.stdout, p.stdout[:200])

    # ── a page found blocked at ingest: its ticket is already in a bucket, marked in place (task #111) ──
    (pend / "3-2026-10-13-100007-t7.md").write_text(ticket("https://medium.com/@b/blocked-story"), encoding="utf-8")
    run("--topic", "research", "route", "3-2026-10-13-100007-t7.md", "--to", "proj", "--reason", "memory")
    t7 = intake / "proj" / "3-2026-10-13-100007-t7.md"
    p = run("--topic", "research", "route", "3-2026-10-13-100007-t7.md", "--to", "proj", "--reason", "Cloudflare at ingest",
            "--save-as-pdf", "blocked")
    t7_text = t7.read_text(encoding="utf-8") if t7.is_file() else ""
    check("same-bucket route by bare name: exit 0", p.returncode == 0, (p.returncode, p.stderr[-200:]))
    check("same-bucket route: the ticket is kept, marked save_as_pdf: blocked",
          "\nsave_as_pdf: blocked\n" in t7_text and "source: https://medium.com/@b/blocked-story" in t7_text, t7_text[:200])
    check("same-bucket route: logged",
          "| https://medium.com/@b/blocked-story | proj | save as PDF: blocked (Cloudflare at ingest) |"
          in (intake / "triage-log.md").read_text(encoding="utf-8"))
    p = run("--topic", "research", "route", str(t7), "--to", "proj", "--reason", "again, by full path")
    check("same-bucket route by full path: exit 0 and the ticket still exists (it used to be deleted)",
          p.returncode == 0 and t7.is_file(), (p.returncode, t7.is_file()))
    p = run("--topic", "research", "save-list")
    check("save-list: the page marked at ingest is listed", "medium.com/@b/blocked-story" in p.stdout, p.stdout[-300:])

failed = [n for ok, n in results if not ok]
for ok, n in results:
    print(("PASS " if ok else "FAIL ") + n)
print(f"\n{len(results) - len(failed)}/{len(results)} passed")
sys.exit(1 if failed else 0)
