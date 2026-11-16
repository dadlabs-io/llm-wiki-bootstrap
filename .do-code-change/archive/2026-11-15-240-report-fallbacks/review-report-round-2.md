# Review report, round 2 (focused): 240-report-fallbacks

Fixed point 1bcb08d (resolves; merge-base is the same commit). The working tree against it, leaving out `.do-code-change/`, is non-empty (11 files, no untracked files). This is a focused round: the lenses saw the fix round's diff (`git diff 5457328 HEAD`, 6 files) plus the sibling sites of each round-1 finding. `tests/skills/PENDING.md`, `skills/wiki-report/SKILL.md` and `reference.md` were read as sibling sites only. `cases.json` and the other round-1 files the fix left alone are out of the round; nothing new is raised in them. One Standards and one Spec lens ran, as `code-reviewer-lens`, unnamed, on the default tier, spawned with `run_in_background: false`; the harness ran them in the background anyway and both reports came back on their completion notifications. No file is HIGH, so the Change risk lens was not run. The prescan was clean, and the lenses were told not to raise review ids, dates or width in `.py` files.

## Standards

- [important] S6 / F3 / S4, `tests/skills/wiki-cycle/check.py:2633-2639`: the `variant` mode argument is still branched in several places, so a new variant needs an edit in each.
  - Sites: `if variant == FB_CLEAN:` (2633), `if variant == FB_BROKEN:` (2639), `if variant == FB_RESUMED:` (2568, 2598), `if variant == FB_CLEAN:` (2581, 2596), and the dispatch `if _fb_variant(case) == FB_RESUMED:` (2529).
  - The `(variant, add, ctx, run_dir)` group repeats across four functions.
  - Fix: give each variant its own check list, chosen once in `_check_fallbacks`, so the helpers take no `variant`.
  - Round 1's standards-5 asked for "one function per variant, or a helper for the file checks"; the split chosen leaves the branching in place.
- [important] R3 (doc contradiction), `skills/wiki-cycle/SKILL.md:110` against `:71`: line 110 says the Decisions log gets the line "as `Step 2 | X | Y | Z`", while line 71 says "Add the same line to the scratchpad's Decisions log: `- <now_stamp()> — fallback: <the file's line>`".
  - The check at check.py:2618 needs the word "fallback" in the log, which only line 71's form guarantees.
  - Fix: have line 110 point to line 71's form for the log.
- [important] R15 / PY9, `check.py:2512` (`FB_BRIEF`), comment at `:2511`, name at `:2627-2628`: the old regex required `\bnotes?\b`, the new one does not (the comment says "Notes may or may not be mentioned next to it"), and the check name still reads "tells it to name any fallback in its Notes".
  - The loosening is not stated anywhere (the CHANGELOG is silent).
  - Fix: add a `Notes` requirement to the same test. The name stays, because `baseline-sonnet.json:905` pins it.
  - The Spec lens raised the same point.
- [suggestion] PY9, `check.py:2508` (`FB_DEFAULT_MODEL = re.compile(r"\bdefault\b|\bsonnet\b", re.I)`), name at `:2613-2614`: the third-field restriction is fixed, but "used the default setting" with no model named still passes. Fix: match a model name, for example `default (model|sonnet|opus|haiku)`.
- [suggestion] S2 / G25, `check.py:2467` and `:2634`: both hold `res[:] = [x for x in res if x["name"] != "quick steps all wrote their pair"]`, and the drop sets at `:541` and `:2231` repeat the same literal. Round 1's (d) is not fixed. Fix: a shared `_drop_quick_pair(res)` helper and one constant for the name.
- [suggestion] S2, `check.py:2539-2540`: `_fb_read` has the same body as the `read` closure at `:2234-2235` and the one at `:2478-2480`. Fix: use the module helper in both.
- [suggestion] S2, heading parses: the Needs-you pattern `r"^##\s+[^\n]*needs you"` appears at `:2316`, `:2496` and `:2546`, beside `_needs_you` at `:2224`, and `[l for l in rtext.splitlines() if l.startswith("## ")]` appears twice in one function (`:2593`, `:2603`). Fix: one heading helper.
- [suggestion] Accuracy, `skills/wiki-cycle/SKILL.md:67` with `skills/wiki-report/SKILL.md:273`: a resumed run where nothing fell back reports `not checked` although it was checked. `cases.json:67` pins this, and plan confirmation choice 3 (Mark, 2026-11-15) chose one "not checked" label, so it is a design call for Mark. Fix: state the case in the usage page.
- [nit] C1, `skills/wiki-cycle/wiki-seed/wiki-cycle.md:51`: the bare "(2026-11-15)" remains on a usage page, so round 1's (k) is fixed only in part. Fix: drop the date, since the CHANGELOG holds it.
- [nit] PY3, `check.py:2533`: `def _fb_section(rtext: str):` has no return annotation for `str | None`, unlike `_fb_before_needs`. Fix: `-> str | None`.

