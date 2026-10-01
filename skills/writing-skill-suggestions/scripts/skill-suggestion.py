#!/usr/bin/env python3
"""skill-suggestion.py — drop one skill suggestion into the project notebook's suggestion box. The script of the
writing-skill-suggestions skill (moved there from do-code-change on 2026-09-27, task 87, so any session can use it).

When a skill, agent or script got in the way during a run (a workaround it forced, a check that missed something, a
rule that did not fit the case, the requester correcting how the work was done), the lesson would otherwise end with
the session. This script writes it down as one small file in the project notebook's box,

  <notebook>/_inbox/skill-suggestions/<skill>--<slug>.md

four labelled lines:

  Skill: <the exact name of the skill, agent or workflow; a script's own skill>
  Seen in: <the run, task or session where it happened> (<date>)
  Issue: <what happened>
  Fix: <the fix that worked or is suggested, or "none yet">

`/wrap-up` empties the box: it puts each suggestion to the user, who decides whether it goes to the skill's owner or is
dropped, and it moves the file to `archive/` with the decision (Mark's design, 2026-09-26, agent-builder task 31).
This script only ever writes to the top level of the box, never into `archive/`, and never edits a file already there.

The notebook is resolved in promote-agent Step 5.5's order, as archive-change.py resolves it:
`.claude/wiki-config.json` `llm_wiki_root`, else its `notebook` + `registry`, else `<repo>/llm-wiki/`;
`--wiki <notebook root>` overrides.

Exit codes (never let a 1, 2 or 3 read as a 0):
  0  written (the path is printed)
  1  refused: the box already holds a suggestion with the same skill and the same issue; nothing written
  2  could not run: a bad skill name, an empty or multi-line field, a bad --date, a --wiki with no wiki/ folder, or a
     write that failed
  3  no wiki found: nothing written; the suggestion is printed so the caller can keep it elsewhere

Usage:
  python scripts/skill-suggestion.py add --skill <name> --seen-in "<run, task or session>" --issue "<what happened>"
                                         [--fix "<fix>"] [--date YYYY-MM-DD] [--slug <slug>] [--wiki <root>]
                                         [--repo <path>] [--dry-run]
  python scripts/skill-suggestion.py --self-test

Stdlib-only, Python 3.8+. Paths print with forward slashes.
"""
from __future__ import annotations

import argparse
import contextlib
import datetime as dt
import io
import json
import re
import sys
import tempfile
from pathlib import Path
from typing import Dict, List, Optional, Tuple

BOX = Path("_inbox") / "skill-suggestions"
ARCHIVE = "archive"
FIELDS = ("Skill", "Seen in", "Issue", "Fix")
NO_FIX = "none yet"
SELF_TEST_MINIMUM = 34
SLUG_WORDS = 6                # the issue's first words name the file: enough to tell two suggestions apart
SLUG_MAX = 48                 # a file name stays short in a folder listing and far below any path limit
_SKILL = re.compile(r"^[a-z0-9][a-z0-9-]{0,63}$")   # the library's artifact names: lowercase-hyphen, at most 64
_DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_WORD = re.compile(r"[a-z0-9]+")


# ── resolving the notebook (promote-agent Step 5.5's order; the same lookup as archive-change.py) ─

