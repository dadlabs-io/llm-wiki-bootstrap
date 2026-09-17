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

Skills with no suite yet: every other shipped skill. The next ones are the user's pick (task #16).
