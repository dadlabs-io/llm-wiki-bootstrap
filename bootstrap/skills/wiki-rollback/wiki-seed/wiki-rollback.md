---
title: "wiki-rollback — skill"
type: how-to
artifact: skill
name: wiki-rollback
installed_by: install-wiki
date: 2026-07-31
---

# wiki-rollback — skill

Reverts a wiki entry to the last state you actually trusted. It follows the entry's `revises:` chain backward until it finds a verified ancestor, marks every entry in between as rolled back, and writes a new audit entry explaining what was reverted and why. Nothing is deleted — rolled-back entries stay on disk and remain findable in an audit view — so this is a change of status rather than a destructive undo.

**Trigger:** */wiki-rollback*, or natural phrasings like "roll back the X entry", "this entry is wrong, restore the previous version". A `--reason` is required; `--dry-run` previews the walk, and `--cluster-walk` additionally flags sibling entries for your attention.

**Input / Output:** Takes a slug, relative path, or full path (ambiguous slugs error out with the candidate list). Flips `verified: rolled_back` plus a timestamp in each intermediate entry's sidecar, leaving frontmatter and content untouched. Creates a new `type: rollback` entry beside the verified ancestor listing what was rolled back and citing your reason, then re-runs the backlink, index, and map scripts so it is cross-linked. Prints a JSON summary naming the restored ancestor, the rolled-back entries, and the new entry's path.

**Works with:** [`wiki-verify`](./wiki-verify.md) is a hard prerequisite — if the chain contains no verified ancestor the rollback is refused outright rather than guessing where to stop, and the fix is to verify an ancestor first and re-run. [`wiki-search`](./wiki-search.md) hides rolled-back entries from normal results but can surface them on demand with its include-rolled-back flag.

**Note:** `--cluster-walk` is review-only by design. Flagged siblings are never rolled back automatically; the intent is to draw your attention to entries that may share the same flaw, not to act on them.
