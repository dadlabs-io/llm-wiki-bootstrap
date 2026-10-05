#!/usr/bin/env python3
"""The scripts' own uv environment (task #71, 2026-10-04): the installer copies pyproject.toml, uv.lock and
.python-version beside the scripts and builds `.venv` there with `uv sync --locked`; every shipped call runs
`uv run --project <scripts dir> python <script>`; the hooks call that environment's python by path.

Run: uv run python tests/scripts/test_tooling_env.py   (needs uv; builds one environment in a temp folder)
"""
from __future__ import annotations

import ast
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
import _install_tooling as it  # noqa: E402

for stream in (sys.stdout, sys.stderr):
    if hasattr(stream, "reconfigure"):
        stream.reconfigure(encoding="utf-8", errors="replace")

results = []


def check(name: str, ok: bool, detail: object = ""):
    results.append(ok)
    print(f"{'PASS' if ok else 'FAIL'} {name}" + ("" if ok else f"  [{detail}]"))


uv = it.find_uv()
check("uv is found", bool(uv), uv)

# the lock matches pyproject.toml
lock = subprocess.run([uv, "lock", "--check", "--project", str(ROOT)], capture_output=True, text=True)
check("uv.lock is current with pyproject.toml (uv lock --check)", lock.returncode == 0, lock.stderr.strip()[-300:])

with tempfile.TemporaryDirectory() as tmp:
    td = Path(tmp)
    dest = td / "wiki-scripts"

    # build, then import every third-party package the scripts use
    line = it.build_tooling_env(ROOT, dest)
    py = it.env_python(dest)
    check("build_tooling_env builds .venv beside the scripts", py.is_file(), line)
    check("the three environment files are copied", all((dest / n).is_file() for n in it.ENV_FILES))
    imp = subprocess.run([uv, "run", "--project", str(dest), "python", "-c",
                          "import yaml, requests, pypdf, yt_dlp, googleapiclient, google.oauth2, google_auth_oauthlib, markitdown"],
                         capture_output=True, text=True)
    check("uv run --project <dest> imports every declared package", imp.returncode == 0, imp.stderr.strip()[-300:])

    # status: current, then stale (a changed lock), then missing (no .venv)
    check("status: current right after the build", it.tooling_env_status(ROOT, dest) == "current",
          it.tooling_env_status(ROOT, dest))
    (dest / ".python-version").write_text("3.12\n", encoding="utf-8")
    check("status: stale when an installed environment file differs from the package",
          it.tooling_env_status(ROOT, dest) == "stale", it.tooling_env_status(ROOT, dest))
    shutil.copy2(ROOT / ".python-version", dest / ".python-version")
    shutil.rmtree(dest / ".venv")
    check("status: missing without .venv", it.tooling_env_status(ROOT, dest) == "missing",
          it.tooling_env_status(ROOT, dest))

    # the hooks call the environment's python by path, never `uv run` (exit 2 there would block every tool call)
    entry = it.hook_entry(dest.as_posix(), "read-guard.py", 30)
    check("hook entry runs the environment's python", entry["command"] == it.env_python(dest.as_posix()).as_posix(),
          entry["command"])
    check("hook entry keeps the script-gone guard", entry["args"][0] == "-c" and entry["args"][-1].endswith("/read-guard.py"),
          entry["args"])
    check("run_command is uv run --project <dir> python <dir>/<script>",
          it.run_command("C:/x/wiki-scripts", "wiki-tasks.py") ==
          "uv run --project C:/x/wiki-scripts python C:/x/wiki-scripts/wiki-tasks.py",
          it.run_command("C:/x/wiki-scripts", "wiki-tasks.py"))

    # refused before anything is written: no uv, and a package without the environment files
    real_find = it.find_uv
    it.find_uv = lambda: None
    try:
        empty_dest = td / "never-written"
        try:
            it.install_tooling(ROOT, scripts_dest=empty_dest, skills_dest=td / "skills-never")
            err = None
        except Exception as e:  # noqa: BLE001
            err = e
        check("no uv: install_tooling raises UvMissing", isinstance(err, it.UvMissing), type(err).__name__)
        check("UvMissing is a FileNotFoundError (callers report it as a missing source)",
              isinstance(err, FileNotFoundError))
        check("no uv: the message names the uv installer", err is not None and "astral.sh/uv" in str(err), err)
        check("no uv: nothing was written", not empty_dest.exists() and not (td / "skills-never").exists())
    finally:
        it.find_uv = real_find
    pkg = td / "pkg-no-env"
    for d in ("scripts", "skills"):
        (pkg / d).mkdir(parents=True)
    try:
        it.install_tooling(pkg, scripts_dest=td / "dest2", skills_dest=td / "skills2")
        err = None
    except Exception as e:  # noqa: BLE001
        err = e
    check("a package without the environment files: FileNotFoundError, not InstallIncomplete",
          type(err) is FileNotFoundError and "pyproject.toml" in str(err), repr(err))
    check("... and nothing was written", not (td / "dest2").exists() and not (td / "skills2").exists())

    # the status report carries the environment
    st = it.global_tooling_status(ROOT, skills_dest=td / "s", scripts_dest=td / "w", agents_dest=td / "a")
    check("global_tooling_status reports env", st.get("env") == "missing", st.get("env"))

# no shipped text calls a wiki script with a bare python
CALL = re.compile(r"(?<!\S)python3? +[\"']?(\{\{WIKI_SCRIPTS_DIR\}\}|~/\.claude/wiki-scripts|<wiki-scripts>)/")
bare = []
for base in ("skills", "agents", "wiki-seed"):
    for f in (ROOT / base).rglob("*.md"):
        for n, text in enumerate(f.read_text(encoding="utf-8").splitlines(), 1):
            for m in CALL.finditer(text):
                if not re.search(r"uv run --project \S+ $", text[:m.start()]):
                    bare.append(f"{f.relative_to(ROOT).as_posix()}:{n}")
check("every shipped call to a wiki script runs through uv run --project", not bare, bare[:10])

# every third-party import in the scripts is declared in pyproject.toml
DIST_OF = {"yaml": "pyyaml", "requests": "requests", "pypdf": "pypdf", "yt_dlp": "yt-dlp",
           "googleapiclient": "google-api-python-client", "google": "google-auth",
           "google_auth_oauthlib": "google-auth-oauthlib", "markitdown": "markitdown"}
declared = set(re.findall(r'^\s*"([A-Za-z0-9_.-]+)', (ROOT / "pyproject.toml").read_text(encoding="utf-8"), re.M))
local = {p.stem for p in (ROOT / "scripts").glob("*.py")}
undeclared = []
for f in sorted((ROOT / "scripts").glob("*.py")) + sorted((ROOT / "skills").glob("*/scripts/*.py")):
    tree = ast.parse(f.read_text(encoding="utf-8"))
    mods = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            mods |= {a.name.split(".")[0] for a in node.names}
        elif isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
            mods.add(node.module.split(".")[0])
    for m in sorted(mods - set(sys.stdlib_module_names) - local):
        if m.startswith("_"):
            continue
        if DIST_OF.get(m) not in declared:
            undeclared.append(f"{f.relative_to(ROOT).as_posix()}: {m}")
check("every third-party import in the scripts is declared in pyproject.toml", not undeclared, undeclared)

print()
print(f"{sum(results)}/{len(results)} passed")
sys.exit(0 if all(results) else 1)
