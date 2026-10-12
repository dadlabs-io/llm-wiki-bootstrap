#!/usr/bin/env python3
"""Checks for wiki-feeds.py and _feeds.py (task #97: /wiki-discover reads trusted sources by feed). Never shipped. No
network: the fetch is replaced by saved samples (RSS 2.0, RSS 1.0, Atom, JSON Feed 1.0 and 1.1, a YouTube feed and a
yt-dlp listing), shaped on real feeds read 2026-10-11.

    uv run python tests/scripts/test_feeds.py    # exit 0 = every check passed
"""
from __future__ import annotations

import contextlib
import importlib.util
import io
import json
import sys
import tempfile
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

import _feeds as feeds  # noqa: E402

spec = importlib.util.spec_from_file_location("wiki_feeds", ROOT / "scripts" / "wiki-feeds.py")
wf = importlib.util.module_from_spec(spec)
spec.loader.exec_module(wf)

results: list[tuple[bool, str]] = []


def check(name: str, ok: bool, detail: object = ""):
    results.append((bool(ok), name + (f"  [{detail}]" if not ok and detail != "" else "")))


RSS2 = b"""<?xml version="1.0"?><rss version="2.0"><channel><title>Hamel</title>
<item><title>Evals in practice</title><link>https://hamel.dev/blog/posts/evals-practice/</link>
<guid>https://hamel.dev/blog/posts/evals-practice/</guid><pubDate>Wed, 30 Sep 2026 07:00:00 GMT</pubDate></item>
<item><title>An old post</title><link>https://hamel.dev/blog/posts/old/</link>
<guid>https://hamel.dev/blog/posts/old/</guid><pubDate>Mon, 01 Jun 2026 07:00:00 GMT</pubDate></item>
<item><title>Before the floor</title><link>https://hamel.dev/blog/posts/2025/</link>
<guid>https://hamel.dev/blog/posts/2025/</guid><pubDate>Mon, 01 Dec 2025 07:00:00 GMT</pubDate></item>
</channel></rss>"""
RDF = b"""<?xml version="1.0"?><rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#"
 xmlns="http://purl.org/rss/1.0/" xmlns:dc="http://purl.org/dc/elements/1.1/">
<channel rdf:about="https://example.org/"><title>Ex</title></channel>
<item rdf:about="https://example.org/a"><title>Post A</title><link>https://example.org/a</link>
<dc:date>2026-10-01T10:00:00Z</dc:date><dc:creator>Ann</dc:creator></item>
<item rdf:about="https://example.org/b"><title>Post B</title><link>https://example.org/b</link>
<dc:date>2026-10-02T10:00:00Z</dc:date></item></rdf:RDF>"""
ATOM = b"""<?xml version="1.0"?><feed xmlns="http://www.w3.org/2005/Atom"><title>releases</title>
<entry><id>tag:github.com,2008:Repository/1/v0.30.0</id><title>v0.30.0</title>
<link rel="alternate" href="https://github.com/getzep/graphiti/releases/tag/v0.30.0"/>
<updated>2026-10-05T20:38:41Z</updated><author><name>danielchalef</name></author></entry>
<entry><id>tag:github.com,2008:Repository/1/v0.29.0</id><title>v0.29.0</title>
<link rel="alternate" href="https://github.com/getzep/graphiti/releases/tag/v0.29.0"/>
<updated>2026-09-08T20:38:41Z</updated></entry></feed>"""
JSON10 = json.dumps({"version": "https://jsonfeed.org/version/1", "items": [
    {"id": "j1", "url": "https://example.net/j1", "title": "J1", "author": {"name": "Cy"},
     "date_published": "2026-10-04T00:00:00Z"}]}).encode()
JSON11 = json.dumps({"version": "https://jsonfeed.org/version/1.1", "items": [
    {"id": "j2", "url": "https://example.net/j2", "title": "J2", "authors": [{"name": "Bo"}, {"name": "Di"}],
     "date_published": "2026-10-05T00:00:00Z"}]}).encode()
