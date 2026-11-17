# Red-team: plan.md revision 2 (240-loud-backlogs, round 3)

Written by the orchestrator from the red-team's report. The red-team was a fresh architect running strategy-red-team, with one red-team-reviewer (haiku) spawn. The readonly-guard check passed (639 files, HEAD unchanged). Rounds 1 and 2 are in plan-red-team-round1.md and plan-red-team-round2.md.

**What the architect read:**
- check.py lines 68-73, 525-565, 1150-1190, 1295-1325, 1535-1565, 1750-1870, 2540-2560, 2618-2640, 2700-2780
- wiki-cycle SKILL.md and wiki-cycle-scope.py, in full
- wiki-dequeue.py 1-140; wiki-triage.py 70-190; _pdf_match.py 35-80
- wiki-lint-mechanical.py 448-480 and 1470-1520; wiki-report SKILL.md 255-305
- greps of wiki-discover and tests/skills/README.md

Points marked "reviewer only" were not re-read by the architect.

## Round-2 kill-assumptions: resolved, or turned into a Decision?
- **R2-1:** resolved by Decision 1, except for the `applied` number (KA3).
- **R2-2:** partly resolved. "Last run" now has a definition, but it has a new hole (KA4).
- **R2-3:** resolved for lint-fixes. Tier-4 became Decision 2, but the checklist option relies on a label the template does not carry (KA5).
- **R2-4:** resolved for semantic, claims and synthesis. Not resolved for a lint-mechanical.json with `status: partial` (KA3).
- **R2-5:** resolved, but a same-day under-count is left undecided (KA3).
- **R2-6:** resolved.
- **R2-7:** not resolved. The plan names the wrong check.py guards and misses the ones that fire (KA1).
- **R2-8, R2-9:** resolved.
- **README trigger:** now Decision 4, Mark's call.

## Kill-assumptions (ranked)

### KA1. The seeded case A fails the common checks
**Claim:** "the guards that key on lint-semantic.json (546-547, 1163, 1307, 1548) may fire … a new kind's check is its own `kind == ...` branch". Case A is a resumed run with every phase through 7 done.

**Fails if:**
- Those four lines sit inside other kinds' checks (`_check_promote_setting`, `_check_synthesis`, `_check_model_choice`, `_check_checker_promote`), so the plan names the wrong guards. The common checks below run for every kind:
  - **2749-2750 ("no --full-only step ran"):** fails when a lint-semantic*/claims* JSON is present. Existing full-run kinds drop it (1162, 1306, 1546, 1930); the plan doesn't say the new branch must do the same.
  - **2747-2748:** require pairs for `QUICK_STEPS` (line 71: update, lint-mechanical, reciprocate-backlinks, index-per-folder, map-compile). A run resumed at Step 8 can't produce the last three, and the seed list has none of them.
  - **2730 and 2743:** require a sibling .md for each step JSON and the `STEP_FIELDS` with this run's cycle_id. Neither is in the seed list.
  - **2765 and 2770-2779:** default to 2 staged entries, 2 done tickets and an empty `pending/`. Case A plants 3 pending tickets and 1 staged entry.
- That a run resumed with every phase through 7 done goes straight to Step 8 is unproven. Every existing resume fixture resumes at 2.5 or 2.6; the closest precedent is fixtures/promote/scratchpad-full.md.

**Kill criterion:** any common check in 2726-2780 fails on the seeded folder with no branch dropping it.

**Cheapest test:** test_left_undone_fixture.py also runs the common checks over the built A and B folders, unpaid. The first paid session then answers the Step-8 resume question.

**Fix class:** plan error.
- Name the common checks and say whether the new branch drops or sets each one.
- Seed the .md files and STEP_FIELDS.
- Set the staged, done and pending counts.
- Make the Step-8 resume part of the first paid session's expected result.

