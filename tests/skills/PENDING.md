# Untested changes, per skill

A skill's suite costs real money to run (task-list: about $4.20 on both models; wiki-update: more).
Running it for a wording fix is not worth it, so **small changes accrue here and are checked by the
next run** (the user, 2026-09-17: "if we're making little tweaks here and there we can compile these
all up and wait until we've got enough of them that needs a test — or if we start seeing problems,
then we can run it").

## The rule

- **A behavioural change runs the suite before it is installed.** Anything that changes what the skill
  does or decides: a new or removed step, a different command, a changed rule or gate, a new input it
  must handle. This is the original standing rule and it has not moved.
- **A small change may be installed and logged here instead.** Wording, a clarified flag, a fixed
  typo, a reference the skill always should have named — something that cannot change an outcome.
- **Run the suite when** the pending list for a skill is long enough to be worth a run, a behavioural
  change lands on top of it, or anything looks wrong in real use. The run clears that skill's rows.
- A run that follows pending rows **reads them first** and checks each one landed as intended, not just
  that the totals still match. Equal totals with a silently lost edit is the failure this guards.
- Never install a change with no baseline at all for the skill. There the first run is the baseline.

## Pending

| Skill | Date | Change | Why it was not run |
|---|---|---|---|
| _(none)_ | | | |

## Last full run

| Skill | Date | Result |
|---|---|---|
| wiki-update | 2026-09-15 | 22/22, Sonnet and Opus |
| wiki-search | 2026-09-17 | 10/10, Sonnet and Opus (old skill 9/10) |
| task-list | 2026-09-17 | 14/14 twice, 108 checks; re-run after the CLI-reference edit, 0 regressions |
| wrap-up | 2026-09-17 | 10/10 on the 5 core cases after the trim; 0 regressions against the pre-trim baseline, 1 newly passing |
| wiki-lint | 2026-09-17 | 8/8 on the 4 core cases, 35 checks each model; no skill change — the suite is new |
| new-wiki | 2026-09-18 | Opus 6/6 cases, 116/116 checks; Sonnet 4/6, 113/116 (a PowerShell denial in `go-inproject-auto`, `--force` without asking in `existing-folder-asks-force`); no skill change — the suite is new |

The three `complex` wrap-up cases (auto-promote, research-only, trivial) and wiki-lint's `prior-report-trap`
have **no baseline**: they pass the offline harness but have never been run against a model. Run them with
`--tags complex` before relying on them. `prior-report-trap` is the interesting one — it is the only check of
"don't read the existing semantic lint reports before writing your own".

One derivation to know about: `wiki-lint`'s opus `full-finds-planted` baseline entry has its
"read every wiki entry before judging" check re-scored offline against the saved event stream, after the
checker was fixed to recognise a bulk `find … | cat` read. The run itself was real; only that one check,
a pure function of the recorded tool calls, was recomputed. Re-run the case if you want it first-hand.

`new-wiki`'s baseline has two derived parts. `ask-first`'s "no Drive question" check was re-scored offline
against both saved replies after the checker was fixed (it failed on "Drive is off, so no Drive question"; it now
fails only on a question). The two `complex` cases ran in their own run (`--tags complex`, `20260918-013712`) and
were merged into the baseline files from its per-case results. Its untested branches: tooling `partial` or
`missing` (the skills question) and Drive on (the Drive question). Testing them needs a fake home folder, and
a headless session with one writes a fresh `.claude.json` into the real `~/.claude` (`CLAUDE_CONFIG_DIR` is
needed for the login). They wait for a way to point the scripts' home at the sandbox.

Skills with no suite yet: every other shipped skill. The next ones are the user's pick (task #16).
