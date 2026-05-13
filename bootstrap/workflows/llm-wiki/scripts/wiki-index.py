#!/usr/bin/env python3
"""
Generate _INDEX.md for a topic wiki.

Walks {vault}/{topic}/wiki/ and produces an _INDEX.md at the topic root with:
  - Folder tree
  - Per-folder grouped file list with title, summary, tags, mtime

The INDEX is fully derived — safe to delete and regenerate at any time.

Usage:
    python3 wiki-index.py --topic agentic-design
    python3 wiki-index.py --topic agentic-design --vault /custom/vault/path
"""

import argparse
import os
import re
import sys
from datetime import datetime
from pathlib import Path


def _default_vault():
    """Resolve vault_root from <cwd>/.claude/wiki-config.json if present,
    otherwise fall back to "llm-wiki/wiki" relative to CWD. Per-project
    installs put wiki content at <project>/llm-wiki/wiki/."""
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
    return str(Path.cwd() / "llm-wiki" / "wiki")
# Force UTF-8 stdout on Windows so Unicode in wiki content doesn't crash printing
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

DEFAULT_VAULT = _default_vault()


# ── Frontmatter / metadata extraction ────────────────────────────────────────


FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)


def parse_frontmatter(content):
    """Parse a minimal YAML-style frontmatter block. Returns (frontmatter_dict, body).

    Only supports flat key: value pairs and one-line list values like
    `tags: [a, b, c]`. Good enough for INDEX generation; not a full YAML parser.
    """
    m = FRONTMATTER_RE.match(content)
    if not m:
        return {}, content

    raw = m.group(1)
    body = content[m.end():]
    fm = {}
    for line in raw.splitlines():
        if not line.strip() or line.strip().startswith("#"):
            continue
        if ":" not in line:
            continue
        key, _, value = line.partition(":")
        key = key.strip()
        value = value.strip()
        # List form: [a, b, c]
        if value.startswith("[") and value.endswith("]"):
            inner = value[1:-1]
            fm[key] = [v.strip().strip('"').strip("'") for v in inner.split(",") if v.strip()]
        else:
            fm[key] = value.strip('"').strip("'")
    return fm, body


def extract_title(body, fallback):
    """First H1 heading, else fallback (filename stem)."""
    for line in body.splitlines():
        m = re.match(r"^#\s+(.+)$", line)
        if m:
            return m.group(1).strip()
    return fallback


def extract_summary(body, max_chars=220):
    """First non-heading, non-blank paragraph, truncated."""
    # Strip code fences entirely
    body = re.sub(r"```.*?```", "", body, flags=re.DOTALL)
    paragraphs = []
    current = []
    for line in body.splitlines():
        stripped = line.strip()
        if not stripped:
            if current:
                paragraphs.append(" ".join(current))
                current = []
            continue
        if stripped.startswith("#"):
            if current:
                paragraphs.append(" ".join(current))
                current = []
            continue
        # Skip frontmatter-style **Bold:** prefixed metadata lines that are common
        # in notes (e.g. **Source**: ..., **Status**: ...)
        if re.match(r"^\*\*[^*]+\*\*\s*[:.]", stripped):
            continue
        # Skip horizontal rules
        if re.match(r"^-{3,}$", stripped):
            continue
        current.append(stripped)
    if current:
        paragraphs.append(" ".join(current))

    if not paragraphs:
        return ""
    summary = paragraphs[0]
    # Strip markdown emphasis for cleaner display
    summary = re.sub(r"[*_`]", "", summary)
    if len(summary) > max_chars:
        summary = summary[: max_chars - 1].rstrip() + "…"
    return summary


def extract_tags(frontmatter, body, filename):
    """Tags from frontmatter `tags:` first, otherwise lightweight auto-detect."""
    if "tags" in frontmatter:
        if isinstance(frontmatter["tags"], list):
            return frontmatter["tags"]
        return [t.strip() for t in str(frontmatter["tags"]).split(",") if t.strip()]
    # No frontmatter — return empty. Auto-tagging is wiki-update.py's job.
    return []


# ── Walk and build ───────────────────────────────────────────────────────────


def collect_files(wiki_root):
    """Yield (relative_path, absolute_path) for every .md file under wiki_root."""
    for root, dirs, files in os.walk(wiki_root):
        # Skip hidden dirs (.git etc)
        dirs[:] = sorted([d for d in dirs if not d.startswith(".")])
        for f in sorted(files):
            if f.endswith(".md") and not f.startswith("."):
                abs_path = os.path.join(root, f)
                rel_path = os.path.relpath(abs_path, wiki_root)
                # Normalize to forward slashes for markdown links
                rel_path = rel_path.replace(os.sep, "/")
                yield rel_path, abs_path


def read_file_meta(abs_path, rel_path):
    """Read a wiki file and return a dict of metadata used by the index."""
    try:
        with open(abs_path, "r", encoding="utf-8") as f:
            content = f.read()
    except (UnicodeDecodeError, OSError) as e:
        return {
            "rel_path": rel_path,
            "title": Path(rel_path).stem.replace("-", " ").replace("_", " ").title(),
            "summary": f"(could not read: {e})",
            "tags": [],
            "mtime": "",
            "size": 0,
        }

    fm, body = parse_frontmatter(content)
    fallback_title = Path(rel_path).stem.replace("-", " ").replace("_", " ").title()
    title = extract_title(body, fallback_title)
    summary = extract_summary(body)
    tags = extract_tags(fm, body, rel_path)
    mtime = datetime.fromtimestamp(os.path.getmtime(abs_path)).strftime("%Y-%m-%d")
    size = os.path.getsize(abs_path)

    return {
        "rel_path": rel_path,
        "title": title,
        "summary": summary,
        "tags": tags,
        "mtime": mtime,
        "size": size,
    }


