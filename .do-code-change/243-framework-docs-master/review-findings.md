# Review report, round 2 (focused): 243-framework-docs-master

Fixed point 7b66e2a92fc2cfa3892050f143bd35fe0e6bd40d; HEAD c9a7c89; round 1 reviewed 88e9482. Change under review: the fix round's diff (`git diff 88e9482 c9a7c89`) in the files the fix moved, plus the sibling sites of each addressed finding. Files round 1 reviewed and the fix left alone are out of this round, and nothing new is raised in them. The brief asked for no skip; all three lenses ran, in the foreground (each came back as a launch notice and its report arrived on completion). Lenses ran at the default one-tier-down model. There are no untracked files outside `.do-code-change/`. Spec source: `plan.md`, `requirements.md`, `checkpoints.md`, `doubt-log.md` (resolved from the brief).

## Standards

- [suggestion] S2 `scripts/_wiki_config.py:114` and `:136`: `"best-practices/local"` is now written in `MERGED_TAXONOMY` and again in `taxonomy_for()` (`folders.append("best-practices/local")`), so one fact lives in two places. Fix: one module constant used in both.
- [suggestion] PY9 `tests/scripts/test_global_toolset.py:635-638`: the scaffold test discards stderr and asserts only `code == 1 and not target.exists()`. Traced against `phase_b` (new-wiki.py 826-962), it passes for the right reason today: the toolset branch is the only `return 1` reachable with these args. But if `seed/best-practices-local/README.md` were ever missing, the unfixed code would also exit 1 with no target and the test would stay green. Fix: assert the mocked `_install_tooling` was called once and that stderr holds "the global toolset refresh is incomplete". `_ArgsDefaultingToNone` returns None for any misspelt attribute, which also hides argument-name drift.
- [suggestion] R14 `tests/scripts/test_global_toolset.py:575` (`sys.modules[module_name] = mod`) and `tests/scripts/test_local_folder.py:420`: modules are loaded under fixed names and registered process-wide, never removed. Fix: drop the registration unless needed, or pop the entries afterwards.
- [suggestion] T4 `tests/scripts/test_global_toolset.py:172-174, 196-198, 211-213, 469-471`: the `_skip` cases record no check, so off Windows (and as root) the held-file and read-only behaviour is untested and nothing in the run footer counts them. Fix: add a skip count to the run footer, or run those cases on a Windows leg.
- [nit] `scripts/new-wiki.py:779-780`: the reflowed `phase_docs` docstring leaves a short line ("global-toolset notebook. No project wiki") before "carries a copy any more". Fix: reflow the paragraph.

Unverified:
- That the dropped `not in files` clause in `toolset_status` was dead: the Standards lens did not read `toolset_files`. (Spec and Change-risk lenses and my own check below read it and found it dead.)
- The `"FAILED " in out` assertions assume `_print_tooling_summary` prints to stdout; the lens did not resolve the alias. (`print_summary` prints, `_install_tooling.py:1395-1398`.)
- That a bare `--folder local` now resolves to `best-practices/local` is untested (wiki-promote.py:110,121; wiki-update.py:693).
- Nothing was executed; test outcomes come from reading.

Checks made:
- Every caller of `print_summary` / `_print_tooling_summary` / `install_tooling` / `_install_tooling` found by Grep: wiki-upgrade.py:61/68, new-wiki.py:500/510 (phase_tooling), 907/915 (phase_b); each now returns 1 on a failed toolset write. `phase_docs` already did. Test files call the functions directly.
- The Phase B test's earlier `return 1` paths (new-wiki.py 831, 837, 842, 901, 918, 944, 962) traced by me: none fires with the test's args.
- Standards-4: `toolset_files` keys never lie under `wiki/project/...`, so the dropped clause was always true and the output is unchanged.

Read depth: every fix-round hunk of every moved file was read; each file is `in part` as a whole file because the lens read around the hunks (details in the file table). Only the comment lines at `_install_tooling.py:144-149` were seen by Grep alone, not by the lens's own read. No retry was spawned.

