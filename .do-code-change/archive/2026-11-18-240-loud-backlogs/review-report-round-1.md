# Review report, round 1, 240-loud-backlogs

Change under review: the working tree against merge-base `6f23c8c` (HEAD `f7759e1`; linear history, 36 commits), `.do-code-change/` excluded, no untracked files. Spec source: `.do-code-change/240-loud-backlogs/plan.md` (revision 7) and `requirements.md`. The Spec lenses were also told what the doubt log and checkpoints already settle. Pre-flight: `git rev-parse 6f23c8c` resolves, the diff is non-empty. Prescan passed (no review id, round, Q number or date in added Python comments, no over-width line), so no lens raised those.

The three lens pairs ran in the foreground, unnamed, as `code-reviewer-lens`, each pair on its own part. The lens model was the default tier, not raised. Each lens read its part's diff from a file written outside the project (the scratchpad), because the lenses have no shell. The reports below are each lens's own, kept un-merged. Where I converted a lens's indented sub-bullets to indented text, the words are the lens's.

Size check (`git diff --numstat`): part 1 source 1,006 changed lines; part 2 tests 2,091; part 3 docs and the rest 55. All under 3,000, so three parts (one lens per axis per part), every file in exactly one part.

## Standards

Part 1 (source)

- [important] `scripts/wiki-cycle-scope.py:1484` (`cmd_left_undone`), with the module at large (S16, S13): one script now holds a second tool.
    The diff grows it by +934/-56, and the left-undone counter is about 900 lines of it, including a module docstring of about 180 lines that specifies the output file. Quote: `def cmd_left_undone(nb: Path, args) -> int:`. One reader cannot hold the cycle-scope dispatch, the scope functions and the counter at once. Fix: move the counter into its own module (for example `scripts/_left_undone.py`) and keep `wiki-cycle-scope.py` as the dispatch; put the file-shape spec in `wiki-seed/` or the CHANGELOG, not the module docstring. S13 also applies to `cmd_left_undone`: it mixes review-date counts, event computation and two writes in one body, for example `events = copied_event_lines(last) if reporting else (`.
- [important] `scripts/wiki-cycle-scope.py:1008` (`session_buckets`), R8: `except Exception:  # noqa: BLE001` falls back to a `main` bucket for any failure.
    A broken `_inbox/intake/README.md` or an I/O error is silently counted as the default bucket. Fix: catch the parse and read errors `buckets()` can raise (`wiki-triage.py:125-132`) and let anything else surface.
- [suggestion] `scripts/wiki-cycle-scope.py:1012, 1121, 1300, 1347` (and `source_lines`), S4: the same `mode: str | None, problem: str | None` pair is passed to five functions, e.g. `def lint_lines(rf: Path, mode: str | None, problem: str | None) -> list[str]:`.
    Fix: one small reading record built once in `cmd_left_undone` that carries mode, modifiers and problem.
- [suggestion] `scripts/wiki-cycle-scope.py:1107` and `1127`, S5 and G19: the seven-field tuple `ENTRY_BACKLOGS` is unpacked positionally, `for label, result, scope_file, name, key, off, ran in ENTRY_BACKLOGS:`.
    Fix: a NamedTuple with named fields, and rename `off` to `mode_absent_wording`.
- [suggestion] `scripts/wiki-cycle-scope.py:1030`, N1: `for folder, _path, _source, _front_ in tri.intake_tickets(nb, bs):`; `_front_` reads as the `_front` function.
    Fix: use `_` for the unused fields. (Nit-level; kept as the lens labelled it.)
- [suggestion] `scripts/wiki-cycle-scope.py:995` (`_triage`) and `1226` (`_feeds`), S2: the same loader body is written twice, for example `spec = importlib.util.spec_from_file_location("_wiki_feeds_pkg", ...)`.
    Fix: one `_load_sibling(filename)` helper.
- [suggestion] `scripts/wiki-cycle-scope.py:943` (`def _iso_date(value: str) -> date | None:`), S2: duplicates `scripts/wiki-lint-mechanical.py:494` (`def _iso_date(value: str) -> bool:`), the same YYYY-MM-DD calendar check.
    Fix: one helper in `_wiki_config.py`.
- [suggestion] `scripts/wiki-cycle-scope.py:1090` (`uncovered`), S2: repeats the live-entry filter `if not (in_tasks(Path(e).relative_to("wiki")) or in_sessions(Path(e).relative_to("wiki")))`, which `review_date_counts` also writes out (`if in_tasks(rel) or in_sessions(rel): continue`).
    Fix: one `live_entries(nb)` helper.
- [suggestion] `scripts/wiki-cycle-scope.py:103` and `scripts/wiki-triage.py:166`, C1: change-history references in comments: `to <rf>/left-undone.txt and read by /wiki-report (task #240, lesson #9; Mark's rule: after a run, anything left` and `(task #240, step 3; the dequeue`.
    Fix: drop the task, lesson and attribution references; git holds that history. (The prescan covers review ids, rounds, Q numbers and dates, not task or lesson references.)
