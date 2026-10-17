# Skill test baselines

A standing test for each shipped skill: one of each kind of input the skill handles, run by a real Claude session into a throwaway sandbox, then checked by a script. A **behavioural** change to a skill (or to a script it calls) is installed once its new cases run red then green (below), on both models. **Red then green always; anything more is asked first** (Mark, 2026-10-17: "red/green always, ask before doing more, recommend if it makes sense"). When a full suite looks worth its cost (a change that rewrites several steps, or a script many steps call, where a targeted case cannot see the side effects), say so with the cost and wait for Mark's yes; never run it by default. Log the change in [PENDING.md](PENDING.md) so the next full run of that skill checks it.

A **small** change — wording, a clarified flag, a typo — needs no run of its own: install it and log it in PENDING.md.

**A full suite runs only on Mark's yes**, recommended on one of these triggers (the same list as agent-builder's), never on a calendar:
- a model change: a suite's model list, or a `model_default` in `wiki-ingester-config.json`, `wiki-checker-config.json` or `skills/wiki-cycle/helper-models.json`;
- a change to the runner's grading (`run_skill_test.py`, `_trajectory.py`, `_jsonl_cases.py`) or to a script many skills call (`_entry_checks.py`, `_wiki_config.py`, the search helper); a purely additive check does not count;
- a suite not run in a long while, before a change that depends on it ships;
- something looks wrong in real use.

Why: the targeted red-then-green cases found every real defect so far (Sonnet forcing past a duplicate, a step read as optional, a wording gap a large context slipped through), while full runs cost $40-90 a skill and came back "0 regressions" run after run. A skill with no baseline at all is never installed on a pending row — there the first run is the baseline.

## Who writes the cases

