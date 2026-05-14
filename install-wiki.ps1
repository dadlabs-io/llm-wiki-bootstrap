<#
install-wiki.ps1 -- install the LLM-wiki framework, optionally scaffold a project.

Two modes:
  1. Global install only (no -TargetFolder):
     Installs the /new-wiki skill at ~/.claude/skills/new-wiki/ and
     records this package's path so /new-wiki can find it later.
  2. One-shot install + scaffold (with -TargetFolder):
     Does the global install AS NEEDED, then scaffolds the project at
     -TargetFolder (skills + scripts + llm-wiki/ + CLAUDE.md + agentmemory
     for dev projects + Drive OAuth if enabled).

Usage examples (from this package's root):
  # Global install only
  .\install-wiki.ps1

  # Install + scaffold a new project in one command (interactive prompts for
  # anything not passed):
  .\install-wiki.ps1 -TargetFolder C:\github.com\dnd-project

  # Fully scripted (no prompts):
  .\install-wiki.ps1 -TargetFolder C:\github.com\dnd-project `
      -ProjectType development -ProjectName dnd-project `
      -ProjectDescription "D&D combat engine" -DriveEnabled yes

  # Re-run / refresh global skill from current bootstrap source:
  .\install-wiki.ps1 -RefreshOnly

After install (whether one-shot or two-step):
  - Restart Claude Code so it picks up new skills
  - cd to the project folder
  - Start coding -- /wrap-up at session end, /wiki-search to look things up

Flags:
  -TargetFolder      : enable scaffold; project root to create/populate
  -Tool              : claude-code (default) | cursor
  -ProjectType       : research | development (asked if not set + -TargetFolder)
  -ProjectName       : project slug (defaults to target-folder leaf name)
  -ProjectDescription: one-liner (asked if not set + -TargetFolder)
  -DriveEnabled      : yes | no (default no)
  -DriveParentFolder : Google Drive parent folder name (default "__FOR CLAUDE")
  -Force             : skip already-installed prompt; wipe + reinstall skill
  -RefreshOnly       : skip prompt; idempotent refresh
#>

param(
    # Phase B (per-project scaffold) -- set this to trigger the one-shot path
    [string]$TargetFolder = "",

    [ValidateSet("claude-code", "cursor")]
    [string]$Tool = "claude-code",

    [ValidateSet("research", "development")]
    [string]$ProjectType = "",

    [string]$ProjectName = "",

    [string]$ProjectDescription = "",

    [ValidateSet("yes", "no")]
    [string]$DriveEnabled = "no",

    [string]$DriveParentFolder = "__FOR CLAUDE",

    # Bypass the already-installed prompt -- always refresh from current
    # bootstrap source without asking. Useful for scripted / unattended runs.
    [switch]$Force,

    # Skip the agentmemory MCP install (dev projects only). User can wire it
    # later by hand. See https://github.com/rohitg00/agentmemory.
    [switch]$NoAgentmemory,

    # Refresh the skill files but don't change Drive config or other settings.
    # If passed with -Force, prompt is skipped AND no drive args are written.
    [switch]$RefreshOnly
)

$ErrorActionPreference = "Stop"
$Bootstrap = $PSScriptRoot
$Script = Join-Path $Bootstrap "bootstrap\workflows\llm-wiki\scripts\new-wiki.py"

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

# Idempotent install check -- detect existing install and prompt if found
$SkillPath = Join-Path $env:USERPROFILE ".claude\skills\new-wiki\SKILL.md"
$ConfigPath = Join-Path $env:USERPROFILE ".claude\wiki-config.json"
$AlreadyInstalled = (Test-Path $SkillPath) -and (Test-Path $ConfigPath)

if ($AlreadyInstalled -and -not $Force -and -not $RefreshOnly) {
    try { $cfg = Get-Content $ConfigPath -Raw | ConvertFrom-Json } catch { $cfg = $null }
    Write-Host "LLM-wiki framework is already installed on this machine." -ForegroundColor Yellow
    if ($cfg) {
        Write-Host "  bootstrap source: $($cfg.bootstrap_source)"
        Write-Host "  install version:  $($cfg.install_version)"
        Write-Host "  last installed:   $($cfg.last_phase_a)"
        if ($cfg.bootstrap_source -ne $Bootstrap) {
            Write-Host "  NOTE: previous bootstrap_source differs from current ($Bootstrap)" -ForegroundColor Cyan
        }
    }
    Write-Host ""

    # Detect non-interactive mode (stdin redirected, no console UI). When the
    # script is run by an agent / CI / piped, Read-Host hangs forever. Default
    # to Refresh in that case -- it's the safe idempotent path.
    $nonInteractive = [Console]::IsInputRedirected -or -not [Environment]::UserInteractive
    if ($nonInteractive) {
        Write-Host "Non-interactive run detected -- defaulting to Refresh (pass -Force to wipe instead)." -ForegroundColor Cyan
    } else {
        Write-Host "Choose:"
        Write-Host "  [R] Refresh -- re-copy /new-wiki skill from current bootstrap source (default)"
        Write-Host "  [S] Skip   -- exit without changes"
        Write-Host "  [F] Force  -- wipe existing install + reinstall fresh"
        $choice = Read-Host "Choice [R/S/F]"
        switch -Regex ($choice) {
            '^[Ss]' {
                Write-Host "Skipping." -ForegroundColor Cyan
                exit 0
            }
            '^[Ff]' {
                Write-Host "Wiping existing /new-wiki skill..." -ForegroundColor Yellow
                $skillDir = Join-Path $env:USERPROFILE ".claude\skills\new-wiki"
                Remove-Item -Recurse -Force $skillDir -ErrorAction SilentlyContinue
                # Keep wiki-config.json -- it will be updated, not wiped (user settings live there)
            }
            default {
                Write-Host "Refreshing existing install." -ForegroundColor Cyan
            }
        }
    }
    Write-Host ""
}

Write-Host "Installing LLM-wiki framework (global, one-time)..." -ForegroundColor Cyan
Write-Host "  Bootstrap source: $Bootstrap"
Write-Host "  Drive ingest:     $DriveEnabled"
if ($DriveEnabled -eq "yes") {
    Write-Host "  Drive parent:     $DriveParentFolder"
}
Write-Host ""

& $py.Source $Script `
    --phase A `
    --bootstrap-source $Bootstrap `
    --drive-enabled $DriveEnabled `
    --drive-parent-folder $DriveParentFolder

$exit = $LASTEXITCODE

if ($exit -ne 0) {
    exit $exit
}

# ---------- Phase B (per-project scaffold) -- only if -TargetFolder provided ----------

if (-not $TargetFolder) {
    Write-Host ""
    Write-Host "Global install complete." -ForegroundColor Green
    Write-Host "Next steps:" -ForegroundColor Green
    Write-Host "  1. Restart Claude Code" -ForegroundColor Green
    Write-Host "  2. cd to any project folder" -ForegroundColor Green
    Write-Host "  3. Run /new-wiki -- it asks tool, type, name, Drive prefs and does the rest" -ForegroundColor Green
    Write-Host ""
    Write-Host "Or skip the two-step: re-run install-wiki.ps1 with -TargetFolder <path> to scaffold a project in one shot." -ForegroundColor DarkGray
    exit 0
}

Write-Host ""
Write-Host "Scaffolding project at $TargetFolder..." -ForegroundColor Cyan

# Interactive prompts for anything not provided
if (-not $ProjectType) {
    Write-Host ""
    Write-Host "What kind of project is this?"
    Write-Host "  1. research     -- ingesting external content into a knowledge base"
    Write-Host "  2. development  -- building code, capturing design decisions"
    $ptChoice = Read-Host "Pick (1 or 2)"
    if ($ptChoice -eq "1" -or $ptChoice -eq "research") { $ProjectType = "research" }
    elseif ($ptChoice -eq "2" -or $ptChoice -eq "development") { $ProjectType = "development" }
    else { Write-Host "ERR: invalid choice" -ForegroundColor Red; exit 2 }
}

if (-not $ProjectName) {
    $defaultName = (Split-Path $TargetFolder -Leaf).ToLower() -replace "[^a-z0-9]+", "-"
    $defaultName = $defaultName.Trim("-")
    $ProjectName = Read-Host "Project name (slug) [default: $defaultName]"
    if (-not $ProjectName) { $ProjectName = $defaultName }
}

if (-not $ProjectDescription) {
    $ProjectDescription = Read-Host "One-line description (optional)"
}

Write-Host ""
Write-Host "About to scaffold:" -ForegroundColor Cyan
Write-Host "  Tool:           $Tool"
Write-Host "  Project type:   $ProjectType"
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
    "--project-type", $ProjectType,
    "--target-folder", $TargetFolder,
    "--bootstrap-source", $Bootstrap,
    "--drive-enabled", $DriveEnabled,
    "--drive-parent-folder", $DriveParentFolder
)
if ($NoAgentmemory) { $phaseBArgs += "--no-agentmemory" }

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

    # Register a Scheduled Task that auto-starts the agentmemory iii-engine
    # at every Windows login. Machine-global, idempotent (skip if already
    # registered). Only for development projects; only if -NoAgentmemory
    # was not passed. Requires Docker Desktop OR native iii.exe to be
    # available at run time -- we don't enforce that here, just register.
    if (-not $NoAgentmemory -and $ProjectType -eq "development") {
        $taskName = "AgentMemoryEngine"
        $existing = Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue
        if ($existing) {
            Write-Host ""
            Write-Host "agentmemory auto-start: task '$taskName' already registered (skipping)." -ForegroundColor Cyan
        } else {
            Write-Host ""
            Write-Host "Registering Scheduled Task '$taskName' to auto-start agentmemory at login..." -ForegroundColor Cyan
            try {
                $action = New-ScheduledTaskAction -Execute "npx" -Argument "@agentmemory/agentmemory"
                $trigger = New-ScheduledTaskTrigger -AtLogon -User $env:USERNAME
                $taskSettings = New-ScheduledTaskSettingsSet -StartWhenAvailable -DontStopOnIdleEnd -ExecutionTimeLimit ([TimeSpan]::Zero)
                $principal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType Interactive
                Register-ScheduledTask -TaskName $taskName -Action $action -Trigger $trigger -Settings $taskSettings -Principal $principal -Description "agentmemory iii-engine REST server (auto-start at login)" | Out-Null
                Start-ScheduledTask -TaskName $taskName
                Write-Host "  Task registered + started. Engine will boot on every login from now on." -ForegroundColor Green
                Write-Host "  To disable later: Unregister-ScheduledTask -TaskName '$taskName' -Confirm:`$false" -ForegroundColor Gray
                Write-Host "  PREREQ: Docker Desktop running OR native iii.exe v0.11.2 on PATH" -ForegroundColor Gray
            } catch {
                Write-Host "  WARN: could not register Scheduled Task (need admin?). You can run agentmemory manually." -ForegroundColor Yellow
                Write-Host "  Error: $_" -ForegroundColor Yellow
            }
        }
    }
    # Note: if agentmemory was wired, the Python script already printed the
    # RESTART banner. We exit 0 either way so tool wrappers don't read it as
    # a failure.
}

exit $phaseBExit
