# Machine-wide git pre-commit hook

One hook for every repository on the machine, every bot and Mark (task #135, from the Ruflo deep dive: their
public repo carried an unrelated client's cloud ids and an OAuth client id). It runs at commit, the moment
something enters history.

- **gitleaks** (`gitleaks git --pre-commit --staged`, with `gitleaks.toml`): API keys, tokens, private keys in
  the staged changes.
- **Private words** (`private-words.txt`, one word or phrase per line, any case): looked for in the lines a
  commit adds, never in lines already committed. Mark fills the list in `~/.git-hooks/private-words.txt`; a repo
  where a word belongs lists it in `.private-words-allow` at its root.
- **The repo's own hooks still run**: a global `core.hooksPath` replaces `.git/hooks`, so every hook name here
  hands over to the repo's own hook of that name (`_local`). A repo that sets its own `core.hooksPath` (one does:
  sudoku-app) keeps its own hooks and skips this one.

A blocked commit names the file and line. To commit anyway, on purpose: `git commit --no-verify`.
If gitleaks cannot be found, the commit is blocked as NOT checked, never let through silently.

## Install, refresh, remove

The framework offers it: `/new-wiki` asks "Block secrets in commits?" when it is not on (default no), and the
installer takes `-GitHooks yes` / `--git-hooks yes` with a project; both install gitleaks first when missing
(winget or brew) and turn nothing on when they cannot. `new-wiki.py --mode status` reports `git_hooks` (`on`,
`off`, `on-no-gitleaks`), and `--mode uninstall` turns it off (task #141). By hand:

```bash
sh tools/git-hooks/install.sh            # copy to ~/.git-hooks, record gitleaks, set the global core.hooksPath
sh tools/git-hooks/install.sh --remove   # unset core.hooksPath (each repo's .git/hooks runs again)
```

Re-run the install after changing anything here; it never overwrites `~/.git-hooks/private-words.txt`.
gitleaks: `winget install --id Gitleaks.Gitleaks` (8.30.1 on 2026-10-14) or `brew install gitleaks`.

## What gitleaks.toml allows, and why

Measured 2026-10-14 on the last 300 commits of llm-wiki-bootstrap, project-notebooks, agent-builder-bootstrap
and investment-agent: 45 findings, none a secret of ours. Content and commit hashes (pure hex of 40 or 64
characters) are let through for the two rules that read them as keys; a notebook's `raw/` folder is not scanned,
since a raw is a source's own words (one security paper quoted example keys). After the allowances: 0 findings.

## Tests

`tests/scripts/test_git_hooks.py` (run under a temporary HOME, so the real machine is never touched): a clean
commit, a planted token, a private word with its file and line, the allow file, `--no-verify`, the repo's own
pre-commit and commit-msg hooks, a missing gitleaks, and the remove.
