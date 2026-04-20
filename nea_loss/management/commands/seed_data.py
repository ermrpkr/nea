"""
NEA Loss Analysis System - Seed Data
Creates all demo users with correct roles:
  sysadmin / nea@admin123  → System Administrator (full control, not MD)
  md_user  / nea@2024      → Managing Director    (view only)
  dmd_user / nea@2024      → Deputy Managing Director (view only)
  prov_kvdd / nea@2024     → Provincial Manager KVDD
  dc_ktm   / nea@2024      → DC Staff Kathmandu
  dc_nuw   / nea@2024      → DC Staff Nuwakot
  dc_lpr   / nea@2024      → DC Staff Lalitpur
  dc_pkr   / nea@2024      → DC Staff Pokhara
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from nea_loss.models import (
    Province, ProvincialOffice, DistributionCenter, NEAUser,
    FiscalYear, ConsumerCategory, MeterPoint
)


class Command(BaseCommand):
    help = 'Seed initial data for NEA Loss Analysis System'

    def handle(self, *args, **kwargs):
        self.stdout.write('Seeding NEA Loss Analysis System data...')

        # ---- FISCAL YEARS ----
        fy_data = [
            {'year_bs': '2080/081', 'year_ad_start': 2023, 'year_ad_end': 2024, 'loss_target_percent': 3.50, 'is_active': False},
            {'year_bs': '2081/082', 'year_ad_start': 2024, 'year_ad_end': 2025, 'loss_target_percent': 3.40, 'is_active': False},
            {'year_bs': '2082/083', 'year_ad_start': 2025, 'year_ad_end': 2026, 'loss_target_percent': 3.35, 'is_active': True},
        ]
        for d in fy_data:
            FiscalYear.objects.get_or_create(year_bs=d['year_bs'], defaults=d)
        self.stdout.write(self.style.SUCCESS('  [OK] Fiscal Years created'))

        # ---- PROVINCES ----
        provinces_data = [
            ('Koshi Province', 'P1'),
            ('Madhesh Province', 'P2'),
            ('Bagmati Province', 'P3'),
            ('Gandaki Province', 'P4'),
            ('Lumbini Province', 'P5'),
            ('Karnali Province', 'P6'),
            ('Sudurpashchim Province', 'P7'),
        ]
        provinces = {}
        for name, code in provinces_data:
            p, _ = Province.objects.get_or_create(code=code, defaults={'name': name})
            provinces[code] = p
        self.stdout.write(self.style.SUCCESS('  [OK] Provinces created'))

        # ---- PROVINCIAL OFFICES ----
        po_data = [
            ('P3', 'Kathmandu Valley Distribution Division (KVDD)', 'KVDD'),
            ('P3', 'Bagmati Distribution Division', 'BDD'),
            ('P1', 'Koshi Distribution Division', 'KDD'),
            ('P4', 'Gandaki Distribution Division', 'GDD'),
            ('P5', 'Lumbini Distribution Division', 'LDD'),
        ]
        pos = {}
        for pcode, name, code in po_data:
            po, _ = ProvincialOffice.objects.get_or_create(
                code=code,
                defaults={'province': provinces[pcode], 'name': name}
            )
            pos[code] = po
        self.stdout.write(self.style.SUCCESS('  [OK] Provincial Offices created'))

        # ---- DISTRIBUTION CENTERS ----
        dc_data = [
            ('KVDD', 'Kathmandu Distribution Center', 'KTM-DC'),
            ('KVDD', 'Lalitpur Distribution Center', 'LPR-DC'),
            ('KVDD', 'Bhaktapur Distribution Center', 'BKT-DC'),
            ('KVDD', 'Nuwakot Distribution Center', 'NUW-DC'),
            ('BDD', 'Hetauda Distribution Center', 'HTD-DC'),
            ('KDD', 'Biratnagar Distribution Center', 'BRT-DC'),
            ('GDD', 'Pokhara Distribution Center', 'PKR-DC'),
            ('LDD', 'Butwal Distribution Center', 'BTW-DC'),
        ]
        dcs = {}
        for po_code, name, code in dc_data:
            dc, _ = DistributionCenter.objects.get_or_create(
                code=code,
                defaults={'provincial_office': pos[po_code], 'name': name}
            )
            dcs[code] = dc
        self.stdout.write(self.style.SUCCESS('  [OK] Distribution Centers created'))

        # ---- METER POINTS for Kathmandu DC ----
        ktm_dc = dcs.get('KTM-DC')
        if ktm_dc:
            meter_points = [
                ('S/S Feeder (11kV)', 'KTM-MP-01', 'FEEDER_11KV', '11 kV', 100),
                ('Bazaar Feeder (11kV)', 'KTM-MP-02', 'FEEDER_11KV', '11 kV', 100),
                ('Industrial Feeder (33kV)', 'KTM-MP-03', 'FEEDER_33KV', '33 kV', 200),
                ('IPP - Solar Plant', 'KTM-MP-04', 'IPP', '11 kV', 50),
                ('Export to Lalitpur DC', 'KTM-MP-05', 'EXPORT_DC', '11 kV', 100),
            ]
            for name, code, stype, voltage, mf in meter_points:
                MeterPoint.objects.get_or_create(
                    code=code,
                    defaults={
                        'distribution_center': ktm_dc,
                        'name': name,
                        'source_type': stype,
                        'voltage_level': voltage,
                        'multiplying_factor': mf,
                    }
                )

        # Meter points for Nuwakot DC
        nuw_dc = dcs.get('NUW-DC')
        if nuw_dc:
            nuw_meters = [
                ('S/S Feeder (11kV)', 'NUW-MP-01', 'FEEDER_11KV', '11 kV', 100),
                ('Bazaar Feeder (11kV)', 'NUW-MP-02', 'FEEDER_11KV', '11 kV', 100),
                ('Bidur Feeder (11kV)', 'NUW-MP-03', 'FEEDER_11KV', '11 kV', 100),
            ]
            for name, code, stype, voltage, mf in nuw_meters:
                MeterPoint.objects.get_or_create(
                    code=code,
                    defaults={
                        'distribution_center': nuw_dc,
                        'name': name,
                        'source_type': stype,
                        'voltage_level': voltage,
                        'multiplying_factor': mf,
                    }
                )

        # Meter points for Lalitpur DC
        lpr_dc = dcs.get('LPR-DC')
        if lpr_dc:
            lpr_meters = [
                ('Patan Feeder (11kV)', 'LPR-MP-01', 'FEEDER_11KV', '11 kV', 100),
                ('Jawalakhel Feeder (11kV)', 'LPR-MP-02', 'FEEDER_11KV', '11 kV', 100),
                ('Import from KTM-DC', 'LPR-MP-03', 'INTERBRANCH', '11 kV', 100),
            ]
            for name, code, stype, voltage, mf in lpr_meters:
                MeterPoint.objects.get_or_create(
                    code=code,
                    defaults={
                        'distribution_center': lpr_dc,
                        'name': name,
                        'source_type': stype,
                        'voltage_level': voltage,
                        'multiplying_factor': mf,
                    }
                )

        # Meter points for Pokhara DC
        pkr_dc = dcs.get('PKR-DC')
        if pkr_dc:
            pkr_meters = [
                ('Pokhara S/S Feeder (11kV)', 'PKR-MP-01', 'FEEDER_11KV', '11 kV', 100),
                ('Hemja Feeder (11kV)', 'PKR-MP-02', 'FEEDER_11KV', '11 kV', 100),
                ('Lekhnath Feeder (11kV)', 'PKR-MP-03', 'FEEDER_11KV', '11 kV', 100),
                ('Rupa Feeder (33kV)', 'PKR-MP-04', 'FEEDER_33KV', '33 kV', 200),
            ]
            for name, code, stype, voltage, mf in pkr_meters:
                MeterPoint.objects.get_or_create(
                    code=code,
                    defaults={
                        'distribution_center': pkr_dc,
                        'name': name,
                        'source_type': stype,
                        'voltage_level': voltage,
                        'multiplying_factor': mf,
                    }
                )

        self.stdout.write(self.style.SUCCESS('  [OK] Meter Points created'))

        # ---- CONSUMER CATEGORIES ----
        categories = [
            ('Domestic', 'DOM', 1),
            ('Commercial', 'COM', 2),
            ('Industrial (Small)', 'IND-S', 3),
            ('Industrial (Medium)', 'IND-M', 4),
            ('Industrial (Large)', 'IND-L', 5),
            ('Non-Commercial Institution', 'NCI', 6),
            ('Government', 'GOV', 7),
            ('Agriculture', 'AGR', 8),
            ('Street Light', 'STL', 9),
            ('Water Supply', 'WS', 10),
            ('Export to India', 'EXP-IN', 11),
            ('Export to Other DCs', 'EXP-DC', 12),
            ('Traction', 'TRA', 13),
            ('Mix / Others', 'OTH', 14),
            ('NEA Internal Use', 'NEA-INT', 15),
        ]
        for name, code, order in categories:
            ConsumerCategory.objects.get_or_create(
                code=code,
                defaults={'name': name, 'display_order': order}
            )
        self.stdout.write(self.style.SUCCESS('  [OK] Consumer Categories created'))

        # ---- USERS ----
        user_data = [
            # ---- System Administrator (separate from MD - full system control)
            {
                'username': 'sysadmin',
                'email': 'sysadmin@nea.org.np',
                'full_name': 'System Administrator',
                'role': 'SYS_ADMIN',
                'password': 'nea@admin123',
                'is_staff': True,
                'is_superuser': True,
                'designation': 'System Engineer',
                'employee_id': 'NEA-SYS-001',
            },
            # ---- Managing Director (view only - NOT system admin)
            {
                'username': 'md_user',
                'email': 'md@nea.org.np',
                'full_name': 'Ram Prasad Sharma',
                'role': 'MD',
                'password': 'nea@2024',
                'designation': 'Managing Director',
                'employee_id': 'NEA-MD-001',
            },
            # ---- Deputy Managing Director (same rights as MD - view only)
            {
                'username': 'dmd_user',
                'email': 'dmd@nea.org.np',
                'full_name': 'Sunita Rajbhandari',
                'role': 'DMD',
                'password': 'nea@2024',
                'designation': 'Deputy Managing Director',
                'employee_id': 'NEA-DMD-001',
            },
            # ---- Provincial Manager - KVDD
            {
                'username': 'prov_kvdd',
                'email': 'prov.kvdd@nea.org.np',
                'full_name': 'Gopal Thapa',
                'role': 'PROVINCIAL_MANAGER',
                'password': 'nea@2024',
                'provincial_office_code': 'KVDD',
                'designation': 'Provincial Manager',
                'employee_id': 'NEA-PM-001',
            },
            # ---- DC Staff
            {
                'username': 'dc_ktm',
                'email': 'dc.ktm@nea.org.np',
                'full_name': 'Sita Sharma',
                'role': 'DC_STAFF',
                'password': 'nea@2024',
                'dc_code': 'KTM-DC',
                'provincial_office_code': 'KVDD',
                'designation': 'DC Staff Officer',
                'employee_id': 'NEA-DC-001',
            },
            {
                'username': 'dc_nuw',
                'email': 'dc.nuw@nea.org.np',
                'full_name': 'Hari Bahadur KC',
                'role': 'DC_STAFF',
                'password': 'nea@2024',
                'dc_code': 'NUW-DC',
                'provincial_office_code': 'KVDD',
                'designation': 'DC Staff Officer',
                'employee_id': 'NEA-DC-002',
            },
            {
                'username': 'dc_lpr',
                'email': 'dc.lpr@nea.org.np',
                'full_name': 'Prakash Karki',
                'role': 'DC_STAFF',
                'password': 'nea@2024',
                'dc_code': 'LPR-DC',
                'provincial_office_code': 'KVDD',
                'designation': 'DC Staff Officer',
                'employee_id': 'NEA-DC-003',
            },
            {
                'username': 'dc_pkr',
                'email': 'dc.pkr@nea.org.np',
                'full_name': 'Mina Gurung',
                'role': 'DC_STAFF',
                'password': 'nea@2024',
                'dc_code': 'PKR-DC',
                'provincial_office_code': 'GDD',
                'designation': 'DC Staff Officer',
                'employee_id': 'NEA-DC-004',
            },
        ]

        for u in user_data:
            if NEAUser.objects.filter(username=u['username']).exists():
                self.stdout.write(f"  [WARNING] User '{u['username']}' already exists - skipped")
                continue
            kwargs = {
                'email': u['email'],
                'full_name': u['full_name'],
                'role': u['role'],
                'is_staff': u.get('is_staff', False),
                'is_superuser': u.get('is_superuser', False),
                'designation': u.get('designation', ''),
                'employee_id': u.get('employee_id', ''),
            }
            if u.get('provincial_office_code'):
                kwargs['provincial_office'] = pos.get(u['provincial_office_code'])
            if u.get('dc_code'):
                kwargs['distribution_center'] = dcs.get(u['dc_code'])

            NEAUser.objects.create_user(
                username=u['username'],
                password=u['password'],
                **kwargs
            )
            self.stdout.write(f"  [OK] Created user: {u['username']} ({u['role']})")

        self.stdout.write(self.style.SUCCESS('\n[OK] Seeding complete!'))
        self.stdout.write('')
        self.stdout.write('=' * 56)
        self.stdout.write('LOGIN CREDENTIALS:')
        self.stdout.write('=' * 56)
        self.stdout.write('  sysadmin   / nea@admin123  -> System Administrator')
        self.stdout.write('  md_user    / nea@2024      -> Managing Director')
        self.stdout.write('  dmd_user   / nea@2024      -> Deputy Managing Director')
        self.stdout.write('  prov_kvdd  / nea@2024      -> Provincial Manager (KVDD)')
        self.stdout.write('  dc_ktm     / nea@2024      -> DC Staff (Kathmandu DC)')
        self.stdout.write('  dc_nuw     / nea@2024      -> DC Staff (Nuwakot DC)')
        self.stdout.write('  dc_lpr     / nea@2024      -> DC Staff (Lalitpur DC)')
        self.stdout.write('  dc_pkr     / nea@2024      -> DC Staff (Pokhara DC)')
        self.stdout.write('=' * 56)
