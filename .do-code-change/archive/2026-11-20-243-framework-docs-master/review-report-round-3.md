# Review report, round 3 (focused): 243-framework-docs-master

Fixed point 7b66e2a92fc2cfa3892050f143bd35fe0e6bd40d (resolves; merge-base is itself); HEAD 99757ca; round 2 reviewed c9a7c89. Change under review: fix round 2's diff (`git diff c9a7c89 99757ca`, 69 changed lines in 4 files, one part) plus the sibling sites of each addressed finding. Files round 2 reviewed and fix round 2 did not touch (`_install_tooling.py`, `_wiki_config.py` and the rest) are out of this round, and nothing new is raised in them. Left-open items from the brief were not re-raised. The Standards and Spec lenses ran at the default one-tier-down model; each came back as a launch notice and its report arrived on completion. The brief asked for no skip. No untracked files outside `.do-code-change/`. Spec source: `plan.md`, `requirements.md`, `checkpoints.md`, `doubt-log.md`, and CLAUDE.md "Step 0".

## Standards

- [suggestion] S2 `scripts/new-wiki.py:920-922` and `:931-933`: the remedy text "`install-wiki.ps1 -RefreshOnly` (or `new-wiki.py --phase docs` ...)" is written out twice in the diff, and the frontmatter/toolset exit block is repeated at `new-wiki.py:511-516`, `:916-923` and `wiki-upgrade.py:69-76`. Fix: one shared constant for the hint, one helper in `_install_tooling` for the exit mapping.
- [suggestion] S2/S7 `scripts/new-wiki.py:515` and `scripts/wiki-upgrade.py:74`: `"the global toolset refresh is incomplete (see the FAILED lines above) — fix and re-run"` keeps the vague wording fix round 2 replaced in `phase_b` (`new-wiki.py:920-922`), so one failure has two messages. Fix: use phase_b's wording at both sites.
- [nit] S1 `scripts/new-wiki.py:927`: `differs` reads like a flag but holds stale item names. Fix: `stale_names`.
- [nit] `scripts/new-wiki.py:929` says "toolset docs" where `scripts/_install_tooling.py:1279` says "global toolset docs": one state, two names. Fix: pick one.
- [nit] C3-adjacent `scripts/new-wiki.py:780`: the docstring reflow leaves the short line "    A global install (`--mode tooling`," before the next. Fix: rewrap the paragraph.
- [nit] T1 `tests/scripts/test_global_toolset.py:602-612`: the new wiki-upgrade test checks only `code == 1`, not the new stderr text. Fix: also assert the "refused" message, as the scaffold test does at `:657-658`.

Unverified: none. No test was run (read only).

Checks made:
- Round-1 standards-2 (skipped tests print SKIP and record no check) still holds: `tests/scripts/test_global_toolset.py:40-42`, `def _skip(...)` with `print(f"SKIP {test_name}: {reason}")` and no `check` call; fix round 2 did not touch it.
- Round-1 standards-1 (a failed toolset write exits 1) still holds: `new-wiki.py:819-821` (phase_docs), `:514-516` (phase_tooling), `:919-923` (phase_b), `wiki-upgrade.py:73-76`. Grep over scripts/ finds `install_tooling(` only at `new-wiki.py:500`, `:907`, `wiki-upgrade.py:61`, and `seed_toolset(` at `new-wiki.py:808` and `_install_tooling.py:795`; every caller tests `toolset.failed`.
- The warning branch `elif not tooling["current"]` is reached only for stale or not-current state (`_install_tooling.py:1228`, `:1262-1263`), so the `differs` logic is right there.
- The three new or changed tests each fail on the pre-fix code (the old warning printed `()` with no "toolset docs"; the old message had no `install-wiki.ps1 -RefreshOnly`; the old `wiki-upgrade` returned 0).

| Rule / section | Verdict | Search |
|---|---|---|
| S1 | found | `differs` (nit) |
| S2 | found | remedy string and exit block, four sites |
| S3-S12 | clear | added lines read; no new type, class, forwarding function or subclass |
| G25 Magic numbers | clear | literals in the diff read |
| F3 Flag Argument | clear | no new parameter |
| R1, N7 | clear | no new function |
| C5 Commented-out Code | clear | diff read |
| R26 New code nothing uses | clear | no new function, constant or class; new tests are in the run list (`:815-819`) |
| Comments (C1 C2 C3 R2) | found | docstring orphan line (nit); no TODO |
| Functions (S13 G34 S14 G19 G28 G29 R4 G31 G16 S15) | clear | `phase_b` grows by 4 lines; nesting not deepened |
| Error handling (R7 R8 R9 G4 R10 R11) | clear | the four exit sites read |
| Tests (T1 T3 T5 T6 R12 R13 R14 R15 T4) | found | T1 nit; no new skip; assertions exact |
| Python (PY1-PY8, PY10, PY11) | clear / n/a | no cast, async, third-party import; plain-function convention of the repo's test scripts |
| PY9 | clear | each new test fails pre-fix (see Checks made) |

