---
name: wiki-cycle
description: Run the full research cycle — discover, triage, ingest, check, lint, fix, report. Maintains a scratchpad so the run can be resumed if interrupted. This is the "update the wiki" command. Use when the user says "update the database", "run the cycle", "wiki-cycle", "update the wiki", "full wiki update".
last_reviewed: 2026-09-24
review_after: 2026-12-24
reviewed_for_model: claude-opus-5-5
---

# /wiki-cycle

Runs a notebook's research cycle end to end: gather new sources, give each an owner, ingest this session's share, check the long transcripts, lint, fix, report, commit. Every step writes its result to the run folder, and a scratchpad there lets an interrupted run resume. [reference.md](./reference.md), beside this file, holds the scratchpad template and the detail some steps point to; read it when a step says so.

This is the universal interface: the other `wiki-*` skills (discover, triage, lint, claims, refresh, report, list, promote) are its steps. Public commands: `/wiki-cycle`, `/wiki-update`, `/wiki-search`, `/wrap-up`, `/wiki-verify`, `/wiki-rollback`, `/new-wiki`.

## Modes and what each runs

```
/wiki-cycle                     # quick (default; also --quick)
/wiki-cycle --full              # also written /wiki-cycle full
/wiki-cycle --ingest-only       # drain what is queued; no gathering
/wiki-cycle --discover-only     # gather and write the checklist, then stop
/wiki-cycle --prompt-for-urls   # the user pastes URLs; ingest them
/wiki-cycle --lint-only [--semantic]
/wiki-cycle --report-only | --refresh-only | --claims-only
# modifiers: <notebook> · --direct · --resume <cycle_id> · --no-confirm-discovery · --since <hours> · --lint-all
```

