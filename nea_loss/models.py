"""
NEA Loss Analysis System - Database Models
Hierarchy: SYS_ADMIN (system) | MD/DMD/Director (view) | Provincial Office | Distribution Center
"""
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator
import decimal


# ─────────────────────────── ORGANIZATION HIERARCHY ───────────────────────────

class Province(models.Model):
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=20, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['name']


class ProvincialOffice(models.Model):
    province = models.ForeignKey(Province, on_delete=models.CASCADE, related_name='offices')
    name = models.CharField(max_length=150)
    code = models.CharField(max_length=30, unique=True)
    address = models.TextField(blank=True)
    contact = models.CharField(max_length=20, blank=True)
    # Password for approving DCS detail edits
    edit_approval_password = models.CharField(max_length=100, blank=True, help_text='Password for approving DCS detail edit requests')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['name']


class DistributionCenter(models.Model):
    """DCS - primary report generating unit"""
    MONTH_CHOICES = [
        (1,'Shrawan'),(2,'Bhadra'),(3,'Ashwin'),(4,'Kartik'),
        (5,'Mangsir'),(6,'Poush'),(7,'Magh'),(8,'Falgun'),
        (9,'Chaitra'),(10,'Baisakh'),(11,'Jestha'),(12,'Ashadh'),
    ]
    provincial_office = models.ForeignKey(ProvincialOffice, on_delete=models.CASCADE, related_name='distribution_centers')
    name = models.CharField(max_length=150)
    code = models.CharField(max_length=30, unique=True)
    address = models.TextField(blank=True)
    contact = models.CharField(max_length=20, blank=True)
    # Admin can set which month this DC starts reporting from (default Shrawan=1)
    report_start_month = models.PositiveSmallIntegerField(
        choices=MONTH_CHOICES, default=1,
        help_text='First month this DC is required to submit a report for the fiscal year. '
                  'Admin sets this — e.g. a DC added mid-year starts from Mangsir (5).'
    )
    is_active = models.BooleanField(default=True, help_text='Inactive DCs are hidden from reports and lists.')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['name']


# ─────────────────────────── USER MANAGEMENT ───────────────────────────

