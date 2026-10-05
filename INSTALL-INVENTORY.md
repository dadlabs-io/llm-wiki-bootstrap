# LLM-Wiki Install Inventory

Authored 2026-05-12; sections B–F and the tail rewritten 2026-09-08 to describe what ships rather than the May design draft. The complete list of pieces that travel when `/new-wiki` runs the install. **The manifests decide, this file describes**: `TRAVEL_SKILLS`, `TRAVEL_SCRIPTS`, `TRAVEL_AGENTS` and the helper lists in `scripts/_install_tooling.py` are what the installer copies; a row here without a manifest entry does not travel.

## Principle

**Structure travels, content doesn't.** A new project gets the wiki skeleton + skills + scripts + conventions + templates. It does NOT get the agentic-design (or any other existing topic's) entries — those stay where they are as their own topic in the vault.

## Categories

- **A. Global skills** — installed once at `~/.claude/skills/`, used in every Claude Code session
- **B. Global scripts** — installed once at `~/.claude/wiki-scripts/`, invoked by skills
- **C. Templates** — copied as needed when scaffolding a new project
- **D. Configuration** — the machine config (`~/.claude/wiki-config.json`), the per-project thin pointer (`<project>/.claude/wiki-config.json`) and the notebook registry (`linked-notebooks.json`)
- **E. Per-project structure** — created by `/new-wiki` Phase B (empty scaffold, two layouts)
- **G. The global toolset** — one notebook holding every usage doc and the framework-contract docs once (2026-10-04)
- **F. External dependencies** — host-installed tools the scripts shell out to

---

## A. Global skills

Source-of-truth: `skills/<skill>/SKILL.md`
Install target: `~/.claude/skills/<skill>/SKILL.md`

