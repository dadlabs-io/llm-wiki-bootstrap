#!/usr/bin/env python3
"""Checks that the Related section ends at the next heading (task #233). Never shipped.

    uv run python tests/scripts/test_related_section.py   # exit 0 = every check passed

agentic-design's semantic lint (cycle 2026-10-30-01) found links added by `wiki-promote.py` and
`wiki-link-gaps.py apply` sitting under `## Sources` instead of `## Related in this wiki`. Both add
a link through `_entry_checks.add_related_link`, which looks for the heading that ends the Related
section. Since 2026-10-06 (#81 P4) a second, single-line `_HEADING_RE` defined further down the
module replaced the multi-line one, so no later heading was ever found: the new bullet went after
the last bullet above the footer, often under Sources. The gate's Related count
(`_related_section`) read the same way and counted links under Sources as Related.
"""
from __future__ import annotations

import sys
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[2] / "scripts"
sys.path.insert(0, str(SCRIPTS))
import _entry_checks as ec  # noqa: E402

results: list[tuple[bool, str]] = []


def check(name: str, ok: bool):
    results.append((ok, name))


ENTRY = (
    "---\ntitle: T\n---\n\n# T\n\n## TL;DR\n\nSummary.\n\n"
    "## Related in this wiki\n\n- [A](a.md) — agrees.\n- [B](b.md) — extends.\n\n"
    "## Sources\n\n- External: the paper.\n- Internal: this summary.\n\n"
    "---\n\n**Source**: <https://example.org/x>\n**Raw**: [x.md](../../raw/x.md)\n"
)
NEW = "- [C](./c.md)"

out = ec.add_related_link(ENTRY, NEW)
related, sources = out.split("## Sources")[0], out.split("## Sources")[1]
check("add_related_link: the new bullet lands in Related", NEW in related)
check("add_related_link: nothing is added under Sources", NEW not in sources)
check("add_related_link: it follows Related's last bullet",
      "- [B](b.md) — extends.\n" + NEW + "\n" in out)

# A Related section with no bullets yet, followed by another section.
EMPTY = ENTRY.replace("- [A](a.md) — agrees.\n- [B](b.md) — extends.\n", "")
out2 = ec.add_related_link(EMPTY, NEW)
check("add_related_link: an empty Related gets the bullet, not Sources",
      NEW in out2.split("## Sources")[0] and NEW not in out2.split("## Sources")[1])

# A sub-heading inside Related does not end it; a same-level heading does.
SUB = ENTRY.replace("- [B](b.md) — extends.\n", "- [B](b.md) — extends.\n\n### Older\n\n- [D](d.md) — older.\n")
out3 = ec.add_related_link(SUB, NEW)
check("add_related_link: a ### inside Related keeps the bullet in Related",
      NEW in out3.split("## Sources")[0])

# The gate's count reads Related only.
ONE = ENTRY.replace("- [B](b.md) — extends.\n", "").replace(
    "- Internal: this summary.\n", "- Internal: this summary.\n- [E](e.md)\n- [F](f.md)\n")
_, body = ec.split_frontmatter(ONE, flat=True)
section = ec._related_section(body)
check("_related_section: stops at the next ## heading", section is not None and "e.md" not in section)
errs = ec.check_entry_body(body, tags=["a", "b", "c"])["errors"]
check("gate: one Related link plus two under Sources is refused",
      any("`## Related` section has 1 wiki link" in e for e in errs))
_, body2 = ec.split_frontmatter(ENTRY, flat=True)
check("gate: two Related links still pass",
      not any("Related" in e for e in ec.check_entry_body(body2, tags=["a", "b", "c"])["errors"]))

# The transcription split (the second regex's own use) still works.
own, tr = ec.split_transcriptions("Text.\n\n## Transcribed from s1.png by w, 2026-10-06\n\nSlide words.\n\n## Next\n\nMore.\n")
check("split_transcriptions: unchanged", "Slide words." in tr and "More." in own and "Slide words." not in own)

failed = [n for ok, n in results if not ok]
for ok, n in results:
    print(("PASS " if ok else "FAIL ") + n)
print(f"\n{len(results) - len(failed)}/{len(results)} passed")
sys.exit(1 if failed else 0)
