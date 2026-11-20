## Red-team round 3 (narrow): 243-framework-docs-master, steps 3, 4, 14, 17 and the reconciled requirements

Written by the orchestrator from the red-team's report (a fresh `architect` running `strategy-red-team`, one `red-team-reviewer` on haiku, foreground); `readonly-guard.py check --step red-team` exited 0 (695 files compared, HEAD unchanged) before this file was written. Rounds 1 and 2: `plan-red-team-round-1.md`, `plan-red-team-round-2.md`. "Verified" = read by the red-team itself; "reviewer-cited" = not re-read. Two reviewer attacks were dropped as noise by the red-team (the per-file flag the plan already adds; the lessons folder path, already `research/wiki/` in Decision 5).

### Kill-assumptions (ranked)

**K1. A Phase B re-run overwrites a populated wiki's compiled `_MAP.md` with the day-1 placeholder.**
- Claim: "`_MAP.md` is regenerated every run" (Choice D); step 3 "`_MAP.md` is regenerated to the template's render".
- Fails if: `_render_template` writes `seed/wiki/_MAP.md.tmpl` over the file (verified, `new-wiki.py:1064-1070, 1342-1365`); the template is a placeholder ("This section will populate once entries exist"); the real map is built by `wiki-map-compile.py` (`new-wiki.py:1036-1037`); the project CLAUDE.md @-imports `_MAP.md` into every session (`new-wiki.py:1104-1107`). Mark's "map should get refreshed as its changed" means a compile, not a template render.
- Kill criterion: a second Phase B run over a wiki with entries leaves the placeholder.
- Cheapest test: step 3's retrofit tree-diff asserting `_MAP.md` keeps its entry list.
- Fix class: choice — (a) run `wiki-map-compile.py` after Phase B; (b) write the template only when missing; (c) leave `_MAP.md` alone. Standing rule: `10-install-and-setup.md:233-234` "Scaffold files are written once ... No refresh touches an existing project."

