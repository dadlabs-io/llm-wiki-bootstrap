# Review report, round 3 (focused) — 240-backlink-block-check

Fixed point `f9b3aa200a86ce60716ce42dae48b6cff1022f88` (resolves). The change under review for the lenses is the fix round's diff, commit `043937e` to HEAD, for the nine files in `round3-changed.txt` (`.do-code-change/` left out; about 40 changed lines: 8+/13- in the rebuild script, 4+/3- lint docstring, 2+/2- promote comment, 16+ test, 5 doc lines), plus sibling sites of each addressed round-2 finding. One part per axis, far below 3,000 lines. The lenses ran as unnamed `code-reviewer-lens` spawns on the default tier, with `run_in_background: false` written out on each; the harness returned both as launch notices, so I waited for their completion and took the reports from them. Spec source: `plan.md`, `requirements.md` (both amended), `checkpoints.md` (the entry "Review round 2 and fix round 2" read whole), `doubt-log.md`. The prescan ran clean, so the Standards lens skipped dates, review ids and width in Python comments. Items left with reasons in round 2 (standards-16..22) were not re-raised. Nothing was run: the producer's claims (59/59, four invariant files, check-freeze PASS) are unverified here.

## Standards

- [suggestion] C2 `scripts/wiki-promote.py:303-304` — standards-15 is not fixed: the comment now says "Outside a promotion only /wiki-cycle runs it (before each lint)", but `skills/wiki-verify/SKILL.md:90` runs `wiki-reciprocate-backlinks.py --topic <topic> --vault <vault>` ("re-run the integration scripts so the change propagates to backlinks/INDEX/MAP") and `skills/wiki-rollback/SKILL.md:92` runs it in its Step 5 (I re-ran the Grep over `skills/**/SKILL.md` and saw both lines). The round-2 wording had the same false "only" claim; the round only reworded it. Fix: "Outside a promotion, /wiki-cycle (before its lint), /wiki-verify and /wiki-rollback run it too."
- [suggestion] S2/T5 `scripts/wiki-lint-mechanical.py:332, 336-338` against `scripts/wiki-reciprocate-backlinks.py:59-61` — two copies of the block rule now differ: the rebuild anchors START/END to their own line ("a marker quoted mid-line is prose"), the lint still counts `text.count(BACKLINK_START) > text.count(BACKLINK_END)` and cuts at `BACKLINK_START in prose` on text where only inline code is stripped, so an unticked mid-line START reads as "block not closed" in the lint while the rebuild ignores it. The new test (`tests/scripts/test_backlink_blocks.py:541`) backticks the marker, so the unticked case is untested. Fix: anchor the lint's START test the same way, or name the difference in the lint comment, and add a test with an unticked mid-line START. (Context, not raised: `scripts/_entry_checks.py:253` holds a third unanchored copy, untouched by this diff.)
- [nit] S1 `tests/scripts/test_backlink_blocks.py:540` — the name `..._when_a_start_marker_is_quoted_inline_twice` suggests two quotes, but the prose quotes the START once; "twice" means two rebuilds. Fix: rename to `..._survives_two_rebuilds`.

Unverified:
- `framework-docs/cycle-step-return-format.md:175`, `CHANGELOG.md:17` and `skills/wiki-report/SKILL.md:278` give repo counts (+10, +20, +187, "three backlinks") that the diff cannot check.
- Whether `/wiki-cycle --lint-only` runs Step 3 (affects the "before each lint" wording in the promote comment).

Checks made:
- standards-23 (the lint docstring naming the row kinds): fixed. `scripts/wiki-lint-mechanical.py:319-322` names extra, missing, unclosed and `in_fence`, matching the rows built at `:352-361`.
- Tests run: none (a review runs no test).