- [suggestion] `scripts/wiki-cycle-scope.py:430, 450, 484`, F3: `forced: bool = False` selects behaviour in `semantic_scope`, `claims_scope` and `synthesis_scope`; in `semantic_scope` and `synthesis_scope` it only changes the reason text.
    Fix: have the caller build the reason string.
- [suggestion] `scripts/wiki-cycle-scope.py:1498`, G28: `if past or (not problem and mode in STEP_MODES["refresh"] and refresh != "completed"):`, a compound condition with no name.
    Fix: `refresh_unchecked = ...` above it.
- [suggestion] `scripts/wiki-cycle-scope.py:1149`, G28: `elif own is None and key == "semantic" and found and datetime.now().astimezone() - cutoff < timedelta(hours=24):`; the clock is read inline.
    Fix: extract a named `ran_within_a_day(cutoff)` predicate.
- [nit] `scripts/wiki-cycle-scope.py:1476`, G4: `fmt = lambda s: ",".join(map(str, sorted(s)))  # noqa: E731`, a linter suppression with no reason.
    Fix: a one-line `def`.

Part 2 (tests)

- [important] `tests/scripts/test_cycle_scope.py:814` (also :1171, :1634, :1807, :1825, :1895), PY9: the header count is recomputed from the output's own bullet lines, e.g. `lines[:1] == [f"Left undone: {len([l for l in lines if l.startswith('- ')])} queue(s)"]`.
    The expected number is the implementation's arithmetic, not a known answer. Fix: pin the number as the neighbouring checks do, e.g. `["Left undone: 3 queue(s)", ...]`. The invariant (header equals bullet count) is real; the defect is that no check pins the number. Same defect at :1720, where `n >= len(want)` loosens the count to a bound (R15).
- [important] `tests/skills/wiki-cycle/check.py:3112-3113` with `tests/scripts/test_left_undone_fixture.py:66-84` (`compose_report`), PY9: the fixture grades check.py against a report the test composes.
    Quote: `f"| Stale (past review_after) | {stale} |", ""]`, where `stale` is read from the same `left-undone.txt` the check reads; check.py: `"the Numbers row's stale count equals Left undone's past count"`. In the fixture that check cannot fail, and the Needs-you checks pass on wording the test wrote. The docstring discloses the composition, which does not make the check bite. Fix: grade report-section checks on a report the wiki-report skill writes, or label them harness-only.
- [suggestion] `tests/scripts/test_cycle_scope.py:1109-1113` (`s4_entry`) and `:618-623` (`page`), S2, R3, N3: both rebuild the frontmatter that the existing `entry()` (file lines 31-34) already builds, and one file kind is named both `entry` and `page`.
    Fix: one builder with an `extra` argument and one name.
- [suggestion] `tests/scripts/test_left_undone_fixture.py:187-188` and `tests/skills/wiki-cycle/check.py:3125-3126`, S2: the same count filter, `counts = {k: v for k, v in summ.items() if k not in ("files_scanned", "standalone")`.
    Fix: one function in check.py, used by both.
- [suggestion] `tests/scripts/test_cycle_scope.py:1116` and `:826`, R14, G31: `git("add", "-A")` runs on the whole `tmp` root, so each scenario's commit also commits leftovers of earlier scenarios; line 826 (`root = tmp / "notebooks" / "lu1"`) reuses a notebook built by an earlier function.
    Results depend on run order; the lens found no failing check from it. Fix: a fresh `mknb` per scenario and commit only its path.
- [suggestion] `tests/scripts/test_cycle_scope.py:1231`, R14: `now = datetime.now().astimezone()` reads the wall clock while every other scenario uses fixed days.
    Fix: pin the time.
- [suggestion] `tests/skills/wiki-cycle/check.py:2822-2823`, S14: `_lu_step(run, cid, skill, step, stamp, status, summary, **extra)` takes seven parameters, and `cid` is always `ctx["cycle_id"]`.
    Fix: a step writer bound to the run folder and cycle.
- [suggestion] `tests/scripts/test_cycle_scope.py:848` and `:1051`, S2: the importlib spec-load is repeated.
    Fix: one loader near the top.
- [suggestion] `tests/scripts/test_cycle_scope.py:1046` and `:1644`, R15: `"names another notebook" in doc` and `"partial" in doc[...]` pass on any wording, not on behaviour.
    Fix: test the behaviour the docstring describes, or drop.
- [suggestion] `tests/scripts/test_cycle_scope.py:1109, 1367, 1371, 1678`, S1: the `s4_`, `s5_`, `s6_` prefixes name plan steps, and `SEMF`, `SUP`, `COLL`, `CLM` are abbreviations.
    Fix: name them by what they build.
- [suggestion] `tests/scripts/test_left_undone_fixture.py:185`, R13: `lj = suite._bl_lint(rf)`, and `suite._script` likewise, call check.py's private helpers.
    Fix: read `lint-mechanical.json` directly or expose a public helper.
