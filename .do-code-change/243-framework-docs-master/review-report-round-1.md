# Review report, round 1 — 243-framework-docs-master

Fixed point 7b66e2a92fc2cfa3892050f143bd35fe0e6bd40d (resolves; merge-base is the same commit), HEAD 88e9482, working tree clean, no untracked files. Diff non-empty: 54 changed files (the lenses counted 54 `diff --git` headers), about 1,750 changed lines, so one part per axis (under the 3,000-line cap). Spec source: `plan.md` and `requirements.md` in the artifact folder, with `checkpoints.md` overriding the plan where Mark's answers changed it. The lenses ran in the foreground by flag; the harness returned launch notices and I took each report from its completion notification. The three lenses ran on the default tier.

## Standards

Skipped by the prescan: review ids, round and Q numbers and dates in Python comments and docstrings, line width. Python rules, the every-diff rules and the Comments, Names, Functions, Classes, Error handling and Tests sections were pasted; Boundary, Concurrency and Refactoring were marked n/a.

- [important] `CHANGELOG.md` (2026-11-19 entry, "What" bullet) with `scripts/wiki-upgrade.py:68-69` and `scripts/new-wiki.py:510-514` — G4: a failed write on the global refresh path prints FAILED and still exits 0.
  Quote: "A refresh that cannot write or remove one file now lists it as `FAILED <path>: <reason>`, finishes the rest and exits 1." Code: wiki-upgrade.py `print_summary(summary)` then `return 0`; new-wiki.py `--mode tooling` returns 0 unless frontmatter failed. Only `--phase docs` returns 1.
  Fix: return 1 from both paths when `summary["toolset"]["failed"]` is non-empty, or correct the CHANGELOG line. Add a test pinning the exit code on that path (T1 gap).
- [important] `tests/scripts/test_global_toolset.py:459` — T4: a skipped case records a PASS.
  Quote: `check("unwritable README: skipped, root writes through a read-only file (nothing proved here)", True)`.
  Fix: record a visible skip, fail the case, or drop it with the reason in a comment.
- [important] `tests/scripts/test_standalone.py:170` — R26: new constant nothing uses.
  Quote: `PRACTICE_PAGE_ROOT = "notebooks/agentic-design/wiki/research/wiki/"`; grep finds only the definition.
  Fix: a question for the author: delete it, or build `STEP9_DOCS` from it.
- [suggestion] `scripts/_install_tooling.py:200` — S15: the clause can never be false, so it is dead logic.
  Quote: `if TOOLSET_OLD_FRAMEWORK_DOCS / p.name not in files] if old_docs.is_dir() else []`. `files` holds only `how-to/` and `wiki/best-practices/` keys. The lens agrees M20 is equivalent and M22 is equivalent (`glob` on a missing folder yields nothing, so the `is_dir()` guard is redundant). Also S2: lines 196 and 199 are the same comprehension for the same reason.
  Fix: drop the clause; one helper for the two remove scans.
- [suggestion] `scripts/wiki-map-compile.py:375` — C2: stale comment beside the changed line 378.
  Quote: `# Container folders (research/, project/) hold subfolders instead of direct` beside `CONTAINER_FOLDERS = {"research", "project", "best-practices"}`.
  Fix: add best-practices/ to the comment.
- [suggestion] `scripts/_wiki_config.py:103` — C2: the comment no longer matches what the scaffold creates.
  Quote: `# What a default scaffold creates: both halves with stubs, plus sessions/.` `taxonomy_for` (lines 135-136) now also appends `best-practices/local`. `SCAFFOLD_TAXONOMY` is read by `tests/skills/wiki-cycle/check.py:146-148` and `tests/skills/wiki-update/check.py:97-104` as "the folders a default /new-wiki creates".
  Fix: say the local folder is added by `taxonomy_for`, or derive the constant from it.
- [suggestion] `scripts/_wiki_config.py:112` — S7: the folder list is kept in two places and the diff updated one.
  Quote: `MERGED_TAXONOMY = (RESEARCH_TAXONOMY + LEGACY_RESEARCH_TAXONOMY + PROJECT_TAXONOMY`, whose comment says "Every path the folder guards recognise". A wiki with no top-level `best-practices/` (any wiki made before this change) refuses `--folder best-practices/local`; new wikis pass through Case 1.
  Fix: add `"best-practices/local"` to the list.
