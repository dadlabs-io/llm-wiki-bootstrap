## Requirements confirmation — 2026-11-15

Shown, not asked: Facts 30-32 (a documented fallback is still reported when it fires; a keyword-mode machine is not a fallback; a reported fallback says only what happened).
Decision 1: "Report it as a broken rule (Recommended)" (Mark, terminal, after asking whether keyword is the backup for the AI-aided search).
Decision 2: A, "a run-folder side file read by /wiki-report, no contract change" (Mark, terminal).
Decision 3: "Own section, 'none' line (Recommended)" (Mark, terminal).
Decision 4: "One general rule (Recommended)" (Mark, terminal).
Decision 5: "Worker notes them, cycle copies (Recommended)" (Mark, terminal).
Decision 6: excluded, as recommended ("sounds good", Mark, terminal, after asking whether a longer timeout would help: no, a listing should take seconds, so a 120 s hit is a hang; a longer limit only waits longer; a recurrence is now reported under Decision 4, and the cause is found then).
Size: full (Mark chose full, the recommendation; criterion 1, no open design decision, cannot be confirmed before the plan).
Branch: stay on main (Mark).

## Plan confirmation — 2026-11-15

Shown: plan.md and plan-red-team.md (VERDICT: KILL-ASSUMPTIONS FOUND). Orchestrator's probes: `WIKI_SEARCH_MODE=keyword wiki-qmd-query.py --preflight` says "search mode keyword" (main session; workers unproven); `fixtures/resume/scratchpad.md` resumes from Phase 2.5, so its later steps run under the new rule (kill-assumption 4's criterion met; put as choice 3); a grep of saved events for "exit 75|Fallback: " matched 450+ files but only because the skill text itself carries those words: inconclusive, so choice 2 avoids live fetches instead.
Plan errors (Fix class: plan error, applied by the planner, no question): 1b the keyword check reads only a Fallbacks-section line (moot after choice 1); 2a pin `WIKI_SEARCH_MODE=full` in the cases' env; 3 add `fallbacks` to check.py's quick-run dispatch tuple, set `"ingester_config_broken": true` on its case, and a free offline smoke of `_prepare_fallbacks`/`_check_fallbacks` before the paid run; 5a the worker note format without `>`; 6 one rendering rule for the departure line.
Choices (Mark, terminal, one at a time):
- Choice 1 (kill-assumption 1a, the keyword-machine case): "Drop it (Recommended)" — three new cases; the keyword-machine exclusion is a manual read of the rule.
- Choice 2 (2b, clean case stability): "Empty queue, nothing fetched (Recommended)".
- Choice 3 (4a, an absent file on a resumed pre-rule run): "'not checked' (Recommended)" — one label.
- Choice 4 (4b, --brief): "One line, only when any (Recommended)" — `Fallbacks: N — see the full report` in --brief only when N > 0.
Accepted trade-off: 5b, the worker-note copy and the departure line stay manual (plan's own).
- Go to implement, including the paid red-then-green run of the 3 cases (about $20-30): "proceed" (Mark, terminal, 2026-11-15).

## Implement — 2026-11-15

Developer (skill text, never opened cases.json or check.py): wiki-cycle SKILL.md (the general rule after "Every step writes...", Step 0 creates `fallbacks.txt`, the `--resume` line, Step 2's worker-brief bullet, Step 8's Fallbacks section, Step 9's keep list), reference.md's run-folder paragraph, wiki-report SKILL.md (data source, `## Fallbacks` section with its three states and the rendering rule, the `--brief` line). The Step 2 stop-and-report sentence is byte-identical (grep -cF HEAD:1 NOW:1). Orchestrator read the whole diff.
eval-case-writer (mode new-set; the first dispatch stopped for want of a mode in the brief, resent), saved unchanged: three `fallbacks` cases in cases.json; check.py: `fallbacks` in the quick-run dispatch tuple, a `_prepare_fallbacks` branch in `prompt`, the `_check_fallbacks` branch in `check`, the kind's functions. Its open questions answered by the plan as written: no Numbers-before-Fallbacks check (the plan checks "before Needs you"); "default model" read as `default` or `sonnet`; the not-checked line graded as the fixed value; a resumed run meeting a real fallback would fail "did not create" (rare, no live fetch in that fixture); the Decisions-log check may pass on the old copy (red comes from the file and report checks).
Free proof (scratchpad prove_fallbacks.py, no model): 41 passed, 0 failed — (a) setup/prompt smoke for all three cases (dispatch accepts the kind, queue 1/0/0, resume fixture only for the resumed case, the setting file unparseable only for the broken case, env pins full); (b) an ideal run folder passes every check (8, 5, 15 checks); (c) each of 11 planted mistakes fails exactly its own check.

## Suite red then green, and a Step 9 order fix — 2026-11-15

Clean case alone on Sonnet first (run 20261115-140512-red-green-1bcb08d, $0.92): RED THEN GREEN (old failed: no fallbacks.txt, no Fallbacks section).
All three cases, Sonnet and Opus (run 20261115-140849-red-green-1bcb08d, about $18): 5 of 6 red then green, each old copy failing for the right reason (no file / no section / no fallback line). The sixth, the resumed case on Opus, failed on the new copy only "nothing left uncommitted in the notebook" (scratchpad.md modified after the commit); its fallback checks passed. Rerun on Opus, new copy (20261115-144059, $2.51): the same single failure, so 2 of 2. The session commits, then sets the scratchpad `completed` "per Step 9" (Step 9 read: "commit once, at the end ... Set the scratchpad to `completed`, then show the report"). The old copy's Opus run set it before the commit; the check passed in 13 of 13 earlier Opus `resume` runs. Cause in this change's text not found; the sentence predates the change.
Put to Mark (Discord): A, reorder so the scratchpad is set completed before the one commit; B, leave it as a known flaky Opus result. Mark: "A makes sense. Update before commit". Orchestrator's one-line edit to Step 9 (the orchestrator saved the cases earlier, so this edit was made by a session that had read cases.json; the edit touches only the Step 9 order, which no new case's check reads). Next: rerun the resumed case and the existing `resume` case on Opus.
Opus after the Step 9 reorder (run 20261115-145233, $3.93): the resumed case PASS, `resume` PASS. Regression on Sonnet (20261115-150229, $2.76): `resume`, `models-unreadable-setting-file`, `earlier-complete-and-interrupted-runs-not-named`, `empty-queue-clean-notebook-reads-zero-and-no-backlink-line-in-needs-you` 4/4. Baselines merged per case for the three new cases (Sonnet from 140849; Opus clean and unreadable-config from 140849, the resumed case from 145233), each from a passing run (asserted). Tests' spend for the run about $30.

## Step 7 docs — 2026-11-15

CHANGELOG 2026-11-15 entry; the wiki-cycle usage page's "Fallbacks" bullet; the wiki-report usage page's Fallbacks paragraph; PENDING.md row. INSTALL-INVENTORY: its wiki-cycle and wiki-report rows name no run-folder files or report sections, so unchanged (plan Scope's condition).

## Review round 1 and fix round 1 — 2026-11-15

Review round 1 (code-reviewer; read-only guard PASS): 15 findings, 4 blocking (standards-1 absent-file label narrowed in docs; standards-2 two forms of a worker's fallback note; standards-3 loose brief and default-model checks; spec-1 the Step 9 edit made by a session that had read the cases). Per-file blocking list sent to Mark (Discord). Change risk not run (no HIGH file).
Fix round 1, split by the honour rule: a developer that never opened cases.json or check.py did the skill and doc text (standards-1, -2, -6, -7, -12, spec-1, spec-2): the absent-file label is "any run folder with no fallbacks.txt" in both usage pages and CHANGELOG; one copy rule for every `Fallback:` line (a fetcher's `Fallback: transcribed (<why>)` becomes `Step 2 | subtitles | transcription | <why>`), into the file and the Decisions log; Step 8 points to /wiki-report's section; the usage page's dated clause shortened; Step 9 re-owned and reworded ("Before the commit, set the scratchpad's Status to `completed` and Phase 9 to `done`..."). The stop-and-report sentence byte-identical (md5 equal). eval-case-writer (replay), saved unchanged: FB_BRIEF needs the `Fallback: expected ...; used ...; why ...` shape; the default model read in the used field only; the check split into three functions; nits (no ticket reference, the dispatch an `elif`, `_prepare_fallbacks` runs `_prepare_quick` itself, variant names). Check names byte-identical. Offline proof 52/52 (three new plants, each failing only its own check). Ledger: all 15 set addressed. Next: rerun the three cases on both models on the new text (spec-1 asked for the resumed case on Opus).
