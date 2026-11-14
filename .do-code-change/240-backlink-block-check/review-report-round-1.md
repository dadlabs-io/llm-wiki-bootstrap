# Review report, round 1 — 240-backlink-block-check

Fixed point `f9b3aa200a86ce60716ce42dae48b6cff1022f88` (resolves; merge-base is itself; the diff, `.do-code-change/` left out, is non-empty: 24 files, about 1,030 changed lines plus 4 generated JSON lines, one part per axis). No untracked files. Commits since the fixed point: 9 (`288e011`..`45e32fc`). Spec source: `plan.md` and `requirements.md` (Decisions 1-4), with `plan-red-team.md`, `checkpoints.md`, `doubt-log.md`. The lenses ran as unnamed foreground `code-reviewer-lens` spawns on the default tier. The prescan had run clean, so the Standards lens skipped dates, review ids, round numbers and width in Python comments. Findings in `tests/skills/wiki-cycle/{cases.json,check.py}` are tagged [eval-case-writer].

## Standards

- [suggestion] `scripts/wiki-lint-mechanical.py:282-284` — S2: the diff adds `BACKLINK_START`, `BACKLINK_END` and `BACKLINK_BLOCK_RE` for the block marker and block regex, which `scripts/_entry_checks.py:251-253` already defines (`_BACKLINKS_START`/`_BACKLINKS_END`/`_BACKLINKS_RE`) and which the lint already imports from at line 43. The plan's "written apart" decision (plan.md:15) covers the link rule, not the marker. Fix: make the three names public in `_entry_checks.py`, import them, delete the new definitions (scope question: `_entry_checks.py` is outside the plan's Scope).
    - quote: `BACKLINK_START = "<!-- BACKLINKS-AUTO START -->"` against `_BACKLINKS_START = "<!-- BACKLINKS-AUTO START -->"`
- [suggestion] `scripts/wiki-reciprocate-backlinks.py:86` — S2: the `_inbox` exclusion is a raw inline test among `_wiki_config` helper calls, though the file's header says path-resolution helpers live in `_wiki_config`; the same rule is inline at `scripts/wiki-lint-mechanical.py:193` and `scripts/wiki-fix-links.py:119`. Fix: add `in_inbox(path)` beside `in_sessions` (`scripts/_wiki_config.py:152`) and use it in all three (same scope question).
    - quote: `and "_inbox" not in p.relative_to(wiki_root).parts  # _inbox/ = staged and scratch, not entries`
- [suggestion] `scripts/wiki-lint-mechanical.py:416-417` (call at 1450, closing line 1469) — S14: `emit_cycle_artifacts` gains a tenth positional parameter and the call passes it positionally among same-typed lists. Fix: `}, broken_links, orphans, standalone, wiki_root, report_path, not_checked=not_checked, backlink_blocks=backlink_blocks)`.
    - quote: `}, broken_links, orphans, standalone, wiki_root, report_path, not_checked, backlink_blocks)`
- [suggestion] `tests/scripts/test_backlink_blocks.py:47` and `:333` — S2: `run_lint` and `rebuild_then_lint` repeat the same notebook scaffold and `fake_qmd_env` setup. Fix: one `_make_notebook(tmp, pages)` helper returning `(nb, w, proj, env)`.
    - quote (in both): `(tmp / "linked-notebooks.json").write_text(json.dumps({"notebooks": {"t": {"root": "notebooks/t"}}}),`
- [important] `tests/skills/wiki-cycle/baseline-opus.json:836` (also :450, :487, :526, :573, :627, :677, :721, :762) — the key `"run: read reference.md before writing the scratchpad": true` appears in nine opus entries and in no sonnet entry; the same case ids in `baseline-sonnet.json` (e.g. :799-833, :315-348) lack it, so the two models' entries differ in key set. A recorded check, not a failing one: every value is `true`, and no `false`/`null` exists in either file. Fix: confirm whether the `read_before` rule (`tests/skills/wiki-cycle/trajectory_rules.py:21`) is meant to score both models; if yes, find why sonnet never records it; if no, drop it from opus. (The producer may have recorded this by design; the lens could not tell. It is a generated file.)
    - quote: `"run: read reference.md before writing the scratchpad": true,`
