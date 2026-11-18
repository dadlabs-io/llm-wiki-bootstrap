# 2026-11-18 240-loud-backlogs — the cycle report names everything a run leaves undone

## TL;DR
Every `/wiki-cycle` run now ends its report with a "Left undone" section, just above Needs you: each queue the run left non-empty (entries past or missing `review_after`, entries not linted, without claims or not synthesised, lint and semantic findings, dropped, failed and deferred sources, tickets in pending and in the buckets, staged entries, discovery checklists) with its count and why, or "Left undone: nothing". A script writes it (`wiki-cycle-scope.py left-undone`, with `lint-fixes` recording what the user applied at cycle Step 5) and the report pastes it, so no count is the model's. This is lesson #9 of task #240 (Mark: "after we run everything should be completed no? otherwise we should know about it and why?"); review moved the run-state reporting (`unfinished`, `left-undone`, `lint-fixes`) into its own module, `_run_state.py`. Kept on main, verified (tests-bite a named exception Mark approved), installed by the SOP.

## What changed
- Part 1. The script: header, mode, review-date lines, the third state for refresh
- Part 1. The report text: the section, the Numbers row, the brief line, the cycle Step 8 call, the template line
- Part 1. Buckets, pending, staged entries and discovery checklists
- Part 2. Entries not linted, without claims, not synthesised — counted by the covered-set rule
- Part 2. Lint findings, semantic findings, the fixes record, the earlier-run backlog and the Needs-you line
- Part 2. Dropped, failed and deferred sources, tier-4 deferrals, and `--report-only`'s copy of the last run
- Eval cases red then green, docs, finish
- The run-state reporting in its own module

New tags: none.

## Why: decisions and exclusions
All settled by Mark on 2026-11-16 (answers in `checkpoints.md` and in the Facts above); none is open.

1. Scope is whatever the run leaves undone, every non-empty queue it owns, named with count and reason, no age rule: "this is after we run, after we run everything should be comnpleted no? otherwise we should know about it and why?"
2. New "Left undone" section just above Needs you; "Left undone: nothing" when empty (Mark: "A").
3. The five backlogs a mode skips on purpose each get a count and a reason, counted fresh without running the skipped step (Mark: "A").
4. Each dropped, failed or deferred source is named with its reason, tier-4 deferrals included (Mark: "A").
5. Every lint finding kind above 0 gets a count and a reason; the fixes-awaiting line gets its count (Mark: "A").
6. Other readers' and `mark` buckets: one line naming them once, each with the count still to be processed (Mark: "If its not your bucket you dont really care. Naming them once with the left to be processed is fine").

- No refreshing, re-reading or re-dating of any entry, and no step run in a mode that does not run it today: clearing agentic-design's 607 is task #245, on Mark's go, in batches.
- No change to the review cadence or to when `review_after` is written.
- The rollback bug (`wiki-rollback.py` writes `review_after` = today, wiki `project/architecture/50-quality-and-promotion.md:268`) is not fixed here.
- No change to a queue the report already names with count and reason (rows 6, 9, 14, 16 to 20).
- No age rule and no threshold on any queue (Mark, 2026-11-16: the test is "left undone", not "old").
- No ingesting, triage or promotion of other readers' buckets: the cycle names them once, with counts, and never works them. No owner, reason or item list for them (Decision 6).
- No new lifecycle rule for skill files: `wiki-refresh` Step 1b keeps its own Skills table.
- No change to the framework-contract docs unless the cycle-step contract needs a new field (not shown to be needed; see the last section).
- No change to the lint's exit codes or to which findings are warn-only.
- No louder notification (no ping, no message outside the report), as Mark answered.

The plan's twelve further Decisions (2026-11-17, each answered with its recommended form) and the run-state module split (2026-11-18, review round 1) are in `checkpoints.md`.

