---
name: new-wiki
description: "Scaffold a new project with the LLM-wiki framework. Checks the global tooling first (use it, install it once, or bundle — never re-copies an installed set), then a two-round interview: name + review gate; description, project folder (stubs / empty / none), research folder (stubs / empty / none), where the wiki lives. Every project gets one merged wiki; each half is opt-in. Sets up llm-wiki/ (or a notebook in the vault), the wiki folders, CLAUDE.md and the project config. Use when the user says \"new project\", \"create a new wiki\", \"install a new wiki\", \"set up a new wiki\", \"bootstrap a project\", \"start a new project\", or types \"/new-wiki\"."
last_reviewed: 2026-09-09
review_after: 2026-12-09
reviewed_for_model: claude-fable-5-1
---

# /new-wiki

Conversational scaffold for a new project. The only global thing is the tooling in `~/.claude/` (this skill, the other wiki skills, the scripts, the agent); everything else is per-project.

## Layout this skill creates

```
<target>/                              ← the code project (e.g., C:\github.com\fitness-app)
├── .claude/
│   ├── wiki-config.json               ← points at the global tooling + the wiki's location
│   ├── skills/, wiki-scripts/, wiki-templates/   ← bundled mode ONLY (global mode copies nothing here)
│   └── settings.json                  ← (legacy; not written any more)
├── CLAUDE.md                          ← imports the wiki README and _MAP.md
├── README.md
└── .gitignore

Wiki content, one of two places (Q6):
  notebook in the vault (default)      C:\github.com\project-notebooks\notebooks\<slug>\   ← registered in linked-notebooks.json
  inside the project                   <target>\llm-wiki\

Either way the wiki root holds:
├── README.md
├── how-to/llm-wiki/                   ← pack usage docs (framework-managed)
├── wiki/
│   ├── HOME.md, README.md, _MAP.md, _INDEX.md
│   ├── project/                       ← Q4: stubs | empty | none   (what we build; /wrap-up files here)
│   │   ├── components/ decisions/ architecture/ patterns/ troubleshooting/   ← "stubs"
│   │   └── best-practices/framework/  ← the six framework-contract docs (stubs AND empty; skipped for none)
│   ├── research/                      ← Q5: stubs | empty | none   (what we ingest; /wiki-update files here)
│   │   └── active/ long-term/ tooling/ best-practices/ interesting-docs/    ← "stubs"
│   └── sessions/                      ← always (per-persona journals + dashboards, /wrap-up)
└── raw/sessions/
```

Cursor variant: substitutes `.cursor/` for `.claude/`, always bundles, and generates `.cursor/rules/<skill-name>.mdc` from each SKILL.md.

> **Both halves are opt-in.** A wiki with neither `project/` nor `research/` is a plain notes notebook (only `sessions/` is created; the framework-contract docs are skipped, the same rule `--phase docs` applies). A wiki that later needs the other half just creates the folder — every script resolves folders on disk first. Neither half is ever created with the old agentic-design research topics (implementation, skills, orchestration); those are recognised for existing wikis, not scaffolded.

## Flow at a glance

```
User: /new-wiki [name]
   ↓
Step 0.0  state check  — python new-wiki.py --mode status  (global tooling: installed | stale | partial | missing)
   ↓
Round 1 (AskUserQuestion, 2 questions)
   Q1  project name (slug)
   Q2  review gate (yes = manual, default | no = auto)
Round 2 (AskUserQuestion, 4 questions — built from the slug)
   Q3  description
   Q4  project folder?   stubs (Recommended) | empty | none
   Q5  research folder?  stubs (Recommended) | empty | none
   Q6  where the wiki lives: notebook in the vault (Recommended) | inside the project
Round 3 (only when needed, ≤2 questions)
   Q7  skills — ONLY when the state check says partial or missing: install globally now + use it (Recommended) | bundle into the project
   Q8  Drive — ONLY when ~/.claude/wiki-config.json has drive.enabled true: use Drive for this project? + subfolder
   ↓
Plan summary (tool, target folder, folder tree, skills line, Drive line) → wait for "yes" / "go" / "create"
   ↓
Phase B — python new-wiki.py --phase B ...   (Phase A already done by install-wiki.ps1)
   B1.  mkdir <target> + git init (skipped inside an existing repo)
   B2–4. Copy skills / scripts / templates into the project           — bundled mode only
   B5.  Seed how-to/ (pack usage docs)
   B6.  Create the wiki folders from Q4 + Q5 (+ sessions/)
   B6.1 Land the framework-contract docs at wiki/project/best-practices/framework/ (when project/ exists)
   B7.  Render CLAUDE.md / README.md / .gitignore (never overwrites an existing one)
   B8.  Write .claude/wiki-config.json (+ the registry entry for a vault notebook)
   B9.  Drive OAuth walkthrough (only if Drive is on)
   B11. JSON summary + next steps
```

