#!/usr/bin/env python3
"""Checks for task #65 part 1: wiki-fetch-gmail.py turns a label of newsletters into
candidates, queues only what was approved, and archives only after the decision.
Never shipped; no Gmail access (the emails are .eml files, redirects a map).

    python tests/scripts/test_gmail_fetch.py    # exit 0 = every check passed

The four emails are the shapes found in the user's label on 2026-10-03: a Medium daily
digest (stories, author and publication pages, app and account links), a full-text
Substack newsletter (the email is the article; its links are wrapped in redirects),
a link roundup (daily.dev-style redirects to GitHub, X, Instagram, YouTube), and a
plain-text email.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from email.message import EmailMessage
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "scripts"
GMAIL = SCRIPTS / "wiki-fetch-gmail.py"

results: list[tuple[bool, str]] = []


def check(name: str, ok: bool, detail: object = ""):
    results.append((bool(ok), name + (f"  [{detail}]" if not ok and detail != "" else "")))


def eml(subject: str, sender: str, html: str | None = None, text: str | None = None) -> bytes:
    m = EmailMessage()
    m["Subject"] = subject
    m["From"] = sender
    m["To"] = "mark@example.com"
    m["Date"] = "Wed, 01 Oct 2026 12:50:00 +0000"
    if text is not None:
        m.set_content(text)
    if html is not None:
        if text is None:
            m.set_content("(html only)")
        m.add_alternative(html, subtype="html")
    return bytes(m)


ESSAY = " ".join(["State is the hardest part of software design because every copy can drift."] * 70)

MEDIUM = eml("Restarting Your Agent Is Not Repairing It | Koshy", "Medium Daily Digest <noreply@medium.com>", html=f"""
<html><body>
<a href="https://medium.com/@koshy?source=email-digest">Koshy</a>
<a href="https://medium.com/@koshy/restarting-your-agent-is-not-repairing-it-0a1b2c3d4e5f?source=email-abc-digest.reader"><img src="x.png" alt=""></a>
<a href="https://medium.com/@koshy/restarting-your-agent-is-not-repairing-it-0a1b2c3d4e5f?source=email-abc-digest.reader">Restarting Your Agent Is Not Repairing It</a>
<a href="https://medium.com/@koshy/restarting-your-agent-is-not-repairing-it-0a1b2c3d4e5f?source=email-abc">Read more</a>
<a href="https://medium.com/data-engineer-things?source=email">Data Engineer Things</a>
<a href="https://medium.com/data-engineer-things/six-skills-every-data-engineer-should-have-9f8e7d6c5b4a?source=email">6 technical skills every data engineer should have</a>
<a href="https://medium.com/@old/an-article-already-in-the-wiki-111122223333?source=email">An article already in the wiki</a>
<a href="https://medium.com/me/email-settings">Email settings</a>
<a href="https://medium.com/m/signin?redirect=x">Sign in</a>
<a href="https://apps.apple.com/app/medium/id828256236">Download on the App Store</a>
<a href="https://medium.com/plans?source=email">Become a member</a>
<a href="https://medium.com/">Medium</a>
<a href="https://help.medium.com/hc/en-us/articles/unsubscribe">Unsubscribe</a>
</body></html>""")

SUBSTACK = eml("Why State is the Hardest Thing in Software Design", "ByteByteGo <bytebytego@substack.com>", html=f"""
<html><body>
<a href="https://substack.com/redirect/2/view-online">View in browser</a>
<h1>Why State is the Hardest Thing in Software Design</h1>
<p>{ESSAY}</p>
<p>See <a href="https://substack.com/redirect/aaa111">the Raft paper</a> and
<a href="https://substack.com/redirect/bbb222">a post on event sourcing</a>.</p>
<a href="https://bytebytego.substack.com/subscribe?utm_source=email">Subscribe</a>
<a href="https://twitter.com/bytebytego">Twitter</a>
<a href="https://substack.com/redirect/dead">a link whose tracker is down</a>
</body></html>""")

ROUNDUP = eml("Stumpy, your personal update from daily.dev is ready", "daily.dev <informer@daily.dev>", html="""
<html><body>
<a href="https://api.daily.dev/r/abc">qmd: local search for your notes</a>
<a href="https://api.daily.dev/r/def">A thread on agent memory</a>
<a href="https://x.com/karpathy">Karpathy on X</a>
<a href="https://www.instagram.com/p/C0ffee123/">A post on Instagram</a>
<a href="https://www.instagram.com/someone/">someone on Instagram</a>
<a href="https://www.youtube.com/@aiDotEngineer">AI Engineer channel</a>
<a href="https://youtu.be/dQw4w9WgXcQ?si=tracking">A talk</a>
<a href="https://app.daily.dev/settings/notifications">Manage your notifications</a>
<a href="https://api.daily.dev/r/queued">Something already queued</a>
</body></html>""")

PLAIN = eml("Two links for the wiki", "A Friend <friend@example.com>",
            text="Have a look at https://simonwillison.net/2026/Sep/30/agents/ and "
                 "https://arxiv.org/abs/2609.11111v1 when you can.\n")

RESOLVE = {
    "https://substack.com/redirect/2/view-online": "https://bytebytego.substack.com/p/why-state-is-the-hardest-thing?utm_source=email",
    "https://substack.com/redirect/aaa111": "https://raft.github.io/raft.pdf?utm_campaign=x",
    "https://substack.com/redirect/bbb222": "https://martinfowler.com/eaaDev/EventSourcing.html",
    "https://api.daily.dev/r/abc": "https://github.com/tobi/qmd?ref=dailydev",
    "https://api.daily.dev/r/def": "https://x.com/someone/status/1234567890",
    "https://api.daily.dev/r/queued": "https://example.org/already-queued-article",
}


def run(*args, cwd):
    return subprocess.run([sys.executable, str(GMAIL), *args], cwd=cwd, capture_output=True, text=True,
                          encoding="utf-8", env={**os.environ, "PYTHONIOENCODING": "utf-8"})


with tempfile.TemporaryDirectory() as td:
    tmp = Path(td)
    nb = tmp / "notebooks" / "t"
    (nb / "wiki" / "research").mkdir(parents=True)
    (nb / "wiki" / "research" / "old.md").write_text(
        "---\ntitle: old\nsource_url: https://medium.com/@old/an-article-already-in-the-wiki-111122223333\n---\n# old\n",
        encoding="utf-8")
    (nb / "_inbox" / "pending").mkdir(parents=True)
    (nb / "_inbox" / "pending" / "3-x-queued.md").write_text(
        "---\nsource: https://example.org/already-queued-article\n---\n", encoding="utf-8")
    (tmp / "linked-notebooks.json").write_text(json.dumps({"notebooks": {"t": {"root": "notebooks/t"}}}), encoding="utf-8")
    proj = tmp / "project"
    (proj / ".claude").mkdir(parents=True)
    (proj / ".claude" / "wiki-config.json").write_text(json.dumps(
        {"notebook": "t", "registry": (tmp / "linked-notebooks.json").as_posix()}), encoding="utf-8")
    mail = tmp / "mail"
    mail.mkdir()
    for name, data in (("m1", MEDIUM), ("m2", SUBSTACK), ("m3", ROUNDUP), ("m4", PLAIN)):
        (mail / f"{name}.eml").write_bytes(data)
    rmap = tmp / "resolve.json"
    rmap.write_text(json.dumps(RESOLVE), encoding="utf-8")
    runf = nb / "_inbox" / "reports" / "2026-10-03" / "2026-10-03-01"

    p = run("fetch", "--topic", "t", "--run-folder", str(runf), "--from-dir", str(mail), "--resolve-map", str(rmap), cwd=proj)
    check("fetch exits 0", p.returncode == 0, p.stderr[-400:])
    step = json.loads((runf / "email-fetch.json").read_text(encoding="utf-8"))
    cands = step["candidates"]
    urls = {c["url"] for c in cands}
    want = {
        "https://medium.com/@koshy/restarting-your-agent-is-not-repairing-it-0a1b2c3d4e5f",
        "https://medium.com/data-engineer-things/six-skills-every-data-engineer-should-have-9f8e7d6c5b4a",
        "https://bytebytego.substack.com/p/why-state-is-the-hardest-thing",   # the full-text email itself
        "https://raft.github.io/raft.pdf",
        "https://martinfowler.com/eaaDev/EventSourcing.html",
        "https://github.com/tobi/qmd?ref=dailydev",
        "https://x.com/someone/status/1234567890",
        "https://www.instagram.com/p/C0ffee123/",
        "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        "https://simonwillison.net/2026/Sep/30/agents/",
        "https://arxiv.org/abs/2609.11111v1",
    }
    check("the candidates are exactly the articles", urls == want,
          {"extra": sorted(urls - want), "missing": sorted(want - urls)})
    check("no Medium source= tracker, no utm_ left", not any("source=" in u or "utm_" in u for u in urls))
    check("the 3 copies of one Medium story are one candidate",
          sum(1 for u in urls if "restarting-your-agent" in u) == 1)
    koshy = next((c for c in cands if "restarting-your-agent" in c["url"]), {})
    check("its title is the story's title, not 'Read more'", koshy.get("title") == "Restarting Your Agent Is Not Repairing It",
          koshy.get("title"))
    full = [c for c in cands if c["kind"] == "email"]
    check("the Substack email is one full-text candidate, at its web address",
          len(full) == 1 and full[0]["url"] == "https://bytebytego.substack.com/p/why-state-is-the-hardest-thing", full)
    check("the digest and the roundup are not full-text",
          {e["subject"][:12] for e in step["emails"] if e["full_text"]} == {"Why State is"})
    skipped = {r["url"]: r["reason"] for r in step["skipped"]}
    check("a story already in the wiki is skipped as known",
          skipped.get("https://medium.com/@old/an-article-already-in-the-wiki-111122223333") == "already in the wiki", skipped)
    check("a link already in the queue is skipped",
          skipped.get("https://example.org/already-queued-article") == "already queued or handled", skipped)
    check("a dead tracker stays unresolved and is not offered",
          not any("redirect/dead" in u for u in urls) and step["summary"]["junk_dropped"] >= 10, step["summary"])
    check("each email's text is saved for the session to read",
          len(list((runf / "email").glob("*.md"))) == 4 and "State is the hardest part" in
          next((runf / "email").glob("*why-state*")).read_text(encoding="utf-8"))
    bbg_text = next((runf / "email").glob("*why-state*")).read_text(encoding="utf-8")
    check("the full-text email is saved as Markdown: its heading and links kept (task #71)",
          "converted: markdown" in bbg_text and "# Why State is the Hardest Thing" in bbg_text.split("---", 1)[-1]
          and "[the Raft paper](https://substack.com/redirect/aaa111)" in bbg_text, bbg_text[:400])
    digest_text = next((runf / "email").glob("*restarting*")).read_text(encoding="utf-8")
    check("an email that is not full-text is saved as plain text", "converted: text\n" in digest_text
          and "](" not in digest_text, digest_text[:300])
    check("fetch queues nothing and touches no email",
          not step["queued"] and len(list(mail.glob("*.eml"))) == 4 and len(list((nb / "_inbox" / "pending").glob("*.md"))) == 1)
    check("the step file has the contract's fields",
          all(k in step for k in ("skill", "cycle_id", "step", "timestamp", "status", "summary", "queued", "skipped",
                                  "deferred", "notes", "errors")) and step["step"] == "email-fetch"
          and step["cycle_id"] == "2026-10-03-01" and step["timestamp"][-6] in "+-", step.get("timestamp"))
    md = (runf / "email-fetch.md").read_text(encoding="utf-8")
    check("the sidecar has Candidates, Queued, Skipped, Deferred", all(f"## {s}" in md for s in
                                                                         ("Candidates", "Queued", "Skipped", "Deferred")))

    p = run("archive", "--run-folder", str(runf), "--from-dir", str(mail), cwd=proj)
    check("archive before any decision is refused", p.returncode == 2 and len(list(mail.glob("*.eml"))) == 4, p.stderr)
    p = run("queue", "--topic", "t", "--run-folder", str(runf), "--approve", "recommended", cwd=proj)
    check("queue without the session's review is refused", p.returncode == 2, p.stderr)

    review = {str(c["n"]): {"decision": "recommend" if c["url"] in (
        "https://medium.com/@koshy/restarting-your-agent-is-not-repairing-it-0a1b2c3d4e5f",
        "https://bytebytego.substack.com/p/why-state-is-the-hardest-thing",
        "https://github.com/tobi/qmd?ref=dailydev") else "skip", "reason": "test"} for c in cands}
    half = dict(list(review.items())[:3])
    (runf / "email-review.json").write_text(json.dumps(half), encoding="utf-8")
    p = run("queue", "--topic", "t", "--run-folder", str(runf), "--approve", "recommended", cwd=proj)
    check("a candidate without a decision blocks the queue", p.returncode == 2 and "no recommend/skip" in p.stderr, p.stderr)
    (runf / "email-review.json").write_text(json.dumps(review), encoding="utf-8")
    p = run("queue", "--topic", "t", "--run-folder", str(runf), "--approve", "99", cwd=proj)
    check("an unknown candidate number is refused", p.returncode == 2, p.stderr)
    p = run("queue", "--topic", "t", "--run-folder", str(runf), "--approve", "recommended", cwd=proj)
    check("queue --approve recommended exits 0", p.returncode == 0, (p.stdout + p.stderr)[-400:])
    tickets = {t.name: t.read_text(encoding="utf-8") for t in (nb / "_inbox" / "pending").glob("*.md")
               if not t.name.startswith("_")}
    sources = {line.split(":", 1)[1].strip() for txt in tickets.values() for line in txt.splitlines()
               if line.startswith("source:")}
    check("exactly the three recommended are queued (plus the one already there)",
          sources == {"https://example.org/already-queued-article",
                      "https://medium.com/@koshy/restarting-your-agent-is-not-repairing-it-0a1b2c3d4e5f",
                      "https://bytebytego.substack.com/p/why-state-is-the-hardest-thing",
                      "https://github.com/tobi/qmd?ref=dailydev"}, sorted(sources))
    bbg = next((t for t in tickets.values() if "why-state-is-the-hardest-thing" in t), "")
    raws = list((nb / "raw").glob("*.md"))
    check("the full-text email is saved to raw/ and its ticket carries raw_path",
          len(raws) == 1 and f"raw_path: raw/{raws[0].name}" in bbg and "added_by: email-fetch" in bbg, bbg[:300])
    check("the raw has the capture header and the article text",
          raws and raws[0].read_text(encoding="utf-8").startswith("# Why State is the Hardest Thing")
          and "source_url: https://bytebytego.substack.com/p/why-state-is-the-hardest-thing" in raws[0].read_text(encoding="utf-8")
          and "State is the hardest part" in raws[0].read_text(encoding="utf-8")
          and "[the Raft paper](" in raws[0].read_text(encoding="utf-8"))
    step = json.loads((runf / "email-fetch.json").read_text(encoding="utf-8"))
    check("the step records 3 queued and the rest skipped as not approved",
          step["summary"]["queued"] == 3 and step["reviewed"] is True
          and sum(1 for r in step["skipped"] if r["reason"].startswith("not approved")) == len(cands) - 3, step["summary"])

    p = run("archive", "--run-folder", str(runf), "--from-dir", str(mail), cwd=proj)
    check("archive after the decision moves every email to the done folder",
          p.returncode == 0 and not list(mail.glob("*.eml")) and len(list((mail / "read").glob("*.eml"))) == 4,
          p.stdout + p.stderr)
    p = run("archive", "--run-folder", str(runf), "--from-dir", str(mail), cwd=proj)
    check("a second archive is a no-op", p.returncode == 0 and '"archived": 0' in p.stdout, p.stdout + p.stderr)

    # A second label pass finds nothing new once the emails are archived.
    run2 = runf.parent / "2026-10-03-02"
    p = run("fetch", "--topic", "t", "--run-folder", str(run2), "--from-dir", str(mail), cwd=proj)
    check("the next fetch sees no archived email", p.returncode == 0 and '"emails_seen": 0' in p.stdout, p.stdout + p.stderr)

    # Task #76: HubSpot's /e3t/ tracker (Towards Data Science) answers 200 with a JavaScript page whose own
    # link is the redirect. A local server plays the tracker, so the real resolver runs with no internet.
    import http.server
    import threading

    class Tracker(http.server.BaseHTTPRequestHandler):
        def log_message(self, *a):
            pass

        def do_GET(self):
            base = f"http://127.0.0.1:{self.server.server_port}"
            hop = f"{base}/events/public/v1/encoded/track/tc/L2/"
            pages = {
                "/e3t/Ctc/article": f'<script>var u="{hop}art?_ud=1&amp;_jss=-2";var v="{hop}art?_ud=1&amp;_jss=0";</script>',
                "/e3t/Ctc/home": f'<script>var v="{hop}home?_jss=0";</script>',
                "/e3t/Ctc/nohop": "<script>fingerprint()</script>",
            }
            moves = {"/events/public/v1/encoded/track/tc/L2/art": "/2026/text-watermarking-in-python/?utm_campaign=tds&_hsenc=p2A",
                     "/events/public/v1/encoded/track/tc/L2/home": "/?utm_campaign=tds"}
            path = self.path.split("?")[0]
            hits[path] = hits.get(path, 0) + 1
            if path == "/e3t/Ctc/blocked" or (path == "/e3t/Ctc/busy" and hits[path] == 1):
                self.send_response(429)  # a rate limit: the first ask for /busy, every ask for /blocked
                self.send_header("Retry-After", "0")
                self.send_header("Content-Type", "text/html")
                self.send_header("Content-Length", "16")
                self.end_headers()
                self.wfile.write(b"Checking browser")
                return
            if path == "/e3t/Ctc/busy":
                path = "/e3t/Ctc/article"
            if path in pages:
                body = pages[path].encode()
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
            elif path in moves:
                self.send_response(307)
                self.send_header("Location", base + moves[path])
                self.end_headers()
            else:
                self.send_response(200)
                self.send_header("Content-Type", "text/html")
                self.send_header("Content-Length", "2")
                self.end_headers()
                self.wfile.write(b"ok")

    hits: dict[str, int] = {}
    srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Tracker)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    t_base = f"http://127.0.0.1:{srv.server_port}"
    tds_mail = tmp / "mail-tds"
    tds_mail.mkdir()
    (tds_mail / "tds.eml").write_bytes(eml("Jev put to the test against LLMs", "Towards Data Science <newsletter@towardsdatascience.com>", html=f"""
