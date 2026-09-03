#!/usr/bin/env python3
"""Shared body-level checks for wiki entries — the MECHANICAL half of the eval rubric.

Single source of truth for every structural rule the eval rubric
(`wiki/research/implementation/eval-rubric.md`) and the wiki-update skill
state in prose. Two callers:

  * `wiki-update.py`           — pre-write GATE. Hard failures refuse to file
                                  (override with --no-gate + a printed reason).
  * `wiki-lint-mechanical.py`  — backlog VIEW. Same checks over every existing
                                  entry, warn-only, so drift is visible.

Why one module: a rule that lives only as prose in a SKILL.md is enforced only
by the drafting agent's goodwill — and the drafting agent scoring its own
draft is circular. The 2026-08-13 lint retrofit found exactly that: "everything
the lint script checks is clean; everything it doesn't check has decayed."
Pairing each prose rule with a deterministic check (the hybrid-artifact
pattern — Huk, "Context as Code", O'Reilly Radar 2026-06-03; ingested into
agentic-design 2026-09-02) is the fix. The judgment dimensions of the rubric
(extraction fidelity, synthesis value) stay with the agent; everything here is
what a script can decide.

Checks (rubric dimension → rule → severity):
  structure  → a `## TL;DR` section exists                         → ERROR
  cross-link → a `## Related…` section with >= 2 links to .md files → ERROR
               (tier `self` entries: WARNING — project notes may legitimately
               start thin, and the CLAUDE.md inline-filing flow files them)
  metadata   → >= 3 tags                                            → WARNING
  structure  → < 30 non-blank body lines and no `stub` tag           → WARNING
  fidelity   → numeric claims in prose outside a `>` blockquote      → WARNING
               (numbers must be quoted + attributed; paraphrased numbers drift)

System pages (HOME.md, README.md, _MAP.md, _INDEX.md, index.md) and
framework-contract docs are skipped by `is_exempt()`.
"""
from __future__ import annotations

import re
from pathlib import Path

SYSTEM_STEMS = {"_INDEX", "_MAP", "HOME", "README", "index", "_pending-list"}

MIN_RELATED_LINKS = 2
MIN_TAGS = 3
STUB_LINE_THRESHOLD = 30

# A `## TL;DR` heading, or the older bold-lead style `**TL;DR**: …` at line
# start (61 entries in agentic-design used it when this check was added).
_TLDR_RE = re.compile(r"^(?:#{1,6}\s*\**\s*|\*\*\s*)TL;?DR\b", re.IGNORECASE | re.MULTILINE)
_RELATED_HEADING_RE = re.compile(r"^(#{1,6})\s*\**\s*Related\b", re.IGNORECASE | re.MULTILINE)
_HEADING_RE = re.compile(r"^(#{1,6})\s", re.MULTILINE)
_MD_LINK_RE = re.compile(r"\]\(([^)\s]+\.md)(?:#[^)]*)?\)")
# Numeric claims that the rubric says must be blockquoted + attributed.
# Deliberately narrow: percentages, multipliers, token/star/size counts,
# latencies, money. Bare integers (dates, step numbers, list numbers) are
# NOT matched — they are almost never "claims".
_NUMBER_CLAIM_RE = re.compile(
    r"(?<![\w./-])"
    r"(?:\$\s?\d[\d,]*(?:\.\d+)?[kKmMbB]?"                   # money
    r"|\d[\d,]*(?:\.\d+)?\s?(?:%|percent|×|x(?![\w-])"       # 40%, 3x, 2.5×
    r"|[kKmMbB]\s?(?:tokens?|stars?|params?|parameters|users?|rows?|docs?|files?)"
    r"|tokens?|stars?|ms|milliseconds|seconds?|minutes?|hours?|GB|MB|TB|LOC)"
    r"(?![\w-]))"
)


# ── Parsing helpers (kept local to avoid circular imports) ───────────────────


