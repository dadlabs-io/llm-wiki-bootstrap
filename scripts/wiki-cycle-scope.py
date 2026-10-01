#!/usr/bin/env python3
"""
What a /wiki-cycle step reads, decided by a script instead of by the model.

    wiki-cycle-scope.py --topic N semantic --run-folder <rf> [--all]
    wiki-cycle-scope.py --topic N claims   --run-folder <rf> [--all]
    wiki-cycle-scope.py --topic N checker  --run-folder <rf> [--min-minutes 15]
    wiki-cycle-scope.py --topic N checker-log --run-folder <rf> --entry <slug> --report <file.json>

`semantic`: the entries added or revised since the last semantic lint (the newest
earlier run folder holding lint-semantic.json; its `timestamp` is the cut-off), plus
this run's staged entries in _inbox/proposed/. With --all, or when no semantic lint
has run yet, every entry. Writes <rf>/semantic-scope.txt, one path per line relative
to the notebook under a `#` header line, and prints the count and the cut-off.

`claims`: the entries no claim in _inbox/claims-index.json comes from, plus those
revised since the index was last written, plus the staged ones. With --all, or no
index, every entry. Writes <rf>/claims-scope.txt.

"Added" is a file created after the cut-off (git when the notebook is in a repository,
else its frontmatter `date`). "Revised" is `last_reviewed` on or after the cut-off's
day: it moves only when an entry is re-read and corrected. A plain "changed" was too
broad: on agentic-design it counted 237 entries a day after a lint, nearly all of them
machine edits (backlink blocks, lint fixes, promotions).

`checker`: the staged entries whose raw is a YouTube transcript at least --min-minutes
long (default: wiki-checker-config.json's min_transcript_minutes, else 15), from the
raw's `duration_seconds`. Writes <rf>/checker-scope.txt.

`checker-log`: appends one line to _inbox/reports/checker-log.jsonl from a checker's
report (entry, source minutes, finding counts by kind, verdict, model), so the pass
rate by length can be read later.

Entries are wiki/**/*.md except `_`-prefixed machine files, README.md and sessions/.
(2026-09-24, task #42: C1 and C3; the 2026-09-23 cycle's findings 10 and 11.)
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _atomic_io import atomic_write_text  # noqa: E402
from _wiki_config import load_config, now_stamp, topic_root  # noqa: E402

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

CHECKER_CONFIG = Path.home() / ".claude" / "agents" / "wiki-checker-config.json"
DEFAULT_MIN_MINUTES = 15


def entries(nb: Path) -> list[str]:
    wiki = nb / "wiki"
    out = []
    for p in wiki.rglob("*.md"):
        rel = p.relative_to(wiki).as_posix()
        if p.name.startswith("_") or p.name.lower() == "readme.md" or rel.startswith("sessions/"):
            continue
        out.append(f"wiki/{rel}")
    return sorted(out)


def staged(nb: Path) -> list[str]:
    prop = nb / "_inbox" / "proposed"
    return sorted(f"_inbox/proposed/{p.name}" for p in prop.glob("*.md")
                  if not p.name.startswith("_") and p.name.lower() != "readme.md") if prop.is_dir() else []


def _parse_time(s: str) -> datetime | None:
    try:
        t = datetime.fromisoformat(str(s).strip().replace("Z", "+00:00"))
        return t if t.tzinfo else t.astimezone()
    except ValueError:
        return None


def _git_top(nb: Path) -> tuple[Path | None, str]:
    try:
        top = subprocess.run(["git", "-C", str(nb), "rev-parse", "--show-toplevel"], capture_output=True,
                             text=True, encoding="utf-8", check=True).stdout.strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None, ""
    repo = Path(top)
    prefix = nb.resolve().relative_to(repo.resolve()).as_posix()
    return repo, ("" if prefix == "." else prefix + "/")


def added_since(nb: Path, cutoff: datetime, among: list[str]) -> list[str]:
    """Entries created after `cutoff`: git's added files (plus untracked ones), else frontmatter `date`."""
    repo, prefix = _git_top(nb)
    if repo:
        log = subprocess.run(["git", "-C", str(repo), "log", f"--since={cutoff.isoformat()}", "--diff-filter=A",
                              "--name-only", "--pretty=format:", "--", f"{prefix}wiki"],
                             capture_output=True, text=True, encoding="utf-8").stdout
        new = subprocess.run(["git", "-C", str(repo), "ls-files", "--others", "--exclude-standard", "--",
                              f"{prefix}wiki"], capture_output=True, text=True, encoding="utf-8").stdout
        got = {l.strip() for l in (log.splitlines() + new.splitlines()) if l.strip()}
        got = {g[len(prefix):] if g.startswith(prefix) else g for g in got}
        return [e for e in among if e in got]
    day = cutoff.date().isoformat()
    return [e for e in among if _front((nb / e).read_text(encoding="utf-8", errors="replace")).get("date", "") > day]


