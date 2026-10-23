# wiki-update — fetchers

Step 1 of the `/wiki-update` flow, by source. Every fetcher prints `raw_path=<path>`; keep it for step 8. After fetching, continue at step 2 of the flow in `SKILL.md`. A raw that is already saved (handed over, or from a PDF the user saved) needs no fetcher: start at step 2.

## Which fetcher

| Source | Fetcher |
|---|---|
| `youtube.com`, `youtu.be` | `wiki-fetch-youtube.py` ([YouTube](#youtube)); a video with no captions: `wiki-transcribe.py` |
| An Instagram post, `instagram.com/p/…` | `wiki-fetch-page.py` ([Instagram](#instagram)): the caption, every slide image, and the slide text Instagram recognised (`slides_text: <n> of <N>`), no login |
| An Instagram reel, a podcast episode, an X video, a local audio or video file | `wiki-transcribe.py` ([Speech](#speech-reels-podcasts-video-without-captions)): the caption and a transcript |
| A PDF: a URL ending `.pdf`, an arXiv paper (`arxiv.org/abs/…`, `/pdf/…` or `/html/…`), or a local `.pdf` | `wiki-fetch-pdf.py` ([PDF](#pdf)) |
| `x.com`, `twitter.com` | `wiki-fetch-tweet.js` ([X](#x--twitter)); the page fetcher only as its fallback |
| `medium.com`, `*.medium.com`, Medium publications on their own domains (`levelup.gitconnected.com`, `pub.towardsai.net`, …) | [Page fetcher](#pages-that-need-javascript). Direct HTTP gets 403, and Medium's Cloudflare often blocks the page fetcher too: then [Save as PDF](#pages-no-fetcher-can-get). |
| `threads.com`, `bsky.app`, `linkedin.com`, public `notion.so` pages | [Page fetcher](#pages-that-need-javascript) |
| `github.com` repos and files, `gist.github.com` | `wiki-update.py --fetch-only` (rewrites to the raw file; a bare repo URL gets its README) |
| A whole GitHub repo: its docs, every SKILL.md, not only the README | `wiki-fetch-repo.py` ([Whole repository](#whole-repository)) |
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

**Subtitles rate-limited** (HTTP 429): the fetcher transcribes the audio itself and prints `Fallback: transcribed (subtitles HTTP 429)`; the raw is then a Whisper transcript, and the exit code is the transcriber's (4 on a machine with no GPU and a talk over 20 minutes: run it where there is a GPU). Don't retry the subtitles: the 429 held for days in October 2026, while the audio download was never limited.

A video's entry is as long as its content deserves: one good idea makes a short entry, a dense talk a full breakdown. Useful sections: key insights, notable quotes, when to watch it.

## PDF

```bash
uv run --project {{WIKI_SCRIPTS_DIR}} python {{WIKI_SCRIPTS_DIR}}/wiki-fetch-pdf.py --topic <topic> --source <url-or-local-pdf> --ingested-by claude-code
```

Runs on the host: text per page through `pdftotext` in reading order, column by column, so a quote that runs over several lines of a two-column paper is in the raw (2026-10-10; it used `-layout` before, which interleaved the columns: a raw saved earlier may still be mixed, so check a quote that is not found against the PDF beside it) (in Git Bash on Windows, poppler elsewhere), falling back to `pypdf` (in the scripts' uv environment) on pages where the text is poor; OCR only if tesseract is installed. It saves the raw with the page count and extraction figures and copies the PDF beside it. An arXiv `abs` or `html` link is fetched as its PDF and kept as the raw's `source_url`; `wiki-update.py --fetch-only` refuses an arXiv paper link and prints this command (2026-10-12: an abs link had saved the abstract page alone).

## Whole repository

When the repo itself is the source (a skills pack, a tool whose docs say what it does), not just its README:

```bash
uv run --project {{WIKI_SCRIPTS_DIR}} python {{WIKI_SCRIPTS_DIR}}/wiki-fetch-repo.py --topic <topic> --url https://github.com/<owner>/<repo> --ingested-by claude-code
```

A shallow clone at the current commit: the README first, then every Markdown or reStructuredText file under `## File: <path>`, so every quote is checked against the raw; code, tests and fixtures, `.github/`, vendored and build folders, other languages' copies and boilerplate (code of conduct, security policy) are left out. The header records the commit and the file list: a later snapshot is filed with `--revises`. Over 1,500 KB it stops (exit 4) and lists the files by size: raise `--max-kb` when the whole repo really is the source, or fetch the files that matter. Use it when the user asks for the whole repo or a ticket says so; a bare repo link otherwise goes through `--fetch-only` and its README (2026-10-12: two whole-repo raws had been built by hand). A raw this size is read in full before drafting, split across helper agents with `wiki-raw-parts.py` when it will not fit (`SKILL.md`, step 2).

## X / Twitter

```bash
node {{WIKI_SCRIPTS_DIR}}/wiki-fetch-tweet.js --topic <topic> --url <url> --ingested-by claude-code
```

One HTTPS request to the public syndication API, on the host: no login, no browser. `--vault` is the vault root, the folder that holds the notebook's folder. When it fails (a deleted or protected post, a block), fetch that one URL with the [page fetcher](#pages-that-need-javascript) instead of retrying. A post whose substance is a video: `wiki-transcribe.py --url <url>`. Photos are linked at their original size.

**An X Article** (a long-form post with a title and a cover) **or a long post** (over 280 characters) prints `completeness=preview` and a warning: the public API gives an Article's title, cover image and opening lines, and a long post's first 280 characters and a link, and the raw is marked `completeness: preview` (an Article's is typed `x-article`). The full text needs a logged-in session, and the page fetcher gets nothing from X (2026-10-11), so it is a [page no fetcher can get](#pages-no-fetcher-can-get): read the preview to judge it, delete that raw (nothing cites it; a `wiki-ingester` worker lists it in its receipt under "Raws to delete" instead), and ask the user to save the post's page as PDF.

## Pages no fetcher can get

A page behind a paywall or a member wall (Medium member-only stories), behind a login, or on a site that blocks the fetcher (a Cloudflare "you have been blocked" page) has one path: the user saves it. Medium is the usual case, not a special one.

- **Never copy a page out of the browser into `raw/`** (2026-10-05). The session may open a page in the user's browser (Claude in Chrome) to read it and judge it, for triage or to tell the user whether it is worth saving, but never saves its text as a raw.
- **Never fetch it another way** (Mark, 2026-10-05): no archive copy, no cache, no proxy, and never the user's password. The page fetcher flags a paywalled or nearly empty page (`paywall=suspected`, and a `paywall:` line in the raw's header) instead of working around it, and marks it `completeness: preview`; a site's block page counts the same. That raw holds no article: delete it (nothing cites it yet; a `wiki-ingester` worker lists it in its receipt under "Raws to delete" instead).
- **A preview is never filed as the whole source** (task #96). `wiki-update.py` refuses to file from a raw marked `completeness: preview` or `summary` (the X fetcher and the page fetcher write the mark; a raw saved before 2026-10-11 counts by its `paywall:` line or the X fetcher's long-post note). Only on the user's word, `--partial-source '<why>'` files it anyway, and the entry carries `source_completeness:`.
- **Save as PDF.** Leave the item where it is (its queue ticket or intake bucket) with the reason "save as PDF: <paywall | login | blocked>", and tell the user which page it is. **A page the user handed over directly has no ticket yet: make one**, so it goes on the list (Mark, 2026-10-11): queue it with `wiki-list-add.py`, then route it to `main` with `wiki-triage.py --topic <topic> route <ticket> --to main --reason "<what it is>" --save-as-pdf <paywall|login|blocked>`. **The list** of every page waiting for the user is `wiki-triage.py --topic <topic> save-list`: each page's title, link, why, and the folder to save it into. Whenever you add to it, give the user the list as printed, with each page's link: a description of the list is not the list. In a cycle, the report lists every such page under **Save as PDF** with its link. When you ask the user to save one, name the folder as a full path they can paste into Chrome's Save dialog: the intake folder its ticket waits in, e.g. `C:\github.com\project-notebooks\notebooks\agentic-design\_inbox\intake\llm-wiki\` (any intake folder, or the Drive folder `<drive.parent_folder>/<drive.subfolder>`, also works). The user opens it in Chrome, Print → Save as PDF, into that folder; the next cycle attaches each PDF to the ticket waiting for it (`wiki-triage.py attach-pdfs`; the Drive step does the same), keeping the article's URL, so it is filed with its full text. A PDF the user hands over directly is a local file ([PDF](#pdf)).

A spawned `wiki-ingester` worker meeting such a page marks the item failed "save as PDF", marks its ticket in the bucket it sits in (`wiki-triage.py --topic <topic> route <ticket file name> --to <that bucket> --save-as-pdf <why> --reason "<what blocked it>"`; routing to its own bucket rewrites the ticket in place), and moves on.

## Pages that need JavaScript

For pages that show their text only once JavaScript runs (Threads, LinkedIn, public Notion pages, Bluesky, Medium) and as the fallback for X. It runs on this machine, in headless Chromium (Playwright, in the scripts' environment; the install fetches the browser):

```bash
uv run --project {{WIKI_SCRIPTS_DIR}} python {{WIKI_SCRIPTS_DIR}}/wiki-fetch-page.py --topic <topic> --url <url> --ingested-by claude-code
```

The page is saved as Markdown with its site chrome (login banners, sidebars, footers): read past it to the post itself. Cookie-consent banners from the known consent managers (CookieYes, OneTrust, Cookiebot and others) are removed before saving, never accepted (2026-10-06: a Towards Data Science raw went from 1,234 lines to 456). `paywall=suspected` means the page looked paywalled or nearly empty: see [Pages no fetcher can get](#pages-no-fetcher-can-get). At most two run at once on the machine; a third waits. Exit 3 names the command when Chromium is missing.

## Instagram

An Instagram post goes through the same fetcher (it recognises the URL), with no login: the raw holds the post's whole caption and the text of every carousel slide, clicked through, and never the comments. Each slide's text is Instagram's own automatic recognition of the image, which garbles some words and sometimes finds none ("May be an image of magazine and text"), so each slide image is saved in `<raw>-slides/` and named under its slide. The header's `slides_text: <n> of <N>` counts the slides it recognised text on, and the fetcher prints a warning at `0 of <N>`: logged out, Instagram recognised text on no slide of the 7 posts fetched on 2026-10-16 (on 2026-10-05 it had on every one), so read every image then. **Read the image** wherever a slide says Instagram recognised no text, or its text reads garbled, and quote only what you read. Before filing, append what you read to the raw, one section per image: `## Transcribed from <image file> by <you>, <date>`, then the text. The quote check then finds those quotes and reports them on their own line, as checked against your transcription rather than the source (2026-10-06: before this, every slide quote was "not found", and the gate could not tell a true one from an invented one). The same goes for any image a raw holds: an X post's picture, a screenshot. A dense single-image post is common: its whole substance is the image.

Triage on the caption first: many posts are engagement bait ("comment AGENT and I'll DM you") and need no slides read.

## Speech: reels, podcasts, video without captions

```bash
uv run --project {{WIKI_SCRIPTS_DIR}} python {{WIKI_SCRIPTS_DIR}}/wiki-transcribe.py --topic <topic> --url <url> --ingested-by claude-code
```

Local Whisper (faster-whisper): yt-dlp fetches the audio and the post's caption, and the raw holds the caption and a timestamped transcript, never the comments. On an NVIDIA GPU it runs large-v3-turbo (a one-minute reel in about 5 s; it takes one of the search's GPU slots); without one, the CPU runs `small`, and audio over 20 minutes exits 4 with the override named (`--max-cpu-minutes 0`). `--file <path>` transcribes a local recording. Music with no speech says so. The same auto-caption check as [YouTube](#youtube) applies before you blockquote a transcript.

A reel that will not download (yt-dlp's "empty media response": Instagram throttling, or a private reel) gets one more try after your other work; if that fails too, report it and leave the item, never with cookies or a login.
