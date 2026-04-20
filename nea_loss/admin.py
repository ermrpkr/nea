"""
NEA Loss Analysis System — Enhanced Django Admin
Provides full system control with beautiful UI and granular permissions.
"""
import decimal
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django.db.models import Sum, Count, Avg
from django.urls import reverse
from django.utils import timezone
from .models import (
    NEAUser, Province, ProvincialOffice, DistributionCenter,
    FiscalYear, LossReport, MonthlyLossData, MeterPoint, MeterReading,
    ConsumerCategory, EnergyUtilisation, ConsumerCount,
    AuditLog, Notification, ProvincialReport, DCMonthlyTarget, DCYearlyTarget,
    MonthlyMeterPointStatus,
)

# ── Site branding ──────────────────────────────────────────────────────────────
admin.site.site_header  = mark_safe(
    '''<span style="display:flex;align-items:center;gap:12px;">
      <span style="font-size:22px;">⚡</span>
      <span><span style="font-weight:800;">NEA</span> Loss Analysis — Admin Panel</span>
    </span>'''
)
admin.site.site_title   = "NEA Admin"
admin.site.index_title  = "System Administration Dashboard"


# ── Helper: coloured badge ─────────────────────────────────────────────────────
def badge(text, colour):
    colours = {
        "green":  ("#D5F5E3", "#1E8449"),
        "red":    ("#FADBD8", "#C0392B"),
        "blue":   ("#EBF5FB", "#1B4F72"),
        "yellow": ("#FEF9E7", "#B7770D"),
        "grey":   ("#F0F4F8", "#718096"),
    }
    bg, fg = colours.get(colour, colours["grey"])
    return format_html(
        '<span style="background:{};color:{};padding:3px 10px;border-radius:12px;'
        'font-size:11px;font-weight:700;">{}</span>',
        bg, fg, text
    )


