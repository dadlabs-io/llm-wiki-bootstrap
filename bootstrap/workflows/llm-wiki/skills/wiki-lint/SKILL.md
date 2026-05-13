---
name: wiki-lint
description: Run a health check on a topic wiki. Two modes — default is the fast mechanical pass (broken links, orphans, stale phrases, missing frontmatter, missing tiers). --full mode adds a semantic pass where the agent reads every entry, finds contradictions, missing cross-references, thin coverage, concept gaps, and tier accuracy, then writes a report. Use when the user says "lint the wiki", "wiki-lint", "wiki health check", "full wiki lint", "wiki-lint --full", "find missing connections in the wiki", "check the wiki for issues", "semantic lint".
---

> **⚙️ Internal skill.** This is invoked by `/wiki-cycle` (the orchestrator) — users normally don't call it directly. Public-facing commands are `/wiki-cycle`, `/wiki-update`, `/wiki-search`, `/wiki-init`. This skill is documented + callable for programmatic use.

Two modes. Pick the right one based on what the user asked for.

## Mode 1 — Mechanical lint (default)

When the user says: `lint the wiki`, `/wiki-lint`, `quick wiki check`, `wiki health`.

Pure Python script. Fast, deterministic, no LLM in the loop. Reports only — never modifies files.

```bash
python .claude/wiki-scripts/wiki-lint-mechanical.py \
  --topic <topic> \
  --vault llm-wiki/wiki
```

