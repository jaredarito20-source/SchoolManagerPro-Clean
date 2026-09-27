# ============================================================
# SchoolManagerPro Automated Backup
# ============================================================

$ErrorActionPreference = "Stop"

$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$VenvPython = Join-Path $ProjectRoot "venv\Scripts\python.exe"
$LogDirectory = Join-Path $ProjectRoot "backups"
$LogFile = Join-Path $LogDirectory "backup_scheduler.log"

Set-Location $ProjectRoot

if (-not (Test-Path $VenvPython)) {
    throw "Python virtual environment was not found at $VenvPython"
}

if (-not (Test-Path $LogDirectory)) {
    New-Item -ItemType Directory -Path $LogDirectory | Out-Null
}

$StartTime = Get-Date

"============================================================" | Add-Content $LogFile
"SchoolManagerPro automated backup" | Add-Content $LogFile
"Started: $StartTime" | Add-Content $LogFile

try {

    & $VenvPython manage.py backup_schoolmanagerpro

    if ($LASTEXITCODE -ne 0) {
        throw "Backup command failed with exit code $LASTEXITCODE"
    }

    & $VenvPython manage.py cleanup_schoolmanagerpro_backups --keep 14 --confirm

    if ($LASTEXITCODE -ne 0) {
        throw "Backup retention cleanup failed with exit code $LASTEXITCODE"
    }

    $EndTime = Get-Date

    "Backup completed successfully." | Add-Content $LogFile
    "Finished: $EndTime" | Add-Content $LogFile
    "" | Add-Content $LogFile

    exit 0
}
catch {

    $FailureTime = Get-Date

    "BACKUP FAILED." | Add-Content $LogFile
    "Time: $FailureTime" | Add-Content $LogFile
    "Error: $($_.Exception.Message)" | Add-Content $LogFile
    "" | Add-Content $LogFile

    exit 1
}