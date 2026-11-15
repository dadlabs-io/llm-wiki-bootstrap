# Review report, round 1: 240-report-fallbacks

Fixed point 1bcb08d (resolves; merge-base is the same commit). The working tree against it, leaving out `.do-code-change/`, is non-empty: 11 files, about 330 changed lines, no untracked files, so one part per axis. The Standards and Spec lenses ran in one message, in the foreground, unnamed, as `code-reviewer-lens` on the default tier. Both returned their reports as a hand-back message. No file is HIGH, so the Change risk lens was not run.

## Standards

- [important] `skills/wiki-cycle/SKILL.md` (the `--resume` paragraph), `skills/wiki-report/SKILL.md` (`## Fallbacks`), `skills/wiki-report/wiki-seed/wiki-report.md` and `CHANGELOG.md` (the 2026-11-15 entry): the docs say different things about when `not checked` appears.
  - SKILL.md says "A resumed run does not create `fallbacks.txt` unless a step has a fallback to record".
  - The report SKILL says "the file is absent: `Fallbacks: not checked (no fallbacks.txt in the run folder)`, never `none`".
  - The seed says "or "Fallbacks: not checked" for a run begun before the rule".
  - The CHANGELOG says "A run resumed from before this change reports `Fallbacks: not checked`".
  - Under the SKILL rules, any resumed run after this change with nothing to record also reads `not checked`, so the seed and CHANGELOG narrow the label to runs "begun before the rule". The wording is Mark's choice (plan confirmation, 2026-11-15), so only the docs are wrong.
  - Fix: make the seed and CHANGELOG say "any run folder with no `fallbacks.txt`" (a resumed run included).
  - Rule: doc accuracy, no rule code.
- [important] `skills/wiki-cycle/SKILL.md` (the YouTube bullet and the worker-note bullet): two note forms exist for a worker's fallback.
  - The YouTube bullet names "`Fallback: transcribed`". `skills/wiki-update/fetchers.md` prints `Fallback: transcribed (subtitles HTTP 429)`.
  - The worker rule asks for "`Fallback: expected X; used Y; why Z`", and the orchestrator copies only that form.
  - The one fetcher fallback the skill names does not fit the copy rule, which is the miss lesson #12 is about.
  - Fix: state one note form in SKILL.md and say how the fetcher's printed line maps to it.
  - Rule: skill-prose contradiction.
- [important] PY9, `tests/skills/wiki-cycle/check.py`: `FB_BRIEF = re.compile(r"fallback.{0,250}?\bnotes?\b|\bnotes?\b.{0,250}?fallback", re.I | re.S)`, used by "every wiki-ingester worker's brief tells it to name any fallback in its Notes". It passes any brief where the words "fallback" and "notes" sit within 250 characters, without the `expected` / `used` / `why` sentence. Fix: match `Fallback: expected` plus `used` and `why`.
  - Same family: `FB_DEFAULT_MODEL = re.compile(r"\bdefault\b|\bsonnet\b", re.I)` passes on the word "default" anywhere in the setting-file line, including the why field. Fix: test the model field only.
  - The Spec lens raised the `FB_BRIEF` point separately; the two lenses agree.
- [suggestion] S2, `check.py`: `_check_fallbacks` repeats code already in the file.
  - The `res[:] = [x for x in res if x["name"] != "quick steps all wrote their pair"]` filter appears in `_check_backlinks` and again here.
  - `_fb_before_needs` rebuilds the `heads = [l[3:].strip()...]` list the existing Needs-you check builds.
  - The `read` closure copies the one in `_check_backlinks`.
  - Fix: a shared `_report_headings(rtext)` and a shared drop helper.
