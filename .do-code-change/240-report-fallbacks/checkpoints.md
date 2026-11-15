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
