@echo off
title II Indexation Checker - Inbound Interactive
echo.
echo ================================
echo  II INDEXATION CHECKER v2.0
echo  Inbound Interactive SEO Tool
echo ================================
echo.
echo Starting beautiful GUI interface...
echo.
python ii_indexation_gui_simple.py
if errorlevel 1 (
    echo.
    echo Error: Failed to start the application.
    echo Please ensure Python is installed and requirements are met.
    echo.
)
pause