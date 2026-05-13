<#
install-wiki.ps1 — install the LLM-wiki framework on this machine.

Runs new-project.py --phase A using this package as the bootstrap source.
After it completes, /new-project is available in Claude Code and you can
run it to scaffold any new project (research or development).

Usage (from the package root):
  .\install-wiki.ps1                                # claude-code, research, no Drive
  .\install-wiki.ps1 -Tool cursor -TargetFolder C:\proj
  .\install-wiki.ps1 -ProjectType development -DriveEnabled yes

After install:
  1. Restart Claude Code (or Cursor)
  2. Run /new-project in a session to scaffold per-project structure
#>

param(
    [ValidateSet("claude-code", "cursor")]
    [string]$Tool = "claude-code",

    [ValidateSet("research", "development")]
    [string]$ProjectType = "research",

    [string]$TargetFolder = "",

    [ValidateSet("yes", "no")]
    [string]$DriveEnabled = "no",

    [string]$DriveParentFolder = "__FOR CLAUDE"
)

$ErrorActionPreference = "Stop"
$Bootstrap = $PSScriptRoot
$Script = Join-Path $Bootstrap "bootstrap\workflows\llm-wiki\scripts\new-project.py"

if (-not (Test-Path $Script)) {
    Write-Host "ERR: new-project.py not found at $Script" -ForegroundColor Red
    Write-Host "Is this the correct package root?" -ForegroundColor Red
    exit 2
}

# Verify python is on PATH
$py = Get-Command python -ErrorAction SilentlyContinue
if (-not $py) { $py = Get-Command python3 -ErrorAction SilentlyContinue }
if (-not $py) {
    Write-Host "ERR: python not found on PATH. Install Python 3.10+ first: https://www.python.org/" -ForegroundColor Red
    exit 2
}

Write-Host "Installing LLM-wiki framework..." -ForegroundColor Cyan
Write-Host "  Tool:         $Tool"
Write-Host "  Project type: $ProjectType"
Write-Host "  Drive ingest: $DriveEnabled"
Write-Host ""

$args = @(
    $Script,
    "--phase", "A",
    "--tool", $Tool,
    "--project-type", $ProjectType,
    "--bootstrap-source", $Bootstrap,
    "--drive-enabled", $DriveEnabled,
    "--drive-parent-folder", $DriveParentFolder
)

if ($Tool -eq "cursor") {
    if (-not $TargetFolder) {
        Write-Host "ERR: -TargetFolder is required for Cursor installs (no global skills dir)" -ForegroundColor Red
        exit 2
    }
    $args += @("--target-folder", $TargetFolder)
}

& $py.Source @args
$exit = $LASTEXITCODE

if ($exit -eq 0) {
    Write-Host ""
    Write-Host "Install complete." -ForegroundColor Green
    Write-Host "Next steps:" -ForegroundColor Green
    Write-Host "  1. Restart Claude Code (or Cursor)"
    Write-Host "  2. In any new project folder, run /new-project to scaffold it"
} elseif ($exit -eq 2) {
    Write-Host ""
    Write-Host "Restart Claude Code, then re-run install-wiki.ps1 to finish setup." -ForegroundColor Yellow
}

exit $exit
