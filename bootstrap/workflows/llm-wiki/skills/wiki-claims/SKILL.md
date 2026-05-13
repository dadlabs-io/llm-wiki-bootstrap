---
name: wiki-claims
description: Extract factual claims from wiki entries, classify them (direct-quote/sourced/synthesis/inference), compare across entries, and flag contradictions at the sentence level. Use when the user says "extract claims", "find contradictions", "wiki-claims", "claim analysis", "what contradicts what".
---

> **⚙️ Internal skill.** This is invoked by `/wiki-cycle` (the orchestrator) — users normally don't call it directly. Public-facing commands are `/wiki-cycle`, `/wiki-update`, `/wiki-search`, `/wiki-init`. This skill is documented + callable for programmatic use.

# /wiki-claims

Extract factual claims from wiki entries, classify each by evidence type, and find contradictions across the wiki at the sentence level — not the page level.

## Usage

```
/wiki-claims                              # full extraction across all entries
/wiki-claims <folder>                     # extract from one folder (active/, long-term/, etc.)
/wiki-claims --entry <filename>           # extract from a single entry (e.g., during ingestion)
/wiki-claims --compare <filename>         # extract from one entry + compare against existing claims index
/wiki-claims --contradictions-only        # skip extraction, just scan existing claims index for conflicts
```

## Why claim-level matters

