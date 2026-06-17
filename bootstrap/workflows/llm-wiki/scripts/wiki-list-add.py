#!/usr/bin/env python3
"""
Add a source to a topic wiki's ingest queue.

Drops a .queue file into <topic>/_inbox/pending/ that wiki-list-process.py
will later batch-ingest. The producer half of a producer/consumer pattern —
called from ClawD (Discord) or Claude Code throughout the day, then processed
in a deliberate batch later.

Queue file format (simple key: value lines):
    source: https://example.com/article
    folder: memory-systems
    title: Optional Title
    tags: tag1, tag2
    added_at: 2026-04-08T12:34:56
    added_by: clawd

Usage:
    python3 wiki-list-add.py --topic <topic> \\
        --source https://example.com/article --folder memory-systems

    python3 wiki-list-add.py --topic <topic> \\
        --source ./notes.md --folder tooling --title "My Notes"
"""

import argparse
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

# Atomic-write helper (icarus §8).
sys.path.insert(0, str(Path(__file__).resolve().parent))
from _atomic_io import atomic_write_text  # noqa: E402


# Path-resolution helpers live in the shared _wiki_config module (single
# source of truth for the multi-wiki config schema). Re-exported under the
# historical private names so the rest of this script is unchanged.
sys.path.insert(0, str(Path(__file__).resolve().parent))
from _wiki_config import default_vault as _default_vault, default_topic as _default_topic  # noqa: E402
# Force UTF-8 stdout on Windows so Unicode in wiki content doesn't crash printing
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

DEFAULT_VAULT = _default_vault()
ACTIVITY_LOG = str(Path.home() / ".config" / "wiki-cycle" / "activity.jsonl")

SLUG_RE = re.compile(r"[^a-z0-9]+")


def _write_activity_log(entry):
    """Append a structured record of this invocation to the activity log.
    Ground truth for what actually ran — independent of any AI claims in
    chat sessions. Used by the hallucination watchdog to detect when an
    agent claims to have queued an item without actually invoking this
    script."""
    try:
        log_path = Path(ACTIVITY_LOG)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        entry.setdefault("ts", datetime.now().astimezone().isoformat(timespec="seconds"))
        with log_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    except OSError:
        # Logging failure must not break the script's primary job
        pass


def slugify(text, max_len=60):
    if not text:
        return "untitled"
    s = text.lower().strip()
    s = SLUG_RE.sub("-", s).strip("-")
    if not s:
        return "untitled"
    return s[:max_len].rstrip("-") or "untitled"


def derive_slug(source, title):
    if title:
        return slugify(title)
    if source.startswith(("http://", "https://")):
        # Use last path segment
        from urllib.parse import urlparse
        path = urlparse(source).path.rstrip("/").split("/")[-1] or urlparse(source).netloc
        return slugify(path)
    return slugify(Path(source).stem)


def unique_path(target):
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


def regenerate_pending_list(vault_root, topic):
    """Call wiki-list-render.py to refresh the human-readable list view."""
    render_script = Path(__file__).parent / "wiki-list-render.py"
    if not render_script.exists():
        return
    import subprocess
    subprocess.run(
        [sys.executable, str(render_script), "--topic", topic, "--vault", str(vault_root)],
        capture_output=True, text=True,
    )


def _scan_for_url(path_iter, keys, target_url):
    """Iterate over `.md` files yielded by path_iter, scan the first 30 lines
    of each for any of `keys` (`source:` for queue tickets, `source_url:` for
    wiki entries), and return the first file whose value equals target_url.
    Returns the Path or None. Tolerates unreadable files (skips silently)."""
    for p in path_iter:
        try:
            text = p.read_text(encoding="utf-8")
        except OSError:
            continue
        for line in text.splitlines()[:30]:
            stripped = line.strip()
            for key in keys:
                if stripped.startswith(key):
                    existing = stripped.split(":", 1)[1].strip()
                    # Strip quotes if wrapped — frontmatter often uses "..."
                    if existing.startswith(('"', "'")) and existing.endswith(existing[0]):
                        existing = existing[1:-1]
                    if existing == target_url:
                        return p
                    break  # only check the first matching key per file
            else:
                continue
            break
    return None


def _find_existing_url(topic_root, source):
    """Search every location where a URL might already exist in the topic.
    Returns (location_label, file_name) on first match, or None."""
    pending_dir = topic_root / "_inbox" / "pending"
    done_dir = topic_root / "_inbox" / "done"
    proposed_dir = topic_root / "_inbox" / "proposed"
    wiki_dir = topic_root / "wiki"

    # Order matters — most recent/relevant first. A URL in pending/ is "still
    # queued"; in proposed/ is "already ingested but unpromoted"; in wiki/ is
    # "already published"; in done/ is "queue ticket cleaned up after ingest".
    locations = [
        ("pending/", pending_dir.glob("*.md"), ("source:",)),
        ("proposed/", proposed_dir.rglob("*.md"), ("source_url:", "source:")),
        ("wiki/", wiki_dir.rglob("*.md"), ("source_url:",)),
        ("done/", done_dir.glob("*.md"), ("source:",)),
    ]
    for label, iter_paths, keys in locations:
        match = _scan_for_url(iter_paths, keys, source)
        if match:
            return label, match.name
    return None


