"""Match PDFs the user saved by hand to the tickets waiting for them (task #81 P7).

A page no fetcher can get stays in its intake bucket as "save as PDF"; the user saves it from Chrome,
which names the file after the page's title. On 2026-10-05, 28 such PDFs were matched to their tickets
by a one-off script; the Drive route queued a saved PDF as a new ticket under its Drive link, losing the
article's URL and queueing the item twice. Both routes now use this: `wiki-triage.py attach-pdfs` for a
PDF saved into an intake folder, `wiki-fetch-drive-folder.py` for one saved to Drive.

Each PDF goes to its best waiting ticket (one with a source URL and no raw_path yet, in `_inbox/pending/`
or any intake bucket) by the words it shares with the ticket's title and URL path: three shared words,
or one long word no other ticket has (an X handle). Two tickets equally good: ambiguous, left to the user.
"""
from __future__ import annotations

import re
from collections import Counter
from pathlib import Path
from urllib.parse import urlsplit

MIN_SHARED = 3
STOP = {"the", "and", "for", "with", "you", "your", "are", "how", "what", "why", "this", "that", "from", "into",
        "not", "but", "can", "its", "our", "all", "about", "medium", "com", "www", "https", "http", "html", "pdf",
        "status", "post", "posts", "part"}
_WORD_RE = re.compile(r"[a-z0-9]+")


def words(text: str) -> set[str]:
    return {w for w in _WORD_RE.findall(text.lower()) if len(w) > 2 and w not in STOP}


def _front(text: str) -> dict:
    m = re.match(r"\A---\s*\n(.*?)\n---", text, re.S)
    out = {}
    for line in (m.group(1).splitlines() if m else []):
        k, _, v = line.partition(":")
        if v:
            out[k.strip()] = v.strip().strip("\"'")
    return out


def waiting_tickets(nb: Path) -> list[dict]:
    """Tickets with a source URL and no raw yet, in _inbox/pending/ and every intake bucket."""
    inbox = nb / "_inbox"
    dirs = [inbox / "pending"]
    if (inbox / "intake").is_dir():
        dirs += sorted(d for d in (inbox / "intake").iterdir() if d.is_dir())
    out = []
    for d in dirs:
        if not d.is_dir():
            continue
        for f in sorted(d.glob("*.md")):
            if f.name.startswith(("_", "README")) or f.name == "triage-log.md":
                continue
            fm = _front(f.read_text(encoding="utf-8", errors="replace"))
            src = fm.get("source", "")
            if not src.startswith(("http://", "https://")) or fm.get("raw_path"):
                continue
            out.append({"path": f, "source": src, "title": fm.get("title", ""),
                        "words": words(fm.get("title", "")) | words(urlsplit(src).path)})
    return out


def match(pdfs: list[Path], tickets: list[dict]):
    """(matched [(pdf, ticket)], unmatched [pdf], ambiguous [(pdf, [tickets])]); the surest pairs first,
    each ticket taken once."""
    df = Counter(w for t in tickets for w in t["words"])
    ranked = {}
    for pdf in pdfs:
        mine = words(pdf.stem)
        scored = []
        for t in tickets:
            shared = mine & t["words"]
            unique = any(df[w] == 1 and len(w) >= 5 for w in shared)
            if len(shared) >= MIN_SHARED or (unique and shared):
                scored.append((len(shared) + (1 if unique else 0), t))
        ranked[pdf] = sorted(scored, key=lambda s: -s[0])
    matched, unmatched, ambiguous, taken = [], [], [], set()
    for pdf in sorted(pdfs, key=lambda p: -(ranked[p][0][0] if ranked[p] else 0)):
        left = [(s, t) for s, t in ranked[pdf] if t["path"] not in taken]
        if not left:
            unmatched.append(pdf)
        elif len(left) > 1 and left[0][0] == left[1][0]:
            ambiguous.append((pdf, [t for s, t in left if s == left[0][0]]))
        else:
            matched.append((pdf, left[0][1]))
            taken.add(left[0][1]["path"])
    return matched, unmatched, ambiguous


def set_raw_path(ticket: Path, raw_rel: str) -> None:
    """Record the raw in the ticket's frontmatter; its source URL stays as it is."""
    text = ticket.read_text(encoding="utf-8")
    text = re.sub(r"^raw_path:.*\n", "", text, flags=re.M)
    text = re.sub(r"\A---\s*\n", f"---\nraw_path: {raw_rel}\n", text, count=1)
    ticket.write_text(text, encoding="utf-8", newline="\n")
