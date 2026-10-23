#!/usr/bin/env python3
"""Checks for the one qmd launcher, `_wiki_config.qmd_command()` (task #181). Never shipped.

    uv run python tests/scripts/test_qmd_launcher.py    # exit 0 = every check passed

Three copies started qmd three ways: the search helper ran `node <pkg>/dist/cli/qmd.js` (npm's Windows shim hands
off to /bin/sh, which Python cannot find) and honoured $WIKI_QMD_BIN and $WIKI_QMD_INDEX; the lint's index check
tried the shim, then the sh script through Git Bash, and ignored $WIKI_QMD_BIN; the wiki-search suite kept a third
copy. One function now, and each caller passes the index it means.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
import _wiki_config as wc  # noqa: E402

results: list[tuple[bool, str]] = []


def check(name: str, ok: bool, detail: object = ""):
    results.append((bool(ok), name + (f"  [{detail}]" if not ok and detail != "" else "")))


with tempfile.TemporaryDirectory() as td:
    tmp = Path(td)
    saved = {k: os.environ.get(k) for k in ("PATH", "WIKI_QMD_BIN")}
    try:
        # an npm-style install: the shim on PATH, qmd's package beside it, and node
        npm = tmp / "npm"
        entry = npm / "node_modules" / "@tobilu" / "qmd" / "dist" / "cli" / "qmd.js"
        entry.parent.mkdir(parents=True)
        entry.write_text("// qmd\n", encoding="utf-8")
        shim = npm / ("qmd.cmd" if os.name == "nt" else "qmd")
        shim.write_text("@echo off\r\n" if os.name == "nt" else "#!/bin/sh\n", encoding="utf-8")
        shim.chmod(0o755)
        fake_node = tmp / "nodebin" / ("node.exe" if os.name == "nt" else "node")
        fake_node.parent.mkdir()
        fake_node.write_bytes(b"")
        fake_node.chmod(0o755)
        os.environ["PATH"] = os.pathsep.join([str(npm), str(fake_node.parent)])
        os.environ.pop("WIKI_QMD_BIN", None)
        cmd = wc.qmd_command()
        check("npm install: node + qmd.js, never the /bin/sh shim",
              cmd is not None and len(cmd) == 2 and Path(cmd[1]).resolve() == entry.resolve(), cmd)
        cmd = wc.qmd_command("sandbox-index")
        check("an index passed in becomes --index <it>", cmd is not None and cmd[-2:] == ["--index", "sandbox-index"], cmd)
        os.environ["WIKI_QMD_BIN"] = str(tmp / "my-qmd")
        check("$WIKI_QMD_BIN wins", wc.qmd_command() == [str(tmp / "my-qmd")], wc.qmd_command())
        os.environ.pop("WIKI_QMD_BIN")
        os.environ["PATH"] = str(tmp / "empty")
        check("no qmd anywhere: None, never a crash", wc.qmd_command() is None, wc.qmd_command())
    finally:
        for k, v in saved.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v

    # the lint's index check goes through the same launcher, so $WIKI_QMD_BIN reaches it too
    nb = tmp / "notebooks" / "t"
    wiki = nb / "wiki" / "research"
    wiki.mkdir(parents=True)
    (wiki / "a.md").write_text("---\ntitle: A\n---\n\n# A\n", encoding="utf-8")
    line = f"qmd://{(nb / 'wiki').resolve().as_posix()}/ (1 files)"
    stub = tmp / "stub-qmd.py"
    stub.write_text(f"print({line!r})\n", encoding="utf-8")
    if os.name == "nt":
        bin_ = tmp / "stub-qmd.bat"
        bin_.write_text(f'@"{sys.executable}" "{stub}" %*\r\n', encoding="utf-8")
    else:
        bin_ = tmp / "stub-qmd"
        bin_.write_text(f'#!/bin/sh\nexec "{sys.executable}" "{stub}" "$@"\n', encoding="utf-8")
        bin_.chmod(0o755)
    probe = ("import sys, json; sys.path.insert(0, sys.argv[1]); import importlib.util as u; "
             "s = u.spec_from_file_location('lint', sys.argv[1] + '/wiki-lint-mechanical.py'); m = u.module_from_spec(s); "
             "s.loader.exec_module(m); print(json.dumps(m.qmd_index_coverage(sys.argv[2])))")
    env = {**os.environ, "WIKI_QMD_BIN": str(bin_), "PATH": str(tmp / "empty"), "PYTHONIOENCODING": "utf-8"}
    env.pop("WIKI_QMD_INDEX", None)
    p = subprocess.run([sys.executable, "-c", probe, str(ROOT / "scripts"), str(nb / "wiki")], capture_output=True,
                       text=True, encoding="utf-8", env=env)
    out = json.loads(p.stdout.strip().splitlines()[-1]) if p.stdout.strip() else {}
    check("the lint's index check uses the shared launcher ($WIKI_QMD_BIN, no qmd on PATH)",
          out.get("state") == "ok" and out.get("indexed") == 1, (out, p.stderr[-300:]))

failed = [n for ok, n in results if not ok]
for ok, n in results:
    print(("PASS " if ok else "FAIL ") + n)
print(f"\n{len(results) - len(failed)}/{len(results)} passed")
sys.exit(1 if failed else 0)
