---
name: wiki-refresh
description: Scan wiki entries for stale content based on review_after dates, confidence decay, and source freshness. Flags entries that need re-checking, re-fetching, or updating. Use when the user says "refresh the wiki", "check for stale entries", "wiki-refresh", "what needs updating", "decay scan", "stale check".
---

> **⚙️ Internal skill.** This is invoked by `/wiki-cycle` (the orchestrator) — users normally don't call it directly. Public-facing commands are `/wiki-cycle`, `/wiki-update`, `/wiki-search`, `/wiki-init`. This skill is documented + callable for programmatic use.

# /wiki-refresh

Find entries that are past their review date, have low confidence, reference sources that may have changed, or have stale data. The maintenance half of the research cycle — not just "what's new?" but "what's old, weak, or now questionable?"

## Usage

```
/wiki-refresh                         # full scan, all entries
/wiki-refresh --overdue-only          # only entries past review_after date
/wiki-refresh --low-confidence        # only entries with confidence: low or medium
/wiki-refresh --high-value            # only entries with 5+ inbound links (most referenced = most important to keep fresh)
/wiki-refresh --tier <N>              # only entries of a specific tier (e.g., --tier 4 for community sources)
/wiki-refresh --dry-run               # report only, don't offer to fix
```

## What You Must Do When Invoked

### Step 1 — Scan all entries

Read the frontmatter of every `.md` file in `wiki/` (not the full body — just YAML frontmatter). Extract:

```bash
for f in $(find docker/shared/openclaw/vault/wikis/<topic>/wiki -name "*.md" ! -name "_INDEX.md"); do
  echo "---FILE: $f"
  head -30 "$f" | grep -E "^(title|date|source_url|tier|confidence|last_reviewed|review_after|tags):"
done
```

For each entry, record:
- `title`
- `path`
- `date` (when created)
- `last_reviewed` (when last checked)
- `review_after` (when next review is due)
- `tier` (source quality)
- `confidence` (our certainty)
- `source_url` (for re-fetch check)
- `inbound_links` (count how many other entries link to this one)

### Step 2 — Classify each entry

Apply these rules:

| Category | Condition | Priority |
|---|---|---|
| **Overdue** | `review_after` < today | HIGH — past the review date we set |
| **Low confidence** | `confidence: low` | HIGH — we flagged this as uncertain |
| **Medium confidence + old** | `confidence: medium` AND `last_reviewed` > 90 days ago | MEDIUM — uncertain and aging |
| **Tier 4 unverified** | `tier: 4` AND no corroboration from tier 1-2 entries | MEDIUM — community source, unchecked |
| **High inbound + aging** | 5+ inbound links AND `last_reviewed` > 60 days ago | MEDIUM — load-bearing entry getting stale |
| **Source may have changed** | `source_url` points to a GitHub repo/release page AND `last_reviewed` > 30 days ago | LOW — source is likely to have updates |
| **Current** | None of the above | OK — no action needed |

### Step 3 — For each flagged entry, suggest an action

| Category | Suggested action |
|---|---|
| Overdue | Re-read the entry. Is it still accurate? If yes, update `last_reviewed` and `review_after`. If no, update the content. |
| Low confidence | Find a second source that corroborates or contradicts. Upgrade to medium/high or add a disclaimer. |
| Tier 4 unverified | Search for a tier 1-2 source covering the same topic. If found, either corroborate (upgrade confidence) or supersede (replace with better source). |
| High inbound + aging | Priority re-read — many entries depend on this one being correct. |
| Source may have changed | Re-fetch `source_url`, compare against raw. If content changed substantially, flag for re-synthesis. |

### Step 4 — Write the refresh report

Save to `_inbox/reports/refresh-report-<date>.md`:

```markdown
# Refresh Report — <date>

**Topic**: <topic>
**Entries scanned**: N
**Needing attention**: N

## Overdue (past review_after)

| Entry | Review due | Days overdue | Action |
|---|---|---|---|
| <title> | <date> | N | Re-read and update last_reviewed |
...

## Low confidence

| Entry | Confidence | Tier | Action |
|---|---|---|---|
| <title> | low | N | Find corroborating source |
...

## Tier 4 unverified

| Entry | Created | Last reviewed | Action |
|---|---|---|---|
| <title> | <date> | <date> | Search for tier 1-2 corroboration |
...

## High-value aging (5+ inbound links, >60 days)

| Entry | Inbound links | Last reviewed | Action |
|---|---|---|---|
| <title> | N | <date> | Priority re-read |
...

## Source may have changed

| Entry | Source URL | Last reviewed | Action |
|---|---|---|---|
| <title> | <url> | <date> | Re-fetch and compare |
...

## Current (no action needed)

N entries are current and within their review window.
```

### Step 5 — Offer to act

After showing the report:

- "Want me to batch-update `last_reviewed` on entries you've confirmed are still accurate?"
- "Want me to re-fetch any of the source URLs and check for changes?"
- "Want me to search for corroborating sources for the low-confidence entries?"

If the user approves batch updates, update `last_reviewed: <today>` and recalculate `review_after` based on tier:

| Tier | Default review interval |
|---|---|
| 1 (paper) | 6 months |
| 2 (vendor) | 3 months |
| 3 (expert) | 3 months |
| 4 (community) | 2 months |
| self | 3 months |

### Step 6 — Quick-refresh mode (for batch confirmation)

If the user says "I've reviewed these, they're fine" for a batch:

```bash
# Update last_reviewed and review_after for all confirmed entries
```

Read each file, update the two frontmatter fields, save. This is the fast path — the user read the report, confirmed accuracy, and the wiki records that the review happened.

## Integration with the research cycle

This skill implements **Phase 10 (Refresh/decay)** of the research cycle. It ensures the cycle spends part of its budget maintaining old entries, not just discovering new ones.

The `/wiki-report` morning report references this skill's output — the "Stale entries" section pulls from the refresh scan.

## Key paths

- Refresh report: `docker/shared/openclaw/vault/wikis/<topic>/_inbox/reports/refresh-report-<date>.md`
- Wiki entries: `docker/shared/openclaw/vault/wikis/<topic>/wiki/`

## Don't

- Don't auto-update entries — only update `last_reviewed` dates with user confirmation
- Don't delete stale entries — flag them for review, human decides
- Don't re-fetch URLs without asking — some sources may be paywalled or rate-limited
- Don't treat "overdue" as "wrong" — it just means the scheduled review hasn't happened yet
- Don't scan raw/ files — only wiki/ entries have lifecycle metadata


## Cycle contract

When invoked inside `/wiki-cycle`, this skill writes `<run-folder>/<step>.json` and `<step>.md` per the [Cycle Step Return Format contract](./best-practices/framework/cycle-step-return-format.md) — that doc defines the shape, counters, and queued/skipped/deferred semantics for this step.
