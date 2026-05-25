#!/usr/bin/env python3
"""Ensure every outbound wiki link has a reciprocal inbound link.

For each target entry, the script maintains a dedicated auto-managed section
("<!-- BACKLINKS-AUTO -->" fenced block) that holds every other wiki entry
currently linking to it. The section is regenerated from scratch on every run
so drift can't accumulate. Hand-curated "Related" sections are untouched.

Usage
-----
    python wiki-reciprocate-backlinks.py \
        --topic agentic-design \
        --vault llm-wiki/wiki

    # Only process entries modified in the last N hours:
    python wiki-reciprocate-backlinks.py --topic agentic-design --since-hours 24

    # Dry run — show what would change without writing:
    python wiki-reciprocate-backlinks.py --topic agentic-design --dry-run

    # Emit cycle-contract JSON alongside normal stdout:
    python wiki-reciprocate-backlinks.py --topic agentic-design \
        --cycle-id 2026-04-24-01 \
        --run-folder docker/.../2026-04-24/2026-04-24-01/

Cycle contract
--------------
When --cycle-id and --run-folder are supplied, writes
<run-folder>/reciprocate-backlinks.json and .md per the shared return-format
contract. Step name: "reciprocate-backlinks".
"""

from __future__ import annotations


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
import argparse
import json
import re
import sys
import time
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

# Local helper for atomic writes (icarus integration plan §8).
sys.path.insert(0, str(Path(__file__).resolve().parent))
from _atomic_io import atomic_write_text  # noqa: E402

MARKER_START = "<!-- BACKLINKS-AUTO START -->"
MARKER_END = "<!-- BACKLINKS-AUTO END -->"
LINK_RE = re.compile(r"\[([^\]]+)\]\(([^)]+\.md)\)")


def iso_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def read_frontmatter_title(path: Path) -> str:
    """Extract title from frontmatter; fall back to H1 or filename."""
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return path.stem
    # Frontmatter title:
    m = re.search(r"^---\s*\n(.*?)\n---\s*\n", text, re.DOTALL | re.MULTILINE)
    if m:
        fm = m.group(1)
        tm = re.search(r'^title:\s*["\']?(.+?)["\']?\s*$', fm, re.MULTILINE)
        if tm:
            return tm.group(1).strip().strip('"').strip("'")
    # H1 fallback:
    hm = re.search(r"^# (.+)$", text, re.MULTILINE)
    if hm:
        return hm.group(1).strip()
    return path.stem


def find_wiki_entries(wiki_root: Path) -> list[Path]:
    skip_names = {"_INDEX.md", "_MAP.md"}
    return sorted(
        p for p in wiki_root.rglob("*.md")
        if not p.name.startswith(".") and p.name not in skip_names
    )


def extract_outbound_links(entry: Path) -> list[tuple[str, Path]]:
    """Return list of (link_text, resolved_target_path) for outbound .md links."""
    text = entry.read_text(encoding="utf-8")
    # Strip the auto-backlinks section so we don't re-count auto links:
    text = re.sub(
        rf"{re.escape(MARKER_START)}.*?{re.escape(MARKER_END)}",
        "",
        text,
        flags=re.DOTALL,
    )
    out = []
    for match in LINK_RE.finditer(text):
        link_text = match.group(1)
        target_rel = match.group(2)
        target_abs = (entry.parent / target_rel).resolve()
        out.append((link_text, target_abs))
    return out


def build_reverse_index(entries: list[Path]) -> dict[Path, set[Path]]:
    """Map target -> set of entries that link to it."""
    reverse: dict[Path, set[Path]] = defaultdict(set)
    for entry in entries:
        for _, target in extract_outbound_links(entry):
            try:
                target_resolved = target.resolve()
                if target_resolved.exists() and target_resolved != entry.resolve():
                    reverse[target_resolved].add(entry.resolve())
            except OSError:
                continue
    return reverse


def rewrite_backlinks_section(
    entry: Path, referrers: set[Path], wiki_root: Path, dry_run: bool = False
) -> tuple[bool, list[str], list[str]]:
    """Rewrite the auto-backlinks block. Returns (changed, added, removed)."""
    text = entry.read_text(encoding="utf-8")

    # Build the new block
    if not referrers:
        new_block = ""  # no backlinks → no section at all
    else:
        lines = [MARKER_START, "", "## Backlinks (auto-maintained)", ""]
        lines.append(
            "_Other entries linking to this one. Managed by `wiki-reciprocate-backlinks.py`; "
            "do not hand-edit within the BACKLINKS-AUTO markers._"
        )
        lines.append("")
        ref_sorted = sorted(referrers, key=lambda p: p.name)
        for ref in ref_sorted:
            title = read_frontmatter_title(ref)
            rel = Path(
                *([".."] * (len(entry.parent.relative_to(wiki_root).parts)))
                + list(ref.relative_to(wiki_root).parts)
            ).as_posix()
            lines.append(f"- [{title}]({rel})")
        lines.append("")
        lines.append(MARKER_END)
        new_block = "\n".join(lines)

    # Find existing block, if any
    existing_match = re.search(
        rf"{re.escape(MARKER_START)}.*?{re.escape(MARKER_END)}",
        text,
        flags=re.DOTALL,
    )

    if existing_match:
        old_refs = set()
        for m in LINK_RE.finditer(existing_match.group(0)):
            try:
                tgt = (entry.parent / m.group(2)).resolve()
                old_refs.add(tgt)
            except OSError:
                pass
        if new_block:
            new_text = text[: existing_match.start()] + new_block + text[existing_match.end():]
        else:
            # Remove block entirely (plus surrounding whitespace)
            new_text = (
                text[: existing_match.start()].rstrip() + "\n" + text[existing_match.end():].lstrip()
            )
    else:
        old_refs = set()
        if new_block:
            if not text.endswith("\n"):
                text += "\n"
            new_text = text + "\n" + new_block + "\n"
        else:
            new_text = text

    new_refs = referrers
    added = sorted(p.name for p in new_refs - old_refs)
    removed = sorted(p.name for p in old_refs - new_refs)
    changed = new_text != text

    if changed and not dry_run:
        atomic_write_text(entry, new_text)

    return changed, added, removed


