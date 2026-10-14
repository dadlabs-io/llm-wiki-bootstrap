#!/bin/sh
# The private-words check (task #135): every word in private-words.txt (one per line, any case; # comments)
# is looked for in the lines the staged diff ADDS, never in lines already committed. A repo may allow
# some words with a .private-words-allow file at its root (same format). Prints file:line per hit.
here="$(cd "$(dirname "$0")" && pwd)"
words="$here/private-words.txt"
[ -f "$words" ] || exit 0
top="$(git rev-parse --show-toplevel)"
allow="$top/.private-words-allow"
[ -f "$allow" ] || allow=/dev/null
git diff --cached -U0 --no-color --no-ext-diff | awk -v words="$words" -v allow="$allow" '
BEGIN {
    while ((getline a < allow) > 0) { sub(/\r$/, "", a); if (a !~ /^[ \t]*(#|$)/) A[tolower(a)] = 1 }
    while ((getline w < words) > 0) {
        sub(/\r$/, "", w); if (w ~ /^[ \t]*(#|$)/) continue
        if (!(tolower(w) in A)) W[++n] = tolower(w)
    }
}
/^\+\+\+ / { f = substr($0, 7); next }
/^@@/ { split($3, p, ","); ln = substr(p[1], 2) + 0; next }
/^\+/ {
    line = tolower(substr($0, 2))
    for (i = 1; i <= n; i++) if (index(line, W[i])) { printf "%s:%d: private word \"%s\"\n", f, ln, W[i]; hit = 1 }
    ln++; next
}
END {
    if (hit) print "pre-commit: BLOCKED — private words in the lines being added (above). Remove them, or list a word in this repo'"'"'s .private-words-allow if it belongs here." > "/dev/stderr"
    exit hit ? 1 : 0
}'
