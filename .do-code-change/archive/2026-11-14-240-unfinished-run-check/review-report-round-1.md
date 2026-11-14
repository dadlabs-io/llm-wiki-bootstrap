# Review report, round 1: 240-unfinished-run-check

Fixed point `08d9c6cb7db1df6d731976fc00fd326fde8e0b09` (resolves; merge-base with HEAD is the same commit), working tree, `.do-code-change/` left out. No untracked files outside it. Non-empty diff, 10 files, about 1,000 changed lines (cases.json 565 of them), so one part per axis. Spec source: `plan.md` and `requirements.md` (artifact directory), with `doubt-log.md` and `name-review.md` given to the Spec lens. The review prescan (dates, review ids, width) was reported clean and the Standards lens skipped those. Lenses ran in the foreground as `code-reviewer-lens`, default tier; the Spec lens read `cases.json` only in part, so that one file got its one retry, which read it in full.

## Standards

- [important] `tests/skills/wiki-cycle/cases.json` (whole file) — R25 cleanup past the task: the file was re-serialised from one case per line to indented JSON (509 added / 56 removed), hiding the two new cases in the diff.
  - [eval-case-writer / saver] The two appended cases were saved unchanged by rule; the re-layout is in the saved file.
  - Fix: restore the compact one-case-per-line layout and append only the two new case lines.
- [important] `scripts/wiki-cycle-scope.py` (`unfinished_runs`, `mark_interrupted`) — G26/G2 a run another session is still writing (scratchpad `in_progress`, no report yet) is named "unfinished", and `mark_interrupted` does `text = pad.read_text(...)` then `atomic_write_text(pad, ...)` with no age or lock check.
  - Overlaps the doubt log's "marking a run still running — trade-off"; raised here because the Standards lens did not see that log.
  - Fix: refuse `--mark-interrupted` on a recently written scratchpad unless forced, or say in the listing line that the run may still be live.
- [suggestion] `scripts/wiki-cycle-scope.py` (`unfinished_runs` / `mark_interrupted` / `cmd_unfinished`) — S2/S5/S7 the `_inbox/reports/<date>/<id>` path and the `RUN_ID` check are built in more than one place. Fix: one helper `run_folder_of(nb, cid) -> Path | None` used by both callers.
- [suggestion] `scripts/wiki-cycle-scope.py` (`mark_interrupted`) — G16/G19/S13 status rewrite, heading insertion and section append are interleaved in regex code, and `log` / `after` hold `re.Match` objects (S1). Fix: split into `_set_status(text)` and `_append_under(text, heading, line)`; rename the matches.
- [suggestion] `scripts/wiki-cycle-scope.py` (`cmd_unfinished`) — S15 `out = write_scope(...)` is never read, while the sibling `promote` print ends `-> {out}`. Fix: print it or drop the assignment.
- [suggestion] `skills/wiki-cycle/SKILL.md` (Step 8) and `skills/wiki-report/SKILL.md` (Needs-you item) — S2 the "nothing about earlier runs when none" rule is stated in both. Fix: keep it in wiki-report and point to it from Step 8.
- [suggestion] `tests/scripts/test_cycle_scope.py` (`unfinished_names_runs_without_report`) — R14 `ids == ["2026-09-10-01", "2026-09-24-01", "2026-10-01-01", "2026-10-02-01"]` depends on folders made by earlier sections of the same script. Fix: create them inside this section or use a fresh notebook.
- [suggestion] `scripts/wiki-cycle-scope.py` (`main`, `cmd_unfinished`) — T3 no test runs `unfinished` with neither flag, or with both `--run-folder` and `--mark-interrupted` (the second silently ignores `--run-folder`). Fix: add the two exit-2 tests, or reject the combination.
- [suggestion] `tests/skills/wiki-cycle/check.py` (`_check_unfinished`, the "does not name the {name} run" check) — PY9 `i not in utext` passes when no file is written, so the complete-and-interrupted case passes even if Step 0 never ran. [eval-case-writer] Fix: also assert `utext.startswith("#")` in that branch.
- [suggestion] `tests/skills/wiki-cycle/check.py` (`_runs_mark_interrupted`) — G16 a 15-line command parser whose `\$\{?\w+\}?` alternative counts any shell variable as the script. [eval-case-writer] Fix: keep the variable case only if a real run needs it, and say so in one line.
- [nit] `scripts/wiki-cycle-scope.py` — R3 `RUN_ID` against `cycle_id` for the same concept. Fix: rename to `CYCLE_ID`.
- [nit] `scripts/wiki-cycle-scope.py` (`cmd_unfinished`) — R3 `cid = args.mark_interrupted` is bound, then `args.mark_interrupted` is read again. Fix: use `cid`.
- [nit] `scripts/wiki-cycle-scope.py` (`unfinished_runs`) — R24 `return sorted(out)` repeats the order of the `sorted(...glob("*/*"))`. Fix: drop one sort.
- [nit] `tests/skills/wiki-cycle/check.py` (`_unfinished_ids`) — R24 `from datetime import date, timedelta` inside a function with no reason. [eval-case-writer] Fix: move to the module top.

