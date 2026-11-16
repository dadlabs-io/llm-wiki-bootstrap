# 2026-11-15 240-report-fallbacks — the cycle's report names every fallback from the expected tool path

## TL;DR
A `/wiki-cycle` run now writes every step that left its expected tool path (a different agent type, a different fetcher, a re-run, a default where a setting file could not be read) to `fallbacks.txt` in the run folder and to the scratchpad's Decisions log, and `/wiki-report` shows them in a `## Fallbacks` section just before ⚠️ Needs you: one line each, `Fallbacks: none` when there were none, `Fallbacks: not checked (no fallbacks.txt in the run folder)` when the file is absent. This closes pre-mortem lesson #12 of task #240 (a shell timeout worked around by another tool left no trace in the report). It ended as `keep` on `main` (the branch the run started on), no push: four review rounds, the retry ceiling reached after round 4 and Mark's "Continue", then verify with four named FAILs that Mark accepted (tests, findings-addressed, frozen-tests, tests-bite), then installed by the SOP.

## What changed
- A cycle's report has a Fallbacks section that reads `Fallbacks: none` when nothing left its path
- A run folder with no `fallbacks.txt` reads `Fallbacks: not checked`, never `none`
- A fallback the orchestrator made is recorded and listed
- `--brief` carries one line when fallbacks were recorded
- A keyword search on a machine set to full is listed as a departure, never as an allowed fallback, and a machine set to keyword is not listed
- Ingest workers name their fallbacks and the orchestrator copies them into the file
- Docs

Three `fallbacks` cases were added to the wiki-cycle suite (an empty-queue clean run, a resumed run without the file, an unreadable ingester setting file); `skills/wiki-cycle/SKILL.md`, `reference.md`, `skills/wiki-report/SKILL.md`, both usage pages, `CHANGELOG.md` and `tests/skills/PENDING.md` changed. No script, agent definition or framework-contract doc changed.

New tags: `wiki-report` (skills), added to the folder README's table by this change. `code-change`, the group `skills` and `wiki-cycle` (skills) already existed. This change revises no earlier record.

## Why: decisions and exclusions
Decisions:

1. **Matters most. A keyword search on a machine that is set to full.** The request lists "a keyword search instead of the full search" as a fallback to report; the recorded rule (`wiki-update/SKILL.md:41`, decision 2026-09-13) says there is no such fallback: stop and report, "never a lower-quality search". Recommended: the report lists it if it happened anyway, worded as a departure from the rule (not an allowed fallback), and the stop-and-report rule is not softened; a keyword-mode machine is not listed (Fact). Alternative: leave keyword search out of the examples, so the rule never names a thing the cycle may not do. **Decided (Mark, 2026-11-15): the recommendation.**
2. **What ships to carry a fallback to the report.** Recommended: a plain-text file in the run folder (like `unfinished-runs.txt`) that the orchestrator writes as fallbacks happen, with one line in the scratchpad, read by `/wiki-report`; no contract change. Alternative: a `fallbacks[]` field in the common step skeleton, filled by every step: reaches each step's own file, but edits a framework-contract doc (version bump), every step's writer and `/wiki-report`. **Decided (Mark, 2026-11-15): the recommendation.**
3. **Where the report shows it, and what it says when there is none.** Recommended: its own short section before ⚠️ Needs you (a fallback is something that happened, not something waiting on the user), one line each (step, expected path, what was used, why), and when there are none one line "Fallbacks: none", so silence cannot be read as unchecked. Alternative: lines inside ⚠️ Needs you, and nothing at all when none (what lesson #10 does for unfinished runs). **Decided (Mark, 2026-11-15): the recommendation.**
4. **One general rule, or a line at each place a fallback is written.** Recommended: one rule in `/wiki-cycle` `SKILL.md` (a short paragraph beside "Every step writes…") that covers every step; the existing specific lines (Step 2's `general-purpose`, 429 transcription, keyword machine, exit 75) stay as written. Alternative: add "and report it" at each of those sites (no general rule, but each new fallback needs its own line). **Decided (Mark, 2026-11-15): the recommendation.**
5. **Fallbacks a worker meets.** The cycle's fetcher and transcription fallbacks happen inside `wiki-ingester` workers, whose receipt the orchestrator reads. Recommended: the worker's brief says to name any fallback it used in the receipt's Notes column, and the orchestrator copies each into the report; no change to the receipt's columns or to `AGENT.md`. Alternative: the report names only fallbacks the orchestrator itself made (the agent type, a retried script), and a worker's fallback shows only in its own notes. **Decided (Mark, 2026-11-15): the recommendation.**
6. **The timeout half of #12.** Recommended: excluded. The 120 s was a shell tool's limit, not llm-wiki code; under the new rule a timeout worked around is a fallback that gets reported, which is the part of the lesson Mark asked for; and a rule "use Glob/Grep, not `ls`, on the notebook" would be an obvious rule (bloat, Mark 2026-10-14). Alternative: add that rule, or a timeout on the cycle's own directory scans, as part of this change. **Decided (Mark, 2026-11-15): the recommendation.**

Exclusions:

- Not the timeout half of #12 as a code or skill rule: no new or longer timeout, no instruction to use Glob/Grep instead of `ls` (Decision 6, decided).
- Not the concurrency half of #12: the spawn rule (`wiki-ingester` workers, unnamed, background, up to 4) is already fixed (page `...failures-we-hit...md:68`); the pre-mortem's second sentence ("an instruction that holds only in some execution contexts says which") is not added here.
- No change to which fallbacks are allowed: no new fallback is introduced, none removed. In particular the 2026-09-13 rule stays: on a full machine a failed full search is stop-and-report, never a keyword downgrade.
- Not lesson #9 (silent backlogs) and nothing from #10 or #11.
- No change to the framework-contract step JSON unless Decision 2 says so.
- No new fallback output added inside the scripts (`wiki-feeds.py`, `wiki-fetch-*.py`, `wiki-qmd-query.py`): a branch a script takes without printing is not reported by this change.
- No change to `/wiki-update`, `/wiki-discover`, `/wiki-triage` or the `wiki-ingester` agent beyond what Decision 5 asks for the worker's receipt.
- No enforcement script that checks a run for unreported fallbacks: the rule is prose in the skill and a suite case, as for the earlier two lessons.

Rulings made at the plan confirmation (2026-11-15, Mark, one at a time): the `keyword-machine` case dropped (the keyword-machine exclusion is read by hand from the rule's wording); the clean case runs on an empty queue with nothing fetched; one `not checked` label for every absent-file case; `--brief` shows `Fallbacks: N — see the full report` only when N is above zero. Accepted trade-off: the worker-note copy and the departure line stay manual. Branch: stay on main.

## What the review found
Four review rounds (15, 16, 11, 13 findings) with three fix rounds and a manual fix after the cap; the retry ceiling was reached after round 4 and Mark answered "Continue" (continue manually). Verdicts below are `review-ledger.json`'s own: no finding was closed `wontfix` (no fp-check ran); `open` means left, with the reason in `checkpoints.md` ("Review round 4 and the retry-ceiling exhaustion" and "Verify").

- standards-1 — the docs say different things about when `not checked` appears — addressed
- standards-2 — two note forms exist for a worker's fallback — addressed
- standards-3 — `FB_BRIEF` passes any brief where "fallback" and "notes" sit within 250 characters — addressed
- standards-4 — `_check_fallbacks` repeats code already in the file — addressed
- standards-5 — `_check_fallbacks` is about 70 lines mixing the file, report and unreadable-config checks — addressed
- standards-6 — the three Fallbacks states and the definition are restated in three places — addressed
- standards-7 — the worker-note copy rule omits the Decisions-log line — addressed
- standards-8 — a ticket reference in a `check.py` header comment — addressed
- standards-9 — a comment names a "suite idiom" that does not exist — addressed
- standards-10 — the `fallbacks` dispatch follows the `elif` chain and `_prepare_fallbacks` is a one-branch forwarder — addressed
- standards-11 — variant name literals repeat although `FB_VARIANTS` exists — addressed
- standards-12 — dated incident history on a usage page — addressed
- spec-1 — the Step 9 reorder broke the plan's honour rule and its stated reason does not hold — addressed
- spec-2 — the docs narrow the absent-file label to "a run begun before the rule" — addressed
- spec-3 — the brief check is a two-word proximity match, not the instruction's own words — addressed
- standards-13 — the `variant` mode argument is branched in several places — addressed
- standards-14 — SKILL.md carries two forms of the Decisions-log line — addressed
- standards-15 — `FB_BRIEF` no longer requires Notes while the check name says it does — addressed
- standards-16 — "used the default setting" with no model named still passes — addressed
- standards-17 — the quick-pair drop filter is still repeated — addressed
- standards-18 — `_fb_read` duplicates two existing readers — addressed
- standards-19 — the Needs-you heading parse repeats — addressed
- standards-20 — a resumed run where nothing fell back reports `not checked` although it was checked — addressed
- standards-21 — a bare date remains on a usage page — addressed
- standards-22 — `_fb_section` has no return annotation — addressed
- spec-4 — the PENDING row is stale against the fix round and omits the process deviation — addressed
- spec-5 — the record's reason for the first Step 9 edit is wrong (the check is in the common tail) — addressed
- spec-6 — Step 9 names a Phase 9 Status field the template lacks — addressed
- spec-7 — the brief check name over-claims (Notes) — addressed
- spec-8 — short forms of the absent-file label across docs — addressed
- spec-9 — angle-bracket placeholders in the skill text against the plan's no-`>` rule — addressed
- standards-23 — the Notes word is searched across the whole brief — addressed
- standards-24 — `_fb_lines` is a second reader of `fallbacks.txt` — addressed
- standards-25 — the variant dispatch is a dict of lambdas with a splat — addressed
- standards-26 — a docstring refers to earlier code ("as before") — addressed
- standards-27 — `report` names a pair of check thunks — addressed
- standards-28 — the default-model rule is stated in a comment and a docstring — addressed
- standards-29 — the PENDING row narrates which session broke the honour rule — addressed
- spec-10 — the check name says "in its Notes" but the test needs only the word somewhere — addressed
- spec-11 — the usage page's resumed-run clause against plan.md:26 — addressed
- spec-12 — the comment lets placeholders through, an inference from the plan's rule — addressed
- spec-13 — the PENDING row omits the `reference.md` Phase 9 line the earlier runs lacked — addressed
- standards-30 — `FB_BRIEF` rejects a correct brief that writes `<placeholders>` — addressed
- standards-31 — `_fb_brief_ok` has no committed test — open (accepted trade-off, plan.md:47: the proof is a throwaway script, never committed; planted briefs were added to it)
- standards-32 — the PENDING row's verification record is stale — addressed
- standards-33 — a natural two-sentence brief fails the check — open (the docstring's same-sentence bound is a design call)
- standards-34 — `why` accepts a backtick, and a `;` lets a wrong brief pass — open (the `;` pass accepted; the backtick fixed by the manual fix, ledger not re-set)
- standards-35 — the model-name shape is stated twice — open (nit)
- standards-36 — `else:` silently covers `FB_BROKEN` — open (nit)
- spec-14 — the PENDING row's "final text" claim is stale — addressed
- spec-15 — the honour-rule deviation is no longer recorded in the PENDING row — addressed
- spec-16 — Step 9's clause carries the first edit's words, so the honour rule holds in form, not in substance — open (ruled as spec-1 was: settled in round 2; recorded in the PENDING row)
- spec-17 — a pre-rule run resumed and then given a fallback never says the earlier steps were not checked — open (suggestion; the not-checked label covers a run with no file)
- spec-18 — `FB_NOTES` matches "Note:" and passes without asking for the Notes column — open (nit)
- spec-19 — plan.md:26 is stale against SKILL.md:53 (not shipped) — open (nit, a pipeline note)

## What was verified
Verify (`verification-result.md`, run 2026-11-15 by the architect against fixed point 1bcb08d, no paid model run started) ended `VERDICT: FAIL — tests, findings-addressed, frozen-tests, tests-bite`. Mark accepted all four at the Finishing decision ("A", Discord); they are named FAILs, not passes. Per-layer lines:

- tests: not checked — the proving commands for the skill text are paid model runs; none was started. Free evidence only (below).
- diff-contains-fix: PASS — `git diff 1bcb08d --stat` lists every file the plan names (skills/wiki-cycle/SKILL.md, reference.md, wiki-seed/wiki-cycle.md, skills/wiki-report/SKILL.md, wiki-seed/wiki-report.md, CHANGELOG.md, tests/skills/PENDING.md, tests/skills/wiki-cycle/{cases.json,check.py,baseline-opus.json,baseline-sonnet.json}); `git status --short` empty, so none is untracked or uncommitted; INSTALL-INVENTORY.md is absent from the diff, as plan Scope allows ("only if its rows name run-folder files").
- findings-addressed: FAIL — `review-ledger.py query --diff-base 1bcb08d --cap 3` exit 3: "review-ledger: exit 3 - halt: the retry-ceiling checkpoint"; 6 round-4 items open (spec-14, spec-15, spec-16, standards-30, standards-31, standards-32), 7 earlier verdicts STALE (spec-1, spec-4, standards-1, -13, -2, -23, -3). Requester's recorded checkpoint answer is beside it. (After verify the orchestrator set standards-30, -32, spec-14 and spec-15 addressed on a re-read of each site; standards-31 and spec-16 stay open by Mark's rulings; the query still exits 3 on the cap itself.)
- frozen-tests: not checked — `check-freeze.py .do-code-change/240-report-fallbacks/test-freeze.json` exit 2, "check-freeze: exit 2 - not checked: the record is missing, unreadable or holds nothing live". The run never froze a test (its tests are suite cases proven red then green, not Python tests).
- coverage: PASS — every done criterion maps to an `existing` check (map below); the criteria no test reaches are marked manual in plan.md Testing Decisions, and each manual check was run (below).
- bar-unmoved: PASS — floor-guard.py exit 0, "floor-guard: exit 0 - clean: no move lowers the bar" ("floor-guard: clean (480 added, 8 removed lines checked)").
- in-scope: PASS — scope-guard.py check exit 0, "scope-guard: exit 0 - PASS: every touched file is inside the declared scope" (11 touched files, all inside `skills/wiki-cycle/**`, `skills/wiki-report/**`, `tests/skills/wiki-cycle/**`, `tests/skills/PENDING.md`, `CHANGELOG.md`).
- tests-bite: not checked — `prove_tests_bite.py --check --base 1bcb08d` exit 2, "tests-bite layer: COULD-NOT-RUN against 1bcb08d (0 changed source file(s)); report .artifacts/python-mutation.json" and "no mutation report: run the pass on the change (or record each trivial-stakes file with --exempt)". The change has no changed `src/` file: the only Python is the suite's own `check.py`.

Free evidence behind the tests layer: the throwaway offline proof, 74 passed with setup and 56 passed without (the three cases' setup and prompt, ideal run folders, 17 planted mistakes each failing exactly its own check); the final brief check re-scored over the saved worker briefs of run 20261115-163745 (Sonnet [True], Opus [True]); that run, the three new cases PASS on Sonnet and Opus (6/6, $9.93), on the final skill text. Earlier: run 20261115-140849 red then green, 5 of 6 (the sixth, the resumed case on Opus, failed only on "nothing left uncommitted in the notebook", fixed by setting the scratchpad `completed` before the commit and passing in run 20261115-145233); regression four on Sonnet 4/4 (20261115-150229). Not covered by any run: `check.py` changed after run 163745 (fix round 3 and the manual fix after the cap), so the final checker was proven offline only; the PENDING row says so. Not provable by a test, read by hand (the plan's `manual:` lines): the `--brief` line, the keyword-departure sentence and the keyword-machine exclusion, the worker-note copy, the docs. The cost of the model runs for this change was about $30 of tests; the run's estimated total was $38.19 of $120.00.

## Working files
Unchanged copies in the notebook's raw folder; the same files are archived in the code repository at `.do-code-change/archive/2026-11-15-240-report-fallbacks/`.

- [budget.json](../../../raw/code-changes/2026-11-15-240-report-fallbacks/budget.json)
- [checkpoints.md](../../../raw/code-changes/2026-11-15-240-report-fallbacks/checkpoints.md)
- [plan-red-team.md](../../../raw/code-changes/2026-11-15-240-report-fallbacks/plan-red-team.md)
- [plan.md](../../../raw/code-changes/2026-11-15-240-report-fallbacks/plan.md)
- [readonly-red-team.json](../../../raw/code-changes/2026-11-15-240-report-fallbacks/readonly-red-team.json)
- [readonly-review.json](../../../raw/code-changes/2026-11-15-240-report-fallbacks/readonly-review.json)
- [requirements.md](../../../raw/code-changes/2026-11-15-240-report-fallbacks/requirements.md)
- [review-findings.md](../../../raw/code-changes/2026-11-15-240-report-fallbacks/review-findings.md)
- [review-ledger.json](../../../raw/code-changes/2026-11-15-240-report-fallbacks/review-ledger.json)
- [review-report-round-1.md](../../../raw/code-changes/2026-11-15-240-report-fallbacks/review-report-round-1.md)
- [review-report-round-2.md](../../../raw/code-changes/2026-11-15-240-report-fallbacks/review-report-round-2.md)
- [review-report-round-3.md](../../../raw/code-changes/2026-11-15-240-report-fallbacks/review-report-round-3.md)
- [review-report-round-4.md](../../../raw/code-changes/2026-11-15-240-report-fallbacks/review-report-round-4.md)
- [run.json](../../../raw/code-changes/2026-11-15-240-report-fallbacks/run.json)
- [scope-baseline.json](../../../raw/code-changes/2026-11-15-240-report-fallbacks/scope-baseline.json)
- [verification-result.md](../../../raw/code-changes/2026-11-15-240-report-fallbacks/verification-result.md)

## Related
- [code-changes/ — the folder and its tags](README.md)
- [2026-11-15 240-backlink-block-check — the lint checks every backlink block against the real links](2026-11-15-240-backlink-block-check-the-lint-checks-every-backlink-block-against.md) (the previous change on task #240)
- [Research-cycle failures we hit, 2026-04 to 10](../troubleshooting/research-cycle-failures-we-hit-2026-04-to-10.md) (failure #12, the lesson this change builds in)
- [The research cycle](../architecture/30-the-research-cycle.md), [Quality and promotion](../architecture/50-quality-and-promotion.md) and [Testing the skills](../architecture/95-testing-the-skills.md) (the living design pages this change touches)