| Rule / section | Verdict | Search |
|---|---|---|
| 1 Mysterious Name S1/N1 | found (nit) | new identifiers read in context: START_LINE_RE, BLOCK_RE, stray, kept; the test name |
| 2 Duplicated Code S2/G5 | found (suggestion) | Grep BACKLINKS-AUTO, BACKLINK_BLOCK_RE, _BACKLINKS_RE over scripts/ and tests/ |
| 3 Feature Envy S3/G14 | clear | diff functions read |
| 4 Data Clumps S4 | clear | no repeated value group added |
| 5 Primitive Obsession S5 | clear | none added |
| 6 Repeated Switches S6/G23 | clear | none added |
| 7 Shotgun Surgery S7 | clear | marker rule spans scripts, tests and docs; the edits are mechanical wording |
| 8 Divergent Change S8 | clear | none added |
| 9 Speculative Generality S9 | clear | none added |
| 10 Message Chains S10/G36 | clear | `stray.start()` is one level |
| 11 Middle Man S11 | clear | none added |
| 12 Refused Bequest S12 | clear | no subclass in diff |
| 13 Magic numbers G25 | clear | literals in added lines |
| 14 Flag Argument F3/G15 | clear | none added |
| 15 Answers and mutates R1 | clear | extract_outbound_links, rewrite_backlinks_section read |
| 16 Hidden Side Effect N7/G20 | clear | same functions |
| 17 Commented-out Code C5 | clear | added comments read |
| 18 New code nothing uses R26 | clear | START_LINE_RE used at rebuild :112; BLOCK_RE at :111, :164 |
| Comments and docstrings C1-C3, R2 | found (C2) | promote comment and lint docstring read; no TODO added |
| Names N2, N3, N5, N6, R3 | clear | START_LINE_RE and BLOCK_RE read |
| Functions and control flow | clear | extract_outbound_links read in full |
| Tests T1, T3, T5, T6, R12-R15, T4 | found (T5, under the S2 finding) | test file 330-369, 480-569 read |
| Python PY1-PY11 | clear | read; PY9: the `kept` slice finds the real START, not the inline one |
| standards-15 verified | not fixed | Grep of wiki-reciprocate-backlinks over skills/: wiki-cycle:134, wiki-verify:90, wiki-rollback:92 |
| standards-23 verified | fixed | lint :319-322 against :352-361 |

| File | Part | Standards read depth |
|---|---|---|
| `scripts/wiki-reciprocate-backlinks.py` | 1 | in full |
| `scripts/wiki-promote.py` | 1 | in part (280-324; the changed comment at 299-305 read) |
| `scripts/wiki-lint-mechanical.py` | 1 | in part (278-369; the changed docstring read) |
| `tests/scripts/test_backlink_blocks.py` | 1 | in part (1-119, 330-369, 480-569; the added test read) |
| `skills/wiki-lint/SKILL.md`, `skills/wiki-lint/wiki-seed/wiki-lint.md`, `skills/wiki-report/SKILL.md`, `framework-docs/cycle-step-return-format.md`, `CHANGELOG.md` | 1 | in part (each changed line read) |

Every changed hunk of each file falls inside the ranges read; the lens read other lines only for context.

Well built: the line-anchored `BLOCK_RE` and `START_LINE_RE` replace the old unanchored search, the regression test pins the prose-above-block case byte for byte, and the lint docstring now names all four row kinds.

## Spec

- [important] `skills/wiki-report/SKILL.md:278`, `framework-docs/cycle-step-return-format.md:175`, `skills/wiki-lint/SKILL.md:37` — a page with a START and no END is not safe to leave for the cycle's next run, and the docs do not say so.
    - Intent: `skills/wiki-report/SKILL.md:278`: "a page listed as a block not closed, or as a block inside an unclosed code fence, needs a hand fix to the page (add the end marker, or close the fence), which no rebuild makes". `plan.md:61`: "a page with a START and no END is listed as "block not closed", never a crash".
    - Implemented: `scripts/wiki-reciprocate-backlinks.py:164` `existing_match = BLOCK_RE.search(text)`, with `BLOCK_RE` (line 61) running from a START line to the next END line. On a stray START the first run appends a block (line 186) and the next run splices from the stray line to the new END (lines 175, 179), deleting the author's text between. `skills/wiki-cycle/SKILL.md:131-135` runs the rebuild every cycle. Read from code, not run. Pre-existing: the old `START.*?END` did the same. `checkpoints.md` records this as the red-team choice 5 trade-off ("a stray START on its own line with no END can still be spliced by a second rebuild"), but the docs' "hand fix, which no rebuild makes" wording still lets the cycle's own rerun do it first.
    - Affected: any page with a stray START; its body text is deleted on the next cycle, and the lint then reads the page as clean.
    - Fix: have the rebuild skip a page whose START count exceeds its END count, and say "do not rerun" for those rows; add a test that two rebuilds keep the text below a stray START. Or record the ruling that the trade-off stands.
