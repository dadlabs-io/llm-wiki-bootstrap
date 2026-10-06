# wiki-update — fetchers

Step 1 of the `/wiki-update` flow, by source. Every fetcher prints `raw_path=<path>`; keep it for step 8. After fetching, continue at step 2 of the flow in `SKILL.md`. A raw that is already saved (handed over, or from a PDF the user saved) needs no fetcher: start at step 2.

## Which fetcher

| Source | Fetcher |
|---|---|
| `youtube.com`, `youtu.be` | `wiki-fetch-youtube.py` ([YouTube](#youtube)); a video with no captions: `wiki-transcribe.py` |
| An Instagram post, `instagram.com/p/…` | `wiki-fetch-page.py` ([Instagram](#instagram)): the caption and every slide's text, no login |
| An Instagram reel, a podcast episode, an X video, a local audio or video file | `wiki-transcribe.py` ([Speech](#speech-reels-podcasts-video-without-captions)): the caption and a transcript |
| A PDF: a URL ending `.pdf`, `arxiv.org/pdf/…`, or a local `.pdf` | `wiki-fetch-pdf.py` ([PDF](#pdf)) |
| `x.com`, `twitter.com` | `wiki-fetch-tweet.js` ([X](#x--twitter)); the page fetcher only as its fallback |
| `medium.com`, `*.medium.com`, Medium publications on their own domains (`levelup.gitconnected.com`, `pub.towardsai.net`, …) | [Page fetcher](#pages-that-need-javascript). Direct HTTP gets 403, and Medium's Cloudflare often blocks the page fetcher too: then [Save as PDF](#pages-no-fetcher-can-get). |
| `threads.com`, `bsky.app`, `linkedin.com`, public `notion.so` pages | [Page fetcher](#pages-that-need-javascript) |
| `github.com` repos and files, `gist.github.com` | `wiki-update.py --fetch-only` (rewrites to the raw file; a bare repo URL gets its README) |
| Anything else | `wiki-update.py --fetch-only` |

`--fetch-only` saves an HTML page as Markdown (MarkItDown, in the scripts' environment): headings, links, lists and quotes are kept, and so are the site's menus and footer, so read past them. It prints `Converted: Markdown`; `Converted: plain text (<reason>)` means MarkItDown was unavailable and the page was saved as before, without links or headings.

A raw under about 1 KB, one that is mostly navigation, or one that says "enable JavaScript" came from the wrong fetcher: use the [page fetcher](#pages-that-need-javascript). An X post is short by nature: judge it by whether the text reads complete, not by its size.

## YouTube

```bash
uv run --project {{WIKI_SCRIPTS_DIR}} python {{WIKI_SCRIPTS_DIR}}/wiki-fetch-youtube.py --topic <topic> --url <url> --ingested-by claude-code
```

Runs on the host; its `yt_dlp` package comes with the scripts' uv environment.

**Check the transcript before you blockquote it.** Auto-captions mis-hear this wiki's vocabulary systematically: "Claude Code" arrives as "Cloud Code" or "Quad Code", `CLAUDE.md` as "quadmd", "CloudMD" or "clawed MD". Correct the entry's own key terms by context before placing a passage in a `>` quote, disclose the correction once in a dated transcription note near the top of the entry, and paraphrase (no blockquote) any passage you cannot disambiguate. Doctrine: authoring best practices, principle 5.

**No captions** (the fetcher stops with "no subtitle file produced"): transcribe the speech instead, `wiki-transcribe.py --url <url>` ([Speech](#speech-reels-podcasts-video-without-captions)).

A video's entry is as long as its content deserves: one good idea makes a short entry, a dense talk a full breakdown. Useful sections: key insights, notable quotes, when to watch it.

## PDF

```bash
uv run --project {{WIKI_SCRIPTS_DIR}} python {{WIKI_SCRIPTS_DIR}}/wiki-fetch-pdf.py --topic <topic> --source <url-or-local-pdf> --ingested-by claude-code
```

Runs on the host: text per page through `pdftotext` (in Git Bash on Windows, poppler elsewhere), falling back to `pypdf` (in the scripts' uv environment) on pages where the text is poor; OCR only if tesseract is installed. It saves the raw with the page count and extraction figures and copies the PDF beside it.

## X / Twitter

```bash
node {{WIKI_SCRIPTS_DIR}}/wiki-fetch-tweet.js --topic <topic> --url <url> --vault <vault_root> --ingested-by claude-code
```

One HTTPS request to the public syndication API, on the host: no login, no browser. `--vault` is the vault root, the folder that holds the notebook's folder. When it fails (a deleted or protected post, a block), fetch that one URL with the [page fetcher](#pages-that-need-javascript) instead of retrying. If the raw ends with the note about a long-form post and the text reads cut off, fetch that URL with the page fetcher too. A post whose substance is a video: `wiki-transcribe.py --url <url>`.

## Pages no fetcher can get

A page behind a paywall or a member wall (Medium member-only stories), behind a login, or on a site that blocks the fetcher (a Cloudflare "you have been blocked" page) has one path: the user saves it. Medium is the usual case, not a special one.

- **Never copy a page out of the browser into `raw/`** (2026-10-05). The session may open a page in the user's browser (Claude in Chrome) to read it and judge it, for triage or to tell the user whether it is worth saving, but never saves its text as a raw.
- **Never fetch it another way** (Mark, 2026-10-05): no archive copy, no cache, no proxy, and never the user's password. The page fetcher flags a paywalled or nearly empty page (`paywall=suspected`, and a `paywall:` line in the raw's header) instead of working around it; a site's block page counts the same. That raw holds no article: delete it (nothing cites it yet).
- **Save as PDF.** Leave the item where it is (its queue ticket or intake bucket) with the reason "save as PDF: <paywall | login | blocked>", and tell the user which page it is. In a cycle, the report lists every such page under **Save as PDF** with its link. The user opens it in Chrome, Print → Save as PDF, into the Drive folder `<drive.parent_folder>/<drive.subfolder>` (`__FOR CLAUDE/<notebook>` by default); the next cycle's Drive step saves the PDF as a raw and queues it, so it is filed with its full text. A PDF the user hands over directly is a local file ([PDF](#pdf)).

A spawned `wiki-ingester` worker meeting such a page marks the item failed "save as PDF" and moves on.

## Pages that need JavaScript

For pages that show their text only once JavaScript runs (Threads, LinkedIn, public Notion pages, Bluesky, Medium) and as the fallback for X. It runs on this machine, in headless Chromium (Playwright, in the scripts' environment; the install fetches the browser):

```bash
uv run --project {{WIKI_SCRIPTS_DIR}} python {{WIKI_SCRIPTS_DIR}}/wiki-fetch-page.py --topic <topic> --url <url> --ingested-by claude-code
```

The page is saved as Markdown with its site chrome (login banners, sidebars, footers): read past it to the post itself. `paywall=suspected` means the page looked paywalled or nearly empty: see [Pages no fetcher can get](#pages-no-fetcher-can-get). At most two run at once on the machine; a third waits. Exit 3 names the command when Chromium is missing.

## Instagram

An Instagram post goes through the same fetcher (it recognises the URL), with no login: the raw holds the post's whole caption and the text of every carousel slide, clicked through, and never the comments. Each slide's text is Instagram's own automatic recognition of the image, which garbles some words and sometimes finds none ("May be an image of magazine and text"), so each slide image is saved in `<raw>-slides/` and named under its slide. **Read the image** wherever a slide says Instagram recognised no text, or its text reads garbled, and quote only what you read. A dense single-image post is common: its whole substance is the image.

Triage on the caption first: many posts are engagement bait ("comment AGENT and I'll DM you") and need no slides read.

## Speech: reels, podcasts, video without captions

```bash
uv run --project {{WIKI_SCRIPTS_DIR}} python {{WIKI_SCRIPTS_DIR}}/wiki-transcribe.py --topic <topic> --url <url> --ingested-by claude-code
```

Local Whisper (faster-whisper): yt-dlp fetches the audio and the post's caption, and the raw holds the caption and a timestamped transcript, never the comments. On an NVIDIA GPU it runs large-v3-turbo (a one-minute reel in about 5 s; it takes one of the search's GPU slots); without one, the CPU runs `small`, and audio over 20 minutes exits 4 with the override named (`--max-cpu-minutes 0`). `--file <path>` transcribes a local recording. Music with no speech says so. The same auto-caption check as [YouTube](#youtube) applies before you blockquote a transcript.

A reel that will not download (yt-dlp's "empty media response": Instagram throttling, or a private reel) gets one more try after your other work; if that fails too, report it and leave the item, never with cookies or a login.
