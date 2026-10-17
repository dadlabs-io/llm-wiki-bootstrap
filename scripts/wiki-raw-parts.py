#!/usr/bin/env python3
"""wiki-raw-parts.py — split a raw too big for one reader into parts, with an index.

A raw too big for one context (a whole repository, a book, a long transcript) is read by
several helpers, each reading one part whole. This script decides the parts, so the split is
the same every time and its coverage can be checked: every line of the raw is in exactly one
part, parts are contiguous and in order. It writes nothing; it prints the index.

Parts follow the raw's own headings (markdown `#`, `##`, `###` lines): sections are joined into
a part until the next one would push it over --max-tokens. A section bigger than that on its own
(a chapter with no sub-headings, a transcript) is cut into windows at blank lines, else at line
ends, each at most --max-tokens. A single line longer than that stays whole and is flagged.

Sizes are in tokens, estimated as characters / 4 (no tokenizer installed; good enough to size a
read, never quoted as a measurement). Lines vary too much between sources to size a read by
(task #163 idea A, from book-to-skill's index-plus-parts layout, 2026-10-17).

Usage:
  wiki-raw-parts.py <raw>                       # the index, one line per part
  wiki-raw-parts.py <raw> --json                # the same as JSON
  wiki-raw-parts.py <raw> --max-tokens 40000 --fit-tokens 80000

Prints `fits_one_worker=yes|no`: yes when the whole raw is at most --fit-tokens, so one worker
reads it whole and no split is needed. Exit 0 on success, 2 on a bad call (no such file).
"""
from __future__ import annotations

import argparse
import json
import math
import re
import sys
from pathlib import Path

DEFAULT_MAX_TOKENS = 40_000   # one part: about two Read pages (the Read tool caps a call near 25,000 tokens)
DEFAULT_FIT_TOKENS = 80_000   # a whole raw one worker reads, beside its skill reading and searches
HEADING = re.compile(r"^#{1,3}\s+\S")


def tokens_of(text: str) -> int:
    return math.ceil(len(text) / 4)


def _label(line: str) -> str:
    s = line.strip()
    return s[:80] + ("…" if len(s) > 80 else "")


def _sections(lines: list[str]) -> list[tuple[int, int]]:
    """(start, end) 0-based inclusive line ranges, one per heading section; text before the first
    heading is its own section."""
    starts = [0] + [i for i, ln in enumerate(lines) if i > 0 and HEADING.match(ln)]
    return [(s, (starts[k + 1] - 1) if k + 1 < len(starts) else len(lines) - 1) for k, s in enumerate(starts)]


def _windows(lines: list[str], sizes: list[int], start: int, end: int, max_tokens: int) -> list[tuple[int, int, str]]:
    """Cut lines[start..end] into windows of at most max_tokens, preferring to end a window at a
    blank line. A line longer than max_tokens on its own becomes a window of one ('oversized')."""
    out: list[tuple[int, int, str]] = []
    i = start
    while i <= end:
        total, j, last_blank = 0, i, None
        while j <= end and total + sizes[j] <= max_tokens:
            total += sizes[j]
            if not lines[j].strip():
                last_blank = j
            j += 1
        if j == i:  # one line bigger than a whole part
            out.append((i, i, "oversized"))
            i += 1
            continue
        if j <= end and last_blank is not None and last_blank > i:
            j = last_blank + 1  # end the window after the blank line
        out.append((i, j - 1, "window"))
        i = j
    return out


