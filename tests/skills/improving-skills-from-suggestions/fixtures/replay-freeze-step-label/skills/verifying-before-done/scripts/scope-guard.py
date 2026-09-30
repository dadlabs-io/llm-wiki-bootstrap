#!/usr/bin/env python3
"""scope-guard.py — the in-scope layer of verifying-before-done: every file touched since implement
started is inside the change's declared scope, as a script rather than a habit.

A declared scope with no check after the writing step is prose (workflow contract §3, governance).
This guard closes the gap the do-code-change workflow carried from 2026-09-07: a file touched and
reverted mid-run, or written outside the change, was invisible until the finish pre-flight.

Two commands, in pipeline order:

  baseline   Run at the START of implement, before the first red. Captures where the tree stood:
               * `git stash create` — a commit object of HEAD plus every uncommitted change, without
                 touching the stash list or the working tree (HEAD when the tree is clean);
               * a snapshot of every untracked, not-ignored file with its mtime (a stash never holds
                 untracked files, so without this a pre-existing untracked file looks new forever);
               * HEAD, so a linear advance of HEAD during implement is still diffed.
             Writes `scope-baseline.json` into the artifact directory.
             (Anthropic's security-guidance plugin captures exactly this at every prompt, 2026.)

  check      Run at verify (the Pre-finish gate reads its exit code). The TOUCHED set is the name-only
             diff against the baseline object, plus files committed since the captured HEAD when HEAD
             advanced linearly, plus every untracked file that was not in the snapshot or whose mtime
             changed; minus `.do-code-change/` (every run's notes, committed at each checkpoint, and
             their archive). The DECLARED set is the `## Scope` section
             of plan.md (one path or glob per bullet; `**` matches across folders) plus any `--allow`
             globs. Every touched file must match the declared set.

Exit codes (never let a 2 read as a 0):
  0  every touched file is declared
  1  at least one touched file is outside the declared scope — the run routes back to implement, and
     the stray file is a finding to explain, not just delete
  2  the guard could not check: not a git repository, no commits, no baseline, an unreadable plan, no
     boundary declared (a plan whose scope is only `**` or `*` has declared nothing), or nothing touched
     since the baseline (a check over nothing is not a pass; Trail of Bits, 2026)

Usage:
  python scripts/scope-guard.py baseline --artifact-dir .do-code-change/<slug> [--repo <path>]
  python scripts/scope-guard.py check    --artifact-dir .do-code-change/<slug> [--plan <plan.md>]
                                         [--allow <glob> ...] [--max-files N] [--repo <path>]
  python scripts/scope-guard.py --self-test

Stdlib-only, Python 3.8+. Paths are printed repo-relative with forward slashes.
"""
from __future__ import annotations

import argparse
import fnmatch
import json
import os
import re
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

BASELINE_NAME = "scope-baseline.json"
UNTRACKED_CAP = 2000          # the plugin's cap; past it the snapshot is partial and says so
DEFAULT_MAX_FILES = 200       # a touched set past this is reported as over the cap, not silently truncated
MATCH_ALL = {"**", "*", "**/*", "./**", "."}
SELF_TEST_MINIMUM = 29
_SCOPE_HEADING = re.compile(r"^#{2,3}\s*scope\b.*$", re.IGNORECASE | re.MULTILINE)


# ── git helpers: bytes in, lenient UTF-8 out (a non-ASCII path must never crash the guard) ───────────

def git(args: List[str], cwd: Path, timeout: int = 30) -> Optional[str]:
    try:
        out = subprocess.run(["git", "-c", "core.quotePath=false", *args], cwd=str(cwd),
                             capture_output=True, timeout=timeout)
    except (OSError, subprocess.SubprocessError):
        return None
    if out.returncode != 0:
        return None
    return (out.stdout or b"").decode("utf-8", errors="replace")


def toplevel(repo: Path) -> Optional[Path]:
    out = git(["rev-parse", "--show-toplevel"], repo, 5)
    return Path(out.strip()) if out and out.strip() else None


def head_sha(repo: Path) -> Optional[str]:
    out = git(["rev-parse", "HEAD"], repo, 5)
    return out.strip() if out and out.strip() else None


