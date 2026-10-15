@echo off
cd /d "%~dp0"
powershell.exe -NoProfile -File "%~dp0RUN_REVIEW3.ps1" %*
if errorlevel 1 echo Workflow failed. Read the error above; no research result should be inferred.
pause
