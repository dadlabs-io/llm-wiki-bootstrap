# LLM-Wiki Install Inventory

Authored 2026-05-12. The complete list of pieces that travel when `/new-wiki` runs the install. Updated as new pieces are added.

## Principle

**Structure travels, content doesn't.** A new project gets the wiki skeleton + skills + scripts + conventions + templates. It does NOT get the agentic-design (or any other existing topic's) entries — those stay where they are as their own topic in the vault.

## Categories

- **A. Global skills** — installed once at `~/.claude/skills/`, used in every Claude Code session
- **B. Global scripts** — installed once at `~/.claude/wiki-scripts/`, invoked by skills
- **C. Templates** — copied as needed when scaffolding a new project
- **D. Configuration** — written once per machine (`~/.claude/wiki-config.json`, `~/.claude/settings.json`)
- **E. Per-project structure** — created by `/wiki-init` per topic (empty scaffold)
- **F. External dependencies** — `npx`-installed runtimes (agentmemory)

---

## A. Global skills

Source-of-truth: `bootstrap/workflows/llm-wiki/skills/<skill>/SKILL.md`
Install target: `~/.claude/skills/<skill>/SKILL.md`

| Skill | Project type | Purpose |
|---|---|---|
| `new-wiki` | both | The bootstrap orchestrator (to be written) |
| `wiki-init` | both | Scaffolds a new topic in the vault |
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

## B. Global scripts

Source-of-truth: `bootstrap/workflows/llm-wiki/scripts/<script>.py`
Install target: `~/.claude/wiki-scripts/<script>.py`

| Script | Purpose |
|---|---|
| `wiki-init.py` | Scaffold a topic folder structure + README + INDEX |
| `wiki-list-add.py` | Add URL to topic's `_inbox/pending/` queue (URL-dedup across pending+proposed+wiki+done) |
| `wiki-list-render.py` | Regenerate human-readable pending-list view |
| `wiki-lint-mechanical.py` | Deterministic lint: broken links, orphans, raw_path integrity, stale-pending, missing frontmatter |
| `wiki-reciprocate-backlinks.py` | Ensure every outbound `.md` link has a reciprocal BACKLINKS-AUTO section |
| `wiki-index-per-folder.py` | Regenerate `_INDEX.md` per folder |
| `wiki-map-compile.py` | Regenerate root-level `_MAP.md` (~2900 tokens, always-loaded) |
| `wiki-fetch-drive-folder.py` | Google Drive `__FOR CLAUDE/<topic>/` → pending queue + cleanup |
| `wiki-promote.py` | Move `_inbox/proposed/<folder>/<slug>.md` → `wiki/<folder>/<slug>.md` + backlinks |
| `wiki-verify.py` | Sidecar update flipping truth-status to verified (called by /wiki-verify) |
| `wiki-rollback.py` | Walk `revises:` chain to verified ancestor + write rollback entry (called by /wiki-rollback) |
| `new-wiki.py` | The bootstrap helper (to be written) |

## C. Templates

Source-of-truth: `bootstrap/workflows/llm-wiki/templates/`
Install target: `~/.claude/wiki-templates/`
Usage: copied/rendered into a new project at `/new-wiki` time

