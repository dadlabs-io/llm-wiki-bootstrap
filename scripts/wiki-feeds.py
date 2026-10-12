#!/usr/bin/env python3
"""
wiki-feeds.py — read a notebook's trusted sources by their feeds, for /wiki-discover (task #97, Mark 2026-10-11).

A row of `_config/feeds.md` whose **Feed** column holds a feed URL (or `youtube:<channel id | @handle>`) is read
here instead of by web search; a row without one (`—`, or no Feed column at all) stays on web search.

    uv run --project <scripts> python <scripts>/wiki-feeds.py --topic <nb> check [--feed <name>] [--json]
    uv run --project <scripts> python <scripts>/wiki-feeds.py --topic <nb> mark-seen --checklist <file> [--url <u>…]
    uv run --project <scripts> python <scripts>/wiki-feeds.py --topic <nb> known <url> [<url>…]

`check` prints, per source, the items it has not shown before that the notebook does not already hold (wiki,
staged, queued, done, or waiting in an intake bucket, compared by `_source_identity.source_key`), nothing published
before the 2026-01-01 floor. It never marks an item seen: `mark-seen` does, for the items a discovery checklist
lists, so an item held back by the checklist's limit comes back next run (Chubby Skills lost 43 that way).
The first read of a feed shows only items published on or after the row's `To` date (its last web search); the
older and the undated ones are recorded as seen, so a new feed never floods the checklist.

State lives in `<notebook>/_config/feed-state.json`, written only by this script. Exit codes: 0 done; 1 `check`
finished but at least one source failed (each failure is named; that source falls back to web search); 2 bad input
(no feeds.md, no such --feed, no such notebook).
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import _feeds as feeds  # noqa: E402
from _atomic_io import atomic_write_text  # noqa: E402
from _source_identity import source_key  # noqa: E402
from _wiki_config import now_stamp, resolve_vault_topic, today_label  # noqa: E402

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

FLOOR = "2026-01-01"
NO_FEED = {"", "—", "-", "–", "none", "n/a"}
STATE_VERSION = 1
PARALLEL = 6
URL_RE = re.compile(r"https?://[^\s)\]>|`\"']+")


# ---------- feeds.md ----------

def _cells(line: str) -> list[str]:
    return [c.strip() for c in line.strip().strip("|").split("|")]


def _plain(cell: str) -> str:
    return cell.replace("**", "").replace("`", "").strip()


def read_sources(feeds_md: Path) -> list[dict]:
    """Every table row of feeds.md: name, section, tier, to, and its feed ("" when none)."""
    rows, section, header = [], "", None
    lines = feeds_md.read_text(encoding="utf-8").splitlines()
    for i, line in enumerate(lines):
        if line.startswith("#"):
            section, header = line.lstrip("#").strip(), None
            continue
        if not line.lstrip().startswith("|"):
            header = None
            continue
        cells = _cells(line)
        if all(re.fullmatch(r":?-{3,}:?", c) for c in cells if c):
            continue
        if header is None:
            nxt = lines[i + 1] if i + 1 < len(lines) else ""
            if re.match(r"^\s*\|\s*:?-{3,}", nxt):
                header = [_plain(c).lower() for c in cells]
            continue
        cols = dict(zip(header, cells))
        feed = _plain(cols.get("feed", ""))
        rows.append({"name": _plain(cells[0]), "section": section, "tier": _plain(cols.get("tier", "")),
                     "to": _plain(cols.get("to", "")), "feed": "" if feed.lower() in NO_FEED else feed})
    return rows


# ---------- what the notebook already holds ----------

def known_sources(root: Path) -> dict[str, str]:
    """source key -> where it is (wiki/, proposed/, pending/, done/, intake/<bucket>/), from each file's
    `source_url:` / `source:` line. Built once per run: the queue's own check re-reads every file per link."""
    inbox = root / "_inbox"
    places = [("wiki/", root / "wiki", "**/*.md"), ("proposed/", inbox / "proposed", "*.md"),
              ("pending/", inbox / "pending", "*.md"), ("done/", inbox / "done", "*.md"),
              ("intake/", inbox / "intake", "**/*.md")]
    found: dict[str, str] = {}
    for label, folder, pattern in places:
        if not folder.is_dir():
            continue
        for path in folder.glob(pattern):
            try:
                head = path.read_text(encoding="utf-8", errors="replace").splitlines()[:30]
            except OSError:
                continue
            for line in head:
                m = re.match(r"\s*(source_url|source)\s*:\s*(.+)$", line)
                if m:
                    value = m.group(2).strip().strip("\"'")
                    if value.startswith(("http://", "https://")):
                        where = label if label != "intake/" else f"intake/{path.parent.name}/"
                        found.setdefault(source_key(value), where)
                    break
    return found


