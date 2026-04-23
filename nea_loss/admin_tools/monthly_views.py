from django.shortcuts import render, get_object_or_404
from django.contrib import messages
from django.db.models import Q

from ..models import (
    LossReport, MonthlyLossData, MeterPoint, MeterReading,
    MonthlyMeterPointStatus, ConsumerCategory, EnergyUtilisation,
    ConsumerCount, DCYearlyTarget, DCReportOverride
)

class AdminMonthlyDataView:
    """Override view for admin-created reports with editable readings"""
    
    @staticmethod
    def get(request, report_pk, month):
        report = get_object_or_404(LossReport, pk=report_pk)
        
        # Only handle admin-created reports
        if not getattr(report.created_by, 'is_system_admin', False):
            # Fall back to original view
            from ..views import MonthlyDataView
            return MonthlyDataView.as_view()(request, report_pk, month)
        
        # Check if report is submitted/approved - normally view-only.
        # System admin and top management can edit APPROVED reports to make corrections.
        from ..views import _can_edit_report, _can_view_report
        if _can_edit_report(request.user, report):
            can_edit = True
        elif _can_view_report(request.user, report):
            can_edit = False
        else:
            messages.error(request, 'You do not have permission to view this report.')
            from django.shortcuts import redirect
            return redirect('report_list')
            
        month_names = {
            1: 'Shrawan', 2: 'Bhadra', 3: 'Ashwin', 4: 'Kartik',
            5: 'Mangsir', 6: 'Poush', 7: 'Magh', 8: 'Falgun',
            9: 'Chaitra', 10: 'Baisakh', 11: 'Jestha', 12: 'Ashadh'
        }
        
        # Get previous month's present readings for each meter point
        previous_readings_dict = {}
        
        if month > 1:  # For months after Shrawan
            previous_month = month - 1
            
            # Check if there's an approved and active override for this month that allows skipping previous months
            approved_override = DCReportOverride.objects.filter(
                distribution_center=report.distribution_center,
                fiscal_year=report.fiscal_year,
                resume_month=month,
                status='APPROVED',
                is_active=True
            ).first()
            
            try:
                # First check if previous month report exists and is approved
                previous_loss_report = LossReport.objects.get(
                    distribution_center=report.distribution_center,
                    fiscal_year=report.fiscal_year,
                    month=previous_month
                )
                
                if previous_loss_report.status != 'APPROVED' and not approved_override:
                    messages.error(
                        request,
                        f'Previous month report ({month_names.get(previous_month, "")}) must be approved before creating {month_names.get(month, "")} report.'
                    )
                    from django.shortcuts import redirect
                    return redirect('report_create')
                    
                # Get present readings from previous month
                previous_monthly_data = previous_loss_report.monthly_data.filter(month=previous_month).first()
                if previous_monthly_data:
                    for reading in previous_monthly_data.meter_readings.all():
                        previous_readings_dict[reading.meter_point_id] = reading.present_reading
                        
            except LossReport.DoesNotExist:
                # Previous month report doesn't exist
                # Check if there's an approved override that allows this
                if approved_override:
                    # Override approved - use 0 for all previous readings
                    pass  # previous_readings_dict will remain empty, so all readings start from 0
                elif request.user.is_dc_level:  # Only show error to DC users
                    messages.error(
                        request,
                        f'Previous month report ({month_names.get(previous_month, "")}) hasn\'t been created. Please create that first.'
                    )
                    from django.shortcuts import redirect
                    return redirect('report_create')
        else:
            # For Shrawan (month 1), previous reading is 0
            if month == 1:
                previous_month_present_reading = 0
        
        # Editable flows must have a MonthlyLossData row to persist AJAX saves.
        if can_edit:
            monthly, _ = MonthlyLossData.objects.get_or_create(
                report=report,
                month=month,
                defaults={'month_name': month_names.get(month, '')},
            )
        else:
            # View-only: do not create empty rows.
            monthly = MonthlyLossData.objects.filter(report=report, month=month).first()

        existing_readings = {r.meter_point_id: r for r in monthly.meter_readings.all()} if monthly else {}

        # IDs explicitly marked inactive for this month (deleted/disabled for this month only)
        inactive_for_month = set()
        if monthly:
            inactive_for_month = set(
                MonthlyMeterPointStatus.objects.filter(
                    monthly_data=monthly,
                    is_active=False
                ).values_list('meter_point_id', flat=True)
            )

        # Determine which meter points to show based on report status
        if report.status in ['APPROVED']:
            # Approved report: show feeders that had readings, BUT still respect
            # per-month soft-deletes — if a feeder was deleted for THIS specific month,
            # hide it from this month's view (other months are unaffected).
            meter_points = MeterPoint.objects.filter(
                distribution_center=report.distribution_center,
                is_active=True
            ).exclude(
                pk__in=inactive_for_month
            )
        else:
            # Draft/submitted: show all active feeders for this DC, excluding those deleted for this month
            meter_points = MeterPoint.objects.filter(
                distribution_center=report.distribution_center,
                is_active=True
            ).exclude(
                pk__in=inactive_for_month
            )

        # Split by source type
        import_points = meter_points.filter(
            source_type__in=['SUBSTATION', 'FEEDER_11KV', 'FEEDER_33KV', 'INTERBRANCH', 'IPP', 'ENERGY_IMPORT']
        )
        export_points = meter_points.filter(source_type__in=['EXPORT_DC', 'EXPORT_IPP', 'ENERGY_EXPORT'])

        # IDs of single-reading meter points (ENERGY_IMPORT / ENERGY_EXPORT)
        single_reading_ids = set(
            meter_points.filter(source_type__in=['ENERGY_IMPORT', 'ENERGY_EXPORT']).values_list('pk', flat=True)
        )

        consumer_categories = ConsumerCategory.objects.filter(is_active=True).filter(
            Q(distribution_center__isnull=True)
            | Q(distribution_center_id=report.distribution_center_id)
        ).order_by('display_order', 'name')

        # Load DC yearly target for this fiscal year (set by provincial office)
        dc_yearly_target = None
        if report.fiscal_year:
            t = DCYearlyTarget.objects.filter(
                distribution_center=report.distribution_center,
                fiscal_year=report.fiscal_year,
            ).first()
            dc_yearly_target = float(t.target_loss_percent) if t else None

        existing_utilisations = {e.consumer_category_id: e for e in monthly.energy_utilisations.all()} if monthly else {}
        existing_counts = {c.consumer_category_id: c for c in monthly.consumer_counts.all()} if monthly else {}

        import_type_choices = [
            (k, v) for k, v in MeterPoint.SOURCE_TYPE_CHOICES
            if k in ['SUBSTATION', 'FEEDER_11KV', 'FEEDER_33KV', 'INTERBRANCH', 'IPP', 'ENERGY_IMPORT']
        ]
        export_type_choices = [
            (k, v) for k, v in MeterPoint.SOURCE_TYPE_CHOICES
            if k in ['EXPORT_DC', 'EXPORT_IPP', 'ENERGY_EXPORT']
        ]

        # For admin-created reports, we want to allow editing previous readings
        # So we identify new meter points and approved override
        new_meter_point_ids = set()
        if month > 1:
            # IDs that have a reading in any prior approved report
            prior_approved_ids = set(
                MeterReading.objects.filter(
                    meter_point__distribution_center=report.distribution_center,
                    monthly_data__report__status='APPROVED',
                    monthly_data__report__fiscal_year=report.fiscal_year,
                    monthly_data__month__lt=month,
                ).values_list('meter_point_id', flat=True).distinct()
            )
            # IDs that have a reading in a prior month of the same (possibly draft) report
            prior_same_report_ids = set(
                MeterReading.objects.filter(
                    monthly_data__report=report,
                    monthly_data__month__lt=month,
                ).values_list('meter_point_id', flat=True).distinct()
            )
            has_prior = prior_approved_ids | prior_same_report_ids
            new_meter_point_ids = set(
                mp.pk for mp in meter_points if mp.pk not in has_prior
            )

        months_nav = list(month_names.items())
        
        return render(request, 'admin_tools/monthly_data.html', {
            'report': report,
            'monthly': monthly,
            'month': month,  # Use URL parameter month instead of report.month
            'month_name': month_names.get(month, ''),
            'previous_readings_dict': previous_readings_dict,
            'months_nav': months_nav,
            'import_points': import_points,
            'export_points': export_points,
            'existing_readings': existing_readings,
            'consumer_categories': consumer_categories,
            'existing_utilisations': existing_utilisations,
            'existing_counts': existing_counts,
            'can_edit': can_edit,
            'import_type_choices': import_type_choices,
            'export_type_choices': export_type_choices,
            'new_meter_point_ids': list(new_meter_point_ids),
            'single_reading_ids': list(single_reading_ids),  # ENERGY_IMPORT / ENERGY_EXPORT
            'dc_yearly_target': dc_yearly_target,
            'approved_override': approved_override if month > 1 else None,
            'admin_created_report': True,  # Flag for admin-created reports - makes both readings editable
        })
