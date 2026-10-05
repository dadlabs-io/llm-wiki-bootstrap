#!/usr/bin/env python3
"""_install_tooling.py — shared global tooling-install logic for the LLM-wiki
framework.

Single source of truth for: the script + skill manifests, bootstrap-source
discovery, and the copy/install loop (built on the install-skill.py per-skill
primitive). Imported by BOTH:

  - wiki-upgrade.py   — the standalone "refresh global tooling from master" command
  - new-wiki.py       — project bootstrap (also lays down the global tooling)

Keeping this here means the manifests and the install loop are defined ONCE.
This module is claude-code-focused for the global install; Cursor's rule-based
install stays in new-wiki.py (_phase_tooling_cursor) but reuses these manifests.
"""
from __future__ import annotations

import importlib.util
import json
import os
import shutil
import subprocess
import sys
import traceback
from datetime import datetime
from pathlib import Path

# ---------- Global install targets (claude-code) ----------
CC_GLOBAL_DIR = Path.home() / ".claude"
CC_GLOBAL_SKILLS_DIR = CC_GLOBAL_DIR / "skills"
CC_GLOBAL_WIKI_SCRIPTS_DIR = CC_GLOBAL_DIR / "wiki-scripts"
CC_GLOBAL_AGENTS_DIR = CC_GLOBAL_DIR / "agents"
CC_GLOBAL_CONFIG_PATH = CC_GLOBAL_DIR / "wiki-config.json"
CC_GLOBAL_SETTINGS_PATH = CC_GLOBAL_DIR / "settings.json"

# The SessionStart hook that loads a wiki project's resume files (2026-09-14).
SESSION_HOOK_SCRIPT = "wiki-session-start.py"
SESSION_HOOK_MATCHER = "startup|clear"
SESSION_HOOK_TIMEOUT = 30  # seconds

# The read guard (2026-09-18): refuses a partial read of a document before it runs
# and, at the end of each turn, blocks a stop while a document read in this turn
# has lines not read. One script, three events.
READ_GUARD_SCRIPT = "read-guard.py"
READ_GUARD_EVENTS = {"PreToolUse": "Read|Bash|PowerShell", "Stop": None, "SubagentStop": None}
READ_GUARD_TIMEOUT = 30  # seconds

# ---------- Manifests (single source of truth) ----------
# User-invokable scripts that travel to every install.
TRAVEL_SCRIPTS = [
    "new-wiki.py",
    "read-guard.py",  # PreToolUse/Stop/SubagentStop hook: documents are read whole (2026-09-18)
    "wiki-fetch-drive-folder.py",
    "wiki-fetch-gmail.py",  # the cycle's email step: a Gmail label's links as reviewed candidates (2026-10-03)
    "wiki-fetch-pdf.py",
    "wiki-fetch-youtube.py",
    "wiki-index.py",
    "wiki-index-per-folder.py",
    "wiki-lint-mechanical.py",
    "wiki-fix-links.py",
    "wiki-dequeue.py",
    "wiki-list-add.py",
    "wiki-list-process.py",
    "wiki-list-render.py",
    "wiki-map-compile.py",
    "wiki-promote.py",
    "wiki-qmd-query.py",  # full qmd search behind three GPU slots (two before qmd 2.8.3), no keyword fallback, per-call wait/run log (2026-09-13); keyword-only on a machine with no GPU (search_mode, 2026-10-02)
    "wiki-reciprocate-backlinks.py",
    "wiki-rollback.py",
    "wiki-search-rerank.py",  # truth-status bucket sort over qmd JSON (search spec surface 1); shipped 2026-09-08
    "wiki-session-start.py",  # SessionStart hook: prints the project's resume files, silent elsewhere (2026-09-14)
    "wiki-tasks.py",  # the At a glance task list in sessions/<persona>/task.md, behind /task-list (2026-09-15)
    "wiki-cycle-scope.py",  # what /wiki-cycle's semantic lint, claims and checker read (2026-09-24)
    "wiki-triage.py",  # intake buckets + routing pending tickets, behind /wiki-triage (2026-09-24)
    "wiki-update.py",
    "wiki-upgrade.py",
    "wiki-verify.py",
]

# Skill directories that travel to every install.
TRAVEL_SKILLS = [
    "new-wiki", "wrap-up", "task-list",
    "wiki", "wiki-update", "wiki-search", "wiki-cycle",
    "wiki-discover", "wiki-list", "wiki-triage", "wiki-claims", "wiki-refresh",
    "wiki-report", "wiki-lint", "wiki-promote",
    "wiki-rollback", "wiki-verify",
    # the skill-suggestions loop, moved from agent-builder's library 2026-09-30 (each carries its own scripts/)
    "writing-skill-suggestions", "improving-skills-from-suggestions",
]

# Agent definitions that travel to every claude-code install (→ ~/.claude/agents/).
# Each entry is a folder under the package's agents/ dir containing AGENT.md
# (installed renamed to <name>.md) plus sidecar files (<name>-reading-list.json,
# <name>-config.json — copied as-is if present). evals/ stays gold-only.
TRAVEL_AGENTS = [
    "wiki-ingester",
    "wiki-checker",  # read-only second reader of a staged entry against its raw (2026-09-24, task #42 C3)
]

