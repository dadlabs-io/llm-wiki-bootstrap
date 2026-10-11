#!/usr/bin/env python3
"""Checks for tasks #92/#93 (agent-builder's suggestions, 2026-10-10): wiki-fetch-pdf.py saves a
two-column page in reading order, so a quote that runs over several lines of one column is in the raw.

    uv run python tests/scripts/test_fetch_pdf_columns.py    # exit 0 = every check passed

`pdftotext -layout` keeps the page's look: on a two-column paper each output line holds a line of the
left column and a line of the right, so every multi-line sentence is interleaved with the other column
and the quote gate cannot find it. Measured on 24 arXiv PDFs against arXiv's HTML text: plain
pdftotext kept 87% of sentences word for word, -layout 59%, MarkItDown 58% (two-column papers: plain
78-98%, -layout 2-10%). The fixture PDF is built here, two columns of three lines each.
"""
from __future__ import annotations

import importlib.util
import shutil
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
import _entry_checks as ec  # noqa: E402

results: list[tuple[bool, str]] = []


def check(name: str, ok: bool, detail: object = ""):
    results.append((bool(ok), name + (f"  [{detail}]" if not ok and detail != "" else "")))


LEFT = ["The left column starts here and", "continues on the second line of", "the left column to its end."]
RIGHT = ["The right column has its own", "sentence that runs down the", "right side of the page."]


def two_column_pdf(path: Path):
    """A one-page PDF, Helvetica 11 pt: LEFT at x=60, RIGHT at x=320, the same three baselines."""
    lines = []
    for i, (l, r) in enumerate(zip(LEFT, RIGHT)):
        y = 700 - 14 * i
        lines.append(f"BT /F1 11 Tf 60 {y} Td ({l}) Tj ET")
        lines.append(f"BT /F1 11 Tf 320 {y} Td ({r}) Tj ET")
    stream = "\n".join(lines).encode("latin-1")
    objs = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R "
        b"/Resources << /Font << /F1 5 0 R >> >> >>",
        b"<< /Length %d >>\nstream\n" % len(stream) + stream + b"\nendstream",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
    ]
    out = bytearray(b"%PDF-1.4\n")
    offsets = []
    for n, body in enumerate(objs, 1):
        offsets.append(len(out))
        out += b"%d 0 obj\n" % n + body + b"\nendobj\n"
    xref = len(out)
    out += b"xref\n0 %d\n0000000000 65535 f \n" % (len(objs) + 1)
    out += b"".join(b"%010d 00000 n \n" % o for o in offsets)
    out += b"trailer\n<< /Size %d /Root 1 0 R >>\nstartxref\n%d\n%%%%EOF\n" % (len(objs) + 1, xref)
    path.write_bytes(bytes(out))


if not shutil.which("pdftotext"):
    print("SKIP: pdftotext is not installed on this machine (the fetcher falls back to pypdf)")
    sys.exit(0)

spec = importlib.util.spec_from_file_location("wiki_fetch_pdf", ROOT / "scripts" / "wiki-fetch-pdf.py")
fetch = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fetch)

with tempfile.TemporaryDirectory() as td:
    pdf = Path(td) / "two-column.pdf"
    two_column_pdf(pdf)
    text = fetch.extract_page_pdftotext(str(pdf), 1)
    squashed = ec._squash(text)
    check("the fixture page has text", bool(text.strip()), repr(text))
    check("#92: the left column's sentence is whole, in reading order", ec._squash(" ".join(LEFT)) in squashed,
          repr(text))
    check("#92: the right column's sentence is whole, in reading order", ec._squash(" ".join(RIGHT)) in squashed,
          repr(text))
    body = f'> "{" ".join(LEFT)}"\n\nRelated.\n'
    check("#92: the quote gate finds a quote that runs over three lines of one column",
          ec.check_quotes(body, text) == [], ec.check_quotes(body, text))

failed = [n for ok, n in results if not ok]
for ok, n in results:
    print(("PASS " if ok else "FAIL ") + n)
print(f"\n{len(results) - len(failed)}/{len(results)} passed")
sys.exit(1 if failed else 0)
