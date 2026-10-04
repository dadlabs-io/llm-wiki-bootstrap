#!/usr/bin/env python3
"""
Read a Gmail label of newsletters and saved emails and turn it into a list of
candidate sources for a wiki cycle: every article link in every email, plus each
email that is itself the article (a full-text newsletter).

The email step of /wiki-cycle (beside the Drive step, 2026-10-03, task #65). Drive
links are queued straight away because the user put each one there; a newsletter is
not hand-picked (a Medium digest links fifteen stories), so this script never queues
on its own. It lists; the session judges each candidate (recommend or skip, with a
reason); the user approves ("approve recommended", or numbers); then `queue` writes
the approved ones into `_inbox/pending/` and `archive` moves the handled emails to
the done label.

    wiki-fetch-gmail.py fetch   --topic N --run-folder D [--label L] [--done-label L2]
    wiki-fetch-gmail.py queue   --topic N --run-folder D --approve recommended|all|none|1,4,9
    wiki-fetch-gmail.py archive --run-folder D
    wiki-fetch-gmail.py auth                      one-time sign-in (opens a browser)

`fetch` never changes the mailbox. It writes, in the run folder:
  email-fetch.json / .md   the cycle step (cycle-step-return-format), with the emails
                           and the numbered candidates
  email/<file>.md          each email's text, so the session can read what it judges
`queue` reads `email-review.json`, the session's judgment, from the same folder:
  {"1": {"decision": "recommend", "reason": "..."}, "2": {"decision": "skip", ...}}
Every candidate needs a decision before anything is queued. A full-text email that is
approved is copied to `<notebook>/raw/` and queued with that raw, so its ingest never
fetches it again. `archive` refuses to run before `queue` has (even `--approve none`):
a handled email leaves the label only once its links are decided.

Links: tracking redirects are followed to the article (newsletter platforms wrap
every link); tracking parameters are stripped; footer, account, social-profile,
app-store and home-page links are dropped; a link already in the wiki, staged, or in
the queue is listed as known and not offered. The email's "view online" link is its
own address, not a candidate.

Sign-in: the Gmail API with the `gmail.modify` scope (read, and move labels), token
cached at ~/.config/wiki-cycle/gmail-token.json. The OAuth client is
--client-secrets, $WIKI_GMAIL_CLIENT_SECRETS, ~/.config/wiki-cycle/client_secrets.json,
or else the client recorded in the Drive token (the same Google app). The app's
Google Cloud project must have the Gmail API enabled.

For tests and offline runs: --from-dir reads .eml files instead of Gmail (archive then
moves them into <dir>/read/), and --resolve-map names a JSON file of url -> final url
used instead of following redirects over the network.

Exit codes: 0 done; 2 bad input (unknown label, missing review, unknown candidate);
3 sign-in failed; 1 anything else.
"""
from __future__ import annotations

