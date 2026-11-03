# PowerShell Launcher for NASA Space Fire AI System
$ErrorActionPreference = "Stop"

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $scriptDir

$env:PYTHONPATH = "C:\Program Files\Autodesk\3ds Max 2023\Python"
$env:PYTHONIOENCODING = "utf-8"
$pythonExe = "C:\Program Files\Autodesk\3ds Max 2023\Python\python.exe"

Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host "   NASA SPACE FIRE AI SYSTEM - MULTI-AGENT MISSION CONTROL" -ForegroundColor White
Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host "  [Agent 1] NASA Fire Occurrence & Hazard Predictor" -ForegroundColor Green
Write-Host "  [Agent 2] Incident Root-Cause & Safety Action Chatbot" -ForegroundColor Yellow
Write-Host "  [Agent 3] Autonomous ISS Live Telemetry Streamer (1s updates)" -ForegroundColor Blue
Write-Host "  [Agent 4] AI Flame Visual Dynamics Simulation (Physics-Grounded)" -ForegroundColor Red
Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host "Server running at: http://localhost:8500" -ForegroundColor Green

& $pythonExe server.py 8500
