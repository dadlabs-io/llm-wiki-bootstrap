#!/usr/bin/env python3
"""
The link-gap pass (task #201): Related-link candidates for the entries that need them, for a person to review.

    wiki-link-gaps.py --topic N suggest [--since YYYY-MM-DD] [--min-links 2] [-k 20] [--min-score 0.45] [--out <sheet>]
    wiki-link-gaps.py --topic N apply --sheet <sheet> [--dry-run]

`suggest` picks the targets: every entry with fewer than --min-links curated links (under a Related, See also or
Cross-references heading), plus every entry dated on or after --since (default: the date of the newest earlier
sheet in _inbox/reports/; with none, thin entries only). For each it runs the full search on the title and TL;DR
(`wiki-qmd-query.py --json`, the notebook only) and keeps a result that is another entry, scored at least
--min-score (below about 0.45 was mostly noise, 2026-09-14), and not already linked either way. Never a target or
a candidate: session pages, task cards, HOME/README and machine pages (`_*.md`), framework-contract docs, pages at
the wiki root (hubs), keyword-only finds (unscored). It writes a review sheet, one `- [ ] a -> b (score) title`
line per pair, and changes no entry.

`apply` links the pairs a person ticked (`- [x]`), both ways, each bullet at the end of the first Related section
above the footer (`_entry_checks.add_related_link`), skipping a direction already linked. A search result is a
pointer, not a verdict: rank alone kept 421 auto links on agentic-design where a reader kept 43 (2026-09-14), so
nothing is linked unticked.

Exit: 0 done; 2 bad input; 3 NOT checked (every search failed, or nothing to search). Test seam:
WIKI_LINK_GAPS_SEARCH_FROM=<json> maps a target's path under wiki/ to its result rows (`{"_fail": true}` fails all).
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _entry_checks import add_related_link, split_frontmatter  # noqa: E402
from _atomic_io import atomic_write_text  # noqa: E402
from _wiki_config import topic_root  # noqa: E402

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

CURATED = re.compile(r"^(#{2,6})\s*(related\b.*|see also\b.*|cross[- ]references?\b.*)$", re.I | re.M)
HEADING = re.compile(r"^(#{1,6})\s", re.M)
MD_LINK = re.compile(r"\]\(([^)\s#]+\.md)(?:#[^)]*)?\)")
SHEET_LINE = re.compile(r"^- \[([ xX])\] (\S+\.md) -> (\S+\.md) \(([\d.]+)\)")


def eligible(wiki: Path, p: Path, fm: dict) -> bool:
    rel = p.relative_to(wiki).as_posix()
    if "/" not in rel:  # a page at the wiki root: HOME, README, hubs
        return False
    if rel.startswith(("sessions/", "tasks/")) or p.name.startswith("_") or p.name.lower() == "readme.md":
        return False
    return str(fm.get("framework-contract", "")).lower() != "true"


def load(wiki: Path) -> dict:
    """path under wiki/ -> {path, title, date, tldr, text}, for every eligible entry."""
    out = {}
    for p in sorted(wiki.rglob("*.md")):
        text = p.read_text(encoding="utf-8", errors="replace")
        fm, body = split_frontmatter(text, flat=True)
        if not eligible(wiki, p, fm or {}):
            continue
        m = re.search(r"(?ims)^##\s*TL;DR\s*$(.*?)(?=^#|\Z)", body or "")
        out[p.relative_to(wiki).as_posix()] = {
            "path": p, "title": (fm or {}).get("title") or p.stem, "date": str((fm or {}).get("date") or "")[:10],
            "tldr": " ".join((m.group(1) if m else "").split())[:400], "text": text}
    return out


def links_from(rel: str, text: str) -> set[str]:
    """The wiki paths an entry links to (any link in its body)."""
    base = Path(rel).parent
    found = set()
    for t in MD_LINK.findall(text):
        found.add(os.path.normpath(base / t.replace("%20", " ")).replace(os.sep, "/"))
    return found


def curated_count(text: str) -> int:
    n = 0
    for m in CURATED.finditer(text):
        level = len(m.group(1))
        end = len(text)
        for h in HEADING.finditer(text, m.end()):
            if len(h.group(1)) <= level:
                end = h.start()
                break
        n += len(MD_LINK.findall(text[m.end():end]))
    return n


def wiki_relative(file: str) -> str:
    f = str(file).replace("\\", "/")
    i = f.lower().rfind("/wiki/")
    return f[i + 6:] if i >= 0 else f.removeprefix("qmd://")


def search(topic: str, rel: str, query: str, k: int) -> list[dict] | None:
    seam = os.environ.get("WIKI_LINK_GAPS_SEARCH_FROM")
    if seam:
        data = json.loads(Path(seam).read_text(encoding="utf-8"))
        return None if data.get("_fail") else data.get(rel, [])
    helper = Path(__file__).resolve().parent / "wiki-qmd-query.py"
    p = subprocess.run([sys.executable, str(helper), "--notebook", topic, "-k", str(k), "--json", query],
                       capture_output=True, text=True, encoding="utf-8", errors="replace")
    if p.returncode != 0:
        return None
    try:
        rows = json.loads(p.stdout)
    except json.JSONDecodeError:
        return None
    return rows if isinstance(rows, list) else None


def last_sheet_date(reports: Path) -> str | None:
    days = sorted(m.group(1) for f in reports.glob("link-gaps-*.md")
                  for m in [re.match(r"link-gaps-(\d{4}-\d{2}-\d{2})", f.name)] if m)
    return days[-1] if days else None


def cmd_suggest(topic: str, nb: Path, args) -> int:
    wiki, reports = nb / "wiki", nb / "_inbox" / "reports"
    entries = load(wiki)
    since = args.since or last_sheet_date(reports)
    links = {rel: links_from(rel, e["text"]) for rel, e in entries.items()}
    targets = [rel for rel, e in entries.items()
               if curated_count(e["text"]) < args.min_links or (since and e["date"] >= since)]
    if not targets:
        print("link-gap pass: NOT checked: no entry is thin or new", file=sys.stderr)
        return 3
    pairs, failed, seen = [], [], set()
    for rel in targets:
        e = entries[rel]
        rows = search(topic, rel, f"{e['title']} {e['tldr']}".strip(), args.k)
        if rows is None:
            failed.append(rel)
            continue
        for r in rows:
            if r.get("found_by") == "keyword":
                continue
            cand = wiki_relative(r.get("file", ""))
            score = float(r.get("score") or 0)
            key = frozenset((rel, cand))
            if (cand == rel or cand not in entries or score < args.min_score or key in seen
                    or cand in links[rel] or rel in links.get(cand, set())):
                continue
            seen.add(key)
            pairs.append((rel, cand, score, entries[cand]["title"]))
    if len(failed) == len(targets):
        print(f"link-gap pass: NOT checked: every search failed ({len(failed)})", file=sys.stderr)
        return 3
    today = date.today().isoformat()
    out = Path(args.out) if args.out else reports / f"link-gaps-{today}.md"
    body = [f"# Link-gap review sheet — {topic}, {today}", "",
            f"Targets: {len(targets)} ({'thin, or dated on or after ' + since if since else 'thin'}; "
            f"fewer than {args.min_links} curated links counts as thin). Candidates: the full search on title + "
            f"TL;DR, score >= {args.min_score}, not already linked either way. A score is a pointer, not a "
            "verdict: tick only a pair about the same subject.", "",
            "Nothing is linked until you tick a line (`- [x]`) and run "
            f"`wiki-link-gaps.py --topic {topic} apply --sheet <this file>`; each ticked pair is linked both ways.", ""]
    body += [f"- [ ] wiki/{a} -> wiki/{b} ({s:.2f}) {t}" for a, b, s, t in sorted(pairs)] or ["(no candidates)"]
    if failed:
        body += ["", f"Not checked (search failed): {len(failed)}", *[f"- wiki/{r}" for r in failed]]
    out.parent.mkdir(parents=True, exist_ok=True)
    atomic_write_text(out, "\n".join(body) + "\n")
    print(f"link-gap pass: {len(targets)} targets, {len(pairs)} candidate pairs, {len(failed)} not checked -> {out}")
    return 0


def cmd_apply(topic: str, nb: Path, args) -> int:
    wiki = nb / "wiki"
    sheet = Path(args.sheet)
    if not sheet.is_file() and not sheet.is_absolute():  # the sheet's own apply line names it from the notebook
        sheet = nb / sheet
    if not sheet.is_file():
        print(f"no sheet at {sheet}", file=sys.stderr)
        return 2
    added = skipped = 0
    for line in sheet.read_text(encoding="utf-8").splitlines():
        m = SHEET_LINE.match(line)
        if not m or m.group(1) == " ":
            continue
        a, b = (x.removeprefix("wiki/") for x in (m.group(2), m.group(3)))
        for src, dst in ((a, b), (b, a)):
            p, q = wiki / src, wiki / dst
            if not p.is_file() or not q.is_file():
                print(f"  missing: {src if not p.is_file() else dst}", file=sys.stderr)
                skipped += 1
                continue
            text = p.read_text(encoding="utf-8")
            if dst in links_from(src, text):
                skipped += 1
                continue
            fm, _ = split_frontmatter(q.read_text(encoding="utf-8"), flat=True)
            rel = os.path.relpath(q, p.parent).replace(os.sep, "/")
            bullet = f"- [{(fm or {}).get('title') or q.stem}]({rel})"
            if not args.dry_run:
                atomic_write_text(p, add_related_link(text, bullet))
            added += 1
    print(f"link-gap apply: {'would add' if args.dry_run else 'added'} {added} link(s), {skipped} already there or missing")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="The link-gap pass: suggest Related links for review, apply ticked ones.")
    ap.add_argument("--topic")
    common = argparse.ArgumentParser(add_help=False)  # --topic before or after the subcommand
    common.add_argument("--topic", dest="sub_topic")
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("suggest", parents=[common])
    s.add_argument("--since")
    s.add_argument("--min-links", type=int, default=2)
    s.add_argument("-k", type=int, default=20)
    s.add_argument("--min-score", type=float, default=0.45)
    s.add_argument("--out")
    a = sub.add_parser("apply", parents=[common])
    a.add_argument("--sheet", required=True)
    a.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    args.topic = args.sub_topic or args.topic
    if not args.topic:
        ap.error("--topic is required")
    try:
        nb = topic_root(args.topic)
    except Exception as e:  # unknown notebook: refused, never created
        print(str(e), file=sys.stderr)
        return 2
    return cmd_suggest(args.topic, Path(nb), args) if args.cmd == "suggest" else cmd_apply(args.topic, Path(nb), args)


if __name__ == "__main__":
    sys.exit(main())