class NEAUserManager(BaseUserManager):
    def create_user(self, username, email, password=None, **extra_fields):
        if not email:
            raise ValueError('Email is required')
        email = self.normalize_email(email)
        user = self.model(username=username, email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('role', 'SYS_ADMIN')
        return self.create_user(username, email, password, **extra_fields)


class NEAUser(AbstractBaseUser, PermissionsMixin):
    ROLE_CHOICES = [
        ('SYS_ADMIN', 'System Administrator'),
        ('MD', 'Managing Director'),
        ('DMD', 'Deputy Managing Director'),
        ('DIRECTOR', 'Director'),
        ('PROVINCIAL_MANAGER', 'Provincial Manager'),
        ('DC_MANAGER', 'DC Manager'),
        ('DC_STAFF', 'DC Staff'),
    ]

    username = models.CharField(max_length=50, unique=True)
    email = models.EmailField(unique=True)
    full_name = models.CharField(max_length=150)
    role = models.CharField(max_length=30, choices=ROLE_CHOICES, default='DC_STAFF')
    employee_id = models.CharField(max_length=30, blank=True)
    phone = models.CharField(max_length=20, blank=True)
    designation = models.CharField(max_length=100, blank=True)

    provincial_office = models.ForeignKey(ProvincialOffice, null=True, blank=True, on_delete=models.SET_NULL)
    distribution_center = models.ForeignKey(DistributionCenter, null=True, blank=True, on_delete=models.SET_NULL)

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(default=timezone.now)
    last_login_ip = models.GenericIPAddressField(null=True, blank=True)

    objects = NEAUserManager()

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['email', 'full_name']

    def __str__(self):
        return f"{self.full_name} ({self.get_role_display()})"

    @property
    def is_system_admin(self):
        """System Administrator - full control, different from MD/DMD"""
        return self.role == 'SYS_ADMIN' or self.is_superuser

    @property
    def is_top_management(self):
        """MD, DMD, Director - view/approve only, cannot create reports"""
        return self.role in ['MD', 'DMD', 'DIRECTOR']

    @property
    def is_provincial(self):
        return self.role == 'PROVINCIAL_MANAGER'

    @property
    def is_dc_level(self):
        return self.role in ['DC_MANAGER', 'DC_STAFF']

    class Meta:
        verbose_name = 'NEA User'
        verbose_name_plural = 'NEA Users'


# ─────────────────────────── FISCAL YEAR ───────────────────────────

class FiscalYear(models.Model):
    year_bs = models.CharField(max_length=20, unique=True)
    year_ad_start = models.IntegerField()
    year_ad_end = models.IntegerField()
    loss_target_percent = models.DecimalField(max_digits=5, decimal_places=2)
    is_active = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"FY {self.year_bs}"

    class Meta:
        ordering = ['-year_ad_start']


# ─────────────────────────── LOSS REPORT ───────────────────────────

class LossReport(models.Model):
    STATUS_CHOICES = [
        ('DRAFT', 'Draft'),
        ('SUBMITTED', 'Submitted'),
        ('PROVINCIAL_REVIEWED', 'Provincial Reviewed'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
    ]

    distribution_center = models.ForeignKey(DistributionCenter, on_delete=models.CASCADE, related_name='loss_reports')
    fiscal_year = models.ForeignKey(FiscalYear, on_delete=models.CASCADE, related_name='loss_reports')
    month = models.PositiveSmallIntegerField(choices=[
        (1, 'Shrawan'), (2, 'Bhadra'), (3, 'Ashwin'), (4, 'Kartik'),
        (5, 'Mangsir'), (6, 'Poush'), (7, 'Magh'), (8, 'Falgun'),
        (9, 'Chaitra'), (10, 'Baisakh'), (11, 'Jestha'), (12, 'Ashadh')
    ], default=1)
    status = models.CharField(max_length=25, choices=STATUS_CHOICES, default='DRAFT')

    total_received_kwh = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    total_utilised_kwh = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    total_loss_kwh = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    cumulative_loss_percent = models.DecimalField(max_digits=7, decimal_places=4, default=0)

    created_by = models.ForeignKey(NEAUser, on_delete=models.SET_NULL, null=True, related_name='created_reports')
    submitted_by = models.ForeignKey(NEAUser, on_delete=models.SET_NULL, null=True, blank=True, related_name='submitted_reports')
    reviewed_by = models.ForeignKey(NEAUser, on_delete=models.SET_NULL, null=True, blank=True, related_name='reviewed_reports')
    approved_by = models.ForeignKey(NEAUser, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_reports')

    submission_date = models.DateTimeField(null=True, blank=True)
    review_date = models.DateTimeField(null=True, blank=True)
    approval_date = models.DateTimeField(null=True, blank=True)
    remarks = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.distribution_center.name} - {self.fiscal_year.year_bs} - {self.get_month_display()}"

    def get_month_display(self):
        month_names = {
            1: 'Shrawan', 2: 'Bhadra', 3: 'Ashwin', 4: 'Kartik',
            5: 'Mangsir', 6: 'Poush', 7: 'Magh', 8: 'Falgun',
            9: 'Chaitra', 10: 'Baisakh', 11: 'Jestha', 12: 'Ashadh'
        }
        return month_names.get(self.month, '')

    def calculate_summary(self):
        months = self.monthly_data.all()
        self.total_received_kwh = sum(m.net_energy_received for m in months)
        self.total_utilised_kwh = sum(m.total_energy_utilised for m in months)
        self.total_loss_kwh = self.total_received_kwh - self.total_utilised_kwh
        if self.total_received_kwh > 0:
            self.cumulative_loss_percent = (self.total_loss_kwh / self.total_received_kwh)
        else:
            self.cumulative_loss_percent = 0

        cumulative_received = decimal.Decimal('0')
        cumulative_loss = decimal.Decimal('0')
        for m in self.monthly_data.order_by('month'):
            cumulative_received += m.net_energy_received
            cumulative_loss += m.loss_unit
            if m.month == 1:
                # Shrawan (first month of fiscal year): cumulative loss = monthly loss %
                if m.net_energy_received > 0:
                    m.cumulative_loss_percent = m.loss_unit / m.net_energy_received
                else:
                    m.cumulative_loss_percent = 0
            else:
                # Bhadra onwards: cumulative = (sum of all loss units so far) /
                #                              (sum of all received units so far) * 100
                if cumulative_received > 0:
                    m.cumulative_loss_percent = cumulative_loss / cumulative_received
                else:
                    m.cumulative_loss_percent = 0
            m.save(update_fields=['cumulative_loss_percent'])

        self.save()

    class Meta:
        unique_together = ['distribution_center', 'fiscal_year', 'month']
        ordering = ['-fiscal_year__year_ad_start', 'month', 'distribution_center__name']


# ─────────────────────────── MONTHLY DATA ───────────────────────────

NEPALI_MONTH_CHOICES = [
    (1, 'Shrawan'), (2, 'Bhadra'), (3, 'Ashwin'), (4, 'Kartik'),
    (5, 'Mangsir'), (6, 'Poush'), (7, 'Magh'), (8, 'Falgun'),
    (9, 'Chaitra'), (10, 'Baisakh'), (11, 'Jestha'), (12, 'Ashadh'),
]


class MonthlyLossData(models.Model):
    report = models.ForeignKey(LossReport, on_delete=models.CASCADE, related_name='monthly_data')
    month = models.IntegerField(choices=NEPALI_MONTH_CHOICES)
    month_name = models.CharField(max_length=20)

    total_energy_import = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    total_energy_export = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    net_energy_received = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    total_energy_utilised = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    loss_unit = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    monthly_loss_percent = models.DecimalField(max_digits=7, decimal_places=4, default=0)
    cumulative_loss_percent = models.DecimalField(max_digits=7, decimal_places=4, default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def calculate(self):
        self.net_energy_received = self.total_energy_import - self.total_energy_export
        self.loss_unit = self.net_energy_received - self.total_energy_utilised
        if self.net_energy_received > 0:
            self.monthly_loss_percent = self.loss_unit / self.net_energy_received
        self.save()

    def __str__(self):
        return f"{self.report} - {self.month_name}"

    class Meta:
        unique_together = ['report', 'month']
        ordering = ['month']


# ─────────────────────────── METER POINTS ───────────────────────────

class MeterPoint(models.Model):
    SOURCE_TYPE_CHOICES = [
        ('SUBSTATION', 'Substation'),
        ('FEEDER_11KV', '11 kV Feeder'),
        ('FEEDER_33KV', '33 kV Feeder'),
        ('INTERBRANCH', 'Interbranch Import'),
        ('IPP', 'Independent Power Producer'),
        ('ENERGY_IMPORT', 'Energy Import'),       # Single present-reading only; no auto-fill next month
        ('EXPORT_DC', 'Export to Other DC'),
        ('EXPORT_IPP', 'Export to IPP'),
        ('ENERGY_EXPORT', 'Energy Export'),        # Single present-reading only; no auto-fill next month
    ]

    # Types that use only a present-reading (no previous reading, no carry-forward)
    SINGLE_READING_TYPES = {'ENERGY_IMPORT', 'ENERGY_EXPORT'}

    distribution_center = models.ForeignKey(DistributionCenter, on_delete=models.CASCADE, related_name='meter_points')
    name = models.CharField(max_length=200)
    code = models.CharField(max_length=50, blank=True)
    source_type = models.CharField(max_length=20, choices=SOURCE_TYPE_CHOICES)
    voltage_level = models.CharField(max_length=20, blank=True)
    multiplying_factor = models.DecimalField(max_digits=10, decimal_places=3, default=1)
    is_active = models.BooleanField(default=True)
    # New field: Substation/Grid/Powerhouse connection source
    connection_source = models.CharField(
        max_length=200, blank=True,
        help_text='Substation/Grid/Powerhouse from which this feeder is connected'
    )
    # For cross-DC energy transfer validation
    linked_distribution_center = models.ForeignKey(
        DistributionCenter, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='linked_meter_points',
        help_text='For ENERGY_IMPORT: source DC. For ENERGY_EXPORT/EXPORT_DC: destination DC. Used for cross-DC validation.'
    )
    linked_distribution_center_name = models.CharField(
        max_length=200, blank=True,
        help_text='Free-text name of linked DC for cross-DC validation. Used when exact DC match is not found.'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def is_single_reading(self):
        """Energy Import / Energy Export types need only a present reading (no previous, no carry-forward)."""
        return self.source_type in self.SINGLE_READING_TYPES

    def __str__(self):
        return f"{self.name} ({self.get_source_type_display()})"

    class Meta:
        ordering = ['source_type', 'name']


class MeterReading(models.Model):
    monthly_data = models.ForeignKey(MonthlyLossData, on_delete=models.CASCADE, related_name='meter_readings')
    meter_point = models.ForeignKey(MeterPoint, on_delete=models.CASCADE, related_name='readings')
    present_reading = models.DecimalField(max_digits=15, decimal_places=3)
    previous_reading = models.DecimalField(max_digits=15, decimal_places=3, default=0)
    difference = models.DecimalField(max_digits=15, decimal_places=3, default=0)
    multiplying_factor = models.DecimalField(max_digits=10, decimal_places=3, default=1)
    unit_kwh = models.DecimalField(max_digits=15, decimal_places=2, default=0)

    def save(self, *args, **kwargs):
        # For ENERGY_IMPORT / ENERGY_EXPORT: unit = present_reading * MF (no subtraction)
        if self.meter_point.is_single_reading:
            self.previous_reading = decimal.Decimal('0')
            self.difference = self.present_reading
        else:
            self.difference = self.present_reading - self.previous_reading
        self.unit_kwh = self.difference * self.multiplying_factor
        super().save(*args, **kwargs)

    class Meta:
        unique_together = ['monthly_data', 'meter_point']


class MonthlyMeterPointStatus(models.Model):
    """Track which meter points are active/inactive for specific months"""
    monthly_data = models.ForeignKey(MonthlyLossData, on_delete=models.CASCADE, related_name='meter_point_statuses')
    meter_point = models.ForeignKey(MeterPoint, on_delete=models.CASCADE, related_name='monthly_statuses')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['monthly_data', 'meter_point']


# ─────────────────────────── CONSUMER CATEGORIES ───────────────────────────

class ConsumerCategory(models.Model):
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=40, unique=True)
    distribution_center = models.ForeignKey(
        DistributionCenter, on_delete=models.CASCADE, null=True, blank=True,
        related_name='consumer_categories'
    )
    display_order = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['display_order', 'name']


class EnergyUtilisation(models.Model):
    monthly_data = models.ForeignKey(MonthlyLossData, on_delete=models.CASCADE, related_name='energy_utilisations')
    consumer_category = models.ForeignKey(ConsumerCategory, on_delete=models.CASCADE)
    energy_kwh = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    remarks = models.CharField(max_length=200, blank=True)

    class Meta:
        unique_together = ['monthly_data', 'consumer_category']


class ConsumerCount(models.Model):
    monthly_data = models.ForeignKey(MonthlyLossData, on_delete=models.CASCADE, related_name='consumer_counts')
    consumer_category = models.ForeignKey(ConsumerCategory, on_delete=models.CASCADE)
    count = models.IntegerField(default=0)
    remarks = models.CharField(max_length=200, blank=True)

    class Meta:
        unique_together = ['monthly_data', 'consumer_category']


# ─────────────────────────── PROVINCIAL REPORT ───────────────────────────

class ProvincialReport(models.Model):
    """Monthly consolidated report generated by Provincial Office from DC reports"""
    STATUS_CHOICES = [
        ('DRAFT', 'Draft'),
        ('SUBMITTED_TO_DMD', 'Submitted to DMD'),
        ('DMD_APPROVED', 'DMD Approved'),
        ('DMD_REJECTED', 'DMD Rejected'),
    ]
    provincial_office = models.ForeignKey(ProvincialOffice, on_delete=models.CASCADE, related_name='provincial_reports')
    fiscal_year = models.ForeignKey(FiscalYear, on_delete=models.CASCADE, related_name='provincial_reports')
    month = models.PositiveSmallIntegerField(choices=[
        (1, 'Shrawan'), (2, 'Bhadra'), (3, 'Ashwin'), (4, 'Kartik'),
        (5, 'Mangsir'), (6, 'Poush'), (7, 'Magh'), (8, 'Falgun'),
        (9, 'Chaitra'), (10, 'Baisakh'), (11, 'Jestha'), (12, 'Ashadh')
    ], default=1)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='DRAFT')
    created_by = models.ForeignKey(NEAUser, on_delete=models.SET_NULL, null=True)
    
    # DMD approval fields
    submitted_to_dmd_by = models.ForeignKey(NEAUser, on_delete=models.SET_NULL, null=True, blank=True, related_name='submitted_provincial_reports')
    submitted_to_dmd_at = models.DateTimeField(null=True, blank=True)
    dmd_reviewed_by = models.ForeignKey(NEAUser, on_delete=models.SET_NULL, null=True, blank=True, related_name='dmd_reviewed_provincial_reports')
    dmd_reviewed_at = models.DateTimeField(null=True, blank=True)
    dmd_remarks = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    remarks = models.TextField(blank=True)

    def get_month_display(self):
        month_names = {
            1: 'Shrawan', 2: 'Bhadra', 3: 'Ashwin', 4: 'Kartik',
            5: 'Mangsir', 6: 'Poush', 7: 'Magh', 8: 'Falgun',
            9: 'Chaitra', 10: 'Baisakh', 11: 'Jestha', 12: 'Ashadh'
        }
        return month_names.get(self.month, '')

    def __str__(self):
        return f"{self.provincial_office.name} - {self.fiscal_year.year_bs} - {self.get_month_display()}"

    class Meta:
        unique_together = ['provincial_office', 'fiscal_year', 'month']
        ordering = ['-fiscal_year__year_ad_start', 'month']


# ─────────────────────────── AUDIT LOG ───────────────────────────

# ─────────────────────────── DC YEARLY TARGETS ───────────────────────────

class DCYearlyTarget(models.Model):
    """Provincial office sets a yearly loss % target for each DC."""
    distribution_center = models.ForeignKey(
        'DistributionCenter', on_delete=models.CASCADE, related_name='yearly_targets'
    )
    fiscal_year = models.ForeignKey(
        'FiscalYear', on_delete=models.CASCADE, related_name='dc_yearly_targets'
    )
    target_loss_percent = models.DecimalField(max_digits=6, decimal_places=3)
    set_by = models.ForeignKey(
        'NEAUser', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='dc_yearly_targets_set'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['distribution_center', 'fiscal_year']
        ordering = ['fiscal_year', 'distribution_center']

    def __str__(self):
        return (
            f"{self.distribution_center.name} — "
            f"{self.fiscal_year.year_bs}: "
            f"{self.target_loss_percent}%"
        )


# ─────────────────────────── DC MONTHLY TARGETS (DEPRECATED) ───────────────────────────

class DCMonthlyTarget(models.Model):
    """Provincial office sets a monthly loss % target for each DC."""
    MONTH_CHOICES = [
        (1, 'Shrawan'), (2, 'Bhadra'), (3, 'Ashwin'), (4, 'Kartik'),
        (5, 'Mangsir'), (6, 'Poush'), (7, 'Magh'), (8, 'Falgun'),
        (9, 'Chaitra'), (10, 'Baisakh'), (11, 'Jestha'), (12, 'Ashadh'),
    ]

    distribution_center = models.ForeignKey(
        'DistributionCenter', on_delete=models.CASCADE, related_name='monthly_targets'
    )
    fiscal_year = models.ForeignKey(
        'FiscalYear', on_delete=models.CASCADE, related_name='dc_monthly_targets'
    )
    month = models.PositiveSmallIntegerField(choices=MONTH_CHOICES)
    target_loss_percent = models.DecimalField(max_digits=6, decimal_places=3)
    set_by = models.ForeignKey(
        'NEAUser', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='dc_targets_set'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['distribution_center', 'fiscal_year', 'month']
        ordering = ['fiscal_year', 'distribution_center', 'month']

    def __str__(self):
        return (
            f"{self.distribution_center.name} — "
            f"{self.get_month_display()} {self.fiscal_year.year_bs}: "
            f"{self.target_loss_percent}%"
        )


class AuditLog(models.Model):
    user = models.ForeignKey(NEAUser, on_delete=models.SET_NULL, null=True)
    action = models.CharField(max_length=50)
    model_name = models.CharField(max_length=50)
    object_id = models.IntegerField(null=True)
    description = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.user} - {self.action} - {self.timestamp}"


# ─────────────────────────── NOTIFICATION ───────────────────────────

class Message(models.Model):
    """User-to-user internal messaging for all NEA system users."""
    sender    = models.ForeignKey('NEAUser', on_delete=models.CASCADE, related_name='sent_messages')
    recipient = models.ForeignKey('NEAUser', on_delete=models.CASCADE, related_name='received_messages')
    subject   = models.CharField(max_length=200)
    body      = models.TextField()
    is_read   = models.BooleanField(default=False)
    parent    = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True,
                                   related_name='replies')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"From {self.sender} to {self.recipient}: {self.subject}"


class DCReportOverride(models.Model):
    """Admin-approved override to allow DC to skip missing months due to technical issues"""
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
    ]
    
    distribution_center = models.ForeignKey(DistributionCenter, on_delete=models.CASCADE, related_name='report_overrides')
    fiscal_year = models.ForeignKey(FiscalYear, on_delete=models.CASCADE, related_name='report_overrides')
    requested_by = models.ForeignKey(NEAUser, on_delete=models.CASCADE, related_name='requested_overrides')
    approved_by = models.ForeignKey(NEAUser, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_overrides')
    
    # Month from which DC wants to resume reporting (e.g., Kartik=4)
    resume_month = models.PositiveSmallIntegerField(choices=NEPALI_MONTH_CHOICES)
    
    # Range of months to skip (e.g., 3-6 means skip Ashwin, Kartik, Mangsir, Poush)
    skip_from_month = models.PositiveSmallIntegerField(choices=NEPALI_MONTH_CHOICES, null=True, blank=True)
    skip_to_month = models.PositiveSmallIntegerField(choices=NEPALI_MONTH_CHOICES, null=True, blank=True)
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    is_active = models.BooleanField(default=True, help_text='Whether this override is currently active')
    reason = models.TextField(help_text='Reason for override request (e.g., technical problems, system downtime)')
    admin_notes = models.TextField(blank=True, help_text='Admin notes on approval/rejection')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    approved_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.distribution_center.name} - {self.fiscal_year.year_bs} - Resume {self.get_resume_month_display()} ({self.status})"

    def get_resume_month_display(self):
        month_names = {
            1: 'Shrawan', 2: 'Bhadra', 3: 'Ashwin', 4: 'Kartik',
            5: 'Mangsir', 6: 'Poush', 7: 'Magh', 8: 'Falgun',
            9: 'Chaitra', 10: 'Baisakh', 11: 'Jestha', 12: 'Ashadh'
        }
        return month_names.get(self.resume_month, '')

    def approve(self, approved_by, admin_notes=''):
        """Approve the override request"""
        self.status = 'APPROVED'
        self.approved_by = approved_by
        self.admin_notes = admin_notes
        self.approved_at = timezone.now()
        self.save()

    def reject(self, approved_by, admin_notes=''):
        """Reject the override request"""
        self.status = 'REJECTED'
        self.approved_by = approved_by
        self.admin_notes = admin_notes
        self.approved_at = timezone.now()
        self.save()

    def activate(self):
        """Activate the override"""
        self.is_active = True
        self.save()

    def deactivate(self):
        """Deactivate the override"""
        self.is_active = False
        self.save()

    class Meta:
        unique_together = ['distribution_center', 'fiscal_year', 'resume_month']
        ordering = ['-created_at']


class Notification(models.Model):
    TYPE_CHOICES = [
        ('REPORT_SUBMITTED', 'Report Submitted'),
        ('REPORT_APPROVED', 'Report Approved'),
        ('REPORT_REJECTED', 'Report Rejected'),
        ('LOSS_EXCEEDED', 'Loss Target Exceeded'),
        ('REMINDER', 'Submission Reminder'),
        ('OVERRIDE_REQUESTED', 'Override Requested'),
        ('OVERRIDE_APPROVED', 'Override Approved'),
        ('OVERRIDE_REJECTED', 'Override Rejected'),
        ('FEEDER_REQUESTED', 'Feeder Change Requested'),
        ('FEEDER_APPROVED', 'Feeder Change Approved'),
        ('FEEDER_REJECTED', 'Feeder Change Rejected'),
    ]

    recipient = models.ForeignKey(NEAUser, on_delete=models.CASCADE, related_name='notifications')
    notification_type = models.CharField(max_length=30, choices=TYPE_CHOICES)
    title = models.CharField(max_length=200)
    message = models.TextField()
    related_report = models.ForeignKey(LossReport, on_delete=models.CASCADE, null=True, blank=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']


# ─────────────────────────── FEEDER REQUEST ───────────────────────────

class FeederRequest(models.Model):
    """DC users can request feeder additions/deletions. Provincial users approve/reject."""
    REQUEST_TYPE_CHOICES = [
        ('ADD', 'Add Feeder'),
        ('DELETE', 'Delete Feeder'),
        ('MODIFY', 'Modify Feeder'),
    ]
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
    ]

    distribution_center = models.ForeignKey(DistributionCenter, on_delete=models.CASCADE, related_name='feeder_requests')
    requested_by = models.ForeignKey(NEAUser, on_delete=models.CASCADE, related_name='feeder_requests')
    request_type = models.CharField(max_length=20, choices=REQUEST_TYPE_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    
    # Feeder details
    feeder_name = models.CharField(max_length=200, help_text='Name of the feeder')
    connection_source = models.CharField(max_length=200, blank=True, help_text='Substation/Grid/Powerhouse from which this feeder is connected')
    source_type = models.CharField(max_length=30, choices=MeterPoint.SOURCE_TYPE_CHOICES, blank=True)
    voltage_level = models.CharField(max_length=20, blank=True)
    multiplying_factor = models.DecimalField(max_digits=10, decimal_places=3, default=1, blank=True, null=True)
    
    # For DELETE requests, reference existing meter point
    meter_point = models.ForeignKey(MeterPoint, on_delete=models.SET_NULL, null=True, blank=True, 
                                    related_name='feeder_requests', help_text='Existing feeder to delete')
    
    # Reason and approval
    reason = models.TextField(help_text='Reason for this request')
    provincial_notes = models.TextField(blank=True, help_text='Notes from provincial office')
    approved_by = models.ForeignKey(NEAUser, on_delete=models.SET_NULL, null=True, blank=True, 
                                    related_name='approved_feeder_requests')
    approved_at = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def approve(self, approved_by, notes=''):
        """Approve the feeder request and make the actual change"""
        self.status = 'APPROVED'
        self.approved_by = approved_by
        self.provincial_notes = notes
        self.approved_at = timezone.now()
        
        if self.request_type == 'ADD':
            # Create the new meter point
            MeterPoint.objects.create(
                distribution_center=self.distribution_center,
                name=self.feeder_name,
                code='',
                source_type=self.source_type,
                voltage_level=self.voltage_level,
                multiplying_factor=self.multiplying_factor or 1,
                connection_source=self.connection_source or '',
                is_active=True,
            )
        elif self.request_type == 'DELETE' and self.meter_point:
            # Soft delete: mark as inactive
            self.meter_point.is_active = False
            self.meter_point.save()
        
        self.save()

    def reject(self, approved_by, notes=''):
        """Reject the feeder request"""
        self.status = 'REJECTED'
        self.approved_by = approved_by
        self.provincial_notes = notes
        self.approved_at = timezone.now()
        self.save()

    def __str__(self):
        return f"{self.get_request_type_display()} - {self.feeder_name} ({self.status})"

    class Meta:
        ordering = ['-created_at']


# ─────────────────────────── ENERGY IMPORT DETAIL ───────────────────────────

class EnergyImportDetail(models.Model):
    """Detailed tracking of energy imports with feeder-to-feeder linking"""
    monthly_data = models.ForeignKey(MonthlyLossData, on_delete=models.CASCADE, related_name='energy_import_details')
    meter_point = models.ForeignKey(MeterPoint, on_delete=models.CASCADE, related_name='import_details')
    
    # Source feeder details
    source_feeder_name = models.CharField(max_length=200, help_text='Name of the source feeder')
    source_connection = models.CharField(max_length=200, blank=True, help_text='Substation/Grid/Powerhouse of source')
    source_type = models.CharField(max_length=20, choices=MeterPoint.SOURCE_TYPE_CHOICES)
    source_voltage = models.CharField(max_length=20, blank=True)
    source_mf = models.DecimalField(max_digits=10, decimal_places=3, default=1)
    
    # Import details
    present_reading = models.DecimalField(max_digits=15, decimal_places=3)
    previous_reading = models.DecimalField(max_digits=15, decimal_places=3, default=0)
    difference = models.DecimalField(max_digits=15, decimal_places=3, default=0)
    unit_kwh = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    
    # Linking to export (for automatic matching)
    linked_export_detail = models.ForeignKey(
        'EnergyExportDetail', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='linked_import_details',
        help_text='Automatically linked export detail when this import matches an export'
    )
    
    remarks = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        # Calculate difference and units
        if self.meter_point.is_single_reading:
            self.previous_reading = decimal.Decimal('0')
            self.difference = self.present_reading
        else:
            self.difference = self.present_reading - self.previous_reading
        self.unit_kwh = self.difference * self.source_mf
        super().save(*args, **kwargs)
        
        # Auto-link to matching export detail
        self.auto_link_export()

    def auto_link_export(self):
        """Automatically link this import to a matching export detail"""
        from django.db.models import Q
        
        # Find export details in the same monthly data
        # Match by feeder name and unit amount (allowing small tolerance)
        exports = EnergyExportDetail.objects.filter(
            monthly_data=self.monthly_data
        ).exclude(
            pk__in=[self.linked_export_detail.pk] if self.linked_export_detail else []
        )
        
        # Try to find exact match by destination feeder name matching source feeder name
        # and unit amount matching (within 0.1% tolerance)
        tolerance = self.unit_kwh * decimal.Decimal('0.001') if self.unit_kwh > 0 else decimal.Decimal('0.01')
        
        for export in exports:
            if (export.destination_feeder_name == self.source_feeder_name and
                abs(export.unit_kwh - self.unit_kwh) <= tolerance):
                # Found a match - link them
                self.linked_export_detail = export
                export.linked_import_detail = self
                export.save(update_fields=['linked_import_detail'])
                self.save(update_fields=['linked_export_detail'])
                break

    def __str__(self):
        return f"{self.source_feeder_name} - {self.unit_kwh} kWh"

    class Meta:
        unique_together = ['monthly_data', 'meter_point']
        ordering = ['source_feeder_name']


# ─────────────────────────── ENERGY EXPORT DETAIL ───────────────────────────

class EnergyExportDetail(models.Model):
    """Detailed tracking of energy exports with feeder-to-feeder linking"""
    monthly_data = models.ForeignKey(MonthlyLossData, on_delete=models.CASCADE, related_name='energy_export_details')
    meter_point = models.ForeignKey(MeterPoint, on_delete=models.CASCADE, related_name='export_details')
    
    # Destination feeder details
    destination_feeder_name = models.CharField(max_length=200, help_text='Name of the destination feeder')
    destination_connection = models.CharField(max_length=200, blank=True, help_text='Substation/Grid/Powerhouse of destination')
    destination_type = models.CharField(max_length=20, choices=MeterPoint.SOURCE_TYPE_CHOICES)
    destination_voltage = models.CharField(max_length=20, blank=True)
    destination_mf = models.DecimalField(max_digits=10, decimal_places=3, default=1)
    
    # Export details
    present_reading = models.DecimalField(max_digits=15, decimal_places=3)
    previous_reading = models.DecimalField(max_digits=15, decimal_places=3, default=0)
    difference = models.DecimalField(max_digits=15, decimal_places=3, default=0)
    unit_kwh = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    
    # Linking to import (for automatic matching)
    linked_import_detail = models.ForeignKey(
        EnergyImportDetail, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='linked_export_details',
        help_text='Automatically linked import detail when this export matches an import'
    )
    
    remarks = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        # Calculate difference and units
        if self.meter_point.is_single_reading:
            self.previous_reading = decimal.Decimal('0')
            self.difference = self.present_reading
        else:
            self.difference = self.present_reading - self.previous_reading
        self.unit_kwh = self.difference * self.destination_mf
        super().save(*args, **kwargs)
        
        # Auto-link to matching import detail
        self.auto_link_import()

    def auto_link_import(self):
        """Automatically link this export to a matching import detail"""
        from django.db.models import Q
        
        # Find import details in the same monthly data
        # Match by feeder name and unit amount (allowing small tolerance)
        imports = EnergyImportDetail.objects.filter(
            monthly_data=self.monthly_data
        ).exclude(
            pk__in=[self.linked_import_detail.pk] if self.linked_import_detail else []
        )
        
        # Try to find exact match by source feeder name matching destination feeder name
        # and unit amount matching (within 0.1% tolerance)
        tolerance = self.unit_kwh * decimal.Decimal('0.001') if self.unit_kwh > 0 else decimal.Decimal('0.01')
        
        for import_detail in imports:
            if (import_detail.source_feeder_name == self.destination_feeder_name and
                abs(import_detail.unit_kwh - self.unit_kwh) <= tolerance):
                # Found a match - link them
                self.linked_import_detail = import_detail
                import_detail.linked_export_detail = self
                import_detail.save(update_fields=['linked_export_detail'])
                self.save(update_fields=['linked_import_detail'])
                break

    def __str__(self):
        return f"{self.destination_feeder_name} - {self.unit_kwh} kWh"

    class Meta:
        unique_together = ['monthly_data', 'meter_point']
        ordering = ['destination_feeder_name']


# ─────────────────────────── DCS DETAIL ───────────────────────────

class DCSDetail(models.Model):
    """Detailed information about a Distribution Center"""
    distribution_center = models.OneToOneField(DistributionCenter, on_delete=models.CASCADE, related_name='dcs_detail')
    
    # Basic information
    image = models.ImageField(upload_to='dcs_images/', blank=True, null=True, help_text='Picture of the DCS')
    introduction = models.TextField(blank=True, help_text='Introduction/description of the DCS')
    
    # Additional information
    established_date = models.DateField(blank=True, null=True, help_text='Date when DCS was established')
    coverage_area = models.TextField(blank=True, help_text='Geographical area covered by this DCS')
    total_capacity = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True, help_text='Total capacity in kVA')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.distribution_center.name} - Detail"
    
    class Meta:
        verbose_name = 'DCS Detail'
        verbose_name_plural = 'DCS Details'


