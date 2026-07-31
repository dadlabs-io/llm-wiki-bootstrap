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

**Input / Output:** Reads entries under `llm-wiki/wiki/`. Writes a structured claims index to `llm-wiki/wiki/_inbox/claims-index.json` (appended to, never rebuilt from scratch in single-entry modes) and a human-readable report to `llm-wiki/wiki/_inbox/claims-report-<date>.md` grouping contradictions by severity and listing every inference claim for periodic review.

**Works with:** [`wiki-update`](./wiki-update.md) can call it in `--compare` mode during ingestion, surfacing conflicts at the evaluation gate before a new entry is filed. [`wiki-lint`](./wiki-lint.md) in full semantic mode can delegate its contradiction check here, which is more precise than reading entries and guessing. [`wiki-cycle`](./wiki-cycle.md) runs it as a step and collects its queued findings.

**Note:** Contradictions are flagged, never auto-resolved — the policy is to keep both sides and let a human decide. Not every flag is a real conflict; a `framing_difference` is the same fact with different emphasis and needs no action.
