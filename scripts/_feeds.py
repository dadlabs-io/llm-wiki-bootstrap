"""
_feeds.py — fetch one public feed and parse it into items: RSS 2.0, RSS 1.0 (RDF), Atom and JSON Feed, plus a
YouTube channel's latest videos. Used by wiki-feeds.py (task #97: /wiki-discover reads trusted sources by feed).

Adapted from Chubby Skills (https://github.com/chubbyguan/chubbyskills, tools/subscription_adapters.py and
tools/subscription_store.py at commit 1b759b1), under the MIT License:

    MIT License
    Copyright (c) 2026 Chubby
    Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated
    documentation files (the "Software"), to deal in the Software without restriction, including without limitation
    the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to
    permit persons to whom the Software is furnished to do so, subject to the following conditions:
    The above copyright notice and this permission notice shall be included in all copies or substantial portions of
    the Software.
    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO
    THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
    AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT,
    TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
    SOFTWARE.

What changed from theirs: an RSS 1.0 (RDF) feed's items sit beside its `channel`, not inside it, so theirs found
none; a JSON Feed author is an object (`{"name": …}`, a list `authors` in 1.1), which theirs printed as a dict; the
User-Agent is the browser one wiki-fetch-page.py sends (OpenAI, Latent Space and DEV refuse a plain script,
2026-10-11); the YouTube fallback lists a channel with yt-dlp and never passes cookies or a login; requests go through
urllib's own HTTPS handler (theirs set an SSL context that offers no ALPN, and KDnuggets answered 403); arXiv's API is
called at most once every 3 seconds, as its terms ask; a gzip body sent unasked (DeepMind) is unpacked. Their scheduler,
SQLite store, executor and site are not taken. `item_key` is their `entry_key` rule, with the link compared by our
shared source key.
"""
from __future__ import annotations

import email.utils
import gzip
import hashlib
import http.client
import io
import ipaddress
import json
import re
import socket
import subprocess
import sys
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _source_identity import source_key  # noqa: E402

USER_AGENT = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
              "Chrome/141.0 Safari/537.36")  # the page fetcher's
ACCEPT = ("application/rss+xml, application/atom+xml, application/feed+json, application/json, text/xml, "
          "application/xml;q=0.9, */*;q=0.1")
MAX_BODY_BYTES = 16 * 1024 * 1024
MAX_REDIRECTS = 3
TIMEOUT = 20
YOUTUBE_LISTING = 15
# Local proxy clients (Clash and the like) answer DNS from this benchmarking range and resolve upstream; every other
# non-public address is refused.
FAKE_IP_NETWORK = ipaddress.ip_network("198.18.0.0/15")
CHANNEL_ID_RE = re.compile(r"UC[A-Za-z0-9_-]{22}")


class FeedError(RuntimeError):
    """A fetch or parse failure with a short machine-readable code (http_404, network, parse, …)."""

    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code


@dataclass(frozen=True)
class Item:
    id: str
    url: str
    title: str
    author: str
    published: str  # ISO-8601 UTC, or "" when the feed gives no date

    def as_dict(self) -> dict:
        return asdict(self)


@dataclass(frozen=True)
class Fetched:
    status: int
    body: bytes
    etag: str
    last_modified: str
    not_modified: bool = False


# ---------- fetching ----------

def _check_public_https(url: str) -> None:
    try:
        parsed = urllib.parse.urlsplit(url)
    except ValueError as exc:
        raise FeedError("invalid_url", f"invalid feed URL: {exc}") from exc
    if parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password:
        raise FeedError("invalid_url", "a feed URL must be public HTTPS without credentials")
    if parsed.port not in (None, 443):
        raise FeedError("invalid_url", "a feed URL may only use HTTPS port 443")
    host = parsed.hostname.rstrip(".").lower()
    if host in ("localhost", "localhost.localdomain") or host.endswith(".local"):
        raise FeedError("unsafe_url", "local feed hosts are not allowed")
    try:
        addresses = socket.getaddrinfo(host, 443, type=socket.SOCK_STREAM)
    except socket.gaierror as exc:
        raise FeedError("network", f"cannot resolve the feed host: {exc}") from exc
    for item in addresses:
        address = ipaddress.ip_address(item[4][0])
        if address not in FAKE_IP_NETWORK and not address.is_global:
            raise FeedError("unsafe_url", "the feed host resolves to a non-public address")


