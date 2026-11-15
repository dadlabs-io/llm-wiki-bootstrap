# Review report, round 3 (focused): 240-report-fallbacks

Fixed point 1bcb08d (`git rev-parse` resolves). The working tree against it, leaving out `.do-code-change/`, is non-empty; no untracked files. This is the run's third round (cap 3). It is focused: the lenses saw the fix round's diff (`git diff a6704c0 HEAD`, 9 files) plus the sibling sites of each round-2 finding. Files round 2 reviewed and the fix left alone are out of the round and nothing new is raised in them. One Standards and one Spec lens ran as `code-reviewer-lens`, unnamed, default tier, spawned with `run_in_background: false`; the harness ran both in the background anyway and I took each report from its hand-back. No file is HIGH, so the Change risk lens was not run. The prescan was clean and the Standards lens was told not to raise review ids, dates or width in `.py` files. Round-2 ids are cited by the order of `review-findings.md` (Standards 1-10, Spec 1-6); by the checkpoints' list, spec-8 is the short-form label nit, spec-9 the `<why>` nit and standards-19 the heading-parse duplication.

## Standards

- [important] PY9 / R15, `tests/skills/wiki-cycle/check.py:2514` and `:2570`: the Notes requirement is unanchored, so the check name overstates what it tests.
  - The check is named "every wiki-ingester worker's brief tells it to name any fallback in its Notes". `FB_NOTES = re.compile(r"\bnotes\b", re.I)` is applied to the whole prompt: `return bool(FB_BRIEF.search(prompt) and FB_NOTES.search(prompt))`. A brief that drops the Notes instruction still passes if "notes" appears elsewhere in it.
  - Fix: require the shape and `Notes` in one line or sentence (a bounded window), or rename the check (the name is pinned by the baselines).
  - Reviewer's note: round 2 asked for "a `Notes` requirement to the same test" and this is that fix as written, so the finding is the fix's weakness, not a missed request. The lens could not tell whether a real worker brief mentions "notes" elsewhere (unverified below). The Spec lens raised the same point as a suggestion; the two labels are kept apart.
- [suggestion] S2, `check.py:2577-2580` (`_fb_lines`) beside `:2542` (`_fb_read`): a second reader of `fallbacks.txt` with the same utf-8 `errors="replace"` decode. Fix: `_fb_lines` returns `_fb_read(run_dir / "fallbacks.txt").splitlines()`, the `is_file` guard living in `_fb_read`.
- [suggestion] G16 / S6, `check.py:2671-2678`: the variant dispatch is a dict of tuples of lambdas with a `*report` splat; the order is set by tuple position and the lambdas only defer calls. Fix: a short `if`/`elif` on `_fb_variant(case)` calling the named helpers in order.
- [nit] C1, `check.py:2620`: `"""Without a Fallbacks section there is nothing to order, so no check is added (as before)."""` refers to earlier code. Fix: drop "(as before)".
- [nit] S1, `check.py:2670`: `report` names a pair of check thunks, not a report. Fix: `report_checks`.
- [nit] C3, `check.py:2508` and `:2563`: the third-field rule for the default model is stated in both the comment and the docstring. Fix: keep the docstring, cut the comment to the regex's shape.
- [nit] C1, `tests/skills/PENDING.md:73`: the row narrates which session broke the honour rule ("made by a session that had read `cases.json` (against the honour rule)…"); the row's columns are the change and why it was not run. Fix: keep run ids and checks not run in the row.

Unverified:
- Whether a real worker brief carries an unrelated word "notes" (which would make the false pass in the first finding happen in practice); it needs the brief text from a saved run.
- The baseline key reorder was checked against the diff hunks only; the suite was not run (a review runs no test).
- "Offline proof 63/63" and the run ids in PENDING.md: the run folders are not in the repository.

