# Review report, round 5 (focused, confirming) — 240-backlink-block-check

Fixed point `f9b3aa200a86ce60716ce42dae48b6cff1022f88` (resolves). Change under review for the lenses: the diff from commit `c6289bc` to HEAD for the four files in `round5-changed.txt` (CHANGELOG.md, scripts/wiki-lint-mechanical.py, scripts/wiki-reciprocate-backlinks.py, tests/scripts/test_backlink_blocks.py; 13+1, 43+19, 29+0 and 1+1 changed lines by `git diff --numstat`, about 110 lines), plus sibling sites (the lint's `backlink_split`, `scripts/_entry_checks.py:251-269`, `wiki-promote.py:295-310`). One part per axis, far under 3,000 lines. Spec source: `plan.md`, `requirements.md`, `checkpoints.md` (the "Review round 4 and fix round 4" entry whole), `doubt-log.md`, `review-findings.md` (round 4). The prescan ran clean, so the Standards lens skipped dates, review ids and width in Python comments. Both lenses ran as unnamed `code-reviewer-lens` spawns with `run_in_background: false` written out; the harness returned launch notices and I waited for their reports. Both ran on the default tier. Recorded trade-offs (a fenced END between START and END; `START / START / END / END` paired; `_entry_checks.py`'s unanchored regex) were not re-raised. Nothing was run: no tests; the producer's claims (84/84, four invariant files, check-freeze PASS) are unverified here. Files the earlier rounds reviewed and this fix did not touch are out of the round.

## Standards

- [important] S2/G5 `scripts/wiki-lint-mechanical.py:296` against `scripts/wiki-reciprocate-backlinks.py:103` — the two copies of the fence rule now split lines differently: the lint's `backlink_split` uses `lines = text.splitlines()`, the rebuild's new `fence_walk` uses `for line in text.split("\n"):`. This round created the split (the removed `strip_code` used `splitlines()`).
    - Trace (read from code, not run): a page whose line before a fence ends in a form-feed or U+2028 character, then `[B](b.md)`, then a fence line: the lint sees a fence from that line and does not count the link, the rebuild does not see the first line as a fence and counts it. Rare trigger (U+2028, form feed, vertical tab, U+0085 and similar).
    - Fix: use `text.split("\n")` in `backlink_split` so both copies read one separator, and add a test with such a character before a fence.
