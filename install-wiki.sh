#!/usr/bin/env bash
# install-wiki.sh -- install the LLM-wiki framework.
#
# Interactive flow:
#   Q1: install target?  [1] global tooling (default)  |  [2] a specific project
#   Q2: tool?            [1] claude-code (default)      |  [2] cursor (not yet supported -> exits)
#
# Two modes:
#   1. Global tooling-only (DEFAULT):
#      Installs ALL wiki skills into ~/.claude/skills/ and all wiki scripts into
#      ~/.claude/wiki-scripts/. No project/content scaffold. Idempotent.
#      -> new-wiki.py --mode tooling --tool claude-code
#   2. A specific project (--target-folder, or pick [2]):
#      Records this package as the global bootstrap source (Phase A), then
#      scaffolds the project at --target-folder. The research-vs-development
#      prompt has been removed; the project path uses a merged taxonomy default.
#
# Usage examples (from this package's root):
#   ./install-wiki.sh                                        # global tooling (default)
#   ./install-wiki.sh --mode tooling                         # same, explicit
#   ./install-wiki.sh --target-folder ~/proj/dnd-project     # scaffold a project (interactive)
#   ./install-wiki.sh --target-folder ~/proj/dnd-project \
#       --project-name dnd-project \
#       --project-description "D&D combat engine" --drive-enabled yes
#
# Flags:
#   --mode                tooling (default) | project
#   --target-folder       Project root to create/populate (implies --mode project)
#   --tool                claude-code (default) | cursor (cursor exits 0 -- not yet supported)
#   --project-name        Project slug (defaults to target leaf name)
#   --project-description One-liner (asked if missing, interactive only)
#   --project-type        research | development -- DEPRECATED prompt removed; still
#                         accepted for scripted back-compat. TODO: merged taxonomy.
#   --drive-enabled       yes | no (default no)
#   --drive-parent-folder Google Drive parent folder name (default "__FOR CLAUDE")
#   --force / --refresh-only  retained for back-compat (no longer gate a prompt)

set -euo pipefail

MODE=""
TARGET_FOLDER=""
TOOL="claude-code"
TOOL_SET="no"
PROJECT_TYPE=""
PROJECT_NAME=""
PROJECT_DESCRIPTION=""
DRIVE_ENABLED="no"
DRIVE_PARENT_FOLDER="__FOR CLAUDE"
FORCE="no"
REFRESH_ONLY="no"

while [[ $# -gt 0 ]]; do
    case "$1" in
        --mode) MODE="$2"; shift 2;;
        --target-folder) TARGET_FOLDER="$2"; shift 2;;
        --tool) TOOL="$2"; TOOL_SET="yes"; shift 2;;
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
SCRIPT="$HERE/bootstrap/workflows/llm-wiki/scripts/new-wiki.py"

if [[ ! -f "$SCRIPT" ]]; then
    echo "ERR: new-wiki.py not found at $SCRIPT" >&2
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

# Detect non-interactive mode (no TTY on stdin). When run by an agent / CI /
# piped, read hangs or returns empty, so default every prompt.
if [[ -t 0 ]]; then NONINTERACTIVE="no"; else NONINTERACTIVE="yes"; fi

# ---------- Q1: install target ----------
# Default is global tooling-only. --target-folder implies a project install.
if [[ -z "$MODE" ]]; then
    if [[ -n "$TARGET_FOLDER" ]]; then
        MODE="project"
    elif [[ "$NONINTERACTIVE" == "yes" ]]; then
        MODE="tooling"
        echo "Non-interactive run -- defaulting to global tooling install."
    else
        echo "What do you want to install?"
        echo "  1. global tooling  -- all wiki skills + scripts into ~/.claude/ (default)"
        echo "  2. a specific project -- scaffold an llm-wiki project folder"
        read -p "Pick (1 or 2) [1]: " tchoice
        case "$tchoice" in
            2|project) MODE="project" ;;
            *) MODE="tooling" ;;
        esac
    fi
fi

# ---------- Q2: tool ----------
if [[ "$NONINTERACTIVE" != "yes" && "$TOOL_SET" != "yes" ]]; then
    echo
    echo "Which tool?"
    echo "  1. claude-code (default)"
    echo "  2. cursor"
    read -p "Pick (1 or 2) [1]: " toolchoice
    case "$toolchoice" in
        2|cursor) TOOL="cursor" ;;
        *) TOOL="claude-code" ;;
    esac
fi

if [[ "$TOOL" == "cursor" ]]; then
    echo "Cursor not supported yet -- exiting."
    exit 0
fi

# ---------- Mode: global tooling-only ----------
if [[ "$MODE" == "tooling" ]]; then
    echo
    echo "Installing LLM-wiki global tooling (skills + scripts)..."
    echo "  Bootstrap source: $HERE"
    echo
    "$PY" "$SCRIPT" \
        --mode tooling \
        --tool claude-code \
        --bootstrap-source "$HERE"
    exit $?
fi

# ---------- Mode: project scaffold ----------
if [[ -z "$TARGET_FOLDER" ]]; then
    if [[ "$NONINTERACTIVE" == "yes" ]]; then
        echo "ERR: project install requires --target-folder in non-interactive mode." >&2
        exit 2
    fi
    read -p "Project target folder: " TARGET_FOLDER
    if [[ -z "$TARGET_FOLDER" ]]; then
        echo "ERR: a target folder is required for a project install." >&2
        exit 2
    fi
fi

# Project install still needs the global /new-wiki skill + recorded bootstrap
# source (Phase A) before scaffolding (Phase B).
echo
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

echo
echo "Scaffolding project at $TARGET_FOLDER..."

# Research-vs-development is no longer prompted. Default to a single merged
# taxonomy. new-wiki.py Phase B still hard-requires a type, so we pass
# "development" (the superset code+research taxonomy) as the merged default
# unless --project-type was explicitly supplied for a scripted run.
# TODO: merged taxonomy -- swap this default for a real combined taxonomy +
# template once they exist; remove the research/development split entirely.
if [[ -z "$PROJECT_TYPE" ]]; then
    PROJECT_TYPE="development"
fi

if [[ -z "$PROJECT_NAME" ]]; then
    DEFAULT_NAME=$(basename "$TARGET_FOLDER" | tr '[:upper:]' '[:lower:]' | sed 's/[^a-z0-9]\+/-/g' | sed 's/^-\|-$//g')
    if [[ "$NONINTERACTIVE" == "yes" ]]; then
        PROJECT_NAME="$DEFAULT_NAME"
    else
        read -p "Project name (slug) [default: $DEFAULT_NAME]: " PROJECT_NAME
        PROJECT_NAME="${PROJECT_NAME:-$DEFAULT_NAME}"
    fi
fi

if [[ -z "$PROJECT_DESCRIPTION" && "$NONINTERACTIVE" != "yes" ]]; then
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
    echo "  claude       # start Claude Code in this project"
    echo "  Read llm-wiki/README.md for an overview"
fi

exit $PHASE_B_EXIT
