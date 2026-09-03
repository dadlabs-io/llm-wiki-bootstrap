---
name: wiki-report
description: Generate a morning report summarizing wiki health, recent changes, pending items, contradictions, stale entries, and promotion candidates. The batch summary for human review checkpoint #2. Use when the user says "morning report", "wiki report", "wiki status", "what changed in the wiki", "wiki-report", "show me the wiki health".
last_reviewed: 2026-09-02
review_after: 2026-12-02
reviewed_for_model: claude-fable-5-1
---

> **⚙️ Internal skill.** This is invoked by `/wiki-cycle` (the orchestrator) — users normally don't call it directly. Public-facing commands are `/wiki-cycle`, `/wiki-update`, `/wiki-search`, `/wiki-init`. This skill is documented + callable for programmatic use.

# /wiki-report

Generate a single-page morning report covering everything that changed, everything that's pending, and everything that needs attention. This is the human review checkpoint #2 from the research cycle — a batch quality review, not a per-item gate.

## Usage

```
/wiki-report                    # full report for the configured default topic
/wiki-report <topic>            # specific topic
/wiki-report --since <date>     # changes since a specific date (default: last 7 days)
/wiki-report --brief             # summary counts only, no details
```

## What You Must Do When Invoked

### Step 1 — Gather data (all read-only, no changes)

Run these in parallel where possible:

**A. Recent changes** (git log):
```bash
git log --oneline --since="7 days ago" -- llm-wiki/ | head -30
```

**B. Current entry count**:
```bash
find llm-wiki/wiki -name "*.md" ! -name "_INDEX.md" | wc -l
```

**C. Mechanical lint** (fast, 2 seconds):
```bash
python {{WIKI_SCRIPTS_DIR}}/wiki-lint-mechanical.py \
  --topic <topic> --vault llm-wiki/wiki
```

**D. Pending queue**:
```bash
ls llm-wiki/wiki/_inbox/pending/*.md 2>/dev/null | wc -l
```

**E. Proposed (staged) entries**:
```bash
ls llm-wiki/wiki/_inbox/proposed/*.md 2>/dev/null | grep -v README | wc -l
```

**F. Discovery checklist** (if exists):
```bash
ls llm-wiki/wiki/_inbox/intake-*/*discovery*.md llm-wiki/wiki/_inbox/discovered/*.md 2>/dev/null | head -5
```

**G. Stale entries** (review_after date has passed):
```bash
grep -rl "review_after:" llm-wiki/wiki/ --include="*.md" | while read f; do
  date=$(grep "review_after:" "$f" | head -1 | awk '{print $2}')
  if [[ "$date" < "$(date +%Y-%m-%d)" ]]; then
    echo "$f|$date"
  fi
done
```

**H. Claims report** (if exists):
```bash
ls llm-wiki/wiki/_inbox/reports/claims-report-*.md 2>/dev/null | tail -1
```

**I. Concept gaps count**:
Read `wiki/concept-gaps-things-mentioned-not-yet-covered.md` — count rows in Current gaps table.

**J. Best practices gap analysis**:
Compare what the wiki recommends as best practice against what our system actually does. Read the key best-practice entries and cross-check against current implementation state:

1. Read `wiki/research/implementation/research-cycle-setup.md` — what does the cycle say we should have? What's built, what's not?
2. Read `wiki/research/implementation/getting-started.md` — is the "Current status" table accurate?
3. Scan recent ingests — did any new entry introduce a best practice we're not following? Look for entries with tags containing `best-practice`, `architecture`, `pattern`, or `recommendation`.
4. Check if any newly ingested entry contradicts or updates an existing best practice. For example: if we ingested an article saying "staging is essential" and we're not using staging, that's a gap.
5. Check automation table — compare the checklist (feeds, discovery, ingestion, lint, staging, eval, claims, report, refresh, scratchpad, cron) against actual working state.

