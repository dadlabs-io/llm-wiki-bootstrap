# Review report, round 4 — 243-framework-docs-master (focused round)

Fixed point `7b66e2a92fc2cfa3892050f143bd35fe0e6bd40d` (resolves). Scope of this round: commits `2d962d4..HEAD` as named by the brief; the code moved since round 3 (`git diff 069261e HEAD`) is 4 changed lines in 3 test files, comment-only. The lenses ran as `code-reviewer-lens`, unnamed, with the foreground flag written out (the harness returned launch notices; both reports came back by completion message and were waited for). No file is HIGH, so the change-risk lens was not run. Files the earlier rounds reviewed and this window did not touch are out of the round; nothing new is raised in them. `git ls-files --others` lists nothing untracked.

## Standards

- standards-24 [suggestion] `tests/scripts/test_local_folder.py:25` (C3 / Python): the removed `# noqa: E402` leaves `import _wiki_config as wc` with no recorded reason for sitting after the `sys.path.insert` on line 24, and the same pattern is marked differently elsewhere (`test_search_mode.py:63` keeps `# noqa: E402`; `test_global_toolset.py:695` has no marker). Fix: a plain reason line above the import ("after the sys.path insert"), or one form in all three files.
- standards-25 [nit] `tests/scripts/test_search_mode.py:323` (G4): `gpu = lambda: ("cuda", "CUDA: available")  # noqa: E731` (and `:324`) is a suppression in a file this window edited. It predates the change (present at the fixed point, so floor-guard does not count it). Fix: a local `def`, or leave it.

Unverified:
- Whether any ruff or other lint configuration exists in the repo (the lens did not search for one; verify round 2 states none exists).
- That the earlier fake PASS on the skipped case existed in history (the lens had no git history).

Checks made:
- standards-2 (a skipped case recorded a PASS): still addressed. `_skip` is defined at `test_global_toolset.py:40`; its call sites (`:173`, `:197`, `:212`, `:469`) each `return` before any check; no `check(..., True)` stands for a skip. The window's only edit to that file is the `_run` comment at `:686`.
- The three `_run` bodies and the import behave identically to before (comment-only; diff read).
- `Grep noqa` over `tests/scripts` finds no `noqa` on a line this change added.

Coverage (Standards lens): every-diff rules S1 to S12, G25, F3, R1, N7, R26 `n/a` or `clear` (no identifier, logic, function or constant added; the four lines are a comment and an import); C5 `clear`; C1, C2, C3, R2 `clear` except the C3 finding above; R7 to R11 `clear`/`n/a`; G4 `found` (nit above; the four removals tighten, not loosen); T1 to T6, R12 to R15 `n/a`/`clear` (T4: no skip added this round); PY1 to PY8, PY10, PY11 `n/a`; PY9 `clear`; the Names, Functions, Classes, Boundary, Concurrency and Refactoring sections were not pasted (Paste-when not met). Well built: `_run` keeps every crash as a named failed check, and `_skip` records no PASS.

## Spec

- spec-15 [important] `.do-code-change/243-framework-docs-master/plan.md:189` — the clause "`.claude/wiki-config.json`'s `wiki_folders` keeps only the interview's two answers (`project`, `research`)" is an Expected line that no test and no `manual:` line backs.
  Intent: plan.md:186 "done when the new checks in `tests/scripts/test_local_folder.py` pass".
  Code: `scripts/new-wiki.py:1218` and `:1256` write `"wiki_folders": {"project": args.project_folder, "research": args.research_folder}`. The behaviour is true and unchanged by this run (neither line is in the `7b66e2a..HEAD` diff of `new-wiki.py`). No test reads a scaffolded `.claude/wiki-config.json`'s content (`test_local_folder.py:145-146` reads the Phase B stdout summary list, a different value). `## Testing Decisions` has no `manual: step 3` line.
  Affected: verify's coverage layer (row 3c) fails on it.
  Fix: a `manual: step 3` line in `## Testing Decisions` quoting the probe output; reasoning under Checks made, question 2.
- spec-16 [suggestion] `plan.md:26` — still says `taxonomy_for`'s one caller "`new-wiki.py:1016` ... also feeds `wiki_folders_md` ... and `.claude/wiki-config.json`'s `wiki_folders`", which contradicts plan.md:189. The caller is `new-wiki.py:1043` (`folders = taxonomy_for(...)`); the list reaches only the README folder list and the stdout summary (`:1345`), never the config. Fix: edit with spec-15's fix: "feeds `wiki_folders_md` and the Phase B summary", citing `:1043`.
- spec-17 [suggestion] `plan.md:32` — "so the mechanical lint finds nothing in it" contradicts plan.md:190 and checkpoints.md:83 (the lint does draw findings on the new README, the same as HOME.md). Fix: reword to match line 190.
- spec-18 [suggestion] `plan.md` step 17 (lines 297, 303, 306) — the literal done criterion ("every case 'red then green' on Sonnet and Opus"; "a case that passes on the old copy: not counted as proof") is still unmet for `local-readme-project-none`; it is met only under Mark's recorded ruling (checkpoints.md:102, "It meant what you recommended", DM 2026-11-20 15:28Z). The ruling does not say in words that the free check is model-independent. Fix: a one-line dated amendment under step 17 citing checkpoints.md:102. This does not reopen spec-1.
- spec-19 [nit] `plan.md:49` — red-team history "step 3 lints a freshly scaffolded wiki and expects no finding from `best-practices/`" is superseded by line 190. Fix: mark it superseded.