YT_FEED = b"""<?xml version="1.0"?><feed xmlns="http://www.w3.org/2005/Atom" xmlns:yt="http://www.youtube.com/xml/schemas/2015">
<entry><id>yt:video:AAAAAAAAAAA</id><title>A new talk</title>
<link rel="alternate" href="https://www.youtube.com/watch?v=AAAAAAAAAAA"/><published>2026-10-08T12:00:00+00:00</published></entry>
</feed>"""
YTDLP = json.dumps({"channel": "Cole Medin", "entries": [{"id": "cWjS56edaUA", "title": "Agentic Apps"},
                                                         {"id": "Cl3OWig5hkk", "title": "Jev use cases"}]})
CHANNEL = "UCMwVTLZIRRUyyVrkjDpn4pA"

# ── the parser ──
r2 = feeds.parse(RSS2)
check("RSS 2.0: three items with links, titles and UTC dates",
      len(r2) == 3 and r2[0].title == "Evals in practice" and r2[0].published == "2026-09-30T07:00:00+00:00", r2)
rd = feeds.parse(RDF)
check("RSS 1.0 (RDF): items beside the channel are found (Chubby's parser found none)",
      [i.title for i in rd] == ["Post A", "Post B"], rd)
check("RSS 1.0: dc:creator and dc:date are read", rd and rd[0].author == "Ann" and rd[0].published.startswith("2026-10-01"))
check("RSS 1.0: rdf:about is the item's id", rd and rd[0].id == "https://example.org/a")
at = feeds.parse(ATOM)
check("Atom: the alternate link, the author, and updated when no published",
      at and at[0].url.endswith("v0.30.0") and at[0].author == "danielchalef" and at[0].published.startswith("2026-10-05"), at)
j10, j11 = feeds.parse(JSON10), feeds.parse(JSON11)
check("JSON Feed 1.0: the author object gives its name (Chubby printed the dict)", j10 and j10[0].author == "Cy", j10)
check("JSON Feed 1.1: the authors list gives every name", j11 and j11[0].author == "Bo, Di", j11)
for bad, code in ((b"<!DOCTYPE html><html><body>hi</body></html>", "parse"), (b"{\"no\": 1}", "parse"),
                  (b"<opml/>", "parse")):
    try:
        feeds.parse(bad)
        check(f"not a feed is refused: {bad[:20]!r}", False)
    except feeds.FeedError as exc:
        check(f"not a feed is refused with code {code}: {bad[:20]!r}", exc.code == code, exc.code)
check("an item key is stable and the same for the same id", feeds.item_key(rd[0]) == feeds.item_key(feeds.parse(RDF)[0]))
check("an item with no id is keyed by its link's source key (x.com and twitter.com alike)",
      feeds.item_key(feeds.Item("", "https://x.com/a/status/1", "t", "", ""))
      == feeds.item_key(feeds.Item("", "https://twitter.com/a/status/1?s=20", "u", "", "")))

# ── arXiv asks for one request every 3 seconds: two calls are spaced, other hosts are not ──
import time  # noqa: E402
feeds._last_call.clear()
t0 = time.monotonic()
feeds._pace("https://export.arxiv.org/api/query?a")
feeds._pace("https://example.org/feed")
t1 = time.monotonic()
feeds._pace("https://export.arxiv.org/api/query?b")
check("arXiv calls are spaced 3 s apart; another host is not held up",
      t1 - t0 < 0.5 and time.monotonic() - t0 >= 2.9, round(time.monotonic() - t0, 2))

# ── a gzip body sent without being asked for (DeepMind, 2026-10-11) is unpacked ──
import gzip  # noqa: E402
check("a gzipped feed body is unpacked before parsing",
      [i.title for i in feeds.parse(feeds._gunzip(gzip.compress(RSS2), feeds.MAX_BODY_BYTES))][:1] == ["Evals in practice"])
check("a plain body is left as it is", feeds._gunzip(RSS2, feeds.MAX_BODY_BYTES) == RSS2)
try:
    feeds._gunzip(gzip.compress(b"x" * 5000), 1000)
    check("a gzip body over the size cap once unpacked is refused", False)
except feeds.FeedError as exc:
    check("a gzip body over the size cap once unpacked is refused", exc.code == "body_too_large", exc.code)