import argparse
import base64
import html
import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from email import policy
from email.parser import BytesParser
from email.utils import parsedate_to_datetime, parseaddr
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse, urlunparse

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _atomic_io import atomic_write_text  # noqa: E402
from _wiki_config import load_config, now_stamp, today_label, topic_root  # noqa: E402

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def _drive_helpers():
    """canonical_url / url_dedup_key / wiki_source_url_keys live in the Drive script;
    one copy of the URL rules for both inboxes."""
    spec = importlib.util.spec_from_file_location(
        "wiki_fetch_drive_folder", Path(__file__).resolve().parent / "wiki-fetch-drive-folder.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


_drive = _drive_helpers()
canonical_url = _drive.canonical_url
url_dedup_key = _drive.url_dedup_key

GMAIL_SCOPE = "https://www.googleapis.com/auth/gmail.modify"
CONFIG_DIR = Path.home() / ".config" / "wiki-cycle"
DEFAULT_TOKEN_CACHE = CONFIG_DIR / "gmail-token.json"
DRIVE_TOKEN = CONFIG_DIR / "drive-token.json"
DEFAULT_LABEL = "...wiki-inbox"
DEFAULT_DONE_LABEL = "...wiki-inbox/read"
FULL_TEXT_MIN_WORDS = 700
FULL_TEXT_MAX_LINKS_PER_100_WORDS = 3.0
BROWSER_UA = _drive.BROWSER_UA

# Hosts and paths that wrap a link in a click tracker: followed to the article.
REDIRECT_HOST_RE = re.compile(
    r"(^|\.)(hubspotlinks\.com|list-manage\.com|sendgrid\.net|mailchimp\.com|mailchi\.mp|"
    r"beehiiv\.com|convertkit-mail\d*\.com|ck\.page|substackcdn\.com|mailgun\.org|"
    r"mandrillapp\.com|cmail\d+\.com|createsend\d*\.com|awstrack\.me|"
    r"t\.co|bit\.ly|ow\.ly|tinyurl\.com|lnkd\.in|share\.google|goo\.gl|youtu\.be)$")
REDIRECT_HOST_PREFIX_RE = re.compile(r"^(click|clicks|link|links|track|trk|email|e|go|r|url\d*)\.")
REDIRECT_PATH_RE = re.compile(r"/(redirect|r|ss/c|c|click|track|l|ls/click)(/|$)")

# Dropped outright: not an article.
JUNK_TEXT_RE = re.compile(
    r"unsubscribe|manage (your )?(subscription|preferences|notifications|email)|email preferences|"
    r"opt[- ]out|update (your )?profile|privacy|terms of (service|use)|help center|"
    r"view (this email )?(in|on) (your |a )?browser|view online|read online|web version|"
    r"forward (this|to a friend)|refer a friend|download (on|the) app|get the app|"
    r"sign in|log ?in|become a member|upgrade|advertise|sponsor", re.I)
JUNK_URL_RE = re.compile(
    r"unsubscribe|/preferences|/account|/settings|/subscribe(\b|$)|/signin|/login|/membership|"
    r"/plans(\b|$)|/m/signin|/me/|optout|opt-out|/privacy|/terms|/tos(\b|$)|/legal|"
    r"/app-link|/redirect-to-app|/share(\b|$)", re.I)
APP_HOSTS = {"apps.apple.com", "itunes.apple.com", "play.google.com"}
IMAGE_EXT_RE = re.compile(r"\.(png|jpe?g|gif|webp|svg)$", re.I)
MEDIUM_POST_RE = re.compile(r"-[0-9a-f]{8,12}$")
MEDIUM_HOSTS_EXTRA = {"towardsdatascience.com", "levelup.gitconnected.com", "pub.towardsai.net",
                      "ai.plainenglish.io", "betterprogramming.pub", "uxdesign.cc"}
GENERIC_TEXT = {"", "read more", "read", "here", "click here", "view", "open", "learn more",
                "continue reading", "read the full story", "read story", "read the story",
                "read article", "read the article", "more", "link", "watch", "listen", "→", "»"}


# ---------- parsing an email ----------

class _HTMLText(HTMLParser):
    """Text of an HTML body plus every <a href> with its text, in order."""
    BLOCK = {"p", "div", "br", "tr", "li", "h1", "h2", "h3", "h4", "h5", "h6", "table", "section", "article"}

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []
        self.links: list[tuple[str, str]] = []
        self._skip = 0
        self._href: str | None = None
        self._atext: list[str] = []

    def handle_starttag(self, tag, attrs):
        if tag in ("script", "style", "head", "title"):
            self._skip += 1
        if tag in self.BLOCK:
            self.parts.append("\n")
        if tag == "a":
            self._href = dict(attrs).get("href")
            self._atext = []
        if tag == "img" and self._href is not None:
            alt = dict(attrs).get("alt") or ""
            if alt:
                self._atext.append(alt)

    def handle_endtag(self, tag):
        if tag in ("script", "style", "head", "title") and self._skip:
            self._skip -= 1
        if tag == "a" and self._href is not None:
            self.links.append((self._href.strip(), " ".join("".join(self._atext).split())))
            self._href = None
        if tag in self.BLOCK:
            self.parts.append("\n")

    def handle_data(self, data):
        if self._skip:
            return
        self.parts.append(data)
        if self._href is not None:
            self._atext.append(data)

    def text(self) -> str:
        raw = "".join(self.parts)
        lines = [" ".join(l.split()) for l in raw.splitlines()]
        out, blank = [], 0
        for l in lines:
            if l:
                out.append(l)
                blank = 0
            elif not blank:
                out.append("")
                blank = 1
        return "\n".join(out).strip()


URL_IN_TEXT_RE = re.compile(r"https?://[^\s<>()\"']+")


def parse_message(raw_bytes: bytes, msg_id: str) -> dict:
    """One email -> {id, subject, sender, date, text, links:[(href, text)], words, web_url}."""
    msg = BytesParser(policy=policy.default).parsebytes(raw_bytes)
    subject = " ".join(str(msg.get("subject", "")).split())
    name, addr = parseaddr(str(msg.get("from", "")))
    sender = f"{name} <{addr}>" if name else addr
    try:
        date = parsedate_to_datetime(str(msg.get("date"))).astimezone().strftime("%Y-%m-%d")
    except (TypeError, ValueError):
        date = today_label()
    html_part = msg.get_body(preferencelist=("html",))
    text_part = msg.get_body(preferencelist=("plain",))
    links: list[tuple[str, str]] = []
    text = ""
    if html_part is not None:
        p = _HTMLText()
        p.feed(html_part.get_content())
        links = p.links
        text = p.text()
    if text_part is not None:
        plain = text_part.get_content().strip()
        if plain and (not text or len(plain.split()) >= 0.6 * len(text.split())):
            text = plain
        if not links:
            links = [(u.rstrip(".,;:!?"), "") for u in URL_IN_TEXT_RE.findall(plain)]
    web_url = None
    for href, atext in links:
        if re.search(r"view (this email |this post |it )?(in|on) (your |a )?browser|view online|read online|web version|"
                     r"open in (browser|app)|read in (browser|app)", atext, re.I):
            web_url = href
            break
    words = len(text.split())
    return {"id": msg_id, "subject": subject, "sender": sender, "sender_addr": addr.lower(),
            "date": date, "text": text, "links": links, "words": words, "web_url": web_url}


# ---------- links ----------

def needs_resolving(url: str) -> bool:
    try:
        p = urlparse(url)
    except ValueError:
        return False
    host = p.netloc.lower()
    return bool(REDIRECT_HOST_RE.search(host) or REDIRECT_HOST_PREFIX_RE.match(host)
                or (host.endswith("substack.com") and p.path.startswith("/redirect/"))
                or (host.endswith("daily.dev") and p.path.startswith("/r/"))
                or (REDIRECT_PATH_RE.search(p.path) and not host.endswith(("medium.com", "youtube.com", "github.com"))))


def make_resolver(resolve_map: dict | None, network: bool):
    def resolve(url: str) -> tuple[str, str | None]:
        if resolve_map is not None:
            return resolve_map.get(url, url), None
        if not network:
            return url, None
        try:
            import requests
            r = requests.get(url, headers={"User-Agent": BROWSER_UA}, allow_redirects=True, timeout=20, stream=True)
            final = r.url
            r.close()
            return final, None
        except Exception as exc:  # noqa: BLE001 — a dead tracker keeps its own address, with the reason
            return url, f"redirect not followed: {exc.__class__.__name__}"
    return resolve


def clean_url(url: str) -> str:
    """canonical_url (tracking params, YouTube form) plus Medium's `source=` tracker."""
    url = canonical_url(url)
    try:
        p = urlparse(url)
    except ValueError:
        return url
    host = p.netloc.lower()
    if (host.endswith("medium.com") or host in MEDIUM_HOSTS_EXTRA) and p.query:
        kept = [kv for kv in p.query.split("&") if kv.split("=", 1)[0] not in ("source", "sectionName")]
        url = urlunparse(p._replace(query="&".join(kept)))
    return url


def junk_reason(url: str, text: str) -> str | None:
    """Why a link is not an article, or None when it may be one."""
    try:
        p = urlparse(url)
    except ValueError:
        return "unparseable"
    if p.scheme not in ("http", "https"):
        return "not a web link"
    host = p.netloc.lower()
    bare = host[4:] if host.startswith("www.") else host
    path = p.path.rstrip("/")
    if JUNK_TEXT_RE.search(text or "") or JUNK_URL_RE.search(p.path + ("?" + p.query if p.query else "")):
        return "footer or account link"
    if bare in APP_HOSTS:
        return "app store"
    if IMAGE_EXT_RE.search(path):
        return "image"
    if not path:
        return "home page"
    if bare in ("facebook.com", "tiktok.com", "threads.net"):
        return "social profile"
    if bare in ("twitter.com", "x.com") and "/status/" not in path:
        return "social profile"
    if bare == "instagram.com" and not re.match(r"^/(p|reel|tv)/", path):
        return "social profile"
    if bare.endswith("linkedin.com") and not re.match(r"^/(pulse|posts|feed/update|newsletters)/", path):
        return "social profile"
    if bare == "youtube.com" and not (p.query.startswith("v=") or "/watch" in path or "/shorts/" in path):
        return "channel page"
    if bare.endswith("medium.com") or bare in MEDIUM_HOSTS_EXTRA:
        last = path.split("/")[-1]
        if not MEDIUM_POST_RE.search(last):
            return "Medium profile or publication page"
    if bare.endswith("substack.com") and not re.match(r"^/p/[^/]+$", path):
        return "Substack page that is not a post"
    return None


def _title_from(texts: list[str], url: str) -> str:
    good = [t for t in texts if t.lower().strip(" .:!") not in GENERIC_TEXT and len(t) > 3]
    if good:
        return max(good, key=len)[:200]
    tail = urlparse(url).path.rstrip("/").split("/")[-1]
    tail = MEDIUM_POST_RE.sub("", tail)
    return re.sub(r"[-_]+", " ", tail).strip()[:200] or url


def queue_keys(nb: Path) -> set[str]:
    """Dedup keys of every source already queued, routed or done (ticket `source:` lines)."""
    keys = set()
    inbox = nb / "_inbox"
    for folder in [inbox / "pending", inbox / "done", *sorted((inbox / "intake").glob("*"))]:
        if not folder.is_dir():
            continue
        for t in folder.glob("*.md"):
            try:
                head = t.read_text(encoding="utf-8", errors="replace")[:1500]
            except OSError:
                continue
            m = re.search(r"^source:\s*(\S+)", head, re.M)
            if m and m.group(1).startswith(("http://", "https://")):
                keys.add(url_dedup_key(m.group(1)))
    return keys


def is_full_text(e: dict, n_article_links: int) -> bool:
    if e["words"] < FULL_TEXT_MIN_WORDS:
        return False
    return n_article_links * 100.0 / max(e["words"], 1) <= FULL_TEXT_MAX_LINKS_PER_100_WORDS


def slugify(text: str, n: int = 60) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", (text or "").lower()).strip("-")
    return s[:n].rstrip("-") or "untitled"


# ---------- Gmail ----------

def _client_config(client_secrets: str | None) -> dict | None:
    for cand in [client_secrets, os.environ.get("WIKI_GMAIL_CLIENT_SECRETS"), str(CONFIG_DIR / "client_secrets.json")]:
        if cand and Path(cand).expanduser().is_file():
            return json.loads(Path(cand).expanduser().read_text(encoding="utf-8"))
    if DRIVE_TOKEN.is_file():
        tok = json.loads(DRIVE_TOKEN.read_text(encoding="utf-8"))
        if tok.get("client_id") and tok.get("client_secret"):
            return {"installed": {"client_id": tok["client_id"], "client_secret": tok["client_secret"],
                                  "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                                  "token_uri": tok.get("token_uri") or "https://oauth2.googleapis.com/token",
                                  "redirect_uris": ["http://localhost"]}}
    return None


def gmail_service(client_secrets: str | None, token_cache: str):
    try:
        from google.auth.transport.requests import Request
        from google.oauth2.credentials import Credentials
        from google_auth_oauthlib.flow import InstalledAppFlow
        from googleapiclient.discovery import build
    except ImportError as exc:
        print(f"error: missing dependency: {exc}. Install with: pip install google-api-python-client google-auth-oauthlib",
              file=sys.stderr)
        sys.exit(1)
    scopes = [GMAIL_SCOPE]
    path = Path(token_cache).expanduser()
    creds = None
    if path.exists():
        try:
            creds = Credentials.from_authorized_user_file(str(path), scopes)
        except Exception:  # noqa: BLE001
            creds = None
    if creds and not creds.has_scopes(scopes):
        creds = None
    if creds and creds.expired and creds.refresh_token:
        try:
            creds.refresh(Request())
        except Exception:  # noqa: BLE001
            creds = None
    if not creds or not creds.valid:
        cfg = _client_config(client_secrets)
        if not cfg:
            print("error: no Gmail token and no OAuth client: pass --client-secrets, or keep the Drive token "
                  f"({DRIVE_TOKEN}), whose client this script reuses", file=sys.stderr)
            sys.exit(3)
        try:
            creds = InstalledAppFlow.from_client_config(cfg, scopes).run_local_server(port=0, prompt="consent")
        except Exception as exc:  # noqa: BLE001
            print(f"error: Gmail sign-in failed: {exc}", file=sys.stderr)
            sys.exit(3)
        path.parent.mkdir(parents=True, exist_ok=True)
        atomic_write_text(path, creds.to_json())
        print(f"Gmail token cached at {path}", file=sys.stderr)
    return build("gmail", "v1", credentials=creds, cache_discovery=False)


def label_ids(service, *names: str) -> list[str]:
    labels = service.users().labels().list(userId="me").execute().get("labels", [])
    by_name = {l["name"]: l["id"] for l in labels}
    missing = [n for n in names if n not in by_name]
    if missing:
        print(f"error: no Gmail label named {', '.join(repr(m) for m in missing)}", file=sys.stderr)
        sys.exit(2)
    return [by_name[n] for n in names]


class GmailSource:
    def __init__(self, service, label: str, done_label: str):
        self.service = service
        self.label_id, self.done_id = label_ids(service, label, done_label)

    def messages(self):
        ids, token = [], None
        while True:
            resp = self.service.users().messages().list(userId="me", labelIds=[self.label_id],
                                                        pageToken=token, maxResults=100).execute()
            ids += [m["id"] for m in resp.get("messages", [])]
            token = resp.get("nextPageToken")
            if not token:
                break
        for mid in ids:
            m = self.service.users().messages().get(userId="me", id=mid, format="raw").execute()
            if self.done_id in m.get("labelIds", []):
                continue
            yield mid, base64.urlsafe_b64decode(m["raw"].encode("ascii"))

    def archive(self, mid: str) -> None:
        self.service.users().messages().modify(
            userId="me", id=mid, body={"addLabelIds": [self.done_id], "removeLabelIds": [self.label_id]}).execute()


class DirSource:
    """Offline: .eml files in a folder; archive moves a file into <dir>/read/."""
    def __init__(self, folder: str):
        self.dir = Path(folder)

    def messages(self):
        for p in sorted(self.dir.glob("*.eml")):
            yield p.stem, p.read_bytes()

    def archive(self, mid: str) -> None:
        (self.dir / "read").mkdir(exist_ok=True)
        shutil.move(str(self.dir / f"{mid}.eml"), str(self.dir / "read" / f"{mid}.eml"))


# ---------- step files ----------

def _row(url, reason, stamp, priority=None):
    return {"priority": priority, "url": url, "reason": reason, "timestamp": stamp}


def render_md(step: dict) -> str:
    s = step["summary"]
    cell = lambda v: str(v or "").replace("|", "\\|").replace("\n", " ").strip()  # noqa: E731
    out = [f"# Email fetch — {step['cycle_id']}", "",
           f"**Status**: {step['status']}", f"**Timestamp**: {step['timestamp']}",
           f"**Summary**: {s['emails_seen']} emails, {s['candidates']} candidates "
           f"({s['full_text_emails']} full-text emails), {s['known']} already known, {s['junk_dropped']} junk links dropped"
           + (f"; {s['queued']} queued" if step.get("reviewed") else "; not reviewed yet")
           + (f"; {s['archived']} emails archived" if s.get("archived") else ""), ""]
    review = step.get("review") or {}
    out += ["## Candidates", "", "| # | Email | Title | URL | Recommendation |", "|---|---|---|---|---|"]
    subj = {e["id"]: e["subject"] for e in step["emails"]}
    for c in step["candidates"]:
        r = review.get(str(c["n"])) or {}
        rec = f"{r.get('decision', '')}: {r.get('reason', '')}".strip(": ")
        kind = " (full-text email)" if c["kind"] == "email" else ""
        out.append(f"| {c['n']} | {cell(subj.get(c['email'], ''))[:60]} | {cell(c['title'])}{kind} | {c['url']} | {cell(rec)} |")
    for title, key in (("Queued", "queued"), ("Skipped", "skipped"), ("Deferred", "deferred")):
        out += ["", f"## {title}", "", "| Priority | URL | Reason | Timestamp |", "|---|---|---|---|"]
        for r in step[key]:
            out.append(f"| {r.get('priority') or '—'} | {r['url']} | {cell(r['reason'])} | {r['timestamp']} |")
    out += ["", "## Notes", "", step.get("notes") or "", "", "## Errors", ""]
    out += [f"- {e.get('code')}: {e.get('message')} ({e.get('item', '')})" for e in step["errors"]]
    return "\n".join(out) + "\n"


def write_step(run: Path, step: dict) -> None:
    atomic_write_text(run / "email-fetch.json", json.dumps(step, indent=2, ensure_ascii=False))
    atomic_write_text(run / "email-fetch.md", render_md(step))


def load_step(run: Path) -> dict:
    p = run / "email-fetch.json"
    if not p.is_file():
        print(f"error: no {p}: run fetch first", file=sys.stderr)
        sys.exit(2)
    return json.loads(p.read_text(encoding="utf-8"))


# ---------- commands ----------

def cmd_fetch(args) -> int:
    nb = Path(topic_root(args.topic))
    if not (nb / "wiki").is_dir():
        print(f"error: no wiki at {nb}", file=sys.stderr)
        return 2
    run = Path(args.run_folder)
    (run / "email").mkdir(parents=True, exist_ok=True)
    cfg = (load_config() or {}).get("email") or {}
    label = args.label or cfg.get("label") or DEFAULT_LABEL
    done_label = args.done_label or cfg.get("done_label") or DEFAULT_DONE_LABEL
    source = DirSource(args.from_dir) if args.from_dir else GmailSource(
        gmail_service(args.client_secrets, args.token_cache), label, done_label)
    resolve_map = json.loads(Path(args.resolve_map).read_text(encoding="utf-8")) if args.resolve_map else None
    resolver = make_resolver(resolve_map, network=not args.no_resolve)

    emails = []
    for mid, raw in source.messages():
        emails.append(parse_message(raw, mid))
        if args.max and len(emails) >= args.max:
            break

    # Follow every tracker once, in parallel.
    to_resolve = sorted({h for e in emails for h, _t in e["links"] if needs_resolving(h)})
    with ThreadPoolExecutor(max_workers=8) as pool:
        resolved = dict(zip(to_resolve, pool.map(resolver, to_resolve)))
    if emails:
        for e in emails:
            if e["web_url"] and e["web_url"] in resolved:
                e["web_url"] = resolved[e["web_url"]][0]
            if e["web_url"]:
                e["web_url"] = clean_url(e["web_url"])

    wiki_keys = _drive.wiki_source_url_keys(args.topic)
    q_keys = queue_keys(nb)
    stamp = now_stamp()
    candidates, skipped, deferred = [], [], []
    seen: dict[str, dict] = {}
    junk = 0
    n = 0
    for e in emails:
        own = {url_dedup_key(e["web_url"])} if e["web_url"] else set()
        groups: dict[str, list[str]] = {}
        order: list[str] = []
        for href, text in e["links"]:
            final, err = resolved.get(href, (href, None))
            url = clean_url(final)
            if junk_reason(url, text):
                junk += 1
                continue
            key = url_dedup_key(url)
            if key in own:
                continue
            if err and needs_resolving(url):
                deferred.append(_row(url, err, stamp))
                continue
            if key not in groups:
                groups[key] = []
                order.append(key)
                groups[key].append(url)
            groups[key].append(text)
        article_links = len(order)
        e["full_text"] = is_full_text(e, article_links)
        fname = f"{e['date']}-{slugify(e['subject'], 50)}-{e['id'][-8:]}.md"
        e["file"] = f"email/{fname}"
        atomic_write_text(run / "email" / fname,
                          f"# {e['subject']}\n\nfrom: {e['sender']}\ndate: {e['date']}\ngmail_id: {e['id']}\n"
                          f"web_url: {e['web_url'] or ''}\nwords: {e['words']}\nfull_text: {str(e['full_text']).lower()}\n"
                          f"---\n\n{e['text']}\n")
        if e["full_text"]:
            n += 1
            url = e["web_url"] or f"gmail:{e['id']}"
            known = bool(e["web_url"]) and url_dedup_key(url) in (wiki_keys | q_keys)
            if known:
                skipped.append(_row(url, "full-text email already in the wiki or the queue", stamp))
            else:
                candidates.append({"n": n, "kind": "email", "email": e["id"], "url": url,
                                   "title": e["subject"], "words": e["words"]})
        for key in order:
            url, *texts = groups[key]
            if key in seen:
                seen[key]["also_in"].append(e["id"])
                continue
            if key in wiki_keys or key in q_keys:
                skipped.append(_row(url, "already in the wiki" if key in wiki_keys else "already queued or handled", stamp))
                seen[key] = {"also_in": []}
                continue
            n += 1
            c = {"n": n, "kind": "link", "email": e["id"], "url": url, "title": _title_from(texts, url), "also_in": []}
            seen[key] = c
            candidates.append(c)

    step = {
        "skill": "wiki-fetch-gmail", "cycle_id": args.cycle_id or run.name, "step": "email-fetch",
        "timestamp": stamp, "status": "completed",
        "summary": {"emails_seen": len(emails), "links_found": sum(len(e["links"]) for e in emails),
                    "candidates": len(candidates), "full_text_emails": sum(1 for c in candidates if c["kind"] == "email"),
                    "known": len(skipped), "junk_dropped": junk, "redirects_followed": len(to_resolve),
                    "queued": 0, "archived": 0},
        "queued": [], "skipped": skipped, "deferred": deferred,
        "notes": f"label {label!r} (done label {done_label!r}); nothing queued until reviewed",
        "errors": [],
        "label": label, "done_label": done_label, "source": "dir" if args.from_dir else "gmail",
        "reviewed": False, "archived_ids": [],
        "emails": [{k: e[k] for k in ("id", "subject", "sender", "date", "words", "web_url", "full_text", "file")}
                   for e in emails],
        "candidates": candidates,
    }
    write_step(run, step)
    print(json.dumps({"status": "ok", **{k: step["summary"][k] for k in
                                        ("emails_seen", "candidates", "full_text_emails", "known", "junk_dropped")},
                      "review_file": str(run / "email-review.json"), "report": str(run / "email-fetch.md")}))
    return 0


def _parse_approve(value: str, review: dict, candidates: list[dict]) -> set[int] | None:
    nums = {c["n"] for c in candidates}
    if value == "none":
        return set()
    if value == "all":
        return nums
    if value == "recommended":
        return {c["n"] for c in candidates if (review.get(str(c["n"])) or {}).get("decision") == "recommend"}
    try:
        chosen = {int(x) for x in value.split(",") if x.strip()}
    except ValueError:
        return None
    return chosen if chosen <= nums else None


def _raw_for(nb: Path, run: Path, email: dict, cand: dict) -> str:
    """Copy an approved full-text email into the notebook's raw/; return raw/<file>."""
    body = (run / email["file"]).read_text(encoding="utf-8").split("\n---\n", 1)[-1].strip()
    name = f"{email['date']}-{slugify(email['subject'])}.md"
    dest = nb / "raw" / name
    k = 2
    while dest.exists():
        dest = nb / "raw" / f"{email['date']}-{slugify(email['subject'])}-{k}.md"
        k += 1
    dest.parent.mkdir(parents=True, exist_ok=True)
    atomic_write_text(dest, f"# {email['subject']}\nsource_url: {cand['url']}\nauthor: {email['sender']}\n"
                            f"published: {email['date']}\nfetched: {today_label()} via Gmail "
                            f"(full-text newsletter; images omitted)\n---\n{body}\n")
    return f"raw/{dest.name}"


def cmd_queue(args) -> int:
    run = Path(args.run_folder)
    step = load_step(run)
    nb = Path(topic_root(args.topic))
    rp = run / "email-review.json"
    if not rp.is_file():
        print(f"error: no {rp}: the session writes its judgment there first "
              '({"<n>": {"decision": "recommend|skip", "reason": "..."}})', file=sys.stderr)
        return 2
    review = json.loads(rp.read_text(encoding="utf-8"))
    cands = step["candidates"]
    undecided = [c["n"] for c in cands if (review.get(str(c["n"])) or {}).get("decision") not in ("recommend", "skip")]
    if undecided:
        print(f"error: no recommend/skip decision for candidate(s) {undecided[:20]}", file=sys.stderr)
        return 2
    approved = _parse_approve(args.approve, review, cands)
    if approved is None:
        print("error: --approve takes recommended, all, none, or candidate numbers from the list", file=sys.stderr)
        return 2
    emails = {e["id"]: e for e in step["emails"]}
    stamp = now_stamp()
    add = Path(__file__).resolve().parent / "wiki-list-add.py"
    queued, skipped, failed = [], [], 0
    for c in cands:
        reason = (review.get(str(c["n"])) or {}).get("reason", "")
        if c["n"] not in approved:
            skipped.append(_row(c["url"], f"not approved ({review[str(c['n'])]['decision']}): {reason}", stamp))
            continue
        cmd = [sys.executable, str(add), "--topic", args.topic, "--title", c["title"][:200],
               "--added-by", "email-fetch", "--priority", str(args.priority)]
        if c["kind"] == "email":
            raw = _raw_for(nb, run, emails[c["email"]], c)
            source = c["url"] if c["url"].startswith(("http://", "https://")) else str(nb / raw)
            cmd += ["--source", source, "--raw-path", raw]
        else:
            cmd += ["--source", c["url"]]
        p = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
        if p.returncode == 0:
            queued.append(_row(c["url"], reason or "approved", stamp, args.priority))
        else:
            failed += 1
            lines = (p.stderr or p.stdout or "").strip().splitlines()
            step["deferred"].append(_row(c["url"], lines[-1] if lines else "queue failed", stamp))
    step["queued"] = queued
    step["skipped"] = [r for r in step["skipped"] if not r["reason"].startswith("not approved")] + skipped
    step["review"] = review
    step["reviewed"] = True
    step["summary"]["queued"] = len(queued)
    step["status"] = "partial" if failed else "completed"
    write_step(run, step)
    print(json.dumps({"status": "ok", "approved": len(approved), "queued": len(queued), "failed": failed}))
    return 1 if failed else 0


def cmd_archive(args) -> int:
    run = Path(args.run_folder)
    step = load_step(run)
    if not step.get("reviewed"):
        print("error: queue has not run for this fetch: decide the candidates first (queue --approve ..., "
              "even --approve none), so no email leaves the label undecided", file=sys.stderr)
        return 2
    if step["source"] == "dir":
        if not args.from_dir:
            print("error: this fetch read a folder: pass the same --from-dir", file=sys.stderr)
            return 2
        source = DirSource(args.from_dir)
    else:
        svc = gmail_service(args.client_secrets, args.token_cache)
        source = GmailSource(svc, step["label"], step["done_label"])
    done = set(step.get("archived_ids") or [])
    moved, failed = 0, 0
    for e in step["emails"]:
        if e["id"] in done:
            continue
        try:
            source.archive(e["id"])
            done.add(e["id"])
            moved += 1
        except Exception as exc:  # noqa: BLE001 — a failed move leaves the email for next time
            failed += 1
            step["errors"].append({"code": "archive_failed", "message": str(exc), "item": e["id"]})
    step["archived_ids"] = sorted(done)
    step["summary"]["archived"] = len(done)
    write_step(run, step)
    print(json.dumps({"status": "ok" if not failed else "partial", "archived": moved, "failed": failed,
                      "to": step["done_label"]}))
    return 1 if failed else 0


def cmd_auth(args) -> int:
    gmail_service(args.client_secrets, args.token_cache)
    print(json.dumps({"status": "auth_ok", "token_cache": str(args.token_cache), "scopes": [GMAIL_SCOPE]}))
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0].strip())
    ap.add_argument("--client-secrets", default=None, help="OAuth Desktop client JSON (default: reuse the Drive token's client)")
    ap.add_argument("--token-cache", default=str(DEFAULT_TOKEN_CACHE))
    sub = ap.add_subparsers(dest="cmd", required=True)
    f = sub.add_parser("fetch", help="list the label's emails and their candidate links (changes nothing in Gmail)")
    f.add_argument("--topic", required=True)
    f.add_argument("--run-folder", required=True)
    f.add_argument("--cycle-id", default=None)
    f.add_argument("--label", default=None, help=f"default: email.label in .claude/wiki-config.json, else {DEFAULT_LABEL!r}")
    f.add_argument("--done-label", default=None, help=f"default: email.done_label, else {DEFAULT_DONE_LABEL!r}")
    f.add_argument("--max", type=int, default=0, help="read at most N emails (0 = all)")
    f.add_argument("--from-dir", default=None, help="read .eml files from this folder instead of Gmail")
    f.add_argument("--resolve-map", default=None, help="JSON url -> final url, instead of following redirects")
    f.add_argument("--no-resolve", action="store_true", help="do not follow tracking redirects")
    q = sub.add_parser("queue", help="queue the approved candidates into _inbox/pending/")
    q.add_argument("--topic", required=True)
    q.add_argument("--run-folder", required=True)
    q.add_argument("--approve", required=True, help="recommended | all | none | 1,4,9")
    q.add_argument("--priority", type=int, default=3)
    a = sub.add_parser("archive", help="move the fetched emails to the done label (after queue)")
    a.add_argument("--run-folder", required=True)
    a.add_argument("--from-dir", default=None)
    sub.add_parser("auth", help="sign in to Gmail once and cache the token")
    args = ap.parse_args()
    return {"fetch": cmd_fetch, "queue": cmd_queue, "archive": cmd_archive, "auth": cmd_auth}[args.cmd](args)


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("error: interrupted", file=sys.stderr)
        sys.exit(130)
