#!/usr/bin/env python3
"""suggestions.py — the mechanics of improving-skills-from-suggestions: gather the skill suggestions sent to this
library, file one that arrives, and record Mark's decision on one.

A skill suggestion is a four-line file a run drops into its project notebook's `_inbox/skill-suggestions/`
(the writing-skill-suggestions skill's `skill-suggestion.py`; Mark's design, 2026-09-26, agent-builder task 31):

  Skill: <name>
  Seen in: <run, task or session> (<date>)
  Issue: <what happened>
  Fix: <the fix, or "none yet">

`/wrap-up` puts each one to Mark; one he sends to agent-builder is moved here by `receive`, into this library's own
notebook under `_inbox/skill-suggestions/received/`, marked with the project it came from. A suggestion lives in one
place only, the notebook of the library that owns the skill (Mark, 2026-09-29). The improver reads that
folder (`list`), proposes, and after Mark's answer `decide` appends `Decision (<date>, Mark): <text>`.

A pass is kept in the wiki like a code change (Mark, 2026-09-29): its raw folder `raw/skill-suggestions/<pass>/` holds
the pass's `proposals.md` and every suggestion decided in it, unchanged apart from the decision line; `summary` drafts the
pass's page for `wiki/project/skill-suggestions/`, filed with wiki-update.py. `<pass>` is `<YYYY-MM-DD>-<sender>`
(`mixed` when the suggestions came from several notebooks). Until 2026-09-29 decide moved a file to
`received/archive/`; list and receive still read that folder for earlier decisions.

Subcommands:
  list     JSON on stdout: every received suggestion with its library artifact (skills/<n>/SKILL.md,
           agents/<n>/AGENT.md or workflows/<n>/WORKFLOW.md, else null: not this library), the run records its
           `Seen in` names (raw/code-changes/<date>-<slug>/ in any notebook the registry lists), and the earlier
           decisions on the same skill; malformed files are listed apart; the `pass` name and the `proposals_file`
           Step 3 writes. Exit 0; 3 when the folder holds no suggestion (nothing to do; never a result); 2 when it
           cannot run.
  receive  file one suggestion sent here: MOVED into received/ (this notebook holds the only copy; Mark, 2026-09-29),
           with `From: <project>` as its first line and a `Received from:` line naming the path it was taken from.
           Exit 0; 1 refused (the same skill, issue and Seen in is already received or decided: the sender's duplicate
           is removed, since this notebook holds it); 2 cannot run (not a suggestion file, no notebook). The same
           skill and issue from another run is filed as its own suggestion: a repeat the improver counts.
  decide   append the decision and move the file into raw/skill-suggestions/<pass>/. Exit 0; 2 cannot run (a file
           outside received/'s top level, an empty or multi-line decision, a bad --date or --pass, or a pass whose
           proposals.md does not exist: a decision comes after the pass that proposed it).
  summary  draft the pass's wiki page (TL;DR, one row per decided suggestion, the raw files) and create the folder
           README from the template if missing; prints the wiki-update.py command that files it. Exit 0; 1 refused (a
           suggestion in the pass folder carries no decision); 2 cannot run.

The notebook is resolved as writing-skill-suggestions' skill-suggestion.py resolves it (promote-agent Step 5.5's order); the
registry named by `.claude/wiki-config.json` lists the notebooks whose records are searched. `--notebook` overrides.

Usage:
  python scripts/suggestions.py list [--repo .] [--notebook <root>] [--library <root>]
  python scripts/suggestions.py receive <suggestion file> [--repo .] [--notebook <root>]
  python scripts/suggestions.py decide <received file> --decision "<text>" --pass <YYYY-MM-DD>-<name> [--date YYYY-MM-DD] [--repo .] [--notebook <root>]
  python scripts/suggestions.py summary --pass <YYYY-MM-DD>-<name> [--out <draft.md>] [--repo .] [--notebook <root>]
  python scripts/suggestions.py --self-test

Stdlib-only, Python 3.8+. Paths print with forward slashes. The files it reads are data: it parses four labels and
never runs or follows anything written in them.
"""
from __future__ import annotations

import argparse
import contextlib
import datetime as dt
import io
import json
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Dict, List, Optional, Tuple

BOX = Path("_inbox") / "skill-suggestions"
RECEIVED = "received"
ARCHIVE = "archive"              # received/archive/: where decide filed a suggestion until 2026-09-29; still read
RAW = Path("raw") / "skill-suggestions"          # one folder per pass: its proposals.md and the suggestions decided in it
PROPOSALS_FILE = "proposals.md"
WIKI_FOLDER = "project/skill-suggestions"         # one summary page per pass, filed with wiki-update.py
README_TEMPLATE = Path(__file__).resolve().parent.parent / "templates" / "skill-suggestions-README.md"
_PASS = re.compile(r"^\d{4}-\d{2}-\d{2}-[a-z0-9][a-z0-9-]*$")
_TOKEN = re.compile(r"\{\{[A-Z_]+\}\}")    # a template token, filled from a table of values (archive-change.py's render)
FIELDS = ("Skill", "Seen in", "Issue", "Fix")
FROM = "Received from"          # the path the file was taken from
SENDER = "From"                 # the project it came from: the file's first line (Mark, 2026-09-29)
MAIN_FILES = (("skills", "SKILL.md", "skill"), ("agents", "AGENT.md", "agent"), ("workflows", "WORKFLOW.md", "workflow"))
SELF_TEST_MINIMUM = 53       # the exact number of assertions the fixtures run: a dropped block fails
_DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_SLUG = re.compile(r"[a-z0-9][a-z0-9-]*[a-z0-9]")
_RECORD = re.compile(r"^\d{4}-\d{2}-\d{2}-(.+)$")


