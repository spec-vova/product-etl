@echo off
chcp 65001 >nul
echo.
echo ========================================
echo   Product Inheritance Migration
echo ========================================
echo.
echo This script will:
echo 1. Add inherited fields to product table
echo 2. Update existing products with collection data
echo 3. Create necessary indexes
echo.
echo Fields to be inherited:
echo - product_collection_url
echo - product_collection_image  
echo - images (array)
echo.
set /p confirm="Do you want to continue? (y/N): "
if /i not "%confirm%"=="y" (
    echo Migration cancelled.
    pause
    exit /b
)

echo.
echo Starting migration...
echo.

python migrate_product_inheritance.py

if %errorlevel% equ 0 (
    echo.
    echo ✅ Migration completed successfully!
) else (
    echo.
    echo ❌ Migration failed! Check the error messages above.
)

echo.
echo Press any key to exit...
pause >nul