# ══════════════════════════════════════════════════════════════════════════════
#  USER
# ══════════════════════════════════════════════════════════════════════════════
@admin.register(NEAUser)
class NEAUserAdmin(UserAdmin):
    list_display  = ['username', 'full_name', 'role_badge', 'provincial_office',
                     'distribution_center', 'active_badge', 'date_joined']
    list_filter   = ['role', 'is_active', 'provincial_office']
    search_fields = ['username', 'full_name', 'email', 'employee_id']
    ordering      = ['role', 'full_name']
    list_per_page = 30

    fieldsets = (
        ('Login Credentials', {'fields': ('username', 'password')}),
        ('Personal Information', {'fields': ('full_name', 'email', 'phone', 'designation', 'employee_id')}),
        ('Role & Organisation', {'fields': ('role', 'provincial_office', 'distribution_center'),
          'description': ('<div style="background:#EBF5FB;padding:10px 14px;border-radius:8px;'
                           'font-size:12px;margin-bottom:8px;color:#1B4F72;">'
                           '<strong>Role guidance:</strong> DC_MANAGER / DC_STAFF → assign a Distribution Center. '
                           'PROVINCIAL_MANAGER → assign a Provincial Office. '
                           'MD / DMD / DIRECTOR → no DC/Province needed.</div>')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Dates', {'fields': ('date_joined', 'last_login')}),
    )
    add_fieldsets = (
        (None, {'classes': ('wide',), 'fields': (
            'username', 'email', 'full_name', 'role',
            'provincial_office', 'distribution_center', 'password1', 'password2'
        )}),
    )

    @admin.display(description='Role')
    def role_badge(self, obj):
        colours = {
            'SYS_ADMIN': 'red', 'MD': 'blue', 'DMD': 'blue', 'DIRECTOR': 'blue',
            'PROVINCIAL_MANAGER': 'yellow', 'DC_MANAGER': 'green', 'DC_STAFF': 'grey',
        }
        return badge(obj.get_role_display(), colours.get(obj.role, 'grey'))

    @admin.display(description='Active', boolean=False)
    def active_badge(self, obj):
        return badge('Active', 'green') if obj.is_active else badge('Inactive', 'red')


# ══════════════════════════════════════════════════════════════════════════════
#  ORGANISATION
# ══════════════════════════════════════════════════════════════════════════════
@admin.register(Province)
class ProvinceAdmin(admin.ModelAdmin):
    list_display  = ['name', 'code', 'office_count', 'created_at']
    search_fields = ['name', 'code']

    @admin.display(description='Provincial Offices')
    def office_count(self, obj):
        return obj.offices.count()


@admin.register(ProvincialOffice)
class ProvincialOfficeAdmin(admin.ModelAdmin):
    list_display  = ['name', 'code', 'province', 'dc_count', 'contact', 'created_at']
    list_filter   = ['province']
    search_fields = ['name', 'code']

    @admin.display(description='DCs')
    def dc_count(self, obj):
        return obj.distribution_centers.count()


@admin.register(DistributionCenter)
class DistributionCenterAdmin(admin.ModelAdmin):
    list_display  = ['name', 'code', 'provincial_office', 'start_month_badge',
                     'active_status', 'feeder_count', 'contact', 'created_at']
    list_filter   = ['is_active', 'report_start_month',
                     'provincial_office', 'provincial_office__province']
    list_editable = []
    search_fields = ['name', 'code']
    list_per_page = 30

    fieldsets = (
        ('Basic Information', {'fields': ('name', 'code', 'provincial_office', 'address', 'contact')}),
        ('Reporting Configuration', {
            'fields': ('report_start_month', 'is_active'),
            'description': (
                '<div style="background:#FEF9E7;padding:12px 16px;border-radius:8px;'
                'font-size:12px;border-left:4px solid #F39C12;margin-bottom:12px;">' 
                '<strong>⚙️ Admin Configuration:</strong><br>'
                '<b>Report Start Month</b>: Set the first month this DC must submit a report for. '
                'For example, a DC established in Mangsir should start from month 5 (Mangsir). '
                'The system will not require or show report slots for earlier months.<br><br>'
                '<b>Active/Inactive</b>: Inactive DCs are hidden from all report lists and '
                'provincial dashboards. Use this when a DC is decommissioned or merged.'
                '</div>'
            ),
        }),
    )

    @admin.display(description='Start Month')
    def start_month_badge(self, obj):
        month_names = {
            1:'Shrawan',2:'Bhadra',3:'Ashwin',4:'Kartik',
            5:'Mangsir',6:'Poush',7:'Magh',8:'Falgun',
            9:'Chaitra',10:'Baisakh',11:'Jestha',12:'Ashadh'
        }
        colour = 'green' if obj.report_start_month == 1 else 'yellow'
        return badge(month_names.get(obj.report_start_month, '?'), colour)

    @admin.display(description='Status')
    def active_status(self, obj):
        return badge('Active', 'green') if obj.is_active else badge('Inactive', 'red')

    @admin.display(description='Feeders')
    def feeder_count(self, obj):
        active = obj.meter_points.filter(is_active=True).count()
        total  = obj.meter_points.count()
        return format_html('{} / {}', active, total)


# ══════════════════════════════════════════════════════════════════════════════
#  FISCAL YEAR
# ══════════════════════════════════════════════════════════════════════════════
@admin.register(FiscalYear)
class FiscalYearAdmin(admin.ModelAdmin):
    list_display  = ['year_bs', 'year_ad_start', 'year_ad_end',
                     'target_display', 'active_badge', 'report_count']
    list_editable = []
    ordering      = ['-year_ad_start']

    fieldsets = (
        ('Fiscal Year Details', {'fields': ('year_bs', 'year_ad_start', 'year_ad_end')}),
        ('Targets & Status', {
            'fields': ('loss_target_percent', 'is_active'),
            'description': (
                '<div style="background:#EBF5FB;padding:10px 14px;border-radius:8px;'
                'font-size:12px;margin-bottom:8px;color:#1B4F72;">'
                '<strong>Note:</strong> Only one fiscal year should be Active at a time. '
                'The Loss Target applies to NEA overall — provincial offices set '
                'per-DC monthly targets separately.</div>'
            ),
        }),
    )

    @admin.display(description='NEA Target')
    def target_display(self, obj):
        # Handle SafeString properly
        try:
            value = float(obj.loss_target_percent)
        except (ValueError, TypeError):
            value = 0.0
        return f"{value}%"

    @admin.display(description='Active')
    def active_badge(self, obj):
        return badge('Active FY', 'green') if obj.is_active else badge('Inactive', 'grey')

    @admin.display(description='Reports')
    def report_count(self, obj):
        return obj.loss_reports.count()


# ══════════════════════════════════════════════════════════════════════════════
#  LOSS REPORTS
# ══════════════════════════════════════════════════════════════════════════════
class MonthlyLossDataInline(admin.TabularInline):
    model         = MonthlyLossData
    extra         = 0
    can_delete    = False
    readonly_fields = ['month', 'month_name', 'net_energy_received', 'total_energy_utilised',
                        'loss_unit', 'monthly_loss_pct_display', 'cumulative_loss_pct_display']
    fields        = readonly_fields
    verbose_name  = "Monthly Summary"
    verbose_name_plural = "Monthly Summaries"
    ordering      = ['month']

    def has_add_permission(self, request, obj=None):
        return False

    @admin.display(description='Monthly Loss %')
    def monthly_loss_pct_display(self, obj):
        try:
            pct = float(obj.monthly_loss_percent) * 100
        except (ValueError, TypeError):
            pct = 0.0
        col = '#C0392B' if pct > 5 else '#1E8449'
        return format_html('<strong style="color:{}">{:.4f}%</strong>', col, pct)

    @admin.display(description='Cumul. Loss %')
    def cumulative_loss_pct_display(self, obj):
        try:
            pct = float(obj.cumulative_loss_percent) * 100
        except (ValueError, TypeError):
            pct = 0.0
        col = '#C0392B' if pct > 5 else '#1E8449'
        return format_html('<strong style="color:{}">{:.4f}%</strong>', col, pct)


@admin.register(LossReport)
class LossReportAdmin(admin.ModelAdmin):
    list_display  = ['distribution_center', 'fiscal_year', 'month', 'status']  # Temporarily simplified
    list_filter   = ['status', 'fiscal_year', 'month',
                     'distribution_center__provincial_office',
                     'distribution_center__provincial_office__province']
    search_fields = ['distribution_center__name', 'distribution_center__code']
    readonly_fields = ['total_received_kwh', 'total_utilised_kwh', 'total_loss_kwh',
                        'cumulative_loss_percent', 'created_at', 'updated_at',
                        'submitted_by', 'reviewed_by', 'approved_by',
                        'submission_date', 'review_date', 'approval_date']
    inlines       = [MonthlyLossDataInline]
    actions       = ['action_approve', 'action_reject', 'action_revert_to_draft',
                     'action_recalculate']
    list_per_page = 25
    date_hierarchy = 'created_at'

    fieldsets = (
        ('Report Identity', {'fields': (
            'distribution_center', 'fiscal_year', 'month', 'status'
        )}),
        ('Summary Figures (Auto-calculated)', {'fields': (
            'total_received_kwh', 'total_utilised_kwh',
            'total_loss_kwh', 'cumulative_loss_percent'
        ), 'classes': ('collapse',)}),
        ('Audit Trail', {'fields': (
            'created_by', 'submitted_by', 'reviewed_by', 'approved_by',
            'submission_date', 'review_date', 'approval_date',
            'created_at', 'updated_at'
        ), 'classes': ('collapse',)}),
        ('Remarks', {'fields': ('remarks',)}),
    )

    @admin.display(description='Distribution Center', ordering='distribution_center__name')
    def dc_link(self, obj):
        url = reverse('admin:nea_loss_distributioncenter_change', args=[obj.distribution_center_id])
        return format_html('<a href="{}" style="font-weight:600;color:#1B4F72;">{}</a>',
                           url, obj.distribution_center.name)

    @admin.display(description='Province')
    def provincial_office(self, obj):
        return obj.distribution_center.provincial_office.name

    @admin.display(description='Month')
    def month_display(self, obj):
        return obj.get_month_display()

    @admin.display(description='Status')
    def status_badge(self, obj):
        mapping = {
            'DRAFT': 'grey', 'SUBMITTED': 'blue',
            'PROVINCIAL_REVIEWED': 'yellow', 'APPROVED': 'green', 'REJECTED': 'red'
        }
        return badge(obj.get_status_display(), mapping.get(obj.status, 'grey'))

    @admin.display(description='Loss %', ordering='cumulative_loss_percent')
    def loss_pct_display(self, obj):
        try:
            pct = float(obj.cumulative_loss_percent) * 100
        except (ValueError, TypeError):
            pct = 0.0
        col = '#C0392B' if pct > 5 else '#F39C12' if pct > 3.35 else '#1E8449'
        return format_html('<strong style="color:{}">{:.4f}%</strong>', col, pct)

    @admin.display(description='Received (kWh)')
    def received_kwh(self, obj):
        try:
            value = float(obj.total_received_kwh)
        except (ValueError, TypeError):
            value = 0.0
        return f"{value:,.2f}"

    @admin.action(description='✅ Approve selected reports')
    def action_approve(self, request, queryset):
        count = queryset.update(status='APPROVED', approval_date=timezone.now(), approved_by=request.user)
        self.message_user(request, f'{count} report(s) approved.')

    @admin.action(description='❌ Reject selected reports')
    def action_reject(self, request, queryset):
        count = queryset.update(status='REJECTED')
        self.message_user(request, f'{count} report(s) rejected.')

    @admin.action(description='↩ Revert selected to Draft')
    def action_revert_to_draft(self, request, queryset):
        count = queryset.update(status='DRAFT')
        self.message_user(request, f'{count} report(s) reverted to Draft.')

    @admin.action(description='🔄 Recalculate summaries')
    def action_recalculate(self, request, queryset):
        count = 0
        for report in queryset:
            report.calculate_summary()
            count += 1
        self.message_user(request, f'Recalculated {count} report(s).')


# ══════════════════════════════════════════════════════════════════════════════
#  METER POINTS
# ══════════════════════════════════════════════════════════════════════════════
@admin.register(MeterPoint)
class MeterPointAdmin(admin.ModelAdmin):
    list_display  = ['name', 'code', 'distribution_center', 'source_type_badge',
                     'voltage_level', 'multiplying_factor', 'active_badge']
    list_filter   = ['source_type', 'is_active',
                     'distribution_center__provincial_office']
    list_editable = ['multiplying_factor']
    search_fields = ['name', 'code', 'distribution_center__name']
    list_per_page = 40

    fieldsets = (
        ('Feeder Identity', {'fields': ('distribution_center', 'name', 'code', 'source_type')}),
        ('Technical Details', {'fields': ('voltage_level', 'multiplying_factor', 'is_active')}),
    )

    @admin.display(description='Type')
    def source_type_badge(self, obj):
        colour_map = {
            'SUBSTATION': 'blue', 'FEEDER_11KV': 'blue', 'FEEDER_33KV': 'blue',
            'INTERBRANCH': 'yellow', 'IPP': 'green',
            'EXPORT_DC': 'red', 'EXPORT_IPP': 'red',
            'ENERGY_IMPORT': 'blue', 'ENERGY_EXPORT': 'red',
        }
        return badge(obj.get_source_type_display(), colour_map.get(obj.source_type, 'grey'))

    @admin.display(description='Active')
    def active_badge(self, obj):
        return badge('Active', 'green') if obj.is_active else badge('Inactive', 'red')


# ══════════════════════════════════════════════════════════════════════════════
#  DC YEARLY TARGETS
# ══════════════════════════════════════════════════════════════════════════════
@admin.register(DCYearlyTarget)
class DCYearlyTargetAdmin(admin.ModelAdmin):
    list_display = ['distribution_center', 'fiscal_year', 'target_loss_percent', 'set_by', 'created_at']
    list_filter = ['fiscal_year', 'distribution_center__provincial_office']
    search_fields = ['distribution_center__name', 'fiscal_year__year_bs']
    readonly_fields = ['created_at', 'updated_at', 'set_by']
    
    fieldsets = (
        ('Target Information', {
            'fields': ('distribution_center', 'fiscal_year', 'target_loss_percent')
        }),
        ('Metadata', {
            'fields': ('set_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def save_model(self, request, obj, form, change):
        if not change:
            obj.set_by = request.user
        super().save_model(request, obj, form, change)


#  DC MONTHLY TARGETS (DEPRECATED)
# ══════════════════════════════════════════════════════════════════════════════
@admin.register(DCMonthlyTarget)
class DCMonthlyTargetAdmin(admin.ModelAdmin):
    list_display  = ['distribution_center', 'fiscal_year', 'month_display',
                     'target_badge', 'set_by', 'updated_at']
    list_filter   = ['fiscal_year', 'month',
                     'distribution_center__provincial_office']
    search_fields = ['distribution_center__name']
    list_per_page = 40
    list_editable = []

    @admin.display(description='Month')
    def month_display(self, obj):
        return obj.get_month_display()

    @admin.display(description='Target %')
    def target_badge(self, obj):
        try:
            pct = float(obj.target_loss_percent)
        except (ValueError, TypeError):
            pct = 0.0
        col = 'green' if pct <= 3.35 else 'yellow' if pct <= 5 else 'red'
        return badge(f'{pct:.3f}%', col)


# ══════════════════════════════════════════════════════════════════════════════
#  CONSUMER CATEGORY
# ══════════════════════════════════════════════════════════════════════════════
@admin.register(ConsumerCategory)
class ConsumerCategoryAdmin(admin.ModelAdmin):
    list_display  = ['name', 'code', 'distribution_center', 'display_order', 'active_badge']
    list_filter   = ['is_active', 'distribution_center']
    list_editable = ['display_order']
    search_fields = ['name', 'code']

    @admin.display(description='Active')
    def active_badge(self, obj):
        return badge('Active', 'green') if obj.is_active else badge('Inactive', 'red')


# ══════════════════════════════════════════════════════════════════════════════
#  PROVINCIAL REPORT
# ══════════════════════════════════════════════════════════════════════════════
@admin.register(ProvincialReport)
class ProvincialReportAdmin(admin.ModelAdmin):
    list_display  = ['provincial_office', 'fiscal_year', 'month_display',
                     'status_badge', 'created_by', 'created_at']
    list_filter   = ['status', 'fiscal_year', 'provincial_office']
    readonly_fields = ['created_at', 'updated_at', 'created_by']
    actions       = ['action_approve']

    @admin.display(description='Month')
    def month_display(self, obj):
        return obj.get_month_display()

    @admin.display(description='Status')
    def status_badge(self, obj):
        return badge(obj.get_status_display(),
                     {'DRAFT': 'grey', 'SUBMITTED': 'blue', 'APPROVED': 'green'}.get(obj.status, 'grey'))

    @admin.action(description='✅ Approve selected provincial reports')
    def action_approve(self, request, queryset):
        count = queryset.update(status='APPROVED')
        self.message_user(request, f'{count} provincial report(s) approved.')


# ══════════════════════════════════════════════════════════════════════════════
#  AUDIT LOG
# ══════════════════════════════════════════════════════════════════════════════
@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display  = ['timestamp', 'user', 'action_badge', 'model_name', 'object_id',
                     'short_description', 'ip_address']
    list_filter   = ['action', 'model_name']
    search_fields = ['user__username', 'description']
    readonly_fields = ['timestamp', 'user', 'action', 'model_name',
                        'object_id', 'description', 'ip_address']
    date_hierarchy = 'timestamp'
    list_per_page = 50

    @admin.display(description='Action')
    def action_badge(self, obj):
        colour_map = {'CREATE': 'green', 'UPDATE': 'blue', 'DELETE': 'red', 'VIEW': 'grey'}
        return badge(obj.action, colour_map.get(obj.action, 'grey'))

    @admin.display(description='Description')
    def short_description(self, obj):
        text = obj.description[:80] + '…' if len(obj.description) > 80 else obj.description
        return format_html('<span style="color:#4A5568;font-size:12px;">{}</span>', text)

    def has_add_permission(self, request):    return False
    def has_change_permission(self, request, obj=None): return False
    def has_delete_permission(self, request, obj=None): return False


# ══════════════════════════════════════════════════════════════════════════════
#  NOTIFICATION
# ══════════════════════════════════════════════════════════════════════════════
@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display  = ['title', 'recipient', 'type_badge', 'read_badge', 'created_at']
    list_filter   = ['notification_type', 'is_read']
    search_fields = ['title', 'recipient__username']
    actions       = ['mark_read', 'mark_unread']

    @admin.display(description='Type')
    def type_badge(self, obj):
        col = {'REPORT_SUBMITTED': 'blue', 'REPORT_APPROVED': 'green',
               'REPORT_REJECTED': 'red', 'LOSS_EXCEEDED': 'red', 'REMINDER': 'yellow'}
        return badge(obj.get_notification_type_display(), col.get(obj.notification_type, 'grey'))

    @admin.display(description='Read')
    def read_badge(self, obj):
        return badge('Read', 'grey') if obj.is_read else badge('Unread', 'blue')

    @admin.action(description='Mark selected as Read')
    def mark_read(self, request, queryset):
        queryset.update(is_read=True)

    @admin.action(description='Mark selected as Unread')
    def mark_unread(self, request, queryset):
        queryset.update(is_read=False)