#!/usr/bin/env bash
# install-wiki.sh — one-time machine install for the LLM-wiki framework.
#
# What this does:
#   1. Installs the /new-project skill globally at ~/.claude/skills/new-project/
#   2. Records this package's path in ~/.claude/wiki-config.json as bootstrap_source
#   3. (Optional) Records a default Drive parent folder for ingest
#
# What this does NOT do:
#   - Scaffold any project. That happens per-project when you run /new-project
#     inside a project folder via Claude Code (or Cursor).
#
# After this script succeeds:
#   1. Restart Claude Code so it picks up the new global skill
#   2. cd to any project folder
#   3. Start Claude Code there
#   4. Run /new-project — it asks tool, type, name, Drive prefs and does the rest
#
# Usage (from this package's root):
#   ./install-wiki.sh                                       # no Drive default
#   ./install-wiki.sh --drive-enabled yes                   # Drive ingest, default folder
#   ./install-wiki.sh --drive-enabled yes --drive-parent-folder "MyDriveFolder"
#
# Re-running the script:
#   By default, if the framework is already installed, you'll see the existing
#   install info and be prompted: Refresh / Skip / Force-reinstall.
#
#   --force          : skip prompt; wipe existing skill + reinstall fresh
#   --refresh-only   : skip prompt; refresh skill from current bootstrap (idempotent)

set -euo pipefail

DRIVE_ENABLED="no"
DRIVE_PARENT_FOLDER="__FOR CLAUDE"
FORCE="no"
REFRESH_ONLY="no"

while [[ $# -gt 0 ]]; do
    case "$1" in
        --drive-enabled) DRIVE_ENABLED="$2"; shift 2;;
        --drive-parent-folder) DRIVE_PARENT_FOLDER="$2"; shift 2;;
        --force) FORCE="yes"; shift;;
        --refresh-only) REFRESH_ONLY="yes"; shift;;
        -h|--help)
            sed -n '2,/^$/p' "$0"
            exit 0;;
        *) echo "Unknown option: $1" >&2; exit 2;;
    esac
done

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SCRIPT="$HERE/bootstrap/workflows/llm-wiki/scripts/new-project.py"

if [[ ! -f "$SCRIPT" ]]; then
    echo "ERR: new-project.py not found at $SCRIPT" >&2
    echo "Is this the correct package root?" >&2
    exit 2
fi

if command -v python3 >/dev/null 2>&1; then
    PY="python3"
elif command -v python >/dev/null 2>&1; then
    PY="python"
else
    echo "ERR: python not found on PATH. Install Python 3.10+ first: https://www.python.org/" >&2
    exit 2
fi

# Idempotent install check
SKILL_PATH="$HOME/.claude/skills/new-project/SKILL.md"
CONFIG_PATH="$HOME/.claude/wiki-config.json"

if [[ -f "$SKILL_PATH" && -f "$CONFIG_PATH" && "$FORCE" != "yes" && "$REFRESH_ONLY" != "yes" ]]; then
    echo "LLM-wiki framework is already installed on this machine."
    # Use python to safely parse the JSON
    "$PY" -c "
import json, pathlib
p = pathlib.Path('$CONFIG_PATH')
try:
    cfg = json.loads(p.read_text(encoding='utf-8'))
    print(f'  bootstrap source: {cfg.get(\"bootstrap_source\", \"(unknown)\")}')
    print(f'  install version:  {cfg.get(\"install_version\", \"(unknown)\")}')
    print(f'  last installed:   {cfg.get(\"last_phase_a\", \"(unknown)\")}')
    if cfg.get('bootstrap_source') and cfg['bootstrap_source'] != '$HERE':
        print(f'  NOTE: previous bootstrap_source differs from current ($HERE)')
except Exception as e:
    print(f'  (config unreadable: {e})')
"
    echo
    echo "Choose:"
    echo "  [R] Refresh — re-copy /new-project skill from current bootstrap source (default)"
    echo "  [S] Skip   — exit without changes"
    echo "  [F] Force  — wipe existing install + reinstall fresh"
    read -p "Choice [R/S/F]: " choice
    case "$choice" in
        [Ss]*)
            echo "Skipping."
            exit 0
            ;;
        [Ff]*)
            echo "Wiping existing /new-project skill..."
            rm -rf "$HOME/.claude/skills/new-project"
            ;;
        *)
            echo "Refreshing existing install."
            ;;
    esac
    echo
fi

echo "Installing LLM-wiki framework (global, one-time)..."
echo "  Bootstrap source: $HERE"
echo "  Drive ingest:     $DRIVE_ENABLED"
if [[ "$DRIVE_ENABLED" == "yes" ]]; then
    echo "  Drive parent:     $DRIVE_PARENT_FOLDER"
fi
echo

"$PY" "$SCRIPT" \
    --phase A \
    --bootstrap-source "$HERE" \
    --drive-enabled "$DRIVE_ENABLED" \
    --drive-parent-folder "$DRIVE_PARENT_FOLDER"

EXIT=$?

if [[ $EXIT -eq 0 ]]; then
    echo
    echo "Install complete."
    echo "Next steps:"
    echo "  1. Restart Claude Code"
    echo "  2. cd to any project folder"
    echo "  3. Start Claude Code there"
    echo "  4. Run /new-project — it asks tool, type, name, Drive prefs and does the rest"
fi

exit $EXIT
