#!/usr/bin/env python3
"""
Render a topic's queue (pending + done + failed) as a human-readable markdown
table at <topic>/_inbox/pending-list.md.

This is a DERIVED view — never edit pending-list.md by hand. It gets
regenerated on every wiki-list-add and wiki-list-process call. Same pattern
as wiki/ + _INDEX.md: the .queue files are canonical, this is the visible map.

Usage:
    python3 wiki-list-render.py --topic <topic>
"""

import argparse
import os
import re
import sys
from datetime import datetime
from pathlib import Path

# Atomic-write helper (icarus §8).
sys.path.insert(0, str(Path(__file__).resolve().parent))
from _atomic_io import atomic_write_text  # noqa: E402


def _default_vault():
    """Resolve vault_root from <cwd>/.claude/wiki-config.json if present,
    otherwise fall back to CWD (project root). Per-project installs record
    vault_root = <project-root>; combined with wiki_topic this gives
    <project>/<topic>/wiki/ (default <topic> = 'llm-wiki')."""
    import json as _json
    cfg_path = Path.cwd() / ".claude" / "wiki-config.json"
    if cfg_path.exists():
        try:
            cfg = _json.loads(cfg_path.read_text(encoding="utf-8"))
            v = cfg.get("vault_root")
            if v:
                return str(Path(v))
        except (_json.JSONDecodeError, OSError):
            pass
    return str(Path.cwd())


def _default_topic():
    """Resolve wiki_topic from <cwd>/.claude/wiki-config.json if present,
    otherwise fall back to 'llm-wiki' (the v1 per-project wiki folder name).
    Used by scripts that take --topic as an arg to provide a sensible
    default in per-project installs."""
    import json as _json
    cfg_path = Path.cwd() / ".claude" / "wiki-config.json"
    if cfg_path.exists():
        try:
            cfg = _json.loads(cfg_path.read_text(encoding="utf-8"))
            t = cfg.get("wiki_topic")
            if t:
                return t
        except (_json.JSONDecodeError, OSError):
            pass
    return "llm-wiki"
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

DEFAULT_VAULT = _default_vault()


def parse_queue_file(path):
    """Parse a .queue file into a dict."""
    fields = {}
    try:
        text = path.read_text(encoding="utf-8")
    except (UnicodeDecodeError, OSError):
        return None
    for line in text.splitlines():
        if not line.strip() or line.strip().startswith("#"):
            continue
        if ":" not in line:
            continue
        key, _, value = line.partition(":")
        fields[key.strip().lower()] = value.strip()
    return fields


def truncate(s, n):
    if not s:
        return ""
    return s if len(s) <= n else s[: n - 1] + "…"


def collect_items(directory, status):
    """Collect queue items from a directory, tag with status."""
    items = []
    if not directory.exists():
        return items
    for path in sorted(directory.iterdir()):
        if path.suffix not in (".md", ".queue"):
            continue
        fields = parse_queue_file(path)
        if fields is None:
            continue
        items.append({
            "filename": path.name,
            "status": status,
            "priority": fields.get("priority", "3"),
            "source": fields.get("source", ""),
            "folder": fields.get("folder", ""),
            "title": fields.get("title", ""),
            "added_by": fields.get("added_by", ""),
            "added_at": fields.get("added_at", ""),
        })
    return items


def render_table(items, status_label):
    """Render a list of items as a markdown table."""
    if not items:
        return f"_({status_label}: empty)_\n"
    out = []
    out.append("| P | Source | Folder | Title | Added by | Added at |")
    out.append("|---|---|---|---|---|---|")
    for it in items:
        priority = it.get("priority", "3")
        source = truncate(it["source"], 70)
        # Escape pipes in source for markdown table
        source = source.replace("|", "\\|")
        # Make source a clickable link
        if source.startswith(("http://", "https://")):
            source_md = f"[{truncate(it['source'], 60)}]({it['source']})"
        else:
            source_md = source
        folder = it["folder"] or "—"
        title = truncate(it["title"], 30) or "—"
        added_by = it["added_by"] or "—"
        added_at = truncate(it["added_at"], 19) or "—"
        out.append(f"| {priority} | {source_md} | {folder} | {title} | {added_by} | {added_at} |")
    return "\n".join(out) + "\n"


def render_pending_list(vault_root, topic):
    topic_root = Path(vault_root) / topic
    if not topic_root.exists():
        print(f"ERROR: topic '{topic}' not found at {topic_root}", file=sys.stderr)
        return 1

    pending_dir = topic_root / "_inbox" / "pending"
    done_dir = topic_root / "_inbox" / "done"
    failed_dir = topic_root / "_inbox" / "failed"

    pending = collect_items(pending_dir, "pending")
    done = collect_items(done_dir, "done")
    failed = collect_items(failed_dir, "failed")

    # Sort pending by priority then added_at
    def sort_key(it):
        try:
            p = int(it.get("priority", "3"))
        except (ValueError, TypeError):
            p = 3
        return (p, it.get("added_at", ""))
    pending.sort(key=sort_key)

    out = []
    out.append(f"# {topic} — Ingestion List")
    out.append("")
    out.append(f"**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    out.append(f"**Pending**: {len(pending)} | **Done**: {len(done)} | **Failed**: {len(failed)}")
    out.append("")
    out.append("> This file is auto-generated by `wiki-list-render.py`. Do not edit by hand —")
    out.append("> changes will be overwritten. Edit the underlying `.queue` files in")
    out.append("> `_inbox/pending/` to change priority or other fields.")
    out.append("")
    out.append("**Priority**: 1 = highest, 5 = lowest. Default 3.")
    out.append("")
    out.append("---")
    out.append("")
    out.append("## Pending")
    out.append("")
    out.append(render_table(pending, "pending"))
    out.append("")
    out.append("---")
    out.append("")
    out.append("## Done")
    out.append("")
    out.append(render_table(done, "done"))
    out.append("")
    out.append("---")
    out.append("")
    out.append("## Failed")
    out.append("")
    out.append(render_table(failed, "failed"))
    out.append("")

    target = topic_root / "_inbox" / "pending-list.md"
    atomic_write_text(target, "\n".join(out))
    print(f"Wrote: {target}")
    print(f"  Pending: {len(pending)}, Done: {len(done)}, Failed: {len(failed)}")
    return 0


def main():
    parser = argparse.ArgumentParser(description="Render queue as a markdown table view")
    parser.add_argument("--topic", required=True)
    parser.add_argument("--vault", default=DEFAULT_VAULT)
    args = parser.parse_args()
    return render_pending_list(args.vault, args.topic)


if __name__ == "__main__":
    sys.exit(main())
