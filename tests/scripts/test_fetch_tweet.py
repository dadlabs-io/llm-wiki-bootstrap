#!/usr/bin/env python3
"""Checks for wiki-fetch-tweet.js (the X fetcher, public syndication API). Never shipped. No network: the
payloads below are trimmed from real syndication responses fetched 2026-10-11, and the script's raw is built
from them through its exported buildRaw(). Needs `node` on PATH.

    uv run python tests/scripts/test_fetch_tweet.py    # exit 0 = every check passed
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "wiki-fetch-tweet.js"

results: list[tuple[bool, str]] = []


def check(name: str, ok: bool, detail: object = ""):
    results.append((bool(ok), name + (f"  [{detail}]" if not ok and detail != "" else "")))


# Andrew Ng's X Article, x.com/AndrewYNg/status/2090840747738374568: the API gives the title, the cover
# and the opening only; `text` is a bare t.co link to the article.
ARTICLE = {
    "__typename": "Tweet",
    "created_at": "2026-09-01T16:02:11.000Z",
    "favorite_count": 1200,
    "conversation_count": 80,
    "id_str": "2090840747738374568",
    "text": "The most important skills in Building and Deploying AI Applications. https://t.co/IyWIKLIzeM",
    "user": {"name": "Andrew Ng", "screen_name": "AndrewYNg"},
    "entities": {"urls": [{"display_url": "x.com/i/article/2090…",
                           "expanded_url": "http://x.com/i/article/2090836273036763142",
                           "url": "https://t.co/IyWIKLIzeM"}]},
    "article": {
        "cover_media": {"media_info": {"__typename": "ApiImage",
                                       "original_img_url": "https://pbs.twimg.com/media/HQQk9jqboAEpbvE.jpg"}},
        "preview_text": "I previously wrote about our AI Engineering Skills Map, with the highest level skills being "
                        "(i) Building and deploying AI applications, (ii) Software engineering fundamentals, "
                        "(iii) Using coding",
        "rest_id": "2090836273036763142",
        "title": "AI Engineering Skills Map: Building and Deploying AI Applications",
    },
}
ARTICLE_URL = "https://x.com/AndrewYNg/status/2090840747738374568"

# A plain post with one photo and one video, x.com/GithubProjects/status/2075588383297171604 (the video
# entry is added to check videos keep their own URL).
PHOTO = {
    "__typename": "Tweet",
    "created_at": "2026-07-12T10:00:00.000Z",
    "id_str": "2075588383297171604",
    "text": "PraisonAI lets you deploy a multi-agent system in a few lines.",
    "user": {"name": "GitHub Projects Community", "screen_name": "GithubProjects"},
    "mediaDetails": [
        {"type": "photo", "media_url_https": "https://pbs.twimg.com/media/HM34opBaoAAfAmT.jpg"},
        {"type": "video", "media_url_https": "https://pbs.twimg.com/ext_tw_video_thumb/1/pu/img/a.jpg",
         "video_info": {"variants": [{"url": "https://video.twimg.com/ext_tw_video/1/pu/vid/a.mp4"}]}},
    ],
}
PHOTO_URL = "https://x.com/GithubProjects/status/2075588383297171604"

# A long post (over 280 characters), x.com/DanKornas/status/2081497527690678357: `note_tweet` holds only an id,
# and `text` is the opening cut off mid-sentence with a t.co link to the rest. The page fetcher gets nothing
# from X without a login (0 characters, 2026-10-11).
LONG = {
    "__typename": "Tweet",
    "created_at": "2026-08-02T14:00:00.000Z",
    "id_str": "2081497527690678357",
    "text": "Large coding requests can turn an AI assistant into a black box. Break the work into checkpoints you "
            "can review.\n\nAI Dev Tasks is a set of Markdown prompt files for developers using AI coding "
            "assistants to plan and implement features.\n\nIt helps you move from feature idea to "
            "https://t.co/ui5kzl2J2e",
    "user": {"name": "Dan Kornas", "screen_name": "DanKornas"},
    "note_tweet": {"id": "Tm90ZVR3ZWV0UmVzdWx0czoyMDgxNDk3NTI3NTkwMDI3MjY0"},
    "mediaDetails": [{"type": "photo", "media_url_https": "https://pbs.twimg.com/media/HOL293fWEAAvzVn.png"}],
}
LONG_URL = "https://x.com/DanKornas/status/2081497527690678357"

HARNESS = """
const m = require(process.argv[1]);
const input = JSON.parse(require('fs').readFileSync(0, 'utf-8'));
process.stdout.write(JSON.stringify(m.buildRaw(input.tweet, {url: input.url, ingestedBy: 'test'})));
"""


def build(tweet: dict, url: str) -> dict:
    proc = subprocess.run(["node", "-e", HARNESS, str(SCRIPT)], input=json.dumps({"tweet": tweet, "url": url}),
                          capture_output=True, text=True, encoding="utf-8")
    if proc.returncode != 0:
        return {"error": proc.stderr.strip()[-400:]}
    return json.loads(proc.stdout)


def frontmatter(content: str) -> dict:
    if not content.startswith("---\n"):
        return {}
    return yaml.safe_load(content.split("\n---\n", 1)[0][4:]) or {}


# --- An X Article ---
art = build(ARTICLE, ARTICLE_URL)
check("buildRaw is exported and builds an Article's raw", "content" in art, art.get("error", ""))
content = art.get("content", "")
fm = frontmatter(content)
check("an Article's title is the article's own title, not the t.co text",
      "AI Engineering Skills Map: Building and Deploying AI Applications" in art.get("title", "")
      and "t.co" not in art.get("title", ""), art.get("title"))
check("the frontmatter parses", bool(fm), content[:300])
check("an Article is typed x-article", fm.get("type") == "x-article", fm.get("type"))
check("an Article raw is marked a preview", fm.get("completeness") == "preview", fm.get("completeness"))
check("the frontmatter names the article's own URL",
      fm.get("article_url") == "https://x.com/i/article/2090836273036763142", fm.get("article_url"))
check("the body carries the preview text", ARTICLE["article"]["preview_text"] in content)
check("the body carries the article title as a heading",
      "## AI Engineering Skills Map: Building and Deploying AI Applications" in content)
check("the cover image is linked at original size",
      "https://pbs.twimg.com/media/HQQk9jqboAEpbvE.jpg?name=orig" in content)
check("the body says the full text was not captured and how to get it",
      "preview" in content.lower() and "save" in content.lower() and "pdf" in content.lower())
check("the post's own text is still in the raw", ARTICLE["text"] in content)
check("the summary line reports the preview", art.get("completeness") == "preview", art.get("completeness"))

# --- A plain post with photos ---
ph = build(PHOTO, PHOTO_URL)
pc = ph.get("content", "")
pfm = frontmatter(pc)
check("a plain post builds", "content" in ph, ph.get("error", ""))
check("a plain post stays typed tweet", pfm.get("type") == "tweet", pfm.get("type"))
check("a plain post has no completeness mark (only a partial raw is marked)", "completeness" not in pfm, pfm)
check("... and reports none", ph.get("completeness") is None, ph.get("completeness"))
check("a photo is linked at original size", "https://pbs.twimg.com/media/HM34opBaoAAfAmT.jpg?name=orig" in pc)
check("a video keeps its video URL, untouched",
      "https://video.twimg.com/ext_tw_video/1/pu/vid/a.mp4" in pc and "a.mp4?name=orig" not in pc)
check("a plain post's title is its text", "PraisonAI lets you deploy" in ph.get("title", ""), ph.get("title"))

# --- A long post (note_tweet): the API gives its opening only ---
lg = build(LONG, LONG_URL)
lc = lg.get("content", "")
lfm = frontmatter(lc)
check("a long post builds", "content" in lg, lg.get("error", ""))
check("a long post stays typed tweet", lfm.get("type") == "tweet", lfm.get("type"))
check("a long post raw is marked a preview", lfm.get("completeness") == "preview", lfm.get("completeness"))
check("... and reports it", lg.get("completeness") == "preview", lg.get("completeness"))
check("its opening is kept", LONG["text"] in lc)
check("the note says only the opening was captured and to save the page as PDF",
      "preview only" in lc.lower() and "pdf" in lc.lower() and "never fetch it another way" in lc.lower(), lc[-700:])
check("the note no longer calls it an Article or sends to a Playwright recipe",
      "article" not in lc.lower().split("## media")[0].split("---", 3)[-1] and "playwright" not in lc.lower(),
      lc[-700:])

# --- A photo URL that already has a query keeps it ---
q = dict(PHOTO, mediaDetails=[{"type": "photo",
                               "media_url_https": "https://pbs.twimg.com/media/X.jpg?format=jpg&name=small"}])
qc = build(q, PHOTO_URL).get("content", "")
check("a photo URL with its own size is set to the original, not doubled",
      "X.jpg?format=jpg&name=orig" in qc and "name=small" not in qc, qc[-300:])

# --- The script still runs as a CLI (main guarded by require.main) ---
proc = subprocess.run(["node", str(SCRIPT)], capture_output=True, text=True, encoding="utf-8")
check("run with no arguments it still exits 2 with the usage error",
      proc.returncode == 2 and "--topic" in proc.stderr, (proc.returncode, proc.stderr[-200:]))

failed = [n for ok, n in results if not ok]
for ok, n in results:
    print(("PASS " if ok else "FAIL ") + n)
print(f"\n{len(results) - len(failed)}/{len(results)} passed")
sys.exit(1 if failed else 0)