Read depth: `CHANGELOG.md` in part (10-25), `scripts/new-wiki.py` in part (470-539, 770-827, 880-933), `scripts/wiki-upgrade.py` in full, `tests/scripts/test_global_toolset.py` in part (1-90, 570-827; every changed line).

Well built: the stale-warning test fails before the fix, and the scaffold test now checks that the mocked install ran once.

## Spec

- [suggestion] `scripts/new-wiki.py:920-922`: the failed-write message says "free the file named there", but the FAILED line names the file being written, not the blocker.
  Intent: plan.md line 181, "`local` exists as a plain file where the folder should be → the refresh does not raise; the README is listed in `failed` with the reason".
  Implemented: `_guarded(partial(dst.parent.mkdir, ...), dst, failed)` at `scripts/_install_tooling.py:251` records `dst` (the README path), so the user is told to free README.md while the real blocker is the `local` entry.
  Affected: a user following the message after a plain file sits where `local/` belongs.
  Fix: record the blocking parent path when mkdir fails, or word it "free the path named in the FAILED line or the entry that blocks it".
- [suggestion] `scripts/new-wiki.py:927-933`: when the stale cause is only the uv environment, `differs` is empty and the warning names nothing.
  Intent: CLAUDE.md Step 0, "a stale set is named in the plan summary with `-RefreshOnly` as the fix".
  Implemented: `stale` is true for `env == "stale"` (`_install_tooling.py:1228`), which `differs` does not include; the text reads "differs from the bootstrap source — not refreshed here". The new test sets empty lists with only the toolset stale, so this case is untested.
  Affected: a user whose only drift is the scripts' environment gets a warning that names no cause (the `()` is gone, the information is not there).
  Fix: when `differs` is empty and `env` is stale, name "the scripts' environment (uv)"; add a test.
- [nit] `scripts/new-wiki.py:920-922`, `:931-933`, `:514-516`, `:916-918`, `:819-821`, `scripts/wiki-upgrade.py:73-76`: sibling "fix and re-run" messages name no repair path as phase_b's now does (the phase_docs one has no re-run hint at all). Intent: plan.md line 23 requires only "says the refresh is incomplete", so this is consistency, not a gap. Fix: reuse phase_b's wording.
- [nit] `install-wiki.ps1:120` (`[switch]$RefreshOnly`) and `install-wiki.sh:66,85` (`REFRESH_ONLY`) are parsed but never read (Grep: no other use), so the repair `install-wiki.ps1 -RefreshOnly` named by the new text (`new-wiki.py:921`, `:932`) reaches a refresh only through the Mode prompt default (`install-wiki.ps1:172-184`). Pre-existing wording the new lines repeat; the runtime was not run. Fix: wire the switch to `-Mode tooling`, or name the command that works.

Unverified:
- `_install_tooling.py:208-220` (`_register_toolset`) and `:243-244` run before the `_guarded` loop and are not guarded: an OSError on the registry write would escape `phase_docs` and stop the rest, so CHANGELOG.md:16 "finishes the rest" holds for toolset files, not the registry. Outside this diff; a test with a read-only `linked-notebooks.json` would settle it.
- No test was run.

Checks made:
- Round-1 risk-1 / standards-1 (exit 1 from every global-tooling entry point) still holds: phase_docs `:819-821`, phase_tooling `:514-516`, phase_b `:919-923`, wiki-upgrade `:73-76`; `install-wiki.ps1` `exit $LASTEXITCODE` (`:215`), `exit $exit` (`:249-251`), `exit $phaseBExit` (`:336`); `install-wiki.sh` `exit $?` (`:183`), `exit $EXIT` (`:216-218`), `exit $PHASE_B_EXIT` (`:290`).
- (A) The new warning text is true: `()` omitted (`:931`), "toolset docs" added when the toolset is stale (`:928-929`); `--phase docs` repairs a stale toolset (`seed_toolset` add/replace/remove, `_install_tooling.py:249-257`; `phase_docs` `:808`); a re-run after a freed file proceeds because `complete` ignores toolset staleness (`_install_tooling.py:1262`).
- (B) `wiki-upgrade.py:69-72` returns 1 on `frontmatter_failed`; `print_summary` prints it (`_install_tooling.py:1369-1373`).
- (C) Every clause of CHANGELOG.md:16 verified: FAILED line printed by phase_docs (`:815`), `_print_tooling_summary` (`_install_tooling.py:1395-1398`) and wiki-upgrade; "finishes the rest" (`:249-257`, `_guarded` `:223-231`); exit 1 on all four paths; the scaffold stops before the project (`phase_b` returns at `:923`, project work starts at `:938`).
- (D) The three tests (`:602-612`, `:635-658`, `:661-678`) are in the run list (`:815-819`) and fail on the old code; the stale test's `unrelated.txt` triggers the refusal at `new-wiki.py:940-950`, so the scaffold does stop after the warning.

