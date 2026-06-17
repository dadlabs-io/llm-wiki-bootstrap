#!/usr/bin/env python3
"""
Fetch a PDF (URL or local file) and save extracted text as a verbatim raw
archive file under <topic>/raw/. Sibling to wiki-fetch-youtube.py and
wiki-fetch-page.js — same pattern: fetch verbatim → save to raw/ → caller
synthesizes a curated wiki entry on top.

Extraction is hybrid (lifted from ingest-pdf.py in the older
research-data-ingestion skill):
  1. Per-page text via `pdftotext` (primary)
  2. Per-page fallback to `pypdf` when text quality is low
  3. Optional OCR fallback via tesseract (when --ocr auto/tesseract and
     tesseract is installed). Skipped silently if tesseract missing.

Designed to run inside the openclaw Docker container where pdftotext + pypdf
are installed. The original PDF is preserved alongside the extracted text.

Usage (inside container):
    python3 wiki-fetch-pdf.py --topic <topic> --source /path/to/file.pdf
    python3 wiki-fetch-pdf.py --topic <topic> --source https://arxiv.org/pdf/2310.08560
"""

import argparse
import os
import re
import shutil
import subprocess
import sys
import tempfile
import urllib.parse
import urllib.request
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

# Atomic-write helper (icarus §8).
sys.path.insert(0, str(Path(__file__).resolve().parent))
from _atomic_io import atomic_write_text  # noqa: E402
from typing import List, Optional, Tuple


# Path-resolution helpers live in the shared _wiki_config module (single
# source of truth for the multi-wiki config schema). Re-exported under the
# historical private names so the rest of this script is unchanged.
sys.path.insert(0, str(Path(__file__).resolve().parent))
from _wiki_config import default_vault as _default_vault, default_topic as _default_topic  # noqa: E402
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

DEFAULT_VAULT = _default_vault()
USER_AGENT = "Mozilla/5.0 (research-wiki/1.0)"

SLUG_RE = re.compile(r"[^a-z0-9]+")


def slugify(text, max_len=60):
    if not text:
        return "untitled"
    s = text.lower().strip()
    s = SLUG_RE.sub("-", s).strip("-")
    return (s[:max_len].rstrip("-") or "untitled")


def unique_path(target):
    target = Path(target)
    if not target.exists():
        return target
    stem, suffix, parent = target.stem, target.suffix, target.parent
    n = 2
    while True:
        cand = parent / f"{stem}-{n}{suffix}"
        if not cand.exists():
            return cand
        n += 1


# ── Hybrid PDF extraction (lifted from ingest-pdf.py) ────────────────────────


@dataclass
class PageResult:
    page: int
    method: str
    text: str


def has_command(cmd):
    return subprocess.run(["bash", "-lc", f"command -v {cmd}"], capture_output=True).returncode == 0


def normalize_text(text):
    return re.sub(r"\s+", " ", (text or "")).strip()


def text_quality_score(text):
    """Heuristic quality score in [0,1]. Higher is better."""
    raw = text or ""
    if not raw.strip():
        return 0.0
    n = len(raw)
    alnum = sum(ch.isalnum() for ch in raw)
    printable = sum(ch.isprintable() for ch in raw)
    spaces = sum(ch.isspace() for ch in raw)
    alnum_ratio = alnum / max(n, 1)
    printable_ratio = printable / max(n, 1)
    space_ratio = spaces / max(n, 1)
    score = (0.55 * alnum_ratio) + (0.35 * printable_ratio) + (0.10 * min(space_ratio / 0.25, 1.0))
    if n < 80:
        score *= 0.6
    return max(0.0, min(score, 1.0))


def is_low_quality(text, threshold):
    return text_quality_score(text) < threshold


def extract_page_pdftotext(pdf_path, page):
    cmd = ["pdftotext", "-layout", "-nopgbrk", "-f", str(page), "-l", str(page), pdf_path, "-"]
    result = subprocess.run(cmd, check=False, capture_output=True, text=True)
    if result.returncode != 0:
        return ""
    return (result.stdout or "").strip()


def extract_page_pypdf(reader, page):
    try:
        return (reader.pages[page - 1].extract_text() or "").strip()
    except Exception:
        return ""


