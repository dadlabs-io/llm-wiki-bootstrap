"""Duplicate check by a raw's content, not only its source URL (task #81 P5).

Cycle 2026-10-05-02: a Drive copy of a 482-page book already filed from its Amazon URL passed the
URL dedup, and a worker read all 482 pages before noticing. Three layers (Mark, 2026-10-06):

- exact copy: the same size, then the same SHA-256 (a PDF saved twice)            -> duplicate
- near-identical text: NEAR or more of the new raw's 5-word runs are in an older raw
  (the same article under another URL, another fetch header, a few words off)      -> duplicate
- partial overlap: OVERLAP to NEAR (the same review reaching us from two sources)  -> a warning

A twin counts only when an entry, filed under wiki/ or staged in _inbox/proposed/, cites it by its
raw_path; a raw nobody filed is reported as a note, not a duplicate. Used by wiki-update.py:
`--check-duplicate <raw>`, after `--fetch-only` saves a raw, and before filing with `--raw-path`.
"""
from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field
from pathlib import Path

SHINGLE = 5          # words per run: a changed word breaks 5 runs, so scattered edits still read as a copy
SAMPLE = 4           # keep one run in SAMPLE (by hash), so a 36 MB raw folder checks in a few seconds
MIN_RUNS = 40        # fewer sampled runs than this (a short post) gets no text verdict: too little to judge
NEAR = 0.85
OVERLAP = 0.50
TEXT_SUFFIXES = {".md", ".txt", ".html", ".htm", ".vtt", ".srt"}
_WORD_RE = re.compile(r"[a-z0-9]+")
_RAW_PATH_RE = re.compile(r"^raw_path:\s*['\"]?(.+?)['\"]?\s*$", re.M)


@dataclass
class Verdict:
    duplicate: list[tuple[Path, Path, str]] = field(default_factory=list)  # (entry, twin raw, how)
    overlap: list[tuple[Path, Path, float]] = field(default_factory=list)  # (entry, raw, share)
    unfiled: list[tuple[Path, str]] = field(default_factory=list)          # (twin raw, how): no entry cites it


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _body(text: str) -> str:
    if text.startswith("---"):
        end = text.find("\n---", 3)
        if end > 0:
            text = text[end + 4:]
    return text


def runs(text: str) -> set[int]:
    """The sampled 5-word runs of a text raw's body, frontmatter dropped."""
    words = _WORD_RE.findall(_body(text).lower())
    out = set()
    for i in range(len(words) - SHINGLE + 1):
        h = hash(" ".join(words[i:i + SHINGLE]))
        if h % SAMPLE == 0:
            out.add(h)
    return out


def _stem(path: Path) -> str:
    return path.name.rsplit(".", 1)[0]


def citing_entries(topic_root: Path) -> dict[str, list[Path]]:
    """Every raw a filed or staged entry cites, by the raw's file stem (an entry may cite the .md
    the PDF fetcher wrote or the .pdf beside it)."""
    cited: dict[str, list[Path]] = {}
    for base in (topic_root / "wiki", topic_root / "_inbox" / "proposed"):
        if not base.is_dir():
            continue
        for entry in base.rglob("*.md"):
            try:
                head = entry.read_text(encoding="utf-8", errors="replace")[:4000]
            except OSError:
                continue
            m = _RAW_PATH_RE.search(head)
            if m:
                cited.setdefault(_stem(Path(m.group(1).strip())), []).append(entry)
    return cited


def check_raw(raw: Path, topic_root: Path) -> Verdict:
    raw = raw.resolve()
    verdict = Verdict()
    raw_dir = topic_root / "raw"
    if not raw_dir.is_dir() or not raw.is_file():
        return verdict
    cited = citing_entries(topic_root)
    me = _stem(raw)
    others = [p for p in raw_dir.iterdir() if p.is_file() and p.resolve() != raw and _stem(p) != me]

    def record(twin: Path, how: str):
        # an entry cites the twin by its own name, or by a raw named after it (a PDF's text raw was
        # once saved as <date>-<the PDF's name>.md: the book of cycle 2026-10-05-02)
        t = _stem(twin)
        entries = [e for s, es in cited.items() if s == t or t in s for e in es if _stem(e) != me]
        if entries:
            verdict.duplicate.extend((e, twin, how) for e in entries)
        else:
            verdict.unfiled.append((twin, how))

    size = raw.stat().st_size
    digest = None
    for p in others:
        if p.stat().st_size == size:
            digest = digest or _sha256(raw)
            if _sha256(p) == digest:
                record(p, "an exact copy")
    if verdict.duplicate or raw.suffix.lower() not in TEXT_SUFFIXES:
        return verdict
    mine = runs(raw.read_text(encoding="utf-8", errors="replace"))
    if len(mine) < MIN_RUNS:
        return verdict
    exact = {t for t, _ in verdict.unfiled}
    for p in others:
        if p in exact or p.suffix.lower() not in TEXT_SUFFIXES:
            continue
        theirs = runs(p.read_text(encoding="utf-8", errors="replace"))
        if not theirs:
            continue
        share = len(mine & theirs) / len(mine)
        if share >= NEAR:
            record(p, f"near-identical text ({share:.0%} of its passages)")
        elif share >= OVERLAP:
            verdict.overlap.extend((e, p, share) for e in cited.get(_stem(p), []) if _stem(e) != me)
    return verdict


def report(verdict: Verdict, topic_root: Path) -> list[str]:
    """Lines for the caller: duplicate_of= first (what dedup prints), then warnings and notes."""
    def rel(p: Path) -> str:
        try:
            return p.resolve().relative_to(topic_root.resolve()).as_posix()
        except ValueError:
            return str(p)
    lines = []
    for entry, twin, how in verdict.duplicate:
        lines.append(f"Duplicate: this raw is {how} of {rel(twin)}, which {rel(entry)} cites")
        lines.append(f"duplicate_of={entry}")
    for entry, raw, share in verdict.overlap:
        lines.append(f"Warning: overlap: {share:.0%} of this raw's passages are in {rel(raw)}, which {rel(entry)} cites; "
                     "read it as a possible second copy of the same piece before filing")
    for twin, how in verdict.unfiled:
        lines.append(f"Note: this raw is {how} of {rel(twin)}, which no entry cites")
    return lines