def emit_cycle_json(
    run_folder: Path,
    cycle_id: str,
    changes: list[dict],
    summary: dict,
) -> None:
    run_folder.mkdir(parents=True, exist_ok=True)
    payload = {
        "skill": "wiki-reciprocate-backlinks",
        "cycle_id": cycle_id,
        "step": "reciprocate-backlinks",
        "timestamp": iso_now(),
        "status": "completed",
        "summary": summary,
        "queued": changes,  # each change is a row describing what got updated
        "skipped": [],
        "deferred": [],
        "notes": "",
        "errors": [],
    }
    atomic_write_text(run_folder / "reciprocate-backlinks.json", json.dumps(payload, indent=2))

    md_lines = [
        f"# reciprocate-backlinks — {cycle_id}",
        "",
        f"**Status**: completed  ",
        f"**Timestamp**: {payload['timestamp']}  ",
        f"**Summary**: {summary['entries_processed']} entries processed, "
        f"{summary['entries_updated']} updated, {summary['backlinks_added']} backlinks added, "
        f"{summary['backlinks_removed']} removed.",
        "",
        "## Queued (entries with backlink changes)",
        "",
        "| Priority | Target | Reason | Timestamp |",
        "|---|---|---|---|",
    ]
    for ch in changes:
        md_lines.append(
            f"| — | {ch['url']} | {ch['reason']} | {ch['timestamp']} |"
        )
    md_lines += [
        "",
        "## Skipped",
        "",
        "_(none — script is deterministic, no skip logic)_",
        "",
        "## Deferred",
        "",
        "_(none)_",
        "",
    ]
    atomic_write_text(run_folder / "reciprocate-backlinks.md", "\n".join(md_lines))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--topic", required=True)
    ap.add_argument("--vault", default=_default_vault())
    ap.add_argument(
        "--since-hours",
        type=float,
        default=None,
        help="Only rewrite targets whose referrer set changed in the last N hours (cheap optimization).",
    )
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--cycle-id", default=None)
    ap.add_argument("--run-folder", default=None)
    args = ap.parse_args()

    vault = Path(args.vault).resolve()
    wiki_root = (vault / args.topic / "wiki").resolve()
    if not wiki_root.is_dir():
        print(f"error: wiki root not found: {wiki_root}", file=sys.stderr)
        return 2

    entries = find_wiki_entries(wiki_root)
    reverse_index = build_reverse_index(entries)

    now = time.time()
    cutoff = (now - args.since_hours * 3600) if args.since_hours else None

    changes: list[dict] = []
    entries_processed = 0
    entries_updated = 0
    total_added = 0
    total_removed = 0

    for entry in entries:
        entries_processed += 1
        referrers = reverse_index.get(entry.resolve(), set())

        # Optimization: skip if entry AND none of referrers changed recently
        if cutoff is not None:
            entry_mtime = entry.stat().st_mtime
            ref_mtime = max((r.stat().st_mtime for r in referrers), default=0)
            if entry_mtime < cutoff and ref_mtime < cutoff:
                continue

        changed, added, removed = rewrite_backlinks_section(
            entry, referrers, wiki_root, dry_run=args.dry_run
        )
        if changed:
            entries_updated += 1
            total_added += len(added)
            total_removed += len(removed)
            changes.append(
                {
                    "priority": None,
                    "url": str(entry.relative_to(wiki_root)).replace("\\", "/"),
                    "reason": f"+{len(added)} -{len(removed)} backlinks",
                    "timestamp": iso_now(),
                }
            )
            if args.dry_run:
                print(f"[dry-run] {entry.relative_to(wiki_root)}: +{len(added)} -{len(removed)}")

    summary = {
        "entries_processed": entries_processed,
        "entries_updated": entries_updated,
        "backlinks_added": total_added,
        "backlinks_removed": total_removed,
    }

    print(
        f"Processed {entries_processed} entries; "
        f"updated {entries_updated}; "
        f"+{total_added} backlinks, -{total_removed}."
    )

    if args.cycle_id and args.run_folder:
        emit_cycle_json(Path(args.run_folder), args.cycle_id, changes, summary)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