class DCSOfficial(models.Model):
    """Officials working at a Distribution Center"""
    dcs_detail = models.ForeignKey(DCSDetail, on_delete=models.CASCADE, related_name='officials')
    
    name = models.CharField(max_length=150)
    designation = models.CharField(max_length=100, help_text='e.g., Chief, Deputy Chief, Engineer')
    phone = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    joining_date = models.DateField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.name} - {self.designation}"
    
    class Meta:
        verbose_name = 'DCS Official'
        verbose_name_plural = 'DCS Officials'
        ordering = ['designation', 'name']


class DCSFeeder(models.Model):
    """Feeder details for a Distribution Center"""
    dcs_detail = models.ForeignKey(DCSDetail, on_delete=models.CASCADE, related_name='feeders')
    
    name = models.CharField(max_length=200, help_text='Name of the feeder')
    feeder_code = models.CharField(max_length=50, blank=True)
    voltage_level = models.CharField(max_length=20, blank=True, help_text='e.g., 11 kV, 33 kV')
    length_km = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True, help_text='Length in kilometers')
    connected_load = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True, help_text='Connected load in kVA')
    transformer_count = models.IntegerField(blank=True, null=True, help_text='Number of transformers')
    is_active = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.name} ({self.voltage_level})"
    
    class Meta:
        verbose_name = 'DCS Feeder'
        verbose_name_plural = 'DCS Feeders'
        ordering = ['name']