def resolve_notebook(repo: Path, override: Optional[str]) -> Tuple[Optional[Path], str]:
    """(notebook root holding wiki/, how it was found) or (None, why not)."""
    if override:
        r = Path(override).expanduser()
        r = r if r.is_absolute() else repo / r
        if (r / "wiki").is_dir():
            return r.resolve(), f"--wiki {override}"
        return None, f"--wiki {override} has no wiki/ folder"
    cfg = repo / ".claude" / "wiki-config.json"
    if cfg.is_file():
        try:
            data = json.loads(cfg.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            data = {}
        root = data.get("llm_wiki_root") if isinstance(data, dict) else None
        if root:
            r = Path(root).expanduser()
            r = r if r.is_absolute() else repo / r
            if (r / "wiki").is_dir():
                return r.resolve(), ".claude/wiki-config.json llm_wiki_root"
        nb = data.get("notebook") if isinstance(data, dict) else None
        reg = data.get("registry") if isinstance(data, dict) else None
        if nb and reg:
            reg_path = Path(reg).expanduser()
            reg_path = reg_path if reg_path.is_absolute() else repo / reg_path
            try:
                registry = json.loads(reg_path.read_text(encoding="utf-8"))
                entry = (registry.get("notebooks") or registry).get(nb)
                root_val = entry.get("root") if isinstance(entry, dict) else entry
                if root_val:
                    r = Path(root_val).expanduser()
                    r = r if r.is_absolute() else reg_path.parent / r
                    if (r / "wiki").is_dir():
                        return r.resolve(), f".claude/wiki-config.json notebook '{nb}' via {reg_path.name}"
            except (OSError, ValueError, AttributeError):
                pass
    if (repo / "llm-wiki" / "wiki").is_dir():
        return (repo / "llm-wiki").resolve(), "llm-wiki/ in the repository"
    return None, ("no .claude/wiki-config.json that resolves to a notebook with a wiki/ folder, "
                  "and no llm-wiki/ folder in the repository")


# ── the suggestion ───────────────────────────────────────────────────────────────────────────────

def one_line(value: str) -> str:
    """The value with its spacing collapsed; a line break inside it is a caller error, checked before this."""
    return " ".join(value.split())


def slug_of(text: str) -> str:
    words = _WORD.findall(text.lower())[:SLUG_WORDS]
    return "-".join(words)[:SLUG_MAX].strip("-")


def render(values: Dict[str, str]) -> str:
    return "".join(f"{f}: {values[f]}\n" for f in FIELDS)


def parse(text: str) -> Dict[str, str]:
    out: Dict[str, str] = {}
    for line in text.splitlines():
        for f in FIELDS:
            if line.startswith(f + ":"):
                out.setdefault(f, one_line(line[len(f) + 1:]))
    return out


def same_suggestion(a: Dict[str, str], b: Dict[str, str]) -> bool:
    return a.get("Skill") == b.get("Skill") and a.get("Issue", "").lower() == b.get("Issue", "").lower()


def add(repo_arg: str, skill: str, seen_in: str, issue: str, fix: Optional[str], date: Optional[str],
        slug: Optional[str], wiki: Optional[str], dry_run: bool, today: Optional[dt.date] = None) -> int:
    today = today or dt.date.today()
    raw = {"--skill": skill, "--seen-in": seen_in, "--issue": issue, "--fix": fix or "", "--slug": slug or ""}
    broken = [k for k, v in raw.items() if "\n" in v or "\r" in v]
    if broken:
        print(f"skill-suggestion: cannot run - {', '.join(broken)} holds a line break; each field is one line",
              file=sys.stderr)
        return 2
    skill = skill.strip()
    if not _SKILL.match(skill):
        print(f"skill-suggestion: cannot run - --skill '{skill}' is not an artifact name (lowercase letters, digits "
              f"and hyphens, at most 64); name the skill, agent or workflow exactly as it is installed",
              file=sys.stderr)
        return 2
    seen_in, issue = one_line(seen_in), one_line(issue)
    fix_value = one_line(fix) if fix and fix.strip() else NO_FIX
    if not seen_in or not issue:
        print("skill-suggestion: cannot run - --seen-in and --issue must both say something", file=sys.stderr)
        return 2
    if date is not None and not _DATE.match(date):
        print(f"skill-suggestion: cannot run - --date {date} is not YYYY-MM-DD", file=sys.stderr)
        return 2
    when = date or today.isoformat()
    values = {"Skill": skill, "Seen in": f"{seen_in} ({when})" if when not in seen_in else seen_in,
              "Issue": issue, "Fix": fix_value}
    text = render(values)

    repo = Path(repo_arg).resolve()
    root, how = resolve_notebook(repo, wiki)
    if root is None:
        if wiki:
            print(f"skill-suggestion: cannot run - {how}", file=sys.stderr)
            return 2
        print(f"skill-suggestion: no wiki found ({how}); nothing was written. Keep the suggestion elsewhere "
              f"(the run's checkpoints.md, under '## Skill suggestions'):\n{text}", end="", file=sys.stderr)
        return 3

    box = root / BOX
    for existing in sorted(box.glob("*.md")) if box.is_dir() else []:
        try:
            if same_suggestion(parse(existing.read_text(encoding="utf-8")), values):
                print(f"skill-suggestion: refused - the box already holds this suggestion: {existing.as_posix()}",
                      file=sys.stderr)
                return 1
        except OSError:
            continue

    base = slug_of(slug) if slug else slug_of(issue)
    stem = f"{skill}--{base or 'suggestion'}"
    target = box / f"{stem}.md"
    n = 2
    while target.exists():
        target = box / f"{stem}-{n}.md"
        n += 1

    print(f"skill-suggestion: box {box.as_posix()} ({how})")
    if dry_run:
        print(f"skill-suggestion: dry run - would write {target.as_posix()}:\n{text}", end="")
        return 0
    try:
        box.mkdir(parents=True, exist_ok=True)
        with open(target, "x", encoding="utf-8", newline="\n") as fh:
            fh.write(text)
    except OSError as e:
        print(f"skill-suggestion: cannot run - writing {target.as_posix()} failed ({e})", file=sys.stderr)
        return 2
    print(f"written: {target.as_posix()}")
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

    def quiet(*args, **kwargs) -> Tuple[int, str]:
        buf_out, buf_err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(buf_out), contextlib.redirect_stderr(buf_err):
            code = add(*args, **kwargs)
        return code, buf_out.getvalue() + buf_err.getvalue()

    day = dt.date(2026, 9, 26)
    issue = "check-freeze.py --step takes only an integer, so the fix round's freeze entries were relabelled by hand."
    with tempfile.TemporaryDirectory(prefix="skill-suggestion-selftest-") as td:
        base = Path(td).resolve()
        repo = base / "repo"
        repo.mkdir()
        nb = base / "vault" / "nb"
        (nb / "wiki").mkdir(parents=True)
        box = nb / BOX

        def files() -> List[Path]:
            return sorted(box.glob("*.md")) if box.is_dir() else []

        # no wiki: nothing written, the suggestion printed, exit 3
        code, out = quiet(str(repo), "verifying-before-done", "committee-names-from-history", issue, "let --step take a label",
                          None, None, None, False, day)
        check("no wiki exits 3", code == 3, out)
        check("no wiki writes nothing", not box.exists())
        check("no wiki prints the suggestion so the caller can keep it", "Issue: " + issue in out and "Skill: verifying-before-done" in out, out)

        # the refusals, each before anything is written
        reg = base / "linked-notebooks.json"
        reg.write_text(json.dumps({"notebooks": {"nb": {"root": "vault/nb"}}}), encoding="utf-8")
        (repo / ".claude").mkdir()
        (repo / ".claude" / "wiki-config.json").write_text(json.dumps({"notebook": "nb", "registry": reg.as_posix()}),
                                                          encoding="utf-8")
        root, how = resolve_notebook(repo, None)
        check("the notebook resolves through wiki-config + registry", root == nb.resolve(), f"{root} ({how})")
        check("a skill name with a capital or a space exits 2",
              quiet(str(repo), "Verifying Before Done", "x", issue, None, None, None, None, False, day)[0] == 2)
        check("a skill name with a path exits 2",
              quiet(str(repo), "../evil", "x", issue, None, None, None, None, False, day)[0] == 2)
        check("an empty issue exits 2", quiet(str(repo), "reviewing-code", "x", "   ", None, None, None, None, False, day)[0] == 2)
        check("an empty seen-in exits 2", quiet(str(repo), "reviewing-code", "", issue, None, None, None, None, False, day)[0] == 2)
        check("a line break inside a field exits 2 (each field is one line)",
              quiet(str(repo), "reviewing-code", "x", "one\nIssue: two", None, None, None, None, False, day)[0] == 2)
        check("a bad --date exits 2", quiet(str(repo), "reviewing-code", "x", issue, None, "26-09-2026", None, None, False, day)[0] == 2)
        check("a --wiki with no wiki/ folder exits 2 and never falls back to wiki-config",
              quiet(str(repo), "reviewing-code", "x", issue, None, None, None, str(base / "vault"), False, day)[0] == 2)
        check("no refusal wrote anything", not box.exists())

        code, out = quiet(str(repo), "verifying-before-done", "committee-names-from-history", issue, "let --step take a label",
                          None, None, None, True, day)
        check("--dry-run exits 0 and writes nothing", code == 0 and not box.exists(), out)
        check("--dry-run shows the file it would write", "verifying-before-done--check-freeze-py-step-takes-only.md" in out, out)

        # a written suggestion: its name, its four lines, nothing else
        code, out = quiet(str(repo), "verifying-before-done", "committee-names-from-history", issue, "let --step take a label",
                          None, None, None, False, day)
        written = files()
        check("a suggestion is written (exit 0)", code == 0 and len(written) == 1, out)
        check("the file is named <skill>--<the issue's first words>.md",
              bool(written) and written[0].name == "verifying-before-done--check-freeze-py-step-takes-only.md",
              str([p.name for p in written]))
        text = written[0].read_text(encoding="utf-8") if written else ""
        check("the file is exactly four labelled lines",
              text.splitlines() == ["Skill: verifying-before-done",
                                    "Seen in: committee-names-from-history (2026-09-26)",
                                    "Issue: " + issue,
                                    "Fix: let --step take a label"], repr(text))
        check("the file is written with LF line endings", "\r" not in (written[0].read_bytes().decode("utf-8") if written else ""))
        check("the report prints the path written", bool(written) and written[0].as_posix() in out, out)
        check("the file lands in the box's top level, never in archive/", not (box / ARCHIVE).exists())

        # the same suggestion twice is refused; a different one about the same skill gets its own file
        code, out = quiet(str(repo), "verifying-before-done", "another-run", issue.upper(), None, None, None, None, False, day)
        check("the same skill and issue (any case) is refused (exit 1)", code == 1 and len(files()) == 1, out)
        code, _ = quiet(str(repo), "verifying-before-done", "another-run", "check-freeze.py --step takes only an integer, again",
                        None, None, None, None, False, day)
        check("a second suggestion whose name would clash gets -2", code == 0 and (box / "verifying-before-done--check-freeze-py-step-takes-only-2.md").is_file(),
              str([p.name for p in files()]))
        check("the earlier file is never touched", written and written[0].read_text(encoding="utf-8") == text)

        # the defaults and the options
        code, _ = quiet(str(repo), "reviewing-code", "task 12", "A lens wrote a file.", None, "2026-01-02", "lens-writes", None, False, day)
        f = box / "reviewing-code--lens-writes.md"
        check("--slug names the file", code == 0 and f.is_file(), str([p.name for p in files()]))
        body = f.read_text(encoding="utf-8") if f.is_file() else ""
        check("no --fix writes 'Fix: none yet'", "Fix: none yet\n" in body, body)
        check("--date dates the Seen in line", "Seen in: task 12 (2026-01-02)\n" in body, body)
        code, _ = quiet(str(repo), "reviewing-code", "session 2026-09-26", "Spacing   is\tcollapsed.", None, None, None, None, False, day)
        f2 = box / "reviewing-code--spacing-is-collapsed.md"
        body2 = f2.read_text(encoding="utf-8") if f2.is_file() else ""
        check("a Seen in that already holds the date is not dated twice", "Seen in: session 2026-09-26\n" in body2, body2)
        check("spacing inside a field is collapsed", "Issue: Spacing is collapsed.\n" in body2, body2)
        check("parse reads back what render wrote",
              parse(text) == {"Skill": "verifying-before-done", "Seen in": "committee-names-from-history (2026-09-26)",
                              "Issue": issue, "Fix": "let --step take a label"})
        check("an issue with no letters or digits still gets a file name",
              quiet(str(repo), "reviewing-code", "x", "?!", None, None, None, None, False, day)[0] == 0
              and (box / "reviewing-code--suggestion.md").is_file(), str([p.name for p in files()]))

        # an archived suggestion is not the box: the same issue can be suggested again after it was decided
        (box / ARCHIVE).mkdir()
        (box / ARCHIVE / "reviewing-code--lens-writes.md").write_text(body + "Decision (2026-01-03, Mark): dropped\n", encoding="utf-8")
        (box / "reviewing-code--lens-writes.md").unlink()
        code, _ = quiet(str(repo), "reviewing-code", "task 13", "A lens wrote a file.", None, None, "lens-writes", None, False, day)
        check("a suggestion already decided (in archive/) does not block a new one", code == 0 and (box / "reviewing-code--lens-writes.md").is_file())

        # the other routes: --wiki, llm_wiki_root, an in-repo llm-wiki/
        other = base / "other"
        (other / "wiki").mkdir(parents=True)
        code, _ = quiet(str(repo), "tdd-implementation", "x", "Something else.", None, None, None, str(other), False, day)
        check("--wiki overrides the wiki-config lookup", code == 0 and (other / BOX / "tdd-implementation--something-else.md").is_file())
        (repo / ".claude" / "wiki-config.json").write_text(json.dumps({"llm_wiki_root": "notes-wiki"}), encoding="utf-8")
        (repo / "notes-wiki" / "wiki").mkdir(parents=True)
        check("llm_wiki_root resolves first", resolve_notebook(repo, None)[0] == (repo / "notes-wiki").resolve())
        (repo / ".claude" / "wiki-config.json").unlink()
        (repo / "llm-wiki" / "wiki").mkdir(parents=True)
        check("an llm-wiki/ folder resolves when there is no wiki-config", resolve_notebook(repo, None)[0] == (repo / "llm-wiki").resolve())

    total = passed + len(failed)
    for f in failed:
        print(f"FAIL {f}")
    if failed:
        print(f"FAIL skill-suggestion self-test ({passed}/{total})")
        return 1
    if passed < SELF_TEST_MINIMUM:
        print(f"FAIL skill-suggestion self-test ran only {passed} assertions (floor {SELF_TEST_MINIMUM}) - a dropped block")
        return 1
    print(f"OK skill-suggestion self-test passed ({passed} assertions; floor {SELF_TEST_MINIMUM})")
    return 0


def main(argv: Optional[List[str]] = None) -> int:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser(description="Drop one skill suggestion into the project notebook's suggestion box.")
    ap.add_argument("--self-test", action="store_true", help="prove every rule still fires on a known-bad fixture")
    sub = ap.add_subparsers(dest="cmd")
    a = sub.add_parser("add", help="write one suggestion")
    a.add_argument("--skill", required=True, help="the exact name of the skill, agent or workflow (a script: its skill)")
    a.add_argument("--seen-in", required=True, help="the run, task or session where it happened")
    a.add_argument("--issue", required=True, help="what happened, one line")
    a.add_argument("--fix", default=None, help=f"the fix that worked or is suggested (default: '{NO_FIX}')")
    a.add_argument("--date", default=None, help="YYYY-MM-DD for the Seen in line (default: today)")
    a.add_argument("--slug", default=None, help="the file name after '<skill>--' (default: the issue's first words)")
    a.add_argument("--wiki", default=None, help="the notebook root (the folder holding wiki/); overrides the wiki-config lookup")
    a.add_argument("--repo", default=".", help="the project (default: current directory)")
    a.add_argument("--dry-run", action="store_true", help="print the file it would write; write nothing")
    args = ap.parse_args(argv)
    if args.self_test:
        return self_test()
    if args.cmd != "add":
        ap.print_usage()
        return 2
    return add(args.repo, args.skill, args.seen_in, args.issue, args.fix, args.date, args.slug, args.wiki, args.dry_run)


if __name__ == "__main__":
    sys.exit(main())
