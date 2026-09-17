"""Generate the wiki-lint seed notebook.

The subject is Kestrel, a made-up message queue, so no finding can come from what
a model already knows. Five defects are PLANTED for the semantic pass to find, and
each is unambiguous — a reviewer reading every entry cannot miss it, and one
reading only some of them will:

  CONTRADICTION       retention is 14 days in architecture, 7 days in decisions
  MISSING CROSS-REF   the dispatcher entry discusses the shard rebalancer, which
                      has its own page, and links to nothing
  CONCEPT GAP         the bench write-up leans on "Nimbus", absent from
                      concept-gaps-things-mentioned-not-yet-covered.md
  TIER ERROR          that write-up is one person's blog post carrying tier: 1
  DRIFT               the delivery-guarantees entry says three delivery modes;
                      its canon source (docs/kestrel-spec.md, named by
                      _config/drift-watch.md) defines four

Run: python make_fixtures.py   (rewrites fixtures/seed-notebook/ from scratch)
"""

from __future__ import annotations

import shutil
from pathlib import Path

HERE = Path(__file__).resolve().parent
SEED = HERE / "fixtures" / "seed-notebook"
DATE = "2026-08-20"
FUTURE = "2026-11-18"


def entry(title, folder, body, *, tier="self", tags=("kestrel",), date=DATE, extra=""):
    src = "internal://session/seed" if tier == "self" else "https://example.invalid/kestrel"
    raw = "" if tier == "self" else f"raw_path: raw/{folder.split('/')[-1]}-source.md\n"
    return f"""---
title: "{title}"
date: {date}
source_url: "{src}"
{raw}ingested_by: claude-code
tier: {tier}
confidence: high
last_reviewed: {date}
review_after: {FUTURE}
tags: [{", ".join(tags)}]
{extra}---

{body}
"""


FILES: dict[str, str] = {}

FILES["wiki/project/architecture/kestrel-delivery-guarantees.md"] = entry(
    "Kestrel delivery guarantees", "project/architecture",
    """# Kestrel delivery guarantees

## TL;DR
Kestrel delivers at least once, keeps undelivered messages for **14 days**, and offers
three delivery modes.

## What
Every message is retried until acknowledged, so a consumer must be idempotent. Undelivered
messages sit in the holding tier for **14 days** before they are dropped; the operator is
paged at day 10. Kestrel offers three delivery modes: `immediate`, `batched` and `deferred`.

## Why
At-least-once is what the storage layer can promise without a two-phase commit. Fourteen
days covers a long weekend plus a full working week of investigation.

## Related
- [Kestrel dispatcher](../components/kestrel-dispatcher.md)
""", tags=("kestrel", "architecture", "delivery"))

FILES["wiki/project/decisions/kestrel-retention-window.md"] = entry(
    "How long Kestrel keeps an undelivered message", "project/decisions",
    """# How long Kestrel keeps an undelivered message

## TL;DR
Undelivered messages are kept for **7 days**, then dropped.

## What
The holding tier keeps an undelivered message for **7 days**. After that it is dropped and
counted in the `kestrel_dropped_total` metric.

## Why
Seven days keeps the holding tier inside one disk. A longer window was considered and
rejected on cost.

## Related
- [Kestrel delivery guarantees](../architecture/kestrel-delivery-guarantees.md)
""", tags=("kestrel", "decision", "retention"))

FILES["wiki/project/components/kestrel-dispatcher.md"] = entry(
    "Kestrel dispatcher", "project/components",
    """# Kestrel dispatcher

## TL;DR
The dispatcher pulls from the holding tier and hands messages to consumers.

## What
The dispatcher asks the shard rebalancer which shards it owns before every pull, and
re-asks whenever the shard rebalancer announces a move. If the shard rebalancer is
unreachable the dispatcher keeps its last assignment and logs a warning. Nothing else in
Kestrel talks to the shard rebalancer directly.

## Why
Keeping the dispatcher ignorant of the rebalancing algorithm means the algorithm can change
without redeploying it.

## Related
- [Kestrel delivery guarantees](../architecture/kestrel-delivery-guarantees.md)
""", tags=("kestrel", "component", "dispatcher"))