Checks:
- Broken markdown links (to `.md` files that don't exist)
- Orphan pages (no inbound links from other entries)
- Stale "pending" / "TODO" phrases
- Missing frontmatter fields (`title`, `date`)
- Missing or invalid `tier` values (must be `1`, `2`, `3`, `4`, or `self`)

Output: report printed to stdout + saved at `<topic>/_inbox/lint-report.md`.

After running: show the user the summary counts. Don't auto-fix.

## Mode 2 — Full semantic lint (`--full`)

When the user says: `full wiki lint`, `wiki-lint --full`, `do a full lint`, `semantic lint`, `find missing connections`, `find contradictions`.

This mode runs the mechanical script first, then YOU do a full semantic review of every entry.

### Step 1: Mechanical pass

Run `wiki-lint-mechanical.py` as in Mode 1. Capture the baseline.

### Step 1.5: Load drift-watch list

Read `<topic>/_config/drift-watch.md` if it exists. This file lists high-drift-risk entries (self-authored docs, system overviews, vision targets, implementation plans) that need an explicit deep-compare against named canon sources every full lint pass — generic semantic lint isn't enough for these.

For each entry on the drift-watch list:
- Note its canon source(s) and "what to deep-compare" guidance.
- Plan to do the deep-compare in Step 3.5 (separate from the standard 6 criteria).

If the file doesn't exist, skip this step. Topic owners can choose whether to maintain a drift-watch list.

### Step 2: Read ALL files first

Read every `.md` file in `<topic>/wiki/` (excluding _INDEX.md) using the Read tool. **Read them all before writing any findings.** This gives you full context for cross-reference and contradiction detection — you can't judge if something is missing a link unless you know what pages exist.

For drift-watch entries (from Step 1.5), also read the named canon source(s) — these are typically `.claude/skills/<skill>/SKILL.md` files outside the wiki, or other internal docs.

### Step 3: Evaluate each file against 6 criteria

For each file, evaluate:

| # | Criterion | What to look for |
|---|---|---|
| 1 | **CONTRADICTIONS** | Does this entry make a claim that contradicts a claim in another entry? Cite both entries and the specific conflicting text. Include stale data (entry counts, "not yet built" claims that are now built, etc.) |
| 2 | **MISSING CROSS-REFERENCES** | Does this entry mention a topic that has its own dedicated page in the wiki but doesn't link to it? List each missing link with the target page. |
| 3 | **THIN COVERAGE** | Are there sections that feel under-supported relative to peer entries on similar topics? Is the entry's depth appropriate for its tier and importance? |
| 4 | **CONCEPT GAPS** | Does this entry mention a project, person, framework, or paper that should be tracked in `concept-gaps-things-mentioned-not-yet-covered.md` but isn't? List the term and where it's mentioned. |
| 5 | **TIER REVIEW** | Is the assigned `tier` value in frontmatter defensible? Flag any you'd assign differently and explain why. Tier definitions: 1=peer-reviewed/primary, 2=vendor/official docs, 3=expert/first-hand, 4=community/blog, self=our own synthesis. |
| 6 | **OTHER** | Anything else — broken external links, emoji inconsistency, stale tooling references, formatting issues. |

### Step 3.5: Deep-compare drift-watch entries

For each entry on the drift-watch list (from Step 1.5):

- Read the entry alongside its named canon source(s).
- Look for specific drift in the areas the drift-watch list flags ("what to deep-compare" column).
- Examples of drift: phase numbering changed in SKILL.md but entry still cites old count; entry says feature X is "not built" but commit history shows it's shipped; canon source has a new mode flag the entry doesn't mention.
- Flag findings under a dedicated **DRIFT-WATCH** section in the report (separate from the 6 standard criteria), with severity: high (breaks reader's mental model) / medium (factually incorrect but recoverable) / low (cosmetic).

If a drift-watch entry passes deep-compare cleanly, log it as "no drift detected" — this is the audit trail.

**If a wiki entry is found to be stale that *wasn't* on the drift-watch list**: flag it in OTHER, and recommend adding it to `_config/drift-watch.md` so future cycles catch it. The list grows organically through these discoveries.

### Step 4: Write the report

Save findings to: `<topic>/_inbox/<agent>-semantic-lint-<date>.md`

Use `claude-semantic-lint-YYYY-MM-DD.md` when run from Claude Code.

Format:
```markdown
# Semantic Lint Report — <topic>

**Generated**: <date>
**Agent**: <model name>
**Files reviewed**: <count>

---

## Progress table

| # | File | Status |
|---|---|---|
| 1 | `path/to/file.md` | reviewed |
...

---

## DRIFT-WATCH FINDINGS

(Only present when `_config/drift-watch.md` exists.)

### <entry-name>

**Canon source**: <path>
**Drift detected**: yes / no / partial
**Specific mismatches**:
- <line/section in entry> claims X; <canon location> says Y
- (etc.)
**Severity**: high / medium / low
**Suggested fix**: edit-in-place / re-synthesize / defer-for-promote-review

---

## 1. <filename>

### CONTRADICTIONS
<findings or "None found.">

### MISSING CROSS-REFERENCES
<findings or "None.">

### THIN COVERAGE
<findings or "Adequate.">

### CONCEPT GAPS
<findings or "None new.">

### TIER REVIEW
<assessment>

### OTHER
<findings or "None.">

---
## 2. <next file>
...

## Cross-cutting issues
<patterns that appear across multiple files>

## Highest-priority fixes
<numbered list, most impactful first>
```

### Step 5: Present summary to user

After writing the report, show the user:
- Total files reviewed
- Count of contradictions, missing cross-refs, concept gaps, tier issues
- Top 5 highest-priority fixes
- Path to the full report

**Do NOT auto-apply fixes.** The user reviews and decides. If they approve fixes, apply them, then re-run the mechanical lint (Step 6) to verify.

### Step 6: Mechanical re-run (if fixes were applied)

After applying approved fixes, run `wiki-lint-mechanical.py` again to verify:
- No new broken links introduced
- No new orphans
- Previous issues are resolved

## Decision tree

| User says | Mode |
|---|---|
| "lint the wiki" | Mode 1 (mechanical) |
| "wiki health check" | Mode 1 |
| "full lint" / "semantic lint" / "find contradictions" / "find missing connections" | Mode 2 |
| "wiki-lint --full" | Mode 2 |
| Ambiguous | Ask: "mechanical (fast, just reports) or full (reads every file, finds contradictions + gaps)?" |

## Don't

- Don't run Mode 2 by default — it reads every file, costs tokens, takes minutes
- Don't auto-apply semantic fixes without user approval
- Don't skip reading ALL files before evaluating — partial reads miss cross-reference gaps
- Don't read the existing semantic lint reports before writing your own — independent evaluation

## Key paths

- Mechanical script: `.claude/wiki-scripts/wiki-lint-mechanical.py`
- Mechanical report: `<vault>/<topic>/_inbox/lint-report.md`
- Semantic report: `<vault>/<topic>/_inbox/<agent>-semantic-lint-<date>.md`


## Cycle contract

When invoked inside `/wiki-cycle`, this skill writes `<run-folder>/<step>.json` and `<step>.md` per the [Cycle Step Return Format contract](./best-practices/framework/cycle-step-return-format.md) — that doc defines the shape, counters, and queued/skipped/deferred semantics for this step.