# Helper scripts copied alongside TRAVEL_SCRIPTS in a tooling install (not
# user-invoked; imported/called by the tooling). Copied only if present.
TOOLING_HELPER_SCRIPTS = ["install-skill.py", "_atomic_io.py", "_wiki_config.py", "_entry_checks.py", "_install_tooling.py"]

# Shared helper modules imported by the travel scripts — MUST ship anywhere the
# scripts run (both global tooling install and per-project Phase B).
SHARED_HELPER_SCRIPTS = ["_atomic_io.py", "_wiki_config.py", "_entry_checks.py", "_install_tooling.py"]

# The scripts' own uv environment (task #71, 2026-10-04): these three files, at the package root, are copied
# beside the scripts and `uv sync --locked` builds `.venv` there. Every script then runs as
# `uv run --project <scripts dir> python <scripts dir>/<x>.py`; the hooks call that environment's python by path.
ENV_FILES = ["pyproject.toml", "uv.lock", ".python-version"]
UV_INSTALL_HINT = {
    "win32": 'powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"',
    "other": "curl -LsSf https://astral.sh/uv/install.sh | sh",
}


def uv_install_command() -> str:
    """The official one-line uv installer for this platform (https://docs.astral.sh/uv/)."""
    return UV_INSTALL_HINT["win32" if sys.platform == "win32" else "other"]


def find_uv():
    """The uv executable's path, or None. Also looks in uv's default install folder, which a shell opened
    before uv was installed does not yet have on PATH."""
    found = shutil.which("uv")
    if found:
        return found
    for folder in (Path.home() / ".local" / "bin", Path.home() / ".cargo" / "bin"):
        exe = folder / ("uv.exe" if sys.platform == "win32" else "uv")
        if exe.is_file():
            return str(exe)
    return None


def env_python(scripts_dir) -> Path:
    """The python of the environment built beside the scripts."""
    venv = Path(scripts_dir) / ".venv"
    return venv / "Scripts" / "python.exe" if sys.platform == "win32" else venv / "bin" / "python"


class UvMissing(FileNotFoundError):
    """uv is not installed: the scripts' environment cannot be built. A FileNotFoundError, so every caller
    that already reports a missing source before anything is written reports this the same way."""


def build_tooling_env(pkg: Path, scripts_dest: Path, dry_run: bool = False) -> str:
    """Copy ENV_FILES from the package root beside the scripts and build the environment there with
    `uv sync --locked`. Raises UvMissing when uv is absent, RuntimeError when the sync fails.
    Returns the line the summary prints."""
    pkg, scripts_dest = Path(pkg), Path(scripts_dest)
    missing = [n for n in ENV_FILES if not (pkg / n).is_file()]
    if missing:
        raise FileNotFoundError(f"environment files missing from the package root {pkg}: {', '.join(missing)}")
    uv = find_uv()
    if not uv:
        raise UvMissing(f"uv is not installed, so the scripts' environment cannot be built. "
                        f"Install it ({uv_install_command()}), open a new terminal, and run the install again.")
    if dry_run:
        for n in ENV_FILES:
            print(f"  WOULD copy {pkg / n} -> {scripts_dest / n}")
        print(f"  WOULD run {uv} sync --locked --project {scripts_dest.as_posix()}")
        return f"would be built with uv sync --locked → {env_python(scripts_dest).as_posix()}"
    scripts_dest.mkdir(parents=True, exist_ok=True)
    for n in ENV_FILES:
        shutil.copy2(pkg / n, scripts_dest / n)
    result = subprocess.run([uv, "sync", "--locked", "--quiet", "--project", str(scripts_dest)],
                            capture_output=True, text=True, encoding="utf-8", errors="replace")
    if result.returncode != 0:
        raise RuntimeError(f"uv sync --locked failed in {scripts_dest} (exit {result.returncode}): "
                           f"{(result.stderr or result.stdout).strip()}")
    return f"built with uv sync --locked → {env_python(scripts_dest).as_posix()}"


def tooling_env_status(pkg: Path, scripts_dest: Path) -> str:
    """current | stale | missing | uv-missing: whether the environment beside the scripts exists, carries the
    package's ENV_FILES, and matches its lock (`uv sync --locked --check`). Read-only."""
    pkg, scripts_dest = Path(pkg), Path(scripts_dest)
    if not env_python(scripts_dest).is_file() or not all((scripts_dest / n).is_file() for n in ENV_FILES):
        return "missing"
    if any((pkg / n).is_file() and (pkg / n).read_bytes() != (scripts_dest / n).read_bytes() for n in ENV_FILES):
        return "stale"
    uv = find_uv()
    if not uv:
        return "uv-missing"
    check = subprocess.run([uv, "sync", "--locked", "--check", "--quiet", "--project", str(scripts_dest)],
                           capture_output=True, text=True, encoding="utf-8", errors="replace")
    return "current" if check.returncode == 0 else "stale"


