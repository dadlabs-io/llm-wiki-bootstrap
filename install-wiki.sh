#!/usr/bin/env bash
# install-wiki.sh — install the LLM-wiki framework, optionally scaffold a project.
#
# Two modes:
#   1. Global install only (no --target-folder):
#      Installs the /new-project skill at ~/.claude/skills/new-project/.
#   2. One-shot install + scaffold (with --target-folder):
#      Global install AS NEEDED, then scaffolds the project at --target-folder.
#
# Usage examples (from this package's root):
#   ./install-wiki.sh                                        # global only
#   ./install-wiki.sh --target-folder ~/proj/dnd-project     # install + scaffold (interactive)
#   ./install-wiki.sh --target-folder ~/proj/dnd-project \
#       --project-type development --project-name dnd-project \
#       --project-description "D&D combat engine" --drive-enabled yes
#
# Flags:
#   --target-folder       Enable scaffold; project root to create/populate
#   --tool                claude-code (default) | cursor
#   --project-type        research | development (asked if missing + --target-folder)
#   --project-name        Project slug (defaults to target leaf name)
#   --project-description One-liner (asked if missing + --target-folder)
#   --drive-enabled       yes | no (default no)
#   --drive-parent-folder Google Drive parent folder name (default "__FOR CLAUDE")
#   --force               Skip already-installed prompt; wipe + reinstall skill
#   --refresh-only        Skip prompt; idempotent refresh

set -euo pipefail

TARGET_FOLDER=""
TOOL="claude-code"
PROJECT_TYPE=""
PROJECT_NAME=""
PROJECT_DESCRIPTION=""
DRIVE_ENABLED="no"
DRIVE_PARENT_FOLDER="__FOR CLAUDE"
FORCE="no"
REFRESH_ONLY="no"

while [[ $# -gt 0 ]]; do
    case "$1" in
        --target-folder) TARGET_FOLDER="$2"; shift 2;;
        --tool) TOOL="$2"; shift 2;;
        --project-type) PROJECT_TYPE="$2"; shift 2;;
        --project-name) PROJECT_NAME="$2"; shift 2;;
        --project-description) PROJECT_DESCRIPTION="$2"; shift 2;;
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

if [[ $EXIT -ne 0 ]]; then
    exit $EXIT
fi

# ---------- Phase B (per-project scaffold) — only if --target-folder provided ----------

if [[ -z "$TARGET_FOLDER" ]]; then
    echo
    echo "Global install complete."
    echo "Next steps:"
    echo "  1. Restart Claude Code"
    echo "  2. cd to any project folder"
    echo "  3. Run /new-project — it asks tool, type, name, Drive prefs and does the rest"
    echo
    echo "Or skip the two-step: re-run with --target-folder <path> to scaffold in one shot."
    exit 0
fi

echo
echo "Scaffolding project at $TARGET_FOLDER..."

# Interactive prompts for anything not provided
if [[ -z "$PROJECT_TYPE" ]]; then
    echo
    echo "What kind of project is this?"
    echo "  1. research     — ingesting external content into a knowledge base"
    echo "  2. development  — building code, capturing design decisions"
    read -p "Pick (1 or 2): " pt
    case "$pt" in
        1|research) PROJECT_TYPE="research" ;;
        2|development) PROJECT_TYPE="development" ;;
        *) echo "ERR: invalid choice" >&2; exit 2 ;;
    esac
fi

if [[ -z "$PROJECT_NAME" ]]; then
    DEFAULT_NAME=$(basename "$TARGET_FOLDER" | tr '[:upper:]' '[:lower:]' | sed 's/[^a-z0-9]\+/-/g' | sed 's/^-\|-$//g')
    read -p "Project name (slug) [default: $DEFAULT_NAME]: " PROJECT_NAME
    PROJECT_NAME="${PROJECT_NAME:-$DEFAULT_NAME}"
fi

if [[ -z "$PROJECT_DESCRIPTION" ]]; then
    read -p "One-line description (optional): " PROJECT_DESCRIPTION
fi

echo
echo "About to scaffold:"
echo "  Tool:           $TOOL"
echo "  Project type:   $PROJECT_TYPE"
echo "  Project name:   $PROJECT_NAME"
echo "  Target folder:  $TARGET_FOLDER"
echo "  Description:    $PROJECT_DESCRIPTION"
echo "  Drive ingest:   $DRIVE_ENABLED"
echo

"$PY" "$SCRIPT" \
    --phase B \
    --tool "$TOOL" \
    --project-name "$PROJECT_NAME" \
    --project-description "$PROJECT_DESCRIPTION" \
    --project-type "$PROJECT_TYPE" \
    --target-folder "$TARGET_FOLDER" \
    --bootstrap-source "$HERE" \
    --drive-enabled "$DRIVE_ENABLED" \
    --drive-parent-folder "$DRIVE_PARENT_FOLDER"

PHASE_B_EXIT=$?

if [[ $PHASE_B_EXIT -eq 0 ]]; then
    echo
    echo "Project scaffolded."
    echo "Next steps:"
    echo "  cd $TARGET_FOLDER"
    if [[ "$TOOL" == "claude-code" ]]; then
        echo "  claude       # start Claude Code in this project"
    else
        echo "  cursor .     # open in Cursor"
    fi
    echo "  Read llm-wiki/README.md for an overview"
elif [[ $PHASE_B_EXIT -eq 2 ]]; then
    echo
    echo "RESTART CLAUDE CODE — agentmemory MCP was wired and needs a reload."
fi

exit $PHASE_B_EXIT
