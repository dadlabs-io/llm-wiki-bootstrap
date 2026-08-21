<#
install-wiki.ps1 -- install the LLM-wiki framework.

Interactive flow:
  Q1: install target?  [1] global tooling (default)  |  [2] a specific project
  Q2: tool?            [1] claude-code (default)      |  [2] cursor

Two modes:
  1. Global tooling-only (DEFAULT):
     Installs ALL wiki skills into ~/.claude/skills/ and all wiki scripts into
     ~/.claude/wiki-scripts/. No project/content scaffold. Idempotent.
     -> new-wiki.py --mode tooling --tool <claude-code|cursor>
  2. A specific project (-TargetFolder, or pick [2]):
     Records this package as the global bootstrap source (Phase A), then
     scaffolds the project at -TargetFolder (skills + scripts + llm-wiki/ +
     CLAUDE.md + Drive OAuth if enabled). The research-vs-development prompt
     has been removed; the project path uses a single merged taxonomy default.

Usage examples (from this package's root):
  # Global tooling-only install (default -- just run it):
  .\install-wiki.ps1
  .\install-wiki.ps1 -Mode tooling

  # Scaffold a project (interactive prompts for anything not passed):
  .\install-wiki.ps1 -Mode project -TargetFolder C:\github.com\dnd-project
  .\install-wiki.ps1 -TargetFolder C:\github.com\dnd-project   # -TargetFolder implies project

  # Fully scripted project scaffold (no prompts):
  .\install-wiki.ps1 -TargetFolder C:\github.com\dnd-project `
      -ProjectName dnd-project -ProjectDescription "D&D combat engine" -DriveEnabled yes

After install:
  - Restart Claude Code so it picks up new skills/scripts
  - (project mode) cd to the project folder and start working

Flags:
  -Mode              : tooling (default) | project
  -TargetFolder      : project root to create/populate (implies -Mode project)
  -Tool              : claude-code (default) | cursor
  -ProjectName       : project slug (defaults to target-folder leaf name)
  -ProjectDescription: one-liner (asked if not set, interactive only)
  -ProjectType       : research | development -- DEPRECATED prompt removed; still
                       accepted for scripted back-compat. TODO: merged taxonomy.
  -DriveEnabled      : yes | no (default no)
  -DriveParentFolder : Google Drive parent folder name (default "__FOR CLAUDE")
  -Force / -RefreshOnly : retained for back-compat (no longer gate a prompt)
#>

param(
    # Install target. "tooling" = global tooling-only install (default).
    # "project" = scaffold a specific project (requires -TargetFolder).
    [ValidateSet("tooling", "project")]
    [string]$Mode = "",

    # Phase B (per-project scaffold) -- set this to trigger the project path.
    # If passed, implies -Mode project.
    [string]$TargetFolder = "",

    [ValidateSet("claude-code", "cursor")]
    [string]$Tool = "claude-code",

    # Project taxonomy type. Research-vs-development is no longer prompted; the
    # project path defaults to a single merged default. Still accepted for
    # scripted runs that want the old per-type behaviour.
    # TODO: merged taxonomy -- replace research/development split with one
    # combined taxonomy + template once the merged template lands.
    [ValidateSet("research", "development")]
    [string]$ProjectType = "",

    [string]$ProjectName = "",

    [string]$ProjectDescription = "",

    # Skills install: global (shared ~/.claude, default) | bundled (per-project copy).
    [ValidateSet("global", "bundled")]
    [string]$SkillsInstall = "global",

    # If set, wiki content lives at <VaultRoot>/<name>/ instead of <target>/llm-wiki/.
    [string]$VaultRoot = "",

    [ValidateSet("yes", "no")]
    [string]$DriveEnabled = "no",

    [string]$DriveParentFolder = "__FOR CLAUDE",

    # Bypass the already-installed prompt -- always refresh from current
    # bootstrap source without asking. Useful for scripted / unattended runs.
    [switch]$Force,

    # Deprecated as of 2026-05-14 -- agentmemory integration removed. Kept
    # for backward-compat with old scripted invocations; no-op.
    [switch]$NoAgentmemory,

    # Refresh the skill files but don't change Drive config or other settings.
    # If passed with -Force, prompt is skipped AND no drive args are written.
    [switch]$RefreshOnly
)

$ErrorActionPreference = "Stop"
$Bootstrap = $PSScriptRoot
$Script = Join-Path $Bootstrap "bootstrap\scripts\new-wiki.py"

if (-not (Test-Path $Script)) {
    Write-Host "ERR: new-wiki.py not found at $Script" -ForegroundColor Red
    Write-Host "Is this the correct package root?" -ForegroundColor Red
    exit 2
}

$py = Get-Command python -ErrorAction SilentlyContinue
if (-not $py) { $py = Get-Command python3 -ErrorAction SilentlyContinue }
if (-not $py) {
    Write-Host "ERR: python not found on PATH. Install Python 3.10+ first: https://www.python.org/" -ForegroundColor Red
    exit 2
}

# Detect non-interactive mode (stdin redirected / no console UI). When run by
# an agent / CI / piped, Read-Host hangs forever, so we default every prompt.
$nonInteractive = [Console]::IsInputRedirected -or -not [Environment]::UserInteractive

# ---------- Q1: install target ----------
# Default is global tooling-only. -TargetFolder implies a project install.
if (-not $Mode) {
    if ($TargetFolder) {
        $Mode = "project"
    } elseif ($nonInteractive) {
        $Mode = "tooling"
        Write-Host "Non-interactive run -- defaulting to global tooling install." -ForegroundColor Cyan
    } else {
        Write-Host "What do you want to install?"
        Write-Host "  1. global tooling  -- all wiki skills + scripts into ~/.claude/ (default)"
        Write-Host "  2. a specific project -- scaffold an llm-wiki project folder"
        $tChoice = Read-Host "Pick (1 or 2) [1]"
        if ($tChoice -eq "2" -or $tChoice -eq "project") { $Mode = "project" }
        else { $Mode = "tooling" }
    }
}

# ---------- Q2: tool ----------
if (-not $nonInteractive -and -not $PSBoundParameters.ContainsKey("Tool")) {
    Write-Host ""
    Write-Host "Which tool?"
    Write-Host "  1. claude-code (default)"
    Write-Host "  2. cursor"
    $toolChoice = Read-Host "Pick (1 or 2) [1]"
    if ($toolChoice -eq "2" -or $toolChoice -eq "cursor") { $Tool = "cursor" }
    else { $Tool = "claude-code" }
}

# ---------- Mode: global tooling-only ----------
if ($Mode -eq "tooling") {
    Write-Host ""
    if ($Tool -eq "cursor") {
        Write-Host "Installing LLM-wiki global Cursor tooling (rules + scripts)..." -ForegroundColor Cyan
    } else {
        Write-Host "Installing LLM-wiki global tooling (skills + scripts)..." -ForegroundColor Cyan
    }
    Write-Host "  Bootstrap source: $Bootstrap"
    Write-Host "  Tool:             $Tool"
    Write-Host ""

    & $py.Source $Script `
        --mode tooling `
        --tool $Tool `
        --bootstrap-source $Bootstrap
    exit $LASTEXITCODE
}

