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
    wiki-cycle-scope.py --topic N unfinished --run-folder <rf>
    wiki-cycle-scope.py --topic N unfinished --mark-interrupted <cycle_id> --reason "<why>"
    wiki-cycle-scope.py --topic N writer <raw> [<raw> ...] [--ingester <config.json>]
    wiki-cycle-scope.py --topic N left-undone --run-folder <rf> [--today YYYY-MM-DD]
    wiki-cycle-scope.py --topic N lint-fixes --run-folder <rf> [--show | --applied <ids> --declined <ids>]

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
file that is missing or unreadable is named, with the fallback used. The ingest workers'
line also gives the size from which a raw is written on another model (`large_raw_kb`,
`large_raw_model` in the ingester's file; 10 and opus when absent).

`writer`: which model writes each raw given, by its size on disk against that line:
`<raw>\t<KB>\t<model>` per raw, exit 1 when one is missing. Mark, 2026-11-09 (task #239):
Sonnet writes a raw under 10 KB, Opus one of 10 KB or more; on 10 sources Opus left 2
unsupported sentences to Sonnet's 17, with about twice the content on raws of 10 KB+.
Every agentic-design transcript of 15+ minutes was 15 KB or more, so the size line also
covers the long-transcript rule it replaced for writers.

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

`unfinished`, `left-undone` and `lint-fixes`: what a run left behind and the record of cycle Step 5's fixes. Their
rules, file shapes and wording tables are in the docstring of `_run_state.py`, the one source; this script imports
and dispatches them.

Entries are wiki/**/*.md except `_`-prefixed machine files, README.md and sessions/.
(2026-09-24, task #42: C1 and C3; the 2026-09-23 cycle's findings 10 and 11.)
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _atomic_io import atomic_write_text
from _cycle_common import (
    _front, claims_scope, newest_step, semantic_scope, staged, synthesis_scope, write_scope)
from _run_state import cmd_left_undone, cmd_lint_fixes, cmd_unfinished
from _wiki_config import (
    confirm_before_promote, load_config, now_stamp, topic_root)

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

CHECKER_CONFIG = Path.home() / ".claude" / "agents" / "wiki-checker-config.json"
DEFAULT_MIN_MINUTES = 15
DEFAULT_MIN_RAW_KB = 60.0  # task #202: a long PDF or a whole repo carries the same omission risk as a long talk
DEFAULT_SAMPLE_EVERY = 1  # task #236: every entry; 43 of 44 checked entries needed fixes
# raw types that are a transcript with a length (task #105: cycle 2026-10-11-01's 30-minute Whisper
# transcript was missed, when only YouTube's counted)
TRANSCRIPT_TYPES = {"youtube-transcript", "media-transcript"}


def last_semantic(nb: Path, run_folder: Path) -> datetime | None:
    """The timestamp of the newest earlier run's lint-semantic.json."""
    found = newest_step(nb, "lint-semantic.json", skip=run_folder)
    return found[0] if found else None


def cmd_semantic(nb: Path, args) -> int:
    rf = Path(args.run_folder)
    picked, all_entries, why = semantic_scope(nb, None if args.all else last_semantic(nb, rf), args.all)
    st = staged(nb)
    scope = picked + st
    out = write_scope(rf, "semantic-scope.txt", scope, why)
    print(f"semantic scope: {len(scope)} of {len(all_entries)} entries + {len(st)} staged ({why}) -> {out}")
    return 0


def cmd_claims(nb: Path, args) -> int:
    rf = Path(args.run_folder)
    scope, all_entries, why, _written = claims_scope(nb, args.all)
    st = staged(nb)
    out = write_scope(rf, "claims-scope.txt", scope, why)
    print(f"claims scope: {len(scope)} of {len(all_entries)} entries ({why}); {len(st)} staged left out -> {out}")
    return 0


def last_synthesis(nb: Path, run_folder: Path) -> datetime | None:
    """The timestamp of the newest earlier synthesis the user answered (status completed). One nobody
    could answer (awaiting_approval) leaves the cut-off where it was, so its entries come round again."""
    found = newest_step(nb, "synthesis.json", "completed", run_folder)
    return found[0] if found else None


def cmd_synthesis(nb: Path, args) -> int:
    """Research entries promoted since the last answered synthesis (task #176): synthesis runs in
    every cycle that ingests, so it covers what the user promoted between cycles, never only this run's batch."""
    rf = Path(args.run_folder)
    scope, research, why = synthesis_scope(nb, None if args.all else last_synthesis(nb, rf), args.all)
    out = write_scope(rf, "synthesis-scope.txt", scope, why)
    print(f"synthesis scope: {len(scope)} of {len(research)} research entries ({why}) -> {out}")
    return 0


def min_minutes(args) -> float:
    if args.min_minutes is not None:
        return args.min_minutes
    try:
        return float(json.loads(CHECKER_CONFIG.read_text(encoding="utf-8")).get("min_transcript_minutes",
                                                                                  DEFAULT_MIN_MINUTES))
    except (OSError, json.JSONDecodeError, ValueError):
        return DEFAULT_MIN_MINUTES


def checker_setting(args, flag: str, key: str, default):
    """A checker scope setting: the flag, else wiki-checker-config.json's key, else the default."""
    if getattr(args, flag) is not None:
        return getattr(args, flag)
    try:
        return type(default)(json.loads(CHECKER_CONFIG.read_text(encoding="utf-8")).get(key, default))
    except (OSError, json.JSONDecodeError, ValueError, TypeError):
        return default


def spot_checked(entry: str, every: int) -> bool:
    """1 in `every` entries, by a hash of the entry's name: random across entries, the same on every run."""
    return every > 0 and int(hashlib.sha1(Path(entry).stem.encode("utf-8")).hexdigest(), 16) % every == 0


def cmd_checker(nb: Path, args) -> int:
    """Staged entries the checker reads: a transcript of --min-minutes+, a raw of --min-raw-kb+ (a long PDF, a whole
    repo), and 1 in --sample-every of the rest as a spot check (task #202, Mark 2026-10-23). An entry with no raw
    is never in scope."""
    rf, floor = Path(args.run_folder), min_minutes(args)
    min_kb = checker_setting(args, "min_raw_kb", "min_raw_kb", DEFAULT_MIN_RAW_KB)
    every = checker_setting(args, "sample_every", "sample_every", DEFAULT_SAMPLE_EVERY)
    picked, skipped = [], []
    for e in staged(nb):
        rp = _front((nb / e).read_text(encoding="utf-8", errors="replace")).get("raw_path", "")
        raw = nb / rp if rp and not rp.startswith("(") else None
        if not (raw and raw.is_file()):
            skipped.append(e)
            continue
        meta = _front(raw.read_text(encoding="utf-8", errors="replace"))
        secs = meta.get("duration_seconds", "")
        minutes = float(secs) / 60 if secs.replace(".", "", 1).isdigit() else None
        kb = raw.stat().st_size / 1024
        mins = f"{minutes:.0f}" if minutes is not None else "-"
        if meta.get("type") in TRANSCRIPT_TYPES and minutes is not None and minutes >= floor:
            picked.append((f"{e}\t{rp}\t{mins}", f"transcript of {mins} minutes"))
        elif min_kb > 0 and kb >= min_kb:
            picked.append((f"{e}\t{rp}\t{mins}", f"raw of {kb:.0f} KB"))
        elif spot_checked(e, every):
            picked.append((f"{e}\t{rp}\t{mins}", f"spot check, 1 in {every}"))
        else:
            skipped.append(e)
    rules = [f"transcripts of {floor:g}+ minutes"] + ([f"raws of {min_kb:g}+ KB"] if min_kb > 0 else []) \
        + ([f"1 in {every} of the rest"] if every > 0 else [])
    out = write_scope(rf, "checker-scope.txt", [line for line, _ in picked],
                      f"staged entries: {', '.join(rules)}; entry, raw, minutes ('-' when not a transcript)")
    print(f"checker scope: {len(picked)} of {len(picked) + len(skipped)} staged entries ({', '.join(rules)}) -> {out}")
    for line, why in picked:
        print("  " + line.replace("\t", "  ") + f"  ({why})")
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
            "semantic_lint": "sonnet", "lint_fixes": "sonnet", "synthesis": "sonnet",
            "large_raw_kb": 10, "large_raw_model": "opus"}


def _settings(path: str) -> tuple[dict | None, str]:
    p = Path(path).expanduser()
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
        return (data, "") if isinstance(data, dict) else (None, f"{p}: not a JSON object")
    except FileNotFoundError:
        return None, f"{p}: missing"
    except (OSError, json.JSONDecodeError) as e:
        return None, f"{p}: unreadable ({e})"


def _large_raw(ing: dict | None) -> tuple[float, str]:
    """The size (KB) from which a raw is written on large_raw_model (task #239)."""
    ing = ing or {}
    try:
        kb = float(ing.get("large_raw_kb", FALLBACK["large_raw_kb"]))
    except (TypeError, ValueError):
        kb = float(FALLBACK["large_raw_kb"])
    return kb, ing.get("large_raw_model") or FALLBACK["large_raw_model"]


def cmd_writer(nb: Path, args) -> int:
    ing, err = _settings(args.ingester)
    if err:
        print(f"warning: {err}; using the fallback ({FALLBACK['ingest_workers']}, "
              f"{FALLBACK['large_raw_model']} from {FALLBACK['large_raw_kb']} KB)")
    kb, big = _large_raw(ing)
    small = (ing or {}).get("model_default") or FALLBACK["ingest_workers"]
    rc = 0
    for r in args.raws:
        p = Path(r)
        if not p.is_absolute() and not p.is_file():
            p = nb / r
        if not p.is_file():
            print(f"missing: {r}", file=sys.stderr)
            rc = 1
            continue
        size_kb = p.stat().st_size / 1024
        print(f"{r}\t{size_kb:.0f}\t{big if size_kb >= kb else small}")
    return rc


def cmd_models(nb: Path, args) -> int:
    rf = Path(args.run_folder)
    roles, problems = {}, []
    ing, err = _settings(args.ingester)
    if err:
        problems.append(err)
    kb, big = _large_raw(ing)
    roles["ingest_workers"] = {"model": (ing or {}).get("model_default") or FALLBACK["ingest_workers"],
                               "ask_each_run": bool((ing or {}).get("confirm_model_each_run", False)),
                               "large_raw_kb": kb, "large_raw_model": big,
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
    print(f"ingest workers: {w['model']}"
          + (" (ask the user each run when the session can ask; this is the default)" if w["ask_each_run"] else "")
          + f"; {w['large_raw_model']} for a raw of {w['large_raw_kb']:g} KB or more")
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
    c.add_argument("--min-raw-kb", type=float, default=None, help="a raw this big is checked too (0: off)")
    c.add_argument("--sample-every", type=int, default=None, help="spot-check 1 in N other entries (0: off)")
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
    un = sub.add_parser("unfinished")
    un.add_argument("--run-folder", default=None)
    un.add_argument("--mark-interrupted", metavar="CYCLE_ID", default=None)
    un.add_argument("--reason", default=None)
    wr = sub.add_parser("writer")
    wr.add_argument("raws", nargs="+", help="raw files (absolute, or relative to the notebook)")
    wr.add_argument("--ingester", default=str(HOME_CLAUDE / "agents" / "wiki-ingester-config.json"))
    ld = sub.add_parser("left-undone")
    ld.add_argument("--run-folder", required=True)
    ld.add_argument("--today", default=None, help="YYYY-MM-DD, for tests (default: the local date)")
    lf = sub.add_parser("lint-fixes")
    lf.add_argument("--run-folder", required=True)
    lf.add_argument("--show", action="store_true", help="print the findings with their ids; write nothing")
    lf.add_argument("--applied", default=None, help="ids of the findings applied, comma-separated")
    lf.add_argument("--declined", default=None, help="ids of the findings declined, comma-separated")
    args = ap.parse_args()
    if args.cmd == "unfinished" and bool(args.run_folder) == bool(args.mark_interrupted):
        un.error("give --run-folder (to list) or --mark-interrupted (to close one), not both and not neither")
    if args.cmd == "unfinished" and args.mark_interrupted and not args.reason:
        un.error("--mark-interrupted needs --reason \"<why>\"")
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
            "promote": cmd_promote, "unfinished": cmd_unfinished, "writer": cmd_writer,
            "left-undone": cmd_left_undone, "lint-fixes": cmd_lint_fixes}[args.cmd](nb, args)


if __name__ == "__main__":
    sys.exit(main())
