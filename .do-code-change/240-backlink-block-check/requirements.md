# Requirements — the lint checks every backlink block against the real links (task #240, lesson #11)

## Facts

- user confirmed (Mark, 2026-11-12, card #240): each pre-mortem lesson is built into llm-wiki; lesson #11 is "check backlink blocks against the forward-link graph"; code change, red then green, then install.
- user confirmed (Mark, 2026-11-14, Discord): "Send the suggestions first, then continue with 11".
- wiki `project/troubleshooting/research-cycle-failures-we-hit-2026-04-to-10.md` #11 (2026-08-01): `wiki-reciprocate-backlinks.py` wrote one fixed ~35-item list onto 25+ files, and 5+ link targets had no block; status 2026-10-13 "the corruption looks fixed … a sample, not a sweep. Not built: validating a block against the forward-link graph."
- found in `scripts/wiki-reciprocate-backlinks.py`: each run rebuilds every page's `<!-- BACKLINKS-AUTO START/END -->` block from scratch from the pages that link to it (`build_reverse_index` over every entry, its own block stripped first; `--since-hours` limits which pages are rewritten); a page with no linker gets no block; a self-link does not count; `_INDEX.md`, `_MAP.md`, `sessions/` and `tasks/` are not entries.
- found on 2026-11-14 (`--dry-run` on four notebooks): no block anywhere lists a page that does not link to it; blocks are only behind: llm-wiki-bootstrap 1 page (+1), agent-builder-bootstrap 2 (+2), agentic-design 0, investment-agent 98 pages (+161). Blocks fall behind whenever a page is edited between rebuilds.
- found in `skills/wiki-cycle/SKILL.md`: Step 3 runs `wiki-lint-mechanical.py --cycle-id --run-folder` (writes `lint-mechanical.json`); Step 3.5 then runs the backlink rebuild, index and map; Step 5.5 (automatic promotion only) re-runs the lint and Step 3.5. Step 3.5 says "Treat a large unexplained `backlinks_added` as a signal to look".
- found in `scripts/wiki-lint-mechanical.py`: warn-only sections such as "Design Pages Behind Their Notes" and "Code Drift" sit beside the counted checks; a section's count goes into the summary block at the top and into `lint-mechanical.json`.
- user confirmed (Mark, 2026-11-14, Discord, choosing (a) over a self-check inside the backlink script): "Regular lint that runs at the 2nd of each cycle? That makes sense" — the check lives in the mechanical lint, written apart from the backlink script, so a bug in the script cannot hide itself.
- follows from the lint's pattern: the new section is warn-only and changes no file; the fix for a page it lists is the backlink rebuild.
- follows from Mark's rule (CLAUDE.md "tests/skills"): a behavioural change to a skill is installed once its new cases run red then green; script behaviour is tested in `tests/scripts/`.

## Exclusions

- The lint does not rewrite blocks; it reports them.
- Not lessons #12 or #9; not a fix of investment-agent's 98 pages (that notebook's project runs its own rebuild).
- No change to how `wiki-reciprocate-backlinks.py` builds blocks.

## Decisions

1. **What the check counts.** Recommended: two kinds per page: an *extra* backlink (the block lists a page that does not link here — the 2026-08-01 kind, the alarming one) and a *missing* backlink (a page links here but the block does not list it, including a page with no block at all). Alternative: extra only (quiet, but misses the "no block" half of the incident).
2. **When the cycle looks, and what the report says.** Recommended: Step 3.5 ends with the lint run again (as Step 5.5 already does after promotion), so the cycle's lint result describes the notebook after the rebuild; then any page still out of step means the rebuild itself went wrong, and the report's ⚠️ Needs you names the count and the first pages. Alternative: only the Step 3 lint, before the rebuild: every link added since the last rebuild shows as missing, so a count above zero is normal and says nothing about the script.
