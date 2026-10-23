#!/usr/bin/env python3
"""
What a /wiki-cycle step reads, decided by a script instead of by the model.

    wiki-cycle-scope.py --topic N semantic --run-folder <rf> [--all]
    wiki-cycle-scope.py --topic N claims   --run-folder <rf> [--all]
    wiki-cycle-scope.py --topic N synthesis --run-folder <rf> [--all]
    wiki-cycle-scope.py --topic N checker  --run-folder <rf> [--min-minutes 15]
    wiki-cycle-scope.py --topic N checker-log --run-folder <rf> --entry <slug> --report <file.json>
    wiki-cycle-scope.py --topic N checker-corrected --entry <slug>
    wiki-cycle-scope.py --topic N cost --run-folder <rf> --mark start|end [--session-id <id>]
    wiki-cycle-scope.py --topic N session-cost [--session-id <id>]
    wiki-cycle-scope.py --topic N promote --run-folder <rf>

`semantic`: the entries added or revised since the last semantic lint (the newest
earlier run folder holding lint-semantic.json; its `timestamp` is the cut-off), plus
this run's staged entries in _inbox/proposed/. With --all, or when no semantic lint
has run yet, every entry. Writes <rf>/semantic-scope.txt, one path per line relative
to the notebook under a `#` header line, and prints the count and the cut-off.

`claims`: the entries no claim in _inbox/claims-index.json comes from, plus those
revised since the index was last written. With --all, or no index, every entry. Writes
<rf>/claims-scope.txt. Never a staged entry (task #184, 2026-10-19): one still staged at
this step waits for the user or was held by the checker, so its claims wait until it is
promoted.

`synthesis`: the live research/ entries added since the last synthesis the user answered
(the newest earlier synthesis.json with status completed; its `timestamp` is the cut-off).
Staged entries are never in it: synthesis reads wiki/. No best-practices pages: an empty
scope. With --all, or no earlier synthesis, every live research entry. Writes
<rf>/synthesis-scope.txt (task #176, 2026-10-19).

"Added" is a file created after the cut-off (git when the notebook is in a repository,
else its frontmatter `date`). "Revised" is `last_reviewed` on or after the cut-off's
day: it moves only when an entry is re-read and corrected. A plain "changed" was too
broad: on agentic-design it counted 237 entries a day after a lint, nearly all of them
machine edits (backlink blocks, lint fixes, promotions).

`checker`: the staged entries whose raw is a transcript at least --min-minutes long
(default: wiki-checker-config.json's min_transcript_minutes, else 15), from the raw's
`duration_seconds`: YouTube captions (wiki-fetch-youtube.py) and Whisper transcripts
(wiki-transcribe.py), the TRANSCRIPT_TYPES. A page that carries a transcript is not
counted (Mark, 2026-10-12). Writes <rf>/checker-scope.txt.

`checker-log`: appends one line to _inbox/reports/checker-log.jsonl from a checker's
report (entry, source minutes, finding counts by kind, verdict, model), so the pass
rate by length can be read later, and writes the verdict into the staged entry's sidecar
(`checker`: verdict, report, corrected false). wiki-promote.py holds an entry whose verdict
is `fix` until `checker-corrected --entry <slug>` records that it was corrected from its
report (task #178 row 8, 2026-10-22).

`models`: the model each kind of helper is spawned on, read from the setting files
(--ingester, --checker, --helpers; default the installed paths), printed one line per
role and written to <rf>/models.json. A cycle runs it at Step 0 and spawns from it,
because a sentence asking it to read the files was skipped in 21 of 22 test runs
(task #99, 2026-10-12): the workers got the agent description's default instead. A
file that is missing or unreadable is named, with the fallback used.

`cost`: what the run cost, from the session's running total that the user's status line
saves to ~/.claude/session-cost/<session_id>.json (`total_cost_usd`, Claude Code's own
API-price estimate, subagents included; on a subscription plan it is a comparison figure,
not a bill). `--mark start` records the session's total in <rf>/cost.json; `--mark end`
reads it again and writes the difference to cost.json and cost.md. The session is the
newest file whose `cwd` is this folder (or --session-id); with no such file the step is
NOT checked (exit 3), never a zero (task #138, 2026-10-14). `session-cost [--session-id <id>]`
prints the session's running total alone, for /wrap-up's report (task #182, 2026-10-22).

`promote`: whether the cycle's new entries wait for the user or are promoted without
asking, from the notebook's confirm_before_promote (registry → project wiki-config.json →
true, as /wrap-up reads it). Prints one line and writes <rf>/promote-setting.txt. Until
2026-10-19 the cycle never read the setting: --full promoted everything and every other
mode staged everything (task #184).

Entries are wiki/**/*.md except `_`-prefixed machine files, README.md and sessions/.
(2026-09-24, task #42: C1 and C3; the 2026-09-23 cycle's findings 10 and 11.)
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _entry_checks import split_frontmatter  # noqa: E402
from _atomic_io import atomic_write_text  # noqa: E402
from _wiki_config import confirm_before_promote, load_config, now_stamp, topic_root  # noqa: E402

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

CHECKER_CONFIG = Path.home() / ".claude" / "agents" / "wiki-checker-config.json"
DEFAULT_MIN_MINUTES = 15
# raw types that are a transcript with a length (task #105: cycle 2026-10-11-01's 30-minute Whisper
# transcript was missed, when only YouTube's counted)
TRANSCRIPT_TYPES = {"youtube-transcript", "media-transcript"}


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
        scope = all_entries
        why = "--all" if args.all else "no claims index: every entry"
    else:
        idx = json.loads(idx_path.read_text(encoding="utf-8"))
        known = {Path(str(c.get("source_entry", ""))).name for c in idx.get("claims", [])}
        missing = [e for e in all_entries if Path(e).name not in known]
        written = _index_written(nb, idx_path)
        revised = revised_since(nb, written, all_entries)
        scope = sorted(set(missing) | set(revised))
        why = (f"{len(missing)} with no claims in the index, {len(set(revised) - set(missing))} revised since "
               f"the index was written ({written.date().isoformat()})")
    out = write_scope(rf, "claims-scope.txt", scope, why)
    print(f"claims scope: {len(scope)} of {len(all_entries)} entries ({why}); {len(st)} staged left out -> {out}")
    return 0


def last_synthesis(nb: Path, run_folder: Path) -> datetime | None:
    """The timestamp of the newest earlier synthesis the user answered (status completed). One nobody
    could answer (awaiting_approval) leaves the cut-off where it was, so its entries come round again."""
    best = None
    for p in (nb / "_inbox" / "reports").glob("*/*/synthesis.json"):
        if p.parent.resolve() == run_folder.resolve():
            continue
        try:
            d = json.loads(p.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue
        t = _parse_time(d.get("timestamp", "")) if d.get("status") == "completed" else None
        if t and (best is None or t > best):
            best = t
    return best


def cmd_synthesis(nb: Path, args) -> int:
    """Research entries promoted since the last answered synthesis (task #176, 2026-10-19): synthesis runs in
    every cycle that ingests, so it covers what the user promoted between cycles, never only this run's batch."""
    rf = Path(args.run_folder)
    canon = [p for p in (nb / "wiki" / "project" / "best-practices").glob("*.md")
             if not p.name.startswith("_") and p.name.lower() != "readme.md"]
    research = [e for e in entries(nb) if e.startswith("wiki/research/")
                and not _front((nb / e).read_text(encoding="utf-8", errors="replace")).get("superseded_by")]
    cutoff = None if args.all else last_synthesis(nb, rf)
    if not canon:
        scope, why = [], "no best-practices pages: nothing to synthesise into"
    elif cutoff is None:
        scope, why = research, ("--all" if args.all else "no earlier synthesis: every research entry")
    else:
        scope, why = added_since(nb, cutoff, research), f"research entries added since {cutoff.isoformat()}"
    out = write_scope(rf, "synthesis-scope.txt", scope, why)
    print(f"synthesis scope: {len(scope)} of {len(research)} research entries ({why}) -> {out}")
    return 0


def _front(text: str) -> dict:
    """The frontmatter, by the one shared parser (task #177, 2026-10-22)."""
    return split_frontmatter(text, flat=True)[0]


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
        if meta.get("type") in TRANSCRIPT_TYPES and minutes is not None and minutes >= floor:
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
    kinds = ("unsupported_claims", "skipped_sections", "misquotes", "vague_passages")  # the last since 2026-10-15
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
    # The verdict also goes into the staged entry's sidecar, where wiki-promote.py holds an uncorrected fix
    # (task #178 row 8: the hold rested only on the orchestrator leaving the slug out of the promote call).
    sc = _sidecar(nb, args.entry)
    if sc is None:
        print(f"warning: {args.entry} is not staged (no sidecar in _inbox/proposed/): the verdict is only logged")
        return 0
    meta = json.loads(sc.read_text(encoding="utf-8"))
    meta["checker"] = {"verdict": row["verdict"], "report": args.report, "corrected": False, "logged_at": row["ts"]}
    atomic_write_text(sc, json.dumps(meta, indent=2, ensure_ascii=False) + "\n")
    if row["verdict"] == "fix":
        print(f"held from promotion until corrected: fix the entry from the report, then "
              f"`wiki-cycle-scope.py checker-corrected --entry {args.entry}`")
    return 0


def _sidecar(nb: Path, slug: str) -> Path | None:
    f = nb / "_inbox" / "proposed" / f"{slug}.proposed_metadata.json"
    return f if f.is_file() else None


def cmd_checker_corrected(nb: Path, args) -> int:
    """The staged entry was corrected from its checker report: wiki-promote.py may promote it now."""
    sc = _sidecar(nb, args.entry)
    if sc is None:
        print(f"error: {args.entry} is not staged (no {args.entry}.proposed_metadata.json in _inbox/proposed/)",
              file=sys.stderr)
        return 2
    meta = json.loads(sc.read_text(encoding="utf-8"))
    chk = meta.get("checker")
    if not isinstance(chk, dict):
        print(f"error: {args.entry} has no checker verdict to correct (run checker-log first)", file=sys.stderr)
        return 2
    chk.update({"corrected": True, "corrected_at": now_stamp()})
    atomic_write_text(sc, json.dumps(meta, indent=2, ensure_ascii=False) + "\n")
    print(f"corrected: {args.entry} (checker verdict {chk.get('verdict')}) may be promoted -> {sc}")
    return 0


HOME_CLAUDE = Path.home() / ".claude"
# what each role falls back to when its setting file cannot be read
FALLBACK = {"ingest_workers": "sonnet", "checker": "opus",
            "semantic_lint": "sonnet", "lint_fixes": "sonnet", "synthesis": "sonnet"}


def _settings(path: str) -> tuple[dict | None, str]:
    p = Path(path).expanduser()
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
        return (data, "") if isinstance(data, dict) else (None, f"{p}: not a JSON object")
    except FileNotFoundError:
        return None, f"{p}: missing"
    except (OSError, json.JSONDecodeError) as e:
        return None, f"{p}: unreadable ({e})"


def cmd_models(nb: Path, args) -> int:
    rf = Path(args.run_folder)
    roles, problems = {}, []
    ing, err = _settings(args.ingester)
    if err:
        problems.append(err)
    roles["ingest_workers"] = {"model": (ing or {}).get("model_default") or FALLBACK["ingest_workers"],
                               "ask_each_run": bool((ing or {}).get("confirm_model_each_run", False)),
                               "from": str(Path(args.ingester).expanduser()) if ing else "fallback"}
    chk, err = _settings(args.checker)
    if err:
        problems.append(err)
    roles["checker"] = {"model": (chk or {}).get("model_default") or FALLBACK["checker"],
                        "from": str(Path(args.checker).expanduser()) if chk else "fallback"}
    hlp, err = _settings(args.helpers)
    if err:
        problems.append(err)
    for role in ("semantic_lint", "lint_fixes", "synthesis"):
        roles[role] = {"model": (hlp or {}).get(role) or FALLBACK[role],
                       "from": str(Path(args.helpers).expanduser()) if hlp and hlp.get(role) else "fallback"}
    rf.mkdir(parents=True, exist_ok=True)
    out = rf / "models.json"
    atomic_write_text(out, json.dumps({"timestamp": now_stamp(), "roles": roles, "problems": problems}, indent=2) + "\n")
    w = roles["ingest_workers"]
    print(f"ingest workers: {w['model']}" + (" (ask the user each run when the session can ask; this is the default)"
                                              if w["ask_each_run"] else ""))
    for role in ("checker", "semantic_lint", "lint_fixes", "synthesis"):
        print(f"{role.replace('_', ' ')}: {roles[role]['model']}")
    for p in problems:
        print(f"warning: {p}; its roles use the fallback above")
    print(f"-> {out}")
    return 0


def cmd_promote(nb: Path, args) -> int:
    wait, where = confirm_before_promote(args.topic_name)
    rf = Path(args.run_folder)
    rf.mkdir(parents=True, exist_ok=True)
    # plain text, not JSON: the run folder's *.json files are step results under the cycle contract
    out = rf / "promote-setting.txt"
    atomic_write_text(out, f"confirm_before_promote: {str(wait).lower()}\nfrom: {where}\nat: {now_stamp()}\n")
    if wait:
        print(f"promote: wait for the user (confirm_before_promote: true, from {where}): nothing is promoted; "
              f"new entries stay staged for /wiki-promote -> {out}")
    else:
        print(f"promote: automatic (confirm_before_promote: false, from {where}): every new entry the checker "
              f"did not hold is promoted at Step 5.5 -> {out}")
    return 0


SESSION_COST_DIR = HOME_CLAUDE / "session-cost"


def _norm(p: str) -> str:
    return str(Path(p)).replace("\\", "/").rstrip("/").lower()


def _session_cost(sid):
    folder = Path(os.environ.get("WIKI_SESSION_COST_DIR") or SESSION_COST_DIR)
    if sid:
        f = folder / f"{sid}.json"
        if not f.is_file():
            return None, f"no session-cost file for session {sid} in {folder}"
        try:
            return json.loads(f.read_text(encoding="utf-8")), ""
        except (OSError, ValueError) as e:
            return None, f"{f}: unreadable ({e})"
    here, best = _norm(os.getcwd()), None
    for f in (folder.glob("*.json") if folder.is_dir() else []):
        try:
            d = json.loads(f.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        if _norm(d.get("cwd") or "") == here and isinstance(d.get("total_cost_usd"), (int, float)):
            if best is None or str(d.get("updated", "")) > str(best.get("updated", "")):
                best = d
    if best is None:
        return None, (f"no session-cost file for {os.getcwd()} in {folder} "
                      "(the status line writes one; see the wiki-cycle usage page)")
    return best, ""


def _write_json(path: Path, rec: dict) -> None:
    atomic_write_text(path, json.dumps(rec, indent=2) + "\n")


def cmd_session_cost(nb: Path, args) -> int:
    """The session's running total, for /wrap-up's report (task #182 row 34): no run folder, writes nothing."""
    cur, err = _session_cost(args.session_id)
    if cur is None:
        print(f"cost: NOT checked: {err}")
        return 3
    print(f"cost: ${cur['total_cost_usd']:.2f} so far this session (session {cur['session_id']}; Claude Code's "
          "API-price estimate, subagents included; on a subscription plan a comparison figure, not a bill)")
    return 0


def cmd_cost(nb: Path, args) -> int:
    rf = Path(args.run_folder)
    rf.mkdir(parents=True, exist_ok=True)
    out = rf / "cost.json"
    rec = json.loads(out.read_text(encoding="utf-8")) if out.is_file() else {}
    sid = args.session_id or (rec.get("session_id") if args.mark == "end" else None)
    cur, err = _session_cost(sid)
    if cur is None:
        rec.update({"step": "cost", "status": "not_checked", "not_checked": [err]})
        _write_json(out, rec)
        print(f"cost: NOT checked: {err}")
        return 3
    if args.mark == "start":
        _write_json(out, {"step": "cost", "status": "in_progress", "session_id": cur["session_id"],
                          "start_usd": cur["total_cost_usd"], "start_at": now_stamp()})
        print(f"cost: start ${cur['total_cost_usd']:.2f} (session {cur['session_id']})")
        return 0
    if "start_usd" not in rec:
        rec.update({"step": "cost", "status": "not_checked", "not_checked": ["no start mark in cost.json"]})
        _write_json(out, rec)
        print("cost: NOT checked: no start mark (run `cost --mark start` at Step 0)")
        return 3
    delta = round(cur["total_cost_usd"] - rec["start_usd"], 2)
    rec.update({"status": "completed", "end_usd": cur["total_cost_usd"], "end_at": now_stamp(), "run_usd": delta})
    _write_json(out, rec)
    atomic_write_text(rf / "cost.md", (
        f"# Cost\n\nThis run: ${delta:.2f} (session {rec['session_id']}: ${rec['start_usd']:.2f} at the start, "
        f"${cur['total_cost_usd']:.2f} at the end; Claude Code's API-price estimate, subagents included; "
        "on a subscription plan a comparison figure, not a bill)\n"))
    print(f"cost: this run ${delta:.2f}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[1].strip())
    ap.add_argument("--topic", default=None, help="notebook (default: this project's)")
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name in ("semantic", "claims", "synthesis"):
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
    cc = sub.add_parser("checker-corrected")
    cc.add_argument("--entry", required=True)
    m = sub.add_parser("models")
    m.add_argument("--run-folder", required=True)
    m.add_argument("--ingester", default=str(HOME_CLAUDE / "agents" / "wiki-ingester-config.json"))
    m.add_argument("--checker", default=str(HOME_CLAUDE / "agents" / "wiki-checker-config.json"))
    m.add_argument("--helpers", default=str(HOME_CLAUDE / "skills" / "wiki-cycle" / "helper-models.json"))
    co = sub.add_parser("cost")
    co.add_argument("--run-folder", required=True)
    co.add_argument("--mark", choices=("start", "end"), required=True)
    co.add_argument("--session-id", default=None)
    sco = sub.add_parser("session-cost")
    sco.add_argument("--session-id", default=None)
    pr = sub.add_parser("promote")
    pr.add_argument("--run-folder", required=True)
    args = ap.parse_args()
    topic = args.topic or (load_config() or {}).get("notebook")
    if not topic:
        print("error: no notebook: pass --topic or run inside a wiki project", file=sys.stderr)
        return 2
    args.topic_name = topic
    nb = Path(topic_root(topic))
    if not (nb / "wiki").is_dir():
        print(f"error: no wiki at {nb}", file=sys.stderr)
        return 2
    return {"semantic": cmd_semantic, "claims": cmd_claims, "synthesis": cmd_synthesis, "checker": cmd_checker,
            "checker-log": cmd_checker_log, "checker-corrected": cmd_checker_corrected, "models": cmd_models,
            "cost": cmd_cost, "session-cost": cmd_session_cost,
            "promote": cmd_promote}[args.cmd](nb, args)


if __name__ == "__main__":
    sys.exit(main())
