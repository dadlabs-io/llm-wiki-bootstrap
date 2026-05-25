#!/usr/bin/env python3
"""
wiki-promote.py — promote entries from _inbox/proposed/ to wiki/<folder>/.

Reads each *.md in <vault>/_inbox/proposed/, loads its
.proposed_metadata.json sidecar (written by `wiki-update.py --staged`),
optionally asks the user, then moves the entry to its target folder,
strips status: proposed from the frontmatter, applies the suggested
backlinks (Edit-ing each listed file to add a See-also line), and
regenerates _INDEX.md + _MAP.md.

Modes:
  --review      Interactive: print each entry's summary, prompt
                accept/reject/skip. (Default if no mode flag.)
  --auto / --auto-promote / --all
                Promote everything without prompting.
  --reject-all  Move everything to _inbox/rejected/.

Optional filters:
  --slug <slug>      Only consider this one entry.
  --max <n>          Stop after N promotions.

Exit codes:
  0  success
  1  unrecoverable error
  3  user cancelled

Usage:
  python wiki-promote.py --vault llm-wiki/wiki --review
  python wiki-promote.py --vault llm-wiki/wiki --auto
  python wiki-promote.py --vault llm-wiki/wiki --slug foo-bar --auto
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


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


# ---------- Helpers ----------


def _info(msg):
    print(f"[wiki-promote] {msg}")


def _ok(msg):
    print(f"[wiki-promote] OK {msg}")


def _warn(msg):
    print(f"[wiki-promote] ! {msg}", file=sys.stderr)


def _err(msg):
    print(f"[wiki-promote] ERR {msg}", file=sys.stderr)


def _strip_status_proposed(text: str) -> str:
    """Remove the `status: proposed` line from frontmatter, leaving the rest
    of the frontmatter intact. Safe to run on entries that don't have the
    line — they're returned unchanged."""
    if not text.startswith("---"):
        return text
    end = text.find("---", 3)
    if end < 0:
        return text
    header = text[3:end]
    new_header_lines = [
        ln for ln in header.split("\n")
        if not re.match(r"^\s*status\s*:\s*proposed\s*$", ln)
    ]
    new_header = "\n".join(new_header_lines)
    return f"---{new_header}---{text[end + 3:]}"


def _add_backlink(target_file: Path, link_text: str, link_target: str) -> bool:
    """Add a one-line `See also` link to the target file. Idempotent — skips
    if the link target already appears anywhere in the file. Returns True if
    a backlink was added, False if skipped."""
    if not target_file.exists():
        return False
    text = target_file.read_text(encoding="utf-8")
    # Skip if link target already mentioned
    if link_target in text:
        return False
    # Append to a "See also" section, creating one if missing
    see_also_re = re.compile(r"\n#+\s*See also\s*\n", re.IGNORECASE)
    m = see_also_re.search(text)
    new_link = f"- [{link_text}](./{link_target})"
    if m:
        # Insert immediately after the heading
        insert_at = m.end()
        text = text[:insert_at] + new_link + "\n" + text[insert_at:]
    else:
        # Append a new See also section at the end
        suffix = "" if text.endswith("\n") else "\n"
        text = f"{text}{suffix}\n## See also\n\n{new_link}\n"
    target_file.write_text(text, encoding="utf-8")
    return True


def _regenerate_indexes(scripts_dir: Path, topic: str, vault: Path, dry_run: bool):
    """Run wiki-index-per-folder.py + wiki-map-compile.py to refresh the
    index and map after a promotion. Best-effort — warns on failure."""
    for script_name in ("wiki-index-per-folder.py", "wiki-map-compile.py"):
        script = scripts_dir / script_name
        if not script.exists():
            _warn(f"{script_name} not found at {script}; skipping regen")
            continue
        cmd = [sys.executable, str(script), "--topic", topic, "--vault", str(vault)]
        if dry_run:
            print(f"  WOULD run: {' '.join(cmd)}")
            continue
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            _warn(f"{script_name} exited {result.returncode}: {result.stderr.strip()[:200]}")


# ---------- Promote ----------


def list_proposed(vault: Path):
    """Return all proposed entries as (md_path, sidecar_path_or_None) tuples."""
    proposed_dir = vault / "_inbox" / "proposed"
    if not proposed_dir.exists():
        return []
    items = []
    for md in sorted(proposed_dir.glob("*.md")):
        sidecar = md.with_suffix(".proposed_metadata.json")
        items.append((md, sidecar if sidecar.exists() else None))
    return items


