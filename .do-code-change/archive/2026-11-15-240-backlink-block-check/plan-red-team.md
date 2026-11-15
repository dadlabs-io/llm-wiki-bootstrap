# Plan red-team — 240-backlink-block-check

Run by a fresh `architect` instance with the strategy-red-team skill (one `red-team-reviewer`, haiku; reconciled by the architect against the plan and the code; a read-only prototype on llm-wiki-bootstrap, agent-builder-bootstrap and global-toolset). Read-only guard: snapshot before, `check` exit 0 after. Saved by the orchestrator from the hand-back.

## Kill-assumptions (ranked)

1. **Step 5.6's lint re-run sees hub edits the rebuild never saw.** Fails if: Step 5.6 adds a hub line (a new link) and re-runs the lint with `--cycle-id --run-folder` (SKILL.md:161) with no rebuild between, so every newly hub-linked entry is "missing" the hub and Needs you fires falsely on every hub-editing cycle. Evidence: SKILL.md:161; LINT:730-747; plan names only 5.5. Kill criterion: a hub-case run whose final `lint-mechanical.json` has `backlink_blocks_out_of_step` > 0. Cheapest test: the hub case asserts 0 out of step. Fix class: plan error — Step 5.6 runs the three scripts, then its lint.
2. **`--direct`'s `wiki-fix-links.py` must come before the rebuild.** Fails if the folded Step 3 drops it or puts it after the rebuild (fixed links change the graph after blocks were built). Evidence: `wiki-promote.py:301-310` (fix-links, reciprocate, index, map). Fix class: plan error — order: fix-links (when `--direct` promoted), reciprocate, index, map, lint.
3. **Code stripping removes links the script counts today.** A backticked `[t](x.md)` to a real entry is in x's block today and would leave it; Invariant 2 does not cover this and Decision 3 names only section links and bracketed text. Prototype: 0 links removed on llm-wiki-bootstrap, agent-builder-bootstrap, global-toolset; agentic-design and investment-agent unmeasured. Kill criterion: one block losing a line on a real notebook. Cheapest test: dry run of the changed script on agentic-design and investment-agent. Fix class: choice.
4. **The lint's independent rule may disagree with the script after a rebuild.** Differences in code: entry sets (the lint has no dot-file check, the script has no `_inbox` check — the plan named only one direction); empty link text (script needs 1+ chars); whitespace in targets; fence stripping (mid-line ```, `~~~`, unclosed fence). None triggered today. Real-notebook agreement untested (the synthetic notebook agrees by construction). Kill criterion: any page listed after a rebuild on a real notebook. Cheapest test: post-change `--dry-run` then the lint section on each real notebook, expect 0 and 0; fixture pages for each difference. Fix class: plan error (name both set differences, one fence and one text rule for both, the real-notebook check at verify).
5. **A page with a START marker and no END.** The rebuild finds no block, appends a second; the next run's regex spans from the stray START to the new END and replaces body text. Old behaviour, but now the rebuild runs first every cycle; Step 2's "lists nothing after one rebuild" cannot hold for such a page. Fix class: choice — fix the rebuild (outside Decision 3 and the Exclusions) or the lint reports it as a named trade-off.
6. **The lint test needs `fake_qmd_env`.** Without it the lint exits 3 when qmd is missing or the wiki is not a collection (LINT:790-800, 1377-1384), so "exit code stays 0" goes red for an environment reason; `test_hub_tag.py:21,69` and `_fake_qmd.py` exist; `test_promote_backlinks.py:101-106` runs the lint without it and asserts only a header (weak evidence for Invariant 1). Fix class: plan error.
7. **The suite cases need a planted fixture.** With no stale block the count is always 0 and the Needs-you branch never fires; `check.py` has no step-order assertion (`QUICK_STEPS`, line 71), so an order case is new harness code; `/wiki-report` has no suite. Fix class: plan error — Step 3 names the fixture (one planted stale block, one page without a block) and the red-for-the-right-reason check.
8. **Step 3.5 references outside Scope.** `framework-docs/cycle-step-return-format.md` lines 17, 63, 180, 206; `scripts/wiki-promote.py:303` (comment); four suite fixtures' scratchpads ("### Phase 3.5: Integration scripts"); `reference.md` Phase 3 and 3.5; a resume with Phase 3 done and 3.5 pending could skip the scripts. Fix class: plan error — add `framework-docs/cycle-step-return-format.md` and `scripts/wiki-promote.py` to Scope; the fixtures and the resume rule in Step 3.

## Smaller points (findings)

- Order moves counts: block lines count as inbound links, broken links and hub links, so a rebuild that removes a stale line can raise orphans; requirements Fact 15 ("can only lower") is false as a rule (latent: no stale lines today). Contract gap.
- `--lint-only` runs 0, 3 and 8: folded, it now rewrites blocks, index and map; the plan must say so or exclude the scripts there. Contract gap.
- Step 5.5's lint (SKILL.md:156) has no `--cycle-id`, so the run folder's lint JSON can describe the pre-promotion state. Contract gap.
- Requirements Fact 13's prototype did not strip code; the architect's, with code stripped, found 0 links lost and 0 extra on the three notebooks measured.
- global-toolset has no blocks at all (15 missing): a standalone lint there lists every linked page until a first rebuild. Noise.

## What holds up

- The lint's exit logic is additive; a print-only warn section leaves exit codes unchanged.
- Block format and placement are untouched by a link-rule change; self-link and out-of-set exclusions exist.
- `_INDEX.md`, `_MAP.md`, `sessions/`, `tasks/` exclusions agree between lint and script.
- 0 links lost and no extra block line on the three notebooks measured; the new rule found 9 and 1 links the old one missed.
- The suite's trajectory rules say nothing about the lint/rebuild order.
- Step 5.5 already rebuilds through `wiki-promote.py`, so "no second lint run" holds for promotion.

## Could not assess

- agentic-design's stripping effect and investment-agent's agreement (prototype timed out / not run).
- Whether the new cases are red on HEAD and green after (the paid run); exact-key assertions in `test_cycle_script_fixes.py` and `test_lint_spec_values.py`.

VERDICT: KILL-ASSUMPTIONS FOUND
