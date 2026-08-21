# llm-wiki — QUICKSTART

**For humans**: read this top-to-bottom and run the commands yourself, OR hand this folder to a coding-agent and ask it to set things up — the agent will follow these same steps.

**For AI agents** reading this on a user's behalf: this is your install runbook. Execute each numbered step in order. Where a step says "ask the user," ask. Where a step says "verify," check. Don't skip the verification.

---

## What this is

A self-improving knowledge-wiki framework. Markdown-based, AI-maintained, git-versioned. Works for any topic (research notes, recipes, documentation — anything you want a curated, search-able knowledge base for).

After install, you have:
- A blank topic wiki (your subject — sourdough / agentic design / Rust async / whatever)
- 4 commands you'll actually use day-to-day: `/wiki-cycle`, `/wiki-update`, `/wiki-search`, `/wiki-init`
- Auto-maintained INDEX, MAP, backlinks, lint, contradiction detection, and morning reports

---

## Before you start

You need **Python 3.11 or newer**.

Check by running:

```
python --version
```

You should see `Python 3.11.x` or higher. If you see `command not found` or a version below 3.11, install Python from [python.org](https://www.python.org/downloads/) before proceeding.

You also need a coding-agent harness — **Claude Code** is the primary target; Codex CLI, Gemini CLI, and Cursor also work. If you don't have one, install Claude Code first.

---

## Step 1 — Decide where llm-wiki goes

Two pieces of information:

### 1a. The **target directory**

This is the project root where llm-wiki gets installed. Pick somewhere you control — usually a folder under your home directory, like:
- `~/research/` (Mac/Linux)
- `C:\Users\<you>\research\` (Windows)

**Don't** install into the `llm-wiki` download folder itself — that folder is the source. Install into a project of your own.

If you don't have a target folder yet, make one:

```
mkdir ~/research
```

(adjust the path for Windows: `mkdir C:\Users\<you>\research`)

### 1b. The **topic name**

This is what your wiki is about. Use lowercase, hyphenated, no spaces. Examples:
- `agentic-design`
- `sourdough`
- `rust-async`
- `medieval-architecture`

You can have multiple topics later — each gets its own subfolder. Pick the first one now.

> **AI agent note:** ask the user both questions if they haven't told you. Don't assume — print what you've decided and confirm before running the install command.

---

## Step 2 — Run the installer

From the `llm-wiki/` folder (the one this QUICKSTART is in), run:

```
python install.py --target <target-directory> --topic <topic-name>
```

Replace `<target-directory>` with the path from Step 1a, and `<topic-name>` with the name from Step 1b. Concrete example:

```
python install.py --target ~/research --topic sourdough
```

**Want to preview before writing anything?** Add `--dry-run`:

```
python install.py --target ~/research --topic sourdough --dry-run
```

Dry-run prints what *would* be copied. Re-run without `--dry-run` to actually install.

What the installer does:

| Lands at | What |
|---|---|
| `<target>/scripts/llm-wiki/*.py` | Python tools |
| `<target>/.claude/skills/wiki-*/SKILL.md` | Slash-commands for Claude Code |
| `<target>/vault/wikis/<topic>/` | Your blank topic wiki |

---

## Step 3 — Verify the install worked

Run these three checks. Each should print a path (no `not found` errors):

```
ls <target>/scripts/llm-wiki/wiki-cycle.py
ls <target>/.claude/skills/wiki-cycle/SKILL.md
ls <target>/vault/wikis/<topic>/wiki/llm-wiki-user-guide.md
```

(On Windows: replace `ls` with `dir` or use Git Bash / WSL.)

If all three print a path, the install succeeded. If any of them errors, the install didn't complete — re-run Step 2 and watch the output.

---

## Step 4 — Open your harness in the target directory

Now switch to your target directory and start your coding agent there:

```
cd <target-directory>
claude          # or: codex / gemini / etc.
```

The harness will load `.claude/skills/` automatically. The four user-facing slash-commands (`/wiki-cycle`, `/wiki-update`, `/wiki-search`, `/wiki-init`) are now available.

---

## Step 5 — First wiki actions

In your harness, in this order:

### 5a. Read the user guide (one-time orientation)

Tell your agent:
```
read vault/wikis/<topic>/wiki/llm-wiki-user-guide.md
```

This is the canonical "how to use llm-wiki" reference. Read it once and you understand the system.

### 5b. Edit your feeds list

Open `vault/wikis/<topic>/_config/feeds.md` and add the trusted sources you want llm-wiki to sweep when discovering new content. The file ships with a template — replace the example rows with your real feeds. (Skip this if you're not using auto-discovery yet — you can come back later.)

### 5c. Ingest your first entry

```
/wiki-update <a-url-you-care-about>
```

Example:
```
/wiki-update https://en.wikipedia.org/wiki/Sourdough
```

The agent fetches the URL, synthesizes a wiki entry, and files it under `vault/wikis/<topic>/wiki/<some-folder>/<slug>.md`. You'll be asked which folder if one doesn't exist yet.

### 5d. After ~10 entries — first full cycle

Once you have ~10 entries, run:

```
/wiki-cycle --full
```

This is the full self-improvement pass: discover → ingest pending → semantic lint → claim contradictions → refresh stale → morning report. Takes 30-40 min depending on size. After this, _MAP.md and per-folder _INDEX.md exist and the wiki is in steady-state.

Daily flow from here is just `/wiki-cycle` (quick mode, ~5-10 min) plus `/wiki-update <url>` when you stumble on something good.

---

## Updating to a newer llm-wiki version

When new framework versions ship, refresh the contracts (your content is untouched):

```
cd <where you cloned llm-wiki>
git pull
python install.py --target <target> --topic <topic> --update
```

`--update` refreshes ONLY the 4 framework contracts + user-guide in your topic's `wiki/best-practices/framework/`. Your entries, feeds, raw dumps, and inbox are not touched.

---

## Cross-harness notes

Primary target is Claude Code. For other harnesses:
- **Codex CLI / Cursor / Gemini CLI**: SKILL.md files double as AGENTS.md-compatible. May need to symlink or rename per your harness's discovery rules.
- **Pure Python**: every script in `scripts/llm-wiki/` works standalone — no harness required.

---

## Troubleshooting

| Symptom | Fix |
|---|---|
| `python: command not found` | Install Python ≥ 3.11 from [python.org](https://www.python.org/downloads/) |
| `target not found` (during install) | The target directory doesn't exist. Create it first: `mkdir <target>` |
| `topic already exists` | Use `--update` instead of fresh install (see "Updating" above) |
| Permission denied | Pick a target directory you own (e.g., under `~/`, not `/` or `C:\Program Files\`) |
| `/wiki-cycle` says "no feeds configured" | Edit `_config/feeds.md` first; you need at least one feed |
| Broken links after upgrade | `/wiki-cycle --lint-only` shows what's broken; usually a path that changed |
| _MAP.md not loading in agent context | Add `@vault/wikis/<topic>/wiki/_MAP.md` to your harness's CLAUDE.md / AGENTS.md |

---

## What ships in this folder

```
llm-wiki/
├── README.md             What this is, design overview
├── QUICKSTART.md         You're reading it
├── install.py            Cross-platform installer (this is what you ran in Step 2)
├── scripts/              Python tools (copied to <target>/scripts/llm-wiki/)
├── skills/               SKILL.md files (copied to <target>/.claude/skills/)
└── topic-template/       The blank topic skeleton (copied to <target>/vault/wikis/<topic>/)
```

---

## See also

- [`README.md`](./README.md) — high-level overview
- [`topic-template/wiki/llm-wiki-user-guide.md`](./topic-template/wiki/llm-wiki-user-guide.md) — full user guide (the canonical reference for using the system, post-install)