- [nit] `scripts/wiki-lint-mechanical.py:855-856` — S2: the new pass walks the tree again though `files = list(collect_md_files(wiki_root))` (line 490) holds the same set. Fix: `backlink_blocks_out_of_step(wiki_root, [f for f in files if not f.name.startswith(".")])`.
- [nit] `scripts/wiki-lint-mechanical.py:305` — G4: `except (OSError, ValueError): continue` swallows with no stated reason. Fix: a one-line comment naming what is skipped, or drop the `try`.
- [nit] `scripts/wiki-promote.py:303` — C1: "Until promote ran it too, only /wiki-cycle's Step 3 ran it" narrates a past state git holds. Fix: state the present rule or drop the clause.
- [nit] `scripts/wiki-lint-mechanical.py:177` against `:1431` — R3: the key is `"unclosed": True`, the section says "block not closed", the usage page says "not closed". Fix: one word, e.g. key `not_closed`.
- [nit] [eval-case-writer] `tests/skills/wiki-cycle/check.py:2465` — N7: `_check_backlinks` silently removes the "quick steps all wrote their pair" result from `res` (an established pattern at seven sites; invisible at the call site). Fix: a named `drop` tuple with a comment, as `_check_unfinished` does at line 2230.
- [nit] [eval-case-writer] `tests/skills/wiki-cycle/check.py:2441` — R9/R8: `_bl_lint` turns a missing or corrupt lint JSON into `{}`, so the zero check reports "no backlink_blocks_out_of_step in the summary" as the cause. Fix: return the reason with the value.
- [nit] `scripts/wiki-lint-mechanical.py` (`name()` fallback `return path.as_posix()`) — T3: no test reaches it. Fix: one case with a block linking to `../../outside.md`.
- [nit] `scripts/wiki-lint-mechanical.py:280` and the test module docstring — C1: bare `(task #240)` tags. Fix: keep only where they link to the plan, or drop.
- [nit] [eval-case-writer] `tests/skills/wiki-cycle/check.py` (`_prepare_backlinks`, `_check_backlinks`) — S6: `variant == "dirty"` branches in two places. Fix: one branch keyed by variant.

Unverified:
- `backlink_prose` (lint, ~line 288) and `strip_code` (`wiki-reciprocate-backlinks.py:92`) are the same nine-line body; plan.md:15 puts code stripping inside the rule written twice on purpose, so no S2 was raised. Raise it if "written apart" means "not identical".
- G26: `block = BACKLINK_BLOCK_RE.search(text)` reads only the first block while `.sub` removes all; a page with two blocks may show a "missing" row. A two-block test through rebuild and lint would settle it.
- An END before its START (equal counts) is not flagged unclosed; reading `rewrite_backlinks_section` for the shapes it writes would settle it.
- Whether the `files` list at lint:490 is mutated before line 856 (reassignment only was checked).
- The hub baseline entry's `+77/-1`: which line was removed or replaced could not be seen (no git in the lens). `git diff f9b3aa2 -- tests/skills/wiki-cycle/baseline-opus.json` settles it.
- Case-set mismatch outside the three named ids: opus has `spot-check-picks-one-small-entry-only-that-one-checked` (baseline-opus.json:352), sonnet has `claims-scope-new-and-revised-not-unchanged` (baseline-sonnet.json:387); `cases.json` would settle whether intended.
- `trajectory_rules.py:21` was quoted from one grep hit; its per-model scope was not read.

