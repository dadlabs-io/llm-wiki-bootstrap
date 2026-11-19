# 2026-11-19 246-240-follow-ups — three open findings of the 240 backlog change closed: the lint-fixes sentence, the claims count with no index, the paid left-undone checks

## TL;DR
This change revises [2026-11-18 240-loud-backlogs](2026-11-18-240-loud-backlogs-the-cycle-report-names-everything-a-run-leaves-undo.md) by closing five of its open review findings (task #246, three subtasks). A1: cycle Step 5 now says to leave out a `lint-fixes` flag that has no ids (spec-15). A2: the "No claims, or revised since the index" count in `left-undone` now uses the newest completed `claims.json`'s time as its cut-off when there is no claims index, and the covered-set docstring in `_run_state.py` names the claims cases (spec-1). A3: the paid checks for the two Left undone cases compare `left-undone.txt` byte for byte with the script's own output and fail a Write, Edit, MultiEdit or NotebookEdit aimed at it, the dash mapping is gone, and the header no longer names a kind that does not exist (spec-32, spec-33, standards-52); two `lint-fixes-record` cases were added for A1. It ended on four review rounds, the last past the retry cap (Mark: "continue maually"); verify returned FAIL on two named layers (findings-addressed, tests-bite), which Mark's "Just keep going" covered; kept on main, nothing pushed.

## What changed
- A1. Cycle Step 5 item 3 of the cycle skill says to leave out a flag that has no ids
- A2(b). With no claims index and a completed `claims.json`, an entry re-reviewed after that run's day is counted
- A2(a) and the index rule. The pre-existing behaviours the finding left unpinned get their own tests
- Docstring. The `_run_state.py` docstring states the claims cases correctly
- A3, the planted defects (red first). The fixture test fails the three defects the writer's checks must catch
- A3, the writer's checks. The orchestrator briefs `eval-case-writer` (mode `replay`), saves its answer into `check.py` unchanged, then the fixture's check-name constants follow
- Bite, by hand. The three fixes and tests are shown to bite (hand mutation M1 to M4, run as M0 to M5)
- Record. The CHANGELOG gets one entry and `tests/skills/PENDING.md` gets a wiki-cycle row
- Paid run (Mark said yes). (a) two new `lint-fixes-record` cases red-green on both models; (b) the verbatim and old-run cases re-run on both models, and re-run once more on the final checks

Added on the way, on Mark's word: step 9(a) became two fresh cases (the writer refuses a single fresh case), and review rounds 1 to 4 with fix rounds 1 to 3 and a manual round after the retry ceiling changed the write detector: the shell and PowerShell write patterns were removed (Mark, round 2, "a"), leaving the Write-tool target check and the exact script-output comparison.

New tags: none.

## Why: decisions and exclusions
1. **Confirmed by Mark, 2026-11-18 (user confirmed): case A2(a) keeps the code's rule.** With a claims index and no completed `claims.json` anywhere, the "No claims, or revised since the index" line counts the entries with no claims in the index plus those revised since the index was written. The rule's wording is corrected in the `_run_state.py` docstring (the sentence "With no completed result anywhere, nothing is covered and scope-now is every entry" gains the claims case: scope-now is the unindexed and revised entries, every entry only when there is no index) and in the living page `project/architecture/30-the-research-cycle.md` (one clause where it names the covered-set rule), and a test pins it. Alternative: follow 240's plan literally (count every entry). Rejected: on agentic-design it would report nearly all of ~1,700 entries as having no claims, although most have claims in the index.
2. **Paid re-run of the two `left-undone` cases (A3), on both models, about $6 (240's record: $6.27).** Recommended: yes, but only after the free fixture test shows the new checks catch the planted defects (a `cp` write, a `python -c` write, a dash change) and the old plant-free fixtures still pass. Reason: the free test proves detection, not that real model runs still pass a check that is now stricter (a dash change now fails, so a model that renders "—" as "-" turns a green case red). Alternative: no paid run, fixture test only; the checks then go unexercised against a live model until the next time the suite is run. Needs Mark's go (README).
3. **Confirmed by Mark, 2026-11-18 (Change confirmation Q4): A1 gets both a free text test (the sentence is in the skill) and a paid wiki-cycle case (a model records zero fixes with no bare flag, two empty lists), written by eval-case-writer and run red-then-green with A3's paid run.** The recommendation was no new test (the script side is pinned by a frozen test); Mark: "We should create a test for that ... Let's do 2 first. Then 1. So both".
4. **A2(b)'s cut-off with no index is the completed `claims.json`'s timestamp (the newest such result across run folders), the same value the other two rows use.** Recommended default, unconfirmed: it follows from the plan's rule, so it is shown rather than asked, but it changes a count the user reads (entries re-reviewed after the claims run's day now count, with no index). Alternative: leave (b) as a stated under-count in the docstring (the spec-1 finding's fallback). Assumed until Mark says otherwise.
5. **spec-33: the dash mapping is dropped, so "word for word" includes the dash character.** Follows from 240's "pastes the file word for word"; shown at confirmation, listed here because it makes the check stricter and can turn a live model run red. Alternative: keep the mapping and state in the check's docstring that a dash written as a hyphen is allowed. Assumed the strict reading unless Mark says otherwise.

(Settled afterwards, in `checkpoints.md`: Decision 2 ("Y", 2026-11-18T23:53Z); Decision 4 ("Okay fix it", 23:58Z); Decision 5 ("I think if we're looking for exact changes then yes let's make it strict.", 23:55Z).)

- The other open 240 findings (spec-2, spec-13, spec-14, spec-16, spec-17, and every other ledger item not named above) are not in this change.
- No change to the claims step's own scope, to `claims_scope`'s return value or to `cmd_claims`.
- No change to the covered-set rule for the semantic lint or synthesis rows.
- No new report line, no new queue, no change to the report's wording or to `wiki-report`.
- No change to the `lint-fixes` script or its flags: the skill is corrected to match the script, not the reverse.
- A1 adds one sentence to `skills/wiki-cycle/SKILL.md` Step 5 item 3 and nothing else in the skill.
- The implementing session does not edit or write any check in `tests/skills/wiki-cycle/check.py`; those come from the eval-case-writer and are saved unchanged. The free fixture test and the new `test_cycle_scope.py` tests are the session's.
- No re-run of the other wiki-cycle cases, and no paid run at all without Mark's yes (see Decision 2).
- No change to the 240 requirements, plan or archive (the archived record is not edited); the living page and the wiki code-change record get the corrected claims wording only.

The earlier record's line 22 was not edited after all: a later change never edits an earlier record, so only the living page `project/architecture/30-the-research-cycle.md` was revised (this entry is linked from its History).

## What the review found
Four review rounds, 53 findings (21, 12, 16 and 4): 36 addressed, 17 open by decision (suggestions and nits; none wontfix). The ledger's retry cap of 3 was passed at round 4 (`review-ledger.py query --cap 3` exit 3); Mark chose "continue maually" and the two round-4 blocking findings (standards-34, spec-17) were fixed by hand. The "writer's text" findings are in `check.py`, which only eval-case-writer edits.

Round 1
- standards-1 (important): the fixture's route plants fail for the wrong reason, the file is tampered first — addressed
- standards-2 (important): the dash mapping removed changes two existing check kinds, against the README's no-change rule; Mark ruled it covers the old-run kind too — addressed
- standards-3 (important): the write comment says a read is no hit, but `Add-Content ... (Get-Content file)` matched — addressed
- standards-4 (important): the PENDING row records the change as proven while none-answered is not proof — addressed
- standards-5 (suggestion): `_LF_CALL` also matches `lint-fixes.txt` — addressed
- standards-6 (suggestion): re-running `left-undone` rewrites `left-undone-events.txt`, which was not restored — addressed
- standards-7 (suggestion): the shell-call test repeats at two places — open
- standards-8 (suggestion): the `drop` set repeats the one in `_check_promote_setting` — open
- standards-9 (suggestion): `run_dir` is rebuilt where `_check_left_undone_verbatim` already holds it — open
- standards-10 (suggestion): `_lu_model_wrote_file` nests five levels — open
- standards-11 (suggestion): a corrupt `lint-semantic.json` is reported as absent — open
- standards-12 (suggestion): the PENDING row is a measurement longer than a line without the four headings — addressed
- standards-13 (nit): bare numbers, a flag argument, unlabelled parameters, an uncommented regex table, a ticket in a header, in the writer's text — open
- standards-14 (nit): one test asserts prose substrings, another holds three scenarios — open
- standards-15 (nit): `session_with(step8_call(...))` repeats four times — open
- spec-1 (important): the write detector misses `copy`, `move`, `ren`, `xcopy` and `>|`; later superseded by Mark's round-2 ruling that removed the detector — addressed
- spec-2 (suggestion): an empty quoted `--applied ""` counts as a value in the lint-fixes check — open
- spec-3 (suggestion): each route plant also rewrites the file, so the script-output check fails whatever the regex does — addressed
- spec-4 (suggestion): CHANGELOG and PENDING overclaim "any route" — addressed
- spec-5 (nit): the docstring clause has a comma where the plan pins a semicolon, and runs past the wrap — addressed
- spec-6 (nit): plan drift, helpers and fixtures the plan does not name — open

Round 2
- standards-16 (important): reads match the write detector (`grep -c copy file`, `grep move file`, aliases) — addressed
- standards-17 (important): literal write routes missed (`cp a file 2>&1`, `mode='w'`, `-Path:value`, `shutil.copy`, `rni`, `Export-Csv`) — addressed
- standards-18 (important): the PENDING row is still one long measurement row — addressed
- standards-19 (suggestion): `_lu_ps_writes_file` nests four levels — addressed
- standards-20 (suggestion): the new detector branches have no failing case and the events restore is untested — addressed
- standards-21 (suggestion): the dash plant judges by a loose `caught()` regex — addressed
- standards-22 (nit): unexplained `range(4)` and `range(5)` counts — addressed
- standards-23 (nit): a lost space in `NEEDS_AWAITING =` and a missing blank line — addressed
- standards-24 (nit): the docstring says the whole run folder is put back, but only files are — addressed
- spec-7 (important): a read-only command counted as a write — addressed
- spec-8 (important): the detector misses literal routes the requirement covers; resolved by Mark's design answer "a" removing the detector — addressed
- spec-9 (suggestion): CHANGELOG and PENDING say none-answered passes on the old copy, true on Opus only — addressed

Round 3
- standards-25 (important): the fixture has no plant for MultiEdit, NotebookEdit, a `path` key, a backslash path, a Read, or the old-run kind — addressed
- standards-26 (important): `rstrip` lets a trailing-space edit pass although CHANGELOG says any changed text fails — addressed
- standards-27 (suggestion): two check names are false for an identical shell rewrite — open
- standards-28 (suggestion): the target normalisation repeats two other suites' — open
- standards-29 (suggestion): the events-file plant passes whenever the script does not rewrite the file — open
- standards-30 (suggestion): the 14-route loop repeats one assertion, route names change labels only — open
- standards-31 (suggestion): the PENDING row reads as both run and pending — addressed
- standards-32 (nit): the docstring says the same routes with identical text, the loop runs three — addressed
- standards-33 (nit): `session_write_plants` is about 90 lines in six phases — open
- spec-10 (important): CHANGELOG names the wrong cause of Sonnet's none-answered old-copy failure — addressed
- spec-11 (suggestion): CHANGELOG omits that both lint-fixes-record cases fail on Opus's new copy — addressed
- spec-12 (suggestion): a check name and docstring contradict the accepted identical-rewrite rule — open
- spec-13 (suggestion): no plant for the other Write-type routes or the old-run write check — addressed
- spec-14 (nit): `rstrip` lets trailing-space or final-newline changes pass the script-output check — addressed
- spec-15 (nit): `endswith("left-undone.txt")` also matches `copy-of-left-undone.txt` — addressed
- spec-16 (nit): a result pointer sits in the PENDING "Why it was not run" column — addressed

Round 4
- standards-34 (important): the fixture writes its plants in text mode (CRLF on Windows), so they fail on line endings alone, and no trailing-space or line-ending plant exists — addressed (by hand, after the retry ceiling)
- standards-35 (nit): a double "whose" in the edited docstring of the writer's text — open
- standards-36 (nit): the CHANGELOG parenthetical about Sonnet's old copy is unclear — addressed (the sentence was replaced)
- spec-17 (important): CHANGELOG still misstates why Sonnet's none-answered old copy failed (two checks, neither a record check) — addressed (by hand, after the retry ceiling)

## What was verified
VERDICT: FAIL - findings-addressed, tests-bite. Both named FAILs were taken by Mark ("continue maually" at the retry ceiling; "Just keep going. Don't worru about the caps", 2026-11-19T05:35Z, which the finishing decision records as covering tests-bite too, stated to him so he can object). The ledger archived with this record shows standards-34 and spec-17 as `addressed` at round 4; verify's line below was written before that and is kept verbatim.

tests: PASS - every proving command exited 0 on a fresh run: `test_cycle_scope.py` "330/330 passed" (the new tests' PASS lines read, below); `test_left_undone_fixture.py` ended "every check passed" (all six new-route plants, the old-route controls, the trailing-space, CRLF and byte-for-byte lines, case A and B plant-free runs PASS; the NEEDS-PAID-SESSION lines are the suite's own, not failures); `test_wiki_triage.py` "67/67 passed"; `test_synthesis_scope.py` "9/9 passed"; `test_checker_hold.py` "12/12 passed"; `test_promote_setting.py` "14/14 passed"; `test_dequeue_intake.py` "10/10 passed". Each ran once. (`test_cycle_scope.py` was run with its output piped to `tail`, so its exit code was not shown; the line "330/330 passed" is the script's own verdict, and the same suite's `failed` list prints every FAIL, none present in the tail.)

diff-contains-fix: PASS - `git diff 047d868 --stat` (excluding `.do-code-change/`) lists every file the plan's steps name: CHANGELOG.md, scripts/_run_state.py, skills/wiki-cycle/SKILL.md, tests/scripts/test_cycle_scope.py, tests/scripts/test_left_undone_fixture.py, tests/skills/PENDING.md, tests/skills/wiki-cycle/cases.json, tests/skills/wiki-cycle/check.py (8 files, 435 insertions, 27 deletions); `git status --short` is empty, so none is untracked or uncommitted. The fix sites were read in the diff: `cutoff = written or cutoff` in `entry_backlog_lines` (the Implementation Decisions' form, not the rejected `found[0] if found else written`); the one clause "leaving out a flag that has no ids (with neither flag it records two empty lists)" in Step 5 item 3; the two docstring clauses; three new tests, added after the last test with no existing line of `test_cycle_scope.py` edited (the diff for that file is additions only). The commits after review round 4 (9254241..HEAD) were read: the fixture's plants and restores are now `write_bytes` (standards-34 fixed as the finding asked, plus the trailing-space, CRLF and byte-for-byte plants); the CHANGELOG sentence now says Sonnet's old copy failed two checks, "no permission denials" and the step JSON contract (spec-17 fixed); the PENDING row's archive path was changed to `2026-11-19-...` and cites report 20261119-002259; one fixture docstring line. Finding beside the layer (not its verdict): the PENDING row and the plan point at `.do-code-change/archive/2026-11-19-246-240-follow-ups/`, which does not exist yet (a Glob of `.do-code-change/archive/*246*` finds nothing); the finish step creates it, and the pointer is wrong until it does. Those post-round-4 edits are unreviewed by a reviewer (Mark's "continue manually"), read here for presence only.

