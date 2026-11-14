# Plan — the lint checks every backlink block against the real links (task #240, lesson #11)

Classification: vertical slice (one user-visible behaviour: a cycle's lint names any page whose backlink block does not match the links, after the rebuild has run).

## Problem Statement

A backlink block can list pages that do not link there, or leave out pages that do (2026-08-01: one fixed list on 25+ files), and nothing checks a block against the links; the backlink script also skips section links and bracketed link text, so backlinks go unwritten.

## Solution

The mechanical lint gets a warn-only section that works out, on its own, which pages link to each page and compares that with each page's block. The backlink script reads links by the same rule. Wherever the cycle lints, the backlink rebuild, index and map run first, so the lint's count is what the rebuild left wrong; the report's Needs you carries it when above zero.

## Implementation Decisions

- **One link rule, written twice on purpose** (requirements Decision 1, "written apart"; amended after review round 1: code is stripped before the page's own block is found, so a marker quoted in code is no block; a target with whitespace or parentheses is not read, which the old rule read for whitespace (the real-notebook dry run found no such link); a fence line may be indented): in a page's text, with its own BACKLINKS-AUTO block removed, then fenced code (a line starting with ``` or ~~~ up to the next such line, or to the end of the page when unclosed) and inline code (`` `...` `` on one line) removed, a link is `](<target>)` where `<target>` has no whitespace, ends in `.md`, and may carry `#section`; the link text may be empty and may hold brackets. The target resolves relative to the page and counts only when it is another page of the entry set. The lint implements this in its own function; the backlink script's `LINK_RE` and stripping change to the same rule (code stripping included: red-team choice 3, below). `_entry_checks._MD_LINK_RE` already matches the target part; neither script imports the other's pattern.
- **Entry set, the same for both**: every `.md` under `wiki/` except `_INDEX.md`, `_MAP.md`, files whose name starts with `.`, and anything under `_inbox/`, `sessions/` or `tasks/`. The lint's check uses this set (its other passes keep `collect_md_files`); the backlink script gains the `_inbox/` exclusion (no wiki has one today).
- **Lint section** `## 🔗 Backlink Blocks Out of Step`, warn-only (exit codes unchanged): one line per page with its extra pages and missing pages, by path; a page with a BACKLINKS-AUTO START and no END is listed as "block not closed" (the rebuild is not changed for it: red-team choice 5); a summary line `**Backlink blocks out of step**: N page(s) (extra E, missing M)` at the top; `lint-mechanical.json` gains `backlink_blocks_out_of_step` (pages) in `summary` and a `backlink_blocks` array (`file`, `extra`, `missing`, `unclosed`).
- **Wiki-cycle order** (requirements Decision 2): Step 3 becomes "Integration scripts, then the mechanical lint", in this order: `wiki-fix-links.py --topic <notebook>` only when this run promoted with `--direct` (as today), then `wiki-reciprocate-backlinks.py`, `wiki-index-per-folder.py`, `wiki-map-compile.py`, then `wiki-lint-mechanical.py`, each with `--cycle-id --run-folder`. Step 3.5 is folded into Step 3. Step 5.5's re-run becomes the three scripts then the lint, the lint with `--cycle-id --run-folder` (today it has none). Step 5.6's re-lint after a hub edit runs the three scripts first. `--lint-only` (Steps 0, 3, 8) therefore also rebuilds blocks, index and map; the mode table and the `--lint-only` line say so. Every reference to Step 3.5 / Phase 3.5 is rewritten in place: `SKILL.md`, `reference.md` (one Phase 3 with both), the usage page, `framework-docs/cycle-step-return-format.md` (lines 17, 63, 180, 206), the comment at `scripts/wiki-promote.py:303`, and the suite fixtures' scratchpads; a resumed run whose scratchpad has the old "Phase 3.5" pending runs the scripts and the lint again (they are idempotent).
- **The order moves other counts**: the lint counts block lines as links, so a rebuild before it can lower or raise the orphan, broken-link and hub counts (a stale block line removed). requirements Fact 15 is corrected to say so; nothing today has a stale line (Fact 9).
- **Report** (amended after review round 1: the report's lint table also gains a `Backlink blocks out of step` row from the cycle's lint JSON): `/wiki-report`'s Needs you gains "Backlink blocks the rebuild left out of step: N — <first 3 pages>; run `wiki-reciprocate-backlinks.py --topic <notebook>` and, if they stay, look at the script" only when the count is above zero; nothing when zero.

## Testing Decisions

- Seam: the two scripts through their command lines on a throwaway notebook, in a new `tests/scripts/test_backlink_blocks.py` (one function per check, `check(name, ok, detail)`), the lint always run with `_fake_qmd.fake_qmd_env` (as `tests/scripts/test_hub_tag.py` does), so an exit code is never red for a missing qmd collection.
- Seam: the wiki-cycle skill suite: new cases from `eval-case-writer`, on a fixture notebook with one planted extra block line (a page listing a page that does not link to it) and one linked page with no block: after the cycle the run folder's `lint-mechanical.json` has `backlink_blocks_out_of_step` 0 and both pages fixed, the report has no backlink line; and the hub case's final lint JSON reads 0 out of step. Red on `HEAD` before the change for the right reason (the key absent, or the planted page still out of step), green after (Sonnet and Opus); the writer is told `check.py` has no step-order assertion today.
- Verify (real notebooks, read-only): after the change, the backlink script `--dry-run`, then the lint's new section on llm-wiki-bootstrap, agentic-design, agent-builder-bootstrap and investment-agent on a scratch copy rebuilt once: 0 pages listed; and the number of block lines a real notebook loses to code stripping, reported (red-team choice 3's kill criterion).
- manual: step 4 — the usage pages, CHANGELOG, INSTALL-INVENTORY and `framework-docs/cycle-step-return-format.md` read against steps 1-3; `grep -rn "3\.5"` over `skills/ framework-docs/ scripts/ tests/skills/wiki-cycle/` finds no stale reference.
- Mutation: `prove_tests_bite.py` cannot run on `scripts/` (Decision 4): a hand mutation pass over the added lines of both scripts; survivors become tests or are left with a reason.

## Out of Scope

- The lint's own `LINK_RE` for broken links and orphans; changing how the rebuild places a block (a START with no END); lessons #12 and #9; investment-agent's notebook content.

## Scope

- scripts/wiki-lint-mechanical.py
- scripts/wiki-reciprocate-backlinks.py
- scripts/wiki-promote.py
- tests/scripts/test_backlink_blocks.py
- skills/wiki-cycle/**
- skills/wiki-report/**
- skills/wiki-lint/**
- tests/skills/wiki-cycle/**
- tests/skills/PENDING.md
- framework-docs/cycle-step-return-format.md
- CHANGELOG.md
- INSTALL-INVENTORY.md

## Invariants

- Every existing check in `tests/scripts/test_promote_backlinks.py`, `test_cycle_script_fixes.py`, `test_lint_spec_values.py` and `test_hub_tag.py` stays green.
- The backlink block's format (markers, heading, line form, sort order) and placement are unchanged; a notebook whose links use none of the newly read forms, none inside code and no target with whitespace gets byte-identical blocks.
- The lint's exit codes are unchanged (the new section is warn-only).

## Decisions needed

none beyond requirements Decisions 1-4 (red-team choices 3 and 5 decided under them, recorded in checkpoints.md)

## Steps

1. The lint names each page whose backlink block is out of step — done when the block checks in `test_backlink_blocks.py` pass:
   - Expected: a block listing a page that does not link here is reported with it as extra; a linked page with no block, or a block leaving a linker out, is reported with it as missing; a matching block is not reported; the summary line, the JSON key and array carry the counts and pages.
   - Expected: a link to `x.md#section`, a link whose text holds brackets and a link with empty text count; a link inside inline code, inside a ``` or ~~~ fence, or after an unclosed fence does not; a page's own block, a self-link, a target with whitespace, and a target outside the entry set (`_INDEX.md`, `sessions/`, a dot-file) do not.
   - Failures: a page with a START and no END is listed as "block not closed", never a crash; exit 0 in non-strict mode (with `fake_qmd_env`).
   Trivial stakes: no
2. The backlink script reads links by the same rule — done when its checks pass:
   - Expected: a section link, a bracketed-text link and an empty-text link put the linker in the target's block; a link in code or to a page under `_inbox/` does not; after one rebuild, the lint's new section lists nothing on the test notebook (the unclosed-block page aside, which stays listed).
   - Expected: on a notebook using none of the new forms and no link inside code, every block is byte-identical before and after (Invariant 2).
   Trivial stakes: no
3. The cycle runs the rebuild before every lint and reports what is left — done when the new wiki-cycle cases run red on the old copy and green on the new (Sonnet and Opus), the hub case's final lint reads 0 out of step, the suite fixtures and `reference.md` carry one Phase 3, and `/wiki-report`'s Needs-you template carries the line. Trivial stakes: no
4. Docs — the wiki-cycle, wiki-lint and wiki-report usage pages, CHANGELOG, INSTALL-INVENTORY and `framework-docs/cycle-step-return-format.md` say what changed; the `wiki-promote.py` comment names Step 3 (manual: step 4). The refresh and `--mode status` run at the finish. Trivial stakes: yes — docs only
