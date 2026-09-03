---
name: wiki-rollback
description: Roll back a wiki entry to its verified ancestor. Walks the `revises:` chain backward, marks intermediates `verified: rolled_back` in their sidecars (no frontmatter mutation, no content deletion), then writes a new `type: rollback` entry documenting what was rolled back and why. Use when the user says "rollback the X entry", "wiki-rollback", "this entry is wrong, restore the previous version", "/wiki-rollback".
last_reviewed: 2026-09-02
review_after: 2026-12-02
reviewed_for_model: claude-fable-5-1
---

> **🛠️ Public-facing skill.** Invoked by the user directly when an entry is found to be wrong and needs to be reverted to the last verified state. The rollback is non-destructive — rolled-back entries stay on disk and remain searchable with `--include-rolled-back` (audit view).

# /wiki-rollback

First-class rollback primitive per [icarus-integration-plan.md §4](../topic-template/wiki/best-practices/framework/icarus-integration-plan.md). Restores the verified state of an entry by walking its `revises:` chain backward, marking intermediates as rolled_back, and writing a new audit entry.

## Usage

```
/wiki-rollback <slug> --reason "<why>" [--topic <topic>]
/wiki-rollback wiki/active/foo-2026.md --reason "..."
/wiki-rollback foo-2026 --reason "..." --topic agentic-design

# Optional refinement (cycle 2026-05-24-01 / Oblivion cluster-decay):
/wiki-rollback <slug> --reason "..." --cluster-walk    # also flag sibling entries for human review

# Dry-run:
/wiki-rollback <slug> --reason "..." --dry-run
```

## Hard rules

1. **No verified ancestor → rollback refused.** If the chain has no `verified: verified` ancestor, the script exits 1 with an explicit error. We do NOT guess where to stop.
2. **No frontmatter mutation on intermediates.** The rolled-back entries' frontmatter is untouched; only their sidecar `verified` flips to `rolled_back`. This keeps git history clean — sidecars are designed for telemetry-class writes.
3. **No content deletion, ever.** Rolled-back entries stay on disk. Default retrieval excludes them. `wiki-search-rerank.py --include-rolled-back` surfaces them on demand.
4. **`--reason` is required.** The new rollback entry's body cites your reason. Don't ship rollbacks without an explanation.

## What You Must Do When Invoked

### Step 1 — Resolve the target

The user gives you a slug, a relative path, or a full path. Use the script's resolver (it handles all three). If the slug matches multiple files in `wiki/`, error out with the candidate list — the user must disambiguate.

### Step 2 — Run the script

```bash
python {{WIKI_SCRIPTS_DIR}}/wiki-rollback.py "<slug>" \
    --reason "<reason>" \
    --topic "<topic>" \
    [--cluster-walk] \
    [--dry-run]
```

The script:
1. Walks `revises:` backward from the target
2. Finds the first ancestor with `verified: verified` (frontmatter wins, sidecar fallback)
3. Marks every intermediate entry's sidecar with `verified: rolled_back` + `rolled_back_at` ISO timestamp
4. Writes a new entry next to the verified ancestor: `rollback-to-<ancestor-slug>-<date>-<short-hex>.md` with `type: rollback`, `revises: <ancestor>`, and a body that lists what was rolled back + the user's reason

### Step 3 — Report to the user

The script emits a JSON summary on stdout:

```json
{
  "status": "completed",
  "target": "wiki/active/foo-2026.md",
  "verified_ancestor": "wiki/active/foo-original-2026.md",
  "rolled_back": ["wiki/active/foo-revision-2026.md", "wiki/active/foo-2026.md"],
  "new_rollback_entry": "wiki/active/rollback-to-foo-original-2026-...-abc123.md",
  "cluster_walk_siblings": [],
  "timestamp": "..."
}
```

Show the user:
- Which ancestor was restored
- How many intermediate entries got marked rolled_back
- Where the new rollback entry lives
- If `--cluster-walk` was used: the sibling-entries list (these need a separate human review pass — the script does NOT auto-roll-back siblings)

### Step 4 — If the script exits 1 (no verified ancestor)

Don't retry. Tell the user:
- The chain has no `verified: verified` ancestor — rollback would corrupt the lineage
- To proceed: verify an ancestor first via `/wiki-verify <ancestor-slug>`, then re-run rollback
- Show the chain the script discovered so the user can see where to verify

### Step 5 — Post-rollback hygiene (do automatically)

After a successful rollback, run the integration scripts so the rollback entry is indexed + cross-linked:

```bash
python {{WIKI_SCRIPTS_DIR}}/wiki-reciprocate-backlinks.py --topic <topic> --vault <vault>
python {{WIKI_SCRIPTS_DIR}}/wiki-index-per-folder.py --topic <topic> --vault <vault>
python {{WIKI_SCRIPTS_DIR}}/wiki-map-compile.py --topic <topic> --vault <vault>
```

### Step 6 — Commit

One commit per rollback. Message format:

```
wiki: rollback <target-slug> to <verified-ancestor-slug>

Reason: <user's --reason text>

Marked N intermediate entries as verified=rolled_back via sidecar updates
(no frontmatter mutation, no content deletion). Default retrieval now
excludes the rolled-back chain; --include-rolled-back surfaces them.

New entry: <path-to-rollback-entry>
```

## Don't

- Don't auto-roll-back siblings even when `--cluster-walk` flags them — that mode is review-only by design (Oblivion's cluster-decay argues for *attention*, not auto-action)
- Don't skip the `--reason` field — every rollback needs traceable justification
- Don't mutate frontmatter on intermediates — sidecar-only by design (keeps git clean)
- Don't delete the rolled-back entries or their raw archives in `raw/`
- Don't re-run rollback on an already-rolled-back chain — check the sidecar first; if all intermediates already say `verified: rolled_back`, the rollback was already done

## Related

- [icarus-integration-plan.md §4](../topic-template/wiki/best-practices/framework/icarus-integration-plan.md)
- [memory-signals-sidecar-vs-frontmatter-pattern.md](../topic-template/wiki/best-practices/framework/memory-signals-sidecar-vs-frontmatter-pattern.md) — sidecar truth-status block this updates
- [wiki-verify SKILL.md](../wiki-verify/SKILL.md) — the verify side; needed to create verified ancestors before rollback works
- [wiki-search-bucket-rerank-spec.md](../topic-template/wiki/best-practices/framework/wiki-search-bucket-rerank-spec.md) — `--include-rolled-back` audit flag on the search side
