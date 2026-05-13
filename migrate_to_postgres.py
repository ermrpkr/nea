"""
migrate_to_postgres.py
======================
Run this ONCE from the nea_work/ directory to migrate all data
from db.sqlite3 → PostgreSQL.

Usage:
    python migrate_to_postgres.py

Requirements:
    - .env file configured with correct PostgreSQL credentials
    - PostgreSQL database already created (empty)
    - psycopg2-binary installed  (pip install psycopg2-binary)
    - Django + project dependencies installed
"""

import os
import sys
import subprocess
import django

# ── Bootstrap Django with SQLITE so we can read existing data ─────────────────
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'nea_project.settings')

# Force SQLite for the dump phase
from decouple import config
_orig_engine = None

def run(cmd, check=True, **kw):
    print(f"\n>>> {cmd}")
    result = subprocess.run(cmd, shell=True, **kw)
    if check and result.returncode != 0:
        print(f"ERROR: command failed with exit code {result.returncode}")
        sys.exit(1)
    return result

print("=" * 60)
print("  NEA Loss System - SQLite -> PostgreSQL Migration")
print("=" * 60)

# ── Step 1: Dump SQLite data to JSON ─────────────────────────────────────────
print("\n[1/5] Exporting data from SQLite to data_dump.json …")

# Temporarily override DB to SQLite for the dumpdata command
env_sqlite = os.environ.copy()
env_sqlite['DB_ENGINE'] = 'django.db.backends.sqlite3'

result = subprocess.run(
    'python manage.py dumpdata --natural-foreign --natural-primary '
    '--exclude auth.permission --exclude contenttypes '
    '-o data_dump.json',
    shell=True, env=env_sqlite
)
if result.returncode != 0:
    print("ERROR: dumpdata failed. Make sure db.sqlite3 exists and migrations are applied.")
    sys.exit(1)

import json
with open('data_dump.json') as f:
    dump = json.load(f)
print(f"    Exported {len(dump)} records across {len(set(r['model'] for r in dump))} models.")

# ── Step 2: Apply migrations to PostgreSQL ────────────────────────────────────
print("\n[2/5] Running migrate on PostgreSQL (creates all tables) …")
run('python manage.py migrate --run-syncdb')

# ── Step 3: Load data into PostgreSQL ────────────────────────────────────────
print("\n[3/5] Loading data into PostgreSQL …")
run('python manage.py loaddata data_dump.json')

# ── Step 4: Reset PostgreSQL sequences ───────────────────────────────────────
print("\n[4/5] Resetting PostgreSQL auto-increment sequences …")
run('python manage.py sqlsequencereset nea_loss | python manage.py dbshell', check=False)

# ── Step 5: Verify ────────────────────────────────────────────────────────────
print("\n[5/5] Verifying record counts …")
django.setup()

from nea_loss.models import (
    NEAUser, Province, ProvincialOffice, DistributionCenter,
    FiscalYear, LossReport, MonthlyLossData, MeterPoint,
    MeterReading, ConsumerCategory, AuditLog
)

checks = [
    ('NEAUser',             NEAUser.objects.count()),
    ('Province',            Province.objects.count()),
    ('ProvincialOffice',    ProvincialOffice.objects.count()),
    ('DistributionCenter',  DistributionCenter.objects.count()),
    ('FiscalYear',          FiscalYear.objects.count()),
    ('LossReport',          LossReport.objects.count()),
    ('MonthlyLossData',     MonthlyLossData.objects.count()),
    ('MeterPoint',          MeterPoint.objects.count()),
    ('MeterReading',        MeterReading.objects.count()),
    ('ConsumerCategory',    ConsumerCategory.objects.count()),
    ('AuditLog',            AuditLog.objects.count()),
]

print(f"\n    {'Model':<25} {'Count':>8}")
print(f"    {'-'*25} {'-'*8}")
for model, count in checks:
    print(f"    {model:<25} {count:>8}")

print("\n" + "=" * 60)
print("  Migration complete!  Your data is now in PostgreSQL.")
print("  You can delete db.sqlite3 once you have verified.")
print("  Start the server:  python manage.py runserver")
print("=" * 60)