PACED_HOSTS = {"export.arxiv.org": 3.0}  # arXiv's API terms: one request every 3 seconds (a burst got 429s, 2026-10-11)
_pace_lock = threading.Lock()
_last_call: dict[str, float] = {}


def _pace(url: str) -> None:
    """Wait our turn on a host that asks for spacing; one caller at a time per such host."""
    host = (urllib.parse.urlsplit(url).hostname or "").lower()
    gap = PACED_HOSTS.get(host)
    if not gap:
        return
    with _pace_lock:
        wait = _last_call.get(host, 0.0) + gap - time.monotonic()
        if wait > 0:
            time.sleep(wait)
        _last_call[host] = time.monotonic()


def _gunzip(body: bytes, max_bytes: int) -> bytes:
    """A gzip body unpacked: DeepMind's feed arrives gzipped though no Accept-Encoding was sent (2026-10-11)."""
    if body[:2] != b"\x1f\x8b":
        return body
    try:
        with gzip.GzipFile(fileobj=io.BytesIO(body)) as stream:
            out = stream.read(max_bytes + 1)
    except (OSError, EOFError) as exc:
        raise FeedError("parse", f"a gzip body that would not unpack: {exc}") from exc
    if len(out) > max_bytes:
        raise FeedError("body_too_large", f"the feed is over {max_bytes} bytes unpacked")
    return out


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def fetch(url: str, *, etag: str = "", last_modified: str = "", timeout: int = TIMEOUT,
          max_bytes: int = MAX_BODY_BYTES) -> Fetched:
    """One public feed, with conditional headers (a 304 costs nothing) and every redirect checked."""
    # urllib's own HTTPS handler (it verifies certificates, and offers ALPN http/1.1): Chubby's explicit
    # HTTPSHandler(context=ssl.create_default_context()) offers no ALPN, and KDnuggets' server answers 403 (2026-10-11).
    opener = urllib.request.build_opener(_NoRedirect())
    current = url
    for _ in range(MAX_REDIRECTS + 1):
        _check_public_https(current)
        _pace(current)
        headers = {"User-Agent": USER_AGENT, "Accept": ACCEPT}
        if etag:
            headers["If-None-Match"] = etag
        if last_modified:
            headers["If-Modified-Since"] = last_modified
        try:
            response = opener.open(urllib.request.Request(current, headers=headers), timeout=timeout)
            try:
                body = response.read(max_bytes + 1)
                if len(body) > max_bytes:
                    raise FeedError("body_too_large", f"the feed is over {max_bytes} bytes")
                body = _gunzip(body, max_bytes)
                return Fetched(getattr(response, "status", 200), body, response.headers.get("ETag", ""),
                               response.headers.get("Last-Modified", ""))
            finally:
                response.close()
        except urllib.error.HTTPError as exc:
            if exc.code == 304:
                return Fetched(304, b"", etag, last_modified, not_modified=True)
            if exc.code in (301, 302, 303, 307, 308):
                target = exc.headers.get("Location", "")
                if not target:
                    raise FeedError("http_3xx", f"redirect {exc.code} had no Location") from exc
                current = urllib.parse.urljoin(current, target)
                continue
            raise FeedError(f"http_{exc.code}", f"the feed returned HTTP {exc.code}") from exc
        except FeedError:
            raise
        except (urllib.error.URLError, TimeoutError, OSError, http.client.HTTPException) as exc:
            raise FeedError("network", f"the feed request failed: {exc}") from exc
    raise FeedError("redirect_limit", f"more than {MAX_REDIRECTS} redirects")