def list_untracked(repo: Path) -> Tuple[Dict[str, int], bool]:
    """Repo-relative untracked, not-ignored path -> mtime_ns. Second value: True when capped."""
    out = git(["ls-files", "--others", "--exclude-standard", "-z"], repo, 30)
    if out is None:
        return {}, False
    snap: Dict[str, int] = {}
    for p in out.split("\0"):
        if not p:
            continue
        try:
            snap[p] = os.stat(repo / p).st_mtime_ns
        except OSError:
            snap[p] = 0
        if len(snap) >= UNTRACKED_CAP:
            return snap, True
    return snap, False


def name_only(repo: Path, base: str, head: str = "") -> Optional[Set[str]]:
    args = ["diff", "--name-only", "-z", base] + ([head] if head else [])
    out = git(args, repo, 30)
    if out is None:
        return None
    return {p for p in out.split("\0") if p}


def is_ancestor(repo: Path, older: str, newer: str) -> bool:
    try:
        r = subprocess.run(["git", "merge-base", "--is-ancestor", older, newer], cwd=str(repo),
                           capture_output=True, timeout=5)
        return r.returncode == 0
    except (OSError, subprocess.SubprocessError):
        return False


def rel_posix(path: Path, repo: Path) -> Optional[str]:
    try:
        return path.resolve().relative_to(repo.resolve()).as_posix()
    except ValueError:
        return None


# ── baseline ─────────────────────────────────────────────────────────────────────────────────────

def capture_baseline(repo: Path, artifact_dir: Path) -> Tuple[int, str]:
    top = toplevel(repo)
    if top is None:
        return 2, "scope-guard: cannot capture - not a git repository"
    head = head_sha(top)
    if head is None:
        return 2, "scope-guard: cannot capture - the repository has no commits"
    stash = git(["stash", "create"], top, 15)
    baseline = (stash or "").strip() or head
    untracked, capped = list_untracked(top)
    artifact_rel = rel_posix(artifact_dir, top)
    record = {
        "schema": 1,
        "captured_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "repo_root": top.resolve().as_posix(),
        "baseline_sha": baseline,
        "head_at_capture": head,
        "tree_was_clean": not bool((stash or "").strip()),
        "untracked_at_baseline": untracked,
        "untracked_capped": capped,
        "artifact_dir": artifact_rel,
    }
    artifact_dir.mkdir(parents=True, exist_ok=True)
    (artifact_dir / BASELINE_NAME).write_text(json.dumps(record, indent=2), encoding="utf-8")
    return 0, (f"scope-guard: baseline {baseline[:12]} captured (HEAD {head[:12]}, "
               f"{'clean tree' if record['tree_was_clean'] else 'uncommitted changes included'}, "
               f"{len(untracked)} untracked file(s) snapshotted{' — CAPPED' if capped else ''}) "
               f"-> {(artifact_dir / BASELINE_NAME).as_posix()}")


# ── declared scope ───────────────────────────────────────────────────────────────────────────────

def bullet_glob(item: str) -> str:
    """One Scope bullet's path or glob: its first backticked span when it has one, else its first token, so a
    trailing note never joins the glob, whether or not the path holds a `/` (investment-agent, 2026-09-22:
    "`CONSTRAINTS.md` — added for one edit only" became one glob of the whole line). A path containing a
    space must be backticked."""
    m = re.search(r"`([^`]+)`", item)
    if m:
        return m.group(1).strip()
    tokens = item.split()
    return tokens[0] if tokens else ""


def plan_scope(plan: Path) -> Optional[List[str]]:
    """The bullets under plan.md's `## Scope` heading, or None when the file or section is absent."""
    if not plan.is_file():
        return None
    text = plan.read_text(encoding="utf-8", errors="replace")
    m = _SCOPE_HEADING.search(text)
    if not m:
        return None
    rest = text[m.end():]
    globs: List[str] = []
    for line in rest.splitlines():
        if re.match(r"^#{1,6}\s", line):
            break
        m = re.match(r"^\s*[-*]\s+(.*)$", line)   # the marker and its space only: a glob's own `**` stays
        if m:
            item = bullet_glob(m.group(1).strip())
            if item and not item.lower().startswith(("none", "n/a")):
                globs.append(item)
    return globs


