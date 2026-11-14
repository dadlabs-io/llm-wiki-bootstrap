# Review report, round 4 (focused): 240-unfinished-run-check

Fixed point `08d9c6cb7db1df6d731976fc00fd326fde8e0b09` resolves; the diff against it is non-empty (13 files; no untracked files outside `.do-code-change/`). Focused round: scope is the two files in `round4-changed.txt` (`CHANGELOG.md`, `scripts/wiki-cycle-scope.py`), read as the diff from `fc6d606` to the working tree (commits `ac34d95`, `3c54e47`), plus the sibling sites of each addressed finding (standards-24, standards-25, spec-18's recorded rule, spec-20, spec-21). Spec source: `plan.md` and `requirements.md`; `checkpoints.md` (newest entry "Retry-ceiling exhaustion — 2026-11-14") read. The prescan ran clean, so the Standards lens raised no dates, review ids or width. Both lenses ran as `code-reviewer-lens`, foreground flag set, default tier; both came back as launch notices and were waited for. Rulings held and not re-raised: spec-18's skip, standards-21, standards-23/spec-19, standards-22 left open. Files other rounds reviewed and this fix did not move are out of the round: nothing raised there.

## Standards

- [suggestion] `scripts/wiki-cycle-scope.py:555` and `:562` — G5/S2: the heading text `## Decisions log` is still written out in both write sites (the new-scratchpad template at 555 and the append at 562) beside the new `DECISIONS_LOG` pattern at 519, so the heading lives in three places; this is the sibling of standards-24 the fix did not cover.
  - Quote: `text = text.rstrip("\n") + "\n\n## Decisions log\n"` (562) and `f"# Cycle Run — {cycle_id[:10]}\n\n**Status**: interrupted\n\n## Decisions log\n"` (555).
  - Failure mode: editing the pattern at 519 alone makes the search at 563 return None and `log.end()` raise AttributeError.
  - Fix: one `DECISIONS_HEADING = "## Decisions log"`, `DECISIONS_LOG = re.compile(rf"^{re.escape(DECISIONS_HEADING)}$", re.M)`, and the heading used in both writes.

Unverified:
- Whether argparse accepts `--topic` before the subcommand, as CHANGELOG line 16 and the printed lines show: the parser was not in the lens's read ranges. (The script's own usage lines at `:5-16` and the existing tests use that order; not traced by the lens.)

Checks made:
- standards-25 addressed: the module docstring (`:86`), `unfinished_runs`' docstring (`:524-525`) and `run_folder_of`'s (`:547`) all state the id's-own-date rule, matching the guard at `:531` and the glob at `:528`.
- standards-24 addressed in form: `DECISIONS_LOG` is the one pattern, used at `:561` and `:563` with `re.M`, as before; behaviour unchanged (the Spec lens traced the same).
- CHANGELOG line 16 read as a sentence; its command forms match the printed lines at `:583-586`.
- Rulings applied consistently: nothing in the diff re-opens the own-date skip, the no-resume-check wording, or the final-reply check.

| Rule | Verdict | Search |
|---|---|---|
| S2 / G5 | found | Grep "Decisions log" in the script: `:519`, `:555`, `:562`, prose `:97`, `:552` |
| S7 | found, under S2 | same root cause |
| S1, S3-S5, S8-S11, G25, F3, C5 | clear | added lines and `DECISIONS_LOG`, `CYCLE_ID` read in context |
| S6, S12, R1, N7 | n/a | no switch, subclass, new value-returning writer or new function in the diff |
| R26 | clear | `DECISIONS_LOG` used at `:561`, `:563` |
| C1, C2, C3 | clear | docstrings `:86-88`, `:523-526`, `:547` checked against `:531-532`, `:583-586` |
| R2 | n/a | no TODO |
| N2, N3, N5, N6, R3 | clear | `DECISIONS_LOG` read in context |
| PY1, PY8 | clear | diff lines read |
| PY2, PY3, PY4-PY6, PY7, PY9-PY11 | n/a | none added |

Read depth: `scripts/wiki-cycle-scope.py` in part (`:80-100`, `:505-594`, plus a Grep for the heading and run-folder literals; every changed line falls inside); `CHANGELOG.md` in full.
Well built: the one-constant pattern and the three docstrings now state the same run-folder rule the code enforces at `:531`, and the printed resume and close lines match the CHANGELOG and module docstring.

## Spec