# ---------- parsing ----------

def normalize_timestamp(value: str) -> str:
    """A timezone-aware ISO timestamp in UTC, or "" when the value is no date."""
    raw = (value or "").strip()
    if not raw:
        return ""
    try:
        parsed = datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except ValueError:
        try:
            parsed = email.utils.parsedate_to_datetime(raw)
        except (TypeError, ValueError, IndexError, OverflowError):
            return ""
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC).replace(microsecond=0).isoformat()


def _local(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def _text(node) -> str:
    return "" if node is None else "".join(node.itertext()).strip()


def _first(node, *names):
    wanted = set(names)
    return next((c for c in node if _local(c.tag) in wanted), None)


def _all(node, *names):
    wanted = set(names)
    return [c for c in node if _local(c.tag) in wanted]


def _rss_items(root) -> list[Item]:
    # RSS 2.0 keeps its items in <channel>; RSS 1.0 (RDF) keeps them beside it, at the root (theirs missed these).
    channel = _first(root, "channel")
    nodes = (_all(channel, "item") if channel is not None else []) or _all(root, "item")
    items = []
    for node in nodes:
        link = _text(_first(node, "link"))
        guid = _text(_first(node, "guid")) or node.attrib.get(
            "{http://www.w3.org/1999/02/22-rdf-syntax-ns#}about", "")
        items.append(Item(guid, link, _text(_first(node, "title")) or "Untitled", _text(_first(node, "author", "creator")),
                          normalize_timestamp(_text(_first(node, "pubDate", "published", "date")))))
    return items


def _atom_items(root) -> list[Item]:
    items = []
    for node in _all(root, "entry"):
        url = ""
        for link in _all(node, "link"):
            href, rel = (link.attrib.get("href") or "").strip(), (link.attrib.get("rel") or "alternate").lower()
            if rel == "alternate" and href:
                url = href
                break
        author_node = _first(node, "author")
        author = _text(_first(author_node, "name")) if author_node is not None else ""
        published = _text(_first(node, "published")) or _text(_first(node, "updated"))
        items.append(Item(_text(_first(node, "id")), url or _text(_first(node, "link")),
                          _text(_first(node, "title")) or "Untitled", author, normalize_timestamp(published)))
    return items


def _json_author(item: dict) -> str:
    # JSON Feed 1.0: "author": {"name": …}; 1.1: "authors": [{"name": …}, …] (theirs printed the object)
    people = item.get("authors") if isinstance(item.get("authors"), list) else [item.get("author")]
    names = [p.get("name", "").strip() if isinstance(p, dict) else str(p or "").strip() for p in people]
    return ", ".join(n for n in names if n)


def _json_items(data) -> list[Item]:
    if not isinstance(data, dict) or not isinstance(data.get("items"), list):
        raise FeedError("parse", "a JSON Feed must have an items array")
    return [Item(str(i.get("id") or "").strip(), str(i.get("url") or i.get("external_url") or "").strip(),
                 str(i.get("title") or "Untitled").strip(), _json_author(i),
                 normalize_timestamp(str(i.get("date_published") or "")))
            for i in data["items"] if isinstance(i, dict)]


def parse(body: bytes) -> list[Item]:
    """RSS 2.0, RSS 1.0, Atom or JSON Feed, told apart by the content."""
    if len(body) > MAX_BODY_BYTES:
        raise FeedError("body_too_large", f"the feed is over {MAX_BODY_BYTES} bytes")
    if body.lstrip().startswith((b"{", b"[")):
        try:
            return _json_items(json.loads(body.decode("utf-8")))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise FeedError("parse", f"not a valid JSON Feed: {exc}") from exc
    try:
        root = ET.fromstring(body)
    except ET.ParseError as exc:
        raise FeedError("parse", f"not valid XML (a web page, not a feed?): {exc}") from exc
    name = _local(root.tag).lower()
    if name == "feed":
        return _atom_items(root)
    if name in ("rss", "rdf"):
        return _rss_items(root)
    raise FeedError("parse", f"not a feed: the document's root is <{name}>")


# ---------- YouTube ----------

def youtube_channel_id(value: str) -> str:
    """A channel id from `UC…`, `@handle` or a channel URL (a page fetch for the last two)."""
    raw = (value or "").strip()
    if CHANNEL_ID_RE.fullmatch(raw):
        return raw
    if m := re.search(r"/channel/(UC[A-Za-z0-9_-]{22})", raw):
        return m.group(1)
    if raw.startswith("@"):
        url = f"https://www.youtube.com/{raw}"
    elif "youtube.com" in raw:
        url = raw if raw.startswith("http") else "https://" + raw
    else:
        raise FeedError("invalid_config", "a YouTube source is a channel id (UC…), an @handle or a channel URL")
    text = fetch(url, max_bytes=8 * 1024 * 1024).body.decode("utf-8", "replace")
    for pattern in (r'"channelId"\s*:\s*"(UC[A-Za-z0-9_-]{22})"',
                    r'rel="canonical" href="https://www\.youtube\.com/channel/(UC[A-Za-z0-9_-]{22})"'):
        if m := re.search(pattern, text):
            return m.group(1)
    raise FeedError("parse", "no channel id found on that page")


def youtube_listing(channel_id: str, *, runner=subprocess.run) -> list[Item]:
    """The channel's latest videos through yt-dlp (no cookies, no login): ids and titles, no dates."""
    url = f"https://www.youtube.com/channel/{channel_id}/videos"
    cmd = [sys.executable, "-m", "yt_dlp", "--flat-playlist", "--dump-single-json",
           "--playlist-end", str(YOUTUBE_LISTING), url]
    try:
        proc = runner(cmd, capture_output=True, text=True, encoding="utf-8", timeout=120)
    except (OSError, subprocess.SubprocessError) as exc:
        raise FeedError("network", f"yt-dlp could not list the channel: {exc}") from exc
    if proc.returncode != 0:
        raise FeedError("network", "yt-dlp could not list the channel: " + (proc.stderr or "").strip()[-200:])
    try:
        data = json.loads(proc.stdout)
    except json.JSONDecodeError as exc:
        raise FeedError("parse", f"yt-dlp gave no JSON: {exc}") from exc
    author = str(data.get("channel") or data.get("title") or "")
    return [Item(f"yt:video:{v['id']}", f"https://www.youtube.com/watch?v={v['id']}", str(v.get("title") or v["id"]),
                 author, "")
            for v in data.get("entries") or [] if v.get("id")]


def youtube_items(value: str, *, etag: str = "", last_modified: str = "", runner=subprocess.run):
    """(Fetched or None, items, how): the channel's Atom feed (dated) first, else the yt-dlp listing."""
    channel = youtube_channel_id(value)
    feed_url = f"https://www.youtube.com/feeds/videos.xml?channel_id={channel}"
    try:
        got = fetch(feed_url, etag=etag, last_modified=last_modified)
        return got, ([] if got.not_modified else parse(got.body)), "feed"
    except FeedError as exc:
        # The public feed answers 404/500 from some networks (2026-10-11, this machine); the listing still works.
        return None, youtube_listing(channel, runner=runner), f"yt-dlp listing (feed: {exc.code})"


# ---------- identity ----------

def item_key(item: Item) -> str:
    """One item's identity across reads: its feed id, else its link's source key, else title and date."""
    if item.id:
        material = "id:" + item.id
    elif item.url:
        material = "url:" + source_key(item.url)
    else:
        material = f"fallback:{item.title}\n{item.published}"
    return hashlib.sha256(material.encode("utf-8")).hexdigest()[:24]
