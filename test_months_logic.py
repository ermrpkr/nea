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

def test_months_logic():
    print("=== TESTING MONTHS LOGIC ===")
    
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
    
    # Test the exact logic from ReportCreateView
    dcs = [dc_ktm]  # Simulate DC user
    all_months = [
        (1,'Shrawan'),(2,'Bhadra'),(3,'Ashwin'),(4,'Kartik'),
        (5,'Mangsir'),(6,'Poush'),(7,'Magh'),(8,'Falgun'),
        (9,'Chaitra'),(10,'Baisakh'),(11,'Jestha'),(12,'Ashadh'),
    ]
    
    available_months = []
    
    for month_num, month_name in all_months:
        print(f'\nChecking Month {month_num} ({month_name}):')
        can_create = True
        
        # Check if report already exists for this month
        existing_report = LossReport.objects.filter(
            distribution_center__in=dcs,
            fiscal_year=active_fy,
            month=month_num
        ).first()
        
        if existing_report:
            print(f'  - Report already exists: {existing_report.status}')
            can_create = False
        else:
            print(f'  - No existing report')
            # For new reports, check if month is before the DC's report start month
            for dc in dcs:
                if month_num < dc.report_start_month:
                    print(f'  - Month {month_num} is before start month {dc.report_start_month}')
                    can_create = False
                    break
        
        # For months other than Shrawan, check if previous month is approved
        # But skip this check for the DC's start month
        if month_num > 1 and can_create:
            # Check if this is the start month for any DC
            is_start_month = False
            for dc in dcs:
                if month_num == dc.report_start_month:
                    is_start_month = True
                    break
            
            if not is_start_month:
                previous_month = month_num - 1
                previous_report = LossReport.objects.filter(
                    distribution_center__in=dcs,
                    fiscal_year=active_fy,
                    month=previous_month,
                    status='APPROVED'
                ).first()
                
                if not previous_report:
                    print(f'  - Previous month {previous_month} not approved')
                    can_create = False
                else:
                    print(f'  - Previous month {previous_month} is approved')
            else:
                print(f'  - This is start month, skipping previous month approval check')
        
        if can_create:
            print(f'  - CAN CREATE: Adding to available months')
            available_months.append((month_num, month_name))
        else:
            print(f'  - CANNOT CREATE')
    
    print(f'\n=== FINAL RESULT ===')
    print(f'Available months: {available_months}')

if __name__ == '__main__':
    test_months_logic()
