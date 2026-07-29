REM Hide command echoing so users see only launcher status and errors.
@echo off

REM Windows wrapper; secure token handling lives in the PowerShell script.
REM %~dp0 resolves the script's own folder, so it works from any directory.
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0start_ai_demo.ps1"

REM Keep the terminal open only when setup or application startup fails.
if errorlevel 1 pause
