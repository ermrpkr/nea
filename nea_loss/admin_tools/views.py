from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.db import transaction
from django.contrib import messages
from decimal import Decimal
from django.db.models import Q

from ..models import (
    DistributionCenter, FiscalYear, LossReport, MonthlyLossData,
    MeterReading, MeterPoint, MonthlyMeterPointStatus,
    EnergyUtilisation, ConsumerCategory, ConsumerCount,
    AuditLog, Notification, NEAUser
)

# ─────────────────────────── ADMIN DC REPORT CREATION ───────────────────────────

def admin_dc_report(request):
    """Admin view to create draft reports for DC using approved reports as templates"""
    if not getattr(request.user, 'is_system_admin', False):
        messages.error(request, 'Only system administrators can create DC reports.')
        return redirect('dashboard')
    
    # Handle AJAX requests first
    if request.method == 'POST' and request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        action = request.POST.get('action')
        
        if action == 'get_months':
            dc_id = request.POST.get('dc_id')
            if not dc_id:
                return JsonResponse({'error': 'DC ID required'}, status=400)
            
            try:
                dc = DistributionCenter.objects.get(pk=dc_id)
                active_fy = FiscalYear.objects.filter(is_active=True).first()
                
                if not active_fy:
                    return JsonResponse({'error': 'No active fiscal year'}, status=400)
                
                # Get existing reports for this DC
                existing_months = set(
                    LossReport.objects.filter(
                        distribution_center=dc, 
                        fiscal_year=active_fy
                    ).values_list('month', flat=True)
                )
                
                # Get all months in order
                all_months = [(i, name) for i, name in [
                    (1, 'Shrawan'), (2, 'Bhadra'), (3, 'Ashwin'), (4, 'Kartik'),
                    (5, 'Mangsir'), (6, 'Poush'), (7, 'Magh'), (8, 'Falgun'),
                    (9, 'Chaitra'), (10, 'Baisakh'), (11, 'Jestha'), (12, 'Ashadh')
                ]]
                
                # Find the next available month
                next_month = None
                for month_num, month_name in all_months:
                    if month_num not in existing_months:
                        next_month = month_num
                        break
                
                if next_month:
                    # Only show the next available month
                    month_name = dict(all_months)[next_month]
                    available_months = [{'value': next_month, 'text': month_name}]
                else:
                    # All months have reports
                    available_months = []
                
                return JsonResponse({'months': available_months})
                
            except DistributionCenter.DoesNotExist:
                return JsonResponse({'error': 'DC not found'}, status=404)
            except Exception as e:
                return JsonResponse({'error': f'Error: {str(e)}'}, status=500)
        
        elif action == 'get_approved_reports':
            dc_id = request.POST.get('dc_id')
            month = request.POST.get('month')
            
            if not all([dc_id, month]):
                return JsonResponse({'error': 'DC ID and month required'}, status=400)
            
            try:
                dc = DistributionCenter.objects.get(pk=dc_id)
                active_fy = FiscalYear.objects.filter(is_active=True).first()
                
                if not active_fy:
                    return JsonResponse({'error': 'No active fiscal year'}, status=400)
                
                # Get ALL approved reports from ALL DCs to use as templates
                approved_reports = LossReport.objects.filter(
                    fiscal_year=active_fy,
                    status='APPROVED'
                ).select_related('distribution_center', 'created_by').order_by('distribution_center__name', 'month')
                
                reports_data = []
                for report in approved_reports:
                    monthly_data = report.monthly_data.first()
                    reports_data.append({
                        'id': report.pk,
                        'dc_name': report.distribution_center.name,
                        'month': report.get_month_display(),
                        'received': float(monthly_data.net_energy_received) if monthly_data else 0,
                        'loss': float(monthly_data.loss_unit) if monthly_data else 0,
                        'loss_percent': float(monthly_data.monthly_loss_percent * 100) if monthly_data else 0,
                        'created_by': report.created_by.full_name if report.created_by else 'System'
                    })
                
                return JsonResponse({'reports': reports_data})
                
            except DistributionCenter.DoesNotExist:
                return JsonResponse({'error': 'DC not found'}, status=404)
            except Exception as e:
                return JsonResponse({'error': f'Error: {str(e)}'}, status=500)
    
    # Handle GET request - show the form
    if request.method == 'GET':
        # Get all DCs
        dcs = DistributionCenter.objects.filter(is_active=True).order_by('name')
        active_fy = FiscalYear.objects.filter(is_active=True).first()
        
        context = {
            'dcs': dcs,
            'active_fy': active_fy,
        }
        return render(request, 'admin_tools/dc_report.html', context)
    
    # Handle POST request - create the report
    elif request.method == 'POST':
        action = request.POST.get('action')
        
        # Handle AJAX create report request
        if action == 'create_report':
            dc_id = request.POST.get('dc_id')
            month = request.POST.get('month')
            template_report_id = request.POST.get('template_report_id')
            
            if not all([dc_id, month, template_report_id]):
                return JsonResponse({'success': False, 'error': 'Please select DC, month, and template report'})
            
            try:
                dc = DistributionCenter.objects.get(pk=dc_id)
                month = int(month)
                template_report = LossReport.objects.get(pk=template_report_id)
                active_fy = FiscalYear.objects.filter(is_active=True).first()
                
                if not active_fy:
                    return JsonResponse({'success': False, 'error': 'No active fiscal year found'})
                
                # Check if report already exists
                existing_report = LossReport.objects.filter(
                    distribution_center=dc, fiscal_year=active_fy, month=month
                ).first()
                if existing_report:
                    return JsonResponse({
                        'success': False, 
                        'error': f'Report for {existing_report.get_month_display()} already exists for {dc.name}'
                    })
                
                # Create the draft report
                with transaction.atomic():
                    new_report = LossReport.objects.create(
                        distribution_center=dc,
                        fiscal_year=active_fy,
                        month=month,
                        status='DRAFT',
                        created_by=request.user,
                        total_received_kwh=Decimal('0'),
                        total_utilised_kwh=Decimal('0'),
                        total_loss_kwh=Decimal('0'),
                        cumulative_loss_percent=Decimal('0')
                    )
                    
                    # Copy data from template
                    template_data = template_report.monthly_data.first()
                    if template_data:
                        month_names = {
                            1:'Shrawan',2:'Bhadra',3:'Ashwin',4:'Kartik',
                            5:'Mangsir',6:'Poush',7:'Magh',8:'Falgun',
                            9:'Chaitra',10:'Baisakh',11:'Jestha',12:'Ashadh'
                        }
                        
                        # Create MonthlyLossData
                        new_monthly_data = MonthlyLossData.objects.create(
                            report=new_report,
                            month=month,
                            month_name=month_names[month],
                            total_energy_import=template_data.total_energy_import,
                            total_energy_export=template_data.total_energy_export,
                            net_energy_received=template_data.net_energy_received,
                            total_energy_utilised=template_data.total_energy_utilised,
                            loss_unit=template_data.loss_unit,
                            monthly_loss_percent=template_data.monthly_loss_percent,
                            cumulative_loss_percent=template_data.cumulative_loss_percent
                        )
                        
                        # Copy all data
                        _copy_meter_readings_simple(template_data, new_monthly_data, dc)
                        _copy_energy_utilisations_simple(template_data, new_monthly_data, dc)
                        _copy_consumer_counts_simple(template_data, new_monthly_data, dc)
                        
                        # Update report totals
                        new_report.total_received_kwh = template_data.net_energy_received
                        new_report.total_utilised_kwh = template_data.total_energy_utilised
                        new_report.total_loss_kwh = template_data.loss_unit
                        new_report.cumulative_loss_percent = template_data.cumulative_loss_percent
                        new_report.save()
                    
                    # Create audit log
                    AuditLog.objects.create(
                        user=request.user,
                        action='CREATE',
                        model_name='LossReport',
                        object_id=new_report.pk,
                        description=f"Admin created draft report for {dc.name} - {new_report.get_month_display()} using template from {template_report.distribution_center.name}"
                    )
                    
                    # Notify DC users
                    dc_users = NEAUser.objects.filter(
                        distribution_center=dc,
                        role__in=['DC_MANAGER', 'DC_STAFF']
                    )
                    for user in dc_users:
                        Notification.objects.create(
                            recipient=user,
                            notification_type='REPORT_SUBMITTED',
                            title=f'Draft Report Created for {month_names[month]}',
                            message=f'System administrator has created a draft {month_names[month]} report for {dc.name}. Please review and complete the data entry.',
                            related_report=new_report
                        )
                
                return JsonResponse({
                    'success': True,
                    'message': f'Successfully created draft {month_names[month]} report for {dc.name}',
                    'report_url': f'/admin-tools/monthly-data/{new_report.pk}/{month}/'
                })
                
            except Exception as e:
                return JsonResponse({'success': False, 'error': f'Error creating report: {str(e)}'})
        
        # Handle regular POST (shouldn't happen with current setup)
        else:
            return JsonResponse({'success': False, 'error': 'Invalid request'})


