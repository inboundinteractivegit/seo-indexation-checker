@echo off
echo.
echo ====================================
echo   II Indexation Checker - Modern GUI
echo ====================================
echo.
echo Starting modern PyQt6 interface...
echo.

cd /d "%~dp0"
python ii_indexation_gui_modern.py

echo.
echo GUI closed. Press any key to exit...
pause > nul