from django.contrib import admin, messages
from django.shortcuts import redirect
from nea_loss.models import DistributionCenter, LossReport


def change_dc_start_month(self, request, queryset):
    """Admin action to change a DC's report_start_month.

    When the start month is moved forward (e.g. from Shrawan to Poush), any
    existing reports for months that now fall *before* the new start month are
    deleted — they are no longer part of the required reporting period.  This
    makes the reset idempotent: re-running the action with the same value is
    safe.
    """
    if queryset.count() != 1:
        self.message_user(
            request,
            'Please select exactly one distribution center to change.',
            level=messages.WARNING,
        )
        return redirect('admin:nea_loss_distributioncenter_changelist')

    dc = queryset[0]
    new_start_month_raw = request.POST.get('report_start_month')

    if not new_start_month_raw:
        self.message_user(request, 'Please select a start month.', level=messages.WARNING)
        return redirect('admin:nea_loss_distributioncenter_changelist')

    try:
        new_start_month = int(new_start_month_raw)
        if new_start_month < 1 or new_start_month > 12:
            raise ValueError('Out of range')
    except ValueError:
        self.message_user(request, 'Invalid start month value.', level=messages.ERROR)
        return redirect('admin:nea_loss_distributioncenter_changelist')

    old_start_month = dc.report_start_month

    # Delete reports for months that are now before the new start month.
    # Only delete if the new start month is later than the old one (moving forward).
    deleted_count = 0
    if new_start_month > old_start_month:
        obsolete_reports = LossReport.objects.filter(
            distribution_center=dc,
            month__lt=new_start_month,
        )
        deleted_count = obsolete_reports.count()
        obsolete_reports.delete()

    dc.report_start_month = new_start_month
    dc.save()

    month_display = dc.get_report_start_month_display()
    if deleted_count:
        self.message_user(
            request,
            f'Start month for {dc.name} changed to {month_display}. '
            f'Reports for previous months are no longer required '
            f'({deleted_count} report(s) deleted).',
            level=messages.SUCCESS,
        )
    else:
        self.message_user(
            request,
            f'Start month for {dc.name} changed to {month_display}. '
            f'Reports for previous months are no longer required.',
            level=messages.SUCCESS,
        )

    return redirect('admin:nea_loss_distributioncenter_changelist')
