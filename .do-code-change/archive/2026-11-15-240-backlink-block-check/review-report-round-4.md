# Review report, round 4 (focused) — 240-backlink-block-check

Fixed point `f9b3aa200a86ce60716ce42dae48b6cff1022f88` (resolves). Change under review for the lenses: the fix round's diff, commit `91d4c31` to HEAD, for the seven files in `round4-changed.txt` (CHANGELOG.md, scripts/wiki-lint-mechanical.py, scripts/wiki-promote.py, scripts/wiki-reciprocate-backlinks.py, skills/wiki-cycle/SKILL.md, skills/wiki-report/SKILL.md, tests/scripts/test_backlink_blocks.py; 142 added, 24 removed lines by `git diff --numstat`), plus sibling sites of the addressed findings (`scripts/_entry_checks.py:251-269`). One part per axis, far under 3,000 lines. `git status --short` shows no untracked files (only the run's own `readonly-review.json`). Spec source: `plan.md`, `requirements.md`, `checkpoints.md`, `doubt-log.md`, `review-findings.md` (round 3). The prescan ran clean, so the Standards lens skipped dates, review ids and width in Python comments. The lenses ran as unnamed `code-reviewer-lens` spawns with `run_in_background: false` written out; the harness returned launch notices and I waited for their reports. The Spec lens ran one tier up (sonnet) because the round turns on a hand trace of the rebuild over two runs. Items left in earlier rounds (standards-26 / spec-21, standards-16..22) were not re-raised. Nothing was run: no tests.

## Standards

- [important] G2/C2 `scripts/wiki-reciprocate-backlinks.py:117-119` with `:191-214` — this round's `find_block` makes the rebuild append a new backlink block on every run to a page whose block sits inside an unclosed code fence, and three texts say the rebuild leaves such a page alone.
    - Trace: `strip_code` drops every line after an unclosed fence opener, so the guard at `:164-166` counts 0 STARTs and 0 ENDs and passes; `find_block` marks every later line as fenced (`elif in_fence: fenced_at.add(offset)`), skips the START, returns None, and the else branch (`new_text = text + "\n" + new_block + "\n"`) appends another block. The removed `BLOCK_RE.search(text)` ran on raw text and replaced that block in place, so this is a regression from this fix. Read from code, not run (I traced it independently and reached the same result).
    - False texts: `scripts/wiki-lint-mechanical.py:1445-1446` "(the rebuild leaves such a page alone)"; `skills/wiki-cycle/SKILL.md:141` "the rebuild leaves it alone"; `skills/wiki-report/SKILL.md:278` covers only the not-closed page, but its sentence on in-fence pages says "no rebuild makes" a fix. `wiki-promote.py` runs the rebuild on every wrap-up, so the growth also happens there.
    - Tests: `test_backlink_blocks.py:453-459` runs one rebuild only; `:635-640` (R13) pins the false sentence by wording.
    - Fix: return early from `rewrite_backlinks_section` when a START line sits inside an unclosed fence (as the START guard does), so the docs become true; add a two-rebuild test for an in-fence page.
- [important] G3/G26/T5/T6 `scripts/wiki-reciprocate-backlinks.py:164-166` — the guard's comment says "a START with no END" but it compares line counts, so order is ignored. Page `X / END / Y / START / Z` has counts 1/1, passes, the first run appends a block, and the second run's `find_block` takes the orphan START through the appended END and deletes `Y`..`Z`; the lint (`wiki-lint-mechanical.py:337`) compares counts too and lists no row. `test_rebuild_leaves_a_page_with_a_stray_start_untouched_over_two_rebuilds` (`:571`) covers only START-before-END. Fix: guard on "a START outside a fence with no END after it" (`find_block` None while such a START exists), the same order-aware test in the lint, and this page in the test.
- [suggestion] S2 `scripts/wiki-reciprocate-backlinks.py:101` against `:115` — `strip_code` walks `text.splitlines()`, `find_block` walks `text.split("\n")`; they disagree on fences after `\x0c` or similar line breaks. Fix: one fence walk that yields per-line flags, used by both.
- [suggestion] S2/S5 `scripts/_entry_checks.py:253` — `_BACKLINKS_RE` (and `body.find(_BACKLINKS_END)` at `:268`) is a third, unanchored copy of the marker rule, a sibling of the rule this round line-anchored in both scripts; `_strip_footer` (`:261`) would cut a mid-line quoted START through the real END. Fix: anchor it (or share one pattern), or record the trade-off.
- [nit] G19/N1 `scripts/wiki-reciprocate-backlinks.py:121-122` — `for start in START_LINE_RE.finditer(text)` binds a Match named `start`, and `text.rfind("\n", 0, start.start()) + 1` is an unnamed line start. Fix: `for match in ...` and `line_start = text.rfind("\n", 0, match.start()) + 1`.