def _load_sidecar(sidecar: Path) -> dict:
    if not sidecar or not sidecar.exists():
        return {}
    try:
        return json.loads(sidecar.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as e:
        _warn(f"sidecar unreadable ({e}); promoting without metadata")
        return {}


def _summarize_entry(md_path: Path, meta: dict) -> str:
    """One-line summary for the --review prompt."""
    title = meta.get("title") or md_path.stem
    tier = meta.get("tier") or "?"
    folder = meta.get("target_folder") or "<root>"
    n_backlinks = len(meta.get("suggested_backlinks", []))
    return f"{md_path.name}  →  {folder}/  [T{tier}]  ({n_backlinks} backlinks)  {title}"


def promote_entry(md_path: Path, meta: dict, vault: Path, dry_run: bool = False) -> dict:
    """Promote one entry. Returns a result dict with counts."""
    folder = meta.get("target_folder") or ""
    target_dir = vault / folder if folder else vault
    target_path = target_dir / md_path.name

    result = {
        "slug": md_path.stem,
        "from": str(md_path),
        "to": str(target_path),
        "moved": False,
        "backlinks_added": 0,
        "backlinks_skipped": 0,
    }

    if not dry_run:
        target_dir.mkdir(parents=True, exist_ok=True)
        # Strip status: proposed from frontmatter
        text = md_path.read_text(encoding="utf-8")
        text = _strip_status_proposed(text)
        target_path.write_text(text, encoding="utf-8")
        md_path.unlink()
        # Clean up sidecar
        sidecar = md_path.with_suffix(".proposed_metadata.json")
        if sidecar.exists():
            sidecar.unlink()
        result["moved"] = True

        # Apply backlinks
        for bl in meta.get("suggested_backlinks", []):
            target_file = vault / bl["file"]
            if _add_backlink(target_file, bl["link_text"], bl["link_target"]):
                result["backlinks_added"] += 1
            else:
                result["backlinks_skipped"] += 1
    else:
        result["moved"] = True  # would have moved
        result["backlinks_added"] = len(meta.get("suggested_backlinks", []))
    return result


def reject_entry(md_path: Path, vault: Path, dry_run: bool = False) -> dict:
    """Move an entry to _inbox/rejected/. Sidecar moves with it."""
    rejected_dir = vault / "_inbox" / "rejected"
    target_path = rejected_dir / md_path.name
    sidecar = md_path.with_suffix(".proposed_metadata.json")

    if not dry_run:
        rejected_dir.mkdir(parents=True, exist_ok=True)
        md_path.rename(target_path)
        if sidecar.exists():
            sidecar.rename(rejected_dir / sidecar.name)

    return {"slug": md_path.stem, "moved_to": str(target_path)}


# ---------- Main ----------


def main():
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--topic", default=None,
                        help="Topic name (only needed if vault default doesn't resolve correctly)")
    parser.add_argument("--vault", default=None,
                        help="Wiki vault root (default: resolved from .claude/wiki-config.json or llm-wiki/wiki)")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--review", action="store_true",
                      help="Interactive: prompt accept/reject/skip per entry (default)")
    mode.add_argument("--auto", "--auto-promote", "--all", dest="auto", action="store_true",
                      help="Promote everything without prompting")
    mode.add_argument("--reject-all", action="store_true",
                      help="Move everything in _inbox/proposed/ to _inbox/rejected/")
    parser.add_argument("--slug", default=None, help="Only operate on this slug")
    parser.add_argument("--max", type=int, default=None, help="Stop after N promotions")
    parser.add_argument("--dry-run", action="store_true", help="Print actions without writing")
    parser.add_argument(
        "--verify", action="store_true",
        help="Also run /wiki-verify on each successfully promoted entry. "
             "Use for tier-1 entries with strong empirical backing where you're "
             "willing to certify in the same human-review pass. Most entries "
             "should NOT be auto-verified at promote time — verification is a "
             "deliberate later step. icarus integration plan §9.",
    )
    parser.add_argument(
        "--verify-by", default="human", choices=["human", "agent", "tool"],
        help="Who is doing the verification when --verify is set. Default: human.",
    )
    parser.add_argument(
        "--verify-evidence", default="",
        help="Optional one-line evidence note recorded with the verification.",
    )
    args = parser.parse_args()

    vault = Path(args.vault) if args.vault else Path(_default_vault())
    if not vault.exists():
        _err(f"vault not found: {vault}")
        return 1

    # Default mode = review (if nothing else specified)
    if not (args.auto or args.review or args.reject_all):
        args.review = True

    items = list_proposed(vault)
    if args.slug:
        items = [(m, s) for m, s in items if m.stem == args.slug]
    if not items:
        _info("nothing in _inbox/proposed/ to promote")
        return 0

    _info(f"found {len(items)} proposed entries in {vault}/_inbox/proposed/")
    scripts_dir = Path(__file__).resolve().parent

    # Topic name fallback for index/map regen
    topic = args.topic or vault.parent.name  # llm-wiki/wiki -> "llm-wiki" if not set

    promoted = []
    rejected = []
    skipped = []
    promote_count = 0

    for md_path, sidecar in items:
        meta = _load_sidecar(sidecar)
        summary = _summarize_entry(md_path, meta)

        if args.reject_all:
            r = reject_entry(md_path, vault, dry_run=args.dry_run)
            rejected.append(r)
            _info(f"REJECTED  {summary}")
            continue

        decision = "p"  # default: promote
        if args.review and not args.auto:
            print()
            print("─" * 70)
            print(summary)
            if meta.get("source_url"):
                print(f"  Source: {meta['source_url']}")
            if meta.get("suggested_backlinks"):
                print(f"  Backlinks to add:")
                for bl in meta["suggested_backlinks"][:5]:
                    print(f"    - {bl['file']}")
                if len(meta["suggested_backlinks"]) > 5:
                    print(f"    ... and {len(meta['suggested_backlinks']) - 5} more")
            choice = input("  [P]romote / [R]eject / [S]kip / [Q]uit: ").strip().lower()
            if choice.startswith("q"):
                _info("user quit")
                break
            if choice.startswith("r"):
                decision = "r"
            elif choice.startswith("s"):
                decision = "s"
            else:
                decision = "p"

        if decision == "p":
            r = promote_entry(md_path, meta, vault, dry_run=args.dry_run)
            promoted.append(r)
            _info(f"PROMOTED  {summary}  (+{r['backlinks_added']} backlinks)")
            # §9: optional verify-after-promote for tier-1 entries with strong empirical backing.
            # Most entries should stay unverified post-promote; this flag is opt-in per cycle.
            if args.verify and r.get("moved") and not args.dry_run:
                try:
                    import subprocess
                    verify_cmd = [
                        sys.executable,
                        str(scripts_dir / "wiki-verify.py"),
                        r["slug"],
                        "--topic", topic,
                        "--vault", str(vault.parent),  # wiki-verify wants the vault-of-topic-roots
                        "--by", args.verify_by,
                    ]
                    if args.verify_evidence:
                        verify_cmd += ["--evidence", args.verify_evidence]
                    res = subprocess.run(verify_cmd, capture_output=True, text=True, check=False)
                    if res.returncode == 0:
                        r["verified"] = True
                        _info(f"VERIFIED  {r['slug']}  (by={args.verify_by})")
                    else:
                        r["verified"] = False
                        r["verify_error"] = res.stderr.strip().splitlines()[-1] if res.stderr else "(no stderr)"
                        _warn(f"verify failed for {r['slug']}: {r['verify_error']}")
                except Exception as e:
                    r["verified"] = False
                    r["verify_error"] = str(e)
                    _warn(f"verify subprocess crashed for {r['slug']}: {e}")
            promote_count += 1
            if args.max and promote_count >= args.max:
                _info(f"--max {args.max} reached, stopping")
                break
        elif decision == "r":
            r = reject_entry(md_path, vault, dry_run=args.dry_run)
            rejected.append(r)
            _info(f"REJECTED  {summary}")
        else:
            skipped.append(md_path.stem)
            _info(f"SKIPPED   {summary}")

    # Regen indexes if anything was promoted
    if promoted and not args.dry_run:
        _info("regenerating _INDEX.md + _MAP.md...")
        _regenerate_indexes(scripts_dir, topic, vault, args.dry_run)

    # JSON summary for orchestrator
    print(json.dumps({
        "status": "ok",
        "vault": str(vault),
        "topic": topic,
        "counts": {
            "promoted": len(promoted),
            "rejected": len(rejected),
            "skipped": len(skipped),
        },
        "promoted": promoted,
        "rejected": rejected,
        "skipped": skipped,
        "completed_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