Checks made:
- `framework-docs/wiki-authoring-best-practices.md:199` and `skills/wrap-up/SKILL.md` name `/wrap-up` Step 3.5, not `/wiki-cycle`'s: no stale reference. `skills/wiki-cycle/SKILL.md:141` "Phase 3.5" is the intended resume rule.
- Callers of the changed functions: `emit_cycle_artifacts` (lint:1450 only), `find_wiki_entries` (reciprocate:282), `extract_outbound_links` (reciprocate:126), `rewrite_backlinks_section` (reciprocate:305): consistent.

| Rule | Verdict | Search |
|---|---|---|
| S1 Mysterious Name | clear | every identifier in the added functions and helpers read in context |
| S2 Duplicated Code | found | Grep `BACKLINKS-AUTO START`, `"_inbox"`, `collect_md_files`, `LINK_RE`; the link-rule copy is plan.md:15 (Unverified) |
| S3 Feature Envy | clear | `backlink_blocks_out_of_step` reads only its own page text |
| S4 Data Clumps | clear | the row dict is built and read inside one function |
| S5 Primitive Obsession | clear | no domain value carried through several layers |
| S6 Repeated Switches | found (nit) | `variant == "dirty"` in check.py |
| S7 Shotgun Surgery | clear | the two-script link-rule edit is the plan's decision |
| S8 Divergent Change | clear | the new pass is self-contained |
| S9 Speculative Generality | clear | no interface or hook added |
| S10 Message Chains | clear | `page.parent / m.group(1)` is one level |
| S11 Middle Man | clear | no forwarding function or class |
| S12 Refused Bequest | n/a | the diff adds no class |
| G25 Magic numbers | clear | literals in added lines: regex, markers, "3" pages in report prose |
| F3 Flag Argument | clear | no boolean or mode argument in added functions |
| R1 Answers and mutates | clear | `backlink_targets`, `backlink_blocks_out_of_step`, `strip_code` only return |
| N7 Hidden Side Effect | found (nit) | check.py:2465 |
| C5 Commented-out code | clear | every added comment read: prose |
| R26 New code nothing uses | clear | Grep each new name: all have callers |
| Comments and docstrings | found (nit) | wiki-promote:303, task tags |
| Names | found (nit) | R3 `unclosed` vs "not closed" |
| Functions and control flow | found (suggestion) | S14; S13 `lint()` clear (length not measured) |
| Classes, modules and boundaries | clear | no class; added module-level names are constants |
| Error handling | found (nit) | G4 lint:305; R8/R9 in check.py |
| Boundary conditions | clear | body read: empty entries, no block, unclosed handled; G26 in Unverified |
| Tests | found (nit) | T3 `name()` fallback; duplicated setup; R13/R14/R15 clear |
| Python | clear | PY1-PY8 read; PY9 known answers; PY10 plain functions; PY11 no coverage claim |

Markdown and JSON were reviewed on the language-agnostic rules only (no language section applies).

| File | Part | Read depth (Standards) |
|---|---|---|
| all `scripts/*`, `tests/scripts/test_backlink_blocks.py`, `cases.json`, `check.py`, the four fixture scratchpads, `PENDING.md`, all skill/framework docs, `CHANGELOG.md`, `INSTALL-INVENTORY.md` | 1 | in full |
| `baseline-opus.json`, `baseline-sonnet.json` | 1 | in part on the first pass, in full after the one retry |

Well built: the link rule has one test per form (section link, bracketed or empty text, inline and fenced code, `_inbox`, sessions, tasks, dot-files), the lint section is warn-only with exit codes unchanged, and the cycle-step contract change is versioned and consistent with the usage pages.

## Spec