def _glob_match(path: str, pattern: str) -> bool:
    """gitignore-flavoured matching on posix paths: `**` spans folders, `*` does not, a bare folder
    name (or `folder/`) matches everything under it."""
    pattern = pattern.strip().replace("\\", "/")
    if pattern.endswith("/"):
        pattern = pattern + "**"
    if "*" not in pattern and "?" not in pattern and "[" not in pattern:
        return path == pattern or path.startswith(pattern.rstrip("/") + "/")
    rx = ""
    i = 0
    while i < len(pattern):
        c = pattern[i]
        if pattern.startswith("**", i):
            rx += ".*"
            i += 2
            if i < len(pattern) and pattern[i] == "/":
                i += 1
            continue
        if c == "*":
            rx += "[^/]*"
        elif c == "?":
            rx += "[^/]"
        else:
            rx += re.escape(c)
        i += 1
    return re.fullmatch(rx, path) is not None


def declared(path: str, globs: List[str]) -> bool:
    return any(_glob_match(path, g) for g in globs)


# ── check ────────────────────────────────────────────────────────────────────────────────────────

def compute_touched(repo: Path, record: Dict) -> Tuple[Optional[str], Set[str], Dict]:
    """(error, touched_set, notes). Mirrors the plugin's review set: dirty-versus-baseline ∪ new or
    modified untracked ∪ committed-since-capture when HEAD advanced linearly."""
    notes: Dict = {}
    base = record.get("baseline_sha")
    if not base:
        return "baseline record has no baseline_sha", set(), notes
    changed = name_only(repo, base)
    if changed is None:
        return f"git cannot diff against baseline {base[:12]} (pruned or not a commit of this repository)", set(), notes
    head_then = record.get("head_at_capture")
    head_now = head_sha(repo)
    if head_then and head_now and head_then != head_now:
        if is_ancestor(repo, head_then, head_now):
            committed = name_only(repo, head_then, head_now) or set()
            changed |= committed
            notes["committed_since_capture"] = sorted(committed)
        else:
            notes["head_moved_sideways"] = f"{head_then[:12]} -> {head_now[:12]}"
    snap = record.get("untracked_at_baseline") or {}
    untracked_now, _ = list_untracked(repo)
    new_untracked = set()
    for p, mtime in untracked_now.items():
        if p in snap and snap[p] == mtime:
            continue          # pre-existing and untouched
        new_untracked.add(p)
    changed |= new_untracked
    notes["new_or_modified_untracked"] = sorted(new_untracked)
    return None, changed, notes


