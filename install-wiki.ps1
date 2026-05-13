<#
install-wiki.ps1 — one-time machine install for the LLM-wiki framework.

What this does:
  1. Installs the /new-project skill globally at ~/.claude/skills/new-project/
  2. Records this package's path in ~/.claude/wiki-config.json as bootstrap_source
  3. (Optional) Records a default Drive parent folder for ingest

What this does NOT do:
  - Scaffold any project. That happens per-project when you run /new-project
    inside a project folder via Claude Code (or Cursor).

After this script succeeds:
  1. Restart Claude Code so it picks up the new global skill
  2. cd to any project folder
  3. Start Claude Code there
  4. Run /new-project — it asks tool, type, name, Drive prefs and does the rest

Usage (from this package's root):
  .\install-wiki.ps1                                     # no Drive default
  .\install-wiki.ps1 -DriveEnabled yes                   # Drive ingest, default folder
  .\install-wiki.ps1 -DriveEnabled yes -DriveParentFolder "MyDriveFolder"

Re-running the script:
  By default, if the framework is already installed, you'll see the existing
  install info and be prompted: Refresh / Skip / Force-reinstall.

  -Force          : skip prompt; wipe existing skill + reinstall fresh
  -RefreshOnly    : skip prompt; refresh skill from current bootstrap (idempotent)
#>

param(
    [ValidateSet("yes", "no")]
    [string]$DriveEnabled = "no",

    [string]$DriveParentFolder = "__FOR CLAUDE",

    # Bypass the already-installed prompt — always refresh from current
    # bootstrap source without asking. Useful for scripted / unattended runs.
    [switch]$Force,

    # Refresh the skill files but don't change Drive config or other settings.
    # If passed with -Force, prompt is skipped AND no drive args are written.
    [switch]$RefreshOnly
)

$ErrorActionPreference = "Stop"
$Bootstrap = $PSScriptRoot
$Script = Join-Path $Bootstrap "bootstrap\workflows\llm-wiki\scripts\new-project.py"

if (-not (Test-Path $Script)) {
    Write-Host "ERR: new-project.py not found at $Script" -ForegroundColor Red
    Write-Host "Is this the correct package root?" -ForegroundColor Red
    exit 2
}

$py = Get-Command python -ErrorAction SilentlyContinue
if (-not $py) { $py = Get-Command python3 -ErrorAction SilentlyContinue }
if (-not $py) {
    Write-Host "ERR: python not found on PATH. Install Python 3.10+ first: https://www.python.org/" -ForegroundColor Red
    exit 2
}

# Idempotent install check — detect existing install and prompt if found
$SkillPath = Join-Path $env:USERPROFILE ".claude\skills\new-project\SKILL.md"
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
    Write-Host "Choose:"
    Write-Host "  [R] Refresh — re-copy /new-project skill from current bootstrap source (default)"
    Write-Host "  [S] Skip   — exit without changes"
    Write-Host "  [F] Force  — wipe existing install + reinstall fresh"
    $choice = Read-Host "Choice [R/S/F]"
    switch -Regex ($choice) {
        '^[Ss]' {
            Write-Host "Skipping." -ForegroundColor Cyan
            exit 0
        }
        '^[Ff]' {
            Write-Host "Wiping existing /new-project skill..." -ForegroundColor Yellow
            $skillDir = Join-Path $env:USERPROFILE ".claude\skills\new-project"
            Remove-Item -Recurse -Force $skillDir -ErrorAction SilentlyContinue
            # Keep wiki-config.json — it will be updated, not wiped (user settings live there)
        }
        default {
            Write-Host "Refreshing existing install." -ForegroundColor Cyan
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

if ($exit -eq 0) {
    Write-Host ""
    Write-Host "Install complete." -ForegroundColor Green
    Write-Host "Next steps:" -ForegroundColor Green
    Write-Host "  1. Restart Claude Code" -ForegroundColor Green
    Write-Host "  2. cd to any project folder" -ForegroundColor Green
    Write-Host "  3. Start Claude Code there" -ForegroundColor Green
    Write-Host "  4. Run /new-project — it asks tool, type, name, Drive prefs and does the rest" -ForegroundColor Green
}

exit $exit
