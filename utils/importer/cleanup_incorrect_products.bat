@echo off
echo Product Cleanup Script
echo ======================
echo.
echo This script will remove incorrectly processed products from the database.
echo Run this BEFORE executing the corrected ETL.py script.
echo.
pause

cd /d "%~dp0"
python cleanup_incorrect_products.py

echo.
echo Cleanup completed. Press any key to exit.
pause > nul