- [important] `scripts/wiki-reciprocate-backlinks.py:140,165-169,189-191` against `scripts/wiki-lint-mechanical.py:288-297,320-321` — the lint and the rebuild find the block in different text, so a page with an unclosed fence before its block is listed "missing" for every linker on every cycle.
    - Intent: plan Step 2: "after one rebuild, the lint's new section lists nothing on the test notebook"; red-team #4 kill criterion: "any page listed after a rebuild on a real notebook".
    - Implemented: the lint runs `text = backlink_prose(f.read_text(...))` then `BACKLINK_BLOCK_RE.search(text)`; `backlink_prose` drops everything after an unclosed fence, so a block after that fence is invisible. The rebuild reads the raw text and, with no block found, appends one (`new_text = text + "\n" + new_block + "\n"`), after the fence.
    - Affected: notebook owners; Needs you fires every cycle and points at the script though the rebuild's output is correct; the block also sits inside the fence and does not render.
    - Fix: run the rebuild's block search and append through the same code-stripped view (or skip and report such a page); add a test: page with an unclosed fence plus one linker, one rebuild, lint lists nothing.
    - Same root cause, second case (pre-existing in the rebuild): a START quoted in backticks before a real block: the raw regex at line 165 spans from the quoted START to the real END and replaces the text between, while the lint sees only the real block. checkpoints.md's "code is stripped before blocks are found (both scripts…)" holds for link reading and the lint only.
- [suggestion] `scripts/wiki-reciprocate-backlinks.py:86` — `and "_inbox" not in p.relative_to(wiki_root).parts` changes which pages get blocks, not only which links are read.
    - Intent: requirements Exclusion: "No change to how `wiki-reciprocate-backlinks.py` builds or places blocks beyond which links it reads (Decision 3)." (Plan line 16 does order the `_inbox/` exclusion.)
    - Fix: record the exception as a ruling amending the Exclusion, or drop the exclusion.
- [suggestion] `scripts/wiki-reciprocate-backlinks.py:59,97`; `scripts/wiki-lint-mechanical.py:285` — the link rule departs from plan line 15 in three ways.
    - (a) Plan: "`](<target>)` where `<target>` has no whitespace"; the code also excludes parentheses (not in plan) and drops whitespace targets the old `\[([^\]]+)\]\(([^)]+\.md)\)` read, so `[x](my page.md)` loses its linker. Invariant 2 ("byte-identical blocks") does not hold for such a notebook, and the CHANGELOG Migration line says only "adds the backlinks the old rule never wrote".
    - (b) Plan: a fence is "a line starting with ``` or ~~~"; `line.lstrip()` makes any indented fence a fence (no test).
    - (c) Plan order: block removed first, then code; both scripts strip code first (checkpoints.md acknowledges it; the plan was not amended).
    - Fix: amend plan and CHANGELOG to name the whitespace and parenthesis cases, or keep reading whitespace targets; decide on indented fences.
- [suggestion] `skills/wiki-lint/SKILL.md:26-40` — the mechanical check list omits the new section; each check there is listed with its date (e.g. "Hubs behind their tag (added 2026-10-23)"). The section text "Run after the rebuild, so a page listed here means the rebuild went wrong" is wrong for a standalone `/wiki-lint` run, which the same file calls "Reports only" (line 19) and runs no rebuild. Fix: add the bullet; reword the section to say it is read after a cycle's rebuild.
- [suggestion] `skills/wiki-report/SKILL.md:188` — the health-count row `| Backlink blocks out of step | N |` is not in the plan (plan Report: only the Needs-you line, when above zero). Its source is the cycle's lint JSON, so it is not stale. Fix: keep it and add it to the plan, or drop it.
- [suggestion] [eval-case-writer] `tests/skills/wiki-cycle/baseline-sonnet.json:300` — the hub case's final-lint check has no premise that the rebuild ran, so a 0 can pass with nothing rebuilt.
    - Intent: plan Step 3 and Testing Decisions: the hub case's final lint reads 0 out of step after the rebuild.
    - Implemented: quote `"the final lint reads backlink_blocks_out_of_step 0 (the rebuild ran before the last lint)": true`; the two new cases carry `"premise: the integration scripts ran (reciprocate-backlinks wrote its pair)"` (:780, :817), the hub case (:274-312) has none.
    - Fix: add the same premise check to the hub case.