No findings. Every addressed item traced to code and to the recorded requirement.

Unverified:
- requirements Decision 1's "a cycle always files it there" is supported by the current skill text, but whether the five folders named in Facts line 10 (and the original `2026-07-17-01`) sit under their own id's date folder is not settled by any file in this repo; it needs a Glob of each notebook's `_inbox/reports/*/*` (the lens did not open the notebooks). Older cycles filed under another date were not checked.
- No code was run; the printed lines were checked by reading the f-string at `:583-586`. The 86/86 pass and check-freeze are producer claims.

Checks made:
- Decision 1's own-date rule against code: `unfinished_runs` `:528-532`, module docstring `:86-88` and `unfinished_runs`' docstring `:523-526` all match; the close-out refuses a misfiled folder via `run_folder_of(...).is_dir()` at `:572-574`, so listing and close-out share one builder.
- spec-20: CHANGELOG line 16 forms (`/wiki-cycle <notebook> --resume <cycle_id>`, `--topic <notebook> unfinished ...`) against `:583-586`, `plan.md:16` and requirements Decision 2: match.
- spec-21: Grep of `mark-interrupted` across the repo: every form carries `--topic` (`:14-15`, `:90`, `:96`).
- Rulings applied consistently: skip of a misfiled folder (`:531-532`, SKILL.md `:53`, reference.md `:76`, usage page `:16`, wiki-report `:99-101`); resume only with a scratchpad (`:583-584`, CHANGELOG, SKILL.md `:63`, docstring `:89`); one cycle per notebook, no lock (SKILL.md `:182`, docstring `:93-94`).

| Spec item | Verdict | Search / sites |
|---|---|---|
| Decision 1 own-date rule vs code | clear | `:528-532` |
| Module docstring `:86-88` and `unfinished_runs` docstring vs code | clear | same |
| Ruling: misfiled folder skipped, consistent | clear | `:531-532`, `:572-574`, four skill/doc sites above |
| Ruling: resume only with a scratchpad | clear | `:583-584` and the sites above |
| Ruling: one cycle per notebook | clear | SKILL.md `:182`, `:93-94` |
| spec-20 CHANGELOG forms | clear | vs `:583-586`, plan, requirements |
| spec-21 docstring form | clear | Grep across the repo |
| standards-24 behaviour unchanged | clear | `mark_interrupted` `:551-566` |
| standards-23/spec-19 | n/a | out of round (check.py) |

Read depth: `scripts/wiki-cycle-scope.py` in full; `CHANGELOG.md` in part (lines 1-40, includes line 16); plan, requirements and checkpoints in full.
Well built: the listing and the close-out use one builder, `run_folder_of`, so the own-date skip and the close-out's refusal cannot drift apart; the printed lines take the notebook from the same `args.topic_name`.

## Change risk

| File | Risk | Part | Standards | Spec | Change risk |
|---|---|---|---|---|---|
| `scripts/wiki-cycle-scope.py` | MEDIUM (new public CLI, rewrites a scratchpad; this round: docstrings and one constant) | 1 | in part (changed lines in full) | in full | — |
| `CHANGELOG.md` | LOW | 1 | in full | in part (line 16) | — |

No high-risk file; the change-risk lens was not run. Other files in the run (SKILL.md, wiki-report, usage page, tests, baselines) were reviewed in earlier rounds and the fix did not move them: out of this round.

## needs-a-human

None. No auth, authz, token or session handling, and no production-data migration.

## Summary

Standards: 1 finding (suggestion: the heading text `## Decisions log` still sits in two write sites beside the new constant; worst and only). Spec: 0 findings. Change risk: not run. Of the findings marked addressed: standards-24 and standards-25 are addressed in form (the heading-text sibling above is the remainder of standards-24), spec-18's rule is recorded and consistent across the docstrings and code, spec-20 and spec-21 are addressed with no bare forms left in the CHANGELOG or the script docstring. The rulings are applied consistently. The one Standards suggestion is cheap and sits on the lines this fix already touched; it would be worth acting on, or leaving open with a reason. The Spec Unverified item (whether the original incident's folders sit under their own id's date) is a person's or a Glob's to settle.

Risks or assumptions: the lenses read at the changed lines (the Standards lens marks the script `in part`, with every changed line inside its ranges), so no read-depth retry was spawned; no code or test was run.

VERDICT: Standards FINDINGS · Spec CLEAR · Change risk NOT RUN · needs-a-human 0