def revised_since(nb: Path, cutoff: datetime, among: list[str]) -> list[str]:
    day = cutoff.date().isoformat()
    return [e for e in among
            if _front((nb / e).read_text(encoding="utf-8", errors="replace")).get("last_reviewed", "")[:10] >= day]


def _index_written(nb: Path, idx_path: Path) -> datetime:
    """When the claims index was last written: its last commit, else its file time."""
    repo, _prefix = _git_top(nb)
    if repo:
        out = subprocess.run(["git", "-C", str(repo), "log", "-1", "--format=%cI", "--", str(idx_path)],
                             capture_output=True, text=True, encoding="utf-8").stdout.strip()
        if out and not subprocess.run(["git", "-C", str(repo), "status", "--porcelain", "--", str(idx_path)],
                                      capture_output=True, text=True, encoding="utf-8").stdout.strip():
            return _parse_time(out)
    return datetime.fromtimestamp(idx_path.stat().st_mtime).astimezone()


def last_semantic(nb: Path, run_folder: Path) -> datetime | None:
    """The timestamp of the newest earlier run's lint-semantic.json."""
    best = None
    for p in (nb / "_inbox" / "reports").glob("*/*/lint-semantic.json"):
        if p.parent.resolve() == run_folder.resolve():
            continue
        try:
            t = _parse_time(json.loads(p.read_text(encoding="utf-8")).get("timestamp", ""))
        except (json.JSONDecodeError, OSError):
            t = None
        if t and (best is None or t > best):
            best = t
    return best


def write_scope(run_folder: Path, name: str, paths: list[str], why: str) -> Path:
    """One path per line under a `#` header line, so an empty scope is never a zero-byte
    file (the stray-file sweeps delete those; the first suite run flagged one, 2026-09-24)."""
    run_folder.mkdir(parents=True, exist_ok=True)
    out = run_folder / name
    atomic_write_text(out, f"# {name}: {len(paths)} ({why})\n" + "".join(p + "\n" for p in paths))
    return out


def cmd_semantic(nb: Path, args) -> int:
    rf = Path(args.run_folder)
    all_entries, st = entries(nb), staged(nb)
    cutoff = None if args.all else last_semantic(nb, rf)
    if cutoff is None:
        scope, why = all_entries + st, ("--all" if args.all else "no earlier semantic lint: every entry")
    else:
        picked = sorted(set(added_since(nb, cutoff, all_entries)) | set(revised_since(nb, cutoff, all_entries)))
        scope, why = picked + st, f"added or revised since {cutoff.isoformat()} + staged"
    out = write_scope(rf, "semantic-scope.txt", scope, why)
    print(f"semantic scope: {len(scope)} of {len(all_entries)} entries + {len(st)} staged ({why}) -> {out}")
    return 0


def cmd_claims(nb: Path, args) -> int:
    rf = Path(args.run_folder)
    all_entries, st = entries(nb), staged(nb)
    idx_path = nb / "_inbox" / "claims-index.json"
    if args.all or not idx_path.is_file():
        scope = all_entries + st
        why = "--all" if args.all else "no claims index: every entry"
    else:
        idx = json.loads(idx_path.read_text(encoding="utf-8"))
        known = {Path(str(c.get("source_entry", ""))).name for c in idx.get("claims", [])}
        missing = [e for e in all_entries if Path(e).name not in known]
        written = _index_written(nb, idx_path)
        revised = revised_since(nb, written, all_entries)
        scope = sorted(set(missing) | set(revised)) + st
        why = (f"{len(missing)} with no claims in the index, {len(set(revised) - set(missing))} revised since "
               f"the index was written ({written.date().isoformat()}) + staged")
    out = write_scope(rf, "claims-scope.txt", scope, why)
    print(f"claims scope: {len(scope)} of {len(all_entries)} entries + {len(st)} staged ({why}) -> {out}")
    return 0


