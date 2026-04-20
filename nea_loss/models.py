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
        ('SUBMITTED', 'Submitted'),
        ('APPROVED', 'Approved'),
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


class Notification(models.Model):
    TYPE_CHOICES = [
        ('REPORT_SUBMITTED', 'Report Submitted'),
        ('REPORT_APPROVED', 'Report Approved'),
        ('REPORT_REJECTED', 'Report Rejected'),
        ('LOSS_EXCEEDED', 'Loss Target Exceeded'),
        ('REMINDER', 'Submission Reminder'),
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