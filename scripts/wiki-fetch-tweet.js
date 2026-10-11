#!/usr/bin/env node
/**
 * wiki-fetch-tweet.js — fetch a single X/Twitter post via the public
 * syndication API (cdn.syndication.twimg.com), no login, no headless
 * browser, no Docker container. Replaces the old Playwright-via-openclaw
 * recipe for the common case (public, non-deleted, non-protected tweets).
 *
 * Why this exists: the previous recipe spun up headless Chromium inside
 * the `openclaw` Docker container per tweet. Run 4-way parallel across a
 * batch of X links (as a /wiki-cycle ingest run does), that's 15-20+
 * concurrent Chromium processes inside the WSL2 VM — real host RAM/CPU,
 * invisible to Windows Task Manager's process list, and it hung the
 * operator's machine mid-cycle on 2026-07-10. The syndication API is a
 * single plain HTTPS GET returning JSON — effectively free.
 *
 * Runs on the HOST directly (Node is available natively — no docker exec
 * needed). Matches the wiki-scripts family's CLI + raw-file conventions
 * (see wiki-fetch-youtube.py / wiki-update.py): --topic, --url, --vault
 * (vault_root; topic_root = vault/topic), writes to
 * <topic_root>/raw/<date>-<slug>.md, prints `raw_path=<path>` for the
 * caller to pick up.
 *
 * Usage:
 *   node wiki-fetch-tweet.js --topic agentic-design \
 *     --url https://x.com/AndrewYNg/status/2071988145667928442 \
 *     --vault "C:/github.com/project-notebooks/notebooks" \
 *     --ingested-by claude-code
 *
 * Exit code 0 + raw_path=... on success. Non-zero + a clear stderr reason
 * on failure (protected account, deleted tweet, no numeric id in the URL,
 * network error) — the caller should fall back to the Playwright recipe
 * documented in wiki-update/SKILL.md for those cases, not retry this
 * script blindly.
 */

const fs = require('fs');
const path = require('path');
const https = require('https');

function parseArgs(argv) {
  const args = { ingestedBy: 'cli', timeoutMs: 15000 };
  for (let i = 2; i < argv.length; i++) {
    const a = argv[i];
    if (a === '--topic') args.topic = argv[++i];
    else if (a === '--url') args.url = argv[++i];
    else if (a === '--vault') args.vault = argv[++i];
    else if (a === '--ingested-by') args.ingestedBy = argv[++i];
    else if (a === '--slug') args.slugOverride = argv[++i];
  }
  if (!args.topic || !args.url || !args.vault) {
    console.error('ERROR: --topic, --url, and --vault are required');
    process.exit(2);
  }
  return args;
}

function extractTweetId(url) {
  // Matches x.com/twitter.com status URLs, with or without a trailing
  // query string / path segment (e.g. /photo/1).
  const m = url.match(/(?:x\.com|twitter\.com)\/[^/]+\/status(?:es)?\/(\d+)/i);
  return m ? m[1] : null;
}

function syndicationToken(id) {
  // Ported from the public (unofficial but widely relied-upon) algorithm:
  // ((id / 1e15) * PI).toString(36).replace(/(0+|\.)/g, '')
  const val = (Number(id) / 1e15) * Math.PI;
  return val.toString(36).replace(/(0+|\.)/g, '');
}

function httpGetJson(url, timeoutMs) {
  return new Promise((resolve, reject) => {
    const req = https.get(
      url,
      { headers: { 'User-Agent': 'Mozilla/5.0 (compatible; wiki-fetch-tweet/1.0)' } },
      (res) => {
        if (res.statusCode !== 200) {
          reject(new Error(`HTTP ${res.statusCode}`));
          res.resume();
          return;
        }
        let data = '';
        res.on('data', (chunk) => (data += chunk));
        res.on('end', () => {
          try {
            resolve(JSON.parse(data));
          } catch (e) {
            reject(new Error(`Non-JSON response: ${e.message}`));
          }
        });
      }
    );
    req.on('error', reject);
    req.setTimeout(timeoutMs, () => {
      req.destroy(new Error('Request timed out'));
    });
  });
}

