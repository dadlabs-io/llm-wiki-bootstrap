"""_markdown.py — HTML to Markdown for the raws the scripts save (task #71, 2026-10-04).

MarkItDown (Microsoft, MIT; in the scripts' uv environment) keeps headings, links, lists, quotes, tables and
every HTML entity, which the old tag-stripper lost. It converts the whole page, menus and footer included:
it is a converter, not an article extractor. Only its stream converter is used, on bytes we already
fetched: never its URL fetching (its own security advice).

When MarkItDown cannot be loaded or fails on a page, `html_to_markdown` returns None with the reason, and
the caller falls back to its plain-text converter and says so.
"""
from __future__ import annotations

import io

_converter = None


def html_to_markdown(html: str) -> tuple[str | None, str]:
    """(markdown, "markitdown") or (None, why it could not convert)."""
    global _converter
    try:
        from markitdown import MarkItDown, StreamInfo
    except ImportError as e:
        return None, f"markitdown not installed ({e})"
    try:
        if _converter is None:
            _converter = MarkItDown(enable_plugins=False)
        result = _converter.convert_stream(io.BytesIO(html.encode("utf-8")),
                                           stream_info=StreamInfo(extension=".html", mimetype="text/html",
                                                                  charset="utf-8"))
    except Exception as e:  # noqa: BLE001 - any converter failure falls back to plain text, named
        return None, f"markitdown failed: {type(e).__name__}: {e}"
    text = (result.text_content or "").strip()
    if not text:
        return None, "markitdown returned no text"
    return text, "markitdown"


def file_to_markdown(path) -> tuple[str | None, str]:
    """A local Word, PowerPoint, Excel, EPUB or Outlook file as Markdown (the Drive step, 2026-10-05):
    (markdown, "markitdown") or (None, why it could not convert). A local file only, never a URL."""
    global _converter
    try:
        from markitdown import MarkItDown
    except ImportError as e:
        return None, f"markitdown not installed ({e})"
    try:
        if _converter is None:
            _converter = MarkItDown(enable_plugins=False)
        result = _converter.convert_local(str(path))
    except Exception as e:  # noqa: BLE001 - any converter failure is reported, never raised
        return None, f"markitdown failed: {type(e).__name__}: {e}"
    text = (result.text_content or "").strip()
    return (text, "markitdown") if text else (None, "markitdown returned no text")
