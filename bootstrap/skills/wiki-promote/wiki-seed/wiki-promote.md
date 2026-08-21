---
title: "wiki-promote — skill"
type: how-to
artifact: skill
name: wiki-promote
installed_by: install-wiki
date: 2026-07-31
---

# wiki-promote — skill

Moves staged entries out of the holding area and into the live wiki. Staged ingestion writes new entries to `_inbox/proposed/` rather than publishing them directly, so nothing lands in the wiki until a human has looked at it. This skill is that review gate: it shows you what is waiting, takes your approve or reject decision per entry, then does the mechanical work of filing, cross-linking, and re-indexing.

**Trigger:** */wiki-promote* — also "promote", "approve wiki entries", "what's in proposed", "move proposed to wiki". Accepts `all`, a specific filename, or `--review` to see each entry's TL;DR and Related section before deciding.

**Input / Output:** Consumes the `.md` entries in `_inbox/proposed/` together with their `<slug>.proposed_metadata.json` sidecars, which carry the target folder and the suggested backlinks. Produces the entry moved into `wiki/<target_folder>/` with `status: proposed` stripped from its frontmatter, backlinks written into the related entries, cross-links resolved to real relative paths, the sidecar deleted, and the wiki INDEX regenerated. Rejected entries move to `_inbox/rejected/` — kept for the audit trail, never deleted.

**Works with:** [`wiki-update`](./wiki-update.md) stages the entries this skill later approves, and [`wiki-cycle`](./wiki-cycle.md) invokes it as a step in a full run. [`wiki-lint`](./wiki-lint.md) is re-run afterwards to confirm the promotion left zero broken links, and [`wiki-report`](./wiki-report.md) counts what is still sitting in `_inbox/proposed/`. The optional `--verify` flag hands each promoted entry to [`wiki-verify`](./wiki-verify.md).

**Note:** Most entries should *not* be auto-verified at promote time — verification is a deliberate later step. Only pass `--verify` when whoever is reviewing the promotion can personally vouch for the entry's claims.
