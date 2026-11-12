#!/usr/bin/env python3
"""Checks for task #241: the machine pre-commit calls do-code-change's commit check. Never shipped.

    python tests/scripts/test_git_hooks_dcc.py            # every check; exit 0 = all passed
    python tests/scripts/test_git_hooks_dcc.py <test>     # one check by its function name

Each check installs the hooks under its own temporary HOME (never the real machine) and drives a fake
dcc-commit-check.py placed where the hook looks for it. Needs git, sh, python and gitleaks.
"""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HOOKS = ROOT / "tools" / "git-hooks"
SH = shutil.which("sh") or shutil.which("bash")
DCC_REL = Path(".claude") / "workflows" / "do-code-change" / "scripts" / "dcc-commit-check.py"


class Machine:
    """A temporary HOME with the hooks installed, and helpers to commit in scratch repos under it."""

    def __init__(self):
        self._td = tempfile.TemporaryDirectory()
        self.base = Path(self._td.name)
        self.home = self.base / "home"
        self.home.mkdir()
        self.env = {**os.environ, "HOME": str(self.home), "GIT_CONFIG_NOSYSTEM": "1"}
        self.env.pop("GIT_DIR", None)
        p = self.run([SH, str(HOOKS / "install.sh")], ROOT)
        assert p.returncode == 0, p.stderr[-300:] + p.stdout[-300:]

    def run(self, args, cwd) -> subprocess.CompletedProcess:
        return subprocess.run(args, cwd=cwd, env=self.env, capture_output=True, text=True,
                              encoding="utf-8", errors="replace")

    def fake_dcc(self, exit_code: int, message: str) -> None:
        f = self.home / DCC_REL
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text(f"import sys\nprint({message!r}, file=sys.stderr)\nsys.exit({exit_code})\n", encoding="utf-8")

    def repo(self, name: str) -> Path:
        r = self.base / name
        r.mkdir()
        for args in (["git", "init", "-q"], ["git", "config", "user.email", "t@example.invalid"],
                     ["git", "config", "user.name", "T"], ["git", "config", "core.autocrlf", "false"]):
            self.run(args, r)
        return r

    def commit(self, r: Path, files: dict[str, str]) -> subprocess.CompletedProcess:
        for rel, body in files.items():
            (r / rel).write_text(body, encoding="utf-8")
        self.run(["git", "add", "-A"], r)
        return self.run(["git", "commit", "-q", "-m", "test"], r)

    def head(self, r: Path) -> str:
        return self.run(["git", "rev-parse", "-q", "--verify", "HEAD"], r).stdout.strip()

    def close(self) -> None:
        self._td.cleanup()


def test_dcc_pass_lets_the_commit_through():
    m = Machine()
    try:
        ran = m.base / "dcc-ran.txt"
        dcc = m.home / DCC_REL
        dcc.parent.mkdir(parents=True, exist_ok=True)
        dcc.write_text(f"from pathlib import Path\nPath({ran.as_posix()!r}).write_text('ran')\n", encoding="utf-8")
        r = m.repo("a")
        p = m.commit(r, {"notes.md": "An ordinary note.\n"})
        assert ran.is_file(), "the dcc check did not run"
        assert p.returncode == 0, p.stderr[-400:]
        assert m.head(r), "no commit was made"
        assert "do-code-change" not in p.stderr and "FAKE-DCC" not in p.stderr, p.stderr[-400:]
    finally:
        m.close()


def test_dcc_refusal_blocks_the_commit():
    m = Machine()
    try:
        r = m.repo("a")
        first = m.commit(r, {"notes.md": "An ordinary note.\n"})
        assert first.returncode == 0, first.stderr[-400:]
        before = m.head(r)
        m.fake_dcc(1, "FAKE-DCC-REFUSED: tool.py changed without a run")
        p = m.commit(r, {"tool.py": "print('hi')\n"})
        assert p.returncode != 0, "the commit went through"
        assert "FAKE-DCC-REFUSED" in p.stderr, p.stderr[-400:]
        assert m.head(r) == before, "a commit was made despite the refusal"
    finally:
        m.close()


def test_absent_pack_commits_with_a_not_checked_line():
    m = Machine()
    try:
        r = m.repo("a")
        p = m.commit(r, {"notes.md": "An ordinary note.\n"})
        assert p.returncode == 0, p.stderr[-400:]
        assert m.head(r), "no commit was made"
        assert "do-code-change commit check NOT CHECKED - pack not installed" in p.stderr, p.stderr[-400:]
    finally:
        m.close()


def test_blocked_commit_says_no_verify_needs_mark():
    m = Machine()
    try:
        r = m.repo("a")
        m.fake_dcc(1, "FAKE-DCC-REFUSED: tool.py changed without a run")
        p = m.commit(r, {"tool.py": "print('hi')\n"})
        assert p.returncode != 0, "the commit went through"
        last = p.stderr.strip().splitlines()[-1]
        assert last == "pre-commit: fix the lines above. --no-verify only when Mark has said so.", last
        assert "commit anyway" not in p.stderr, p.stderr[-400:]
    finally:
        m.close()


TESTS = {name: fn for name, fn in dict(globals()).items() if name.startswith("test_") and callable(fn)}


def main(argv: list[str]) -> int:
    names = argv or list(TESTS)
    failed = 0
    for name in names:
        try:
            TESTS[name]()
            print(f"PASS {name}")
        except AssertionError as e:
            failed += 1
            print(f"FAIL {name}  [{e}]")
    print(f"\n{len(names) - failed}/{len(names)} passed")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