# ── YouTube: the feed first, the yt-dlp listing when it fails ──
real_fetch = feeds.fetch
feeds.fetch = lambda url, **k: feeds.Fetched(200, YT_FEED, "", "")
got, items, how = feeds.youtube_items(CHANNEL)
check("YouTube: the channel feed is used when it answers (dated items)", how == "feed" and items[0].published, how)
feeds.fetch = lambda url, **k: (_ for _ in ()).throw(feeds.FeedError("http_404", "gone"))
calls = []
runner = lambda cmd, **k: calls.append(cmd) or SimpleNamespace(returncode=0, stdout=YTDLP, stderr="")
got, items, how = feeds.youtube_items(CHANNEL, runner=runner)
check("YouTube: a failing feed falls back to the yt-dlp listing", how.startswith("yt-dlp") and len(items) == 2, how)
check("... with no cookies and no login in the yt-dlp call",
      calls and not any("cookie" in a.lower() for a in calls[0]), calls)
check("... ids keyed like the feed's (yt:video:<id>), undated",
      items and items[0].id == "yt:video:cWjS56edaUA" and items[0].published == "")
feeds.fetch = real_fetch

# ── feeds.md ──
FEEDS_MD = """# Discovery Feeds — nb

## Blogs & Newsletters

| Author | URL / Search Pattern | Feed | Tier | From | To | Topics | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- |
| **Hamel Husain** | `hamel.dev/blog/` | `https://hamel.dev/index.xml` | 3 | 2026-01-01 | 2026-09-14 | evals | x |
| **Anthropic Blog** | `anthropic.com/research` | — | 1-2 | 2026-01-01 | 2026-09-23 | agents | no feed |
| **Example RDF** | `example.org` | https://example.org/rdf | 3 | 2026-01-01 | — | x | x |
| **Hamel again** | `hamel.dev` | https://hamel.dev/index.xml | 3 | 2026-01-01 | 2026-09-14 | x | two rows, one feed |

## YouTube Channels

| Creator | Channel | Feed | Tier | From | To | Topics | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- |
| **Cole Medin** | `youtube.com/@ColeMedin` | `youtube:UCMwVTLZIRRUyyVrkjDpn4pA` | 3 | 2026-01-01 | 2026-09-14 | x | x |

## GitHub Repos & Projects

| Project | URL | Feed | Tier | From | To | What to watch | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- |
| **Graphiti** | `github.com/getzep/graphiti` | https://github.com/getzep/graphiti/releases.atom | 2 | 2026-03-14 | 2026-09-14 | x | x |
| **Broken** | `example.com` | https://broken.example.com/feed | 2 | 2026-03-14 | 2026-09-14 | x | x |
"""
OLD_MD = """## Blogs

| Author | URL / Search Pattern | Tier | From | To | Topics | Notes |
| --- | --- | --- | --- | --- | --- | --- |
| **Simon Willison** | `simonwillison.net` | 3 | 2026-01-01 | 2026-09-23 | agents | x |
"""

SAMPLES = {"https://hamel.dev/index.xml": RSS2, "https://example.org/rdf": RDF,
           "https://github.com/getzep/graphiti/releases.atom": ATOM}
fetch_log: list[tuple[str, str]] = []


def fake_fetch(url, *, etag="", last_modified="", **k):
    fetch_log.append((url, etag))
    if url.startswith("https://www.youtube.com/feeds/"):
        raise feeds.FeedError("http_500", "Internal Server Error")
    if url not in SAMPLES:
        raise feeds.FeedError("http_404", "the feed returned HTTP 404")
    tag = f"e-{url}-{len(SAMPLES[url])}"  # changes when the content does, like a real ETag
    if etag == tag:
        return feeds.Fetched(304, b"", etag, last_modified, not_modified=True)
    return feeds.Fetched(200, SAMPLES[url], tag, "")


feeds.fetch = fake_fetch
real_listing = feeds.youtube_listing
feeds.youtube_listing = lambda channel, runner=None: real_listing(
    channel, runner=lambda cmd, **k: SimpleNamespace(returncode=0, stdout=YTDLP, stderr=""))


def run(*argv):
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = wf.main(list(argv))
    return code, out.getvalue(), err.getvalue()


