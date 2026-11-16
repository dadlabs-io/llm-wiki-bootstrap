# Verification result — 240-report-fallbacks (task #240, lesson #12)

Verified 2026-11-15 by the architect, against fixed point 1bcb08d, HEAD 76d987f, branch main, tree clean (`git status --short` printed nothing). No paid model run was started. Every command below ran fresh, alone, in this session.

## Layers

tests: not checked — the proving commands for the skill text are paid model runs; none was started. Free evidence only (below).
diff-contains-fix: PASS — `git diff 1bcb08d --stat` lists every file the plan names (skills/wiki-cycle/SKILL.md, reference.md, wiki-seed/wiki-cycle.md, skills/wiki-report/SKILL.md, wiki-seed/wiki-report.md, CHANGELOG.md, tests/skills/PENDING.md, tests/skills/wiki-cycle/{cases.json,check.py,baseline-opus.json,baseline-sonnet.json}); `git status --short` empty, so none is untracked or uncommitted; INSTALL-INVENTORY.md is absent from the diff, as plan Scope allows ("only if its rows name run-folder files").
findings-addressed: FAIL — `review-ledger.py query --diff-base 1bcb08d --cap 3` exit 3: "review-ledger: exit 3 - halt: the retry-ceiling checkpoint"; 6 round-4 items open (spec-14, spec-15, spec-16, standards-30, standards-31, standards-32), 7 earlier verdicts STALE (spec-1, spec-4, standards-1, -13, -2, -23, -3). Requester's recorded checkpoint answer is beside it, see "How I read the ledger".
frozen-tests: not checked — `check-freeze.py .do-code-change/240-report-fallbacks/test-freeze.json` exit 2, "check-freeze: exit 2 - not checked: the record is missing, unreadable or holds nothing live". The run never froze a test (its tests are suite cases proven red then green, not Python tests).
coverage: PASS — every done criterion maps to an `existing` check (map below); the criteria no test reaches are marked manual in plan.md Testing Decisions, and each manual check was run (below).
bar-unmoved: PASS — floor-guard.py exit 0, "floor-guard: exit 0 - clean: no move lowers the bar" ("floor-guard: clean (480 added, 8 removed lines checked)").
in-scope: PASS — scope-guard.py check exit 0, "scope-guard: exit 0 - PASS: every touched file is inside the declared scope" (11 touched files, all inside `skills/wiki-cycle/**`, `skills/wiki-report/**`, `tests/skills/wiki-cycle/**`, `tests/skills/PENDING.md`, `CHANGELOG.md`).
tests-bite: not checked — `prove_tests_bite.py --check --base 1bcb08d` exit 2, "tests-bite layer: COULD-NOT-RUN against 1bcb08d (0 changed source file(s)); report .artifacts/python-mutation.json" and "no mutation report: run the pass on the change (or record each trivial-stakes file with --exempt)". The change has no changed `src/` file: the only Python is the suite's own `check.py`. plan.md expected this ("come back as named FAILs or not checked, as in lesson #11"; red then green is the bite evidence).

## tests — what ran, what it shows, what it does not

Free runs, fresh:
- `prove_fallbacks.py` (scratchpad; throwaway, never committed, per plan.md Testing Decisions), full, with setup: "74 passed, 0 failed" (setup and prompt smoke for all three cases, ideal run folders pass 8/5/15 checks, the brief and default-model tests, 17 planted mistakes each failing exactly its own check).
- The same with `--skip-setup`: "56 passed, 0 failed", the figure PENDING.md row 28 and checkpoints.md give.
- `rescore_briefs.py`, the final `_fb_brief_ok` over the saved worker briefs of run 20261115-163745: "opus 1 [True]", "sonnet 1 [True]".
- Saved result `tests/skills/.results/wiki-cycle/20261115-163745/report.md` (read, not re-run): the three new cases PASS on Sonnet and Opus (6/6), "0 regressions, 0 newly passing" against baseline, $9.93. `git diff 42a1904 HEAD --stat -- skills` shows only `skills/wiki-cycle/wiki-seed/wiki-cycle.md` moved since fix round 2 (a usage page the run does not read), so SKILL.md, reference.md and wiki-report/SKILL.md are the text that run used.

