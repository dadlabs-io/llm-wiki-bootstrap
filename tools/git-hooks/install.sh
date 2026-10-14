#!/bin/sh
# Installs the machine-wide git hooks (task #135): copies this folder's hooks to ~/.git-hooks, records where
# gitleaks is, writes a hand-over hook for every other hook name (so each repo's own .git/hooks still runs),
# and sets git config --global core.hooksPath. Re-run after changing anything here. private-words.txt is
# copied only the first time: after that it is Mark's list, edited in ~/.git-hooks.
#   sh tools/git-hooks/install.sh            # install or refresh
#   sh tools/git-hooks/install.sh --remove   # unset core.hooksPath (the folder is left)
set -e
src="$(cd "$(dirname "$0")" && pwd)"
dest="$HOME/.git-hooks"
if [ "$1" = "--remove" ]; then
    git config --global --unset core.hooksPath || true
    echo "core.hooksPath unset; each repo's own .git/hooks runs again. $dest left in place."
    exit 0
fi
gl="$(command -v gitleaks 2>/dev/null || true)"
if [ -z "$gl" ]; then
    for c in "$LOCALAPPDATA/Microsoft/WinGet/Packages/Gitleaks.Gitleaks_Microsoft.Winget.Source_8wekyb3d8bbwe/gitleaks.exe" \
             /opt/homebrew/bin/gitleaks /usr/local/bin/gitleaks; do
        [ -f "$c" ] && gl="$c" && break
    done
fi
[ -n "$gl" ] || { echo "gitleaks not found: install it (winget install Gitleaks.Gitleaks / brew install gitleaks)" >&2; exit 1; }
mkdir -p "$dest"
cp "$src/pre-commit" "$src/private-words.sh" "$src/_local" "$src/gitleaks.toml" "$dest/"
[ -f "$dest/private-words.txt" ] || cp "$src/private-words.txt" "$dest/"
printf 'GITLEAKS="%s"\n' "$gl" > "$dest/hooks.conf"
for name in applypatch-msg pre-applypatch post-applypatch pre-merge-commit prepare-commit-msg commit-msg \
            post-commit pre-rebase post-checkout post-merge pre-push post-rewrite push-to-checkout pre-auto-gc \
            sendemail-validate; do
    printf '#!/bin/sh\n# hands over to the repo'"'"'s own %s hook (tools/git-hooks/install.sh)\nexec sh "$(dirname "$0")/_local" %s "$@"\n' \
        "$name" "$name" > "$dest/$name"
done
chmod +x "$dest"/* 2>/dev/null || true
git config --global core.hooksPath "$dest"
echo "installed: $dest (gitleaks: $gl); git config --global core.hooksPath = $(git config --global core.hooksPath)"
