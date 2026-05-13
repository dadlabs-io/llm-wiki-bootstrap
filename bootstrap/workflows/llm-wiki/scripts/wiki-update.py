#!/usr/bin/env python3
"""
Update (add) a source to a topic wiki.

Workflow:
  1. Resolve target topic dir under vault
  2. Dedup check — if --source URL is already in the wiki, skip (unless --force)
  3. If source is a URL: fetch HTML, convert to markdown (basic), save to raw/
     If source is a local file: copy to raw/
     (For YouTube URLs, the caller should run wiki-fetch-youtube.py first and
      pass the curated summary as --source plus --raw-path pointing to the
      verbatim transcript.)
  4. Write a curated copy under wiki/{folder}/{slug}.md with full frontmatter
     (title, date, source_url, raw_path, ingested_by, tags)
  5. Regenerate _INDEX.md by calling wiki-index.py

Usage:
    python3 wiki-update.py --topic <topic> --folder memory-systems \\
        --source https://example.com/article --title "Article Title" \\
        --ingested-by claude-code

    python3 wiki-update.py --topic <topic> --folder memory-systems \\
        --source ./summary.md --source-url https://youtu.be/abc \\
        --raw-path raw/2026-04-08-talk-transcript.md \\
        --ingested-by claude-code
"""

import argparse
import os
import re
import shutil
import subprocess
import sys
import urllib.parse
import urllib.request
from datetime import datetime
from pathlib import Path

# Force UTF-8 stdout on Windows so Unicode in wiki content doesn't crash printing
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

DEFAULT_VAULT = "/shared/openclaw/vault/wikis"
USER_AGENT = "Mozilla/5.0 (research-wiki/1.0)"


# ── Slug + path helpers ──────────────────────────────────────────────────────


SLUG_RE = re.compile(r"[^a-z0-9]+")


def slugify(text, max_len=80):
    """Filesystem-safe slug. Lowercase, hyphens, no path separators or punctuation."""
    if not text:
        return "untitled"
    s = text.lower().strip()
    s = SLUG_RE.sub("-", s)
    s = s.strip("-")
    if not s:
        return "untitled"
    if len(s) > max_len:
        s = s[:max_len].rstrip("-")
    return s


def unique_path(target):
    """If target exists, append -2, -3, … until unique. Returns Path."""
    target = Path(target)
    if not target.exists():
        return target
    stem = target.stem
    suffix = target.suffix
    parent = target.parent
    n = 2
    while True:
        candidate = parent / f"{stem}-{n}{suffix}"
        if not candidate.exists():
            return candidate
        n += 1


# ── Source acquisition ──────────────────────────────────────────────────────


GIST_URL_RE = re.compile(r"^https?://gist\.github\.com/([^/]+)/([a-f0-9]+)/?$")
GITHUB_BLOB_RE = re.compile(r"^https?://github\.com/([^/]+)/([^/]+)/blob/([^/]+)/(.+)$")
GITHUB_REPO_RE = re.compile(r"^https?://github\.com/([^/]+)/([^/]+?)/?$")


def maybe_rewrite_url(url):
    """Rewrite known JS-rendered URLs to text-friendly equivalents.

    Returns (rewritten_url, was_rewritten). Original URL is preserved by caller
    so frontmatter still shows the human-friendly source URL.
    """
    m = GIST_URL_RE.match(url)
    if m:
        user, gist_id = m.group(1), m.group(2)
        return f"https://gist.githubusercontent.com/{user}/{gist_id}/raw", True
    m = GITHUB_BLOB_RE.match(url)
    if m:
        user, repo, branch, path = m.group(1), m.group(2), m.group(3), m.group(4)
        return f"https://raw.githubusercontent.com/{user}/{repo}/{branch}/{path}", True
    m = GITHUB_REPO_RE.match(url)
    if m:
        # Bare repo URL → fetch README.md from default branch (HEAD).
        # Excludes paths like /issues/, /pull/, /blob/, /tree/ via the regex.
        user, repo = m.group(1), m.group(2)
        # Skip if 2nd segment is a known github top-level path
        if repo not in ("orgs", "settings", "marketplace", "topics", "trending", "explore", "notifications"):
            return f"https://raw.githubusercontent.com/{user}/{repo}/HEAD/README.md", True
    return url, False