- [suggestion] S13 / F3 / R4, `check.py` `_check_fallbacks`: about 70 lines that mix the file, report and unreadable-config checks. It branches on `variant` in four places and nests `if data:` under `if f.is_file():` inside an `else`. Fix: one function per variant, or a helper for the file checks.
- [suggestion] S8 / S6, rule drift: the three Fallbacks states appear in SKILL.md Step 8 and again in the report SKILL's `## Fallbacks`. The fallback definition is restated in `wiki-seed/wiki-cycle.md`. Fix: Step 8 points at the report section, and the seed points at SKILL.md.
- [suggestion] `skills/wiki-cycle/SKILL.md` worker-note bullet: "The orchestrator copies each such note … as `Step 2 | X | Y | Z`" omits the Decisions-log line the general rule requires for every fallback. Fix: say the copied line also goes to the Decisions log.
- [nit] C1, `check.py` header comment `(task #240, lesson #12)`: a ticket reference in a comment. The file already does this at "task #84 (Mark, 2026-10-06)", so the repo's own precedent may override. Fix: keep or drop per that precedent.
- [nit] C3, `check.py` `FB_CONFIG = … # the suite's own 'names the setting file' idiom`: no such idiom exists under `tests/skills`; the phrase appears only in new check names. Fix: name the function it copies, or drop the comment.
- [nit] `check.py` dispatch: `if case["kind"] == "fallbacks":` follows the `elif` chain, and `_prepare_fallbacks` is a one-branch forwarder to `_prepare_resume`. Fix: add it to the chain as an `elif`.
- [nit] G25, `check.py`: the literals `"clean"` and `"resumed-run-without-the-file"` repeat although `FB_VARIANTS` exists. Fix: name them as constants.
- [nit] `skills/wiki-cycle/wiki-seed/wiki-cycle.md` Fallbacks paragraph: carries dated incident history ("on 2026-08-01 shell timeouts were quietly worked around"), but the seed is a usage page for a developer who never saw the repo. Fix: keep the history in the CHANGELOG.

Unverified:
- The seed says keyword mode is for a machine with "no GPU"; not checked against the search script.
- Whether a case's `env` (`WIKI_SEARCH_MODE: full`) reaches the wiki-cycle run through `ctx["env"]` (the lens saw only `run_skill_test.py:322` apply case `env` generically). The Spec lens read the same line and judged it honoured; this stays unconfirmed for the wiki-cycle path.
- T1: the `--brief` line, the keyword-departure line, the orchestrator copying a worker's note and the Decisions-log line have no check. `PENDING.md` discloses the first three; this is not a new finding.

| Coverage row | Verdict | Search |
|---|---|---|
| S1 Mysterious Name | clear | every added identifier read in context |
| S2 Duplicated Code | found | the filter, heading parse and `read` closure (grep) |
| S3 Feature Envy | clear | new check functions read only their own inputs |
| S4 Data Clumps | clear | the six-parameter signature matches the siblings |
| S5 Primitive Obsession | clear | variant strings validated once in `_fb_variant` |
| S6 Repeated Switches | found | `fallbacks` kind in three dispatch places (the existing pattern) |
| S7 Shotgun Surgery | clear | edits are per feature |
| S8 Divergent Change | found | rule drift between SKILL Step 8 and the report SKILL |
| S9 Speculative Generality | clear | no interface added |
| S10 Message Chains | clear | none in added lines |
| S11 Middle Man | found (nit) | `_prepare_fallbacks` forwards for one variant |
| S12 Refused Bequest | n/a | no subclass |
| G25 Magic numbers | found (nit) | variant literals |
| F3 Flag Argument | found | `variant` branches inside `_check_fallbacks` |
| R1 Answers and mutates | clear | `_check_fallbacks` asserts only |
| N7 Hidden Side Effect | clear | `_prepare_fallbacks` side effect announced by name and docstring |
| C5 Commented-out code | clear | grep of added lines |
| R26 New code nothing uses | clear | every `FB_` constant and helper has a caller |
| Comments (C1, C2, C3, R2) | found | C1 and C3 nits above; C2 and R2 clear |
| Names (N2, N3, N5, N6, R3) | clear | `FB_` prefix matches the `BL_` precedent |
| Functions (S13, G34, S14, G19, G28, G29, R4, G31, G16, S15) | found | S13 and R4 above; the rest clear |
| Error handling (R7-R11, G4) | clear | no catch-all added; the clean-variant drop mirrors `_check_backlinks` |
| Tests (T1, T3, T5, T6, R12-R15, T4) | found | T1 disclosed gaps (Unverified), R15 via the PY9 items |
| Python (PY1-PY8, PY10, PY11) | clear | none added; PY5 and PY6 n/a (no async) |
| PY9 Test passes for the wrong reason | found | `FB_BRIEF`, `FB_DEFAULT_MODEL` |