with tempfile.TemporaryDirectory() as td:
    vault = Path(td)
    nb = vault / "nb"
    (nb / "_config").mkdir(parents=True)
    (nb / "wiki" / "research").mkdir(parents=True)
    (nb / "_config" / "feeds.md").write_text(FEEDS_MD, encoding="utf-8")
    V = ("--vault", str(vault), "--topic", "nb")

    rows = wf.read_sources(nb / "_config" / "feeds.md")
    check("feeds.md: every row read, names without the bold", [r["name"] for r in rows] ==
          ["Hamel Husain", "Anthropic Blog", "Example RDF", "Hamel again", "Cole Medin", "Graphiti", "Broken"], rows)
    check("feeds.md: the Feed column, backticks stripped; — means web search",
          rows[0]["feed"] == "https://hamel.dev/index.xml" and rows[1]["feed"] == "", rows[:2])
    check("feeds.md: To and Tier read per row", rows[0]["to"] == "2026-09-14" and rows[5]["tier"] == "2", rows)
    (nb / "_config" / "old.md").write_text(OLD_MD, encoding="utf-8")
    old = wf.read_sources(nb / "_config" / "old.md")
    check("feeds.md without a Feed column: every row stays on web search", old and not old[0]["feed"], old)

    # The wiki already holds the RDF feed's Post B, in another link form; an intake ticket holds the Graphiti v0.30.0.
    (nb / "wiki" / "research" / "post-b.md").write_text(
        "---\ntitle: Post B\nsource_url: https://www.example.org/b/?utm_source=x\n---\n\nbody\n", encoding="utf-8")
    (nb / "_inbox" / "intake" / "llm-wiki").mkdir(parents=True)
    (nb / "_inbox" / "intake" / "llm-wiki" / "graphiti.md").write_text(
        "---\nsource: https://github.com/getzep/graphiti/releases/tag/v0.30.0\ntitle: g\n---\n", encoding="utf-8")

    # ── first read ──
    fetch_log.clear()
    code, out, err = run(*V, "check", "--json")
    data = json.loads(out) if out.strip().startswith("{") else {}
    by = {s["name"]: s for s in data.get("sources", [])}
    check("check: exit 1 when one source fails, the others still read", code == 1 and len(by) == 5, (code, err[-300:]))
    check("check: the failing source is named with its reason", "http_404" in by.get("Broken", {}).get("error", ""),
          by.get("Broken"))
    check("check: sources without a feed are listed for web search", data.get("web_search") == ["Anthropic Blog"], data)
    check("two rows naming one feed are read once, under both names", "Hamel Husain / Hamel again" in by
          and sum(1 for u, e in fetch_log if u == "https://hamel.dev/index.xml") == 1, list(by))
    by = {k.split(" / ")[0]: v for k, v in by.items()}
    hamel = by.get("Hamel Husain", {})
    check("first read with To 2026-09-14: only the item on or after it is new", [i["title"] for i in hamel.get("new", [])]
          == ["Evals in practice"], hamel)
    check("... and the status says it is a first read", hamel.get("status", "").startswith("first read"), hamel)
    rdf = by.get("Example RDF", {})
    check("first read with no To date: a baseline, nothing shown", rdf.get("new") == [] and "baseline" in rdf.get("status", ""),
          rdf)
    yt = by.get("Cole Medin", {})
    check("YouTube on first read: the listing is undated, so all of it is the baseline",
          yt.get("new") == [] and yt.get("how", "").startswith("yt-dlp"), yt)
    gr = by.get("Graphiti", {})
    check("an item already waiting in an intake bucket is not new (counted as held)",
          gr.get("new") == [] and gr.get("held") == 1, gr)
    state = json.loads((nb / "_config" / "feed-state.json").read_text(encoding="utf-8"))
    check("state: written to _config/feed-state.json, keyed by feed", "https://hamel.dev/index.xml" in state["feeds"], state)
    check("state: the shown item is pending, not seen",
          len(state["feeds"]["https://hamel.dev/index.xml"].get("pending", {})) == 1)

    # ── second read: nothing marked seen yet, so the same item comes back; the feed is unchanged (304) ──
    del SAMPLES["https://example.org/rdf"]
    SAMPLES["https://example.org/rdf"] = RDF.replace(b"Post B", b"Post B").replace(
        b"</rdf:RDF>", b'<item rdf:about="https://example.org/c"><title>Post C</title><link>https://example.org/c</link>'
                       b"<dc:date>2026-10-09T10:00:00Z</dc:date></item></rdf:RDF>")
    fetch_log.clear()
    code, out, err = run(*V, "check", "--json")
    by = {s["name"].split(" / ")[0]: s for s in json.loads(out)["sources"]}
    check("second read sends the ETag; an unchanged feed (304) is read as unchanged",
          any(u == "https://hamel.dev/index.xml" and e.startswith("e-") for u, e in fetch_log)
          and "unchanged" in by["Hamel Husain"]["how"], by["Hamel Husain"])
    check("an unchanged feed keeps its pending item: still to put on a checklist",
          json.loads((nb / "_config" / "feed-state.json").read_text())["feeds"]["https://hamel.dev/index.xml"]["pending"],
          "pending emptied by a 304")
    check("after the baseline, a new item in the feed is new", [i["title"] for i in by["Example RDF"]["new"]] == ["Post C"],
          by["Example RDF"])

    # ── mark-seen from a checklist: only what the checklist lists ──
    checklist = nb / "_inbox" / "discovered" / "2026-10-11-discovery.md"
    checklist.parent.mkdir(parents=True)
    checklist.write_text("# Discovery\n\n- [ ] [Post C](https://example.org/c) — tier 3\n", encoding="utf-8")
    code, out, err = run(*V, "mark-seen", "--checklist", str(checklist))
    check("mark-seen: marks the listed item and says how many still wait", code == 0 and "marked seen: 1" in out, out)
    code, out, err = run(*V, "check", "--json")
    by = {s["name"].split(" / ")[0]: s for s in json.loads(out)["sources"]}
    check("a marked item is not shown again", by["Example RDF"]["new"] == [], by["Example RDF"])
    check("an item no checklist listed comes back (the 20-limit rule)",
          [i["title"] for i in by["Hamel Husain"]["new"]] == ["Evals in practice"], by["Hamel Husain"])

    # ── a changed feed URL starts fresh ──
    (nb / "_config" / "feeds.md").write_text(FEEDS_MD.replace("https://example.org/rdf", "https://example.org/rdf2"),
                                              encoding="utf-8")
    SAMPLES["https://example.org/rdf2"] = SAMPLES["https://example.org/rdf"]
    code, out, err = run(*V, "check", "--json", "--feed", "rdf")
    by = {s["name"].split(" / ")[0]: s for s in json.loads(out)["sources"]}
    check("--feed reads only the matching source", list(by) == ["Example RDF"], list(by))
    check("a changed feed URL is a first read again (baseline, nothing shown)",
          by["Example RDF"]["new"] == [] and "first read" in by["Example RDF"]["status"], by["Example RDF"])

    # ── known ──
    code, out, err = run(*V, "known", "https://example.org/b", "https://x.com/someone/status/42",
                         "https://github.com/getzep/graphiti/releases/tag/v0.30.0")
    lines = out.splitlines()
    check("known: a link the wiki holds in another form is held, with where",
          lines and lines[0].startswith("held wiki/"), lines)
    check("known: an unknown link is new", len(lines) > 1 and lines[1].startswith("new "), lines)
    check("known: an intake ticket counts as held (the queue's own check misses intake)",
          len(lines) > 2 and lines[2].startswith("held intake/llm-wiki/"), lines)

    # ── bad input ──
    code, out, err = run(*V, "check", "--feed", "nothing-like-this")
    check("--feed with no match: exit 2, said", code == 2 and "no source" in err, (code, err))
    (nb / "_config" / "feeds.md").unlink()
    code, out, err = run(*V, "check")
    check("no feeds.md: exit 2, said", code == 2 and "trusted-sources page" in err, (code, err))

feeds.fetch = real_fetch
failed = [n for ok, n in results if not ok]
for ok, n in results:
    print(("PASS " if ok else "FAIL ") + n)
print(f"\n{len(results) - len(failed)}/{len(results)} passed")
sys.exit(1 if failed else 0)
