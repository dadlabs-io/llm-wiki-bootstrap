#!/usr/bin/env python3
"""HTML pages are saved as Markdown (task #71, 2026-10-04): `_markdown.html_to_markdown` and
`wiki-update.py`'s fetch step, with MarkItDown and with it unavailable (the plain-text fallback, named).

    uv run python tests/scripts/test_html_markdown.py    # exit 0 = every check passed

No network: the fetch is stubbed.
"""
from __future__ import annotations

import contextlib
import importlib.util
import io
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
import _markdown  # noqa: E402

for stream in (sys.stdout, sys.stderr):
    if hasattr(stream, "reconfigure"):
        stream.reconfigure(encoding="utf-8", errors="replace")

results: list[tuple[bool, str]] = []


def check(name: str, ok: bool, detail: object = ""):
    results.append((bool(ok), name + (f"  [{str(detail)[:300]}]" if not ok and detail != "" else "")))


PAGE = """<!doctype html><html><head><title>Building effective agents \\ Example</title>
<style>body{color:red}</style><script>var x = 1;</script></head><body>
<nav><a href="/news">News</a></nav>
<h1>Building effective agents</h1>
<p>We&#x27;ve worked with dozens of teams &amp; learned that <a href="https://example.com/simple">simple patterns</a> win.</p>
<h2>What are agents?</h2>
<ul><li>Workflows follow a fixed path</li><li>Agents choose their own steps</li></ul>
<blockquote>Start simple.</blockquote>
</body></html>"""


def load_wiki_update():
    spec = importlib.util.spec_from_file_location("wiki_update_mod", ROOT / "scripts" / "wiki-update.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@contextlib.contextmanager
def markitdown_blocked():
    """Make `from markitdown import …` fail, as on a machine whose environment lacks it."""
    saved = {k: v for k, v in sys.modules.items() if k == "markitdown" or k.startswith("markitdown.")}
    for k in saved:
        del sys.modules[k]
    sys.modules["markitdown"] = None  # an import of a None entry raises ImportError
    _markdown._converter = None
    try:
        yield
    finally:
        del sys.modules["markitdown"]
        sys.modules.update(saved)
        _markdown._converter = None


# the helper
md, how = _markdown.html_to_markdown(PAGE)
check("markitdown converts the page", md is not None and how == "markitdown", how)
md = md or ""
check("headings are kept as Markdown headings", "# Building effective agents" in md and "## What are agents?" in md, md)
check("links are kept with their address", "[simple patterns](https://example.com/simple)" in md, md)
check("list items are kept", "Workflows follow a fixed path" in md and any(
    line.lstrip().startswith(("-", "*")) and "Agents choose" in line for line in md.splitlines()), md)
check("entities are decoded (no &#x27; or &amp; left)", "We've" in md and "&#x27;" not in md and "&amp;" not in md, md)
check("scripts and styles are dropped", "var x" not in md and "color:red" not in md, md)
with markitdown_blocked():
    none, why = _markdown.html_to_markdown(PAGE)
check("without markitdown: None and the reason", none is None and "not installed" in why, why)

# wiki-update.py's fetch step (acquire_source), the network stubbed
wu = load_wiki_update()
wu.fetch_url = lambda url: (PAGE, "text/html; charset=utf-8")
with tempfile.TemporaryDirectory() as td:
    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        raw_path, body, title, _ = wu.acquire_source("https://example.com/agents", Path(td) / "raw", None)
    saved = Path(raw_path).read_text(encoding="utf-8")
    check("the saved raw is Markdown with its links", "[simple patterns](https://example.com/simple)" in saved
          and "# Building effective agents" in saved, saved[:400])
    check("the raw keeps its source header", saved.startswith("---\nsource_url: https://example.com/agents\n"), saved[:120])
    check("the fetch says it converted to Markdown", "Converted: Markdown" in out.getvalue(), out.getvalue())
    check("the title still comes from <title>", title == "Building effective agents \\ Example", title)

    out = io.StringIO()
    with markitdown_blocked(), contextlib.redirect_stdout(out):
        raw_path, body, title, _ = wu.acquire_source("https://example.com/agents-2", Path(td) / "raw", None)
    saved = Path(raw_path).read_text(encoding="utf-8")
    check("without markitdown the raw is plain text, as before", "Building effective agents" in saved
          and "](" not in saved, saved[:300])
    check("... and the fetch says so, with the reason", "Converted: plain text" in out.getvalue()
          and "not installed" in out.getvalue(), out.getvalue())

failed = [n for ok, n in results if not ok]
for ok, n in results:
    print(("PASS " if ok else "FAIL ") + n)
print(f"\n{len(results) - len(failed)}/{len(results)} passed")
sys.exit(1 if failed else 0)
