<#
Simple helper to create a virtualenv (if missing), optionally install requirements,
and start the FastAPI backend with Uvicorn.

Usage:
  PowerShell: .\start_backend.ps1             # start server (no install)
  PowerShell: .\start_backend.ps1 --install   # install deps then start
#>

param(
    [switch]$install
)

$venv = ".venv"
if (-not (Test-Path $venv)) {
    python -m venv $venv
}

$py = Join-Path $venv "Scripts\python.exe"
if ($install) {
    & $py -m pip install -r backend/requirements.txt
}

Write-Host "Starting backend via $py..."
& $py -m uvicorn backend.app:app --reload --host 127.0.0.1 --port 8000