| Rule / claim | Verdict | Search |
|---|---|---|
| A1 warning never prints `()` | clear | `new-wiki.py:926-933`; test `:676` |
| A2 names "toolset docs" when stale | clear | `:928-929` |
| A3 empty `differs` case | found | `_install_tooling.py:1228` |
| A4 `--phase docs` is the docs repair | clear | `seed_toolset` `:234-259`, `phase_docs` `:808` |
| A5 re-run after a freed file proceeds | clear | `phase_b` `:893`, `:926`; `:1262` |
| A6 "free the file named there" is true | found | `_install_tooling.py:223-257` |
| B wiki-upgrade returns 1 on frontmatter_failed | clear | `wiki-upgrade.py:69-72` |
| C CHANGELOG.md:16 clauses | clear | four exit paths read |
| D tests prove A-C | clear | `:602-678`, run list `:815-819` |
| Sibling "fix and re-run" messages | found | nit above |
| Every entry point exits 1 | clear | Grep `install_tooling\(\|seed_toolset\(\|from _install_tooling` over scripts/ |
| Wrappers pass the exit code | clear | Grep `LASTEXITCODE\|exit \$\?` in install-wiki.* |
| `-RefreshOnly` read by a wrapper | found | Grep `RefreshOnly` in install-wiki.ps1 / .sh |
| Registry write guarded | unverified | `_install_tooling.py:208-220` |

Read depth: `CHANGELOG.md` in part (1-25), `scripts/new-wiki.py` in part (156-170, 480-539, 770-938), `scripts/wiki-upgrade.py` in full, `tests/scripts/test_global_toolset.py` in part (590-680, 790-827; every added test and the run list); siblings read in part: `_install_tooling.py`, `install-wiki.ps1`, `install-wiki.sh`.

Well built: the failed-write path records each failure and keeps running, so one held file does not stop the refresh, and each exit-1 path has a test that fails on the old code.

## Change risk

| File | Risk | Why | Part | Standards | Spec | Change risk |
|---|---|---|---|---|---|---|
| `scripts/new-wiki.py` | MEDIUM | exit-code message and warning text in phase_b; docstring | 1 | in part (changed hunks) | in part (changed hunks) | — |
| `scripts/wiki-upgrade.py` | MEDIUM | exit code of the global upgrade | 1 | in full | in full | — |
| `tests/scripts/test_global_toolset.py` | LOW | tests | 1 | in part (every changed line) | in part (every changed line) | — |
| `CHANGELOG.md` | LOW | docs | 1 | in part (line 16) | in part (line 16) | — |

No high-risk file: the change-risk lens was not run (the diff changes message text, one added exit-1 check and tests; no auth, crypto, external call, migration or removed validation). Files round 2 reviewed and fix round 2 did not touch are out of this round.

## needs-a-human

None: no finding touches auth, authz, tokens, sessions or a production-data migration. A spec resolved, so there is no no-spec line.

## Summary

Standards: 6 findings (2 suggestion, 4 nit); worst: the remedy text and the exit-mapping block are repeated across four sites, and two sibling messages keep the vague wording (S2, suggestions). Spec: 4 findings (2 suggestion, 2 nit); worst: "free the file named there" points at the README while the blocker can be the `local` entry, and a uv-environment-only stale state still gets a warning that names no cause. Change risk: not run. The axes agree on one point: the sibling "fix and re-run" messages in `new-wiki.py:515` and `wiki-upgrade.py:74` were not brought to phase_b's wording. Acting on the Spec suggestions is worth doing. Re-verification you asked for: standards-1 / risk-1 (exit 1 from every global-tooling entry point) still holds, and standards-2 (skipped tests print SKIP and record no check) still holds. Fix round 2's addressed items risk-5, spec-8, risk-8, standards-14, spec-9 and standards-17 are met as claimed, each new test failing on the old code. Every file was read in full or in part with every changed line read; none is `not read`.

VERDICT: Standards FINDINGS · Spec FINDINGS · Change risk NOT RUN · needs-a-human 0