function slugify(text, maxLen = 60) {
  let s = (text || 'untitled')
    .toLowerCase()
    .replace(/https?:\/\/\S+/g, '')
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-+|-+$/g, '');
  if (s.length > maxLen) s = s.slice(0, maxLen).replace(/-+$/g, '');
  return s || 'untitled';
}

function uniquePath(target) {
  if (!fs.existsSync(target)) return target;
  const ext = path.extname(target);
  const base = target.slice(0, -ext.length);
  let n = 2;
  let candidate = `${base}-${n}${ext}`;
  while (fs.existsSync(candidate)) {
    n += 1;
    candidate = `${base}-${n}${ext}`;
  }
  return candidate;
}

function originalSize(url) {
  // A pbs.twimg.com/media photo is served at a reduced size unless the URL asks for the original
  // (`name=orig`: 78 KB vs 135 KB on a real post, 2026-10-11). Anything else is returned unchanged.
  if (!url || !/^https:\/\/pbs\.twimg\.com\/media\//.test(url)) return url;
  const u = new URL(url);
  u.searchParams.set('name', 'orig');
  return u.toString();
}

function buildRaw(tweet, opts) {
  // The raw's title and Markdown for one syndication payload. An X Article (a non-empty `article`)
  // comes back as its title, cover and opening only: the full text needs a logged-in session, so the
  // raw is marked `completeness: preview` and says how the full text is got (task #96, from Chubby
  // Skills' x-ingest; the field names checked against a real Article payload, 2026-10-11). A long post
  // (`note_tweet`, which holds only an id) is the same: `text` is its first 280 characters and a link.
  const name = tweet.user ? tweet.user.name : 'Unknown';
  const author = tweet.user ? `${tweet.user.name} (@${tweet.user.screen_name})` : 'unknown';
  const article = tweet.article && tweet.article.title ? tweet.article : null;
  const headline = article ? article.title : tweet.text;
  const title = `${name} on X: "${headline.slice(0, 200)}${headline.length > 200 ? '…' : ''}"`;
  const hasNoteTweet = !!tweet.note_tweet;
  const mediaLines = (tweet.mediaDetails || []).map((m, i) => {
    const url = m.type === 'photo'
      ? originalSize(m.media_url_https)
      : (m.video_info?.variants?.[0]?.url || m.media_url_https || '(no direct url)');
    return `- Media ${i + 1} (${m.type}): ${url}`;
  });

  const fm = [
    '---',
    `title: ${JSON.stringify(title)}`,
    `source_url: ${opts.url}`,
    `fetched_via: syndication-api`,
    `fetched: ${new Date().toISOString()}`,
    `ingested_by: ${opts.ingestedBy}`,
    `type: ${article ? 'x-article' : 'tweet'}`,
    `author: ${JSON.stringify(author)}`,
    `created_at: ${tweet.created_at || ''}`,
    `favorite_count: ${tweet.favorite_count ?? ''}`,
    `conversation_count: ${tweet.conversation_count ?? ''}`,
  ];
  if (article || hasNoteTweet) fm.push('completeness: preview');
  if (article) {
    if (article.rest_id) fm.push(`article_url: https://x.com/i/article/${article.rest_id}`);
  }
  fm.push('---', '');

  const body = [
    `# ${title}`,
    '',
    `**Source**: <${opts.url}>`,
    `**Author**: ${author}`,
    '',
    '---',
    '',
    tweet.text,
    '',
  ];

  if (article) {
    const cover = originalSize(article.cover_media?.media_info?.original_img_url);
    body.push(`## ${article.title}`, '');
    if (cover) body.push(`Cover image: ${cover}`, '');
    if (article.preview_text) body.push(article.preview_text, '');
    body.push(
      '> **Preview only**: this post is an X Article. The public API gives its title, cover and opening',
      '> lines, not the full text, which needs a logged-in session. To file the whole article, ask the user',
      '> to save the post\'s page as PDF (wiki-update fetchers.md, "Pages no fetcher can get"); never fetch',
      '> it another way.',
      ''
    );
  }

  if (hasNoteTweet && !article) {
    body.push(
      '> **Preview only**: this is a long post. The public API gives its first 280 characters and a link,',
      '> not the full text, which needs a logged-in session (the page fetcher gets nothing from X). To file',
      '> the whole post, ask the user to save the post\'s page as PDF (wiki-update fetchers.md, "Pages no',
      '> fetcher can get"); never fetch it another way.',
      ''
    );
  }

  if (mediaLines.length) {
    body.push('## Media', '', ...mediaLines, '');
  }

  return {
    title,
    author,
    content: fm.join('\n') + body.join('\n'),
    completeness: article || hasNoteTweet ? 'preview' : null,
    isArticle: !!article,
  };
}

async function main() {
  const args = parseArgs(process.argv);

  const tweetId = extractTweetId(args.url);
  if (!tweetId) {
    console.error(`ERROR: could not extract a numeric tweet id from URL: ${args.url}`);
    console.error('Not an x.com/twitter.com status URL, or the id is missing — fall back to Playwright.');
    process.exit(1);
  }

  const token = syndicationToken(tweetId);
  const apiUrl = `https://cdn.syndication.twimg.com/tweet-result?id=${tweetId}&token=${token}&lang=en`;

  let tweet;
  try {
    tweet = await httpGetJson(apiUrl, args.timeoutMs);
  } catch (e) {
    console.error(`ERROR: syndication API fetch failed: ${e.message}`);
    console.error('Common causes: deleted tweet, protected/private account, or a transient block.');
    console.error('Fall back to the Playwright-via-openclaw recipe in wiki-update/SKILL.md for this URL.');
    process.exit(1);
  }

  if (tweet.__typename === 'TweetTombstone' || !tweet.text) {
    console.error('ERROR: syndication API returned a tombstone/empty result (deleted, protected, or age-restricted).');
    console.error('Fall back to the Playwright-via-openclaw recipe in wiki-update/SKILL.md for this URL.');
    process.exit(1);
  }

  const raw = buildRaw(tweet, { url: args.url, ingestedBy: args.ingestedBy });

  const topicRoot = path.join(args.vault, args.topic);
  if (!fs.existsSync(topicRoot)) {
    console.error(`ERROR: topic '${args.topic}' not found at ${topicRoot}`);
    process.exit(1);
  }
  const rawDir = path.join(topicRoot, 'raw');
  fs.mkdirSync(rawDir, { recursive: true });

  const date = new Date().toISOString().slice(0, 10);
  const slug = args.slugOverride || slugify(raw.title);
  const rawFilename = `${date}-${slug}.md`;
  const rawPath = uniquePath(path.join(rawDir, rawFilename));

  fs.writeFileSync(rawPath, raw.content, 'utf-8');

  if (raw.completeness === 'preview') {
    const what = raw.isArticle
      ? 'an X Article; only its title, cover and opening were captured'
      : 'a long post; only its first 280 characters were captured';
    console.error(`WARNING: this post is ${what} (a preview).`);
    console.error('The full text needs the user to save the page as PDF; see the note in the raw.');
  }
  console.log(`Saved raw: ${rawPath}`);
  console.log(`  Author: ${raw.author}`);
  console.log(`  Length: ${tweet.text.length} chars${raw.completeness ? ' (a preview: the rest was not captured)' : ''}`);
  console.log('');
  console.log(`raw_path=${rawPath}`);
  console.log(`source_url=${args.url}`);
  console.log(`suggested_title=${raw.title}`);
  if (raw.completeness) console.log(`completeness=${raw.completeness}`);
}

module.exports = { buildRaw, originalSize };

if (require.main === module) {
  main().catch((e) => {
    console.error(`ERROR: unexpected failure: ${e.stack || e.message}`);
    process.exit(1);
  });
}