def add_to_queue(vault_root, topic, source, folder, title, tags, added_by, priority):
    topic_root = Path(vault_root) / topic
    if not topic_root.exists():
        msg = f"topic '{topic}' not found at {topic_root}"
        print(f"Error: {msg}", file=sys.stderr)
        _write_activity_log({
            "topic": topic, "source": source, "added_by": added_by,
            "result": "error", "error": msg,
        })
        return 1

    pending_dir = topic_root / "_inbox" / "pending"
    pending_dir.mkdir(parents=True, exist_ok=True)

    # URL-based dedup. The source URL is the natural identity key — slug/title
    # can vary. Check against every location where this URL might already exist:
    #
    #   1. _inbox/pending/        — open queue tickets (look for `source:` line)
    #   2. _inbox/done/           — processed queue tickets (same `source:` line)
    #   3. _inbox/proposed/       — staged-but-not-promoted wiki entries
    #                                (frontmatter `source_url:` field)
    #   4. wiki/                  — promoted wiki entries (same `source_url:`)
    #
    # Without checking proposed/ + wiki/, a same-day re-scan (e.g. a Drive folder
    # re-fetch after an earlier cycle staged 76 entries to proposed/) re-queues
    # every URL even though wiki-update would no-op against the staged entries.
    # Cycle 2026-05-11-03 slice 4 burned an agent on 18 such no-ops; this fix
    # closes that gap.
    if source.startswith(("http://", "https://")):
        match = _find_existing_url(topic_root, source)
        if match:
            location, existing_file = match
            _write_activity_log({
                "topic": topic, "source": source, "added_by": added_by,
                "result": "duplicate_skipped",
                "existing_location": location,
                "existing_file": existing_file,
            })
            print(f"Already present in {location}: {existing_file}")
            print(f"  source: {source}")
            return 0

    # Default priority 3, validate single digit
    if not priority:
        priority = "3"
    if priority not in "0123456789":
        msg = f"priority must be a single digit 0-9 (got {priority!r})"
        print(f"Error: {msg}", file=sys.stderr)
        _write_activity_log({
            "topic": topic, "source": source, "added_by": added_by,
            "result": "error", "error": msg,
        })
        return 1

    timestamp = datetime.now().strftime("%Y-%m-%d-%H%M%S")
    slug = derive_slug(source, title)
    queue_filename = f"{priority}-{timestamp}-{slug}.md"
    queue_path = unique_path(pending_dir / queue_filename)

    # YAML frontmatter wrapping so Obsidian renders the metadata as a block
    lines = ["---"]
    lines.append(f"source: {source}")
    if folder:
        lines.append(f"folder: {folder}")
    else:
        lines.append("folder:")
    if title:
        lines.append(f"title: {title}")
    if tags:
        lines.append(f"tags: {', '.join(tags)}")
    lines.append(f"priority: {priority}")
    lines.append(f"added_at: {datetime.now().astimezone().isoformat(timespec='seconds')}")
    lines.append(f"added_by: {added_by}")
    lines.append("---")
    lines.append("")
    # Visible body for Obsidian — clickable link plus minimal context
    title_line = title if title else (source if len(source) < 80 else source[:77] + "…")
    lines.append(f"# {title_line}")
    lines.append("")
    lines.append(f"**Source**: <{source}>")
    lines.append("")
    lines.append(f"_Queued by `{added_by}` at {datetime.now().astimezone().isoformat(timespec='seconds')}, priority {priority}._")
    lines.append("")
    lines.append("_Awaiting processing. Will be moved to `_inbox/done/` when ingested._")

    atomic_write_text(queue_path, "\n".join(lines) + "\n")
    _write_activity_log({
        "topic": topic, "source": source, "added_by": added_by,
        "result": "queued", "pending_file": queue_path.name,
        "priority": priority,
    })

    print(f"Queued: {queue_path}")
    print(f"  source: {source}")
    if folder:
        print(f"  folder: {folder}")
    if title:
        print(f"  title:  {title}")
    if priority:
        print(f"  priority: {priority}")

    # Show how many items in queue now (accept .md current + .queue legacy)
    pending_count = sum(1 for p in pending_dir.iterdir() if p.suffix in (".md", ".queue"))
    print(f"\nPending queue items: {pending_count}")
    print(f"Process with: wiki-list-process.py --topic {topic}")

    # Regenerate the human-readable list view
    regenerate_pending_list(vault_root, topic)
    return 0


def main():
    parser = argparse.ArgumentParser(description="Add a source to a wiki ingest queue")
    parser.add_argument("--topic", required=True, help="Topic name")
    parser.add_argument("--source", required=True, help="URL or local file path")
    parser.add_argument("--folder", default="", help="Target wiki/ subfolder")
    parser.add_argument("--title", default="", help="Optional title override")
    parser.add_argument("--tags", default="", help="Comma-separated tags")
    parser.add_argument("--priority", default="", help="Priority 1-5 (1=highest, default 3)")
    parser.add_argument("--vault", default=DEFAULT_VAULT, help=f"Vault root (default: {DEFAULT_VAULT})")
    parser.add_argument("--added-by", default="cli", help="Who added this (e.g. 'clawd', 'cli', 'discord')")
    args = parser.parse_args()

    tags = [t.strip() for t in args.tags.split(",") if t.strip()]
    return add_to_queue(args.vault, args.topic, args.source, args.folder, args.title, tags, args.added_by, args.priority)


if __name__ == "__main__":
    sys.exit(main())