def _front(text: str) -> dict:
    m = re.match(r"\A---\s*\n(.*?)\n---", text, re.S)
    out = {}
    for line in (m.group(1).splitlines() if m else []):
        k, _, v = line.partition(":")
        if v.strip():
            out[k.strip()] = v.strip().strip('"').strip("'")
    return out


def min_minutes(args) -> float:
    if args.min_minutes is not None:
        return args.min_minutes
    try:
        return float(json.loads(CHECKER_CONFIG.read_text(encoding="utf-8")).get("min_transcript_minutes",
                                                                                  DEFAULT_MIN_MINUTES))
    except (OSError, json.JSONDecodeError, ValueError):
        return DEFAULT_MIN_MINUTES


def cmd_checker(nb: Path, args) -> int:
    rf, floor = Path(args.run_folder), min_minutes(args)
    picked, skipped = [], []
    for e in staged(nb):
        rp = _front((nb / e).read_text(encoding="utf-8", errors="replace")).get("raw_path", "")
        raw = nb / rp if rp and not rp.startswith("(") else None
        meta = _front(raw.read_text(encoding="utf-8", errors="replace")) if raw and raw.is_file() else {}
        secs = meta.get("duration_seconds", "")
        minutes = float(secs) / 60 if secs.replace(".", "", 1).isdigit() else None
        if meta.get("type") == "youtube-transcript" and minutes is not None and minutes >= floor:
            picked.append(f"{e}\t{rp}\t{minutes:.0f}")
        else:
            skipped.append(e)
    out = write_scope(rf, "checker-scope.txt", picked, f"staged transcripts of {floor:g}+ minutes: entry, raw, minutes")
    print(f"checker scope: {len(picked)} of {len(picked) + len(skipped)} staged entries are transcripts of "
          f"{floor:g}+ minutes -> {out}")
    for line in picked:
        print("  " + line.replace("\t", "  "))
    return 0


def cmd_checker_log(nb: Path, args) -> int:
    rep = json.loads(Path(args.report).read_text(encoding="utf-8"))
    kinds = ("unsupported_claims", "skipped_sections", "misquotes")
    row = {"ts": now_stamp(), "cycle": Path(args.run_folder).name, "entry": args.entry,
           "source_minutes": rep.get("source_minutes"), "model": rep.get("model"),
           **{k: len(rep.get(k) or []) for k in kinds},
           "verdict": rep.get("verdict") or ("pass" if not any(rep.get(k) for k in kinds) else "fix")}
    log = nb / "_inbox" / "reports" / "checker-log.jsonl"
    log.parent.mkdir(parents=True, exist_ok=True)
    with open(log, "a", encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")
    print(f"logged: {row['entry']} {row['verdict']} "
          + ", ".join(f"{k.replace('_', ' ')} {row[k]}" for k in kinds) + f" -> {log}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[1].strip())
    ap.add_argument("--topic", default=None, help="notebook (default: this project's)")
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name in ("semantic", "claims"):
        s = sub.add_parser(name)
        s.add_argument("--run-folder", required=True)
        s.add_argument("--all", action="store_true", help="every entry (the user's --lint-all)")
    c = sub.add_parser("checker")
    c.add_argument("--run-folder", required=True)
    c.add_argument("--min-minutes", type=float, default=None)
    lg = sub.add_parser("checker-log")
    lg.add_argument("--run-folder", required=True)
    lg.add_argument("--entry", required=True)
    lg.add_argument("--report", required=True)
    args = ap.parse_args()
    topic = args.topic or (load_config() or {}).get("notebook")
    if not topic:
        print("error: no notebook: pass --topic or run inside a wiki project", file=sys.stderr)
        return 2
    nb = Path(topic_root(topic))
    if not (nb / "wiki").is_dir():
        print(f"error: no wiki at {nb}", file=sys.stderr)
        return 2
    return {"semantic": cmd_semantic, "claims": cmd_claims, "checker": cmd_checker,
            "checker-log": cmd_checker_log}[args.cmd](nb, args)


if __name__ == "__main__":
    sys.exit(main())
