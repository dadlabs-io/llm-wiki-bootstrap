#!/usr/bin/env python3
"""Checks for task #135: the machine-wide git pre-commit hook (tools/git-hooks). Never shipped.

    python tests/scripts/test_git_hooks.py    # exit 0 = every check passed

Everything runs under a temporary HOME, so the install writes its ~/.git-hooks and the global
core.hooksPath there, never on the real machine. Needs git, sh and gitleaks.
"""
from __future__ import annotations

import os
import random
import shutil
import string
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HOOKS = ROOT / "tools" / "git-hooks"
results: list[tuple[bool, str]] = []


def check(name: str, ok: bool, detail: object = ""):
    results.append((bool(ok), name + (f"  [{detail}]" if not ok and detail != "" else "")))


SH = shutil.which("sh") or shutil.which("bash")
td = tempfile.TemporaryDirectory()
home = Path(td.name) / "home"
home.mkdir()
env = {**os.environ, "HOME": str(home), "GIT_CONFIG_NOSYSTEM": "1"}
env.pop("GIT_DIR", None)


def run(args, cwd, **kw) -> subprocess.CompletedProcess:
    return subprocess.run(args, cwd=cwd, env=kw.pop("env", env), capture_output=True, text=True,
                          encoding="utf-8", errors="replace", **kw)


p = run([SH, str(HOOKS / "install.sh")], ROOT)
check("install exits 0", p.returncode == 0, p.stderr[-300:] + p.stdout[-300:])
hooks = home / ".git-hooks"
check("install sets the global core.hooksPath to ~/.git-hooks",
      run(["git", "config", "--global", "core.hooksPath"], ROOT).stdout.strip().replace("\\", "/").endswith(".git-hooks"),
      run(["git", "config", "--global", "core.hooksPath"], ROOT).stdout)
check("install writes the hand-over hooks", (hooks / "pre-push").is_file() and (hooks / "commit-msg").is_file())
check("install records gitleaks", "GITLEAKS=" in (hooks / "hooks.conf").read_text(encoding="utf-8"))
(hooks / "private-words.txt").write_text("# test list\nAcme Widgets Ltd\nsecret-codename\n", encoding="utf-8")


def repo(name: str) -> Path:
    r = Path(td.name) / name
    r.mkdir()
    run(["git", "init", "-q"], r)
    run(["git", "config", "user.email", "t@example.invalid"], r)
    run(["git", "config", "user.name", "T"], r)
    run(["git", "config", "core.autocrlf", "false"], r)
    return r


def commit(r: Path, files: dict[str, str], *extra: str) -> subprocess.CompletedProcess:
    for rel, body in files.items():
        (r / rel).parent.mkdir(parents=True, exist_ok=True)
        (r / rel).write_text(body, encoding="utf-8")
    run(["git", "add", "-A"], r)
    return run(["git", "commit", "-q", "-m", "test", *extra], r)


r = repo("a")
p = commit(r, {"notes.md": "An ordinary note.\n"})
check("a clean commit goes through", p.returncode == 0, p.stderr[-300:])

token = "ghp_" + "".join(random.SystemRandom().choice(string.ascii_letters + string.digits) for _ in range(36))
p = commit(r, {"config.py": f'TOKEN = "{token}"\n'})
check("a staged GitHub token is blocked", p.returncode != 0 and "gitleaks found a secret" in p.stderr, p.stderr[-400:])
check("... and gitleaks names the file", "config.py" in (p.stdout + p.stderr), (p.stdout + p.stderr)[-400:])
run(["git", "reset", "-q"], r)
(r / "config.py").unlink()

p = commit(r, {"report.md": "line one\nWe worked for ACME WIDGETS LTD last year.\n"})
check("a private word in an added line is blocked, any case", p.returncode != 0 and "private word" in p.stderr, p.stderr[-300:])
check("... naming the file and line", "report.md:2:" in p.stderr, p.stderr[-300:])
p = run(["git", "commit", "-q", "-m", "on purpose", "--no-verify"], r)
check("--no-verify commits anyway, on purpose", p.returncode == 0, p.stderr[-200:])
p = commit(r, {"other.md": "unrelated change\n"})
check("a word already committed is not re-checked (only added lines)", p.returncode == 0, p.stdout[-300:] + p.stderr[-300:])

r2 = repo("b")
(r2 / ".private-words-allow").write_text("acme widgets ltd\n", encoding="utf-8")
p = commit(r2, {"client.md": "Acme Widgets Ltd, our client.\n"})
check("a repo's .private-words-allow lets that word through", p.returncode == 0, p.stdout[-300:] + p.stderr[-300:])
p = commit(r2, {"more.md": "the secret-codename again\n"})
check("... but not the other words", p.returncode != 0 and "secret-codename" in p.stderr, p.stderr[-300:])
run(["git", "reset", "-q"], r2)
(r2 / "more.md").unlink()

r3 = repo("c")
marker = Path(td.name) / "local-ran.txt"
(r3 / ".git" / "hooks" / "pre-commit").write_text(f"#!/bin/sh\necho ran > '{marker.as_posix()}'\nexit 0\n", encoding="utf-8")
(r3 / ".git" / "hooks" / "commit-msg").write_text("#!/bin/sh\ngrep -q 'needs-ticket' \"$1\" && exit 1\nexit 0\n", encoding="utf-8")
p = commit(r3, {"x.md": "x\n"})
check("the repo's own pre-commit hook still runs", p.returncode == 0 and marker.is_file(), p.stderr[-300:])
(r3 / "y.md").write_text("y\n", encoding="utf-8")
run(["git", "add", "-A"], r3)
p = run(["git", "commit", "-q", "-m", "needs-ticket"], r3)
check("the repo's own commit-msg hook still runs (and can refuse)", p.returncode != 0, p.stderr[-300:])
(r3 / ".git" / "hooks" / "pre-commit").write_text("#!/bin/sh\necho local-refused >&2\nexit 1\n", encoding="utf-8")
p = run(["git", "commit", "-q", "-m", "fine"], r3)
check("a failing local pre-commit still blocks", p.returncode != 0 and "local-refused" in p.stderr, p.stderr[-300:])

conf = hooks / "hooks.conf"
conf.write_text('GITLEAKS="/nowhere/gitleaks"\n', encoding="utf-8")
r4 = repo("d")
p = commit(r4, {"z.md": "z\n"})
check("no gitleaks: blocked as NOT checked, never a silent pass", p.returncode != 0 and "NOT checked" in p.stderr, p.stderr[-300:])

p = run([SH, str(HOOKS / "install.sh"), "--remove"], ROOT)
check("--remove unsets core.hooksPath", run(["git", "config", "--global", "core.hooksPath"], ROOT).stdout.strip() == "",
      p.stdout[-200:])
td.cleanup()

failed = [n for ok, n in results if not ok]
for ok, n in results:
    print(("PASS " if ok else "FAIL ") + n)
print(f"\n{len(results) - len(failed)}/{len(results)} passed")
raise SystemExit(1 if failed else 0)