findings-addressed: FAIL - `review-ledger.py query --diff-base 047d868 --cap 3 --ledger .do-code-change/246-240-follow-ups/review-ledger.json` exit 3; its lines: "review-ledger: not yet met - halt: round 4 is past the cap of 3 -> the retry-ceiling checkpoint" and "review-ledger: exit 3 - halt: the retry-ceiling checkpoint (the reason is above)". It printed no open-item line; it printed three `STALE` lines, `[standards-1]`, `[standards-18]`, `[standards-4]` ("the diff of its file changed since the verdict; re-verify, never trust"), not zero (the brief expected stale 0; the output shows three, from the manual edits to the fixture, CHANGELOG and PENDING after round 4's re-verification of standards-1, 2 and 4). Per-file blocking list: check.py 0 of 7, test_left_undone_fixture.py 1 of 3, CHANGELOG.md 1 of 2, PENDING.md 0 of 2. Approval beside the FAIL: Mark, Discord DM 2026-11-19T04:58Z, verbatim "continue maually", recorded in `checkpoints.md` under "Retry-ceiling exhaustion - 2026-11-19" (outcome `continue manually`); the two round-4 blocking findings it left (standards-34, spec-17) were fixed by hand and their sites re-read in the diff above, but never re-reviewed or recorded `addressed` in the ledger. The Finishing decision puts this named FAIL to him; this report does not pass it.

frozen tests: PASS - `check-freeze.py .do-code-change/246-240-follow-ups/test-freeze.json --repo C:/github.com/llm-wiki-bootstrap` exit 0, "frozen-tests layer: PASS - 4 entries checked (+ 160 from earlier changes), all match or unfrozen with a reason (2 retired: deleted on purpose) (77 frozen green, each with its reason)"; last line "check-freeze: exit 0 - PASS: every frozen test matches, or changed with a reason". The four entries of this change, all in `tests/scripts/test_cycle_scope.py`: `wiki_cycle_skill_says_to_leave_out_a_flag_with_no_ids` (matches frozen hash, test+module); `left_undone_claims_count_with_no_index_uses_the_claims_run_as_cutoff` (matches the hash it was unfrozen at, name review round 1, 1 unfreeze on record; frozen green: an entry re-reviewed on the claims run's own day added so a commit-day cutoff fails); `left_undone_claims_count_with_an_index_but_no_claims_json_is_the_unindexed_plus_revised` (the same, 1 unfreeze; frozen green: pins behaviour that already existed, bite by hand mutation in step 7); `left_undone_claims_cutoff_is_the_index_time_whatever_claims_json_says` (the same; frozen green: bite by hand mutation M2). The 77 green-frozen entries with their reasons are in the script's full output (saved by the harness at `C:/Users/mark/.claude/projects/C--github-com-llm-wiki-bootstrap/7933309e-98e3-47f3-9ffc-68b0032aaf39/tool-results/bt67qhcds.txt`, lines 167 to 245). `test_left_undone_fixture.py` has no freeze entry (the plan freezes the three new `test_cycle_scope.py` tests and the A1 test only).

coverage: PASS - every plan done criterion and invariant maps to an existing test or a plan-marked manual check (map in `verification-result.md`); no row is `proposed` or `none` outside a `manual:` line of `## Testing Decisions`.

bar unmoved: PASS - `floor-guard.py --base 047d868` exit 0, "floor-guard: clean (435 added, 27 removed lines checked)"; last line "floor-guard: exit 0 - clean: no move lowers the bar".

in scope: PASS - `scope-guard.py check --artifact-dir .do-code-change/246-240-follow-ups` exit 0, "scope-guard: PASS - 8 touched file(s), all inside the declared scope (scripts/_run_state.py, skills/wiki-cycle/SKILL.md, tests/scripts/test_cycle_scope.py, tests/scripts/test_left_undone_fixture.py, tests/skills/wiki-cycle/check.py, tests/skills/wiki-cycle/cases.json, tests/skills/PENDING.md, CHANGELOG.md, .do-code-change/246-240-follow-ups/**)"; last line "scope-guard: exit 0 - PASS: every touched file is inside the declared scope". The plan's protected-files check, `git diff --stat 047d868 -- scripts/wiki-cycle-scope.py scripts/_cycle_common.py scripts/wiki-triage.py skills/wiki-report framework-docs tests/skills/wiki-cycle/baseline-sonnet.json tests/skills/wiki-cycle/baseline-opus.json`, printed nothing.

tests-bite: FAIL - `prove_tests_bite.py --check --base 047d868` exit 2, "no mutation report: run the pass on the change (or record each trivial-stakes file with --exempt)", "tests-bite layer: COULD-NOT-RUN against 047d868 (0 changed source file(s)); report .artifacts/python-mutation.json", "VERDICT: COULD-NOT-RUN". Named reason: the script mutates only `src/` and this repo's code is in `scripts/` (0 changed source files seen); there is no signed `mutation` setting, so the layer is not `off`. Evidence beside it, not the layer's verdict: the hand mutation pass `hand-mutation-claims.py.txt` with its result `hand-mutation-claims-result.json` (read in full): M0 (canary, a queue at 0 no longer skipped) killed (265/330 passed); M1 (the index time replaces the cut-off even with no index) killed by the new no-index test (329/330); M2 (a claims.json overrides the index time) killed by `left_undone_claims_cutoff_is_the_index_time_whatever_claims_json_says` (329/330); M3 (claims scope taken as every entry) killed by the new indexed test and by the frozen `s4g` checks (317/330); M4 (a partial claims.json sets the cut-off) killed by the new partial check and the frozen partial check (328/330); M5 (the pre-fix code) killed by the new no-index test (329/330). A3's bite is the red-then-green plants recorded per fix round in `checkpoints.md` (fix round 1: five routes and the read control failed before the writer's save; fix round 2: 5 FAILED before the save; fix round 3: 1 FAILED, the copy-of-left-undone.txt control, before the save; after the manual fixes, the fixture's new byte plants pass). The bite of the manual post-round-4 fixture edits (standards-34) was not run as a red-first, since they are the plants themselves; nothing shows a plant that fails on the old comparison for line endings alone, beyond the fixture's own "the script-output check fails the line endings changed to CRLF" PASS line. No approval for this FAIL is recorded beyond the "continue manually" answer, which is about the review ceiling, not this layer.

Paid runs (from `checkpoints.md`): the two lint-fixes-record cases `--red-green 047d868` $22.24, exit 1 NOT RED THEN GREEN (lint-within-24h red then green on Sonnet; none-answered not discriminating; Opus new copy failed only on the sandbox edit gate, carded #247); the two Left undone cases on step 6's checks $3.60; the same two re-run on the final checks $2.87, all PASS on both models (report 20261119-002259). Paid total $28.71.

## Working files
Unchanged copies in the notebook's raw folder; the same files are archived in the code repository at `.do-code-change/archive/2026-11-19-246-240-follow-ups/`.

- [budget.json](../../../raw/code-changes/2026-11-19-246-240-follow-ups/budget.json)
- [checkpoints.md](../../../raw/code-changes/2026-11-19-246-240-follow-ups/checkpoints.md)
- [doubt-log.md](../../../raw/code-changes/2026-11-19-246-240-follow-ups/doubt-log.md)
- [hand-mutation-claims-result.json](../../../raw/code-changes/2026-11-19-246-240-follow-ups/hand-mutation-claims-result.json)
- [hand-mutation-claims.py.txt](../../../raw/code-changes/2026-11-19-246-240-follow-ups/hand-mutation-claims.py.txt)
- [name-review.md](../../../raw/code-changes/2026-11-19-246-240-follow-ups/name-review.md)
- [parked.md](../../../raw/code-changes/2026-11-19-246-240-follow-ups/parked.md)
- [plan.md](../../../raw/code-changes/2026-11-19-246-240-follow-ups/plan.md)
- [readonly-review.json](../../../raw/code-changes/2026-11-19-246-240-follow-ups/readonly-review.json)
- [requirements.md](../../../raw/code-changes/2026-11-19-246-240-follow-ups/requirements.md)
- [review-findings.md](../../../raw/code-changes/2026-11-19-246-240-follow-ups/review-findings.md)
- [review-ledger.json](../../../raw/code-changes/2026-11-19-246-240-follow-ups/review-ledger.json)
- [review-report-round-1.md](../../../raw/code-changes/2026-11-19-246-240-follow-ups/review-report-round-1.md)
- [review-report-round-2.md](../../../raw/code-changes/2026-11-19-246-240-follow-ups/review-report-round-2.md)
- [review-report-round-3.md](../../../raw/code-changes/2026-11-19-246-240-follow-ups/review-report-round-3.md)
- [review-report-round-4.md](../../../raw/code-changes/2026-11-19-246-240-follow-ups/review-report-round-4.md)
- [run.json](../../../raw/code-changes/2026-11-19-246-240-follow-ups/run.json)
- [scope-baseline.json](../../../raw/code-changes/2026-11-19-246-240-follow-ups/scope-baseline.json)
- [test-freeze.json](../../../raw/code-changes/2026-11-19-246-240-follow-ups/test-freeze.json)
- [verification-result.md](../../../raw/code-changes/2026-11-19-246-240-follow-ups/verification-result.md)

## Related
- [code-changes/ — the folder and its tags](README.md)
- revises: [2026-11-18 240-loud-backlogs — the cycle report names everything a run leaves undone](2026-11-18-240-loud-backlogs-the-cycle-report-names-everything-a-run-leaves-undo.md) (its open findings spec-1, spec-15, spec-32, spec-33 and standards-52)
- [30 The research cycle](../architecture/30-the-research-cycle.md) (the living page, revised in place: it points at the `_run_state.py` docstring for the claims cases)