def fetch_url(url):
    """Fetch a URL, return (content_text, content_type). Raises on failure."""
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=30) as resp:
        ctype = resp.headers.get("Content-Type", "")
        raw = resp.read()
    # Try common encodings
    for enc in ("utf-8", "latin-1"):
        try:
            return raw.decode(enc), ctype
        except UnicodeDecodeError:
            continue
    return raw.decode("utf-8", errors="replace"), ctype


HTML_TAG_RE = re.compile(r"<[^>]+>")
HTML_SCRIPT_RE = re.compile(r"<(script|style)[^>]*>.*?</\1>", re.DOTALL | re.IGNORECASE)
HTML_ENTITY_MAP = {
    "&amp;": "&",
    "&lt;": "<",
    "&gt;": ">",
    "&quot;": '"',
    "&apos;": "'",
    "&#39;": "'",
    "&nbsp;": " ",
}


def html_to_text(html):
    """Crude HTML → plain text. Strips scripts/styles, all tags, decodes a few entities.

    Not pretty. For real fidelity, capture the page elsewhere first.
    """
    text = HTML_SCRIPT_RE.sub("", html)
    text = HTML_TAG_RE.sub("\n", text)
    for entity, char in HTML_ENTITY_MAP.items():
        text = text.replace(entity, char)
    # Numeric entities
    text = re.sub(r"&#(\d+);", lambda m: chr(int(m.group(1))), text)
    # Collapse whitespace runs
    lines = [ln.strip() for ln in text.splitlines()]
    lines = [ln for ln in lines if ln]
    return "\n\n".join(lines)


def extract_html_title(html):
    m = re.search(r"<title[^>]*>(.*?)</title>", html, re.IGNORECASE | re.DOTALL)
    if m:
        return re.sub(r"\s+", " ", m.group(1)).strip()
    return None


def acquire_source(source, raw_dir, slug_hint, skip_raw_copy=False):
    """Acquire a source. Returns (raw_path, body_text, suggested_title, source_url).

    If skip_raw_copy is True, do NOT write a copy to raw_dir — just read the
    body and return raw_path=None. Used when --raw-path override is given,
    meaning the verbatim raw was already saved by an earlier --fetch-only call
    and the current --source is a synthesized summary that shouldn't pollute raw/.
    """
    raw_dir = Path(raw_dir)
    raw_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y-%m-%d")

    # URL?
    if source.startswith(("http://", "https://")):
        fetch_url_actual, was_rewritten = maybe_rewrite_url(source)
        if was_rewritten:
            print(f"  Rewrote: {source}")
            print(f"       to: {fetch_url_actual}")
        print(f"  Fetching: {fetch_url_actual}")
        content, ctype = fetch_url(fetch_url_actual)
        is_html = "html" in ctype.lower() or content.lstrip().startswith("<")
        suggested_title = None
        if is_html:
            suggested_title = extract_html_title(content)
            body_text = html_to_text(content)
        else:
            body_text = content
            # For raw text (e.g. gist raw), try to extract title from first H1 or first non-empty line
            for line in body_text.splitlines():
                stripped = line.strip()
                if not stripped:
                    continue
                m = re.match(r"^#+\s+(.+)$", stripped)
                if m:
                    suggested_title = m.group(1).strip()
                    break
                # First non-empty line as fallback title (truncate)
                suggested_title = stripped[:80]
                break

        slug = slug_hint or slugify(suggested_title or urllib.parse.urlparse(source).path or "url-source")
        raw_filename = f"{timestamp}-{slug}.md"
        raw_path = unique_path(raw_dir / raw_filename)
        # Save with a small frontmatter pointing back to the ORIGINAL URL
        raw_content = f"---\nsource_url: {source}\nfetched_url: {fetch_url_actual}\nfetched: {datetime.now().isoformat()}\n---\n\n{body_text}\n"
        raw_path.write_text(raw_content, encoding="utf-8")
        print(f"  Saved raw: {raw_path}")
        return raw_path, body_text, suggested_title, source

    # Local file
    src_path = Path(source).expanduser().resolve()
    if not src_path.exists():
        raise FileNotFoundError(f"Source file not found: {src_path}")

    suggested_title = src_path.stem.replace("-", " ").replace("_", " ").title()
    body_text = src_path.read_text(encoding="utf-8")
    source_url = f"file://{src_path}"

    if skip_raw_copy:
        # Caller has its own raw at --raw-path; just read body, don't pollute raw/
        return None, body_text, suggested_title, source_url

    slug = slug_hint or slugify(src_path.stem)
    raw_filename = f"{timestamp}-{slug}{src_path.suffix or '.md'}"
    raw_path = unique_path(raw_dir / raw_filename)
    shutil.copy2(src_path, raw_path)
    print(f"  Copied raw: {raw_path}")
    return raw_path, body_text, suggested_title, source_url


