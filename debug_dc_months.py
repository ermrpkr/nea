#!/usr/bin/env python
import os
import sys
import django

# Add the project path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'nea_project.settings')
django.setup()

from nea_loss.models import DistributionCenter, LossReport, FiscalYear

def debug_dc_months():
    print("=== DC START MONTH DEBUG ===")
    
    # Get DC Kathmandu
    dc_ktm = DistributionCenter.objects.filter(name__icontains='kathmandu').first()
    if dc_ktm:
        print(f'DC Kathmandu found: {dc_ktm.name}')
        print(f'  Report Start Month: {dc_ktm.report_start_month} ({dc_ktm.get_report_start_month_display()})')
        print(f'  Is Active: {dc_ktm.is_active}')
    else:
        print('DC Kathmandu not found')
        return
    
    # Check active fiscal year
    active_fy = FiscalYear.objects.filter(is_active=True).first()
    if active_fy:
        print(f'\nActive Fiscal Year: {active_fy.year_bs}')
    else:
        print('\nNo active fiscal year found')
        return
    
    # Check existing reports for DC Kathmandu
    print(f'\nExisting reports for DC Kathmandu:')
    reports = LossReport.objects.filter(
        distribution_center=dc_ktm,
        fiscal_year=active_fy
    ).order_by('month')
    
    if reports.exists():
        for report in reports:
            print(f'  Month {report.month} ({report.get_month_display()}) - Status: {report.status}')
    else:
        print('  No reports found')
    
    # Show what months should be available
    all_months = [
        (1,'Shrawan'),(2,'Bhadra'),(3,'Ashwin'),(4,'Kartik'),
        (5,'Mangsir'),(6,'Poush'),(7,'Magh'),(8,'Falgun'),
        (9,'Chaitra'),(10,'Baisakh'),(11,'Jestha'),(12,'Ashadh'),
    ]
    
    print(f'\nMonths that should be available (start month = {dc_ktm.report_start_month}):')
    for month_num, month_name in all_months:
        if month_num >= dc_ktm.report_start_month:
            # Check if report already exists
            existing = reports.filter(month=month_num).exists()
            status = "EXISTS" if existing else "AVAILABLE"
            print(f'  Month {month_num} ({month_name}) - {status}')

if __name__ == '__main__':
    debug_dc_months()