Unverified:
- `test_local_folder.py:149-157` compares lint report section headings, not each finding's text, so a same-heading finding could pass the line-190 check (the lens did not read the lint report format).
- requirements.md was only grepped by the lens (line 43 agrees with the plan's local-folder rule); not re-read for this round.

Checks made:
- Question 1, spec-1: still addressed. checkpoints.md:102 records Mark's verbatim "It meant what you recommended" with date and time, and the recommendation it answers is checkpoints.md:93 (count the free old-vs-new script check as the red). The window did not move step 17's text or the new-wiki suite.
- Question 1, standards-2: still addressed (see Standards, Checks made). Both items are stale in the ledger only because 89f72bd edited the file or file set their fingerprints cover; neither site changed in substance. The orchestrator re-records both verdicts.
- Question 2, is the unpinned `wiki_folders` clause a blocking Spec finding? Labelled `important`, so the ledger counts it as blocking, but it is a plan-text and evidence gap, not a code defect: the behaviour is true and untouched by this run, and plan.md:95 puts `.claude/wiki-config.json` out of scope. The right fix is a `manual: step 3` line in plan.md's `## Testing Decisions`, quoting the scratch Phase B probe verify round 2 already ran (`{'project': 'stubs', 'research': 'stubs'}`), plus the plan.md:26 and :32 edits above. Not a new test in `tests/scripts/test_local_folder.py`: it would pin unchanged behaviour of an out-of-scope file, be a new frozen test that sends the run back through implement, and cost another retry. If Mark wants a regression guard on the config, that is one assertion in `test_local_folder.py` and his call; deleting the clause instead would drop a recorded ruling (spec-6), so the manual line is the lower-loss route.
- Question 3, sibling sites: the plan has no `noqa` text, `## Scope` lists `tests/scripts/**`, and `## Invariants` states no rule that tests keep suppression comments. The shipped README's frontmatter carries `confidence: high` and a `standalone:` reason with no review dates (`seed/best-practices-local/README.md:6-7`), and `test_lint_of_a_fresh_scaffold_draws_no_finding_on_the_local_readme_that_home_does_not` asserts README kinds are a subset of HOME's, with a control that the same lint names a bad note; plan line 190 matches code and test.

Coverage:

| Spec item | Verdict | Search |
|---|---|---|
| spec-1 / step 17 ruling | clear (met under the ruling) | checkpoints.md 92, 93, 98, 102 |
| standards-2 site | clear | Grep `_skip(`; test_global_toolset.py 36-47, 440-485 |
| step 3 line 189 `wiki_folders` | found | new-wiki.py 1218, 1256, 1345; Grep `wiki_folders` and `wiki-config.json` in tests |
| step 3 line 190 lint line | clear | seed README; test_local_folder.py 160-189 |
| plan lines 26, 32, 49 vs 189/190 | found | read plan.md |
| noqa removal vs Scope and Invariants | clear | Grep `noqa` in the spec folder; plan.md 106-155 |
| comment-only edits change no logic | clear | the three `_run` bodies and the import line read |

Well built: the lint check carries a control that fails when the lint stops naming a bad note, and the `_skip` helper replaced a fake PASS with a visible skip line.

## Change risk

| File | Risk | Part | Standards | Spec | Change risk |
|---|---|---|---|---|---|
| `tests/scripts/test_global_toolset.py` | LOW (test comment) | 1 | in part (changed line read) | in part (changed line read) | — |
| `tests/scripts/test_local_folder.py` | LOW (test comment, import) | 1 | in full | in part (changed lines read) | — |
| `tests/scripts/test_search_mode.py` | LOW (test comment) | 1 | in part (changed line read) | in part (changed line read) | — |
| `plan.md`, `checkpoints.md` (spec source) | not code | — | — | in full | — |

No high-risk file; the change-risk lens was not run. Every changed line of the round was read by both lenses; three files read "in part" because the lenses read the changed hunks and their surroundings, not whole files.

Summary: Standards 2 findings (worst: a suggestion, the import's missing reason). Spec 5 findings (worst: important, plan.md:189's unpinned `wiki_folders` clause; the other four are suggestion or nit and share the plan-text root). Change risk not run. spec-1 and standards-2 are each still addressed; no earlier finding was broken by the moved hunks. Acting on spec-15 with the plan.md:26 and :32 edits before verify is advised; they are plan-text and evidence edits, not code changes.

VERDICT: Standards FINDINGS · Spec FINDINGS · Change risk NOT RUN · needs-a-human 0
