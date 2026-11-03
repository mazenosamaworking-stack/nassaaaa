@echo off
title Reset & Start NASA Space Fire AI Server
echo ======================================================================
echo    WIPING OLD DATA & STARTING FRESH NASA SPACE FIRE AI SERVER
echo ======================================================================

cd /d "%~dp0"

echo [1/3] Closing any active server on ports 8000 and 8500...
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :8000') do (
    taskkill /F /PID %%a 2>nul
)
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :8500') do (
    taskkill /F /PID %%a 2>nul
)

echo [2/3] Deleting old database and cache...
if exist space_fire_system.db del /f /q space_fire_system.db
if exist __pycache__ rmdir /s /q __pycache__
if exist core\__pycache__ rmdir /s /q core\__pycache__

echo [3/3] Starting Fresh Server on http://localhost:8500 ...
set PYTHONPATH=C:\Program Files\Autodesk\3ds Max 2023\Python
set PYTHONIOENCODING=utf-8
"C:\Program Files\Autodesk\3ds Max 2023\Python\python.exe" server.py 8500
pause
