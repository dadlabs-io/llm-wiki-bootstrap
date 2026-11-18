# Review report, round 2 (focused), 240-loud-backlogs

Change under review: the files the fix rounds moved since round 1, taken as the delta f7759e1 -> HEAD 6954da3 (working tree clean, no untracked files), `.do-code-change/` excluded, plus the sibling sites of the ten addressed findings. Fixed point `6f23c8c` (`git rev-parse` resolves; `git merge-base 6f23c8c HEAD` returns `6f23c8c`; the diff is non-empty). Spec source: `plan.md` (revision 8) and `requirements.md`, with `doubt-log.md` and `checkpoints.md`. Prescan passed (clean) and the lenses were told so. The 41 open suggestions and nits of round 1 were not re-raised.

Files in the round, from the caller: CHANGELOG.md, scripts/wiki-cycle-scope.py, skills/wiki-cycle/SKILL.md, skills/wiki-cycle/wiki-seed/wiki-cycle.md, skills/wiki-report/SKILL.md, skills/wiki-report/wiki-seed/wiki-report.md, tests/scripts/test_cycle_scope.py, tests/scripts/test_left_undone_fixture.py, tests/skills/PENDING.md, tests/skills/wiki-cycle/check.py, and new since round 1: INSTALL-INVENTORY.md, scripts/_cycle_common.py, scripts/_install_tooling.py, scripts/_run_state.py. Files the earlier round reviewed and the fix rounds did not touch (`scripts/wiki-triage.py`, `tests/scripts/test_wiki_triage.py`, `tests/skills/wiki-cycle/cases.json`, `skills/wiki-cycle/reference.md`) are out of this round; nothing new is raised in them.

Size: the delta is about 2,450 changed lines (source 2,231 of which the moved bodies are most; tests 199; docs 24), under 3,000 for every axis. Two parts per axis: part 1 source (`wiki-cycle-scope.py`, `_run_state.py`, `_cycle_common.py`, `_install_tooling.py`, `INSTALL-INVENTORY.md`), part 2 tests and docs. Four lenses, all `code-reviewer-lens`, foreground, unnamed, `run_in_background: false` written out; each came back as a launch notice and its report was taken from its completion notification. Models: both part 1 lenses were raised to `sonnet` (a two-sided comparison of about 1,100 moved lines is beyond the default tier); both part 2 lenses ran on the default tier. The lenses read the diffs from files written outside the project (the scratchpad), because they have no shell.

How the move was reviewed: the AST identity check (`split-ast-check.py.txt`) compares 625223a with HEAD by top-level name only (95 of 97 identical). It does not cover module docstrings, imports or other statements, and its old side is 625223a, not the f7759e1 text round 1 reviewed, so a fix-round-1 edit inside a moved body (`session_buckets`) passes it. The part 1 lenses were therefore briefed to compare each moved name and docstring section against its `-` text in the f7759e1 -> HEAD delta, and to treat only the differences as new code.

## Standards

Part 1 (source)

- [suggestion] `scripts/wiki-triage.py:167` (`intake_tickets` docstring) — C2: names a caller the move changed. Quote: `Used by wiki-cycle-scope.py's left-undone counts`.
    The counts now live in `_run_state.py` (callers `bucket_ticket_lines` and `ticket_marked_sources`). Sibling site of standards-1. Fix: "Used by `_run_state.py`'s left-undone counts".
- [suggestion] `scripts/_run_state.py:271` (`cmd_unfinished`, `cmd_lint_fixes`, `cmd_left_undone`) with `scripts/wiki-cycle-scope.py:494-508,512-518` — S7/G31: the move split an implicit argparse contract across two files.
    `main()` defines `--mark-interrupted`, `--reason`, `--today`, `--show`, `--applied`, `--declined`, sets `args.topic_name` by hand and runs the `un.error(...)` checks; the consumers in `_run_state.py` read those attributes. A flag renamed in one file fails only at run time in the other. Fix: `_run_state.py` exports `add_arguments(sub)` for its three commands and `main()` calls it; a cheaper option is to name the Namespace attributes in each `cmd_*` docstring.