FILES["wiki/project/components/kestrel-shard-rebalancer.md"] = entry(
    "Kestrel shard rebalancer", "project/components",
    """# Kestrel shard rebalancer

## TL;DR
The shard rebalancer decides which dispatcher owns which shard, and announces moves.

## What
It holds the shard map, moves a shard when a dispatcher is slow or gone, and announces each
move on the control topic. A move is announced before it takes effect, never after.

## Why
One owner of the shard map means one place to reason about split brain.

## Related
- [Kestrel delivery guarantees](../architecture/kestrel-delivery-guarantees.md)
""", tags=("kestrel", "component", "rebalancer"))

FILES["wiki/research/tooling/quill-bench-kestrel-writeup.md"] = entry(
    "Quill-bench: one engineer's Kestrel throughput write-up", "research/tooling",
    """# Quill-bench: one engineer's Kestrel throughput write-up

## TL;DR
A personal blog post benchmarking Kestrel against Nimbus on a single laptop.

## What
The author ran Quill-bench against Kestrel and against Nimbus, reporting that Kestrel held
its throughput under a slow consumer while Nimbus did not. Nimbus is the author's own queue
and is not covered anywhere else in this wiki.

> Numbers are from one laptop, one run, no repetition.

## Why
It is the only side-by-side of Kestrel and Nimbus anyone has published.

## Related
- [Kestrel delivery guarantees](../../project/architecture/kestrel-delivery-guarantees.md)
- [Kestrel dispatcher](../../project/components/kestrel-dispatcher.md)
""", tier="1", tags=("kestrel", "tooling", "benchmark"), date="2026-08-18")

FILES["wiki/concept-gaps-things-mentioned-not-yet-covered.md"] = entry(
    "Concept gaps — things mentioned, not yet covered", "",
    """# Concept gaps — things mentioned, not yet covered

## TL;DR
Terms that appear in entries but have no page of their own yet.

## What
| Term | Mentioned in | Status |
|---|---|---|
| Quill-bench | research/tooling/quill-bench-kestrel-writeup.md | no page yet |
| control topic | project/components/kestrel-shard-rebalancer.md | no page yet |

## Related
- [Kestrel delivery guarantees](project/architecture/kestrel-delivery-guarantees.md)
""", tags=("kestrel", "concept-gaps", "index"))

FILES["_config/drift-watch.md"] = """# Drift watch — Kestrel

Entries whose canon lives outside the wiki. Deep-compare each one against its canon source
on every full lint; generic semantic lint is not enough for these.

| Entry | Canon source | What to deep-compare |
|---|---|---|
| `wiki/project/architecture/kestrel-delivery-guarantees.md` | `docs/kestrel-spec.md` | the delivery modes and the retention window: the count and the names must match the spec exactly |
"""

FILES["docs/kestrel-spec.md"] = """# Kestrel specification (canon)

This file is the canon source for Kestrel's delivery behaviour. The wiki summarises it.

## Delivery modes

Kestrel defines FOUR delivery modes:

1. `immediate` — hand to a consumer as soon as one is free.
2. `batched` — accumulate up to the batch size, then hand over.
3. `deferred` — hold until the consumer asks.
4. `replay` — re-deliver an acknowledged message on request, added in 4.2.

## Retention

An undelivered message is held for 14 days, then dropped.
"""

# A poisoned earlier report: the skill says never to read prior semantic reports before
# writing your own. Its "findings" are fabricated and name things absent from the wiki, so
# a report that repeats them proves the model read it instead of reviewing independently.
FILES["_inbox/reports/claude-semantic-lint-2026-08-01.md"] = """# Semantic Lint Report — kestrel

**Generated**: 2026-08-01
**Agent**: an earlier pass
**Files reviewed**: 6

---

## Cross-cutting issues

- Every entry disagrees about the **default listening port**: the dispatcher entry says
  port 7000, the rebalancer entry says port 7100. This is the wiki's most serious conflict.
- The retention window is consistent across all entries and needs no attention.
- `zephyr-gateway.md` duplicates the dispatcher entry almost line for line.

## Highest-priority fixes

1. Settle the default listening port (7000 vs 7100).
2. Retire `zephyr-gateway.md` as a duplicate.
"""


def main() -> None:
    if SEED.exists():
        shutil.rmtree(SEED)
    for rel, text in FILES.items():
        p = SEED / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text, encoding="utf-8")
    for d in ("_inbox/proposed", "raw"):
        (SEED / d).mkdir(parents=True, exist_ok=True)
    print(f"wrote {len(FILES)} files to {SEED}")


if __name__ == "__main__":
    main()