Unverified:
- F3: `unfinished` both lists and closes (`if args.mark_interrupted:`); left out because `cost --mark start|end` already does the same. A separate subcommand would remove it.
- `mark_interrupted` on a scratchpad whose last line is `## Decisions log` with no trailing newline: the heading regex needs `\n`, so a second heading may be appended. Not run.
- `unfinished_runs` reads with `errors="replace"`, `mark_interrupted` reads strictly. Not run.

Checks made:
- cases.json content against the fixed point (parsed both with `uv run python -B -I -c`): the first 31 cases equal the fixed point's, `skill`, `sources` and `_planned` are equal, no new top-level key, 33 cases now. The reformat changed layout only; this settles the Standards lens's unverified "pre-change layout" point and the Spec lens's "no existing case changed" point.

| Rule | Verdict | Search |
|---|---|---|
| S1 | found | `log`/`after`/`n` in `mark_interrupted` |
| S2 | found | path build in two places; SKILL.md Step 8 vs wiki-report |
| S3, S4, S6, S8–S12 | clear / n/a | read the three new functions; no subclass (S12 n/a) |
| S5 | found | `RUN_ID` validated twice (folded into S2 finding) |
| S7 | found | folded into S2 finding |
| G25 | clear | `[:10]` is the date length `RUN_ID` defines |
| F3 | found | moved to Unverified |
| R1, N7, C5 | clear | `unfinished_runs` is a pure query; `mark_interrupted` names its write |
| R26 | clear | all reached from `main` dispatch; plan asks for the subcommand |
| Comments C1–C3, R2 | clear | task references follow the module's docstring habit; no TODO added |
| Names N2, N3, N6 | clear | read each new name |
| Names N5, R3 | found | nits |
| Functions S13, G19, G16, Dead Code | found | `mark_interrupted`; `out` assignment |
| G34, S14, G28, G29, R4, G31 | clear | at most 3 parameters, nesting at most 2 |
| Classes/modules S16, G8, G17, G18, G13, S17, R5, R6, G35, G1 | clear | module-scope `RUN_ID` is an immutable regex |
| Error handling R7–R11, G4 | clear / n/a | line naming the id on a bad cycle id; check.py `res[:] = ...` follows the file's pattern |
| Boundary G3, G33 | clear | edge cases in Unverified |
| G26, G2 | found | live-run finding |
| Tests T1, T5, T6, R12, R13, R15, T4 | clear | every new branch has a test; refusal cases snapshot the tree |
| T3 | found | missing-flag paths |
| R14 | found | order-dependent ids |
| Refactoring R21–R24 | clear / found | R24 nits |
| R25 | found | cases.json reformat |
| PY1, PY4–PY6 | n/a | none added |
| PY2, PY3, PY7, PY8, PY10, PY11 | clear | stdlib only; plain-script test pattern wins over PY10 |
| PY9 | found | check.py negative check |

Read depth: all ten files `in full`.
Well built: the subcommand reuses `write_scope`, `atomic_write_text` and `now_stamp`, and every new branch in `test_cycle_scope.py` runs the real script in a throwaway notebook.

## Spec

- [important] `scripts/wiki-cycle-scope.py` (`unfinished_runs` no-scratchpad branch, and the printed line in `cmd_unfinished`) — the "resume" way out is printed for folders with no scratchpad, and `--resume` cannot continue those.
  - Intent: plan Step 1, "are each printed with their why and the two ways out"; SKILL.md, "`--resume <cycle_id>`: read that run's scratchpad and continue from the phase after the last `done`".
  - Implemented: `out.append((d.name, "no scratchpad"))`, then `resume: /wiki-cycle --resume {cid}` is printed for every found folder. A `completed`-status folder with no report has no phase left after its last `done` either.
  - Affected: the user, on the very incident's shape (no scratchpad, 2026-07-17-01). Pinned by `test_cycle_scope.py` ("each line gives both ways out") and [eval-case-writer] check.py ("both ways out given: resume").
  - Fix: for a no-scratchpad folder print only the close way out, or give `--resume` a branch that reads the step JSONs; amend the plan line to match.
