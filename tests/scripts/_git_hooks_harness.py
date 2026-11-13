"""Shared harness for the machine-wide git hook tests (tests/scripts/test_git_hooks*.py). Never shipped.

Each check builds its own `Machine`: a temporary HOME with `tools/git-hooks/install.sh` run under it, so the
global core.hooksPath, ~/.git-hooks and any fake do-code-change pack live there and never on the real machine,
and no check can see another's state. `run_tests` is the one runner both test files use.
"""
from __future__ import annotations

import os
import random
import shutil
import string
import subprocess
import tempfile
from contextlib import contextmanager
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HOOKS = ROOT / "tools" / "git-hooks"
SH = shutil.which("sh") or shutil.which("bash")
DCC_REL = Path(".claude") / "workflows" / "do-code-change" / "scripts" / "dcc-commit-check.py"
GITHUB_TOKEN_BODY_LEN = 36  # characters after the "ghp_" prefix in a classic GitHub token


def github_token() -> str:
    """A GitHub-shaped token built at run time, so no secret sits in the repository."""
    return "ghp_" + "".join(random.SystemRandom().choice(string.ascii_letters + string.digits) for _ in range(GITHUB_TOKEN_BODY_LEN))


def write_marker_hook(path: Path, marker: Path) -> None:
    """A git hook script that records it ran by writing `marker`, then lets git go on."""
    path.write_text(f"#!/bin/sh\necho ran > '{marker.as_posix()}'\nexit 0\n", encoding="utf-8")


class Machine:
    """A temporary HOME with the hooks installed, and helpers to commit in scratch repos under it."""

    pre_commit_override: str | None = None  # when set, installed over ~/.git-hooks/pre-commit (a bite check's old hook)

    def __init__(self):
        self._td = tempfile.TemporaryDirectory()
        self.base = Path(self._td.name)
        self.home = self.base / "home"
        self.home.mkdir()
        self.hooks = self.home / ".git-hooks"
        self.env = {**os.environ, "HOME": str(self.home), "GIT_CONFIG_NOSYSTEM": "1"}
        self.env.pop("GIT_DIR", None)
        self.install = self.run([SH, str(HOOKS / "install.sh")], ROOT)
        if self.install.returncode != 0:
            self._td.cleanup()
            raise AssertionError(f"install.sh failed: {self.install.stderr[-300:]}{self.install.stdout[-300:]}")
        if Machine.pre_commit_override is not None:
            (self.hooks / "pre-commit").write_text(Machine.pre_commit_override, encoding="utf-8")

    def run(self, args, cwd) -> subprocess.CompletedProcess:
        return subprocess.run(args, cwd=cwd, env=self.env, capture_output=True, text=True,
                              encoding="utf-8", errors="replace")

    def write_words(self, text: str) -> None:
        (self.hooks / "private-words.txt").write_text(text, encoding="utf-8")

    def fake_dcc(self, exit_code: int, message: str = "", ran_marker: Path | None = None) -> None:
        """Write a fake do-code-change commit check where the hook looks for it."""
        body = "import sys\n"
        if ran_marker is not None:
            body += f"from pathlib import Path\nPath({ran_marker.as_posix()!r}).write_text('ran')\n"
        if message:
            body += f"print({message!r}, file=sys.stderr)\n"
        body += f"sys.exit({exit_code})\n"
        f = self.home / DCC_REL
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text(body, encoding="utf-8")

    def new_repo(self, name: str) -> Path:
        r = self.base / name
        r.mkdir()
        for args in (["git", "init", "-q"], ["git", "config", "user.email", "t@example.invalid"],
                     ["git", "config", "user.name", "T"], ["git", "config", "core.autocrlf", "false"]):
            p = self.run(args, r)
            assert p.returncode == 0, f"{' '.join(args)} failed: {p.stderr[-300:]}"
        return r

    def commit(self, r: Path, files: dict[str, str]) -> subprocess.CompletedProcess:
        for rel, body in files.items():
            (r / rel).parent.mkdir(parents=True, exist_ok=True)
            (r / rel).write_text(body, encoding="utf-8")
        self.run(["git", "add", "-A"], r)
        return self.run(["git", "commit", "-q", "-m", "test"], r)

    def head(self, r: Path) -> str | None:
        p = self.run(["git", "rev-parse", "-q", "--verify", "HEAD"], r)
        return p.stdout.strip() if p.returncode == 0 and p.stdout.strip() else None

    def close(self) -> None:
        self._td.cleanup()


@contextmanager
def machine():
    """A Machine for one check, cleaned up however the check ends."""
    m = Machine()
    try:
        yield m
    finally:
        m.close()


def collect_tests(namespace: dict) -> dict:
    """The module's checks: every callable whose name starts with test_, in definition order."""
    return {name: fn for name, fn in namespace.items() if name.startswith("test_") and callable(fn)}


def run_tests(tests: dict, argv: list[str]) -> int:
    """Run the named checks (all when none is named); exit 0 all passed, 1 any failed, 2 an unknown name."""
    unknown = [n for n in argv if n not in tests]
    if unknown:
        print(f"unknown check(s): {', '.join(unknown)}\nknown: {', '.join(tests)}")
        return 2
    names = argv or list(tests)
    failed = 0
    for name in names:
        try:
            tests[name]()
            print(f"PASS {name}")
        except AssertionError as e:
            failed += 1
            print(f"FAIL {name}  [{e}]")
        except Exception as e:  # noqa: BLE001 - a crashing check is reported as one, never ends the run
            failed += 1
            print(f"ERROR {name}  [{type(e).__name__}: {e}]")
    print(f"\n{len(names) - failed}/{len(names)} passed")
    return 1 if failed else 0
