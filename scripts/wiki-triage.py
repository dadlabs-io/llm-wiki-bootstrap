#!/usr/bin/env python3
"""
The mechanical half of /wiki-triage: a notebook's intake buckets, its untriaged
queue, and the move of one queue ticket into the bucket a session chose for it.

A notebook's research sources arrive in `_inbox/pending/` (Drive, discovery, feeds,
queued URLs). Triage gives each one a single owner by moving its ticket into
`_inbox/intake/<folder>/`; the bucket's reader ingests it from there. The buckets are
the frontmatter of `_inbox/intake/README.md`:

    ---
    buckets:
      - folder: main
        purpose: Anything relevant that fits no other bucket
        reader: llm-wiki
      - folder: agent-builder
        purpose: Building agents, workflows, skills, harnesses
        reader: agent-builder
    ---

`reader` is a project's Discord bot name or notebook name from the registry, or `mark`
(the user reads that folder himself; no session ingests from it unasked). A notebook
with no README has one bucket, `main`, read by the session's own project. `main` is
the catch-all: an item that fits no bucket clearly, or two equally, goes there.

    wiki-triage.py buckets  [--topic N]          the buckets, their readers, who is "me"
    wiki-triage.py pending  [--topic N]          tickets waiting in _inbox/pending/
    wiki-triage.py route <ticket> --to <folder> --reason "<why>" [--raw raw/<file>] [--topic N]
    wiki-triage.py log      [--last 30] [--topic N]   past calls, the precedents
    wiki-triage.py check    [--topic N]          validate the config (exit 1 on a problem)

`route` refuses a folder that is not a bucket (exit 2), moves the ticket, records
`raw_path` in it when --raw names a captured raw, and appends a row to
`_inbox/intake/triage-log.md`. Nothing is ever deleted.
(2026-09-24, task #42 section T.)
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _atomic_io import atomic_write_text  # noqa: E402
from _wiki_config import load_config, load_registry, today_label, topic_root  # noqa: E402

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

LOG_HEADER = ("# Triage log\n\nOne row per call, newest last. `/wiki-triage` reads the recent rows as precedents;"
              " a correction by the user is a row like any other.\n\n"
              "| Date | Item | Folder | Reason | By |\n|---|---|---|---|---|\n")


def _registry() -> dict:
    reg, _path = load_registry()
    return reg or {}


def me() -> str:
    """The running session's reader name: its project's bot name, else its notebook name."""
    cfg = load_config() or {}
    nb = cfg.get("notebook") or cfg.get("default_topic") or ""
    disc = (_registry().get(nb) or {}).get("discord") or {}
    return disc.get("bot_name") or nb


def reader_info(reader: str) -> dict:
    """Who a reader is: the user, or a registered project (its Discord id when it has one)."""
    if reader.lower() == "mark":
        return {"reader": reader, "kind": "user", "discord_id": None}
    for name, nb in _registry().items():
        disc = nb.get("discord") or {}
        if reader in (name, disc.get("bot_name")):
            return {"reader": reader, "kind": "project", "notebook": name, "discord_id": disc.get("user_id")}
    return {"reader": reader, "kind": "unknown", "discord_id": None}


def _parse_buckets(front: str) -> list[dict]:
    try:
        import yaml  # optional; the fallback below reads the documented shape
        data = yaml.safe_load(front) or {}
        return [dict(b) for b in data.get("buckets") or []]
    except ImportError:
        pass
    out: list[dict] = []
    for line in front.splitlines():
        m = re.match(r"^\s*(-\s+)?(folder|purpose|reader):\s*(.*?)\s*$", line)
        if not m:
            continue
        if m.group(1):
            out.append({})
        if out:
            out[-1][m.group(2)] = m.group(3).strip().strip('"').strip("'")
    return out


def buckets(nb: Path) -> tuple[list[dict], bool]:
    """(buckets, configured). No README means one `main` bucket read by this project."""
    readme = nb / "_inbox" / "intake" / "README.md"
    if readme.is_file():
        m = re.match(r"\A---\s*\n(.*?)\n---\s*\n", readme.read_text(encoding="utf-8"), re.S)
        if m:
            return _parse_buckets(m.group(1)), True
    return [{"folder": "main", "purpose": "Everything relevant (a notebook with one reader)", "reader": me()}], False


def _problems(bs: list[dict]) -> list[str]:
    out, seen = [], set()
    for i, b in enumerate(bs, 1):
        for f in ("folder", "purpose", "reader"):
            if not str(b.get(f) or "").strip():
                out.append(f"bucket {i}: no {f}")
        folder = str(b.get("folder") or "")
        if folder in seen:
            out.append(f"bucket {i}: folder '{folder}' listed twice")
        seen.add(folder)
        if folder and not re.fullmatch(r"[a-z0-9][a-z0-9-]*", folder):
            out.append(f"bucket {i}: folder '{folder}' is not a plain lower-case name")
        if b.get("reader") and reader_info(str(b["reader"]))["kind"] == "unknown":
            out.append(f"bucket {i}: reader '{b['reader']}' is not 'mark', a notebook or a bot in the registry")
    if "main" not in seen:
        out.append("no 'main' bucket: every notebook needs the catch-all")
    return out


def _tickets(nb: Path) -> list[Path]:
    pend = nb / "_inbox" / "pending"
    return sorted(p for p in pend.glob("*.md") if not p.name.startswith(("_", "README"))) if pend.is_dir() else []


def _front(text: str) -> dict:
    m = re.match(r"\A---\s*\n(.*?)\n---", text, re.S)
    out = {}
    for line in (m.group(1).splitlines() if m else []):
        k, _, v = line.partition(":")
        if v:
            out[k.strip()] = v.strip()
    return out


def cmd_buckets(nb: Path, args) -> int:
    bs, configured = buckets(nb)
    mine = me()
    print(f"notebook: {nb}")
    print(f"config: {'_inbox/intake/README.md' if configured else 'none (one bucket, main)'}; this session reads as: {mine}")
    for b in bs:
        info = reader_info(str(b.get("reader", "")))
        who = ("this session" if b.get("reader") == mine else
               "the user (reviews it himself)" if info["kind"] == "user" else
               f"{info['reader']}" + (f" <@{info['discord_id']}>" if info.get("discord_id") else " (no Discord)"))
        print(f"- {b.get('folder')}: {b.get('purpose')}  [reader: {who}]")
    return 0


def cmd_pending(nb: Path, args) -> int:
    ts = _tickets(nb)
    print(f"{len(ts)} ticket(s) in _inbox/pending/")
    for t in ts:
        fm = _front(t.read_text(encoding="utf-8", errors="replace"))
        print(f"- {t.name}  source={fm.get('source', '?')}" + (f"  raw_path={fm['raw_path']}" if fm.get("raw_path") else ""))
    return 0


def cmd_route(nb: Path, args) -> int:
    bs, _ = buckets(nb)
    folders = {str(b.get("folder")): b for b in bs}
    if args.to not in folders:
        print(f"error: '{args.to}' is not a bucket; buckets: {', '.join(folders)}", file=sys.stderr)
        return 2
    src = Path(args.ticket)
    if not src.is_absolute():
        src = nb / "_inbox" / "pending" / src.name
    if not src.is_file():
        print(f"error: no ticket {src}", file=sys.stderr)
        return 2
    if not args.reason.strip():
        print("error: --reason is required (one line: why this bucket)", file=sys.stderr)
        return 2
    text = src.read_text(encoding="utf-8")
    if args.raw:
        if not ((nb / args.raw).exists()):
            print(f"error: --raw {args.raw} does not exist under the notebook", file=sys.stderr)
            return 2
        text = re.sub(r"^raw_path:.*\n", "", text, flags=re.M)
        text = re.sub(r"\A---\s*\n", f"---\nraw_path: {args.raw}\n", text, count=1)
    dest_dir = nb / "_inbox" / "intake" / args.to
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = dest_dir / src.name
    atomic_write_text(dest, text)
    src.unlink()
    log = nb / "_inbox" / "intake" / "triage-log.md"
    body = log.read_text(encoding="utf-8") if log.is_file() else LOG_HEADER
    item = _front(text).get("source", src.name)
    cell = lambda s: str(s).replace("|", "\\|").replace("\n", " ").strip()  # noqa: E731
    body += f"| {today_label()} | {cell(item)} | {args.to} | {cell(args.reason)} | {cell(args.by or me())} |\n"
    atomic_write_text(log, body)
    reader = folders[args.to].get("reader")
    print(f"routed {src.name} -> _inbox/intake/{args.to}/ (reader: {reader}"
          f"{', this session' if reader == me() else ''})" + (f"; raw_path={args.raw}" if args.raw else ""))
    return 0


def cmd_log(nb: Path, args) -> int:
    log = nb / "_inbox" / "intake" / "triage-log.md"
    if not log.is_file():
        print("no triage log yet")
        return 0
    rows = [l for l in log.read_text(encoding="utf-8").splitlines() if l.startswith("| ") and not l.startswith("| Date")]
    print(f"{len(rows)} call(s); the last {min(args.last, len(rows))}:")
    print("\n".join(rows[-args.last:]))
    return 0


def cmd_check(nb: Path, args) -> int:
    bs, configured = buckets(nb)
    probs = _problems(bs) if configured else []
    for p in probs:
        print(f"PROBLEM: {p}")
    print(f"{len(bs)} bucket(s), {'configured' if configured else 'default (no README)'}; "
          f"{len(probs)} problem(s)")
    return 1 if probs else 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[1].strip())
    ap.add_argument("--topic", default=None, help="notebook (default: this project's)")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("buckets")
    sub.add_parser("pending")
    r = sub.add_parser("route")
    r.add_argument("ticket")
    r.add_argument("--to", required=True)
    r.add_argument("--reason", required=True)
    r.add_argument("--raw", default=None, help="the captured raw, relative to the notebook (raw/<file>)")
    r.add_argument("--by", default=None, help="who decided (default: this session's reader name)")
    lg = sub.add_parser("log")
    lg.add_argument("--last", type=int, default=30)
    sub.add_parser("check")
    args = ap.parse_args()
    topic = args.topic or (load_config() or {}).get("notebook")
    if not topic:
        print("error: no notebook: pass --topic or run inside a wiki project", file=sys.stderr)
        return 2
    nb = Path(topic_root(topic))
    if not (nb / "wiki").is_dir():
        print(f"error: no wiki at {nb}", file=sys.stderr)
        return 2
    return {"buckets": cmd_buckets, "pending": cmd_pending, "route": cmd_route,
            "log": cmd_log, "check": cmd_check}[args.cmd](nb, args)


if __name__ == "__main__":
    sys.exit(main())