- [important] `scripts/wiki-lint-mechanical.py:1437` and `skills/wiki-cycle/SKILL.md:141` — the rerun advice is not scoped to extra and missing rows (sibling site of spec-9).
    - Intent: `framework-docs/cycle-step-return-format.md:175` says only extra and missing rows are "one the backlink rebuild got wrong"; `scripts/wiki-lint-mechanical.py:1446` says "block not closed (a `BACKLINKS-AUTO START` with no `END`): fix it by hand".
    - Implemented: lint:1437 "so a page listed there means the rebuild went wrong; on its own, a page listed here is one whose block is behind its links: run `wiki-reciprocate-backlinks.py`, and if it stays listed, look at the script." The cycle SKILL line 141 says "so a page it still lists means the rebuild went wrong". Both cover every row.
    - Affected: readers of the lint section and the cycle report for unclosed and in-fence rows.
    - Fix: scope both sentences to extra and missing rows, and send unclosed and in-fence rows to the hand fix.
- [important] `scripts/wiki-lint-mechanical.py:332` — the lint and the rebuild disagree on a START quoted mid-line in plain prose (spec-10, sibling site c).
    - Intent: `doubt-log.md:13`: "keeps lint and rebuild in agreement on that page". `plan.md:67`: after one rebuild the lint "lists nothing ... (the unclosed-block page aside, which stays listed)".
    - Implemented: the lint runs `if text.count(BACKLINK_START) > text.count(BACKLINK_END):` on text where only inline code is removed (lint:330, 299). The rebuild matches only line-anchored markers (`scripts/wiki-reciprocate-backlinks.py:60-61`). Prose such as "The block starts at <!-- BACKLINKS-AUTO START --> and ends ..." plus a real block is listed `unclosed` (`if me in unclosed:` at lint:352), which hides that page's extra and missing rows and gives a wrong hand-fix instruction. `scripts/_entry_checks.py:253, 261` uses a third, unanchored regex. The test at `tests/scripts/test_backlink_blocks.py:541` backticks the marker, which the lint strips, so this shape is untested. The trade-off is not recorded in `checkpoints.md`.
    - Affected: a page that quotes the marker in prose; the lint's report for it.
    - Fix: use the same line-anchored rule in the lint (and `_entry_checks.py`), or record the trade-off; add a lint test with the unticked prose.
- [important] `scripts/wiki-reciprocate-backlinks.py:60-61, 164` — an indented block is no longer matched (spec-10, point b).
    - Intent: `plan.md:52` (Invariant 2): "a notebook whose links use none of the newly read forms, none inside code and no target with whitespace gets byte-identical blocks". Indentation is not in its exclusions.
    - Implemented: `BLOCK_RE` starts `^{START}[ \t]*$`, with no leading whitespace; the removed line was `START.*?END` with DOTALL. An old block whose markers are indented is no longer found, so the rebuild appends a second block, while the lint (non-anchored, `:284`) still reads the old one and the extra row survives a rerun. That contradicts `CHANGELOG.md:17` ("a rerun of the rebuild clears only extra and missing rows"). No test has an indented marker (Grep). CRLF is unchanged: `read_text` translates and `scripts/_atomic_io.py:80` writes `newline=""`, so output is LF before and after.
    - Affected: any page whose block markers are indented; live presence unverified.
    - Fix: allow `[ \t]*` before the markers in `BLOCK_RE` and `START_LINE_RE`, or record it as a trade-off; add a test.
- [important] `plan.md:15` — "a marker quoted in code is no block" is not true for block placement (spec-10/12).
    - Intent: `plan.md:15`: "code is stripped before the page's own block is found, so a marker quoted in code is no block".
    - Implemented: `scripts/wiki-reciprocate-backlinks.py:139` reads raw text and `:164` searches it with no `strip_code`. A fenced example whose markers stand alone on their lines is matched and overwritten by the real block (`:175`). Pre-existing; this round's test covers only inline quotes.
    - Affected: a page that shows the block format in a fence.
    - Fix: run the placement search on the code-stripped view, or reword the plan to "for link reading"; add a fenced-example test.
