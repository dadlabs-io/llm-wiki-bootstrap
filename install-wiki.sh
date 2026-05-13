#!/usr/bin/env bash
# install-wiki.sh — install the LLM-wiki framework on this machine.
#
# Runs new-project.py --phase A using this package as the bootstrap source.
# After it completes, /new-project is available in Claude Code and you can
# run it to scaffold any new project (research or development).
#
# Usage (from the package root):
#   ./install-wiki.sh                                       # claude-code, research, no Drive
#   ./install-wiki.sh --tool cursor --target-folder ~/proj
#   ./install-wiki.sh --project-type development --drive-enabled yes
#
# After install:
#   1. Restart Claude Code (or Cursor)
#   2. Run /new-project in a session to scaffold per-project structure

set -euo pipefail

TOOL="claude-code"
PROJECT_TYPE="research"
TARGET_FOLDER=""
DRIVE_ENABLED="no"
DRIVE_PARENT_FOLDER="__FOR CLAUDE"

while [[ $# -gt 0 ]]; do
    case "$1" in
        --tool) TOOL="$2"; shift 2;;
        --project-type) PROJECT_TYPE="$2"; shift 2;;
        --target-folder) TARGET_FOLDER="$2"; shift 2;;
        --drive-enabled) DRIVE_ENABLED="$2"; shift 2;;
        --drive-parent-folder) DRIVE_PARENT_FOLDER="$2"; shift 2;;
        -h|--help)
            sed -n '1,/^$/p' "$0"
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

# Locate python
if command -v python3 >/dev/null 2>&1; then
    PY="python3"
elif command -v python >/dev/null 2>&1; then
    PY="python"
else
    echo "ERR: python not found on PATH. Install Python 3.10+ first: https://www.python.org/" >&2
    exit 2
fi

echo "Installing LLM-wiki framework..."
echo "  Tool:         $TOOL"
echo "  Project type: $PROJECT_TYPE"
echo "  Drive ingest: $DRIVE_ENABLED"
echo

ARGS=(
    "$SCRIPT"
    --phase A
    --tool "$TOOL"
    --project-type "$PROJECT_TYPE"
    --bootstrap-source "$HERE"
    --drive-enabled "$DRIVE_ENABLED"
    --drive-parent-folder "$DRIVE_PARENT_FOLDER"
)

if [[ "$TOOL" == "cursor" ]]; then
    if [[ -z "$TARGET_FOLDER" ]]; then
        echo "ERR: --target-folder is required for Cursor installs (no global skills dir)" >&2
        exit 2
    fi
    ARGS+=(--target-folder "$TARGET_FOLDER")
fi

"$PY" "${ARGS[@]}"
EXIT=$?

if [[ $EXIT -eq 0 ]]; then
    echo
    echo "Install complete."
    echo "Next steps:"
    echo "  1. Restart Claude Code (or Cursor)"
    echo "  2. In any new project folder, run /new-project to scaffold it"
elif [[ $EXIT -eq 2 ]]; then
    echo
    echo "Restart Claude Code, then re-run install-wiki.sh to finish setup."
fi

exit $EXIT