# ── Dedup ────────────────────────────────────────────────────────────────────


# ── Integration: bidirectional cross-link helpers ────────────────────────────


# Match `[text](./foo.md)` and `[text](../folder/foo.md)` style relative links
LINK_RE = re.compile(r"\[([^\]]+)\]\((\.{1,2}/[^)]+\.md)\)")


def _build_slug_index(wiki_dir):
    """Map of stem → [Path, ...] for every .md file under wiki/. Used by the
    outbound-link resolver to fuzzy-match broken slugs to the real ones."""
    slug_index = {}
    for md in Path(wiki_dir).rglob("*.md"):
        slug_index.setdefault(md.stem, []).append(md)
    return slug_index


def resolve_outbound_links(curated_path, wiki_dir):
    """Scan the just-written curated entry for relative markdown links to other
    wiki files. For each link whose target doesn't exist, try to fuzzy-match
    against the actual slug index. Unambiguous matches get auto-rewritten in
    place. Ambiguous / no-match links are returned as warnings.

    Returns (fixed_count, warnings) where warnings = [(text, target, [candidates])].
    """
    curated_path = Path(curated_path)
    wiki_dir = Path(wiki_dir)
    try:
        content = curated_path.read_text(encoding="utf-8")
    except (UnicodeDecodeError, OSError):
        return 0, []

    slug_index = _build_slug_index(wiki_dir)
    fixed = 0
    warnings = []
    new_content = content

    for match in LINK_RE.finditer(content):
        link_text = match.group(1)
        link_target = match.group(2)
        target_abs = (curated_path.parent / link_target).resolve()
        if target_abs.exists():
            continue  # link already valid

        target_stem = Path(link_target).stem
        target_stem_lower = target_stem.lower()

        # Pass 1: exact stem match (single result only)
        exact = slug_index.get(target_stem, [])
        if len(exact) == 1:
            real_path = exact[0]
            new_rel = os.path.relpath(real_path, curated_path.parent).replace(os.sep, "/")
            new_link = f"[{link_text}]({new_rel})"
            new_content = new_content.replace(match.group(0), new_link)
            fixed += 1
            continue

        # Pass 2: contains/prefix match — collect candidates
        candidates = []
        for stem, paths in slug_index.items():
            stem_lower = stem.lower()
            if stem_lower == target_stem_lower:
                continue  # exact already tried
            if stem_lower.startswith(target_stem_lower) or target_stem_lower in stem_lower:
                candidates.extend(paths)

        if len(candidates) == 1:
            real_path = candidates[0]
            new_rel = os.path.relpath(real_path, curated_path.parent).replace(os.sep, "/")
            new_link = f"[{link_text}]({new_rel})"
            new_content = new_content.replace(match.group(0), new_link)
            fixed += 1
        else:
            warnings.append((
                link_text,
                link_target,
                [str(c.relative_to(wiki_dir)).replace(os.sep, "/") for c in candidates],
            ))

    if new_content != content:
        curated_path.write_text(new_content, encoding="utf-8")

    return fixed, warnings