def _copy_meter_readings_simple(template_data, new_monthly_data, target_dc):
    """Copy meter readings from template to target DC with editable readings"""
    # Get target DC's meter points to ensure proper data structure
    target_meter_points = MeterPoint.objects.filter(distribution_center=target_dc, is_active=True)
    
    template_readings = list(template_data.meter_readings.all())
    
    if not target_meter_points.exists():
        # If target DC has no meter points, create them based on template
        for template_reading in template_readings:
            template_mp = template_reading.meter_point
            # Create a new meter point for target DC based on template structure
            new_mp = MeterPoint.objects.create(
                distribution_center=target_dc,
                name=template_mp.name,
                source_type=template_mp.source_type,
                voltage_level=template_mp.voltage_level,
                multiplying_factor=template_mp.multiplying_factor,
                is_single_reading=template_mp.is_single_reading,
                is_active=True
            )
            
            # Create reading for the new meter point
            MeterReading.objects.create(
                monthly_data=new_monthly_data,
                meter_point=new_mp,
                present_reading=template_reading.present_reading,
                previous_reading=template_reading.previous_reading,
                difference=template_reading.difference,
                multiplying_factor=template_reading.multiplying_factor,
                unit_kwh=template_reading.unit_kwh
            )
            
            MonthlyMeterPointStatus.objects.create(
                monthly_data=new_monthly_data,
                meter_point=new_mp,
                is_active=True
            )
    else:
        # Use target DC's existing meter points and copy data
        for i, target_mp in enumerate(target_meter_points):
            if i < len(template_readings):
                template_reading = template_readings[i]
                
                # Create reading for existing target meter point
                MeterReading.objects.create(
                    monthly_data=new_monthly_data,
                    meter_point=target_mp,
                    present_reading=template_reading.present_reading,
                    previous_reading=template_reading.previous_reading,
                    difference=template_reading.difference,
                    multiplying_factor=target_mp.multiplying_factor,  # Use target's multiplying factor
                    unit_kwh=template_reading.unit_kwh
                )
                
                MonthlyMeterPointStatus.objects.create(
                    monthly_data=new_monthly_data,
                    meter_point=target_mp,
                    is_active=True
                )


