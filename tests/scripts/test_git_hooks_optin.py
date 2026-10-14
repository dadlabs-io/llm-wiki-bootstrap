#!/usr/bin/env python3
"""Checks for task #141: /new-wiki's opt-in git hooks (status, install, a refused install, removal). Never shipped.

    uv run python tests/scripts/test_git_hooks_optin.py    # exit 0 = every check passed

Runs under a temporary home (HOME and USERPROFILE), so ~/.git-hooks and git's global core.hooksPath are the
temporary ones, never the machine's. Needs git, sh and gitleaks (tools/git-hooks/install.sh needs them).
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
td = tempfile.TemporaryDirectory()
HOME = Path(td.name) / "home"
HOME.mkdir()
os.environ.update({"HOME": str(HOME), "USERPROFILE": str(HOME), "GIT_CONFIG_NOSYSTEM": "1"})
sys.path.insert(0, str(ROOT / "scripts"))
import _install_tooling as it  # noqa: E402  (imported after the home is moved, so its ~ is the temporary one)

results: list[tuple[bool, str]] = []


def check(name: str, ok: bool, detail: object = ""):
    results.append((bool(ok), name + (f"  [{detail}]" if not ok and detail != "" else "")))


check("the hooks folder is under the temporary home", it.GIT_HOOKS_DIR == HOME / ".git-hooks", it.GIT_HOOKS_DIR)
check("status: off on a machine without them", it.git_hooks_status()["state"] == "off", it.git_hooks_status())

# gitleaks missing and nothing to install it with: nothing is installed, and the fix is named
real_find, real_cmd = it.find_gitleaks, it.gitleaks_install_command
it.find_gitleaks, it.gitleaks_install_command = (lambda: None), (lambda: None)
r = it.install_git_hooks(ROOT)
check("no gitleaks, no installer: not installed, a fix named", not r["installed"] and r["fix"] and "gitleaks" in r["reason"], r)
check("... and nothing turned on", it.git_hooks_status()["state"] == "off" and not (HOME / ".git-hooks").exists())
it.find_gitleaks, it.gitleaks_install_command = real_find, real_cmd

r = it.install_git_hooks(ROOT, dry_run=True)
check("dry run: not installed, nothing written", not r["installed"] and not (HOME / ".git-hooks").exists(), r)

r = it.install_git_hooks(ROOT)
check("install: installed", r["installed"], r)
s = it.git_hooks_status()
check("status: on after install, hooksPath the temporary folder", s["state"] == "on"
      and Path(os.path.expanduser(s["hooks_path"])).resolve() == (HOME / ".git-hooks").resolve(), s)

conf = HOME / ".git-hooks" / "hooks.conf"
good = conf.read_text(encoding="utf-8")
conf.write_text('GITLEAKS="/no/such/gitleaks"\n', encoding="utf-8")
check("status: on-no-gitleaks when the recorded gitleaks is gone (secrets not checked)",
      it.git_hooks_status()["state"] == "on-no-gitleaks", it.git_hooks_status())
conf.write_text(good, encoding="utf-8")

p = subprocess.run([sys.executable, str(ROOT / "scripts" / "new-wiki.py"), "--mode", "status",
                    "--bootstrap-source", str(ROOT)], capture_output=True, text=True, encoding="utf-8")
try:
    data = json.loads(p.stdout)
except ValueError:
    data = {}
check("--mode status reports git_hooks beside the tooling state", (data.get("git_hooks") or {}).get("state") == "on",
      p.stdout[-400:] + p.stderr[-300:])
check("... and the tooling state does not depend on it", data.get("state") in ("missing", "partial"), data.get("state"))

p = subprocess.run([sys.executable, str(ROOT / "scripts" / "new-wiki.py"), "--phase", "B", "--git-hooks", "maybe"],
                   capture_output=True, text=True, encoding="utf-8")
check("--git-hooks takes only yes or no", p.returncode == 2 and "--git-hooks" in p.stderr, p.stderr[-300:])

os.environ["WIKI_GIT_HOOKS_STATE"] = "off"
check("WIKI_GIT_HOOKS_STATE pins the reported state (suites)", it.git_hooks_status()["state"] == "off")
del os.environ["WIKI_GIT_HOOKS_STATE"]
os.environ["WIKI_GIT_HOOKS_DRY_RUN"] = "1"
r = it.install_git_hooks(ROOT)
check("WIKI_GIT_HOOKS_DRY_RUN: install writes nothing", not r["installed"] and r["reason"] == "dry run", r)
msg = it.remove_git_hooks(ROOT)
check("WIKI_GIT_HOOKS_DRY_RUN: remove leaves it on", "would run" in msg and it.git_hooks_status()["state"] == "on", msg)
del os.environ["WIKI_GIT_HOOKS_DRY_RUN"]

msg = it.remove_git_hooks(ROOT, dry_run=True)
check("remove, dry run: says what it would run, still on", "would run" in msg and it.git_hooks_status()["state"] == "on", msg)
msg = it.remove_git_hooks(ROOT)
check("remove: off afterwards", it.git_hooks_status()["state"] == "off", msg)
check("remove when off: says nothing to remove", "nothing to remove" in it.remove_git_hooks(ROOT))

failed = [n for ok, n in results if not ok]
for ok, n in results:
    print(("PASS " if ok else "FAIL ") + n)
print(f"\n{len(results) - len(failed)}/{len(results)} passed")
sys.exit(1 if failed else 0)
