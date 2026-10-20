#!/usr/bin/env python3
"""Checks that the notebook's confirm_before_promote decides where an entry goes (task #184). Never shipped.

Until 2026-10-19 only /wrap-up read the setting: /wiki-update filed straight into wiki/ unless --staged was
passed, and /wiki-cycle staged in every mode but --full, which promoted everything. Now `wiki-update.py` with
neither --staged nor --direct follows the setting (true: stage; false: file), a typed flag wins for that run, and
`wiki-cycle-scope.py promote` prints the setting for the cycle's Step 0. No network.

    uv run python tests/scripts/test_promote_setting.py    # exit 0 = every check passed
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[2] / "scripts"
results: list[tuple[bool, str]] = []


def check(name: str, ok: bool, detail: object = ""):
    results.append((bool(ok), name + (f"  [{detail}]" if not ok and detail != "" else "")))


with tempfile.TemporaryDirectory() as td:
    tmp = Path(td)
    reg = {"notebooks": {"ask": {"root": "notebooks/ask", "confirm_before_promote": True},
                         "auto": {"root": "notebooks/auto", "confirm_before_promote": False},
                         "unset": {"root": "notebooks/unset"}}}
    for name in reg["notebooks"]:
        nb = tmp / "notebooks" / name
        (nb / "wiki" / "research" / "tooling").mkdir(parents=True)
        (nb / "raw").mkdir()
        (nb / "raw" / "src.md").write_text("---\ntitle: A source\n---\n\nAgents keep state in files.\n",
                                           encoding="utf-8")
    (tmp / "linked-notebooks.json").write_text(json.dumps(reg), encoding="utf-8")
    proj = tmp / "project"
    (proj / ".claude").mkdir(parents=True)
    (proj / ".claude" / "wiki-config.json").write_text(json.dumps(
        {"notebook": "ask", "registry": (tmp / "linked-notebooks.json").as_posix()}), encoding="utf-8")
    draft = tmp / "draft.md"
    draft.write_text("## TL;DR\n\nState in files lets a later run pick up.\n\n"
                     "## Related\n\n- [a](a.md)\n- [b](b.md)\n", encoding="utf-8")
    env = {**os.environ, "PYTHONIOENCODING": "utf-8"}
    n = 0

    def file(topic: str, *flags: str):
        global n
        n += 1
        p = subprocess.run([sys.executable, str(SCRIPTS / "wiki-update.py"), "--topic", topic,
                            "--folder", "research/tooling", "--source", str(draft),
                            "--source-url", f"https://example.com/{n}", "--raw-path", "raw/src.md",
                            "--title", f"Promote setting entry {n}", "--tags", "a,b,c", "--tier", "3",
                            "--confidence", "medium", "--no-index", "--skip-integration", *flags],
                           cwd=proj, capture_output=True, text=True, encoding="utf-8", env=env, timeout=120)
        nb = tmp / "notebooks" / topic
        slug = f"promote-setting-entry-{n}.md"
        where = ("staged" if (nb / "_inbox" / "proposed" / slug).is_file()
                 else "filed" if (nb / "wiki" / "research" / "tooling" / slug).is_file() else "nowhere")
        return p.returncode, p.stdout + p.stderr, where

    # ── wiki-update.py follows the setting when no flag is typed ──
    code, out, where = file("ask")
    check("true, no flag: staged in _inbox/proposed/", code == 0 and where == "staged", (code, where, out[-300:]))
    check("... and says why (promote_mode=staged, the setting named)",
          "promote_mode=staged" in out and "confirm_before_promote" in out, out[-300:])
    code, out, where = file("auto")
    check("false, no flag: filed into wiki/", code == 0 and where == "filed", (code, where, out[-300:]))
    check("... and says why (promote_mode=direct)", "promote_mode=direct" in out, out[-300:])
    code, out, where = file("unset")
    check("no setting: staged (the default is true)", code == 0 and where == "staged", (code, where, out[-300:]))

    # ── a typed flag wins for that run ──
    code, out, where = file("ask", "--direct")
    check("true + --direct: filed into wiki/", code == 0 and where == "filed", (code, where, out[-300:]))
    code, out, where = file("auto", "--staged")
    check("false + --staged: staged", code == 0 and where == "staged", (code, where, out[-300:]))
    code, out, where = file("auto", "--staged", "--direct")
    check("--staged and --direct together: refused (exit 2), nothing written",
          code == 2 and where == "nowhere", (code, where, out[-300:]))

    # ── wiki-cycle-scope.py promote: the cycle's Step 0 reads the setting from a script ──
    def promote(topic: str):
        rf = tmp / "notebooks" / topic / "_inbox" / "reports" / "2026-10-19" / "2026-10-19-01"
        p = subprocess.run([sys.executable, str(SCRIPTS / "wiki-cycle-scope.py"), "--topic", topic, "promote",
                            "--run-folder", str(rf)], cwd=proj, capture_output=True, text=True, encoding="utf-8",
                           env=env, timeout=60)
        f = rf / "promote-setting.txt"
        rec = {}
        for line in (f.read_text(encoding="utf-8").splitlines() if f.is_file() else []):
            k, _, v = line.partition(": ")
            rec[k] = {"true": True, "false": False}.get(v, v)
        check("promote: no JSON in the run folder (its *.json are step results)",
              not (rf / "promote-setting.json").exists())
        return p, rec

    p, rec = promote("ask")
    check("promote, true: exit 0, prints that entries wait for the user, records it",
          p.returncode == 0 and "promote: wait for the user" in p.stdout and rec.get("confirm_before_promote") is True,
          (p.stdout, p.stderr[-200:], rec))
    p, rec = promote("auto")
    check("promote, false: prints that entries are promoted without asking, records it",
          p.returncode == 0 and "promote: automatic" in p.stdout and rec.get("confirm_before_promote") is False,
          (p.stdout, rec))
    p, rec = promote("unset")
    check("promote, no setting: waits for the user, and says it is the default",
          p.returncode == 0 and "promote: wait for the user" in p.stdout and "default" in p.stdout
          and rec.get("confirm_before_promote") is True, (p.stdout, rec))

failed = [n for ok, n in results if not ok]
for ok, n in results:
    print(("PASS " if ok else "FAIL ") + n)
print(f"\n{len(results) - len(failed)}/{len(results)} passed")
sys.exit(1 if failed else 0)
