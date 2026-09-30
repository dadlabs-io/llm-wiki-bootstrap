#!/usr/bin/env python3
"""check-freeze.py — the frozen-tests layer of verifying-before-done, as a script rather than a habit.

`tdd-implementation` writes `test-freeze.json` when a test first fails for the right reason:
    [{"file": "tests/test_slug.py", "test_name": "...", "hash": "<sha256 hex>", "frozen_at_step": 1,
      "unfrozen_reason": "<optional — present only when the test was changed out loud>"}, ...]

An entry may record `"hash_of": "test"`, and then the hash covers that ONE test instead of the whole file.
That is what `freeze` writes for a Python test file (2026-09-17): with a whole-file hash, appending step 2's
test to step 1's file broke step 1's freeze, so an honest multi-step run failed this layer every time (found
by do-code-change's hand-off chain). An entry with no `hash_of`, or `"hash_of": "file"`, is the original
whole-file digest and is checked exactly as before; a file whose tests this script cannot find (any language
but Python today) falls back to the whole-file hash, and then each step's tests belong in their own file.

**What "that one test" covers is versioned in the entry** (`hash_scope`, 2026-09-21). An entry written today
records `"hash_scope": "test+module"`: the test's own source — decorators through its last line — plus the
source of every module-level name it loads, transitively. A test that asserts `tables == EXPECTED_TABLES`
reads that list; a `@parametrize` decorator reads its table; a helper assertion reads its own constants. With
the body alone fingerprinted, loosening any of them passed this layer in silence while the test's own lines
stood still — the exact weakening the layer exists to catch (investment-agent, 2026-09-21). An entry with no
`hash_scope` predates the widening and is still verified the old way, so archived records do not all read as
edited; re-freezing an entry moves it to the current scope.

**A freeze file is a record of its own change's moment.** Only the most recent record is meaningful against
HEAD: re-checking a superseded one — `.do-code-change/archive/<date>-<slug>/test-freeze.json` — after later
work legitimately touched those files is expected to fail, and says nothing about the change it recorded
(investment-agent, 2026-09-20: an archived record reported FAIL 45 of 45, every entry, and read as a breach).
Every run prints the record's date, and an archived one is announced in the header and the failure line.

    python scripts/check-freeze.py freeze --freeze-file <dir>/test-freeze.json --file tests/test_x.py \
        --test test_name --step 2 [--unfrozen-reason "..."]

writes or updates that entry — the writer never computes a digest by hand, so the two sides cannot drift.

    python scripts/check-freeze.py retire --freeze-file <json> --file tests/test_x.py --test test_name \n        --reason "<why it was deleted, on whose word>"

marks a frozen test that was DELETED on purpose (task 89, investment-agent 2026-09-27: a test deleted on the owner's
word read exactly like a silently lost one, and an unfreeze needs the file to exist). The entry is kept with the
reason and the date; the check passes it only while the test stays gone and fails it the moment the test exists
again. `retire` refuses (exit 1) while the test still exists, so it is never an exemption for a live test; a
freeze file whose every entry is retired checks nothing and exits 2. Freezing the test again replaces the entry.

This script recomputes the SHA-256 of every listed file and exits:
    0  every entry matches its recorded hash
    1  at least one entry's file differs from its recorded hash, or a listed file is missing, or a
       recorded hash is not a 64-hex digest (unverifiable counts as a failure)

An `unfrozen_reason` records that a change was made deliberately and out loud; it is NOT a permanent
exemption (2026-09-18, found while building the vb6-migration pack). The entry is re-frozen at the new
content and is still compared from then on, so the NEXT silent edit is caught. Before this, one
legitimate unfreeze exempted that test from the layer forever — the exact silent weakening the
mechanism exists to prevent.
    2  the freeze file is missing, unreadable, or lists zero entries — a check over nothing is not a pass
       (Trail of Bits, 2026: a checker that inspects zero items fails)

A whole-file entry whose file differs from the record ONLY in its line endings still matches (2026-09-17,
investment-agent): git's `core.autocrlf` rewrites a checkout, and this layer read that as an edit — two files
with one commit each failed it, untouched. A per-test entry folds line endings already.

Paths in the freeze file resolve from the freeze file's own folder first, then from the current working
directory (the repo root when `do-code-change` keeps the freeze file under `.do-code-change/<slug>/`).

Usage: python scripts/check-freeze.py <path/to/test-freeze.json>
       python scripts/check-freeze.py freeze --freeze-file <json> --file <test file> --test <name> --step <n>
       python scripts/check-freeze.py retire --freeze-file <json> --file <test file> --test <name> --reason "<why>"
       python scripts/check-freeze.py --self-test
Stdlib-only, Python 3.8+.
"""
from __future__ import annotations