Unverified:
- `find_block:124` searches the END on raw text, so a fenced END between a real START and its real END ends the block early (the checkpoints record it as known; it is only reachable with a real END elsewhere, since the guard counts prose only). Not traced through the lint, not run.
- Whether any real page holds `\x0c` or `U+2028` before a fence (for the splitlines suggestion).
- The producer's claims: test_backlink_blocks 75/75, the four invariant files green, check-freeze PASS. Nothing was run here.

Checks made:
- standards-24 (the `wiki-promote.py` comment): fixed. `wiki-verify` and `wiki-rollback` both call the rebuild (Grep over `skills/`); the new comment names them with `/wiki-cycle`.
- The three anchored regexes in the diff (`START_LINE_RE`, `END_LINE_RE`, `BLOCK_RE` in the rebuild; the three `BACKLINK_*_LINE_RE` in the lint) read the same rule.

| Rule / section | Verdict | Search |
|---|---|---|
| 1 S1/N1 | found (nit) | `start` is a Match in `find_block` |
| 2 S2/G5 | found | fence walks in `strip_code` and `find_block`; `_entry_checks.py:253` |
| 3 S3/G14 | clear | changed functions read |
| 4 S4 | clear | added lines read |
| 5 S5 | found | the marker rule validated by three regexes (the S2 sibling above) |
| 6 S6/G23 | clear | Grep `in_fence`, `fenced` in both scripts |
| 7 S7 | clear | edits stay in the two scripts and docs; the third copy is S2 |
| 8 S8 | clear | read |
| 9 S9 | clear | no new interface |
| 10 S10 | clear | added lines read |
| 11 S11 | clear | no new class |
| 12 S12 | n/a | no subclass |
| 13 G25 | clear | literals in added lines |
| 14 F3/G15 | clear | signatures read |
| 15 R1 | clear | `find_block` only reads; the write is pre-existing |
| 16 N7/G20 | clear | names match bodies |
| 17 C5 | clear | added comments read |
| 18 R26 | clear | `find_block` has one caller (`:191`); `BLOCK_RE` still used at `:134` |
| Comments C1-C3, R2 | found (C2) | lint `:1445-1446`, wiki-cycle `:141` |
| Names N2-N6, R3 | clear | read in context |
| Functions S13-G16, S15 | clear | `find_block`, guard and lint hunks read |
| Boundary G3, G26, G2 | found | findings 1 and 2 |
| Tests T1, T3, T5, T6, R12-R15, T4 | found (T5, T6, R13) | test file read in full |
| Python PY1-PY11 | clear / n/a | no casts, dicts, async, third-party imports; PY9 assertions are on produced text |

| File | Part | Standards read depth |
|---|---|---|
| `scripts/wiki-reciprocate-backlinks.py` | 1 | in full |
| `tests/scripts/test_backlink_blocks.py` | 1 | in full |
| `scripts/wiki-lint-mechanical.py` | 1 | in part (270-345, 1425-1465; every changed line) |
| `scripts/wiki-promote.py` | 1 | in part (295-310; the changed comment) |
| `CHANGELOG.md`, `skills/wiki-cycle/SKILL.md`, `skills/wiki-report/SKILL.md` | 1 | in part (each changed line) |

Well built: one anchored marker rule in both scripts, `find_block` skipping a closed fence's example, and a byte-for-byte test matrix for the fence, indent and quoted-marker cases.

## Spec

- [important] `scripts/wiki-reciprocate-backlinks.py:164-166, 109-127, 209-214` — the rebuild does not leave an in-fence page alone: it appends a block each run, against the docs and the CHANGELOG.
    - Intent: `scripts/wiki-lint-mechanical.py:1445-1446`, "A block not closed, or inside an unclosed code fence, needs a hand fix to the page (the rebuild leaves such a page alone)"; the same claim at `skills/wiki-cycle/SKILL.md:141`; `CHANGELOG.md:17` "a rerun of the rebuild clears only extra and missing rows"; `plan.md:52` Invariant 2, "placement ... unchanged".
    - Implemented: the guard counts on `strip_code(text)` (0 to 0 for this page), `find_block` skips the fenced START and returns None, and the append branch runs. Trace for page `B` = `"```\nnever closed"` linked from A: before, no block; after rebuild 1, one block after the fence (the premise `test_backlink_blocks.py:453-457` asserts); after rebuild 2, a second; after rebuild 3, a third; the lint row stays `in_fence`. An unlinked in-fence page is unchanged. Read from code, not run.
    - Affected: any linked page with an unclosed fence; it gains a block per cycle (and per wrap-up) until someone closes the fence, then holds stale duplicates. Before this fix round the old `BLOCK_RE.search(text)` replaced the block in place.
    - Fix: extend the guard to skip a page with a START line inside an unclosed fence, or change the three sentences to say what the rebuild does; add a two-rebuild test for an in-fence page.
