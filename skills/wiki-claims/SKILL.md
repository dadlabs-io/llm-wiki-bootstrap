---
name: wiki-claims
description: Extract factual claims from wiki entries, classify them (direct-quote/sourced/synthesis/inference), compare across entries, flag contradictions at the sentence level, and score how many independent sources back each claim. Use when the user says "extract claims", "find contradictions", "wiki-claims", "claim analysis", "what contradicts what". Not for checking one staged entry against its own raw (the wiki-checker, in /wiki-cycle) or for finding stale entries (/wiki-refresh).
last_reviewed: 2026-10-13
review_after: 2027-01-13
reviewed_for_model: claude-opus-5-5
---

> **⚙️ Internal skill.** This is invoked by `/wiki-cycle` (the orchestrator) — users normally don't call it directly. Public-facing commands are `/wiki-cycle`, `/wiki-update`, `/wiki-search`, `/wrap-up`, `/wiki-verify`, `/wiki-rollback` and `/new-wiki`. This skill is documented + callable for programmatic use.

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

**A figure's evidence (since 2026-10-14, task #136).** On a claim that carries a figure (a score, a speed-up, an accuracy, a count, a cost), also record `evidence`: `measured`, `claimed` or `unknown`, as the entry marks it in the figure's attribution (authoring doctrine, principle 5, "Measured or claimed"); an entry that does not mark it is `unknown`. A contradiction between a `claimed` figure and a `measured` one is reported with both statuses: the measured one is the better evidence, and both sides stay.

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

For `--entry` or `--compare` mode, append to the existing index (don't rebuild the whole thing). New claims take ids after the index's highest; when several agents extract in parallel, give each a block of ids up front (agent 1 from `max+1`, agent 2 from `max+2001`, ...), so the `agrees_with` links of Step 5 hold when their claims are merged.

### Step 5 — Record agreements, then find contradictions

**Agreements (since 2026-10-13, task #110).** Claims that agree make each other stronger, but only when they come from independent sources: seven reposts of one benchmark are one source, three different authors are three. While comparing claims by subject, record each agreement on the claims themselves:

- `agrees_with: [<claim id>, ...]` — on a claim, the ids of other entries' claims that state the same fact (the same subject, a compatible object: "82.1% of bugs" and "about four in five bugs" agree). A claim in the same entry is not an agreement.
- `origin: "<url or name>"` — on a claim that restates someone else's evidence (a paper, a benchmark, a vendor's dashboard, a person's post), the original: its URL when the entry gives one, else its name ("CRBugBench paper", "TypeSafe dashboard"). Leave it out when the entry is the original itself.

Then run the arithmetic, which groups the agreeing claims, merges claims that share an origin or a source URL into one source, weighs each source by its entry's tier (1.0 / 0.6 / 0.3 / 0.1 for tiers 1-4; our own `self` synthesis weighs 0), and writes a `corroboration` record on every grouped claim. A merged source counts once, at the best tier among its entries: four tier-4 reposts of a tier-1 paper are one source weighing 1.0, and the reposts add nothing. Every claim in a group carries the same record, with these keys:

- `group`: the ids of the claims in the group;
- `sources`: one item per independent source, each with `key`, `entries`, `claims`, `tier`, `weight` and `merged_because` (why its claims were counted as one source: "same origin: <origin>" or "same source URL"; empty when it holds one claim);
- `independent_sources`, `score`, `computed` (the date).

```bash
uv run --project {{WIKI_SCRIPTS_DIR}} python {{WIKI_SCRIPTS_DIR}}/wiki-claims-corroborate.py --topic <notebook> --report _inbox/reports/corroboration-<date>.md
# inside /wiki-cycle: --report <run-folder>/corroboration.md
```

It never changes an entry's `confidence`; it lists where the two disagree (a high-confidence entry with a score under 0.3; a low-confidence one scoring 1.0 or more from two or more independent sources). Deciding that two claims share an original is a best guess: the record shows each merge and its reason, so a wrong one can be seen and corrected by editing `origin` and running the script again.

Its printed summary also counts the index (`index_claims`, `index_entries`): take the report's and Step 7's claim and entry totals from it rather than counting by hand. A relative `--report` path is the notebook's, whatever folder the command runs from.

The section it writes has a fixed layout, which the report keeps unchanged: `## Corroboration`, one summary line, a table `| Score | Sources | Claim | Sources counted (merged because) |` with one row per group (highest score first), then `### Confidence and corroboration disagree` with one line per flag (`- <claim id> in <entry>: confidence <high|low>, score <n> (<why>)`, or `None.`).

**Contradictions.** Scan two axes:

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

When emitting to the cycle-contract `queued[]` (see [cycle-step-return-format]({{TOOLSET_DIR}}/wiki/project/best-practices/framework/cycle-step-return-format.md)), map these fields into the contract's shape:
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

Save to `_inbox/reports/claims-report-<date>.md`:

```markdown
# Claims Report — <date>

**Entries scanned**: N
**Claims extracted**: N
**By classification**: direct-quote N, sourced N, synthesis N, inference N
**Figures by evidence**: measured N, claimed N, unknown N
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

<the section wiki-claims-corroborate.py wrote to its --report file, pasted unchanged — it starts with its own
`## Corroboration` heading, so add none above it: the groups of agreeing
claims by score, the sources each counted and why claims were merged, the claims resting on a single tier-4
entry, and where an entry's confidence and its claims' corroboration disagree>
```

### Step 7 — Report to user

Print a summary:
```
Claims extraction complete
  Entries: N
  Claims: N (quote: N, sourced: N, synthesis: N, inference: N)
  Contradictions: N (high: N, medium: N, low: N)
  Corroboration: N groups, N well corroborated, N single tier-4 claims, N confidence disagreements
  Report: _inbox/reports/claims-report-<date>.md
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

- Claims index: `_inbox/claims-index.json`
- Claims report: `_inbox/reports/claims-report-<date>.md`
- Corroboration section (the script's `--report`): `_inbox/reports/corroboration-<date>.md`, or in the cycle's run folder
- Wiki entries: `wiki/`
- All relative to the notebook root: `_inbox/` sits beside `wiki/`, not inside it

## Don't

- Don't extract opinions as claims — only factual assertions
- Don't auto-resolve contradictions — flag them, human decides per wiki contradiction policy (keep both sides)
- Don't delete the claims index between runs — append to it, let it grow
- Don't run full extraction during ingestion — use `--compare` mode (one entry against existing index)
- Don't treat `framing_difference` as a real contradiction — note it and move on
- Don't count agreement by hand or write a `corroboration` record yourself — record `agrees_with` and `origin`, and let `wiki-claims-corroborate.py` do the counting and weighting
- Don't change an entry's `confidence` from a corroboration score — the report lists the disagreements for a human


## Cycle contract

When invoked inside `/wiki-cycle`, this skill writes `<run-folder>/<step>.json` and `<step>.md` per the [Cycle Step Return Format contract]({{TOOLSET_DIR}}/wiki/project/best-practices/framework/cycle-step-return-format.md) — that doc defines the shape, counters, and queued/skipped/deferred semantics for this step.
