#!/usr/bin/env python3
"""Checks for task #204: a hub page names the tag it collects (`hub_tag: <tag>`), and the lint lists every entry
carrying that tag the hub does not link yet. Never shipped.

    uv run python tests/scripts/test_hub_tag.py    # exit 0 = every check passed

agentic-design's Obsidian hub (2026-09-23) collects every entry tagged `obsidian` across four folders by hand; nothing
noticed a new Obsidian entry left off it. Warn-only, like the other upkeep sections.
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _fake_qmd import fake_qmd_env  # noqa: E402  the lint needs an indexed wiki (task #133)

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "scripts"

results: list[tuple[bool, str]] = []


def check(name: str, ok: bool, detail: object = ""):
    results.append((bool(ok), name + (f"  [{detail}]" if not ok and detail != "" else "")))


def page(title: str, body: str, tags: str = "[x, y, z]", extra: str = "") -> str:
    return (f"---\ntitle: \"{title}\"\ndate: 2026-09-01\ntier: 3\nconfidence: high\n"
            f"tags: {tags}\n{extra}---\n\n# {title}\n\n{body}\n")


def run_lint(with_hub: bool = True):
    td = tempfile.TemporaryDirectory()
    tmp = Path(td.name)
    nb = tmp / "notebooks" / "t"
    w = nb / "wiki"
    for d in ("research/tooling", "research/long-term", "research/skills"):
        (w / d).mkdir(parents=True)
    (nb / "_inbox" / "reports").mkdir(parents=True)
    (tmp / "linked-notebooks.json").write_text(json.dumps({"notebooks": {"t": {"root": "notebooks/t"}}}),
                                               encoding="utf-8")
    proj = tmp / "project"
    (proj / ".claude").mkdir(parents=True)
    (proj / ".claude" / "wiki-config.json").write_text(json.dumps(
        {"notebook": "t", "registry": (tmp / "linked-notebooks.json").as_posix()}), encoding="utf-8")

    t = w / "research" / "tooling"
    (t / "vault-setup.md").write_text(page("Vault setup", "x", "[obsidian, setup, notes]"), encoding="utf-8")
    (w / "research" / "long-term" / "wiki-on-obsidian.md").write_text(
        page("Wiki on Obsidian", "x", "[llm-wiki, obsidian, vault]"), encoding="utf-8")
    (w / "research" / "skills" / "vault-skills.md").write_text(          # block-list tags
        page("Vault skills", "x", "\n  - skills\n  - obsidian\n  - agents"), encoding="utf-8")
    (t / "unrelated.md").write_text(page("Unrelated", "x", "[python, uv, tooling]"), encoding="utf-8")
    (t / "obsidianish.md").write_text(page("Obsidian-ish", "x", "[obsidian-sync, notes, git]"), encoding="utf-8")
    (t / "retired.md").write_text(page("Retired", "x", "[obsidian, old, gone]",
                                       extra="superseded_by: vault-setup.md\nstatus: superseded\n"), encoding="utf-8")
    if with_hub:
        (t / "obsidian-hub.md").write_text(page("Obsidian hub", "- [Vault setup](vault-setup.md)\n",
                                                "[obsidian, hub, index]", extra="hub_tag: obsidian\n"),
                                           encoding="utf-8")

    run = nb / "_inbox" / "reports" / "r"
    env = fake_qmd_env(tmp / "bin", w, env={**os.environ, "PYTHONIOENCODING": "utf-8"})
    p = subprocess.run([sys.executable, str(SCRIPTS / "wiki-lint-mechanical.py"), "--topic", "t",
                        "--cycle-id", "c1", "--run-folder", str(run)],
                       cwd=proj, capture_output=True, text=True, encoding="utf-8", env=env)
    report = nb / "_inbox" / "reports" / "lint-report.md"
    text = report.read_text(encoding="utf-8") if report.is_file() else ""
    jp = run / "lint-mechanical.json"
    summary = (json.loads(jp.read_text(encoding="utf-8")) if jp.is_file() else {}).get("summary") or {}
    td.cleanup()
    return p, text, summary


def section(text: str, word: str) -> str:
    m = re.search(rf"^## [^\n]*{word}[^\n]*$(.*?)(?=^## |\Z)", text, re.MULTILINE | re.DOTALL)
    return m.group(1) if m else ""


p, text, summary = run_lint()
check("lint exits 0 (warn-only)", p.returncode == 0, p.stderr[-300:])
hs = section(text, "Hubs Behind Their Tag")
check("the section is in the report", bool(hs), text[-600:])
check("a tagged entry in another folder the hub does not link is listed",
      "research/long-term/wiki-on-obsidian.md" in hs, hs)
check("a block-list tag counts", "research/skills/vault-skills.md" in hs, hs)
check("the entry the hub already links is not listed", "vault-setup.md`" not in hs.split("is missing")[-1], hs)
check("the hub names its tag", "obsidian-hub.md" in hs and "`obsidian`" in hs, hs)
check("an untagged entry and a near-miss tag are not listed", "unrelated.md" not in hs and "obsidianish.md" not in hs, hs)
check("a retired entry is not listed", "retired.md" not in hs, hs)
check("the hub does not list itself", hs.count("obsidian-hub.md") == 1, hs)
check("the summary counts the missing entries", summary.get("hub_entries_missing") == 2, summary)
check("the header counts them", "**Hubs behind their tag**: 2" in text, text[:1500])

p, text, summary = run_lint(with_hub=False)
check("no hub: the section says no page declares hub_tag", "no page declares `hub_tag`" in section(text, "Hubs Behind"),
      section(text, "Hubs Behind")[:300])

sys.stdout.reconfigure(encoding="utf-8")
failed = [n for ok, n in results if not ok]
for ok, n in results:
    print(("PASS " if ok else "FAIL ") + n)
print(f"\n{len(results) - len(failed)}/{len(results)} passed")
sys.exit(1 if failed else 0)