### KA2. The `--mode` flag can disagree with the run folder
**Fails if:**
- The model passes the wrong mode (e.g. `--mode quick` on a `--full` run), so the line says "this mode does not run refresh" for a step that ran. There is no cross-check against the step files.
- SKILL.md's markdown table has only 5 modes (lines 28-45). The other four (lint-only, report-only, refresh-only, claims-only) are prose at line 47, so the script's table becomes a second source no test can compare.
- reference.md:15 records `**Cycle**: <id> (<mode>)` in the scratchpad, but the model is still the one typing the flag.

**Kill criterion:** the flag and the run folder disagree, and a "does not run" reason is printed for a step whose JSON is present.

**Cheapest test:** `--mode quick` with a completed refresh.json must exit 2 or print `not checked (mode disagrees with the run folder)`; a second test compares the script's table with SKILL.md's.

**Fix class:** plan error.
- Add the cross-check.
- Read the mode from the scratchpad, or reject a disagreement.
- Add a drift test for the five table rows, and say the other four modes are covered only by the cross-check.

### KA3. Lint counts: partial lint, JSON shape, the `applied` arithmetic, same-day under-count
**Fails if:**
- **Partial lint (verified).** The lint writes `status: partial` plus a `not_checked` list (wiki-lint-mechanical.py:464-465), and the unchecked parts report 0. A partial lint with all-zero counts then yields `Left undone: nothing`, against SKILL.md:144 ("never call the lint clean") and the plan's own invariant.
- **The `applied` number.**
  - Step 5 fixes findings of every kind, but `--applied N` is subtracted from the semantic count only. The semantic line can come out short, or negative, and there is no clamp.
  - Fixes and findings are different units.
  - The model types the number, against "the model computes no count".
- **Unknown JSON shape.** No schema is given for lint-semantic.json. The check.py fixture writes `summary.findings`, while "sum of its category arrays" names no key. A different shape counts as 0, which reads as clean.
- **"Awaiting your approval" overstates.** stale_pending, task_problems, design_behind, renamed_terms_left and hub_entries_missing may not be touched by the Step 5 fixers. Reviewer only: concept gaps and tier review too.
- **Same-day under-count.** An entry in the scope file that was revised the same day after the lint counts as covered. Nobody decided that is acceptable, and requirements line 75 says counts are never estimated. Reviewer only: Step 6.5 bumping last_reviewed (SKILL.md:175).

**Kill criterion:** a partial lint reads `nothing`, or a count without `not checked`; an unknown lint-semantic.json shape reads as 0.

**Cheapest test:** a partial lint with all-zero counts; an unknown shape; `applied` larger than the total.

**Fix class:**
- Plan error: a partial lint reads `not checked` for each unchecked part; name the schema key, falling back to `not checked`; clamp at 0, or record applied/declined per source.
- Choice for Mark: accept and label the same-day under-count, or compare by timestamp.

### KA4. `--report-only`: "last run" can be another report-only run
**Fails if:** a report-only run writes a report and so becomes the next one's "last run".
- If it writes no events file, the next report reads "not checked" although a real run exists.
- If it copies the events, they nest as `(from …)`.
- If it writes its own lines, the real counts are lost.
- SKILL.md:47 ("runs 8 from the last run's JSON") is another definition.

**Cheapest test:** folders A (full), B (report-only) and C (report-only); C must cite A.

**Fix class:** plan error. "Last run" is the newest earlier folder holding a report and an events file whose mode is not report-only. A report-only run writes no events file.

### KA5. Tier-4 source and ticket loops
**Fails if:**
- **The tier-4 label isn't in the template.** The checklist template (wiki-discover SKILL.md:163-169) puts `— tier N —` on every candidate. `(NEEDS HUMAN REVIEW)` appears only in a Don't (:273). A model that omits the label gives 0 lines, which can't be told from "none", so the line never reads `not checked`.
- **The checklist may have moved.** A processed checklist moves to `_inbox/done/` (wiki-discover:220), and the plan doesn't say where Step 8 reads it. Reviewer only: whether an unattended run moves it.
- **"Not in pending" is the wrong test at Step 8.** Step 1.7 triage has already moved tickets into buckets.
- **The new ticket loop duplicates existing ones (verified in part).** The plan claims there is no existing loop, but `wiki-triage.py:154-156 _tickets` covers pending, `_pdf_match.waiting_tickets` (42-61) loops over buckets, and `wiki-dequeue.py:122-123` treats pending and buckets differently. Reviewer only: `cmd_retry_list` (~310-336) and `wiki-list-add.py:165-173`. Decision 7's "the dequeue's rule" doesn't hold for `pending/`.

