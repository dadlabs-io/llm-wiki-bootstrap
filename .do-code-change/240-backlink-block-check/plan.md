# Plan — the lint checks every backlink block against the real links (task #240, lesson #11)

Classification: vertical slice (one user-visible behaviour: a cycle's lint names any page whose backlink block does not match the links, after the rebuild has run).

## Problem Statement

A backlink block can list pages that do not link there, or leave out pages that do (2026-08-01: one fixed list on 25+ files), and nothing checks a block against the links; the backlink script also skips section links and bracketed link text, so ~26 backlinks per large notebook are never written.

## Solution

The mechanical lint gets a warn-only section that rebuilds, on its own, which pages link to each page and compares that with each page's block. The backlink script reads links by the same rule. The cycle runs the backlink rebuild, index and map before its lint, so the lint's count is what the rebuild left wrong; the report's Needs you carries it when above zero.

## Implementation Decisions

- **One link rule, written twice on purpose** (Decision 1 "written apart"): a link is `](<target>.md)` with an optional `#section`, whatever the link text holds (brackets included), in the page's text with its own BACKLINKS-AUTO block, fenced code and inline code removed; the target resolves relative to the page, must be another entry in the entry set, and is not the page itself. The lint implements it in its own function; the backlink script's `LINK_RE` and stripping are changed to the same rule. Searched for an existing helper: `_entry_checks._MD_LINK_RE` matches the target part; the lint check uses its own pattern of the same form (sharing one compiled pattern would let one typo hide in both).
- **Entry set**: the lint's `collect_md_files` (every `.md` under `wiki/` except `_INDEX.md`, `_MAP.md`, `_inbox/`, `sessions/`, `tasks/`); the backlink script's set additionally drops dot-files. Pages outside the set are neither linkers nor targets.
- **Lint section** `## 🔗 Backlink Blocks Out of Step`, warn-only (exit code unchanged): one line per page with its extra and missing pages, listed by path; a summary line `**Backlink blocks out of step**: N page(s) (extra E, missing M)` beside the others at the top; `lint-mechanical.json` gains `backlink_blocks_out_of_step` (pages) in `summary` and a `backlink_blocks` array (`file`, `extra`, `missing`).
- **Wiki-cycle**: Step 3 becomes "Integration scripts, then the mechanical lint": `wiki-reciprocate-backlinks.py`, `wiki-index-per-folder.py`, `wiki-map-compile.py`, then `wiki-lint-mechanical.py`, each with `--cycle-id --run-folder`; Step 3.5 is folded into it, and every reference to Step 3.5 (mode table, Step 5.5's re-run, `reference.md`) is rewritten in place. Step 5.5's re-run keeps the same order (scripts, then lint). The "large unexplained `backlinks_added`" sentence stays.
- **Report**: `/wiki-report`'s Needs you gains "Backlink blocks the rebuild left out of step: N — <first 3 pages>; run `wiki-reciprocate-backlinks.py --topic <notebook>` and, if they stay, look at the script" only when the count is above zero; nothing when zero.

## Testing Decisions

- Seam: the two scripts through their command lines on a throwaway notebook, in a new `tests/scripts/test_backlink_blocks.py` (the pattern of `tests/scripts/test_cycle_scope.py`: one function per check, `check(name, ok, detail)`).
- Seam: the wiki-cycle skill suite (`tests/skills/run_skill_test.py wiki-cycle`): new cases from `eval-case-writer` for the step order and the report line; red on `HEAD` before the change, green after (Sonnet and Opus).
- manual: step 4 — the usage pages, CHANGELOG and INSTALL-INVENTORY read against steps 1-3.
- Mutation: `prove_tests_bite.py` cannot run on `scripts/` (Decision 4): a hand mutation pass over the added lines of both scripts, survivors turned into tests or left with a reason.

## Out of Scope

- The lint's own `LINK_RE` for broken links and orphans; lessons #12 and #9; investment-agent's notebook.

## Scope

- scripts/wiki-lint-mechanical.py
- scripts/wiki-reciprocate-backlinks.py
- tests/scripts/test_backlink_blocks.py
- skills/wiki-cycle/**
- skills/wiki-report/**
- skills/wiki-lint/**
- tests/skills/wiki-cycle/**
- tests/skills/PENDING.md
- CHANGELOG.md
- INSTALL-INVENTORY.md

## Invariants

- Every existing check in `tests/scripts/test_promote_backlinks.py`, `test_cycle_script_fixes.py` and `test_lint_spec_values.py` stays green.
- The backlink block's format (markers, heading, line form, sort order) is unchanged; a notebook whose links use none of the newly read forms gets byte-identical blocks.
- The lint's exit codes are unchanged (the new section is warn-only).

## Decisions needed

none beyond requirements Decisions 1-4

## Steps

1. The lint names each page whose backlink block is out of step — done when the block checks in `test_backlink_blocks.py` pass:
   - Expected: a block that lists a page not linking here is reported with that page as extra; a page linked from another with no block, or a block leaving a linker out, is reported with it as missing; a page whose block matches is not reported; the summary line, the JSON key and array carry the counts and pages.
   - Expected: a link to `x.md#section` and a link whose text holds brackets count; a link inside inline or fenced code does not; a page's own block, a self-link and a link to a page outside the entry set (`_INDEX.md`, `sessions/`) do not.
   - Failures: a page whose block has a start marker and no end marker is reported as out of step (its listed pages unreadable), never a crash; the lint's exit code stays 0 in non-strict mode.
   Trivial stakes: no
2. The backlink script reads links by the same rule — done when its checks pass:
   - Expected: a section link and a bracketed-text link put the linker in the target's block; a link in code does not; after one rebuild, the lint's new section lists nothing on the test notebook.
   - Expected: on a notebook using none of the new forms, every block is byte-identical before and after (Invariant 2).
   Trivial stakes: no
3. The cycle runs the rebuild before its lint and reports what is left — done when the new wiki-cycle cases run red on the old copy and green on the new (Sonnet and Opus), and `/wiki-report`'s Needs-you template carries the line. Trivial stakes: no
4. Docs — the wiki-cycle, wiki-lint and wiki-report usage pages, CHANGELOG and INSTALL-INVENTORY say what changed (manual: step 4). The refresh and `--mode status` run at the finish. Trivial stakes: yes — docs only