def _copy_energy_utilisations_simple(template_data, new_monthly_data, target_dc):
    """Copy energy utilizations from template to target DC"""
    target_categories = ConsumerCategory.objects.filter(
        Q(distribution_center=target_dc) | Q(distribution_center__isnull=True)
    ).order_by('display_order', 'name')
    
    used_categories = set()  # Track used categories to avoid duplicates
    
    for template_util in template_data.energy_utilisations.all():
        if target_categories:
            # Find an unused category
            target_category = None
            for cat in target_categories:
                if cat.pk not in used_categories:
                    target_category = cat
                    break
            
            if target_category and target_category.pk not in used_categories:
                EnergyUtilisation.objects.create(
                    monthly_data=new_monthly_data,
                    consumer_category=target_category,
                    energy_kwh=template_util.energy_kwh,
                    remarks=template_util.remarks
                )
                used_categories.add(target_category.pk)


def _copy_consumer_counts_simple(template_data, new_monthly_data, target_dc):
    """Copy consumer counts from template to target DC"""
    target_categories = ConsumerCategory.objects.filter(
        Q(distribution_center=target_dc) | Q(distribution_center__isnull=True)
    ).order_by('display_order', 'name')
    
    used_categories = set()  # Track used categories to avoid duplicates
    
    for template_count in template_data.consumer_counts.all():
        if target_categories:
            # Find an unused category
            target_category = None
            for cat in target_categories:
                if cat.pk not in used_categories:
                    target_category = cat
                    break
            
            if target_category and target_category.pk not in used_categories:
                ConsumerCount.objects.create(
                    monthly_data=new_monthly_data,
                    consumer_category=target_category,
                    count=template_count.count,
                    remarks=template_count.remarks
                )
                used_categories.add(target_category.pk)