| Rule / section | Verdict | Search |
|---|---|---|
| S1 Mysterious Name | clear | new identifiers read in context |
| S2 Duplicated Code | found | `_wiki_config.py:114` vs `:136` |
| S3 Feature Envy | clear | new helpers read |
| S4 Data Clumps | clear | summary dict read once |
| S5 Primitive Obsession | clear | literal read in context |
| S6 Repeated Switches | clear | no new mode branch |
| S7 Shotgun Surgery | clear | the three exit sites are one concept, each listed |
| S8 Divergent Change | clear | none |
| S9 Speculative Generality | clear | none |
| S10 Message Chains | clear | none |
| S11 Middle Man | n/a | no new forwarding class |
| S12 Refused Bequest | n/a | only subclass overrides `__getattr__` |
| G25 Magic numbers | clear | env values read against phase_b:903 |
| F3 Flag Argument | clear | no new boolean parameter |
| R1 Answers and mutates | clear | helpers read |
| N7 Hidden Side Effect | clear | helper names read |
| C5 Commented-out Code | clear | none added |
| R26 New code nothing uses | clear | Grep: `_skip` 4 uses, `_load_script` 3, `_install_summary_with_failed_toolset` 3, `_ArgsDefaultingToNone` 1, new tests in the run lists |
| Comments (C1 C2 C3 R2) | found | only nit above; C2 `_wiki_config.py:103-104` checked against `taxonomy_for` |
| Functions (S13 G34 S14 G19 G28 G29 R4 G31 G16 S15) | clear | S15 dropped clause confirmed dead (see Checks made) |
| Classes, modules, boundaries (S16 G8 G7 G17 G18 G13 S17 S18 R5 R6 G35 G1) | clear | `sys.modules` write counted under R14 |
| Error handling (R7 R8 R9 G4 R10 R11) | clear | G4 is the T4 skips; new `_err` lines name the FAILED lines |
| Tests (T1 T3 T5 T6 R12 R13 R15) | clear | each of the three exit paths and `validate_folder` has a test |
| R14 / T4 | found | lines above |
| Python (PY1-PY8, PY10, PY11) | clear / n/a | no cast, Any, async, third-party import; plain-function convention of the repo's test scripts kept |
| PY9 | found | the scaffold test |

Well built: the three exit-code tests reach the intended branches through the real `phase_b` and `seed_toolset`, and the `validate_folder` test fails without the MERGED_TAXONOMY entry.

## Spec

- [suggestion] `scripts/new-wiki.py:920`: the scaffold's failure message says "fix and re-run", but a re-run only warns and goes on.
  Intent: CHANGELOG.md:16 "a scaffold's `--install-global-if-missing` stops before it creates the project" (the stop itself is met).
  Implemented: `_install_tooling.py:1262` `"complete": not missing and not not_checked`; a stale toolset is not in `missing` (`:1226-1227`), so the re-run takes `new-wiki.py:924-927` (`elif not tooling["current"]:` warns "not refreshed here; run `install-wiki.ps1 -RefreshOnly`") and continues to B1 at `:969`.
  Affected: a user who frees the held file and re-runs gets a project whose toolset docs are still not refreshed. The stale state existed before the change, so it is not a regression.
  Fix: name the repair command in the message (`install-wiki.ps1 -RefreshOnly` or `new-wiki.py --phase docs`).
- [nit] `CHANGELOG.md:16`: "A refresh that cannot write or remove one file now lists it as `FAILED`, finishes the rest and exits 1" holds only for toolset files; `_install_tooling.py:648-651` wraps every other failure in `InstallIncomplete`, which stops the install. Fix: say "a toolset refresh".
- [nit] `plan.md:23`: step 1 says the global install "prints them the same way and says the refresh is incomplete", with no exit code and no scaffold stop; the fix round added both (`checkpoints.md:99`, an orchestrator brief, not a Mark answer). The outcome matches the earlier `InstallIncomplete` path (exit 1 before B1), except that the prune (`:802`) and manifest (`:814`) steps now run. Fix: amend step 1 to record the exit code and the stop.

Unverified:
- `report_incomplete` (`_install_tooling.py:1299`) was not read, so whether the old log file still matters is unknown.
- That `_normalize_target_folder` (wiki-promote.py:105-106) accepts `best-practices/local` in a wiki without the folder has no test (`test_local_folder.py:418-429` covers `validate_folder` only). Not run.
- `checkpoints.md` lines 1-85, `requirements.md` and `doubt-log.md` were searched by Grep, not read in full; `install-wiki.sh` 176-183 and 261-290 were read with context only.
- No test was run.