import argparse
import ast
import contextlib
import datetime as _dt
import io
import hashlib
import json
import re
import sys
import tempfile
from pathlib import Path
from typing import List, Optional, Tuple

_HEX64 = re.compile(r"^[0-9a-f]{64}$", re.IGNORECASE)
SELF_TEST_MINIMUM = 45   # the exact number of assertions the scenarios below run; bump with them


def sha256_of(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_source(path: Path, test_name: str) -> Optional[str]:
    """The source of ONE test in a Python file — its decorators through its last line, line endings folded —
    or None when the file is not Python, does not parse, or holds no (single) test of that name. The name may be
    qualified (`TestClass::test_x`, `TestClass.test_x`); the last component is the function."""
    if path.suffix.lower() != ".py":
        return None
    try:
        text = path.read_text(encoding="utf-8")
        tree = ast.parse(text)
    except (OSError, SyntaxError, UnicodeDecodeError):
        return None
    wanted = re.split(r"::|\.", test_name.strip())[-1]
    lines = text.replace("\r\n", "\n").split("\n")
    found: List[str] = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == wanted:
            start = min([node.lineno] + [d.lineno for d in node.decorator_list]) - 1
            end = node.end_lineno or node.lineno
            found.append("\n".join(lines[start:end]))
    return found[0] if len(found) == 1 else None   # two tests of one name: ambiguous, so fall back to the file


def _segment(node: ast.AST, lines: List[str]) -> str:
    """One top-level definition's source — decorators through its last line, line endings folded."""
    start = min([node.lineno] + [d.lineno for d in getattr(node, "decorator_list", [])]) - 1
    return "\n".join(lines[start:(node.end_lineno or node.lineno)])


def _toplevel_defs(tree: ast.Module, lines: List[str]) -> dict:
    """name -> source, for every module-level assignment, function and class. These are the names a test
    can load without importing anything: an `EXPECTED` constant, a `parametrize` table, a helper assertion."""
    out = {}
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            out[node.name] = _segment(node, lines)
        elif isinstance(node, ast.Assign):
            for t in node.targets:
                if isinstance(t, ast.Name):
                    out[t.id] = _segment(node, lines)
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            out[node.target.id] = _segment(node, lines)
    return out


def _names_loaded(node: ast.AST) -> set:
    """Every name the node reads, decorators included — `ast.walk` covers a function's decorator_list."""
    return {n.id for n in ast.walk(node) if isinstance(n, ast.Name) and isinstance(n.ctx, ast.Load)}


def test_fingerprint(path: Path, test_name: str) -> Optional[str]:
    """The test's own source PLUS the source of every module-level name it loads, transitively (a helper
    that reads a constant brings the constant too), sorted by name and separated by a marker.

    Without this, `test_source` alone fingerprints the function body while the values it asserts against sit
    outside it: loosening a shared `EXPECTED` list, a `parametrize` table, or a helper's assertion passed the
    frozen-tests layer silently — the exact weakening the layer exists to catch (investment-agent,
    2026-09-21). Only names defined at module level in this file resolve; an import resolves to nothing and
    is left out, since its source is not here to hash."""
    if path.suffix.lower() != ".py":
        return None
    try:
        text = path.read_text(encoding="utf-8")
        tree = ast.parse(text)
    except (OSError, SyntaxError, UnicodeDecodeError):
        return None
    own = test_source(path, test_name)
    if own is None:
        return None
    lines = text.replace("\r\n", "\n").split("\n")
    defs = _toplevel_defs(tree, lines)
    wanted = re.split(r"::|\.", test_name.strip())[-1]
    node = next((n for n in ast.walk(tree)
                 if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.name == wanted), None)
    if node is None:
        return None
    pending = _names_loaded(node) - {wanted}
    seen: dict = {}
    while pending:
        name = pending.pop()
        if name in seen or name not in defs:
            continue
        seen[name] = defs[name]
        try:
            sub = ast.parse(defs[name])
        except SyntaxError:
            continue
        pending |= (_names_loaded(sub) - set(seen) - {wanted})
    parts = [own] + [f"\n# module-level: {n}\n{seen[n]}" for n in sorted(seen)]
    return "".join(parts)


def entry_hash(path: Path, entry: dict, recorded: str = "") -> Tuple[str, str]:
    """(digest, what it covers) for one entry: the named test's own source when the entry says so and the test
    can be found, else the whole file.

    The whole-file digest is taken over the bytes as they are, but a file whose only difference from `recorded`
    is its line endings hashes to `recorded` (investment-agent, 2026-09-17: git's autocrlf rewrote two test files
    on checkout and this layer read a conversion as an edit — nothing had touched them, and at that point a real
    edit and a conversion are indistinguishable). Folded both ways, so a digest recorded on either kind of
    checkout still matches. The per-test path folds line endings already."""
    if str(entry.get("hash_of", "file")).lower() == "test":
        name = str(entry.get("test_name") or "")
        # The scope is versioned per entry (2026-09-21): an entry recorded before the widening carries no
        # `hash_scope` and is still verified the old way, so archived records do not all read as edited.
        if str(entry.get("hash_scope", "")).lower() == "test+module":
            src = test_fingerprint(path, name)
            if src is not None:
                return hashlib.sha256(src.encode("utf-8")).hexdigest(), "test+module"
        else:
            src = test_source(path, name)
            if src is not None:
                return hashlib.sha256(src.encode("utf-8")).hexdigest(), "test"
    raw = path.read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    if recorded and digest != recorded:
        folded = raw.replace(b"\r\n", b"\n")
        if hashlib.sha256(folded).hexdigest() == recorded or hashlib.sha256(folded.replace(b"\n", b"\r\n")).hexdigest() == recorded:
            return recorded, "file (line endings differ only)"
    return digest, "file"


def write_freeze(freeze_file: Path, rel: str, test_name: str, step: Optional[int], reason: Optional[str],
           repo_root: Optional[Path] = None) -> int:
    """Record (or re-record) one test's freeze entry, hashing the test's own source where that is possible."""
    base = repo_root or Path.cwd()
    path = (base / rel) if not Path(rel).is_absolute() else Path(rel)
    if not path.is_file():
        print(f"FAIL: {rel} not found from {base} — nothing to freeze")
        return 2
    entries = []
    if freeze_file.is_file():
        try:
            loaded = json.loads(freeze_file.read_text(encoding="utf-8"))
            entries = loaded if isinstance(loaded, list) else (loaded.get("entries") or loaded.get("tests") or [])
        except Exception as e:  # noqa: BLE001
            print(f"FAIL: freeze file unreadable ({e})")
            return 2
    entry = {"file": rel, "test_name": test_name, "hash_of": "test", "hash_scope": "test+module"}
    digest, covers = entry_hash(path, entry)
    entry.update({"hash": digest, "hash_of": "test" if covers.startswith("test") else "file",
                  "frozen_at_step": step, "frozen_at": _today()})
    if covers.startswith("test"):
        entry["hash_scope"] = covers
    else:
        entry.pop("hash_scope", None)
    if reason:
        entry["unfrozen_reason"] = reason
    entries = [e for e in entries if not (str(e.get("file")) == rel and str(e.get("test_name")) == test_name)]
    entries.append(entry)
    freeze_file.parent.mkdir(parents=True, exist_ok=True)
    freeze_file.write_text(json.dumps(entries, indent=2), encoding="utf-8")
    print(f"frozen: {rel} ({test_name}) by {covers} hash {digest[:12]}…"
          + ("" if covers.startswith("test") else
             " — the whole file, so a later test appended here re-freezes this entry"))
    return 0


def test_present(path: Optional[Path], test_name: str) -> bool:
    """True when the test still exists: its file is there and, for a Python file, a function of that name is in it.
    A file that does not parse, or is not Python, counts as present — absence has to be proved, never assumed."""
    if path is None or not path.is_file():
        return False
    if path.suffix.lower() != ".py":
        return True
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"))
    except (OSError, SyntaxError, UnicodeDecodeError):
        return True
    wanted = re.split(r"::|\.", test_name.strip())[-1]
    return any(isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.name == wanted for n in ast.walk(tree))


def retire_entry(freeze_file: Path, rel: str, test_name: str, reason: str, repo_root: Optional[Path] = None) -> int:
    """Mark one frozen test as deleted on purpose, with the reason and the date (task 89, investment-agent
    2026-09-27: a test deleted on the owner's word read exactly like a silently lost one, and an unfreeze needs the
    file to exist). The entry is kept; the check then passes it only while the test stays gone. Refused (exit 1)
    while the test still exists, so a retirement can never become an exemption for a live test."""
    if not (reason or "").strip() or "\n" in reason:
        print("FAIL: retire needs a one-line --reason: why the test was deleted, and on whose word")
        return 2
    try:
        loaded = json.loads(freeze_file.read_text(encoding="utf-8"))
    except Exception as e:  # noqa: BLE001
        print(f"FAIL: freeze file unreadable ({e})")
        return 2
    entries = loaded if isinstance(loaded, list) else (loaded.get("entries") or loaded.get("tests") or [])
    match = [e for e in entries if str(e.get("file")) == rel and str(e.get("test_name")) == test_name]
    if not match:
        print(f"FAIL: {freeze_file.as_posix()} holds no entry for {rel} ({test_name}) — nothing to retire")
        return 2
    if test_present(resolve(rel, freeze_file.parent, repo_root), test_name):
        print(f"REFUSED: {rel} ({test_name}) still exists — retire only a test that was deleted; a test that changed "
              f"is re-frozen with `freeze --unfrozen-reason`")
        return 1
    for e in match:
        e["retired"] = {"reason": " ".join(reason.split()), "date": _today()}
    freeze_file.write_text(json.dumps(entries, indent=2), encoding="utf-8")
    print(f"retired: {rel} ({test_name}) — {' '.join(reason.split())}")
    return 0


ARCHIVED_NOTE = (
    "a freeze file records its OWN change's moment, so only the most recent record is meaningful against "
    "HEAD; re-checking an archived record after later work legitimately touched those files is expected to "
    "fail, and says nothing about the change it recorded")


def _today() -> str:
    return _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%d")


def archived_record(freeze: Path) -> bool:
    """True when the freeze file sits under an `archive/` folder — a superseded record of an earlier change
    (do-code-change moves each finished run to `.do-code-change/archive/<date>-<slug>/`)."""
    return any(part.lower() == "archive" for part in freeze.resolve().parts[:-1])


def record_date(freeze: Path, entries: list) -> str:
    """When the record was written, for the header: the newest `frozen_at` the entries carry, else the date
    in an archive folder's name, else the file's own modification date."""
    stamps = sorted(str(e.get("frozen_at")) for e in entries if isinstance(e, dict) and e.get("frozen_at"))
    if stamps:
        return stamps[-1]
    for part in reversed(freeze.resolve().parts[:-1]):
        m = re.match(r"^(\d{4}-\d{2}-\d{2})", part)
        if m:
            return m.group(1)
    try:
        return _dt.datetime.fromtimestamp(freeze.stat().st_mtime, _dt.timezone.utc).strftime("%Y-%m-%d")
    except OSError:
        return "date not recorded"


def resolve(rel: str, freeze_dir: Path, repo_root: Optional[Path] = None) -> Path | None:
    for base in ([repo_root] if repo_root else []) + [freeze_dir, Path.cwd()]:
        candidate = (base / rel)
        if candidate.is_file():
            return candidate
    return None


def main(argv: list[str]) -> int:
    if len(argv) >= 2 and argv[1] == "freeze":
        ap = argparse.ArgumentParser(prog="check-freeze.py freeze")
        ap.add_argument("--freeze-file", required=True)
        ap.add_argument("--file", required=True, help="the test file, relative to the repo root")
        ap.add_argument("--test", required=True, help="the test's name (TestClass::test_x is accepted)")
        ap.add_argument("--step", type=int, default=None)
        ap.add_argument("--unfrozen-reason", default=None)
        a = ap.parse_args(argv[2:])
        return write_freeze(Path(a.freeze_file), a.file, a.test, a.step, a.unfrozen_reason)
    if len(argv) >= 2 and argv[1] == "retire":
        ap = argparse.ArgumentParser(prog="check-freeze.py retire")
        ap.add_argument("--freeze-file", required=True)
        ap.add_argument("--file", required=True, help="the deleted test's file, as the entry records it")
        ap.add_argument("--test", required=True, help="the deleted test's name, as the entry records it")
        ap.add_argument("--reason", required=True, help="one line: why it was deleted, and on whose word")
        ap.add_argument("--repo", default=None, help="the repo the entry's path is relative to (default: cwd)")
        a = ap.parse_args(argv[2:])
        return retire_entry(Path(a.freeze_file), a.file, a.test, a.reason, Path(a.repo) if a.repo else None)
    if len(argv) == 2 and argv[1] == "--self-test":
        return self_test()
    repo_root = None
    if len(argv) == 4 and argv[2] == "--repo":   # the repo the freeze file's paths are relative to (default: cwd)
        repo_root, argv = Path(argv[3]), argv[:2]
    if len(argv) != 2:
        print("usage: check-freeze.py <test-freeze.json> [--repo <dir>] | freeze --freeze-file <json> --file <f> "
              "--test <name> | --self-test")
        return 2
    freeze = Path(argv[1])
    if not freeze.is_file():
        print(f"FAIL: freeze file not found: {freeze} — no frozen-tests layer can be checked")
        return 2
    try:
        entries = json.loads(freeze.read_text(encoding="utf-8"))
    except Exception as e:  # noqa: BLE001
        print(f"FAIL: freeze file unreadable ({e})")
        return 2
    if isinstance(entries, dict):
        entries = entries.get("entries") or entries.get("tests") or []
    if not isinstance(entries, list) or not entries:
        print("FAIL: freeze file lists zero entries — a check over nothing is a failure, not a pass")
        return 2

    is_archived = archived_record(freeze)
    print(f"checking {freeze.as_posix()} — {len(entries)} entr{'y' if len(entries) == 1 else 'ies'}, "
          f"recorded {record_date(freeze, entries)}"
          + (f"\nNOTE: this is an ARCHIVED RECORD of a finished change — {ARCHIVED_NOTE}." if is_archived else ""))
    failures = 0
    retired = 0
    for i, entry in enumerate(entries, 1):
        rel = str(entry.get("file", "")).strip()
        recorded = str(entry.get("hash", "")).strip().lower()
        reason = entry.get("unfrozen_reason")
        name = entry.get("test_name") or "?"
        path = resolve(rel, freeze.parent, repo_root) if rel else None
        if isinstance(entry.get("retired"), dict):
            # Deleted on purpose (task 89): passes only while the test stays gone.
            why = str(entry["retired"].get("reason", ""))[:100]
            if test_present(path, str(name)):
                print(f"FAIL [{i}] {rel} ({name}): retired as deleted ({why}) but the test exists — re-freeze it with "
                      f"`freeze`, or delete it; a retirement never covers a live test")
                failures += 1
            else:
                print(f"ok   [{i}] {rel} ({name}): retired, deleted on purpose — {why}")
                retired += 1
            continue
        if path is None:
            print(f"FAIL [{i}] {rel or '<no file>'} ({name}): listed file not found")
            failures += 1
            continue
        if not _HEX64.match(recorded):
            print(f"FAIL [{i}] {rel} ({name}): recorded hash {recorded!r} is not a sha256 hex digest — unverifiable")
            failures += 1
            continue
        actual, covers = entry_hash(path, entry, recorded)
        subject = "the test" if covers.startswith("test") else "the file"
        if reason and actual == recorded:
            # An unfreeze is a recorded event, not a permanent exemption: the entry still has to match the hash
            # it was re-frozen at, so the NEXT silent edit is caught (2026-09-18).
            print(f"ok   [{i}] {rel} ({name}): matches the hash it was unfrozen at — {str(reason)[:100]}")
            continue
        if actual != recorded:
            hint = ("" if covers.startswith("test") else
                    " — this entry hashes the whole file, so a later test appended to it reads the same as an edit; "
                    "re-freeze it with `check-freeze.py freeze`, which hashes the test's own source")
            print(f"FAIL [{i}] {rel} ({name}): {subject} changed since it was frozen and no unfrozen_reason is recorded "
                  f"(recorded {recorded[:12]}…, actual {actual[:12]}…){hint}")
            failures += 1
        else:
            print(f"ok   [{i}] {rel} ({name}): matches frozen hash ({covers})")
    checked = len(entries)
    if failures:
        print(f"frozen-tests layer: FAIL — {failures} of {checked} entr{'y' if checked == 1 else 'ies'} failed"
              + (f"\n   This is an ARCHIVED RECORD: {ARCHIVED_NOTE}. Check the current change's freeze file "
                 "instead, and read this result as history, not as broken frozen tests."
                 if is_archived else ""))
        return 1
    if retired == checked:
        print(f"frozen-tests layer: not checked — no live entry: all {checked} are retired, so nothing is left to "
              f"check (a check over nothing is not a pass)")
        return 2
    print(f"frozen-tests layer: PASS — {checked} entr{'y' if checked == 1 else 'ies'} checked, all match or unfrozen with a reason"
          + (f" ({retired} retired: deleted on purpose)" if retired else ""))
    return 0


def _captured(fn) -> str:
    """Run fn() while capturing stdout, and return what it printed (the self-test reads the wording)."""
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        fn()
    return buf.getvalue()


def self_test() -> int:
    """The scorer must still discriminate: a per-test freeze survives a test appended to the same file and still
    catches that test being weakened; a whole-file entry behaves exactly as it did before."""
    ran: List[str] = []
    failures: List[str] = []

    def check(label: str, cond: bool, detail: str = "") -> None:
        ran.append(label)
        if not cond:
            failures.append(f"{label}: {detail or 'condition false'}")

    step1 = "def test_one():\n    assert to_csv([['a']], ['h']) == 'h\\r\\na\\r\\n'\n"
    step1_weak = "def test_one():\n    assert to_csv([['a']], ['h']) is not None\n"
    step2 = "\n\ndef test_two():\n    assert to_csv([], ['h']) == 'h\\r\\n'\n"
    with tempfile.TemporaryDirectory(prefix="check-freeze-selftest-") as td:
        root = Path(td)
        (root / "tests").mkdir()
        f = root / "tests" / "test_x.py"
        f.write_text(step1, encoding="utf-8")
        fz = root / ".do-code-change" / "slug" / "test-freeze.json"
        rc = write_freeze(fz, "tests/test_x.py", "test_one", 1, None, repo_root=root)
        check("freeze records an entry", rc == 0 and fz.is_file(), f"exit {rc}")
        entries = json.loads(fz.read_text(encoding="utf-8"))
        check("a Python test is frozen by its own source, not the whole file", entries[0].get("hash_of") == "test", str(entries[0]))
        check("the entry carries file, test name and step",
              entries[0]["file"] == "tests/test_x.py" and entries[0]["test_name"] == "test_one"
              and entries[0]["frozen_at_step"] == 1, str(entries[0]))
        check("a freshly frozen test passes the check", main([__file__, str(fz), "--repo", str(root)]) == 0)
        f.write_text(step1 + step2, encoding="utf-8")
        check("a test appended to the same file leaves the earlier freeze intact (the 2026-09-17 chain failure)",
              main([__file__, str(fz), "--repo", str(root)]) == 0)
        write_freeze(fz, "tests/test_x.py", "test_two", 2, None, repo_root=root)
        check("both tests in one file are frozen and pass",
              len(json.loads(fz.read_text(encoding="utf-8"))) == 2 and main([__file__, str(fz), "--repo", str(root)]) == 0)
        f.write_text(step1_weak + step2, encoding="utf-8")
        check("weakening the frozen test's assertion still fails", main([__file__, str(fz), "--repo", str(root)]) == 1)
        # An unfreeze is a recorded event, not a permanent exemption: it re-freezes at the NEW content and the
        # entry is still compared from then on, so the next silent edit is caught (2026-09-18).
        f.write_text(step1_weak + step2, encoding="utf-8")
        write_freeze(fz, "tests/test_x.py", "test_one", 1, "the seam was wrong; re-agreed with the user", repo_root=root)
        check("an unfreeze records the deliberate change and passes at its new hash",
              main([__file__, str(fz), "--repo", str(root)]) == 0)
        f.write_text(step1_weak.replace("is not None", "is not None  # weakened again") + step2, encoding="utf-8")
        check("a test that changed AGAIN after an unfreeze fails — an unfreeze is not a permanent exemption",
              main([__file__, str(fz), "--repo", str(root)]) == 1)
        write_freeze(fz, "tests/test_x.py", "test_one", 1, "re-agreed a second time", repo_root=root)
        check("re-freezing with a new reason passes again at the new hash",
              main([__file__, str(fz), "--repo", str(root)]) == 0)
        check("re-freezing a test replaces its entry, never duplicates it",
              [e["test_name"] for e in json.loads(fz.read_text(encoding="utf-8"))] == ["test_two", "test_one"],
              str([e["test_name"] for e in json.loads(fz.read_text(encoding="utf-8"))]))
        # an older freeze file, or a language whose tests cannot be located: the whole-file digest, unchanged
        f.write_text(step1 + step2, encoding="utf-8")
        legacy = root / "legacy.json"
        legacy.write_text(json.dumps([{"file": "tests/test_x.py", "test_name": "test_one", "frozen_at_step": 1,
                                       "hash": sha256_of(f)}]), encoding="utf-8")   # the bytes on disk: a Windows write translates newlines
        check("an entry with no hash_of is still the whole-file digest", main([__file__, str(legacy), "--repo", str(root)]) == 0)
        # a CRLF checkout must not read as an edit (investment-agent, 2026-09-17: two files with one commit each
        # failed this layer after git's autocrlf rewrote them, and a conversion looked exactly like a weakened test)
        f.write_bytes(f.read_bytes().replace(b"\n", b"\r\n"))
        check("a whole-file entry survives a line-ending conversion", main([__file__, str(legacy), "--repo", str(root)]) == 0)
        f.write_bytes((step1_weak + step2).encode("utf-8").replace(b"\n", b"\r\n"))
        check("a whole-file entry still fails when the content changed as well as the line endings",
              main([__file__, str(legacy), "--repo", str(root)]) == 1)
        f.write_text(step1 + step2, encoding="utf-8")
        f.write_text(step1 + step2 + "\n# a comment\n", encoding="utf-8")
        check("a whole-file entry still fails on any edit to the file", main([__file__, str(legacy), "--repo", str(root)]) == 1)
        (root / "tests" / "test_other.txt").write_text("not python\n", encoding="utf-8")
        fz2 = root / "fallback.json"
        write_freeze(fz2, "tests/test_other.txt", "t", 1, None, repo_root=root)
        check("a non-Python test file falls back to the whole-file hash",
              json.loads(fz2.read_text(encoding="utf-8"))[0]["hash_of"] == "file", fz2.read_text(encoding="utf-8"))
        check("freezing a file that does not exist fails",
              write_freeze(root / "x.json", "tests/nope.py", "t", 1, None, repo_root=root) == 2)
        # ── task 55: what a test LOADS from module level is part of what it asserts ──
        mod = root / "tests" / "test_mod.py"
        mod.write_text(
            "import pytest\n\n"
            "EXPECTED = ['orders', 'customers']\n\n"
            "CASES = [(1, 2), (2, 4)]\n\n"
            "SHAPE = (3, 2)\n\n"
            "def _assert_shape(x):\n    assert x.shape == SHAPE\n\n"
            "def test_shape(df):\n    _assert_shape(df)\n\n"
            "def test_tables(db):\n    assert tables(db) == EXPECTED\n\n"
            "@pytest.mark.parametrize('a,b', CASES)\ndef test_double(a, b):\n    assert a * 2 == b\n",
            encoding="utf-8")
        fz3 = root / "mod.json"
        write_freeze(fz3, "tests/test_mod.py", "test_tables", 1, None, repo_root=root)
        write_freeze(fz3, "tests/test_mod.py", "test_double", 1, None, repo_root=root)
        check("a test that reads a module-level name records the wider scope",
              all(e.get("hash_scope") == "test+module" for e in json.loads(fz3.read_text(encoding="utf-8"))),
              fz3.read_text(encoding="utf-8"))
        check("both freshly frozen tests pass", main([__file__, str(fz3), "--repo", str(root)]) == 0)
        before = mod.read_text(encoding="utf-8")
        mod.write_text(before.replace("EXPECTED = ['orders', 'customers']", "EXPECTED = ['orders']"), encoding="utf-8")
        check("loosening a module-level EXPECTED list fails the layer (investment-agent, 2026-09-21)",
              main([__file__, str(fz3), "--repo", str(root)]) == 1)
        mod.write_text(before.replace("CASES = [(1, 2), (2, 4)]", "CASES = [(1, 2)]"), encoding="utf-8")
        check("loosening a parametrize table fails the layer",
              main([__file__, str(fz3), "--repo", str(root)]) == 1)
        mod.write_text(before, encoding="utf-8")
        write_freeze(fz3, "tests/test_mod.py", "test_shape", 2, None, repo_root=root)
        check("the transitive fixture passes as frozen", main([__file__, str(fz3), "--repo", str(root)]) == 0)
        mod.write_text(before.replace("SHAPE = (3, 2)", "SHAPE = (3, 3)"), encoding="utf-8")
        check("a constant the test reaches only through a helper is folded in too (one hop, then another)",
              main([__file__, str(fz3), "--repo", str(root)]) == 1)
        mod.write_text(before + "\nUNUSED = 1\n", encoding="utf-8")
        check("a module-level name no frozen test loads is not folded in — an unrelated edit still passes",
              main([__file__, str(fz3), "--repo", str(root)]) == 0)
        mod.write_text(before, encoding="utf-8")
        check("restoring the module passes again", main([__file__, str(fz3), "--repo", str(root)]) == 0)
        mod.write_text(before.replace("EXPECTED = ['orders', 'customers']", "EXPECTED = ['orders']"), encoding="utf-8")
        wording = _captured(lambda: main([__file__, str(fz3), "--repo", str(root)]))
        check("a per-test failure is not described as a whole-file hash (found by the 2026-09-22 demo)",
              "the test changed since it was frozen" in wording and "hashes the whole file" not in wording, wording)
        mod.write_text(before, encoding="utf-8")
        old_scope = json.loads(fz3.read_text(encoding="utf-8"))
        for e in old_scope:
            e.pop("hash_scope", None)
            e["hash"] = hashlib.sha256((test_source(mod, e["test_name"]) or "").encode("utf-8")).hexdigest()
        (root / "old-scope.json").write_text(json.dumps(old_scope), encoding="utf-8")
        check("an entry recorded under the old scope still verifies the old way",
              main([__file__, str(root / "old-scope.json"), "--repo", str(root)]) == 0)
        mod.write_text(before.replace("EXPECTED = ['orders', 'customers']", "EXPECTED = ['orders']"), encoding="utf-8")
        check("an old-scope entry keeps its old blind spot rather than changing meaning under it",
              main([__file__, str(root / "old-scope.json"), "--repo", str(root)]) == 0)
        mod.write_text(before, encoding="utf-8")

        # ── task 53: an archived record is a record of its own moment ──
        archived = root / ".do-code-change" / "archive" / "2026-09-18-earlier-change" / "test-freeze.json"
        archived.parent.mkdir(parents=True, exist_ok=True)
        archived.write_text(json.dumps([{"file": "tests/test_x.py", "test_name": "test_one", "frozen_at_step": 1,
                                         "hash": "0" * 64}]), encoding="utf-8")
        out = _captured(lambda: main([__file__, str(archived), "--repo", str(root)]))
        check("an archived record is named as superseded in the header", "archived record" in out.lower(), out)
        check("the failure says only the most recent record is meaningful against HEAD",
              "most recent" in out.lower() and "expected to fail" in out.lower(), out)
        live = _captured(lambda: main([__file__, str(fz3), "--repo", str(root)]))
        check("a current record says nothing about archives", "archived record" not in live.lower(), live)

        # ── task 89: a frozen test deleted on purpose is retired, out loud (investment-agent, 2026-09-27) ──
        ret = root / "retire.json"
        gone = root / "tests" / "test_gone.py"
        gone.write_text("def test_a():\n    assert 1 == 1\n\n\ndef test_b():\n    assert 2 == 2\n", encoding="utf-8")
        keep = root / "tests" / "test_keep.py"
        keep.write_text("def test_k():\n    assert 3 == 3\n", encoding="utf-8")
        for rel_, name_ in (("tests/test_gone.py", "test_a"), ("tests/test_gone.py", "test_b"), ("tests/test_keep.py", "test_k")):
            write_freeze(ret, rel_, name_, 1, None, repo_root=root)
        rc = retire_entry(ret, "tests/test_gone.py", "test_a", "the command it tested was deleted", repo_root=root)
        check("retiring a test that still exists is refused (exit 1) — a retirement is never an exemption", rc == 1)
        check("a refused retirement leaves the entry live",
              not any(e.get("retired") for e in json.loads(ret.read_text(encoding="utf-8"))))
        check("retiring with no reason is refused (exit 2)",
              retire_entry(ret, "tests/test_gone.py", "test_a", "  ", repo_root=root) == 2)
        check("retiring an entry the freeze file does not hold is refused (exit 2)",
              retire_entry(ret, "tests/test_gone.py", "test_zzz", "x", repo_root=root) == 2)
        gone.unlink()
        check("a frozen test whose file was deleted fails the check until it is retired",
              main([__file__, str(ret), "--repo", str(root)]) == 1)
        rc_a = retire_entry(ret, "tests/test_gone.py", "test_a", "rename-schemas deleted on Mark's word", repo_root=root)
        rc_b = retire_entry(ret, "tests/test_gone.py", "test_b", "rename-schemas deleted on Mark's word", repo_root=root)
        check("retiring a test whose file is gone succeeds", rc_a == 0 and rc_b == 0, f"{rc_a} {rc_b}")
        rec = {e["test_name"]: e for e in json.loads(ret.read_text(encoding="utf-8"))}
        check("the retired entry keeps its file, test and hash, and records the reason and the date",
              rec["test_a"].get("retired", {}).get("reason") == "rename-schemas deleted on Mark's word"
              and bool(rec["test_a"].get("retired", {}).get("date")) and rec["test_a"].get("hash")
              and rec["test_a"].get("file") == "tests/test_gone.py", str(rec["test_a"]))
        out_r = _captured(lambda: main([__file__, str(ret), "--repo", str(root)]))
        check("retired entries whose tests are gone pass, and the check names them as retired",
              main([__file__, str(ret), "--repo", str(root)]) == 0 and "retired" in out_r.lower()
              and "rename-schemas deleted" in out_r, out_r)
        gone.write_text("def test_a():\n    assert 1 == 1\n", encoding="utf-8")
        check("a retired test that exists again fails the check — the retirement cannot hide a live test",
              main([__file__, str(ret), "--repo", str(root)]) == 1)
        gone.write_text("def test_other():\n    assert 1 == 1\n", encoding="utf-8")
        check("a retired test absent from a file that exists passes", main([__file__, str(ret), "--repo", str(root)]) == 0)
        keep.write_text("def test_k2():\n    assert 3 == 3\n", encoding="utf-8")
        check("a test removed from a file that stays can be retired",
              retire_entry(ret, "tests/test_keep.py", "test_k", "merged into test_k2", repo_root=root) == 0)
        out_all = _captured(lambda: main([__file__, str(ret), "--repo", str(root)]))
        check("a freeze file with every entry retired checks nothing, so it is not a pass (exit 2)",
              main([__file__, str(ret), "--repo", str(root)]) == 2 and "no live entry" in out_all.lower(), out_all)
        keep.write_text("def test_k():\n    assert 3 == 3\n", encoding="utf-8")
        write_freeze(ret, "tests/test_keep.py", "test_k", 2, "brought back", repo_root=root)
        check("freezing a retired test again replaces the retirement with a live entry",
              not any(e.get("retired") for e in json.loads(ret.read_text(encoding="utf-8")) if e["test_name"] == "test_k")
              and main([__file__, str(ret), "--repo", str(root)]) == 0)

        check("an empty freeze file is still a failure, not a pass", main([__file__, str(root / "empty.json"), "--repo", str(root)]) == 2)

    for fnd in failures:
        print(f"  x {fnd}")
    if failures:
        print(f"x check-freeze self-test failed: {len(failures)} of {len(ran)} assertion(s)")
        return 1
    if len(ran) < SELF_TEST_MINIMUM:
        print(f"x self-test ran only {len(ran)} assertions, below the floor of {SELF_TEST_MINIMUM} — a scenario was dropped")
        return 1
    print(f"PASS check-freeze self-test ({len(ran)} assertions; floor {SELF_TEST_MINIMUM})")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
