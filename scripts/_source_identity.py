"""One answer to "is this the same source?" for every duplicate check (task #96, 2026-10-11).

`source_key(url)` is a comparison key, never a URL to fetch or to write into an entry. Filing
(wiki-update.py), the Drive and Gmail steps (url_dedup_key), the queue (wiki-list-add.py) and the
dequeue (wiki-dequeue.py) all compare by it. Before, each had its own rule: the queue compared exact
text, the dequeue cut every query off (so any youtube.com/watch?v= link matched any other and a video
never ingested was moved to done/), and none knew an x.com post from the same twitter.com post.

The platform rules follow Chubby Skills' tools/source_identity.py (MIT; read 2026-10-11, entry in
agentic-design research/tooling/chubby-skills-...): a post or video has one key whatever form its
link takes. Everything else keeps its host and path, lowercased (GitHub's owner/repo is case-blind;
two agentic-design duplicates differed only in case, 2026-09-14), and its query minus tracking tags.
"""
from __future__ import annotations

import re
import urllib.parse

# Query keys that say who shared a link or how, never which source it is. The Drive list
# (2026-09-02, 2026-10-05) plus filing's ref/source (2026-09-14).
TRACKING_KEYS = {
    "shem", "utm_id", "_hsenc", "_hsmi", "_hsq", "si", "fbclid", "gclid", "gbraid", "wbraid", "msclkid",
    "ttclid", "twclid", "igshid", "igsh", "mc_cid", "mc_eid", "ref", "ref_src", "ref_url", "source", "yclid",
    "stkn", "img_index",
}

YOUTUBE_HOSTS = {"youtube.com", "music.youtube.com", "youtube-nocookie.com", "youtu.be"}
YOUTUBE_ID = re.compile(r"^[A-Za-z0-9_-]{6,}$")
X_HOSTS = {"x.com", "twitter.com"}
X_STATUS = re.compile(r"^/(?:[^/]+/status(?:es)?|i/web/status|i/status)/(\d+)(?:/|$)")
ARXIV_ID = re.compile(r"^/(?:abs|pdf|html)/(\d{4}\.\d{4,5})(?:v\d+)?(?:\.pdf)?/?$")
INSTAGRAM_POST = re.compile(r"^/(?:p|reel|reels|tv)/([A-Za-z0-9_-]+)")
ARXIV_PAPER = re.compile(r"^/(?:abs|pdf|html)/(\d{4}\.\d{4,5}(?:v\d+)?)(?:\.pdf)?/?$")


def arxiv_pdf_url(url) -> str | None:
    """The PDF of an arXiv paper link (`abs`, `pdf` or `html`, version kept), else None. Discovery's
    arXiv feeds and triage hand over abs links, whose page is the abstract alone (task #104, 2026-10-12)."""
    try:
        parts = urllib.parse.urlsplit(str(url or "").strip())
    except ValueError:
        return None
    host = re.sub(r"^www\.", "", (parts.hostname or "").lower())
    if parts.scheme.lower() not in ("http", "https") or host != "arxiv.org":
        return None
    m = ARXIV_PAPER.match(parts.path)
    return f"https://arxiv.org/pdf/{m.group(1)}" if m else None


def _youtube_id(host: str, path: str, query: dict) -> str | None:
    if host == "youtu.be":
        vid = path.strip("/").split("/")[0]
    else:
        vid = (query.get("v") or [""])[0]
        if not vid:
            segs = [s for s in path.split("/") if s]
            vid = segs[1] if len(segs) >= 2 and segs[0] in ("shorts", "live", "embed", "v") else ""
    return vid if YOUTUBE_ID.match(vid or "") else None


def source_key(url) -> str:
    """The key two source URLs are compared by. Platform keys (`youtube:<id>`, `x:<id>`,
    `arxiv:<id>`, `instagram:<code>`) keep the id's case; any other http(s) URL becomes
    `<host><path>[?<query>]`, scheme-blind, `www.`/`m.`/`mobile.` dropped, path lowercased,
    GitHub's `blob|tree/<branch>` and `.git` dropped, tracking keys removed and the rest sorted.
    A non-web source (internal://, a file path) is compared as given."""
    u = str(url or "").strip().strip("\"'<>").strip()
    if not u:
        return ""
    try:
        parts = urllib.parse.urlsplit(u)
    except ValueError:
        return u.rstrip("/")
    if parts.scheme.lower() not in ("http", "https") or not parts.netloc:
        return u.rstrip("/")
    host = (parts.hostname or "").lower()
    host = re.sub(r"^(?:www|m|mobile)\.", "", host)
    path = urllib.parse.unquote(parts.path)
    query = urllib.parse.parse_qs(parts.query, keep_blank_values=True)

    if host in YOUTUBE_HOSTS:
        vid = _youtube_id(host, path, query)
        if vid:
            return f"youtube:{vid}"
    if host in X_HOSTS:
        m = X_STATUS.match(path)
        if m:
            return f"x:{m.group(1)}"
    if host == "arxiv.org":
        m = ARXIV_ID.match(path)
        if m:
            return f"arxiv:{m.group(1)}"
    if host == "instagram.com":
        m = INSTAGRAM_POST.match(path)
        if m:
            return f"instagram:{m.group(1)}"
    if host == "github.com":
        path = re.sub(r"^(/[^/]+/[^/]+)/(?:blob|tree)/[^/]+(?=/|$)", r"\1", path)
        path = re.sub(r"^(/[^/]+/[^/]+?)\.git(?=/|$)", r"\1", path)

    keep = sorted((k, v) for k, v in urllib.parse.parse_qsl(parts.query, keep_blank_values=True)
                  if not k.lower().startswith("utm_") and k.lower() not in TRACKING_KEYS)
    key = host + path.lower().rstrip("/")
    return key + ("?" + urllib.parse.urlencode(keep) if keep else "")