Research/development split removed 2026-06-15 — one merged template set; every project gets the same unified wiki (research/* + project/* + sessions/).

| Template | Purpose | When used |
|---|---|---|
| `CLAUDE.md.tmpl` | Project root CLAUDE.md (unified — does both research + project) | every project init |
| `README.md.tmpl` | Project root README | every project init |
| `.gitignore.tmpl` | Project root .gitignore | every project init |
| `seed/wiki/{HOME,README,_MAP,_INDEX}.md.tmpl` | Wiki scaffold files rendered inside `llm-wiki/wiki/` | every project init |

Folder taxonomies per project type:

```
Research topic (matches agentic-design):       Development topic (new pattern):
  wiki/active/                                    wiki/components/
  wiki/long-term/                                 wiki/decisions/
  wiki/tooling/                                   wiki/architecture/
  wiki/best-practices/                            wiki/patterns/
  wiki/implementation/                            wiki/troubleshooting/
  wiki/skills/                                    wiki/best-practices/
  wiki/orchestration/                             wiki/troubleshooting/
  wiki/interesting-docs/
```

Both topic types share: `wiki/`, `raw/`, `raw/sessions/`, `_inbox/{pending,proposed,done,rejected}/`, `_inbox/reports/`, `_signals/`, `_config/`, `_INDEX.md`, `_MAP.md`.

## D. Configuration

Source-of-truth: written by `/new-wiki` Phase A
Install target: `~/.claude/`

| File | Purpose | Written when |
|---|---|---|
| `~/.claude/wiki-config.json` | Vault root path + default topic + project-type defaults | `/new-wiki` first run |
| `~/.claude/settings.json` MCP entry for agentmemory | Wires agentmemory MCP server | `/new-wiki` first dev-project run only |

Shape of `~/.claude/wiki-config.json` (proposal):

```json
{
  "vault_root": "C:/github.com/workflows-core/docker/shared/openclaw/vault/wikis",
  "default_topic": null,
  "skills_installed_at": "~/.claude/skills",
  "scripts_installed_at": "~/.claude/wiki-scripts",
  "templates_installed_at": "~/.claude/wiki-templates",
  "agentmemory_wired": true,
  "agentmemory_server_url": "http://localhost:7890",
  "install_version": "2026-05-12",
  "bootstrap_source": "C:/github.com/workflows-core/bootstrap/workflows/llm-wiki"
}
```

The `bootstrap_source` field is what enables the update mechanism (see "Update mechanism" below).

## E. Per-project structure (the empty scaffold)

Created by `/wiki-init <topic>` inside the vault at `<vault>/<topic>/`. No content copied — just the structural skeleton.

```
<vault>/<topic>/
├── README.md                  ← topic scope ("in scope / out of scope")
├── _INDEX.md                  ← will be regenerated as entries accrete
├── _MAP.md                    ← always-loaded orientation (placeholder until entries exist)
├── _config/                   ← per-topic config (drift-watch list, etc.)
├── _signals/                  ← memory signals sidecar JSON (Gap #1 — currently empty)
├── _inbox/
│   ├── pending/               ← queue tickets
│   ├── proposed/              ← staged entries
│   ├── done/                  ← processed queue tickets
│   ├── rejected/              ← rejected entries
│   └── reports/               ← per-cycle artifacts
├── raw/                       ← immutable WAL
│   └── sessions/              ← session-transcript snapshots (development projects)
└── wiki/                      ← the entries themselves
    └── <folder taxonomy per project type>
```

Plus, **per-project codebase** (separate folder, e.g. `C:\github.com\<project>\`):

```
<project>/
├── CLAUDE.md                  ← @imports the vault MAP
├── README.md                  ← project description
├── .gitignore                 ← standard ignores
└── (your codebase)
```

## F. External dependencies

| Dependency | Install command | When |
|---|---|---|
| `agentmemory` | `npx @agentmemory/agentmemory` | First dev-project on the machine |
| `qmd` | `npm install -g @qmd/qmd` (host) or via docker | Already installed on this machine |
| `yt-dlp` | host-installed | Already installed on this machine |

## Update mechanism

**Source-of-truth lives in `bootstrap/workflows/llm-wiki/`.** When you edit a skill or script there, the installed copies at `~/.claude/skills/` and `~/.claude/wiki-scripts/` go stale.

Proposed: `/new-wiki --sync` (or `/install-sync` as a sister skill).

```
/install-sync
  → reads ~/.claude/wiki-config.json for bootstrap_source path
  → diffs bootstrap/workflows/llm-wiki/skills/ vs ~/.claude/skills/
  → diffs bootstrap/workflows/llm-wiki/scripts/ vs ~/.claude/wiki-scripts/
  → diffs bootstrap/workflows/llm-wiki/templates/ vs ~/.claude/wiki-templates/
  → shows the diff
  → asks: "sync these? (yes/no/review)"
  → on yes: copies bootstrap → installed
  → bumps install_version in wiki-config.json
```

The dog-fooding pattern means: edit a skill in `bootstrap/` while working in workflows-core, the local `.claude/skills/<skill>/` updates via the existing `setup-antigravity-workflow.ps1` sync (or a new Claude-Code-only equivalent). Then `/install-sync` propagates to the global `~/.claude/skills/`.

**This is exactly the sync pattern workflows-core already uses internally — just extended to a global install target.** The mechanism doesn't need to be invented; the equivalent of `scripts/check-sync.py` runs against `~/.claude/skills/` instead of against `<project>/.agent/`.

## Migration sequence

For an existing user (us, today) who wants to move from "skills only work inside workflows-core CWD" to "skills work globally":

1. Run `/install-sync --first-time` — copies skills + scripts + templates to `~/.claude/`, writes `wiki-config.json`
2. Restart Claude Code — picks up global skills
3. Now `/wiki-update`, `/wiki-cycle`, `/wrap-up`, etc. work from any CWD

For a new user (e.g., new machine):

1. `git clone workflows-core` 
2. Run `/new-wiki` (from inside workflows-core, where the skills are still local) — Phase A handles everything global
3. Phase B creates the actual project
4. Future projects: `/new-wiki` works from anywhere

## Open design questions

1. **`bootstrap_source` field** in wiki-config.json — locks the global install to a specific workflows-core checkout. If the user moves workflows-core, the global install breaks. Mitigation: make it configurable + add an `/install-relocate` skill.
2. **Update notifications** — should `/wrap-up` and `/wiki-cycle` warn when bootstrap is newer than installed copies? Probably yes, as a one-line "skills out of date — run /install-sync" warning.
3. **Versioning** — should each skill carry a version frontmatter and the install track per-skill versions? Probably yes, eventually. For v1 just a single `install_version` in wiki-config.json.
4. **Test mode** — `/new-wiki --dry-run` that prints what would happen without writing anything. Worth adding.
5. **OS support** — paths above are Windows-flavored. Need parallel paths for Linux/macOS. Path normalization in `new-wiki.py` handles this.

## Status as of 2026-05-12

| Piece | Status |
|---|---|
| Inventory document | ✅ this file |
| `/wrap-up` skill | ✅ written, installed locally for dog-fooding |
| `/new-wiki` skill | ⬜ pending design confirmation + write |
| `new-wiki.py` helper | ⬜ pending |
| Templates (CLAUDE.md, README.md, .gitignore) | ⬜ pending |
| `wiki-config.json` config schema | ⬜ proposed above, not yet written |
| Sync mechanism | ⬜ designed above, not implemented |
| Global install location | ⬜ designed (`~/.claude/skills/`, `~/.claude/wiki-scripts/`) — not yet populated |

Next: validate `/wrap-up` by using it on this very session, then proceed to `/new-wiki`.