def run_check(repo: Path, artifact_dir: Path, plan: Optional[Path], allow: List[str], max_files: int) -> int:
    top = toplevel(repo)
    if top is None:
        print("scope-guard: cannot check - not a git repository", file=sys.stderr)
        return 2
    baseline_file = artifact_dir / BASELINE_NAME
    if not baseline_file.is_file():
        print(f"scope-guard: cannot check - no {BASELINE_NAME} in {artifact_dir.as_posix()} "
              f"(run `scope-guard.py baseline` at the start of implement)", file=sys.stderr)
        return 2
    try:
        record = json.loads(baseline_file.read_text(encoding="utf-8"))
    except Exception as e:  # noqa: BLE001
        print(f"scope-guard: cannot check - baseline unreadable ({e})", file=sys.stderr)
        return 2
    plan_path = plan if plan is not None else (artifact_dir / "plan.md")
    from_plan = plan_scope(plan_path)
    globs = list(allow) + (from_plan or [])
    if not globs:
        print(f"scope-guard: cannot check - no scope declared ({plan_path.as_posix()} has no `## Scope` "
              f"bullets and no --allow was given); a check against nothing is not a pass", file=sys.stderr)
        return 2
    if all(g.strip() in MATCH_ALL for g in globs):
        print("scope-guard: cannot check - the declared scope is only a match-all (`**`); that declares no boundary",
              file=sys.stderr)
        return 2
    err, touched, notes = compute_touched(top, record)
    if err:
        print(f"scope-guard: cannot check - {err}", file=sys.stderr)
        return 2
    artifact_rel = record.get("artifact_dir") or rel_posix(artifact_dir, top)
    exempt = [artifact_rel] if artifact_rel else []
    exempt.append(".do-code-change")
    touched = {p for p in touched if not any(p == e or p.startswith(e.rstrip("/") + "/") for e in exempt if e)}
    if not touched:
        print("scope-guard: cannot check - nothing was touched since the baseline (a check over nothing is not a pass)",
              file=sys.stderr)
        return 2
    if len(touched) > max_files:
        print(f"scope-guard: {len(touched)} files touched since the baseline, over the cap of {max_files} — "
              f"the change is larger than a scoped run; the first {max_files} are listed", file=sys.stderr)
    listed = sorted(touched)[:max_files]
    outside = [p for p in listed if not declared(p, globs)]
    inside = [p for p in listed if declared(p, globs)]
    if notes.get("head_moved_sideways"):
        print(f"scope-guard: note - HEAD moved sideways ({notes['head_moved_sideways']}); committed files "
              f"could not be attributed to this run", file=sys.stderr)
    if record.get("untracked_capped"):
        print("scope-guard: note - the untracked snapshot was capped at baseline; a pre-existing untracked "
              "file past the cap reads as new", file=sys.stderr)
    if outside:
        print(f"scope-guard: FAIL - {len(outside)} of {len(listed)} touched file(s) outside the declared scope "
              f"({', '.join(globs)}):", file=sys.stderr)
        for p in outside:
            print(f"  [out-of-scope] {p}", file=sys.stderr)
        print("Each is a file the change touched that the plan never declared: route back to implement, "
              "and the file itself is a finding to explain (revert it, or extend the plan's scope out loud).",
              file=sys.stderr)
        return 1
    print(f"scope-guard: PASS - {len(inside)} touched file(s), all inside the declared scope ({', '.join(globs)})")
    for p in inside:
        print(f"  [in-scope] {p}")
    return 0


# ── self-test: a check is unproven until it has caught something ─────────────────────────────────

