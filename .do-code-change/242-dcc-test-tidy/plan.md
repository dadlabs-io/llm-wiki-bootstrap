# Plan — tidy test_git_hooks_dcc.py (task #242)

Classification: wide refactor of the two hook test files (a shared harness, one function per check), no production behaviour change, plus one added check.

## Problem Statement

#241's review left the new hook test file with copied setup, a few unchecked return codes, and a runner that hides
non-assertion errors; one closing-line path is unasserted.

## Solution

Small edits inside the test file only: helper arguments and one constant, checked git setup and cleanup, a safer
runner, and one new check that a gitleaks block also ends on the owner line.

## Implementation Decisions

- New module `tests/scripts/_git_hooks_harness.py` (searched for: an existing shared test harness under tests/scripts — found `_samples.py` and `_fake_qmd.py`, neither a git-hooks harness). It holds `Machine` (temp HOME, install, cleanup on a failed install), `Machine.fake_dcc(exit_code, message="", ran_marker=None)`, `Machine.new_repo(name)` (each git setup call's return code asserted), `Machine.commit(r, files)`, `Machine.head(r) -> str | None`, `Machine.run(args, cwd)`, `Machine.write_words(text)` (the private-words list), `github_token()`, and `run_tests(tests: dict, argv) -> int` (unknown name: exit 2 with the known names; any exception reported as `ERROR <name>  [<type>: <message>]` and counted failed).
- `test_git_hooks.py`: each of its 18 checks becomes one `test_*` function on its own `Machine`, same assertions; the checks that relied on an earlier check's state (the allow file, the already-committed word, the local hooks) set that state up themselves. Its `--remove` check and its install checks keep their own functions.
- `test_git_hooks_dcc.py`: imports the harness; `REFUSAL` constant for both refusal tests; the pass test uses `fake_dcc(0, ran_marker=...)`.
- The new closing-line check plants a GitHub-shaped token so gitleaks blocks, with no fake dcc present.

## Testing Decisions

- Seam: the file's own checks run by name (`uv run python tests/scripts/test_git_hooks_dcc.py <test>`), as in #241.
- The refactor steps change no assertion; their evidence is all checks green before and after, and the re-freeze
  reasons recorded (manual: steps 1-2 — the full file run, 4/4 before and after, in checkpoints.md).
- manual: step 3 — `main()`'s new paths shown by running an unknown name (exit 2) and by a deliberately raising
  test name never added to the file; evidence in checkpoints.md.

## Out of Scope

- The hook, the sibling test, a python-absent test (Exclusions).

## Scope

- tests/scripts/test_git_hooks_dcc.py
- tests/scripts/test_git_hooks.py
- tests/scripts/_git_hooks_harness.py
- tools/git-hooks/README.md

## Invariants

- Every existing check still passes and still fails at the fixed point's hook — pinned by the four frozen tests
  (re-frozen with reasons where their loaded helpers change).

## Decisions needed

none (the which-findings choice is requirements Decision 1)

## Steps

1. Shared harness, and the dcc test file moved onto it (standards-3, -4, -7, -8, -9, -13) — done when the four dcc checks pass, each re-frozen with its reason. Trivial stakes: yes — test structure; no assertion loosened
2. `test_git_hooks.py` converted to one function per check on the harness (standards-2, -7) — done when all 18 checks pass as functions, each frozen green with the reason "existing check moved into a function". Trivial stakes: yes — test structure
3. The runner reports any exception and refuses an unknown name (standards-10) — done when an unknown name exits 2 with the list and every check still passes (manual: shown in checkpoints.md). Trivial stakes: no
4. A gitleaks block also ends on the owner line (standards-5, first half) — done when `test_gitleaks_block_ends_on_the_owner_line` passes, and fails against #241's fixed point (bc898ad) hook. Trivial stakes: no
5. Docstrings say why each check gets its own HOME (standards-6), and the README's Tests paragraph names the harness — done when they read so (manual: read). Trivial stakes: yes — docs
