---
title: "wiki-verify — skill"
type: how-to
artifact: skill
name: wiki-verify
installed_by: install-wiki
date: 2026-07-31
---

# wiki-verify — skill

Marks a wiki entry as verified, recording who certified it, when, and on what basis. Everything ingested into the wiki starts out unverified; this is the only way an entry becomes verified, and that separation is the point — an entry cannot be both the author and the certifier of its own claims, so certification is a distinct, auditable act. The certification is written to a sidecar file rather than the entry itself, which keeps the entry's git history free of metadata churn.

**Trigger:** */wiki-verify*, or natural phrasings like "verify this entry", "mark X as verified". Pass `--by human` (the default, meaning editorial signoff), `--by agent` for an LLM judge, or `--by tool` for a sandbox, test, or static-analyzer signal, plus an optional one-line `--evidence` note. `--dry-run` previews; `--mirror` also writes the field into the entry's frontmatter.

**Input / Output:** Takes an entry slug or path and a topic. Writes the truth-status block to the entry's sidecar at `_signals/<slug>.json` — `verified: verified`, a timestamp, the certifier, and any evidence — and prints a JSON summary naming the target, certifier, timestamp, evidence, and sidecar path. With `--mirror`, the entry file itself is edited too, which then calls for re-running the backlink integration script.

**Works with:** [`wiki-rollback`](./wiki-rollback.md) is the other half of the truth-status lifecycle and depends on this one entirely — rollback walks backward looking for a verified ancestor, so without a prior verification it has no anchor to restore to and refuses. Entries created by [`wiki-update`](./wiki-update.md) arrive unverified by default, and [`wiki-lint`](./wiki-lint.md) in strict mode rejects any entry whose initial frontmatter claims to be verified.

**Note:** Contradicted or rolled-back entries cannot be force-verified. The path back is to review the conflict, write a new entry that revises the old one, and verify that new entry instead.
