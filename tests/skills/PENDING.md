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
| wiki-lint | 2026-09-24 | Task #46: the stale-"pending" check line in the skill and pack page describes the new rule (workflow phrases anywhere; `not yet built` / `TODO:` only in tier-`self` entries; frontmatter, quotes, code, links skipped). Script proven by `tests/scripts/test_stale_pending.py` (15/15) and on four real notebooks | wording only in the skill; the behaviour is the script's. The next wiki-lint run's fixtures may count fewer stale mentions: check the report reads right, not that the count matches the old baseline |
| wiki-promote | 2026-09-24 | Task #44: one sentence on folders known by their README (skill + pack page). Script proven by `tests/scripts/test_folder_readme.py` (11/11) | wording only; wiki-promote has no model suite (script-heavy, its harnesses are free) |
| wiki-lint | 2026-09-24 | Task #54: the orphan check line says a page may declare `standalone: "<reason>"` and is then listed apart (skill + pack page). The script change (a Standalone Pages section, the `standalone` JSON array and counter) is proven by `tests/scripts/test_standalone.py` (22/22, five mutants killed) | wording only in the skill; the behaviour is the script's, tested by its free harness. The next wiki-lint run should show the report's new section read without confusion, and a fixture HOME without the field still listed as an orphan |
| wiki-promote | 2026-09-25 | `wiki-promote.py` runs `wiki-reciprocate-backlinks.py` after the link fixer, so a promoted entry is never left an orphan; the skill's description, Step 3.5 and the pack page say so. Script proven by `tests/scripts/test_promote_backlinks.py` (8/8; 5 failed before the fix) | wording only in the skill; the behaviour is the script's, tested by its free harness; wiki-promote has no model suite |
| wiki-cycle | 2026-09-25 | Nothing changed in the skill, but Step 5.5's "Then re-run Step 3.5" is now redundant: the promote script rebuilds backlinks, folder indexes and MAP itself. Harmless (idempotent) | the next wiki-cycle run can drop the re-run; changing it is a step change, so it waits for that run |
| new-wiki | 2026-09-25 | The scaffold templates brought up to date (CLAUDE.md, the project README, the wiki root README, wiki HOME/README/_MAP: the user guide linked, `raw/` described as sources, the staging contradiction and the agentmemory section removed from CLAUDE.md, `project_type`/`category` dropped from its example frontmatter, the `/wiki-cycle` wording current), and Phase B no longer writes the never-regenerated `wiki/_INDEX.md` placeholder. All six templates rendered with `_render_template` into a scratch notebook: no `{{…}}` left, every relative link resolves | the interview and the scaffold's decisions are unchanged; the suite checks `CLAUDE.md`/`README.md`/`.gitignore` exist, not their wording. The next run should find no `wiki/_INDEX.md` and nothing expecting it |
| wiki-cycle | 2026-09-23 | Step 2 and its pack page say what `--depth-check`'s exit 1 and 2 mean | wording only; still unchecked: the 2026-09-24 baseline runs quick mode only, and the depth check runs in `--full` |

## Last full run

