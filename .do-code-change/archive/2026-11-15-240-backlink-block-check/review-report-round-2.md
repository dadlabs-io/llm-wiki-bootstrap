# Review report, round 2 (focused) — 240-backlink-block-check

Fixed point `f9b3aa200a86ce60716ce42dae48b6cff1022f88` (resolves). The change under review for the lenses is the fix round's diff, commit `33ffce4` to HEAD, for the 7 files in `round2-changed.txt` (`.do-code-change/` left out; 1 changed file's worth of production script: 30+/13- lint, 2/2 promote; tests +105; docs 6 lines), plus the sibling sites of each addressed round-1 finding. One part per axis, well under 3,000 lines. The lenses ran as unnamed `code-reviewer-lens` spawns on the default tier; the harness returned both as launch notices despite `run_in_background: false`, so I waited for their completion and took the reports from them. The brief asked for a quick scope only; no request to skip the lenses was made. Spec source: `plan.md` and `requirements.md` (both amended after round 1), `checkpoints.md` (Review round 1, Fix round 1), `doubt-log.md`, `review-report-fp-check-round-1.md`. The prescan ran clean, so the Standards lens skipped dates, review ids and width in Python comments. Items left with reasons in round 1 (standards-1, -2, -4, -9, -10, -11, -13, -14, spec-6, spec-8) were not re-raised; standards-5 was closed by fp-check. The status of spec-1, -2, -3, -5 and -7 is under `Checks made:` in `## Spec`.

## Standards

- [important] C2 `scripts/wiki-promote.py:303-304` — the reworded comment says "Only /wiki-cycle's Step 3 runs it otherwise", but `skills/wiki-cycle/SKILL.md` Step 5.6 ("run Step 3's integration scripts and the mechanical lint once more") and CHANGELOG line 16 (Steps 5.5 and 5.6 rebuild; `--lint-only` rebuilds too) show the cycle runs it in more places. Fix: `# it and the lint counts it an orphan. /wiki-cycle also runs it at Steps 5.5 and 5.6 and under --lint-only, so without it here every /wrap-up would leave its new entries orphaned.`
    - (The lens read Step 5.6's wording as a second call site; arguably it is Step 3's script list re-run, so the comment is imprecise rather than false.)