Checks made:
- The requester's check (Phase B): the stop after a failed toolset write returns 1 before the project folder exists, the same outcome as the earlier `except InstallIncomplete` branch (new-wiki.py:909-911). I confirmed both branches by reading them.
- Other callers that still exit 0 after a failed toolset write: none (the Standards "Checks made" lists the callers; `install-wiki.ps1` passes `$LASTEXITCODE` and `install-wiki.sh` `exit $?` / `$PHASE_B_EXIT` through, per the Spec and Change-risk lenses).

| Check / finding | Verdict | Search |
|---|---|---|
| A Phase B stop vs the earlier InstallIncomplete outcome | found | nit 3: same exit and stop; prune and manifest now run before the stop |
| B other callers exit 0 after a failed write | clear | Grep `print_summary\|_print_tooling_summary\|install_tooling\|_install_tooling(\|seed_toolset` over scripts, tests, wrappers: all CLI exit paths return 1 |
| C new tests prove the behaviour | clear | only the failed-toolset `return 1` is reachable; red on the unfixed code (see also Standards PY9 suggestion) |
| D MERGED_TAXONOMY accepts best-practices/local | found | accepted by both guards; bare `local` now auto-prefixes (see Change risk); plan is silent on it |
| E CHANGELOG sentence | found | nit 2 |
| F dropped clause | clear | clause always true; output identical |
| standards-1/risk-1/spec-7 | clear | exit 1 on all three paths |
| standards-7/spec-2/risk-4 | clear | validate_folder and promote accept the folder |
| spec-4/5 comments | clear | `wiki-map-compile.py:375`, `_wiki_config.py:103-104` |
| left-open items | not re-raised | per the brief |

Well built: the Phase B and `wiki-upgrade` tests trigger the real `seed_toolset` failure through a plain file, not a mock, and the wrappers pass every exit code through.

## Change risk

| File | Risk | Why | Part | Standards | Spec | Change risk |
|---|---|---|---|---|---|---|
| `scripts/_install_tooling.py` | HIGH | a guard clause removed from the scan whose result feeds file deletion in the user's toolset | 1 | in part (changed hunks; 144-149 by Grep) | in part (changed hunks) | in part (hunk 194-201 in full) |
| `scripts/new-wiki.py` | MEDIUM | exit-code and state change in phase_tooling and phase_b | 1 | in part (changed hunks) | in part (changed hunks) | in part (hunks 514-516, 919-921 in full) |
| `scripts/wiki-upgrade.py` | MEDIUM | exit code of the global upgrade | 1 | in part (all of `main`) | in full | in part (40-78) |
| `scripts/_wiki_config.py` | MEDIUM | widens what the folder guards accept | 1 | in part (all changed lines) | in part | in part |
| `scripts/wiki-map-compile.py` | LOW | comment | 1 | in part (368-377) | in part | not read |
| `CHANGELOG.md` | LOW | docs | 1 | in part (changed line) | in part | not read |
| `tests/scripts/test_global_toolset.py` | LOW | tests | 1 | in part (all new tests in full) | in part | in part |
| `tests/scripts/test_local_folder.py` | LOW | tests | 1 | in part (new test in full) | in part | in part |
| `tests/scripts/test_standalone.py` | LOW | tests | 1 | in part (162-172) | in part | grep only |

Files round 1 reviewed and the fix round did not touch are out of this round. The removed-line history (16 lines, all searched) shows no earlier fix or security commit on any removed line; the script's FIX marks are only because the fix commit's own subject says "fix round".

- [important] `scripts/new-wiki.py:925`: a re-run after a failed toolset write warns and proceeds instead of stopping or refreshing. `global_tooling_status` reports the toolset as stale, not partial, so `complete` is true and the scaffold exits 0.
  Quote: `_warn("global tooling is installed but differs from the bootstrap source " f"({', '.join(tooling['stale_skills'] + tooling['stale_scripts'] + tooling['stale_agents'])}) — "`; the toolset is not in that join, so the message prints `()`.
  Mechanism: `missing` counts only `toolset["state"] == "missing"` (`_install_tooling.py:1226-1228`) and `toolset_status` reports `stale` once the root exists (`:202`).
  Fix: have the warning name the toolset docs and the refresh command, or treat a stale toolset as a reason to refresh before scaffolding.
  Test gap: the scaffold test mocks `global_tooling_status` (`tests/scripts/test_global_toolset.py:632`), so the real re-run state is never exercised.