- [suggestion] `tests/scripts/test_cycle_scope.py:1160, 1267, 1322`, S4: the same step-spec dict shape (`name`, `status`, `stamp`, `scope`) is built three times.
    Fix: one helper.
- [nit] tail, grouped by root cause: imports at `tests/skills/wiki-cycle/check.py:2699` (`from datetime import datetime, timedelta` mid-module) and `tests/scripts/test_cycle_scope.py:1163, 1497` (function-local), to move to the top; `check.py:2834` `_lu_complete(path)` rewrites the file in place and its name does not say so (N7/G20); `check.py:3042` `_lu_position` returns a bool no caller reads (R26).

Part 3 (docs and the rest)

- [important] `skills/wiki-cycle/wiki-seed/wiki-cycle.md:51`, C2: the unchanged bullet says "The report's Fallbacks section, just before Needs you, lists them", but Fallbacks no longer sits just before Needs you.
    Quote from the new line 52: "After the Fallbacks section and before Needs you, the report says what the run left undone". Fix: "The report's Fallbacks section, before Left undone and Needs you, lists them". Same defect at `skills/wiki-report/wiki-seed/wiki-report.md:22` ("the report has a Fallbacks section just before Needs you"; the new line 24 says "a Left undone section between Fallbacks and Needs you"). Fix: "a Fallbacks section, then Left undone, then Needs you".
- [important] `skills/wiki-report/SKILL.md:307`, C1: change history in a skill body, naming a removed line: "so the old generic line is narrowed on purpose".
    Fix: delete the parenthetical; keep "This line is about semantic findings only: mechanical lint findings are named in Left undone alone."
- [suggestion] `skills/wiki-cycle/SKILL.md:25` and `:97`, R3: one term, two sets. Line 25 header "# modifiers: <notebook> · --direct · --resume <cycle_id> · --no-confirm-discovery · --since <hours> · --lint-all"; line 97 "Write the run's modifiers (`--no-confirm-discovery`, `--lint-all`, `--direct`, `--since`)".
    The seed `skills/wiki-cycle/wiki-seed/wiki-cycle.md:38` lists a third set ("`<notebook>`, `--direct`, ... `--resume <cycle_id>`, `--all-topics`"); `reference.md:18` says "- Mode: <mode and flags>". Fix: define "modifiers" once (the four tokens the scope script reads) and use it in all four places, or rename the non-modifier items.
- [suggestion] `skills/wiki-cycle/SKILL.md:97`, S8: the sentence "Write the run's modifiers ... on the scratchpad's `**Cycle**` line" sits in the Step 1.5 block, which the mode table shows is skipped by `--ingest-only`, `--prompt-for-urls` and `--lint-only`, though `--direct` and `--lint-all` apply there.
    Fix: move the sentence to Step 0 (line 53), where the scratchpad is created from `reference.md`'s template (line 15, `**Cycle**: <cycle_id> (<mode>[, <modifiers>])`).
- [suggestion] `skills/wiki-report/SKILL.md:302-307`, S2 and S7 (lean skill): the three Needs-you wordings restate the states `scripts/wiki-cycle-scope.py:228` already writes ("`- Semantic findings: <N> — awaiting your approval; the findings are in lint-semantic.md`"), and the body carries the conditional rules for choosing among them, while the skill says the script's docstring "is the one source".
    Fix: have the script write the Needs-you line text, or move the wording table to `skills/wiki-report/reference.md` and keep one line in SKILL.md.
- [nit] `skills/wiki-cycle/SKILL.md:47`, C1: "(2026-10-19: six `--ingest-only` cycles left agentic-design's best practices 107 research entries behind ...)", a pre-existing date on a re-emitted line.
    Fix: keep the rule, drop the date, or leave it as history; the lens says it is not a new violation.
- [nit] `skills/wiki-report/wiki-seed/wiki-report.md:26` and `skills/wiki-cycle/wiki-seed/wiki-cycle.md:58`: "fixes or synthesis to approve" and "fixes to approve" describe a Needs-you list that now carries semantic findings only.
    Fix: "semantic lint findings and synthesis to approve".

Unverified:

- Part 1: whether the `session_buckets` fallback can hide a real config error in practice depends on which exceptions `buckets()` raises; the lens read only `wiki-triage.py:125-132`.
- Part 2: whether `wiki-cycle-scope.py` reads the wall clock or accepts a fixed `--now` (the lens did not read it, so the :1231 finding stands on the test side only); whether the repo runs ruff/E402 for the mid-module imports; whether `ctx["started"]` is timezone-aware (G26). The rule texts for R24, R25, PY1 and PY3 were not in the part 2 brief, so those four were not looked at in part 2 (part 1 judged them).
- Part 2: the brief said frozen expected counts were edited by 3 to 5 lines. The part 2 diff has no such edit (the only `-` line in `cases.json` is a trailing comma); `git diff --numstat` shows `test_cycle_scope.py` +1362 with 0 removed lines, so the final tree holds no edit of an existing line of that file.
- Part 3: `last_reviewed` and `review_after` in `skills/wiki-cycle/SKILL.md` (2026-10-19) and `skills/wiki-report/SKILL.md` (2026-09-08) were not bumped by this change; no pasted rule requires a bump and the lens did not search for one.