Checks made:
- Round-2 Standards 1 (`variant` branching): fixed. The helpers take no `variant`; `_check_fallbacks` (`check.py:2667-2680`) chooses each variant's ordered checks once. Residual style point is the dispatch finding above.
- Round-2 Standards 2 (two Decisions-log forms): fixed. `SKILL.md:110` now reads "into the Decisions log in the general rule's form (above)", which is line 71's `- <now_stamp()> — fallback: <the file's line>`.
- Round-2 Standards 3 (`FB_BRIEF` Notes): fixed as asked, with the anchoring weakness above.
- Round-2 Standards 4 (default model): fixed. `FB_DEFAULT_MODEL = re.compile(r"\bsonnet\b|\bdefault[\s-]+(?:model|sonnet)\b", re.I)` on the third field rejects "the default setting".
- Round-2 Standards 5 (drop literal): fixed inside the kind (`FB_NO_PAIR`, `_fb_drop_no_pair`). Not fixed as the finding asked: the same drop is still written out at `check.py:541`, `:2231` and `:2467` (the last identical to `_fb_drop_no_pair`'s body), so there is now one more spelling of it. Those sites are other kinds' code, which the developer left on purpose; suggestion level, not blocking.
- Round-2 Standards 6 (`_fb_read` duplicates the read closures): not fixed. `_fb_read` (2542) still repeats the closures at about 2234 and 2478, and `_fb_lines` adds a near copy (first finding group above). Suggestion level, not blocking.
- Round-2 Standards 7 and standards-19 (heading parse): partly fixed. The doubled `startswith("## ")` comprehension is now `_fb_headings` (2573), used at 2616 and 2622. The Needs-you pattern `r"^##\s+[^\n]*needs you"` is still at 2316, 2496 and 2549 (`_fb_before_needs`, this kind) beside `_needs_you` (2224); the sites outside the kind were left on purpose. Suggestion level, not blocking.
- Round-2 Standards 8 (usage page states the resumed-run case): fixed in `wiki-seed/wiki-cycle.md:51`; the Spec section raises a wording point about that clause.
- Round-2 Standards 9 (bare date): fixed; `git grep "(2026-11-15)"` finds it only in review reports. Standards 10 (`_fb_section -> str | None`): fixed; `from __future__ import annotations` is at `check.py:43`, and the lens found `requires-python = ">=3.12"`.
- `check.py` parses; every `add(` name in the kind matches a baseline key (the Spec lens counted 8, 4 and 14 per case, equal on both models).
- No new check was dropped: old and new per-variant check lists were compared branch by branch from the diff; the order of the report checks moved after the config checks and the baselines reflect it.

| Rule or section | Verdict | Search |
|---|---|---|
| S1 | found | `report` (nit) |
| S2 | found | `_fb_lines`; the outside-kind copies at 541, 2039, 2231, 2467, 2736 left on purpose |
| S3, S4, S5, S7, S8, S9, S10, S11, S12 | clear | each helper reads its own inputs; the `add, rtext, section` triple is passed once per variant; every `_fb_*` name has a caller (Grep) |
| S6 / F3 / G16 | found | `_fb_variant` branches at 2532 and 2679; the dict dispatch |
| G25 | clear | literals at 2505-2517 read; the dropped name is a constant |
| R1, N7, C5 | clear | `_fb_drop_no_pair` says what it does; no commented-out code |
| R26 | clear | Grep `_fb_` and `FB_` in tests/skills: every new name is called |
| Comments C1-C3, R2 | found | `check.py:2620`, `PENDING.md:73`, 2508 vs 2563; no TODO |
| Names N2-N6, R3 | clear | R3 settled: `SKILL.md:110` and `:71` agree |
| Functions (S13, G34, S14, G19, G28, G29, R4, G31, S15) | clear | `_check_fallbacks` is 14 lines; longest signature 4 parameters; nesting at most two levels |
| Tests (T1, T3, T5, T6, R12-R14, T4) | clear | no skip added; the fallbacks cases are the coverage |
| R15 | found | `FB_NOTES` |
| Refactoring R21-R25 | clear | same checks per variant; the one behaviour change (Notes, model name) is named in the PENDING row |
| Python PY1-PY8, PY10, PY11 | clear | no cast, Any, async, new import |
| PY9 | found | `FB_NOTES` |

Read depth is in the file table. Well built: the variants' checks are chosen once and the helpers take no variant flag, the doubled heading comprehension is gone, and every new helper has a caller and a return annotation.

## Spec

- [suggestion] `tests/skills/wiki-cycle/check.py:2659`: the check name says each worker's brief tells it to name fallbacks "in its Notes", but the test needs only the shape and the word "Notes" somewhere in the prompt (`check.py:2570`).
  - Intent: `plan.md:106`, "every `wiki-ingester` worker's brief tells it to name any fallback in its Notes"; `requirements.md:52` (Decision 5), "the worker's brief says to name any fallback it used in the receipt's Notes column".
  - Code: `FB_NOTES = re.compile(r"\bnotes\b", re.I)` (`check.py:2514`); nothing binds Notes to the sentence. The shipped sentence at `SKILL.md:110` has both in one clause, so a false pass is narrow.
  - Affected: the suite's only automated proof of the worker-brief step. Fix: one line or sentence for both, or rename. A partial close of round 2's Spec 4 on this point; the same defect as the Standards `important`, labelled by this lens as a suggestion.
- [suggestion] `skills/wiki-cycle/wiki-seed/wiki-cycle.md:51` (new this round): "a resumed run where nothing fell back also reads \"not checked\", since resuming does not create the file".
  - Intent: `plan.md:26` puts "a rule-era run resumed after its Step 0 with nothing found since" under the absent-file label, but `SKILL.md:53` has Step 0 create `fallbacks.txt`.
  - Code: a rule-era run keeps its header-only file, and `skills/wiki-report/SKILL.md:271` reads that as `Fallbacks: none`. The clause is true only for a run begun before the rule; as written, "a resumed run" is broader.
  - Affected: a reader interpreting a resumed run's report. Fix: limit the clause to runs begun before the rule, or cut it; reconcile `plan.md:26` with `SKILL.md:53`.
- [nit] `check.py:2512`: the comment lets X, Y and Z be "letters, words or <placeholders>", and `FB_BRIEF` accepts angle brackets; `plan.md:30` says "X, Y and Z plain words (the skill text writes the shape with no angle brackets…)". The plan's rule is written for the note, so applying it to the brief is an inference. Fix: drop the allowance if the rule binds the brief too.
- [suggestion] `tests/skills/PENDING.md:73`: the row says the resume and regression runs "ran on the text before the review rewordings (Step 2's copy rule, Step 9's wording)", but this round also added the `reference.md` Phase 9 `- **Status**: pending` line, which those runs lacked. Round 2's Spec 1 asked the row to state exactly what ran on which text. Fix: name the template line in that parenthetical.

Unverified:
- Whether the worker prompts of run 20261115-163745 carry the Notes instruction beside the shape (needs the saved Agent calls).
- The "63/63" proof, the run ids and "About $48" (the checkpoints record about $30 and about $9; the 163745 cost is not recorded).
- That `Fallback: transcribed (why)` maps to `Step 2 | subtitles | transcription | why` for every fetcher line form: `wiki-update/fetchers.md` was not read this round.

Checks made:
- Round-2 Spec 1 (PENDING row stale) and Spec 2 (checkpoints' reason for the first Step 9 edit): fixed. The row now says 63/63, cites `20261115-163745` for the green rerun and the baselines, states the honour-rule deviation, and no longer says "only by the two resume cases"; `checkpoints.md` carries "Correction (spec-5)" naming `check()`'s common tail. The row's remaining gap is the suggestion above.
- Round-2 Spec 3 (`reference.md` Phase 9 Status line): fixed; `reference.md:65-66` now has `- **Status**: pending`. It cannot disturb the scripts: `wiki-cycle-scope.py` reads `^\*\*Status\*\*:` at line start (lines 540, 557), and the Phase 9 line starts `- `.
- Round-2 Spec 4 (check-name over-claim): partly, see the findings above.
- Round-2 spec-8 (short forms of the absent-file label): fixed. The full label `Fallbacks: not checked (no fallbacks.txt in the run folder)` is at `wiki-cycle.md:51`, `wiki-report.md:22`, `CHANGELOG.md:16` and `skills/wiki-report/SKILL.md:273`; `CHANGELOG.md:17` points to "the not-checked line above". The seed's later short mention is a back-reference after the full label.
- Round-2 spec-9 (`<why>`): fixed. `SKILL.md:110` now writes `Fallback: transcribed (why)` and `Step 2 | subtitles | transcription | why`; the angle placeholders left in line 71 belong to the Decisions-log template, not to the worker note or the file line. The residual is the nit above.
- Round-2 Spec 6 (Notes name) is the first finding. Round-2 Standards 8's design call (one "not checked" label, Mark 2026-11-15) is kept.
- Invariants: `git diff 1bcb08d HEAD -U0 -- skills/wiki-cycle/SKILL.md` shows hunks only at lines 53, 67, 71, 110, 179 and 181, none touching the Step 2 text outside line 110; no hunk in `scripts/`, `framework-docs/` or `agents/wiki-ingester/`; Step 9's order (Status `completed` and Phase 9 `done` before the one commit) matches Mark's "Update before commit".

| Plan step, decision or invariant | Verdict | Search or cite |
|---|---|---|
| Req D1, D2, D3, D4 | clear | `SKILL.md:71`, `reference.md:77`, `wiki-report/SKILL.md:268-273` |
| Req D5 / plan Steps 3 and 6 (worker note, copy) | found | `SKILL.md:110`; `check.py:2568-2570`, 2658-2660 |
| Req D6, Exclusions | clear | no timeout or Glob/Grep rule added |
| Plan Step 0, Step 1 (file, header, keep list, section) | clear | `SKILL.md:53, 67, 181`; `wiki-report/SKILL.md:268-273` |
| Plan Step 2 (`not checked`; resume creates no file) | found | `SKILL.md:67`; `check.py:2583-2587, 2630-2634`; the seed clause |
| Plan Step 4, Step 5 | clear | `wiki-report/SKILL.md:301`; `SKILL.md:71` |
| Plan Step 7 (docs, CHANGELOG, PENDING) | found | `PENDING.md:73` |
| Invariants (stop-and-report, scripts, framework-docs, ingester agent) | clear | the diffs above |
| Check names against baselines | clear | 8, 4 and 14 names per case equal on both models |
| Round-2 Spec 1-6 | found / clear | see Checks made |

Read depth is in the file table. Well built: each variant's checks are one ordered list and the baseline key order follows it; the full absent-file label is used at all five sites; Step 9 sets the scratchpad `completed` before the one commit as Mark ruled.

## Change risk

No high-risk file; the change-risk lens was not run.

| File | Risk | Part | Standards | Spec | Change risk |
|---|---|---|---|---|---|
| `skills/wiki-cycle/SKILL.md` | MEDIUM (behaviour rule the cycle follows) | 1 | in part (60-80, 107-110, changed lines; I read the whole file) | in full | not run |
| `skills/wiki-cycle/reference.md` | LOW | 1 | in part (40-90) | in full | not run |
| `skills/wiki-cycle/wiki-seed/wiki-cycle.md` | LOW | 1 | in part (the changed line) | in part (the changed lines) | not run |
| `skills/wiki-report/wiki-seed/wiki-report.md` | LOW | 1 | in part (the changed line) | in part (the changed lines) | not run |
| `CHANGELOG.md` | LOW | 1 | in part (the changed lines) | in part (the changed lines) | not run |
| `tests/skills/PENDING.md` | LOW | 1 | in part (the row) | in part (the row) | not run |
| `tests/skills/wiki-cycle/check.py` | LOW (test) | 1 | in part (2500-2690; every changed line) | in part (2480-2683) | not run |
| `tests/skills/wiki-cycle/baseline-sonnet.json`, `baseline-opus.json` | LOW | 1 | in part (diff hunks) | in part (835-970 and hunks) | not run |

Every changed line of each moved file was read by both lenses; no changed line is named unread. `skills/wiki-report/SKILL.md` was a sibling-site read only, and `cases.json` and the other round-1 files the fix left alone are out of the round.

## needs-a-human

Empty: no finding touches auth, authz, token or session handling, or a production-data migration, and a spec resolved.

## Summary

- Standards: 7 findings (1 important, 2 suggestion, 4 nit). The worst is the unanchored Notes test under a name that says Notes.
- Spec: 4 findings (3 suggestion, 1 nit). The worst is the same Notes test, plus the seed clause that says a resumed run reads "not checked" where a rule-era resumed run reads "none".
- Change risk: not run.
- Blocking (critical or important): one, the Standards `important` on `check.py:2514`/`:2570`. It is the fix round-2 asked for, applied literally, so it is a judgement for the run's owner whether it blocks. Everything else is a suggestion or a nit.
- Round-2 findings: all but three are confirmed fixed on the Checks made lines; Standards 5, 6 and 7 are fixed only inside the fallbacks kind, with copies left in other kinds' code (suggestion level).
- Where the axes agree: the Notes test.
- Not confirmed: the run results and the 63/63 proof (not in the repository), and what real worker briefs contain.

VERDICT: Standards FINDINGS · Spec FINDINGS · Change risk NOT RUN · needs-a-human 0