## Step-by-step contract

### Step 0.0 — State check (run this BEFORE asking anything)

Read `~/.claude/wiki-config.json` for `bootstrap_source` (see "Required: the bootstrap-source path" below if it is missing), then:

```
python "<bootstrap_source>/bootstrap/scripts/new-wiki.py" --mode status
```

Writes nothing. Prints JSON with `state` — one of:

| `state` | Meaning | What to do |
|---|---|---|
| `installed` | every skill, script and agent in the manifests is in `~/.claude/` and matches the bootstrap clone | use it; no question, no reinstall |
| `stale` | all present, but some installed copies differ from the clone (`stale_skills` / `stale_scripts` / `stale_agents` list them) | use it; no question; the plan summary names the differing files and says `install-wiki.ps1 -RefreshOnly` refreshes them when the user wants |
| `partial` | some pieces missing (`missing_*` list them) | ask Q7 |
| `missing` | none of the wiki skills are installed (only `/new-wiki` from Phase A, or nothing) | ask Q7 |

Also note whether the current folder has a `.cursor/` directory (→ tool `cursor`; otherwise `claude-code`). The tool is stated in the plan summary, not asked.

**Never re-copy an installed set from here.** A user who wants the current copies runs `install-wiki.ps1 -RefreshOnly` (or `wiki-upgrade.py`); this skill only ever installs the tooling when it is partial or missing, once, via `--install-global-if-missing`.

### Step 0 — Discovery (two rounds of `AskUserQuestion`; never plain-text Q&A, never silent defaults)

**Use the `AskUserQuestion` tool with selectable options.** Every option is a concrete, fully-resolved value — no placeholders like `<slug>`. The tool adds `Other` (free text) itself; don't add one. Put `(Recommended)` on the default so it is one click. Round 2 depends on the slug, so the name is asked first.

**Round 1 (2 questions)**

**Q1 — Project name (slug).** Default: slugify what the user said (lowercase, dashes for non-alphanumerics, trimmed); `new-project` if they said nothing. Option: `fitness-app (Recommended)`.

**Q2 — Review gate.** "Do you want to review new wiki entries before they are filed and published?"
- `Yes — show me candidates and confirm before publishing (Recommended)` → `--confirm-before-create true --confirm-before-promote true`
- `No — file and publish automatically` → both `false`

This one answer sets two independent booleans (`confirm_before_create` for `/wrap-up` Step 2, `confirm_before_promote` for Step 6). They live in the registry entry for a vault notebook (`linked-notebooks.json`), in `.claude/wiki-config.json` for an in-project wiki, and either can be flipped later by asking.

**Round 2 (4 questions, all built from the slug)**

**Q3 — Description.** Options: `Wiki for fitness-app (Recommended)` and one plain alternate; the user free-texts anything else.

**Q4 — Project folder?** "Do you want a `project/` folder (what we build — decisions, components, patterns, troubleshooting; `/wrap-up` files here)?"
- `Yes, with the default stubs (Recommended)` → `--project-folder stubs`: `components/ decisions/ architecture/ patterns/ troubleshooting/ best-practices/`, plus the six framework-contract docs under `best-practices/framework/`
- `Yes, empty` → `--project-folder empty`: `project/` plus the framework docs; subfolders appear as `/wrap-up` files into them
- `No` → `--project-folder none`: no `project/`, framework docs skipped

**Q5 — Research folder?** "Do you want a `research/` folder (what we ingest — articles, videos, papers; `/wiki-update` files here)?"
- `Yes, with the default stubs (Recommended)` → `--research-folder stubs`: `active/ long-term/ tooling/ best-practices/ interesting-docs/`
- `Yes, empty` → `--research-folder empty`: `research/` only; `/wiki-update` proposes and creates a subfolder on the first ingest
- `No` → `--research-folder none`

**Q6 — Where the wiki lives.**
- `Notebook in the vault — C:\github.com\project-notebooks\notebooks\fitness-app (Recommended)` → `--vault-root C:\github.com\project-notebooks\notebooks --registry C:\github.com\project-notebooks\linked-notebooks.json`. The code project carries only `.claude/wiki-config.json` (+ CLAUDE.md etc.); the wiki is registered in `linked-notebooks.json`. macOS/Linux default vault: `~/proj/project-notebooks`.
- `Inside the project — C:\github.com\fitness-app\llm-wiki` → neither flag.

