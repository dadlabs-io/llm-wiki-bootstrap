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
#>

param(
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

$py = Get-Command python -ErrorAction SilentlyContinue
if (-not $py) { $py = Get-Command python3 -ErrorAction SilentlyContinue }
if (-not $py) {
    Write-Host "ERR: python not found on PATH. Install Python 3.10+ first: https://www.python.org/" -ForegroundColor Red
    exit 2
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
