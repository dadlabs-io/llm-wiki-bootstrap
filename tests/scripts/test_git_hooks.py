#!/usr/bin/env python3
"""Checks for task #135: the machine-wide git pre-commit hook (tools/git-hooks). Never shipped.

    python tests/scripts/test_git_hooks.py            # every check; exit 0 = all passed
    python tests/scripts/test_git_hooks.py <test>     # one check by its function name

Each check builds its own Machine (tests/scripts/_git_hooks_harness.py): a temporary HOME where the install
writes its ~/.git-hooks and the global core.hooksPath, so no check depends on another's state and the real machine
is never touched. Needs git, sh and gitleaks.
"""
from __future__ import annotations

import sys

from _git_hooks_harness import HOOKS, ROOT, SH, Machine, collect_tests, github_token, machine, run_tests

WORDS = "# test list\nAcme Widgets Ltd\nsecret-codename\n"


def _hooks_path(m: Machine) -> str:
    return m.run(["git", "config", "--global", "core.hooksPath"], ROOT).stdout.strip().replace("\\", "/")


def test_install_exits_zero():
    with machine() as m:
        assert m.install.returncode == 0, m.install.stderr[-300:] + m.install.stdout[-300:]


def test_install_sets_the_global_hooks_path():
    with machine() as m:
        assert _hooks_path(m).endswith(".git-hooks"), _hooks_path(m)


def test_install_writes_the_hand_over_hooks():
    with machine() as m:
        r = m.new_repo("h")
        for name in ("pre-push", "commit-msg"):
            stub = m.hooks / name
            assert stub.is_file(), f"{name} not written"
            marker = m.base / f"{name}-ran.txt"
            (r / ".git" / "hooks" / name).write_text(f"#!/bin/sh\necho ran > '{marker.as_posix()}'\nexit 0\n",
                                                     encoding="utf-8")
            p = m.run([SH, str(stub)], r)
            assert p.returncode == 0 and marker.is_file(), f"{name} did not reach the repo's own hook: {p.stderr[-200:]}"


def test_install_records_gitleaks():
    with machine() as m:
        assert "GITLEAKS=" in (m.hooks / "hooks.conf").read_text(encoding="utf-8")


def test_clean_commit_goes_through():
    with machine() as m:
        p = m.commit(m.new_repo("a"), {"notes.md": "An ordinary note.\n"})
        assert p.returncode == 0, p.stderr[-300:]


def test_staged_github_token_is_blocked():
    with machine() as m:
        p = m.commit(m.new_repo("a"), {"config.py": f'TOKEN = "{github_token()}"\n'})
        assert p.returncode != 0 and "gitleaks found a secret" in p.stderr, p.stderr[-400:]


def test_gitleaks_names_the_file():
    with machine() as m:
        p = m.commit(m.new_repo("a"), {"config.py": f'TOKEN = "{github_token()}"\n'})
        assert "config.py" in (p.stdout + p.stderr), (p.stdout + p.stderr)[-400:]


def test_private_word_blocked_in_any_case():
    with machine() as m:
        m.write_words(WORDS)
        for i, word in enumerate(("ACME WIDGETS LTD", "acme widgets ltd", "aCmE wIdGeTs LtD")):
            p = m.commit(m.new_repo(f"a{i}"), {"report.md": f"line one\nWe worked for {word} last year.\n"})
            assert p.returncode != 0 and "private word" in p.stderr, f"{word!r}: {p.stderr[-300:]}"


def test_private_word_block_names_file_line():
    with machine() as m:
        m.write_words(WORDS)
        p = m.commit(m.new_repo("a"), {"report.md": "line one\nWe worked for ACME WIDGETS LTD last year.\n"})
        assert "report.md:2:" in p.stderr, p.stderr[-300:]


def test_no_verify_commits_anyway():
    with machine() as m:
        m.write_words(WORDS)
        r = m.new_repo("a")
        blocked = m.commit(r, {"report.md": "We worked for ACME WIDGETS LTD last year.\n"})
        assert blocked.returncode != 0, "the private word was not blocked first"
        p = m.run(["git", "commit", "-q", "-m", "on purpose", "--no-verify"], r)
        assert p.returncode == 0, p.stderr[-200:]
        assert m.head(r) is not None, "no commit was made"