# Common words / stems that show up in too many entries to be useful as
# inbound-mention search terms. Adding to this list trades recall for precision.
NOISE_TERMS = {
    # Generic concepts from this domain — match too many entries
    "agent", "agents", "agentic", "memory", "context", "system", "systems",
    "model", "models", "data", "tools", "framework", "frameworks", "knowledge",
    "wiki", "research", "stateful", "tiered", "intelligent", "design",
    "long", "term", "active", "raw", "open", "source", "based", "first",
    "using", "self", "improving", "production", "pattern", "patterns",
    "layer", "layers", "approach", "ingest", "ingestion", "official",
    "extension", "extensions", "format", "graphs", "graph",
    # Generic descriptive tags — common across many entries
    "foundational", "foundation", "primary", "secondary", "advanced",
    "beginner", "expert", "tutorial", "guide", "overview", "introduction",
    "concept", "concepts", "theory", "practice", "practical", "applied",
    "self-improving", "self-improvement", "production-ready",
    # Common english function words
    "with", "from", "this", "that", "have", "into", "about", "more", "than",
    "what", "when", "where", "which", "their", "there", "these", "those",
    "such", "formerly", "would", "should", "could",
    # Stop-list for terms that aren't useful even if they appear capitalized
    "the-", "an-", "of-",
}


def _title_search_terms(title, slug=None, tags=None):
    """Build a small set of low-noise search terms from a title + slug + tags.

    Strategy:
    - Full title (lowercase) — the most precise match
    - Subtitle parts (split on — / - / : / |) — both halves
    - Slug stem-parts (split on hyphen) filtered for length >= 5 and not in NOISE_TERMS
    - Frontmatter tags filtered for length >= 4 and not in NOISE_TERMS

    Tags + slug stems give us proper-noun matches like 'letta' and 'mem0' that
    the full title won't catch (because they appear by short name in other
    entries). NOISE_TERMS prevents 'memory' / 'agent' / 'system' from matching
    every file in the wiki.
    """
    terms = set()
    if title:
        terms.add(title.lower().strip())
        for sep in (" — ", " - ", ": ", " | "):
            if sep in title:
                left, right = title.split(sep, 1)
                terms.add(left.lower().strip())
                terms.add(right.lower().strip())
    if slug:
        for part in slug.split("-"):
            p = part.lower().strip()
            if p and p not in NOISE_TERMS:
                terms.add(p)
    if tags:
        for tag in tags:
            if isinstance(tag, str):
                t = tag.lower().strip()
                if t and t not in NOISE_TERMS:
                    terms.add(t)
    # Filter: each term must be at least 4 chars and not in noise list
    return {t for t in terms if len(t) >= 4 and t not in NOISE_TERMS}


def _read_frontmatter_tags(path):
    """Pull the `tags:` line from a file's YAML frontmatter. Returns list of strings."""
    try:
        head = Path(path).read_text(encoding="utf-8")[:2000]
    except (UnicodeDecodeError, OSError):
        return []
    m = re.search(r"^tags:\s*\[([^\]]*)\]", head, re.MULTILINE)
    if m:
        return [t.strip().strip("'\"") for t in m.group(1).split(",") if t.strip()]
    # YAML list form
    m = re.search(r"^tags:\s*\n((?:\s*-\s*[^\n]+\n)+)", head, re.MULTILINE)
    if m:
        return [ln.strip().lstrip("-").strip().strip("'\"") for ln in m.group(1).splitlines() if ln.strip()]
    return []


