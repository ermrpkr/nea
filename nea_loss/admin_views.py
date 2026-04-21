from django.contrib import admin, messages
from django.shortcuts import redirect
from nea_loss.models import DistributionCenter

def change_dc_start_month(self, request, queryset):
    """Admin view to change DC start month"""
    if queryset.count() == 1:
        dc = queryset[0]
        # Get the new start month from form
        new_start_month = request.POST.get('report_start_month')
        if new_start_month:
            try:
                dc.report_start_month = int(new_start_month)
                dc.save()
                self.message_user(
                    request,
                    f'Changed {dc.name} start month to {dc.get_report_start_month_display()} ({dc.report_start_month})'
                )
            except ValueError:
                self.message_user(request, 'Invalid start month value.')
        else:
            self.message_user(request, 'Please select a start month.')
    else:
        self.message_user(request, 'Please select one distribution center to change.')
    return redirect('admin:nea_loss_distributioncenter_changelist')
