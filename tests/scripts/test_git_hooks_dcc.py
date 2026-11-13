#!/usr/bin/env python3
"""Checks for task #241: the machine pre-commit calls do-code-change's commit check. Never shipped.

    python tests/scripts/test_git_hooks_dcc.py            # every check; exit 0 = all passed
    python tests/scripts/test_git_hooks_dcc.py <test>     # one check by its function name

Each check builds its own Machine (tests/scripts/_git_hooks_harness.py): a temporary HOME with the hooks
installed, so a fake do-code-change pack placed in one check can never leak into another, and nothing touches the
real machine. Needs git, sh, python and gitleaks.
"""
from __future__ import annotations

import sys

from _git_hooks_harness import collect_tests, github_token, machine, run_tests

REFUSAL = "FAKE-DCC-REFUSED: tool.py changed without a run"
OWNER_LINE = "pre-commit: fix the lines above. --no-verify only when the machine's owner has said so."


def test_dcc_pass_lets_the_commit_through():
    with machine() as m:
        ran = m.base / "dcc-ran.txt"
        m.fake_dcc(0, ran_marker=ran)
        r = m.new_repo("a")
        p = m.commit(r, {"notes.md": "An ordinary note.\n"})
        assert ran.is_file(), "the dcc check did not run"
        assert p.returncode == 0, p.stderr[-400:]
        assert m.head(r) is not None, "no commit was made"
        assert "do-code-change" not in p.stderr and "FAKE-DCC" not in p.stderr, p.stderr[-400:]


def test_dcc_refusal_blocks_the_commit():
    with machine() as m:
        r = m.new_repo("a")
        first = m.commit(r, {"notes.md": "An ordinary note.\n"})
        assert first.returncode == 0, first.stderr[-400:]
        before = m.head(r)
        m.fake_dcc(1, REFUSAL)
        p = m.commit(r, {"tool.py": "print('hi')\n"})
        assert p.returncode != 0, "the commit went through"
        assert REFUSAL in p.stderr, p.stderr[-400:]
        assert m.head(r) == before, "a commit was made despite the refusal"


def test_absent_pack_commits_with_a_not_checked_line():
    with machine() as m:
        r = m.new_repo("a")
        p = m.commit(r, {"notes.md": "An ordinary note.\n"})
        assert p.returncode == 0, p.stderr[-400:]
        assert m.head(r) is not None, "no commit was made"
        assert "do-code-change commit check NOT CHECKED - pack not installed" in p.stderr, p.stderr[-400:]


def test_blocked_commit_says_no_verify_needs_the_owner():
    with machine() as m:
        r = m.new_repo("a")
        m.fake_dcc(1, REFUSAL)
        p = m.commit(r, {"tool.py": "print('hi')\n"})
        assert p.returncode != 0, "the commit went through"
        last = p.stderr.strip().splitlines()[-1]
        assert last == OWNER_LINE, last
        assert "commit anyway" not in p.stderr, p.stderr[-400:]


def test_gitleaks_block_ends_on_the_owner_line():
    with machine() as m:
        r = m.new_repo("a")
        p = m.commit(r, {"config.py": f'TOKEN = "{github_token()}"\n'})
        assert p.returncode != 0, "the commit went through"
        assert "gitleaks found a secret" in p.stderr, p.stderr[-400:]
        last = p.stderr.strip().splitlines()[-1]
        assert last == OWNER_LINE, last


TESTS = collect_tests(dict(globals()))

if __name__ == "__main__":
    raise SystemExit(run_tests(TESTS, sys.argv[1:]))