- [suggestion] T5 `tests/scripts/test_backlink_blocks.py` (new tests, about 450-553) — two boundaries of the new fence logic have no test: (a) a START quoted in a closed fence, then an unclosed fence, must not be `in_fence` (only `if in_fence: opened = i` at lint :296-297 keeps it out); (b) an unclosed START in prose plus a block inside the fence must report only `unclosed` (:331-334). Fix: add `test_marker_quoted_in_a_closed_fence_before_an_unclosed_one_is_not_in_fence` (page `"```\n<!-- BACKLINKS-AUTO START -->\n```\n\n```\nnever closed"`, assert `backlink_blocks == []`) and one for (b) asserting `{"unclosed": True}` with no `in_fence`.
- [suggestion] S4/S5/PY2 `scripts/wiki-lint-mechanical.py:352, 355` read at `:1444, :1446` — the three mutually exclusive causes are carried as two keys and `in_fence` exists only on some rows (`row["unclosed"]` against `row.get("in_fence")`). Fix: one `cause` field, or always emit `"in_fence": False`; `framework-docs/cycle-step-return-format.md:175` and the test's `FENCE_ROW` would change with it (whoever owns the JSON shape decides).
- [nit] S1/R3 `scripts/wiki-lint-mechanical.py:292, 327, 329` — `in_fence` is a bool in `backlink_split` and a set of pages in `backlink_blocks_out_of_step`; `fenced` holds only the unclosed fence's tail. Fix: rename the set `pages_in_fence` and `fenced` `unclosed_fence`.
- [nit] G16/G19 `scripts/wiki-lint-mechanical.py:300` — `return "\n".join(kept), "\n".join(lines[opened:]) if in_fence else ""` is right only because the conditional binds tighter than the comma. Fix: `return "\n".join(kept), ("\n".join(lines[opened:]) if in_fence else "")`.
- [nit] S11 `scripts/wiki-lint-mechanical.py:303-304` — `backlink_prose` forwards to `backlink_split(text)[0]`; its only caller is `:310`. Fix: call `backlink_split(text)[0]` there and delete the wrapper, or give it a docstring.
- [nit] S2 `tests/scripts/test_backlink_blocks.py:486` — `STRAY = "<!-- BACKLINKS-AUTO START -->"` repeats the literal in `blk()` (:40) and `UNCLOSED` (:293). Fix: one module constant.
- [nit] R13 `tests/scripts/test_backlink_blocks.py:467` — `"missing" not in s.split("Warn-only.")[-1]` depends on the intro sentence's wording. Fix: take the page's own line (`[l for l in s.splitlines() if "`research/b.md`" in l]`) and test that.
- [nit] `scripts/wiki-lint-mechanical.py:319` (reviewer's own check, docstring of `backlink_blocks_out_of_step`) — it still says `[{file, extra, missing, unclosed}]` while a row can now also carry `in_fence`. Fix: add `in_fence` to the docstring.

Unverified:
- `CHANGELOG.md:17` "the old rule read one with a space": the old rule is in `wiki-reciprocate-backlinks.py` before `33ffce4`; `git show` of that file settles it (the doubt-log line 7 says the old rule did not read parentheses either).
- `scripts/wiki-lint-mechanical.py:314` comment "(bad characters)": the reason is asserted, not shown, for both `OSError` and `ValueError`.
- `scripts/wiki-lint-mechanical.py:355-356`: a page with a fenced START skips the extra/missing comparison, as the unclosed branch already does; whether that is intended is a correctness point outside Standards.
- The brief's wiki-promote hunk showed "# (new) it and the lint ..."; the file at line 303 does not contain "(new)". The lens quoted the file.
- Fence scanning in `wiki-reciprocate-backlinks.py:95-99` is a near copy of `backlink_split`: "written apart" in round 1, not raised again.

Checks made:
- `files` (lint :504) is assigned once and never mutated, so reusing it at :869 (standards-6) reads the same entry set as `collect_md_files`.
- `emit_cycle_artifacts`'s signature (`not_checked=(), backlink_blocks=()`, :430-431) takes the keywords the call now passes (standards-3).
- Tests run: none (a review runs no test). The claims 56/56, the four invariant files and check-freeze PASS are unverified here; a Grep found 54 `def test_` lines and 58 `check(` lines in `test_backlink_blocks.py`, which does not contradict 56 checks.

| Rule | Verdict | Search |
|---|---|---|
| S1 Mysterious Name | found (nit) | read lint 288-300, 327-334 |
| S2 Duplicated Code | found (nit) | test lines 40, 293, 486 |
| S3 Feature Envy | clear | read 318-361 |
| S4 Data Clumps | found | folded into the row-shape finding |
| S5 Primitive Obsession | found | folded into the row-shape finding |
| S6 Repeated Switches | clear | Grep `in_fence\|unclosed` repo-wide |
| S7 Shotgun Surgery | clear | Grep `backlink_split\|backlink_prose\|in_fence` |
| S8 Divergent Change | clear | read 1420-1464 |
| S9 Speculative Generality | clear | read 288-362 |
| S10 Message Chains | clear | read diff |
| S11 Middle Man | found (nit) | Grep `backlink_prose` |
| S12 Refused Bequest | n/a | no class in the diff |
| G25 Magic numbers | clear | literals read |
| F3 Flag Argument | clear | no boolean parameter added |
| R1 Answers and mutates | clear | read 288-362 |
| N7 Hidden Side Effect | clear | no writes |
| C5 Commented-out Code | clear | added comments read |
| R26 New code nothing uses | clear | Grep `backlink_split`: :304, :329; `in_fence` row read at :1446 |
| Comments and docstrings (C1-C3, R2) | found | C2 promote comment; docstring staleness |
| Names (N2-N6, R3) | found (nit) | `in_fence` overloaded |
| Functions and control flow | found (nit) | G16/G19, S11 |
| Error handling | clear | comment on swallowed error; reason unverified |
| Boundary conditions | clear | `backlink_split("")` gives ("", "") |
| Tests | found | T5, S2, R13 |
| Python (PY1-PY11) | found (PY2 folded) | rest clear; PY4-6 n/a |

| File | Part | Read depth (Standards) |
|---|---|---|
| `scripts/wiki-lint-mechanical.py` | 1 | in full (every changed hunk) |
| `scripts/wiki-promote.py`, `CHANGELOG.md`, `framework-docs/cycle-step-return-format.md`, `skills/wiki-lint/SKILL.md`, `skills/wiki-lint/wiki-seed/wiki-lint.md` | 1 | in full (changed lines) |
| `tests/scripts/test_backlink_blocks.py` | 1 | in full (the 105 added lines) |

Well built: `backlink_split` reads the fence once and returns both views, the `in_fence` row has a test that pins it, and the keyword call at `lint()` removes a positional-argument risk.

## Spec

- [important] `skills/wiki-report/SKILL.md:278` (siblings: `framework-docs/cycle-step-return-format.md:175`, `skills/wiki-lint/wiki-seed/wiki-lint.md:28`) — the Needs-you line sends an unclosed or in-fence page to the backlink script, and a second rebuild of a stray-START page removes body text.
    - Intent: plan Step 1 Failures: "a page with a START and no END is listed as "block not closed", never a crash"; the lint row says "fix it by hand" (`scripts/wiki-lint-mechanical.py:1445`) and "close the fence by hand" (`:1447`); requirements Exclusions: "The lint does not rewrite blocks; it reports them."
    - Implemented: SKILL.md:278 says "any page listed here is one the backlink script got wrong: run `wiki-reciprocate-backlinks.py --topic <notebook>` once, and if the lint still lists it, look at the script"; the contract doc says "a page in `backlink_blocks` is one the backlink rebuild got wrong". A rerun does not clear an in-fence row (the rebuild rewrites the same block in place, `wiki-reciprocate-backlinks.py:165-169, :180`). For an unclosed page, read from code (not run): the first rebuild appends a block after the stray START (`:188-191`); the next rebuild's `START.*?END` search runs from the stray START to the new block's END and `:180` splices over the prose between.
    - Affected: anyone who follows the report on an unclosed or in-fence page; the script is blamed for a fence the user must close, and an unclosed page's prose is at risk on rerun.
    - Fix: for `unclosed` and `in_fence` rows, the report line, the contract doc and the lint section say "fix by hand, do not rerun"; keep the rerun line for extra/missing rows only. Add a test for two rebuilds on a stray-START page.
- [important] `scripts/wiki-reciprocate-backlinks.py:165` — round-1 spec-1's second case is unaddressed and unrecorded.
    - Intent: `review-findings.md` spec-1: "Same root cause, second case (pre-existing in the rebuild): a START quoted in backticks before a real block: the raw regex at line 165 spans from the quoted START to the real END and replaces the text between". The "Fix round 1" entry in `checkpoints.md` does not mention it; `parked.md` holds only an unrelated item.
    - Implemented: the rebuild still reads raw text (`:140`) and matches `START.*?END` on it (`:165-169`); the lint strips code first (`wiki-lint-mechanical.py:299`). The only quoted-marker test is lint-only (`test_marker_quoted_in_inline_code_is_neither_a_block_nor_unclosed`, test file :323-330). Pre-existing behaviour, and the Exclusions bar changing block placement, so the way out is a ruling.
    - Affected: notebook owners whose prose quotes the exact marker in code before a real block; the rebuild replaces the text between. (Whether a live page has this shape is unverified; a Grep of the llm-wiki-bootstrap notebook shows pages that discuss the marker, and the one checked spells it without comment brackets.)
    - Fix: a recorded ruling (parked, outside the Exclusions) in `checkpoints.md`, or have the rebuild search the code-stripped view, with a red rebuild test.
- [suggestion] `plan.md` Step 1 and `requirements.md` Decision 1 — the fourth row kind (`in_fence`) is recorded only in `checkpoints.md`, the CHANGELOG and the contract doc.
    - Intent: requirements Decision 1: "two kinds per page: an extra backlink ... and a missing backlink"; plan Lint-section bullet lists the array fields `file, extra, missing, unclosed`; Step 2 says only "the unclosed-block page aside, which stays listed".
    - Implemented: `scripts/wiki-lint-mechanical.py:354-355` emits `"in_fence": True`; the plan's "after one rebuild the lint lists nothing" also stays unmet for such a page by design.
    - Fix: add the in-fence case to the plan's Lint-section bullet, Step 1 Failures and Step 2 "aside" clause, and to requirements Decision 1.
- [nit] `plan.md:15` "One link rule" — the bullet contradicts itself on order. Intent: main sentence "with its own BACKLINKS-AUTO block removed, then fenced code ... and inline code ... removed" against the amendment "code is stripped before the page's own block is found". Implemented: code first (`scripts/wiki-lint-mechanical.py:288-300`, block at `:329-335`; rebuild `extract_outbound_links`). Fix: reword the main sentence to code first, then block.
- [nit] indented fences — documented in the plan, not in the CHANGELOG, not tested. Intent: plan line 15 "a fence line may be indented"; `CHANGELOG.md:16` "a fence opened by a line starting with ``` or ~~~". Implemented: `scripts/wiki-lint-mechanical.py:294` uses `line.lstrip().startswith(...)`; no test has an indented fence, and the hand mutation pass has no `lstrip()`-removal mutant. Fix: name indentation in the CHANGELOG and add one lint and one rebuild test.

Unverified:
- The second-rebuild loss on a stray-START page is read from `:165-169` and `:180`, not run; two rebuilds on such a page settle it.
- Whether the suite passes (the 56 checks, the 15 new tests) is not run here.
- Whether any live notebook page quotes the exact marker in code before its block.

Checks made:
- Round-1 findings, status:
  - spec-1 (block after an unclosed fence): first case ADDRESSED in the lint. `backlink_split` returns the tail of an unclosed fence; a START inside it gives the page its own row (`in_fence: true`, "close the fence by hand") instead of listing its linkers as missing (`scripts/wiki-lint-mechanical.py:288-300, 329-334, 354-356`); the rebuild is unchanged. The second case is NOT addressed and has no recorded ruling (the second finding above); two sibling sites still say to rerun the script (the first finding above).
  - spec-2 (`_inbox/`): ADDRESSED. `requirements.md:23` Exclusion is amended, the plan's Entry-set bullet already ordered it, and the lint's `collect_md_files` and the rebuild's `find_wiki_entries` exclude the same set.
  - spec-3 (link-rule departures): MOSTLY ADDRESSED. Whitespace and parenthesis targets and the code-before-block order are named in the plan, the Invariant and the CHANGELOG; indented fences are in the plan but not the CHANGELOG and untested (the last nit above); the plan bullet's main sentence still says block first (the nit before it).
  - spec-5 (report's lint row): ADDRESSED. Plan Report bullet amended; the row is at `skills/wiki-report/SKILL.md:188`.
  - spec-7 (missing tests): ADDRESSED. `test_rebuild_ignores_a_link_after_an_unclosed_fence`, `test_rebuild_ignores_links_after_a_stray_start` and `test_lint_ignores_links_after_a_stray_start` exist; each asserts the rebuild ran (a block for `c`) and would fail if the post-fence or post-START link were read. Not run.
- The rebuild script is not in the diff (`git diff 33ffce4 HEAD --stat` lists no `wiki-reciprocate-backlinks.py`): block format and placement are as in round 1, so Invariant 2 and the placement Exclusion are not touched by this round.
- The lint's exit block is outside the diff; the lint only reports (no block write added).
- `skills/wiki-report/SKILL.md:188` carries the lint-table row, and plan line 20 records it (spec-5).

| Item | Verdict | Search |
|---|---|---|
| A spec-1 first case, lint and rebuild agree | clear | lint `:329-337, :354-355`; test `:453-459`; the report-side wording is row C |
| B spec-1 second case | found | Grep `quoted\|backtick` over the run folder and tests; only a lint-only test |
| C sibling sites of spec-1 | found | Grep `left out of step\|went wrong\|look at the script\|in_fence\|close the fence\|block not closed\|backlink_blocks` over skills, scripts, framework-docs, tests, CHANGELOG |
| D `_inbox/` agreement (spec-2) | clear | lint `:187-195` and rebuild `:81-89` exclude the same set; Exclusion amended |
| E spec-3 (a)(b)(c) | found | plan `:15` read; Grep for an indented fence in the tests: none |
| F spec-5 report row | clear | plan line 20; `SKILL.md:188` |
| G spec-7 tests | clear | read the three tests; each fails if the reader were wrong |
| H Invariants and Exclusions | clear | rebuild unchanged; exit block outside the diff |
| I fourth kind recorded | found | Grep `in_fence` in plan.md and requirements.md: none |

| File | Part | Read depth (Spec) |
|---|---|---|
| `plan.md`, `requirements.md`, `checkpoints.md`, `doubt-log.md`, `review-findings.md`, `wiki-reciprocate-backlinks.py`, the test file | 1 | in full |
| `scripts/wiki-lint-mechanical.py` | 1 | in part (270-380, 1420-1495, plus Grep hits); every changed hunk read |
| `scripts/wiki-promote.py`, `CHANGELOG.md`, `framework-docs/cycle-step-return-format.md`, `skills/wiki-lint/SKILL.md`, `skills/wiki-lint/wiki-seed/wiki-lint.md` | 1 | in part (the changed lines and their context) |
| `skills/wiki-report/SKILL.md`, `skills/wiki-report/wiki-seed/wiki-report.md` | 1 | in part (sibling sites) |

Well built: the lint's `in_fence` row and the three spec-7 tests are each pinned, the entry set is the same in both scripts, and the lint and rebuild strip code before reading links.

## Change risk

| File | Risk | Part | Standards | Spec | Change risk |
|---|---|---|---|---|---|
| `scripts/wiki-lint-mechanical.py` | MEDIUM (business logic, a new row kind, JSON shape) | 1 | in full | in part | — |
| `scripts/wiki-promote.py` | LOW (comment) | 1 | in full | in part | — |
| `tests/scripts/test_backlink_blocks.py` | LOW (tests) | 1 | in full | in full | — |
| `CHANGELOG.md`, `framework-docs/cycle-step-return-format.md` | LOW (docs, contract doc) | 1 | in full | in part | — |
| `skills/wiki-lint/SKILL.md`, `skills/wiki-lint/wiki-seed/wiki-lint.md` | LOW (docs) | 1 | in full | in part | — |

No high-risk file: no auth, sessions, tokens, crypto, payments, external call, data migration or removed validation, so the change-risk lens was not run. Prior-round files left out: the rest of round 1's change (the rebuild script, the wiki-cycle and wiki-report skills, the suite files) was reviewed in round 1 and not moved by the fix round; nothing new was raised in them.

## Needs-a-human

none (no auth, authz, token or session handling, or production-data migration finding; a spec resolved, so no no-spec line).

## Summary

Standards: 9 findings (1 important, 2 suggestions, 6 nits; worst: the reworded `wiki-promote.py` comment names Step 3 as the only other caller of the rebuild). Spec: 5 findings (2 important, 1 suggestion, 2 nits; worst: the Needs-you line and the contract doc tell the reader to rerun the backlink script for an unclosed or in-fence page, where a second rebuild can splice over prose; and spec-1's second case is neither fixed nor ruled). Change risk: not run. Round-1 items: spec-2, spec-5 and spec-7 are addressed; spec-3 is addressed except the indented-fence note and test; spec-1 is addressed in the lint for its first case only. The axes agree that the new `in_fence` row's shape and record are thin (Standards on its row shape, Spec on its absence from the plan). Worth acting on the two Spec important findings before the install.

Risks or assumptions: the lenses ran on the default tier and came back as launch notices that I waited out; nothing was run (no tests); two claims rest on reading the code for a second-rebuild path.

VERDICT: Standards FINDINGS · Spec FINDINGS · Change risk NOT RUN · needs-a-human 0