def find_inbound_candidates(new_path, wiki_dir, title, max_results=15):
    """Scan all other wiki .md files for mentions of the new entry.

    Builds search terms from the title + slug-stems + frontmatter tags
    (with noise-word filtering). For each file containing one of those terms
    AND not already linking to the new entry, return (file_path, matched_term,
    snippet).

    Caller decides what to do with the candidates — we never auto-edit other
    files. That's the manual review step (matches the safety rail in the vision
    doc: agent suggests, human commits).

    If results exceed max_results, return the first max_results plus the total
    count (caller can choose to trim or warn).
    """
    new_path = Path(new_path)
    wiki_dir = Path(wiki_dir)

    tags = _read_frontmatter_tags(new_path)
    slug = new_path.stem
    terms = _title_search_terms(title, slug=slug, tags=tags)
    if not terms:
        return []

    new_stem = new_path.stem.lower()
    candidates = []

    for md in wiki_dir.rglob("*.md"):
        if md.resolve() == new_path.resolve():
            continue
        try:
            body = md.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        body_lower = body.lower()

        # Skip if already linked (the new entry's stem appears as a markdown link target)
        if f"({new_stem}.md" in body_lower or f"/{new_stem}.md" in body_lower:
            continue

        # Try each term, longest first (more precise wins)
        for term in sorted(terms, key=len, reverse=True):
            idx = body_lower.find(term)
            if idx >= 0:
                start = max(0, idx - 30)
                end = min(len(body_lower), idx + len(term) + 30)
                snippet = body[start:end].replace("\n", " ").strip()
                candidates.append((md, term, snippet))
                break  # one match per file is enough

    return candidates


# ── Dedup ────────────────────────────────────────────────────────────────────


def find_existing_by_url(wiki_root, url):
    """Walk wiki/ and return the first file whose frontmatter source_url matches.

    Returns Path or None. Comparison is exact-match on the URL string after
    stripping trailing slashes.
    """
    if not url:
        return None
    target = url.rstrip("/")
    wiki_root = Path(wiki_root)
    if not wiki_root.exists():
        return None
    for path in wiki_root.rglob("*.md"):
        try:
            head = path.read_text(encoding="utf-8")[:2000]  # only need frontmatter
        except (UnicodeDecodeError, OSError):
            continue
        m = re.search(r"^source_url:\s*(.+)$", head, re.MULTILINE)
        if m and m.group(1).strip().rstrip("/") == target:
            return path
    return None


# ── Curated wiki file ────────────────────────────────────────────────────────


def write_curated(wiki_dir, folder, slug, title, body, source_url, tags,
                  ingested_by=None, raw_path=None, tier=None, confidence=None):
    """Write the curated copy under wiki/{folder}/{slug}.md.

    Frontmatter includes: title, date, source_url, raw_path, ingested_by, tier,
    confidence, tags. Body footer adds visible links to source_url and raw_path.

    `tier` is the source quality tier:
      1 = peer-reviewed / primary (papers, official spec docs, source code)
      2 = established documentation (vendor docs, framework docs, official blog)
      3 = reputable expert / first-hand (founder posts, expert blogs, conf talks, journalism)
      4 = community / blog / forum (Medium, Reddit, anonymous gists)
      self = self-authored (our own design docs, syntheses, decisions)

    `confidence` is how reliable OUR entry is (not the source — that's tier):
      high = primary source directly fetched, multiple corroborating entries, or describes
             something we actually built and tested (for self-authored)
      medium = single good source fetched, or describes plans/decisions that could change
      low = synthesized from secondary references, source not fetched, or very thin
    """
    wiki_dir = Path(wiki_dir)
    target_dir = wiki_dir / folder if folder else wiki_dir
    target_dir.mkdir(parents=True, exist_ok=True)

    target = unique_path(target_dir / f"{slug}.md")

    # Build frontmatter
    fm_lines = ["---"]
    # Auto-quote titles containing YAML special characters
    YAML_SPECIAL = set(":'\"{}&*?|>!%@`")
    if title and any(ch in title for ch in YAML_SPECIAL) and not (title.startswith('"') and title.endswith('"')):
        fm_lines.append(f'title: "{title}"')
    else:
        fm_lines.append(f"title: {title}")
    fm_lines.append(f"date: {datetime.now().strftime('%Y-%m-%d')}")
    if source_url:
        fm_lines.append(f"source_url: {source_url}")
    if raw_path:
        # Store as relative-to-topic-root if possible (cleaner in frontmatter)
        try:
            rp_obj = Path(raw_path)
            # topic root is wiki_dir.parent (wiki_dir is .../topic/wiki/)
            topic_root = wiki_dir.parent
            rp_rel = rp_obj.resolve().relative_to(topic_root.resolve())
            fm_lines.append(f"raw_path: {rp_rel.as_posix()}")
        except (ValueError, OSError):
            fm_lines.append(f"raw_path: {raw_path}")
    if ingested_by:
        fm_lines.append(f"ingested_by: {ingested_by}")
    if tier is not None:
        fm_lines.append(f"tier: {tier}")
    if confidence is not None:
        fm_lines.append(f"confidence: {confidence}")
    if tags:
        fm_lines.append(f"tags: [{', '.join(tags)}]")
    fm_lines.append("---")
    fm = "\n".join(fm_lines)

    # If the body already starts with a frontmatter block, strip it (we'll write our own)
    body_stripped = re.sub(r"^---\s*\n.*?\n---\s*\n", "", body, count=1, flags=re.DOTALL)

    # Strip any existing Source/Raw footer from the body to prevent duplicates.
    # The synthesis temp file might already have a footer if the agent included one.
    # We always generate our own canonical footer below, so any pre-existing one is duplicate.
    body_stripped = re.sub(
        r"\n---\s*\n\*\*Source\*\*:.*?(?:\n\*\*Raw\*\*:.*?)?\s*$",
        "", body_stripped, flags=re.DOTALL
    )

    # If body lacks an H1, add one with the title
    if not re.search(r"^#\s+", body_stripped, re.MULTILINE):
        body_stripped = f"# {title}\n\n{body_stripped.lstrip()}"

    # Footer with visible links
    footer_parts = ["", "---", ""]
    if source_url:
        footer_parts.append(f"**Source**: <{source_url}>")
    if raw_path:
        # Compute markdown link relative to the curated file's location
        try:
            rp_obj = Path(raw_path).resolve()
            rel = os.path.relpath(rp_obj, target.parent).replace(os.sep, "/")
            footer_parts.append(f"**Raw**: [{rp_obj.name}]({rel})")
        except (ValueError, OSError):
            footer_parts.append(f"**Raw**: `{raw_path}`")
    footer = "\n".join(footer_parts) if (source_url or raw_path) else ""

    content = f"{fm}\n\n{body_stripped.rstrip()}\n{footer}\n"
    target.write_text(content, encoding="utf-8")
    print(f"  Filed:     {target}")
    return target