# ---------- state ----------

def state_path(root: Path) -> Path:
    return root / "_config" / "feed-state.json"


def load_state(root: Path) -> dict:
    path = state_path(root)
    if not path.is_file():
        return {"version": STATE_VERSION, "feeds": {}}
    data = json.loads(path.read_text(encoding="utf-8"))
    data.setdefault("feeds", {})
    return data


def save_state(root: Path, state: dict) -> None:
    path = state_path(root)
    path.parent.mkdir(parents=True, exist_ok=True)
    atomic_write_text(path, json.dumps(state, ensure_ascii=False, indent=1, sort_keys=True) + "\n")


# ---------- reading one source ----------

def read_feed(source: dict, record: dict):
    """(items, how) for one source; raises feeds.FeedError."""
    value = source["feed"]
    if value.lower().startswith("youtube:"):
        got, items, how = feeds.youtube_items(value.split(":", 1)[1].strip(), etag=record.get("etag", ""),
                                              last_modified=record.get("last_modified", ""))
    else:
        got = feeds.fetch(value, etag=record.get("etag", ""), last_modified=record.get("last_modified", ""))
        items, how = ([] if got.not_modified else feeds.parse(got.body)), "feed"
    if got is not None:
        record["etag"], record["last_modified"] = got.etag, got.last_modified
        if got.not_modified:
            how = "feed (unchanged since last read)"
    return items, how


def check_source(source: dict, record: dict, held: dict[str, str]) -> dict:
    """One source's result; updates `record` (first read, last checked, baseline, pending)."""
    out = {"name": source["name"], "section": source["section"], "tier": source["tier"], "feed": source["feed"],
           "status": "", "how": "", "new": [], "held": 0}
    record["name"] = source["name"]
    try:
        items, how = read_feed(source, record)
    except feeds.FeedError as exc:
        out["status"], out["error"] = "failed", f"{exc.code}: {exc}"
        return out
    out["how"] = how
    seen = record.setdefault("seen", {})
    first = "first_read" not in record
    cutoff = source["to"] if re.fullmatch(r"\d{4}-\d{2}-\d{2}", source["to"] or "") else ""
    today = today_label()
    # Waiting items stay until a checklist lists them: an unchanged feed (304) returns none, and a feed that shows
    # only its latest few can drop one before it is listed.
    pending = {k: v for k, v in record.get("pending", {}).items() if k not in seen}
    for item in items:
        key = feeds.item_key(item)
        if key in seen or key in pending:
            continue
        day = item.published[:10]
        if first and not (cutoff and day and day >= cutoff):
            seen[key] = today  # the baseline: what the feed held before we started reading it
            continue
        if day and day < FLOOR:
            seen[key] = today
            continue
        pending[key] = item.as_dict()
    for key, item in list(pending.items()):
        if item.get("url") and source_key(item["url"]) in held:
            out["held"] += 1  # filed, staged or queued since: nothing to show
            seen[key] = today
            del pending[key]
            continue
        out["new"].append({**item, "key": key})
    record["pending"] = pending
    record["last_checked"] = now_stamp()
    if first:
        record["first_read"] = now_stamp()
        out["status"] = f"first read: {len(out['new'])} since {cutoff}" if cutoff else "first read: baseline recorded"
    else:
        out["status"] = f"{len(out['new'])} new"
    return out


# ---------- commands ----------

