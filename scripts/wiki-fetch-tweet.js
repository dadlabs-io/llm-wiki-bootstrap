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

  const author = tweet.user ? `${tweet.user.name} (@${tweet.user.screen_name})` : 'unknown';
  const title = `${tweet.user ? tweet.user.name : 'Unknown'} on X: "${tweet.text.slice(0, 200)}${tweet.text.length > 200 ? '…' : ''}"`;
  const hasNoteTweet = !!tweet.note_tweet;
  const mediaLines = (tweet.mediaDetails || []).map(
    (m, i) => `- Media ${i + 1} (${m.type}): ${m.media_url_https || m.video_info?.variants?.[0]?.url || '(no direct url)'}`
  );

  const topicRoot = path.join(args.vault, args.topic);
  if (!fs.existsSync(topicRoot)) {
    console.error(`ERROR: topic '${args.topic}' not found at ${topicRoot}`);
    process.exit(1);
  }
  const rawDir = path.join(topicRoot, 'raw');
  fs.mkdirSync(rawDir, { recursive: true });

  const date = new Date().toISOString().slice(0, 10);
  const slug = args.slugOverride || slugify(title);
  const rawFilename = `${date}-${slug}.md`;
  const rawPath = uniquePath(path.join(rawDir, rawFilename));

  const fm = [
    '---',
    `title: ${JSON.stringify(title)}`,
    `source_url: ${args.url}`,
    `fetched_via: syndication-api`,
    `fetched: ${new Date().toISOString()}`,
    `ingested_by: ${args.ingestedBy}`,
    `type: tweet`,
    `author: ${JSON.stringify(author)}`,
    `created_at: ${tweet.created_at || ''}`,
    `favorite_count: ${tweet.favorite_count ?? ''}`,
    `conversation_count: ${tweet.conversation_count ?? ''}`,
    '---',
    '',
  ];

  const body = [
    `# ${title}`,
    '',
    `**Source**: <${args.url}>`,
    `**Author**: ${author}`,
    '',
    '---',
    '',
    tweet.text,
    '',
  ];

  if (hasNoteTweet) {
    body.push(
      '> **Note**: this tweet has a `note_tweet` (long-form "Article") payload the syndication API does',
      '> not expand — the `text` field above may be truncated relative to the full post. If the content',
      '> reads as cut off, fall back to the Playwright recipe to capture the full note-tweet body.',
      ''
    );
  }

  if (mediaLines.length) {
    body.push('## Media', '', ...mediaLines, '');
  }

  const content = fm.join('\n') + body.join('\n');
  fs.writeFileSync(rawPath, content, 'utf-8');

  console.log(`Saved raw: ${rawPath}`);
  console.log(`  Author: ${author}`);
  console.log(`  Length: ${tweet.text.length} chars${hasNoteTweet ? ' (+ untruncated note_tweet not captured)' : ''}`);
  console.log('');
  console.log(`raw_path=${rawPath}`);
  console.log(`source_url=${args.url}`);
  console.log(`suggested_title=${title}`);
}

main().catch((e) => {
  console.error(`ERROR: unexpected failure: ${e.stack || e.message}`);
  process.exit(1);
});