class DCSConsumerType(models.Model):
    """Consumer types and counts for a Distribution Center"""
    dcs_detail = models.ForeignKey(DCSDetail, on_delete=models.CASCADE, related_name='consumer_types')
    
    category_name = models.CharField(max_length=100, help_text='e.g., Domestic, Commercial, Industrial')
    consumer_count = models.IntegerField(default=0, help_text='Number of consumers in this category')
    connected_load = models.DecimalField(max_digits=15, decimal_places=2, default=0, help_text='Total connected load in kVA')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.category_name} - {self.consumer_count}"
    
    class Meta:
        verbose_name = 'DCS Consumer Type'
        verbose_name_plural = 'DCS Consumer Types'
        ordering = ['category_name']


class DCSDetailEditRequest(models.Model):
    """Requests to edit DCS details - requires province approval"""
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
    ]
    
    dcs_detail = models.ForeignKey(DCSDetail, on_delete=models.CASCADE, related_name='edit_requests')
    requested_by = models.ForeignKey(NEAUser, on_delete=models.CASCADE, related_name='dcs_detail_edit_requests')
    
    # Store the proposed changes as JSON
    proposed_changes = models.JSONField(help_text='JSON object containing proposed changes')
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    
    # Approval fields
    approved_by = models.ForeignKey(NEAUser, on_delete=models.SET_NULL, null=True, blank=True, 
                                    related_name='approved_dcs_detail_edits')
    approved_at = models.DateTimeField(null=True, blank=True)
    rejection_reason = models.TextField(blank=True, help_text='Reason for rejection if rejected')
    pending_image = models.ImageField(
        upload_to='dcs_images/pending/', blank=True, null=True,
        help_text='Image uploaded with edit request; applied on approval',
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def approve(self, approved_by):
        """Approve the edit request and apply changes"""
        self.status = 'APPROVED'
        self.approved_by = approved_by
        self.approved_at = timezone.now()
        
        # Apply the proposed changes
        changes = self.proposed_changes or {}
        dcs_detail = self.dcs_detail
        
        # Update DCS Detail fields
        if 'introduction' in changes:
            dcs_detail.introduction = changes['introduction'] or ''
        if 'established_date' in changes:
            from datetime import datetime
            val = changes['established_date']
            if val:
                if isinstance(val, str):
                    try:
                        dcs_detail.established_date = datetime.strptime(val[:10], '%Y-%m-%d').date()
                    except ValueError:
                        pass
                else:
                    dcs_detail.established_date = val
            else:
                dcs_detail.established_date = None
        if 'coverage_area' in changes:
            dcs_detail.coverage_area = changes['coverage_area'] or ''
        if 'total_capacity' in changes:
            cap = changes['total_capacity']
            dcs_detail.total_capacity = decimal.Decimal(str(cap)) if cap not in (None, '') else None
        
        if self.pending_image:
            import os
            from django.core.files import File
            img_name = os.path.basename(self.pending_image.name)
            with self.pending_image.open('rb') as img_file:
                dcs_detail.image.save(img_name, File(img_file), save=False)
        
        dcs_detail.save()
        
        # Handle officials updates
        if 'officials' in changes:
            # Delete existing officials
            dcs_detail.officials.all().delete()
            # Create new officials
            for official_data in changes['officials']:
                joining = official_data.get('joining_date')
                if joining and isinstance(joining, str) and joining.strip():
                    from datetime import datetime
                    try:
                        joining = datetime.strptime(joining[:10], '%Y-%m-%d').date()
                    except ValueError:
                        joining = None
                elif not joining:
                    joining = None
                DCSOfficial.objects.create(
                    dcs_detail=dcs_detail,
                    name=official_data.get('name', ''),
                    designation=official_data.get('designation', ''),
                    phone=official_data.get('phone', ''),
                    email=official_data.get('email', ''),
                    joining_date=joining,
                    is_active=official_data.get('is_active', True)
                )
        
        # Handle feeders updates
        if 'feeders' in changes:
            # Delete existing feeders
            dcs_detail.feeders.all().delete()
            # Create new feeders
            for feeder_data in changes['feeders']:
                def _dec(val):
                    if val in (None, ''):
                        return None
                    return decimal.Decimal(str(val))
                DCSFeeder.objects.create(
                    dcs_detail=dcs_detail,
                    name=feeder_data.get('name', ''),
                    feeder_code=feeder_data.get('feeder_code', ''),
                    voltage_level=feeder_data.get('voltage_level', ''),
                    length_km=_dec(feeder_data.get('length_km')),
                    connected_load=_dec(feeder_data.get('connected_load')),
                    transformer_count=int(feeder_data['transformer_count']) if feeder_data.get('transformer_count') not in (None, '') else None,
                    is_active=feeder_data.get('is_active', True)
                )
        
        # Handle consumer types updates
        if 'consumer_types' in changes:
            # Delete existing consumer types
            dcs_detail.consumer_types.all().delete()
            # Create new consumer types
            for consumer_data in changes['consumer_types']:
                load = consumer_data.get('connected_load', 0)
                DCSConsumerType.objects.create(
                    dcs_detail=dcs_detail,
                    category_name=consumer_data.get('category_name', ''),
                    consumer_count=int(consumer_data.get('consumer_count', 0) or 0),
                    connected_load=decimal.Decimal(str(load)) if load not in (None, '') else 0
                )
        
        self.save()
    
    def reject(self, approved_by, reason=''):
        """Reject the edit request"""
        self.status = 'REJECTED'
        self.approved_by = approved_by
        self.approved_at = timezone.now()
        self.rejection_reason = reason
        self.save()
    
    def __str__(self):
        return f"{self.dcs_detail.distribution_center.name} - Edit Request ({self.status})"
    
    class Meta:
        verbose_name = 'DCS Detail Edit Request'
        verbose_name_plural = 'DCS Detail Edit Requests'
        ordering = ['-created_at']


# ─────────────────────────── HISTORY TRACKING ───────────────────────────

class DCHistoryEntry(models.Model):
    """Historical entry for DCS data tracking"""
    distribution_center = models.ForeignKey(DistributionCenter, on_delete=models.CASCADE, related_name='history_entries')
    fiscal_year = models.ForeignKey(FiscalYear, on_delete=models.CASCADE, related_name='history_entries')
    month = models.PositiveSmallIntegerField(choices=NEPALI_MONTH_CHOICES)
    
    # Leadership information
    dc_manager = models.ForeignKey(NEAUser, on_delete=models.SET_NULL, null=True, blank=True, 
                                   related_name='dc_history_entries', help_text='DC Manager at the time')
    provincial_manager = models.ForeignKey(NEAUser, on_delete=models.SET_NULL, null=True, blank=True,
                                          related_name='provincial_history_entries', help_text='Provincial Manager at the time')
    
    # Data snapshot
    total_received_kwh = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    total_utilised_kwh = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    total_loss_kwh = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    loss_percent = models.DecimalField(max_digits=7, decimal_places=4, default=0)
    
    # Consumer counts snapshot
    total_consumers = models.IntegerField(default=0)
    consumer_breakdown = models.JSONField(blank=True, null=True, help_text='JSON object with consumer category breakdown')
    
    # Timestamps
    report_created_at = models.DateTimeField(help_text='When the report was created')
    report_submitted_at = models.DateTimeField(null=True, blank=True, help_text='When the report was submitted')
    report_approved_at = models.DateTimeField(null=True, blank=True, help_text='When the report was approved')
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    def get_month_display(self):
        month_names = {
            1: 'Shrawan', 2: 'Bhadra', 3: 'Ashwin', 4: 'Kartik',
            5: 'Mangsir', 6: 'Poush', 7: 'Magh', 8: 'Falgun',
            9: 'Chaitra', 10: 'Baisakh', 11: 'Jestha', 12: 'Ashadh'
        }
        return month_names.get(self.month, '')
    
    def __str__(self):
        return f"{self.distribution_center.name} - {self.fiscal_year.year_bs} - {self.get_month_display()}"
    
    class Meta:
        verbose_name = 'DC History Entry'
        verbose_name_plural = 'DC History Entries'
        unique_together = ['distribution_center', 'fiscal_year', 'month']
        ordering = ['-fiscal_year__year_ad_start', '-month', 'distribution_center__name']


# ─────────────────────────── FEEDER FILE UPLOADS ───────────────────────────

class FeederFile(models.Model):
    """Files uploaded by DCS from feeders (PDF, Word, Excel, etc.)"""
    FILE_TYPE_CHOICES = [
        ('PDF', 'PDF'),
        ('WORD', 'Word Document'),
        ('EXCEL', 'Excel Spreadsheet'),
        ('IMAGE', 'Image'),
        ('OTHER', 'Other'),
    ]
    
    report = models.ForeignKey(LossReport, on_delete=models.CASCADE, related_name='feeder_files')
    feeder_name = models.CharField(max_length=200, help_text='Name of the feeder')
    file = models.FileField(upload_to='feeder_files/%Y/%m/', help_text='Upload feeder file (PDF, Word, Excel)')
    file_type = models.CharField(max_length=10, choices=FILE_TYPE_CHOICES, default='OTHER')
    description = models.TextField(blank=True, help_text='Description of the file content')
    
    uploaded_by = models.ForeignKey(NEAUser, on_delete=models.SET_NULL, null=True, related_name='uploaded_feeder_files')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.feeder_name} - {self.report.get_month_display()} ({self.file_type})"
    
    def get_filename(self):
        return self.file.name.split('/')[-1] if self.file else ''
    
    class Meta:
        ordering = ['-uploaded_at']
        verbose_name = 'Feeder File'
        verbose_name_plural = 'Feeder Files'