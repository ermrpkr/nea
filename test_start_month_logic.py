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

def test_start_month_logic():
    print("=== TESTING START MONTH LOGIC ===")
    
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
    
    # Test different scenarios
    test_months = [
        (8, 'Falgun'),
        (9, 'Chaitra'),
        (10, 'Baisakh'),
        (11, 'Jestha'),
    ]
    
    for month_num, month_name in test_months:
        print(f'\n--- Testing Month {month_num} ({month_name}) ---')
        
        # Check if month is before start month
        if month_num < dc_ktm.report_start_month:
            print(f'  - Month {month_num} is BEFORE start month ({dc_ktm.report_start_month})')
            print(f'  - SHOULD NOT BE AVAILABLE in dropdown')
            print(f'  - SHOULD NOT ALLOW creation')
        else:
            print(f'  - Month {month_num} is >= start month ({dc_ktm.report_start_month})')
            
            # Check if report already exists
            existing_report = LossReport.objects.filter(
                distribution_center=dc_ktm,
                fiscal_year=active_fy,
                month=month_num
            ).first()
            
            if existing_report:
                print(f'  - Report already exists: {existing_report.status}')
                print(f'  - SHOULD NOT BE AVAILABLE in dropdown')
            else:
                print(f'  - No existing report')
                print(f'  - SHOULD BE AVAILABLE in dropdown')
                
                # Check previous month approval logic
                if month_num == dc_ktm.report_start_month:
                    print(f'  - This is the START MONTH')
                    print(f'  - SHOULD SKIP previous month approval check')
                    print(f'  - SHOULD ALLOW creation')
                else:
                    print(f'  - This is NOT the start month')
                    previous_month = month_num - 1
                    previous_report = LossReport.objects.filter(
                        distribution_center=dc_ktm,
                        fiscal_year=active_fy,
                        month=previous_month
                    ).first()
                    
                    if previous_report and previous_report.status == 'APPROVED':
                        print(f'  - Previous month {previous_month} is APPROVED')
                        print(f'  - SHOULD ALLOW creation')
                    else:
                        print(f'  - Previous month {previous_month} is NOT approved or doesn\'t exist')
                        print(f'  - SHOULD BLOCK creation')

if __name__ == '__main__':
    test_start_month_logic()