- [suggestion] `plan.md:67` — Step 2's "aside" names only the unclosed page; an in-fence page also stays listed after one rebuild (spec-11, partly addressed). Fix: add "or the in-fence page".
- [suggestion] `scripts/wiki-lint-mechanical.py:294`, `scripts/wiki-reciprocate-backlinks.py:100` — indented fences are now in the CHANGELOG (spec-13 addressed), but no test has one (Grep for leading-space fences finds none). Fix: one lint and one rebuild test with an indented fence.
- [nit] `tests/scripts/test_backlink_blocks.py:540` — the name `..._quoted_inline_twice` does not say it means two rebuilds. Fix: rename it (same point as the Standards nit).

Unverified:
- Whether any live notebook has an indented marker or a stray START (the Grep covered this repo only).
- That the new test fails on the pre-fix rebuild: by reading the removed `re.search(START.*?END, text, DOTALL)`, `startswith(kept)` would fail; not run.
- The second-rebuild splice (first finding): read from `scripts/wiki-reciprocate-backlinks.py:164-186`, not run.
- `CHANGELOG.md:17` "the old rule read one with a space": needs `git show 043937e:scripts/wiki-reciprocate-backlinks.py`.
- The dry-run counts in CHANGELOG and checkpoints, and the suite counts (59/59 etc.): not run.
- `scripts/_entry_checks.py:253` (unchanged): unanchored; whether it should match the rebuild is outside this diff.

Checks made:
- spec-9 wording at the four named docs now splits extra/missing (rerun) from unclosed/in_fence (hand fix): done in `skills/wiki-report/SKILL.md:278`, `framework-docs/cycle-step-return-format.md:175`, `skills/wiki-lint/SKILL.md:37`, `skills/wiki-lint/wiki-seed/wiki-lint.md:28`; the siblings left are the first two findings above.
- spec-10 (a): a line-anchored real block is found and placed as before (`scripts/wiki-reciprocate-backlinks.py:135-198` read).
- spec-11: `plan.md:17` and `requirements.md:28` name the `in_fence` row and match `scripts/wiki-lint-mechanical.py:352-356`.
- spec-12: the link-rule order in `plan.md:15` (code first, then the block) matches both scripts for link reading (lint `:288-300`, rebuild `:109-111`); placement is the fifth finding above.
- spec-13: CHANGELOG says a fence line may be indented, matching `lstrip()` in the lint (`:294`) and the rebuild (`:100`).
- CHANGELOG lines 14-17 read sentence by sentence: all match the code except "a rerun of the rebuild clears only extra and missing rows" (fourth finding).

| Item | Verdict | Search / read |
|---|---|---|
| spec-9 wording (four docs) | found | Grep `hand fix`, `rerun`, `went wrong`, `got wrong`, `left out of step`, `look at the script`, `block not closed`, `in_fence`, `unclosed code fence` over skills/, framework-docs/, CHANGELOG.md; hits read |
| spec-9 claim "a rerun clears only extra and missing rows" | found | rebuild `:164-186` read; the indented case keeps the extra row |
| spec-10 (a) real block found and placed | clear | `:135-198` read |
| spec-10 (b) CRLF, indentation | found (indentation); CRLF clear | `_atomic_io.py:70-98` read |
| spec-10 (c) lint and rebuild agreement | found | Grep `BACKLINKS-AUTO`, `_BACKLINKS_RE` over scripts/ |
| spec-10 new test, red-first | unverified | test `:540-553` read; not run |
| second rebuild on a stray START | found | `:164-186` read; not run |
| spec-11 | clear (lint bullet, Decision 1); Step 2 partly (suggestion) | `plan.md:17`, `requirements.md:28`, lint `:352-356, 1446-1448` |
| spec-12 | found (placement); order clear | `plan.md:15` read |
| spec-13 | clear (CHANGELOG, `lstrip`); test gap (suggestion) | Grep indented fences in tests: none |
| CHANGELOG 14-17 | clear except one sentence | read `:12-17`; Grep `backlink_blocks_out_of_step`, `backlink_blocks` |

