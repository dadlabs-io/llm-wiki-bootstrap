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

**Trigger:** */wiki-promote* — also "promote", "approve wiki entries", "what's in proposed", "move proposed to wiki". Accepts `all`, a specific entry, or `--review`, which shows each entry and asks promote / reject / skip (the agent adds the entry's TL;DR and Related section).

**Input / Output:** Consumes the `.md` entries in `_inbox/proposed/` (`_inbox/` sits beside `wiki/` at the notebook root) together with their `<slug>.proposed_metadata.json` sidecars, which carry the target folder and the suggested backlinks. Produces:

- the entry moved into `wiki/<target_folder>/`, with `status: proposed` stripped from its frontmatter and its links rewritten for the new folder; a link normalizer then resolves links written by bare file name
- a backlink added to the Related section of each suggested entry. A suggestion that points into a framework-contract doc is skipped with a warning, because the docs refresh would overwrite it.
- the sidecar deleted, and a truth-status record started for the entry as unverified (the record [`wiki-verify`](./wiki-verify.md) later changes)
- every page a promoted entry links to naming it back in its auto-maintained backlinks block, so a new entry is never left an orphan (the whole notebook's blocks are rebuilt, so a notebook whose blocks were behind catches up)
- the folder indexes and the wiki MAP regenerated

A bare or singular folder name is mapped to its full taxonomy folder. A notebook's own folder (one the framework doesn't list, such as `research/agents` or `research/vendors`) counts as known when it has a `README.md` saying what it is for. Any other folder is used as given, with a warning to check the spelling or add the README: a mistyped folder the script creates never gets one, so it keeps warning. Rejected entries move to `_inbox/rejected/` — kept for the audit trail, never deleted.

**Works with:** [`wiki-update`](./wiki-update.md) stages the entries this skill later approves, and [`wiki-cycle`](./wiki-cycle.md) invokes it as a step in a full run. [`wiki-lint`](./wiki-lint.md) is re-run afterwards to confirm the promotion left zero broken links, and [`wiki-report`](./wiki-report.md) counts what is still sitting in `_inbox/proposed/`. The optional `--verify` flag hands each promoted entry to [`wiki-verify`](./wiki-verify.md); a failed verification leaves the entry promoted and unverified.

**When it skips itself:** with nothing staged it says so and stops. An entry whose sidecar is missing, is not valid JSON (or not a JSON object), or names no target folder is held back — it stays in `_inbox/proposed/` with the reason printed and the run exits 4 — rather than being filed at the wiki root without its backlinks. The script's `--check` mode reports such entries without moving anything and exits 1 if there are any; a full cycle runs it right after ingest.

**Note:** Most entries should *not* be auto-verified at promote time — verification is a deliberate later step. Only pass `--verify` when whoever is reviewing the promotion can personally vouch for the entry's claims.