# ── Main ─────────────────────────────────────────────────────────────────────


def print_slug_for(vault_root, topic, folder, title):
    """Print the canonical slug + path for a title without doing any ingestion.

    Used by the agent during batch ingestion to look up slugs ahead of time so
    cross-references in entry bodies use the actual filename the script would
    generate, not a guess.
    """
    if not title:
        print("Error: --slug-for requires --title", file=sys.stderr)
        return 1
    slug = slugify(title)
    topic_root = Path(vault_root) / topic
    wiki_dir = topic_root / "wiki"
    target_dir = wiki_dir / folder if folder else wiki_dir
    target = unique_path(target_dir / f"{slug}.md")
    print(f"slug={slug}")
    print(f"path={target}")
    if target.name != f"{slug}.md":
        print(f"# Note: collision-suffixed real name = {target.name}")
    return 0


def add_to_wiki(vault_root, topic, folder, source, title, tags, no_index,
                ingested_by=None, source_url_override=None, raw_path_override=None,
                force=False, fetch_only=False, no_raw=False, skip_integration=False,
                tier=None, confidence=None):
    topic_root = Path(vault_root) / topic
    if not topic_root.exists():
        print(f"Error: topic '{topic}' not found at {topic_root}", file=sys.stderr)
        print(f"Hint: create the topic dir first with README.md and wiki/ subfolder", file=sys.stderr)
        return 1

    raw_dir = topic_root / "raw"
    wiki_dir = topic_root / "wiki"

    # Dedup: if --source-url override (or source itself if it's a URL) is already
    # in the wiki, skip unless --force. Skipped in fetch-only mode (raw fetches
    # are idempotent at the file level — caller decides what to do).
    if not fetch_only:
        dedup_url = source_url_override or (source if source.startswith(("http://", "https://")) else None)
        if dedup_url and not force:
            existing = find_existing_by_url(wiki_dir, dedup_url)
            if existing:
                print(f"Skip (dedup): URL already in wiki at {existing}")
                print(f"Use --force to re-ingest anyway.")
                return 0

    # Acquire raw source. Skip the raw/ copy when:
    # - --raw-path override is given AND source is local (verbatim raw already exists)
    # - --no-raw flag is set (self-authored content with no external source)
    slug_hint = slugify(title) if title else None
    is_url = source.startswith(("http://", "https://"))
    skip_raw_copy = no_raw or (bool(raw_path_override) and not is_url)
    try:
        raw_path, body, suggested_title, source_url = acquire_source(source, raw_dir, slug_hint, skip_raw_copy=skip_raw_copy)
    except Exception as e:
        print(f"Error acquiring source: {e}", file=sys.stderr)
        return 1

    # Fetch-only mode: stop here, just return the raw path so the caller (agent)
    # can read it, synthesize a curated summary, then call this script again
    # with --source <summary> --source-url <orig> --raw-path <raw> to file it.
    if fetch_only:
        print(f"raw_path={raw_path}")
        print(f"source_url={source_url}")
        if suggested_title:
            print(f"suggested_title={suggested_title}")
        return 0

    final_title = title or suggested_title or Path(source).stem
    final_slug = slugify(final_title)

    # Apply overrides
    final_source_url = source_url_override or source_url
    if no_raw:
        final_raw_path = None  # self-authored content has no raw archive
    else:
        final_raw_path = raw_path_override or (str(raw_path) if raw_path else None)

    if tier is None:
        print("  Warning: --tier not provided. New entries should always specify a source quality tier (1=primary, 2=vendor, 3=expert, 4=community, self=our own synthesis). Pre-mortem fix #6.", file=sys.stderr)
    if confidence is None:
        print("  Warning: --confidence not provided. Assess how reliable this entry is: high (primary source fetched, corroborated), medium (single good source), low (synthesized from secondary refs).", file=sys.stderr)

    curated_path = write_curated(
        wiki_dir, folder, final_slug, final_title, body, final_source_url, tags,
        ingested_by=ingested_by, raw_path=final_raw_path, tier=tier, confidence=confidence,
    )

    # ── Integration step: bidirectional cross-link helpers ──────────────────
    # Mechanical only: detect broken outbound slug links and find inbound
    # mention candidates. Auto-rewrite unambiguous outbound matches in place.
    # Never auto-edit other files — inbound candidates are reported for the
    # agent to review.
    fixed = 0
    out_warnings = []
    inbound = []
    if not skip_integration:
        fixed, out_warnings = resolve_outbound_links(curated_path, wiki_dir)
        inbound = find_inbound_candidates(curated_path, wiki_dir, final_title)

        if fixed:
            print(f"  Outbound links auto-rewritten: {fixed}")
        if out_warnings:
            print(f"  Outbound link warnings: {len(out_warnings)}")
            for text, target, candidates in out_warnings:
                print(f"    [{text}]({target}) — candidates: {candidates or 'none'}")
        if inbound:
            shown = inbound[:15]
            print(f"  Inbound mention candidates ({len(inbound)} files):")
            for path, term, snippet in shown:
                rel = path.relative_to(wiki_dir).as_posix()
                print(f"    {rel}  [{term}]  ...{snippet}...")
            if len(inbound) > 15:
                print(f"    ... and {len(inbound) - 15} more (truncated)")
            print(f"  → consider adding backlinks to {curated_path.name} from these files")

    # Regenerate INDEX
    if not no_index:
        index_script = Path(__file__).parent / "wiki-index.py"
        if index_script.exists():
            print(f"  Regenerating _INDEX.md...")
            result = subprocess.run(
                [sys.executable, str(index_script), "--topic", topic, "--vault", str(vault_root)],
                capture_output=True, text=True,
            )
            if result.returncode != 0:
                print(f"  Warning: index generation failed: {result.stderr.strip()}")
            else:
                # Print the index script's status lines indented
                for line in result.stdout.strip().splitlines():
                    print(f"    {line}")
        else:
            print(f"  Warning: wiki-index.py not found at {index_script}")

    # Machine-parseable summary for callers (agent + future scripts)
    print(f"wiki_path={curated_path}")
    print(f"wiki_slug={curated_path.stem}")
    print(f"outbound_fixed={fixed}")
    print(f"outbound_warnings={len(out_warnings)}")
    print(f"inbound_candidates={len(inbound)}")

    return 0


