# LLM-Wiki Install Inventory

Authored 2026-05-12; sections B–F and the tail rewritten 2026-09-08 to describe what ships rather than the May design draft. The complete list of pieces that travel when `/new-wiki` runs the install. **The manifests decide, this file describes**: `TRAVEL_SKILLS`, `TRAVEL_SCRIPTS`, `TRAVEL_AGENTS` and the helper lists in `bootstrap/scripts/_install_tooling.py` are what the installer copies; a row here without a manifest entry does not travel.

## Principle

**Structure travels, content doesn't.** A new project gets the wiki skeleton + skills + scripts + conventions + templates. It does NOT get the agentic-design (or any other existing topic's) entries — those stay where they are as their own topic in the vault.

## Categories

- **A. Global skills** — installed once at `~/.claude/skills/`, used in every Claude Code session
- **B. Global scripts** — installed once at `~/.claude/wiki-scripts/`, invoked by skills
- **C. Templates** — copied as needed when scaffolding a new project
- **D. Configuration** — the machine config (`~/.claude/wiki-config.json`), the per-project thin pointer (`<project>/.claude/wiki-config.json`) and the notebook registry (`linked-notebooks.json`)
- **E. Per-project structure** — created by `/new-wiki` Phase B (empty scaffold, two layouts)
- **F. External dependencies** — host-installed tools the scripts shell out to

---

## A. Global skills

Source-of-truth: `bootstrap/skills/<skill>/SKILL.md`
Install target: `~/.claude/skills/<skill>/SKILL.md`

| Skill | Project type | Purpose |
|---|---|---|
| `new-wiki` | both | The bootstrap orchestrator: global tooling install (Phase A / tooling mode), per-project scaffold (Phase B), `--phase docs` refresh of a project's framework-managed docs |
| `wiki` | both | Show the wiki's INDEX (browse rather than search) |
| `wiki-init` | both | Scaffolds a topic folder structure from the same `MERGED_TAXONOMY` the `/new-wiki` scaffold applies (standalone; `/new-wiki` does not call it) |
| `wiki-update` | research (primary), both | Ingests external URLs / files into wiki staging |
| `wiki-search` | both | Hybrid BM25 + vector + LLM-rerank search via qmd |
| `wiki-cycle` | research | Full research-cycle orchestrator (discover → ingest → lint → promote) |
| `wiki-discover` | research | RSS / voices / repos discovery — internal to cycle |
| `wiki-list` | research | Queue management — internal to cycle |
| `wiki-claims` | both | Claim extraction + contradiction detection — internal to cycle |
| `wiki-refresh` | both | Stale-entry scan — internal to cycle |
| `wiki-report` | research | Morning report — internal to cycle |
| `wiki-lint` | both | Mechanical + semantic lint |
| `wiki-promote` | both | Stage → promote with backlink + INDEX regen (runs `/wiki-verify` as a sub-step) |
| `wiki-verify` | both | Flip an entry unverified → verified via sidecar (truth-status lifecycle; added 2026-05-25, registered to travel 2026-07-07) |
| `wiki-rollback` | both | Roll an entry back to its verified ancestor (pairs with `wiki-verify`; added 2026-05-25, registered to travel 2026-07-07) |
| `wrap-up` | development | Session-end distillation into wiki entries (written 2026-05-12) |

## A2. Global agents

Source-of-truth: `bootstrap/agents/<name>/AGENT.md` (+ sidecars; `evals/` stays gold-only)
Install target: `~/.claude/agents/<name>.md` (AGENT.md renamed) + `<name>-*.json` sidecars
Manifest: `TRAVEL_AGENTS` in `bootstrap/scripts/_install_tooling.py` (added 2026-08-20)

| Agent | Project type | Purpose |
|---|---|---|
| `wiki-ingester` | research (primary), both | Spawnable subagent for delegated batch ingestion — full /wiki-update flow per source, one at a time, full-depth reads, staged output, compressed receipt. `/wiki-cycle` Step 2 spawns it (falls back to `general-purpose` if absent). Sidecars: `wiki-ingester-reading-list.json` (skills + pre-reading), `wiki-ingester-config.json` (model_default + confirm_model_each_run — the spawner reads this and asks the user per batch while the confirm flag is true) |