- [suggestion] `scripts/_wiki_config.py:114` with `scripts/wiki-promote.py:109-112`: `MERGED_TAXONOMY` gaining `best-practices/local` makes a bare `local` leaf auto-prefix to `best-practices/local`. It used to be kept as-is with a warning. `_normalize_target_folder` checks only for a README under the folder (`:107`), not that the folder exists, so an existing wiki's own `local/` without a README is silently redirected. `wiki-update.py` is protected by its Case 1 (`:680`). Untested. Fix: add a promote test for bare `local`, or check the directory exists in promote.
- [suggestion] `scripts/_install_tooling.py:199-201`: the old-docs scan lists every `*.md` under `wiki/project/best-practices/framework` for removal with no name check. The removed `not in files` clause was dead (no `toolset_files` key lies under `wiki/project/`, `:153-168`), so the fix changes no behaviour, and a user's own `.md` there was already deleted. Fix: restrict to the six doc names if only the old copy should go.
- [suggestion] `scripts/wiki-upgrade.py:68-72`: a sibling of the fix's toolset check, outside its hunk and outside what the brief named. It tests only `toolset.failed`, not `frontmatter_failed`, which `new-wiki.py:511` and `:916` both test, so `wiki-upgrade` exits 0 when skills were refused. Fix: add the same check.

Unverified:
- Round-1 risk-2 and risk-3 were not in this lens's brief, so it cannot say whether the third finding is one of them (left open on purpose; if it is, it is not re-raised).
- A junction from the old path to the new one would make the scan delete freshly written docs; not checked.
- Whether any existing wiki has a top-level `local/` without a README is unknown.

Checks made:
- Returning 1 on a failed toolset write matches the `InstallIncomplete` branch (new-wiki.py:909-911); nothing project-side is written before the return. The registry entry is written before any file operation (`_install_tooling.py:243-244`), so a failed run still leaves the toolset registered.
- `install-wiki.ps1` passes `$LASTEXITCODE` through (`:215`, `:251`, `:336`); `install-wiki.sh` runs under `set -euo pipefail` (`:48`).
- `TOOLSET_LOCAL_DIR` (`wiki/best-practices/local`) is not under the old folder (`_wiki_config.py:525,527`).
- The Phase B test is not vacuous: without the check the project is created and `not target.exists()` fails.

| Question / file | Verdict | Search |
|---|---|---|
| Q1 old-docs scan deletes only old docs | found | suggestion 3; behaviour unchanged |
| Q2 phase_b re-run state | found | important finding 1 |
| Q3 callers and wrappers | found | suggestion 4 (sibling); callers clear |
| Q4 MERGED_TAXONOMY blast radius | found | suggestion 2 |
| Q5 untested surface | clear / found | each exit-1 branch has a test that would fail without it; the re-run state is untested (finding 1) |
| `_install_tooling.py` (HIGH) | found | seed_toolset, toolset_status, global_tooling_status, print_summary |
| `new-wiki.py`, `wiki-upgrade.py`, `_wiki_config.py` (MEDIUM) | found | phase_tooling, phase_b, phase_docs; main; MERGED_TAXONOMY and TOOLSET_* |

Well built: the failure list is returned and printed, and every write is guarded, so one held file does not stop the rest of the refresh.

## needs-a-human

None: no finding touches auth, authz, tokens, sessions or a production-data migration. A spec resolved, so there is no no-spec line.

## Summary

Standards: 5 findings (4 suggestion, 1 nit); worst: the scaffold test could stay green if another early return fired (PY9, a suggestion). Spec: 3 findings (1 suggestion, 2 nit); worst: the scaffold's "fix and re-run" message points at a re-run that only warns. Change risk: 4 findings (1 important, 3 suggestion); worst: the re-run after a failed toolset write warns and proceeds, and the test mocks that state away. The Spec and Change-risk lenses agree on that re-run behaviour. Acting on the Change-risk important finding and the matching Spec suggestion is worth doing. The requester's two named checks came out as follows: Phase B's exit 1 matches the earlier `InstallIncomplete` outcome, and no other caller of `print_summary` / `_print_tooling_summary` still exits 0 on a failed toolset write (the sibling `frontmatter_failed` gap in `wiki-upgrade.py` is a separate pre-existing difference). No file is read `not read` by every axis; reads are `in part` per the file table, with every fix-round hunk read.

VERDICT: Standards FINDINGS · Spec FINDINGS · Change risk FINDINGS · needs-a-human 0
