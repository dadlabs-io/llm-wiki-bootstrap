#!/usr/bin/env python3
"""Checks for task #104 (improver pass 2026-10-12-mixed P1): an arXiv abstract link is fetched as the paper.

    uv run python tests/scripts/test_arxiv_abs.py    # exit 0 = every check passed

Before: fetchers.md routed only `arxiv.org/pdf/...` to wiki-fetch-pdf.py, so an `arxiv.org/abs/...`
link (what discovery's arXiv feeds and wiki-triage hand over) fell to `wiki-update.py --fetch-only`,
which saved the abstract page: a 51 KB raw with no paper (cycle 2026-10-11-01). Now the PDF fetcher
takes an abs link, downloads the PDF and keeps the abs link as `source_url`; `--fetch-only` refuses
any arXiv paper link, writes nothing, and prints the fetcher command. No check touches the network:
the download is replaced, and the wiki-update run has a dead proxy.
"""
from __future__ import annotations

import importlib.util
import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

results: list[tuple[bool, str]] = []


def check(name: str, ok: bool, detail: object = ""):
    results.append((bool(ok), name + (f"  [{detail}]" if not ok and detail != "" else "")))


def one_line_pdf(path: Path, text: str):
    """A one-page PDF holding one line of Helvetica text."""
    stream = f"BT /F1 11 Tf 60 700 Td ({text}) Tj ET".encode("latin-1")
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


# 1. The URL helper
try:
    from _source_identity import arxiv_pdf_url
except ImportError as exc:
    check("_source_identity.arxiv_pdf_url exists", False, exc)
    arxiv_pdf_url = None

if arxiv_pdf_url:
    cases = {
        "https://arxiv.org/abs/2610.01234": "https://arxiv.org/pdf/2610.01234",
        "https://arxiv.org/abs/2610.01234v2": "https://arxiv.org/pdf/2610.01234v2",
        "http://www.arxiv.org/abs/2610.01234/": "https://arxiv.org/pdf/2610.01234",
        "https://arxiv.org/html/2610.01234v1": "https://arxiv.org/pdf/2610.01234v1",
        "https://arxiv.org/pdf/2610.01234": "https://arxiv.org/pdf/2610.01234",
        "https://arxiv.org/pdf/2610.01234v3.pdf": "https://arxiv.org/pdf/2610.01234v3",
        "https://arxiv.org/list/cs.AI/recent": None,
        "https://example.com/abs/2610.01234": None,
    }
    for url, want in cases.items():
        got = arxiv_pdf_url(url)
        check(f"arxiv_pdf_url({url}) -> {want}", got == want, got)

# 2. The PDF fetcher takes an abs link
spec = importlib.util.spec_from_file_location("wiki_fetch_pdf", SCRIPTS / "wiki-fetch-pdf.py")
fetch = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fetch)

with tempfile.TemporaryDirectory() as td:
    vault = Path(td)
    (vault / "nb" / "wiki").mkdir(parents=True)
    fixture = vault / "paper.pdf"
    one_line_pdf(fixture, "Agents that remember what they read.")
    asked = []

    def fake_download(url, temp_dir):
        asked.append(url)
        dest = Path(temp_dir) / "downloaded.pdf"
        dest.write_bytes(fixture.read_bytes())
        return str(dest)

    fetch.download_pdf = fake_download
    rc = fetch.fetch_pdf(str(vault), "nb", "https://arxiv.org/abs/2610.01234v2", "test", "none", 0.42)
    raws = sorted((vault / "nb" / "raw").glob("*.md"))
    check("fetch-pdf: an abs link exits 0", rc == 0, rc)
    check("fetch-pdf: it downloads the PDF, not the abstract page", asked == ["https://arxiv.org/pdf/2610.01234v2"], asked)
    text = raws[0].read_text(encoding="utf-8") if raws else ""
    check("fetch-pdf: one raw is written", len(raws) == 1, [r.name for r in raws])
    check("fetch-pdf: the raw keeps the abs link as source_url",
          "source_url: https://arxiv.org/abs/2610.01234v2\n" in text, text[:300])
    check("fetch-pdf: the raw holds the paper's text", "Agents that remember what they read." in text, text[-300:])
    check("fetch-pdf: the raw is named after the paper id, not 'abs'",
          bool(raws) and "2610-01234" in raws[0].name, [r.name for r in raws])

# 3. --fetch-only refuses an arXiv paper link and names the fetcher
for link in ("https://arxiv.org/abs/2610.01234", "https://arxiv.org/pdf/2610.01234"):
    with tempfile.TemporaryDirectory() as td:
        vault = Path(td)
        (vault / "nb" / "wiki").mkdir(parents=True)
        env = dict(os.environ, HTTPS_PROXY="http://127.0.0.1:9", HTTP_PROXY="http://127.0.0.1:9",
                   https_proxy="http://127.0.0.1:9", http_proxy="http://127.0.0.1:9", NO_PROXY="", no_proxy="")
        p = subprocess.run([sys.executable, str(SCRIPTS / "wiki-update.py"), "--vault", str(vault), "--topic", "nb",
                            "--source", link, "--fetch-only"], capture_output=True, text=True, encoding="utf-8",
                           env=env, timeout=120)
        out = p.stdout + p.stderr
        raw_dir = vault / "nb" / "raw"
        written = sorted(raw_dir.iterdir()) if raw_dir.is_dir() else []
        check(f"--fetch-only {link}: exits 2", p.returncode == 2, p.returncode)
        check(f"--fetch-only {link}: writes no raw", not written, [w.name for w in written])
        check(f"--fetch-only {link}: names wiki-fetch-pdf.py with the link",
              "wiki-fetch-pdf.py" in out and link in out, out[-400:])

failed = [n for ok, n in results if not ok]
for ok, n in results:
    print(("PASS " if ok else "FAIL ") + n)
print(f"\n{len(results) - len(failed)}/{len(results)} passed")
sys.exit(1 if failed else 0)
