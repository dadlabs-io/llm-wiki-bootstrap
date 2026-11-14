# Review report, round 5 (focused): 240-unfinished-run-check

Fixed point `08d9c6cb7db1df6d731976fc00fd326fde8e0b09` resolves; the merge-base with HEAD is the fixed point itself; the diff is non-empty and there are no untracked files outside `.do-code-change/`. The working tree's only uncommitted change is the excluded `.do-code-change/240-unfinished-run-check/readonly-review.json`. Focused round: the six files in `round5-changed.txt`, read as the diff from `18fc5f5` to HEAD, plus sibling sites. `scripts/wiki-cycle-scope.py` has no hunk in `18fc5f5..HEAD`: the standards-26 fix is in commit `18fc5f5` itself, so the lenses were also given that hunk (`git show 18fc5f5`) and read the script's current lines. Spec source: `plan.md` and `requirements.md`, `doubt-log.md`, and `checkpoints.md` (the three newest entries read; the whole file read by the Spec lens). The prescan ran clean, so the Standards lens raised no dates, review ids or width. Two lenses ran as `code-reviewer-lens`, foreground flag set, default tier; both came back as launch notices and were waited for. Each then got its one read-depth retry in the same round (every file was marked `in part`); both retries reported. Rulings held and not re-raised: a misfiled run folder is skipped; the "told the user" check reads the final reply; one cycle per notebook. Files that earlier rounds reviewed and this fix did not move are out of the round: nothing raised there.

## Standards