| Skill | Date | Result |
|---|---|---|
| wiki-update | 2026-09-24 | **#50 release run** `20260924-214033` ($30): 22/22 on both models, 0 regressions, after the harness learned to count the global read-guard's blocks apart (as wrap-up and wiki-cycle already did); that one check was re-scored from the saved event streams, every other check is first-hand. Pending rows checked: #47's quote check (all 16 filed or staged entries with a raw: every `>` line matches the raw, 0 warnings); #42's backlink rule (3–5 on-topic `suggested_backlinks` per staged entry, none empty); the `-C` wording. New baseline. Previous: 2026-09-15 22/22 |
| wiki-search | 2026-09-23 | 10/10 on both models, 0 regressions, after `-C` became a fixed 120 and the depth check was rebuilt ($2.62; every search in the run logged C=120 with a reranked count). Previous: 2026-09-22 10/10 after `-k` 20 -> 30; 2026-09-17 10/10 (old skill 9/10) |
| task-list | 2026-09-17 | 14/14 twice, 108 checks; re-run after the CLI-reference edit, 0 regressions |
| wrap-up | 2026-09-17 | 10/10 on the 5 core cases after the trim; 0 regressions against the pre-trim baseline, 1 newly passing |
| wiki-lint | 2026-09-17 | 8/8 on the 4 core cases, 35 checks each model; no skill change — the suite is new |
| wrap-up | 2026-09-25 | **`wrap_up_commit` setting** (`none`/`commit`/`push`, a typed flag wins): run `20260925-011911` ($5.98) on 4 cases, 8/8, 0 regressions. New cases `config-push` (setting `push`, no flag: commits and pushes) and `flag-overrides-config` (setting `push`, `--auto-commit` typed: commits, does not push; new "not pushed" check). The checker was validated offline first against six simulated runs, right and wrong. All four replies named what decided. Baseline now 8 core cases: first-run, none-answer, at-a-glance from `20260924-214311` and auto-create from `20260924-220435` (both on the skill before this wording), incremental, auto-push and the two new ones from `20260925-011911` |
| wrap-up | 2026-09-24 | **#50 release run**: 6 core cases, 12/12, new baseline merged per case from three runs on the working tree. Run `20260924-214311` ($7.53): 10/12. Opus `auto-push` wrote both pushes in one `for` loop; the auto-mode classifier refused it and Opus rightly ended `⚠️ WRAP-UP INCOMPLETE`. Step 7 item 4 now says each push is its own plain `git -C <repo> push`; re-run `20260924-215811` passed on both. Sonnet `auto-create` printed a list instead of Step 2's table, twice (the second time claiming it had printed the table): the closing line made the reply one final message and the mid-run table dropped out. Step 2 and Step 5 now say the table opens the final reply; `20260924-220435` passed on both. Baseline cases: first-run, incremental, none-answer, at-a-glance from `214311`, auto-push from `215811`, auto-create from `220435` |
| wrap-up | 2026-09-24 | (the run above covered this) **Behavioural** (task #51): `--auto-commit` / `--auto-push` (Step 7: stray sweep; the project repo gets only the session's paths, never `add -A`; the notebook repo only the notebook's folder; push only a branch that tracks a remote, never force) and a closing line that ends every wrap-up (`✅ WRAP-UP COMPLETE: committed and pushed ✅` / `committed, not pushed` / `nothing committed` / `⚠️ WRAP-UP INCOMPLETE: … ⚠️`). New core case `auto-push` (local bare remotes; the user's untracked `scratch-notes.txt` must stay out), validated offline: empty run fails, a simulated correct run passes 8/8, planted `add -A` / no push / wrong line all caught. Every case gains "ends on the closing line"; the denial check now counts read-guard blocks apart | runs in #50's release run; the existing cases' new closing-line check will show as "new", not a regression |
| wiki-triage | 2026-09-24 | **#50 release run** `20260924-214033` ($2.06): 8/8 on both models, 0 regressions. The pending single-bucket row checked: in `single-no-config` both models routed every ticket to `main` with "the only bucket" and fetched no source |
| wiki-triage | 2026-09-24 | (the run above covered this) After its baseline, step 2 says: with one bucket, route every ticket to `main` without reading it (single-project notebooks triage on every cycle; judging one bucket is wasted reading) | small, cost-only; the `single-no-config` case checks the routing, and the next run should show it reading no source there |
| wiki-triage | 2026-09-24 | **First baseline** of the new skill (4 cases: a shared notebook with five sources incl. one that fits nothing and one that straddles two buckets, no config, a user-dropped ticket, a config with no `main`): 8/8 sessions, every check passed on both models, $2.05. Both routed all five correctly with content-grounded reasons and captured the raws for the other readers. Not installed: ships with #50 |
| wiki-cycle | 2026-09-24 | **#50 release run** `20260924-221246` ($13.64): the rewritten skill (#42), 4 core cases, 8/8 clean on both models, 0 regressions, Opus `quick-staged` newly writing every quick step's pair (Step 3.5 and the lint's own `lint-mechanical.json` via the new flags). Saved as the new baseline. Earlier run `20260924-194212` passed every behaviour check but failed on two harness faults, fixed before this run |
| wiki-cycle | 2026-09-24 | **First baseline**, on the skill as it stood before #42 (2 core cases, quick `--ingest-only` and `--resume`; $9.33 on both models). Sonnet 27/27 + 24/24; Opus 26/27 + 24/24 — Opus skipped Step 3.5's integration scripts, reading `--ingest-only` ("skip discovery; drain the pending queue; cleanup") as excluding them. The denial check was re-scored offline from the saved event streams: each run had one block by the global read-guard hook (recovered), which the harness now counts apart. The other plan cases are added with the changes that build them (`cases.json` `_planned`) |
| new-wiki | 2026-09-18 | after the ask-before-`--force` change: 116/116 on both models, 0 regressions, 3 newly passing on Sonnet (the `--force` case, 0 of 3 runs forcing where it was 3 of 3). First baseline, before the change: Opus 116/116, Sonnet 113/116 |

The three `complex` wrap-up cases (auto-promote, research-only, trivial) and wiki-lint's `prior-report-trap`
have **no baseline**: they pass the offline harness but have never been run against a model. Run them with
`--tags complex` before relying on them. `prior-report-trap` is the interesting one — it is the only check of
"don't read the existing semantic lint reports before writing your own".

One derivation to know about: `wiki-lint`'s opus `full-finds-planted` baseline entry has its
"read every wiki entry before judging" check re-scored offline against the saved event stream, after the
checker was fixed to recognise a bulk `find … | cat` read. The run itself was real; only that one check,
a pure function of the recorded tool calls, was recomputed. Re-run the case if you want it first-hand.

`new-wiki`'s baseline is built from two runs (core `20260918-085713`, `--tags complex` `20260918-090101`), merged
from their per-case results. Two checks in it were re-scored offline against the saved replies after the checker was
fixed: Opus's `plan-only` skills-question check (it matched "Q7 (install or bundle skills) isn't asked") and
Sonnet's `existing-folder-asks-force` ask check (it required a literal "?"; the reply asked with yes/no options). Its untested branches: tooling `partial` or
`missing` (the skills question) and Drive on (the Drive question). Testing them needs a fake home folder, and
a headless session with one writes a fresh `.claude.json` into the real `~/.claude` (`CLAUDE_CONFIG_DIR` is
needed for the login). They wait for a way to point the scripts' home at the sandbox.

`wiki-cycle`'s baseline (run `20260924-153802`) has its "no permission denials" check re-scored offline from the saved
event streams, after the harness learned to tell a read-guard block (the refused call's text carries `hook error:
read-guard:`) from harness friction. Every other check is first-hand.

Skills with no suite yet: every other shipped skill. The next ones are the user's pick (task #16).