# ── the notebook and the registry ────────────────────────────────────────────────────────────────

def _config(repo: Path) -> Dict:
    cfg = repo / ".claude" / "wiki-config.json"
    try:
        data = json.loads(cfg.read_text(encoding="utf-8")) if cfg.is_file() else {}
    except (OSError, ValueError):
        data = {}
    return data if isinstance(data, dict) else {}


def _registry(repo: Path) -> Tuple[Optional[Path], Dict]:
    reg = _config(repo).get("registry")
    if not reg:
        return None, {}
    path = Path(reg).expanduser()
    path = path if path.is_absolute() else repo / path
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return path, {}
    notebooks = data.get("notebooks", data) if isinstance(data, dict) else {}
    return path, notebooks if isinstance(notebooks, dict) else {}


def resolve_notebook(repo: Path, override: Optional[str]) -> Tuple[Optional[Path], str]:
    """(notebook root holding wiki/, how it was found) or (None, why not)."""
    if override:
        r = Path(override).expanduser()
        r = r if r.is_absolute() else repo / r
        if (r / "wiki").is_dir():
            return r.resolve(), f"--notebook {override}"
        return None, f"--notebook {override} has no wiki/ folder"
    data = _config(repo)
    root = data.get("llm_wiki_root")
    if root:
        r = Path(root).expanduser()
        r = r if r.is_absolute() else repo / r
        if (r / "wiki").is_dir():
            return r.resolve(), ".claude/wiki-config.json llm_wiki_root"
    nb = data.get("notebook")
    reg_path, notebooks = _registry(repo)
    if nb and reg_path is not None:
        entry = notebooks.get(nb)
        root_val = entry.get("root") if isinstance(entry, dict) else entry
        if root_val:
            r = Path(root_val).expanduser()
            r = r if r.is_absolute() else reg_path.parent / r
            if (r / "wiki").is_dir():
                return r.resolve(), f".claude/wiki-config.json notebook '{nb}' via {reg_path.name}"
    if (repo / "llm-wiki" / "wiki").is_dir():
        return (repo / "llm-wiki").resolve(), "llm-wiki/ in the repository"
    return None, ("no .claude/wiki-config.json that resolves to a notebook with a wiki/ folder, "
                  "and no llm-wiki/ folder in the repository")


def notebook_roots(repo: Path, own: Path) -> List[Path]:
    """Every notebook the registry lists that exists on disk, this library's own first."""
    roots = [own]
    reg_path, notebooks = _registry(repo)
    for entry in notebooks.values():
        root_val = entry.get("root") if isinstance(entry, dict) else entry
        if not isinstance(root_val, str) or reg_path is None:
            continue
        r = Path(root_val).expanduser()
        r = (r if r.is_absolute() else reg_path.parent / r).resolve()
        if r.is_dir() and r not in roots:
            roots.append(r)
    return roots


def library_root(repo: Path, override: Optional[str]) -> Path:
    if override:
        return Path(override).expanduser().resolve()
    try:
        out = subprocess.run(["git", "rev-parse", "--show-toplevel"], cwd=str(repo), capture_output=True, text=True,
                             timeout=10)
        if out.returncode == 0 and out.stdout.strip():
            return Path(out.stdout.strip()).resolve()
    except (OSError, subprocess.SubprocessError):
        pass
    return repo.resolve()


# ── a suggestion file ────────────────────────────────────────────────────────────────────────────

def one_line(value: str) -> str:
    return " ".join(value.split())


def parse(text: str) -> Dict[str, str]:
    out: Dict[str, str] = {}
    decisions: List[str] = []
    for line in text.splitlines():
        if line.startswith("Decision"):
            decisions.append(one_line(line))
            continue
        for f in FIELDS + (FROM, SENDER):
            if line.startswith(f + ":"):
                out.setdefault(f, one_line(line[len(f) + 1:]))
    if decisions:
        out["Decision"] = " | ".join(decisions)
    return out


def missing_fields(fields: Dict[str, str]) -> List[str]:
    return [f for f in FIELDS if not fields.get(f)]


def same_lesson(a: Dict[str, str], b: Dict[str, str]) -> bool:
    return a.get("Skill") == b.get("Skill") and a.get("Issue", "").lower() == b.get("Issue", "").lower()


def same_suggestion(a: Dict[str, str], b: Dict[str, str]) -> bool:
    """The same file sent twice: the same lesson from the same run. The same lesson from another run is a repeat, which
    the improver counts, so receive files it as its own suggestion."""
    return same_lesson(a, b) and a.get("Seen in", "").lower() == b.get("Seen in", "").lower()


def artifact_of(library: Path, skill: str) -> Tuple[Optional[str], Optional[str]]:
    for folder, main, kind in MAIN_FILES:
        p = library / folder / skill / main
        if p.is_file():
            return f"{folder}/{skill}/{main}", kind
    return None, None


def records_for(seen_in: str, roots: List[Path], received_from: Optional[str]) -> List[str]:
    """The run records (raw/code-changes/<date>-<slug>/) a `Seen in` names, in the notebook it came from first."""
    text = re.sub(r"\([^)]*\)", " ", seen_in.lower())
    slugs = [s for s in _SLUG.findall(text) if "-" in s and not _DATE.match(s)]
    ordered = list(roots)
    if received_from:
        src = Path(received_from)
        first = [r for r in roots if r == src or r in src.parents]
        ordered = first + [r for r in roots if r not in first]
    found: List[str] = []
    for root in ordered:
        base = root / "raw" / "code-changes"
        if not base.is_dir():
            continue
        for d in sorted(base.iterdir()):
            m = _RECORD.match(d.name)
            if d.is_dir() and m and m.group(1) in slugs and d.as_posix() not in found:
                found.append(d.as_posix())
    return found