| Skill | Project type | Purpose |
|---|---|---|
| `new-wiki` | both | The bootstrap orchestrator: global tooling install (Phase A / tooling mode), `--mode status` (is the global tooling installed / stale / partial / missing — read before the skills question, 2026-09-09), per-project scaffold (Phase B, with `--project-folder` / `--research-folder stubs\|empty\|none`; with `research/` it also writes the empty trusted-sources page `_config/feeds.md`, and the skill's optional question can fill it, 2026-09-26), `--phase docs` refresh of the global toolset's docs |
| `wiki` | both | Show the wiki's INDEX (browse rather than search) |
| `wiki-update` | research (primary), both | Ingests external URLs / files into wiki staging |
| `wiki-search` | both | Hybrid BM25 + vector + LLM-rerank search via qmd; keyword-only on a machine set to keyword search (no GPU, 2026-10-02) |
| `wiki-cycle` | research | Full research-cycle orchestrator (discover → ingest → lint → promote) |
| `wiki-discover` | research | RSS / voices / repos discovery — internal to cycle |
| `wiki-list` | research | Queue management — internal to cycle |
| `wiki-claims` | both | Claim extraction + contradiction detection — internal to cycle |
| `wiki-refresh` | both | Stale-entry scan — internal to cycle |
| `wiki-report` | research | Morning report — internal to cycle |
| `wiki-lint` | both | Mechanical + semantic lint |
| `wiki-promote` | both | Stage → promote with backlinks, the backlink rebuild, INDEX and MAP regen (runs `/wiki-verify` as a sub-step with `--verify`) |
| `wiki-verify` | both | Flip an entry unverified → verified via sidecar (truth-status lifecycle; added 2026-05-25, registered to travel 2026-07-07) |
| `wiki-rollback` | both | Roll an entry back to its verified ancestor (pairs with `wiki-verify`; added 2026-05-25, registered to travel 2026-07-07) |
| `wrap-up` | development | Session-end distillation into wiki entries (written 2026-05-12); since 2026-09-26 it also puts each file in `_inbox/skill-suggestions/` to the user (send, keep, drop). Since 2026-09-29 it names each skill's owner from where its usage page sits in `how-to/` (`llm-wiki/` → llm-wiki, any other pack → agent-builder, none → ask); since 2026-10-04 that is the global toolset's `how-to/` (`{{TOOLSET_DIR}}`). A sent file gets a `Sent` line and is left for the owner to collect, so only the owner keeps a copy; a dropped one is archived. Since 2026-10-01 (evening) a note whose owner keeps its notebook here (the registry entry with the owner's bot) is filed into `received/` with the improver's `receive`, without asking |
| `task-list` | both | The project's task list: the At a glance block at the top of `sessions/<persona>/task.md` — one table per owner, then a Backlog table whose Owner column keeps each set-aside task's owner (2026-10-01), numbers never reused, a task removed only on the user's word; `/task-list` or plain speech ("add a task", "delete task 4", "move 5 to the backlog"). Every edit through `wiki-tasks.py` (2026-09-15; not `/tasks`, which is Claude Code's background-jobs panel). Since 2026-10-04 a row is a short overview (Task at most 70 characters, Next at most 60; longer is refused) and a task's details go in a `## Task details` section under the block (`--details`; `show --details`, `show <N>`) |
| `writing-skill-suggestions` | both | Writes a skill suggestion: one four-line note (`Skill`, `Seen in`, `Issue`, `Fix`) in the notebook's `_inbox/skill-suggestions/`, through its own `scripts/skill-suggestion.py` (`add`; self-test floor 34). Moved from agent-builder's library 2026-09-30, so the whole loop ships with `/wrap-up`, which puts each note to the user |
| `improving-skills-from-suggestions` | both | The owner's side of a suggestion: `receive` moves a sent note into the owning library's notebook (`received/`, marked `From:`), `list` / `decide` / `summary` run a pass that proposes changes and records the user's decisions (`scripts/suggestions.py`, self-test floor 53; template `templates/skill-suggestions-README.md`). Runs in whichever library receives the note. Moved from agent-builder's library 2026-09-30 |
| `wiki-triage` | research (primary), both | Gives each untriaged research source in `_inbox/pending/` one owner: moves its ticket into the `_inbox/intake/<folder>/` bucket whose purpose fits (the buckets are the frontmatter of `_inbox/intake/README.md`; `main` is the catch-all), captures the raw for items another reader gets, logs each call as a precedent, tags each other reader once. Every move through `wiki-triage.py` (2026-09-24, task #42) |

## A2. Global agents

Source-of-truth: `agents/<name>/AGENT.md` (+ sidecars; `evals/` stays gold-only)
Install target: `~/.claude/agents/<name>.md` (AGENT.md renamed) + `<name>-*.json` sidecars
Manifest: `TRAVEL_AGENTS` in `scripts/_install_tooling.py` (added 2026-08-20)

| Agent | Project type | Purpose |
|---|---|---|
| `wiki-ingester` | research (primary), both | Spawnable subagent for delegated batch ingestion — full /wiki-update flow per source, one at a time, full-depth reads, staged output, compressed receipt. `/wiki-cycle` Step 2 spawns it (falls back to `general-purpose` if absent). Sidecars: `wiki-ingester-reading-list.json` (skills + pre-reading), `wiki-ingester-config.json` (model_default + confirm_model_each_run — the spawner reads this and asks the user per batch while the confirm flag is true) |
| `wiki-checker` | research (primary), both | A second reader for a staged entry: reads the entry and its raw in full and reports claims the raw does not support, sections the entry skipped, and misquotes, as one JSON report with a `pass` / `fix` verdict. Tools Read, Grep, Glob, Write only (never edits the entry). `/wiki-cycle` spawns one per staged entry whose raw is a transcript of `min_transcript_minutes`+ (default 15) and holds a `fix` entry back from promotion. Sidecar: `wiki-checker-config.json` (`model_default` opus, `min_transcript_minutes`) (2026-09-24, task #42 C3) |

## A3. Pack usage docs (wiki-seed)

Source-of-truth: `wiki-seed/` (the pack page `llm-wiki.md`, plus `user-guide.md`, `commands.md`, `getting-started.md`, `install.md`, `drive-setup.md`) + `skills/<name>/wiki-seed/<name>.md` + `agents/<name>/wiki-seed/<name>.md`
Install target: the global toolset (section G): `how-to/llm-wiki/<page>.md` + `how-to/llm-wiki/skills/<name>.md` + `how-to/llm-wiki/agents/<name>.md`, by every global install and by `--phase docs`. Until 2026-10-04 every project wiki got its own copy

`user-guide.md` is the one-page guide to the whole system (2026-09-25, task #41). Until then it was a file in the old notebook template that no refresh reached, so three copies drifted apart; it moved here so there is one copy and a fix is made once.
Mechanism: `toolset_files()` / `seed_toolset()` in `scripts/_install_tooling.py` (2026-10-04; `seed_pack_docs()` in `new-wiki.py` before, from 2026-09-08)

**Every skill in A and every agent in A2 ships a page; the install warns by name for any that does not** (`undocumented_artifacts()`). One folder per installed package in the toolset's `how-to/` (`how-to/llm-wiki/` here; the agent-factory's packs land as `how-to/<pack>/` beside it); a refresh removes the pages of this pack's skills or agents that no longer ship, and never touches another pack's folder.

## A4. Framework-contract docs

Source-of-truth: `framework-docs/*.md` (six docs, each `framework-contract: true` with a `framework-version`; `bootstrap/framework-docs/` until 2026-10-01, `bootstrap/topic-template/wiki/best-practices/framework/` until 2026-09-26, when the retired `/wiki-init`'s template folder went)
Install target: the global toolset's `wiki/project/best-practices/framework/<name>.md` (section G), by every global install and by `--phase docs`; the skills name it as `{{TOOLSET_DIR}}/wiki/project/best-practices/framework/`. Until 2026-10-04 (from 2026-09-08) every project wiki with `project/` got its own copy, refreshed by `--phase docs --all-notebooks`
Mechanism: `seed_toolset()` in `scripts/_install_tooling.py`, content-compared byte for byte; `--phase docs --check` lists what a refresh would add, replace or remove and exits 1 when anything would change.

**These are the framework's canonical copies.** A project keeps its own conventions in `wiki/project/best-practices/`; an edit made in the toolset is lost on the next refresh.

## B. Global scripts

Source-of-truth: `scripts/<script>.py`
Install target: `~/.claude/wiki-scripts/<script>.py` (`{{WIKI_SCRIPTS_DIR}}` in the skills and agents resolves to it; `{{TOOLSET_DIR}}` to the global toolset's root, 2026-10-04)
Environment (2026-10-04, task #71): `ENV_FILES` (`pyproject.toml`, `uv.lock`, `.python-version`, at the repo root) are copied beside the scripts and `uv sync --locked` builds `.venv` there (`build_tooling_env()`). Every shipped call runs `uv run --project <scripts dir> python <scripts dir>/<script>`; the hooks run that environment's python by its full path (with the scripts folder gone, `uv run --project` exits 2, which a PreToolUse hook turns into a block on every tool call). A machine without uv is refused before anything is written (`UvMissing`), and the installer wrappers ask before installing uv. `--mode status` reports the environment (`env`: current / stale / missing / uv-missing; stale = an environment file differs from the clone or `uv sync --locked --check` fails). Checks: `tests/scripts/test_tooling_env.py`, which also fails on any third-party import in the scripts that `pyproject.toml` does not declare, and on any shipped call to a wiki script without `uv run --project`
Manifest: `TRAVEL_SCRIPTS` (the commands) + `TOOLING_HELPER_SCRIPTS` / `SHARED_HELPER_SCRIPTS` (the `_`-prefixed modules they import) in `_install_tooling.py`

| Script | Purpose |
|---|---|
| `new-wiki.py` | The bootstrap helper behind `/new-wiki`: Phase A / tooling install, Phase B scaffold, `--phase docs [--check]` (the global toolset's docs only, 2026-10-04) |
| `wiki-upgrade.py` | Refresh the global tooling from the recorded bootstrap source: the same install code (`_install_tooling.install_tooling`) that `install-wiki.ps1 -RefreshOnly` / `install-wiki.sh --refresh-only` reach through `new-wiki.py --mode tooling`. Writes its output as UTF-8, so a piped run on Windows no longer stops at the first `→` (2026-10-01). An install that stops partway ends on `⚠️ INSTALL INCOMPLETE` and a log (see Update mechanism). Checks: `tests/scripts/test_wiki_upgrade.py` |
| `wiki-update.py` | File an external source as an entry. The write-time gate lives here: it refuses an entry without a TL;DR, without two Related wiki links (a warning for tier `self`), with its layout out of order, or with frontmatter that would not parse. `--revises <slug>` files a later snapshot of a source (checks the older entry exists, implies `--force`). `--slug-for` exits 2 with near matches when no entry matches. Staged entries' links are checked. `internal://` URLs never count as duplicates, and a duplicate prints `duplicate_of=` (2026-09-15) |
| `wiki-fetch-youtube.py` | YouTube transcript → verbatim raw archive under `raw/` (needs `yt-dlp` on the host) |
| `wiki-fetch-pdf.py` | PDF (URL or local) → extracted text under `raw/` |
| `wiki-fetch-page.py` | A page that shows its text only once JavaScript runs (Threads, Instagram, LinkedIn, Notion, Bluesky; the fallback for X) → raw, in headless Chromium on this machine, saved as Markdown through MarkItDown; og:title when the page title is just the site's name; a paywalled or near-empty page flagged (`paywall=suspected`), never fetched another way; at most two at once. Playwright is in the scripts' environment and the install runs `playwright install chromium` (2026-10-05; it replaced the Node fetcher that ran only in the openclaw container) |
| `wiki-fetch-tweet.js` | An X post → raw, through the public syndication API (node, no login); in the install list since 2026-10-05 (the skills always ran it from here, the list missed it) |
| `wiki-transcribe.py` | Local Whisper (faster-whisper) for media without captions, 2026-10-05: `--url` (a reel, a video, an episode: yt-dlp fetches the audio and the caption) → a raw with the caption and a timestamped transcript, never the comments; `--file` for a local recording. An NVIDIA GPU runs large-v3-turbo and takes one of the search's GPU slots; without one the CPU runs `small`, and audio over `--max-cpu-minutes` (20) exits 4 |
| `wiki-fetch-drive-folder.py` | Google Drive `__FOR CLAUDE/<topic>/` → pending queue, with short-URL resolution and dedup against the wiki's `source_url`s; OAuth reads `--client-secrets`, `$WIKI_DRIVE_CLIENT_SECRETS`, or `~/.config/wiki-cycle/client_secrets.json` (2026-09-15); `--out <run-folder>/drive-fetch.md` also writes the cycle's `drive-fetch.json` beside it (2026-09-24) |
| `wiki-fetch-gmail.py` | The cycle's email step (Step 1.1, 2026-10-03, task #65): reads a Gmail label (`email.label` in the project config) and never queues on its own. `fetch` lists every article link as a numbered candidate (tracking redirects followed, tracking parameters stripped, footer / account / app-store / social-profile links dropped, links already in the wiki or the queue listed as known) and each full-text newsletter as one candidate, saves each email's text in the run folder, and writes the cycle's `email-fetch.json` / `.md`; the session writes `email-review.json` (recommend or skip, with a reason, for every candidate); `queue --approve recommended\|all\|none\|<numbers>` queues the approved ones (an approved full-text email is saved to `raw/` and its ticket carries `raw_path`); `archive` moves the fetched emails to the done label and refuses until `queue` has run; `auth` signs in once. Gmail API, `gmail.modify` scope, token `~/.config/wiki-cycle/gmail-token.json`; the OAuth client is the Drive one, or the client recorded in the Drive token. `--from-dir` / `--resolve-map` run it offline. Checks: `tests/scripts/test_gmail_fetch.py` |
| `wiki-list-add.py` | Add a source to the `_inbox/pending/` queue (URL-dedup across pending + proposed + wiki + done); `--raw-path raw/<file>` records a raw already captured, so the ingest files from it (2026-10-03) |
| `wiki-list-process.py` | Batch-consume `_inbox/pending/` → staged entries |
| `wiki-list-render.py` | Regenerate the human-readable pending-list view |
| `wiki-dequeue.py` | Move already-ingested items to `_inbox/done/`: from the pending queue and, since 2026-10-03, from every intake bucket (where triage leaves a ticket before it is ingested); a file without a `source:` line (a README, the triage log, a handoff note) is never touched. Checks: `tests/scripts/test_dequeue_intake.py` |
| `wiki-promote.py` | Move `_inbox/proposed/<slug>.md` → `wiki/<target_folder>/<slug>.md` (the folder from its sidecar), add backlinks into the related entries' Related sections (never into a framework-contract doc, 2026-09-15), then run the link fixer (scoped to the moved entries), `wiki-reciprocate-backlinks.py` (so no promoted entry is left an orphan, 2026-09-25) and the folder-index and MAP regeneration. An entry whose sidecar is missing, invalid or names no folder is held back (exit 4); `--check` validates staging without moving anything; a folder outside the taxonomy is known when it carries a `README.md` (else a warning, 2026-09-24) |
| `wiki-verify.py` | Sidecar update flipping truth-status to verified (called by `/wiki-verify`) |
| `wiki-rollback.py` | Walk the `revises:` chain to the verified ancestor + write a rollback entry (called by `/wiki-rollback`) |
| `wiki-lint-mechanical.py` | Deterministic lint: broken links, orphans, frontmatter loadability, body checks (warn-only backlog), installed-skill drift, qmd index coverage; a tier-`self` entry without `raw_path` counts as self-authored, not missing (2026-09-15); `--cycle-id` + `--run-folder` write the cycle's `lint-mechanical.json` / `.md` (2026-09-24); a page declaring `standalone: "<reason>"` is listed apart, not as an orphan (2026-09-24); stale-pending flags only our own notes (workflow phrases anywhere, `not yet built` / `TODO:` in tier `self`; frontmatter, quotes, code, link targets skipped; 2026-09-24); the index-coverage advice says `qmd update` alone on a keyword machine (2026-10-02) |
| `wiki-fix-links.py` | Resolve bare-slug / wrong-depth markdown links to the correct relative path |
| `wiki-reciprocate-backlinks.py` | Ensure every outbound `.md` link has a reciprocal BACKLINKS-AUTO block |
| `wiki-index.py` / `wiki-index-per-folder.py` | Regenerate `_INDEX.md` (root / per folder) |
| `wiki-map-compile.py` | Regenerate the always-loaded root `_MAP.md` |
| `wiki-qmd-query.py` | Runs qmd's full search (`qmd query`) for every caller — session, `/wiki-discover`, parallel ingest workers — holding one of three GPU slots (OS file locks; a fourth caller waits; three since the qmd 2.8.3 test of 2026-09-14, two before), with a 120 s timeout that kills the process tree, GPU-full back-off and retry then exit 75 (never a keyword fallback), `--preflight` (the machine's search mode; on a full machine the GPU check, CUDA or Metal, plus a warning when qmd is older than 2.8.3) and `--stats` (per-call wait/run log at `~/.cache/wiki-qmd/searches.jsonl`); `--notebook <name>` scopes a search to one notebook's collection (resolved through the registry; ingest, update and discover always pass it), `--all-notebooks` searches every one; depth is `-k` (results, default 30) and `-C` (the most candidates the reranker may score; default 120, above qmd's ~100 pool of 20 per list — the 8%-of-files sizing was removed 2026-09-23 because it never bound), overridable as `$WIKI_QMD_K` / `$WIKI_QMD_C`; `$WIKI_QMD_INDEX` picks a named qmd index (the skill test baseline's sandbox, 2026-09-15); searches the current project's notebook unless told otherwise; drops `_MAP`/`_INDEX` from results; every search logs qmd's count of candidates reranked, and `--stats` reports it against C; `--depth-check` searches sampled entry titles, reads that count against C (exit 1 when C was reached, 2 when nothing was measured) and logs to `depth-checks.jsonl` (`/wiki-cycle --full` runs it; until 2026-09-23 it compared C with 2C, which could not fail). Added 2026-09-13 when the user retired the workers-use-`qmd search` rule. **Search mode per machine** (2026-10-02, task #63): `search_mode` in `~/.claude/wiki-config.json` is `full` (all of the above) or `keyword` (a machine with no GPU: the helper runs `qmd search`, qmd's keyword index, with the same scoping and filtering, and no model, GPU slot or GPU check; `--depth-check` exits 2). With no GPU the models run on the CPU and take every core: one full search on the CPU used ~9,900 CPU-seconds and hung the laptop without finishing. `--set-mode full\|keyword` switches, refusing `full` while the GPU check fails; the check accepts CUDA or Metal, never Vulkan alone (`gpu_backend()`, which the installer also uses). **The word-pair keyword search** (2026-10-02, task #64): qmd's keyword index needs every word to match, so the helper searches the query's key words together and in every pair (at most 8 key words, 29 searches in parallel, under a second) and fuses them by rank; a keyword machine shows that list. A full machine shows the full search's own top k, then up to `--keyword-extra` (default 20, `$WIKI_QMD_KEYWORD_EXTRA`, 0 = none) entries only the keyword search found, under `## Also found by keyword search` (JSON: `found_by` `keyword`, the ranked rows `full`), never reranked. On 8 real queries the word-pair search found 57 of the full search's top 10 in its top 30 (the query as typed: 25), and 34 of its own top-10 entries were outside the full search's 30. Checks: `tests/scripts/test_search_mode.py` |
| `wiki-search-rerank.py` | Post-filter qmd's `--json` output by truth-status bucket (verified > unverified > temporal > contradicted; rolled_back excluded unless `--include-rolled-back`) — the search spec's surface 1; shipped 2026-09-08. Accepts qmd 2.1's bare-list JSON and `qmd://` file URIs since 2026-09-12 |
| `wiki-session-start.py` | The SessionStart hook: at startup and after `/clear`, prints the paths of the current project's resume files (`sessions/active-context.md`, `sessions/<persona>/handoff.md` + `task.md`, each if present) with the instruction to read them before the first reply, as JSON: `additionalContext` for Claude, and a `systemMessage` the user sees in the terminal at startup — the handoff's `GOAL` line and "send any message for the full recap" (a hook cannot start a model turn; added 2026-09-15 after plain stdout left the user a blank prompt). Paths, not contents: Claude Code keeps only a ~2 KB preview of a hook's output in context (in the first real session, 18.3 KB of contents arrived as a 2 KB preview), so output stays under 2,000 characters. Finds the project's own `.claude/wiki-config.json` (never the machine config in the home folder), resolves the wiki like every wiki script (`_wiki_config.wiki_dir`), persona from the config's `persona` key (default `main`). Anything else — no config, no wiki, no resume files, any error — prints nothing and exits 0. The tooling install adds it to `~/.claude/settings.json` (`hooks.SessionStart`, matcher `startup\|clear`, exec form — `command` = the scripts' environment's python (the installing Python until 2026-10-04), `args` = a `-c` guard + the script, no shell, so cmd.exe never parses it (claude-code #76774); a backup `settings.json.bak-wiki` first; other hooks untouched). Added 2026-09-14 (user: global, silent outside wiki projects) |
| `read-guard.py` | Makes "read this document" mean the whole document, by enforcement (2026-09-18, after a transcript audit found 45 instruction and resume files read only partly since 2026-08-20, each reported as read). A document is `.md .markdown .mdx .rst .adoc .org` (`.txt` left out 2026-09-26: every `.txt` block in the first week was a command's saved output; the same day, `doubt-log.md` and `checkpoints.md` inside `.do-code-change/`, do-code-change's append-only logs, stopped counting too, the user's pick). **PreToolUse** (`Read\|Bash\|PowerShell`) refuses a Read with a `limit` from the top of a document that fits in one Read (≤ 60,000 bytes), a shell `head`/`tail`/`sed -n` on a document or on one piped in, `Get-Content -TotalCount/-Head/-Tail/-First` or a pipe into `Select-Object -First/-Last`, and a shell `cat` of documents over 25,000 bytes combined (the shell would return a preview). Quote- and heredoc-aware, so a commit message or a heredoc body is never read as a command. **Stop / SubagentStop** read the session's own transcript: every document Read this turn is checked against the lines the Read tool reported (`startLine`, `numLines`, `totalLines`), pooled with the session's other Reads of it; one not covered to its last line blocks the stop with the missing ranges, once per turn (`stop_hook_active` lets the second through). That also catches the Read tool's own truncation. Documents the session wrote itself are exempt, and so is a file the same shell command writes (a redirect, `sed -i`, or a `>>` path built from a loop variable), so checking one's own edit is allowed; any error allows the action. Registered by the tooling install for all three events, exec form, like the SessionStart hook. Checks: `tests/hooks/test_read_guard.py` |
| `wiki-tasks.py` | The At a glance task list behind `/task-list`: `show`, `init`, `add [--backlog]`, `set`, `done`, `backlog`, `unbacklog [--owner]`, `remove --confirmed` on `sessions/<persona>/task.md` (persona from the project config); `--details` on add / set / done, `show [<N>] [--details]`, and the 70 / 60-character overview limits (2026-10-04, checks `tests/scripts/test_wiki_tasks_details.py`). Picks each number above every number in the file and records the next free one in a marker comment; refuses a removal without `--confirmed`; keeps the rest of the file as it is (2026-09-15). The `### Backlog` section is always last, after Unassigned, with an Owner column; `Backlog` is refused as an owner name; an older 4-column Backlog section is read with empty Owner cells, filled by `set <N> --owner` (2026-10-01). Checks: `tests/scripts/test_wiki_tasks.py` |
| `wiki-cycle-scope.py` | What `/wiki-cycle` reads, decided by a script: `semantic` (entries added or revised since the last semantic lint, plus this run's staged; `--all` for everything), `claims` (entries with no claims in the index, or revised since it was written, plus staged), `checker` (staged entries whose raw is a transcript of `min_transcript_minutes`+), `checker-log` (one line per checker report in `_inbox/reports/checker-log.jsonl`). "Added" is a file created after the cut-off (git), "revised" is `last_reviewed` on or after it: machine edits such as backlink blocks never count (2026-09-24, task #42 C1/C3) |
| `wiki-triage.py` | The mechanical half of `/wiki-triage`: `buckets` (the config, each reader, who "this session" is; a notebook with no `_inbox/intake/README.md` has one bucket, `main`), `check` (exit 1 on a config problem), `pending`, `route <ticket> --to <folder> --reason … [--raw raw/<file>]` (refuses a folder that is not a bucket, moves the ticket, records `raw_path`, appends to `_inbox/intake/triage-log.md`), `log --last N` (the precedents). Never deletes (2026-09-24) |
| `install-skill.py` (helper) | Copy ONE skill onto the local system with placeholder substitution (`{{WIKI_SCRIPTS_DIR}}`, `{{TOOLSET_DIR}}`) — the per-skill primitive the installer loops over, and Phase A's for `/new-wiki` |
| `_wiki_config.py`, `_entry_checks.py`, `_atomic_io.py`, `_install_tooling.py`, `_markdown.py` (helpers) | Path/registry resolution and the date-time helpers; the shared mechanical entry checks (gate + lint); atomic writes; the install manifests and loop; HTML → Markdown through MarkItDown with a named plain-text fallback (`wiki-update.py --fetch-only`, a full-text email's raw; 2026-10-04, checks `tests/scripts/test_html_markdown.py`) |

## C. Templates

Source-of-truth: `templates/` (project files) and `seed/wiki/` (wiki scaffold files)
Usage: rendered into a new project at `/new-wiki` time (bundled installs also keep a copy at `.claude/wiki-templates/`)

Research/development split removed 2026-06-15 — one merged template set; every project gets the same unified wiki (research/* + project/* + sessions/).

| Template | Purpose | When used |
|---|---|---|
| `CLAUDE.md.tmpl` | Project root CLAUDE.md (unified — does both research + project; carries the precedence rule) | every project init |
| `README.md.tmpl` | Project root README | every project init |
| `.gitignore.tmpl` | Project root .gitignore | every project init |
| `seed/wiki/{HOME,README,_MAP}.md.tmpl` | Wiki scaffold files rendered inside `wiki/` (the full `_INDEX.md` is written beside `wiki/` by `wiki-index.py` on the first filing) | every project init |
| `seed/llm-wiki-readme.md.tmpl` | The wiki root's `README.md` (in-project `llm-wiki/` or the notebook folder) | every project init |
| `seed/global-toolset-README.md`, `seed/how-to/_FRAMEWORK_MANAGED.md` | The global toolset's README and its `how-to/` marker (copied, not rendered) | every global install |
| `feeds.md.tmpl` | The trusted-sources page `_config/feeds.md` beside `wiki/`, the list `/wiki-discover` searches: its six tables with headers only, for the user to fill (or the sources named at `/new-wiki`'s optional question); never overwrites an existing page. `/wiki-discover` offers the same template when a notebook has none (2026-09-26) | project init with `research/` |

The folder taxonomy under `wiki/` lives in `_wiki_config.py` (the single copy; `new-wiki.py` scaffolds from it and the folder guards read it), in two halves since 2026-09-09: `PROJECT_TAXONOMY` = `project/{components,decisions,architecture,patterns,troubleshooting,best-practices}` and `RESEARCH_TAXONOMY` = `research/{active,long-term,tooling,best-practices,interesting-docs}`, plus `sessions/` always. `/new-wiki` asks for each half separately — `stubs` (the half with those subfolders), `empty` (the root only; subfolders appear as `/wiki-update` or `/wrap-up` file into them) or `none` — via `--project-folder` / `--research-folder`; `taxonomy_for()` turns the two answers into the folder list, and the answers are recorded in the project config as `wiki_folders`. `SCAFFOLD_TAXONOMY` is the default (both halves with stubs). `MERGED_TAXONOMY` is the superset the folder guards in `wiki-update.py` / `wiki-promote.py` recognise: it also carries `LEGACY_RESEARCH_TAXONOMY` = `research/{implementation,skills,orchestration}` — the agentic-design notebook's topics that every new wiki used to receive; recognised for existing wikis, no longer created. No framework-contract docs or usage docs are scaffolded into a project (section G).

## D. Configuration

Three files, three scopes:

| File | Scope | Written by | Carries |
|---|---|---|---|
| `~/.claude/wiki-config.json` | machine | Phase A / tooling install; Phase B adds `registry` | `bootstrap_source` (where this clone lives — what `-RefreshOnly`, `/new-wiki --sync` and `--phase docs` read), `install_version`, `last_phase_a`, `drive`, `registry` (the machine-wide fallback pointer to `linked-notebooks.json`, written by the first registry-mode Phase B; lets `--topic <notebook>` resolve from a cwd with no project config, 2026-09-13), `search_mode` (`full` or `keyword`: set by the first global tooling install from the GPU check, never changed by a later one, which only says when it no longer fits; switched with `wiki-qmd-query.py --set-mode`; no key reads as `full`, 2026-10-02). Its `registry` also says where the global toolset is (`_wiki_config.toolset_location()`) |
| `<project>/.claude/wiki-config.json` | project | Phase B | a thin pointer: `tool`, `project_name`, `notebook` + `registry` (registry model) or the in-project wiki location, `skills_install`, `wiki_folders` (the two `stubs\|empty\|none` answers), `drive`; optional `email` (`enabled`, `label`, `done_label`: the Gmail label `/wiki-cycle` reads; set by hand, see the drive-setup page, 2026-10-03) |
| `<vault>/linked-notebooks.json` | vault | Phase B (`_upsert_registry`) | every notebook's root + its two booleans `confirm_before_create` / `confirm_before_promote`; the single source of truth for WHERE a wiki is — every `/wiki-*` script resolves through it (`_wiki_config.py`); optional `wrap_up_commit` (`none`/`commit`/`push`, `/wrap-up`'s Step 7 default), set by hand, not by the scaffold (2026-09-25); the `global-toolset` entry (root only), added by the first global install (2026-10-04) |

The agentmemory MCP wiring from the May draft was removed 2026-05-14 (`-NoAgentmemory` is a no-op kept for back-compat).

## E. Per-project structure (the empty scaffold)

Created by `/new-wiki` Phase B. Two layouts; the `wiki/` folders are whatever the two folder answers chose (section C — `sessions/` always, each half with stubs, empty, or absent):

```
In-project (a wiki inside a code repo):        Notebook in a vault (linked-notebooks.json above it):
<project>/                                     <vault>/notebooks/<name>/
├── .claude/wiki-config.json                   ├── README.md
├── CLAUDE.md, README.md, .gitignore           ├── _config/feeds.md        ← with research/ only: the trusted sources, empty
└── llm-wiki/                                  ├── wiki/                   ← HOME, README, _MAP + the taxonomy (section C)
    ├── README.md                              ├── raw/sessions/
    ├── _config/feeds.md  (with research/)     ├── _inbox/{pending,proposed,done,rejected,reports,skill-suggestions}/   (first use)
    ├── wiki/                                  └── _signals/               ← truth-status sidecars (first use)
    ├── raw/sessions/
    └── _inbox/, _signals/  (first use)
```

Phase B creates the folders above except `_inbox/` and `_signals/`, which the queue, staging and verify scripts create on first use.

The flat layout exists so that every notebook in a vault has the same shape (qmd collections, `_inbox/` staging and `_signals/` sidecars all assume `<root>/wiki/`); the calling code repo then carries only the thin pointer in `.claude/wiki-config.json` and a `CLAUDE.md` that @-imports the notebook's `_MAP.md` by absolute path, and the command reference from the global toolset.

## G. The global toolset (2026-10-04, task #25)

One notebook holds every global tooling doc once, for every project (the user, 2026-10-04: no per-notebook copies). Where: the registry entry `global-toolset`; with a registry but no entry, `<registry folder>/notebooks/global-toolset`, where the first global install creates and registers it; with no registry, `~/.claude/global-toolset` (`_wiki_config.toolset_location()`).

```
global-toolset/
├── README.md                                 (seed/global-toolset-README.md)
├── how-to/_FRAMEWORK_MANAGED.md              (seed/how-to/)
├── how-to/llm-wiki/                          the pack usage docs (section A3)
├── how-to/<pack>/                            each other pack, written by its own installer (agent-builder's)
└── wiki/project/best-practices/framework/    the six framework-contract docs (section A4)
```

Kept by `seed_toolset()` (`_install_tooling.py`) as step 7 of every global install, and by `new-wiki.py --phase docs`. `--mode status` reports it as `toolset` (current / stale / missing, with the files to add, replace and remove); stale docs make the global state stale, a missing toolset makes it partial. It has no `research/`, no sessions, no qmd collection (search stays project-only) and is never edited by hand. The skills and agents name it through `{{TOOLSET_DIR}}`; a rendered project `CLAUDE.md` imports `<toolset>/how-to/llm-wiki/commands.md` by absolute path.

## F. External dependencies

| Dependency | Used by | Notes |
|---|---|---|
| [uv](https://docs.astral.sh/uv/), Git | everything | the only hard requirements for the global install (2026-10-04: uv replaced "Python 3.10+"; it builds the scripts' environment from `uv.lock` and fetches the pinned Python itself; the installer wrappers ask before installing uv) |
| `qmd` (host npm install) | `/wiki-search`, `wiki-qmd-query.py` (every full search), `wiki-search-rerank.py`, the lint's index-coverage section | each wiki is a qmd collection (`qmd collection add <wiki>`; `qmd update && qmd embed` after a batch, `qmd update` alone on a keyword machine). `qmd query` runs three bundled models through node-llama-cpp and needs a GPU backend; without a CUDA runtime it falls back to Vulkan, where generation hung indefinitely (root-caused 2026-09-12, resolves the 2026-09-02 note). BM25 `search` needs no model |
| CUDA 13.1+ runtime (`winget install --id Nvidia.CUDA --version 13.2 --exact --override "-s cudart_13.2 cublas_13.2"`) | `qmd query` via node-llama-cpp | machine-level, NVIDIA Windows only; runtime + cuBLAS is enough (no compiler, no driver). Verify: `node-llama-cpp inspect gpu` prints `CUDA: available`; `/wiki-search` runs that preflight and stops on failure. Optional — a machine with no CUDA or Metal GPU is set to keyword search at install (`qmd search`, no model) |
| `yt-dlp`, `pypdf`, `pyyaml`, `requests`, the Google API client libraries, `markitdown[all]` (HTML → Markdown, 2026-10-04; every extra since the same evening: PDF, Office, Outlook, audio and YouTube transcripts; the environment is ~420 MB) | the fetchers, triage, the entry checks | in the scripts' uv environment (`pyproject.toml` + `uv.lock`), never installed on the machine (2026-10-04) |
| `faster-whisper`, `ctranslate2`, `av` (base); `nvidia-cublas-cu12`, `nvidia-cudnn-cu12` (the `gpu` extra, ~1 GB) | `wiki-transcribe.py` | in the scripts' uv environment; the installer adds `--extra gpu` only where `nvidia-smi` answers (`env_extras()`), and the status check syncs with the same extras. The CUDA 12 libraries run beside a system CUDA 13 (tested 2026-10-05); `av` stays below 16 (16+ breaks faster-whisper 1.2.1). Whisper models download on first use to the Hugging Face cache (~1.6 GB for large-v3-turbo, ~0.5 GB for small) |
| Google OAuth client secrets | `wiki-fetch-drive-folder.py`, `wiki-fetch-gmail.py` | `~/.config/wiki-cycle/client_secrets.json` (Gmail can also reuse the client in the Drive token); the Google Cloud project needs the Drive API, and the Gmail API for email; see the `drive-setup` page |

## Update mechanism (shipped)

**Source-of-truth lives in this repo's shipped folders** (`skills/`, `scripts/`, `agents/`, `templates/`, `seed/`, `wiki-seed/`, `framework-docs/`; inside `bootstrap/` until 2026-10-01). When a skill, script or doc changes there, the installed copies go stale in two places, each with its own refresh:

- **Global tooling** (`~/.claude/skills/`, `~/.claude/wiki-scripts/`, `~/.claude/agents/`): `install-wiki.ps1 -RefreshOnly` / `install-wiki.sh`, or `wiki-upgrade.py` directly — the same copy loop (`_install_tooling.py`), which refuses any skill or agent whose frontmatter does not parse. `/new-wiki --sync` re-runs Phase A, which refreshes only the global `/new-wiki` skill. `new-wiki.py --mode status` (`global_tooling_status()` in `_install_tooling.py`, 2026-09-09) is the drift detector: it compares every installed skill, script and agent with the clone and reports installed / stale / partial / missing. `/new-wiki` reads it before its skills question and Phase B in global mode refuses a partial or missing set (or installs it once with `--install-global-if-missing`, which the installer wrappers pass); a stale set is named, never re-copied by the scaffold. The lint's installed-skill section verifies only that every installed SKILL.md / agent file parses. **An install that stops partway** (2026-10-01, task #61) says so: `install_tooling()` records each script, skill and agent as it lands and raises `InstallIncomplete`; every entry point (`wiki-upgrade.py`, `new-wiki.py --mode tooling` behind both installer scripts, Phase B's `--install-global-if-missing`) passes it to `report_incomplete()`, which writes a log first (`~/.cache/llm-wiki/install-errors/install-<time>.log`, or `$WIKI_INSTALL_LOG_DIR`: the command, where it stopped, the error, what is and is not installed, the traceback, how to finish), then prints one `⚠️ INSTALL INCOMPLETE: stopped at <step> (<error>); <counts>; <log>` line and exits 1. A missing source is still the plain error, since nothing was written. Every shipped command that prints non-ASCII writes UTF-8 (`tests/scripts/test_utf8_output.py` holds that). A global install also sets the machine's search mode the first time, from the GPU check (`configure_search_mode()`; `full` with CUDA or Metal, else `keyword`), and after that only reports it: a keyword machine with a GPU now available, or a full machine whose GPU check fails, is named in the summary with the `--set-mode` command (2026-10-02).
- **The global toolset's docs** (`how-to/llm-wiki/`, the root marker, `wiki/project/best-practices/framework/`): every global install refreshes them; `new-wiki.py --phase docs` does only that, `--check` reports without writing. No project notebook holds a copy since 2026-10-04, so a docs change reaches one place.
- **A bundled install** (skills copied into the project): re-run Phase B against the same folder with `--force` (non-destructive: existing `CLAUDE.md` / `README.md` / `.gitignore` are kept).

## The May 2026 design questions, as they resolved

1. **`bootstrap_source` locks the install to one checkout** — it does, by design; it is one field in `~/.claude/wiki-config.json` and re-running the installer from a new clone rewrites it. No relocate skill was needed.
2. **Update notifications** — none; the refresh is idempotent and cheap, so it is run rather than detected. The lint's installed-skill section checks loadability, not staleness.
3. **Versioning** — the six framework-contract docs carry `framework-version`; every skill and the agent carry `last_reviewed` / `review_after` / `reviewed_for_model`; `install_version` is a date stamp. Extending `framework-version` to the other scaffolded files is on the roadmap.
4. **Test mode** — `--dry-run` on every phase; `--check` on `--phase docs`.
5. **OS support** — `install-wiki.sh` covers Mac/Linux for Claude Code; Cursor is Windows-only (`-Tool cursor`).

Everything listed in this file ships; the manifests in `_install_tooling.py` are the authoritative lists.
