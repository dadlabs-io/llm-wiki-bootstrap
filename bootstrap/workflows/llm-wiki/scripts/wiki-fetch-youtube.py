#!/usr/bin/env python3
"""
Fetch a YouTube video transcript and save it as a verbatim raw archive
file under <topic>/raw/. Does NOT touch the curated wiki/ folder — that's
the caller's job (typically the /wiki-update slash command, which reads
the raw transcript and synthesizes a curated summary).

The download_transcript() function is lifted from the existing
research-data-ingestion/ingest-youtube.py with minor adaptations. Same
proven yt-dlp logic, no SQLite, no note-handler dependencies.

Designed to run inside the openclaw Docker container (yt-dlp lives there
at /usr/local/bin/yt-dlp). Can also run on host if yt-dlp is installed.

Usage:
    python3 wiki-fetch-youtube.py --topic <topic> \\
        --url https://www.youtube.com/watch?v=LCEmiRjPEtQ
"""

import argparse
import json
import os
import re
import sys
import tempfile
import time
from datetime import datetime
from pathlib import Path

# Atomic-write helper (icarus §8).
sys.path.insert(0, str(Path(__file__).resolve().parent))
from _atomic_io import atomic_write_text  # noqa: E402


# Path-resolution helpers live in the shared _wiki_config module (single
# source of truth for the multi-wiki config schema). Re-exported under the
# historical private names so the rest of this script is unchanged.
sys.path.insert(0, str(Path(__file__).resolve().parent))
from _wiki_config import default_vault as _default_vault, default_topic as _default_topic  # noqa: E402
# Force UTF-8 stdout on Windows
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

DEFAULT_VAULT = _default_vault()

try:
    import yt_dlp
    from yt_dlp.utils import DownloadError
except ImportError:
    print(
        "ERROR: yt_dlp not installed. Run inside openclaw container, or `pip install yt-dlp`.",
        file=sys.stderr,
    )
    sys.exit(2)


# ── Slug helpers ─────────────────────────────────────────────────────────────


SLUG_RE = re.compile(r"[^a-z0-9]+")


def slugify(text, max_len=50):
    """Short, filesystem-safe slug. Caps at 50 chars to avoid path length issues."""
    if not text:
        return "untitled"
    s = text.lower().strip()
    s = SLUG_RE.sub("-", s).strip("-")
    return (s[:max_len].rstrip("-") or "untitled")


def unique_path(target):
    target = Path(target)
    if not target.exists():
        return target
    stem, suffix, parent = target.stem, target.suffix, target.parent
    n = 2
    while True:
        cand = parent / f"{stem}-{n}{suffix}"
        if not cand.exists():
            return cand
        n += 1


# ── yt-dlp transcript fetch (lifted from ingest-youtube.py) ──────────────────


def download_transcript(url, max_retries=5, initial_delay=5):
    """Download YouTube transcript using yt-dlp with retries.

    Returns dict with: video_id, title, url, duration, upload_date, channel,
    segment_count, word_count, segments. Or None on failure.
    """
    print(f"Downloading transcript from: {url}")

    temp_dir = tempfile.mkdtemp()
    output_template = os.path.join(temp_dir, "transcript")

    ydl_opts = {
        "skip_download": True,
        "writesubtitles": True,
        "writeautomaticsub": True,
        "subtitleslangs": ["en"],
        "subtitlesformat": "json3",
        "outtmpl": output_template,
        "quiet": True,
        "no_warnings": True,
    }

    for retry_num in range(max_retries):
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)

            json_file = output_template + ".en.json3"
            if not os.path.exists(json_file):
                print("ERROR: no subtitle file produced", file=sys.stderr)
                return None

            with open(json_file, "r", encoding="utf-8") as f:
                transcript_data = json.load(f)

            # Combine tiny word-by-word segments into logical sentences
            segments = []
            current_text = ""
            current_start = None

            for event in transcript_data.get("events", []):
                if "segs" not in event:
                    continue
                for seg in event["segs"]:
                    text = seg.get("utf8", "")
                    if not text:
                        continue
                    start_time = event.get("tStartMs", 0) / 1000.0
                    if current_start is None:
                        current_start = start_time
                    current_text += text
                    if "\n" in text or "." in text or len(current_text) > 80:
                        cleaned = current_text.replace("\n", " ").strip()
                        if cleaned:
                            segments.append({"text": cleaned, "start": current_start})
                        current_text = ""
                        current_start = None

            if current_text.strip():
                segments.append(
                    {
                        "text": current_text.replace("\n", " ").strip(),
                        "start": current_start if current_start is not None else 0,
                    }
                )

            return {
                "video_id": info.get("id", ""),
                "title": info.get("title", "Unknown"),
                "url": url,
                "duration": info.get("duration", 0),
                "upload_date": info.get("upload_date", ""),
                "channel": info.get("channel", "Unknown"),
                "segment_count": len(segments),
                "word_count": sum(len(s["text"].split()) for s in segments),
                "segments": segments,
            }

        except DownloadError as e:
            if retry_num < max_retries - 1:
                delay = initial_delay * (2 ** retry_num)
                print(f"Download failed, retry in {delay}s: {e}", file=sys.stderr)
                time.sleep(delay)
            else:
                print(f"ERROR after {max_retries} retries: {e}", file=sys.stderr)
                return None
        except Exception as e:
            print(f"ERROR: {e}", file=sys.stderr)
            return None
    return None


