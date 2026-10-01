---
title: "wiki-claims — skill"
type: how-to
artifact: skill
name: wiki-claims
installed_by: install-wiki
date: 2026-07-31
---

# wiki-claims — skill

Pulls every factual assertion out of your wiki entries, labels each one by how well it is backed by evidence, and then hunts for places where two claims disagree. It works at the sentence level rather than the page level, which catches the things a page-level check misses: two entries that broadly agree but conflict on one benchmark number, or a stale count embedded in an otherwise-current entry. Each claim is classified as a direct quote, sourced paraphrase, synthesis, or inference — the last of these being your own assertions with no cited source, and therefore the ones most likely to drift.

**Trigger:** */wiki-claims*, or natural phrasings like "extract claims", "find contradictions", "what contradicts what". Scope it with a folder name, `--entry <file>` for a single entry, `--compare <file>` to check one entry against what is already indexed, or `--contradictions-only` to rescan the existing index without re-extracting.

**Input / Output:** Reads the entries under `wiki/`. Writes a structured claims index to `_inbox/claims-index.json` and a report to `_inbox/reports/claims-report-<date>.md` (the `_inbox/` beside `wiki/`); inside a cycle it also writes `claims.json` / `claims.md` to the run's report folder. The index grows: single-entry modes append to it rather than rebuilding it. The report groups contradictions by severity and lists every inference claim for periodic review. There is no script — the model reads, extracts and compares, so results depend on the model running it.

**What it looks for:**
- **Cross-entry contradictions** — two claims about the same subject that disagree.
- **Intra-entry drift** — an entry disagreeing with itself: a TL;DR that overstates the body, tags that don't match the body, a stale count, a missing "abstract-only" caveat. This category turns up the most.

Each finding is typed: `direct_conflict` (keep both sides, add a note), `stale_data` (update the stale one), `scope_difference` (add a scope qualifier to each), `framing_difference` (same fact, different emphasis — no action), or `intra_entry_drift`.

**Works with:** [`wiki-cycle`](./wiki-cycle.md) runs it in `--full` and `--claims-only`: a full extraction the first time, then `--compare` for the new entries. [`wiki-update`](./wiki-update.md) does not run it; `--compare <entry>` checks a new entry against the index by hand. It complements [`wiki-lint`](./wiki-lint.md) `--full`, whose agents judge contradictions by reading entries; this skill works from a structured index.

**When it skips itself:** comparing a new entry needs an existing claims index; with none there is nothing to compare against, so run a full extraction first. Contradictions are flagged, never auto-resolved — the policy is to keep both sides and let a human decide.