<html><body>
<a href="{t_base}/e3t/Ctc/home">Towards Data Science</a>
<a href="{t_base}/e3t/Ctc/article">Text Watermarking in Python: Catch Whoever Copies Your Writing</a>
<a href="{t_base}/e3t/Ctc/article">Read Article</a>
<a href="{t_base}/e3t/Ctc/nohop">A link whose tracker page carries no hop</a>
<a href="{t_base}/e3t/Ctc/busy">The same story, its tracker rate-limited once</a>
<a href="{t_base}/e3t/Ctc/blocked">A story whose tracker stays rate-limited</a>
</body></html>"""))
    run3 = runf.parent / "2026-10-03-03"
    env_net = {k: v for k, v in os.environ.items() if k not in ("WIKI_GMAIL_RESOLVE_MAP", "HTTP_PROXY", "HTTPS_PROXY",
                                                                 "http_proxy", "https_proxy")}
    p = subprocess.run([sys.executable, str(GMAIL), "fetch", "--topic", "t", "--run-folder", str(run3),
                        "--from-dir", str(tds_mail)], cwd=proj, capture_output=True, text=True, encoding="utf-8",
                       env={**env_net, "PYTHONIOENCODING": "utf-8", "NO_PROXY": "127.0.0.1"})
    srv.shutdown()
    check("the TDS fetch exits 0", p.returncode == 0, (p.stdout + p.stderr)[-400:])
    step3 = json.loads((run3 / "email-fetch.json").read_text(encoding="utf-8")) if p.returncode == 0 else {}
    c3 = step3.get("candidates", [])
    check("an /e3t/ tracker resolves through its page's hop to the article, tracking stripped",
          [c["url"] for c in c3] == [f"{t_base}/2026/text-watermarking-in-python/"], [c["url"] for c in c3])
    check("its title is the headline; the 'Read Article' button and the once-rate-limited link are the same candidate",
          len(c3) == 1 and c3[0]["title"] == "Text Watermarking in Python: Catch Whoever Copies Your Writing"
          and hits.get("/e3t/Ctc/busy") == 2, (c3, hits))
    check("the tracker that hops to the home page is dropped as junk", step3.get("summary", {}).get("junk_dropped") == 1,
          step3.get("summary"))
    d3 = {r["url"].rsplit("/", 1)[-1]: r["reason"] for r in step3.get("deferred", [])}
    check("a tracker page with no hop is deferred with the reason, never offered",
          "page, not a redirect" in d3.get("nohop", ""), d3)
    check("a tracker that stays rate-limited is retried twice, then deferred as rate-limited",
          d3.get("blocked") == "tracker rate-limited (429)" and hits.get("/e3t/Ctc/blocked") == 3 and len(d3) == 2,
          (d3, hits))

    # The hop picker on its own: HubSpot writes the link twice; the _jss=0 one is taken, &amp; unescaped.
    import importlib.util
    spec = importlib.util.spec_from_file_location("wfg", GMAIL)
    wfg = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(wfg)
    page = ('<script>a="https://n.example/events/public/v1/encoded/track/tc/X?_ud=1&amp;_jss=-2";'
            'b="https://n.example/events/public/v1/encoded/track/tc/X?_ud=1&amp;_jss=0"</script>')
    check("interstitial_hop takes the _jss=0 link, unescaped",
          wfg.interstitial_hop(page) == "https://n.example/events/public/v1/encoded/track/tc/X?_ud=1&_jss=0",
          wfg.interstitial_hop(page))
    check("interstitial_hop finds nothing on an ordinary page", wfg.interstitial_hop("<p>hello</p>") is None)
    check("an /e3t/ link on a newsletter host needs resolving",
          wfg.needs_resolving("https://newsletter.towardsdatascience.com/e3t/Ctc/L2+113/abc"))
    # Found resolving cycle 2026-10-05-01's 139 real TDS links: articles were dropped, profiles kept.
    check("a Towards Data Science article (off Medium since 2025) is not dropped as a Medium page",
          wfg.junk_reason("https://towardsdatascience.com/text-watermarking-in-python-catch-whoever-copies-your-writing/",
                          "Text Watermarking") is None)
    profiles = ["https://hachyderm.io/@towardsdatascience", "https://www.threads.com/@towardsdatascience",
                "https://bsky.app/profile/towardsdatascience.com", "https://towardsdatascience.com/author/someone/",
                "https://towardsdatascience.com/tag/llm/"]
    check("Mastodon, Threads and Bluesky profiles, author and tag pages are dropped",
          all(wfg.junk_reason(u, "") for u in profiles), {u: wfg.junk_reason(u, "") for u in profiles})
    posts = ["https://bsky.app/profile/someone.bsky.social/post/3kabc", "https://www.threads.com/@someone/post/C0ffee",
             "https://medium.com/@koshy/restarting-your-agent-is-not-repairing-it-0a1b2c3d4e5f"]
    check("an image's file-name alt text is never the title; the URL's slug is",
          wfg._title_from(["1788876230373_1b47e6 copy"], "https://towardsdatascience.com/software-design-in-the-age-of-ai/")
          == "software design in the age of ai"
          and wfg._title_from(["Screenshot-2026-08-22-at-8.21.59-PM", "Jev vs. LLMs"], "https://x.example/a/") == "Jev vs. LLMs"
          and wfg._title_from(["FridgeFlow"], "https://x.example/a/") == "FridgeFlow")
    check("a trailing double slash is made single",
          wfg.clean_url("https://towardsdatascience.com/software-design-in-the-age-of-ai//")
          == "https://towardsdatascience.com/software-design-in-the-age-of-ai/")
    check("a Bluesky or Threads post, and a Medium story, are kept",
          not any(wfg.junk_reason(u, "") for u in posts), {u: wfg.junk_reason(u, "") for u in posts})

failed = [n for ok, n in results if not ok]
for ok, n in results:
    print(("PASS " if ok else "FAIL ") + n)
print(f"\n{len(results) - len(failed)}/{len(results)} passed")
sys.exit(1 if failed else 0)