- [important] `scripts/wiki-reciprocate-backlinks.py:165` — the spec-14 guard counts lines and ignores order, so the text-loss it was written for remains for a page whose END comes before a START that has no END.
    - Intent: `CHANGELOG.md:17`, "a page with more start lines than end lines is left untouched by the rebuild (it once appended a block and spliced the text away on the next run)"; `plan.md:64` "a page with a START and no END is listed as "block not closed", never a crash".
    - Implemented: text `END ... prose ... START` has 1 START, 1 END, so the guard passes; `find_block` finds no END after the START and returns None; rebuild 1 appends a block; the page now reads START, START, END, END; rebuild 2 passes the guard (2 to 2), `find_block` takes the stray START with the appended END, and line 203 replaces everything between with the new block. The lint reads the page clean after rebuild 1. Read from code, not run.
    - Affected: a page with a stray START after an END; its text between is deleted on the second cycle.
    - Fix: guard on pairing (a START outside a fence with no END after it, or `find_block` None while a START line exists outside fences), and the same in the lint; add the END-then-START two-rebuild test (`:571` covers only a lone START).
- [suggestion] `tests/scripts/test_backlink_blocks.py:635-640` and `scripts/wiki-lint-mechanical.py:1443-1446` — `test_report_scopes_the_rerun_advice_to_pages_listed_by_content` pins the sentence "(the rebuild leaves such a page alone)", which is false for in-fence pages (first finding). Fix: update the assertion with the claim when it is corrected.
- [suggestion] `scripts/_entry_checks.py:253, 261, 268` — a sibling of spec-16 left inconsistent with the line rule.
    - Intent: round 3's spec-16 fix text, "use the same line-anchored rule in the lint (and `_entry_checks.py`), or record the trade-off".
    - Implemented: `_BACKLINKS_RE = re.compile(re.escape(_BACKLINKS_START) + r".*?" + re.escape(_BACKLINKS_END), re.DOTALL)` and `body.find(_BACKLINKS_END)`; no trade-off is recorded in `checkpoints.md` and the file is outside the plan's Scope.
    - Affected: a page that quotes a marker mid-line has prose cut from the entry checks' view and `layout_errors` can read a quoted END as the block's end; read-only checks, so no text is lost.
    - Fix: record the trade-off, or anchor the regex and add a test.
- [nit] `scripts/wiki-reciprocate-backlinks.py:124` — an END inside a fence between a block's START and its END still ends the block there; `checkpoints.md` records it as known, with no test. Fix: record it as a trade-off in the plan or add a test.

Unverified:
- All traces are from code, not run, including the first two findings.
- Exotic line breaks (`\x0c`, `U+2028`) make `splitlines` in `strip_code` and `split("\n")` in `find_block` differ; not traced.
- The producer's claims 75/75, the four invariant files, check-freeze PASS, and the CHANGELOG dry-run counts.

Checks made:
- spec-15 (rerun advice scoped): the lint text names extra/missing for the rerun and the other rows for a hand fix, the cycle skill line matches; the sentence "leaves such a page alone" is false only for the in-fence row (first finding).
- spec-16 (lint and rebuild agree): the same `[ \t]*` line rule at lint `:286-287` and rebuild `:61-62`; a mid-line START is ignored by both; closed and unclosed fence lines are dropped by both.
- spec-17 (indented block found): `test_rebuild_finds_a_block_with_indented_markers` and the lint test read; a tab- or space-indented block is matched.
- spec-18 (a fenced example left as written): `find_block` returns the first START outside a closed fence; a page whose only START is in a closed fence returns None, so a block is appended outside the fence; `test_rebuild_replaces_the_real_block_below_a_block_example_in_a_code_fence` checks bytes.
- spec-19 (`plan.md:67` aside) and spec-20 (the indented-fence tests): both read as fixed.
- Invariant 2: `GOLDEN_BLOCK` test (`:442`) and the code read; `find_block` and the guard change nothing for an ordinary block.
- `CHANGELOG.md:17` read sentence by sentence: all match the code except the guard sentence for an END-before-START page (second finding) and the in-fence sentence "a rerun of the rebuild clears only extra and missing rows" read against the append (first finding).

