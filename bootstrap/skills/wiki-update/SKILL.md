---
name: wiki-update
description: "Ingest one EXTERNAL source (a URL, YouTube video, PDF, X post, local file or pasted text) into a wiki as a curated, cross-linked entry, keeping the verbatim original under raw/. Two or more URLs are queued for /wiki-cycle instead. Use when the user says 'add this to the wiki', 'save this article', 'wiki this', 'ingest this video', or hands over a source to file. Not for this session's own work (/wrap-up), and not for draining the queue or 'update the wiki' (/wiki-cycle)."
last_reviewed: 2026-09-14
review_after: 2026-12-14
reviewed_for_model: claude-opus-5
---

# wiki-update

Files one external source as a wiki entry: the verbatim original under `raw/`, and a synthesis in `wiki/<folder>/` that links into what the wiki already holds. Integration is the point; an entry that sits alone is half the value.

This skill does not restate the rules it follows:
- Frontmatter fields, tier and confidence: the frontmatter spec, `<wiki>/project/best-practices/framework/wiki-frontmatter-best-practices.md`.
- Authoring doctrine (claim classes, blockquotes, secondary figures, auto-captions): `wiki-authoring-best-practices.md` in the same folder.
- Structure: `wiki-update.py` refuses to file an entry that fails the gate (step 5).

## What did the user give you?

| Input | Do |
|---|---|
| One URL | The flow below; step 1's fetcher by host is in [fetchers.md](fetchers.md) |
| Two or more URLs (spaces, lines, bullets or a list) | Queue each with `wiki-list-add.py`, then say "queued N items; run `/wiki-cycle --ingest-only` to drain" |
| A local file, or pasted text | The flow from step 2; pasted text goes to a temp file first, passed as `--source` |
| A raw already saved for a URL (a batch hand-over, a browser capture) | The flow from step 2, with no fetcher; file with `--source-url <url> --raw-path raw/<file>` |
| Nothing | Stop: "`/wiki-update` needs a source (a URL, file path or pasted text). To capture what we did this session, run `/wrap-up`." Never synthesize from the session. |

`--now <url>` ingests one item from a list immediately; `--queue <url>` queues even a single URL.

Before starting, settle the notebook and the folder, and confirm them with the user when the source does not make them obvious:
- **Notebook** (`--topic`): this project's by default. Any registered notebook resolves from any folder, so omit `--vault` unless the wiki is a legacy vault outside the registry.
- **Folder** (`--folder`): always the full taxonomy path, `research/<sub>` or `project/<sub>`; list `wiki/` if unsure. A bare leaf is auto-prefixed when it matches one taxonomy folder and refused otherwise; `--allow-new-top-folder` is for a new top-level branch that is really intended.

## Hard rules

- **Read before you reject.** Every queued item is fetched and read in full before any tier, cluster or skip decision. A rejection quotes a passage from the source and names the existing entry it overlaps. No title, URL or domain heuristics: the user curated the list.
- **Numbers and quotes go on `>` lines, attributed to the source.** Inline quotation marks are prose to the gate. Your own synthesis stays plain prose.
- **The search is the full search; there is no fallback.** If the preflight fails, or the search helper exits 75 (GPU busy after retries) or 124 (timed out), stop and report it.
- **Dedup.** `wiki-update.py` skips a source already in `wiki/` or `_inbox/proposed/` (URLs compared normalised). Go past it only when the user says so. A later snapshot of an evolving source (a repo that grew, a new release) is filed with `--revises <slug>`: it records the older entry, refuses if that entry does not exist, and implies `--force`. `internal://` URLs name a session, not a source, and are never treated as duplicates.
- **Before deleting a `raw/` file**, grep for its file name as a `raw_path:` value (`grep -rl "raw_path:.*<file name>" <topic>/wiki/`): another entry may cite it. A raw deleted by mistake comes back with `git show <commit>:<path>`.
- No secrets in an entry, no padding, nothing outside the notebook's scope (its README says what that is).

## The flow

Direct mode, the default: use it unless you were asked for `--staged`. Other skills cite these step numbers (step 5 is the gate).

1. **Fetch the raw.** Ordinary pages: `python {{WIKI_SCRIPTS_DIR}}/wiki-update.py --topic <topic> --source <url> --fetch-only`. YouTube, PDFs, X, Medium and pages rendered by JavaScript: [fetchers.md](fetchers.md). Keep the printed `raw_path=`.
2. **Read the raw in full.** A thin raw, or one that is mostly site navigation, came from the wrong fetcher.
3. **Search the wiki** for 3 to 5 key terms from the source, each with the full search:
   `python {{WIKI_SCRIPTS_DIR}}/wiki-qmd-query.py --notebook <topic> "<term>"`
   Always pass `--notebook`: a cross-link must stay inside the notebook being filed into. It returns 30 results and holds one of three GPU slots; parallel workers add `--caller wiki-ingester`. It needs the CUDA runtime (`--preflight` checks).