Not covered by any run on the final text: `tests/skills/wiki-cycle/check.py` changed after that run (fix round 3, and the manual fix after the cap: `FB_BRIEF` accepts placeholders). The final checker was proven only offline (74/74) and by the re-score of one saved brief per model; PENDING.md row 28 says the same ("no model run used the final `check.py`"). The regression four (`resume`, `models-unreadable-setting-file`, `earlier-complete-and-interrupted-runs-not-named`, `empty-queue-clean-notebook-...`; Sonnet, 20261115-150229, 4/4) and `resume` on Opus ran on the text before fix rounds 1 and 2 (the Step 2 copy rule, Step 9 wording, scratchpad Phase 9 Status line); PENDING.md says so too.

The run that would settle the layer (the requester decides; about $10 by the last run's own cost): `uv run python tests/skills/run_skill_test.py wiki-cycle --cases empty-queue-run-writes-header-only-fallbacks-file-and-report-reads-fallbacks-none-before-needs-you,resumed-run-without-the-file-reads-not-checked-never-none-and-creates-no-file,unreadable-ingester-config-fallback-in-file-decisions-log-report-and-worker-briefs --models sonnet,opus`, and for the regression four on the final text, the same command with `--models sonnet` and those case ids.

## How I read the ledger (findings-addressed)

The ledger still shows round 4's verdicts unrecorded, because the manual fix after the cap was made without a `verdict` call (checkpoints.md, "Review round 4 and the retry-ceiling exhaustion"; Mark answered "Continue" in Discord, read as option A, continue manually). That answer is the Retry-ceiling checkpoint's outcome. It is not a ledger closure and not an approval of a named exception, so the layer is FAIL by its script's exit 3, and the gate stops for the requester rather than passing it. My independent re-read of each open item's site (HEAD):
- standards-30 (`FB_BRIEF` refused placeholders): changed as ruled. `check.py:2514` is now `...why\b[ \t]*[*`_]*[<\w]`; offline proof plants "angle-bracket placeholders, with Notes" accepted and the replay-4 plants 1-4 as expected. Addressed.
- standards-32, spec-14, spec-15 (PENDING row 28 stale, honour-rule deviation dropped): the row now gives the 41/63/56 proof history, the re-score, "no model run used the final `check.py`", and "that first reorder was made by the orchestrator, which had read `cases.json`, against the honour rule, a deviation accepted in review round 2". Addressed.
- standards-31 (`_fb_brief_ok` has no committed test): not changed in the repo. Ruled an accepted trade-off (plan.md:47: the proof is a throwaway script); the plants were added to the throwaway proof, which I ran. Acknowledged, not addressed by the layer's definition.
- spec-16 (Step 9's clause "so the commit holds the final record" is the first edit's wording): `skills/wiki-cycle/SKILL.md:181` unchanged. Ruled as in round 2 (spec-1 settled) and recorded in the PENDING row. Acknowledged, not addressed.
- The 7 STALE verdicts are round-1 to round-3 items whose files moved after their verdicts; round 4's reviewer confirmed all 11 round-3 findings and round-1 standards-1, -2, -3 fixed in form.
Closing standards-31 and spec-16 in the ledger as `wontfix` needs fp-check's verdict line (`review-ledger.py verdict ... wontfix --fp-verdict`), which the run does not have; that is the orchestrator's and requester's route, not mine.

## Frozen tests

Exit 2, not checked. Nothing was frozen; `.do-code-change/240-report-fallbacks/` has no `test-freeze.json`. The tests this change adds are cases in `tests/skills/wiki-cycle/cases.json` and checks in `check.py`, proven by red then green on the old copy (checkpoints.md: run 20261115-140849-red-green-1bcb08d, 5 of 6 red then green, the sixth reasoned and reordered), not by frozen Python tests.

## Coverage map

| Done criterion (plan step) | Test | Status |
|---|---|---|
| 1 Expected: clean empty-queue run leaves `fallbacks.txt` with only its `#` header | clean case: "fallbacks.txt exists in the run folder", "is not zero bytes", "first line is the # header", "holds only its header" (`check.py:2597-2619`) | existing |
| 1 Expected: report has `## Fallbacks` reading `Fallbacks: none`, before Needs you | "the report has a Fallbacks section", "reads 'Fallbacks: none'", "comes before Needs you" (`check.py:2622-2634`, `2690-2691`) | existing |
| 1 Expected: file committed with the run (Step 9 keeps it) | "fallbacks.txt is committed with the run" (`check.py:2609-2611`) | existing |
| 1 Failures: Step 9 deletes the file | same committed-and-present checks | existing (no offline plant for the committed check; bitten by red-then-green only) |
| 1 Failures: report omits the section | "has a Fallbacks section" and "reads 'Fallbacks: none'" | existing |
| 1 Invariant: Needs you is the last section | the suite's common "the cycle report's last section is Needs you" check, run in every case | existing |
| 2 Expected: resumed run without the file reads `Fallbacks: not checked (no fallbacks.txt in the run folder)` | `_fb_label_not_checked` (`check.py:2637-2641`) | existing |
| 2 Expected / Failures: the resume does not create the file | "the resume did not create fallbacks.txt" (`check.py:2590-2594`) | existing |
| 2 Failures: `Fallbacks: none` for an absent file | `_fb_label_not_checked` fails when `FB_NONE` matches the report | existing |
| 3 Expected: four-field line naming the step, the ingester setting file and a default model | "names the ingester setting file in four non-empty ' \| ' fields", "names a default model" (`check.py:2650-2653`) | existing |
| 3 Expected: Decisions log carries a `fallback` line | `check.py:2656-2658` | existing |
| 3 Expected: report lists it `- S: expected E; used U; why W` before Needs you | `check.py:2659-2661`, `2691` | existing |
| 3 Expected: every worker brief tells it to name a fallback in its Notes | `_fb_brief_ok` via `check.py:2663-2667` | existing |
| 3 Failures: line with fewer than four fields; line holding `>` | `_fb_four_fields`; "no fallback line holds '>'" (`check.py:2654`) | existing |
| 3 Failures: fallback in the report only, or in the file only | file-line checks and section-line check, each separate | existing |
| 3 Invariant: `models-unreadable-setting-file`'s `report_names` still matches | the existing case, run on Sonnet at 20261115-150229 (text before fix rounds 1-2) | existing (stale run, see tests) |
| Invariant: earlier-run lines in Needs you unchanged | `earlier-complete-and-interrupted-runs-not-named`, same stale run | existing (stale run) |
| Invariant: stop-and-report sentence, `skills/wiki-update/`, `agents/wiki-ingester/`, `framework-docs/` untouched | `git diff 1bcb08d HEAD --stat -- framework-docs agents scripts skills/wiki-update INSTALL-INVENTORY.md` printed nothing; the Step 2 exit-75 sentence is not in the SKILL.md diff hunks | manual: read |
| 4 `--brief` line only when N > 0 | none (no cycle case reaches `--brief`) | manual (plan: step 4): `skills/wiki-report/SKILL.md:301` reads "After Numbers, and only when `fallbacks.txt` holds N > 0 fallback lines, add one line: `Fallbacks: N — see the full report`"; `## Fallbacks` sits after Recommendations and before Needs you, which stays last; the three states are at lines 268-273 |
| 5 keyword departure is listed, a keyword-mode machine is not | none (the case was dropped by Mark) | manual (plan: step 5): the rule in `SKILL.md` (diff hunk at Step 0/"A step that leaves its expected tool path") names a keyword search on a full machine as "a departure from the stop-and-report rule, never an allowed fallback: its why begins `departure from the stop-and-report rule:`" and excludes "a machine set to `search_mode: keyword` searching by keyword" |
| 6 workers name fallbacks, orchestrator copies them | brief sentence: step 3's case (above); the copy: none | manual (plan: step 6): `SKILL.md:110`, one copy rule incl. `Fallback: transcribed (why)` -> `Step 2 \| subtitles \| transcription \| why`; `agents/wiki-ingester/` absent from the diff stat |
| 7 docs say what changed | none | manual (plan: step 7): CHANGELOG 2026-11-15 entry, both usage pages and the PENDING row read in the diff; the standalone-report omission is in `wiki-report/SKILL.md` ("Standalone (no run folder): omit this section") |

No policy shadow: no helper is tested without its wiring. The two rows marked stale rest on runs that predate fix rounds 1-2.

## Routes

- findings-addressed (FAIL): the retry cap is spent, so there is no round to go back to; the orchestrator records the round-4 verdicts (`addressed` for standards-30, -32, spec-14, -15; standards-31 and spec-16 are accepted trade-offs that `wontfix` only with fp-check's line), or the requester rules on them at the Finishing decision.
- tests (not checked): the requester decides whether to pay for the named run, or to accept the offline proof and the saved run 20261115-163745 as the evidence and record that.
- frozen-tests (not checked), tests-bite (not checked): per Pre-finish, `not checked` fails the layer; the plan expected both, and neither has a thing to check here (no frozen Python test, no `src/` file). The requester decides whether to record them as accepted, as lesson #11's run did.

VERDICT: FAIL — tests, findings-addressed, frozen-tests, tests-bite
