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

# §9 of icarus-integration-plan: promote-and-verify in one pass for tier-1 entries
# with strong empirical backing. MOST entries should NOT be auto-verified at
# promote time — verification is a deliberate later step. Use this flag only
# when the human reviewing the promote can also vouch for the claims.
/wiki-promote --verify --verify-by human --verify-evidence "<one line>"
/wiki-promote --slug <slug> --auto --verify --verify-by tool --verify-evidence "Aardvark sandbox-verified PoCs"
```

### --verify flag semantics

- Runs `/wiki-verify` on each successfully-promoted entry as a sub-step
- `--verify-by` is `human` by default (editorial signoff); use `agent` for LLM-judge, `tool` for sandbox/static-analyzer
- `--verify-evidence` is the one-line note recorded in the sidecar
- Failures during verify are logged + included in the result JSON but don't roll back the promotion (the entry stays promoted as `unverified`)
- See [wiki-verify SKILL.md](../wiki-verify/SKILL.md) for the per-entry semantics

## What You Must Do When Invoked

### Step 1 — List what's in proposed/

```bash
ls _inbox/proposed/*.md 2>/dev/null | grep -v README
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

1. **Read the metadata file** (`<slug>.proposed_metadata.json` — DOT form — next to the entry):
   ```json
   {
     "target_folder": "research/tooling",
     "inbound_candidates": ["file1.md", "file2.md", "..."],
     "suggested_backlinks": [{"file": "research/tooling/other.md", "link_text": "Other (Author)", "link_target": "<slug>.md"}]
   }
   ```
   `target_folder` is the FULL taxonomy path (`research/<sub>` or `project/<sub>`). `suggested_backlinks[]` items are objects (see the staged-ingest sidecar contract in `wiki-update/SKILL.md`). `wiki-promote.py` tolerates legacy/hand-authored variants (underscore filename, bare-string backlinks, bare-leaf `target_folder`) by normalizing them, but new sidecars should conform.

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
   rm <topic>/_inbox/proposed/<slug>.proposed_metadata.json
   ```

6. **Regenerate INDEX**:
   ```bash
   python {{WIKI_SCRIPTS_DIR}}/wiki-index.py \
     --topic <topic> --vault llm-wiki/wiki
   ```

### Step 3.5 — Normalize links on promoted entries (ALWAYS)

After moving entries into `wiki/`, run the link normalizer:

```bash
python C:/Users/mark/.claude/wiki-scripts/wiki-fix-links.py --topic <topic>
```

Ingest agents author cross-links by BARE slug (`[Title](other-slug.md)`) per the staged-ingest contract. `wiki-promote.py` recomputes the entry's own relative links (raw_path footer + `./`/`../` links) robustly on move, but BARE-slug body links to entries in OTHER folders only become valid once resolved to `../folder/slug.md`. `wiki-fix-links.py` does that resolution deterministically (idempotent; 0-ambiguous/0-missing on a clean run). Skipping it is the recurring "~50 broken links after promote" bug. Then re-run `wiki-lint-mechanical.py` to confirm 0 broken links before reciprocate/index/map.

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
rm <topic>/_inbox/proposed/<slug>.proposed_metadata.json
```

Create `_inbox/rejected/` if it doesn't exist. Rejected entries are kept (not deleted) for audit trail.

## If metadata file is missing

If an entry in `proposed/` has no `<slug>.proposed_metadata.json`, it was probably placed there manually or by an older flow. In this case:
- Ask the user which folder to promote to
- Run a quick qmd search to identify backlink candidates
- Proceed with promotion as normal

## Key paths

- Proposed entries: `_inbox/proposed/`
- Rejected entries: `_inbox/rejected/`
- Metadata files: `<slug>.proposed_metadata.json` (DOT form, adjacent to the entry)
- INDEX script: `{{WIKI_SCRIPTS_DIR}}/wiki-index.py`

## Don't

- Don't promote without user approval (unless `all` was explicitly passed)
- Don't delete rejected entries — move to `_inbox/rejected/`
- Don't skip backlinks — that's the whole point of the two-phase flow
- Don't modify the entry content during promotion (only remove `status: proposed` from frontmatter)
