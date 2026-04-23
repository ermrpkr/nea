"""
NEA Loss Analysis System - Duplicate Month Data Command

Duplicates all data from a source month into a target month for a given
Distribution Center, optionally scaling numeric readings by a multiplier.

Usage:
    python manage.py duplicate_month_data \\
        --from-month=1 --to-month=2 --dc-code=PKR-DC --multiply=1.05

    python manage.py duplicate_month_data \\
        --from-month=1 --to-month=2 --dc-code=dc_pul --fiscal-year=2082/083
"""

import decimal
import sys

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from nea_loss.models import (
    DistributionCenter,
    EnergyUtilisation,
    FiscalYear,
    LossReport,
    MeterReading,
    MonthlyLossData,
    MonthlyMeterPointStatus,
    ConsumerCount,
)

MONTH_NAMES = {
    1: 'Shrawan',  2: 'Bhadra',  3: 'Ashwin',  4: 'Kartik',
    5: 'Mangsir',  6: 'Poush',   7: 'Magh',    8: 'Falgun',
    9: 'Chaitra', 10: 'Baisakh', 11: 'Jestha', 12: 'Ashadh',
}

# Meter point source types that contribute to import / export totals
IMPORT_TYPES = {'SUBSTATION', 'FEEDER_11KV', 'FEEDER_33KV', 'INTERBRANCH', 'IPP', 'ENERGY_IMPORT'}
EXPORT_TYPES = {'EXPORT_DC', 'EXPORT_IPP', 'ENERGY_EXPORT'}


