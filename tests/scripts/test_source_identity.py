#!/usr/bin/env python3
"""Checks for one source identity across every duplicate check (task #96 step 1, 2026-10-11).
Never shipped.

    python tests/scripts/test_source_identity.py    # exit 0 = every check passed

Four scripts decided "is this the same source" four ways: filing (wiki-update.py), the
Drive and Gmail steps (url_dedup_key), the queue (wiki-list-add.py, exact text) and the
dequeue (wiki-dequeue.py, which cut the query off, so every youtube.com/watch?v= link
matched every other). A post that arrived as twitter.com after an x.com entry, or a
YouTube Short after the watch link, was filed twice. `_source_identity.source_key()` is
the one rule now; the rules come from Chubby Skills' tools/source_identity.py
(agentic-design research/tooling/chubby-skills-...).
"""
from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))
results: list[tuple[bool, str]] = []


def check(name: str, ok: bool, detail: object = ""):
    results.append((bool(ok), name + (f"  [{detail}]" if not ok and detail != "" else "")))


def load(name: str):
    spec = importlib.util.spec_from_file_location(name.replace("-", "_"), SCRIPTS / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


try:
    from _source_identity import source_key
except ImportError as exc:  # the module does not exist yet: every key check fails
    print(f"FAIL import _source_identity: {exc}")
    def source_key(url):  # noqa: E306
        return f"<no module>{url}"

# ── the rule: the same source in any link form has one key ──
SAME = {
    "an X post on x.com, twitter.com, mobile and with share tags": [
        "https://x.com/karpathy/status/1886192184808149383",
        "https://twitter.com/karpathy/status/1886192184808149383",
        "https://mobile.twitter.com/karpathy/status/1886192184808149383?s=20&t=abc",
        "http://www.twitter.com/karpathy/status/1886192184808149383/",
        "https://x.com/i/web/status/1886192184808149383",
        "https://x.com/karpathy/status/1886192184808149383/photo/1",
        "https://x.com/karpathy/status/1886192184808149383/video/1",
        "https://x.com/karpathy/status/1886192184808149383#m",
    ],
    "a YouTube video as watch, youtu.be, Shorts, embed, live, mobile, with a start time": [
        "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        "https://youtu.be/dQw4w9WgXcQ?si=abc123",
        "https://www.youtube.com/shorts/dQw4w9WgXcQ",
        "https://www.youtube.com/embed/dQw4w9WgXcQ?start=30",
        "https://www.youtube.com/live/dQw4w9WgXcQ",
        "https://m.youtube.com/watch?v=dQw4w9WgXcQ&t=42s",
        "https://www.youtube.com/watch?t=42&v=dQw4w9WgXcQ&feature=share",
        "https://music.youtube.com/watch?v=dQw4w9WgXcQ",
    ],
    "an article with click and mail tracking": [
        "https://example.com/post/agents",
        "https://example.com/post/agents?utm_source=x&utm_medium=social",
        "https://example.com/post/agents?fbclid=IwAR0abc",
        "https://example.com/post/agents?gclid=Cj0K&mc_cid=1&mc_eid=2",
        "https://www.example.com/post/agents/#section",
        "http://example.com/post/agents?ref=newsletter&source=rss",
        "https://example.com/post/agents?_hsenc=p2&_hsmi=9",
    ],
    "an arXiv paper as abs, pdf, html and with a version": [
        "https://arxiv.org/abs/2502.12110",
        "https://arxiv.org/pdf/2502.12110",
        "https://arxiv.org/pdf/2502.12110v2",
        "https://arxiv.org/html/2502.12110v1",
    ],
    "a GitHub repo in any case, with .git": [
        "https://github.com/NousResearch/hermes-agent",
        "https://github.com/nousresearch/hermes-agent/",
        "https://github.com/NousResearch/hermes-agent.git",
    ],
    "a GitHub file on any branch": [
        "https://github.com/u/r/blob/main/skills/a/SKILL.md",
        "https://github.com/u/r/blob/dev/skills/a/SKILL.md",
        "https://github.com/u/r/tree/main/skills/a/SKILL.md",
    ],
    "an Instagram post as /p/ and /reel/, with share tags": [
        "https://www.instagram.com/p/DAbc123XyZ/",
        "https://www.instagram.com/reel/DAbc123XyZ/?igsh=abc",
        "https://instagram.com/p/DAbc123XyZ?img_index=3",
    ],
}
for what, urls in SAME.items():
    keys = {source_key(u) for u in urls}
    check(f"one key: {what}", len(keys) == 1, sorted(keys))

# ── and different sources never share one ──
DIFFERENT = {
    "two YouTube videos": ["https://www.youtube.com/watch?v=dQw4w9WgXcQ", "https://www.youtube.com/watch?v=9bZkp7q19f0"],
    "two X posts by one author": ["https://x.com/a/status/111", "https://x.com/a/status/222"],
    "a repo and a file in it": ["https://github.com/u/r", "https://github.com/u/r/blob/main/README.md"],
    "two files in one repo": ["https://github.com/u/r/blob/main/skills/codex-first/SKILL.md",
                              "https://github.com/u/r/blob/main/skills/codex-review/SKILL.md"],
    "two arXiv papers": ["https://arxiv.org/abs/2502.12110", "https://arxiv.org/abs/2502.12111"],
    "a page whose query is the content": ["https://example.com/item?id=1", "https://example.com/item?id=2"],
    "two Instagram posts differing only in case": ["https://www.instagram.com/p/DAbc123XyZ/",
                                                   "https://www.instagram.com/p/dabc123xyz/"],
    "an X profile and a post": ["https://x.com/karpathy", "https://x.com/karpathy/status/1886192184808149383"],
}
for what, (a, b) in DIFFERENT.items():
    check(f"different keys: {what}", source_key(a) != source_key(b), (source_key(a), source_key(b)))

check("a key ignores http vs https and a trailing slash",
      source_key("http://example.com/a/") == source_key("https://example.com/a"))
check("an internal:// source compares as given", source_key("internal://session/2026-10-11-x") == "internal://session/2026-10-11-x")
check("an empty source has an empty key", source_key("") == "" and source_key(None) == "")
check("quotes and angle brackets around a frontmatter value are ignored",
      source_key('"https://x.com/a/status/111"') == source_key("<https://twitter.com/a/status/111>"))

# ── each duplicate check uses it ──
with tempfile.TemporaryDirectory() as td:
    tmp = Path(td)
    nb = tmp / "notebooks" / "t"
    (nb / "wiki" / "research").mkdir(parents=True)
    (nb / "_inbox" / "proposed").mkdir(parents=True)
    (nb / "_inbox" / "pending").mkdir(parents=True)
    (nb / "wiki" / "research" / "post.md").write_text(
        "---\nsource_url: https://x.com/karpathy/status/1886192184808149383\n---\n", encoding="utf-8")
    (nb / "wiki" / "research" / "video.md").write_text(
        "---\nsource_url: https://www.youtube.com/watch?v=dQw4w9WgXcQ\n---\n", encoding="utf-8")
    (tmp / "linked-notebooks.json").write_text(json.dumps({"notebooks": {"t": {"root": "notebooks/t"}}}), encoding="utf-8")
    proj = tmp / "project"
    (proj / ".claude").mkdir(parents=True)
    (proj / ".claude" / "wiki-config.json").write_text(json.dumps(
        {"notebook": "t", "registry": (tmp / "linked-notebooks.json").as_posix()}), encoding="utf-8")
    env = {**os.environ, "PYTHONIOENCODING": "utf-8", "HOME": str(tmp), "USERPROFILE": str(tmp)}

    def run(script: str, *a):
        return subprocess.run([sys.executable, str(SCRIPTS / script), *a], cwd=proj, capture_output=True,
                              text=True, encoding="utf-8", env=env)

    # filing: wiki-update.py finds the entry under another link form
    wu = load("wiki-update")
    hit = wu.find_existing_by_url(nb / "wiki", "https://twitter.com/karpathy/status/1886192184808149383?s=20")
    check("filing: a twitter.com link finds the x.com entry", hit is not None and hit.name == "post.md", hit)
    hit = wu.find_existing_by_url(nb / "wiki", "https://www.youtube.com/shorts/dQw4w9WgXcQ")
    check("filing: a Shorts link finds the watch entry", hit is not None and hit.name == "video.md", hit)
    hit = wu.find_existing_by_url(nb / "wiki", "https://www.youtube.com/watch?v=9bZkp7q19f0")
    check("filing: another video is not a duplicate", hit is None, hit)

    # Drive and Gmail: one key per source
    drive = load("wiki-fetch-drive-folder")
    check("Drive/Gmail: x.com and twitter.com links share a key",
          drive.url_dedup_key("https://x.com/a/status/111") == drive.url_dedup_key("https://twitter.com/a/status/111?s=20"))
    check("Drive/Gmail: a click-tagged link shares the plain link's key",
          drive.url_dedup_key("https://example.com/p?fbclid=1") == drive.url_dedup_key("https://example.com/p"))

    # the queue: wiki-list-add.py refuses a source already in the wiki under another link form
    p = run("wiki-list-add.py", "--topic", "t", "--source",
            "https://mobile.twitter.com/karpathy/status/1886192184808149383?s=20")
    queued = sorted(x.name for x in (nb / "_inbox" / "pending").glob("*.md") if not x.name.startswith("_"))
    check("queue: a twitter.com link to a filed x.com post is not queued",
          p.returncode == 0 and "Already present in wiki/" in p.stdout and not queued, (p.stdout + p.stderr)[-300:])
    p = run("wiki-list-add.py", "--topic", "t", "--source", "https://www.youtube.com/watch?v=9bZkp7q19f0")
    queued = sorted(x.name for x in (nb / "_inbox" / "pending").glob("*.md") if not x.name.startswith("_"))
    check("queue: a new video is queued", p.returncode == 0 and len(queued) == 1, (p.stdout + p.stderr)[-300:])
    p = run("wiki-list-add.py", "--topic", "t", "--source", "https://youtu.be/9bZkp7q19f0?si=zz")
    queued = sorted(x.name for x in (nb / "_inbox" / "pending").glob("*.md") if not x.name.startswith("_"))
    check("queue: the same video as youtu.be is already pending",
          "Already present in pending/" in p.stdout and len(queued) == 1, (p.stdout + p.stderr)[-300:])

    # the dequeue: only tickets whose source is really ingested move
    pend = nb / "_inbox" / "pending"
    for x in pend.glob("*.md"):
        x.unlink()
    for name, url in (("3-new-video.md", "https://www.youtube.com/watch?v=9bZkp7q19f0"),
                      ("3-same-video.md", "https://youtu.be/dQw4w9WgXcQ?si=abc"),
                      ("3-same-post.md", "https://twitter.com/karpathy/status/1886192184808149383")):
        (pend / name).write_text(f"---\nsource: {url}\npriority: 3\n---\n\n# x\n", encoding="utf-8")
    p = run("wiki-dequeue.py", "--topic", "t")
    done = sorted(x.name for x in (nb / "_inbox" / "done").glob("*.md")) if (nb / "_inbox" / "done").exists() else []
    check("dequeue: a video not in the wiki stays pending (every watch?v= link used to match)",
          (pend / "3-new-video.md").exists(), done)
    check("dequeue: the filed video and post, under other link forms, move to done/",
          done == ["3-same-post.md", "3-same-video.md"], (done, (p.stdout + p.stderr)[-300:]))

# ── the module ships with the scripts ──
it = load("_install_tooling")
check("the installer ships _source_identity.py with the scripts",
      "_source_identity.py" in it.TOOLING_HELPER_SCRIPTS and "_source_identity.py" in it.SHARED_HELPER_SCRIPTS)

failed = [n for ok, n in results if not ok]
for ok, n in results:
    print(("PASS " if ok else "FAIL ") + n)
print(f"\n{len(results) - len(failed)}/{len(results)} passed")
sys.exit(1 if failed else 0)
