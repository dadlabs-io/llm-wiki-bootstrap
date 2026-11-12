# Requirements — the machine pre-commit calls do-code-change's commit check (task #241)

## Facts

- user confirmed (Mark, Discord, 2026-11-12): "probably good to do": add the commit check to the machine pre-commit; every script change in llm-wiki-bootstrap goes through do-code-change (repo gate mode `auto`, committed 79aae8b).
- earlier change request: agent-builder-bootstrap `workflows/do-code-change/reference/llm-wiki-change-request.md` (task 260) asks for exactly two lines, placed after the private-words check and before the `if [ $status -ne 0 ]` block:
  ```
  dcc="$HOME/.claude/workflows/do-code-change/scripts/dcc-commit-check.py"
  if [ -f "$dcc" ]; then python "$dcc" || status=1; else echo "pre-commit: do-code-change commit check NOT CHECKED - pack not installed" >&2; fi
  ```
  It was run by agent-builder on a scratch copy of this pre-commit: clean commit passes, a staged `.py` with no open run is refused, pack absent prints the NOT CHECKED line and the commit goes on.
- earlier change request, same file: "No other file changes, and no rows file"; the `--no-verify` sentence after a dcc refusal "is llm-wiki's wording to keep or change".
- found in `tools/git-hooks/pre-commit`: today it runs gitleaks (missing gitleaks = blocked, NOT checked), then `private-words.sh`, then on any block prints "pre-commit: fix the lines above, or commit anyway on purpose with: git commit --no-verify" and exits 1; otherwise hands over to the repo's own hook through `_local`.
- found in `tests/scripts/test_git_hooks.py`: 18 checks under a temporary HOME (install, clean commit, token, private word, allow file, `--no-verify`, repo hooks, missing gitleaks, remove). Under that HOME the dcc pack is absent.
- wiki `project/decisions/machine-wide-pre-commit-hook-gitleaks-and-private-words-2026-10-14.md`: `--no-verify` is the deliberate override; a missing tool blocks as NOT checked, never a silent pass.
- found in `tools/git-hooks/README.md` and `wiki-seed/install.md` ("Blocking secrets in commits"): both describe the hook's checks and `--no-verify`; neither names the dcc check.
- existing callers: git, through `core.hooksPath`, on every commit in every repo on the machine; `_install_tooling.py` only copies and reports the hook (install.sh), it does not read its content.
- unchanged cases: gitleaks and private-words behaviour, their messages, the hand-over to `_local`, the install and remove.
- follows from the earlier change request: the pack absent → the NOT CHECKED line and the commit goes on (not blocked).

## Exclusions

- No change to `dcc-commit-check.py` or any do-code-change file (agent-builder's).
- No change to install.sh, `_install_tooling.py` or `--mode status`.
- No new check for repos that set their own `core.hooksPath` (they skip this hook today and still will).

## Decisions

1. **The closing hint after a block** — decided by Mark (2026-11-12): every block is fixed; `--no-verify` only when the machine's owner (Mark, here) has said so. The line becomes "pre-commit: fix the lines above. --no-verify only when the machine's owner has said so." (wording ruled at fix round 1: the shipped hook names no person) Alternative was keeping the old line.
2. **`python` cannot run** — decided by Mark (2026-11-12): fail loud, no special handling. The change request's line is used as given: a missing python makes the shell print its own error and sets status=1, so the commit is blocked. Alternative was a guard with its own BLOCKED line (dropped as unneeded).