def group_by_folder(file_metas):
    """Return ordered {folder: [meta, ...]} dict."""
    grouped = {}
    for meta in file_metas:
        folder = os.path.dirname(meta["rel_path"]) or "(root)"
        grouped.setdefault(folder, []).append(meta)
    return dict(sorted(grouped.items()))


def render_tree(grouped):
    """Render the folder tree as a markdown code block."""
    lines = ["wiki/"]
    folders = list(grouped.keys())
    for i, folder in enumerate(folders):
        is_last_folder = i == len(folders) - 1
        prefix_folder = "└── " if is_last_folder else "├── "
        if folder == "(root)":
            label = "(root)"
        else:
            label = folder + "/"
        files = grouped[folder]
        lines.append(f"{prefix_folder}{label}  ({len(files)} file{'s' if len(files) != 1 else ''})")
        child_indent = "    " if is_last_folder else "│   "
        for j, meta in enumerate(files):
            is_last_file = j == len(files) - 1
            prefix_file = "└── " if is_last_file else "├── "
            lines.append(f"{child_indent}{prefix_file}{os.path.basename(meta['rel_path'])}")
    return "\n".join(lines)


def render_index(topic_name, grouped, total_files, total_size_kb):
    """Render the full _INDEX.md content."""
    out = []
    out.append(f"# {topic_name} Wiki — Index")
    out.append("")
    out.append(f"**Topic**: `{topic_name}`")
    out.append(f"**Files**: {total_files}")
    out.append(f"**Size**: {total_size_kb:.1f} KB")
    out.append(f"**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    out.append("")
    out.append("> This file is auto-generated by `wiki-index.py`. Do not edit by hand —")
    out.append("> changes will be overwritten on next regeneration.")
    out.append("")
    out.append("**See also**: [README.md](README.md) — topic scope and ingest rules")
    out.append("")
    out.append("---")
    out.append("")
    out.append("## Folder Tree")
    out.append("")
    out.append("```")
    out.append(render_tree(grouped))
    out.append("```")
    out.append("")
    out.append("---")
    out.append("")
    out.append("## Files by Folder")
    out.append("")

    for folder, files in grouped.items():
        if folder == "(root)":
            heading = "### (root)"
        else:
            heading = f"### {folder}/"
        out.append(heading)
        out.append("")
        for meta in files:
            link = f"[{meta['title']}](wiki/{meta['rel_path']})"
            out.append(f"- **{link}**")
            if meta["summary"]:
                out.append(f"  {meta['summary']}")
            tag_part = ""
            if meta["tags"]:
                tag_part = " · " + " ".join(f"#{t}" for t in meta["tags"])
            out.append(f"  *Updated {meta['mtime']}{tag_part}*")
            out.append("")
        out.append("")

    # Tag summary across all files
    all_tags = {}
    for files in grouped.values():
        for meta in files:
            for tag in meta["tags"]:
                all_tags[tag] = all_tags.get(tag, 0) + 1
    if all_tags:
        out.append("---")
        out.append("")
        out.append("## Tags")
        out.append("")
        for tag, count in sorted(all_tags.items(), key=lambda x: (-x[1], x[0])):
            out.append(f"- `#{tag}` ({count})")
        out.append("")

    return "\n".join(out)


# ── Main ─────────────────────────────────────────────────────────────────────


def generate_index(vault_root, topic):
    topic_root = Path(vault_root) / topic
    wiki_root = topic_root / "wiki"

    if not topic_root.exists():
        print(f"Error: topic '{topic}' not found at {topic_root}", file=sys.stderr)
        return 1

    if not wiki_root.exists():
        print(f"Error: wiki/ folder missing under {topic_root}", file=sys.stderr)
        return 1

    files = list(collect_files(str(wiki_root)))
    metas = [read_file_meta(abs_p, rel_p) for rel_p, abs_p in files]
    grouped = group_by_folder(metas)
    total_size_kb = sum(m["size"] for m in metas) / 1024.0

    content = render_index(topic, grouped, len(metas), total_size_kb)
    index_path = topic_root / "_INDEX.md"
    with open(index_path, "w", encoding="utf-8") as f:
        f.write(content)

    print(f"Wrote {index_path}")
    print(f"  Files: {len(metas)}")
    print(f"  Folders: {len(grouped)}")
    print(f"  Size: {total_size_kb:.1f} KB")
    return 0


def main():
    parser = argparse.ArgumentParser(description="Generate a topic wiki _INDEX.md")
    parser.add_argument("--topic", required=True, help="Topic name (folder under vault)")
    parser.add_argument("--vault", default=DEFAULT_VAULT, help=f"Vault root (default: {DEFAULT_VAULT})")
    args = parser.parse_args()
    return generate_index(args.vault, args.topic)


if __name__ == "__main__":
    sys.exit(main())