def run_command(scripts_dir, script_name: str) -> str:
    """How a session runs one of the scripts: through uv, in the scripts' own environment."""
    d = Path(scripts_dir).as_posix().rstrip("/")
    return f"uv run --project {d} python {d}/{script_name}"


def _log(msg):
    print(f"[install-tooling] {msg}")


def is_bootstrap_source(folder: Path) -> bool:
    """The llm-wiki-bootstrap repo root: its installer script beside the /new-wiki skill."""
    return (folder / "scripts" / "new-wiki.py").is_file() and (folder / "skills" / "new-wiki" / "SKILL.md").is_file()


def derive_bootstrap_source(explicit=None):
    """Find the workflows-core / llm-wiki-bootstrap source. Order: explicit arg,
    ~/.claude/wiki-config.json `bootstrap_source`, walk up from this script,
    walk up — looking for `scripts/new-wiki.py` beside `skills/new-wiki/SKILL.md` (the repo root,
    since `bootstrap/` was removed 2026-10-01)."""
    if explicit:
        return Path(explicit).resolve()
    try:
        if CC_GLOBAL_CONFIG_PATH.exists():
            cfg = json.loads(CC_GLOBAL_CONFIG_PATH.read_text(encoding="utf-8"))
            if cfg.get("bootstrap_source"):
                return Path(cfg["bootstrap_source"]).resolve()
    except (json.JSONDecodeError, OSError):
        pass
    here = Path(__file__).resolve()
    for parent in [here.parent, *here.parents]:
        if is_bootstrap_source(parent):
            return parent.resolve()
    cwd_root = Path.cwd()
    for parent in [cwd_root, *cwd_root.parents]:
        if is_bootstrap_source(parent):
            return parent.resolve()
    return None


def _load_frontmatter_checker(scripts_src: Path):
    """Import check_frontmatter_loadable() from the PACKAGE's _entry_checks.py
    (not whatever older copy may already sit in ~/.claude/wiki-scripts). Falls
    back to a permissive no-op with a warning if the import fails — the gate
    must never make the install impossible."""
    path = scripts_src / "_entry_checks.py"
    if path.is_file():
        spec = importlib.util.spec_from_file_location("_entry_checks_pkg", path)
        if spec and spec.loader:
            mod = importlib.util.module_from_spec(spec)
            try:
                spec.loader.exec_module(mod)
                fn = getattr(mod, "check_frontmatter_loadable", None)
                if fn:
                    return fn
            except Exception as e:  # noqa: BLE001
                _log(f"WARN: could not import check_frontmatter_loadable() ({e}); frontmatter gate disabled")
    else:
        _log("WARN: _entry_checks.py missing from package; frontmatter gate disabled")
    return lambda text: []


