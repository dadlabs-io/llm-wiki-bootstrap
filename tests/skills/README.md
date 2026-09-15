# Skill test baselines

A standing test for each shipped skill: one of each kind of input the skill handles, run by a real Claude session into a throwaway sandbox, then checked by a script. Re-run it whenever the skill (or a script it calls) changes; a changed skill is not installed until its run is at least as good as the baseline.

## Run it

From the repo root:

```bash
python tests/skills/run_skill_test.py wiki-update                     # every case, Sonnet and Opus side by side
python tests/skills/run_skill_test.py wiki-update --models sonnet     # one model
python tests/skills/run_skill_test.py wiki-update --cases pdf-cached-staged,no-source-redirect
python tests/skills/run_skill_test.py wiki-update --skill-ref HEAD    # the committed skill, to compare old with new
python tests/skills/run_skill_test.py wiki-update --save-baseline     # accept this run as the baseline
python tests/skills/run_skill_test.py wiki-update --tags complex      # the harder cases, run only on request
```

The report is `tests/skills/.results/<skill>/<stamp>/report.md` (not committed): each case per model, pass or fail with turns, cost and minutes, what regressed against the baseline, every failed check, and the live fetch status of the fixture sources. A full wiki-update run is about a dozen sessions per model.

## What a run does

1. The suite's `check.py` builds a sandbox per model: a copy of its seed notebook, its own registry, and its own qmd index (`WIKI_QMD_INDEX`), so real notebooks and the real search index are never touched.
2. The skill under test is rendered into the sandbox from the working tree, or from a git ref, with `{{WIKI_SCRIPTS_DIR}}` pointing at this repo's scripts. The installed copy is never used.
3. Each case is a headless `claude -p` session in the sandbox, in `--permission-mode auto` (the mode real sessions use) with the common commands pre-approved (`--allowedTools`). The prompt goes on stdin and the runner starts `claude.exe` directly: on Windows the npm `claude.cmd` shim cuts a command line at its first newline. The session's event stream is kept for review.
4. `check.py` checks each step by what it leaves behind, never by parsing commands (models batch commands in loops): files created, frontmatter, the real entry gate (`_entry_checks.py`), links that resolve, sidecars, searches counted from the search helper's own log (each case's searches carry its own `WIKI_QMD_CALLER`), the filing script's footer on the entry, and the model's printed `Scores:` line.

## Adding a skill

Create `tests/skills/<skill>/` with:
- `cases.json`: the cases (one of each input the skill handles; tag the expensive or unusual ones `complex`).
- `check.py`: `prepare_fixtures(repo, refresh)`, `setup(model, sandbox, repo)`, `snapshot(ctx)`, `prompt(case, ctx)`, `check(case, before, after, run, ctx)`, `teardown(ctx)`; optionally `ALLOWED_TOOLS`.
- `fixtures/`: written-for-the-test inputs only. Third-party text (articles, transcripts, papers) is fetched into `~/.cache/llm-wiki-skilltest/<skill>/` on first use and never committed.

Start with the largest skills; see the CHANGELOG entry that introduced this folder.
