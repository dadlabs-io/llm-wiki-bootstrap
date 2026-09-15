# wiki-update — fetchers

Step 1 of the `/wiki-update` flow, by source. Every fetcher prints `raw_path=<path>`; keep it for step 8. After fetching, continue at step 2 of the flow in `SKILL.md`. A raw that is already saved (handed over, or captured in the browser) needs no fetcher: start at step 2.

## Which fetcher

| Source | Fetcher |
|---|---|
| `youtube.com`, `youtu.be` | `wiki-fetch-youtube.py` ([YouTube](#youtube)) |
| A PDF: a URL ending `.pdf`, `arxiv.org/pdf/…`, or a local `.pdf` | `wiki-fetch-pdf.py` ([PDF](#pdf)) |
| `x.com`, `twitter.com` | `wiki-fetch-tweet.js` ([X](#x--twitter)). Never Playwright first: four parallel Playwright fetches once hung the machine with 15 to 20 Chromium processes. |
| `medium.com`, `*.medium.com`, Medium publications on their own domains (`levelup.gitconnected.com`, `pub.towardsai.net`, …) | [Browser capture](#browser-capture) when the session is interactive and the user is signed in; [Playwright](#playwright-recipe) otherwise. Direct HTTP gets 403. |
| `threads.net`, `instagram.com`, `bsky.app`, `linkedin.com`, public `notion.so` pages | [Playwright](#playwright-recipe) |
| `github.com` repos and files, `gist.github.com` | `wiki-update.py --fetch-only` (rewrites to the raw file; a bare repo URL gets its README) |
| Anything else | `wiki-update.py --fetch-only` |

A raw under about 1 KB, one that is mostly navigation, or one that says "enable JavaScript" came from the wrong fetcher: use Playwright. An X post is short by nature: judge it by whether the text reads complete, not by its size.

## YouTube

```bash
python {{WIKI_SCRIPTS_DIR}}/wiki-fetch-youtube.py --topic <topic> --url <url> --ingested-by claude-code
```

Runs on the host and needs the `yt_dlp` Python package (`pip install yt-dlp`).

**Check the transcript before you blockquote it.** Auto-captions mis-hear this wiki's vocabulary systematically: "Claude Code" arrives as "Cloud Code" or "Quad Code", `CLAUDE.md` as "quadmd", "CloudMD" or "clawed MD". Correct the entry's own key terms by context before placing a passage in a `>` quote, disclose the correction once in a dated transcription note near the top of the entry, and paraphrase (no blockquote) any passage you cannot disambiguate. Doctrine: authoring best practices, principle 5.

A video's entry is as long as its content deserves: one good idea makes a short entry, a dense talk a full breakdown. Useful sections: key insights, notable quotes, when to watch it.

## PDF

```bash
python {{WIKI_SCRIPTS_DIR}}/wiki-fetch-pdf.py --topic <topic> --source <url-or-local-pdf> --ingested-by claude-code
```

Runs on the host: text per page through `pdftotext` (in Git Bash on Windows, poppler elsewhere), falling back to `pypdf` on pages where the text is poor (`pip install pypdf`); OCR only if tesseract is installed. It saves the raw with the page count and extraction figures and copies the PDF beside it.

## X / Twitter

```bash
node {{WIKI_SCRIPTS_DIR}}/wiki-fetch-tweet.js --topic <topic> --url <url> --vault <vault_root> --ingested-by claude-code
```

One HTTPS request to the public syndication API, on the host: no login, no browser. `--vault` is the vault root, the folder that holds the notebook's folder. When it fails (a deleted or protected post, a block), fetch that one URL with Playwright instead of retrying. If the raw ends with the note about a long-form post and the text reads cut off, fetch that URL with Playwright too.

## Browser capture

For a page the user can read in their own browser but no fetcher can: Medium member-only stories, anything behind a login the user holds. The interactive session reads the page through Claude in Chrome, in the user's signed-in session, and saves the text as the raw. This is the user's own access, never a bypass. If the page shows "Member-only story" and the body stops after a few paragraphs, the user is not a member of that site: the item is preview only, so say so in the raw header or skip it, and never ingest the fragment as the article.

**Only the interactive session can do this.** A spawned `wiki-ingester` worker has no browser. For a batch, the session captures every gated raw first, then hands the workers `--source <raw> --source-url <url> --raw-path raw/<file>`.

1. **Open and read.** `tabs_context_mcp`, then `navigate` to the URL and wait two to three seconds. Medium's `https://medium.com/p/<12-hex-id>` resolves to the canonical URL; a digest email's tracking parameter ending `reader-<publication>-<postid>----N-…` or `reader--<postid>----N-…` carries the post id. Read with `get_page_text` (scripts and screenshots are refused on many hosts), and take the final URL and title from its result. Medium redirects author posts to `<author>.medium.com` and publication posts to the publication's domain, and each host needs its own site permission in the extension: "Permission denied for reading page content on this domain" is that setting, not a fetch error. A page that returns only site chrome was still loading: wait and read again. A feed renders only the cards near the viewport: read it with `read_page` (interactive filter) at each scroll stop and collect the article links.
2. **Save the raw** with the Write tool (a shell heredoc breaks on article-length text) at `<topic>/raw/<YYYY-MM-DD>-<slug>.md`, header first, then the text with images dropped and captions kept:
   ```
   # <article title>
   source_url: <canonical url>
   author: <name> (<publication>, if any)
   published: <date as the page shows it>
   fetched: <YYYY-MM-DD> via browser capture (<Medium member view | not member-only>; images omitted; charts captions only)
   ---
   <full text>
   ```
   Keep the author's promotional blocks out or mark them `[Promo: …]`; keep everything else verbatim. A figure that reaches the raw only as the author's caption of a chart is a secondary-summary figure (authoring best practices, principle 5): `sourced` via the author, confidence low.
3. **Continue at step 2 of the flow**, and file with `--source <synthesis> --source-url <url> --raw-path raw/<file>`. Say in the entry's Sources how the raw was captured ("Raw captured <date> through the user's Medium membership").

## Playwright recipe

For pages rendered by JavaScript (Medium without a browser session, Threads, Notion, LinkedIn, Instagram, Bluesky) and as the fallback for X. Playwright and Chromium live in the `openclaw` Docker container:

```bash
MSYS_NO_PATHCONV=1 docker exec openclaw bash -c 'mkdir -p /tmp/scratch-vault/<topic> && node /home/node/.openclaw/agents-training/main/skills/research-wiki/wiki-fetch-page.js --topic <topic> --url <url> --vault /tmp/scratch-vault --ingested-by claude-code'
docker cp openclaw:/tmp/scratch-vault/<topic>/raw/<file>.md "<vault_root>/<topic>/raw/<file>.md"
```

The script exists only at that path inside the container, and the project notebooks are not mounted there, so it writes to a scratch vault and you copy the raw out; the `raw_path=` it prints is the container's. `MSYS_NO_PATHCONV=1` stops Git Bash rewriting the paths (harmless elsewhere). The raw includes the site's chrome (login banners, sidebars): read past it to the post itself.