def extract_page_ocr_tesseract(pdf_path, page, temp_dir):
    """Render one page to PNG with pdftoppm, then OCR via tesseract."""
    prefix = os.path.join(temp_dir, f"page-{page}")
    ppm_cmd = ["pdftoppm", "-f", str(page), "-l", str(page), "-singlefile", "-r", "300", "-png", pdf_path, prefix]
    ppm = subprocess.run(ppm_cmd, check=False, capture_output=True, text=True)
    if ppm.returncode != 0:
        return ""
    image_path = f"{prefix}.png"
    if not os.path.exists(image_path):
        return ""
    ocr_cmd = ["tesseract", image_path, "stdout", "--psm", "6"]
    ocr = subprocess.run(ocr_cmd, check=False, capture_output=True, text=True)
    if ocr.returncode != 0:
        return ""
    return (ocr.stdout or "").strip()


def extract_hybrid(pdf_path, quality_threshold, ocr_mode):
    try:
        from pypdf import PdfReader
    except ImportError as e:
        raise RuntimeError("pypdf is required. Install: pip install pypdf") from e

    if not has_command("pdftotext"):
        raise RuntimeError("pdftotext not found. Install poppler-utils (apt-get install poppler-utils).")

    ocr_enabled = False
    if ocr_mode == "tesseract":
        if not has_command("tesseract") or not has_command("pdftoppm"):
            raise RuntimeError("OCR=tesseract requested but tesseract/pdftoppm missing.")
        ocr_enabled = True
    elif ocr_mode == "auto":
        ocr_enabled = has_command("tesseract") and has_command("pdftoppm")

    reader = PdfReader(pdf_path)
    total_pages = len(reader.pages)
    results = []
    stats = {"pages": total_pages, "pdftotext": 0, "pypdf": 0, "ocr": 0, "empty": 0}

    with tempfile.TemporaryDirectory(prefix="wiki-fetch-pdf-") as ocr_temp:
        for page in range(1, total_pages + 1):
            text = extract_page_pdftotext(pdf_path, page)
            method = "pdftotext"
            if is_low_quality(text, quality_threshold):
                pypdf_text = extract_page_pypdf(reader, page)
                if text_quality_score(pypdf_text) > text_quality_score(text):
                    text = pypdf_text
                    method = "pypdf"
            if is_low_quality(text, quality_threshold) and ocr_enabled:
                ocr_text = extract_page_ocr_tesseract(pdf_path, page, ocr_temp)
                if text_quality_score(ocr_text) > text_quality_score(text):
                    text = ocr_text
                    method = "ocr"
            normalized = normalize_text(text)
            if not normalized:
                stats["empty"] += 1
            stats[method] += 1
            results.append(PageResult(page=page, method=method, text=text.strip()))

    return results, stats


# ── Source acquisition (URL or local file) ───────────────────────────────────


def download_pdf(url, temp_dir):
    """Download a URL to a temp .pdf file. Returns path."""
    print(f"  Downloading: {url}")
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=60) as resp:
        ctype = resp.headers.get("Content-Type", "").lower()
        if "pdf" not in ctype and not url.lower().endswith(".pdf"):
            print(f"  Warning: Content-Type is '{ctype}', not application/pdf")
        data = resp.read()
    tmp_path = os.path.join(temp_dir, "downloaded.pdf")
    with open(tmp_path, "wb") as f:
        f.write(data)
    return tmp_path


# ── Main ─────────────────────────────────────────────────────────────────────