# ── Render raw transcript as markdown ────────────────────────────────────────


def render_raw_markdown(td, ingested_by):
    """Build the verbatim raw transcript markdown file content."""
    duration_min = td["duration"] // 60 if td["duration"] else 0
    duration_str = f"{duration_min}m" if duration_min else "?"
    fetched_at = datetime.now().isoformat(timespec="seconds")

    fm = [
        "---",
        f'title: "{td["title"]}"',
        f"source_url: {td['url']}",
        f"video_id: {td['video_id']}",
        f"channel: {td['channel']}",
        f"duration_seconds: {td['duration']}",
        f"duration: {duration_str}",
        f"upload_date: {td['upload_date']}",
        f"fetched_at: {fetched_at}",
        f"ingested_by: {ingested_by}",
        f"segment_count: {td['segment_count']}",
        f"word_count: {td['word_count']}",
        "type: youtube-transcript",
        "---",
        "",
    ]

    body = [
        f"# {td['title']} — Transcript",
        "",
        f"**Channel**: {td['channel']}  ",
        f"**Duration**: {duration_str}  ",
        f"**Source**: <{td['url']}>",
        "",
        "---",
        "",
        "## Transcript",
        "",
    ]

    for seg in td["segments"]:
        body.append(seg["text"])
        body.append("")

    return "\n".join(fm + body)


# ── Main ─────────────────────────────────────────────────────────────────────


def fetch_to_raw(vault_root, topic, url, ingested_by, slug_override=None):
    topic_root = Path(vault_root) / topic
    if not topic_root.exists():
        print(f"ERROR: topic '{topic}' not found at {topic_root}", file=sys.stderr)
        return 1

    raw_dir = topic_root / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)

    td = download_transcript(url)
    if td is None:
        return 1

    slug = slug_override or slugify(td["title"])
    date = datetime.now().strftime("%Y-%m-%d")
    raw_filename = f"{date}-{slug}-transcript.md"
    raw_path = unique_path(raw_dir / raw_filename)

    raw_content = render_raw_markdown(td, ingested_by)
    atomic_write_text(raw_path, raw_content)
    print(f"Saved raw transcript: {raw_path}")
    print(f"  Title: {td['title']}")
    print(f"  Channel: {td['channel']}")
    print(f"  Duration: {td['duration'] // 60 if td['duration'] else '?'}m")
    print(f"  Segments: {td['segment_count']}")
    print(f"  Words: {td['word_count']}")
    print()
    print("Next: read this file and synthesize a curated summary, then call wiki-update.py")
    print(f"raw_path={raw_path}")  # machine-readable for caller
    return 0


def main():
    parser = argparse.ArgumentParser(description="Fetch YouTube transcript to wiki raw/")
    parser.add_argument("--topic", required=True, help="Topic name")
    parser.add_argument("--url", required=True, help="YouTube URL")
    parser.add_argument("--vault", default=DEFAULT_VAULT, help=f"Vault root (default: {DEFAULT_VAULT})")
    parser.add_argument("--ingested-by", default="cli", help="Who initiated this fetch (claude-code, clawd, cli)")
    parser.add_argument("--slug", default=None, help="Override slug (otherwise derived from title)")
    args = parser.parse_args()
    return fetch_to_raw(args.vault, args.topic, args.url, args.ingested_by, args.slug)


if __name__ == "__main__":
    sys.exit(main())