- [nit] Test gaps: no rebuild test for a link after an unclosed fence (plan Step 2 "a link in code … does not"; the lint has one); the rule that links after a stray START are ignored (a doubt-log decision, not in the plan) has no test.
- [nit] [eval-case-writer] `tests/skills/wiki-cycle/baseline-sonnet.json:783-784` — the planted-page checks name no page ("the linked page that had no block now has one listing the page that links to it", "the stale block no longer lists the page that does not link there"). Fix: name the fixture's two page paths in the check labels.

Unverified:
- Plan Verify: the lint section on llm-wiki-bootstrap, agentic-design, agent-builder-bootstrap and investment-agent after one rebuild on scratch copies, expected 0: checkpoints.md records only the dry-run counts.
- Dry-run counts (+10/+20/+187/+3-3) and CHANGELOG "three backlinks from one page": producer claims; rerunning the dry run settles them.
- Red-team choice 3 kill criterion: agent-builder loses 3 block lines; checkpoints.md says "to be named to Mark before install"; no record that he was told.
- Red-team #5, body replacement on a second rebuild of a page with a stray START: accepted by checkpoint, not in the CHANGELOG; not a plan mismatch.
- Test counts 41/41, 14/14, 44/44, 11/11, 12/12 and run `20261114-162044-red-green-84cdf16_6`: cannot run here (this review runs no test). Grep found 40 `def test_` and 41 `check(` in `test_backlink_blocks.py`, consistent with 41 checks.
- Plan Testing Decisions mutation pass over the added lines: no mutation record found under `.do-code-change/240-backlink-block-check` (a Glob for `*mutat*` found nothing; checkpoints.md mentions only a "heading mutant").
- "No wiki has an `_inbox/` page today": not checkable from the repo.
- Whether agent-builder's page with the line-99 fence has a block (the first finding applied to a live page).
- The red-on-HEAD run and the Opus baseline entries are not evidenced inside the baseline files.

Checks made:
- `grep 3\.5` over `skills/ framework-docs/ scripts/ tests/skills/wiki-cycle/`: only history lines (reference.md:124, SKILL.md:141) and wrap-up/wiki-lint/wiki-promote's own Step 3.5, not `/wiki-cycle`'s.
- Exit block at lint lines 1472-1485 is not in the diff: exit codes unchanged (Invariant 3).

| Plan item | Verdict | Search |
|---|---|---|
| Step 1 (lint section, JSON, summary, Failures) | clear | 40 `def test_`, 41 `check(`; each Expected/Failures bullet maps to a test in lines 610-860 |
| Step 2 (rebuild reads links by the rule) | found | findings 1, 3, test gaps |
| Step 3 (cycle order, 5.5/5.6, `--lint-only`, resume rule) | clear | Grep `3\.5` as above |
| Step 4 (docs) | found | wiki-lint SKILL.md, wiki-report table row |
| Invariant 1 (existing checks green) | n/a here | tests not run by a review; unverified |
| Invariant 2 (byte-identical blocks) | found | whitespace-target drop; golden test at 966-971 |
| Invariant 3 (exit codes unchanged) | clear | exit block unchanged |
| Decision 1 (extra, missing, unclosed) | clear | lint diff; tests 610-700 |
| Decision 2 (rebuild first, lint once, Needs you) | clear | SKILL Steps 3, 8 |
| Decision 3 (section links, brackets, empty text) | clear | tests 728-765; whitespace drop noted in finding 3 |
| Decision 4 (tests, install) | clear for the test file | red/green and install unverified |
| Exclusion: lint does not rewrite blocks | clear | no block write added |
| Exclusion: not lessons #12/#9 | clear | diff read |
| Exclusion: no change to building/placing beyond links read | found | `_inbox` exclusion (finding 2) |
| Exclusion: lint's own `LINK_RE` unchanged | clear | line 50 unchanged |
| Fact 15 / Step 5.5 "0 broken links" | clear | block lines name existing entries |
| Testing: new and hub cases | found | premise gap; page names |
| Testing: mutation pass | not evidenced | Glob |
| framework-version 8 to 9 | clear | CHANGELOG bumps follow the convention |

