@echo off
title NEA Loss Analysis System
color 0A
cd /d "%~dp0"

echo.
echo ============================================================
echo   NEA Loss Analysis System - Starting...
echo ============================================================
echo.

if not exist ".venv\Scripts\python.exe" (
    echo ERROR: Virtual environment not found!
    echo Please run setup first.
    pause
    exit /b 1
)

if not exist ".env" (
    echo ERROR: .env file not found!
    echo Please create .env from the .env template provided.
    pause
    exit /b 1
)

echo [1/3] Installing / checking dependencies...
.venv\Scripts\pip.exe install -r requirements.txt -q

echo [2/3] Running database migrations...
.venv\Scripts\python.exe manage.py migrate --run-syncdb

echo [3/3] Starting server...
echo.
echo ============================================================
echo   OPEN IN BROWSER: http://127.0.0.1:8000
echo.
echo   sysadmin   / nea@admin123   System Administrator
echo   md_user    / nea@2024       Managing Director
echo   dmd_user   / nea@2024       Deputy Managing Director
echo   prov_kvdd  / nea@2024       Provincial Manager (KVDD)
echo   dc_ktm     / nea@2024       DC Staff (Kathmandu DC)
echo   dc_lpr     / nea@2024       DC Staff (Lalitpur DC)
echo   dc_nuw     / nea@2024       DC Staff (Nuwakot DC)
echo   dc_pkr     / nea@2024       DC Staff (Pokhara DC)
echo ============================================================
echo   Django Admin: http://127.0.0.1:8000/admin/
echo   Press Ctrl+C to stop.
echo.

start http://127.0.0.1:8000
.venv\Scripts\python.exe manage.py runserver 0.0.0.0:8000
pause