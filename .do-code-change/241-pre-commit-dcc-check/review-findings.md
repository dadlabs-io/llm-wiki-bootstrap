# Review findings — 241-pre-commit-dcc-check, round 1

Fixed point bc898ad; change = working tree against it, `.do-code-change/` left out; 5 files, 166 added lines, one part
per axis. Prescan: clean. Read-only guard: PASS.

## Standards

- [important] `tools/git-hooks/pre-commit:31` and `wiki-seed/install.md:124` — R3, two words for one authority: the hook and README say "--no-verify only when Mark has said so", the shipped install page says "only when the machine's owner has agreed the hit is a false alarm"; the hook is copied to every machine that opts in, so every installer's blocked commits print a maintainer's name. Fix: one phrase in the hook, README and install.md, and the pinned line in the test to match.
- [suggestion] `tests/scripts/test_git_hooks_dcc.py:56-74` against `tests/scripts/test_git_hooks.py:52-67` — S2: the temp-HOME setup and `repo`/`commit` helpers are copied from the sibling test. Fix: one shared helper both import, or say why the copy stands in the docstring.
- [suggestion] `tests/scripts/test_git_hooks_dcc.py:93-95` against `:63-66` — S2 within the diff: the pass test writes its fake inline, duplicating `fake_dcc`. Fix: give `fake_dcc` a body argument.
- [suggestion] `tests/scripts/test_git_hooks_dcc.py:113` and `:138` — S2 within the diff: the same refusal setup twice. Fix: a constant or helper.
- [suggestion] `tests/scripts/test_git_hooks_dcc.py:142` — T1: the closing line changed on every block path but only the dcc path asserts it; the python-missing behaviour the CHANGELOG states has no test. Fix: assert the closing line on a gitleaks block too; a python-absent case.
- [suggestion] `tests/scripts/test_git_hooks_dcc.py:25-86` — PY10: a fixture class in the test module where the sibling keeps setup at module level. Fix: match the sibling, or say why per-test HOME needs the class.
- [nit] `tests/scripts/test_git_hooks_dcc.py:47` — N7: `repo()` creates and inits a repository; reads as a lookup. Fix: `new_repo` (the sibling uses the same name).
- [nit] `tests/scripts/test_git_hooks_dcc.py:50`/`:57` — R10: a failing install assert in `__init__` leaves the temp dir uncleaned. Fix: clean up before the assert.
- [nit] `tests/scripts/test_git_hooks_dcc.py:73` — G4: `git init`/`git config` return codes ignored. Fix: check them.
- [nit] `tests/scripts/test_git_hooks_dcc.py:156`/`:158` — R9: `main` catches only AssertionError; an unknown name is a bare KeyError. Fix: catch per test, validate names.
- [nit] `tools/git-hooks/pre-commit:19` against `:28` — R3: "NOT checked:" and "NOT CHECKED -" for one state. Fix: one form (the dcc line is the change request's text as given).
- [nit] `tools/git-hooks/pre-commit:28` — G16: the new conditional is one line where the file's other blocks are multi-line. Fix: expand it.
- [nit] `tests/scripts/test_git_hooks_dcc.py:101-104` — R8: `head()` returns `""` for no HEAD. Fix: return None.

Unverified:
- `python` vs `python3` on Mac/Linux for the hook's call; python-missing blocking (not run); no real `dcc-commit-check.py` in this repo, so the fake is the only check here.

Coverage: every every-diff rule and pasted section (Comments, Names, Functions, Classes, Error handling, Tests, Python) has a row in the lens report; found: S2, N7, R3, G16, R8, R9, G4, R10, T1, PY10; the rest clear or n/a with reasons. Shell reviewed on the language-agnostic rules (no shell section).
Well built: every branch of the new check is tested (pass, refusal, pack absent, closing line), each in its own temporary HOME.

## Spec

- [suggestion] `wiki-seed/install.md:124` — the plan says README and install.md "name the third check and the new hint"; requirements Decision 1 says "--no-verify only when Mark has said so"; install.md says "only when the machine's owner has agreed the hit is a false alarm", a different rule from the one the hook prints. Fix: match the closing line, or have Mark rule on the public page's wording.
- [suggestion] `tools/git-hooks/README.md:15` and `CHANGELOG.md:16` — the plan's manual rule says each docs sentence names behaviour a test proves; "If `python` cannot run, the shell's own error blocks the commit" has no test (that step was removed by ruling). Fix: drop the sentence, or record the untested behaviour as accepted.
- [nit] `tests/scripts/test_git_hooks_dcc.py:113-122` — plan step 3 says the test checks "the refused commit of step 1"; the test builds its own refusal. Fix: amend the plan wording.

Unverified:
- No green run recorded in the spec files (settle: run both test files). The change request's "No other file changes" against README, install.md, CHANGELOG and the test (settle with Mark or the request's author). The scope widening carries no quoted Mark ruling.

Coverage: every plan step, invariant, decision and exclusion has a row in the lens report; found: step 3 install.md (partial) and the manual rule; the rest found or clear.
Well built: the hook line is the change request's text verbatim, and the tests run real commits under a temporary HOME.

## Change risk

| File | Risk | Part | Standards | Spec | Change risk |
|---|---|---|---|---|---|
| `tools/git-hooks/pre-commit` | MEDIUM (commit behaviour on every repo) | 1 | in full | in full | — |
| `tests/scripts/test_git_hooks_dcc.py` | LOW (test) | 1 | in full | in full | — |
| `tools/git-hooks/README.md` | LOW (docs) | 1 | in part (changed hunks) | in full (changed lines) | — |
| `wiki-seed/install.md` | LOW (docs) | 1 | in part (changed hunk) | in full (changed lines) | — |
| `CHANGELOG.md` | LOW (docs) | 1 | in part (changed hunks) | in full (changed lines) | — |

No high-risk file; the change-risk lens was not run.

Standards: 13 findings (1 important: Mark's name in a shipped hook vs install.md). Spec: 3 findings (worst: install.md's rule differs from the hook's). Change risk: not run.

VERDICT: Standards FINDINGS · Spec FINDINGS · Change risk NOT RUN · needs-a-human 0
