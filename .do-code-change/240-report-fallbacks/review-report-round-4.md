# Review report, round 4 (focused, the last the retry cap allows): 240-report-fallbacks

Fixed point 1bcb08d (`git rev-parse` resolved earlier in the run; the working tree against it, leaving out `.do-code-change/`, is non-empty, 12 files by `git diff --numstat`, far under 3,000 changed lines for an axis: one part). The round is focused: the lenses saw fix round 3's diff (`git diff 70f251a HEAD`: `check.py`, the wiki-cycle usage page, `PENDING.md`) plus the sibling sites of each round-3 finding, and re-verified four round-1 verdicts against the current text. Files earlier rounds reviewed and the fix left alone (`skills/wiki-cycle/SKILL.md`, `reference.md`, `skills/wiki-report/**`, `CHANGELOG.md`, `cases.json`, the baselines) are out of the round; the lenses read them only as siblings or for the re-verification. One Standards and one Spec lens ran as `code-reviewer-lens`, unnamed, default tier, spawned with `run_in_background: false`; the harness ran both in the background anyway and each report came back as a hand-back message. No file is HIGH, so the Change risk lens was not run. The prescan was clean and the Standards lens was told not to raise review ids, dates or width in `.py` comments.

## Standards

- [important] PY9 / T1-adjacent correctness, `tests/skills/wiki-cycle/check.py:2513`: `FB_BRIEF` rejects a correct brief that writes placeholders.
  - Quote: `expected\b[^;\n<>]*;`. A brief `Fallback: expected <tool>; used <substitute>; why <reason>` matches nothing, so `_fb_brief_ok` returns False and the check at `check.py:2665` fails the run.
  - Fix: drop `<` from the pattern; the `>` test at `check.py:2654` already catches a placeholder that reaches `fallbacks.txt`.
  - Reviewer's note: `plan.md:30` says the skill text writes the shape with no angle brackets, and fix round 3 recorded the saved briefs of run 20261115-163745 re-scored True on Sonnet and Opus, so the shipped wording passes; the defect is a stricter check than the plan's rule on the brief (the rule binds the note and the skill text, not an orchestrator's own brief wording).
  - The lens also said the comment's pointer to `plan.md` (`check.py:2511-2512`) is unbacked because `plan.md:107` forbids only `>`. Disproved: `plan.md:30` states the no-angle-bracket rule for the shape; not a finding.
- [important] T1, `tests/skills/wiki-cycle/check.py:2570` `_fb_brief_ok`: no test pins the round-3 window and angle-bracket rules; a grep of `tests/` finds the function only in `check.py`.
  - Fix: add planted briefs to the free proof (a two-sentence brief, a placeholder brief, a Notes word more than 160 characters back).
  - Reviewer's note: `plan.md:47` makes the free proof a throwaway script "never committed", so by the plan's own design the proof is not in the repository; the finding stands as the lens labelled it, and whether the plan's choice answers it is the run owner's call.
- [important] C2, `tests/skills/PENDING.md:28`: the verification record is stale. The row says "after the two review fix rounds' check tightenings … 63/63" and "Green on the final text, both models: `20261115-163745`", but fix round 3 changed `_fb_brief_ok`'s pattern and window after that run. Fix: say the proof predates round 3 and what was re-scored, or rerun the free proof and the saved worker prompts through the new check.
- [suggestion] `check.py:2571-2577`: a natural two-sentence brief fails. Traced by the lens: `Put any fallback in your Notes. Fallback: expected X; used Y; why Z` returns False, because the last sentence of the before-slice is empty after `. `. The docstring states the same-sentence bound on purpose, so this is a design call. Fix: accept the preceding sentence, or document the one-sentence form.
- [nit] `check.py:2514`: `why\b[ \t]*[^\s<>]` accepts `` `…; why` `` with no reason (the backtick matches), and `Do not use Notes; Fallback: expected X; used Y; why Z` passes because `;` is not a sentence end. Fix: `why\b[ \t]+[^\s<>\`]`; the `;` wrong pass may be accepted.
- [nit] C3, `check.py:2508` and `:2565`: both state the model-name shape; round-3 item 6 is half done. Fix: keep the shape in the docstring and make the comment name only `_fb_default_model`.
- [nit] `check.py:2687`: `else:` silently covers `FB_BROKEN`. Fix: `elif variant == FB_BROKEN:`.

Unverified:
- The saved worker prompts of run 20261115-163745 are not in the repository (a Glob found no run folder); only a re-score through `_fb_brief_ok` settles whether a real brief carries an unrelated "note".
- R21: the old dispatch tuples are elided in the lens's diff, so it could not confirm each variant runs the same checks as before. (My own check below read the old and new hunks.)
- The 52/52 offline proof and the saved-brief re-score are the run's own records; a review runs no test.

Checks made:
- Round-3 Standards 1 (Notes unanchored): fixed in form. The Notes word must now sit in the shape's sentence or line within 160 characters (`check.py:2570-2578`); the lens traced `Notes:` before the shape passes, `Notes\nFallback…` fails, a Notes word further back fails. Weaknesses are the findings above.
- Round-3 Standards 2 (`_fb_lines` duplicate decode): fixed, `_fb_read(run_dir / "fallbacks.txt").splitlines()` at `check.py:2587`.
- Round-3 Standards 3 (dict of lambdas): fixed, an if/elif at `check.py:2679-2689`. I compared old and new hunks: the order of checks per variant is unchanged (clean: drop, file, header, none-label, then section and order; resumed: absent-file, not-checked label, then the two; broken: file, config, then the two), so the baseline key order still holds.
- Round-3 Standards 4 ("(as before)") and 5 (the name `report`): fixed, both gone.
- Round-3 Standards 6 (model rule in a comment and a docstring): partly fixed, see the nit.
- Round-3 Standards 7 (PENDING narrating which session broke a rule): reworded to "Step 9's wording is by a developer that never opened the cases (review fix round 1)"; see the Spec section for what that rewording dropped.
- Round-1 standards-1 held: the full label `Fallbacks: not checked (no fallbacks.txt in the run folder)` or "any run folder with no `fallbacks.txt`" is at `wiki-cycle.md:51`, `wiki-report.md:22`, `wiki-report/SKILL.md:273` (as "the file is absent"), `CHANGELOG.md:16-17`.
- Round-1 standards-2 held: `SKILL.md:110` is the one copy rule; it maps `Fallback: transcribed (why)` to `Step 2 | subtitles | transcription | why`, matching `fetchers.md:36` (`Fallback: transcribed (subtitles HTTP 429)`); the YouTube bullet (line 107) names the short form without a second rule.
- Round-1 standards-3 held for the default-model check (third field only, must hold `sonnet` or `default model/sonnet`: `Step 2 | wiki-ingester-config | default model | …` passes, `default setting` fails). The brief check is tight, tighter than its name on the points above.
- Sibling sites of the worker-note shape (`SKILL.md:110`, `PENDING.md:28`, `CHANGELOG.md:16`, `wiki-report/SKILL.md:273`): all write plain `X; Y; Z` with Notes; none disagrees.

| Rule or section | Verdict | Search |
|---|---|---|
| S1, S3, S8, S9, S10 | clear | names and helpers read in context |
| S2 | clear | `_fb_lines` now reuses `_fb_read`; the copies in other kinds are outside the round |
| S4, S5, S6 | clear | one dispatch at 2679-2689; variant validated once in `_fb_variant` |
| S7, S11, S12 | n/a | single file; no class or subclass added |
| G25 | clear | `FB_WINDOW` named |
| F3, R1, N7, C5 | clear | no flag parameter; `_fb_drop_no_pair` named for its mutation; no commented code |
| R26 | clear | `FB_SENT_END`, `FB_WINDOW`, `_fb_headings`, `FB_NONE`, `FB_REPORT_LINE` each used (2574, 2629, 2623, 2634, 2659) |
| Comments C1-C3, R2 | found | C1 plan pointer disproved; C3 at 2508/2565; PENDING C2 above |
| Names N2, N3, N5, N6, R3 | clear | new names read in context |
| Functions S13, G34, S14, G19, G28, G29, G31, G16, S15 | clear | functions short; regex documented; constants used; R4 n/a (no nesting added) |
| Tests T1 | found | `_fb_brief_ok` untested in the repo |
| Tests T3, T5, T6, R12-R14, T4 | clear | no test behaviour beyond T1; no skip |
| R15 | clear | the `notes?` loosening is stated in the comment |
| Python PY1-PY3, PY7, PY8 | clear | types and imports read |
| PY4-PY6, PY10, PY11 | n/a | no async, no unittest |
| PY9 | found | the brief check's false fail on a placeholder brief |
| R21-R25 | clear | R21 in part (old tuples compared by me); no test deleted |

| File | Risk | Read depth |
|---|---|---|
| `tests/skills/wiki-cycle/check.py` | LOW (test) | in full, 2500-2695 |
| `tests/skills/PENDING.md` | LOW | in part (line 28, the changed row) |
| `skills/wiki-cycle/wiki-seed/wiki-cycle.md` | LOW | in part (line 51, the changed line) |

Well built: the Fallbacks checks are split into per-variant helpers with one dispatch, and the label, the file and the brief each have one definition.

## Spec

- [important] `tests/skills/PENDING.md:28` (wiki-cycle, wiki-report row): the verification record is stale.
  - Intent: round-2 spec-4 asked the row to state exactly what ran on which text.
  - Code: the row says "Green on the final text, both models: `20261115-163745` (the three new cases, 6/6)" and "63/63". `check.py` changed in fix round 3; `checkpoints.md` says "Offline proof 52/52 (setup part skipped: unchanged)" and "re-scored on the saved worker briefs of 20261115-163745: Sonnet True, Opus True". The row says neither, and no model run used the final `check.py`.
  - Affected: anyone reading the row as proof of the final checker.
  - Fix: "check.py changed in fix round 3: offline proof 52/52; the brief check re-scored on the saved briefs of 20261115-163745 (Sonnet True, Opus True); no model run on the final check.py".
- [important] `tests/skills/PENDING.md:28`: the honour-rule deviation is no longer recorded.
  - Intent: round-2 spec-4 asked the row to carry the honour-rule deviation (`plan.md` Testing Decisions: the session that edits the skill does not read `cases.json`).
  - Code: round-3 Standards 7 had the row's sentence "The first Step 9 reorder was made by a session that had read `cases.json` (against the honour rule) …" cut to "Step 9's wording is by a developer that never opened the cases (review fix round 1)"; the row still says "Step 9 reordered (Mark: "Update before commit")", and `checkpoints.md` (the round-2 correction) says the first edit was made by a session that had read `cases.json`. The fix to a style nit removed a record a Spec finding had asked for.
  - Fix: restore one clause: the first Step 9 reorder was made by a session that had read `cases.json`, and the deviation was accepted in round 2.
- [important] `skills/wiki-cycle/SKILL.md:181` (round-1 spec-1 re-verified): the honour rule holds in form, not in substance.
  - Intent: `plan.md` Testing Decisions, the Step 9 wording comes from a session that did not read `cases.json`.
  - Code: current text "Before the commit, set the scratchpad's Status to `completed` and Phase 9 to `done`, so the commit holds the final record and nothing is changed after it." The first edit (commit `4f0c393`, made by the session that had read the cases) read "… before the commit, so the commit holds the final record and nothing is left uncommitted." I confirmed with `git show` that the clause "so the commit holds the final record" carries over verbatim; the order is the one the "nothing left uncommitted" check forced.
  - Affected: the claim that fix round 1 re-owned the decision. Round 2 accepted spec-1; whether the fix-round-1 developer saw the first text is not in the repository.
  - Fix: have a session that has not read `cases.json` restate the Step 9 order from the plan alone, or record the deviation as accepted (round 2 did) in the PENDING row (see the finding above).
- [suggestion] `skills/wiki-cycle/SKILL.md:67` with `wiki-seed/wiki-cycle.md:51`: a pre-rule run resumed and then given a fallback writes the header first, so its report lists that fallback and never says the steps before the resume were not checked.
  - Intent: `requirements.md` Decision 3 / `plan.md:26`, "so silence cannot be read as unchecked".
  - Fix: say in the header or the report that steps before the resume were not checked.
- [nit] `check.py:2514`: `FB_NOTES = re.compile(r"\bnotes?\b", re.I)` matches "Note" in "Note: …", so a brief sentence "Note: a fallback is written as `Fallback: expected X; used Y; why Z`." passes without asking for the Notes column. Fix: require "Notes" followed by "column", "cell" or "in that item's Notes".
- [nit] `.do-code-change/240-report-fallbacks/plan.md:26` (not shipped, stale intent): "including a rule-era run resumed after its Step 0 with nothing found since" reads `not checked`; `SKILL.md:53` has Step 0 create the header-only file, which the report reads as `Fallbacks: none`. No shipped file says otherwise. Fix: correct `plan.md:26` to pre-rule runs.

Unverified:
- Whether the fix-round-1 developer saw the first Step 9 text or the failing check; only the session transcript settles it.
- Byte-identity of the exit-75 and stop-and-report sentences to 1bcb08d, and that `framework-docs/`, `agents/wiki-ingester/`, `scripts/` and `skills/wiki-update/` are untouched: the lens had no shell. (My own check is below.)
- The 52/52 offline proof and the saved-brief re-score; the run folders are not in the repository.

Checks made:
- Round-3 Spec 1 (Notes word anywhere in the prompt): fixed in form; the residue is the `note` nit above.
- Round-3 Spec 2 (seed clause on a resumed run): fixed in the shipped text. `wiki-cycle.md:51` now reads "a run begun before this rule, or resumed from one; such a run reads "not checked" even when nothing fell back after the resume, since resuming does not create the file", true for each kind of run (begun before the rule; begun after it and resumed after Step 0 reads `none`, since the file exists). The second half of that finding, reconciling `plan.md:26`, was not done (`git diff 70f251a HEAD` shows `plan.md` unchanged): the nit above.
- Round-3 Spec 3 (placeholders): fixed, `<` and `>` now refused in the brief's shape (the Standards `important` is the side effect).
- Round-3 Spec 4 (PENDING parenthetical): fixed, it now names "the scratchpad template's Phase 9 Status line"; the row's proof claims are the stale-record finding.
- Round-1 standards-1, -2, -3: held (see Standards, Checks made).
- Invariants and exclusions, by file list: `git diff 70f251a HEAD --stat` shows only the three files above moved this round; no timeout or Glob/Grep rule in the shipped text (`SKILL.md:71` lists "a timeout worked around" as reportable only); "up to 4" unchanged in `reference.md`; the exit-75 sentence at `SKILL.md:103` matches `requirements.md` Fact 13.

| Plan step, decision or question | Verdict | Search or cite |
|---|---|---|
| S3-1 (i) worker brief names Notes | found (nit) | `check.py:2570-2578`, 2514 |
| S3-1 (ii) seed clause per run kind | clear for shipped text; plan.md:26 stale | `SKILL.md:53, 67`, `wiki-cycle.md:51`, `wiki-report/SKILL.md:270-273` |
| S3-1 (iii) no angle brackets | clear | `check.py:2511-2513` |
| S3-1 (iv) Phase 9 template line named | clear | `PENDING.md:28` |
| S3-2 row's 63/63 and "final text" | found | `PENDING.md:28`, `checkpoints.md` round 3 |
| R1 standards-1 label in every doc | clear | `CHANGELOG.md:16-17`, `wiki-cycle.md:51`, `wiki-report.md:22`, `wiki-report/SKILL.md:273` |
| R1 standards-2 one copy rule | clear | `SKILL.md:110`, `fetchers.md:36` |
| R1 standards-3 tight checks | clear | `check.py:2505-2580` |
| R1 spec-1 honour rule | found | `SKILL.md:181`, `git show 4f0c393`, `checkpoints.md` |
| S3-3 exclusions and invariants | clear for the files read | Grep timeout, Glob, ls, up to 4, AGENT.md, framework-docs |

| File | Risk | Part | Standards | Spec | Change risk |
|---|---|---|---|---|---|
| `tests/skills/wiki-cycle/check.py` | LOW (test) | 1 | in full (2500-2695) | in part (2480-2719, 3100-3138, 810-829) | not run |
| `tests/skills/PENDING.md` | LOW | 1 | in part (row 28) | in part (1-92; row 28 in full) | not run |
| `skills/wiki-cycle/wiki-seed/wiki-cycle.md` | LOW | 1 | in part (line 51) | in full | not run |
| `skills/wiki-cycle/SKILL.md` | MEDIUM (behaviour rule), not moved this round | 1 | sibling read | in full | not run |
| `skills/wiki-cycle/reference.md`, `skills/wiki-report/SKILL.md`, `skills/wiki-report/wiki-seed/wiki-report.md`, `CHANGELOG.md` | LOW, not moved this round | 1 | sibling read | in full / in part | not run |

Well built: the three report states and the one rendering rule read the same in `SKILL.md:41` and `wiki-report/SKILL.md`, the check order per variant survived the dispatch rewrite, and every new helper has a caller.

## Change risk

No high-risk file; the change-risk lens was not run. The table in the Spec section above is the file table.

## needs-a-human

Empty: no finding touches auth, authz, token or session handling, or a production-data migration, and a spec resolved.

## Summary

- Standards: 7 findings (3 important, 1 suggestion, 3 nit). The worst: the brief check refuses a correct brief that writes placeholders, and no test pins the new window and bracket rules.
- Spec: 6 findings (3 important, 1 suggestion, 2 nit). The worst: the PENDING row's verification record is stale and has lost the honour-rule deviation, and the Step 9 sentence keeps the first edit's clause.
- Change risk: not run.
- Blocking (critical or important): 6 labelled important, 5 distinct defects. By defect: (1) `FB_BRIEF` rejects angle brackets in a brief (Standards); (2) `_fb_brief_ok` untested in the repo (Standards, T1; `plan.md:47` makes the proof a throwaway); (3) PENDING row stale after fix round 3 (Standards and Spec, one defect on two axes); (4) PENDING row dropped the honour-rule deviation (Spec); (5) Step 9 sentence carries the first edit's clause (Spec; round 2 accepted it, so this is a re-verification, not a new fault). Everything else is a suggestion or a nit.
- Round-3 findings: all 11 confirmed on the Checks made lines, fixed in form; two were fixed with a side effect (the bracket rule, the PENDING trim), one half done (the comment), one not done (`plan.md:26`, a pipeline note).
- Round-1 verdicts: standards-1, -2, -3 still hold; spec-1 holds only as round 2 accepted it.
- Where the axes agree: the PENDING row is stale.
- Not confirmed: the run results, the 52/52 and 63/63 proofs, the saved worker briefs, and who read `cases.json` when.

VERDICT: Standards FINDINGS · Spec FINDINGS · Change risk NOT RUN · needs-a-human 0