**K2. The re-run the plan calls "the supported way" has no supported entry, and has unlisted side effects.**
- Claim: Out of Scope "a Phase B re-run over an existing wiki is the supported way to add `local/README.md` and refresh `_MAP.md`"; step 3 "nothing else changed"; card #248 relies on it.
- Fails if: `new-wiki.py:920-930` refuses a non-empty target without `--force` (verified); the wrappers never pass `--force` (`10-install-and-setup.md:254`); `SKILL.md:213` forbids `--force` without the user's yes; step 3's test must pass `--force` and the plan does not say so. B8 `_upsert_registry` merges `confirm_before_create`/`confirm_before_promote` from CLI defaults (true) over the registry entry, and rewrites `.claude/wiki-config.json` (`wiki_folders`, `project_description`) (verified, `new-wiki.py:189-224, 1145-1163, 1178-1203`): a "retrofit" re-run resets a `false` gate to `true`. B7.5 renders `llm-wiki/README.md` on every run without `skip_if_exists` (verified, `:1109-1113`). The `--force` warning text (`new-wiki.py:927-929`, `SKILL.md:213`) still says it "writes everything else".
- Kill criterion: any file or registry key besides `best-practices/local/README.md` changes on a retrofit re-run.
- Fix class: plan error (llm-wiki/README.md into `skip_if_exists` and the invariant; the `--force` text; the test passes `--force`) and choice (may a re-run reset gates and `wiki_folders`, or must Phase B preserve them; or #248 retrofits by a narrower route).

**K3. The plan names `WIKI_FOLDERS` and `folder_notes` but not `taxonomy_for`.**
- Fails if: `best-practices/` is created only from what `taxonomy_for()` returns (reviewer-cited, `_wiki_config.py:118-134`, `new-wiki.py:1016-1023`); for `none` that is `sessions` only.
- Cheapest test: step 3's first Expected bullet already catches it.
- Fix class: plan error — name the `taxonomy_for` edit and its other callers.

**K4. Step 14's scope misses live in-notebook pages outside `wiki/**`.**
- Fails if: the notebook root `_INDEX.md` carries the old link (lines 614, 626, 665, reviewer-cited; match verified); `_inbox/design-rebuild/**` matches (drafts of the architecture pages; no disposition); card #248 names the old path as its subject (a link-only repoint would change its meaning); `10-install-and-setup.md:215` states the old path in live prose, which "prose left" would leave wrong.
- Cheapest test: list over the whole notebook folder, classify each hit.
- Fix class: plan error — widen the listing; `_INDEX.md` is rebuilt by the indexer (list, don't edit); architecture prose goes to the finish step's wiki record; card #248 excluded. Choice: the `_inbox/design-rebuild/**` copies.

**K5. Step 17's old-path guard has no return slot, and scenario 2 is not drivable through the skill.**
- Fails if: the guard at `check.py:368-372` sits in the shared scaffold branch, not a `kind`, and `tests/skills/README.md:21` says "an existing kind is never changed"; after step 1 the guarded path can never exist, so it is vacuous; requirements' "code change means test change" and that rule are not reconciled. Scenario 2 (a re-run over edited HOME/README) needs the user's `--force` yes (`SKILL.md:213`; the `force` case at `check.py:286-296`), so a paid red-green run could end asking a question on both copies. The two scenarios are step 3's own Expected bullets (README line 20 asks for scenarios that did not exist while the change was made); README line 19 asks for the requirement quoted in full.
- Cheapest test: give the writer the drafted brief and ask first whether scenario 2 can run (free).
- Fix class: choice (how the guard is fixed) and plan error (quote Decision 7 in full; scenario 2 gives the `--force` yes, or is dropped for script tests).

**K6. The reconciled requirements still contradict plan.md (verified).**
- Fact line 13 says "plan step 13"; it is step 16.
- Fact line 38 and Decision 2 say 53 files / "the 53 mentions are repointed"; the plan has 83 files, 180 occurrences, split 60 left / 3 listed / 19 repointed / 1 moved.
- Exclusion line 59 ("No change to the 231 ... 00-95 pages beyond what the architecture-decisions move needs") vs step 14 repointing the 00, 20, 50 pages (Choice B).
- Decision 7 says `local/` files are "linted as entries and searched" for wiki and toolset; `10-install-and-setup.md:217` says `list_topics()` hides `global-toolset`, so the toolset's `local/` is neither.
- Fix class: plan error — reconcile requirements.

### Skip, drop and default rules in steps 3, 4, 14, 17 against the standing rules
- README/HOME written only when missing, `_MAP.md` and `local/` README refreshed: `10-install-and-setup.md:233-234` (written once; no refresh touches an existing project) vs Mark's Choice D; K1 and K2 follow.
- `_copy_tree` not used: no standing rule found; the plan's reason holds (`new-wiki.py:316-318`).
- Lint has no exemption for `local/`: settled by Choice C; holds (reviewer-cited `wiki-lint-mechanical.py:187-195`).
- `sample_titles` gains `best-practices`; `drop_machine_files` keeps user notes: no standing rule found; holds (reviewer-cited `wiki-qmd-query.py:571-596, 770-774`).
- Step 14 journals and prose left; other projects left: Choices 2 and B; holds except K4.
- Step 17 no full suite by default; paid only on Mark's go: `tests/skills/README.md:3, 7-13` agree; holds.
- Step 17 PENDING rows for lint and search: no standing rule beyond the README's "small change" line; holds if `sample_titles` is the only search change.
- Step 17 cost $2-6: based on the $2.23 precedent (PENDING 2026-10-23); no standing rule for the range.

### What holds up
- Step 4's code claims (lint covers `best-practices/local/`; `sample_titles` is the only list naming `research`/`project`; `drop_machine_files` keeps user notes).
- The qmd collection covers the whole `wiki/` folder: `40-search-and-indexing.md:44`; also the orchestrator's check (the lint tells users `qmd collection add "<wiki_root>"`). The real pattern is step 4's manual evidence.
- No existing test relies on a re-run re-rendering README/HOME (grep of `tests/skills/new-wiki/`, `tests/scripts/`, both wrappers).
- `eval-case-writer` is installed; step 17 agrees with `tests/skills/README.md` on red-then-green on both models, the writer writing the cases, the full suite waiting for Mark.

### Could not assess
- no standing rule found: the `local/` README replaced by byte comparison on a re-run (Choice 3).
- no standing rule found: `sample_titles` addition and its "no timing run".
- no standing rule found: step 14's "edit link-only, leave prose".
- no standing rule found: step 17's $2-6 range.
- Not run: Phase B, qmd, any suite, `qmd collection list`. `taxonomy_for` and the `_INDEX.md` line numbers are reviewer-cited. Whether `_inbox/design-rebuild/**` is live is the requester's call. Whether the writer returns a usable guard fix needs a paid run.

VERDICT: KILL-ASSUMPTIONS FOUND
