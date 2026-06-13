#!/usr/bin/env python3
"""
Lint a topic wiki — Karpathy-style health check.

Walks the wiki and reports:
  1. Broken internal links (markdown links to .md files that don't exist)
  2. Orphan pages (wiki entries with no inbound links from other wiki entries)
  3. Stale "pending" mentions — references to items as pending/not-built
     when the underlying state has changed (queue items now in done/, etc.)
  4. Missing frontmatter fields (no source_url, no ingested_by, etc.)
  5. Files outside the canonical structure (e.g. .md at unexpected paths)

Output: a markdown report printed to stdout AND saved at <topic>/_inbox/lint-report.md
so you can open it in Obsidian.

Usage:
    python3 wiki-lint.py --topic agentic-design
    python3 wiki-lint.py --topic agentic-design --vault /custom/path
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


# Path-resolution helpers live in the shared _wiki_config module (single
# source of truth for the multi-wiki config schema). Re-exported under the
# historical private names so the rest of this script is unchanged.
sys.path.insert(0, str(Path(__file__).resolve().parent))
from _wiki_config import default_vault as _default_vault, default_topic as _default_topic  # noqa: E402
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

DEFAULT_VAULT = _default_vault()

# Markdown link pattern: [text](path) — captures the path
LINK_RE = re.compile(r"\[([^\]]*)\]\(([^)]+)\)")

# Frontmatter capture
FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)

# Phrases that suggest "pending / not yet done" — used for staleness detection
PENDING_PHRASES = [
    r"pending ingestion",
    r"awaiting playwright",
    r"awaiting fetch",
    r"not yet built",
    r"to-?do[- :]",
    r"todo[- ]after[- ]ingest",
]
PENDING_RE = re.compile("|".join(PENDING_PHRASES), re.IGNORECASE)


def parse_frontmatter(content):
    """Return (frontmatter_dict, body) from a markdown file."""
    m = FRONTMATTER_RE.match(content)
    if not m:
        return {}, content
    raw = m.group(1)
    body = content[m.end():]
    fm = {}
    for line in raw.splitlines():
        if not line.strip() or line.strip().startswith("#") or ":" not in line:
            continue
        key, _, value = line.partition(":")
        fm[key.strip().lower()] = value.strip()
    return fm, body


def collect_md_files(wiki_root):
    """Yield Path of every .md file under wiki_root."""
    for path in sorted(wiki_root.rglob("*.md")):
        if path.name in {"_INDEX.md", "_MAP.md"}:
            continue  # skip auto-generated index/map files
        yield path


def extract_links(content):
    """Yield (link_text, target) for every markdown link in content.
    Skips external (http/https) and anchor-only (#) links.
    """
    for m in LINK_RE.finditer(content):
        text = m.group(1)
        target = m.group(2).strip()
        # Skip external
        if target.startswith(("http://", "https://", "mailto:", "ftp://")):
            continue
        # Skip pure anchors
        if target.startswith("#"):
            continue
        # Strip anchor fragment from path
        if "#" in target:
            target = target.split("#", 1)[0]
        if not target:
            continue
        yield text, target


def resolve_link(file_path, target):
    """Resolve a markdown link target to an absolute path. Returns Path or None."""
    try:
        return (file_path.parent / target).resolve()
    except (ValueError, OSError):
        return None


def lint(vault_root, topic, strict=False):
    topic_root = Path(vault_root) / topic
    wiki_root = topic_root / "wiki"
    if not wiki_root.exists():
        print(f"ERROR: wiki/ folder not found at {wiki_root}", file=sys.stderr)
        return 1

    files = list(collect_md_files(wiki_root))

    # Pass 1: build a map of all wiki files (resolved absolute paths)
    file_map = {p.resolve(): p for p in files}
    file_set = set(file_map.keys())

    # Pass 2: for each file, parse links and check
    broken_links = []  # (file, link_text, target, reason)
    incoming_count = {p.resolve(): 0 for p in files}
    outgoing_links = {p.resolve(): [] for p in files}
    stale_pending = []  # (file, line_number, line_text)
    missing_frontmatter = []  # (file, missing_fields)
    missing_tier = []  # (file,) — entries without a tier: field
    invalid_tier = []  # (file, value) — entries with a tier value outside the allowed set
    missing_confidence = []  # (file,) — entries without a confidence: field
    invalid_confidence = []  # (file, value) — entries with invalid confidence value
    unquoted_yaml = []  # (file, field, value) — frontmatter values with YAML-breaking chars that aren't quoted
    missing_raw_path = []  # (file,) — entries with no raw_path field
    phantom_raw_path = []  # (file, raw_path_value) — raw_path doesn't resolve to a real file
    self_authored_count = 0  # informational — entries with explicit "(none ...)" marker

    REQUIRED_FM_FIELDS = ["title", "date"]  # source_url + ingested_by may be intentionally absent
    VALID_TIERS = {"1", "2", "3", "4", "self"}
    VALID_CONFIDENCE = {"high", "medium", "low"}

    # Icarus schema (frontmatter §1 of icarus-integration-plan).
    # Optional fields, but when present must obey the enum + write-time invariants.
    VALID_VERIFIED = {"unverified", "verified", "temporal", "contradicted", "rolled_back"}
    VALID_TYPE = {"decision", "observation", "attempt", "rollback", "review"}

    # Icarus validation tracking
    invalid_verified = []         # (file, value)
    invalid_type = []             # (file, value)
    missing_contradicted_by = []  # (file,) — verified='contradicted' but no contradicted_by
    missing_revises_on_rollback = []  # (file,) — type='rollback' but no revises
    missing_review_of_on_review = []  # (file,) — type='review' but no review_of
    broken_icarus_ref = []        # (file, field, ref_value) — revises/review_of/contradicted_by/synthesis_of[i] points at non-existent file

    for f in files:
        try:
            content = f.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError) as e:
            broken_links.append((f, "<file read>", str(e), "unreadable"))
            continue

        fm, body = parse_frontmatter(content)

        # Check required frontmatter
        missing = [k for k in REQUIRED_FM_FIELDS if k not in fm]
        if missing:
            missing_frontmatter.append((f, missing))

        # Check tier (separate from required FM because we want to track it explicitly)
        tier_value = fm.get("tier", "").strip()
        if not tier_value:
            missing_tier.append(f)
        elif tier_value not in VALID_TIERS:
            invalid_tier.append((f, tier_value))

        # Check confidence
        conf_value = fm.get("confidence", "").strip()
        if not conf_value:
            missing_confidence.append(f)
        elif conf_value not in VALID_CONFIDENCE:
            invalid_confidence.append((f, conf_value))

        # Check raw_path — load-bearing for the no-deletion rule
        # (see wiki/best-practices/memory-architecture-best-practices.md Principle 2 carve-out).
        # Resolution attempts: as-is from CWD, then topic_root, then wiki_root.
        # "(none — self-authored)" or other parenthetical markers are explicit no-raw flags and skip the check.
        raw_path_value = fm.get("raw_path", "").strip()
        if not raw_path_value:
            missing_raw_path.append(f)
        elif raw_path_value.startswith("("):
            # Explicit no-raw marker (e.g., "(none — self-authored)")
            self_authored_count += 1
        else:
            candidates = [
                Path(raw_path_value),
                topic_root / raw_path_value,
                wiki_root / raw_path_value,
            ]
            if not any(c.exists() for c in candidates):
                phantom_raw_path.append((f, raw_path_value))

        # Check for unquoted YAML special characters in frontmatter values
        # Colons, apostrophes, and other chars break YAML parsing if not quoted
        YAML_DANGER_CHARS = [":", "'", '"', "{", "}", "[", "]", "&", "*", "?", "|", ">", "!", "%", "@", "`"]
        for fm_key in ("title",):  # title is the most common offender
            raw_value = fm.get(fm_key, "")
            if raw_value and not (raw_value.startswith('"') and raw_value.endswith('"')):
                if any(ch in raw_value for ch in YAML_DANGER_CHARS):
                    unquoted_yaml.append((f, fm_key, raw_value))

        # Check icarus schema fields (optional, but invariants apply when present)
        verified_value = fm.get("verified", "").strip()
        if verified_value and verified_value not in VALID_VERIFIED:
            invalid_verified.append((f, verified_value))

        type_value = fm.get("type", "").strip()
        if type_value and type_value not in VALID_TYPE:
            invalid_type.append((f, type_value))

        contradicted_by = fm.get("contradicted_by", "").strip()
        revises = fm.get("revises", "").strip()
        review_of = fm.get("review_of", "").strip()

        # Invariant: verified='contradicted' requires contradicted_by
        if verified_value == "contradicted" and not contradicted_by:
            missing_contradicted_by.append(f)
        # Invariant: type='rollback' requires revises
        if type_value == "rollback" and not revises:
            missing_revises_on_rollback.append(f)
        # Invariant: type='review' requires review_of
        if type_value == "review" and not review_of:
            missing_review_of_on_review.append(f)

        # Reference integrity: revises / review_of / contradicted_by must resolve to existing files
        for ref_field, ref_value in (("revises", revises), ("review_of", review_of), ("contradicted_by", contradicted_by)):
            if not ref_value:
                continue
            # Resolve relative to the entry's folder (same as markdown link semantics)
            ref_resolved = resolve_link(f, ref_value)
            if ref_resolved is None or not ref_resolved.exists():
                broken_icarus_ref.append((f, ref_field, ref_value))

        # synthesis_of: list of slugs (project entry distilling research entries).
        # YAML inline-list parsed as "[a.md, b.md, c.md]" or block-list across lines.
        # Our parse_frontmatter() returns the raw value as a string; detect both forms.
        synthesis_of_raw = fm.get("synthesis_of", "").strip()
        synthesis_refs = []
        if synthesis_of_raw:
            # Inline form: [item1, item2, ...]
            if synthesis_of_raw.startswith("[") and synthesis_of_raw.endswith("]"):
                inner = synthesis_of_raw[1:-1]
                synthesis_refs = [s.strip().strip("\"' ") for s in inner.split(",") if s.strip()]
            else:
                # Single value treated as one ref
                synthesis_refs = [synthesis_of_raw.strip("\"' ")]
        for ref_value in synthesis_refs:
            if not ref_value:
                continue
            ref_resolved = resolve_link(f, ref_value)
            if ref_resolved is None or not ref_resolved.exists():
                broken_icarus_ref.append((f, "synthesis_of", ref_value))

        # Check links
        for link_text, target in extract_links(content):
            # Only check links that look like .md or directory paths
            if not (target.endswith(".md") or target.endswith("/") or "/" in target):
                continue
            resolved = resolve_link(f, target)
            if resolved is None:
                broken_links.append((f, link_text, target, "could not resolve path"))
                continue
            if resolved not in file_set:
                # Check if it's a non-md file that exists (e.g., README.md outside wiki)
                if not resolved.exists():
                    broken_links.append((f, link_text, target, "file not found"))
                continue
            # Track for inbound counting
            incoming_count[resolved] += 1
            outgoing_links[f.resolve()].append(resolved)

        # Check stale pending mentions
        for line_no, line in enumerate(content.splitlines(), 1):
            if PENDING_RE.search(line):
                stale_pending.append((f, line_no, line.strip()[:120]))

    # Pass 3: orphans — files with zero inbound links
    orphans = [f for f in files if incoming_count[f.resolve()] == 0]

    # Render report
    out = []
    out.append(f"# Wiki Lint Report — {topic}")
    out.append("")
    out.append(f"**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    out.append(f"**Files scanned**: {len(files)}")
    out.append(f"**Broken links**: {len(broken_links)}")
    out.append(f"**Orphan pages**: {len(orphans)}")
    out.append(f"**Stale 'pending' mentions**: {len(stale_pending)}")
    out.append(f"**Missing frontmatter fields**: {len(missing_frontmatter)}")
    out.append(f"**Missing tier**: {len(missing_tier)}")
    out.append(f"**Invalid tier values**: {len(invalid_tier)}")
    out.append(f"**Missing confidence**: {len(missing_confidence)}")
    out.append(f"**Invalid confidence**: {len(invalid_confidence)}")
    out.append(f"**Unquoted YAML values**: {len(unquoted_yaml)}")
    out.append(f"**Missing `raw_path`**: {len(missing_raw_path)}")
    out.append(f"**Phantom `raw_path` (file does not exist)**: {len(phantom_raw_path)}")
    out.append(f"**Explicit self-authored (no raw)**: {self_authored_count}")
    icarus_total = (len(invalid_verified) + len(invalid_type) + len(missing_contradicted_by)
                    + len(missing_revises_on_rollback) + len(missing_review_of_on_review)
                    + len(broken_icarus_ref))
    out.append(f"**Icarus schema issues**: {icarus_total}"
               + (f" (invalid_verified={len(invalid_verified)}, invalid_type={len(invalid_type)}, "
                  f"missing_contradicted_by={len(missing_contradicted_by)}, "
                  f"missing_revises_on_rollback={len(missing_revises_on_rollback)}, "
                  f"missing_review_of_on_review={len(missing_review_of_on_review)}, "
                  f"broken_icarus_ref={len(broken_icarus_ref)})" if icarus_total else ""))
    out.append("")
    out.append("---")
    out.append("")

    # Section: broken links
    out.append("## 🔗 Broken Links")
    out.append("")
    if not broken_links:
        out.append("_None — all internal links resolve._")
    else:
        for f, link_text, target, reason in broken_links:
            rel = f.relative_to(wiki_root)
            out.append(f"- **{rel.as_posix()}** → `{target}` ({reason})")
            if link_text:
                out.append(f"  link text: \"{link_text[:80]}\"")
    out.append("")

    # Section: orphans
    out.append("## 🏝️ Orphan Pages (no inbound links)")
    out.append("")
    if not orphans:
        out.append("_None — every page has at least one inbound link._")
    else:
        out.append("These pages are not linked from any other wiki entry. Either:")
        out.append("- Add a backlink from a related entry, OR")
        out.append("- Verify it's intentionally standalone (e.g., the root hub)")
        out.append("")
        for f in orphans:
            rel = f.relative_to(wiki_root)
            out.append(f"- `{rel.as_posix()}`")
    out.append("")

    # Section: stale pending
    out.append("## ⏳ Stale 'Pending' Mentions")
    out.append("")
    out.append("These lines mention pending/awaiting/not-built state. Verify they're still accurate — if the underlying state changed (item ingested, feature built), update the text.")
    out.append("")
    if not stale_pending:
        out.append("_None found._")
    else:
        for f, line_no, line in stale_pending:
            rel = f.relative_to(wiki_root)
            out.append(f"- `{rel.as_posix()}:{line_no}` — {line}")
    out.append("")

    # Section: missing frontmatter
    out.append("## 📋 Missing Frontmatter Fields")
    out.append("")
    if not missing_frontmatter:
        out.append("_All files have required frontmatter (title, date)._")
    else:
        for f, missing in missing_frontmatter:
            rel = f.relative_to(wiki_root)
            out.append(f"- `{rel.as_posix()}` — missing: {', '.join(missing)}")
    out.append("")

    # Section: source quality tiers
    out.append("## 🎯 Source Quality Tiers")
    out.append("")
    if not missing_tier and not invalid_tier:
        out.append("_All entries have a valid tier (1=primary, 2=vendor, 3=expert, 4=community, self=our own)._")
    else:
        if missing_tier:
            out.append(f"**Missing tier ({len(missing_tier)} files):** add `tier: 1|2|3|4|self` to frontmatter.")
            for f in missing_tier:
                rel = f.relative_to(wiki_root)
                out.append(f"- `{rel.as_posix()}`")
            out.append("")
        if invalid_tier:
            out.append(f"**Invalid tier values ({len(invalid_tier)} files):** must be one of `1, 2, 3, 4, self`.")
            for f, value in invalid_tier:
                rel = f.relative_to(wiki_root)
                out.append(f"- `{rel.as_posix()}` — got `{value}`")
            out.append("")
    out.append("")

    # Section: confidence
    out.append("## 🔍 Entry Confidence")
    out.append("")
    if not missing_confidence and not invalid_confidence:
        out.append("_All entries have valid confidence (high/medium/low)._")
    else:
        if missing_confidence:
            out.append(f"**Missing confidence ({len(missing_confidence)} files):** add `confidence: high|medium|low` to frontmatter.")
            for f in missing_confidence:
                rel = f.relative_to(wiki_root)
                out.append(f"- `{rel.as_posix()}`")
            out.append("")
        if invalid_confidence:
            out.append(f"**Invalid confidence ({len(invalid_confidence)} files):** must be `high`, `medium`, or `low`.")
            for f, value in invalid_confidence:
                rel = f.relative_to(wiki_root)
                out.append(f"- `{rel.as_posix()}` — got `{value}`")
            out.append("")
    out.append("")

    # Section: unquoted YAML values
    out.append("## ⚠️ Unquoted YAML Values")
    out.append("")
    if not unquoted_yaml:
        out.append("_All frontmatter values with special characters are properly quoted._")
    else:
        out.append(f"**{len(unquoted_yaml)} file(s)** have frontmatter values containing YAML special characters (`:`, `'`, etc.) that aren't quoted. Wrap them in double quotes to prevent Obsidian/YAML parsing issues.")
        out.append("")
        for f, field, value in unquoted_yaml:
            rel = f.relative_to(wiki_root)
            out.append(f"- `{rel.as_posix()}` — `{field}:` contains special chars: `{value[:60]}`")
    out.append("")

    # Section: raw_path integrity
    out.append("## 📁 `raw_path` Integrity (load-bearing for no-deletion rule)")
    out.append("")
    out.append("Every wiki entry is a paged-in view of an immutable raw source. `raw_path` must point to a real file in `<topic>/raw/` (or be the explicit marker `(none — self-authored)`). If `raw_path` is missing or phantom, the entry's information cannot be re-derived if the wiki entry is ever deleted, compacted, or migrated. See `wiki/best-practices/memory-architecture-best-practices.md` Principle 2 carve-out.")
    out.append("")
    out.append(f"_Stats_: {self_authored_count} self-authored (explicit no-raw), {len(missing_raw_path)} missing field, {len(phantom_raw_path)} phantom (file not found).")
    out.append("")
    if not missing_raw_path and not phantom_raw_path:
        out.append("_All non-self-authored entries have a valid `raw_path` resolving to an existing file._")
    else:
        if missing_raw_path:
            out.append(f"### Missing `raw_path` field ({len(missing_raw_path)} entries)")
            out.append("")
            out.append("Entries with no `raw_path` frontmatter at all. Either add a path to the preserved raw source, or add the explicit marker `raw_path: (none — self-authored)`.")
            out.append("")
            for f in missing_raw_path:
                rel = f.relative_to(wiki_root)
                out.append(f"- `{rel.as_posix()}`")
            out.append("")
        if phantom_raw_path:
            out.append(f"### Phantom `raw_path` ({len(phantom_raw_path)} entries)")
            out.append("")
            out.append("Entries with `raw_path` pointing to a non-existent file. Either re-fetch the source into `raw/` or correct the path. **Do not delete these entries** — they are the only surviving copy of their information.")
            out.append("")
            for f, value in phantom_raw_path:
                rel = f.relative_to(wiki_root)
                out.append(f"- `{rel.as_posix()}` → `{value}`")
            out.append("")
    out.append("")

    # Section: icarus schema (truth-status + lineage)
    out.append("## 🧬 Icarus Schema (truth-status + lineage)")
    out.append("")
    out.append("Fields adopted from icarus-memory-infra (MIT schema lift). See `wiki/best-practices/framework/icarus-integration-plan.md` §1 and §7. These checks WARN by default; pass `--strict` to fail the run on any of these (CI mode).")
    out.append("")
    if icarus_total == 0:
        out.append("_All icarus-schema fields valid (or absent)._")
    else:
        if invalid_verified:
            out.append(f"### Invalid `verified` values ({len(invalid_verified)})")
            out.append("")
            out.append("Must be one of `unverified | verified | contradicted | rolled_back` (or omit the field entirely).")
            out.append("")
            for f, v in invalid_verified:
                rel = f.relative_to(wiki_root)
                out.append(f"- `{rel.as_posix()}` — got `{v}`")
            out.append("")
        if invalid_type:
            out.append(f"### Invalid `type` values ({len(invalid_type)})")
            out.append("")
            out.append("Must be one of `decision | observation | attempt | rollback | review` (or omit).")
            out.append("")
            for f, v in invalid_type:
                rel = f.relative_to(wiki_root)
                out.append(f"- `{rel.as_posix()}` — got `{v}`")
            out.append("")
        if missing_contradicted_by:
            out.append(f"### `verified='contradicted'` missing `contradicted_by` ({len(missing_contradicted_by)})")
            out.append("")
            out.append("If you mark an entry as contradicted, you must point at the newer entry that contradicts it (so retrieval can present both sides).")
            out.append("")
            for f in missing_contradicted_by:
                rel = f.relative_to(wiki_root)
                out.append(f"- `{rel.as_posix()}`")
            out.append("")
        if missing_revises_on_rollback:
            out.append(f"### `type='rollback'` missing `revises` ({len(missing_revises_on_rollback)})")
            out.append("")
            out.append("A rollback entry must point at the verified ancestor it restores via `revises:`.")
            out.append("")
            for f in missing_revises_on_rollback:
                rel = f.relative_to(wiki_root)
                out.append(f"- `{rel.as_posix()}`")
            out.append("")
        if missing_review_of_on_review:
            out.append(f"### `type='review'` missing `review_of` ({len(missing_review_of_on_review)})")
            out.append("")
            out.append("A review entry must point at the audited target via `review_of:`.")
            out.append("")
            for f in missing_review_of_on_review:
                rel = f.relative_to(wiki_root)
                out.append(f"- `{rel.as_posix()}`")
            out.append("")
        if broken_icarus_ref:
            out.append(f"### Broken icarus-ref ({len(broken_icarus_ref)})")
            out.append("")
            out.append("`revises`, `review_of`, and `contradicted_by` must each point at an existing wiki entry.")
            out.append("")
            for f, field, value in broken_icarus_ref:
                rel = f.relative_to(wiki_root)
                out.append(f"- `{rel.as_posix()}` — `{field}: {value}` (file not found)")
            out.append("")
    out.append("")

    # Save report
    report_path = topic_root / "_inbox" / "lint-report.md"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_text = "\n".join(out)
    atomic_write_text(report_path, report_text)
    # Print to stdout
    print(report_text)
    print()
    print(f"Report saved to: {report_path}")

    # Exit code: strict mode fails on broken links OR any icarus invariant violation.
    # Non-strict (default) always returns 0 — report is informational.
    if strict:
        if broken_links or icarus_total > 0:
            return 1
    return 0


def main():
    parser = argparse.ArgumentParser(description="Lint a topic wiki for broken links, orphans, stale claims, and icarus-schema invariants")
    parser.add_argument("--topic", required=True)
    parser.add_argument("--vault", default=DEFAULT_VAULT)
    parser.add_argument(
        "--strict", action="store_true",
        help="Fail (exit 1) if there are broken links or icarus-schema violations. "
             "Use in CI. Default: always exit 0 (report-only mode).",
    )
    args = parser.parse_args()
    return lint(args.vault, args.topic, strict=args.strict)


if __name__ == "__main__":
    sys.exit(main())
