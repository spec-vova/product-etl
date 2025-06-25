@echo off
echo Furnithai ETL Process Runner
echo ===========================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo Error: Python is not installed or not in PATH
    echo Please install Python and try again
    exit /b 1
)

REM Check if required files exist
if not exist ETL.py (
    echo Error: ETL.py not found
    echo Please run this batch file from the utils/importer directory
    exit /b 1
)

if not exist run_etl.py (
    echo Error: run_etl.py not found
    echo Please run this batch file from the utils/importer directory
    exit /b 1
)

REM Check if .env file exists
if not exist .env (
    echo Warning: .env file not found
    echo Creating a template .env file...
    echo DB_NAME=furnithai> .env
    echo DB_USER=postgres>> .env
    echo DB_PASS=postgres>> .env
    echo DB_PORT=5433>> .env
    echo Please edit the .env file with your database credentials
    echo.
)

echo Available commands:
echo 1. Install dependencies
echo 2. Run tests
echo 3. Run ETL with dry-run (no database changes)
echo 4. Run ETL (with database changes)
echo 5. Exit
echo.

set /p choice=Enter your choice (1-5): 

if "%choice%"=="1" (
    echo Installing dependencies...
    pip install -r requirements.txt
    echo.
    echo Dependencies installed.
    pause
    exit /b 0
)

if "%choice%"=="2" (
    echo Running tests...
    python test_etl.py
    pause
    exit /b 0
)

if "%choice%"=="3" (
    echo Running ETL in dry-run mode...
    python run_etl.py --dry-run
    pause
    exit /b 0
)

if "%choice%"=="4" (
    echo WARNING: This will modify the database.
    set /p confirm=Are you sure you want to continue? (y/n): 
    if /i "%confirm%"=="y" (
        echo Running ETL...
        python run_etl.py
    ) else (
        echo Operation cancelled.
    )
    pause
    exit /b 0
)

if "%choice%"=="5" (
    echo Exiting...
    exit /b 0
)

echo Invalid choice. Please try again.
pause