def sender_of(fields: Dict[str, str]) -> str:
    """The project a suggestion came from: its `From:` line, else the folder holding the `_inbox/` its `Received from:`
    path names, else "unknown"."""
    if fields.get(SENDER):
        return fields[SENDER].strip().lower()
    received_from = fields.get(FROM)
    parts = Path(received_from).parts if received_from else ()
    return parts[parts.index("_inbox") - 1].lower() if "_inbox" in parts and parts.index("_inbox") > 0 else "unknown"


def decided_files(root: Path) -> List[Path]:
    """Every decided suggestion: in a pass folder under raw/skill-suggestions/ (never its proposals.md), and in the
    received/archive/ folder decide used before 2026-09-29."""
    out = [p for p in sorted((root / RAW).glob("*/*.md")) if p.name != PROPOSALS_FILE]
    legacy = root / BOX / RECEIVED / ARCHIVE
    return out + (sorted(legacy.glob("*.md")) if legacy.is_dir() else [])


def _free(folder: Path, name: str) -> Path:
    target = folder / name
    n = 2
    while target.exists():
        target = folder / f"{Path(name).stem}-{n}{Path(name).suffix}"
        n += 1
    return target


# ── the subcommands ──────────────────────────────────────────────────────────────────────────────

def cmd_list(repo_arg: str, notebook: Optional[str], library: Optional[str]) -> int:
    repo = Path(repo_arg).resolve()
    root, how = resolve_notebook(repo, notebook)
    if root is None:
        print(f"suggestions: cannot run - {how}", file=sys.stderr)
        return 2
    received = root / BOX / RECEIVED
    files = sorted(received.glob("*.md")) if received.is_dir() else []
    if not files:
        print(f"suggestions: no suggestion received - {received.as_posix()} holds none; nothing to propose",
              file=sys.stderr)
        return 3
    lib = library_root(repo, library)
    roots = notebook_roots(repo, root)
    earlier_all = []
    for p in decided_files(root):
        try:
            earlier_all.append((p, parse(p.read_text(encoding="utf-8"))))
        except OSError:
            continue
    senders = set()
    for p in files:
        with contextlib.suppress(OSError):
            senders.add(sender_of(parse(p.read_text(encoding="utf-8"))))
    base_name = f"{dt.date.today().isoformat()}-{senders.pop() if len(senders) == 1 else 'mixed'}"
    pass_name, n = base_name, 2
    while (root / RAW / pass_name / PROPOSALS_FILE).exists():   # a second pass the same day gets its own folder
        pass_name, n = f"{base_name}-{n}", n + 1
    out: Dict[str, object] = {"notebook": root.as_posix(), "found_by": how, "library": lib.as_posix(),
                              "received": received.as_posix(), "pass": pass_name,
                              "proposals_file": (root / RAW / pass_name / PROPOSALS_FILE).as_posix(),
                              "suggestions": [], "malformed": []}
    for p in files:
        try:
            fields = parse(p.read_text(encoding="utf-8"))
        except OSError as e:
            out["malformed"].append({"file": p.as_posix(), "missing": list(FIELDS), "error": str(e)})
            continue
        gone = missing_fields(fields)
        if gone:
            out["malformed"].append({"file": p.as_posix(), "missing": gone})
            continue
        artifact, kind = artifact_of(lib, fields["Skill"])
        out["suggestions"].append({
            "file": p.as_posix(), "skill": fields["Skill"], "seen_in": fields["Seen in"], "issue": fields["Issue"],
            "fix": fields["Fix"], "received_from": fields.get(FROM),
            "artifact": artifact, "kind": kind,
            "records": records_for(fields["Seen in"], roots, fields.get(FROM)),
            "earlier": [{"file": a.as_posix(), "issue": f.get("Issue", ""), "decision": f.get("Decision", ""),
                         "same_issue": same_lesson(f, fields)}
                        for a, f in earlier_all if f.get("Skill") == fields["Skill"]]})
    print(json.dumps(out, indent=2, ensure_ascii=False))
    return 0


def cmd_receive(repo_arg: str, source_arg: str, notebook: Optional[str]) -> int:
    repo = Path(repo_arg).resolve()
    source = Path(source_arg).expanduser()
    source = source if source.is_absolute() else repo / source
    if not source.is_file():
        print(f"suggestions: cannot run - {source.as_posix()} does not exist", file=sys.stderr)
        return 2
    text = source.read_text(encoding="utf-8")
    fields = parse(text)
    gone = missing_fields(fields)
    if gone:
        print(f"suggestions: cannot run - {source.as_posix()} is not a skill suggestion (missing: {', '.join(gone)})",
              file=sys.stderr)
        return 2
    root, how = resolve_notebook(repo, notebook)
    if root is None:
        print(f"suggestions: cannot run - {how}", file=sys.stderr)
        return 2
    received = root / BOX / RECEIVED
    waiting = sorted(received.glob("*.md")) if received.is_dir() else []
    for p, state in [(p, "received") for p in waiting] + [(p, "decided") for p in decided_files(root)]:
        with contextlib.suppress(OSError):
            if same_suggestion(parse(p.read_text(encoding="utf-8")), fields):
                # the sender's copy goes too: left in the box with its Sent line it would wait for a pickup that never
                # comes, and this notebook already holds the suggestion (one copy, Mark 2026-09-29)
                try:
                    source.unlink()
                except OSError as e:
                    print(f"suggestions: cannot run - already {state} at {p.as_posix()}, but removing the sender's "
                          f"duplicate failed ({e})", file=sys.stderr)
                    return 2
                print(f"suggestions: refused - already {state}: {p.as_posix()}; the sender's duplicate "
                      f"{source.as_posix()} is removed", file=sys.stderr)
                return 1
    taken_from = source.resolve().as_posix()
    body = (f"{SENDER}: {sender_of({FROM: taken_from})}\n" + "".join(f"{f}: {fields[f]}\n" for f in FIELDS)
            + f"{FROM}: {taken_from}\n")
    try:
        received.mkdir(parents=True, exist_ok=True)
        target = _free(received, source.name)
        with open(target, "x", encoding="utf-8", newline="\n") as fh:
            fh.write(body)
        source.unlink()   # moved, not copied: this notebook holds the only copy (Mark, 2026-09-29)
    except OSError as e:
        print(f"suggestions: cannot run - filing failed ({e})", file=sys.stderr)
        return 2
    print(f"received: {target.as_posix()}")
    return 0


