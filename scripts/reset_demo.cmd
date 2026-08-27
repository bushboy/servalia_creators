@echo off
cd /d "%~dp0\.."
python scripts\reset_demo.py %*
if errorlevel 1 pause
