#!/usr/bin/env python
import os
import sys
import django

# Add the project path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'nea_project.settings')
django.setup()

from nea_loss.models import DistributionCenter, LossReport, FiscalYear, NEAUser

def test_report_creation_logic():
    print("=== TESTING REPORT CREATION LOGIC ===")
    
    # Get DC Kathmandu
    dc_ktm = DistributionCenter.objects.filter(name__icontains='kathmandu').first()
    if not dc_ktm:
        print('DC Kathmandu not found')
        return
    
    print(f'DC: {dc_ktm.name}')
    print(f'Start Month: {dc_ktm.report_start_month} ({dc_ktm.get_report_start_month_display()})')
    
    # Get active fiscal year
    active_fy = FiscalYear.objects.filter(is_active=True).first()
    if not active_fy:
        print('No active fiscal year found')
        return
    
    print(f'Active Fiscal Year: {active_fy.year_bs}')
    
    # Test the POST method logic for month 9 (Chaitra)
    month = 9
    month_name = 'Chaitra'
    
    print(f'\n=== TESTING MONTH {month} ({month_name}) CREATION ===')
    
    # Check if this is the DC's start month
    if month == dc_ktm.report_start_month:
        print(f'  - This is the DC start month ({dc_ktm.report_start_month})')
        print(f'  - SKIPPING previous month approval check')
        print(f'  - SHOULD ALLOW CREATION')
    else:
        print(f'  - This is NOT the DC start month')
        print(f'  - Would check previous month approval')
        previous_month = month - 1
        previous_report = LossReport.objects.filter(
            distribution_center=dc_ktm,
            fiscal_year=active_fy,
            month=previous_month
        ).first()
        
        if previous_report and previous_report.status == 'APPROVED':
            print(f'  - Previous month {previous_month} is approved')
            print(f'  - SHOULD ALLOW CREATION')
        else:
            print(f'  - Previous month {previous_month} is not approved or doesn\'t exist')
            print(f'  - WOULD BLOCK CREATION')
    
    # Test month 10 (Baisakh) - should be blocked
    month = 10
    month_name = 'Baisakh'
    print(f'\n=== TESTING MONTH {month} ({month_name}) CREATION ===')
    
    if month == dc_ktm.report_start_month:
        print(f'  - This is the DC start month')
        print(f'  - SKIPPING previous month approval check')
        print(f'  - SHOULD ALLOW CREATION')
    else:
        print(f'  - This is NOT the DC start month')
        print(f'  - Would check previous month approval')
        previous_month = month - 1
        previous_report = LossReport.objects.filter(
            distribution_center=dc_ktm,
            fiscal_year=active_fy,
            month=previous_month
        ).first()
        
        if previous_report and previous_report.status == 'APPROVED':
            print(f'  - Previous month {previous_month} is approved')
            print(f'  - SHOULD ALLOW CREATION')
        else:
            print(f'  - Previous month {previous_month} is not approved or doesn\'t exist')
            print(f'  - WOULD BLOCK CREATION')

if __name__ == '__main__':
    test_report_creation_logic()
