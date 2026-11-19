## Change confirmation — 2026-11-18

Size: small (proposed; see plan hand-back)

- Split (plan Decisions needed 1): follows from Mark's word 2026-11-18 (terminal): "Lets create a new card, and do trhose ... Please create subtasks foir each of the 3 items" — one card, three subtasks, so one change. Not asked.
- Requirements Decision 1: confirmed earlier (AskUserQuestion answer "Keep the code's rule (Recommended)").
- Q1 Decision 2 (paid re-run of the two left-undone cases, both models, ~$6, after the free fixture test is green): Mark, Discord DM 2026-11-18T23:53Z, verbatim: "Y"
- Q2 Decision 5 (spec-33, dash strict): Mark, Discord DM 2026-11-18T23:55Z, verbatim: "I think if we're looking for exact changes then yes let's make it strict." He asked whether a dash mismatch ever occurred; answer from the 240 record: none, the mapping was the writer's up-front allowance and both paid cases passed.
- Q2 follow-up (Mark, Discord DM 2026-11-18T23:56Z, verbatim): "We'll just fail loudly if we ever have something that doesn't match. These should be the exact same documents so it should match. If we have a dash and a-then that's something we really want to see. What's different" -> added to the eval-case-writer brief (step 6): a copy-check failure names the first differing line, the file's text beside the section's.
- Q3 Decision 4 (A2(b): no index + completed claims.json -> cut-off is that run's timestamp): Mark, Discord DM 2026-11-18T23:58Z, verbatim: "Okay fix it" (after: the state has never occurred in any of the 11 notebooks; only agentic-design ran claims, 10 runs, and it has an index).
- Q4 Decision 3 (A1 test): Mark rejected 'no new test'. Discord DM 2026-11-18T23:58Z: "We should create a test for that. Shouldn't we? Is there a test we can do?"; offered (1) a paid eval case (lint finds nothing to fix; the session records with no bare flag, two empty lists; writer's case, joins the step-9 run, ~$3 more) and (2) a free text check that the sentence is in the skill. Mark 2026-11-18T23:59Z, verbatim: "Let's do 2 first. Then 1. So both". Plan steps 1 and 9 and the cases.json invariant are rewritten in place for this.
- Q5 Trivial stakes: yes for steps 1, 4, 7, 8, 9 (skip mutation) and Size: small: Mark, Discord DM 2026-11-19T00:00Z, verbatim: "Ok. Let's skip for those".
- Test seams (plan Testing Decisions seams 1 and 2): shown in the plan, unchanged by any answer; Mark's go covers the plan as amended.

Size: small — the six criteria: no open design decision (the split question follows from Mark's one-card word); callers of uncovered, entry_backlog_lines, claims_scope, _lu_* all inside Scope (architect's caller search); no schema or migration; no live-data write; no HIGH file; no program refusal changed. Production files in Scope: 2 (shown, not deciding).
Branch: main (small path stays on its branch).

## Step 6 — 2026-11-19
- eval-case-writer (replay) answer saved unchanged into tests/skills/wiki-cycle/check.py (blocks 1-4: header, _lu_norm_line without the dash mapping, _lu_model_wrote_file widened, _lu_first_diff + _lu_script_output + _lu_copy_checks). No check renamed, so no fixture constant re-pointed.
- Fixture: uv run python tests/scripts/test_left_undone_fixture.py -> exit 0, 'every check passed'; all six new plants caught (dash, cp, mv, sed -i, python -c, PowerShell), four old-route controls caught, plain runs pass; the new script-output comparison passes on plain runs (writer's question 1, determinism, answered by this run).
- Writer's questions 2-5 put to Mark (pending).
- Fresh-case writer (step 9a) refused 'Mode: new': fresh mode needs two cases; put to Mark (two cases, ~$12 total, or none) — pending.
- Step 9(a) two fresh cases (~$12 total paid run): Mark, Discord DM 2026-11-19T00:43Z, verbatim: "yes but do we report them?" -> answered: results per case per model, red-green outcome, posted to him and kept in the record.
- Writer's design questions 2-5 (script-output comparison as main guard; detector counts writes to the file only; identical rewrite through a variable path unflagged): Mark, Discord DM 2026-11-19T00:47Z, verbatim: "yes".
- Step 9(a) cases saved unchanged from eval-case-writer (fresh, second answer after a replay with the mode facts: --lint-only --semantic never reaches Step 5): two lint-fixes-record cases in cases.json + kind lint-fixes-record in check.py; json parses, check.py compiles.
- Cost correction before running: red-green runs each new case on the old copy and the new, so 9(a) is 8 sessions (similar resumed --full case: ~$1.2 Sonnet + ~$2.7 Opus), ~$16, plus 9(b) ~$6.27: ~$22 total, not the ~$12 put to Mark. Put to Mark before any run.
