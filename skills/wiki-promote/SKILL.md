---
name: wiki-promote
description: Promote staged wiki entries from _inbox/proposed/ to wiki/. Reviews what's pending, lets the user approve/reject, then moves approved entries to their target folder, adds backlinks, rebuilds the backlink blocks so no new entry is an orphan, and regenerates the indexes and map. Use when the user says "promote", "approve wiki entries", "what's in proposed", "wiki-promote", "move proposed to wiki".
last_reviewed: 2026-09-25
review_after: 2026-12-24
reviewed_for_model: claude-fable-5-1
---

> **⚙️ Internal skill.** This is invoked by `/wiki-cycle` (the orchestrator) — users normally don't call it directly. Public-facing commands are `/wiki-cycle`, `/wiki-update`, `/wiki-search`, `/wrap-up`, `/wiki-verify`, `/wiki-rollback` and `/new-wiki`. This skill is documented + callable for programmatic use.

> **Wiki resolution (2026-09-08; any-cwd since 2026-09-13).** The scripts resolve the wiki through the registry: `--topic <notebook>` is looked up in `linked-notebooks.json` first, found via the nearest `<cwd>/.claude/wiki-config.json` or, when there is none above the cwd, the machine config `~/.claude/wiki-config.json` (which records `registry` from the first registry-mode `/new-wiki`). So `wiki-promote.py --topic <notebook>` works from any folder. Omit `--vault`; pass it only for a legacy in-project vault that is not in the registry. The `--vault llm-wiki/wiki` examples that used to appear here pointed registry notebooks at a folder that does not exist.

# /wiki-promote

Promote staged entries from `_inbox/proposed/` into the live wiki. This is the second half of the staged ingestion flow — `/wiki-update --staged` files entries here, `/wiki-promote` moves them to `wiki/`.

## Usage

```
/wiki-promote                    # show what's in proposed/, let user pick
/wiki-promote all                # promote everything in proposed/
/wiki-promote <filename>         # promote a specific entry
/wiki-promote --review           # show details of each entry before prompting
wiki-promote.py --topic <topic> --check [--slug <slug>]   # validate staging, move nothing (exit 1 on a problem)

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
   `target_folder` is the FULL taxonomy path (`research/<sub>` or `project/<sub>`). A notebook's own folder outside the framework's list (agentic-design's `research/agents`) is known when it carries a `README.md` saying what it is for; a folder without one is still promoted, with a warning to check the spelling or add the README (2026-09-24). `suggested_backlinks[]` items are objects (see the staged-ingest sidecar contract in `wiki-update/SKILL.md`). `wiki-promote.py` tolerates legacy/hand-authored variants (underscore filename, bare-string backlinks, bare-leaf `target_folder`) by normalizing them, but new sidecars should conform.

2. **Move the entry** from `_inbox/proposed/` to `wiki/<target_folder>/`:
   ```bash
   mv <topic>/_inbox/proposed/<slug>.md <topic>/wiki/<target_folder>/<slug>.md
   ```

3. **Remove `status: proposed`** from frontmatter (edit the moved file).

4. **Add backlinks** to existing entries — use the `suggested_backlinks` from metadata. For each:
   - Read the target file
   - Find the Related section — it sits above the Source/Raw footer (entry layout: body → footer → auto backlinks block)
   - Add the backlink there, never as a `## See also` at the end of the file (`wiki-promote.py` does this through `add_related_link()` in `_entry_checks.py`; until 2026-09-14 it appended See also after the backlinks block)
   - This is the deferred Step 5-6 from `/wiki-update --staged`

5. **Delete the metadata file**:
   ```bash
   rm <topic>/_inbox/proposed/<slug>.proposed_metadata.json
   ```

6. **Regenerate INDEX**:
   ```bash
   python {{WIKI_SCRIPTS_DIR}}/wiki-index.py \
     --topic <topic>
   ```

### Step 3.5 — Normalize links on promoted entries (ALWAYS)

After moving entries into `wiki/`, run the link normalizer:

```bash
python {{WIKI_SCRIPTS_DIR}}/wiki-fix-links.py --topic <topic>
```

Ingest agents author cross-links by BARE slug (`[Title](other-slug.md)`) per the staged-ingest contract. `wiki-promote.py` recomputes the entry's own relative links (raw_path footer + `./`/`../` links) robustly on move, but BARE-slug body links to entries in OTHER folders only become valid once resolved to `../folder/slug.md`. `wiki-fix-links.py` does that resolution deterministically (idempotent; 0-ambiguous/0-missing on a clean run). Skipping it is the recurring "~50 broken links after promote" bug. Then re-run `wiki-lint-mechanical.py` to confirm 0 broken links before reciprocate/index/map.

`wiki-promote.py` runs all of this itself after a promotion, in order: `wiki-fix-links.py` (scoped to the entries it moved), then `wiki-reciprocate-backlinks.py`, then the folder indexes and the map. The backlink rebuild is what keeps a promoted entry from being an orphan: the entry links out to older ones, and until their `BACKLINKS-AUTO` blocks name it, nothing links to it (until 2026-09-25 only `/wiki-cycle` ran it, so every `/wrap-up` left its new entries orphaned). It rebuilds every block in the notebook and is idempotent, so a notebook whose blocks were behind catches up on its next promotion.

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

## If the metadata file is missing, broken, or names no folder

`wiki-promote.py` holds such an entry back instead of promoting it: it stays in `_inbox/proposed/`, the reason is printed (`HELD … no sidecar` / `sidecar is not valid JSON (…)` / `sidecar names no target_folder`), and the run exits 4. Promoting it would drop it at the wiki root with no backlinks — which, until 2026-09-14, is what happened after a one-line warning. `--check` finds these without moving anything; `/wiki-cycle` runs it after ingest so a bad hand-edited sidecar is caught before review.

To release a held entry:
- Broken JSON: fix the file (a trailing comma after the last list item is the usual cause) and re-run.
- Missing sidecar or no folder: ask the user which folder it belongs in, run a quick qmd search for backlink candidates, write or complete `<slug>.proposed_metadata.json` per the sidecar contract in `wiki-update/SKILL.md`, then re-run.

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
