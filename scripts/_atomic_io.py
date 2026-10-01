"""
Shared atomic-write helpers for llm-wiki scripts (icarus integration plan §8).

Why this exists
---------------
Most scripts in this directory write files with `Path.write_text(content)` directly.
That call is NOT atomic — on Windows it issues a CreateFile + WriteFile + CloseHandle
sequence, and a crash mid-write leaves the target file truncated or partially written.
Scripts that touch many files in a single run (wiki-reciprocate-backlinks.py,
wiki-index-per-folder.py, wiki-map-compile.py) compound this risk: a crash on entry
247 of 600 corrupts entry 247 *and* leaves the run half-done.

icarus uses `os.replace`, which IS atomic on POSIX *and* NTFS (Windows since Vista).
This module wraps that pattern in two helpers that wiki scripts should use instead
of bare `write_text` / `open(w)` whenever the target file:
  - is read by other scripts (config, frontmatter, sidecar JSON)
  - is the only copy of important state (signals sidecars, INDEX/MAP files)
  - is touched in a multi-file batch where partial-write would leave broken state

What it does
------------
  atomic_write_text(path, content, encoding="utf-8")
    1. Write content to <path>.tmp.<pid>.<short-uuid>
    2. fsync the temp file (best-effort)
    3. os.replace(<path>.tmp.*, <path>)  ← atomic on POSIX + NTFS
    4. On any exception, the temp file is removed and the original is untouched

  atomic_write_bytes(path, data)
    Same pattern for binary writes (rare in wiki scripts, included for completeness).

Both helpers accept Path or str. The temp file lives next to the target (same filesystem),
so os.replace is guaranteed to be atomic (no cross-device move).

Usage
-----
    from _atomic_io import atomic_write_text

    # Replace this:
    Path("foo.md").write_text(rendered, encoding="utf-8")

    # With this:
    atomic_write_text("foo.md", rendered)

That's it. Same semantics, crash-safe.

Limitations
-----------
- Not safe across concurrent writers to the SAME target — pick one writer per file.
- The fsync is best-effort; if your storage layer has its own caching (network mount,
  some VM disk drivers) it may still lie about durability. Same caveat as icarus.
"""

from __future__ import annotations

import os
import uuid
from pathlib import Path
from typing import Union

PathLike = Union[str, os.PathLike]


def _temp_path_for(target: Path) -> Path:
    """Build a sibling temp path. Same parent → guaranteed same filesystem → os.replace is atomic."""
    # Use pid + short uuid to avoid collisions across parallel script invocations
    suffix = f".tmp.{os.getpid()}.{uuid.uuid4().hex[:8]}"
    return target.parent / (target.name + suffix)


def atomic_write_text(path: PathLike, content: str, encoding: str = "utf-8") -> None:
    """Atomically write text to `path`. Crash-safe via tempfile + os.replace.

    On any error, the temp file is removed and the original `path` (if any) is untouched.
    """
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    tmp = _temp_path_for(target)
    try:
        # Write the temp file with explicit encoding
        with open(tmp, "w", encoding=encoding, newline="") as f:
            f.write(content)
            # Best-effort fsync — guarantees the OS has flushed write buffers before rename
            try:
                f.flush()
                os.fsync(f.fileno())
            except OSError:
                # Some filesystems (network mounts, FUSE) don't support fsync; non-fatal
                pass
        # Atomic rename: replaces target if it exists; on POSIX + NTFS this is guaranteed atomic.
        os.replace(tmp, target)
    except Exception:
        # Best-effort cleanup; do NOT mask the original exception
        try:
            if tmp.exists():
                tmp.unlink()
        except OSError:
            pass
        raise


def atomic_write_bytes(path: PathLike, data: bytes) -> None:
    """Atomically write bytes to `path`. Same crash-safety story as atomic_write_text."""
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    tmp = _temp_path_for(target)
    try:
        with open(tmp, "wb") as f:
            f.write(data)
            try:
                f.flush()
                os.fsync(f.fileno())
            except OSError:
                pass
        os.replace(tmp, target)
    except Exception:
        try:
            if tmp.exists():
                tmp.unlink()
        except OSError:
            pass
        raise


__all__ = ["atomic_write_text", "atomic_write_bytes"]
