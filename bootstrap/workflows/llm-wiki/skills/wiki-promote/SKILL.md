---
name: wiki-promote
description: Promote staged wiki entries from _inbox/proposed/ to wiki/. Reviews what's pending, lets the user approve/reject, then moves approved entries to their target folder, adds backlinks, and regenerates INDEX. Use when the user says "promote", "approve wiki entries", "what's in proposed", "wiki-promote", "move proposed to wiki".
---

> **⚙️ Internal skill.** This is invoked by `/wiki-cycle` (the orchestrator) — users normally don't call it directly. Public-facing commands are `/wiki-cycle`, `/wiki-update`, `/wiki-search`, `/wiki-init`. This skill is documented + callable for programmatic use.

# /wiki-promote

Promote staged entries from `_inbox/proposed/` into the live wiki. This is the second half of the staged ingestion flow — `/wiki-update --staged` files entries here, `/wiki-promote` moves them to `wiki/`.

## Usage

```
/wiki-promote                    # show what's in proposed/, let user pick
/wiki-promote all                # promote everything in proposed/
/wiki-promote <filename>         # promote a specific entry
/wiki-promote --review           # show details of each entry before prompting
```

## What You Must Do When Invoked

### Step 1 — List what's in proposed/

```bash
ls docker/shared/openclaw/vault/wikis/<topic>/_inbox/proposed/*.md 2>/dev/null | grep -v README
```

If empty, say "Nothing in staging — all entries are going direct to wiki." and stop.

For each entry found, show:
```
1. <title> (tier N, <date>) — <first line of TL;DR>
2. <title> (tier N, <date>) — <first line of TL;DR>
```

### Step 2 — User decides

If `all`: promote everything, go to Step 3 for each.
If `<filename>`: promote just that one.
If no arg: ask "Promote all, or pick by number?"

If `--review`: for each entry, show the full TL;DR + Related section before asking approve/reject/skip.

### Step 3 — Promote each approved entry

For each entry to promote:

1. **Read the metadata file** (`_proposed_metadata.json` next to the entry):
   ```json
   {
     "target_folder": "tooling",
     "inbound_candidates": ["file1.md", "file2.md", ...],
     "suggested_backlinks": [{"file": "...", "link_text": "..."}]
   }
   ```

2. **Move the entry** from `_inbox/proposed/` to `wiki/<target_folder>/`:
   ```bash
   mv <topic>/_inbox/proposed/<slug>.md <topic>/wiki/<target_folder>/<slug>.md
   ```

3. **Remove `status: proposed`** from frontmatter (edit the moved file).

4. **Add backlinks** to existing entries — use the `suggested_backlinks` from metadata. For each:
   - Read the target file
   - Find the Related section
   - Add the backlink
   - This is the deferred Step 5-6 from `/wiki-update --staged`

5. **Delete the metadata file**:
   ```bash
   rm <topic>/_inbox/proposed/<slug>_proposed_metadata.json
   ```

6. **Regenerate INDEX**:
   ```bash
   python bootstrap/docker-setup/openclaw/agents-training/main/skills/research-wiki/wiki-index.py \
     --topic <topic> --vault docker/shared/openclaw/vault/wikis
   ```

### Step 4 — Report

```
Promoted N entries:
  - <title> → wiki/<folder>/<slug>.md (N backlinks added)
  - <title> → wiki/<folder>/<slug>.md (N backlinks added)

Remaining in proposed/: N
```

### Step 5 — Reject (if user rejects an entry)

If the user says "reject" or "delete" for an entry:

```bash
mv <topic>/_inbox/proposed/<slug>.md <topic>/_inbox/rejected/<slug>.md
rm <topic>/_inbox/proposed/<slug>_proposed_metadata.json
```

Create `_inbox/rejected/` if it doesn't exist. Rejected entries are kept (not deleted) for audit trail.

## If metadata file is missing

If an entry in `proposed/` has no `_proposed_metadata.json`, it was probably placed there manually or by an older flow. In this case:
- Ask the user which folder to promote to
- Run a quick qmd search to identify backlink candidates
- Proceed with promotion as normal

## Key paths

- Proposed entries: `docker/shared/openclaw/vault/wikis/<topic>/_inbox/proposed/`
- Rejected entries: `docker/shared/openclaw/vault/wikis/<topic>/_inbox/rejected/`
- Metadata files: `<slug>_proposed_metadata.json` (adjacent to the entry)
- INDEX script: `bootstrap/docker-setup/openclaw/agents-training/main/skills/research-wiki/wiki-index.py`

## Don't

- Don't promote without user approval (unless `all` was explicitly passed)
- Don't delete rejected entries — move to `_inbox/rejected/`
- Don't skip backlinks — that's the whole point of the two-phase flow
- Don't modify the entry content during promotion (only remove `status: proposed` from frontmatter)