**Round 3 (only when needed)**

**Q7 — Skills** (only when the state check said `partial` or `missing`):
- `Install the global tooling now and use it (Recommended)` → `--skills-install global --install-global-if-missing` (one install into `~/.claude/`, then the project points at it; Claude Code needs a restart afterwards)
- `Bundle the skills into this project` → `--skills-install bundled` (self-contained, version-pinned; Cursor always bundles)

**Q8 — Drive** (only when `~/.claude/wiki-config.json` has `drive.enabled: true`): "Ingest from your Drive folder for this project?" `Yes — __FOR CLAUDE/fitness-app (Recommended)` / `No`. → `--drive-enabled yes --drive-subfolder fitness-app` or `--drive-enabled no`. When Drive is not enabled globally, don't ask; pass `--drive-enabled no`.

### Step 0.5 — Plan summary, then wait

Show one block and wait for "yes" / "go" / "create":

```
Tool:            claude-code
Project:         fitness-app — "Wiki for fitness-app"
Target folder:   C:\github.com\fitness-app          ← the cwd when its leaf name equals the slug, else C:\github.com\<slug>; say so to change it
Wiki content:    C:\github.com\project-notebooks\notebooks\fitness-app  (registered notebook)
Folders:         wiki/project/{components,decisions,architecture,patterns,troubleshooting,best-practices/framework}
                 wiki/research/{active,long-term,tooling,best-practices,interesting-docs}
                 wiki/sessions/
Skills:          global — installed and current (16 skills, 26 scripts, 1 agent in ~/.claude)
                 [or: installed; 4 files differ from the clone — `install-wiki.ps1 -RefreshOnly` refreshes them when you want]
                 [or: will be installed now (missing), then used]
Drive:           off
Review gate:     manual (confirm before filing and before publishing)
```

Every line is overridable by saying so; a changed line is re-shown before running.

### Step 1 — Run Phase B

**TOOL CHOICE — IMPORTANT**:
- **Windows**: invoke `python new-wiki.py ...` via the **PowerShell tool**, not the Bash tool. Bash → PowerShell argument bridging mangles empty quoted strings (`--project-description ""` collapses, the next flag becomes the description, exit 2). If the PowerShell tool is denied, ask the user to run the command themselves — do NOT fall back to `bash` → `powershell.exe ...`.
- **macOS/Linux**: the Bash tool directly.

```bash
python "<bootstrap_source>/bootstrap/scripts/new-wiki.py" \
  --phase B \
  --tool <claude-code|cursor> \
  --project-name <slug> \
  --project-description "<desc>" \
  --target-folder <path> \
  --project-folder <stubs|empty|none> \
  --research-folder <stubs|empty|none> \
  --skills-install <global|bundled> \
  [--install-global-if-missing]            `# Q7 first option only` \
  --confirm-before-create <true|false> \
  --confirm-before-promote <true|false> \
  [--vault-root <vault>/notebooks --registry <vault>/linked-notebooks.json]   `# Q6 notebook; omit both for in-project` \
  --drive-enabled <yes|no> \
  [--drive-subfolder <slug>]
