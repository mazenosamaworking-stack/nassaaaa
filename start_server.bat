@echo off
title NASA Space Fire AI System - Server
echo ======================================================================
echo    NASA SPACE FIRE AI SYSTEM - MULTI-AGENT MISSION CONTROL
echo ======================================================================
echo  [Agent 1] NASA Fire Occurrence and Hazard Predictor
echo  [Agent 2] Incident Root-Cause and Safety Action Chatbot
echo  [Agent 3] Autonomous ISS Live Telemetry Streamer (1s updates)
echo  [Agent 4] AI Flame Visual Dynamics Simulation (Physics-Grounded)
echo ======================================================================

set PYTHONPATH=C:\Program Files\Autodesk\3ds Max 2023\Python
set PYTHONIOENCODING=utf-8
set PYTHON_EXE="C:\Program Files\Autodesk\3ds Max 2023\Python\python.exe"

cd /d "%~dp0"
echo Starting Server on http://localhost:8500 ...
%PYTHON_EXE% server.py 8500
pause