- [suggestion] S2: duplicated test code added in this diff: `def _run(fn):` with the same body at `tests/scripts/test_global_toolset.py:561`, `tests/scripts/test_local_folder.py:418`, `tests/scripts/test_search_mode.py:414`; the lint subprocess twice in `test_local_folder.py` (lines 169 and 292); the same 8-key `summary` literal in two `test_global_toolset.py` tests.
  Fix: one shared helper; reuse `_lint_report_after_writing`.
- [suggestion] `tests/scripts/test_global_toolset.py:166`, `:189`, `:203` — T4: `if sys.platform != "win32": ... return` records no check on other platforms, so the check count differs by OS and the skip is invisible.
  Fix: record a named skip.
- [suggestion] `scripts/_install_tooling.py:222` — N7: `def _guarded(op, path, failed: list) -> bool:` appends to its `failed` argument and the name does not say so.
  Fix: rename to say it records the OSError.
- [suggestion] `tests/skills/new-wiki/check.py:372` — R15: `add("local/README.md names the framework docs", bool(re.search(r"framework", body, re.I)))` passes on the bare word.
  Fix: match the sentence the README must carry.
- [nit] Tail, grouped by root cause: C2 at `scripts/_install_tooling.py:145` and the `phase_docs` docstring at `scripts/new-wiki.py:773-775` (neither lists the local README the same functions now write); `scripts/new-wiki.py:957` reads `# B1— mkdir + git init` where the original read `# B1 — mkdir + git init`; S15 `tests/scripts/test_search_mode.py:397` and `:409` assign `dropped` and never read it; R8 `tests/scripts/test_local_folder.py:144` `summary = {}` after `except ValueError` hides the parse error; S17 `tests/scripts/test_standalone.py:369` `_RENDERED: list[str] = []` is module-level mutable state (a test cache).

