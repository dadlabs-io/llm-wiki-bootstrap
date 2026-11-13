#!/usr/bin/env python3
"""Checks for the shared git-hook test harness's runner (tests/scripts/_git_hooks_harness.py). Never shipped.

    python tests/scripts/test_git_hooks_harness.py            # every check; exit 0 = all passed
    python tests/scripts/test_git_hooks_harness.py <test>     # one check by its function name

The runner is what both hook test files report through, so a check that crashes or a mistyped name must
show up as a failure, never end the run silently.
"""
from __future__ import annotations

import io
import re
import sys
from contextlib import redirect_stdout

from _git_hooks_harness import collect_tests, run_tests


def _run(tests: dict, argv: list[str]) -> tuple[int, str]:
    out = io.StringIO()
    with redirect_stdout(out):
        code = run_tests(tests, argv)
    return code, out.getvalue()


def test_runner_reports_a_crashing_check_as_error():
    def test_raises():
        raise RuntimeError("deliberate")

    def test_passes():
        pass

    code, out = _run({"test_raises": test_raises, "test_passes": test_passes}, [])
    assert code == 1, out
    assert re.search(r"^ERROR test_raises  \[RuntimeError: deliberate\]$", out, re.MULTILINE), out
    assert "PASS test_passes" in out and "1/2 passed" in out, out


def test_runner_refuses_an_unknown_check_name():
    code, out = _run({"test_passes": lambda: None}, ["test_nope"])
    assert code == 2, out
    assert "unknown check(s): test_nope" in out and "known: test_passes" in out, out


TESTS = collect_tests(dict(globals()))

if __name__ == "__main__":
    raise SystemExit(run_tests(TESTS, sys.argv[1:]))