- [suggestion] `scripts/_run_state.py:213-215` (import of `_front`, `_parse_time`) — N2: underscore-private names imported across modules. Quote: `_front, _parse_time, claims_scope, entries, newest_step, ...`.
    `wiki-cycle-scope.py` imports `_front` too, so a name marked private now has two importers. Fix: drop the underscore (`front`, `parse_time`) in `_cycle_common.py`, in its own rename step.
- [suggestion] `scripts/_cycle_common.py:4` (module docstring) — C1/C2: change history, and not quite true. Quote: `Moved here unchanged from wiki-cycle-scope.py so the import runs one way`.
    `write_scope` and `_front` lost a date from their docstrings, so "unchanged" is false for those two. Fix: keep the rationale only: "wiki-cycle-scope.py imports this module and `_run_state.py`; `_run_state.py` imports this module; this module imports neither."
- [suggestion] `scripts/_run_state.py:413-426` (`session_buckets`, the standards-2 fix) — R11/R8: the narrowed `except` still swallows a read error that its own docstring says surfaces. Quote: `parse_errors: tuple[type[BaseException], ...] = (AttributeError, TypeError, ValueError)`.
    `wiki-triage.py:129` reads with `readme.read_text(encoding="utf-8")`; invalid UTF-8 raises `UnicodeDecodeError`, a `ValueError`, so it falls back to `main`, while the docstring says "a read error or any other failure surfaces". Fix: `except UnicodeDecodeError: raise` before `except parse_errors:`, or say in the docstring that an undecodable README counts as unparseable. (The Spec axis raises the same site below, from the plan's side.)
- [nit] `scripts/_cycle_common.py` (module name) — N2/S16: `_cycle_common` names the sharing, not the concept; its contents are notebook entries, run-folder step results and the scope functions. Fix: a concept name such as `_cycle_scopes.py`. The module is cohesive today, so S16 is not triggered.

Part 2 (tests and docs)

- [important] `tests/skills/wiki-cycle/check.py:3079-3088` — repo convention (tests/skills/README.md, "Who writes the cases"): the two checks grading the new `left-undone-planted` kind were added to the editing session's branch by hand.
    Quote README:17 "The session that changes a skill never writes or edits the cases that grade its change"; README:21 "(an existing kind is never changed)"; check.py:3079 "# the report pastes left-undone.txt word for word". The kind is new in this change, so the clause does not exempt it. Fix: send the two `add(...)` checks to eval-case-writer as text for the branch and save them unchanged; log the hand edit in PENDING until then. Sub-point (suggestion): the comment says "word for word" but `_lu_lines` (check.py:3031) strips `*` and backticks and the code drops `---` rules; reword the comment.
- [important] `tests/skills/PENDING.md:28` (the 2026-11-17 row; the lens cited line 353 of the file as it read it) — repo convention (every change is logged): the row still reads "Cases by `eval-case-writer`, saved unchanged" and "`test_cycle_scope.py` 302/302" after this diff added runtime `check()` calls, and never records the two hand-added check.py checks. The 2026-11-15 row shows the convention: "`check.py` changed after it".
    Fix: add "check.py: two checks added by hand after the runs (lines 3079-3088), no model run used them" and re-run the count.
- [important] `tests/scripts/test_left_undone_fixture.py:172` — PY9: `own(label, f"compose_report words the '{name}' branch as the skill does", got == want, (got, want))` prints a plain PASS on a check of the test's own composer. The same holds for the section checks, which pass by construction because `compose_report` writes `lu.rstrip()` (line 108): check.py:3083 "the section equals left-undone.txt" in grade A, and check.py:3148 "the section reads 'Left undone: nothing'" plus :3151 in case B. Line 54 says "the section is the script's file verbatim, so those checks do bite"; they bite only on tampered text (`tamper_checks`).
    Fix: add `"compose_report words"`, `"the section equals left-undone.txt"`, `"the section reads 'Left undone: nothing'"`, `"no queue line under"` to `COMPOSED`, have `own()` honour the label, and reword line 54. (Sibling of standards-15.)
- [important] `tests/scripts/test_cycle_scope.py:1874` — R15, sibling of standards-14, unaddressed: `lines[0].startswith("Left undone: ") and lines[0].endswith(" queue(s)")` under "with queues the header counts them"; a wrong count passes.
    Fix: `lines[:1] == ["Left undone: N queue(s)"]` with N the header this fixture yields.
- [suggestion] `tests/scripts/test_cycle_scope.py`, new `left_undone_session_buckets_lets_an_unexpected_error_surface` — R12/R3: the four README-shape checks carry the surfacing test's name (`..._lets_an_unexpected_error_surface: {label} in the intake README reads as`), so a failure there reads as a surfacing regression. Fix: rename that prefix to `left_undone_session_buckets_falls_back_on_a_malformed_intake_readme`, or split the function.
- [suggestion] `tests/scripts/test_left_undone_fixture.py:60-62` vs `:100` — S2: the `NEEDS_NO_FIX` and `NEEDS_NOT_RECORDED` constants repeat `compose_report`'s literal "applied or declined not recorded (no fix step in this mode)". Fix: build the composer's strings from the constants.
- [suggestion] `skills/wiki-report/wiki-seed/wiki-report.md:94` (the lens's line number; the `--brief` sentence of the Left undone paragraph) — C2: "With `--brief` it adds the file's first line." omits the no-file line that `skills/wiki-report/SKILL.md` now adds. Fix: append "With no file it adds that state's not-checked line."
- [nit] `INSTALL-INVENTORY.md:123` — C2: "whose docstring is the one source of their rules" sits after `wiki-cycle-scope.py`; the docstring is in `_run_state.py`. Fix: "whose docstring (in `_run_state.py`) is the one source".
- [nit] `skills/wiki-cycle/wiki-seed/wiki-cycle.md:46` — C1: "a run begun before this rule" is migration wording on a line this change edited; CHANGELOG already has a Migration field. Fix: drop it if the note is kept elsewhere.
- [nit] `tests/scripts/test_cycle_scope.py:851` — names: `"wiki_cycle_scope_under_test"`, `"wiki_cycle_scope_newest_step"` and `"wiki_cycle_scope_session_buckets"` now load `_run_state.py` or `_cycle_common.py`. Fix: rename to `run_state_*` / `cycle_common_*`.

Unverified:

- Part 1: the moved docstring was compared with the `-` text by reading only (no difference found); the AST check does not cover module docstrings, so a mechanical `diff` of the two texts would settle it.
- Part 2: who typed `check.py:3079-3088`; the header literal wanted at `test_cycle_scope.py:1874`; whether PENDING's 302/302 was re-run after the new checks; whether `case_a_expected`'s wording matches the script's real output (no run in a review).

Coverage (the two parts joined; a row is `clear` only when both parts' were):

| Row | Verdict | Search or reason |
|---|---|---|
| 1 Mysterious Name S1/N1 | clear | p1 every new name is moved, `parse_errors` read; p2 each added identifier read in scope |
| 2 Duplicated Code S2/G5 | found | p2 `NEEDS_*` constants vs composer literals; p1 clear (`_front` duplicate in wiki-triage is round-1 territory) |
| 3 Feature Envy S3 | clear | p1, p2 read |
| 4 Data Clumps S4 | clear | p1 moved; p2 tuples appear once |
| 5 Primitive Obsession S5 | clear | p1 moved; p2 test-local literals |
| 6 Repeated Switches S6/G23 | clear | no new mode branch |
| 7 Shotgun Surgery S7 | found | p1 argparse contract split across two files; p2 clear |
| 8 Divergent Change S8 | clear | p1 one concept per new module; p2 test files only add tests |
| 9 Speculative Generality S9 | clear | no hook added |
| 10 Message Chains S10 | clear | none in added lines |
| 11 Middle Man S11 | clear | none |
| 12 Refused Bequest S12 | clear | no subclass |
| 13 Magic numbers G25 | clear | no new literal; test expected values |
| 14 Flag Argument F3 | clear | no boolean parameter added; `forced` is round 1 |
| 15 Answers and mutates R1 | clear | `session_buckets` returns only; `tamper_checks` returns None |
| 16 Hidden Side Effect N7 | clear | `tamper_checks` name says it writes and restores |
| 17 Commented-out Code C5 | clear | read the added comment lines, p1 and p2 |
| 18 New code nothing uses R26 | clear | p1 every import and new name has a caller (Grep); p2 each new name called from main, a test or a check |
| Comments C1, C2 | found | p1 `_cycle_common.py:4`, `wiki-triage.py:167`; p2 wiki-report.md:94, INSTALL-INVENTORY:123, wiki-cycle.md:46 |
| Comments C3, R2 | clear | no TODO; new comments are rationale |
| Names N2, N3, N5, N6, R3 | found | p1 private-name import and module name; p2 stale load names |
| Functions (S13, G34, S14, G19, G28, G29, R4, G31, G16, S15) | clear | p1 only `session_buckets` is new (14 lines, flat); p2 each new function read |
| Classes S16, G8, G7, G17, G18, G13, S17, S18, R5, R6, G35, G1 | clear | p1 import direction one-way and acyclic by reading imports; p2 path constants only |
| Error handling R7, R9, R10 | clear | one `try`, flat |
| Error handling R8, G4, R11 | found | p1 `session_buckets` read errors; p2 `except type(exc)` scoped, clear |
| Boundary G3, G33, G26, G2 | clear | no new arithmetic; p2 four malformed README shapes covered |
| Tests T1, T3, T5, T6, T4 | clear | p2 session_buckets and tamper paths covered; no skip added |
| Tests R12 | found | p2 prefix naming |
| Tests R13 | clear | assertions on output and the check() result list |
| Tests R14 | clear | `lu10b` appears once, tmp-scoped; wall clock not read |
| Tests R15 | found | p2 `test_cycle_scope.py:1874` |
| Refactoring R21, R22, R23, R24, R25 | clear | p1 pure move per AST check and the lens's read of the `-` text; touched lines are imports and the docstring pointer; p2 no test removed |
| Python PY1, PY2, PY3, PY7, PY8 | clear | no cast, Any, new dependency or deprecated API |
| Python PY9 | found | p2 composed-label finding |
| Python PY10, PY11 | clear | plain functions; no coverage claimed |
| Repo conventions (README "Who writes the cases", PENDING log, wiki-seed rules) | found | p2 check.py hand edit and PENDING row |
| Sibling install lists | clear | Grep `_feeds.py` / `_task_cards.py|_source_identity.py` over scripts, tests and the repo: only `_install_tooling.py:119,125` (updated) and the INVENTORY row |

Read depth, Standards: part 1 all five files `in full`; part 2 `test_cycle_scope.py`, `test_left_undone_fixture.py`, `PENDING.md`, CHANGELOG and the four skill and usage files `in full` for every changed line; `check.py` `in part` by the lens's table (lines 3025-3153, which holds the whole 10-line delta and the neighbouring checks), so every changed line was read. Well built: the import direction is strictly one-way, every moved import is used and none is missing, and the install lists and inventory row were extended together (p1); `session_buckets` now lets OSError and RuntimeError surface and pins four malformed README shapes against exact outputs, the tamper check restores the report in a `finally`, and the two `COMPOSED` prefixes match check.py's names (p2).

## Spec

Part 1 (source): no findings. The lens tried to disprove each plan-step-8 claim (pure move, one-way import, `main()` and the docstring pointer kept, install lists and inventory, free names resolve, `STEP_MODES` and `STEP_FILES` readers, siblings, the docstring whole) and could not break any.

Part 2 (tests and docs)

- [important] `tests/skills/PENDING.md:28` — the paid evidence for case A is presented as covering the final check, but the strict check postdates those runs and nothing re-scores them.
    Intent: plan.md:295 "Done when the red-green command exits 0 with each of A and B `red then green` on both models" and "A's lines are the expected lines listed under Case A and equal the script's file". Code: the row says "**Red then green on both models** (old copy b7401bb)"; the equality checks are at check.py:3083-3088 ("the section equals left-undone.txt"), added after runs 20261117-193036 and -222534. The 2026-11-15 row records the same situation ("`check.py` changed after it, … no model run used the final `check.py`"), the 11-17 row does not. Affected: the case-A section-equality criterion is not shown on the final check.py. Fix: re-score the two saved case-A reports against the final check (no paid run), then say so in the row, or say the row covers the earlier check only.
- [suggestion] `tests/skills/PENDING.md:28` — "Script tests: `test_cycle_scope.py` 302/302" matches no recorded count: checkpoints.md:176 says 310/310, :193 says 317/317, and "302" appears nowhere in checkpoints.md. Fix: date the figure ("302 at the 2026-11-17 red-green run") or update it to 317/317.
- [suggestion] `tests/scripts/test_left_undone_fixture.py:146-147` — the docstring says "compose_report writes each branch from the left-undone.txt line the skill says picks it" and names "each no-file line compose_report writes". `compose_report` (:86-109) writes three wordings and no no-file line; its else branch (:101-102) picks by line text alone, while SKILL.md:305 also reads whether `lint-fixes.txt` exists for the partial and unreadable lines.
    Fix: state what is checked (skill substrings; the three composer branches); PENDING already lists the partial-with-record gap. (Sibling of spec-5.)
- [suggestion] `tests/scripts/test_left_undone_fixture.py:52-54` — the COMPOSED comment says "the section is the script's file verbatim, so those checks do bite"; in `grade()` the composed section is the file itself (compose_report :108), so the equality check passes by construction there and `tamper_checks` (:178-201) only shows it can fail. Fix: say that, or drop "do bite".
- [suggestion] `scripts/_run_state.py:417` — `parse_errors` includes `ValueError`, and `UnicodeDecodeError` is one. `wiki-triage.py:129` calls `readme.read_text(encoding="utf-8")` inside `buckets()`, which `session_buckets` calls in its try (:424); its docstring says "a read error or any other failure surfaces" (:416). A non-UTF-8 intake README becomes the silent `main` bucket and no test at test_cycle_scope.py:1053-1086 covers it.
    Intent: plan step 3 "an unparseable intake README falls to `buckets()`'s one-bucket default"; whether an undecodable file is "unparseable" or a read error needs a ruling. Fix: decide; if a read error, catch only the parse types and add a non-UTF-8 case. (Sibling of standards-2; the Standards axis raises the same site.)
- [suggestion] `skills/wiki-report/wiki-seed/wiki-report.md:24` and `CHANGELOG.md:16` — siblings of spec-12: they say "With `--brief` it adds the file's first line" and "`--brief` carries its first line" with no absent-file state, while `skills/wiki-report/SKILL.md:317` now says "When `left-undone.txt` is absent, print that no-file state's line instead". Fix: add that sentence to both. (The missing suffix rule is round 1's open nit, not re-raised.)
- [nit] `INSTALL-INVENTORY.md:123` — "the run-state reporting of `wiki-cycle-scope.py` … whose docstring is the one source of their rules": the commands and their docstring now live in `_run_state.py`. Fix: name `_run_state.py`'s docstring.
- [nit] `skills/wiki-report/wiki-seed/wiki-report.md:22` — "read from the run folder's `fallbacks.txt`" now sits in a sentence covering Left undone and Needs you, which do not read that file. Fix: move the clause to the Fallbacks item.
- [nit] `tests/skills/wiki-cycle/check.py:3030-3031` and `:3082` — `_lu_lines` filters `l.strip()` before stripping backticks, so a line of only "```" becomes "", and `-{3,}` leaves a `___` rule in place; a fenced or `___`-separated paste would fail a non-verbatim report. Fix: strip first, then drop blanks, and drop `_{3,}` too.

Unverified:

- Who wrote `check.py:3079-3088` (plan "Seam 2": cases and check branches come from eval-case-writer, saved unchanged); checkpoints.md:154 and :160 record the writer's fixes but none for these two checks.
- Whether saved paid reports (20261117-193036, -222534) pass the strict check; the lens's Glob found nothing under the repo or project-notebooks. Settle by re-scoring.
- When 302/302 was measured (see the suggestion above).
- Frozen-test count: checkpoints.md:194 says "6 from fix round 1 … and 3 from step 8"; the delta shows seven header-pin checks and four functions repointed to `_run_state.py` or `_cycle_common.py`. Recount before Mark's yes to re-freeze (the checkpoints say 9 frozen tests changed and await it).
- Whether the drift test was red on an empty table before the fix (plan.md:302); the checkpoints record only "316 → 317".
- Case A's exact lines depend on builder data not read (bucket order "security 2, mark 1", lint key order).
- Part 1: the producer's "saved outputs byte-identical" and "316 to 317" claims, and the AST check's own result, were not run by the lens; it compared every `-` body against the new modules by eye and agrees with "95 identical, 2 docstring dates". `requirements.md` and `doubt-log.md` were only grepped by the part 1 lens.

Checks made:
  - Plan step 8's pure-move claim, two-sided (part 1 lens, from the f7759e1 -> HEAD delta): the only differences between the `-` text and the new modules are `session_buckets` (the standards-2 fix: `parse_errors`, `YAMLError`) and the two docstring dates in `write_scope` and `_front`; every moved docstring section of `unfinished`, `left-undone` and `lint-fixes` is present in `_run_state.py:1-201`.
  - Free names: all 29 names defined only in `wiki-cycle-scope.py` were searched in the two new modules (no live reference), and every name the script still uses from the moved code is imported there.
  - Tests loading the script as a subprocess (`test_checker_hold.py:67`, `test_promote_setting.py:88`, `test_synthesis_scope.py:21`, `test_left_undone_fixture.py:252,277`) need no moved attribute; `STEP_MODES` is read only at `test_cycle_scope.py:854` from `_run_state.py`, and the guard at `:889-890` fails on an empty table.
  - `case_a_expected` has 15 queue lines, matching its header and plan.md:126 item by item; the pinned header counts 5, 4, 4, 9, 5, 1, 3 derive from their scenarios.
  - Orchestrator's own sibling searches: `except Exception` / `noqa: BLE001` in `_run_state.py`, `_cycle_common.py`, `wiki-cycle-scope.py`, `wiki-triage.py`: none (only specific exception tuples); `len([l for l in lines if l.startswith("- ")])` in `test_cycle_scope.py`: remaining at :679 (`== 6`) and :1754 (`n == 9`), both pinned; none in `check.py`.

| Plan item | Verdict | Search or reading |
|---|---|---|
| Step 8 pure move, bodies unchanged | clear | p1 every `-def` / `-NAME =` read against the new modules |
| Step 8 one-way import | clear | `_run_state.py:213`; `_cycle_common.py` imports only `_entry_checks`, `_atomic_io` |
| Step 8 script keeps scope commands, `main()`, usage lines, pointer | clear | `wiki-cycle-scope.py:5-18`, `88-90`, `main()` |
| Step 8 install lists and inventory | clear | `_install_tooling.py:118-126`; INVENTORY row |
| Step 8 free names resolve | clear | p1 Greps (above) |
| Step 8 docstring whole | clear | p1 section by section |
| Step 8 tests load where the name lives; drift test red on empty table | clear | p2 Grep `spec_from_file_location`: :851 RUN_STATE, :1055 RUN_STATE, :1091 CYCLE_COMMON; guard :889-890 |
| Step 8 docs name the new module | clear, nit | p2 Grep `docstring`; INVENTORY:123 and wiki-report.md:22/24 residue |
| spec-3 section equals file | clear logic; paid evidence found | check.py:3079-3088 traced; PENDING finding |
| spec-4 exact lines in the unpaid side | clear | `case_a_expected` against plan.md:126 |
| spec-5 Needs-you branches and no-file lines | clear (text), suggestion on the composer docstring | `needs_you_wordings` against SKILL.md:303-307 |
| spec-12 `--brief` absent file | clear in SKILL.md; siblings found | SKILL.md:317; wiki-report.md:24, CHANGELOG:16 |
| standards-14 pinned counts | clear, one sibling found | line 1874 |
| standards-15 "PASS (composed)" | clear, sibling found | COMPOSED names match check.py:3111-3123; PY9 finding |
| standards-27 Fallbacks position | clear | wiki-cycle.md:46, wiki-report.md:91, SKILL.md:192 |
| standards-28 change history | clear | SKILL.md:307 has no parenthetical |
| Step 3 `session_buckets` unparseable README | found | `_run_state.py:417` |

Read depth, Spec: part 1 all five files `in full`; part 2 `test_left_undone_fixture.py` `in full`; `test_cycle_scope.py`, `check.py`, `PENDING.md`, CHANGELOG and the four skill and usage files reported `in part` by the lens (every delta hunk and its neighbours read, the unchanged remainder not): every changed line of the round was read, so no retry was spawned. Well built: the move is exactly a move (p1); case A's expected list is written out in full and its tamper variants prove the equality check bites, the header counts are literal, and the drift guard and loads point at the module where each name lives (p2).

## Change risk

No file is HIGH, so the lens was not run; the triage table follows (risk from the diff alone; no auth, authz, session or token, crypto, payment, external call, data migration or removed validation).

| File | Risk | Why | Part | Standards | Spec | Change risk |
|---|---|---|---|---|---|---|
| `scripts/wiki-cycle-scope.py` | MEDIUM | business logic: dispatch and imports after the move | 1 | in full | in full | not run |
| `scripts/_run_state.py` | MEDIUM | new module, moved business logic | 1 | in full | in full | not run |
| `scripts/_cycle_common.py` | MEDIUM | new module, shared helpers and scope functions | 1 | in full | in full | not run |
| `scripts/_install_tooling.py` | MEDIUM | install manifests: a missing entry breaks every installed scope command | 1 | in full | in full | not run |
| `INSTALL-INVENTORY.md` | LOW | docs | 1 | in full | in full | not run |
| `tests/scripts/test_cycle_scope.py` | LOW | tests | 2 | in full | in part (all delta hunks read) | not run |
| `tests/scripts/test_left_undone_fixture.py` | LOW | tests | 2 | in full | in full | not run |
| `tests/skills/wiki-cycle/check.py` | LOW | tests | 2 | in part (delta hunk and 3025-3153) | in part (delta hunk and 3020-3200) | not run |
| `tests/skills/PENDING.md` | LOW | docs | 2 | in full | in part (changed row) | not run |
| `CHANGELOG.md` | LOW | docs | 2 | in full | in part (changed lines) | not run |
| `skills/wiki-cycle/SKILL.md` | LOW | docs (skill text) | 2 | in full | in part (changed lines) | not run |
| `skills/wiki-cycle/wiki-seed/wiki-cycle.md` | LOW | docs | 2 | in full | in part (changed lines) | not run |
| `skills/wiki-report/SKILL.md` | LOW | docs (skill text) | 2 | in full | in part (262-321) | not run |
| `skills/wiki-report/wiki-seed/wiki-report.md` | LOW | docs | 2 | in full | in part (changed lines) | not run |

No high-risk file; the change-risk lens was not run. Out of the round (reviewed in round 1 and untouched by the fix rounds): `scripts/wiki-triage.py`, `tests/scripts/test_wiki_triage.py`, `tests/skills/wiki-cycle/cases.json`, `skills/wiki-cycle/reference.md`.

needs-a-human: none (0). No finding touches auth, authz, tokens or sessions (the "session" in the code is the cycle's scratchpad and sessions pages) or a production-data migration. A spec resolved, so there is no no-spec line.

Summary. Standards: 16 findings (part 1: 6, all suggestion or nit; part 2: 10, of which four important: the two hand-added case-A checks in `check.py` against the README's "who writes the cases" rule, the PENDING row left stale, the composed-report checks that print a plain PASS, and the loosened header check at `test_cycle_scope.py:1874`). Spec: 9 findings (part 1: 0; part 2: 9, worst the one important item: the PENDING row still presents the paid red-then-green runs as covering a case-A check that was added after them). The two axes point the same way on `session_buckets` (`_run_state.py:417`: an undecodable intake README reads as the silent default bucket although the docstring says read errors surface) and on the PENDING row. The pure move itself is clean on both axes: no moved body differs from its earlier text apart from the expected `session_buckets` fix and two docstring dates. All findings are worth acting on before the change moves on. Change risk: lens not run, no HIGH file. Every changed line was read; files named `in part` above are read by their changed hunks plus context.

Notes for the caller: the Spec part 2 and Standards part 2 lenses, and the part 1 lenses, all returned reports on the first spawn; no retry was needed. Bash use in this review exceeded the 12-call budget by one (13 calls; the three full diffs printed first duplicated the later writes to files); no call changed the project.

VERDICT: Standards FINDINGS · Spec FINDINGS · Change risk NOT RUN · needs-a-human 0