def _load_gpu_check(scripts_src: Path):
    """gpu_backend() from the PACKAGE's wiki-qmd-query.py (the copy just installed). If it
    cannot be imported, the check reports no GPU: keyword never loads a model, so it is the
    safe side for a machine whose state is unknown."""
    path = scripts_src / "wiki-qmd-query.py"
    try:
        spec = importlib.util.spec_from_file_location("_wiki_qmd_query_pkg", path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod.gpu_backend
    except Exception as e:  # noqa: BLE001 - the search mode must never make the install impossible
        return lambda: (None, f"GPU check unavailable: {e}")


def load_install_skill_fn(scripts_src: Path):
    """Import install_skill() from the package's install-skill.py. Falls back to
    a subprocess shim if the import fails for any reason."""
    install_path = scripts_src / "install-skill.py"
    if install_path.is_file():
        spec = importlib.util.spec_from_file_location("_install_skill_mod", install_path)
        if spec and spec.loader:
            mod = importlib.util.module_from_spec(spec)
            try:
                spec.loader.exec_module(mod)
                if hasattr(mod, "install_skill"):
                    return mod.install_skill
            except Exception as e:  # noqa: BLE001
                _log(f"WARN: could not import install_skill() ({e}); using subprocess fallback")

    def _subprocess_install(skill, tool, skills_src, skills_dest, scripts_dir, dry_run):
        cmd = [
            sys.executable, str(install_path),
            "--skill", skill, "--tool", tool,
            "--skills-src", str(skills_src), "--skills-dest", str(skills_dest),
            "--scripts-dir", str(scripts_dir),
        ]
        if dry_run:
            cmd.append("--dry-run")
        return subprocess.run(cmd).returncode

    return _subprocess_install


# Exec form (command + args), never a shell line: on Windows a shell-form hook can
# pass through cmd.exe, which turns a `>` into a redirect (claude-code #76774, the
# stray zero-byte files). The -c guard keeps "script gone -> exit 0, print nothing",
# so a removed install never breaks a session start.
_SESSION_HOOK_GUARD = ("import os, runpy, sys; p = sys.argv[1]; "
                       "os.path.isfile(p) and runpy.run_path(p, run_name='__main__')")


def hook_entry(scripts_dir, script_name: str, timeout: int, python: str = None) -> dict:
    """A hooks entry: the python of the scripts' own uv environment, named by its full path, running the
    script through the -c guard. Never `uv run` here: with the scripts folder gone, `uv run --project`
    exits 2, and a PreToolUse hook that exits 2 blocks every tool call (measured 2026-10-04)."""
    py = Path(python or env_python(scripts_dir)).as_posix()
    script = f"{str(scripts_dir).rstrip('/')}/{script_name}"
    return {"type": "command", "command": py, "args": ["-c", _SESSION_HOOK_GUARD, script], "timeout": timeout}


def session_hook_entry(scripts_dir, python: str = None) -> dict:
    """The hooks.SessionStart entry for the wiki resume hook."""
    return hook_entry(scripts_dir, SESSION_HOOK_SCRIPT, SESSION_HOOK_TIMEOUT, python)


def _runs_script(h, script_name: str) -> bool:
    return isinstance(h, dict) and any(script_name in str(x)
                                       for x in [h.get("command", ""), *(h.get("args") or [])])


def install_session_hook(entry: dict, settings_path: Path = None, dry_run: bool = False) -> str:
    """Add the wiki resume hook under hooks.SessionStart in settings.json (see install_hooks)."""
    return install_hooks({"SessionStart": SESSION_HOOK_MATCHER}, entry, SESSION_HOOK_SCRIPT,
                         settings_path, dry_run)


def install_hooks(events: dict, entry: dict, script_name: str, settings_path: Path = None,
                  dry_run: bool = False) -> str:
    """Register one script's hook entry under each event in `events` ({event: matcher
    or None}) in settings.json, or bring existing ones up to date, leaving every
    other hook and setting as it is. Backs the file up (<name>.bak-wiki) before
    changing it; writes nothing when already current.
    Returns added | updated | unchanged | would be … | skipped: …"""
    path = Path(settings_path) if settings_path else CC_GLOBAL_SETTINGS_PATH
    try:
        data = json.loads(path.read_text(encoding="utf-8")) if path.is_file() else {}
    except (json.JSONDecodeError, OSError, UnicodeDecodeError) as e:
        return f"skipped: {path} is not readable JSON ({e}); add the {script_name} hook by hand"
    hooks = data.setdefault("hooks", {}) if isinstance(data, dict) else None
    if not isinstance(hooks, dict):
        return f"skipped: unexpected hooks layout in {path}; add the {script_name} hook by hand"
    changes = []
    for event, matcher in events.items():
        groups = hooks.setdefault(event, [])
        if not isinstance(groups, list):
            return f"skipped: unexpected hooks layout in {path}; add the {script_name} hook by hand"
        found = False
        for group in groups:
            if not isinstance(group, dict):
                continue
            for h in group.get("hooks") or []:
                if _runs_script(h, script_name):
                    found = True
                    if h != entry or group.get("matcher") != matcher:
                        h.clear()
                        h.update(entry)
                        if matcher is None:
                            group.pop("matcher", None)
                        else:
                            group["matcher"] = matcher
                        changes.append("updated")
        if not found:
            groups.append({"hooks": [entry]} if matcher is None else {"matcher": matcher, "hooks": [entry]})
            changes.append("added")
    if not changes:
        return "unchanged"
    status = "added" if all(c == "added" for c in changes) else "updated"
    if dry_run:
        return f"would be {status}"
    if path.is_file():
        shutil.copy2(path, path.with_name(path.name + ".bak-wiki"))
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp-wiki")
    tmp.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    tmp.replace(path)
    return status


def configure_search_mode(gpu_fn, config_path: Path = None, dry_run: bool = False) -> str:
    """Set this machine's search mode (`search_mode` in ~/.claude/wiki-config.json) from the
    GPU check, the first time; after that, never change it, only say when it no longer fits
    (task #63, 2026-10-02). `gpu_fn()` returns (backend|None, detail): wiki-qmd-query.py's
    gpu_backend(). Returns the line the summary prints."""
    path = Path(config_path) if config_path else CC_GLOBAL_CONFIG_PATH
    try:
        current = json.loads(path.read_text(encoding="utf-8")).get("search_mode") if path.is_file() else None
    except (json.JSONDecodeError, OSError, AttributeError):
        current = None
    backend, detail = gpu_fn()
    switch = f"{run_command(CC_GLOBAL_WIKI_SCRIPTS_DIR, 'wiki-qmd-query.py')} --set-mode"
    if current is None:
        mode = "full" if backend else "keyword"
        if not dry_run:
            cfg = {}
            if path.is_file():
                try:
                    cfg = json.loads(path.read_text(encoding="utf-8"))
                except (json.JSONDecodeError, OSError):
                    cfg = {}
            cfg["search_mode"] = mode
            path.parent.mkdir(parents=True, exist_ok=True)
            tmp = path.with_name(path.name + ".tmp-wiki")
            tmp.write_text(json.dumps(cfg, indent=2, sort_keys=True), encoding="utf-8")
            tmp.replace(path)
        verb = "would be set" if dry_run else "set"
        if backend:
            return f"{verb}: full (GPU: {backend})"
        return (f"{verb}: keyword — no CUDA or Metal GPU ({detail}), so search is keyword-only and no model "
                f"loads; once the machine has a GPU: {switch} full")
    if current == "keyword" and backend:
        return f"keyword (unchanged) — a GPU is available now ({backend}); to use it: {switch} full"
    if current == "full" and not backend:
        return (f"full (unchanged) — WARNING: the GPU check fails now ({detail}); searches will stop until it "
                f"is fixed, or on a machine with no GPU: {switch} keyword")
    return f"{current} (unchanged)"


class InstallIncomplete(Exception):
    """An install that stopped partway: what was done, where it stopped, and the original error with its
    traceback, so the caller can say so and keep a record (report_incomplete). 2026-10-01: a crash after
    the scripts and before any skill left only a traceback, and nothing said the skills were the old ones."""

    def __init__(self, progress: dict, error: BaseException, traceback_text: str):
        self.progress, self.error, self.traceback_text = progress, error, traceback_text
        self.stopped_at = progress.get("step", "?")
        super().__init__(f"install stopped at {self.stopped_at}: {type(error).__name__}: {error}")


def install_tooling(bootstrap_source: Path, dry_run: bool = False,
                    skills_dest: Path = None, scripts_dest: Path = None) -> dict:
    """Global claude-code tooling install: copy TRAVEL_SCRIPTS (+ helpers) to
    the scripts dir and install each TRAVEL_SKILLS dir via the install-skill
    primitive. Idempotent. Returns a summary dict (caller prints).

    A missing source raises FileNotFoundError before anything is written. Any
    error after that raises InstallIncomplete (what was done, where it stopped,
    the traceback); callers pass it to report_incomplete()."""
    progress = {"step": "start", "dry_run": dry_run, "scripts": [], "skills": [], "agents": []}
    if not find_uv():  # checked before anything is written: without uv the scripts' environment cannot be built
        raise UvMissing(f"uv is not installed, so the scripts' environment cannot be built; nothing was installed. "
                        f"Install it ({uv_install_command()}), open a new terminal, and run the install again.")
    try:
        return _install_tooling_steps(bootstrap_source, dry_run, skills_dest, scripts_dest, progress)
    except Exception as e:  # noqa: BLE001 - every failure after the start is reported the same way
        if progress["step"] == "start":
            raise
        raise InstallIncomplete(progress, e, traceback.format_exc()) from e


def _install_tooling_steps(bootstrap_source, dry_run, skills_dest, scripts_dest, progress: dict) -> dict:
    bootstrap = Path(bootstrap_source)
    pkg = bootstrap
    scripts_src = pkg / "scripts"
    skills_src = pkg / "skills"
    if not scripts_src.is_dir() or not skills_src.is_dir():
        raise FileNotFoundError(f"package scripts/ or skills/ missing under {pkg}")
    env_missing = [n for n in ENV_FILES if not (pkg / n).is_file()]
    if env_missing:  # the scripts' environment is part of the source: refuse before anything is written
        raise FileNotFoundError(f"environment files missing from the package root {pkg}: {', '.join(env_missing)}")

    skills_dest = Path(skills_dest) if skills_dest else CC_GLOBAL_SKILLS_DIR
    scripts_dest = Path(scripts_dest) if scripts_dest else CC_GLOBAL_WIKI_SCRIPTS_DIR
    scripts_dest_value = scripts_dest.expanduser().resolve().as_posix()

    # 1) Copy scripts (TRAVEL_SCRIPTS + helpers)
    progress["step"] = "scripts"
    if not dry_run:
        scripts_dest.mkdir(parents=True, exist_ok=True)
    script_names = list(TRAVEL_SCRIPTS)
    for helper in TOOLING_HELPER_SCRIPTS:
        if (scripts_src / helper).is_file():
            script_names.append(helper)
    travel_copied = helpers_copied = 0
    scripts_missing = []
    for name in script_names:
        s = scripts_src / name
        if not s.is_file():
            scripts_missing.append(name)
            continue
        progress["step"] = f"script {name}"
        if dry_run:
            print(f"  WOULD copy {s} -> {scripts_dest / name}")
        else:
            shutil.copy2(s, scripts_dest / name)
        progress["scripts"].append(name)
        if name in TOOLING_HELPER_SCRIPTS:
            helpers_copied += 1
        else:
            travel_copied += 1

    # 1b) The scripts' own uv environment, built beside them (task #71)
    progress["step"] = "the scripts' environment"
    tooling_env = build_tooling_env(pkg, scripts_dest, dry_run=dry_run)
    progress["env"] = True

    # 2) Install each skill via the install-skill primitive
    #    Gate (2026-09-08): a SKILL.md / AGENT.md whose frontmatter does not
    #    parse is REFUSED — Claude Code's loader drops every field of an
    #    unparseable block, so the artifact would install with no description
    #    and never trigger by description. Installing it silently is worse
    #    than not installing it; the previous copy stays in place.
    check_loadable = _load_frontmatter_checker(scripts_src)
    frontmatter_failed = []  # (artifact, [detail, ...])

    def _frontmatter_ok(label: str, md_path: Path) -> bool:
        try:
            text = md_path.read_text(encoding="utf-8")
        except OSError as e:
            frontmatter_failed.append((label, [f"unreadable: {e}"]))
            return False
        errors = [f"{code}: {detail}" for sev, code, detail in check_loadable(text) if sev == "ERROR"]
        if errors:
            frontmatter_failed.append((label, errors))
            _log(f"ERROR: {label} — frontmatter does not parse; NOT installed. " + "; ".join(errors))
            return False
        return True

    install_fn = load_install_skill_fn(scripts_src)
    skills_installed = 0
    skills_failed = []
    for skill in TRAVEL_SKILLS:
        progress["step"] = f"skill {skill}"
        if not _frontmatter_ok(f"skill {skill}", skills_src / skill / "SKILL.md"):
            skills_failed.append(skill)
            continue
        rc = install_fn(skill=skill, tool="claude-code", skills_src=skills_src,
                        skills_dest=skills_dest, scripts_dir=scripts_dest, dry_run=dry_run)
        if rc == 0:
            skills_installed += 1
            progress["skills"].append(skill)
        else:
            skills_failed.append(skill)

    # 3) Install agents (TRAVEL_AGENTS) → ~/.claude/agents/
    #    AGENT.md → <name>.md; sidecars (<name>-*.json) copied as-is; evals/ not installed.
    agents_src = pkg / "agents"
    agents_dest = CC_GLOBAL_AGENTS_DIR
    agents_installed = 0
    agents_failed = []
    for agent in TRAVEL_AGENTS:
        progress["step"] = f"agent {agent}"
        src_dir = agents_src / agent
        agent_md = src_dir / "AGENT.md"
        if not agent_md.is_file():
            agents_failed.append(agent)
            continue
        if not _frontmatter_ok(f"agent {agent}", agent_md):
            agents_failed.append(agent)
            continue
        sidecars = sorted(p for p in src_dir.glob(f"{agent}-*.json") if p.is_file())
        if dry_run:
            print(f"  WOULD copy {agent_md} -> {agents_dest / (agent + '.md')}")
            for sc in sidecars:
                print(f"  WOULD copy {sc} -> {agents_dest / sc.name}")
        else:
            agents_dest.mkdir(parents=True, exist_ok=True)
            shutil.copy2(agent_md, agents_dest / f"{agent}.md")
            for sc in sidecars:
                shutil.copy2(sc, agents_dest / sc.name)
        agents_installed += 1
        progress["agents"].append(agent)

    # 4) The SessionStart resume hook → ~/.claude/settings.json. Global installs
    #    only: the hook runs for every session on the machine, so it must point
    #    at the global scripts, never at one project's bundled copy.
    session_hook = read_guard = "skipped: not the global scripts folder"
    if os.path.normcase(str(scripts_dest.expanduser().resolve())) == \
            os.path.normcase(str(CC_GLOBAL_WIKI_SCRIPTS_DIR.expanduser().resolve())):
        progress["step"] = "the SessionStart hook"
        session_hook = install_session_hook(session_hook_entry(scripts_dest_value), dry_run=dry_run)
        # 5) The read guard, same rules: global scripts only
        progress["step"] = "the read-guard hooks"
        read_guard = install_hooks(READ_GUARD_EVENTS,
                                   hook_entry(scripts_dest_value, READ_GUARD_SCRIPT, READ_GUARD_TIMEOUT),
                                   READ_GUARD_SCRIPT, dry_run=dry_run)
        # 6) This machine's search mode (task #63), from the package's own GPU check
        progress["step"] = "the search mode"
        search_mode = configure_search_mode(_load_gpu_check(scripts_src), dry_run=dry_run)
    else:
        search_mode = "skipped: not the global scripts folder"

    return {
        "tooling_env": tooling_env,
        "session_hook": session_hook,
        "read_guard": read_guard,
        "search_mode": search_mode,
        "bootstrap": str(bootstrap),
        "scripts_copied": travel_copied,
        "helpers_copied": helpers_copied,
        "skills_installed": skills_installed,
        "skills_failed": skills_failed,
        "scripts_missing": scripts_missing,
        "agents_installed": agents_installed,
        "agents_failed": agents_failed,
        "frontmatter_failed": frontmatter_failed,
        "scripts_dest": str(scripts_dest),
        "skills_dest": str(skills_dest),
        "agents_dest": str(agents_dest),
        "scripts_dest_value": scripts_dest_value,
        "dry_run": dry_run,
    }


def global_tooling_status(bootstrap_source: Path, skills_dest: Path = None,
                          scripts_dest: Path = None, agents_dest: Path = None) -> dict:
    """What the global claude-code tooling looks like right now, against the
    manifests: which skills / scripts / agents are installed, missing, or
    stale (the installed copy differs from the package copy). Read-only.

    Used by /new-wiki before it asks the global-vs-bundled question (so the
    question is driven by the machine's state, not asked blind) and by Phase B
    as the guard that refuses to point a project at an empty global folder.

    A skill is compared with its {{WIKI_SCRIPTS_DIR}} placeholder substituted
    the way install-skill.py writes it; scripts and agents are byte copies.
    """
    bootstrap = Path(bootstrap_source)
    pkg = bootstrap
    skills_src, scripts_src, agents_src = pkg / "skills", pkg / "scripts", pkg / "agents"
    skills_dest = Path(skills_dest) if skills_dest else CC_GLOBAL_SKILLS_DIR
    scripts_dest = Path(scripts_dest) if scripts_dest else CC_GLOBAL_WIKI_SCRIPTS_DIR
    agents_dest = Path(agents_dest) if agents_dest else CC_GLOBAL_AGENTS_DIR
    scripts_value = scripts_dest.expanduser().resolve().as_posix()

    def _read(path: Path):
        try:
            return path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            return None

    missing_skills, stale_skills = [], []
    for skill in TRAVEL_SKILLS:
        src_md = skills_src / skill / "SKILL.md"
        dst_md = skills_dest / skill / "SKILL.md"
        if not dst_md.is_file():
            missing_skills.append(skill)
            continue
        src_text, dst_text = _read(src_md), _read(dst_md)
        if src_text is None:
            continue  # package copy missing — the install would warn, not this check
        if dst_text is None or src_text.replace("{{WIKI_SCRIPTS_DIR}}", scripts_value) != dst_text:
            stale_skills.append(skill)

    missing_scripts, stale_scripts = [], []
    script_names = [n for n in TRAVEL_SCRIPTS + TOOLING_HELPER_SCRIPTS if (scripts_src / n).is_file()]
    for name in script_names:
        src, dst = scripts_src / name, scripts_dest / name
        if not dst.is_file():
            missing_scripts.append(name)
        elif src.read_bytes() != dst.read_bytes():
            stale_scripts.append(name)

    missing_agents, stale_agents = [], []
    for agent in TRAVEL_AGENTS:
        src, dst = agents_src / agent / "AGENT.md", agents_dest / f"{agent}.md"
        if not src.is_file():
            continue
        if not dst.is_file():
            missing_agents.append(agent)
        elif src.read_bytes() != dst.read_bytes():
            stale_agents.append(agent)

    # The scripts' uv environment (task #71): missing or uv-missing counts as missing, stale as stale.
    env = tooling_env_status(pkg, scripts_dest)

    missing = bool(missing_skills or missing_scripts or missing_agents) or env in ("missing", "uv-missing")
    stale = bool(stale_skills or stale_scripts or stale_agents) or env == "stale"
    if len(missing_skills) == len(TRAVEL_SKILLS):
        state = "missing"
    elif missing:
        state = "partial"
    elif stale:
        state = "stale"
    else:
        state = "installed"
    return {
        "bootstrap": str(bootstrap),
        "skills_dest": str(skills_dest),
        "scripts_dest": str(scripts_dest),
        "agents_dest": str(agents_dest),
        "skills_expected": len(TRAVEL_SKILLS),
        "scripts_expected": len(script_names),  # travel scripts + the helpers they import
        "agents_expected": len(TRAVEL_AGENTS),
        "missing_skills": missing_skills,
        "stale_skills": stale_skills,
        "missing_scripts": missing_scripts,
        "stale_scripts": stale_scripts,
        "missing_agents": missing_agents,
        "stale_agents": stale_agents,
        "env": env,
        "complete": not missing,
        "current": not missing and not stale,
        # one word for the skill's question: installed | stale | partial | missing
        "state": state,
    }


def format_tooling_status(status: dict) -> str:
    """A few lines a person can read: what is installed, what is missing, what is stale."""
    lines = [f"Global tooling: {status['state']} - "
             f"{status['skills_expected'] - len(status['missing_skills'])}/{status['skills_expected']} skills, "
             f"{status['scripts_expected'] - len(status['missing_scripts'])}/{status['scripts_expected']} scripts, "
             f"{status['agents_expected'] - len(status['missing_agents'])}/{status['agents_expected']} agents "
             f"at {status['skills_dest']}"]
    if status.get("env") and status["env"] != "current":
        lines.append(f"  environment: {status['env']}" + (f" (install uv: {uv_install_command()})"
                                                           if status["env"] == "uv-missing" else ""))
    for key, label in (("missing_skills", "missing skills"), ("missing_scripts", "missing scripts"),
                       ("missing_agents", "missing agents"), ("stale_skills", "stale skills"),
                       ("stale_scripts", "stale scripts"), ("stale_agents", "stale agents")):
        if status[key]:
            lines.append(f"  {label}: {', '.join(status[key])}")
    return "\n".join(lines)


INSTALL_LOG_DIR = Path.home() / ".cache" / "llm-wiki" / "install-errors"


def report_incomplete(exc: InstallIncomplete, command=None, log_dir=None):
    """Say that an install stopped partway, and keep a record a later session can read.

    Writes the log FIRST (the command, the source, where it stopped, what was and was not done, the full
    traceback, how to finish), then prints one closing line naming it. The printing cannot itself fail on
    encoding: the error that stopped the install may have been exactly that. Folder: $WIKI_INSTALL_LOG_DIR,
    else ~/.cache/llm-wiki/install-errors/. Returns the log's path (None if it could not be written)."""
    p = exc.progress
    dry = p.get("dry_run")
    now = datetime.now().astimezone()
    skills_left = [s for s in TRAVEL_SKILLS if s not in p["skills"]]
    agents_left = [a for a in TRAVEL_AGENTS if a not in p["agents"]]
    error = f"{type(exc.error).__name__}: {exc.error}"
    body = "\n".join([
        "llm-wiki install incomplete" + (" (dry run: nothing was written)" if dry else ""),
        f"when: {now.isoformat(timespec='seconds')}",
        f"command: {' '.join(str(c) for c in (command or sys.argv))}",
        f"python: {sys.executable}",
        f"stopped at: {exc.stopped_at}",
        f"error: {error}",
        "",
        f"done: {len(p['scripts'])} scripts; skills {len(p['skills'])} of {len(TRAVEL_SKILLS)}: "
        f"{', '.join(p['skills']) or 'none'}; agents {len(p['agents'])} of {len(TRAVEL_AGENTS)}: "
        f"{', '.join(p['agents']) or 'none'}",
        f"not done: skills {', '.join(skills_left) or 'none'}; agents {', '.join(agents_left) or 'none'}; "
        "the hooks, if it stopped before them",
        "",
        "to finish: fix the cause above, then re-run `install-wiki.ps1 -RefreshOnly` (or `install-wiki.sh "
        "--refresh-only`, or `wiki-upgrade.py`); `new-wiki.py --mode status` then shows what is current.",
        "",
        "traceback:",
        exc.traceback_text.rstrip(),
        "",
    ])
    log = None
    try:
        folder = Path(log_dir or os.environ.get("WIKI_INSTALL_LOG_DIR") or INSTALL_LOG_DIR)
        folder.mkdir(parents=True, exist_ok=True)
        log = folder / f"install-{now.strftime('%Y%m%d-%H%M%S')}.log"
        log.write_text(body, encoding="utf-8")
    except OSError:
        log = None
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            try:
                stream.reconfigure(encoding="utf-8", errors="replace")
            except (ValueError, OSError):
                pass
    done = (f"{len(p['scripts'])} scripts, {len(p['skills'])} of {len(TRAVEL_SKILLS)} skills, "
            f"{len(p['agents'])} of {len(TRAVEL_AGENTS)} agents {'would have been ' if dry else ''}installed")
    where = (f"full error and what is left: {log}" if log
             else "the log could not be written; the traceback was:\n" + exc.traceback_text)
    line = f"\u26a0\ufe0f INSTALL INCOMPLETE: stopped at {exc.stopped_at} ({error}); {done}; {where}"
    print()
    try:
        print(line)
    except UnicodeEncodeError:
        print(line.encode("ascii", "replace").decode("ascii"))
    sys.stdout.flush()
    return log


def print_summary(summary: dict):
    dry = summary.get("dry_run")
    if summary.get("scripts_missing"):
        _log(f"WARN: scripts not found in package (skipped): {summary['scripts_missing']}")
    if summary.get("skills_failed"):
        _log(f"WARN: skills that failed to install: {summary['skills_failed']}")
    if summary.get("agents_failed"):
        _log(f"WARN: agents that failed to install (missing AGENT.md or unparseable frontmatter): {summary['agents_failed']}")
    if summary.get("frontmatter_failed"):
        _log("ERROR: refused to install artifacts whose frontmatter does not parse "
             "(the loader would drop every field — quote any value containing `: `):")
        for label, errors in summary["frontmatter_failed"]:
            _log(f"  - {label}: " + "; ".join(errors))
    print()
    print("=" * 60)
    print("Global tooling install summary")
    print("=" * 60)
    verb = "would be copied" if dry else "copied"
    print(f"  scripts {verb}:   {summary['scripts_copied']}  (+ {summary['helpers_copied']} helpers)  → {summary['scripts_dest']}")
    verb_s = "would be installed" if dry else "installed"
    print(f"  skills {verb_s}: {summary['skills_installed']}  → {summary['skills_dest']}")
    print(f"  agents {verb_s}: {summary.get('agents_installed', 0)}  → {summary.get('agents_dest', '')}")
    print(f"  environment:      {summary.get('tooling_env', '')}")
    print(f"  session hook:     {summary.get('session_hook', '')}  → {CC_GLOBAL_SETTINGS_PATH} (SessionStart)")
    print(f"  read guard:       {summary.get('read_guard', '')}  → {CC_GLOBAL_SETTINGS_PATH} (PreToolUse, Stop, SubagentStop)")
    print(f"  search mode:      {summary.get('search_mode', '')}  → {CC_GLOBAL_CONFIG_PATH}")
    print(f"  placeholder {{{{WIKI_SCRIPTS_DIR}}}} → {summary['scripts_dest_value']}")
    print()
    print("  Restart Claude Code if these dirs are new so it picks up the")
    print("  new skills + scripts.")
    print("=" * 60)