def cmd_check(root: Path, args) -> int:
    feeds_md = root / "_config" / "feeds.md"
    if not feeds_md.is_file():
        print(f"error: no trusted-sources page at {feeds_md}", file=sys.stderr)
        return 2
    sources = [s for s in read_sources(feeds_md) if s["feed"]]
    web = [s["name"] for s in read_sources(feeds_md) if not s["feed"]]
    if args.feed:
        sources = [s for s in sources if args.feed.lower() in s["name"].lower()]
        if not sources:
            print(f"error: no source with a feed matches {args.feed!r}", file=sys.stderr)
            return 2
    # Two rows naming one feed (two authors on one blog) are read once, under both names: one state record each.
    unique: dict[str, dict] = {}
    for s in sources:
        if s["feed"] in unique:
            unique[s["feed"]]["name"] += f" / {s['name']}"
        else:
            unique[s["feed"]] = dict(s)
    sources = list(unique.values())
    state = load_state(root)
    held = known_sources(root)
    records = [state["feeds"].setdefault(s["feed"], {}) for s in sources]
    with ThreadPoolExecutor(PARALLEL) as pool:
        results = list(pool.map(lambda pair: check_source(pair[0], pair[1], held), zip(sources, records)))
    save_state(root, state)
    failed = [r for r in results if r["status"] == "failed"]
    total = sum(len(r["new"]) for r in results)
    if args.json:
        print(json.dumps({"sources": results, "new_total": total, "web_search": web}, ensure_ascii=False, indent=1))
    else:
        print(f"{len(sources)} source(s) read by feed, {total} new item(s); {len(web)} on web search.")
        for r in results:
            line = f"- {r['name']}: {r['status']}" + (f" — {r['error']}" if r.get("error") else "")
            if r["held"]:
                line += f" ({r['held']} already in the notebook)"
            if r["how"] and r["how"] != "feed":
                line += f" [{r['how']}]"
            print(line)
            for item in r["new"]:
                print(f"    {item['published'][:10] or 'undated'}  {item['title'][:90]}  {item['url']}")
    return 1 if failed else 0


def cmd_mark_seen(root: Path, args) -> int:
    urls = list(args.url or [])
    if args.checklist:
        path = Path(args.checklist)
        if not path.is_file():
            print(f"error: no checklist at {path}", file=sys.stderr)
            return 2
        urls += URL_RE.findall(path.read_text(encoding="utf-8"))
    wanted = {source_key(u) for u in urls}
    state, marked, today = load_state(root), 0, today_label()
    for record in state["feeds"].values():
        pending = record.get("pending", {})
        for key, item in list(pending.items()):
            url = item.get("url", "")
            if url and source_key(url) in wanted:
                record.setdefault("seen", {})[key] = today
                del pending[key]
                marked += 1
    save_state(root, state)
    left = sum(len(r.get("pending", {})) for r in state["feeds"].values())
    print(f"marked seen: {marked}; still waiting for a later checklist: {left}")
    return 0


def cmd_known(root: Path, args) -> int:
    held = known_sources(root)
    for url in args.urls:
        where = held.get(source_key(url))
        print(f"held {where} {url}" if where else f"new {url}")
    return 0


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__.strip().splitlines()[0])
    p.add_argument("--topic", required=True, help="the notebook whose _config/feeds.md is read")
    p.add_argument("--vault", default=None, help="legacy vault root; default: resolve --topic through the registry")
    sub = p.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("check", help="new items from every source with a feed")
    c.add_argument("--feed", help="only sources whose name contains this (case-insensitive)")
    c.add_argument("--json", action="store_true", help="machine-readable output for /wiki-discover")
    m = sub.add_parser("mark-seen", help="mark seen the items a discovery checklist lists")
    m.add_argument("--checklist", help="the discovery checklist (every link in it)")
    m.add_argument("--url", action="append", help="a link to mark seen (repeatable)")
    k = sub.add_parser("known", help="is each link already in the notebook (wiki, staged, queue, intake)?")
    k.add_argument("urls", nargs="+")
    args = p.parse_args(argv)
    try:
        vault, topic = resolve_vault_topic(args.topic, args.vault)
    except SystemExit as exc:
        return int(exc.code or 2)
    root = Path(vault) / topic
    if not root.is_dir():
        print(f"error: notebook '{topic}' not found at {root}", file=sys.stderr)
        return 2
    return {"check": cmd_check, "mark-seen": cmd_mark_seen, "known": cmd_known}[args.cmd](root, args)


if __name__ == "__main__":
    sys.exit(main())
