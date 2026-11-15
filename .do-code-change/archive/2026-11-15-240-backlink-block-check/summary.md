# 2026-11-15 240-backlink-block-check — the lint checks every backlink block against the real links

## TL;DR
The mechanical lint now checks every page's backlink block against the pages that really link to it (a warn-only section with its own summary line and `backlink_blocks` JSON array), the backlink script reads links by the same rule (section links, bracketed and empty link text; no links from code or `_inbox/`), and `/wiki-cycle` rebuilds blocks, indexes and the map before every lint, so the lint runs once and its count is what the rebuild left wrong. This closes pre-mortem lesson #11 of task #240 (a fixed block list once landed on 25+ files and nothing checked a block against the links). It ended as `keep` on `main` (the branch the run started on): six review rounds and a test-only round, verify with two named FAILs that Mark approved (bar-unmoved, tests-bite), then installed. Known effect: agent-builder's page `intake-build-candidates-seven-skills-built-derive-tests-folded-into-verify-2026-09-08.md` loses 3 backlinks, because of an unclosed code fence at its line 99; the lint lists it and the fix is agent-builder's.

## What changed
- The lint names each page whose backlink block is out of step
- The backlink script reads links by the same rule
- The cycle runs the rebuild before every lint and reports what is left
- Docs

New tags: `wiki-lint` (skills), added to the folder README's table by this change. `code-change`, the group `skills` and `wiki-cycle` (skills) already existed. This change revises no earlier record.

## Why: decisions and exclusions
Decisions:

1. **What the check counts.** (Confirmed by Mark, 2026-11-14, choosing (a): "lists each page whose backlink block doesn't match the real links (missing or extra)". Two rows that need a hand fix were added under it: a block not closed (red-team choice 5) and a block inside an unclosed code fence (review round 1, spec-1).) Recommended: two kinds per page: an *extra* backlink (the block lists a page that does not link here — the 2026-08-01 kind, the alarming one) and a *missing* backlink (a page links here but the block does not list it, including a page with no block at all). Alternative: extra only (quiet, but misses the "no block" half of the incident).
2. **When the cycle looks, and what the report says.** (Ruled 2026-11-14, Mark: "I think it only needs to run once didn't it?", then "Excellent" to swapping the order: the backlink rebuild, index and map run first, then the mechanical lint once, so its count is what the rebuild left wrong; a count above zero goes in Needs you. No second lint run.) So the cycle's integration scripts (backlink rebuild, folder index, map) come before its mechanical lint, and the lint runs once; any page it still lists out of step means the rebuild itself went wrong, and the report's ⚠️ Needs you names the count and the first pages. Rejected: a second lint run after the rebuild (only the rebuild happens between the two runs), and only the pre-rebuild lint (every link added since the last rebuild shows as missing).
3. **The backlink script reads links the way the check does.** (Ruled 2026-11-14, Mark: "Agreed with all".) The script counts a link to a section of a page (`page.md#section`) and a link whose text holds brackets as a link to that page, so the check does not flag the same ~26 backlinks on every run. Alternative: the check copies the script's blind spot.
4. **Tests and install.** (Mark, 2026-11-14: "Agreed with all. Ignore the limit. Please continue".) One red-then-green run of the new and changed skill cases (~$7-10), install after verify; prove_tests_bite.py's COULD-NOT-RUN on `scripts/` accepted once more as a named FAIL with a hand mutation pass as evidence; the review retry ceiling does not stop the run.

Exclusions:

- The lint does not rewrite blocks; it reports them.
- Not lessons #12 or #9; not a fix of investment-agent's 98 pages (that notebook's project runs its own rebuild).
- No change to how `wiki-reciprocate-backlinks.py` builds or places blocks beyond which links it reads (Decision 3), and one entry-set change ordered by the plan: a page under `_inbox/` is not an entry (ruled after review round 1, 2026-11-14: no wiki has one; the lint skips `_inbox/` too, so the two sets agree).
- Not the lint's own `LINK_RE` for broken links and orphans (parked).

## What the review found
Six review rounds (23, 14, 11, 10, 6, 4 findings), each with a fix round, and a test-only round after verify. Ledger at the end: met, no open blocking item, every verdict current (17 closed, 50 non-blocking), 6 rounds. Verdicts below are `review-ledger.json`'s own; `open` means non-blocking and left, with the reason in `checkpoints.md` (Review rounds 1-6).