**Kill criterion:** the unattended checklist isn't where the counter looks, or a tier-4 candidate lacks the label.

**Cheapest test:** a checklist with `— tier 4 —` and no label; a checklist in `_inbox/done/`.

**Fix class:**
- Plan error: build on the existing loops or say why not; fix the pending `source:` rule.
- Choice inside Decision 2: key tier 4 on the field, the label, or both, and say where an unattended run's checklist is read.

## What holds up
- **No contract change needed.** The .txt file needs none (`promote-setting.txt` precedent; check.py:2726 reads only *.json as steps).
- **Section order passes.** A section between Fallbacks and Needs you passes the ordering checks (2757, 2549-2552, 2540).
- **The `tasks/` filter.**
- **The extraction and the newest_step walker.** Exactly two walkers exist (scope.py:205, :265). The migration must keep last_semantic ignoring status, which the unchanged tests cover.
- **The covered-set rule, the bounded stem bridge** (0 duplicates live), and the three states with their `not checked` wording.
- **Partial-step handling** for semantic, claims and synthesis.
- **The mode table.** It matches SKILL.md's markdown rows and the lint-only prose.
- **Reuse and cost.** `buckets()`/`me()` exist (wiki-triage.py:87, :125). The live arithmetic is bounded.
- **Decision 4's reading.** README.md:9 lists _entry_checks.py, _wiki_config.py and the search helper, not the scope script. Four skills call the scope script.

## Skip, drop, exempt and default rules against the standing rules
**Settled, or holds:**
- Decision 5 ("already covered" drops): a choice that quotes both sides.
- Staged entries left out when the setting is true: holds (requirements 68, 42; Mark's D2).
- `tasks/` and `sessions/` not counted: holds.
- "Not checked", never silent: holds.

**Gaps and conflicts:**
- **Rows 15, 22, 23 left out:** conflicts with Mark's rule "anything left undone". Row 22 (concept gaps) is non-empty in every mode. Choice for Mark.
- **A quoted review_after counts as a date:** this differs from wiki-report Step 1G's awk, so a `--full` report shows two past-due numbers (the Stale table/Numbers row and Left undone). Contract gap: say which one stays.
- **Needs-you count taken from the semantic line:** in `--lint-only --semantic` the Left undone line reads "no fix step in this mode", and the plan doesn't say what Needs you shows. Contract gap.
- **Part 1 interim wording:** two forms are offered. Plan error: pick one.
- **"Part 1 needs no step file":** the `ran` reason for past-review_after reads refresh.json. One sentence fixes it.

**No standing rule found:**
- A missing bucket folder counts 0.
- A malformed review_after gets its own line.
- The `Sources: not checked` and `(no reason recorded)` defaults.
- The `--brief` position and its "nothing" case.
- Other readers' buckets as one line (covered by Mark's D6).
- The reasons for a report-only run's disk-state lines.

## Is the plan complete enough to build?
Not yet, but it is close. Five plan errors are the planner's to fix:
- the check.py common checks and seed shape
- the mode cross-check and the drift test
- partial lint, the JSON shape, and the applied arithmetic
- the "last run" definition
- the existing ticket loops

Choices for Mark, beyond the seven Decisions:
- the same-day under-count
- whether concept gaps (row 22) are named
- the tier-4 field or label, and where the checklist is read

## Could not assess
- Whether the model goes straight to Step 8 on the resumed fixture (only a paid session shows it).
- Whether /wiki-refresh or Step 6.5 bumps last_reviewed after the lint.
- Whether an unattended run moves the checklist before Step 8.
- Reviewer only: `cmd_retry_list`, `wiki-list-add.py`.
- wiki-lint-mechanical.py beyond the lines read.
- The cost of the fixture builder.

VERDICT: KILL-ASSUMPTIONS FOUND