def split_frontmatter(text: str):
    """Return (frontmatter_dict, body). Minimal YAML: `key: value` lines only;
    inline `[a, b]` lists are returned as lists; block lists (`- item`) too."""
    fm: dict = {}
    body = text
    if text.startswith("---"):
        end = text.find("\n---", 3)
        if end > 0:
            header = text[3:end]
            body = text[end + 4:]
            last_key = None
            for line in header.splitlines():
                if not line.strip():
                    continue
                if line.startswith(("-", "  -")) and last_key:
                    fm.setdefault(last_key, [])
                    if isinstance(fm[last_key], list):
                        fm[last_key].append(line.strip().lstrip("-").strip().strip("\"'"))
                    continue
                if ":" in line and not line.startswith(" "):
                    key, value = line.split(":", 1)
                    key = key.strip()
                    value = value.strip()
                    if value.startswith("[") and value.endswith("]"):
                        fm[key] = [v.strip().strip("\"'") for v in value[1:-1].split(",") if v.strip()]
                    elif value == "":
                        fm[key] = []  # block list follows (or genuinely empty)
                    else:
                        fm[key] = value.strip("\"'")
                    last_key = key
    return fm, body


def is_exempt(path, fm: dict | None = None, wiki_root=None) -> bool:
    """System / hub / framework-contract pages are not 'entries' and skip body checks.
    Pass `wiki_root` to also exempt files sitting directly at the wiki root
    (HOME, glossary, concept-gaps, user guide, system overview — hub pages by
    position, whatever their names)."""
    path = Path(path)
    stem = path.stem
    if stem in SYSTEM_STEMS or stem.startswith("_"):
        return True
    if wiki_root is not None:
        try:
            if path.resolve().parent == Path(wiki_root).resolve():
                return True
        except OSError:
            pass
    if fm and str(fm.get("framework-contract", "")).lower() == "true":
        return True
    if fm and str(fm.get("type", "")).lower() in {"rollback", "review"}:
        return True
    return False


def _strip_footer(body: str) -> str:
    """Drop the canonical `---\\n**Source**: … **Raw**: …` footer and any
    auto-managed BACKLINKS block so their links/numbers don't count."""
    body = re.sub(r"<!-- BACKLINKS-AUTO START -->.*?<!-- BACKLINKS-AUTO END -->", "", body, flags=re.DOTALL)
    body = re.sub(r"\n---\s*\n\*\*Source\*\*:.*?(?:\n\*\*Raw\*\*:.*?)?\s*$", "", body, flags=re.DOTALL)
    return body


def _prose_only(body: str) -> str:
    """Body with fenced code, inline code, blockquote lines, and table rows removed."""
    b = re.sub(r"```.*?```", "", body, flags=re.DOTALL)
    b = re.sub(r"`[^`\n]*`", "", b)
    keep = []
    for line in b.splitlines():
        s = line.lstrip()
        if s.startswith(">") or s.startswith("|"):
            continue
        keep.append(line)
    return "\n".join(keep)


def _related_section(body: str) -> str | None:
    """Text of the first `## Related…` section (up to the next heading of the
    same or higher level), or None if absent."""
    m = _RELATED_HEADING_RE.search(body)
    if not m:
        return None
    level = len(m.group(1))
    start = m.end()
    for h in _HEADING_RE.finditer(body, start):
        if len(h.group(1)) <= level:
            return body[start:h.start()]
    return body[start:]


# ── The checks ───────────────────────────────────────────────────────────────