Page-level contradiction detection (what semantic lint does) catches "entry A says X, entry B says not-X." But it misses:
- Two entries that agree overall but have one conflicting detail (e.g., a benchmark number)
- Claims that are synthesis (our interpretation) vs direct quotes (source's words) — synthesis can drift
- Stale claims embedded in otherwise-current entries (e.g., "97 entries" when there are 105)

Claim extraction makes every assertion explicit and classifiable.

## What You Must Do When Invoked

### Step 1 — Determine scope

| Flag | Scope |
|---|---|
| No flag | All entries in `wiki/` |
| `<folder>` | All entries in `wiki/<folder>/` |
| `--entry <file>` | Single entry (fast, use during ingestion) |
| `--compare <file>` | Single entry extracted + compared against existing claims index |
| `--contradictions-only` | Read existing `_inbox/claims-index.json`, scan for contradictions |

### Step 2 — Read the entries

Read each entry in scope. For `--entry` or `--compare`, read just that one file.

### Step 3 — Extract claims

For each entry, extract every **factual assertion** — statements that can be true or false. Skip:
- Opinions ("this matters because...")
- Framing ("this entry fills the X slot")
- Questions ("should we...?")
- Instructions ("run this command")

For each claim, record:

```json
{
  "claim": "agentmemory achieves 95.2% LongMemEval R@5",
  "source_entry": "active/agentmemory-rohitg00.md",
  "source_line": "approximately line 47",
  "classification": "sourced",
  "confidence": 0.9,
  "subject": "agentmemory",
  "predicate": "benchmark_score",
  "object": "95.2% LongMemEval R@5"
}
```

### Classification types

| Type | Definition | Example | Trust level |
|---|---|---|---|
| `direct-quote` | Verbatim from source, in blockquotes | `> "Memory scaling is the property that..."` | Highest — it's their words |
| `sourced` | Paraphrased but attributed to a specific source | "Databricks found accuracy rose from 2.5% to 50%" | High — we cited the source |
| `synthesis` | Our conclusion drawn from multiple sources | "This validates our three-layer architecture" | Medium — our interpretation |
| `inference` | Our own assertion not directly supported by any cited source | "The bottleneck is metacognition, not embeddings" | Lowest — may be wrong |

### Step 4 — Build the claims index

Write extracted claims to `_inbox/claims-index.json`:

```json
{
  "generated": "2026-04-12",
  "entry_count": 105,
  "claim_count": 847,
  "claims": [
    {
      "id": "claim-001",
      "claim": "...",
      "source_entry": "...",
      "classification": "sourced",
      "confidence": 0.9,
      "subject": "agentmemory",
      "predicate": "benchmark_score",
      "object": "95.2%"
    }
  ]
}
```

For `--entry` or `--compare` mode, append to the existing index (don't rebuild the whole thing).

### Step 5 — Find contradictions

Scan two axes:

**Cross-entry contradictions** — every claim pair across different entries where:
- Same `subject` (same entity/project/concept being discussed)
- Different `object` or incompatible `predicate` (conflicting facts about it)

**Intra-entry drift** — conflicting statements *within* a single entry:
- TL;DR overstates what the body actually shows (the highest-yield category per the 2026-04-24 validation run)
- Frontmatter tags don't match body content
- Stale counts embedded in an otherwise-current entry
- "Abstract-only" caveat missing when the entry was actually abstract-only

Both surface as entries in `queued[]` in the cycle-contract JSON.

For each potential contradiction, the internal record shape is:

```json
{
  "claim_a": "claim-042",
  "claim_b": "claim-187",
  "type": "direct_conflict | stale_data | scope_difference | framing_difference | intra_entry_drift",
  "severity": "high | medium | low",
  "explanation": "One sentence explaining why these conflict"
}
```

When emitting to the cycle-contract `queued[]` (see [cycle-step-return-format](./best-practices/framework/cycle-step-return-format.md)), map these fields into the contract's shape:
- Cross-entry: `{ priority, slug_a, slug_b, claim_a, claim_b, severity, confidence, reason, timestamp }`
- Intra-entry: `{ priority, slug, claim_a, claim_b, severity, confidence, reason, timestamp }` (single slug, both claims from it)

The internal `type` collapses into the cycle-contract `reason` field.

**Contradiction types**:

| Type | What it means | Action |
|---|---|---|
| `direct_conflict` | Two sources say opposite things | Keep both, add disambiguation note |
| `stale_data` | One claim is outdated (old count, old version) | Update the stale one |
| `scope_difference` | Both true in different contexts, looks like a conflict | Add scope qualifier to each |
| `framing_difference` | Same fact, different emphasis — not a real conflict | No action, note in report |

### Step 6 — Write the report

Save to `_inbox/claims-report-<date>.md`:

```markdown
# Claims Report — <date>

**Entries scanned**: N
**Claims extracted**: N
**By classification**: direct-quote N, sourced N, synthesis N, inference N
**Contradictions found**: N (high: N, medium: N, low: N)

## High-severity contradictions

### 1. <subject>: <claim A text> vs <claim B text>
- **Claim A**: <entry A> (line ~N) — classification: <type>
- **Claim B**: <entry B> (line ~N) — classification: <type>
- **Type**: direct_conflict
- **Suggested fix**: <what to do>

## Medium-severity contradictions
...

## Low-severity (framing differences)
...

## Inference claims (highest drift risk)

These are our own assertions not backed by a cited source. Review periodically:
- <claim> in <entry> — confidence <score>
- ...
```

### Step 7 — Report to user

Print a summary:
```
Claims extraction complete
  Entries: N
  Claims: N (quote: N, sourced: N, synthesis: N, inference: N)
  Contradictions: N (high: N, medium: N, low: N)
  Report: _inbox/claims-report-<date>.md
  Index: _inbox/claims-index.json
```

## Integration with other skills

### During `/wiki-update` (ingestion)

After step 4 (synthesize) and before step 5 (eval gate), optionally run:
```
/wiki-claims --compare <new-entry-temp-file>
```
This extracts claims from the new entry and compares against the existing claims index. If contradictions are found, they're surfaced in the eval gate output so the user can decide before filing.

This is optional — only run it if `claims-index.json` exists. If it doesn't, skip (no index to compare against).

### During `/wiki-lint --full` (semantic lint)

The CONTRADICTIONS criterion in semantic lint can delegate to this skill:
```
/wiki-claims --contradictions-only
```
This is more precise than the agent reading entries and guessing at contradictions — it uses the structured claims index.

## Key paths

- Claims index: `llm-wiki/wiki/_inbox/claims-index.json`
- Claims report: `llm-wiki/wiki/_inbox/claims-report-<date>.md`
- Wiki entries: `llm-wiki/wiki/`

## Don't

- Don't extract opinions as claims — only factual assertions
- Don't auto-resolve contradictions — flag them, human decides per wiki contradiction policy (keep both sides)
- Don't delete the claims index between runs — append to it, let it grow
- Don't run full extraction during ingestion — use `--compare` mode (one entry against existing index)
- Don't treat `framing_difference` as a real contradiction — note it and move on


## Cycle contract

When invoked inside `/wiki-cycle`, this skill writes `<run-folder>/<step>.json` and `<step>.md` per the [Cycle Step Return Format contract](./best-practices/framework/cycle-step-return-format.md) — that doc defines the shape, counters, and queued/skipped/deferred semantics for this step.