def split(lines: list[str], max_tokens: int) -> list[dict]:
    if not lines:
        return []
    sizes = [tokens_of(ln) for ln in lines]
    pieces: list[tuple[int, int, str]] = []  # (start, end, kind) before joining
    for s, e in _sections(lines):
        if sum(sizes[s:e + 1]) <= max_tokens:
            pieces.append((s, e, "heading"))
        else:
            pieces.extend(_windows(lines, sizes, s, e, max_tokens))
    parts: list[list] = []  # [start, end, tokens, kind]
    for s, e, kind in pieces:
        t = sum(sizes[s:e + 1])
        if parts and kind == "heading" and parts[-1][3] == "heading" and parts[-1][2] + t <= max_tokens:
            parts[-1][1], parts[-1][2] = e, parts[-1][2] + t  # join whole sections up to the budget
        else:
            parts.append([s, e, t, kind])
    out = []
    for n, (s, e, t, kind) in enumerate(parts, 1):
        first = next((lines[k] for k in range(s, e + 1) if lines[k].strip()), "")
        out.append({"part": n, "start_line": s + 1, "end_line": e + 1, "tokens": t,
                    "split": kind, "starts_with": _label(first)})
    return out


def check_coverage(parts: list[dict], n_lines: int) -> list[str]:
    """Problems with the parts' coverage of lines 1..n_lines: gaps, overlaps, wrong order."""
    problems, expect = [], 1
    for p in parts:
        if p["start_line"] != expect:
            problems.append(f"part {p['part']} starts at line {p['start_line']}, expected {expect}")
        if p["end_line"] < p["start_line"]:
            problems.append(f"part {p['part']} ends before it starts")
        expect = p["end_line"] + 1
    if n_lines and expect != n_lines + 1:
        problems.append(f"parts end at line {expect - 1}, the raw has {n_lines}")
    return problems


def main(argv: list[str] | None = None) -> int:
    for stream in (sys.stdout, sys.stderr):  # piped on Windows, stdout is cp1252 (see wiki-upgrade.py)
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser(description="Split a raw too big for one reader into parts, with an index.")
    ap.add_argument("raw", help="path to the raw file")
    ap.add_argument("--max-tokens", type=int, default=DEFAULT_MAX_TOKENS,
                    help=f"largest part, in estimated tokens (default {DEFAULT_MAX_TOKENS:,})")
    ap.add_argument("--fit-tokens", type=int, default=DEFAULT_FIT_TOKENS,
                    help=f"largest raw one worker reads whole (default {DEFAULT_FIT_TOKENS:,})")
    ap.add_argument("--json", action="store_true", help="print the index as JSON")
    args = ap.parse_args(argv)
    path = Path(args.raw)
    if not path.is_file():
        print(f"error: no such file: {path}", file=sys.stderr)
        return 2
    if args.max_tokens < 1 or args.fit_tokens < 1:
        print("error: --max-tokens and --fit-tokens must be positive", file=sys.stderr)
        return 2
    text = path.read_text(encoding="utf-8", errors="replace")
    lines = text.splitlines(keepends=True)
    parts = split(lines, args.max_tokens)
    total = sum(p["tokens"] for p in parts)
    fits = total <= args.fit_tokens
    problems = check_coverage(parts, len(lines))
    if problems:  # by construction this never happens; say so loudly if it does
        for p in problems:
            print(f"error: coverage: {p}", file=sys.stderr)
        return 1
    if args.json:
        print(json.dumps({"raw": str(path), "lines": len(lines), "tokens_estimated": total,
                          "fits_one_worker": fits, "max_tokens": args.max_tokens,
                          "fit_tokens": args.fit_tokens, "parts": parts}, ensure_ascii=False, indent=2))
        return 0
    print(f"raw={path}")
    print(f"lines={len(lines)} tokens≈{total:,} (characters / 4)")
    print(f"fits_one_worker={'yes' if fits else 'no'} (limit {args.fit_tokens:,})")
    print(f"parts={len(parts)} (each at most {args.max_tokens:,}; coverage checked: lines 1-{len(lines)}, no gaps)")
    for p in parts:
        flag = "  OVERSIZED: one line bigger than a part" if p["split"] == "oversized" else ""
        print(f"part {p['part']}: lines {p['start_line']}-{p['end_line']}  ≈{p['tokens']:,} tokens  "
              f"[{p['split']}]  {p['starts_with']}{flag}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
