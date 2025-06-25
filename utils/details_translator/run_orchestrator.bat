@echo off
setlocal enabledelayedexpansion

REM Check if Python is installed
python --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo Python is not installed or not in PATH. Please install Python 3.7 or higher.
    pause
    exit /b 1
)

REM Check if .env file exists, create template if not
if not exist ".env" (
    echo .env file not found. Creating template...
    copy .env.template .env
    echo Please edit the .env file with your database and API credentials.
    notepad .env
    pause
    exit /b 0
)

REM Display menu
:menu
cls
echo ===== Details Translator with Database Integration =====
echo.
echo 1. Install dependencies
echo 2. Test environment setup
echo 3. Run in dry-run mode (no database changes)
echo 4. Run with database changes (with confirmation)
echo 5. Run with custom options
echo 6. Exit
echo.

set /p choice=Enter your choice (1-6): 

if "%choice%"=="1" goto install_deps
if "%choice%"=="2" goto test_env
if "%choice%"=="3" goto dry_run
if "%choice%"=="4" goto run_with_changes
if "%choice%"=="5" goto custom_options
if "%choice%"=="6" goto end

echo Invalid choice. Please try again.
pause
goto menu

:install_deps
echo Installing dependencies...
pip install -r requirements.txt
echo Dependencies installed.
pause
goto menu

:test_env
echo Testing environment setup...
python test_connection.py
pause
goto menu

:dry_run
echo Running in dry-run mode...
python run_orchestrator.py --dry-run
pause
goto menu

:run_with_changes
echo WARNING: This will make changes to the database.
set /p confirm=Are you sure you want to continue? (y/n): 
if /i "%confirm%"=="y" (
    echo Running with database changes...
    python run_orchestrator.py
) else (
    echo Operation cancelled.
)
pause
goto menu

:custom_options
echo Enter custom options (leave blank to skip):
echo.

set limit=
set /p limit=Limit number of products (0 = no limit): 

set product_id=
set /p product_id=Process specific product ID (optional): 

set collection_id=
set /p collection_id=Process specific collection ID (optional): 

set skip_options=

set /p skip_download=Skip image download? (y/n): 
if /i "%skip_download%"=="y" set skip_options=!skip_options! --skip-download

set /p skip_ocr=Skip OCR processing? (y/n): 
if /i "%skip_ocr%"=="y" set skip_options=!skip_options! --skip-ocr

set /p skip_translation=Skip translation? (y/n): 
if /i "%skip_translation%"=="y" set skip_options=!skip_options! --skip-translation

set /p skip_logistics=Skip logistics extraction? (y/n): 
if /i "%skip_logistics%"=="y" set skip_options=!skip_options! --skip-logistics

set /p dry_run=Run in dry-run mode? (y/n): 
if /i "%dry_run%"=="y" set skip_options=!skip_options! --dry-run

set command=python run_orchestrator.py

if not "%limit%"=="" set command=!command! --limit %limit%
if not "%product_id%"=="" set command=!command! --product-id "%product_id%"
if not "%collection_id%"=="" set command=!command! --collection-id "%collection_id%"

echo.
echo Running command: !command!!skip_options!
echo.
!command!!skip_options!

pause
goto menu

:end
echo Exiting...
exit /b 0