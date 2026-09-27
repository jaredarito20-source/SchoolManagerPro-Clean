# ============================================================
# SchoolManagerPro Production Server
# ============================================================

$ErrorActionPreference = "Stop"

$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$VenvPython = Join-Path $ProjectRoot "venv\Scripts\python.exe"

Set-Location $ProjectRoot

if (-not (Test-Path $VenvPython)) {
    Write-Error "Python virtual environment was not found at $VenvPython"
    exit 1
}

Write-Host "Starting SchoolManagerPro..." -ForegroundColor Green
Write-Host "Project: $ProjectRoot"
Write-Host "Server: 127.0.0.1:8000"
Write-Host ""

& $VenvPython -m waitress `
    --listen=127.0.0.1:8000 `
    school.wsgi:application