def main():
    parser = argparse.ArgumentParser(description="Update (add) a source to a topic wiki")
    parser.add_argument("--topic", required=True, help="Topic name (folder under vault)")
    parser.add_argument("--folder", default="", help="Concept subfolder under wiki/ (e.g. 'memory-systems')")
    parser.add_argument("--source", required=False, help="URL or local file path (the body content). Not required for --slug-for mode.")
    parser.add_argument("--source-url", default=None, help="Override source URL stored in frontmatter (use when --source is a local synthesized summary but the canonical URL is elsewhere — e.g. YouTube case)")
    parser.add_argument("--raw-path", default=None, help="Override raw archive path stored in frontmatter and footer link (e.g. pre-fetched YouTube transcript path)")
    parser.add_argument("--title", help="Override auto-detected title")
    parser.add_argument("--tags", default="", help="Comma-separated tags")
    parser.add_argument("--ingested-by", default=None, help="Who ingested this (claude-code, clawd, cli)")
    parser.add_argument("--vault", default=DEFAULT_VAULT, help=f"Vault root (default: {DEFAULT_VAULT})")
    parser.add_argument("--no-index", action="store_true", help="Skip _INDEX.md regeneration")
    parser.add_argument("--force", action="store_true", help="Re-ingest even if source URL already in wiki")
    parser.add_argument("--fetch-only", action="store_true", help="Only fetch source to raw/, do NOT file a curated wiki entry. Prints raw_path= for the caller to read and synthesize on top of.")
    parser.add_argument("--no-raw", action="store_true", help="Self-authored content with no external source. Skip the raw/ copy and omit raw_path from frontmatter. Use for design docs, decisions, session synthesis, etc.")
    parser.add_argument("--tier", default=None, choices=["1", "2", "3", "4", "self"], help="Source quality tier: 1=peer-reviewed/primary (papers, official spec docs, source code), 2=established documentation (vendor docs, framework docs, official blog), 3=reputable expert/first-hand (founder posts, expert blogs, conf talks, journalism), 4=community (Medium, Reddit, anonymous gists), self=self-authored synthesis. STRONGLY recommended for every new entry — prerequisite for source-quality-aware answer weighting and the future nightly auto-ingest cycle's quarantine rules.")
    parser.add_argument("--confidence", default=None, choices=["high", "medium", "low"], help="Entry confidence level. Measures how reliable OUR entry is (not the source — that's tier). high=primary source fetched + corroborated, medium=single good source fetched, low=synthesized from secondary refs or source not fetched. STRONGLY recommended for every new entry.")
    parser.add_argument("--slug-for", dest="slug_for", action="store_true", help="Lookup mode: print the canonical slug + path for --title without ingesting. Use during batch ingestion to discover slugs ahead of time so cross-references in entry bodies match the actual filenames.")
    parser.add_argument("--skip-integration", action="store_true", help="Skip the post-write integration step (outbound link resolution + inbound mention scan). Default is to run it.")
    args = parser.parse_args()

    # Lookup mode — no ingestion, just print the slug + path
    if args.slug_for:
        return print_slug_for(args.vault, args.topic, args.folder, args.title)

    if not args.source:
        parser.error("--source is required (unless using --slug-for)")

    tags = [t.strip() for t in args.tags.split(",") if t.strip()]
    return add_to_wiki(
        args.vault, args.topic, args.folder, args.source, args.title, tags, args.no_index,
        ingested_by=args.ingested_by,
        source_url_override=args.source_url,
        raw_path_override=args.raw_path,
        force=args.force,
        fetch_only=args.fetch_only,
        no_raw=args.no_raw,
        skip_integration=args.skip_integration,
        tier=args.tier,
        confidence=args.confidence,
    )


if __name__ == "__main__":
    sys.exit(main())
