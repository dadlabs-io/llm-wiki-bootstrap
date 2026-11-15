# Review report, round 6 (focused, confirming) - 240-backlink-block-check

Fixed point `f9b3aa200a86ce60716ce42dae48b6cff1022f88` (resolves). Change under review: the diff from `763e3b2` to the working tree for the four files in `round6-changed.txt` (CHANGELOG.md 1+1, scripts/wiki-lint-mechanical.py 6+5, scripts/wiki-reciprocate-backlinks.py 8+5, tests/scripts/test_backlink_blocks.py 56+0; 82 changed lines by `git diff --numstat`), plus sibling sites of each addressed finding (the other copy of the line-split and the inline-code strip; other `splitlines()` and inline-strip uses in `scripts/`; the docs that carried the old "no skip logic" claim). One part per axis. Spec source: `plan.md`, `requirements.md`, `checkpoints.md` (Review round 5 and Fix round 5 whole), `doubt-log.md` (Fix round 5 block), `name-review.md` (last block), `review-report-round-5.md`. The prescan ran clean, so the Standards lens skipped review ids, dates and width in Python comments. Both lenses ran as unnamed `code-reviewer-lens` spawns with `run_in_background: false` written out; the harness ran them in the background anyway and I waited for their reports. Both ran on the default tier. Recorded trade-offs were not re-raised (a fenced END between a START and its END; `START / START / END / END` paired; `_entry_checks.py`'s unanchored regex; the four-backtick fence case; spec-30). Files the earlier rounds reviewed and this fix did not touch are out of the round. Nothing was run: the producer's counts (test_backlink_blocks 99/99, the invariant files, check-freeze, prescan) are unverified here.

## Standards

- [important] G16 / S1 `tests/scripts/test_backlink_blocks.py:625` - the second separator in `for sep in ("\x0c", ...)` is a literal U+2028 character that shows as a plain space in an editor or diff; if any tool normalises it to a space, the test goes vacuous (a space is no `str.splitlines()` separator, so the old lint would pass too), and the check label already needed `unicode_escape` to be readable.
    - Evidence: Grep and a count of the character in the file find exactly one, at line 625; the form feed beside it is written as an escape.
    - Fix: write the separator as the escape `" "`, matching `"\x0c"`.
- [suggestion] S1 / N3 `tests/scripts/test_backlink_blocks.py:486` and `:651` - `STRAY = "<!-- BACKLINKS-AUTO START -->"   # a START and no END` is reused in the Trace B test as `"`note` " + STRAY + ...`, where the test itself asserts the line is no START at all, so the name and its comment say the opposite of the use.
    - Fix: a second constant for the bare marker text, or inline the marker in that test.

Unverified:
- A decoding difference outside the changed lines: the lint reads pages with `errors="replace"` (`wiki-lint-mechanical.py:348`), the rebuild strictly (`wiki-reciprocate-backlinks.py:160`). Not a line-split difference; whether the lint should match is a decision for a person.
- The producer's test counts and check-freeze result: nothing was run.

Checks made:
- standards-32 holds: no `splitlines()` on the backlink path of either script. The lint uses `split("\n")` at `:297` and `:317`, the rebuild's `fence_walk` at `:105`; both read with `read_text`, so newline translation is the same. The remaining `splitlines()` hits in the lint (`:70`, `:105`, `:240`, `:436`, `:445`, `:741`) feed other checks.
- standards-33 holds, for the right reason: without the guard, `find_block` (`:148-155`) would find the real block above the fence and rewrite the stale `old.md` line, changing the bytes; the page stays identical only because `rewrite_backlinks_section` returns at `:192`.
- The Trace A, Trace B and link-below tests each fail on the pre-fix code for the reason they name; no wrong-reason pass found.
- standards-15 still holds: `wiki-promote.py:301-304` names `/wiki-cycle`, `/wiki-verify` and `/wiki-rollback`, and `skills/wiki-cycle`, `skills/wiki-verify`, `skills/wiki-rollback` each hold a `SKILL.md`.

| Rule / section | Verdict | Search |
|---|---|---|
| S1, N1, N3 | found | the U+2028 literal; the STRAY reuse |
| S2 | clear | lint `backlink_split` against the rebuild's `strip_code` and `fence_walk` compared line by line |
| S3-S12 | clear | no class or hook added; changed functions read in full |
| G25 | clear | literals read in context |
| F3, R1, N7 | clear | `backlink_split` and `strip_code` read in full |
| C5 | clear | no commented-out code |
| C1-C3, R2 | clear | each changed comment and docstring read against its code |
| N2, N5, N6, R3 | clear | new names and `END_MARKER` read against scope |
| Functions rows | clear | changed bodies read |
| G3, G33, G26, G2 | clear | empty, no-fence and trailing-fence inputs traced |
| T1, T3, T5, T6, R12-R15, T4 | clear | every new test read |
| PY7-PY11 | clear | no new import; plain functions with the file's `check` helper |
| R26 | clear | the new tests are collected by the file's `run_all` discovery |

| File | Part | Standards read depth |
|---|---|---|
| `scripts/wiki-lint-mechanical.py` | 1 | in part (275-385; every changed line) |
| `scripts/wiki-reciprocate-backlinks.py` | 1 | in part (1-230, 290-310; every changed line) |
| `tests/scripts/test_backlink_blocks.py` | 1 | in part (1-60, 330-360, 440-765; every changed line) |
| `CHANGELOG.md` | 1 | in part (10-20; every changed line) |
| `scripts/wiki-promote.py` | sibling | in part (290-314) |

Well built: the lint's marker, fence and inline-code rule is written apart from the rebuild's, and each new test fails on the pre-fix code for the reason it names.

## Spec

- [suggestion] `scripts/wiki-lint-mechanical.py:305` and `scripts/wiki-reciprocate-backlinks.py:121` - a link written inside a double-backtick code span still counts, in both scripts (pre-existing: the same regex stripped to `""` before; the replacement line is in this diff).
    - Intent: `plan.md` line 63, "a link inside inline code, inside a ``` or ~~~ fence, or after an unclosed fence does not [count]".
    - Implemented: `re.sub(r"`[^`\n]*`", "x", line)` pairs the first two backticks of a double-backtick span as an empty span, so the text becomes `x[B](b.md)x` and the link regex reads `b.md`. Both scripts agree, so no lint row flags it; the target's block just gains a line.
    - Affected: a page that shows link syntax in double-backtick code gains a backlink in the target's block.
    - Fix: match the closing run to the opening run's length (for example `(`+)(.+?)(?<!`)\1(?!`)`, untested; check it first) in both scripts, with a test, keeping `test_lint_reads_a_link_on_a_line_starting_with_a_double_backtick_span` green.
- [nit] `scripts/wiki-lint-mechanical.py:305` and `scripts/wiki-reciprocate-backlinks.py:121` - the placeholder `x` can turn a code span into a link target, which the old `""` could not.
    - Intent: `plan.md` line 15, inline code is "removed".
    - Implemented: `[B](`b`.md)` becomes `[B](x.md)`, which the link regex reads as a link to `x.md`; with `""` it was `](.md)`, which matches nothing.
    - Affected: only a notebook with a page named `x.md` in the entry set, linked this way; contrived.
    - Fix: a placeholder that is non-space, absent from the marker text and outside the link regex's target class `[^()\s#]` (for example `(`); check it against the marker-equivalence trace before adopting it.

Unverified:
- Whether CommonMark renders `[B](`b`.md)` or a double-backtick link as a link: not run; the two findings rest on the regex trace.
- Whether any notebook page uses a double-backtick link or a glued span: the repo's `*.md` hold only script docstrings; the notebooks were not searched.
- Test counts and red-on-old status: traced, not run.

Checks made:
- spec-29 holds: every line split on the backlink path of both scripts is at `\n` (lint `:297`, `:306`, `:317`; rebuild `:105`, `:147` with `len(line) + 1`), the MULTILINE anchors match only at `\n`, and both read pages with `read_text`, so the newline translation is the same.
- spec-27 holds for marker lines: a raw marker line holds only whitespace and the marker text, no backtick, so the strip leaves it unchanged; a line with a span gains an `x`, which a marker line cannot hold. Walked: unpaired backtick, whole-marker span, two spans, empty span, fence line, indented, tab.
- Trace A, Trace B and link-below: each is red on the old `""` strip and green on the new, by trace (A: the old lint paired an END that the rebuild did not; B: the old lint saw an open START; link-below: the old stray cut dropped the link). Trace B's rebuild assertions were already green on old code; its lint assertion is the red one.
- standards-33, spec side: removing `if unclosed: return True` (`:131-132`) lets `find_block` rewrite the stale block, so the byte-identical assertion fails; the lint row is `in_fence`.
- spec-28 holds: the skip returns at `:192-193` before `atomic_write_text`; for every skipped page the lint lists a row (`unclosed` at `:350`, `in_fence` at `:352`); the module docstring, the report line (`:300`) and CHANGELOG line 17 match the code; `"skipped": []` stays empty in the JSON, which "none listed" does not contradict. Grep for "deterministic" and "no skip logic" finds no other text saying the rebuild does not skip.
- spec-1 still holds (an unclosed fence before the block gives the `in_fence` row; a quoted START fails the rebuild's whole-line rule).
- spec-9 still holds (wiki-lint, wiki-report, wiki-cycle SKILL.md, the contract doc and the lint text send extra/missing to a rerun and unclosed/in_fence to a hand fix; the inline-code marker exception is now closed).
- spec-10 still holds (a START quoted mid-line is prose to the rebuild).
- spec-14 still holds (a START with no END is never rewritten: `:192-193`, `:163-165`).
- spec-15 still holds (the rerun advice is scoped to extra/missing rows).
- spec-16 now holds in full: one marker rule in both scripts, the backticked-marker shape from round 5 is fixed.

| Item | Verdict | Search / read |
|---|---|---|
| spec-29 line split | clear | callers of the backlink helpers by Grep; both read paths traced |
| spec-27 marker equivalence | clear | regexes `:286-287` and `:63-64`; strip at `:305` and `:121`; shapes listed |
| spec-27 link side | found (nit, suggestion) | trace of `:305`, `:121`, `:290` |
| Traces A, B, link-below | clear | traced against old and new code |
| standards-33, spec side | clear | `:131-132`, `:148-154`, `:352-353` |
| spec-28 skip, docs | clear | `:192-193`, `:313-322`, `:350-352`; Grep for the old wording |
| spec-1, 9, 10, 14, 15, 16 | clear | see Checks made |

| File | Part | Spec read depth |
|---|---|---|
| `scripts/wiki-reciprocate-backlinks.py` | 1 | in full |
| `scripts/wiki-lint-mechanical.py` | 1 | in part (270-391, 1435-1484; every changed line) |
| `tests/scripts/test_backlink_blocks.py` | 1 | in part (1-99, 325-675; every changed line) |
| `CHANGELOG.md` | 1 | in part (8-21; every changed line) |
| `plan.md`, `requirements.md`, `checkpoints.md`, `doubt-log.md`, `name-review.md`, `review-report-round-5.md` | - | in full |
| SKILL.md files of wiki-lint, wiki-report, wiki-cycle; `framework-docs/cycle-step-return-format.md` | sibling | in part (cited lines) |

Well built: the marker rule is one regex and one rule in both scripts, and each new test traces to a specific old-code failure.

## Change risk

| File | Risk | Part | Standards | Spec | Change risk |
|---|---|---|---|---|---|
| `scripts/wiki-reciprocate-backlinks.py` | MEDIUM (rewrites wiki pages in place; business logic) | 1 | in part (every changed line) | in full | - |
| `scripts/wiki-lint-mechanical.py` | MEDIUM (check logic) | 1 | in part (every changed line) | in part (every changed line) | - |
| `tests/scripts/test_backlink_blocks.py` | LOW (tests) | 1 | in part (every changed line) | in part (every changed line) | - |
| `CHANGELOG.md` | LOW (docs) | 1 | in part (every changed line) | in part (every changed line) | - |

No high-risk file (no auth, authz, sessions, tokens, crypto, payments, external call, data migration or removed validation), so the change-risk lens was not run.

## Needs-a-human

none (no auth, authz, token or session handling, or production-data migration finding; a spec resolved, so no no-spec line).

## Summary

Standards: 2 findings (1 important, 1 suggestion; worst: the line-split test's second separator is an invisible literal U+2028 character, so a tool that turns it into a space makes the test pass vacuously). Spec: 2 findings (1 suggestion, 1 nit; worst: a link inside a double-backtick span is still read in both scripts, a pre-existing shape the diff leaves in place). The axes do not overlap. All five confirmations hold: standards-32 / spec-29 (both scripts split at `\n` only), spec-27 (both strips use `x`; the three new tests are each red on the old strip), standards-33 (the two-rebuild test fails if the guard branch goes), spec-28 (docstring, report line and CHANGELOG are true to the code), and the earlier verdicts spec-1, 9, 10, 14, 15, 16 and standards-15 still hold. Advice: the important Standards finding is a one-token fix worth making before the install; the two Spec items are small and the double-backtick shape is pre-existing.

Risks or assumptions: both lenses ran on the default tier and read the test file and the lint in part (every changed line in full, as the file table shows); nothing was run, so the producer's counts are unverified here; the notebooks were not searched for double-backtick links.

VERDICT: Standards FINDINGS · Spec FINDINGS · Change risk NOT RUN · needs-a-human 0
