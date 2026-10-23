#!/usr/bin/env python3
"""Checks for task #179 row 25: the test seam that lets the new-wiki suite reach the tooling partial / missing
branches without touching the machine (WIKI_TOOLING_STATE pins the reported state, WIKI_TOOLING_DRY_RUN=1 stops
Phase B's --install-global-if-missing from installing). Never shipped.

    uv run python tests/scripts/test_tooling_state_seam.py    # exit 0 = every check passed

Runs under a temporary home (HOME and USERPROFILE), so ~/.claude is the temporary one, never the machine's.
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
os.environ.update({"HOME": str(HOME), "USERPROFILE": str(HOME), "GIT_CONFIG_NOSYSTEM": "1",
                   "PYTHONIOENCODING": "utf-8"})
for k in ("WIKI_TOOLING_STATE", "WIKI_TOOLING_DRY_RUN"):
    os.environ.pop(k, None)
sys.path.insert(0, str(ROOT / "scripts"))
import _install_tooling as it  # noqa: E402  (imported after the home is moved, so its ~ is the temporary one)

results: list[tuple[bool, str]] = []


def check(name: str, ok: bool, detail: object = ""):
    results.append((bool(ok), name + (f"  [{detail}]" if not ok and detail != "" else "")))


def status_cli(env_extra: dict) -> dict:
    p = subprocess.run([sys.executable, str(ROOT / "scripts" / "new-wiki.py"), "--mode", "status",
                        "--bootstrap-source", str(ROOT)], capture_output=True, text=True, encoding="utf-8",
                       env={**os.environ, **env_extra})
    try:
        return json.loads(p.stdout)
    except ValueError:
        return {"_raw": p.stdout[-300:] + p.stderr[-300:]}


check("the skills folder is under the temporary home", Path(it.CC_GLOBAL_SKILLS_DIR).is_relative_to(HOME),
      it.CC_GLOBAL_SKILLS_DIR)
real = it.global_tooling_status(ROOT)
check("unpinned: a home with no tooling reads missing", real["state"] == "missing", real["state"])
check("unpinned: not marked pinned", not real.get("pinned"), real.get("pinned"))

for state, complete, current in (("installed", True, True), ("stale", True, False),
                                 ("partial", False, False), ("missing", False, False)):
    os.environ["WIKI_TOOLING_STATE"] = state
    s = it.global_tooling_status(ROOT)
    check(f"WIKI_TOOLING_STATE={state} pins the state", s["state"] == state, s["state"])
    check(f"... complete={complete}, current={current}", (s["complete"], s["current"]) == (complete, current),
          (s["complete"], s["current"]))
    check("... and says it is pinned", s.get("pinned") is True, s.get("pinned"))
os.environ["WIKI_TOOLING_STATE"] = "bogus"
check("an unknown value pins nothing", it.global_tooling_status(ROOT)["state"] == "missing")
del os.environ["WIKI_TOOLING_STATE"]

data = status_cli({"WIKI_TOOLING_STATE": "partial"})
check("--mode status reports the pinned state", data.get("state") == "partial", data.get("state") or data)
data = status_cli({"WIKI_TOOLING_STATE": "installed"})
check("--mode status: pinned installed reads installed", data.get("state") == "installed", data.get("state") or data)

# Phase B, global mode, tooling missing, --install-global-if-missing, with the dry run on: nothing installed
work = Path(td.name) / "work"
target, vault = work / "seam-proj", work / "vault"
(vault / "notebooks").mkdir(parents=True)
registry = vault / "linked-notebooks.json"
registry.write_text(json.dumps({"notebooks": {}}), encoding="utf-8")
target.mkdir(parents=True)
p = subprocess.run([sys.executable, str(ROOT / "scripts" / "new-wiki.py"), "--phase", "B",
                    "--target-folder", str(target), "--project-name", "seam-proj",
                    "--project-description", "Wiki for seam-proj", "--project-folder", "none",
                    "--research-folder", "none", "--vault-root", str(vault / "notebooks"),
                    "--registry", str(registry), "--bootstrap-source", str(ROOT), "--drive-enabled", "no",
                    "--skills-install", "global", "--install-global-if-missing"],
                   capture_output=True, text=True, encoding="utf-8",
                   env={**os.environ, "WIKI_TOOLING_DRY_RUN": "1"})
out = p.stdout + p.stderr
check("Phase B with WIKI_TOOLING_DRY_RUN=1 finishes (exit 0)", p.returncode == 0, out[-500:])
check("... installs no skill into ~/.claude", not (Path(it.CC_GLOBAL_SKILLS_DIR) / "wiki-update").exists())
check("... installs no wiki script", not (Path(it.CC_GLOBAL_WIKI_SCRIPTS_DIR) / "wiki-update.py").exists())
check("... and says the install was a dry run", "dry run" in out.lower(), out[-500:])
check("... the project is still scaffolded", (target / ".claude" / "wiki-config.json").is_file(), out[-300:])

sys.stdout.reconfigure(encoding="utf-8")
failed = [n for ok, n in results if not ok]
for ok, n in results:
    print(("PASS " if ok else "FAIL ") + n)
print(f"\n{len(results) - len(failed)}/{len(results)} passed")
sys.exit(1 if failed else 0)
