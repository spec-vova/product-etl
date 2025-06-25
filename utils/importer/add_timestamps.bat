@echo off
REM Batch file to add timestamp fields to database tables
REM This script runs the Python script to add created_on and modified_on fields

echo ===============================================
echo Add Timestamp Fields to Database Tables
echo ===============================================
echo.

REM Change to the script directory
cd /d "%~dp0"

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python is not installed or not in PATH
    echo Please install Python and try again.
    pause
    exit /b 1
)

REM Check if .env file exists
if not exist "..\..\..env" (
    echo Warning: .env file not found in project root
    echo Please ensure your database credentials are set in environment variables
    echo.
)

REM Run the Python script
echo Running timestamp addition script...
echo.
python add_timestamps.py

REM Check exit code
if errorlevel 1 (
    echo.
    echo Script completed with errors.
) else (
    echo.
    echo Script completed successfully!
)

echo.
echo Press any key to exit...
pause >nul