# ---------- Mode: project scaffold ----------
if (-not $TargetFolder) {
    if ($nonInteractive) {
        Write-Host "ERR: project install requires -TargetFolder in non-interactive mode." -ForegroundColor Red
        exit 2
    }
    $TargetFolder = Read-Host "Project target folder"
    if (-not $TargetFolder) {
        Write-Host "ERR: a target folder is required for a project install." -ForegroundColor Red
        exit 2
    }
}

# Project install still needs the global /new-wiki skill + recorded bootstrap
# source (Phase A) before scaffolding (Phase B).
Write-Host ""
Write-Host "Installing LLM-wiki framework (global, one-time)..." -ForegroundColor Cyan
Write-Host "  Bootstrap source: $Bootstrap"
Write-Host "  Drive ingest:     $DriveEnabled"
if ($DriveEnabled -eq "yes") {
    Write-Host "  Drive parent:     $DriveParentFolder"
}
Write-Host ""

& $py.Source $Script `
    --phase A `
    --tool $Tool `
    --bootstrap-source $Bootstrap `
    --drive-enabled $DriveEnabled `
    --drive-parent-folder $DriveParentFolder

$exit = $LASTEXITCODE
if ($exit -ne 0) {
    exit $exit
}

Write-Host ""
Write-Host "Scaffolding project at $TargetFolder..." -ForegroundColor Cyan

# Research-vs-development split removed 2026-06-15. new-wiki.py Phase B now applies
# a single merged taxonomy (research/* + project/* + sessions/) and ignores
# --project-type entirely, so the wrapper no longer prompts, prints, or passes it.

if (-not $ProjectName) {
    $defaultName = (Split-Path $TargetFolder -Leaf).ToLower() -replace "[^a-z0-9]+", "-"
    $defaultName = $defaultName.Trim("-")
    if ($nonInteractive) {
        $ProjectName = $defaultName
    } else {
        $ProjectName = Read-Host "Project name (slug) [default: $defaultName]"
        if (-not $ProjectName) { $ProjectName = $defaultName }
    }
}

if (-not $ProjectDescription -and -not $nonInteractive) {
    $ProjectDescription = Read-Host "One-line description (optional)"
}

Write-Host ""
Write-Host "About to scaffold:" -ForegroundColor Cyan
Write-Host "  Tool:           $Tool"
Write-Host "  Project name:   $ProjectName"
Write-Host "  Target folder:  $TargetFolder"
Write-Host "  Description:    $ProjectDescription"
Write-Host "  Drive ingest:   $DriveEnabled"
Write-Host ""

$phaseBArgs = @(
    $Script,
    "--phase", "B",
    "--tool", $Tool,
    "--project-name", $ProjectName,
    "--project-description", $ProjectDescription,
    "--target-folder", $TargetFolder,
    "--skills-install", $SkillsInstall,
    "--bootstrap-source", $Bootstrap,
    "--drive-enabled", $DriveEnabled,
    "--drive-parent-folder", $DriveParentFolder
)
if ($VaultRoot) { $phaseBArgs += @("--vault-root", $VaultRoot) }
# -NoAgentmemory is a deprecated no-op as of 2026-05-14, kept for back-compat.

& $py.Source @phaseBArgs
$phaseBExit = $LASTEXITCODE

if ($phaseBExit -eq 0) {
    Write-Host ""
    Write-Host "Project scaffolded." -ForegroundColor Green
    Write-Host "Next steps:" -ForegroundColor Green
    Write-Host "  cd $TargetFolder" -ForegroundColor Green
    if ($Tool -eq "claude-code") {
        Write-Host "  claude       # start Claude Code in this project" -ForegroundColor Green
    } else {
        Write-Host "  cursor .     # open in Cursor" -ForegroundColor Green
    }
    Write-Host "  Read llm-wiki/README.md for an overview" -ForegroundColor Green

    # agentmemory integration removed 2026-05-14 -- the proactive-listener
    # pattern (agent files durable items to _inbox/proposed/ inline) replaces
    # the auto-capture-via-hooks pipeline. No Docker, no iii-engine, no
    # scheduled task, no API-key burn.
    #
    # Existing AgentMemoryEngine scheduled task on this machine from a prior
    # install is left ALONE -- the user can keep it or remove it via:
    #   Unregister-ScheduledTask -TaskName AgentMemoryEngine -Confirm:$false
}

exit $phaseBExit