def self_test() -> int:
    passed = 0
    failed: List[str] = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        nonlocal passed
        if ok:
            passed += 1
        else:
            failed.append(f"{name}{(' - ' + detail) if detail else ''}")

    env = {**os.environ, "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t", "GIT_COMMITTER_NAME": "t",
           "GIT_COMMITTER_EMAIL": "t@t"}
    with tempfile.TemporaryDirectory(prefix="scope-guard-selftest-") as td:
        repo = Path(td).resolve()

        def g(*args: str) -> None:
            subprocess.run(["git", *args], cwd=str(repo), check=True, capture_output=True, env=env)

        def w(rel: str, text: str) -> None:
            p = repo / rel
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(text, encoding="utf-8")

        art = repo / ".do-code-change" / "slug"

        # not a repository yet
        code, _ = capture_baseline(repo, art)
        check("baseline exits 2 outside a repository", code == 2)

        g("init", "-q", "-b", "main")
        check("baseline exits 2 with no commits", capture_baseline(repo, art)[0] == 2)
        w("src/app.py", "def run():\n    return 1\n")
        w("tests/test_app.py", "def test_run():\n    assert True\n")
        w("notes/old.txt", "pre-existing untracked\n")
        g("add", "src", "tests")
        g("commit", "-q", "-m", "base")
        w("src/app.py", "def run():\n    return 2\n")          # an uncommitted change at baseline time
        code, msg = capture_baseline(repo, art)
        check("baseline captured", code == 0, msg)
        record = json.loads((art / BASELINE_NAME).read_text(encoding="utf-8"))
        check("baseline is a stash object, not HEAD, when the tree is dirty",
              record["baseline_sha"] != record["head_at_capture"] and not record["tree_was_clean"])
        check("pre-existing untracked file snapshotted", "notes/old.txt" in record["untracked_at_baseline"])
        check("artifact dir recorded repo-relative", record["artifact_dir"] == ".do-code-change/slug")

        # no scope declared -> 2 ; match-all -> 2 ; nothing touched -> 2
        check("check exits 2 with no scope declared", run_check(repo, art, None, [], DEFAULT_MAX_FILES) == 2)
        check("check exits 2 when the scope is only a match-all", run_check(repo, art, None, ["**"], DEFAULT_MAX_FILES) == 2)
        w(".do-code-change/slug/plan.md", "## Steps\n1. x\n\n## Scope\n- src/**\n- tests/\n")
        check("check exits 2 when nothing was touched since the baseline",
              run_check(repo, art, None, [], DEFAULT_MAX_FILES) == 2)

        # declared changes only -> 0 (the pre-baseline dirty edit must NOT count: it is in the stash object)
        w("src/app.py", "def run():\n    return 3\n")
        w("tests/test_more.py", "def test_more():\n    assert True\n")      # new untracked, declared
        check("declared edits pass", run_check(repo, art, None, [], DEFAULT_MAX_FILES) == 0)
        check("plan scope parsed (two bullets)", plan_scope(art / "plan.md") == ["src/**", "tests/"])

        # a stray file -> 1 ; the artifact directory itself is exempt
        w("notes/scratch.md", "stray\n")
        w(".do-code-change/slug/doubt-log.md", "no non-trivial decision\n")
        check("stray untracked file fails", run_check(repo, art, None, [], DEFAULT_MAX_FILES) == 1)
        check("--allow extends the declared scope", run_check(repo, art, None, ["notes/**"], DEFAULT_MAX_FILES) == 0)

        # a pre-existing untracked file edited in place is touched; untouched it is not
        os.remove(repo / "notes" / "scratch.md")
        check("pre-existing untracked file untouched is ignored", run_check(repo, art, None, [], DEFAULT_MAX_FILES) == 0)
        time.sleep(0.02)
        w("notes/old.txt", "edited during implement\n")
        os.utime(repo / "notes" / "old.txt", ns=(time.time_ns(), time.time_ns()))
        check("pre-existing untracked file edited in place is touched",
              run_check(repo, art, None, [], DEFAULT_MAX_FILES) == 1)
        w("notes/old.txt", "pre-existing untracked\n")
        os.utime(repo / "notes" / "old.txt", ns=(record["untracked_at_baseline"]["notes/old.txt"],) * 2)

        # a tracked file edited and reverted is NOT touched (name-only against the stash object)
        check("reverted edit leaves nothing touched outside scope", run_check(repo, art, None, [], DEFAULT_MAX_FILES) == 0)

        # a new file that was staged but not committed is touched (the eval runner's post_files shape)
        w("etc/staged.cfg", "staged only\n")
        g("add", "etc")
        check("staged new file outside the scope fails", run_check(repo, art, None, [], DEFAULT_MAX_FILES) == 1)
        g("rm", "-q", "--cached", "etc/staged.cfg")
        os.remove(repo / "etc" / "staged.cfg")

        # a commit during implement (HEAD advanced linearly) is still diffed
        w("docs/README.md", "committed during implement\n")
        g("add", "docs")
        g("commit", "-q", "-m", "mid-implement commit")
        check("file committed after the baseline is touched", run_check(repo, art, None, [], DEFAULT_MAX_FILES) == 1)
        check("committed file passes when declared", run_check(repo, art, None, ["docs/**"], DEFAULT_MAX_FILES) == 0)

        # the run's notes, committed at a checkpoint during implement, are never out of scope (2026-09-14)
        w(".do-code-change/slug/checkpoints.md", "## Plan confirmation\nok\n")
        w(".do-code-change/archive/2026-01-01-old/plan.md", "an earlier run's archived notes\n")
        g("add", ".do-code-change/slug/checkpoints.md", ".do-code-change/archive")
        g("commit", "-q", "-m", "do-code-change(slug): notes")
        check("notes committed during implement are never out of scope",
              run_check(repo, art, None, ["docs/**"], DEFAULT_MAX_FILES) == 0)

        # a bullet's trailing note is never part of its glob (investment-agent, 2026-09-22): the first token was
        # kept only when it held a `/`, so a root-level file with a note became one glob of the whole line
        def parsed(bullets: str) -> Optional[List[str]]:
            w(".do-code-change/parse/plan.md", "## Scope\n" + bullets)
            return plan_scope(repo / ".do-code-change" / "parse" / "plan.md")
        check("a bare root-level file with an em-dash note parses to the file",
              parsed("- CONSTRAINTS.md — added for one edit only: widening Exceptions\n") == ["CONSTRAINTS.md"],
              str(parsed("- CONSTRAINTS.md — added for one edit only: widening Exceptions\n")))
        check("a backticked root-level file with a note parses to the backticked span (the reported bullet)",
              parsed("- `CONSTRAINTS.md` — added 2026-09-22 (review round 2, Q1), for one edit only\n") == ["CONSTRAINTS.md"],
              str(parsed("- `CONSTRAINTS.md` — added 2026-09-22 (review round 2, Q1), for one edit only\n")))
        check("a backticked glob with a note parses to the glob",
              parsed("- `src/tracker/**` — the parser and its store\n") == ["src/tracker/**"])
        check("a note that itself holds a slash never becomes the glob",
              parsed("- CONSTRAINTS.md — see review/round-2 for why\n") == ["CONSTRAINTS.md"],
              str(parsed("- CONSTRAINTS.md — see review/round-2 for why\n")))
        check("a bullet that is only a glob keeps it whole, leading `**` included",
              parsed("- **/*.py\n- tests/\n") == ["**/*.py", "tests/"], str(parsed("- **/*.py\n- tests/\n")))
        check("a star bullet marker is stripped, the glob's own stars are not",
              parsed("* `docs/**`\n") == ["docs/**"], str(parsed("* `docs/**`\n")))

        # glob semantics
        check("`*` does not cross folders", not _glob_match("src/a/b.py", "src/*.py") and _glob_match("src/b.py", "src/*.py"))
        check("bare folder matches everything under it", _glob_match("tests/unit/test_x.py", "tests") and not _glob_match("tests_old/x", "tests"))
        check("baseline file unreadable exits 2", (lambda: ((art / BASELINE_NAME).write_text("{not json", encoding="utf-8"),
                                                              run_check(repo, art, None, [], DEFAULT_MAX_FILES))[1])() == 2)

    total = passed + len(failed)
    for f in failed:
        print(f"FAIL {f}")
    if failed:
        print(f"FAIL scope-guard self-test ({passed}/{total})")
        return 1
    if passed < SELF_TEST_MINIMUM:
        print(f"FAIL scope-guard self-test ran only {passed} assertions (floor {SELF_TEST_MINIMUM}) - a dropped block")
        return 1
    print(f"OK scope-guard self-test passed ({passed} assertions; floor {SELF_TEST_MINIMUM})")
    return 0