The session that changes a skill never writes or edits the cases that grade its change (task #86, 2026-10-06; the same rule as agent-builder's skill contract §6). They come from the `eval-case-writer` agent, installed globally by agent-builder: it can only read, it writes from the skill's stated requirement and each scenario, never from the skill, its scripts or its diff, and it hands the cases back as text for the session to save unchanged.

- **Brief:** the skill and its path; its requirement, quoted in full; the scenarios; the mode (`new-set`, `fresh`, `replay` or `legacy-review`); the case format, "llm-wiki's test suite in the folder `tests/skills/<skill>/`"; and, for every mode but `new-set`, the case file `tests/skills/<skill>/cases.json`. Spawn it in the foreground (`subagent_type: eval-case-writer`).
- **After each behavioural change:** two `fresh` cases, scenarios that did not exist while the change was made. A failure seen in real use gets a `replay` case. Each new or changed case then runs red then green (below) before the change is installed.
- **What comes back** is saved unchanged: cases in the suite's existing kinds; a new kind's check as a `kind == "<new>"` branch of `check()` (an existing kind is never changed); any new seed file in full. Its questions go to the user, never answered by the editing session from the skill's own text unless the quoted requirement already settles them.
- **Author key:** every case ends in `"author": "eval-case-writer" | "human" | "legacy"`. The 80 cases written before this rule are `legacy`; the next time their skill changes, the writer reviews them (`legacy-review`: keep, rewrite or flag each).
- **Honour rule:** the editing session does not read the suite's cases while it edits the skill. Nothing enforces it; the independence comes from who writes the checks.

## Run it

From the repo root:

```bash
uv run python tests/skills/run_skill_test.py wiki-update                     # every case, Sonnet and Opus side by side
uv run python tests/skills/run_skill_test.py wiki-update --models sonnet     # one model
uv run python tests/skills/run_skill_test.py wiki-update --cases pdf-cached-staged,no-source-redirect
uv run python tests/skills/run_skill_test.py wiki-update --skill-ref HEAD    # the committed skill, to compare old with new
uv run python tests/skills/run_skill_test.py wiki-update --save-baseline     # accept this run as the baseline
uv run python tests/skills/run_skill_test.py wiki-update --tags complex      # the harder cases, run only on request
uv run python tests/skills/run_skill_test.py wiki-update --cases new-case --red-green HEAD   # fails on the committed skill, passes on yours
```

The report is `tests/skills/.results/<skill>/<stamp>/report.md` (not committed): each case per model, pass or fail with turns, cost and minutes, what regressed against the baseline, every failed check, and the live fetch status of the fixture sources. A full wiki-update run is about a dozen sessions per model.

## A new case must fail on the old skill (red, then green)

A case written for a behavioural change proves the change only if it **fails on the skill before the change and passes after it** (task #134, from the Ruflo deep dive). A case that passes on the old skill too tests something else, however well it reads. So before a behavioural change is installed, its new or changed cases run red then green:

```bash
uv run python tests/skills/run_skill_test.py wiki-update --cases <new-case>,<changed-case> --red-green <ref before the change>
```

Each case runs on an export of that ref (its skill **and** its scripts, agents and docs, so a change made in a script counts), then on the working tree. The report's Red then green table gives each case and model one verdict: red then green (proves the change, with the checks that failed on the old copy, so you can see it failed for the right reason), passes on the old copy too, fails on the new copy. The exit code is 0 only when every case is red then green. A case that passes on the old copy goes back to `eval-case-writer` (mode `replay`) with the old run's reply; it is not counted as proof. The old copy's sessions cost the same as the new ones: run only the new and changed cases this way, then the suite as usual.

## Nothing reads clean that checked nothing

- A run that selects zero cases stops with an error (exit 1), never a clean report.
- A case whose checks came back empty fails, with the check "the case produced checks".
- A case can be switched off only with a date: `"off_until": "YYYY-MM-DD"` and `"off_reason": "..."` in `cases.json`. Until that day it does not run (unless named in `--cases`); from that day it runs again by itself. A run rule (`trajectory_rules.py`) takes the same `off_until`; the older `"in_suite": False` with no date still switches a rule off, and the report lists it as undated until it gets one. Every report names each switched-off case and rule with its date, so nothing is off for good without anyone seeing it.

## Reporting a measurement

Every report opens with the same four headings, and a measurement written by hand (a PENDING.md row worth more than a line, a model or effort comparison, the search-question set of task #82) uses them too, so two results can be compared without rereading how each was made:

```markdown
## Compared with
What the result is measured against: the stored baseline, the old ref, the other model, a control arm. "Nothing" is an answer.

## n
How many cases, models, sessions or questions, and how many runs of each.

## Cost
Dollars and minutes, in all.

## What this does not show
What was not run (cases not selected, switched off, complex), what one run per case cannot tell (a single flip is noise until rerun), and what no case covers.
```

A suite may list its known gaps once in `cases.json` as `"not_covered": ["...", "..."]`; the runner copies them under the last heading of every report.

## Switching a model: shadow it first, against a bar set before

Before a `model_default` changes (`wiki-ingester-config.json`, `wiki-checker-config.json`, `skills/wiki-cycle/helper-models.json`, or a suite's model list), the new model runs beside the old on the same real work, and it is switched only if a bar written down **before** the run is met (task #128, from the Ruflo deep dive: metaharness switches only through a fixed gate, quality not more than 2% lower, cost and latency lower). The default bar, unless the decision names another:

- **quality not lower**: on the same cases or entries, every check the old model passes the new one passes too (one flip is rerun before it counts), and a blind judgment of the output, where there is one, rates it no worse;
- **cost lower**: dollars per accepted result (per passing case, per entry promoted), not per session;
- **nothing new breaks**: no new kind of failure in the event streams (a refused call, a skipped step).

Write the bar, the work it runs on and n in the decision before the run, run both, and report under the four headings above. The 2026-10-12 helper-model comparison (#87: Sonnet matched Opus on lint, fixes and synthesis at 40-45% of the cost) is the pattern. Planned first use: ingest workers on Sonnet with any entry the wiki-checker fails redone on Opus, against all-Opus, measured per accepted entry (task #128, folded in from #127); it needs the checker run on every entry, not only long transcripts.

## What a run does

1. The suite's `check.py` builds a sandbox per model: a copy of its seed notebook, its own registry, and its own qmd index (`WIKI_QMD_INDEX`), so real notebooks and the real search index are never touched.
2. The skill under test is rendered into the sandbox from the working tree, or from a git ref, with `{{WIKI_SCRIPTS_DIR}}` pointing at this repo's scripts. The installed copy is never used.
3. Each case is a headless `claude -p` session in the sandbox, in `--permission-mode auto` (the mode real sessions use) with the common commands pre-approved (`--allowedTools`). The prompt goes on stdin and the runner starts `claude.exe` directly: on Windows the npm `claude.cmd` shim cuts a command line at its first newline. The session's event stream is kept for review.
4. A suite run by `_jsonl_cases.py` (the improver, writing-skill-suggestions) also asks a Sonnet judge YES/NO questions about the session's reply, the majority of up to three calls. The judge states what settles the question first and gives its answer alone on the last line, and only that line is read (2026-10-13: told to answer in one word, it wrote "NO" followed by a sentence meaning yes, and the first word was taken).
5. `check.py` checks each step by what it leaves behind, never by parsing commands (models batch commands in loops): files created, frontmatter, the real entry gate (`_entry_checks.py`), links that resolve, sidecars, searches counted from the search helper's own log (each case's searches carry its own `WIKI_QMD_CALLER`), the filing script's footer on the entry, and the model's printed `Scores:` line.

## Run checks: what the session did on the way

A pass on the output can hide a skipped step: a file the skill says to read, never opened, or a step it forbids, taken and undone (task #99, from agentic-design's WN-S7). A suite with `<skill>/trajectory_rules.py` lists the skill's own read-first and never rules, each quoting its line in the skill; `_trajectory.py` checks them on the run's tool calls (a refused call never counts), and the runner adds them to every case as `run: <rule>`. `score_trajectory.py <skill> [--since <stamp>]` scores the rules over every saved run in `.results/` at no model cost: use it on a new rule before it joins the suite, and keep a rule with false alarms at `"in_suite": False` until they are fixed. wiki-update, wiki-cycle and wrap-up have rules (2026-10-12).

## Adding a skill

Create `tests/skills/<skill>/` with:
- `cases.json`: the cases (one of each input the skill handles; tag the expensive or unusual ones `complex`), written by `eval-case-writer` in mode `new-set`, which also returns each new kind's check for `check.py`.
- `check.py`: `prepare_fixtures(repo, refresh)`, `setup(model, sandbox, repo)`, `snapshot(ctx)`, `prompt(case, ctx)`, `check(case, before, after, run, ctx)`, `teardown(ctx)`; optionally `ALLOWED_TOOLS`. A skill that calls other skills (wiki-cycle) also sets `EXTRA_SKILLS` (rendered beside it), `DISALLOWED_TOOLS = ["Skill"]` (so nothing falls through to an installed copy) and `render_replacements(ctx)` (install paths → sandbox copies). `run["error_texts"]` maps each refused call to its error text, so a check can tell the global read-guard hook's blocks from harness friction.
- `fixtures/`: written-for-the-test inputs only. Third-party text (articles, transcripts, papers) is fetched into `~/.cache/llm-wiki-skilltest/<skill>/` on first use and never committed.

Start with the largest skills; see the CHANGELOG entry that introduced this folder.