def cmd_decide(repo_arg: str, file_arg: str, decision: str, pass_name: str, date: Optional[str], notebook: Optional[str],
               today: Optional[dt.date] = None) -> int:
    today = today or dt.date.today()
    if "\n" in decision or "\r" in decision or not decision.strip():
        print("suggestions: cannot run - --decision must be one non-empty line", file=sys.stderr)
        return 2
    if date is not None and not _DATE.match(date):
        print(f"suggestions: cannot run - --date {date} is not YYYY-MM-DD", file=sys.stderr)
        return 2
    if not _PASS.match(pass_name or ""):
        print(f"suggestions: cannot run - --pass {pass_name!r} is not <YYYY-MM-DD>-<name> (the pass list named)",
              file=sys.stderr)
        return 2
    repo = Path(repo_arg).resolve()
    root, how = resolve_notebook(repo, notebook)
    if root is None:
        print(f"suggestions: cannot run - {how}", file=sys.stderr)
        return 2
    pass_dir = root / RAW / pass_name
    if not (pass_dir / PROPOSALS_FILE).is_file():
        print(f"suggestions: cannot run - {(pass_dir / PROPOSALS_FILE).as_posix()} does not exist: a decision is recorded "
              f"after the pass that proposed it (Step 3 writes that file)", file=sys.stderr)
        return 2
    received = (root / BOX / RECEIVED).resolve()
    f = Path(file_arg).expanduser()
    f = (f if f.is_absolute() else repo / f).resolve()
    if not f.is_file() or f.parent != received:
        print(f"suggestions: cannot run - {f.as_posix()} is not a file in {received.as_posix()} (only a received, "
              f"undecided suggestion is decided)", file=sys.stderr)
        return 2
    line = f"Decision ({date or today.isoformat()}, Mark): {one_line(decision)}\n"
    try:
        text = f.read_text(encoding="utf-8")
        target = _free(pass_dir, f.name)
        target.parent.mkdir(parents=True, exist_ok=True)
        with open(target, "x", encoding="utf-8", newline="\n") as fh:
            fh.write(text if text.endswith("\n") else text + "\n")
            fh.write(line)
        f.unlink()
    except OSError as e:
        print(f"suggestions: cannot run - recording the decision failed ({e})", file=sys.stderr)
        return 2
    print(f"decided: {target.as_posix()}")
    return 0


def _cell(text: str) -> str:
    return one_line(text).replace("|", "\\|")


_DECISION_PREFIX = re.compile(r"^Decision \(([^)]*)\):\s*")


def decision_text(decisions: str) -> str:
    """A file's decision lines as a table cell reads them: `<text> (<date, who>)`, each line's label taken off;
    several decisions (parse joins them with " | ") are kept in order, separated by "; then "."""
    parts = []
    for piece in decisions.split(" | "):
        m = _DECISION_PREFIX.match(piece)
        parts.append(f"{piece[m.end():]} ({m.group(1)})" if m else piece)
    return "; then ".join(parts)