def fetch_pdf(vault_root, topic, source, ingested_by, ocr_mode, quality_threshold, slug_override=None, keep_pdf=True):
    topic_root = Path(vault_root) / topic
    if not topic_root.exists():
        print(f"ERROR: topic '{topic}' not found at {topic_root}", file=sys.stderr)
        return 1

    raw_dir = topic_root / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)

    is_url = source.startswith(("http://", "https://"))
    source_url = source if is_url else f"file://{os.path.abspath(source)}"

    with tempfile.TemporaryDirectory(prefix="wiki-fetch-pdf-src-") as temp_dir:
        if is_url:
            try:
                pdf_path = download_pdf(source, temp_dir)
            except Exception as e:
                print(f"ERROR downloading PDF: {e}", file=sys.stderr)
                return 1
        else:
            pdf_path = os.path.abspath(source)
            if not os.path.exists(pdf_path):
                print(f"ERROR: PDF not found at {pdf_path}", file=sys.stderr)
                return 1

        print(f"  Extracting: {pdf_path}")
        try:
            pages, stats = extract_hybrid(pdf_path, quality_threshold, ocr_mode)
        except Exception as e:
            print(f"ERROR during extraction: {e}", file=sys.stderr)
            return 1

        # Build the markdown body — page-by-page
        page_blocks = [f"\n\n## Page {p.page} ({p.method})\n\n{p.text}" for p in pages]
        extracted = "\n".join(page_blocks).strip()

        if not normalize_text(extracted):
            print("ERROR: no usable text extracted from PDF", file=sys.stderr)
            return 1

        # Title from filename or URL
        if is_url:
            url_name = urllib.parse.urlparse(source).path.rstrip("/").split("/")[-1] or "pdf-source"
            title_base = url_name.replace(".pdf", "")
        else:
            title_base = Path(pdf_path).stem
        suggested_title = title_base.replace("-", " ").replace("_", " ").title()

        slug = slug_override or slugify(title_base)
        date = datetime.now().strftime("%Y-%m-%d")
        raw_filename = f"{date}-{slug}.md"
        raw_path = unique_path(raw_dir / raw_filename)

        # Frontmatter + body
        fm = [
            "---",
            f'title: "{suggested_title}"',
            f"source_url: {source_url}",
            "type: pdf",
            f"pdf_pages: {stats['pages']}",
            f"extraction_pdftotext: {stats['pdftotext']}",
            f"extraction_pypdf: {stats['pypdf']}",
            f"extraction_ocr: {stats['ocr']}",
            f"extraction_empty: {stats['empty']}",
            f"fetched: {datetime.now().astimezone().isoformat(timespec='seconds')}",
            f"ingested_by: {ingested_by}",
            "---",
            "",
        ]
        body = [
            f"# {suggested_title}",
            "",
            f"**Source**: <{source_url}>",
            f"**Pages**: {stats['pages']} · **Extraction**: pdftotext={stats['pdftotext']}, pypdf={stats['pypdf']}, ocr={stats['ocr']}, empty={stats['empty']}",
            "",
            "---",
            "",
            extracted,
            "",
        ]

        atomic_write_text(raw_path, "\n".join(fm + body))
        # Optionally copy the source PDF alongside the .md
        if keep_pdf:
            pdf_dest = raw_path.with_suffix(".pdf")
            pdf_dest = unique_path(pdf_dest)
            shutil.copy2(pdf_path, pdf_dest)
            print(f"  Copied PDF: {pdf_dest}")

        print(f"Saved raw: {raw_path}")
        print(f"  Title: {suggested_title}")
        print(f"  Stats: {stats}")
        print()
        print(f"raw_path={raw_path}")
        print(f"source_url={source_url}")
        print(f"suggested_title={suggested_title}")
        return 0


def main():
    parser = argparse.ArgumentParser(description="Fetch a PDF and extract text to wiki raw/")
    parser.add_argument("--topic", required=True, help="Topic name")
    parser.add_argument("--source", required=True, help="URL or local file path")
    parser.add_argument("--vault", default=DEFAULT_VAULT, help=f"Vault root (default: {DEFAULT_VAULT})")
    parser.add_argument("--ingested-by", default="cli", help="Who initiated this fetch")
    parser.add_argument("--slug", default=None, help="Override slug")
    parser.add_argument("--ocr", choices=["none", "auto", "tesseract"], default="auto", help="OCR fallback mode")
    parser.add_argument("--quality-threshold", type=float, default=0.42, help="Quality threshold for fallback")
    parser.add_argument("--no-keep-pdf", dest="keep_pdf", action="store_false", default=True, help="Skip copying source PDF alongside extracted .md")
    args = parser.parse_args()

    return fetch_pdf(args.vault, args.topic, args.source, args.ingested_by, args.ocr, args.quality_threshold, args.slug, args.keep_pdf)


if __name__ == "__main__":
    sys.exit(main())
