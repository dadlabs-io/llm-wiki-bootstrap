#!/usr/bin/env python3
"""
Process a topic wiki's ingest queue — batch consume _inbox/pending/ → wiki/.

Walks <topic>/_inbox/pending/, parses each .queue file, runs wiki-update.py for
the source, and moves successful items to _inbox/done/. Failed items move to
_inbox/failed/ with an .error sidecar.

Queue file format (parsed line-by-line):
    source: <url or path>
    folder: <wiki subfolder>
    title: <optional>
    tags: <comma-separated, optional>

Usage:
    python3 wiki-list-process.py --topic <topic>
    python3 wiki-list-process.py --topic <topic> --dry-run
    python3 wiki-list-process.py --topic <topic> --limit 5
"""

import argparse
import os
import shutil
import subprocess
import sys
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
# Force UTF-8 stdout on Windows so Unicode in wiki content doesn't crash printing
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

DEFAULT_VAULT = _default_vault()


def parse_queue_file(path):
    """Parse a .queue file into a dict of fields."""
    fields = {}
    try:
        text = path.read_text(encoding="utf-8")
    except (UnicodeDecodeError, OSError) as e:
        return None, f"could not read: {e}"

    for line in text.splitlines():
        if not line.strip() or line.strip().startswith("#"):
            continue
        if ":" not in line:
            continue
        key, _, value = line.partition(":")
        fields[key.strip().lower()] = value.strip()

    if not fields.get("source"):
        return None, "missing 'source' field"
    return fields, None


def move_queue_file(queue_path, target_dir, render_script, vault_root, topic):
    """Move a queue file to target_dir AND re-render the pending-list view.

    These two operations are bundled because the rendered view (`pending-list.md`)
    must always reflect the current state of `_inbox/pending/`, `_inbox/done/`,
    and `_inbox/failed/`. If you move a queue file without re-rendering, the view
    drifts. By making "move + render" a single function, that drift is impossible
    — every code path that moves a queue file uses this helper.
    """
    target_dir.mkdir(parents=True, exist_ok=True)
    shutil.move(str(queue_path), str(target_dir / queue_path.name))
    if render_script and render_script.exists():
        subprocess.run(
            [sys.executable, str(render_script), "--topic", topic, "--vault", str(vault_root)],
            capture_output=True, text=True,
        )


def process_one(vault_root, topic, queue_path, wiki_update_script, dry_run):
    """Process a single queue item. Returns (success: bool, message: str)."""
    fields, err = parse_queue_file(queue_path)
    if err:
        return False, f"parse error: {err}"

    source = fields["source"]
    folder = fields.get("folder", "")
    title = fields.get("title", "")
    tags = fields.get("tags", "")
    added_by = fields.get("added_by", "queue")  # producer's identity becomes ingested_by

    cmd = [
        sys.executable,
        str(wiki_update_script),
        "--topic", topic,
        "--source", source,
        "--vault", str(vault_root),
        "--ingested-by", added_by,
    ]
    if folder:
        cmd += ["--folder", folder]
    if title:
        cmd += ["--title", title]
    if tags:
        cmd += ["--tags", tags]
    # Suppress per-item index regen — we do one at the end
    cmd += ["--no-index"]

    if dry_run:
        return True, f"DRY-RUN would run: {' '.join(cmd)}"

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        msg = (result.stderr.strip() or result.stdout.strip() or "non-zero exit").splitlines()
        return False, "\n  ".join(msg[-5:])
    return True, result.stdout.strip().splitlines()[-1] if result.stdout else "ok"


def process_queue(vault_root, topic, dry_run, limit):
    topic_root = Path(vault_root) / topic
    if not topic_root.exists():
        print(f"Error: topic '{topic}' not found at {topic_root}", file=sys.stderr)
        return 1

    pending_dir = topic_root / "_inbox" / "pending"
    done_dir = topic_root / "_inbox" / "done"
    failed_dir = topic_root / "_inbox" / "failed"

    if not pending_dir.exists():
        print(f"No pending dir at {pending_dir} — nothing to process")
        return 0

    # Accept both .md (current) and .queue (legacy) extensions
    queue_files = sorted(p for p in pending_dir.iterdir() if p.suffix in (".md", ".queue"))
    if not queue_files:
        print(f"Queue is empty: {pending_dir}")
        return 0

    if limit and len(queue_files) > limit:
        queue_files = queue_files[:limit]

    # Locate wiki-update.py relative to this script
    wiki_update_script = Path(__file__).parent / "wiki-update.py"
    if not wiki_update_script.exists():
        print(f"Error: wiki-update.py not found at {wiki_update_script}", file=sys.stderr)
        return 1

    # Locate wiki-list-render.py — used to refresh the rendered list view
    # after EVERY processed item, so the view never goes stale even mid-batch.
    render_script = Path(__file__).parent / "wiki-list-render.py"

    print(f"Processing {len(queue_files)} queue item(s) from {pending_dir}")
    if dry_run:
        print("(DRY RUN — no files will be modified)")
    print()

    succeeded = 0
    failed = 0

    if not dry_run:
        done_dir.mkdir(parents=True, exist_ok=True)

    for i, qpath in enumerate(queue_files, 1):
        print(f"[{i}/{len(queue_files)}] {qpath.name}")
        ok, msg = process_one(vault_root, topic, qpath, wiki_update_script, dry_run)

        if ok:
            print(f"  ✓ {msg}")
            succeeded += 1
            if not dry_run:
                # Move + re-render bundled together — see move_queue_file() docstring
                move_queue_file(qpath, done_dir, render_script, vault_root, topic)
        else:
            print(f"  ✗ {msg}")
            failed += 1
            if not dry_run:
                # Move + re-render bundled together
                move_queue_file(qpath, failed_dir, render_script, vault_root, topic)
                # Drop an .error sidecar in the new location
                err_path = failed_dir / (qpath.name + ".error")
                atomic_write_text(err_path, f"# {datetime.now().astimezone().isoformat()}\n{msg}\n")
        print()

    # Regenerate index once at the end
    if not dry_run and succeeded > 0:
        index_script = Path(__file__).parent / "wiki-index.py"
        if index_script.exists():
            print("Regenerating _INDEX.md...")
            r = subprocess.run(
                [sys.executable, str(index_script), "--topic", topic, "--vault", str(vault_root)],
                capture_output=True, text=True,
            )
            if r.returncode == 0:
                for line in r.stdout.strip().splitlines():
                    print(f"  {line}")
            else:
                print(f"  Warning: index regen failed: {r.stderr.strip()}")

    # Note: pending-list.md is re-rendered after every item inside the loop above,
    # so it's already up to date. No need for a final batch-end render.

    print()
    print(f"Done: {succeeded} succeeded, {failed} failed")
    return 0 if failed == 0 else 2


def main():
    parser = argparse.ArgumentParser(description="Process a wiki ingest queue")
    parser.add_argument("--topic", required=True, help="Topic name")
    parser.add_argument("--vault", default=DEFAULT_VAULT, help=f"Vault root (default: {DEFAULT_VAULT})")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be processed without changing anything")
    parser.add_argument("--limit", type=int, default=0, help="Process at most N items (0 = all)")
    args = parser.parse_args()
    return process_queue(args.vault, args.topic, args.dry_run, args.limit)


if __name__ == "__main__":
    sys.exit(main())