| Step | quick | --full | --ingest-only | --discover-only | --prompt-for-urls |
|---|---|---|---|---|---|
| 0 Run folder + scratchpad | ✓ | ✓ | ✓ | ✓ | ✓ |
| 1.0 Drive-fetch (only when `drive.enabled`) | ✓ | ✓ | — | ✓ | — |
| 1 Discover + 1.5 human review | ✓ | ✓ | — | ✓ (then stop) | — |
| 1.7 Triage | ✓ | ✓ | ✓ | — | — (the user chose them) |
| 1.8 Browser capture (only when a gated item is this session's) | ✓ | ✓ | ✓ | — | ✓ |
| 2 Ingest, 2.5 dequeue + staging check | ✓ | ✓ | ✓ | — | ✓ |
| 2.6 Checker (only when a staged raw is a long transcript) | ✓ | ✓ | ✓ | — | ✓ |
| 3 Mechanical lint, 3.5 integration scripts | ✓ | ✓ | ✓ | — | ✓ |
| 4 Semantic lint, 5 fixes, 5.5 promote | — | ✓ | — | — | — |
| 6 Claims, 6.5 synthesis, 7 refresh | — | ✓ | — | — | — |
| 8 Report, 9 commit | ✓ | ✓ | ✓ | ✓ | ✓ |

`--lint-only` runs 0, 3 and 8 (`--semantic` adds 4); `--report-only` runs 8 from the last run's JSON; `--refresh-only` runs 7; `--claims-only` runs 6. A step outside the mode is recorded once as `skipped (mode)`; a step inside it that has nothing to do (no Drive, nothing gated, no long transcript) is `skipped (<why>)`. **"full" means full**: it includes synthesis (Step 6.5), always. Run it weekly, or when a batch is 25+ items or cuts across many entries. `--lint-all` makes Steps 4 and 6 read every entry instead of what is new.

Entries are staged in `_inbox/proposed/` unless `--direct`; the user reviews them with `/wiki-promote`. An unattended run never files into `wiki/` directly.

## Steps

**Step 0 — run folder.** `cycle_id` = `<local date>-<NN>`, NN the next free number in `_inbox/reports/<date>/`. Create `_inbox/reports/<date>/<cycle_id>/` (the run folder) and its `scratchpad.md` from the template in [reference.md](./reference.md), status `in_progress`. `--resume <cycle_id>`: read that run's scratchpad and continue from the phase after the last `done`; never repeat a done phase (its outputs are on disk).

**Every step writes `<step>.json` + `<step>.md` in the run folder** ([cycle step return format](./best-practices/framework/cycle-step-return-format.md); the JSON is authoritative): the scripts do it when given `--cycle-id <cycle_id> --run-folder <run-folder>` (or `--out` for Drive); for a model step, the orchestrator writes the pair. A step whose JSON says `status != completed` or has `errors` is flagged in the scratchpad; most failures do not block the steps after it. Update the scratchpad after every step.

**Step 1.0 — Drive-fetch** (only when the project config has `drive.enabled: true`):

```bash
python {{WIKI_SCRIPTS_DIR}}/wiki-fetch-drive-folder.py --folder-name "<drive.parent_folder>" --subfolder <drive.subfolder> \
  --queue-into <notebook> --queue-priority 3 --queue-added-by drive-fetch \
  --move-handled --archive-subfolder <cycle_id> --out <run-folder>/drive-fetch.md
```

It queues each new URL into `_inbox/pending/`, archives the handled Drive files, and writes `drive-fetch.md` + `drive-fetch.json`. Folder names, OAuth and the archive rules: [reference.md](./reference.md).

**Step 1 — Discover.** Follow `/wiki-discover <notebook>` with the cycle id; it writes `discover.json` + `.md` and one checklist in `_inbox/discovered/`.

**Step 1.5 — Human review #1** (on unless `--no-confirm-discovery`). Show the Queued / Skipped / Deferred tables from `discover.md` and wait: "yes go" → queue the approved items; "no" / "abort" → mark the run interrupted and stop; "tweak X" → re-read the edited checklist; "show the raw JSON" → print `discover.json`. Queue **only discovery's approved items** with `wiki-list-add.py` (Drive's are already queued by Step 1.0). Never auto-approve a tier-4 source. `--no-confirm-discovery` (unattended runs) queues tiers 1–3 and defers tier 4.

**Step 1.7 — Triage.** Follow `/wiki-triage` for this notebook: every ticket in `_inbox/pending/` moves into one `_inbox/intake/<folder>/` by the buckets in `_inbox/intake/README.md` (`main` is the catch-all; a notebook without the file has `main` alone), with the raw captured for items another reader gets, and each other reader told once. Then list what this session ingests: the tickets in every bucket whose reader is this session (`wiki-triage.py buckets` says which), including ones the user dropped there directly. Other readers' buckets, and a bucket the user reads (`mark`), are never ingested here.

**Step 1.8 — Browser capture** (only when one of this session's tickets is a login-gated page, or its host refused a direct fetch with 403). The session captures the raw through the user's signed-in browser before any worker starts (the Browser-session capture flow in `wiki-update`'s `fetchers.md`); workers have no browser. A session without a browser leaves that ticket in its bucket, lists it in the report as "needs browser capture", and ingests the rest.

**Step 2 — Ingest.** Spawn `wiki-ingester` workers (fall back to `general-purpose` only if it is not installed), **unnamed**, up to 4 at a time, each with a slice of this session's tickets and `--staged` unless `--direct`. Before spawning, read `~/.claude/agents/wiki-ingester-config.json`: with `confirm_model_each_run` true, a session that can ask asks the user which model (default `model_default`); one that cannot uses `model_default` and says so. Pass it as the spawn-time `model`.
- **YouTube**: when the batch has more than one YouTube item, all of them go to **one** worker, fetched one after another (they share one rate limit the GPU slots do not cover). A 429 is retried once, after that worker's other items; a second 429 fails the item with the reason.
- A ticket carrying `raw_path` (captured at triage or Step 1.8) is filed from that raw, never fetched again.
- Each worker runs the full `/wiki-update` flow per source, gate included. **Workers never write `update.json`**: the orchestrator writes `update.json` + `.md` once, from every worker's receipt (staged slugs, skipped and deferred items with reasons).
- After the batch, `python {{WIKI_SCRIPTS_DIR}}/wiki-qmd-query.py --stats` into the report (searches that waited for a GPU slot; slow waits or "full search unavailable" → fewer workers next time). In `--full`, also `wiki-qmd-query.py --depth-check --notebook <notebook>` once: exit 1 (C was reached) is reported to the user; exit 2 (nothing measured) is never a pass.

**Step 2.5 — Dequeue and check staging** (always, after ingest):

```bash
python {{WIKI_SCRIPTS_DIR}}/wiki-dequeue.py --topic <notebook>              # pending tickets whose source is now an entry -> done/
python {{WIKI_SCRIPTS_DIR}}/wiki-promote.py --topic <notebook> --check      # exit 1 names each entry promote would hold
```

Fix every sidecar `--check` names before the commit; a worker's receipt is a claim, the check is the evidence.

**Step 2.6 — Checker** (only when a staged entry's raw is a long transcript):

```bash
python {{WIKI_SCRIPTS_DIR}}/wiki-cycle-scope.py --topic <notebook> checker --run-folder <run-folder>
```

For each line it prints (entry, raw, minutes), spawn a `wiki-checker` agent, unnamed, up to 4 at a time, on the model in `~/.claude/agents/wiki-checker-config.json` (`model_default`), briefed with three paths only: the entry, the raw, and `<run-folder>/checker/<slug>.json`. Log each report: `wiki-cycle-scope.py --topic <notebook> checker-log --run-folder <run-folder> --entry <slug> --report <run-folder>/checker/<slug>.json`. A `fix` verdict: correct the staged entry from the report (take out or correct what the raw does not support, add what it skipped, restore the raw's words in quotes), then re-run `wiki-promote.py --check --slug <slug>`. A session that cannot make the fix leaves the entry staged and lists it under "held: checker findings" with its report. **An entry with an uncorrected `fix` report is never promoted.** The checker never edits anything itself.

**Step 3 — Mechanical lint.** If this run promoted anything into `wiki/` already (`--direct`), run `wiki-fix-links.py --topic <notebook>` first. Then:

```bash
python {{WIKI_SCRIPTS_DIR}}/wiki-lint-mechanical.py --topic <notebook> --cycle-id <cycle_id> --run-folder <run-folder>
```

**Step 3.5 — Integration scripts** (always, in the modes that run Step 3, staged run or not; cheap and idempotent), each with `--topic <notebook> --cycle-id <cycle_id> --run-folder <run-folder>`: `wiki-reciprocate-backlinks.py`, `wiki-index-per-folder.py`, `wiki-map-compile.py`. Treat a large unexplained `backlinks_added` as a signal to look, not a success.

**Step 4 — Semantic lint** (`--full`; `--lint-only --semantic`). Not if one ran in the last 24 hours. Scope first:

```bash
python {{WIKI_SCRIPTS_DIR}}/wiki-cycle-scope.py --topic <notebook> semantic --run-folder <run-folder> [--all when --lint-all]
```

It writes `semantic-scope.txt`: the entries added or revised since the last semantic lint, plus this run's staged entries (read from `_inbox/proposed/`, since Step 5.5 has not promoted them yet). Spawn one agent per ~100 entries in scope, up to 4, unnamed, each given a slice of the scope balanced by file count and the `/wiki-lint --full` criteria; include the drift-watch deep-compares. Merge their findings into `lint-semantic.json` + `.md` (its `timestamp` is the next run's cut-off).

**Step 5 — Fix lint issues.** Show the findings; apply what the user approves (fix agents by category, up to 3). A finding that would edit a `framework-contract: true` doc goes to the user instead: the docs refresh overwrites such edits.

**Step 5.5 — Promote** (`--full`, before Steps 6 and 6.5, which read `wiki/`). Promote every staged entry not held by the checker, one slug at a time, then normalise links and confirm:

```bash
python {{WIKI_SCRIPTS_DIR}}/wiki-promote.py --topic <notebook> --auto --slug <slug>     # per entry not held
python {{WIKI_SCRIPTS_DIR}}/wiki-fix-links.py --topic <notebook>
python {{WIKI_SCRIPTS_DIR}}/wiki-lint-mechanical.py --topic <notebook>                   # 0 broken links before going on
```

Then re-run Step 3.5 (promotion adds entries and backlinks at once). If the user wants staged entries held even in a `--full` run, skip this and tell Steps 6 and 6.5 to treat `_inbox/proposed/` as out of scope.

**Step 6 — Claims** (`--full`; `--claims-only`). Scope: `wiki-cycle-scope.py --topic <notebook> claims --run-folder <run-folder>` (`--all` with `--lint-all`): entries with no claims in the index, or revised since it was written. Follow `/wiki-claims` over that scope: append to the index, never rebuild it, and write `claims.json` + `.md`.

**Step 6.5 — Best-practices synthesis** (`--full` — never skipped). Report-only agents review this cycle's new `research/` entries against the `project/best-practices/*` pages: confirm, a dated watch-note, or a doctrine change (be conservative; prefer watch-notes; contradictions keep both sides). Net-new areas go to `best-practices-candidate-concepts.md`. Each agent writes `synthesis-<area>.md` (section, proposed text in the page's voice, dated, source entry, rationale, confidence). **Human gate:** present the consolidated proposal (take all / pick / none), apply only what the user approves, and bump each touched page's `last_reviewed`. A run nobody can answer writes the proposal and changes no canon.

**Step 7 — Refresh scan** (`--full`; `--refresh-only`): follow `/wiki-refresh --overdue-only`.

**Step 8 — Report.** Follow `/wiki-report`, from the run folder's step JSONs: `<cycle_id>-run-cycle-report.md` + `.json`. It lists what was triaged to whom, what was ingested, what the checker found and held, anything left for a browser session, and the search stats.

**Step 9 — Commit.** First delete zero-byte or junk files left by shell redirects (own or a sub-agent's: `output`, `#`, `${...}`, a stray word). Then add **only the notebook's path** (other sessions may have work in the same repository) and commit once, at the end: `Wiki cycle <date> — N ingested, N fixes, N contradictions, N synthesis changes, wiki at N entries`. Set the scratchpad to `completed`, then show the report and offer to act on its recommendations.

## Don't

- Don't skip the scratchpad: it is how a run resumes.
- Don't run more than 4 agents of a kind at once; spawn every one unnamed and in the background.
- Don't let workers or the checker write step files, commit, or edit outside their brief.
- Don't commit mid-cycle; one commit at the end covers the run.
- Don't skip the report: it is the user's review point.