Unverified:
- `baseline-sonnet.json:910` sets `"run: read reference.md before writing the scratchpad": true`. Nothing in the diff shows a Sonnet run producing it. The same key sits in the same case in `baseline-opus.json`; the Opus and Sonnet key sets for the three new cases are equal once it is added (I compared them).
- The lens could not compare the deleted old `_check_fallbacks` body with the four new functions from the diff; whether a check was dropped is settled by `git show 5457328:tests/skills/wiki-cycle/check.py`. The round-1 fix record says the check names are byte-identical.

Checks made:
- Round-1 findings, confirmed against the current text and `git diff 5457328 HEAD`. standards-1 fixed (seed, CHANGELOG What and Migration, and the report seed all say "any run folder with no `fallbacks.txt`"; `git grep` finds no remaining "begun before" narrowing). standards-2 fixed (one copy rule; the fetcher's printed `Fallback: transcribed (subtitles HTTP 429)` at `scripts/wiki-fetch-youtube.py:267` maps to `Step 2 | subtitles | transcription | <why>`). standards-3 fixed in shape (`FB_BRIEF` needs `expected`, `used` and `why` in order; `_fb_default_model` reads field three), with the Notes loosening and the loose default test above. standards-4 only partly: the filter is still duplicated and `_fb_read` is a further copy of the read closure (the S2 findings above). standards-5 partly: four functions, but the `variant` branching remains (first finding). standards-6 fixed for Step 8, which now points at `/wiki-report`; the seed still restates the rule on purpose, since a usage page carries no paths into the repo. standards-7 fixed (the Decisions log is named; its form conflicts with line 71, above). standards-8, -9, -10, -11 fixed (`git grep "#240|lesson #12"` hits `check.py` only in the earlier `unfinished` block at line 2167; `fallbacks` is an `elif`; `_prepare_fallbacks` calls `_prepare_quick`, as the other callers at lines 603, 1154 and 2341 do; `FB_CLEAN`, `FB_RESUMED` and `FB_BROKEN` replace the literals). standards-12 partly (the incident history is gone, the date remains).
- `check.py` parses (`ast.parse` ok).
- Baseline key sets for the three new cases: Sonnet and Opus agree, and none is false.

| Rule or section | Verdict | Search |
|---|---|---|
| S1, S3, S5, S7, S8, S9, S10, S11, S12 | clear | new names read in context; helpers read only their arguments; no interface or subclass added |
| S2 Duplicated Code | found | filter at 2467/2634; read closures; heading regexes |
| S4 Data Clumps | found | the parameter group, folded into the first finding |
| S6 Repeated Switches / F3 Flag Argument | found | the `variant` branches |
| G25 Magic numbers | found | the repeated drop literal |
| R1, N7, C5 | clear | `_fb_file_checks` records through `add` by design; no commented-out code |
| R26 New code nothing uses | clear | every `_fb_*` and `FB_*` name has a caller (Grep) |
| Comments (C1, C2, C3, R2) | found | C1 date nit; C2 clear for `_prepare_fallbacks`, but the `FB_BRIEF` comment contradicts its check name |
| Names (N2, N3, N5, N6, R3) | found | R3, the two Decisions-log forms |
| Functions (S13, G34, S14, G19, G28, G29, R4, G31, G16, S15) | clear | the 70-line function is split; nesting is at most two levels |
| Tests (T1, T3, T5, T6, R12, R13, R14, T4) | clear | baseline names each match a `check.py` name; no skip added |
| R15 Softened assertion | found | `FB_BRIEF` |
| Refactoring (R21-R25) | clear | the behaviour change is mixed into the restructure; the lens judged it needs no separate finding beyond the Notes loosening |
| Python (PY1-PY8, PY10, PY11) | clear | no cast, `Any`, async or `except` in the block |
| PY3 / PY9 | found | the annotation nit; `FB_BRIEF`, `FB_DEFAULT_MODEL` |

Read depth is in the file table below. Well built: the 70-line function is now four group-named functions, with the field split shared by two helpers; the dispatch is an `elif` chain; the ticket reference and the "idiom" comment are gone.

## Spec

- [important] `tests/skills/PENDING.md:28` (the row for this task) is stale against the fix round and omits the process deviation.
  - Intent: plan.md Step 7, the PENDING row carries "the red-green run id, baselines merged per case".
  - Row says: `Free proof first (no model): 41/41`, `Opus 20261115-145233 passes the resumed case`, and `the Step 9 reorder is checked on Opus only by the two resume cases`.
  - The record says: checkpoints.md, "Offline proof 52/52" and "Rerun on the fix-round text (20261115-152458 ...): all three new cases PASS on Sonnet and Opus (6/6); baselines refreshed per case from it". `check.py:3082-3083` runs "nothing left uncommitted in the notebook" for every case, so "only by the two resume cases" is wrong.
  - Affected: anyone trusting the baselines, which come from 152458, a run the row does not name.
  - Fix: update the row to 52/52, cite 152458 as the baseline source for the three cases on both models, and say that the first Step 9 reorder was made by a session that had read `cases.json`.
- [important] Process record, checkpoints.md ("the edit touches only the Step 9 order, which no new case's check reads"): the reason is wrong.
  - `check.py:3082-3083` (`add("nothing left uncommitted in the notebook", ...)`) sits in the common tail of `check()`, so every case, the three new ones included, reads it.
  - The fix round changed wording only (the order was already "before the commit" in 5457328), and the new words are not the check's words. The record's justification stands uncorrected.
  - Fix: correct the reason in checkpoints.md and PENDING.md:28. The Step 9 wording needs no change.
- [suggestion] `skills/wiki-cycle/SKILL.md:181` names a field the template lacks.
  - Quote: "set the scratchpad's Status to `completed` and Phase 9 to `done`". `reference.md:65` is a bare `### Phase 9: Commit` heading, while other phases carry a `- **Status**: …` line (`reference.md:28`, `:60`).
  - The old text already said "(Phase 9 done)", so the instruction is not new.
  - Affected: the orchestrator at Step 9, which must invent the line.
  - Fix: add `- **Status**: pending | done` under Phase 9 in `reference.md`, or drop "and Phase 9 to `done`".
- [suggestion] Check name over-claims, `check.py:2512` against the name "every wiki-ingester worker's brief tells it to name any fallback in its Notes" (plan Step 3): `FB_BRIEF` tests the sentence shape only, and the comment at 2511 says Notes may be absent. Fix: add a `Notes` search to the same test; the name stays frozen by the baselines (`baseline-sonnet.json:905`, `baseline-opus.json:916`). The Standards lens raised the same point.
- [nit] Short forms of the absent-file label: the wiki-cycle seed (line 51), the wiki-report seed (line 22) and CHANGELOG.md:17 write `Fallbacks: not checked`, while `SKILL.md:273` and `check.py:2514` require `Fallbacks: not checked (no fallbacks.txt in the run folder)`. Fix: quote the full label once per doc, or say the short form is a name.
- [nit] `SKILL.md:110`: `Step 2 | subtitles | transcription | <why>` puts angle-bracket placeholders in skill text, and plan.md:30 rules out `>` in the worker note and file. The lens's reading is that the rule covers the file line, with `<why>` substituted. Fix: write `(why)` to remove the doubt.
  - The same line's "as `Step 2 | X | Y | Z`" for the Decisions log omits line 71's `- <now_stamp()> — fallback:` prefix; the general rule governs (see the Standards finding).

Unverified:
- The run results `20261115-140512`, `-140849`, `-144059`, `-145233`, `-150229` and `-152458` (pass or fail, cost): the run folders are not under the repository (a search of `tests/` for `20261115-152458*` found nothing), so checkpoints.md is the producer's account.
- Whether a real worker brief passes `FB_BRIEF` without Notes: it needs the `_agent_calls` prompt text.
- That the stop-and-report sentence is byte-identical to HEAD (the md5 claim is the producer's). `SKILL.md:103` matches requirements Fact 13 word for word.
- What brief the re-owning developer was given: the checkpoints say it never opened `cases.json` or `check.py`, and I cannot see whether the orchestrator, who had read them, named the failing check in the brief.

Checks made:
- spec-1, the honour rule (the ledger cannot check this one; Mark ruled "A"). I accept it as settling the honour rule, with the record corrections above still owed. Support: the Step 9 sentence now in the repo was written by a session that had not read `cases.json` or `check.py`. The earlier wording echoed the check name ("nothing is left uncommitted"); the new wording does not ("nothing is changed after it"). The order of the two actions (set `completed`, then commit) is the same in 5457328 and HEAD, so the reword changed wording, not behaviour. The three cases then passed on both models on the new text. What the acceptance does not cover: the pass is one run per model and rests on the checkpoints' account (the run folder is unreadable here); `resume` on Opus and the Sonnet regression four ran on the pre-reword text (`-145233`, `-150229`), not on the new one; and the two process-record corrections above are not made.
- spec-2 fixed (all three docs name any run folder with no `fallbacks.txt`); spec-3 fixed except the Notes gap above.
- Plan and invariant rows that moved: check names unchanged against the baselines; no `scripts/` file moved; no hunk in `framework-docs/`; `--brief` and Needs-you order unchanged.

| Plan step, decision or invariant | Verdict | Search or cite |
|---|---|---|
| Step 1 (Fallbacks section, Step 0 header, Step 8, Step 9 keeps the file) | found | SKILL.md:53, 71, 179, 181; wiki-report SKILL.md:268-275 |
| Step 2 (`not checked`; the resume creates no file) | found | SKILL.md:67; wiki-report SKILL.md:273; check.py:2566-2571 |
| Step 3 (four fields, no `>`, log, report line, worker brief) | found | the Notes gap; the log form; SKILL.md:71, 110; check.py:2608-2628 |
| Step 4 (`--brief` only when N is above 0) | clear | wiki-report SKILL.md:301 |
| Step 5 (keyword departure; keyword machine not listed) | clear | SKILL.md:71 |
| Step 6 (worker sentence; the copy) | found | SKILL.md:110; the copy is manual by plan |
| Step 7 (docs, CHANGELOG, PENDING) | found | PENDING.md:28 is stale |
| Decisions 1-5 | clear | SKILL.md:71, 110; wiki-report SKILL.md:268-273; no `fallback` match in `framework-docs/cycle-step-return-format.md` |
| Decision 6 and Exclusions | clear | no timeout, Glob or Grep rule added; no script moved |
| Invariants (stop-and-report sentence; Needs you last; `--brief`) | clear | SKILL.md:103; wiki-report SKILL.md:301-303 |
| Check names unchanged | clear | every `add()` name in check.py:2599-2628 matches a baseline key |
| Round-1 spec-1 | found | the two process findings above |

Read depth is in the file table below. Well built: the Step 2 worker sentence, the copy rule and the Step 9 order are stated once and agree with the wiki-report section and the seeds.

## Change risk

No high-risk file; the change-risk lens was not run.

| File | Risk | Part | Standards | Spec | Change risk |
|---|---|---|---|---|---|
| `skills/wiki-cycle/SKILL.md` | MEDIUM (behavioural rule the cycle follows) | 1 | in part (lines 60-71, 105-112, 176-181; every changed line) | in full | not run |
| `skills/wiki-cycle/wiki-seed/wiki-cycle.md` | LOW | 1 | in part (50-51; the changed line) | in full | not run |
| `skills/wiki-report/wiki-seed/wiki-report.md` | LOW | 1 | in part (line 22; the changed line) | in full | not run |
| `CHANGELOG.md` | LOW | 1 | in full | in part (1-22; every changed line, 12-17) | not run |
| `tests/skills/wiki-cycle/check.py` | LOW (test) | 1 | in part (778-823, 2460-2650, 3066-3075; every changed line) | in part (783-792, 806-827, 2500-2659, 3066-3088; every changed line) | not run |
| `tests/skills/wiki-cycle/baseline-sonnet.json` | LOW | 1 | in part (903-914; the changed line) | in part (888-917; the changed line) | not run |
| `tests/skills/wiki-cycle/baseline-opus.json` | LOW | 1 | — (no hunk in the fix round) | — | not run |
| `skills/wiki-report/SKILL.md`, `reference.md`, `tests/skills/PENDING.md` | MEDIUM / LOW / LOW | 1 | sibling-site reads only | sibling-site reads (PENDING.md:28; reference.md:65) | not run |

Every changed line of each moved file was read by both lenses; the `in part` rows list the lines read, and the lens tables did not call any changed line unread. `cases.json`, `reference.md`, `skills/wiki-report/SKILL.md` and the other files round 1 reviewed and the fix left alone are out of this round.

## needs-a-human

Empty: no finding touches auth, authz, token or session handling, or a production-data migration, and a spec resolved.

## Summary

- Standards: 10 findings (3 important, 5 suggestion, 2 nit). The worst is the `variant` branching that survived the split, with the loosened `FB_BRIEF` (no Notes requirement under a name that says Notes) and the two Decisions-log forms beside it.
- Spec: 6 findings (2 important, 2 suggestion, 2 nit). The worst is the stale PENDING row and the process record whose stated reason for the first Step 9 edit does not hold.
- Change risk: not run.
- Where the axes agree: the `FB_BRIEF` Notes gap, the two Decisions-log forms, and the Step 9 record. Acting on those first would settle five of the sixteen.
- spec-1: accepted by me as settling the honour rule (see Spec, `Checks made:`), with the PENDING and checkpoints corrections owed.
- Not confirmed: the run results (the folders are unreadable here), the brief the re-owning developer was given, and the deleted old `_check_fallbacks` body's check-for-check equivalence.

VERDICT: Standards FINDINGS · Spec FINDINGS · Change risk NOT RUN · needs-a-human 0