- [important] `tests/skills/wiki-cycle/baseline-sonnet.json`, `baseline-opus.json` — plan Step 3's done criterion ("red on the installed skill and green on the changed one (Sonnet and Opus baselines)") is not met in the diff.
  - Intent: plan Step 3; requirements, "installed once its new cases run red then green".
  - Implemented: neither new case id appears in the baseline files; the PENDING row records the run but lacks the "Baselines merged per case" phrase the neighbouring rows carry.
  - Affected: the install gate.
  - Fix: merge both case ids into both baselines after the green runs, or record why not.
- [suggestion] `tests/skills/wiki-cycle/check.py` (`corpus = "\n".join([reply, rtext, utext, stext])`) — the naming checks read a merged corpus, so Step 0 "tell the user each line now" (SKILL.md) is not tested; a run that writes the lines only into files passes. [eval-case-writer] Fix: assert the final reply names the run id separately.
- [suggestion] `skills/wiki-cycle/reference.md` (scratchpad template line), `skills/wiki-cycle/SKILL.md` Step 8 vs requirements Exclusions "No change to how a run writes its report or scratchpad" — the diff follows Decision 3 ("a line in the scratchpad", a Needs-you line) but the Exclusion is unamended. Fix: amend the Exclusion to "beyond Decision 3".
- [suggestion] `skills/wiki-report/wiki-seed/wiki-report.md:22` — the usage page's Needs-you list omits the new item. Stale intent (plan Scope and Step 4 name only the wiki-cycle page), not a defect; fix: add the item to that list.
- [suggestion] `tests/skills/wiki-cycle/cases.json` (second new case) — plan Testing Decisions names "one new case"; two were added. The second is the negative case that requirements and Step 1 call for. Fix: record "two cases" in plan.md, or move its negative checks into `test_cycle_scope.py`. [eval-case-writer]
- [nit] `plan.md` format line vs `cmd_unfinished` print — the plan's `(<why>: no scratchpad | ...)` has a slot the printed `({w})` does not fill. Fix: amend the plan to the printed form.
- [nit] requirements Decision 3 "one line per folder" vs the wiki-report template's one bullet "each id, why, and the two ways out". Fix: say "one line per folder" in the template.
- [nit] `plan.md` Invariant "pinned by step 2's Failures bullet" — that bullet lists only unknown-id and missing-reason; the listing's no-edit is checked only by check.py. `write_scope(rf, ...)` writes into whatever folder is given, so an earlier folder passed as `--run-folder` is edited. Fix: correct the pin text; guard or document.
- [nit] `tests/skills/wiki-cycle/check.py` (`_unfinished_ids`) — `earlier` is an unvalidated free string; any value other than `"open"` takes the complete-and-interrupted branch. [eval-case-writer] Fix: assert it is one of the two values.

Unverified:
- The 79/79 suite result and red-green run `20261113-145815-red-green-1d6b03c` are producer claims (name-review, PENDING); the run folder is outside the repo.
- Requirements' on-disk counts (5 of 37 run folders with no report) not re-checked.
- Whether `--resume <id>` reuses the folder; if it creates a new one, the resumed run's Step 0 names the folder it resumes (the script excludes only `rf`).
- `--mark-interrupted` on a folder that already has its report: the script checks only that the folder exists; the spec is silent.
- Plan Step 1 "nothing created outside rf": `write_scope`'s `mkdir(parents=True)` can create ancestors of `rf`; the test uses a path outside `reports/`.
- The refresh and `--mode status` (plan Step 4) are not in the diff.
- Mutation testing could not run (this repo has no `src/**/*.py`); a known gap for verify, not a finding.

Checks made:
- cases.json existing cases unchanged against the fixed point (see Standards, Checks made): 31 of 31 equal.
- The Spec lens's cases.json retry fields check: kind, earlier, timeout, say, staged, done and author match how check.py reads them; no field missing or misnamed.