4. **Write the synthesis** to `<topic>/_inbox/temp/<slug>.md`:
   - `## TL;DR` that says something the title does not
   - body sections on what matters in the source, and why it is in the wiki
   - Sources, external (the material) apart from internal (our synthesis)
   - `## Related in this wiki`: at least two links, each saying where the source agrees with, extends or contradicts that entry. Link by bare file name (`[Title](<slug>.md)`) and look slugs up with `wiki-update.py --topic <topic> --slug-for --title "<title>" --folder <folder>`; never guess them. It exits 2 and lists near matches when no entry has that title or file name.

   Leave out the Source/Raw footer: the script writes it after your body. Tag a thin entry `stub`.
5. **Eval gate.** The script is the gate. It refuses to file (exit 1, `Refusing to file`) without a `## TL;DR`, without a `## Related` holding two or more wiki links (only a warning for `tier: self`), with anything after the footer but the backlinks block, or with frontmatter that would not parse. It warns on fewer than three tags, an unmarked thin entry, and numbers outside `>` lines. Fix and re-run. `--no-gate '<reason>'` is for an entry a rule is genuinely wrong for, and the reason is what a reviewer reads. Then score the two things a script cannot, 1 to 5 each: **extraction fidelity** (every claim attributed, every number quoted, checked against the raw) and **synthesis value** (it positions the source against what the wiki holds). Print them as one line before filing, `Scores: extraction fidelity N/5, synthesis value N/5`. Below 3, fix it or ask. The score is advisory: you do not certify your own draft.
6. **Pick the existing entries that should link back**: the `inbound_candidates` the script lists, the area's hub page, entries the source speaks to. (Skipped with `--staged`.)
7. **Add the new entry to their Related sections**, acting on every candidate that fits. After five or more ingests into one area, update its hub page too. (Skipped with `--staged`.)
8. **File it.** Tags: three or more, including the source's type when it has one (`youtube` for a video).
   ```bash
   python {{WIKI_SCRIPTS_DIR}}/wiki-update.py --topic <topic> --folder <folder> \
     --source <topic>/_inbox/temp/<slug>.md --source-url <original url> --raw-path <raw_path> \
     --ingested-by claude-code --tier <1|2|3|4|self> --confidence <high|medium|low> \
     --title "<title>" --tags "<tags>"            # add --staged for staged mode
   ```
   It prints `wiki_path=`, `wiki_slug=`, `outbound_fixed=` (links it rewrote), `outbound_warnings=` (links it could not resolve: fix them by hand) and `inbound_candidates=` (step 6's list); a duplicate prints `Skip (dedup)` and `duplicate_of=<path>` instead. Delete the temp files once filing succeeds: the synthesis, and the pasted-text source if you wrote one. For a queued item, move its `.queue` file from `_inbox/pending/` to `_inbox/done/` and re-render the list (`wiki-list-render.py --topic <topic>`).

Tier and confidence are defined only in the frontmatter spec ("tier rubric", "confidence scale"). In short: tier is the source's quality, confidence is our entry's reliability; between two adjacent tiers take the lower; tier 4 never auto-ingests. Our own synthesis is tier `self`, filed with `--no-raw` (no raw copy, no `raw_path`).

## Staged mode (`--staged`)

Only when the user, or the workflow that called this skill (a `/wiki-cycle` ingest worker), asks for `--staged`; never your own choice. It is meant for batches and runs nobody is watching. The entry goes to `_inbox/proposed/` with `status: proposed`, nothing else is edited, and `/wiki-promote` finishes the integration later. Steps 6 and 7 are skipped. `wiki-update.py --staged` writes the sidecar itself.

### Staged-ingest sidecar contract

When you write or edit a sidecar by hand (parallel workers do), follow this exactly; every field has broken a promotion when improvised.

- File name `<slug>.proposed_metadata.json` (the dot form).
- `target_folder`: the full path under `wiki/` (`research/long-term`), never a bare leaf.
- `suggested_backlinks`: objects, never strings, `{"file": "<path under wiki/>", "link_text": "<anchor>", "link_target": "<this entry's bare file name>"}`. At most about eight, each an entry you would cite under Related; never `_MAP.md`, `_INDEX.md`, `HOME.md` or a hub page the entry does not extend.
- Body links by bare file name; the scripts compute the paths.
- Check it: `python {{WIKI_SCRIPTS_DIR}}/wiki-promote.py --topic <topic> --check --slug <slug>`. Exit 0 means it parses and names a folder; promotion holds back an entry that fails. A trailing comma is the usual cause.

```json
{
  "target_folder": "research/long-term",
  "inbound_candidates": ["research/long-term/foo.md"],
  "suggested_backlinks": [
    { "file": "research/long-term/foo.md", "link_text": "Foo (Author)", "link_target": "<slug>.md" }
  ]
}
```

## After running

Tell the user where the entry was filed, the Scores line, any dedup hit and any gate warnings, then stop. Ingest nothing more unless asked.

## Cycle contract

When invoked inside `/wiki-cycle`, this skill writes `<run-folder>/<step>.json` and `<step>.md` per the [Cycle Step Return Format contract](./best-practices/framework/cycle-step-return-format.md).

The incidents behind these rules are recorded in llm-wiki-bootstrap's `CHANGELOG.md` (2026-09-14, "`/wiki-update` trimmed").