class Command(BaseCommand):
    help = (
        'Duplicate all monthly data (meter readings, energy utilisation, '
        'consumer counts) from one month to another for a given DC, with an '
        'optional numeric multiplier applied to readings and energy values.'
    )

    # ------------------------------------------------------------------ #
    #  Argument definitions                                                #
    # ------------------------------------------------------------------ #

    def add_arguments(self, parser):
        parser.add_argument(
            '--from-month',
            type=int,
            required=True,
            metavar='MONTH',
            help='Source month number (1=Shrawan … 12=Ashadh)',
        )
        parser.add_argument(
            '--to-month',
            type=int,
            required=True,
            metavar='MONTH',
            help='Target month number (1=Shrawan … 12=Ashadh)',
        )
        parser.add_argument(
            '--dc-code',
            type=str,
            required=True,
            metavar='CODE',
            help='Distribution center code (e.g. PKR-DC, dc_pul)',
        )
        parser.add_argument(
            '--fiscal-year',
            type=str,
            default=None,
            metavar='YEAR_BS',
            help='Fiscal year in BS format (e.g. 2082/083). Defaults to the active fiscal year.',
        )
        parser.add_argument(
            '--multiply',
            type=float,
            default=1.0,
            metavar='FACTOR',
            help=(
                'Multiplier applied to present_reading, previous_reading '
                '(MeterReading) and energy_kwh (EnergyUtilisation). '
                'Consumer counts are never scaled. Default: 1.0 (exact copy).'
            ),
        )

    # ------------------------------------------------------------------ #
    #  Entry point                                                         #
    # ------------------------------------------------------------------ #

    def handle(self, *args, **options):
        from_month  = options['from_month']
        to_month    = options['to_month']
        dc_code     = options['dc_code']
        fy_label    = options['fiscal_year']
        multiplier  = decimal.Decimal(str(options['multiply']))

        # ── Validate month numbers ──────────────────────────────────────
        for label, value in (('--from-month', from_month), ('--to-month', to_month)):
            if not (1 <= value <= 12):
                raise CommandError(
                    f'{label} must be between 1 and 12 (got {value}).'
                )

        if from_month == to_month:
            raise CommandError(
                '--from-month and --to-month must be different.'
            )

        # ── Resolve Distribution Center ─────────────────────────────────
        dc = self._get_dc(dc_code)

        # ── Resolve Fiscal Year ─────────────────────────────────────────
        fy = self._get_fiscal_year(fy_label)

        # ── Pretty labels ───────────────────────────────────────────────
        from_name = MONTH_NAMES[from_month]
        to_name   = MONTH_NAMES[to_month]

        self.stdout.write('')
        self.stdout.write('=' * 60)
        self.stdout.write('  NEA Loss Analysis — Duplicate Month Data')
        self.stdout.write('=' * 60)
        self.stdout.write(f'  DC           : {dc.name} ({dc.code})')
        self.stdout.write(f'  Fiscal Year  : {fy.year_bs}')
        self.stdout.write(f'  Source month : {from_month} — {from_name}')
        self.stdout.write(f'  Target month : {to_month} — {to_name}')
        self.stdout.write(f'  Multiplier   : {multiplier}')
        self.stdout.write('=' * 60)
        self.stdout.write('')

        # ── Locate source LossReport ────────────────────────────────────
        try:
            src_report = LossReport.objects.get(
                distribution_center=dc,
                fiscal_year=fy,
                month=from_month,
            )
        except LossReport.DoesNotExist:
            raise CommandError(
                f'No LossReport found for {dc.code} / {fy.year_bs} / '
                f'month {from_month} ({from_name}). '
                f'Please create the source month data first.'
            )

        # ── Locate source MonthlyLossData ───────────────────────────────
        src_monthly_qs = MonthlyLossData.objects.filter(
            report=src_report, month=from_month
        )
        if not src_monthly_qs.exists():
            raise CommandError(
                f'LossReport exists for {from_name} but contains no '
                f'MonthlyLossData rows. Nothing to duplicate.'
            )
        src_monthly = src_monthly_qs.first()

        # ── Count source rows ───────────────────────────────────────────
        n_readings  = src_monthly.meter_readings.count()
        n_util      = src_monthly.energy_utilisations.count()
        n_counts    = src_monthly.consumer_counts.count()
        n_statuses  = src_monthly.meter_point_statuses.count()

        self.stdout.write(
            f'  Source data found in {from_name}:\n'
            f'    • {n_readings} MeterReading row(s)\n'
            f'    • {n_util} EnergyUtilisation row(s)\n'
            f'    • {n_counts} ConsumerCount row(s)\n'
            f'    • {n_statuses} MonthlyMeterPointStatus row(s)\n'
        )

        # ── Check for existing target LossReport ────────────────────────
        dst_report_exists = LossReport.objects.filter(
            distribution_center=dc,
            fiscal_year=fy,
            month=to_month,
        ).exists()

        if dst_report_exists:
            dst_report = LossReport.objects.get(
                distribution_center=dc,
                fiscal_year=fy,
                month=to_month,
            )
            dst_monthly_exists = MonthlyLossData.objects.filter(
                report=dst_report, month=to_month
            ).exists()

            if dst_monthly_exists:
                self.stdout.write(
                    self.style.WARNING(
                        f'  [WARNING] A LossReport and MonthlyLossData already exist '
                        f'for {to_name} (month {to_month}).\n'
                        f'  Existing data WILL BE DELETED and replaced.'
                    )
                )
                confirm = input('\n  Type "yes" to overwrite, or anything else to abort: ').strip()
                if confirm.lower() != 'yes':
                    self.stdout.write(self.style.ERROR('  Aborted — no changes made.'))
                    sys.exit(0)
            else:
                self.stdout.write(
                    f'  Target LossReport for {to_name} already exists '
                    f'(status: {dst_report.status}) but has no MonthlyLossData — '
                    f'data will be added to it.'
                )
        else:
            dst_report = None

        # ── Execute inside a single transaction ─────────────────────────
        self.stdout.write('')
        self.stdout.write('  Duplicating data …')

        with transaction.atomic():
            dst_report, dst_monthly = self._duplicate(
                src_report=src_report,
                src_monthly=src_monthly,
                dc=dc,
                fy=fy,
                to_month=to_month,
                to_name=to_name,
                multiplier=multiplier,
                dst_report=dst_report,
            )

        # ── Print summary ────────────────────────────────────────────────
        self._print_summary(dst_report, dst_monthly, to_name, multiplier)

    # ------------------------------------------------------------------ #
    #  Core duplication logic                                              #
    # ------------------------------------------------------------------ #

    def _duplicate(
        self, *, src_report, src_monthly, dc, fy,
        to_month, to_name, multiplier, dst_report,
    ):
        """
        Perform the full duplication inside the caller's transaction.
        Returns (dst_report, dst_monthly).
        """

        # 1. Create or reuse target LossReport
        if dst_report is None:
            dst_report = LossReport.objects.create(
                distribution_center=dc,
                fiscal_year=fy,
                month=to_month,
                status='DRAFT',
                created_by=src_report.created_by,
            )
            self.stdout.write(f'    [+] Created LossReport for {to_name}')
        else:
            self.stdout.write(f'    [~] Reusing existing LossReport for {to_name} (id={dst_report.pk})')

        # 2. Delete any existing MonthlyLossData for the target month
        #    (cascades to MeterReading, EnergyUtilisation, ConsumerCount,
        #     MonthlyMeterPointStatus via on_delete=CASCADE)
        deleted_count, _ = MonthlyLossData.objects.filter(
            report=dst_report, month=to_month
        ).delete()
        if deleted_count:
            self.stdout.write(
                f'    [-] Removed {deleted_count} existing MonthlyLossData '
                f'row(s) (and their children) for {to_name}'
            )

        # 3. Create target MonthlyLossData (totals will be recalculated later)
        dst_monthly = MonthlyLossData.objects.create(
            report=dst_report,
            month=to_month,
            month_name=to_name,
        )
        self.stdout.write(f'    [+] Created MonthlyLossData for {to_name}')

        # 4. Duplicate MonthlyMeterPointStatus rows
        statuses_created = 0
        for status in src_monthly.meter_point_statuses.select_related('meter_point').all():
            MonthlyMeterPointStatus.objects.create(
                monthly_data=dst_monthly,
                meter_point=status.meter_point,
                is_active=status.is_active,
            )
            statuses_created += 1
        if statuses_created:
            self.stdout.write(
                f'    [+] Duplicated {statuses_created} MonthlyMeterPointStatus row(s)'
            )

        # 5. Duplicate MeterReading rows (apply multiplier to readings)
        readings_created = 0
        for reading in src_monthly.meter_readings.select_related('meter_point').all():
            mp = reading.meter_point

            if mp.is_single_reading:
                # ENERGY_IMPORT / ENERGY_EXPORT: only present_reading matters
                new_present  = (reading.present_reading * multiplier).quantize(
                    decimal.Decimal('0.001')
                )
                new_previous = decimal.Decimal('0')
            else:
                new_present  = (reading.present_reading  * multiplier).quantize(
                    decimal.Decimal('0.001')
                )
                new_previous = (reading.previous_reading * multiplier).quantize(
                    decimal.Decimal('0.001')
                )

            # MeterReading.save() recalculates difference and unit_kwh automatically
            MeterReading.objects.create(
                monthly_data=dst_monthly,
                meter_point=mp,
                present_reading=new_present,
                previous_reading=new_previous,
                multiplying_factor=reading.multiplying_factor,
            )
            readings_created += 1

        self.stdout.write(
            f'    [+] Duplicated {readings_created} MeterReading row(s) '
            f'(multiplier={multiplier})'
        )

        # 6. Recalculate MonthlyLossData import/export/net totals from readings
        total_import = decimal.Decimal('0')
        total_export = decimal.Decimal('0')
        for mr in dst_monthly.meter_readings.select_related('meter_point').all():
            if mr.meter_point.source_type in IMPORT_TYPES:
                total_import += mr.unit_kwh
            elif mr.meter_point.source_type in EXPORT_TYPES:
                total_export += mr.unit_kwh

        dst_monthly.total_energy_import = total_import
        dst_monthly.total_energy_export = total_export
        dst_monthly.net_energy_received = total_import - total_export
        dst_monthly.save(update_fields=[
            'total_energy_import', 'total_energy_export', 'net_energy_received'
        ])

        # 7. Duplicate EnergyUtilisation rows (apply multiplier to energy_kwh)
        util_created = 0
        for eu in src_monthly.energy_utilisations.select_related('consumer_category').all():
            new_kwh = (eu.energy_kwh * multiplier).quantize(decimal.Decimal('0.01'))
            EnergyUtilisation.objects.create(
                monthly_data=dst_monthly,
                consumer_category=eu.consumer_category,
                energy_kwh=new_kwh,
                remarks=eu.remarks,
            )
            util_created += 1

        self.stdout.write(
            f'    [+] Duplicated {util_created} EnergyUtilisation row(s) '
            f'(multiplier={multiplier})'
        )

        # 8. Recalculate total_energy_utilised from the new EnergyUtilisation rows
        from django.db.models import Sum as _Sum
        total_utilised = (
            dst_monthly.energy_utilisations.aggregate(s=_Sum('energy_kwh'))['s']
            or decimal.Decimal('0')
        )
        dst_monthly.total_energy_utilised = total_utilised
        dst_monthly.loss_unit = dst_monthly.net_energy_received - total_utilised
        if dst_monthly.net_energy_received > 0:
            dst_monthly.monthly_loss_percent = (
                dst_monthly.loss_unit / dst_monthly.net_energy_received
            )
        else:
            dst_monthly.monthly_loss_percent = decimal.Decimal('0')
        dst_monthly.save(update_fields=[
            'total_energy_utilised', 'loss_unit', 'monthly_loss_percent'
        ])

        # 9. Duplicate ConsumerCount rows (counts are NOT scaled)
        counts_created = 0
        for cc in src_monthly.consumer_counts.select_related('consumer_category').all():
            ConsumerCount.objects.create(
                monthly_data=dst_monthly,
                consumer_category=cc.consumer_category,
                count=cc.count,
                remarks=cc.remarks,
            )
            counts_created += 1

        self.stdout.write(
            f'    [+] Duplicated {counts_created} ConsumerCount row(s) '
            f'(counts unchanged)'
        )

        # 10. Recalculate LossReport-level summary (totals + cumulative %)
        dst_report.calculate_summary()
        self.stdout.write(f'    [✓] Recalculated LossReport summary totals')

        return dst_report, dst_monthly

    # ------------------------------------------------------------------ #
    #  Summary output                                                      #
    # ------------------------------------------------------------------ #

    def _print_summary(self, dst_report, dst_monthly, to_name, multiplier):
        self.stdout.write('')
        self.stdout.write('=' * 60)
        self.stdout.write(self.style.SUCCESS('  DUPLICATION COMPLETE'))
        self.stdout.write('=' * 60)
        self.stdout.write(f'  Target month     : {to_name} (month {dst_monthly.month})')
        self.stdout.write(f'  LossReport id    : {dst_report.pk}  (status: {dst_report.status})')
        self.stdout.write(f'  MonthlyLossData  : id={dst_monthly.pk}')
        self.stdout.write('')
        self.stdout.write('  Energy summary (target month):')
        self.stdout.write(
            f'    Total import     : {dst_monthly.total_energy_import:>15,.2f} kWh'
        )
        self.stdout.write(
            f'    Total export     : {dst_monthly.total_energy_export:>15,.2f} kWh'
        )
        self.stdout.write(
            f'    Net received     : {dst_monthly.net_energy_received:>15,.2f} kWh'
        )
        self.stdout.write(
            f'    Total utilised   : {dst_monthly.total_energy_utilised:>15,.2f} kWh'
        )
        self.stdout.write(
            f'    Loss unit        : {dst_monthly.loss_unit:>15,.2f} kWh'
        )
        loss_pct = float(dst_monthly.monthly_loss_percent) * 100
        self.stdout.write(
            f'    Monthly loss %   : {loss_pct:>14.4f} %'
        )
        self.stdout.write('')
        self.stdout.write('  Row counts:')
        self.stdout.write(
            f'    MeterReading     : {dst_monthly.meter_readings.count()}'
        )
        self.stdout.write(
            f'    EnergyUtilisation: {dst_monthly.energy_utilisations.count()}'
        )
        self.stdout.write(
            f'    ConsumerCount    : {dst_monthly.consumer_counts.count()}'
        )
        self.stdout.write(
            f'    MeterPointStatus : {dst_monthly.meter_point_statuses.count()}'
        )
        self.stdout.write('')
        if multiplier != decimal.Decimal('1'):
            self.stdout.write(
                self.style.WARNING(
                    f'  NOTE: Readings and energy values were scaled by {multiplier}.\n'
                    f'  Consumer counts were NOT scaled.'
                )
            )
        self.stdout.write('=' * 60)
        self.stdout.write('')

    # ------------------------------------------------------------------ #
    #  Helpers                                                             #
    # ------------------------------------------------------------------ #

    def _get_dc(self, dc_code):
        """
        Look up a DistributionCenter by code (case-insensitive).
        Raises CommandError with a helpful list if not found.
        """
        try:
            return DistributionCenter.objects.get(code=dc_code)
        except DistributionCenter.DoesNotExist:
            pass

        # Try case-insensitive match
        qs = DistributionCenter.objects.filter(code__iexact=dc_code)
        if qs.count() == 1:
            return qs.first()

        available = ', '.join(
            DistributionCenter.objects.values_list('code', flat=True).order_by('code')
        )
        raise CommandError(
            f'Distribution center with code "{dc_code}" not found.\n'
            f'Available codes: {available}'
        )

    def _get_fiscal_year(self, fy_label):
        """
        Return the FiscalYear matching fy_label, or the active one if None.
        Raises CommandError if not found.
        """
        if fy_label:
            try:
                return FiscalYear.objects.get(year_bs=fy_label)
            except FiscalYear.DoesNotExist:
                available = ', '.join(
                    FiscalYear.objects.values_list('year_bs', flat=True).order_by('-year_ad_start')
                )
                raise CommandError(
                    f'Fiscal year "{fy_label}" not found.\n'
                    f'Available fiscal years: {available}'
                )

        # Default: active fiscal year
        try:
            return FiscalYear.objects.get(is_active=True)
        except FiscalYear.DoesNotExist:
            raise CommandError(
                'No active fiscal year found. '
                'Please specify one with --fiscal-year=YEAR_BS.'
            )
        except FiscalYear.MultipleObjectsReturned:
            # More than one active — pick the most recent
            fy = FiscalYear.objects.filter(is_active=True).order_by('-year_ad_start').first()
            self.stdout.write(
                self.style.WARNING(
                    f'  [WARNING] Multiple active fiscal years found; '
                    f'using the most recent: {fy.year_bs}'
                )
            )
            return fy