## A3. Pack usage docs (wiki-seed)

Source-of-truth: `bootstrap/wiki-seed/llm-wiki.md` (the pack page) + `bootstrap/skills/<name>/wiki-seed/<name>.md` + `bootstrap/agents/<name>/wiki-seed/<name>.md`
Install target: `<project how-to root>/llm-wiki/llm-wiki.md` + `llm-wiki/skills/<name>.md` + `llm-wiki/agents/<name>.md` (Phase B for a new project; `--phase docs --target-folder <project>` refreshes an existing one)
Mechanism: `seed_pack_docs()` in `bootstrap/scripts/new-wiki.py` (added 2026-09-08; the per-skill copy dates from 2026-07-31)

**Every skill in A and every agent in A2 ships a page; the seeder warns by name for any that does not.** One folder per installed package in the receiving how-to tree (`how-to/llm-wiki/` here; the agent-factory's packs land as `how-to/<pack>/` beside it); a framework refresh never removes another pack's folder.

## A4. Framework-contract docs

Source-of-truth: `bootstrap/topic-template/wiki/best-practices/framework/*.md` (six docs, each `framework-contract: true` with a `framework-version`)
Install target: `<wiki>/project/best-practices/framework/<name>.md` (Phase B for a new project; `--phase docs --target-folder <project>` refreshes an existing one)
Mechanism: `seed_framework_docs()` in `bootstrap/scripts/new-wiki.py` (2026-09-08): content-compared, a differing project copy is overwritten and named; the reciprocation script's backlink block is ignored in the comparison and preserved. `--check` (same day) reports instead of writing — unchanged / ADD / REPLACE per doc with the version on both sides and a diff, exit 1 when a refresh would change anything. A wiki without `project/` is out of scope and skipped by name. `--all-notebooks` runs check or refresh over every registered notebook with a summary — the standing procedure after a framework change is `--check --all-notebooks`, review, then refresh.

**These are the framework's canonical copies.** A project keeps its own notes in a sibling file, never by editing one of these — the edit is lost on the next refresh (`--check` shows it first).

## B. Global scripts

Source-of-truth: `bootstrap/scripts/<script>.py`
Install target: `~/.claude/wiki-scripts/<script>.py` (`{{WIKI_SCRIPTS_DIR}}` in the skills resolves to it)
Manifest: `TRAVEL_SCRIPTS` (the commands) + `TOOLING_HELPER_SCRIPTS` / `SHARED_HELPER_SCRIPTS` (the `_`-prefixed modules they import) in `_install_tooling.py`

| Script | Purpose |
|---|---|
| `new-wiki.py` | The bootstrap helper behind `/new-wiki`: Phase A / tooling install, Phase B scaffold, `--phase docs [--check] [--all-notebooks]` |
| `wiki-upgrade.py` | Refresh the global tooling from the recorded bootstrap source (what `install-wiki.ps1 -RefreshOnly` and `/new-wiki --sync` run) |
| `wiki-init.py` | Scaffold a topic folder structure + templated README |
| `wiki-update.py` | File an external source as an entry (the write-time gate lives here: TL;DR, two Related links, loadable frontmatter) |
| `wiki-fetch-youtube.py` | YouTube transcript → verbatim raw archive under `raw/` (needs `yt-dlp` on the host) |
| `wiki-fetch-pdf.py` | PDF (URL or local) → extracted text under `raw/` |
| `wiki-fetch-drive-folder.py` | Google Drive `__FOR CLAUDE/<topic>/` → pending queue, with short-URL resolution and dedup against the wiki's `source_url`s |
| `wiki-list-add.py` | Add a source to the `_inbox/pending/` queue (URL-dedup across pending + proposed + wiki + done) |
| `wiki-list-process.py` | Batch-consume `_inbox/pending/` → staged entries |
| `wiki-list-render.py` | Regenerate the human-readable pending-list view |
| `wiki-dequeue.py` | Move already-ingested items out of the pending queue |
| `wiki-promote.py` | Move `_inbox/proposed/<folder>/<slug>.md` → `wiki/<folder>/<slug>.md` + backlinks |
| `wiki-verify.py` | Sidecar update flipping truth-status to verified (called by `/wiki-verify`) |
| `wiki-rollback.py` | Walk the `revises:` chain to the verified ancestor + write a rollback entry (called by `/wiki-rollback`) |
| `wiki-lint-mechanical.py` | Deterministic lint: broken links, orphans, frontmatter loadability, body checks (warn-only backlog), installed-skill drift, qmd index coverage |
| `wiki-fix-links.py` | Resolve bare-slug / wrong-depth markdown links to the correct relative path |
| `wiki-reciprocate-backlinks.py` | Ensure every outbound `.md` link has a reciprocal BACKLINKS-AUTO block |
| `wiki-index.py` / `wiki-index-per-folder.py` | Regenerate `_INDEX.md` (root / per folder) |
| `wiki-map-compile.py` | Regenerate the always-loaded root `_MAP.md` |
| `wiki-search-rerank.py` | Post-filter qmd's `--json` output by truth-status bucket (verified > unverified > temporal > contradicted; rolled_back excluded unless `--include-rolled-back`) — the search spec's surface 1; shipped 2026-09-08 |
| `install-skill.py` (helper) | Copy ONE skill onto the local system with placeholder substitution — the per-skill primitive the installer loops over |
| `_wiki_config.py`, `_entry_checks.py`, `_atomic_io.py`, `_install_tooling.py` (helpers) | Path/registry resolution and the date-time helpers; the shared mechanical entry checks (gate + lint); atomic writes; the install manifests and loop |

## C. Templates

Source-of-truth: `bootstrap/templates/` (project files) and `bootstrap/seed/wiki/` (wiki scaffold files)
Usage: rendered into a new project at `/new-wiki` time (bundled installs also keep a copy at `.claude/wiki-templates/`)

Research/development split removed 2026-06-15 — one merged template set; every project gets the same unified wiki (research/* + project/* + sessions/).

| Template | Purpose | When used |
|---|---|---|
| `CLAUDE.md.tmpl` | Project root CLAUDE.md (unified — does both research + project; carries the precedence rule) | every project init |
| `README.md.tmpl` | Project root README | every project init |
| `.gitignore.tmpl` | Project root .gitignore | every project init |
| `seed/wiki/{HOME,README,_MAP,_INDEX}.md.tmpl` | Wiki scaffold files rendered inside `wiki/` | every project init |

The folder taxonomy under `wiki/` is `MERGED_TAXONOMY` in `_wiki_config.py` (the single copy; `wiki-init.py` and `new-wiki.py` both read it): `research/{active,long-term,tooling,best-practices,implementation,skills,orchestration,interesting-docs}`, `project/{components,decisions,architecture,patterns,troubleshooting,best-practices}`, `sessions/`. The six framework-contract docs land in `project/best-practices/framework/` (section A4).

## D. Configuration

Three files, three scopes:

| File | Scope | Written by | Carries |
|---|---|---|---|
| `~/.claude/wiki-config.json` | machine | Phase A / tooling install | `bootstrap_source` (where this clone lives — what `-RefreshOnly`, `/new-wiki --sync` and `--phase docs` read), `install_version`, `last_phase_a`, `drive` |
| `<project>/.claude/wiki-config.json` | project | Phase B | a thin pointer: `tool`, `project_name`, `notebook` + `registry` (registry model) or the in-project wiki location, `skills_install`, `drive` |
| `<vault>/linked-notebooks.json` | vault | Phase B (`_upsert_registry`) | every notebook's root + its two booleans `confirm_before_create` / `confirm_before_promote`; the single source of truth for WHERE a wiki is — every `/wiki-*` script resolves through it (`_wiki_config.py`) |

The agentmemory MCP wiring from the May draft was removed 2026-05-14 (`-NoAgentmemory` is a no-op kept for back-compat).

## E. Per-project structure (the empty scaffold)

Created by `/new-wiki` Phase B. Two layouts, one taxonomy:

```
In-project (a wiki inside a code repo):        Notebook in a vault (linked-notebooks.json above it):
<project>/                                     <vault>/notebooks/<name>/
├── .claude/wiki-config.json                   ├── README.md
├── CLAUDE.md, README.md, .gitignore           ├── how-to/llm-wiki/        ← pack usage docs (+ _FRAMEWORK_MANAGED.md marker)
└── llm-wiki/                                  ├── wiki/                   ← HOME, _MAP, _INDEX + the taxonomy (section C)
    ├── README.md                              ├── raw/sessions/
    ├── how-to/llm-wiki/                       ├── _inbox/{pending,proposed,done,rejected,reports}/   (first use)
    ├── best-practices/                        └── _signals/               ← truth-status sidecars (first use)
    ├── wiki/
    ├── raw/sessions/
    └── _inbox/, _signals/  (first use)
```

Phase B creates the folders above except `_inbox/` and `_signals/`, which the queue, staging and verify scripts create on first use.

The flat layout exists so that every notebook in a vault has the same shape (qmd collections, `_inbox/` staging and `_signals/` sidecars all assume `<root>/wiki/`); the calling code repo then carries only the thin pointer in `.claude/wiki-config.json` and a `CLAUDE.md` that @-imports the notebook's `_MAP.md` by absolute path.

## F. External dependencies

| Dependency | Used by | Notes |
|---|---|---|
| Python 3.10+, Git | everything | the only hard requirements for the global install |
| `qmd` (host npm install) | `/wiki-search`, `wiki-search-rerank.py`, the lint's index-coverage section | each wiki is a qmd collection (`qmd collection add <wiki>`; `qmd update && qmd embed` after a batch); the standalone `query`/`vsearch` modes can hang for minutes — BM25 `search` does not (open, 2026-09-02) |
| `yt-dlp` (host) | `wiki-fetch-youtube.py` | transcript fetch |
| Google OAuth client secrets | `wiki-fetch-drive-folder.py` | `~/.config/wiki-cycle/client_secrets.json`; see the `drive-setup` page |

## Update mechanism (shipped)

**Source-of-truth lives in `bootstrap/`.** When a skill, script or doc changes there, the installed copies go stale in two places, each with its own refresh:

- **Global tooling** (`~/.claude/skills/`, `~/.claude/wiki-scripts/`, `~/.claude/agents/`): `install-wiki.ps1 -RefreshOnly` / `install-wiki.sh`, or `wiki-upgrade.py` directly — the same copy loop (`_install_tooling.py`), which refuses any skill or agent whose frontmatter does not parse. `/new-wiki --sync` re-runs Phase A, which refreshes only the global `/new-wiki` skill. There is no content-drift detector for installed copies: the copy is idempotent, so re-running it *is* the check; the lint's installed-skill section verifies only that every installed SKILL.md / agent file parses.
- **Framework-managed docs inside a project** (`how-to/llm-wiki/`, the root marker, `wiki/project/best-practices/framework/`): `new-wiki.py --phase docs --target-folder <project>`; `--check` reports without writing; `--all-notebooks` covers every notebook in the registry. The standing procedure after any change that lands in a notebook is `--check --all-notebooks` → review every REPLACE → refresh → `-RefreshOnly`.
- **A bundled install** (skills copied into the project): re-run Phase B against the same folder with `--force` (non-destructive: existing `CLAUDE.md` / `README.md` / `.gitignore` are kept).

## The May 2026 design questions, as they resolved

1. **`bootstrap_source` locks the install to one checkout** — it does, by design; it is one field in `~/.claude/wiki-config.json` and re-running the installer from a new clone rewrites it. No relocate skill was needed.
2. **Update notifications** — none; the refresh is idempotent and cheap, so it is run rather than detected. The lint's installed-skill section checks loadability, not staleness.
3. **Versioning** — the six framework-contract docs carry `framework-version` (compared by `--phase docs`); every skill and the agent carry `last_reviewed` / `review_after` / `reviewed_for_model`; `install_version` is a date stamp. Extending `framework-version` to the other scaffolded files is on the roadmap.
4. **Test mode** — `--dry-run` on every phase; `--check` on `--phase docs`.
5. **OS support** — `install-wiki.sh` covers Mac/Linux for Claude Code; Cursor is Windows-only (`-Tool cursor`).

Everything listed in this file ships; the manifests in `_install_tooling.py` are the authoritative lists.