Coverage (every-diff rules and pasted sections, the three parts joined; a row is `clear` only when every part's was; part 3 has no code, so code-only rows are `n/a` there):

| Row | Verdict | Search or reason |
|---|---|---|
| 1 Mysterious Name S1/N1 | found | p1 `_front_`, `off`; p2 `s4_`/`SEMF` prefixes; p3 clear |
| 2 Duplicated Code S2/G5 | found | p1 loaders, `_iso_date`, live filter; p2 `s4_entry`, count filter, importlib; p3 wording tables |
| 3 Feature Envy S3 | clear | every new function read in p1 and p2 |
| 4 Data Clumps S4 | found | p1 `(mode, problem)`; p2 step-spec dict |
| 5 Primitive Obsession S5 | found | p1 `ENTRY_BACKLOGS` tuple; p2 clear |
| 6 Repeated Switches S6/G23 | clear | new mode branches read in one place each (p1, p2); p3 mode table row checked |
| 7 Shotgun Surgery S7 | found | p3 three-state rule across SKILL, two seed pages and CHANGELOG; p1 and p2 clear |
| 8 Divergent Change S8 | found | p1 module growth (S16 bullet); p3 modifiers rule placed in Step 1.5; p2 clear |
| 9 Speculative Generality S9 | clear | p1 no hook added; p2 every helper used |
| 10 Message Chains S10 | clear | read in full, p1 and p2 |
| 11 Middle Man S11 | clear | p1, p2 |
| 12 Refused Bequest S12 | clear | no subclasses |
| 13 Magic numbers G25 | clear | p1 24 h stated in docstring; p2 expected values in tests |
| 14 Flag Argument F3 | found | p1 `forced` at 430, 450, 484; p2 clear |
| 15 Answers and mutates R1 | clear | p1, p2 |
| 16 Hidden Side Effect N7 | found | p2 `_lu_complete` (nit); p1 clear |
| 17 Commented-out Code C5 | clear | p1, p2, p3 |
| 18 New code nothing uses R26 | found | p2 `_lu_position` return (nit); p1 Grep each new name; p3 every named command and file exists in the script |
| Comments C1 | found | p1 :103, wiki-triage :166; p3 SKILL.md:307, :47 |
| Comments C2 | found | p3 two seed pages; p1, p2 clear |
| Comments C3, R2 | clear | p1, p2, p3 |
| Names N2/N3/N5/N6/R3 | found | p2 `entry`/`page` (N3, R3); p3 "modifiers" (R3); p1 clear |
| Functions S13 | found | p1 `cmd_left_undone` |
| Functions S14, G19, G28 | found | p2 `_lu_step`; p1 `ENTRY_BACKLOGS`, :1498, :1149 |
| Functions G34, G29, R4, G16, S15 | clear | p1, p2 |
| Functions G31 | found | p2 `git add -A` and `lu1` order dependence |
| Classes S16 | found | p1 module growth |
| Classes G8, G7, G17, G18, G13, S17, S18, R5, R6, G35, G1 | clear | p1 |
| Error handling R8, G4 | found | p1 `session_buckets`, `noqa` lines |
| Error handling R7, R9, R10, R11 | clear | p1, p2 |
| Boundary G3, G33, G26, G2 | clear | p1, p2 (G26 p2 partly unverified, see above) |
| Tests T1, T3, T5, T6, R12, T4 | clear | p2; grep for skip/xfail: none |
| Tests R13, R14, R15 | found | p2 `_bl_lint`; :826, :1116, :1231; :1720, :1046, :1644 |
| Refactoring R21, R22, R23 | clear | the three extractions are separate hunks (p1); no `-` test lines (p2) |
| Refactoring R24, R25 | clear in p1; not looked at in p2 | rule text was not in the p2 brief |
| Python PY9 | found | p2 header count, composed report |
| Python PY2, PY7, PY8, PY10, PY11 | clear | p1, p2 |
| Python PY1, PY3 | clear in p1; not looked at in p2 | rule text was not in the p2 brief |
| Python PY4-PY6 | n/a | no async |
| Repo conventions (lean skills; no dead references; wiki-seed with no repo paths; CHANGELOG style) | found | p3 lean-skill finding; the other three clear |

Read depth, Standards: every file `in full`; see the file table. Well built: the left-undone checks pin exact expected line lists and the mode-table test reads the skill's own table with a flipped-cell control (p2); each new scope rule is a pure function a command and a backlog line share, with `step_results` as the one walk over step results (p1); every command, flag and file the new text names exists in the scope script (p3).

Checks made:
  - The three parts' file lists against `git diff --numstat 6f23c8c`: every changed file is in exactly one part and none is dropped.
  - `git ls-files --others --exclude-standard` (excluding `.do-code-change`) lists nothing, so no untracked file is outside the lenses' read.

## Spec

Part 1 (source)

- [suggestion] `scripts/wiki-cycle-scope.py` `uncovered()` and `entry_backlog_lines()` (claims branch, `scope, _all, _why, cutoff = claims_scope(nb)`, about line 1133): the claims cut-off and scope-now do not follow the plan's covered-set rule when no claims result exists or no claims index exists.
    Intent: "With no completed result anywhere, nothing is covered and scope-now is every entry" (plan, Implementation Decisions, covered-set bullet); "An entry revised after `C`'s day is counted whatever `S` says"; C for claims is "the claims index's written time". Implemented: `claims_scope()` returns only missing-or-revised entries when an index exists (about line 450-464), so with an index and no completed `claims.json` the claims line counts only those, not every entry; when the index is absent it returns `None` as the cut-off, `uncovered()` then sees `day is None`, and `if seen and (day is None or ...)` treats every S entry as covered, so the later-day rule is skipped. Affected: the "No claims, or revised since the index" line (requirements row 4); it can under-count in the no-claims-result case and skip the later-day rule in the no-index case. Fix: decide which rule is meant and align code and plan text; if the plan's rule holds, scope-now is every entry when no completed `claims.json` exists, and when the index is absent but `claims.json` is completed the cut-off is that run's timestamp, not `None`.
- [suggestion] `earlier_semantic_lines()` (about line 1420-1430): the superseded line uses different wording from the plan's answered Decision 10.
    Intent: "`Semantic findings from <older id>: N, superseded by a newer lint; not shown again; the findings are in lint-semantic.md (run <older id>); no later cycle step shows them again`" (plan, Decisions needed 10 and the Step 5 expected line). Implemented: `f"- Semantic findings from {folder.name}: {n}, superseded by a newer lint; no longer shown in full; " f"{where_findings(folder.name)}"`, and the module docstring carries the same wording. Affected: the Step 5 text in the plan, which asserts "not shown again…". Fix: restore "not shown again", or record the wording change in the plan and the Step 5 expected line. (The part 2 Spec lens raised the same drift from the test side, below.)

Part 2 (tests)

- [important] `tests/skills/wiki-cycle/check.py:3052-3113` (`_check_left_undone_planted`): the paid case-A check never compares the report's Left undone section with `left-undone.txt` and never rejects extra lines, so a paraphrased or padded section passes.
    Intent: plan.md:291 "A's lines are the expected lines listed under Case A and equal the script's file"; plan.md:13 the report pastes the file "word for word". Implemented: the check uses regex windows only (`_lu_find`, `wanted` list, check.py ~3079-3101); Grep for `left-undone\.txt` in check.py: no matches. Affected: case A's verdict on whether the model copies the section. Fix: assert the section's non-blank lines equal the file's lines (markdown stripped), and that no other queue line appears.
- [important] `tests/scripts/test_left_undone_fixture.py:139-167` (`grade`, `case_a`): the unpaid A side asserts only the `--show` output and the loose common checks, not the exact lines.
    Intent: plan.md:129 "plus the exact Left undone lines (A: the planted counts and reasons ...)". Implemented: `case_a` asserts five `--show` lines; `grade` prints `left-undone.txt` and asserts nothing about it. Affected: the planted counts and reasons are unproven before the paid session. Fix: assert `left-undone.txt` equals the case-A expected list in plan.md:126.
- [important] `tests/scripts/test_left_undone_fixture.py:72-82` (`compose_report`): the "applied or declined not recorded" and generic Needs-you branches exist only in the fixture's own composer, and no case exercises them.
    Intent: plan.md:280 "a `--full` fixture with 5 findings ... no `lint-fixes.txt` ... Needs-you line `5 semantic lint findings, applied or declined not recorded`; it is not dropped", and the no-`left-undone.txt` generic line; plan.md:131 makes these wordings a manual read. Implemented: no assertion in test_cycle_scope.py touches a Needs-you line; case A's builder always writes `lint-fixes.txt` (check.py ~2970-2972), so only the "awaiting" branch runs; PENDING.md:28 "not shown by any case" does not list these. Affected: the no-record, partial-lint and no-file outcomes. Fix: add a no-record case or a template-level test of the wiki-report rule, and list the gap in PENDING.md.
- [suggestion] Stale plan wording (not a code defect): plan.md:58, :236 and :280 quote "not shown again"; `scripts/wiki-cycle-scope.py:245-248, :1420, :1425` and `test_cycle_scope.py:1619-1621` use "no longer shown in full"; plan-red-team.md:35 recommended the change and the plan was not updated.
    Fix: update plan.md to the adopted wording.
- [nit] `test_cycle_scope.py:1767` and `:1774`: plan.md:286 names a checklist "in `_inbox/done/`"; the gate test uses `where="discovered"`. Fix: repeat with `where="done"`.
- [nit] `test_cycle_scope.py:1790-1792`: plan.md:285 names folder A as `--full`; the test uses `--quick`. Fix: use `--full`.
- [nit] `test_cycle_scope.py:843-848`: the third state is tested only under `--lint-only` and `--discover-only`; plan.md:280 says "every mode that lints". Fix: add a `--full` run with no `lint-mechanical.json`.
- [nit] `test_cycle_scope.py:837-844`: "missing notebook" (plan.md:259) is tested only as a notebook with no `wiki/`. Fix: add an unregistered notebook name.
- [nit] `test_cycle_scope.py:1811-1814`: plan.md:165's hash invariant is checked for `--report-only` only as "no events file". Fix: hash the tree.

Part 3 (docs and the rest)

- [important] `skills/wiki-report/SKILL.md:317`: the `--brief` rule says to copy line 1 of `left-undone.txt` but gives no printed state when the file is absent, so a brief report can print nothing.
    Intent: plan.md:13 "Silence is never a state", and the two no-file states are "complete as they stand" (so they are printed). Implemented: SKILL.md:317 "line 1 of `left-undone.txt` verbatim, followed by ... only when that line reads `Left undone: <N> queue(s)`", with no instruction for the absent case. Affected: `--brief` on a run folder with no file (or a standalone brief). Fix: add "when the file is absent, print its no-file line from the three states above".
- [suggestion] `skills/wiki-report/SKILL.md:304`: a third Needs-you wording adds "(no fix step in this mode)" to the plan's wording.
    Intent: plan.md:83 gives `<N> semantic lint findings, applied or declined not recorded — <run folder>/lint-semantic.md` (no parenthetical); plan.md:280 repeats it. Implemented: SKILL.md:304 adds the parenthetical; the phrase exists in the script only in Left undone (`wiki-cycle-scope.py:1371`). Affected: a `--lint-only --semantic` report; no test pins that line. Fix: drop the parenthetical, or amend plan.md:83.
- [suggestion] `skills/wiki-report/SKILL.md:307`: the no-line exception is wider than the plan.
    Intent: plan.md:83 "The only exception is an unusable findings list". Implemented: SKILL.md:307 also suppresses the line for "an unreadable file". Fix: narrow the text to an unusable list, or amend the plan.
- [suggestion] `skills/wiki-cycle/SKILL.md:158`: the zero-id record form is not stated; the flags are required by argparse.
    Intent: docstring `wiki-cycle-scope.py:278-280` says "either may be left out" and "with no ids at all it writes two empty lists". Implemented: SKILL.md:158 says "with no ids ... the same command with `--applied <ids> --declined <ids>`"; `:1587-1588` define `--applied`/`--declined` with no `nargs`, so a bare flag is an argparse error; `parse_ids` (`:1432-1434`) accepts `""`. Affected: the Step 5 record step on any run where nothing was applied or declined. Fix: "omit a flag that has no ids, or pass an empty string".
- [suggestion] `skills/wiki-cycle/wiki-seed/wiki-cycle.md:93`: "A script counts them fresh at the report step" has no `--report-only` exception.
    Intent: plan.md:62 and docstring `wiki-cycle-scope.py:121-128`: a `--report-only` run counts the disk-state queues fresh but copies the event lines from the last run. Fix: "counts the disk-state queues fresh; a `--report-only` run copies its event lines from the last run".
- [nit] `CHANGELOG.md:13`: "The rules live once, in the script's docstring" is not what the texts do.
    Implemented: presentation rules sit in skill prose (`wiki-report/SKILL.md:266`, `:302-307`, `:317`), and plan.md:263 places the Numbers and brief rules in prose. Fix: "The counting rules and line wording live in the script's docstring; the report and cycle skill hold the presentation rules".
- [nit] `skills/wiki-report/wiki-seed/wiki-report.md` (changed line, diff 166): "With `--brief` it adds the file's first line" omits the suffix rule at `SKILL.md:317`; "with the count, why and the way out" overstates the other-readers line, which has no reason (requirements Decision 6).
    Fix: state the suffix rule; "each queue with its reason, except the other readers' line".

Unverified:

- Part 1: `last_run()` picks the newest report folder by folder name (`d.name < rf.name`, `max(..., key=d.name)`), while `step_results()` says "never by folder name"; the plan says only "newest earlier run folder", so the lens did not count it as a finding; it needs the cycle-id format and a ruling. `claims_scope()` calls `json.loads` on `claims-index.json` with no guard, and `lint-fixes --show` calls `f.get` on each finding, so a malformed index or a non-object finding would crash the command; the plan states no rule for these inputs. Plan line 81 leaves a staged entry out of Left undone when `confirm_before_promote` is true, relying on Needs you, while requirements line 68 says a leftover staged entry is "named whatever `confirm_before_promote` says"; whether Needs you names it with a count is a skill-side question not checked. `known_sources` reads only the first 30 lines of each ticket (acknowledged gap in the doubt log, not re-raised).
- Part 2: pass counts in PENDING.md:28 (302/302, 67/67), the red-green sessions, the fixture test going green and the "three builder guesses" fix all need a run; a review runs none. PENDING.md:28 says each red-green run had one permission denial per model "under failed checks, the case passing", which conflicts with check.py:3154-3156 ("session completed" and denials); run logs were not in the brief. Whether `_set_confirm`, `_prepare_models` or `_commit_fixture` (check.py:826-835, run after the builder captures `ctx["lu_seeded"]`) write into the run folder, which would break the byte-identical check. Whether the "triage ran" gate (check.py ~3233-3240) excludes the new kinds (gate line not read). `wiki-promote --check` passing on case B (check.py:3224-3225). Whether the real `wiki-feeds.py known` reports `new` for the tier-4 test URLs (test_cycle_scope.py ~1759-1785). The `last_semantic`/`last_synthesis` migration and the unchanged `test_synthesis_scope.py` (plan.md:274) are not in the diff. Step-time invariants of steps 1-5 (interim line, step-1 header) cannot be seen in the final test file. Paid-only rows (session completed, denials, Phase 8/9, no ingester, byte-identical) are printed by the fixture as NEEDS-PAID-SESSION and not graded; the fixture's `empty_session()` would pass them by construction. One coverage row of the part 2 lens (step 1 Failures, "no mode token, never nothing", test ~771-778) reads "found (count differs; advisor-excluded)" with no finding raised; the lens gave no further account, so whether a count differs there is unverified.
- Part 3: the whole-change `framework-docs/` and `scripts/wiki-lint-mechanical.py` numstat (no hunk for either in this part; see Checks made). The `tests/skills/PENDING.md` row is not in this part's diff. CHANGELOG.md:9-14 describes the feature as shipped, while plan.md:290 puts the CHANGELOG after red-green; whether red-green ran is not in the part 3 brief (checkpoints.md records it passing). Requirements.md:68 ("named whatever confirm_before_promote says") against plan.md:45-46 and :81 (only when `false`): a requirements-versus-plan conflict, not a text mismatch.

Coverage (the three parts joined; a row is `clear` only when every part's was):

| Plan item | Verdict | Search |
|---|---|---|
| Step 1 header, mode and modifiers, review-date lines, mode table and drift test, refresh third state, exit-2 cases | clear | p1 diff read and traced; p2 tests ~650-905 and ~825-845 pin each; p2 nits on "missing notebook" and the `--full` lint third state |
| Step 1 Failures, no mode token never `nothing` | unverified | p2 row says the count differs, no finding given (see Unverified) |
| Step 3 `intake_tickets`, buckets, pending, staged, checklists | clear | p1 Grep `intake_tickets` (wiki-triage.py:164, callers 1030, 1191); p2 tests ~930-1047 and test_wiki_triage.py:280-312 |
| Step 3 Invariant, existing wiki-triage checks unchanged | unverified | not in the diff |
| Step 4 extraction, `newest_step`, six script tests | clear | p1 line-by-line comparison of old and new cmd_semantic/claims/synthesis, same output and files; migration tests not in the diff |
| Step 4 covered-set rule | found | p1 finding on the claims branch |
| Step 4 tests (not-linted, claims, synthesis, same-day, 24 h, malformed) | clear | p2 ~1161-1357 |
| Step 5 lint lines, partial lint, staleness guard, `lint-fixes`, semantic findings | clear | p1 diff read; p2 ~1391-1596 |
| Step 5 earlier-run lines, Decision 10 | found | wording drift (p1 and p2 findings) |
| Step 5 Needs-you wordings (script side and report side) | found | p2 three important findings; p3 `--brief` and wording findings |
| Step 6 sources, tier-4, report-only events, interim form removed | clear | p1 diff read; p2 ~1693-1880; p2 nits on folder A mode and the `done/` checklist variant |
| Invariants: no entry changed, no `*-scope.txt`, a false line never written | clear | p1 diff read; p2 hash tests ~679-682 |
| Invariant: `framework-docs/` and `wiki-lint-mechanical.py` unedited | clear | numstat lists neither (Checks made) |
| Testing Decisions: fixture builder, case A and B common checks, session resumed at Step 8 | clear in the checks that exist; paid-only rows unverified | check.py:3052-3231 and the fixture; p2 important findings on the exact-lines gap |
| Step 2 manual checklist (section, three states, Numbers row, `--brief`, Step 8 call and order, `--report-only` pointer, template line, Step 1.5 note) | found | p3: `--brief` absent-file gap; other items clear with cited lines |
| Step 7 manual (CHANGELOG, usage pages, PENDING row) | found | p3 CHANGELOG, usage-page nits; PENDING.md:28 row clear |
| Names the text uses exist in the script (`left-undone`, `lint-fixes`, `--show`, `--applied`, `--declined`, `--today`, `left-undone-events.txt`) | clear | p3 Grep: `:1581`, `:1584`, `:1586-1588`, `:1583`, `EVENTS_FILE :904` |

Read depth, Spec: part 1 both files `in full`; part 2 the diff `in full`, the test and check files read by their changed hunks (check.py `in part` outside the hunk, which is the unchanged remainder), source and `wiki-triage.py` in part by design; part 3 the SKILL.md files `in full`, `CHANGELOG.md`, `reference.md` and the two seed pages by their changed lines only (every changed line read; the unchanged remainder not). Well built: the moved commands reproduce their old output line by line through the new scope functions (p1); the tests pin almost every plan-quoted line verbatim and the drift test proves a flipped cell is caught (p2); the three-state rule, the copied N and the lint-fixes id validation are the same across the skill text, the usage page and the script (p3).

Checks made:
  - `git diff --numstat 6f23c8c -- . ":!.do-code-change"` lists no `framework-docs/` file and not `scripts/wiki-lint-mechanical.py`: the plan's invariant on those two holds for this diff.
  - `test_cycle_scope.py` shows +1362/-0 in the numstat: no line of the base file's existing tests was removed or edited, so no pre-existing test was loosened or deleted by this change.

## Change risk

Triage (per file, from the diff alone). No file is HIGH: no auth, authz, session or token, crypto, payment, external or network call, data migration, or removed validation. The one grep for `subprocess|urllib|requests|socket|os.system|Popen` over the added source lines matched only a docstring ("no subprocess"). The removed source lines are the old bodies of `last_semantic`, `last_synthesis`, `cmd_semantic`, `cmd_claims`, `cmd_synthesis`, re-expressed in the new shared functions, which part 1 Spec compared line by line.

| File | Risk | Why | Part | Standards | Spec | Change risk |
|---|---|---|---|---|---|---|
| `scripts/wiki-cycle-scope.py` | MEDIUM | business logic and shared walkers (`last_semantic`, `last_synthesis`) refactored; new public subcommands | 1 | in full | in full | not run |
| `scripts/wiki-triage.py` | MEDIUM | new function `intake_tickets` (a new public helper) | 1 | in full | in full | not run |
| `tests/scripts/test_cycle_scope.py` | LOW | tests | 2 | in full | in full (diff) | not run |
| `tests/scripts/test_left_undone_fixture.py` | LOW | tests | 2 | in full | in full | not run |
| `tests/scripts/test_wiki_triage.py` | LOW | tests | 2 | in full | in full | not run |
| `tests/skills/wiki-cycle/check.py` | LOW | tests | 2 | in full | in full (diff hunk; the rest of the file in part) | not run |
| `tests/skills/wiki-cycle/cases.json` | LOW | tests | 2 | in full | in full | not run |
| `tests/skills/PENDING.md` | LOW | docs | 2 | in full | in full | not run |
| `CHANGELOG.md` | LOW | docs | 3 | in full | in full (changed lines) | not run |
| `skills/wiki-cycle/SKILL.md` | LOW | docs (skill text) | 3 | in full | in full | not run |
| `skills/wiki-cycle/reference.md` | LOW | docs | 3 | in full | in full (changed line) | not run |
| `skills/wiki-cycle/wiki-seed/wiki-cycle.md` | LOW | docs | 3 | in full | in full (changed lines) | not run |
| `skills/wiki-report/SKILL.md` | LOW | docs (skill text) | 3 | in full | in full | not run |
| `skills/wiki-report/wiki-seed/wiki-report.md` | LOW | docs | 3 | in full | in full (changed lines) | not run |

No high-risk file; the change-risk lens was not run.

needs-a-human: none (0). No finding touches auth, authz, tokens or sessions (the "session" in the code is the cycle's scratchpad and sessions pages), or a production-data migration. A spec resolved, so there is no no-spec line.

Summary. Standards: 33 findings (part 1: 13; part 2: 13; part 3: 7); worst: the two `important` ones in part 1 (the module grows a second tool, `wiki-cycle-scope.py:1484`; the catch-all `session_buckets` fallback, `:1008`), two in part 2 (counts that reproduce the implementation's arithmetic, and a composed report that the Numbers-row check cannot fail on) and two in part 3 (the Fallbacks "just before Needs you" text now stale in two seed pages; change history in `wiki-report/SKILL.md:307`). Spec: 18 findings (part 1: 2; part 2: 9; part 3: 7); worst: four `important`, namely the case-A check that never compares the report's Left undone section with `left-undone.txt`, the unpaid case-A side that asserts no exact lines, the Needs-you branches only the fixture composer exercises, and the `--brief` rule with no printed state when the file is absent. The two axes point the same way on the Needs-you wording and on the not-pinned count assertions, and the Spec lens in part 1 and in part 2 each flagged the "not shown again" wording drift from opposite sides. Each Spec finding is worth acting on before the change moves on. Change risk: lens not run, no HIGH file. No file is still not read in full; the partly read context files are named in the read-depth lines above.

VERDICT: Standards FINDINGS · Spec FINDINGS · Change risk NOT RUN · needs-a-human 0