def cmd_summary(repo_arg: str, pass_name: str, out_arg: Optional[str], notebook: Optional[str]) -> int:
    """The pass's wiki page as a draft, from its raw folder: a TL;DR, one row per decided suggestion (skill, where seen,
    issue, decision), the raw files, and the folder README. Creates wiki/project/skill-suggestions/README.md from the
    template when it is missing, never overwriting one. Prints the wiki-update.py command that files the draft."""
    repo = Path(repo_arg).resolve()
    root, how = resolve_notebook(repo, notebook)
    if root is None:
        print(f"suggestions: cannot run - {how}", file=sys.stderr)
        return 2
    pass_dir = root / RAW / pass_name
    if not _PASS.match(pass_name or "") or not (pass_dir / PROPOSALS_FILE).is_file():
        print(f"suggestions: cannot run - {pass_dir.as_posix()} holds no {PROPOSALS_FILE}", file=sys.stderr)
        return 2
    rows: List[Dict[str, str]] = []
    undecided: List[str] = []
    for p in sorted(pass_dir.glob("*.md")):
        if p.name == PROPOSALS_FILE:
            continue
        fields = parse(p.read_text(encoding="utf-8"))
        if not fields.get("Decision") or missing_fields(fields):
            undecided.append(p.name)
            continue
        rows.append({**fields, "file": p.name})
    if undecided:
        print(f"suggestions: refused - {len(undecided)} file(s) in {pass_dir.as_posix()} carry no decision: "
              f"{', '.join(undecided)}", file=sys.stderr)
        return 1
    senders = sorted({sender_of(r) for r in rows}) or ["unknown"]
    date = pass_name[:10]
    accepted = sum(1 for r in rows if "accepted" in r["Decision"].lower())
    turned = sum(1 for r in rows if "turned down" in r["Decision"].lower())
    rel = f"../../../raw/skill-suggestions/{pass_name}"
    lines = ["## TL;DR", "",
             f"{len(rows)} skill suggestion(s) from {', '.join(senders)}, reviewed in the improver pass of {date}: "
             f"{accepted} accepted, {turned} turned down, {len(rows) - accepted - turned} set aside or later. "
             "Each row's decision names the task it became.", "",
             "## Suggestions", "", "| Skill | Seen in | Issue | Decision |", "|---|---|---|---|"]
    lines += [f"| {_cell(r['Skill'])} | {_cell(r['Seen in'])} | {_cell(r['Issue'])} | {_cell(decision_text(r['Decision']))} |"
              for r in rows]
    lines += ["", "## Working files", "", f"- [{PROPOSALS_FILE}]({rel}/{PROPOSALS_FILE}): the proposals put to Mark"]
    lines += [f"- [{r['file']}]({rel}/{r['file']})" for r in rows]
    lines += ["", "## Related in this wiki", "", "- [skill-suggestions/ — folder purpose](README.md)", ""]
    out = Path(out_arg).expanduser() if out_arg else root / "_inbox" / "temp" / f"skill-suggestions-{pass_name}.md"
    readme = root / "wiki" / WIKI_FOLDER / "README.md"
    try:
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text("\n".join(lines), encoding="utf-8", newline="\n")
        if not readme.exists():
            today = dt.date.today()
            values = {"DATE": today.isoformat(), "REVIEW_AFTER": (today + dt.timedelta(days=90)).isoformat()}
            text = _TOKEN.sub(lambda m: values.get(m.group(0)[2:-2], m.group(0)), README_TEMPLATE.read_text(encoding="utf-8"))
            left = sorted(set(_TOKEN.findall(text)))
            if left:
                print(f"suggestions: cannot run - the README template has token(s) this script does not fill: "
                      f"{', '.join(left)}", file=sys.stderr)
                return 2
            readme.parent.mkdir(parents=True, exist_ok=True)
            readme.write_text(text, encoding="utf-8", newline="\n")
            print(f"created: {readme.as_posix()}")
    except OSError as e:
        print(f"suggestions: cannot run - writing failed ({e})", file=sys.stderr)
        return 2
    topic = root.name
    print(f"draft: {out.as_posix()}")
    scripts = (Path.home() / ".claude" / "wiki-scripts").as_posix()
    print(f"file it: uv run --project {scripts} python {scripts}/wiki-update.py --topic {topic} --folder {WIKI_FOLDER} "
          f"--source \"{out.as_posix()}\" --raw-path raw/skill-suggestions/{pass_name}/ --ingested-by claude-code "
          f"--tier self --confidence high --title \"{pass_name} skill suggestions\" "
          f"--tags \"skill-suggestions,improver-pass,{','.join(senders)}\"")
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

    def quiet(fn, *args, **kwargs) -> Tuple[int, str]:
        buf_out, buf_err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(buf_out), contextlib.redirect_stderr(buf_err):
            code = fn(*args, **kwargs)
        return code, buf_out.getvalue() + buf_err.getvalue()

    def w(path: Path, text: str) -> Path:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        return path

    def sug(skill: str, seen: str, issue: str, fix: str = "none yet") -> str:
        return f"Skill: {skill}\nSeen in: {seen}\nIssue: {issue}\nFix: {fix}\n"

    day = dt.date(2026, 9, 27)
    with tempfile.TemporaryDirectory(prefix="suggestions-selftest-") as td:
        base = Path(td).resolve()
        repo = base / "lib"
        w(repo / "skills" / "verifying-before-done" / "SKILL.md", "# v\n")
        w(repo / "agents" / "code-reviewer" / "AGENT.md", "# a\n")
        w(repo / "workflows" / "do-code-change" / "WORKFLOW.md", "# w\n")
        own = base / "vault" / "own"
        (own / "wiki").mkdir(parents=True)
        other = base / "vault" / "other"
        (other / "wiki").mkdir(parents=True)
        rec = other / "raw" / "code-changes" / "2026-09-26-committee-names-from-history"
        w(rec / "checkpoints.md", "The freeze script takes only an integer --step\n")
        (other / "raw" / "code-changes" / "2026-09-25-committee-names").mkdir(parents=True)
        received = own / BOX / RECEIVED

        # no notebook: cannot run
        check("list with no notebook exits 2", quiet(cmd_list, str(repo), None, str(repo))[0] == 2)
        reg = w(base / "linked-notebooks.json", json.dumps({"notebooks": {"own": {"root": "vault/own"},
                                                                          "other": {"root": "vault/other"},
                                                                          "gone": {"root": "vault/gone"}}}))
        w(repo / ".claude" / "wiki-config.json", json.dumps({"notebook": "own", "registry": reg.as_posix()}))
        root, _ = resolve_notebook(repo, None)
        check("the own notebook resolves through wiki-config + registry", root == own.resolve(), str(root))
        check("notebook_roots lists the own notebook first and skips one missing on disk",
              notebook_roots(repo, own.resolve()) == [own.resolve(), other.resolve()],
              str(notebook_roots(repo, own.resolve())))

        # an empty folder is nothing to do, never a result
        code, out = quiet(cmd_list, str(repo), None, str(repo))
        check("list with no received/ folder exits 3", code == 3, out)
        received.mkdir(parents=True)
        check("list with an empty received/ exits 3", quiet(cmd_list, str(repo), None, str(repo))[0] == 3)

        # receive: a sent suggestion MOVES here, the only copy (Mark, 2026-09-29: "it would stay in your notebook because
        # it involves your code"), marked with the project it came from at the top and the path it was taken from
        sent_text = (sug("verifying-before-done", "committee-names-from-history (2026-09-26)",
                         "check-freeze.py --step takes only an integer.", "let --step take a label")
                     + "Decision (2026-09-27, Mark): sent to agent-builder\n")
        sent = w(other / BOX / "verifying-before-done--freeze-step.md", sent_text)
        sent_path = sent.resolve().as_posix()

        def resend() -> Path:   # the sender's file again, for the refusal checks below
            return w(sent, sent_text)
        code, out = quiet(cmd_receive, str(repo), str(sent), None)
        got = received / "verifying-before-done--freeze-step.md"
        check("receive files the suggestion (exit 0)", code == 0 and got.is_file(), out)
        check("receive moves it: the sender's box no longer holds the file", not sent.exists())
        body = got.read_text(encoding="utf-8") if got.is_file() else ""
        check("the received file starts with the project it came from, then the four lines, then where it was taken from",
              body.splitlines()[:5] == [f"{SENDER}: other", "Skill: verifying-before-done",
                                        "Seen in: committee-names-from-history (2026-09-26)",
                                        "Issue: check-freeze.py --step takes only an integer.", "Fix: let --step take a label"]
              and f"{FROM}: {sent_path}" in body, body)
        check("the sender's decision line is not carried (it was the sender's triage)", "Decision" not in body, body)
        check("sender_of reads the From line first, the taken-from path after",
              sender_of({SENDER: "llm-wiki-bootstrap", FROM: sent_path}) == "llm-wiki-bootstrap"
              and sender_of({FROM: sent_path}) == "other" and sender_of({}) == "unknown")
        code, out = quiet(cmd_receive, str(repo), str(resend()), None)
        check("the same suggestion sent twice (skill, issue and Seen in) is refused (exit 1), naming the copy held here",
              code == 1 and got.as_posix() in out, out)
        check("the sender's duplicate is removed: a refused file left in the box would wait for a pickup that never comes "
              "(2026-09-29, llm-wiki's Sent line)", not sent.exists())
        # the same lesson from another run is a repeat, not a duplicate: its own file, so the improver counts the runs
        again = w(other / BOX / "verifying-before-done--freeze-step-again.md",
                  sug("verifying-before-done", "legislators-ingest (2026-09-29)", "check-freeze.py --step takes only an integer.",
                      "let --step take a label"))
        code, out = quiet(cmd_receive, str(repo), str(again), None)
        check("the same lesson seen in another run is received as its own file (exit 0), the repeat the improver counts",
              code == 0 and (received / again.name).is_file() and not again.exists(), out)
        (received / again.name).unlink(missing_ok=True)
        check("receive refuses a file that is not a suggestion (exit 2)",
              quiet(cmd_receive, str(repo), str(w(base / "note.md", "hello\n")), None)[0] == 2)
        check("receive refuses a missing file (exit 2)", quiet(cmd_receive, str(repo), str(base / "nope.md"), None)[0] == 2)

        # list: artifact, records, earlier decisions, malformed files
        w(received / "code-reviewer--lens.md", sug("code-reviewer", "task 12", "A lens wrote a file."))
        w(received / "wiki-update--quotes.md", sug("wiki-update", "a session", "A quote was reworded."))
        w(received / "broken.md", "Skill: do-code-change\nIssue: no seen-in line\n")
        w(received / ARCHIVE / "code-reviewer--older.md",
          sug("code-reviewer", "task 3", "A lens wrote a file.") + "Decision (2026-09-01, Mark): turned down: not reproducible\n")
        code, out = quiet(cmd_list, str(repo), None, str(repo))
        data = json.loads(out) if code == 0 else {}
        by = {s["skill"]: s for s in data.get("suggestions", [])}
        check("list exits 0 with suggestions", code == 0 and len(by) == 3, out[:300])
        check("a skill resolves to its SKILL.md", by.get("verifying-before-done", {}).get("artifact") == "skills/verifying-before-done/SKILL.md")
        check("an agent resolves to its AGENT.md", by.get("code-reviewer", {}).get("kind") == "agent")
        check("a name outside the library has no artifact (not this library)", by.get("wiki-update", {}).get("artifact") is None)
        check("the record the Seen in names is found, and only that one",
              by.get("verifying-before-done", {}).get("records") == [rec.as_posix()], str(by.get("verifying-before-done", {}).get("records")))
        twin = own / "raw" / "code-changes" / rec.name
        twin.mkdir(parents=True)
        found = records_for("committee-names-from-history (2026-09-26)", [own.resolve(), other.resolve()], sent.resolve().as_posix())
        check("the sender's notebook is searched first, the others after",
              found == [rec.as_posix(), twin.resolve().as_posix()], str(found))
        shutil.rmtree(twin)
        check("a Seen in naming no record finds none", by.get("code-reviewer", {}).get("records") == [])
        earlier = by.get("code-reviewer", {}).get("earlier", [])
        check("an earlier decision on the same skill is shown, marked as the same issue",
              len(earlier) == 1 and earlier[0]["same_issue"] and "turned down" in earlier[0]["decision"], str(earlier))
        check("a skill with no earlier decision shows none", by.get("wiki-update", {}).get("earlier") == [])
        check("a malformed file is listed apart with what it lacks",
              data.get("malformed") and data["malformed"][0]["missing"] == ["Seen in", "Fix"], str(data.get("malformed")))
        check("list writes nothing", not (own / RAW).exists() and len(list(received.glob("*.md"))) == 4)

        # Mark, 2026-09-29: a pass is kept in the wiki like a code change. Its raw folder raw/skill-suggestions/<pass>/
        # holds the pass's proposals.md and every suggestion decided in it; list names the pass and its proposals file
        check("list names the pass after today and the sending notebook, and its proposals file in raw/skill-suggestions/",
              data.get("pass") == f"{dt.date.today().isoformat()}-mixed"
              and data.get("proposals_file", "").endswith(f"raw/skill-suggestions/{dt.date.today().isoformat()}-mixed/proposals.md"),
              f"{data.get('pass')} {data.get('proposals_file')}")

        # decide: the decision is appended and the file moved into its pass's raw folder; nothing else is decided
        pass_name = "2026-09-27-other"
        pass_dir = own / RAW / pass_name
        check("decide refuses an empty decision (exit 2)", quiet(cmd_decide, str(repo), str(got), " ", pass_name, None, None, day)[0] == 2)
        check("decide refuses a multi-line decision (exit 2)",
              quiet(cmd_decide, str(repo), str(got), "a\nb", pass_name, None, None, day)[0] == 2)
        check("decide refuses a bad --date (exit 2)", quiet(cmd_decide, str(repo), str(got), "x", pass_name, "27-09-2026", None, day)[0] == 2)
        check("decide refuses a pass name that is not <date>-<name> (exit 2)",
              quiet(cmd_decide, str(repo), str(got), "x", "Sept pass", None, None, day)[0] == 2)
        code, out = quiet(cmd_decide, str(repo), str(got), "x", pass_name, None, None, day)
        check("decide refuses a pass whose proposals.md does not exist yet: a decision comes after a pass (exit 2)",
              code == 2 and "proposals.md" in out, out)
        w(pass_dir / PROPOSALS_FILE, "# Proposals\n\n## P1 - verifying-before-done: --step takes a label\n")
        check("decide refuses a file already decided (exit 2)",
              quiet(cmd_decide, str(repo), str(received / ARCHIVE / "code-reviewer--older.md"), "x", pass_name, None, None, day)[0] == 2)
        check("decide refuses a file outside received/ (exit 2)",
              quiet(cmd_decide, str(repo), str(sent), "x", pass_name, None, None, day)[0] == 2)
        check("no refused decide moved anything", got.is_file())
        code, out = quiet(cmd_decide, str(repo), str(got), "accepted as task 88", pass_name, None, None, day)
        done = pass_dir / "verifying-before-done--freeze-step.md"
        check("decide moves the file into the pass's raw folder (exit 0)", code == 0 and done.is_file() and not got.exists(), out)
        check("the decision line is appended, dated, and the lines above kept",
              done.is_file() and done.read_text(encoding="utf-8").endswith(
                  f"{FROM}: {sent.resolve().as_posix()}\nDecision (2026-09-27, Mark): accepted as task 88\n"),
              done.read_text(encoding="utf-8") if done.is_file() else "")
        w(received / "code-reviewer--older.md", sug("code-reviewer", "task 4", "Another."))
        w(pass_dir / "code-reviewer--older.md", sug("code-reviewer", "task 2", "Taken.") + "Decision (2026-09-27, Mark): x\n")
        code, _ = quiet(cmd_decide, str(repo), str(received / "code-reviewer--older.md"), "turned down: duplicate", pass_name,
                        None, None, day)
        check("a name already taken in the pass folder gets -2", code == 0 and (pass_dir / "code-reviewer--older-2.md").is_file())
        code, out = quiet(cmd_receive, str(repo), str(resend()), None)
        check("a decided suggestion sent again is refused (exit 1), naming it decided, and the sender's duplicate removed",
              code == 1 and "decided" in out and not sent.exists(), out)
        check("the other received suggestions are untouched",
              (received / "code-reviewer--lens.md").is_file() and (received / "wiki-update--quotes.md").is_file())
        code, out = quiet(cmd_list, str(repo), None, str(repo))
        data2 = json.loads(out) if code == 0 else {}
        early = {e["file"].rsplit("/", 1)[-1] for s in data2.get("suggestions", []) if s["skill"] == "code-reviewer" for e in s["earlier"]}
        check("earlier decisions are read from the pass folders and from the old received/archive/, never proposals.md",
              {"code-reviewer--older-2.md", "code-reviewer--older.md"} <= early and PROPOSALS_FILE not in early, str(early))

        # summary: the pass's wiki page, built from its decided files; the folder README once
        w(received / "wiki-update--quotes2.md", sug("wiki-update", "a session", "Another quote."))
        code, out = quiet(cmd_summary, str(repo), "2026-09-27-nope", None, None)
        check("summary refuses a pass folder that does not exist (exit 2)", code == 2, out)
        undecided = w(pass_dir / "stray--undecided.md", sug("stray", "x", "never decided"))
        code, out = quiet(cmd_summary, str(repo), pass_name, None, None)
        check("summary refuses a pass holding a suggestion with no decision (exit 1), naming it", code == 1 and "stray--undecided" in out, out)
        undecided.unlink()
        draft = base / "draft.md"
        code, out = quiet(cmd_summary, str(repo), pass_name, str(draft), None)
        text = draft.read_text(encoding="utf-8") if draft.is_file() else ""
        readme = own / "wiki" / "project" / "skill-suggestions" / "README.md"
        check("summary writes the draft (exit 0) with a TL;DR, one row per decided suggestion and its decision",
              code == 0 and "## TL;DR" in text and "| verifying-before-done |" in text and "accepted as task 88" in text
              and text.count("\n| code-reviewer |") == 2, out + text[:600])
        check("the decision cell drops the line's label and keeps its date",
              "| accepted as task 88 (2026-09-27, Mark) |" in text and "| Decision (" not in text, text[:900])
        check("the draft links the pass's raw files and the folder README",
              f"raw/skill-suggestions/{pass_name}/{PROPOSALS_FILE}" in text and "(README.md)" in text, text[-600:])
        check("summary prints the wiki-update.py command that files the page with the pass's raw folder",
              "wiki-update.py" in out and "--folder project/skill-suggestions" in out
              and f"--raw-path raw/skill-suggestions/{pass_name}/" in out and "--tier self" in out, out)
        check("summary creates the folder README once from the template", readme.is_file() and "skill-suggestions/" in
              readme.read_text(encoding="utf-8"), out)
        readme.write_text(readme.read_text(encoding="utf-8") + "\nedited by hand\n", encoding="utf-8")
        quiet(cmd_summary, str(repo), pass_name, str(draft), None)
        check("an existing folder README is never overwritten", readme.read_text(encoding="utf-8").endswith("edited by hand\n"))

        # task 118's rule (2026-09-29, found by this skill's eval set): Claude Code 2.1.284 refuses `...; echo exit $?`, so
        # the script says its own exit code as its last line, and the skill says to run it alone, exactly as written
        code, out = quiet(main, ["list", "--repo", str(repo)])
        check("main ends on its own exit line (list, exit 0)",
              code == 0 and out.strip().splitlines()[-1] == "suggestions.py: exit 0 - suggestions listed", out[-200:])
        code, out = quiet(main, ["receive", str(resend()), "--repo", str(repo)])
        check("a refusal ends on its exit line and meaning (receive, exit 1)",
              code == 1 and out.strip().splitlines()[-1]
              == "suggestions.py: exit 1 - refused: already here; the sender's duplicate removed",
              out[-200:])

        # --notebook overrides; a --notebook with no wiki/ is refused
        check("--notebook with no wiki/ folder exits 2", quiet(cmd_list, str(repo), str(base / "vault"), str(repo))[0] == 2)
        code, out = quiet(cmd_list, str(repo), str(other), str(repo))
        check("--notebook overrides the lookup (an empty received/ there exits 3)", code == 3, out)

    total = passed + len(failed)
    for f in failed:
        print(f"FAIL {f}")
    if failed:
        print(f"FAIL suggestions self-test ({passed}/{total})")
        return 1
    if passed < SELF_TEST_MINIMUM:
        print(f"FAIL suggestions self-test ran only {passed} assertions (floor {SELF_TEST_MINIMUM}) - a dropped block")
        return 1
    print(f"OK suggestions self-test passed ({passed} assertions; floor {SELF_TEST_MINIMUM})")
    return 0


