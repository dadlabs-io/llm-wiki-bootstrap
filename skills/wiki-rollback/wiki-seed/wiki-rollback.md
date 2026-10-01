---
title: "wiki-rollback — skill"
type: how-to
artifact: skill
name: wiki-rollback
installed_by: install-wiki
date: 2026-07-31
---

# wiki-rollback — skill

Reverts a wiki entry to the last state you actually trusted. It follows the entry's `revises:` chain backward until it finds a verified ancestor, marks the target and every entry between it and that ancestor as rolled back, and writes a new audit entry explaining what was reverted and why. Nothing is deleted — rolled-back entries stay on disk — so this is a change of status rather than a destructive undo.

**Trigger:** */wiki-rollback*, or natural phrasings like "roll back the X entry", "this entry is wrong, restore the previous version". A `--reason` is required; `--dry-run` previews the walk, and `--cluster-walk` additionally flags sibling entries for your attention.

**Input / Output:** Takes a slug, relative path, or full path, plus the notebook (`--topic`). Sets `verified: rolled_back` plus a timestamp in the truth-status sidecar of the target and of each entry between it and the ancestor, leaving their frontmatter and content untouched. Creates a new `type: rollback` entry beside the verified ancestor — tier `self`, unverified, with `revises:` pointing at the ancestor — that lists what was rolled back and cites your reason. It then re-runs the backlink, index, and map scripts so the new entry is cross-linked, and makes one commit for the rollback. Prints a JSON summary naming the restored ancestor, the rolled-back entries, and the new entry's path.

**When it skips itself:** a slug that matches no entry or several (the candidates are listed), or a `revises:` chain that loops, stops the run (exit 2) before anything is written. A chain whose entries are already marked rolled back has been rolled back once; don't run it again.

**Works with:** [`wiki-verify`](./wiki-verify.md) is a hard prerequisite — if the chain contains no verified ancestor the rollback is refused outright (exit 1) rather than guessing where to stop, and the fix is to verify an ancestor first and re-run. [`wiki-search`](./wiki-search.md)'s optional truth-status rerank drops rolled-back entries unless you pass `--include-rolled-back`; the plain search, the INDEX and the MAP still list them.

**Note:** `--cluster-walk` is review-only by design. It lists every other entry in the rolled-back entries' folders and never rolls them back; the intent is to draw your attention to entries that may share the same flaw, not to act on them.