- standards-1 — the lint repeats the block marker and regex that `_entry_checks.py` already defines — open
- standards-2 — the `_inbox` exclusion is an inline test in three places, not a helper — open
- standards-3 — `emit_cycle_artifacts` takes a tenth positional parameter — addressed
- standards-4 — `run_lint` and `rebuild_then_lint` repeat one notebook scaffold — open
- standards-5 — the opus baseline has a `read reference.md` key the sonnet one lacks — wontfix, fp-check: "VERDICT: standards-5 FALSE POSITIVE — gate 3 (Real impact) FAIL: the key is recorded only when a run applied the rule (`_trajectory.py:150-151`, `run_skill_test.py:443-444`) and the baseline comparison (`run_skill_test.py:581-583`) treats a key absent on either side as neither regression nor gain, so differing key sets change no result; the opus baseline itself omits the key in 14 of 23 entries, so it varies by run, not by model"
- standards-6 — the new pass walks the tree again though `files` holds the set — addressed
- standards-7 — `except (OSError, ValueError): continue` swallows with no stated reason — addressed
- standards-8 — the `wiki-promote.py` comment narrates a past state — addressed
- standards-9 — one cause, three names (`unclosed`, "block not closed", "not closed") — open
- standards-10 — `_check_backlinks` silently removes a result from `res` — open
- standards-11 — `_bl_lint` turns a missing or corrupt lint JSON into `{}` — open
- standards-12 — the `name()` fallback has no test — addressed
- standards-13 — bare `(task #240)` tags — open
- standards-14 — `variant == "dirty"` branches in two places in `check.py` — open
- spec-1 — lint and rebuild find the block in different text: a page with an unclosed fence before its block is "missing" every cycle — addressed
- spec-2 — the `_inbox/` exclusion changes which pages get blocks, against the Exclusion — addressed
- spec-3 — the link rule departs from the plan in three ways (whitespace and parenthesis targets, indented fences, code-then-block order) — addressed
- spec-4 — `wiki-lint` SKILL.md omits the new section, and its text is wrong for a standalone run — addressed
- spec-5 — the report's lint-table row is not in the plan — open
- spec-6 — the hub case's final-lint check has no premise that the rebuild ran — open
- spec-7 — test gaps: a rebuild link after an unclosed fence, links after a stray START — open
- spec-8 — the planted-page checks name no page — open
- standards-15 — the `wiki-promote.py` comment still misstates who runs the rebuild — addressed
- standards-16 — two boundaries of the new fence logic have no test — open
- standards-17 — three mutually exclusive causes carried as two keys — open
- standards-18 — `in_fence` is a bool in one function and a set in another — open
- standards-19 — a return line is right only because the conditional binds tighter than the comma — open
- standards-20 — `backlink_prose` is a one-line wrapper with one caller — open
- standards-21 — `STRAY` repeats the marker literal — open
- standards-22 — a test depends on the intro sentence's wording — open
- standards-23 — the lint function's docstring omits `in_fence` — addressed
- spec-9 — the docs send an unclosed or in-fence page to the rebuild, which cannot fix it — addressed
- spec-10 — a START quoted mid-line before a real block makes the rebuild splice over the prose — addressed
- spec-11 — the fourth row kind (`in_fence`) is missing from the plan and requirements — open (settled in plan.md, which the ledger's diffs leave out)
- spec-12 — plan.md's link-rule bullet contradicts itself on order — open (settled in plan.md)
- spec-13 — indented fences are not in the CHANGELOG or tested — addressed
- standards-24 — the promote comment still misses `/wiki-verify` and `/wiki-rollback` — addressed
- standards-25 — two copies of the block rule differ (the rebuild anchors markers to their own line, the lint did not) — addressed
- standards-26 — a test name says "twice" for two rebuilds — open
- spec-14 — a stray-START page is not safe to leave for the next cycle, and the docs do not say so — addressed
- spec-15 — the rerun advice is not scoped to extra and missing rows — addressed
- spec-16 — lint and rebuild disagree on a START quoted mid-line in prose — addressed
- spec-17 — an indented block is no longer matched by the rebuild — addressed
- spec-18 — "a marker quoted in code is no block" does not hold for block placement — addressed
- spec-19 — Step 2's aside names only the unclosed page, not the in-fence one — open
- spec-20 — no test has an indented fence — addressed
- spec-21 — a test name does not say it means two rebuilds — open
- standards-27 — `find_block` makes the rebuild append a new block on every run to an in-fence page — addressed
- standards-28 — the stray-START guard counts lines and ignores order — addressed
- standards-29 — `strip_code` and `find_block` split lines differently — addressed
- standards-30 — `_entry_checks.py`'s unanchored `_BACKLINKS_RE` is a third copy of the marker rule — open (outside Scope)
- standards-31 — a Match named `start` and an unnamed line start — addressed
- spec-22 — the rebuild does not leave an in-fence page alone — addressed
- spec-23 — the guard ignores order, so text loss remains for END-then-START — addressed
- spec-24 — a test pins a sentence in the report's prose — open
- spec-25 — `_entry_checks.py` left inconsistent with the line rule — open (outside Scope)
- spec-26 — an END inside a fence between START and END still ends the block there — open (recorded trade-off)
- standards-32 — lint `splitlines()` against rebuild `split("\n")` — addressed
- standards-33 — the new guard branch for an in-fence START is pinned only without a real block above — addressed
- spec-27 — the lint strips inline code before testing marker lines and the rebuild does not — addressed
- spec-28 — two stale claims in the rebuild's docstring and report line — addressed
- spec-29 — `splitlines()` against `split("\n")` (the Standards finding, from the Spec side) — addressed
- spec-30 — a page with an open START and a START in an unclosed fence shows only the "not closed" row — open
- standards-34 — a literal U+2028 in a test's separator tuple — addressed
- standards-35 — the `STRAY` constant reused where the line is asserted to be no START — addressed
- spec-31 — a link inside a double-backtick span still counts in both scripts — open
- spec-32 — the `x` placeholder can make a code span a link target — open

Left open as non-blocking at the finish (spec-30 from round 5, spec-31 and spec-32 from round 6), with reasons: spec-30 (a page needs a hand fix either way; fixing the END then shows the fence row; 0 hits in the four notebooks), spec-31 (pre-existing: the old strip read it the same way; both scripts agree, so no lint row is wrong; fixing it needs a new span regex, a design change; 0 hits in the four notebooks) and spec-32 (contrived: needs a page named `x.md`; 0 hits in the four notebooks).

## What was verified
Second verify, `verification-result.md`, per-layer lines (two named FAILs, each with Mark's approval; they are not passes):

- tests: PASS — fresh runs of the five proving files, each ending on its all-passed line: `test_backlink_blocks.py` "106/106 passed", `test_promote_backlinks.py` "14/14 passed", `test_cycle_script_fixes.py` "44/44 passed", `test_lint_spec_values.py` "11/11 passed", `test_hub_tag.py` "12/12 passed". The wiki-cycle skill suite was not re-run (it bills headless models; the red-then-green run `20261114-162044` is a recorded claim in `checkpoints.md`, not a fresh result).
- diff-contains-fix: PASS — the diff from the fixed point lists every file `plan.md`'s Scope names (23 files, 1350 insertions, 78 deletions; nothing untracked, on `main`).
- findings-addressed: FAIL at verify, then PASS — at verify `review-ledger.py query` exited 1 ("[standards-34] STALE - the diff of its file changed since the verdict; re-verify, never trust"), because the test-only round edited the file standards-34 cites. standards-34 was re-recorded after a look at the file (0 literal U+2028; line 625 holds the escape); re-query: "review-ledger: met - no open blocking item, every verdict current (17 closed, 50 non-blocking), 6 round(s)", exit 0. findings-addressed: PASS.
- frozen-tests: PASS — check-freeze.py exit 0, "frozen-tests layer: PASS — 75 entries checked (+ 47 from earlier changes), all match or unfrozen with a reason (2 retired: deleted on purpose) (65 frozen green, each with its reason)".
- coverage: PASS — every Step 1-2 criterion maps to an existing test; rows 3c and 3d have no test and are covered by the `manual: step 3` line in `plan.md`'s Testing Decisions, run by hand at verify (Grep and read).
- bar-unmoved: FAIL (named; approved exception, Mark 2026-11-15 on Discord, "Yes okay", both floor-guard hits approved as named) — floor-guard.py exit 1: "[unfinished-work] INSTALL-INVENTORY.md" (the row already held "not yet built" / "TODO:" and the change appended to it) and "[silenced-checker] tests/scripts/test_backlink_blocks.py: from _fake_qmd import fake_qmd_env  # noqa: E402" (the repo's idiom after a `sys.path` setup). Not a pass.
- in-scope: PASS — scope-guard.py exit 0, "23 touched file(s), all inside the declared scope".
- tests-bite: FAIL (named; approved exception, Mark 2026-11-14, requirements Decision 4) — prove_tests_bite.py --check exit 2, "VERDICT: COULD-NOT-RUN" on `scripts/`. Evidence in its place: a hand mutation pass on the current scripts, 157 mutants, 141 killed, 15 equivalent; the one real gap left (C: a link written on a fence line) is contrived and left open. Not a pass.

Verdict at verify: FAIL on findings-addressed, bar-unmoved and tests-bite; findings-addressed then re-recorded to PASS, leaving bar-unmoved and tests-bite as the two named FAILs. Not checked: the wiki-cycle suite (recorded only), Step 5.5's re-run order (no suite case), the docs read against the steps (Grepped only).

## Working files
Unchanged copies in the notebook's raw folder; the same files are archived in the code repository at `.do-code-change/archive/2026-11-15-240-backlink-block-check/`.

- [budget.json](../../../raw/code-changes/2026-11-15-240-backlink-block-check/budget.json)
- [checkpoints.md](../../../raw/code-changes/2026-11-15-240-backlink-block-check/checkpoints.md)
- [doubt-log.md](../../../raw/code-changes/2026-11-15-240-backlink-block-check/doubt-log.md)
- [hand-mutation-bl-result-verify.json](../../../raw/code-changes/2026-11-15-240-backlink-block-check/hand-mutation-bl-result-verify.json)
- [hand-mutation-bl-result.json](../../../raw/code-changes/2026-11-15-240-backlink-block-check/hand-mutation-bl-result.json)
- [hand-mutation-bl.py.txt](../../../raw/code-changes/2026-11-15-240-backlink-block-check/hand-mutation-bl.py.txt)
- [name-review.md](../../../raw/code-changes/2026-11-15-240-backlink-block-check/name-review.md)
- [parked.md](../../../raw/code-changes/2026-11-15-240-backlink-block-check/parked.md)
- [plan-red-team.md](../../../raw/code-changes/2026-11-15-240-backlink-block-check/plan-red-team.md)
- [plan.md](../../../raw/code-changes/2026-11-15-240-backlink-block-check/plan.md)
- [readonly-red-team.json](../../../raw/code-changes/2026-11-15-240-backlink-block-check/readonly-red-team.json)
- [readonly-review.json](../../../raw/code-changes/2026-11-15-240-backlink-block-check/readonly-review.json)
- [requirements.md](../../../raw/code-changes/2026-11-15-240-backlink-block-check/requirements.md)
- [review-findings.md](../../../raw/code-changes/2026-11-15-240-backlink-block-check/review-findings.md)
- [review-ledger.json](../../../raw/code-changes/2026-11-15-240-backlink-block-check/review-ledger.json)
- [review-report-fp-check-round-1.md](../../../raw/code-changes/2026-11-15-240-backlink-block-check/review-report-fp-check-round-1.md)
- [review-report-round-1.md](../../../raw/code-changes/2026-11-15-240-backlink-block-check/review-report-round-1.md)
- [review-report-round-2.md](../../../raw/code-changes/2026-11-15-240-backlink-block-check/review-report-round-2.md)
- [review-report-round-3.md](../../../raw/code-changes/2026-11-15-240-backlink-block-check/review-report-round-3.md)
- [review-report-round-4.md](../../../raw/code-changes/2026-11-15-240-backlink-block-check/review-report-round-4.md)
- [review-report-round-5.md](../../../raw/code-changes/2026-11-15-240-backlink-block-check/review-report-round-5.md)
- [review-report-round-6.md](../../../raw/code-changes/2026-11-15-240-backlink-block-check/review-report-round-6.md)
- [round2-changed.txt](../../../raw/code-changes/2026-11-15-240-backlink-block-check/round2-changed.txt)
- [round3-changed.txt](../../../raw/code-changes/2026-11-15-240-backlink-block-check/round3-changed.txt)
- [round4-changed.txt](../../../raw/code-changes/2026-11-15-240-backlink-block-check/round4-changed.txt)
- [round5-changed.txt](../../../raw/code-changes/2026-11-15-240-backlink-block-check/round5-changed.txt)
- [round6-changed.txt](../../../raw/code-changes/2026-11-15-240-backlink-block-check/round6-changed.txt)
- [run.json](../../../raw/code-changes/2026-11-15-240-backlink-block-check/run.json)
- [scope-baseline.json](../../../raw/code-changes/2026-11-15-240-backlink-block-check/scope-baseline.json)
- [test-freeze.json](../../../raw/code-changes/2026-11-15-240-backlink-block-check/test-freeze.json)
- [verification-result.md](../../../raw/code-changes/2026-11-15-240-backlink-block-check/verification-result.md)

## Related
- [code-changes/ — the folder and its tags](README.md)
- [2026-11-14 240-unfinished-run-check — a cycle's Step 0 names earlier runs that never finished](2026-11-14-240-unfinished-run-check-a-cycle-s-step-0-names-earlier-runs-that-nev.md) (the previous change on task #240)
- [Research-cycle failures we hit, 2026-04 to 10](../troubleshooting/research-cycle-failures-we-hit-2026-04-to-10.md) (lesson #11, the lesson this change builds in)
- [The research cycle](../architecture/30-the-research-cycle.md), [Quality and promotion](../architecture/50-quality-and-promotion.md) and [Testing the skills](../architecture/95-testing-the-skills.md) (the living design pages this change touches)