- [suggestion] T5 `tests/scripts/test_backlink_blocks.py:596-597` — the new guard branch for a START inside an unclosed fence is pinned only where no real block sits above the fence; quote: `pages = {"research/a.md": page("A", "[B](b.md)"), "research/b.md": page("B", "```\nnever closed")}`.
    - Fix: add a two-rebuild test with a real block above `` ```\nnever closed `` and a START below it, asserting the page is byte-identical after the second rebuild.

Unverified:
- The comment at `wiki-promote.py:303` says the rebuild runs in `/wiki-cycle` "before its lint"; the lens read only `wiki-cycle/SKILL.md:134` and did not check the step order.
- The producer's claims: test_backlink_blocks 84/84, the four invariant files green, check-freeze PASS. Nothing was run.

Checks made:
- standards-27 (an in-fence page gets one block on its first rebuild, then is left alone): holds. Page `"```\nnever closed"` linked from another: rebuild 1 appends one block after the fence; rebuild 2 finds a START with `unclosed` true, `has_unusable_start` returns True, the page is untouched. Pinned at test lines 596-609.
- standards-28 (a START left open after pairing): holds. `END` then `START`: the END leaves the count at 0, the START raises it to 1, the guard returns True; the lint's `backlink_start_unclosed` applies the same pairing. Pinned at test lines 583-593, including the lint row.
- standards-29 (one fence walk): holds for the rebuild: `strip_code` (`:118`) and `find_block` (`:141`) both call `fence_walk`. The lint's copy is the finding above.
- standards-31 (names): holds. `for match in START_LINE_RE.finditer(text):` and `line_start = text.rfind(...)` at `:145-146`.
- No regression found in: START in a closed fence with a real block (skipped by `find_block`); real block above plus a later unclosed fence holding a START (guard True, page untouched, lint `in_fence`); empty referrers with an existing block (removal path, unchanged); a page with no marker (append path).
- standards-15 (the promote comment): still holds. `wiki-promote.py:301-304` names `/wiki-cycle`, `/wiki-verify` and `/wiki-rollback`; Grep of `skills/` shows `wiki-cycle/SKILL.md:134`, `wiki-verify/SKILL.md:90`, `wiki-rollback/SKILL.md:92`.

| Rule / section | Verdict | Search |
|---|---|---|
| 1 S1/N1 | clear | every added or renamed identifier read in context |
| 2 S2/G5 | found | lint `:296` against rebuild `:103`; the pairing copy is written apart on purpose (lint `:280-281`) |
| 3 S3/G14 | clear | `backlink_blocks_out_of_step` read |
| 4 S4 | clear | the `(line, fenced, unclosed)` tuple has one shape |
| 5 S5 | clear | added functions read |
| 6 S6/G23 | clear | START/END branch and the lint pairing are one rule, by design |
| 7 S7 | clear | Grep of `strip_code`, `has_unusable_start`, `fence_walk`, `backlink_start_unclosed`, `find_block`, `backlink_split` |
| 8 S8 | clear | module read |
| 9 S9 | clear | no interface or hook added |
| 10 S10/G36 | clear | tuple unpacking only |
| 11 S11 | clear | every new function does work |
| 12 S12 | n/a | no subclass |
| 13 G25 | clear | literals in added lines read |
| 14 F3/G15 | clear | no boolean parameter added |
| 15 R1 | clear | new functions only return |
| 16 N7/G20 | clear | no writes in new functions |
| 17 C5 | clear | added lines read |
| 18 R26 | clear | `has_unusable_start` at `:189`, `fence_walk` at `:118/126/141`, `backlink_start_unclosed` at lint `:349` |
| Comments C1-C3, R2 | clear | docstrings checked against code |
| Names N2-N6, R3 | clear | read in context |
| Functions S13-G16, S15 | clear | `extract_outbound_links` still calls `strip_code`; no dead code left |
| Classes S16-G1 | n/a | no class added or changed |
| Boundary G3, G33, G26, G2 | clear | `fence_walk("")`, `has_unusable_start("")`, `find_block` first START traced |
| Tests T1, T3, T5, T6, R12-R15, T4 | found (T5) | test file read in full |
| Python PY1-PY11 | clear / n/a | no cast, Any, async; PY9 assertions are on produced bytes; PY10 the file's own plain-function `check` convention |

| File | Part | Standards read depth |
|---|---|---|
| `scripts/wiki-reciprocate-backlinks.py` | 1 | in full |
| `tests/scripts/test_backlink_blocks.py` | 1 | in full |
| `scripts/wiki-lint-mechanical.py` | 1 | in part (275-385, 1449-1475; every changed line) |
| `CHANGELOG.md` | 1 | in part (14-20) |
| `scripts/wiki-promote.py` | sibling | in part (290-314) |

Well built: one fence walk feeds `strip_code` and `find_block`, the guard handles END-then-START and fenced STARTs, and the new tests pin three-rebuild convergence byte for byte.

## Spec

- [important] `scripts/wiki-reciprocate-backlinks.py:127,131,145,149` against `scripts/wiki-lint-mechanical.py:304,317-319,349` — the lint strips inline code before it tests marker lines and the rebuild tests raw lines, so the one marker rule is not read identically (spec-16 does not fully hold).
    - Intent: `CHANGELOG.md:17`, "A backlinks marker counts only on a line of its own (indentation allowed), in both scripts"; the lint's comment at `:284-285`, "(the rebuild reads the same rule)"; `CHANGELOG.md:17`, "a rerun of the rebuild clears only extra and missing rows".
    - Implemented: lint `:304` `kept.append(re.sub(r"`[^`\n]*`", "", line))`, then `:319` `elif BACKLINK_END_LINE_RE.search(line)` on that stripped text; rebuild `:131` `elif not fenced and END_LINE_RE.search(line):` and `:145`/`:149` on raw text (`fence_walk` does no inline strip).
    - Trace A (END side): a page with a START line, `- [A](a.md)`, then `<!-- BACKLINKS-AUTO END --> ` followed by a backticked span on the same line. Raw, the END line fails `[ \t]*$`, so `has_unusable_start` stays True and the rebuild freezes the page; stripped, the END matches, so the lint pairs the markers and compares the block, and any linker change then lists an extra or missing row that a rerun cannot clear. Trace B (START side): a backticked span then a START on one line above a real block: the lint sees an open START and lists the page "block not closed" for good; the rebuild places the block correctly. Read from code, not run; the lines at `:304` and `:131` were re-read by me.
    - Affected: a page with a backticked span on the same line as a marker; its linkers' blocks and the lint's rows.
    - Fix: one rule in both scripts. Simplest: in both strip functions (lint `:304`, rebuild `:118`) replace each span with a non-space placeholder instead of `""`, so a stripped line cannot become a marker line; add one test per trace. Whether the split predates round 4 is unverified (the lint's strip dates from round 1, the rebuild's line anchoring from round 3), so this is not a regression from this round's diff.
- [suggestion] `scripts/wiki-reciprocate-backlinks.py:6-7` and `:297` — two stale claims in the changed script. Intent: docstring "The section is regenerated from scratch on every run so drift can't accumulate" and the cycle report line `_(none — script is deterministic, no skip logic)_`. Implemented: `:189-190` returns early for a page with an unusable START, so the rebuild does skip pages.
    - Affected: readers of the cycle's `reciprocate-backlinks.md`, which shows no skipped page.
    - Fix: say that the guard skips such pages, and report the skipped count or list.
- [nit] `scripts/wiki-lint-mechanical.py:296` against `scripts/wiki-reciprocate-backlinks.py:103` — `splitlines()` against `split("\n")` (the Standards finding above, seen from the Spec side). Ordinary pages do not diverge, because `read_text` turns `\r\n` and `\r` into `\n` first. Fix: `text.split("\n")` in `backlink_split`.
- [nit] `scripts/wiki-lint-mechanical.py:349-352` — a page with an open unfenced START and a START inside an unclosed fence gets only the "block not closed" row, so the fence cause stays hidden until the END is fixed. Fix: let the row carry both causes.

Unverified:
- Whether a four-backtick fence holding an odd number of three-backtick lines occurs in any notebook (the Spec lens found none in this repo's `*.md`; it is a recorded trade-off in `doubt-log.md`, so not raised as a finding).
- All traces are from code, not run, including the important finding.

Checks made:
- spec-22 (in-fence page, three rebuilds, lint `in_fence`): holds. `:189`, `:126-129`; lint `:349-375`; test at `:596`.
- spec-23 (END ... START left open): holds. `:131-133`; lint `:312-321`; test at `:571-594`.
- spec-1: still holds. An unclosed fence before the block gives the `in_fence` row (lint `:1464-1467`), not a "missing" row for each linker; a START quoted in backticks before a real block does not match the rebuild's line rule (`:61`), so nothing is spliced (tests `:453-467`).
- spec-9: holds for the shapes it named. The lint section text (`:1452-1458`), `wiki-cycle/SKILL.md:141`, `wiki-report/SKILL.md:278`, `wiki-lint/SKILL.md:37`, the contract doc `:175` and CHANGELOG line 17 send extra/missing rows to a rerun and not-closed and in-fence rows to a hand fix; the one exception is the marker shape in the important finding.
- spec-10: still holds. A START quoted mid-line is prose to the rebuild (`:61`, `:145`; test `:622-628`).
- spec-14: still holds. A START with no END is never rewritten (`:131-133`, `:189-190`; test `:571-594`), and the END-then-START order is now covered.
- spec-15: still holds. The rerun advice is scoped to extra/missing rows; "(the rebuild leaves such a page alone)" is now true for an in-fence page after its first rebuild.
- spec-16: holds for a marker quoted mid-line in plain prose and for the indentation rule; does not hold for a backticked span on a marker's own line (the important finding).
- Invariant 2 (golden): the guard cannot skip an ordinary block, whose lines hold no fence line (`:126-133`; test `:442`).
- CHANGELOG line 17 guard sentence read against the code: it matches, including "a page whose block sits in an unclosed fence gets that one block and is then left alone".

| Item | Verdict | Search / read |
|---|---|---|
| spec-22 in-fence page, 3 rebuilds | clear | traced; test `:596` |
| spec-23 END ... START | clear | traced; test `:571-594` |
| Neighbours: START in a closed fence plus a real block; real block plus a later unclosed fence; START in an unclosed fence plus a stray END; empty referrers; no marker | clear | traced |
| Lint and rebuild marker rule | found | backticked span on a marker line |
| Lint and rebuild line split | found (nit) | `:296` against `:103` |
| Lint and rebuild entry set | clear | lint `:190-195`, `:888`; rebuild `:87-94` |
| spec-1, 9, 10, 14, 15 | clear | see Checks made |
| spec-16 | found | see the important finding |
| Invariant 2 | clear | `:126-133`; test `:442` |
| Docs true to behaviour | found (suggestion) | docstring `:6-7`, report line `:297` |

| File | Part | Spec read depth |
|---|---|---|
| `scripts/wiki-reciprocate-backlinks.py` | 1 | in full |
| `tests/scripts/test_backlink_blocks.py` | 1 | in full |
| `scripts/wiki-lint-mechanical.py` | 1 | in part (184-197, 275-385, 1440-1479) |
| `CHANGELOG.md` | 1 | in part (10-21) |
| docs: `wiki-cycle/SKILL.md`, `wiki-report/SKILL.md`, `wiki-lint/SKILL.md`, `framework-docs/cycle-step-return-format.md` | sibling | in part (the cited lines) |
| `plan.md`, `requirements.md`, `checkpoints.md`, `doubt-log.md` | — | in full |

Well built: the rebuild's guard is order-aware with each trace matching a frozen test, and the lint and rebuild share the entry set and the link regex.

## Change risk

| File | Risk | Part | Standards | Spec | Change risk |
|---|---|---|---|---|---|
| `scripts/wiki-reciprocate-backlinks.py` | MEDIUM (rewrites wiki pages in place; business logic) | 1 | in full | in full | — |
| `scripts/wiki-lint-mechanical.py` | MEDIUM (check logic) | 1 | in part (changed lines) | in part (changed lines) | — |
| `tests/scripts/test_backlink_blocks.py` | LOW (tests) | 1 | in full | in full | — |
| `CHANGELOG.md` | LOW (docs) | 1 | in part | in part | — |

No high-risk file (no auth, sessions, tokens, crypto, payments, external call, data migration or removed validation), so the change-risk lens was not run.

## Needs-a-human

none (no auth, authz, token or session handling, or production-data migration finding; a spec resolved, so no no-spec line).

## Summary

Standards: 2 findings (1 important, 1 suggestion; worst: the lint and the rebuild now split lines differently, `splitlines()` against `split("\n")`, a rare trigger). Spec: 4 findings (1 important, 1 suggestion, 2 nits; worst: the lint strips inline code before it reads marker lines and the rebuild does not, so a backticked span on a marker's own line freezes the page or lists it "not closed", against the "same rule in both scripts" claim). The axes agree on the line-split difference. The round-4 fixes hold on both axes: standards-27/spec-22, standards-28/spec-23, standards-29 (in the rebuild), standards-31, and standards-15; of the earlier verdicts spec-1, -9, -10, -14 and -15 still hold, spec-16 holds except for the inline-code shape. The marker-rule split is not a regression of this round's diff; it is worth fixing before the install, since the CHANGELOG states the rule as shared. Several files are `in part` because the lenses read the changed hunks and context.

Risks or assumptions: both lenses ran on the default tier; the four-backtick fence case is the recorded doubt-log trade-off and was not raised.

VERDICT: Standards FINDINGS · Spec FINDINGS · Change risk NOT RUN · needs-a-human 0
