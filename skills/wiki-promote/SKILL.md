---
name: wiki-promote
description: Promote staged wiki entries from _inbox/proposed/ to wiki/. Reviews what's pending, lets the user approve/reject, then moves approved entries to their target folder, adds backlinks, rebuilds the backlink blocks so no new entry is an orphan, regenerates the indexes and map, and re-indexes the search. Use when the user says "promote", "approve wiki entries", "what's in proposed", "wiki-promote", "move proposed to wiki". Not for filing a new source (/wiki-update) or for marking an entry as checked (/wiki-verify).
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

If empty, say "Nothing in staging." and stop.

For each entry found, show:
```
1. <title> (tier N, <date>) — <first line of TL;DR>
2. <title> (tier N, <date>) — <first line of TL;DR>
```

### Step 2 — User decides

If `all`: promote everything, go to Step 3 for each.
If `<filename>`: promote just that one.
If no arg: ask "Promote all, or pick by number?"

Several picked: promote them in one `wiki-promote.py --topic <topic> --auto --slug <a> --slug <b> ...` run, so links, indexes, MAP and the search index are rebuilt once, not once per entry (task #112).

If `--review`: for each entry, show the full TL;DR + Related section before asking approve/reject/skip.

### Step 3 — Promote the approved entries with the script

Promotion is the script's job, never a hand procedure (2026-10-19: the old hand steps here, `mv`, `rm` and `wiki-index.py`, skipped the backlink rebuild, the folder indexes, the map and the re-index the script does):

```bash
uv run --project {{WIKI_SCRIPTS_DIR}} python {{WIKI_SCRIPTS_DIR}}/wiki-promote.py --topic <topic> --auto --slug <a> [--slug <b> ...]   # or --auto alone for all
```

For each entry it reads the sidecar, moves the entry to `wiki/<target_folder>/`, removes `status: proposed`, adds the suggested backlinks to the Related sections of older entries, deletes the sidecar, then once for the run: fixes the moved entries' links, rebuilds the backlink blocks, regenerates the indexes and map, and re-indexes the search. What it reads:

1. **The metadata file** (`<slug>.proposed_metadata.json` — DOT form — next to the entry):
   ```json
   {
     "target_folder": "research/tooling",
     "inbound_candidates": ["file1.md", "file2.md", "..."],
     "suggested_backlinks": [{"file": "research/tooling/other.md", "link_text": "Other (Author)", "link_target": "<slug>.md"}]
   }
   ```
   `target_folder` is the FULL taxonomy path (`research/<sub>` or `project/<sub>`). A notebook's own folder outside the framework's list (agentic-design's `research/agents`) is known when it carries a `README.md` saying what it is for; a folder without one is still promoted, with a warning to check the spelling or add the README (2026-09-24). `suggested_backlinks[]` items are objects (see the staged-ingest sidecar contract in `wiki-update/SKILL.md`). `wiki-promote.py` tolerates legacy/hand-authored variants (underscore filename, bare-string backlinks, bare-leaf `target_folder`) by normalizing them, but new sidecars should conform.

2. **The backlinks** it adds go in each older entry's Related section, above the Source/Raw footer (entry layout: body → footer → auto backlinks block), never as a `## See also` at the end (`add_related_link()` in `_entry_checks.py`). This is the deferred Step 5-6 from `/wiki-update --staged`.

### Step 3.5 — Links after promotion: the script does it, scoped

Ingest agents author cross-links by bare slug (`[Title](other-slug.md)`); they become valid once resolved to `../folder/slug.md`. `wiki-promote.py` runs `wiki-fix-links.py` itself, **scoped to the entries it moved**, then `wiki-reciprocate-backlinks.py`, then the folder indexes and the map. Do not run `wiki-fix-links.py` across the whole notebook after a promotion: unscoped, it rewrites links in entries nobody promoted (2026-09-17, the normaliser finding). To confirm, run `wiki-lint-mechanical.py --topic <topic>`: 0 broken links. The backlink rebuild is what keeps a promoted entry from being an orphan: the entry links out to older ones, and until their `BACKLINKS-AUTO` blocks name it, nothing links to it (until 2026-09-25 only `/wiki-cycle` ran it, so every `/wrap-up` left its new entries orphaned). It rebuilds every block in the notebook and is idempotent, so a notebook whose blocks were behind catches up on its next promotion.

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
- `the checker found problems not yet corrected (report: …)`: the `wiki-checker` read the entry against its transcript and asked for fixes (the sidecar's `checker` field; `--review` prints it). Correct the entry from that report as `/wiki-cycle` Step 2.6 says, then `wiki-cycle-scope.py --topic <topic> checker-corrected --entry <slug>` and re-run. An entry the checker flagged is never promoted as flagged (task #178, 2026-10-22: until then only the cycle's choice of slugs held it).

## Key paths

- Proposed entries: `_inbox/proposed/`
- Rejected entries: `_inbox/rejected/`
- Metadata files: `<slug>.proposed_metadata.json` (DOT form, adjacent to the entry)
- Promote script: `{{WIKI_SCRIPTS_DIR}}/wiki-promote.py` (moves, backlinks, links, indexes, map, re-index)

## Don't

- Don't promote without user approval, unless `all` was explicitly passed or the caller promotes under the notebook's `confirm_before_promote: false` (`/wrap-up` Step 6, `/wiki-cycle` Step 5.5)
- Don't delete rejected entries — move to `_inbox/rejected/`
- Don't skip backlinks — that's the whole point of the two-phase flow
- Don't modify the entry content during promotion (only remove `status: proposed` from frontmatter)
