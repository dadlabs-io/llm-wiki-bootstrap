"""A stand-in `qmd` for script tests that run the mechanical lint on a temporary wiki. Never shipped.

The lint asks `qmd ls` how many files the search index holds for the wiki, and since task #133 a wiki
that is not indexed makes the run "not fully checked" (exit 3). Tests about something else put this
stand-in first on PATH: it answers `ls` with the wiki as a collection of `n` files.
"""
from __future__ import annotations

import os
import stat
from pathlib import Path


def fake_qmd_env(bin_dir: Path, wiki_root: Path, n: int | None = None, env: dict | None = None) -> dict:
    """An environment whose PATH starts with a `qmd` that lists ``wiki_root`` with ``n`` files
    (default: the .md files under it now)."""
    bin_dir.mkdir(parents=True, exist_ok=True)
    root = Path(wiki_root).resolve().as_posix()
    count = n if n is not None else sum(1 for _ in Path(wiki_root).rglob("*.md"))
    line = f"qmd://{root}/ ({count} files)"
    if os.name == "nt":
        (bin_dir / "qmd.bat").write_text(f"@echo {line}\r\n", encoding="utf-8")
    else:
        sh = bin_dir / "qmd"
        sh.write_text(f"#!/bin/sh\necho '{line}'\n", encoding="utf-8")
        sh.chmod(sh.stat().st_mode | stat.S_IEXEC)
    base = dict(env if env is not None else os.environ)
    base["PATH"] = str(bin_dir) + os.pathsep + base.get("PATH", "")
    base.pop("WIKI_QMD_INDEX", None)
    return base