## What the review found
Four review rounds, 102 findings: 31 addressed, the rest open by decision (suggestions and nits, none blocking; the writer's-text ones go back to eval-case-writer). The ledger read `met` at the end.

- standards-1 (round 1, important): `scripts/wiki-cycle-scope.py:1484` (`cmd_left_undone`), with the module at large (S16, S13): one script now holds a second tool. The diff grows it... — addressed
- standards-2 (round 1, important): `scripts/wiki-cycle-scope.py:1008` (`session_buckets`), R8: `except Exception: # noqa: BLE001` falls back to a `main` bucket for any failure. A bro... — addressed
- standards-3 (round 1, suggestion): `scripts/wiki-cycle-scope.py:1012, 1121, 1300, 1347` (and `source_lines`), S4: the same `mode: str | None, problem: str | None` pair is passed to f... — open
- standards-4 (round 1, suggestion): `scripts/wiki-cycle-scope.py:1107` and `1127`, S5 and G19: the seven-field tuple `ENTRY_BACKLOGS` is unpacked positionally, `for label, result, sco... — open
- standards-5 (round 1, suggestion): `scripts/wiki-cycle-scope.py:1030`, N1: `for folder, _path, _source, _front_ in tri.intake_tickets(nb, bs):`; `_front_` reads as the `_front` funct... — open
- standards-6 (round 1, suggestion): `scripts/wiki-cycle-scope.py:995` (`_triage`) and `1226` (`_feeds`), S2: the same loader body is written twice, for example `spec = importlib.util.... — open
- standards-7 (round 1, suggestion): `scripts/wiki-cycle-scope.py:943` (`def _iso_date(value: str) -> date | None:`), S2: duplicates `scripts/wiki-lint-mechanical.py:494` (`def _iso_da... — open
- standards-8 (round 1, suggestion): `scripts/wiki-cycle-scope.py:1090` (`uncovered`), S2: repeats the live-entry filter `if not (in_tasks(Path(e).relative_to("wiki")) or in_sessions(P... — open
- standards-9 (round 1, suggestion): `scripts/wiki-cycle-scope.py:103` and `scripts/wiki-triage.py:166`, C1: change-history references in comments: `to <rf>/left-undone.txt and read by... — open
- standards-10 (round 1, suggestion): `scripts/wiki-cycle-scope.py:430, 450, 484`, F3: `forced: bool = False` selects behaviour in `semantic_scope`, `claims_scope` and `synthesis_scope`... — open
- standards-11 (round 1, suggestion): `scripts/wiki-cycle-scope.py:1498`, G28: `if past or (not problem and mode in STEP_MODES["refresh"] and refresh != "completed"):`, a compound condi... — open
- standards-12 (round 1, suggestion): `scripts/wiki-cycle-scope.py:1149`, G28: `elif own is None and key == "semantic" and found and datetime.now().astimezone() - cutoff < timedelta(hou... — open
- standards-13 (round 1, nit): `scripts/wiki-cycle-scope.py:1476`, G4: `fmt = lambda s: ",".join(map(str, sorted(s))) # noqa: E731`, a linter suppression with no reason. Fix: a o... — open
- standards-14 (round 1, important): `tests/scripts/test_cycle_scope.py:814` (also :1171, :1634, :1807, :1825, :1895), PY9: the header count is recomputed from the output's own bullet... — addressed
- standards-15 (round 1, important): `tests/skills/wiki-cycle/check.py:3112-3113` with `tests/scripts/test_left_undone_fixture.py:66-84` (`compose_report`), PY9: the fixture grades che... — addressed
- standards-16 (round 1, suggestion): `tests/scripts/test_cycle_scope.py:1109-1113` (`s4_entry`) and `:618-623` (`page`), S2, R3, N3: both rebuild the frontmatter that the existing `ent... — open
- standards-17 (round 1, suggestion): `tests/scripts/test_left_undone_fixture.py:187-188` and `tests/skills/wiki-cycle/check.py:3125-3126`, S2: the same count filter, `counts = {k: v fo... — open
- standards-18 (round 1, suggestion): `tests/scripts/test_cycle_scope.py:1116` and `:826`, R14, G31: `git("add", "-A")` runs on the whole `tmp` root, so each scenario's commit also comm... — open
- standards-19 (round 1, suggestion): `tests/scripts/test_cycle_scope.py:1231`, R14: `now = datetime.now().astimezone()` reads the wall clock while every other scenario uses fixed days.... — open
- standards-20 (round 1, suggestion): `tests/skills/wiki-cycle/check.py:2822-2823`, S14: `_lu_step(run, cid, skill, step, stamp, status, summary, **extra)` takes seven parameters, and `... — open
- standards-21 (round 1, suggestion): `tests/scripts/test_cycle_scope.py:848` and `:1051`, S2: the importlib spec-load is repeated. Fix: one loader near the top. — open
- standards-22 (round 1, suggestion): `tests/scripts/test_cycle_scope.py:1046` and `:1644`, R15: `"names another notebook" in doc` and `"partial" in doc[...]` pass on any wording, not o... — open
- standards-23 (round 1, suggestion): `tests/scripts/test_cycle_scope.py:1109, 1367, 1371, 1678`, S1: the `s4_`, `s5_`, `s6_` prefixes name plan steps, and `SEMF`, `SUP`, `COLL`, `CLM`... — open
- standards-24 (round 1, suggestion): `tests/scripts/test_left_undone_fixture.py:185`, R13: `lj = suite._bl_lint(rf)`, and `suite._script` likewise, call check.py's private helpers. Fix... — open
- standards-25 (round 1, suggestion): `tests/scripts/test_cycle_scope.py:1160, 1267, 1322`, S4: the same step-spec dict shape (`name`, `status`, `stamp`, `scope`) is built three times.... — open
- standards-26 (round 1, nit): tail, grouped by root cause: imports at `tests/skills/wiki-cycle/check.py:2699` (`from datetime import datetime, timedelta` mid-module) and `tests/... — open
- standards-27 (round 1, important): `skills/wiki-cycle/wiki-seed/wiki-cycle.md:51`, C2: the unchanged bullet says "The report's Fallbacks section, just before Needs you, lists them",... — addressed
- standards-28 (round 1, important): `skills/wiki-report/SKILL.md:307`, C1: change history in a skill body, naming a removed line: "so the old generic line is narrowed on purpose". Fix... — addressed
- standards-29 (round 1, suggestion): `skills/wiki-cycle/SKILL.md:25` and `:97`, R3: one term, two sets. Line 25 header "# modifiers: <notebook> · --direct · --resume <cycle_id> · --no-... — open
- standards-30 (round 1, suggestion): `skills/wiki-cycle/SKILL.md:97`, S8: the sentence "Write the run's modifiers ... on the scratchpad's `**Cycle**` line" sits in the Step 1.5 block,... — open
- standards-31 (round 1, suggestion): `skills/wiki-report/SKILL.md:302-307`, S2 and S7 (lean skill): the three Needs-you wordings restate the states `scripts/wiki-cycle-scope.py:228` al... — open
- standards-32 (round 1, nit): `skills/wiki-cycle/SKILL.md:47`, C1: "(2026-10-19: six `--ingest-only` cycles left agentic-design's best practices 107 research entries behind ...)... — open
- standards-33 (round 1, nit): `skills/wiki-report/wiki-seed/wiki-report.md:26` and `skills/wiki-cycle/wiki-seed/wiki-cycle.md:58`: "fixes or synthesis to approve" and "fixes to... — open
- standards-34 (round 2, suggestion): `scripts/wiki-triage.py:167` (`intake_tickets` docstring) — C2: names a caller the move changed. Quote: `Used by wiki-cycle-scope.py's left-undone... — open
- standards-35 (round 2, suggestion): `scripts/_run_state.py:271` (`cmd_unfinished`, `cmd_lint_fixes`, `cmd_left_undone`) with `scripts/wiki-cycle-scope.py:494-508,512-518` — S7/G31: th... — open
- standards-36 (round 2, suggestion): `scripts/_run_state.py:213-215` (import of `_front`, `_parse_time`) — N2: underscore-private names imported across modules. Quote: `_front, _parse_... — open
- standards-37 (round 2, suggestion): `scripts/_cycle_common.py:4` (module docstring) — C1/C2: change history, and not quite true. Quote: `Moved here unchanged from wiki-cycle-scope.py... — open
- standards-38 (round 2, suggestion): `scripts/_run_state.py:413-426` (`session_buckets`, the standards-2 fix) — R11/R8: the narrowed `except` still swallows a read error that its own d... — addressed
- standards-39 (round 2, nit): `scripts/_cycle_common.py` (module name) — N2/S16: `_cycle_common` names the sharing, not the concept; its contents are notebook entries, run-folde... — open
- standards-40 (round 2, important): `tests/skills/wiki-cycle/check.py:3079-3088` — repo convention (tests/skills/README.md, "Who writes the cases"): the two checks grading the new `le... — addressed
- standards-41 (round 2, important): `tests/skills/PENDING.md:28` (the 2026-11-17 row; the lens cited line 353 of the file as it read it) — repo convention (every change is logged): th... — addressed
- standards-42 (round 2, important): `tests/scripts/test_left_undone_fixture.py:172` — PY9: `own(label, f"compose_report words the '{name}' branch as the skill does", got == want, (got... — addressed
- standards-43 (round 2, important): `tests/scripts/test_cycle_scope.py:1874` — R15, sibling of standards-14, unaddressed: `lines[0].startswith("Left undone: ") and lines[0].endswith("... — addressed
- standards-44 (round 2, suggestion): `tests/scripts/test_cycle_scope.py`, new `left_undone_session_buckets_lets_an_unexpected_error_surface` — R12/R3: the four README-shape checks carr... — open
- standards-45 (round 2, suggestion): `tests/scripts/test_left_undone_fixture.py:60-62` vs `:100` — S2: the `NEEDS_NO_FIX` and `NEEDS_NOT_RECORDED` constants repeat `compose_report`'s l... — open
- standards-46 (round 2, suggestion): `skills/wiki-report/wiki-seed/wiki-report.md:94` (the lens's line number; the `--brief` sentence of the Left undone paragraph) — C2: "With `--brief... — open
- standards-47 (round 2, nit): `INSTALL-INVENTORY.md:123` — C2: "whose docstring is the one source of their rules" sits after `wiki-cycle-scope.py`; the docstring is in `_run_sta... — open
- standards-48 (round 2, nit): `skills/wiki-cycle/wiki-seed/wiki-cycle.md:46` — C1: "a run begun before this rule" is migration wording on a line this change edited; CHANGELOG al... — open
- standards-49 (round 2, nit): `tests/scripts/test_cycle_scope.py:851` — names: `"wiki_cycle_scope_under_test"`, `"wiki_cycle_scope_newest_step"` and `"wiki_cycle_scope_session_b... — open
- standards-50 (round 3, important): PY11 `tests/scripts/test_left_undone_fixture.py:185`: the composer's own check prints as proof. Quote: `own(label, "compose_report writes 'Nothing.... — addressed
- standards-51 (round 3, important): C2 `tests/scripts/test_left_undone_fixture.py:56-57`: the new COMPOSED comment is wrong both ways. It says the section checks "pass by construction... — addressed
- standards-52 (round 3, suggestion): PY9 (writer's text) `tests/skills/wiki-cycle/check.py:3198-3200`: the write detector misses routes. Quote: `elif c["name"] == "Bash" and re.search(... — open
- standards-53 (round 3, suggestion): R9 `scripts/_run_state.py:426`: the re-raised error carries no path. Quote: `raise # an undecodable README is a read error, though UnicodeDecodeErr... — open
- standards-54 (round 3, suggestion): R3 `scripts/_run_state.py:676` (`step_data`: `except (OSError, ValueError): return {}`) and `:400` (`step_status`: `return "unreadable"`): sibling... — open
- standards-55 (round 3, suggestion): S14/S15 (writer's text) `check.py` `_lu_copy_checks(add, ctx: dict, run: dict, rtext: str, ftext: str)`: `ctx` is never used in the body. Fix: drop... — open
- standards-56 (round 3, suggestion): S2 (writer's text) `check.py:3030` `_lu_section` and `_lu_section_lines`: `re.search(r"^##\s+([^\n]*left undone[^\n]*)\n(.*?)(?=^##\s|\Z)", ...)` r... — open
- standards-57 (round 3, suggestion): C2/R3 (writer's text) `check.py:3148`: the header names `"left-undone-resumed"`, a kind `check()` never dispatches (dispatch at :3726 and :3728 use... — open
- standards-58 (round 3, suggestion): PY9 (writer's text) `_lu_report_text` in check.py: the fallback `sorted(run_dir.glob("*report*.md"))` can grade a different file as the report. "th... — open
- standards-59 (round 3, suggestion): C2 `tests/scripts/test_left_undone_fixture.py:16-19`: "the two checks that read them (names in COMPOSED) cannot fail here" and "the Left undone sec... — addressed
- standards-60 (round 3, suggestion): T5 `tests/scripts/test_left_undone_fixture.py:188-211` (`tamper_checks`): the variants are invented, reworded and dropped lines only. The `_lu_norm... — open
- standards-61 (round 3, nit): PY9 `tests/scripts/test_left_undone_fixture.py:52`: `"left-undone-verbatim": (..., "triage ran: one log row")`. check.py emits that check only for... — open
- standards-62 (round 3, nit): `tests/skills/PENDING.md` (the added 2026-11-17 row): "keeping the first wording) the no-file `--brief` line and the standalone-report Left undone... — addressed
- standards-63 (round 4, important): C2 / PY11 `tests/scripts/test_left_undone_fixture.py:16-18` (docstring) and `:56-62` (comment): the new wording says the COMPOSED checks "cannot fa... — addressed
- standards-64 (round 4, suggestion): S5 `tests/scripts/test_left_undone_fixture.py:65-68` and `report()` line 138: a check's name is carried as a raw prefix string in two files and not... — addressed
- spec-1 (round 1, suggestion): `scripts/wiki-cycle-scope.py` `uncovered()` and `entry_backlog_lines()` (claims branch, `scope, _all, _why, cutoff = claims_scope(nb)`, about line... — open
- spec-2 (round 1, suggestion): `earlier_semantic_lines()` (about line 1420-1430): the superseded line uses different wording from the plan's answered Decision 10. Intent: "`Seman... — open
- spec-3 (round 1, important): `tests/skills/wiki-cycle/check.py:3052-3113` (`_check_left_undone_planted`): the paid case-A check never compares the report's Left undone section... — addressed
- spec-4 (round 1, important): `tests/scripts/test_left_undone_fixture.py:139-167` (`grade`, `case_a`): the unpaid A side asserts only the `--show` output and the loose common ch... — addressed
- spec-5 (round 1, important): `tests/scripts/test_left_undone_fixture.py:72-82` (`compose_report`): the "applied or declined not recorded" and generic Needs-you branches exist o... — addressed
- spec-6 (round 1, suggestion): Stale plan wording (not a code defect): plan.md:58, :236 and :280 quote "not shown again"; `scripts/wiki-cycle-scope.py:245-248, :1420, :1425` and... — open
- spec-7 (round 1, nit): `test_cycle_scope.py:1767` and `:1774`: plan.md:286 names a checklist "in `_inbox/done/`"; the gate test uses `where="discovered"`. Fix: repeat wit... — open
- spec-8 (round 1, nit): `test_cycle_scope.py:1790-1792`: plan.md:285 names folder A as `--full`; the test uses `--quick`. Fix: use `--full`. — open
- spec-9 (round 1, nit): `test_cycle_scope.py:843-848`: the third state is tested only under `--lint-only` and `--discover-only`; plan.md:280 says "every mode that lints".... — open
- spec-10 (round 1, nit): `test_cycle_scope.py:837-844`: "missing notebook" (plan.md:259) is tested only as a notebook with no `wiki/`. Fix: add an unregistered notebook name. — open
- spec-11 (round 1, nit): `test_cycle_scope.py:1811-1814`: plan.md:165's hash invariant is checked for `--report-only` only as "no events file". Fix: hash the tree. — open
- spec-12 (round 1, important): `skills/wiki-report/SKILL.md:317`: the `--brief` rule says to copy line 1 of `left-undone.txt` but gives no printed state when the file is absent,... — addressed
- spec-13 (round 1, suggestion): `skills/wiki-report/SKILL.md:304`: a third Needs-you wording adds "(no fix step in this mode)" to the plan's wording. Intent: plan.md:83 gives `<N>... — open
- spec-14 (round 1, suggestion): `skills/wiki-report/SKILL.md:307`: the no-line exception is wider than the plan. Intent: plan.md:83 "The only exception is an unusable findings lis... — open
- spec-15 (round 1, suggestion): `skills/wiki-cycle/SKILL.md:158`: the zero-id record form is not stated; the flags are required by argparse. Intent: docstring `wiki-cycle-scope.py... — open
- spec-16 (round 1, suggestion): `skills/wiki-cycle/wiki-seed/wiki-cycle.md:93`: "A script counts them fresh at the report step" has no `--report-only` exception. Intent: plan.md:6... — open
- spec-17 (round 1, nit): `CHANGELOG.md:13`: "The rules live once, in the script's docstring" is not what the texts do. Implemented: presentation rules sit in skill prose (`... — open
- spec-18 (round 1, nit): `skills/wiki-report/wiki-seed/wiki-report.md` (changed line, diff 166): "With `--brief` it adds the file's first line" omits the suffix rule at `SK... — open
- spec-19 (round 2, important): `tests/skills/PENDING.md:28` — the paid evidence for case A is presented as covering the final check, but the strict check postdates those runs and... — addressed
- spec-20 (round 2, suggestion): `tests/skills/PENDING.md:28` — "Script tests: `test_cycle_scope.py` 302/302" matches no recorded count: checkpoints.md:176 says 310/310, :193 says... — addressed
- spec-21 (round 2, suggestion): `tests/scripts/test_left_undone_fixture.py:146-147` — the docstring says "compose_report writes each branch from the left-undone.txt line the skill... — open
- spec-22 (round 2, suggestion): `tests/scripts/test_left_undone_fixture.py:52-54` — the COMPOSED comment says "the section is the script's file verbatim, so those checks do bite";... — addressed
- spec-23 (round 2, suggestion): `scripts/_run_state.py:417` — `parse_errors` includes `ValueError`, and `UnicodeDecodeError` is one. `wiki-triage.py:129` calls `readme.read_text(e... — addressed
- spec-24 (round 2, suggestion): `skills/wiki-report/wiki-seed/wiki-report.md:24` and `CHANGELOG.md:16` — siblings of spec-12: they say "With `--brief` it adds the file's first lin... — open
- spec-25 (round 2, nit): `INSTALL-INVENTORY.md:123` — "the run-state reporting of `wiki-cycle-scope.py` … whose docstring is the one source of their rules": the commands an... — open
- spec-26 (round 2, nit): `skills/wiki-report/wiki-seed/wiki-report.md:22` — "read from the run folder's `fallbacks.txt`" now sits in a sentence covering Left undone and Nee... — open
- spec-27 (round 2, nit): `tests/skills/wiki-cycle/check.py:3030-3031` and `:3082` — `_lu_lines` filters `l.strip()` before stripping backticks, so a line of only "```" beco... — open
- spec-28 (round 3, important): S1 `scripts/_run_state.py:425-426`: plan step 3 still promises the default for a bad README, but the code now raises for a non-UTF-8 one. Intent, p... — addressed
- spec-29 (round 3, suggestion): S2/S7 `tests/skills/wiki-cycle/check.py:3268-3288` (`_check_left_undone_old_run`) and the PENDING row: the old-run case does not grade the Numbers... — open
- spec-30 (round 3, suggestion): S6 (writer's text) `check.py:3193-3204` (`_lu_model_wrote_file`): it sees only Write, Edit and Bash redirect or tee. In the verbatim kind the only... — open
- spec-31 (round 3, suggestion): S3 `tests/skills/wiki-cycle/check.py:3052, 3076, 3138, 3236, 3274, 3081` and `tests/scripts/test_left_undone_fixture.py:185`: checks the composer s... — addressed
- spec-32 (round 3, nit): (writer's text) `check.py:3148`: the header names `left-undone-resumed`, a kind that does not exist (checkpoints 207-210: held, not saved). Fix: na... — open
- spec-33 (round 3, nit): (writer's text) `_lu_norm_line` (check.py:3150-3163): it maps em and en dashes to hyphens, so a section that changes "—" to "-" passes "word for wo... — open
- spec-34 (round 3, nit): `tests/scripts/test_left_undone_fixture.py:2, 9-14`: the docstring describes "two Left undone cases" (A and B); the verbatim kind is now graded in... — addressed
- spec-35 (round 4, important): `tests/skills/wiki-cycle/check.py:3354` and COMPOSED (fixture lines 65-68): the check "the cycle report's last section is Needs you" is satisfied b... — addressed
- spec-36 (round 4, important): `tests/skills/wiki-cycle/check.py:3142`, `:3081`, `:3145`: "the section reads 'Left undone: nothing'", "the section does not read ...", "no queue l... — addressed
- spec-37 (round 4, nit): `.do-code-change/240-loud-backlogs/plan.md:272`: the amended bullet says an unparseable-frontmatter README "falls to `buckets()`'s one-bucket defau... — addressed
- spec-38 (round 4, nit): `tests/scripts/test_left_undone_fixture.py:45-46`: "scratchpad: Phase 8 done" and "Phase 9 done" are listed NEEDS-PAID-SESSION although the fixture... — open

## What was verified
Second pass (the first pass failed bar-unmoved and coverage; both were routed and fixed):

- tests: PASS — all seven script tests run fresh, each ended on its all-passed line: test_cycle_scope.py "322/322 passed"; test_wiki_triage.py "67/67 passed"; test_synthesis_scope.py "9/9 passed"; test_checker_hold.py "12/12 passed"; test_promote_setting.py "14/14 passed"; test_dequeue_intake.py "10/10 passed"; test_left_undone_fixture.py "every check passed" (wall total 34 s; its NEEDS-PAID-SESSION checks are listed apart by design and graded by the paid runs). The test scripts print no exit-code line of their own; the verdict is the all-passed line.
- diff contains the fix: PASS — `git diff 6f23c8c --stat -- . ':!.do-code-change'`: "18 files changed, 3700 insertions(+), 248 deletions(-)", the same 18 files as the first pass; `git status --short` empty, so all tracked and committed. `git diff 6f23c8c --stat -- framework-docs scripts/wiki-lint-mechanical.py` printed nothing (Invariant held).
- findings addressed: PASS — "review-ledger: met - no open blocking item, every verdict current (21 closed, 81 non-blocking), 4 round(s)" and "review-ledger: exit 0 - met". Cap lifted by Mark's standing word (checkpoints.md "Mark's standing word").
- frozen tests: PASS — "frozen-tests layer: PASS — 38 entries checked (+ 122 from earlier changes), all match or unfrozen with a reason (2 retired: deleted on purpose) (74 frozen green, each with its reason)" and "check-freeze: exit 0 - PASS: every frozen test matches, or changed with a reason".
- coverage: PASS — rows 3d and 8d are now `existing`, row 8b is `manual` per the plan's new line; every other row stays as the first pass found it.
- bar unmoved: PASS — "floor-guard: clean (3700 added, 248 removed lines checked)" and "floor-guard: exit 0 - clean: no move lowers the bar".
- in scope: PASS — "scope-guard: exit 0 - PASS: every touched file is inside the declared scope".
- tests bite: FAIL — NAMED EXCEPTION, approved by Mark (terminal, 2026-11-17, checkpoints.md "Mutation pass": "Hand pass, ~100 bugs (Recommended)"). `prove_tests_bite.py --check` COULD-NOT-RUN (it mutates only `src/`; this repo's code is in `scripts/`). Evidence in its place: 119 hand mutants, 111 killed, 6 survivors each killed by a new frozen test, 2 judged equivalent.

Paid runs: cases A and B red then green on both models (`20261117-193036`, `20261117-222534`, $10.46), the verbatim and old-run cases red then green on both models (`20261118-154943`, $6.27). Not shown by any case: a real `--full` run's report (the first one is the live check), a standalone report's Left undone line.

## Working files
Unchanged copies in the notebook's raw folder; the same files are archived in the code repository at `.do-code-change/archive/2026-11-18-240-loud-backlogs/`.

- [budget.json](../../../raw/code-changes/2026-11-18-240-loud-backlogs/budget.json)
- [checkpoints.md](../../../raw/code-changes/2026-11-18-240-loud-backlogs/checkpoints.md)
- [doubt-log.md](../../../raw/code-changes/2026-11-18-240-loud-backlogs/doubt-log.md)
- [hand-mutation-lu-result.json](../../../raw/code-changes/2026-11-18-240-loud-backlogs/hand-mutation-lu-result.json)
- [hand-mutation-lu.py.txt](../../../raw/code-changes/2026-11-18-240-loud-backlogs/hand-mutation-lu.py.txt)
- [name-review.md](../../../raw/code-changes/2026-11-18-240-loud-backlogs/name-review.md)
- [plan-red-team-round1.md](../../../raw/code-changes/2026-11-18-240-loud-backlogs/plan-red-team-round1.md)
- [plan-red-team-round2.md](../../../raw/code-changes/2026-11-18-240-loud-backlogs/plan-red-team-round2.md)
- [plan-red-team-round3.md](../../../raw/code-changes/2026-11-18-240-loud-backlogs/plan-red-team-round3.md)
- [plan-red-team-round4.md](../../../raw/code-changes/2026-11-18-240-loud-backlogs/plan-red-team-round4.md)
- [plan-red-team-round5.md](../../../raw/code-changes/2026-11-18-240-loud-backlogs/plan-red-team-round5.md)
- [plan-red-team-round6.md](../../../raw/code-changes/2026-11-18-240-loud-backlogs/plan-red-team-round6.md)
- [plan-red-team-round7.md](../../../raw/code-changes/2026-11-18-240-loud-backlogs/plan-red-team-round7.md)
- [plan-red-team.md](../../../raw/code-changes/2026-11-18-240-loud-backlogs/plan-red-team.md)
- [plan.md](../../../raw/code-changes/2026-11-18-240-loud-backlogs/plan.md)
- [readonly-red-team.json](../../../raw/code-changes/2026-11-18-240-loud-backlogs/readonly-red-team.json)
- [readonly-review.json](../../../raw/code-changes/2026-11-18-240-loud-backlogs/readonly-review.json)
- [requirements.md](../../../raw/code-changes/2026-11-18-240-loud-backlogs/requirements.md)
- [review-findings.md](../../../raw/code-changes/2026-11-18-240-loud-backlogs/review-findings.md)
- [review-ledger.json](../../../raw/code-changes/2026-11-18-240-loud-backlogs/review-ledger.json)
- [review-report-round-1.md](../../../raw/code-changes/2026-11-18-240-loud-backlogs/review-report-round-1.md)
- [review-report-round-2.md](../../../raw/code-changes/2026-11-18-240-loud-backlogs/review-report-round-2.md)
- [review-report-round-3.md](../../../raw/code-changes/2026-11-18-240-loud-backlogs/review-report-round-3.md)
- [review-report-round-4.md](../../../raw/code-changes/2026-11-18-240-loud-backlogs/review-report-round-4.md)
- [run.json](../../../raw/code-changes/2026-11-18-240-loud-backlogs/run.json)
- [scope-baseline.json](../../../raw/code-changes/2026-11-18-240-loud-backlogs/scope-baseline.json)
- [split-ast-check.py.txt](../../../raw/code-changes/2026-11-18-240-loud-backlogs/split-ast-check.py.txt)
- [step2-checklist.md](../../../raw/code-changes/2026-11-18-240-loud-backlogs/step2-checklist.md)
- [step5-checklist.md](../../../raw/code-changes/2026-11-18-240-loud-backlogs/step5-checklist.md)
- [test-freeze.json](../../../raw/code-changes/2026-11-18-240-loud-backlogs/test-freeze.json)
- [verification-result.md](../../../raw/code-changes/2026-11-18-240-loud-backlogs/verification-result.md)

## Related
- [code-changes/ — the folder and its tags](README.md)
- [2026-11-15 240-report-fallbacks — the cycle's report names every fallback](2026-11-15-240-report-fallbacks-the-cycle-s-report-names-every-fallback-from-the.md) (lesson #12, the section Left undone sits after)
- [2026-11-14 240-unfinished-run-check — a cycle's Step 0 names earlier runs that never finished](2026-11-14-240-unfinished-run-check-a-cycle-s-step-0-names-earlier-runs-that-nev.md) (lesson #10; its `unfinished` code moved into `_run_state.py` here, unchanged)
- [2026-11-15 240-backlink-block-check](2026-11-15-240-backlink-block-check-the-lint-checks-every-backlink-block-against.md) (lesson #11)
- [Research-cycle failures we hit, 2026-04 to 10](../troubleshooting/research-cycle-failures-we-hit-2026-04-to-10.md) (lesson #9, the failure this change answers)