def main(argv: Optional[List[str]] = None) -> int:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser(description="Gather, receive and decide the skill suggestions sent to this library.")
    ap.add_argument("--self-test", action="store_true", help="prove every rule still fires on a known-bad fixture")
    sub = ap.add_subparsers(dest="cmd")
    for name in ("list", "receive", "decide", "summary"):
        p = sub.add_parser(name)
        p.add_argument("--repo", default=".", help="the library repository (default: current directory)")
        p.add_argument("--notebook", default=None, help="this library's notebook root; overrides the wiki-config lookup")
        if name == "list":
            p.add_argument("--library", default=None, help="the library root (default: the repository's git top level)")
        if name == "receive":
            p.add_argument("file", help="the suggestion file sent here (its path in the sender's box)")
        if name == "decide":
            p.add_argument("file", help="a file in received/")
            p.add_argument("--decision", required=True, help="Mark's decision, one line (e.g. 'accepted as task 88')")
            p.add_argument("--pass", dest="pass_name", required=True,
                           help="the pass that proposed it, <YYYY-MM-DD>-<name> (its raw folder holds proposals.md)")
            p.add_argument("--date", default=None, help="YYYY-MM-DD (default: today)")
        if name == "summary":
            p.add_argument("--pass", dest="pass_name", required=True, help="the pass whose wiki page to draft")
            p.add_argument("--out", default=None, help="where to write the draft (default: <notebook>/_inbox/temp/)")
    args = ap.parse_args(argv)
    if args.self_test:
        return self_test()
    if args.cmd == "list":
        code = cmd_list(args.repo, args.notebook, args.library)
    elif args.cmd == "receive":
        code = cmd_receive(args.repo, args.file, args.notebook)
    elif args.cmd == "decide":
        code = cmd_decide(args.repo, args.file, args.decision, args.pass_name, args.date, args.notebook)
    elif args.cmd == "summary":
        code = cmd_summary(args.repo, args.pass_name, args.out, args.notebook)
    else:
        ap.print_usage()
        return 2
    # the last line says the exit code (task 118's rule): Claude Code 2.1.284 refuses `...; echo exit $?`. On stderr, so
    # list's JSON on stdout stays one clean document.
    print(f"suggestions.py: exit {code} - {EXIT_MEANING.get((args.cmd, code), 'see the message above')}", file=sys.stderr)
    return code


EXIT_MEANING = {("list", 0): "suggestions listed", ("list", 3): "nothing received: nothing to propose",
                ("list", 2): "cannot run", ("receive", 0): "filed in received/",
                ("receive", 1): "refused: already here; the sender's duplicate removed", ("receive", 2): "cannot run",
                ("decide", 0): "decided and moved into the pass folder", ("decide", 2): "cannot run",
                ("summary", 0): "draft written; file it with the command above",
                ("summary", 1): "refused: a suggestion in the pass has no decision", ("summary", 2): "cannot run"}


if __name__ == "__main__":
    sys.exit(main())
