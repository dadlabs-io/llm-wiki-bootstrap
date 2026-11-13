# Requirements — Step 0 names an earlier run that never finished (task #240, lesson #10)

## Facts

- user confirmed (Mark, 2026-11-12, card #240): each pre-mortem lesson is built into llm-wiki; lesson #10 is "a Step 0 check for a run folder without its terminal report"; code change, red then green, then install.
- user confirmed (Mark, 2026-11-13): proceed with #10 first, through do-code-change.
- wiki `project/troubleshooting/research-cycle-failures-we-hit-2026-04-to-10.md` #10: run folder `2026-07-17-01` held step files but no `claims.md`, no `scratchpad.md` and no run-cycle report, and nothing flagged it; status 2026-10-13 "not recurred … Not built: a Step 0 check for a run folder that lacks its terminal report."
- found in `skills/wiki-cycle/reference.md`: a run folder is `_inbox/reports/<date>/<cycle_id>/`, `cycle_id` = `<YYYY-MM-DD>-<NN>`; the terminal report is `<cycle_id>-run-cycle-report.md` (+ `.json`), written at Step 8; the scratchpad's `**Status**:` is `in_progress | completed | interrupted`.
- found in `skills/wiki-cycle/SKILL.md` Step 1.5: "no" / "abort" marks the run `interrupted` and stops; `--resume <cycle_id>` continues a run from its scratchpad.
- found on disk 2026-11-13: `_inbox/reports/` also holds folders that are not runs (`2026-11-13/checker/`, files at the top level); only names matching `<YYYY-MM-DD>-<NN>` are run folders. Of 37 run folders across the notebooks, 5 have no report: agentic-design `2026-05-25-01`, `2026-10-19-01`, `2026-10-31-01` (no scratchpad: steps run by hand), `2026-06-09-01` (scratchpad `completed`, no report), cottage-build `2026-04-25-01` (scratchpad `in_progress`).
- found in `scripts/wiki-cycle-scope.py`: the cycle's own step helper; its subcommands write plain-text side files (`promote-setting.txt`) because the run folder's `*.json` files are step results under the cycle contract. Nothing else calls a new subcommand (new code; no callers).
- found in `skills/wiki-report/SKILL.md`: the report's last section, ⚠️ Needs you, lists everything waiting on the user, one line each.
- follows from Mark's rule (2026-10-17, CLAUDE.md "tests/skills"): a behavioural change to a skill is installed once its new cases run red then green; the wiki-cycle suite gets a case for this.
- follows from the CLAUDE.md SOP: after the change, `-RefreshOnly` (or the tooling mode), then `--mode status` says installed and current; the usage page and CHANGELOG say what changed.
- unchanged cases: every existing `wiki-cycle-scope.py` subcommand and its output; a notebook with no earlier run folders, or none unfinished, gets one quiet line and nothing in Needs you.

## Exclusions

- Nothing is resumed, deleted or repaired automatically: the check only names the folders and what to do.
- Not lessons #11, #12 or #9 (later changes on card #240).
- No lock against two cycles at once: one cycle per notebook at a time (Mark, 2026-11-13); the skill states the rule.
- No change to how a run writes its report or scratchpad, beyond Decision 3's one scratchpad line and one Needs-you line.

## Decisions

1. **What counts as unfinished** (matters most). Recommended: a run folder (name `<YYYY-MM-DD>-<NN>`, not this run's) with no `<cycle_id>-run-cycle-report.md`, unless its scratchpad says `interrupted`. That is the lesson as written, and it catches the original incident (no scratchpad at all). Alternative: only folders whose scratchpad says `in_progress`: quieter (1 of today's 5), but misses a run that died before writing a scratchpad, which is what happened on 2026-07-17.
2. **How a flagged folder stops being flagged.** (Ruled 2026-11-13, review round 1: resume is offered only for a folder that has a scratchpad; a folder with none gets only the close-out.) Recommended: `wiki-cycle-scope.py unfinished --mark-interrupted <cycle_id> --reason "<why>"` sets its scratchpad's status to `interrupted` with the reason in its Decisions log (writing a short scratchpad when there is none); `--resume <cycle_id>` finishes it the other way. Alternative: look back only 30 days, so old folders age out with no command; but a recent hand-run step folder would be named every cycle for a month.
3. **Where it shows.** Recommended: Step 0 prints each folder and the two ways out, writes `unfinished-runs.txt` in the run folder and a line in the scratchpad; the report's ⚠️ Needs you carries one line per folder. Alternative: Step 0 output only (easy to miss in a long run).