| Item | Verdict | Search / read |
|---|---|---|
| A extra / missing rows, two rebuilds | clear | block replaced, rebuild 2 a no-op |
| A unclosed row, two rebuilds | clear | guard returns unchanged twice (test `:571`) |
| A in_fence row, two rebuilds | found | `:109-127, 164-166, 209-214` traced |
| B guard completeness (END before START) | found | traced over two rebuilds |
| C lint and rebuild agree | clear for the two scripts; `_entry_checks` suggestion | lint `:286-287`, rebuild `:61-62`; Grep `BACKLINKS-AUTO` over `scripts/` |
| D spec-17 / spec-18 | clear; fenced-END nit | tests `:556, :606` |
| E spec-15, 19, 20 | clear except the "leaves alone" claim | lint `:1443`, plan `:67`, tests `:621-632` |
| F CHANGELOG line 17 | found (two sentences) | read against the code |
| G tests prove their claims | found | `:453` one rebuild; no END-then-START test; `:635-640` pins a false sentence |
| H Invariant 2 | clear | `:442` and the code |

| File | Part | Spec read depth |
|---|---|---|
| `scripts/wiki-reciprocate-backlinks.py` | 1 | in full |
| `scripts/wiki-lint-mechanical.py` | 1 | in part (270-380, 1415-1465) |
| `scripts/_entry_checks.py` | 1 (sibling) | in part (251-275) |
| `tests/scripts/test_backlink_blocks.py` | 1 | in part (1-120, 420-679) |
| `CHANGELOG.md`, `skills/wiki-cycle/SKILL.md`, `skills/wiki-report/SKILL.md` | 1 | in part (changed lines; the two SKILL lines by Grep hit) |
| `scripts/wiki-promote.py` | 1 | not read by the Spec lens (a comment only; read by Standards) |
| `plan.md`, `requirements.md`, `doubt-log.md`, `checkpoints.md`, `review-findings.md` | — | in full |

Well built: the one `[ \t]*` line rule is identical in both scripts, and the stray-START and fenced-example tests check bytes across two rebuilds.

## Change risk

| File | Risk | Part | Standards | Spec | Change risk |
|---|---|---|---|---|---|
| `scripts/wiki-reciprocate-backlinks.py` | MEDIUM (rewrites wiki pages in place; business logic) | 1 | in full | in full | — |
| `scripts/wiki-lint-mechanical.py` | MEDIUM (check logic and report text) | 1 | in part (changed lines) | in part (changed lines) | — |
| `scripts/wiki-promote.py` | LOW (comment) | 1 | in part (changed lines) | not read | — |
| `tests/scripts/test_backlink_blocks.py` | LOW (tests) | 1 | in full | in part | — |
| `CHANGELOG.md`, `skills/wiki-cycle/SKILL.md`, `skills/wiki-report/SKILL.md` | LOW (docs) | 1 | in part (changed lines) | in part (changed lines) | — |

No high-risk file (no auth, sessions, tokens, crypto, payments, external call, data migration or removed validation), so the change-risk lens was not run. Files the earlier rounds reviewed and this fix did not touch are out of the round; nothing new was raised in them.

## Needs-a-human

none (no auth, authz, token or session handling, or production-data migration finding; a spec resolved, so no no-spec line).

## Summary

Standards: 5 findings (2 important, 2 suggestions, 1 nit; worst: this fix makes the rebuild append a new backlink block on every run to a page whose block sits inside an unclosed fence, while the lint text and the cycle skill say it leaves such a page alone). Spec: 5 findings (2 important, 2 suggestions, 1 nit; worst, in report order: the same in-fence append, which contradicts the docs and CHANGELOG; the START/END guard counts lines and ignores order, so a page with an END before a stray START still loses its text on the second rebuild). Change risk: not run. The axes agree on both important findings, on the unanchored sibling regex in `_entry_checks.py`, and on the test that pins the false sentence. Of the addressed items, standards-24, spec-15 (except the in-fence clause), spec-16 (the two scripts), spec-17, spec-18, spec-19 and spec-20 hold; spec-14 is fixed for a lone START but not for an END before it. Worth acting on both important findings before the install, with a two-rebuild test for each.

Risks or assumptions: the Spec lens ran one tier above the default; the Standards lens ran on the default tier; both returned as launch notices that I waited out. Nothing was run, so every trace, including the two important ones, rests on reading the code (I traced both myself before the lenses reported and reached the same result). Several files are `in part` because the lenses read the changed hunks and context.

VERDICT: Standards FINDINGS · Spec FINDINGS · Change risk NOT RUN · needs-a-human 0