| File | Part | Spec read depth |
|---|---|---|
| `scripts/wiki-reciprocate-backlinks.py` | 1 | in full |
| `scripts/wiki-promote.py` | 1 | in part (298-307; the changed comment read) |
| `scripts/wiki-lint-mechanical.py` | 1 | in part (270-362, 1415-1470; the changed docstring read) |
| `tests/scripts/test_backlink_blocks.py` | 1 | in part (1-85, 520-569; the added test read) |
| `CHANGELOG.md`, `skills/wiki-lint/SKILL.md`, `skills/wiki-lint/wiki-seed/wiki-lint.md`, `skills/wiki-report/SKILL.md`, `framework-docs/cycle-step-return-format.md` | 1 | in part (each changed line read) |
| `plan.md`, `requirements.md`, `checkpoints.md`, `doubt-log.md`, `review-findings.md` | — | in full |

Well built: the line-anchored markers stop a quoted inline START from splicing the prose above a real block, and the lint's `in_fence` row is pinned by tests.

## Change risk

| File | Risk | Part | Standards | Spec | Change risk |
|---|---|---|---|---|---|
| `scripts/wiki-reciprocate-backlinks.py` | MEDIUM (rewrites wiki pages in place; business logic) | 1 | in full | in full | — |
| `scripts/wiki-lint-mechanical.py` | MEDIUM (docstring only in this round) | 1 | in part (changed lines read) | in part (changed lines read) | — |
| `scripts/wiki-promote.py` | LOW (comment) | 1 | in part (changed lines read) | in part (changed lines read) | — |
| `tests/scripts/test_backlink_blocks.py` | LOW (tests) | 1 | in part (changed lines read) | in part (changed lines read) | — |
| `CHANGELOG.md`, `framework-docs/cycle-step-return-format.md`, `skills/wiki-lint/SKILL.md`, `skills/wiki-lint/wiki-seed/wiki-lint.md`, `skills/wiki-report/SKILL.md` | LOW (docs) | 1 | in part (changed lines read) | in part (changed lines read) | — |

No high-risk file (no auth, sessions, tokens, crypto, payments, external call, data migration or removed validation), so the change-risk lens was not run. Files the earlier rounds reviewed and this fix did not touch are out of the round; nothing new was raised in them.

## Needs-a-human

none (no auth, authz, token or session handling, or production-data migration finding; a spec resolved, so no no-spec line).

## Summary

Standards: 3 findings (2 suggestions, 1 nit; worst: the `wiki-promote.py` comment still names /wiki-cycle as the only other caller of the rebuild, while wiki-verify and wiki-rollback run it too, so standards-15 is not fixed). Spec: 8 findings (5 important, 2 suggestions, 1 nit; worst, in order of the report: a stray START page can still lose its text to the cycle's next rebuild while the docs say it needs a hand fix; the rerun advice in the lint report and the cycle skill is not scoped to extra and missing rows; the lint and the rebuild disagree on an unticked mid-line START; an indented block is no longer matched by the rebuild; the plan's "a marker quoted in code is no block" does not hold for placement). Change risk: not run. The axes agree on the lint/rebuild marker rule differing (Standards S2, Spec spec-10c) and on the test name. Of the addressed items, standards-23, spec-11 (lint bullet and Decision 1), spec-12 (link reading) and spec-13 (CHANGELOG) hold; spec-9 is done at its four named docs but its siblings and its claim "a rerun clears only extra and missing rows" are not; spec-10 fixes the reported inline-quote case and opens the cases above. Worth acting on the Spec important findings before the install.

Risks or assumptions: the lenses ran on the default tier and came back as launch notices that I waited out; nothing was run (no tests), so the stray-START splice, the indented-block case and the red-first claim for the new test rest on reading the code; several files are `in part` because the lenses read the changed hunks and context, not the whole file.

VERDICT: Standards FINDINGS · Spec FINDINGS · Change risk NOT RUN · needs-a-human 0
