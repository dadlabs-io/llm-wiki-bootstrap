#!/usr/bin/env python3
"""Checks for wiki-fetch-page.py (the page fetcher on this machine, 2026-10-05; it replaced the Node one
that ran only in the openclaw container). Never shipped. Runs the real headless Chromium on local
test pages (file:// URLs), so no network: a page whose text only appears once JavaScript runs, a
paywall stub, a site-name title. Needs `playwright install chromium` done (the global install does it).

    uv run python tests/scripts/test_fetch_page.py    # exit 0 = every check passed
"""
from __future__ import annotations

import contextlib
import importlib.util
import io
import os
import sys
import tempfile
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

results: list[tuple[bool, str]] = []


def check(name: str, ok: bool, detail: object = ""):
    results.append((bool(ok), name + (f"  [{detail}]" if not ok and detail != "" else "")))


spec = importlib.util.spec_from_file_location("wiki_fetch_page", ROOT / "scripts" / "wiki-fetch-page.py")
fp = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fp)

ARTICLE = " ".join(["Agents keep state in files so a later run can pick up where the last one stopped."] * 20)
JS_PAGE = f"""<!doctype html><html><head><title>Threads</title>
<meta property="og:title" content="someone on Threads: agents and state">
<meta name="description" content="A post about state"></head>
<body><div id="app"></div><script>
document.getElementById('app').innerHTML =
  '<h2>Why state matters</h2><p>{ARTICLE}</p><p>See <a href="https://example.org/raft">the Raft paper</a>.</p>';
</script></body></html>"""
PAYWALL_PAGE = """<!doctype html><html><head><title>A long enough title for a news article</title></head>
<body><h1>Big story</h1><p>The first paragraph of the story.</p><p>Subscribe to continue reading.</p></body></html>"""


def run(argv):
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = fp.main(argv)
    return code, out.getvalue(), err.getvalue()


def header(raw: Path) -> dict:
    return yaml.safe_load(raw.read_text(encoding="utf-8").split("---")[1])


# Pure rules first.
check("a site-name title gives way to og:title", fp.pick_title("Threads", "someone on Threads: x") == "someone on Threads: x")
check("a real title is kept", fp.pick_title("Context engineering for agents", "og") == "Context engineering for agents")
check("no og:title: the page title stays", fp.pick_title("Instagram", None) == "Instagram")
check("a short page reads as paywalled", fp.looks_paywalled("Sign in"))
check("a marker reads as paywalled", fp.looks_paywalled(ARTICLE + " Subscribe to continue reading"))
check("a full article does not", not fp.looks_paywalled(ARTICLE))

with tempfile.TemporaryDirectory() as td:
    tmp = Path(td)
    os.environ["WIKI_PAGE_FETCH_LOCK_DIR"] = str(tmp / "locks")
    (tmp / "nb" / "wiki").mkdir(parents=True)
    js, pw = tmp / "js.html", tmp / "paywall.html"
    js.write_text(JS_PAGE, encoding="utf-8")
    pw.write_text(PAYWALL_PAGE, encoding="utf-8")

    # 1. A page rendered by JavaScript: the text is there, as Markdown, under og:title.
    code, out, err = run(["--topic", "nb", "--vault", str(tmp), "--url", js.as_uri(), "--ingested-by", "claude-code"])
    raws = list((tmp / "nb" / "raw").glob("*.md"))
    check("a JavaScript-rendered page is saved (exit 0, raw_path=)", code == 0 and len(raws) == 1 and "raw_path=" in out,
          (code, err[-300:]))
    if raws:
        text = raws[0].read_text(encoding="utf-8")
        h = header(raws[0])
        check("the text the script inserted is in the raw", "Agents keep state in files" in text)
        check("... as Markdown: the heading and the link kept",
              "## Why state matters" in text and "[the Raft paper](https://example.org/raft)" in text, text[:600])
        check("the header parses, says Markdown, and takes og:title over the site name",
              h.get("converted") == "markdown" and h.get("title") == "someone on Threads: agents and state"
              and h.get("fetched_via") == "playwright-chromium" and h.get("meta_description") == "A post about state", h)
        check("a full page is not flagged as paywalled", "paywall" not in h and "paywall=suspected" not in out)
        check("the file is named from the og:title", "someone-on-threads" in raws[0].name, raws[0].name)

    # 2. A paywall stub: flagged, kept as fetched, never fetched another way.
    code, out, err = run(["--topic", "nb", "--vault", str(tmp), "--url", pw.as_uri()])
    raw = max((tmp / "nb" / "raw").glob("*big-story*.md"), default=None) or \
        max((tmp / "nb" / "raw").glob("*.md"), key=lambda p: p.stat().st_mtime)
    h = header(raw)
    check("a paywall stub is saved and flagged (paywall=suspected, a paywall: line)",
          code == 0 and "paywall=suspected" in out and "user's signed-in browser" in h.get("paywall", ""), (code, h))
    check("... with nothing fetched from elsewhere", "archive" not in raw.read_text(encoding="utf-8").lower())

    # 3. No such notebook.
    code, out, err = run(["--topic", "nope", "--vault", str(tmp), "--url", js.as_uri()])
    check("an unknown notebook is exit 2", code == 2 and "not found" in err, (code, err))

    # 4. Chromium missing: exit 3 naming the command.
    real_render = fp.render
    fp.render = lambda *a, **k: (_ for _ in ()).throw(RuntimeError(
        "BrowserType.launch: Executable doesn't exist at C:\\x\\chrome.exe ... run playwright install"))
    code, out, err = run(["--topic", "nb", "--vault", str(tmp), "--url", js.as_uri()])
    check("Chromium not installed: exit 3, naming `playwright install chromium`",
          code == 3 and "playwright install chromium" in err, (code, err))
    fp.render = lambda *a, **k: (_ for _ in ()).throw(RuntimeError("net::ERR_NAME_NOT_RESOLVED"))
    code, out, err = run(["--topic", "nb", "--vault", str(tmp), "--url", "https://nowhere.invalid/"])
    check("a page that cannot be reached: exit 1, the reason named", code == 1 and "ERR_NAME_NOT_RESOLVED" in err,
          (code, err))
    fp.render = real_render

    # 5. At most two at once: with both slots held, a third caller gets none (exit 5).
    held = [fp.acquire_fetch_slot(1), fp.acquire_fetch_slot(1)]
    check("two fetch slots can be held", all(held))
    check("a third finds none", fp.acquire_fetch_slot(max_wait=1) is None)
    real_acquire = fp.acquire_fetch_slot
    fp.acquire_fetch_slot = lambda *a, **k: None
    code, out, err = run(["--topic", "nb", "--vault", str(tmp), "--url", js.as_uri()])
    check("no slot free in time: exit 5", code == 5, (code, err))
    fp.acquire_fetch_slot = real_acquire
    for s in held:
        s.release()
    check("a released slot can be taken again", (s := fp.acquire_fetch_slot(1)) is not None)
    if s:
        s.release()

failed = [n for ok, n in results if not ok]
for ok, n in results:
    print(("PASS " if ok else "FAIL ") + n)
print(f"\n{len(results) - len(failed)}/{len(results)} passed")
sys.exit(1 if failed else 0)