Flag three categories:
- **NEW**: a best practice appeared in a recently ingested entry that we don't follow yet
- **DRIFT**: a best practice we were following has drifted (status table says "built" but it's broken or unused)
- **UPGRADE**: a better approach to something we already do has been documented (e.g., a new tool replaces an old one)

### Step 2 — Generate the report

**Filename**: `_inbox/reports/<date>/<cycle_id>/<cycle_id>-run-cycle-report.md`

- `cycle_id` = `<date>-<NN>` (e.g. `2026-04-24-01`). If invoked standalone (not inside a `/wiki-cycle` run), determine `NN` by scanning the day's existing folders.
- Also write `<cycle_id>-run-cycle-report.json` alongside it — the aggregated JSON union of per-step JSONs (see [cycle-step-return-format best practice](./best-practices/framework/cycle-step-return-format.md)).

**Data source — when running inside `/wiki-cycle`**: read the per-step JSONs from `<run-folder>/` (`discover.json`, `update.json`, `lint-mechanical.json`, `lint-semantic.json`, `refresh.json`, `claims.json`). The report is assembled from those — don't re-run steps.

**Data source — when running standalone**: fall back to the Step 1 data-gathering commands (git log, filesystem scans). No per-step JSONs to read.

The MD report template:

```markdown
# Wiki Cycle Report — <cycle_id>

**Topic**: <topic>
**Cycle**: <cycle_id> (<date> iteration <NN>)
**Entries**: N (±N since last report)
**Health**: <lint summary — broken/orphans/missing>

---

## This cycle at a glance

| Step | Queued | Skipped | Deferred | Status |
|---|---|---|---|---|
| Discover | N | N | N | ✅ |
| Update | N | N | N | ✅ |
| Lint (mechanical) | — | — | — | ✅ 0 broken links |
| Lint (semantic) | — | — | — | N findings |
| Refresh | N | N | N | ✅ |
| Claims | N | N | N | ✅ |

Pulled from `<cycle_id>/<step>.json` files. Click through to see the Queued / Skipped / Deferred tables per step.

---

## What changed (last 7 days)

| Date | Commit | Summary |
|---|---|---|
| <date> | <hash> | <message> |
...

**New entries added**: N
**Entries modified**: N
**Backlinks added**: N

---

## Pending work

| Queue | Count | Action |
|---|---|---|
| `_inbox/pending/` | N | Ingest via `/wiki-update` or `/wiki-list process` |
| `_inbox/proposed/` | N | Review via `/wiki-promote` |
| `_inbox/intake-*/` (legacy `discovered/`) | N checklists | Review candidates, approve/reject (per bucket owner) |
| Concept gaps | N open | Ingest or mark as not-needed |

---

## Attention needed

### Stale entries (review_after passed)

| Entry | Review was due | Days overdue |
|---|---|---|
| <entry> | <date> | N |
...

(If none: "All entries current.")

### Contradictions (from latest claims report)

| Severity | Count | Top issue |
|---|---|---|
| High | N | <one-line summary> |
| Medium | N | — |
| Low | N | — |

(If no claims report exists: "No claims index yet. Run `/wiki-claims` to build one.")

### Lint issues

| Issue | Count |
|---|---|
| Broken links | N |
| Orphan pages | N |
| Missing frontmatter | N |
| Missing tier | N |

(If all zero: "Clean.")

---

## Best practices gap analysis

Compare what the wiki says we SHOULD do vs what we ACTUALLY do.

### New best practices (from recent ingests)

| Entry | Best practice | Our status | Gap? |
|---|---|---|---|
| <recently ingested entry> | <what it recommends> | <what we do> | YES/NO |
...

(If no new best practices found in recent ingests: "No new best practices identified since last report.")

### Drift (things we built but aren't using)

| Component | Wiki says | Actual state | Action |
|---|---|---|---|
| <component> | "Built and working" | <real state> | Update docs or fix the component |
...

(If no drift: "All documented components match actual state.")

### Upgrades available (better approaches documented)

| Current approach | Better approach (from wiki) | Source entry | Worth switching? |
|---|---|---|---|
| <what we do now> | <what the wiki suggests> | <entry> | Assessment |
...

(If no upgrades: "Current approaches are aligned with wiki recommendations.")

### Automation checklist vs reality

| # | Component | Documented status | Actual status | Match? |
|---|---|---|---|---|
| 1 | Feeds config | ✅ | <verify> | |
| 2 | Discovery | ✅ | <verify> | |
| 3 | Ingestion | ✅ | <verify> | |
| ... | ... | ... | ... | |

Only show rows where documented ≠ actual.

---

## Recommendations

Based on the data above, suggest 3-5 concrete next actions:

1. **[Priority action]** — e.g., "8 items in pending queue — run `/wiki-list process` to drain"
2. **[Stale entry]** — e.g., "3 entries past review_after — re-check against current sources"
3. **[Gap]** — e.g., "A2A protocol gap (P3) has a candidate in discovered/ — ingest it"
4. **[Discovery]** — e.g., "No discovery run in 7 days — run `/wiki-discover`"
5. **[Claims]** — e.g., "No claims index exists — run `/wiki-claims` to build baseline"

---

## Numbers

| Metric | Value |
|---|---|
| Total entries | N |
| By folder | active: N, long-term: N, orchestration: N, tooling: N, implementation: N |
| Open concept gaps | N |
| Pending ingestion | N |
| Staged (proposed) | N |
| Stale (past review_after) | N |
| Last discovery run | <date or "never"> |
| Last semantic lint | <date or "never"> |
| Last claims extraction | <date or "never"> |
```

### Step 3 — Show the user

Print the report inline (not just a file path). The morning report is meant to be READ, not filed and forgotten. Show it directly, then mention where the file is saved.

If `--brief`, just show the Numbers table and Recommendations — skip the details.

## After running

- Tell the user the 3-5 recommendations
- Offer to act on any of them: "Want me to drain the pending queue? Run discovery? Fix stale entries?"
- Don't auto-act — this is a review checkpoint, not an automation trigger

## Integration with the research cycle

This skill implements **Phase 8 (Human review #2)** of the research cycle. It's the batch summary that replaces per-item approval. The user reads one report, gives direction, and the system acts.

```
... → semantic lint → claims → /wiki-report → human reviews → next cycle
                                  Phase 8         Phase 8
```

## Key paths

- Reports: `llm-wiki/wiki/_inbox/reports/`
- Lint report: `llm-wiki/wiki/_inbox/reports/lint-report.md`
- Claims report: `llm-wiki/wiki/_inbox/reports/claims-report-*.md`
- Claims index: `llm-wiki/wiki/_inbox/claims-index.json`
- Concept gaps: `llm-wiki/wiki/concept-gaps-things-mentioned-not-yet-covered.md`

## Don't

- Don't modify any wiki files — this is read-only
- Don't run semantic lint as part of the report (too expensive) — reference the latest existing report
- Don't generate the report silently and just save the file — SHOW it to the user
- Don't suggest more than 5 actions — the report should be a 5-minute review, not a backlog dump
