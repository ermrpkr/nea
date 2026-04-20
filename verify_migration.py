#!/usr/bin/env python
"""
Verify PostgreSQL migration success
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'nea_project.settings')
django.setup()

from nea_loss.models import NEAUser, Province, ProvincialOffice, DistributionCenter, FiscalYear, LossReport, MonthlyLossData, MeterPoint, MeterReading, ConsumerCategory, AuditLog
from django.db import connection

print('PostgreSQL Migration Verification:')
print('=' * 50)

checks = [
    ('NEAUser', NEAUser.objects.count()),
    ('Province', Province.objects.count()),
    ('ProvincialOffice', ProvincialOffice.objects.count()),
    ('DistributionCenter', DistributionCenter.objects.count()),
    ('FiscalYear', FiscalYear.objects.count()),
    ('LossReport', LossReport.objects.count()),
    ('MonthlyLossData', MonthlyLossData.objects.count()),
    ('MeterPoint', MeterPoint.objects.count()),
    ('MeterReading', MeterReading.objects.count()),
    ('ConsumerCategory', ConsumerCategory.objects.count()),
    ('AuditLog', AuditLog.objects.count()),
]

print(f"{'Model':<25} {'Count':>8}")
print(f"{'-'*25} {'-'*8}")
total_records = 0
for model, count in checks:
    print(f"{model:<25} {count:>8}")
    total_records += count

print(f"{'-'*25} {'-'*8}")
print(f"{'TOTAL':<25} {total_records:>8}")

print(f"\nDatabase Engine: {connection.vendor}")
print(f"Database Name: {connection.settings_dict['NAME']}")

if total_records > 0:
    print("\nMigration Status: SUCCESS")
    print(f"Successfully migrated {total_records} records to PostgreSQL")
else:
    print("\nMigration Status: FAILED")
    print("No records found in PostgreSQL")