| Spec item | Verdict | Evidence |
|---|---|---|
| Impl: subcommand in step helper beside `promote` | clear | `cmd_unfinished` follows `cmd_promote` |
| Impl: output format line | found (nit) | script print vs plan |
| Impl: `--mark-interrupted` needs no `--run-folder` | clear | `cmd_unfinished`, parser |
| Impl: writes `unfinished-runs.txt`, exit 0 | clear | `write_scope`; tests |
| Skill Step 0 runs it after promote, tells user | clear | grep across repo shows only SKILL.md, usage page, wiki-report, CHANGELOG, tests |
| Step 8 and wiki-report Needs-you | clear (nit) | diffs |
| Testing seam: `test_cycle_scope.py` | clear | test diff |
| Testing: suite case red then green, baselines | found | baselines finding; count (suggestion) |
| Step 4 docs | clear for wiki-cycle page and CHANGELOG; found for wiki-report page | usage pages |
| Step 1 Expected: listing and two ways out | found | resume finding |
| Step 1 Expected: none gives header only | clear | script, tests |
| Step 1 Failures: reports folder missing | clear | glob on missing dir; "nothing outside rf" unverified |
| Step 2 Expected: status, reason, next run leaves it out | clear | script, tests |
| Step 2 Expected: no scratchpad written | clear | script, tests |
| Step 2 Failures: unknown or malformed id, missing reason | clear | tests snapshot the tree |
| Step 3: Needs-you names the line | clear | wiki-report SKILL.md; check.py |
| Invariant: existing checks stay green | unverified | producer claim |
| Invariant: no edit except `--mark-interrupted` | clear for the listing; found (nit) | pin text |
| Exclusion: nothing resumed, deleted or repaired | clear | SKILL.md "Change nothing in those folders" |
| Exclusion: lessons 11, 12, 9 | n/a | no code path in the diff |
| Exclusion: no change to report or scratchpad | found (suggestion) | Decision 3 conflict |
| Facts and Decisions 1, 2, 3 | found (resume), clear otherwise | see findings |

Read depth: nine files `in full`; `cases.json` `in part` on the first pass, `in full` on the retry.
Well built: `unfinished_runs` filters by `RUN_ID` and skips the current run by resolved path, which handles `checker/` and loose files; the mark path writes through `atomic_write_text`, which leaves no temp file, settling the doubt log's open item.

## Change risk

| File | Risk | Part | Standards | Spec | Change risk |
|---|---|---|---|---|---|
| `scripts/wiki-cycle-scope.py` | MEDIUM (new public CLI, state change: rewrites a scratchpad) | 1 | in full | in full | — |
| `skills/wiki-cycle/SKILL.md` | MEDIUM (procedure the cycle follows) | 1 | in full | in full | — |
| `skills/wiki-report/SKILL.md` | LOW | 1 | in full | in full | — |
| `skills/wiki-cycle/reference.md` | LOW | 1 | in full | in full | — |
| `skills/wiki-cycle/wiki-seed/wiki-cycle.md` | LOW | 1 | in full | in full | — |
| `CHANGELOG.md` | LOW | 1 | in full | in full | — |
| `tests/scripts/test_cycle_scope.py` | LOW | 1 | in full | in full | — |
| `tests/skills/wiki-cycle/check.py` | LOW | 1 | in full | in full | — |
| `tests/skills/wiki-cycle/cases.json` | LOW | 1 | in full | in full (retry) | — |
| `tests/skills/PENDING.md` | LOW | 1 | in full | in full | — |

No high-risk file (no auth, sessions, crypto, payments, external call, migration, or removed validation; the only removed lines are the cases.json re-layout); the change-risk lens was not run.

## needs-a-human

None. No auth, authz, token or session handling, and no production-data migration.

## Summary

Standards: 14 findings (2 important, 7 suggestion incl. 3 for the eval-case-writer, 5 nit incl. 1 more for it; worst: the whole-file cases.json re-layout, and a live run named and rewritable as "unfinished"). Spec: 9 findings (2 important, 4 suggestion, 3 nit; worst: the "resume" way out is printed for runs with no scratchpad, which `--resume` cannot continue, and the new cases are not in the baselines). Change risk: not run. The Standards and Spec axes agree that the "resume" and listing contract around a run folder with no scratchpad (the incident's own shape) and a live `in_progress` run deserve a decision. Worth acting on the important findings of each axis; findings on `cases.json` and `check.py` go back to the eval-case-writer, not the implementer.

VERDICT: Standards FINDINGS · Spec FINDINGS · Change risk NOT RUN · needs-a-human 0