def check_entry_body(body: str, *, tags=None, tier=None) -> dict:
    """Run the mechanical rubric checks on an entry BODY (frontmatter already split off).

    Returns {"errors": [...], "warnings": [...], "stats": {...}}.
    `tags` may be a list or None (None = unknown → tag checks skipped).
    `tier` is the frontmatter tier as a string ("1".."4", "self") or None.
    """
    errors: list[str] = []
    warnings: list[str] = []
    body = _strip_footer(body or "")
    tags = [str(t).strip().lower() for t in (tags or [])] if tags is not None else None
    is_self = str(tier).strip().lower() == "self"

    # structure → TL;DR
    has_tldr = bool(_TLDR_RE.search(body))
    if not has_tldr:
        errors.append("missing `## TL;DR` section (rubric: structural completeness)")

    # cross-link → Related section with >= 2 .md links
    related = _related_section(body)
    related_links = len(_MD_LINK_RE.findall(related)) if related is not None else 0
    if related is None:
        msg = "no `## Related` section (rubric: cross-link quality — orphan trap)"
        (warnings if is_self else errors).append(msg)
    elif related_links < MIN_RELATED_LINKS:
        msg = (f"`## Related` section has {related_links} wiki link(s); need >= {MIN_RELATED_LINKS} "
               "(rubric: cross-link quality)")
        (warnings if is_self else errors).append(msg)

    # metadata → tags
    if tags is not None and len(tags) < MIN_TAGS:
        warnings.append(f"{len(tags)} tag(s); spec wants >= {MIN_TAGS}")

    # structure → stub marking
    nonblank = [l for l in body.splitlines() if l.strip()]
    if len(nonblank) < STUB_LINE_THRESHOLD and tags is not None and "stub" not in tags:
        warnings.append(f"only {len(nonblank)} non-blank lines but not tagged `stub`")

    # fidelity → numbers outside blockquotes
    prose = _prose_only(body)
    number_hits = [m.group(0) for m in _NUMBER_CLAIM_RE.finditer(prose)]
    if number_hits:
        sample = ", ".join(dict.fromkeys(number_hits[:3]))
        warnings.append(
            f"{len(number_hits)} numeric claim(s) in prose outside a blockquote "
            f"(e.g. {sample}) — quote + attribute, or drop (rubric: extraction fidelity)"
        )

    return {
        "errors": errors,
        "warnings": warnings,
        "stats": {
            "has_tldr": has_tldr,
            "has_related": related is not None,
            "related_links": related_links,
            "tags": None if tags is None else len(tags),
            "nonblank_lines": len(nonblank),
            "number_claims": len(number_hits),
        },
    }


def check_entry_text(text: str) -> dict:
    """Convenience: full file text (frontmatter + body) → same result dict,
    with `fm` added. Exempt pages return an empty result with `exempt: True`."""
    fm, body = split_frontmatter(text)
    tags = fm.get("tags")
    if isinstance(tags, str):
        tags = [t.strip() for t in tags.strip("[]").split(",") if t.strip()]
    result = check_entry_body(body, tags=tags if tags is not None else None, tier=fm.get("tier"))
    result["fm"] = fm
    return result


def check_entry_file(path) -> dict:
    path = Path(path)
    text = path.read_text(encoding="utf-8")
    fm, _ = split_frontmatter(text)
    if is_exempt(path, fm):
        return {"errors": [], "warnings": [], "stats": {}, "fm": fm, "exempt": True}
    result = check_entry_text(text)
    result["exempt"] = False
    return result


def format_result(result: dict, label: str = "") -> str:
    lines = []
    head = f"Entry checks{': ' + label if label else ''}"
    lines.append(head)
    for e in result.get("errors", []):
        lines.append(f"  ERROR    {e}")
    for w in result.get("warnings", []):
        lines.append(f"  warning  {w}")
    if not result.get("errors") and not result.get("warnings"):
        lines.append("  clean")
    return "\n".join(lines)


if __name__ == "__main__":  # tiny CLI for ad-hoc use: python _entry_checks.py <file.md> [...]
    import sys
    rc = 0
    for arg in sys.argv[1:]:
        r = check_entry_file(arg)
        if r.get("exempt"):
            print(f"{arg}: exempt")
            continue
        print(format_result(r, arg))
        if r["errors"]:
            rc = 1
    sys.exit(rc)
