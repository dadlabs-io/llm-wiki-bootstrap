#!/usr/bin/env python3
"""
wiki-fetch-page.py — fetch a page that only shows its text once JavaScript runs (Threads, Instagram,
LinkedIn, public Notion pages, Bluesky, Medium without a browser session, the fallback for X) in a
headless Chromium on this machine, and save it as a raw under <topic>/raw/, as Markdown.

    uv run --project <scripts> python <scripts>/wiki-fetch-page.py --topic <topic> --url <url> --ingested-by claude-code

It replaces the Node fetcher that ran only inside the `openclaw` Docker container (2026-10-05: the
container had crashed, so no such page could be fetched; its copy of the script was not ours). Playwright
and its Chromium come with the scripts' uv environment: the install runs `playwright install chromium`.

The rendered page goes through MarkItDown (`_markdown.html_to_markdown`), so headings, links, lists and
tables survive; when that fails, the page's visible text is saved and the header says so. A page that
looks paywalled or nearly empty is flagged (`paywall=suspected`, a `paywall:` header line) and never
fetched another way (Mark, 2026-10-05): read it in the user's own browser, or tell the user.

At most two of these run at once on a machine (an OS lock): four parallel headless browsers once hung it
(2026-07-10). A third caller waits.

Prints raw_path=, source_url=, suggested_title= (and paywall=suspected). Exit codes: 0 saved; 1 the page
could not be fetched; 2 bad input (no such notebook); 3 Chromium is not installed (the message names the
command); 5 no fetch slot came free in time.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from _atomic_io import atomic_write_text  # noqa: E402
from _markdown import html_to_markdown  # noqa: E402
from _wiki_config import resolve_vault_topic  # noqa: E402

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

USER_AGENT = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
              "Chrome/141.0 Safari/537.36")
PAYWALL_MARKERS = ("subscribe to read", "subscribe to continue", "members only", "this post is for paid",
                   "this story is for", "create a free account", "to continue reading", "already a subscriber",
                   "this is a preview")
SHORT_PAGE = 600
MAX_PARALLEL = 2
SLOT_MAX_WAIT = 300


def looks_paywalled(text: str) -> bool:
    t = (text or "").strip()
    return len(t) < SHORT_PAGE or any(m in t.lower() for m in PAYWALL_MARKERS)


class FetchSlot:
    """One of MAX_PARALLEL page-fetch slots, an OS lock on a small file; the OS drops it if we die."""

    def __init__(self, path: Path):
        self.path, self.fh = path, None

    def try_acquire(self) -> bool:
        fh = open(self.path, "a+b")
        try:
            if os.name == "nt":
                import msvcrt
                fh.seek(0)
                msvcrt.locking(fh.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl
                fcntl.flock(fh.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError:
            fh.close()
            return False
        self.fh = fh
        return True

    def release(self) -> None:
        if self.fh is None:
            return
        try:
            if os.name == "nt":
                import msvcrt
                self.fh.seek(0)
                msvcrt.locking(self.fh.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                import fcntl
                fcntl.flock(self.fh.fileno(), fcntl.LOCK_UN)
        finally:
            self.fh.close()
            self.fh = None


def acquire_fetch_slot(max_wait: float = SLOT_MAX_WAIT, n: int = MAX_PARALLEL):
    d = Path(os.environ.get("WIKI_PAGE_FETCH_LOCK_DIR") or Path.home() / ".cache" / "wiki-page-fetch")
    d.mkdir(parents=True, exist_ok=True)
    start, announced = time.monotonic(), False
    while True:
        for i in range(1, n + 1):
            slot = FetchSlot(d / f"slot-{i}.lock")
            if slot.try_acquire():
                return slot
        if time.monotonic() - start >= max_wait:
            return None
        if not announced:
            print(f"  {n} page fetches already running — waiting for one", file=sys.stderr)
            announced = True
        time.sleep(1.0)


def pick_title(page_title: str | None, og_title: str | None) -> str:
    """The page's <title>, unless it is just the site's name ("Instagram", "Threads"): then og:title."""
    t, og = (page_title or "").strip(), (og_title or "").strip()
    return og if og and len(t) < 20 else t


def render(url: str, timeout_ms: int) -> dict:
    """Open the page in headless Chromium; {"title", "html", "text", "og_image", "description", "final_url"}."""
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        browser = p.chromium.launch()
        try:
            page = browser.new_context(user_agent=USER_AGENT).new_page()
            try:
                page.goto(url, wait_until="networkidle", timeout=timeout_ms)
            except Exception as e:  # noqa: BLE001 - a page that never goes idle still renders
                print(f"  networkidle timed out, retrying with domcontentloaded: {' '.join(str(e).split())[:120]}",
                      file=sys.stderr)
                page.goto(url, wait_until="domcontentloaded", timeout=timeout_ms)
            page.wait_for_timeout(2000)
            page.evaluate("document.querySelectorAll('script,style,noscript').forEach(e => e.remove())")
            meta = page.evaluate("""() => {
                const m = s => { const e = document.querySelector(s); return e ? e.getAttribute('content') : null; };
                return {og: m('meta[property="og:image"]'), ogTitle: m('meta[property="og:title"]'),
                        desc: m('meta[name="description"]') || m('meta[property="og:description"]')};
            }""")
            return {"title": pick_title(page.title(), meta.get("ogTitle")), "html": page.content(), "final_url": page.url,
                    "text": page.evaluate("document.body ? document.body.innerText : ''"),
                    "og_image": meta.get("og"), "description": meta.get("desc")}
        finally:
            browser.close()


def slugify(text: str, max_len: int = 50) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", (text or "").lower()).strip("-")
    return s[:max_len].rstrip("-") or "untitled"


def unique_path(target: Path) -> Path:
    if not target.exists():
        return target
    n = 2
    while (cand := target.with_name(f"{target.stem}-{n}{target.suffix}")).exists():
        n += 1
    return cand


def _q(s: str) -> str:
    return json.dumps(s or "", ensure_ascii=False)


def build_raw(url: str, page: dict, ingested_by: str) -> tuple[str, bool]:
    """(the raw's text, paywall suspected). Markdown through MarkItDown, else the visible text."""
    body, how = html_to_markdown(page["html"])
    converted = "markdown" if body else f"text ({how})"
    body = body or (page["text"] or "").strip()
    paywall = looks_paywalled(page["text"])
    fm = ["---", f"title: {_q(page['title'])}", f"source_url: {url}", "fetched_via: playwright-chromium",
          f"fetched: {datetime.now().astimezone().isoformat(timespec='seconds')}", f"ingested_by: {ingested_by}",
          "type: web-page", f"converted: {converted}"]
    if paywall:
        n = len((page["text"] or "").strip())
        note = f"suspected paywall or truncated page ({n} chars): read it in the user's signed-in browser, or tell the user"
        fm.append(f"paywall: {_q(note)}")
    if page.get("description"):
        fm.append(f"meta_description: {_q(page['description'][:300])}")
    if page.get("og_image"):
        fm.append(f"og_image: {page['og_image']}")
    fm += ["---", ""]
    text = "\n".join(fm + [f"# {page['title'] or url}", "", f"**Source**: <{url}>", "", "---", "", body.strip(), ""])
    return text, paywall


def run(args) -> int:
    vault, topic = resolve_vault_topic(args.topic, args.vault)
    root = Path(vault) / topic
    if not root.is_dir():
        _err(f"notebook '{topic}' not found at {root}")
        return 2
    slot = acquire_fetch_slot()
    if slot is None:
        _err(f"no page-fetch slot came free in {SLOT_MAX_WAIT}s; retry later")
        return 5
    print(f"Fetching (playwright): {args.url}", file=sys.stderr)
    try:
        page = render(args.url, args.timeout * 1000)
    except Exception as e:  # noqa: BLE001 - Playwright raises many kinds; the message is what matters
        msg = " ".join(str(e).split())
        if "Executable doesn't exist" in msg or "playwright install" in msg:
            _err("Chromium for Playwright is not installed: run `uv run --project <scripts dir> python -m "
                 "playwright install chromium` (the global install does this)")
            return 3
        _err(f"could not fetch the page: {msg[:300]}")
        return 1
    finally:
        slot.release()
    text, paywall = build_raw(args.url, page, args.ingested_by)
    raw_dir = root / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)
    raw_path = unique_path(raw_dir / f"{datetime.now():%Y-%m-%d}-{args.slug or slugify(page['title'] or args.url)}.md")
    atomic_write_text(raw_path, text)
    print(f"Saved raw: {raw_path}")
    print(f"  Title: {page['title']}")
    print(f"  Length: {len(text)} chars")
    print(f"raw_path={raw_path}")
    print(f"source_url={args.url}")
    if page["title"]:
        print(f"suggested_title={page['title']}")
    if paywall:
        print("paywall=suspected")
    return 0


def _err(msg: str) -> None:
    print(f"error: {msg}", file=sys.stderr)


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__.strip().splitlines()[0])
    p.add_argument("--topic", required=True, help="the notebook whose raw/ gets the page")
    p.add_argument("--url", required=True)
    p.add_argument("--vault", default=None, help="legacy vault root; default: resolve --topic through the registry")
    p.add_argument("--ingested-by", default="cli")
    p.add_argument("--slug", default=None)
    p.add_argument("--timeout", type=int, default=45, help="seconds per page load (default 45)")
    return run(p.parse_args(argv))


if __name__ == "__main__":
    sys.exit(main())
