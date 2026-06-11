#!/usr/bin/env node
/*
 * wiki-fetch-page.js — fetch a JS-rendered web page via Playwright + Chromium
 * and save the rendered text content to <topic>/raw/.
 *
 * Designed to run inside the openclaw Docker container where playwright + chromium
 * are installed (Node module at /home/node/node_modules/playwright, browser binary
 * at /home/node/.cache/ms-playwright/). Apt deps for chromium are installed via
 * the openclaw Dockerfile.
 *
 * Sibling to wiki-fetch-youtube.py — same pattern: fetch verbatim → save to raw/
 * → caller (the agent / wiki-update.py) reads the raw and synthesizes a curated
 * wiki entry on top.
 *
 * Usage (inside container):
 *   node wiki-fetch-page.js \
 *     --topic agentic-design \
 *     --url https://x.com/chappyasel/status/2041166770472644721 \
 *     --vault /shared/openclaw/vault/wikis \
 *     --ingested-by claude-code
 *
 * Output: prints raw_path=<path> on success for the caller to capture.
 */

const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

const DEFAULT_VAULT = '/shared/openclaw/vault/wikis';

function parseArgs(argv) {
  const args = { vault: DEFAULT_VAULT, ingestedBy: 'cli', timeout: 45000 };
  for (let i = 2; i < argv.length; i++) {
    const a = argv[i];
    if (a === '--topic') args.topic = argv[++i];
    else if (a === '--url') args.url = argv[++i];
    else if (a === '--vault') args.vault = argv[++i];
    else if (a === '--ingested-by') args.ingestedBy = argv[++i];
    else if (a === '--slug') args.slug = argv[++i];
    else if (a === '--timeout') args.timeout = parseInt(argv[++i], 10);
  }
  if (!args.topic || !args.url) {
    console.error('ERROR: --topic and --url are required');
    process.exit(2);
  }
  return args;
}

function slugify(text, maxLen = 50) {
  if (!text) return 'untitled';
  return (text.toLowerCase().trim().replace(/[^a-z0-9]+/g, '-').replace(/^-+|-+$/g, '').slice(0, maxLen).replace(/-+$/, '') || 'untitled');
}

function uniquePath(target) {
  if (!fs.existsSync(target)) return target;
  const ext = path.extname(target);
  const stem = path.basename(target, ext);
  const dir = path.dirname(target);
  let n = 2;
  while (true) {
    const cand = path.join(dir, `${stem}-${n}${ext}`);
    if (!fs.existsSync(cand)) return cand;
    n++;
  }
}

function isoNow() {
  return new Date().toISOString().replace(/\.\d{3}/, '');
}

function todayDate() {
  return new Date().toISOString().slice(0, 10);
}

(async () => {
  const args = parseArgs(process.argv);

  const topicRoot = path.join(args.vault, args.topic);
  if (!fs.existsSync(topicRoot)) {
    console.error(`ERROR: topic '${args.topic}' not found at ${topicRoot}`);
    process.exit(1);
  }
  const rawDir = path.join(topicRoot, 'raw');
  fs.mkdirSync(rawDir, { recursive: true });

  console.log(`Fetching (playwright): ${args.url}`);

  let browser;
  try {
    browser = await chromium.launch();
    const context = await browser.newContext({
      userAgent: 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36',
    });
    const page = await context.newPage();

    // Try networkidle first (better for SPAs); fall back to domcontentloaded if it times out.
    try {
      await page.goto(args.url, { waitUntil: 'networkidle', timeout: args.timeout });
    } catch (e) {
      console.log(`  networkidle timed out, retrying with domcontentloaded: ${e.message}`);
      await page.goto(args.url, { waitUntil: 'domcontentloaded', timeout: args.timeout });
    }

    // Give SPA frameworks an extra moment to populate
    await page.waitForTimeout(2000);

    const title = (await page.title()) || '';
    const bodyText = await page.evaluate(() => {
      // Strip script/style/noscript and grab visible text
      document.querySelectorAll('script,style,noscript').forEach(el => el.remove());
      return document.body ? document.body.innerText : '';
    });
    const ogImage = await page.evaluate(() => {
      const m = document.querySelector('meta[property="og:image"]');
      return m ? m.getAttribute('content') : null;
    }).catch(() => null);
    const metaDescription = await page.evaluate(() => {
      const m = document.querySelector('meta[name="description"], meta[property="og:description"]');
      return m ? m.getAttribute('content') : null;
    }).catch(() => null);

    await browser.close();
    browser = null;

    const slug = args.slug || slugify(title || (new URL(args.url)).hostname);
    const filename = `${todayDate()}-${slug}.md`;
    const rawPath = uniquePath(path.join(rawDir, filename));

    const fmLines = [
      '---',
      `title: "${(title || '').replace(/"/g, '\\"')}"`,
      `source_url: ${args.url}`,
      `fetched_via: playwright-chromium`,
      `fetched: ${isoNow()}`,
      `ingested_by: ${args.ingestedBy}`,
      'type: web-page',
    ];
    if (metaDescription) fmLines.push(`meta_description: "${metaDescription.replace(/"/g, '\\"').slice(0, 300)}"`);
    if (ogImage) fmLines.push(`og_image: ${ogImage}`);
    fmLines.push('---', '');

    const body = [
      `# ${title || args.url}`,
      '',
      `**Source**: <${args.url}>`,
      '',
      '---',
      '',
      bodyText.trim(),
      '',
    ];

    fs.writeFileSync(rawPath, fmLines.concat(body).join('\n'), 'utf-8');

    console.log(`Saved raw: ${rawPath}`);
    console.log(`  Title: ${title}`);
    console.log(`  Length: ${bodyText.length} chars`);
    console.log('');
    console.log(`raw_path=${rawPath}`);
    console.log(`source_url=${args.url}`);
    if (title) console.log(`suggested_title=${title}`);
  } catch (err) {
    if (browser) await browser.close().catch(() => {});
    console.error(`ERROR: ${err.message}`);
    process.exit(1);
  }
})();