def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser(description="Baseline the tree at implement start; at verify, fail on any file touched outside the declared scope.")
    ap.add_argument("command", nargs="?", choices=["baseline", "check"])
    ap.add_argument("--artifact-dir", default=None, help="the run's artifact directory (.do-code-change/<slug>)")
    ap.add_argument("--plan", default=None, help="plan.md carrying the `## Scope` bullets (default: <artifact-dir>/plan.md)")
    ap.add_argument("--allow", action="append", default=[], metavar="GLOB", help="extra declared path or glob (repeatable)")
    ap.add_argument("--max-files", type=int, default=DEFAULT_MAX_FILES, help=f"report past this many touched files (default {DEFAULT_MAX_FILES})")
    ap.add_argument("--repo", default=".", help="repository to check (default: current directory)")
    ap.add_argument("--self-test", action="store_true", help="prove every rule still fires on a known-bad fixture")
    args = ap.parse_args(argv)
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")
    if args.self_test:
        return self_test()
    if not args.command or not args.artifact_dir:
        ap.print_usage()
        return 2
    repo = Path(args.repo).resolve()
    artifact_dir = Path(args.artifact_dir)
    artifact_dir = artifact_dir if artifact_dir.is_absolute() else (repo / artifact_dir)
    if args.command == "baseline":
        code, msg = capture_baseline(repo, artifact_dir)
        print(msg, file=sys.stderr if code else sys.stdout)
        return code
    plan = Path(args.plan) if args.plan else None
    if plan is not None and not plan.is_absolute():
        plan = repo / plan
    return run_check(repo, artifact_dir, plan, args.allow, args.max_files)


if __name__ == "__main__":
    sys.exit(main())
