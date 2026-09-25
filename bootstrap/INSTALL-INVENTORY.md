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
| `new-wiki` | both | The bootstrap orchestrator: global tooling install (Phase A / tooling mode), `--mode status` (is the global tooling installed / stale / partial / missing — read before the skills question, 2026-09-09), per-project scaffold (Phase B, with `--project-folder` / `--research-folder stubs\|empty\|none`), `--phase docs` refresh of a project's framework-managed docs |
| `wiki` | both | Show the wiki's INDEX (browse rather than search) |
| `wiki-init` | both | Scaffolds a topic folder structure from the same `SCAFFOLD_TAXONOMY` a default `/new-wiki` applies (standalone; `/new-wiki` does not call it) |
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
| `task-list` | both | The project's task list: the At a glance block at the top of `sessions/<persona>/task.md` — one table per owner, numbers never reused, a task removed only on the user's word; `/task-list` or plain speech ("add a task", "delete task 4"). Every edit through `wiki-tasks.py` (2026-09-15; not `/tasks`, which is Claude Code's background-jobs panel) |
| `wiki-triage` | research (primary), both | Gives each untriaged research source in `_inbox/pending/` one owner: moves its ticket into the `_inbox/intake/<folder>/` bucket whose purpose fits (the buckets are the frontmatter of `_inbox/intake/README.md`; `main` is the catch-all), captures the raw for items another reader gets, logs each call as a precedent, tags each other reader once. Every move through `wiki-triage.py` (2026-09-24, task #42) |

## A2. Global agents

Source-of-truth: `bootstrap/agents/<name>/AGENT.md` (+ sidecars; `evals/` stays gold-only)
Install target: `~/.claude/agents/<name>.md` (AGENT.md renamed) + `<name>-*.json` sidecars
Manifest: `TRAVEL_AGENTS` in `bootstrap/scripts/_install_tooling.py` (added 2026-08-20)

| Agent | Project type | Purpose |
|---|---|---|
| `wiki-ingester` | research (primary), both | Spawnable subagent for delegated batch ingestion — full /wiki-update flow per source, one at a time, full-depth reads, staged output, compressed receipt. `/wiki-cycle` Step 2 spawns it (falls back to `general-purpose` if absent). Sidecars: `wiki-ingester-reading-list.json` (skills + pre-reading), `wiki-ingester-config.json` (model_default + confirm_model_each_run — the spawner reads this and asks the user per batch while the confirm flag is true) |
| `wiki-checker` | research (primary), both | A second reader for a staged entry: reads the entry and its raw in full and reports claims the raw does not support, sections the entry skipped, and misquotes, as one JSON report with a `pass` / `fix` verdict. Tools Read, Grep, Glob, Write only (never edits the entry). `/wiki-cycle` spawns one per staged entry whose raw is a transcript of `min_transcript_minutes`+ (default 15) and holds a `fix` entry back from promotion. Sidecar: `wiki-checker-config.json` (`model_default` opus, `min_transcript_minutes`) (2026-09-24, task #42 C3) |

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
| `wiki-update.py` | File an external source as an entry. The write-time gate lives here: it refuses an entry without a TL;DR, without two Related wiki links (a warning for tier `self`), with its layout out of order, or with frontmatter that would not parse. `--revises <slug>` files a later snapshot of a source (checks the older entry exists, implies `--force`). `--slug-for` exits 2 with near matches when no entry matches. Staged entries' links are checked. `internal://` URLs never count as duplicates, and a duplicate prints `duplicate_of=` (2026-09-15) |
| `wiki-fetch-youtube.py` | YouTube transcript → verbatim raw archive under `raw/` (needs `yt-dlp` on the host) |
| `wiki-fetch-pdf.py` | PDF (URL or local) → extracted text under `raw/` |
| `wiki-fetch-drive-folder.py` | Google Drive `__FOR CLAUDE/<topic>/` → pending queue, with short-URL resolution and dedup against the wiki's `source_url`s; OAuth reads `--client-secrets`, `$WIKI_DRIVE_CLIENT_SECRETS`, or `~/.config/wiki-cycle/client_secrets.json` (2026-09-15); `--out <run-folder>/drive-fetch.md` also writes the cycle's `drive-fetch.json` beside it (2026-09-24) |
| `wiki-list-add.py` | Add a source to the `_inbox/pending/` queue (URL-dedup across pending + proposed + wiki + done) |
| `wiki-list-process.py` | Batch-consume `_inbox/pending/` → staged entries |
| `wiki-list-render.py` | Regenerate the human-readable pending-list view |
| `wiki-dequeue.py` | Move already-ingested items out of the pending queue |
| `wiki-promote.py` | Move `_inbox/proposed/<slug>.md` → `wiki/<target_folder>/<slug>.md` (the folder from its sidecar), add backlinks into the related entries' Related sections (never into a framework-contract doc, 2026-09-15), regenerate the folder indexes and MAP. An entry whose sidecar is missing, invalid or names no folder is held back (exit 4); `--check` validates staging without moving anything; a folder outside the taxonomy is known when it carries a `README.md` (else a warning, 2026-09-24) |
| `wiki-verify.py` | Sidecar update flipping truth-status to verified (called by `/wiki-verify`) |
| `wiki-rollback.py` | Walk the `revises:` chain to the verified ancestor + write a rollback entry (called by `/wiki-rollback`) |
| `wiki-lint-mechanical.py` | Deterministic lint: broken links, orphans, frontmatter loadability, body checks (warn-only backlog), installed-skill drift, qmd index coverage; a tier-`self` entry without `raw_path` counts as self-authored, not missing (2026-09-15); `--cycle-id` + `--run-folder` write the cycle's `lint-mechanical.json` / `.md` (2026-09-24); a page declaring `standalone: "<reason>"` is listed apart, not as an orphan (2026-09-24); stale-pending flags only our own notes (workflow phrases anywhere, `not yet built` / `TODO:` in tier `self`; frontmatter, quotes, code, link targets skipped; 2026-09-24) |
| `wiki-fix-links.py` | Resolve bare-slug / wrong-depth markdown links to the correct relative path |
| `wiki-reciprocate-backlinks.py` | Ensure every outbound `.md` link has a reciprocal BACKLINKS-AUTO block |
| `wiki-index.py` / `wiki-index-per-folder.py` | Regenerate `_INDEX.md` (root / per folder) |
| `wiki-map-compile.py` | Regenerate the always-loaded root `_MAP.md` |
| `wiki-qmd-query.py` | Runs qmd's full search (`qmd query`) for every caller — session, `/wiki-discover`, parallel ingest workers — holding one of three GPU slots (OS file locks; a fourth caller waits; three since the qmd 2.8.3 test of 2026-09-14, two before), with a 120 s timeout that kills the process tree, GPU-full back-off and retry then exit 75 (never a keyword fallback), `--preflight` (the CUDA check, plus a warning when qmd is older than 2.8.3) and `--stats` (per-call wait/run log at `~/.cache/wiki-qmd/searches.jsonl`); `--notebook <name>` scopes a search to one notebook's collection (resolved through the registry; ingest, update and discover always pass it), `--all-notebooks` searches every one; depth is `-k` (results, default 30) and `-C` (the most candidates the reranker may score; default 120, above qmd's ~100 pool of 20 per list — the 8%-of-files sizing was removed 2026-09-23 because it never bound), overridable as `$WIKI_QMD_K` / `$WIKI_QMD_C`; `$WIKI_QMD_INDEX` picks a named qmd index (the skill test baseline's sandbox, 2026-09-15); searches the current project's notebook unless told otherwise; drops `_MAP`/`_INDEX` from results; every search logs qmd's count of candidates reranked, and `--stats` reports it against C; `--depth-check` searches sampled entry titles, reads that count against C (exit 1 when C was reached, 2 when nothing was measured) and logs to `depth-checks.jsonl` (`/wiki-cycle --full` runs it; until 2026-09-23 it compared C with 2C, which could not fail). Added 2026-09-13 when the user retired the workers-use-`qmd search` rule |
| `wiki-search-rerank.py` | Post-filter qmd's `--json` output by truth-status bucket (verified > unverified > temporal > contradicted; rolled_back excluded unless `--include-rolled-back`) — the search spec's surface 1; shipped 2026-09-08. Accepts qmd 2.1's bare-list JSON and `qmd://` file URIs since 2026-09-12 |
| `wiki-session-start.py` | The SessionStart hook: at startup and after `/clear`, prints the paths of the current project's resume files (`sessions/active-context.md`, `sessions/<persona>/handoff.md` + `task.md`, each if present) with the instruction to read them before the first reply, as JSON: `additionalContext` for Claude, and a `systemMessage` the user sees in the terminal at startup — the handoff's `GOAL` line and "send any message for the full recap" (a hook cannot start a model turn; added 2026-09-15 after plain stdout left the user a blank prompt). Paths, not contents: Claude Code keeps only a ~2 KB preview of a hook's output in context (in the first real session, 18.3 KB of contents arrived as a 2 KB preview), so output stays under 2,000 characters. Finds the project's own `.claude/wiki-config.json` (never the machine config in the home folder), resolves the wiki like every wiki script (`_wiki_config.wiki_dir`), persona from the config's `persona` key (default `main`). Anything else — no config, no wiki, no resume files, any error — prints nothing and exits 0. The tooling install adds it to `~/.claude/settings.json` (`hooks.SessionStart`, matcher `startup\|clear`, exec form — `command` = the installing Python, `args` = a `-c` guard + the script, no shell, so cmd.exe never parses it (claude-code #76774); a backup `settings.json.bak-wiki` first; other hooks untouched). Added 2026-09-14 (user: global, silent outside wiki projects) |
| `read-guard.py` | Makes "read this document" mean the whole document, by enforcement (2026-09-18, after a transcript audit found 45 instruction and resume files read only partly since 2026-08-20, each reported as read). A document is `.md .markdown .mdx .txt .rst .adoc .org`. **PreToolUse** (`Read\|Bash\|PowerShell`) refuses a Read with a `limit` from the top of a document that fits in one Read (≤ 60,000 bytes), a shell `head`/`tail`/`sed -n` on a document or on one piped in, `Get-Content -TotalCount/-Head/-Tail/-First` or a pipe into `Select-Object -First/-Last`, and a shell `cat` of documents over 25,000 bytes combined (the shell would return a preview). Quote- and heredoc-aware, so a commit message or a heredoc body is never read as a command. **Stop / SubagentStop** read the session's own transcript: every document Read this turn is checked against the lines the Read tool reported (`startLine`, `numLines`, `totalLines`), pooled with the session's other Reads of it; one not covered to its last line blocks the stop with the missing ranges, once per turn (`stop_hook_active` lets the second through). That also catches the Read tool's own truncation. Documents the session wrote itself are exempt; any error allows the action. Registered by the tooling install for all three events, exec form, like the SessionStart hook. Checks: `tests/hooks/test_read_guard.py` |
| `wiki-tasks.py` | The At a glance task list behind `/task-list`: `show`, `init`, `add`, `set`, `done`, `remove --confirmed` on `sessions/<persona>/task.md` (persona from the project config). Picks each number above every number in the file and records the next free one in a marker comment; refuses a removal without `--confirmed`; keeps the rest of the file as it is (2026-09-15) |
| `wiki-cycle-scope.py` | What `/wiki-cycle` reads, decided by a script: `semantic` (entries added or revised since the last semantic lint, plus this run's staged; `--all` for everything), `claims` (entries with no claims in the index, or revised since it was written, plus staged), `checker` (staged entries whose raw is a transcript of `min_transcript_minutes`+), `checker-log` (one line per checker report in `_inbox/reports/checker-log.jsonl`). "Added" is a file created after the cut-off (git), "revised" is `last_reviewed` on or after it: machine edits such as backlink blocks never count (2026-09-24, task #42 C1/C3) |
| `wiki-triage.py` | The mechanical half of `/wiki-triage`: `buckets` (the config, each reader, who "this session" is; a notebook with no `_inbox/intake/README.md` has one bucket, `main`), `check` (exit 1 on a config problem), `pending`, `route <ticket> --to <folder> --reason … [--raw raw/<file>]` (refuses a folder that is not a bucket, moves the ticket, records `raw_path`, appends to `_inbox/intake/triage-log.md`), `log --last N` (the precedents). Never deletes (2026-09-24) |
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

The folder taxonomy under `wiki/` lives in `_wiki_config.py` (the single copy; `wiki-init.py` and `new-wiki.py` both read it), in two halves since 2026-09-09: `PROJECT_TAXONOMY` = `project/{components,decisions,architecture,patterns,troubleshooting,best-practices}` and `RESEARCH_TAXONOMY` = `research/{active,long-term,tooling,best-practices,interesting-docs}`, plus `sessions/` always. `/new-wiki` asks for each half separately — `stubs` (the half with those subfolders), `empty` (the root only; subfolders appear as `/wiki-update` or `/wrap-up` file into them) or `none` — via `--project-folder` / `--research-folder`; `taxonomy_for()` turns the two answers into the folder list, and the answers are recorded in the project config as `wiki_folders`. `SCAFFOLD_TAXONOMY` is the default (both halves with stubs). `MERGED_TAXONOMY` is the superset the folder guards in `wiki-update.py` / `wiki-promote.py` recognise: it also carries `LEGACY_RESEARCH_TAXONOMY` = `research/{implementation,skills,orchestration}` — the agentic-design notebook's topics that every new wiki used to receive; recognised for existing wikis, no longer created. The six framework-contract docs land in `project/best-practices/framework/` whenever `project/` exists (section A4).

## D. Configuration

Three files, three scopes:

| File | Scope | Written by | Carries |
|---|---|---|---|
| `~/.claude/wiki-config.json` | machine | Phase A / tooling install; Phase B adds `registry` | `bootstrap_source` (where this clone lives — what `-RefreshOnly`, `/new-wiki --sync` and `--phase docs` read), `install_version`, `last_phase_a`, `drive`, `registry` (the machine-wide fallback pointer to `linked-notebooks.json`, written by the first registry-mode Phase B; lets `--topic <notebook>` resolve from a cwd with no project config, 2026-09-13) |
| `<project>/.claude/wiki-config.json` | project | Phase B | a thin pointer: `tool`, `project_name`, `notebook` + `registry` (registry model) or the in-project wiki location, `skills_install`, `wiki_folders` (the two `stubs\|empty\|none` answers), `drive` |
| `<vault>/linked-notebooks.json` | vault | Phase B (`_upsert_registry`) | every notebook's root + its two booleans `confirm_before_create` / `confirm_before_promote`; the single source of truth for WHERE a wiki is — every `/wiki-*` script resolves through it (`_wiki_config.py`); optional `wrap_up_commit` (`none`/`commit`/`push`, `/wrap-up`'s Step 7 default), set by hand, not by the scaffold (2026-09-25) |

The agentmemory MCP wiring from the May draft was removed 2026-05-14 (`-NoAgentmemory` is a no-op kept for back-compat).

## E. Per-project structure (the empty scaffold)

Created by `/new-wiki` Phase B. Two layouts; the `wiki/` folders are whatever the two folder answers chose (section C — `sessions/` always, each half with stubs, empty, or absent):

```
In-project (a wiki inside a code repo):        Notebook in a vault (linked-notebooks.json above it):
<project>/                                     <vault>/notebooks/<name>/
├── .claude/wiki-config.json                   ├── README.md
├── CLAUDE.md, README.md, .gitignore           ├── how-to/llm-wiki/        ← pack usage docs (+ _FRAMEWORK_MANAGED.md marker)
└── llm-wiki/                                  ├── wiki/                   ← HOME, _MAP, _INDEX + the taxonomy (section C)
    ├── README.md                              ├── raw/sessions/
    ├── how-to/llm-wiki/                       ├── _inbox/{pending,proposed,done,rejected,reports}/   (first use)
    ├── wiki/                                  └── _signals/               ← truth-status sidecars (first use)
    ├── raw/sessions/
    └── _inbox/, _signals/  (first use)
```

Phase B creates the folders above except `_inbox/` and `_signals/`, which the queue, staging and verify scripts create on first use.

The flat layout exists so that every notebook in a vault has the same shape (qmd collections, `_inbox/` staging and `_signals/` sidecars all assume `<root>/wiki/`); the calling code repo then carries only the thin pointer in `.claude/wiki-config.json` and a `CLAUDE.md` that @-imports the notebook's `_MAP.md` by absolute path.

## F. External dependencies

| Dependency | Used by | Notes |
|---|---|---|
| Python 3.10+, Git | everything | the only hard requirements for the global install |
| `qmd` (host npm install) | `/wiki-search`, `wiki-qmd-query.py` (every full search), `wiki-search-rerank.py`, the lint's index-coverage section | each wiki is a qmd collection (`qmd collection add <wiki>`; `qmd update && qmd embed` after a batch). `qmd query` runs three bundled models through node-llama-cpp and needs a GPU backend; without a CUDA runtime it falls back to Vulkan, where generation hung indefinitely (root-caused 2026-09-12, resolves the 2026-09-02 note). BM25 `search` needs no model |
| CUDA 13.1+ runtime (`winget install --id Nvidia.CUDA --version 13.2 --exact --override "-s cudart_13.2 cublas_13.2"`) | `qmd query` via node-llama-cpp | machine-level, NVIDIA Windows only; runtime + cuBLAS is enough (no compiler, no driver). Verify: `node-llama-cpp inspect gpu` prints `CUDA: available`; `/wiki-search` runs that preflight and stops on failure. Optional — `qmd search` works without it |
| `yt-dlp` (host) | `wiki-fetch-youtube.py` | transcript fetch |
| Google OAuth client secrets | `wiki-fetch-drive-folder.py` | `~/.config/wiki-cycle/client_secrets.json`; see the `drive-setup` page |

## Update mechanism (shipped)

**Source-of-truth lives in `bootstrap/`.** When a skill, script or doc changes there, the installed copies go stale in two places, each with its own refresh:

- **Global tooling** (`~/.claude/skills/`, `~/.claude/wiki-scripts/`, `~/.claude/agents/`): `install-wiki.ps1 -RefreshOnly` / `install-wiki.sh`, or `wiki-upgrade.py` directly — the same copy loop (`_install_tooling.py`), which refuses any skill or agent whose frontmatter does not parse. `/new-wiki --sync` re-runs Phase A, which refreshes only the global `/new-wiki` skill. `new-wiki.py --mode status` (`global_tooling_status()` in `_install_tooling.py`, 2026-09-09) is the drift detector: it compares every installed skill, script and agent with the clone and reports installed / stale / partial / missing. `/new-wiki` reads it before its skills question and Phase B in global mode refuses a partial or missing set (or installs it once with `--install-global-if-missing`, which the installer wrappers pass); a stale set is named, never re-copied by the scaffold. The lint's installed-skill section verifies only that every installed SKILL.md / agent file parses.
- **Framework-managed docs inside a project** (`how-to/llm-wiki/`, the root marker, `wiki/project/best-practices/framework/`): `new-wiki.py --phase docs --target-folder <project>`; `--check` reports without writing; `--all-notebooks` covers every notebook in the registry. The standing procedure after any change that lands in a notebook is `--check --all-notebooks` → review every REPLACE → refresh → `-RefreshOnly`.
- **A bundled install** (skills copied into the project): re-run Phase B against the same folder with `--force` (non-destructive: existing `CLAUDE.md` / `README.md` / `.gitignore` are kept).

## The May 2026 design questions, as they resolved

1. **`bootstrap_source` locks the install to one checkout** — it does, by design; it is one field in `~/.claude/wiki-config.json` and re-running the installer from a new clone rewrites it. No relocate skill was needed.
2. **Update notifications** — none; the refresh is idempotent and cheap, so it is run rather than detected. The lint's installed-skill section checks loadability, not staleness.
3. **Versioning** — the six framework-contract docs carry `framework-version` (compared by `--phase docs`); every skill and the agent carry `last_reviewed` / `review_after` / `reviewed_for_model`; `install_version` is a date stamp. Extending `framework-version` to the other scaffolded files is on the roadmap.
4. **Test mode** — `--dry-run` on every phase; `--check` on `--phase docs`.
5. **OS support** — `install-wiki.sh` covers Mac/Linux for Claude Code; Cursor is Windows-only (`-Tool cursor`).

Everything listed in this file ships; the manifests in `_install_tooling.py` are the authoritative lists.
