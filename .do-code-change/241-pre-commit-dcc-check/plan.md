# Plan — the machine pre-commit calls do-code-change's commit check (task #241)

Classification: vertical slice (one behaviour added to one hook; each step is a commit outcome a person meets).

## Problem Statement

The machine-wide pre-commit checks secrets and private words but not script changes made without a do-code-change
run, so the edit gate's commit-time backstop never runs on this machine.

## Solution

Add agent-builder's call to `dcc-commit-check.py` after the private-words check, inside the same status/one-stop
flow, with a guard for a missing `python`, and reword the closing hint so it does not offer `--no-verify` as the way
past a dcc refusal. Tests drive a fake `dcc-commit-check.py` placed in the test's temporary HOME.

## Implementation Decisions

- The call sits after `private-words.sh` and before the `if [ $status -ne 0 ]` block, so every block is reported and
  the commit stops once (the change request's placement).
- Pinned shape (decision 2 folded in; the implementer must not pick another):
  ```sh
  dcc="$HOME/.claude/workflows/do-code-change/scripts/dcc-commit-check.py"
  if [ -f "$dcc" ]; then
      if command -v python >/dev/null 2>&1; then
          python "$dcc" || status=1
      else
          echo "pre-commit: BLOCKED — NOT checked: python not found for the do-code-change commit check." >&2
          status=1
      fi
  else
      echo "pre-commit: do-code-change commit check NOT CHECKED - pack not installed" >&2
  fi
  ```
- Closing line (decision 1): `pre-commit: fix the lines above. A do-code-change refusal needs a run (its message says how); --no-verify is only for a gitleaks or private-word hit you are sure is a false alarm.`
- The header comment's numbered list gains item 3 (the dcc check); the repo hand-over becomes item 4.

## Testing Decisions

- Seam: a real `git commit` in a scratch repo under the test's temporary HOME, as the existing 18 checks do; the
  dcc script is a fake written to `$HOME/.claude/workflows/do-code-change/scripts/dcc-commit-check.py` that exits 0
  or 1 and prints a marker.
- Seam for "python not found": the commit run with a PATH that holds git and sh but no python (a scratch bin folder
  with links or copies of only those), checked for the BLOCKED line.
- manual: step 4 — README and `wiki-seed/install.md` read against steps 1-3's tests (each sentence names behaviour a
  test proves).

## Out of Scope

- `dcc-commit-check.py` itself and its rules (agent-builder's; its own tests).
- Installing the changed hook on this machine is the finish: `sh tools/git-hooks/install.sh` after the commit, then a
  live clean commit.

## Scope

- tools/git-hooks/pre-commit
- tools/git-hooks/README.md
- tests/scripts/test_git_hooks.py
- wiki-seed/install.md
- CHANGELOG.md

## Invariants

- A staged secret is still blocked — pinned by "a staged GitHub token is blocked" (existing test).
- A private word is still blocked, naming file and line — pinned by the two existing private-word tests.
- Missing gitleaks still blocks as NOT checked — pinned by the existing "no gitleaks" test.
- The repo's own pre-commit still runs and can block — pinned by the existing two `_local` tests.
- `--no-verify` still commits — pinned by the existing test.

## Decisions needed

none (the two choices are Decisions 1 and 2 in requirements.md, put at Change confirmation)

## Steps

1. A commit whose dcc check refuses is blocked — done when `tests/scripts/test_git_hooks.py` passes these new checks:
   - Expected: a fake dcc script that exits 0 → a clean commit goes through, and nothing about dcc is printed.
   - Failures: a fake dcc script that exits 1 with a marker message → the commit is refused, the marker is on stderr,
     and no new commit exists (HEAD unchanged).
   - Invariant: the five Invariants above stay green in the same run.
   uses: the test file's existing `repo()`, `commit()`, `run()` helpers; no new helper.
   Trivial stakes: no
2. With the pack absent, the commit goes on and says NOT CHECKED — done when the test, with no fake dcc in HOME,
   commits a clean change (exit 0) and stderr holds "do-code-change commit check NOT CHECKED - pack not installed".
   Trivial stakes: no
3. With the pack present and no python, the commit is blocked as NOT checked — done when the test, with the fake dcc
   present and a PATH without python, gets a refused commit, the "python not found" BLOCKED line, and HEAD unchanged.
   Failures: (this step is itself the failure path.)
   new function `_path_without_python()` in the test file, searched for: "PATH", "which" in tests/scripts — found none.
   Trivial stakes: no
4. The closing hint and the docs say what the hook now does — done when the test checks the refused commit of step 1
   ends with the new closing line (no "commit anyway on purpose"), and README + `wiki-seed/install.md` name the third
   check and the new hint (manual: read against steps 1-3). CHANGELOG gets one dated entry.
   Trivial stakes: yes — wording of a message and docs; the refusal itself is pinned by step 1
