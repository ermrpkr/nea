#!/bin/bash
cd "$(dirname "$0")"
echo ""
echo "============================================================"
echo "  NEA Loss Analysis System - Starting..."
echo "============================================================"
echo ""
if [ -f ".venv/Scripts/python.exe" ]; then
    PY=".venv/Scripts/python.exe"
elif command -v python3 &>/dev/null; then
    if ! python3 -c "import django" 2>/dev/null; then
        echo "Installing dependencies..."
        python3 -m pip install django==4.2.16 openpyxl sqlparse 2>/dev/null
    fi
    PY="python3"
else
    echo "ERROR: Python 3 not found!"; exit 1
fi
echo "[1/3] Migrations..."
$PY manage.py migrate --run-syncdb 2>/dev/null
echo "[2/3] Seeding data..."
$PY manage.py seed_data 2>/dev/null
echo "[3/3] Starting server at http://127.0.0.1:8000"
echo ""
echo "  sysadmin   / nea@admin123   System Administrator"
echo "  md_user    / nea@2024       Managing Director"
echo "  dmd_user   / nea@2024       Deputy Managing Director"
echo "  prov_kvdd  / nea@2024       Provincial Manager"
echo "  dc_ktm     / nea@2024       DC Staff (Kathmandu)"
echo ""
command -v xdg-open &>/dev/null && (sleep 2 && xdg-open http://127.0.0.1:8000 &)
command -v open &>/dev/null && (sleep 2 && open http://127.0.0.1:8000 &)
$PY manage.py runserver 0.0.0.0:8000
