# Plan — tidy test_git_hooks_dcc.py (task #242)

Classification: wide refactor of one test file (structure of the harness), no production behaviour change, plus one added assertion.

## Problem Statement

#241's review left the new hook test file with copied setup, a few unchecked return codes, and a runner that hides
non-assertion errors; one closing-line path is unasserted.

## Solution

Small edits inside the test file only: helper arguments and one constant, checked git setup and cleanup, a safer
runner, and one new check that a gitleaks block also ends on the owner line.

## Implementation Decisions

- `fake_dcc(exit_code: int, message: str = "", ran_marker: Path | None = None)`: writes the fake; when `ran_marker` is
  given, the fake also writes that file. The pass test calls it instead of writing the fake inline.
- `REFUSAL = "FAKE-DCC-REFUSED: tool.py changed without a run"`, a module constant used by both refusal tests.
- `Machine.__init__`: if the install fails, `self._td.cleanup()` runs before the assertion.
- `repo()`: each git setup call's return code is asserted, naming the command.
- `head()` returns `str | None` (`None` when `rev-parse` fails or prints nothing); callers assert `is not None` / `==`.
- `main()`: an unknown name exits 2 with the known names listed; a test raising anything else is reported as
  `ERROR <name>  [<type>: <message>]` and counted as failed.
- The new closing-line check plants a GitHub-shaped token (built at runtime, as `test_git_hooks.py` does) so gitleaks
  blocks, with no fake dcc present.

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

## Invariants

- Every existing check still passes and still fails at the fixed point's hook — pinned by the four frozen tests
  (re-frozen with reasons where their loaded helpers change).

## Decisions needed

none (the which-findings choice is requirements Decision 1)

## Steps

1. Harness edits (standards-3, -4, -8, -9, -13) — done when all four checks pass and each re-freeze carries its reason.
   Trivial stakes: yes — test-only structure; no assertion loosened
2. Docstring states why each check gets its own HOME (standards-6) — done when the file reads so; checks still pass.
   Trivial stakes: yes — a docstring
3. The runner reports any exception and refuses an unknown name (standards-10) — done when an unknown name exits 2
   with the list, and the four checks still pass.
   Trivial stakes: no
4. A gitleaks block also ends on the owner line (standards-5, first half) — done when
   `test_gitleaks_block_ends_on_the_owner_line` passes, and fails against #241's fixed point (bc898ad) hook.
   Trivial stakes: no