- [suggestion] S2 `tests/skills/wiki-cycle/check.py:2300-2302` vs `:2317-2318` — two detectors for one "way out" rule: the open branch uses `offers = resume_offers(oid)`, the complete/interrupted branch only `not re.search(way_out("(?:resume|mark-interrupted)", i), corpus)`, so a generic `--resume` line naming that run passes there and fails here. Fix: use `resume_offers` in the else branch too. Route: the eval-case-writer agent (check.py is its file).
- [suggestion] PY9 (reversed: fails a correct answer) `tests/skills/wiki-cycle/check.py:2254` — `found += [l.strip() for l in corpus.splitlines() if i in l and "--resume" in l]` counts any line naming the run and mentioning `--resume`, so a reply such as "no resume for <id>, the scratchpad is missing" is an offer and fails the no-resume check. Fix: exclude negated lines, or match only `--resume` directly followed by the id or `<cycle_id>`. Route: the eval-case-writer agent. (Raised by the first Standards lens; the retry dropped it only because its brief carried an over-broad ruling. The writer's own recorded limit, "a negated mention on the id's line would count", is a note, not a ruling on this finding, so it stays.)
- [suggestion] R14 `tests/skills/wiki-cycle/check.py:2408` with `baseline-opus.json:730` and `baseline-sonnet.json:723` — the check name embeds the run's cycle id (`add(f"one run folder, {cycle_id}", folders == [cycle_id], folders)`), and `tests/skills/run_skill_test.py:581` compares only names already in the baseline (`base.get(cid, {}).get(n)`), so on any other day the name is absent and a regression on it is never reported; the sibling case still reads `"one run folder, 2026-11-13-01"` at `baseline-opus.json:689` and `baseline-sonnet.json:682`, and this round's diff changed the same literal's date in the other entry. Fix: name the check `"one run folder"` with the id in the detail, and regenerate both baselines. Route: the eval-case-writer agent.
- [nit] S2 `tests/skills/wiki-cycle/check.py:2253-2254` — the two clauses of `resume_offers` overlap: every single-line match of `re.finditer(way_out("resume", i), corpus)` is also picked by the line clause, so one offer is listed twice in the detail; the first clause adds only a `--resume` split by a newline (`[\s=]+` admits one). The verdict (`not offers`) is unaffected. Fix: keep one clause, or dedupe. Route: the eval-case-writer agent.
- [nit] C2 `tests/skills/wiki-cycle/check.py:2242-2246` — the `way_out` docstring says `--<option> <id>` (one option name), but `:2318` passes the alternation `"(?:resume|mark-interrupted)"`. Fix: say `option` may be a regex fragment. Route: the eval-case-writer agent.
- [nit] S1/C3 `tests/scripts/test_cycle_scope.py:564` — the label `"unfinished_offers_resume_or_close_as_one_choice: the printed line is the resume or the close-out"` reads as either/or while the asserted line (`:565-567`) joins both with `; or close it:`. Fix: "the printed line offers the resume and the close-out".
- [nit] T6 `tests/scripts/test_cycle_scope.py:564-567` — the exact-line check covers only the scratchpad branch; the no-scratchpad branch (`resume = ""`, `scripts/wiki-cycle-scope.py:584-585`) has substring checks only (`:360`, `:363-365`, `:367-368`), so a doubled space or a stray `; or` there passes. Fix: add one exact-line assertion for a no-scratchpad run.
- [nit] R14 `tests/scripts/test_cycle_scope.py:396-397` and `:407-408` — `p.stdout.strip() == "unfinished: none"` holds only because `unfinished_none_case` (`:378-388`) wrote reports for the four earlier runs first; the new test is order-dependent. Fix: assert `"2026-10-16-01" not in p.stdout`, or seed the state inside the test (the file is one sequential throwaway notebook by design, so this is a judgement call).
- [nit] R24 `tests/skills/PENDING.md:28` — the Date cell of the Task #240 row says `2026-11-13`, but the Change cell now also carries the round-4 check change (dated 2026-11-14) and narrates earlier run ids. Fix: a separate row dated 2026-11-14 holding only the check change (judgement call).

Unverified:
- Runs `20261114-122942-red-green-1d6b03c` and `20261113-164536-red-green-1d6b03c` (PENDING.md row 28): the baseline keys exist, the red-then-green claim is the producer's; a review runs no test.
- The literal `"scratchpad.md"` at `scripts/wiki-cycle-scope.py:536`, `:554`, `:585` repeats in the script; those lines are outside this round's diff, so no finding.

Checks made:
- standards-26 addressed: `git show 18fc5f5 -- scripts/wiki-cycle-scope.py` shows only `DECISIONS_HEADING = "## Decisions log"`, `DECISIONS_LOG = re.compile(rf"^{re.escape(DECISIONS_HEADING)}$", re.M)`, and the two literals in `mark_interrupted` replaced by `{DECISIONS_HEADING}`; behaviour unchanged. Grep of the script finds the literal `## Decisions log` only at `:519`; `:97` and `:553` are prose.
- The old baseline key and the old check name were both `no resume is offered for the earlier run (--resume <id>)` (the removed lines of the `18fc5f5..HEAD` diff). Both briefs to the lenses wrongly said `<cycle_id>`; the first lens's Unverified item on it is settled by the diff: the baseline was in step with the old check.
- The old negative-case pattern `r"--(?:resume|mark-interrupted)[\s=]+[`\"']?" + re.escape(i)` and `way_out("(?:resume|mark-interrupted)", i)` expand to the same regex (`"--" + option + r"[\s=]+[`\"']?" + re.escape(i)`), so the line-2317 rewrite is spelling only.
- The `**Status**` literal (`scripts/wiki-cycle-scope.py:540`, `:556`, `:557`, `:560`) was raised by the first lens as a sibling duplicate of the heading: it predates the fix (`:557` and `:560` are unchanged context in the `18fc5f5` hunk, `:540` is not in it) and is a different literal from the one standards-26 named, so it is out of the focused round and not counted.

| Rule | Verdict | Search |
|---|---|---|
| S1 | found | label at test:564 |
| S2 / G5 | found | check.py:2253-2254, :2300-2302 vs :2317-2318; `DECISIONS_*` Grep clear |
| S3-S12, G25, F3, C5 | clear | new functions and tests read in context by both lenses |
| R1, N7 | clear | `resume_offers` is a pure query; `mark_interrupted`'s name announces the write |
| R26 | clear | `resume_offers` at check.py:2300; `DECISIONS_HEADING` at script :556, :563; the three tests called at test:409, :568, :576 |
| C1 | n/a | prescan: Python comments |
| C2 | found | check.py:2242-2246 |
| C3 | found | test:564 label |
| R2 | clear | no TODO in the diff |
| S13, G34, S14, G19, G28, G29, R4, G31, G16, S15 | clear | first lens's rows (second lens's brief held codes only); `_check_unfinished` growth is one flat list |
| T1, T3, T5, R12, R13, R15, T4 | clear | first lens: printed line and stdout have tests, no skip, no softened assertion |
| T6 | found | test:564-567 |
| R14 | found | check.py:2408; test:396-397, :407-408 |
| PY9 | found | check.py:2254 |
| PY1-PY8, PY10, PY11 | clear | none added; plain-script suite |
| R24 (touched code) | found | PENDING.md:28 |

Read depth (both lenses; the retry's brief named whole ranges): `scripts/wiki-cycle-scope.py` in part (1-110, 505-595; every changed line, 519-520, 556, 563, read); `tests/scripts/test_cycle_scope.py` in part (1-120, 320-580; changed ranges read); `tests/skills/wiki-cycle/check.py` in part (2224-2321, 2396-2411); both baselines in part (the two `unfinished` cases' entries); `tests/skills/PENDING.md` in part (1-28, row 28 whole).
Well built: the stray-file and misfiled-folder tests each fail for one reason, and `mark_interrupted_prints_what_it_closed` pins the exact stdout the script prints.

## Spec

- [suggestion] `tests/skills/wiki-cycle/check.py:2254` — a negated mention is counted as an offer, so a correct reply can fail the open case.
  - Intent: requirements.md:26 "resume is offered only for a folder that has a scratchpad"; a line saying a run has no resume is not an offer.
  - Code: `found += [l.strip() for l in corpus.splitlines() if i in l and "--resume" in l]`; the negative branch (`:2317-2318`) uses only `way_out`, narrower than `resume_offers`.
  - Affected: a false FAIL on a correct model reply; a weaker negative test than the open one. The writer's own note records the limit.
  - Fix: keep the `way_out` match, narrow or drop the line clause, and use one `resume_offers` helper in both branches (eval-case-writer's file).
- [nit] `scripts/wiki-cycle-scope.py:557` — the surviving mutant `count=0` is called equivalent, which holds only for template-shaped scratchpads.
  - Intent: checkpoints.md:76 "`count=0` in the Status substitution (a scratchpad has one Status line: equivalent)"; plan.md:17 "sets the scratchpad's `**Status**:` line to `interrupted`".
  - Code: `text, n = re.subn(r"^(\*\*Status\*\*:).*$", r"\1 interrupted", text, count=1, flags=re.M)`; the listing at `:540` reads only the first match; reference.md:12 is the only column-0 `**Status**:` in the template, and the phase Status lines start with `- **Status**` and do not match.
  - Affected: a hand-edited scratchpad with a second column-0 Status line would have it rewritten too; no test pins first-only.
  - Fix: a test with two column-0 Status lines pinning first-only, or narrow the checkpoint's claim to the reference template.

Unverified:
- The three new tests each failing alone on its mutant, and the 88/89 claim (checkpoints.md:76): `hand-mutation-result.json` holds the 86-mutant pass from before the tests (every tail `86/86`), and both lenses traced each test by reading to fail on its stated mutant (`:530` `and` for `or`, `:577` print dropped, `:584` "; and close it") and pass on the real code (the em dash and the f-string at `:586` match test line 565 character by character); a run against each mutant copy would settle it.
- Red/green runs `20261114-122942`, `20261113-164536`, `20261113-161525` and the "regraded offline" claim (checkpoints.md:74); 89/89 and check-freeze PASS: producer claims, no run logs, no test run here.
- Case 2 (`earlier-complete-and-interrupted-runs-not-named`) was not rerun after this round; its check regex is unchanged (see Checks made).
- The Opus baselines carry `run: read reference.md before writing the scratchpad` in every case, Sonnet none (`trajectory_rules.py:21`, not read): pre-existing, cause not established.
- `write_scope` (called at `:582`) was read by the retry only by call shape.

Checks made:
- The Spec retry lens raised, as `[important]`, that case 2's negative check changed after its last green run so its baselines record a check that no longer exists. Not counted: the old pattern and `way_out("(?:resume|mark-interrupted)", i)` are the same regex (see Standards Checks made), the check's name is unchanged, and the baseline key is unchanged. Its remaining point, that case 2 was not rerun after the spelling change, is listed above as Unverified.
- standards-26's behaviour traced: the pattern at `:519-520` matches what `^## Decisions log$` matched; the writes at `:556`, `:563` produce the same text.
- The wrap-across-lines note in checkpoints.md:74 ("a wrap across lines is not caught") overstates it: `way_out`'s `[\s=]+` (check.py:2246) matches a newline, so `--resume` then a line break then the id is caught; only an id on a separate line with text between escapes.
- The listing and close-out share `run_folder_of`; the printed line (`:584-587`) matches the CHANGELOG, plan and requirements Decision 2 and the new test; SKILL.md Step 0 "tell the user each line" is consistent with the rulings.

| Spec item | Verdict | Search |
|---|---|---|
| Plan 1: listing rules, own date, interrupted excluded | clear | script 523-544, 583-589; tests 350-425 |
| Plan 1: no scratchpad close-out only; in_progress resume and close-out | clear | script 583-587; tests 359-368, 560-568 |
| Plan 2: close-out status, reason, heading, new scratchpad, prints what it closed | clear | script 552-567, 577; tests 427-508, 570-576 |
| Plan 2: refusals, exit 2, nothing written | clear | script 573-575, 713-716; tests 506-545 |
| Plan 3: red then green, both cases, both models | n/a to read; Unverified | producer claim, run ids above |
| Req Decision 1 own-date rule; a file is not a run | clear | script 530-533; tests 390-409 |
| Req Decision 2 resume only with a scratchpad (script) | clear | script 583-585 |
| Req Decision 2 resume clause in the check | found | check.py:2254 |
| Standards-26 constant | clear | Grep `Decisions log\|DECISIONS_` in the script |
| standards-21/22 (check.py) and renamed baseline keys | clear | check.py:2248-2255, 2300-2302, 2317-2318 vs baseline-opus.json:752, baseline-sonnet.json:745 |
| Mutant survivors 530, 557, 577, 584, 714 | found | the first four killed by the tests by reading; 557 is the nit; 714 wording only |
| Sibling `--resume` checks | clear | Grep: only check.py `:2245-2301` and cases.json `say` fields |

Read depth (both lenses, retry in full on the changed ranges): script 1-110, 217-223, 505-600, 670-734; test_cycle_scope.py 320-580; check.py 2150-2321; both baselines the two cases' entries in full; PENDING.md line 28 in full; hand-mutation.py.txt and -result.json in full; plan, requirements, checkpoints, doubt-log, reference.md in full; SKILL.md in part (51-80, 170-185).
Well built: the listing and the close-out use one builder, `run_folder_of`, so the own-date skip and the close-out's refusal cannot drift apart; the refusal tests assert the script's own error sentences.

## Change risk

| File | Risk | Part | Standards | Spec | Change risk |
|---|---|---|---|---|---|
| `scripts/wiki-cycle-scope.py` | MEDIUM (a constant; its fix is in `18fc5f5`, no hunk in this diff) | 1 | in part (changed lines in full) | in part (changed lines in full) | — |
| `tests/scripts/test_cycle_scope.py` | LOW (tests) | 1 | in part (changed lines in full) | in part (changed lines in full) | — |
| `tests/skills/wiki-cycle/check.py` | LOW (test check) | 1 | in part (changed lines in full) | in part (changed lines in full) | — |
| `tests/skills/wiki-cycle/baseline-opus.json` | LOW (data) | 1 | in part (the two cases' entries) | in part (entries in full) | — |
| `tests/skills/wiki-cycle/baseline-sonnet.json` | LOW (data) | 1 | in part (the two cases' entries) | in part (entries in full) | — |
| `tests/skills/PENDING.md` | LOW (docs) | 1 | in part (row 28) | in part (row 28 in full) | — |

No high-risk file; the change-risk lens was not run. Files that earlier rounds reviewed and this fix did not move are out of this round.

## needs-a-human

None. No auth, authz, token or session handling, and no production-data migration; a spec resolved.

## Summary

Standards: 9 findings (3 suggestion-level on check.py or its baselines, 6 nit or suggestion-level in the tests and PENDING.md; worst: the check.py items, the date-keyed check name and the negated-line false FAIL). Spec: 2 findings (worst: the negated `--resume` line counted as an offer, the same root as the Standards PY9 item, counted once per axis; and a nit on the `count=0` equivalence claim). Change risk: not run. Of what the fix addressed: standards-26 is addressed with behaviour unchanged; the standards-21/22 rewrite meets round 4's ask and brings a negated-line limit the writer recorded; the three new tests match the printed strings and, by reading, kill their mutants, but the 88/89 claim and every red/green run remain producer claims. The findings on check.py route to the eval-case-writer, not a hand edit. Acting on them is advisable; none is a regression in the script.

Read depth: every file was marked `in part` by both lenses and again by both retries, with every changed line inside the stated ranges; the files are named here as not read whole: the script, both test files, both baselines and PENDING.md.

Risks or assumptions: both briefs misquoted the old baseline key as `(--resume <cycle_id>)` (it was `<id>`); no finding rests on that wording. The Standards retry's brief carried an over-broad ruling and dropped the PY9 item, which the first lens's report supplies. No code or test was run.

VERDICT: Standards FINDINGS · Spec FINDINGS · Change risk NOT RUN · needs-a-human 0
