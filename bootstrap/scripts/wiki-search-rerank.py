#!/usr/bin/env python3
"""
wiki-search-rerank.py — Post-filter qmd search results by icarus truth-status bucket.

Implements §3 of the icarus integration plan as a wrapper around the external
qmd search tool. Reads qmd's JSON output from stdin, reads each candidate's
`verified` field from its frontmatter (with sidecar fallback), applies the
bucket function, and re-sorts by (bucket, score) DESC.

Default behavior:
  - `verified: rolled_back` entries excluded entirely
  - bucket = 3 (verified) → 2 (unverified / unset) → 1 (contradicted)
  - within a bucket, sort by score DESC; tie-break by last_reviewed DESC

Flags:
  --include-rolled-back   Keep `rolled_back` entries (bucket 0, sorted last)
  --surface-contradicted  Promote `contradicted` entries to bucket 4 (above verified)

Usage:
  qmd search "memory architecture" --json | python wiki-search-rerank.py
  qmd search "..." --json | python wiki-search-rerank.py --surface-contradicted

Failure modes (per spec):
  - Candidate path missing on disk → drop with WARN to stderr
  - No verified field anywhere → bucket = 2 (unverified default)
  - Input JSON has no `results` array → pass-through unchanged
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

FM_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)
VERIFIED_RE = re.compile(r"^verified:\s*(\S+)\s*$", re.MULTILINE)
LAST_REVIEWED_RE = re.compile(r"^last_reviewed:\s*(\S+)\s*$", re.MULTILINE)


def read_verified_and_review(entry_path: Path) -> tuple[str | None, str | None]:
    """Return (verified_value, last_reviewed_iso). Frontmatter first, sidecar fallback."""
    verified = None
    last_reviewed = None
    if entry_path.exists():
        try:
            text = entry_path.read_text(encoding="utf-8", errors="replace")
            m = FM_RE.match(text)
            if m:
                fm_block = m.group(1)
                vm = VERIFIED_RE.search(fm_block)
                if vm:
                    verified = vm.group(1).strip("\"' ")
                lm = LAST_REVIEWED_RE.search(fm_block)
                if lm:
                    last_reviewed = lm.group(1).strip("\"' ")
        except OSError:
            pass

    # Sidecar fallback: <topic-root>/_signals/<entry-slug>.json
    # Sidecar path convention: starting from entry_path, walk up to find a folder
    # containing _signals/, look up <slug>.json there.
    if verified is None and entry_path.exists():
        topic_root = _find_topic_root(entry_path)
        if topic_root is not None:
            sidecar = topic_root / "_signals" / (entry_path.stem + ".json")
            if sidecar.exists():
                try:
                    sc = json.loads(sidecar.read_text(encoding="utf-8"))
                    verified = sc.get("verified")
                except (OSError, json.JSONDecodeError):
                    pass

    return verified, last_reviewed


def _find_topic_root(entry_path: Path) -> Path | None:
    """Walk up from entry_path; first ancestor whose `wiki/` subdir is the entry's tree is the topic root."""
    for ancestor in entry_path.parents:
        if (ancestor / "wiki").is_dir() and (ancestor / "_inbox").is_dir():
            return ancestor
    return None


def bucket(verified: str | None, surface_contradicted: bool, include_rolled_back: bool) -> int | None:
    """Returns bucket index (higher = ranked higher), or None to exclude.

    See wiki-search-bucket-rerank-spec.md §"Bucket function" for the canonical table.

    Buckets (default sort):
      4 - verified (canonical truth)
      3 - unverified / unset (default for fresh entries)
      2 - temporal (correct as-of-a-past-date but no longer current — cycle 2026-05-24-01 refinement)
      1 - contradicted (older side of a contradiction pair — has a newer entry that contradicts)
      None - rolled_back (excluded unless --include-rolled-back)

    --surface-contradicted promotes contradicted to bucket 5 (above verified) for audit mode.
    --include-rolled-back keeps rolled_back at bucket 0 (ranked last).
    """
    if verified == "verified":
        return 4
    if verified == "unverified" or verified is None:
        return 3
    if verified == "temporal":
        return 2
    if verified == "contradicted":
        return 5 if surface_contradicted else 1
    if verified == "rolled_back":
        return 0 if include_rolled_back else None
    # Unknown enum value: treat as unverified, don't fail-closed
    return 3


def rerank(payload: dict, surface_contradicted: bool, include_rolled_back: bool) -> dict:
    """In-place rerank. Returns the same payload object."""
    results = payload.get("results")
    if not isinstance(results, list):
        # Pass-through for non-standard qmd output (no results array)
        return payload

    enriched = []
    for r in results:
        path_str = r.get("path") or r.get("file") or r.get("filepath")
        if not path_str:
            # No path field; bucket = unverified default, no sidecar read
            r["bucket"] = 2
            enriched.append(r)
            continue
        entry = Path(path_str)
        if not entry.exists():
            print(f"WARN: candidate path does not exist on disk: {path_str}", file=sys.stderr)
            continue  # drop
        verified, last_reviewed = read_verified_and_review(entry)
        b = bucket(verified, surface_contradicted, include_rolled_back)
        if b is None:
            continue  # excluded (rolled_back without --include-rolled-back)
        r["bucket"] = b
        r["verified"] = verified  # transparency for downstream
        r["last_reviewed"] = last_reviewed
        enriched.append(r)

    enriched.sort(
        key=lambda x: (
            x.get("bucket", 2),
            x.get("score", 0.0),
            x.get("last_reviewed") or "",
        ),
        reverse=True,
    )

    payload["results"] = enriched
    payload["reranked_by"] = "wiki-search-rerank.py"
    payload["rerank_flags"] = {
        "surface_contradicted": surface_contradicted,
        "include_rolled_back": include_rolled_back,
    }
    return payload


def main() -> int:
    ap = argparse.ArgumentParser(description="Re-rank qmd search results by icarus truth-status bucket")
    ap.add_argument("--surface-contradicted", action="store_true",
                    help="Promote contradicted entries to bucket 4 (above verified). Use case: audit tensions.")
    ap.add_argument("--include-rolled-back", action="store_true",
                    help="Keep rolled_back entries in results (bucket 0, ranked last). Default: exclude.")
    args = ap.parse_args()

    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError as e:
        print(f"ERROR: failed to parse stdin as JSON: {e}", file=sys.stderr)
        return 2

    out = rerank(payload, args.surface_contradicted, args.include_rolled_back)
    json.dump(out, sys.stdout, indent=2)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