| File | Part | Read depth (Spec) |
|---|---|---|
| all files except `baseline-sonnet.json` | 1 | in full |
| `baseline-sonnet.json` | 1 | in part on the first pass, in full after the one retry |
| `baseline-opus.json` | 1 | in part (lines 768-807, the two new ids); the Standards retry read it in full |

Well built: the lint check and the rebuild's link reader are separate functions with one rule, the entry set agrees between them, and the golden test pins the block format against the unchanged rewrite function.

## Change risk

| File | Risk | Part | Standards | Spec | Change risk |
|---|---|---|---|---|---|
| `scripts/wiki-lint-mechanical.py` | MEDIUM (business logic, new warn-only check, JSON keys) | 1 | in full | in full | — |
| `scripts/wiki-reciprocate-backlinks.py` | MEDIUM (rewrites entry bodies; which links and pages count changes) | 1 | in full | in full | — |
| `scripts/wiki-promote.py` | LOW (comment) | 1 | in full | in full | — |
| `tests/scripts/test_backlink_blocks.py` | LOW (tests) | 1 | in full | in full | — |
| `tests/skills/wiki-cycle/{cases.json,check.py}` | LOW (tests) | 1 | in full | in full | — |
| `tests/skills/wiki-cycle/baseline-opus.json` | LOW (generated) | 1 | in full (retry) | in part | — |
| `tests/skills/wiki-cycle/baseline-sonnet.json` | LOW (generated) | 1 | in full (retry) | in full (retry) | — |
| `tests/skills/wiki-cycle/fixtures/*/scratchpad*.md` (4) | LOW | 1 | in full | in full | — |
| `tests/skills/PENDING.md` | LOW | 1 | in full | in full | — |
| `skills/wiki-cycle/{SKILL.md,reference.md,wiki-seed/wiki-cycle.md}` | MEDIUM (the cycle's step order) | 1 | in full | in full | — |
| `skills/wiki-report/{SKILL.md,wiki-seed/wiki-report.md}` | LOW | 1 | in full | in full | — |
| `skills/wiki-lint/wiki-seed/wiki-lint.md` | LOW | 1 | in full | in full | — |
| `framework-docs/cycle-step-return-format.md` | LOW (contract doc) | 1 | in full | in full | — |
| `CHANGELOG.md`, `INSTALL-INVENTORY.md` | LOW | 1 | in full | in full | — |

No high-risk file: no auth, sessions, tokens, crypto, payments, external call, data migration, or removed validation, so the change-risk lens was not run. `baseline-opus.json` stays `in part` for the Spec axis (its Spec retry covered the sonnet file only; the Opus baseline is generated results and the Spec findings on it are limited to the plan's named cases); the Standards lens read it in full.

Prior-round files left out: none (round 1).

## Needs-a-human

none (no auth, authz, token or session handling, or production-data migration finding; a spec resolved, so no no-spec line).

## Summary

Standards: 14 findings (1 important, 4 suggestions, 9 nits; worst: the opus-only `read reference.md` key in the baselines). Spec: 9 findings (1 important, 5 suggestions, 3 nits; worst: after one rebuild the lint still lists a page whose block follows an unclosed fence, so the report's Needs you would fire every cycle for it). Change risk: not run. The axes do not agree on any finding; the Standards and Spec lenses both touch the `_inbox` exclusion in `wiki-reciprocate-backlinks.py:86` from different sides (duplicated inline rule; exclusion beyond the "links read" scope). Worth acting on the Spec important finding and deciding the link-rule departures from the plan before the install.

Risks or assumptions: the lenses ran on the default tier; the baseline files were retried once for read depth; the two first-pass lenses did not read the Opus baseline for Spec. Nothing was changed in the project apart from this file.

VERDICT: Standards FINDINGS · Spec FINDINGS · Change risk NOT RUN · needs-a-human 0
