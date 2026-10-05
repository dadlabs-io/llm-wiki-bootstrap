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
import json
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

# 6. Instagram posts: a fake post served over local http (no network), shaped like the logged-out page.
import base64  # noqa: E402
import http.server  # noqa: E402
import threading  # noqa: E402

check("an Instagram post URL is a post", fp.instagram_kind("https://www.instagram.com/p/Dc0qnosovjl/?stkn=x") == "post")
check("... also with the account in the path", fp.instagram_kind("https://www.instagram.com/genai.works/p/Dc0q/") == "post")
check("a reel is a reel", fp.instagram_kind("https://www.instagram.com/reel/DeCVll9BBzC/") == "reel")
check("another site is neither", fp.instagram_kind("https://example.org/p/x/") is None)
check("share trackers are stripped", fp.canonical_instagram(
    "https://www.instagram.com/p/X/?img_index=3&stkn=abc&igsh=q") == "https://www.instagram.com/p/X/")
og = fp.parse_og_description('534 likes, 2 comments - genai.works on September 3, 2026: "Line one\n\nLine two #ai". ')
check("og:description gives author, date and the whole caption",
      og == {"author": "genai.works", "posted": "September 3, 2026", "caption": "Line one\n\nLine two #ai"}, og)
check("slide text is the quoted part of the description, without direction marks", fp.slide_text(
    "Photo by A on May 1. May be an image of ‎text that says '‎Step 1: Do it‎'‎.") == "Step 1: Do it")
check("a description with no text says to read the image",
      "Read the image" in fp.slide_text("Photo by A on May 1. May be an image of magazine and text."))

PNG = base64.b64decode("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYAAAAAYAAjCB0C8AAAAASUVORK5CYII=")
SLIDES = [f"Photo by Acme on September 03, 2026. May be an image of text that says 'Slide {i} says hello'." for i in range(1, 5)]
POST = """<!doctype html><html><head><title>Instagram</title>
<meta property="og:title" content="Acme on Instagram: &quot;Build agents&quot;">
<meta property="og:description" content="10 likes, 1 comments - acme.ai on September 3, 2026: &quot;Build agents in 4 steps.&#10;&#10;Swipe for the steps.&quot;. ">
</head><body><main>
<div class="post"><img alt="acme.ai's profile picture" src="/img/pp.png"><ul id="c"></ul>
<button aria-label="Next" id="next">next</button><time datetime="2026-09-03T11:07:09.000Z">Sep 3</time>
<div class="comments"><span>bob</span><span>COMMENT TEXT MUST NOT APPEAR</span></div></div>
<h2>More posts from <a href="/acme.ai/">acme.ai</a></h2>
<div class="grid"><ul><li><img alt="Photo by Acme on October 05, 2026. GRID IMAGE" src="/img/grid.png"></li></ul></div>
</main><script>
const S = %s; let shown = 0;
function add() { const li = document.createElement('li'); const im = document.createElement('img');
  im.alt = S[shown]; im.src = '/img/s' + (shown + 1) + '.png'; li.appendChild(im);
  document.getElementById('c').appendChild(li); shown++;
  if (shown >= S.length) document.getElementById('next').style.display = 'none'; }
add(); add();
document.getElementById('next').onclick = () => { if (shown < S.length) add(); };
</script></body></html>""" % json.dumps(SLIDES)


class Handler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        body, ctype = (PNG, "image/png") if self.path.startswith("/img/") else (POST.encode("utf-8"), "text/html")
        self.send_response(200)
        self.send_header("Content-Type", ctype)
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *a):
        pass


srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Handler)
threading.Thread(target=srv.serve_forever, daemon=True).start()
base = f"http://127.0.0.1:{srv.server_address[1]}"
with tempfile.TemporaryDirectory() as td:
    tmp = Path(td)
    os.environ["WIKI_PAGE_FETCH_LOCK_DIR"] = str(tmp / "locks")
    (tmp / "nb" / "wiki").mkdir(parents=True)
    code, out, err = run(["--topic", "nb", "--vault", str(tmp), "--mode", "instagram",
                          "--url", f"{base}/p/ABC/?stkn=x&img_index=2"])
    raws = list((tmp / "nb" / "raw").glob("*.md"))
    check("an Instagram post is captured (exit 0, raw_path=)", code == 0 and len(raws) == 1, (code, err[-400:]))
    if raws:
        text = raws[0].read_text(encoding="utf-8")
        h = header(raws[0])
        check("every slide, in order, clicked through past the two loaded at first",
              [f"Slide {i} says hello" in text for i in range(1, 5)] == [True] * 4 and h.get("slides") == 4
              and text.index("Slide 1 says") < text.index("Slide 4 says"), h)
        check("the grid below (other posts) is not taken as a slide", "GRID IMAGE" not in text)
        check("the comments are left out", "COMMENT TEXT" not in text)
        check("the whole caption from og:description, author and date in the header",
              "Build agents in 4 steps.\n\nSwipe for the steps." in text and h.get("author") == "acme.ai"
              and h.get("type") == "instagram-post" and str(h.get("posted", "")).startswith("2026-09-03"), h)
        check("the trackers are stripped from source_url", h.get("source_url") == f"{base}/p/ABC/", h.get("source_url"))
        imgs = sorted((tmp / "nb" / "raw").glob("*-slides/slide-*.jpg"))
        check("each slide image is saved beside the raw and named in it",
              len(imgs) == 4 and all(f"{imgs[0].parent.name}/{p.name}" in text for p in imgs), [p.name for p in imgs])
    code, out, err = run(["--topic", "nb", "--vault", str(tmp), "--url", "https://www.instagram.com/reel/DeCVll9BBzC/"])
    check("a reel is refused with a pointer to wiki-transcribe.py", code == 2 and "wiki-transcribe.py" in err, (code, err))
srv.shutdown()

failed = [n for ok, n in results if not ok]
for ok, n in results:
    print(("PASS " if ok else "FAIL ") + n)
print(f"\n{len(results) - len(failed)}/{len(results)} passed")
sys.exit(1 if failed else 0)