```

Phase B in global mode checks the tooling itself: it refuses (exit 1, with the fix named) when the global set is partial or missing and `--install-global-if-missing` was not passed; it warns and continues when the set is merely stale; it never re-copies an installed set. The script returns a JSON summary on stdout (`wiki_folders`, `global_tooling`, `global_tooling_installed_now`, `needs_restart`, `next_steps`).

### Step 2 — Read back the summary + post-install reminders

`needs_restart: true` means the global tooling was installed during this run — tell the user to restart Claude Code before the other `/wiki-*` skills will appear.

Then a tailored "you're ready" message, only for the halves that exist:

- **research/ present** — ingest: `/wiki-update <url>` ad-hoc, or drop links into Drive (`<parent>/<slug>/`) and `/wiki-cycle` to discover → ingest → lint → promote. Source tiers T1 primary / T2 vendor / T3 expert / T4 community, set with `--tier`. With `research/` empty: the first `/wiki-update` proposes a subfolder and creates it.
- **project/ present** — capture: as you code/decide/debug, the agent files durable items (decisions, components, architecture, patterns, troubleshooting) to `_inbox/proposed/` (beside `wiki/`) inline; `/wrap-up` at session end catches the rest.
- always — `/wiki-promote --review` to approve staged entries; `/wiki-search "<query>"` to look things up; ask in plain English ("what commands do I have", "show me the wiki").

End with: "Read `how-to/llm-wiki/commands.md` for the full command reference, or `how-to/llm-wiki/getting-started.md` for the first-hour walkthrough. You can also ask me anything in plain English — I have these docs loaded as context."

### Step 3 — Don't

- Don't skip the state check, and don't ask the skills question when the state is `installed` or `stale` — that is the "reinstall at the top every time" this skill was rewritten (2026-09-09) to stop.
- Don't proceed without the plan summary being confirmed.
- Don't overwrite an existing project folder without `--force` unless the user explicitly OKs it (`--force` is non-destructive to `CLAUDE.md` / `README.md` / `.gitignore`).
- Don't ask for a project type — removed 2026-06-15; the two folder questions replaced the last trace of it.
- Don't edit `<target>/.claude/skills/` by hand in a bundled install — edit `<bootstrap_source>/bootstrap/skills/` and re-sync.

## Drive OAuth walkthrough (Phase B, only if `--drive-enabled yes`)

The Drive token is **machine-global** (cached at `~/.config/wiki-cycle/drive-token.json`), not per-project. If you've already done OAuth on this machine for a previous project, Phase B reuses the cached token.

If the token isn't cached, Phase B triggers the OAuth flow:
1. A browser window opens at `accounts.google.com`
2. User signs in with the Google account that holds the Drive folder
3. User approves the "See, edit, create, and delete all of your Google Drive files" scope (full `drive`)
4. Token caches; next time, Phase B reuses it

If `~/.config/wiki-cycle/client_secrets.json` is missing, the helper prints instructions to create OAuth credentials at https://console.cloud.google.com/apis/credentials (Desktop application) and download the JSON to that path.

## Update mode

`/new-wiki --sync` re-runs Phase A — refreshes the global `/new-wiki` skill from the current `bootstrap_source`. Use after `git pull` on the llm-wiki-bootstrap clone. The full global tooling (every skill, script and agent) is refreshed by `install-wiki.ps1 -RefreshOnly` / `wiki-upgrade.py`; `--mode status` shows whether that is needed.

To sync a bundled project install with the current bootstrap (refresh the project's skills + scripts), re-run Phase B against the same target folder with `--force`. To refresh only a project's **framework-managed docs** — the pack usage docs (`how-to/llm-wiki/`: the pack page, one page per skill, one per agent) and, since 2026-09-08, the six framework-contract docs at `wiki/project/best-practices/framework/` — run `python <bootstrap_source>/bootstrap/scripts/new-wiki.py --phase docs --target-folder <project>`; it resolves the wiki through the project's `.claude/wiki-config.json` (or `llm-wiki/how-to/`, or a notebook root), content-compares each framework doc and replaces the ones that differ (naming them, so a project-local edit is visible rather than silently lost), and touches nothing else. Add `--check` to review first: it writes nothing, lists every framework doc as unchanged / ADD / REPLACE with the `framework-version` on both sides and a diff (a lower project version is a stale copy; the same version with different content is a project-local edit the refresh would lose), reports the pack pages a refresh would copy, and exits 1 when anything would change. A wiki without `project/` (a plain notes notebook, or one scaffolded with `--project-folder none`) is named and its framework docs skipped — they are out of scope there; the pack usage docs still refresh. `--all-notebooks` runs either form over every notebook in the registry (`--registry <linked-notebooks.json>`, else the one the cwd's `.claude/wiki-config.json` names) with a one-line-per-notebook summary and a single exit code. This is the Phase 2 / Phase 3 tool of the research-to-framework update process, and the standing procedure after any framework change is `--phase docs --check --all-notebooks`, review every REPLACE, then the same command without `--check`.

## Required: the bootstrap-source path

`/new-wiki` reads `~/.claude/wiki-config.json` to find where the bootstrap source lives (recorded during Phase A by `install-wiki.ps1`).

If `~/.claude/wiki-config.json` is missing or doesn't have `bootstrap_source`, the user hasn't run the one-time machine install. Direct them to:

```
git clone https://github.com/dadlabs-io/llm-wiki-bootstrap ~/llm-wiki-bootstrap
cd ~/llm-wiki-bootstrap
.\install-wiki.ps1     # Windows
./install-wiki.sh      # Mac/Linux
```

After that one-time setup, `/new-wiki` works in any project folder.

## Source

Authored 2026-05-12, restructured 2026-05-13 for the per-project model, 2026-09-09 for the state check and the six-question interview (the folder halves opt-in; the nine-question interview and the fixed research taxonomy retired). Companion skills: `/wrap-up` (end-of-session distillation), `/wiki-cycle` (research orchestrator), `/wiki-search`, `/wiki-update`.
