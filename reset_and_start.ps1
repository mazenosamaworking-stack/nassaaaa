# PowerShell Script to Wipe Old State & Start Fresh Server
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $scriptDir

Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host "   WIPING OLD DATA & STARTING FRESH NASA SPACE FIRE AI SERVER (v3.0)" -ForegroundColor White
Write-Host "======================================================================" -ForegroundColor Cyan

# 1. Kill any process on port 8000 and 8500
Write-Host "[1/3] Closing any active server on ports 8000 and 8500..." -ForegroundColor Yellow
Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue | ForEach-Object {
    Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue
}
Get-NetTCPConnection -LocalPort 8500 -ErrorAction SilentlyContinue | ForEach-Object {
    Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue
}

# 2. Delete old database & caches
Write-Host "[2/3] Wiping old database and temporary caches..." -ForegroundColor Yellow
if (Test-Path "space_fire_system.db") {
    Remove-Item "space_fire_system.db" -Force
    Write-Host "  -> Deleted space_fire_system.db" -ForegroundColor Green
}
if (Test-Path "__pycache__") {
    Remove-Item "__pycache__" -Recurse -Force -ErrorAction SilentlyContinue
}
if (Test-Path "core\__pycache__") {
    Remove-Item "core\__pycache__" -Recurse -Force -ErrorAction SilentlyContinue
}

# 3. Start Fresh Server
Write-Host "[3/3] Starting Fresh Clean Server on http://localhost:8500 ..." -ForegroundColor Cyan
$env:PYTHONPATH = "C:\Program Files\Autodesk\3ds Max 2023\Python"
$env:PYTHONIOENCODING = "utf-8"
$pythonExe = "C:\Program Files\Autodesk\3ds Max 2023\Python\python.exe"

& $pythonExe server.py 8500