Read depth is in the file table below. Well built: the check functions are dispatched by kind, each new regex has a caller, and the baseline additions are pure additions whose keys match the check names the code emits.

## Spec

- [important] `tests/skills/wiki-cycle/` (process, the Step 9 edit): the plan's honour rule was broken for the Step 9 reorder, and the reason given for the edit does not hold.
  - Intent: plan.md:41, "the session that edits the skill does not read `cases.json` while it edits (honour rule)".
  - Implemented: checkpoints.md:35, "this edit was made by a session that had read cases.json", justified as touching "only the Step 9 order, which no new case's check reads". The check that drove the edit was "nothing left uncommitted in the notebook", which every new case carries (baseline-opus.json:863 and :919, and the same key in older cases).
  - Affected: the claim that the reorder fixed the resumed case on Opus (run 20261115-145233) rests on an edit by a session that had read the case file, and the claim that it is test-neutral is unsupported.
  - Fix: record the deviation in the PENDING.md row and in checkpoints.md, then re-run the resumed case on Opus after an edit by a session that has not read cases.json, or have Mark accept the deviation in writing.
- [nit] `skills/wiki-report/wiki-seed/wiki-report.md:139` and `CHANGELOG.md:13-14` narrow the absent-file label to "a run begun before the rule". SKILL.md:113 says "the file is absent" in general, and plan.md:26 lists three cases (a run begun before the rule, a resumed run, `--report-only` on an older folder). The docs are incomplete, not false. Fix: "for any run folder with no `fallbacks.txt`". The Standards lens raised the same text as its first finding.
- [suggestion] `tests/skills/wiki-cycle/check.py:201-202, 305`: plan.md:107 says the brief sentence is pinned by the `FB_BRIEF` check, but a two-word proximity match passes any brief that mentions both words near each other. Fix: match the instruction's own words (`Fallback: expected`, or "name any fallback it used in that item's Notes"). Whether a real brief passes falsely is unverified. The Standards lens raised it as PY9.

Unverified:
- The red/green run results (`20261115-140512`, `-140849`, `-144059`, `-145233`, `-150229`) and the "5 of 6" claim: the run folders were not in the brief, so nobody on this review read them.
- That `tests/skills/wiki-cycle/fixtures/resume` has no `fallbacks.txt` (plan.md:45): the fixture was not read.
- Whether real worker briefs pass `FB_BRIEF` without the sentence: this needs the `_agent_calls` prompt text.
- Whether a worker's receipt Notes reaches the orchestrator's copy: the plan accepts this as manual (plan.md:52, 5b).

Checks made:
- `git merge-base 1bcb08d HEAD` and `git rev-parse 1bcb08d` both gave 1bcb08df90e6d9a354f0eee7255c4aa91a8fc5c9; the numstat names no file under `scripts/`, `agents/`, `framework-docs/` or `skills/wiki-update/`, so "no production Python changed" holds.

| Plan item | Verdict | Search or cite |
|---|---|---|
| Step 1 (Fallbacks: none, Step 0 header, Step 8 section, Step 9 keeps file) | found | SKILL.md:27, 41, 62; wiki-report SKILL.md:268-277; check.py:820-821 |
| Step 2 (not checked, resume creates no file) | found | SKILL.md:37; check.py:253-255 |
| Step 3 (four fields, no `>`, Decisions log, report line, worker brief) | found | SKILL.md:41, 50; check.py:284-307; the brief check is weak (see above) |
| Step 4 (`--brief` only when N is above 0) | found | wiki-report SKILL.md:127 |
| Step 5 (keyword departure; keyword machine not listed) | found | SKILL.md:41; wiki-update SKILL.md has no hunk |
| Step 6 (worker sentence, copy) | found | SKILL.md:50; the copy is manual, accepted |
| Step 7 (docs, CHANGELOG, PENDING) | found | CHANGELOG.md:9-15; wiki-cycle.md:87; wiki-report.md:139; PENDING.md:150; INSTALL-INVENTORY.md rows name no run-folder files: clear |
| Invariants (Needs you last; stop-and-report; setting-file line; earlier-run lines; framework-docs) | clear | wiki-report SKILL.md:279 then 292; no hunk in wiki-update, AGENT.md, framework-docs; SKILL.md:53 and :101 outside any hunk |
| Invariant: `--brief` shows nothing new unless fallbacks recorded | found | wiki-report SKILL.md:127 |
| Decisions 1-5 | found | SKILL.md:41, 50; reference.md:75; section order Numbers 252, Fallbacks 268, Needs you 279 |
| Decision 6 and Exclusions | clear | full diff read; no timeout, Glob/Grep or concurrency rule, no script output |
| Step 9 reorder (user-approved mid-run) | found | SKILL.md:62 sets `completed` before the commit; reference.md:65 has no Phase 9 status line, so no conflict |
| Test seam: env pin honoured; `ingester_config_broken` effective | found | run_skill_test.py:322; check.py:266, 271, 829. The plan says `_prepare_models` "is changed", but the diff does not change it; the code already handled the flag |