def test_committed_word_is_not_rechecked():
    with machine() as m:
        m.write_words(WORDS)
        r = m.new_repo("a")
        blocked = m.commit(r, {"report.md": "We worked for ACME WIDGETS LTD last year.\n"})
        assert blocked.returncode != 0, "the private word was not blocked first"
        forced = m.run(["git", "commit", "-q", "-m", "on purpose", "--no-verify"], r)
        assert forced.returncode == 0, "the word was not committed"
        p = m.commit(r, {"other.md": "unrelated change\n"})
        assert p.returncode == 0, p.stdout[-300:] + p.stderr[-300:]


def test_allow_file_lets_its_word_through():
    with machine() as m:
        m.write_words(WORDS)
        r = m.new_repo("b")
        (r / ".private-words-allow").write_text("acme widgets ltd\n", encoding="utf-8")
        p = m.commit(r, {"client.md": "Acme Widgets Ltd, our client.\n"})
        assert p.returncode == 0, p.stdout[-300:] + p.stderr[-300:]


def test_allow_file_keeps_other_words_blocked():
    with machine() as m:
        m.write_words(WORDS)
        r = m.new_repo("b")
        (r / ".private-words-allow").write_text("acme widgets ltd\n", encoding="utf-8")
        p = m.commit(r, {"more.md": "the secret-codename again\n"})
        assert p.returncode != 0 and "secret-codename" in p.stderr, p.stderr[-300:]


def test_repo_pre_commit_hook_still_runs():
    with machine() as m:
        r = m.new_repo("c")
        marker = m.base / "local-ran.txt"
        (r / ".git" / "hooks" / "pre-commit").write_text(f"#!/bin/sh\necho ran > '{marker.as_posix()}'\nexit 0\n",
                                                        encoding="utf-8")
        p = m.commit(r, {"x.md": "x\n"})
        assert p.returncode == 0 and marker.is_file(), p.stderr[-300:]


def test_repo_commit_msg_hook_can_refuse():
    with machine() as m:
        r = m.new_repo("c")
        (r / ".git" / "hooks" / "commit-msg").write_text("#!/bin/sh\ngrep -q 'needs-ticket' \"$1\" && exit 1\nexit 0\n",
                                                        encoding="utf-8")
        ok = m.commit(r, {"x.md": "x\n"})
        assert ok.returncode == 0, f"a message without the trigger was refused: {ok.stderr[-300:]}"
        before = m.head(r)
        (r / "y.md").write_text("y\n", encoding="utf-8")
        m.run(["git", "add", "-A"], r)
        p = m.run(["git", "commit", "-q", "-m", "needs-ticket"], r)
        assert p.returncode != 0, p.stderr[-300:]
        assert m.head(r) == before, "a commit was made despite the commit-msg hook"


def test_failing_repo_pre_commit_still_blocks():
    with machine() as m:
        r = m.new_repo("c")
        (r / ".git" / "hooks" / "pre-commit").write_text("#!/bin/sh\necho local-refused >&2\nexit 1\n", encoding="utf-8")
        p = m.commit(r, {"x.md": "x\n"})
        assert p.returncode != 0 and "local-refused" in p.stderr, p.stderr[-300:]


def test_missing_gitleaks_blocks_as_not_checked():
    with machine() as m:
        (m.hooks / "hooks.conf").write_text('GITLEAKS="/nowhere/gitleaks"\n', encoding="utf-8")
        p = m.commit(m.new_repo("d"), {"z.md": "z\n"})
        assert p.returncode != 0 and "NOT checked" in p.stderr, p.stderr[-300:]


def test_remove_unsets_the_hooks_path():
    with machine() as m:
        assert _hooks_path(m), "the hooks path was never set"
        p = m.run([SH, str(HOOKS / "install.sh"), "--remove"], ROOT)
        assert p.returncode == 0, p.stderr[-200:]
        assert _hooks_path(m) == "", p.stdout[-200:]


TESTS = collect_tests(dict(globals()))

if __name__ == "__main__":
    raise SystemExit(run_tests(TESTS, sys.argv[1:]))