Unverified:
- Whether `install-wiki.ps1 -RefreshOnly` maps the FAILED output to a non-zero exit (the wrapper was not read; the first finding assumes it runs `--mode tooling` or `wiki-upgrade.py`). The Change risk lens read `install-wiki.ps1:172-215` and reports `exit $LASTEXITCODE`.
- The brief said 62 files; the diff has 54 headers. The read-depth table below lists all 54.
- Leftover (3), `validate_folder` accepting a bare `--folder best-practices`: the lens judged it not a defect (Case 1 is the guard's stated design, "safe regardless of taxonomy"; the diff makes the folder exist in every new wiki). Change risk lists it as a suggestion on its axis.

Read depth (Standards lens): every one of the 54 files `in full` (the whole 2,869-line diff in six chunks; repo files only at cited lines). The files are listed in the file table under Change risk.

| Rule / section | Verdict | Search |
|---|---|---|
| S1 Mysterious Name | clear | identifiers in added Python read in context |
| S2 Duplicated Code | found | `_run` x3, lint subprocess x2, summary literal x2, remove scans |
| S3 Feature Envy | clear | new helpers read in context |
| S4 Data Clumps | found | the 8-key `summary` literal in two tests (in the S2 finding) |
| S5 Primitive Obsession | clear | `failed` entries are dicts, the repo's convention |
| S6 Repeated Switches | clear | no new mode branch |
| S7 Shotgun Surgery | found | MERGED_TAXONOMY omits best-practices/local |
| S8 Divergent Change | clear | `_guarded` sits with the install code it serves |
| S9 Speculative Generality | clear | every new helper has a caller |
| S10 Message Chains | clear | none added |
| S11 Middle Man | clear | none added |
| S12 Refused Bequest | clear | no subclasses |
| G25 Magic numbers | clear | `0o444`/`0o644` in a test; version thresholds follow the bump-check convention |
| F3 Flag Argument | clear | none added |
| R1 Answers and mutates | clear | `_guarded` mutates `failed`; covered by N7 |
| N7 Hidden side effect | found | `_install_tooling.py:222` |
| C5 Commented-out code | clear | grep of added comment lines |
| R26 New code nothing uses | found | `test_standalone.py:170`; every other new function and constant has a caller (grep) |
| S15 Dead Code | found | `_install_tooling.py:200`; the `dropped` nit |
| C1 Metadata in comment | clear | task numbers follow repo precedent |
| C2 Obsolete comment | found | wiki-map-compile:375, _wiki_config:103, _install_tooling:145, new-wiki:773-775 |
| C3 Redundant comment | clear | added comments read |
| R2 TODO with no next step | clear | grep TODO/FIXME in added lines: none |
| N2, N3, N5, N6, R3 (Names) | clear | read in context |
| S13, G34, S14, G19, G28, G29, R4, G31, G16 (Functions) | clear | longest new body `seed_toolset`, about 25 lines |
| S16, G8, G7, G17, G18, G13, S18, R5, R6, G35, G1 (Classes) | clear | none added |
| S17 Global Data | found | test_standalone:369 (nit) |
| R7, R9, R10, R11 (Error handling) | clear | `reason` is `<Class>: <message>`; `_held` uses try/finally; the plan asks for one failure not to stop the rest |
| R8 Absence sentinel | found | test_local_folder:144 (nit) |
| G4 Overridden safety | found | the exit-0 path, first finding |
| T1 Behaviour changed, no test | clear | except the exit-code path, in the first finding |
| T3, T5, R12, R13, R14 | clear | nine answer pairs pinned; each test sets its own temp config |
| T6 | n/a | not a bug fix |
| R15 Softened assertion | found | check.py:372 |
| T4 Test skipped | found | test_global_toolset:166/189/203 and :459 |
| PY1, PY2, PY3, PY7, PY8, PY10 | clear | none present; plain test functions as the repo's existing tests |
| PY9, PY11 | clear | expected values typed out; the mutation pass is not claimed as proof |
| PY4-PY6, Boundary, Concurrency, Refactoring | n/a | no async, arithmetic, threads or refactor claim |
| Leftover (1) CONTAINER_FOLDERS comment | found | wiki-map-compile:375 |
| Leftover (2) MERGED_TAXONOMY and SCAFFOLD comment | found | _wiki_config:103, :112 |
| Leftover (3) validate_folder | clear | see Unverified |
| Leftover (4) M20, M22, M79 | found / clear | M20 and M22 equivalent but the clause is dead; M79 pinned by `test_shipped_local_readme_has_no_template_placeholder` |

Well built: the `_guarded` failure path has tests for a held file, a plain file in the way, an unwritable README and an unremovable folder; the taxonomy is pinned across all nine answer pairs; the hand mutation pass (89 of 92 killed, killing tests added for three survivors) is real evidence.

## Spec

Spec: `plan.md` and `requirements.md`, with `checkpoints.md` overriding where Mark's answers changed the plan. Notebook steps 6-8 and 13-16 are outside this diff and not checked.

- [important] `.do-code-change/243-framework-docs-master/checkpoints.md:92` — step 17's red-then-green is not met for `local-readme-project-none`, which passed on the old copy on both models, so its red rests on a script check, not the suite.
  Intent: "a case that passes on the old copy → not counted as proof" (plan.md step 17, Failures).
  Implemented: checkpoints.md:92 "`local-readme-project-none` passed on the old copy on both models"; checkpoints.md:93 records the recommendation "count the free old-vs-new script check as the red"; Mark's "ok please run" answers the stubs re-run only. The stubs case never ran red on the old copy in the suite.
  Affected: the done criterion "every case 'red then green' on Sonnet and Opus" (plan.md:302) is unmet for both new cases; the baselines record green.
  Fix: Mark decides in writing whether the free script check counts as the red; otherwise fix the harness (old-copy sessions run the export's new-wiki.py) and rerun both cases red-green.
- [suggestion] `scripts/wiki-update.py:710` — `--folder best-practices/local` is refused in any wiki that lacks `wiki/best-practices/`.
  Intent: "folder guards ... that rejects or mishandles best-practices/local -> fixed if the scaffold's own README trips it, otherwise listed in the hand-back" (plan.md step 3, Failures).
  Implemented: wiki-update.py:685-686 (Case 2) and 710 "would create a NEW top-level folder"; `_wiki_config.py:112-113` MERGED_TAXONOMY omits the path. A new wiki passes through Case 1 (wiki-update.py:680-681), so the scaffold's own README does not trip it. The hand-back (implement-log.md:26-29) lists the bare-`best-practices` pass and the MERGED omission, not this refusal.
  Affected: a user filing into `best-practices/local/` in an existing wiki gets an error until the folder is made by hand (card #248).
  Fix: add `best-practices/local` to MERGED_TAXONOMY, or list the refusal in the hand-back and on #248; decide whether bare `--folder best-practices` stays accepted.
- [suggestion] `tests/skills/new-wiki/check.py:391` — the shared scaffold guard still names the old path, so it cannot fail.
  Intent: "its path moves to `wiki/best-practices/framework` because the old path can no longer hold a copy (a vacuous check)" (plan.md step 17, Cases).
  Implemented: check.py:391 `pdir, fw = wiki / "project", wiki / "project" / "best-practices" / "framework"`; the shared branch is unchanged, as checkpoints.md:91 records (overridden by the writer's answer). The new `scaffold-local` kind (check.py:358-378) holds the live guard.
  Affected: the shared no-copy check passes for any wiki.
  Fix: note it as a known vacuous check in the suite README, or move the shared guard through a writer case.
- [nit] `scripts/wiki-map-compile.py:375` — comment not updated after `best-practices` joined the set (plan step 4b); line 378 is `CONTAINER_FOLDERS = {"research", "project", "best-practices"}`.
  Fix: name best-practices/ in the comment.
- [nit] `scripts/_wiki_config.py:103` — the SCAFFOLD_TAXONOMY comment is stale (leftover 2): "What a default scaffold creates: both halves with stubs, plus sessions/." while `taxonomy_for` now appends the folder; suite fixtures read the constant as the folders a default /new-wiki creates.
  Fix: update the comments; decide whether SCAFFOLD_TAXONOMY includes the folder.
- [nit] `.do-code-change/243-framework-docs-master/plan.md:188` — the expected `wiki_folders` entry in `.claude/wiki-config.json` is not met.
  Intent: "`best-practices` is in the wiki's README folder list and in `.claude/wiki-config.json`'s `wiki_folders`" (plan.md step 3).
  Implemented: new-wiki.py:1243 `"wiki_folders": {"project": args.project_folder, "research": args.research_folder},` (the config holds the two answers); the folder key is `best-practices/local` (new-wiki.py:1059). The correction is only in implement-log.md:25; checkpoints.md records no approval.
  Fix: amend plan.md step 3 and the folder_notes line, or record the correction in checkpoints.md.
- [nit] `CHANGELOG.md`, 2026-11-19 entry, "What" bullet — "finishes the rest and exits 1" holds for `--phase docs` only.
  Intent: "`phase_docs` exits 1 with `FAILED <path>: <reason>`; the global install prints them the same way" (plan.md step 1). Implemented: `phase_docs` returns 1 on `failed`; `print_summary` prints the INCOMPLETE line and returns nothing, and the diff does not change the global install's exit path.
  Fix: say "`--phase docs` exits 1; the global install prints INCOMPLETE" (or make the install exit 1: see the Change risk axis).

Unverified:
- M22's equivalence rests on pathlib returning nothing for a non-directory parent; not run.
- `test_global_toolset.py`'s held-file tests return with no check off Windows; the README-replacement failure is proven by a read-only file, not plan.md step 2's open-handle case.
- The qmd "searched as any entry" evidence (implement-log.md:38) was not re-run.
- Writer-saved case text in `cases.json` against the writer's reply was not checked (additions only).
- The six practice links and notebook steps 6-8, 13-16: outside this diff.

Checks made:
- The three agentic-design practice pages the six docs link to exist in `C:\github.com\project-notebooks\notebooks\agentic-design\wiki\research\wiki\` (`wiki-best-practices-authoring.md`, `-frontmatter-and-tiers.md`, `-context-loading.md`), found by Glob.
- Link-depth arithmetic read by me: a doc at `global-toolset/wiki/best-practices/framework/` reaches `notebooks/` in four `../`, so the `../../../../agentic-design/...` and `../../../../llm-wiki-bootstrap/...` links are at the right depth; the wiki-seed skill pages' `../../../wiki/best-practices/framework/` links are unchanged in depth.

Read depth (Spec lens): all 54 files `in full` (diff); see the file table.

| plan step or requirement | found / clear / n/a | search or reason |
|---|---|---|
| 1 | clear | `failed` appears only in `seed_toolset`, never in `toolset_status`; 13 new checks in test_global_toolset.py (exit-code path: see findings) |
| 2 | clear (overridden, checkpoints.md:82) | `toolset_files` adds the README; the remove scan covers only the old folder and the pack; `test_user_files_in_local_are_untouched` |
| 3 | found | wiki-update.py:710; plan.md:188; taxonomy over 9 pairs in test; source guard before B1 (new-wiki.py:950-962) |
| 4 | clear | `sample_titles` hunk; no folder list in wiki-search SKILL.md; lint files not in the diff |
| 4b | found (nit) | wiki-map-compile.py:375 and 378 |
| 5 | clear | repo grep for the old path: only CHANGELOG older entries, the test scan and PENDING records |
| 6, 7, 8, 13, 14, 15, 16 | n/a | notebook steps, outside this diff |
| 9 | clear | each doc: line under frontmatter, `../../../../agentic-design/` links, versions 10/4/4/17/20/3 |
| 10 | clear | rubric span, anchors, no "code read beyond" in framework-docs; `status: proposed` written at wiki-update.py:830, stripped at wiki-promote.py:173-185 |
| 11 | found (nit) | INSTALL-INVENTORY row in section C; docs point to one source; CHANGELOG exit claim |
| 12 | clear | template lines 91 and 161 only; lines 36 and 51 untouched |
| 17 | found | checkpoints.md:92; check.py:391; PENDING rows present; cases.json additions only |
| Invariants: replace/remove/other pack, line endings, `--check` exit and no writes, user files in local/, search exclusions, `{{TOOLSET_DIR}}`, scripts name no agentic-design, framework-contract exemption | clear | existing checks kept; `--check` branch returns before `seed_toolset` (new-wiki.py:790-803); no old path in skills/ or agents/; no added line names agentic-design |
| Invariant: six practice links resolve | n/a (unverified) | notebook files outside this diff |
| Out of scope: copy, drift check, master note; Phase B re-run unchanged; pool.json, _cycle_common, wiki-cycle check, old CHANGELOG entries | clear | no such hunks; phase_b hunks are guard, folder_notes and README render only |
| Leftover (1), (2) | found | wiki-map-compile:375; wiki-update.py:710; _wiki_config:103 |
| Leftover (3) M20, M22, M79 | clear | M20: `toolset_files` keys never under the old path; M79: `_render_template` replaces `{{k}}` only and the shipped text has none; M22 see Unverified |

Well built: the per-file `_guarded` keeps one held file from stopping the refresh and `failed` stays out of `state`; the source-missing check runs before any folder is created; the new tests pin the user-file guarantee and the old-copy removal.

## Change risk

The lens ran because `scripts/_install_tooling.py` is HIGH (a data migration: the global install now deletes the old `wiki/project/best-practices/framework/*.md` copy and its emptied folder in the user's toolset). The history script ran over the HIGH and MEDIUM files (exit 0, 27 removed lines searched); three FIX-marked removed lines were comments, a docstring and the hand-built spec path (`wiki-update.py:1263-1264`, fix 4b38144), whose behaviour the lens found kept.

File table (triage; read depth per axis: S = Standards, P = Spec, C = Change risk):

| File | Risk | Part | S | P | C |
|---|---|---|---|---|---|
| `scripts/_install_tooling.py` | HIGH (data migration, deletes installed files) | 1 | in full | in full | in full |
| `scripts/_wiki_config.py`, `scripts/new-wiki.py`, `scripts/wiki-update.py`, `scripts/wiki-map-compile.py`, `scripts/wiki-qmd-query.py` | MEDIUM (business logic, state; taxonomy and spec lookup) | 1 | in full | in full | in full (qmd: hunk only) |
| `framework-docs/*.md` (6 files) | MEDIUM (ingest prints the tier rubric from `wiki-frontmatter-best-practices.md`) | 1 | in full | in full | in full (diff) |
| `agents/wiki-ingester/wiki-ingester-reading-list.json`; `skills/**` (16 files); `templates/CLAUDE.md.tmpl`, `templates/feeds.md.tmpl`; `seed/**` (3); `wiki-seed/**` (3); `CLAUDE.md`, `INSTALL-INVENTORY.md`, `V2_ROADMAP.md`, `CHANGELOG.md`, `.claude/do-code-change.json` | LOW (docs, path text, config) | 1 | in full | in full | in full (diff) |
| `tests/scripts/` (test_global_toolset, test_link_gaps, test_local_folder, test_search_mode, test_standalone); `tests/skills/PENDING.md`, `tests/skills/new-wiki/{baseline-opus.json, baseline-sonnet.json, cases.json, check.py}` | LOW (tests, eval records) | 1 | in full | in full | in full (diff) |

No earlier round, so nothing is out of round.

- [important, needs-a-human] `scripts/new-wiki.py:510-514` (and `:911-916`), `scripts/wiki-upgrade.py:68-69` — a global refresh whose toolset write or remove failed still exits 0.
  Quotes: `_print_tooling_summary(summary)` / `if summary.get("frontmatter_failed"):` … `return 0`; wiki-upgrade: `print_summary(summary)` / `return 0`. `status["failed"] = failed` (`_install_tooling.py:257`) is only printed (`:1394-1397`).
  Before: `(root / rel).unlink()` raised, `install_tooling` wrapped it in `InstallIncomplete` (`_install_tooling.py:647-650`), and both entry points returned 1 (`wiki-upgrade.py:62-64`, `new-wiki.py:504-506`). CHANGELOG line 35 says the refresh "exits 1"; true only for `--phase docs` (`new-wiki.py:815-817`).
  Path: `install-wiki.ps1:172-186` (no `-TargetFolder` runs tooling), `:211-215` `exit $LASTEXITCODE`.
  Blast radius: the remove loop runs after the add loop regardless (`_install_tooling.py:251-256`). If the new path alone cannot be written (the case `test_write_failure_is_listed_failed_rest_refreshed` builds), the spec exists nowhere; `wiki-update.py:1280-1281` prints `tier rubric: not found` and ingest goes on choosing tiers; the fallback at `wiki-update.py:1265` resolves to `~/.claude/framework-docs/` because `CC_GLOBAL_WIKI_SCRIPTS_DIR = CC_GLOBAL_DIR / "wiki-scripts"` (`_install_tooling.py:32`) and no install creates it. Phase B's `--install-global-if-missing` (`new-wiki.py:903-914`) then scaffolds anyway. Mitigation: `toolset_status` recomputes from disk, so `--mode status` reports stale.
  Fix: return 1 from both tooling paths when `summary["toolset"].get("failed")`, as `frontmatter_failed` already does, or make the CHANGELOG promise true for this path.
- [suggestion, needs-a-human] `scripts/_install_tooling.py:198-200` and `:254-256` — the remove scan follows whatever `root / wiki/project/best-practices/framework` resolves to.
  Not reproduced (no shell to create a junction): `old_docs.glob("*.md")` then `unlink()` would delete the link target's `.md` files.
  Fix: refuse when the realpath is outside `root`.
- [suggestion] `framework-docs/wiki-frontmatter-best-practices.md` (vendor-post paragraph and the tier 2 row) — ingest behaviour changes with an undefined test.
  Quote: "An official vendor post with something checkable behind it (code, docs, a public benchmark) is tier 2; one that is pitch alone is tier 4." The wiki-seed page says "Tier 4 never auto-ingests." "Checkable" is undefined; `test_the_rubric_span_holds_the_vendor_post_rule` pins the sentence's wording, not any tier decision.
  Fix: define "checkable" with an example and say what happens to existing tier-2 vendor entries.
- [suggestion] `scripts/wiki-update.py:680-681` (validate_folder Case 1: "top segment already exists on disk … safe regardless of taxonomy") — every new wiki now has `wiki/best-practices/` (`_wiki_config.py:135`), so `--folder best-practices/<anything>` passes without `--allow-new-top-folder`; before, it was refused (Case 4).
  Fix: add `best-practices/local` to `MERGED_TAXONOMY`. Checked, no mismatch with wiki-promote for `best-practices/local`: both accept it in a new wiki and both refuse in a wiki without the README.

Regressions: one found, the removed exit signal in the first finding (`unlink`/`copyfile` raising into `InstallIncomplete`); no fix commit in the history names those lines, so it is a removed signal, not a re-added line. FIX-marked lines disposed: 4b38144 (`wiki-update.py:1263-1264`) behaviour kept (toolset, then `framework-docs/`) and covered by both `test_spec_lookup_*` tests; f202b1f (`new-wiki.py:943`) comment only, guard intact at `new-wiki.py:969-973`; 6f4a02d (`_wiki_config.py:121`) docstring only. Searched: unlink, copyfile, InstallIncomplete, frontmatter_failed, _guarded, tier_rubric_text, already_in_repo.

Untested changes:

| Function | Risk | What no test covers |
|---|---|---|
| `seed_toolset` failed entries to exit status (`new-wiki.py:500-514`, `:903-914`, `wiki-upgrade.py:61-69`) | HIGH | no exit-code test; `test_global_install_summary_names_failed_paths` checks printed text only |
| old-folder link target (`_install_tooling.py:198-200`, `:254-256`) | MEDIUM | nothing |
| `tier_rubric_text` None branch after a failed spec write (`wiki-update.py:1280-1281`) | MEDIUM | the spec-lookup tests cover only the fallback path |
| `validate_folder` with `best-practices/` present (`wiki-update.py:680`) | LOW | nothing |

Coverage (lens table): `_install_tooling.py` HIGH, diff in full plus file 150-270, 618-660, 770-820, 1205-1230, 1360-1410, history yes, tests yes. `new-wiki.py`, `_wiki_config.py`, `wiki-update.py`, `wiki-map-compile.py` MEDIUM, diff in full plus the cited ranges, history yes, tests yes. `wiki-qmd-query.py` MEDIUM, diff hunk only, history yes, tests yes. `wiki-upgrade.py` (caller of a HIGH file) file 20-80, no exit-code test. `framework-docs/` x6 MEDIUM, diff in full, history not in the output for five, tests yes. Everything LOW, diff in full.

Unverified:
- A second concurrent install, and `install-wiki.sh`'s exit handling (not read).
- Whether any skill reads `wiki_folders` from the project config (the grep covered `*.py` only).
- Whether the held-file test passes on this machine (not run).
- The 62 versus 54 file count: the brief's figure was wrong; the diff has 54 headers.

Well built: the new-path tier-rubric lookup keeps the old fallback order, and the local README's bytes are compared rather than re-rendered.
Limits: no shell, so no tests were run and no junction or held file was created; history covers only the HIGH and MEDIUM files; the exit-code finding rests on reading the code paths, not on a run.

## needs-a-human

- The first Change risk finding (global refresh exits 0 after a failed toolset write or remove; a failed new-path write plus the old-copy removal leaves the spec nowhere): a deletion in the user's installed toolset, which a green suite does not cover.
- The second Change risk finding (the old-folder remove scan following a link outside the toolset root).

## Summary

Standards: 11 findings across the list above (worst: important, three: the exit-0 path on a failed refresh, a skipped case recorded as a pass, an unused test constant). Spec: 7 findings (worst: important, step 17's red-then-green not met for `local-readme-project-none`). Change risk: 4 findings (worst: important, the refresh exits 0 after a failed write, with no exit-code test). The Standards and Change risk axes agree on the exit-0 path and on `MERGED_TAXONOMY` missing `best-practices/local`; the Spec axis agrees on both of those and on the CHANGELOG's exit claim, so those three are worth acting on first. The three stale comments (`wiki-map-compile.py:375`, `_wiki_config.py:103`, `new-wiki.py:773-775`) were listed leftovers and are confirmed by two axes. The three equivalent mutants are judged equivalent by two lenses, one of which finds the guarded clause dead code. All 54 files were read in full by Standards and Spec and in full (diff) by Change risk, except `wiki-qmd-query.py`, read as its one hunk.

VERDICT: Standards FINDINGS · Spec FINDINGS · Change risk FINDINGS · needs-a-human 2
