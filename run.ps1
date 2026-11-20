# One-command script to launch the Robo-helper simulation
$ErrorActionPreference = "Stop"

$RepoRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $RepoRoot

# Use root venv python if available
if (Test-Path "$RepoRoot\.venv\Scripts\python.exe") {
    $PythonExe = "$RepoRoot\.venv\Scripts\python.exe"
} else {
    $PythonExe = "python"
}

Write-Host "Starting Robo-helper simulation via $PythonExe run_simulation.py..." -ForegroundColor Cyan
& $PythonExe run_simulation.py @args