Read depth is in the file table below. Well built: the rule text matches the plan's header, four-field format, rendering rule and three report states, and the `_prepare_models` flag works for the new kind without a code change.

## Change risk

No high-risk file; the change-risk lens was not run.

| File | Risk | Part | Standards | Spec | Change risk |
|---|---|---|---|---|---|
| `skills/wiki-cycle/SKILL.md` | MEDIUM (behavioural rule the cycle follows) | 1 | in part (changed hunks) | in part (changed hunks, 23-62) | not run |
| `skills/wiki-report/SKILL.md` | MEDIUM (report template and `--brief` rule) | 1 | in part (changed hunks) | in part (lines 100, 104-115, 127) | not run |
| `skills/wiki-cycle/reference.md` | LOW | 1 | in part (changed line) | in part (line 75) | not run |
| `skills/wiki-cycle/wiki-seed/wiki-cycle.md` | LOW | 1 | in part (changed line) | in part (line 87) | not run |
| `skills/wiki-report/wiki-seed/wiki-report.md` | LOW | 1 | in part (changed line) | in part (line 139) | not run |
| `CHANGELOG.md` | LOW | 1 | in part (changed entry) | in part (hunk lines 9-15) | not run |
| `tests/skills/PENDING.md` | LOW | 1 | in part (changed row) | in part (line 150) | not run |
| `tests/skills/wiki-cycle/cases.json` | LOW (test) | 1 | in part (changed lines) | in part (diff lines 62-68) | not run |
| `tests/skills/wiki-cycle/check.py` | LOW (test) | 1 | in part (all added lines 2503-2614, dispatch hunks, plus surrounding functions) | in part (diff hunks, 245-275, 780-830) | not run |
| `tests/skills/wiki-cycle/baseline-opus.json` | LOW | 1 | in full (added tail) | in part (lines 835-968) | not run |
| `tests/skills/wiki-cycle/baseline-sonnet.json` | LOW | 1 | in full (added tail) | in part (lines 825-957) | not run |

Read-depth note: the lenses' `in part` rows describe a read of the changed hunks plus a few neighbouring lines, not a sample, but the lens tables do not say "every changed line read". I did not run the one retry for these rows; treat every `in part` row as not confirmed read in full.

## needs-a-human

Empty: no finding touches auth, authz, token or session handling, or a production-data migration, and a spec resolved.

## Summary

- Standards: 11 findings (3 important, 4 suggestion, 4 nit). The worst is the contradicting docs on when `not checked` appears. The two other important ones are two note forms for a worker's fallback, and a brief check that can pass for the wrong reason.
- Spec: 3 findings (1 important, 1 suggestion, 1 nit). The worst is that the Step 9 reorder was made by a session that had read `cases.json`, against the plan's honour rule.
- Change risk: not run.
- Where the axes agree: the `not checked` label's wording in the seed and CHANGELOG, and the weak `FB_BRIEF` check. Acting on those first would settle three of the findings.
- On `doubt-log.md`: the run's missing doubt log is arguable. The Step 9 reorder was a non-trivial skill decision made mid-run by a session that had read the cases, and a logged doubt would have caught the honour-rule point.
- Not confirmed: the red/green run results and the `resume` fixture were not read by any lens, and no file's `in part` read was retried.

VERDICT: Standards FINDINGS · Spec FINDINGS · Change risk NOT RUN · needs-a-human 0
