"""
Loads the Baneshwor Distribution Centre loss report for F/Y 2083/084
(Shrawan, Bhadra, Ashwin/"Ashoj") from the signed paper report.

Idempotent: safe to run on every deploy. It never deletes anything and only
touches the Baneshwor DC and fiscal year 2083/084.
"""
import decimal
from decimal import Decimal as D

from django.core.management.base import BaseCommand
from django.db import transaction

from nea_loss.models import (
    Province, ProvincialOffice, DistributionCenter, FiscalYear, LossReport,
    MonthlyLossData, MeterPoint, MeterReading, ConsumerCategory, EnergyUtilisation,
)

MONTHS = [(1, 'Shrawan'), (2, 'Bhadra'), (3, 'Ashwin')]
SOLD = [D('37969398'), D('35636124'), D('35316787')]  # "Total sold unit" per month


def trio(p, q, u):
    return list(zip(p, q, u))


# (name, source_type, connection_source, multiplying_factor, [(present, previous, printed_unit_kwh) x 3])
# multiplying_factor is the factor that reproduces the printed utilised energy.
F = 'FEEDER_11KV'
POINTS = [
    # Old Chabahil s/s
    ('New Chabahil 1', F, 'Old Chabahil s/s', 1, trio([46329318, 49241406, 52090638], [43471302, 46329318, 49241406], [2858016, 2912088, 2849232])),
    ('New Chabahil 2', F, 'Old Chabahil s/s', 1, trio([45727776, 48627606, 51442338], [42895578, 45727776, 48627606], [2832198, 2899830, 2814732])),
    ('Chabahil 3', F, 'Old Chabahil s/s', 1, trio([29189814, 31121586, 32969178], [27317574, 29189814, 31121586], [1872240, 1931772, 1847592])),
    ('Chabahil 4', F, 'Old Chabahil s/s', 1, trio([29202348, 31055514, 32842788], [27407754, 29202348, 31055514], [1794594, 1853166, 1787274])),
    # New Chabahil s/s
    ('Kapan', F, 'New Chabahil s/s', 1, trio([23581110, 25038120, 26436420], [22148454, 23581110, 25038120], [1432656, 1457010, 1398300])),
    ('Sankhu', F, 'New Chabahil s/s', 1, trio([26014716, 27618771, 29163066], [24431448, 26014716, 27618771], [1583268, 1604055, 1544295])),
    ('Mahankal', F, 'New Chabahil s/s', 1, trio([29403150, 30905052, 32348421], [27924315, 29403150, 30905052], [1478835, 1501902, 1443369])),
    ('Nayabasti', F, 'New Chabahil s/s', 1, trio([30117900, 31558818, 32885136], [28634898, 30117900, 31558818], [1483002, 1440918, 1326318])),
    ('Ramhiti', F, 'New Chabahil s/s', 1, trio([22815966, 23861184, 24856890], [21775903, 22815966, 23861184], [1040063, 1045218, 995706])),
    ('Boudha', F, 'New Chabahil s/s', 1, trio([16377840, 17465652, 18521526], [15291926, 16377840, 17465652], [1085914, 1087812, 1055874])),
    ('Sundarijal', F, 'New Chabahil s/s', 1, trio([17720928, 18746595, 19760190], [16665093, 17720928, 18746595], [1055835, 1025667, 1013595])),
    # Min Bhawan s/s
    ('Dhobikhola', F, 'Min Bhawan s/s', 1, trio([29390271, 31076808, 32639955], [27720098, 29390271, 31076808], [1670173, 1686537, 1563147])),
    ('Bagmati', F, 'Min Bhawan s/s', 1, trio([25185642, 26464137, 27640905], [23923815, 25185642, 26464137], [1261827, 1278495, 1176768])),
    ('Koteswor', F, 'Min Bhawan s/s', 1, trio([24637308, 26445519, 27931587], [23016378, 24637308, 26445519], [1620930, 1808211, 1486068])),
    ('Baneswor', F, 'Min Bhawan s/s', 1, trio([28875905, 30649149, 32270190], [27098328, 28875905, 30649149], [1777577, 1773244, 1621041])),
    ('Airport Old', F, 'Min Bhawan s/s', 1, trio([16257219, 17181312, 18216621], [15568902, 16257219, 17181312], [688317, 924093, 1035309])),
    ('Imadol-1', F, 'Min Bhawan s/s', 1, trio([28206447, 30048685, 31809237], [26431551, 28206447, 30048685], [1774896, 1842238, 1760552])),
    ('ICC Feeder', F, 'Min Bhawan s/s', 1, trio([4263717, 4505316, 4721853], [4036542, 4263717, 4505316], [227175, 241599, 216537])),
    ('Sankhamul', F, 'Min Bhawan s/s', 1, trio([36451737] * 3, [34342203, 36451737, 36451737], [2109534, 0, 0])),
    ('New Airport', F, 'Min Bhawan s/s', 1, trio([34702770, 36659607, 38462961], [32697339, 34702770, 36659607], [2005431, 1956837, 1803354])),
    ('Gothatar', F, 'Min Bhawan s/s', 1, trio([29779521, 31630314, 33441786], [28062321, 29779521, 31630314], [1717200, 1850793, 1811472])),
    ('Battisputali', F, 'Min Bhawan s/s', 1, trio([23400327, 25046274, 26599401], [21791373, 23400327, 25046274], [1608954, 1645947, 1553127])),
    ('KMC', F, 'Min Bhawan s/s', 1, trio([25629825, 27149148, 28563612], [24135414, 25629825, 27149148], [1494411, 1519323, 1414464])),
    # Bhadra/Ashwin printed energy is an estimate (average current / new meter), not a reading difference
    ('New Sankhamul', F, 'Min Bhawan s/s', 1, trio([13800, 0, 0], [4700, 0, 0], [9100, '1984456.32', '1578490.64'])),
    # Mulpani s/s
    ('Gokarna', F, 'Mulpani s/s', 1000, trio([D('11270.2'), 12741, 14146], [9927, D('11270.2'), 12741], [1343200, 1470800, 1405000])),
    # Sundarijal powerplant (energy received = export meter minus import meter)
    ('Sundarijal Powerplant (export meter)', 'IPP', 'Sundarijal Powerplant', 1, trio([1826248, 2278241, 2734819], [1372952, 1826248, 2278241], [453296, 451993, 456578])),
    ('Sundarijal Powerplant (import meter 45230002270)', 'EXPORT_IPP', 'Sundarijal Powerplant', 1, trio([702, 777, 804], [544, 702, 777], [158, 75, 27])),
    # Exports to other DCs
    ('Gothatar (Thimi DC) near Pepsi bridge', 'EXPORT_DC', 'Baneshwor S/S', 1, trio([5010154] * 3, [5010154] * 3, [0, 0, 0])),
    ('Imadole-1 feeder (Thimi DC) Jadibuti bridge', 'EXPORT_DC', 'Baneshwor S/S', 1, trio([47793, 61932, 61932], [47793, 47793, 61932], [0, 14139, 0])),
    ('Tangal (Ratnapark DC)', 'EXPORT_DC', 'Chabahil switching', 100, trio([70642, 73804, 76664], [67517, 70642, 73804], [312500, 316200, 286000])),
    ('Sankhamul feeder (Ratnapark DC) Bijuli Bazar bridge', 'EXPORT_DC', 'Baneshwor S/S', 1, trio([6216322, 6216648, 6216648], [5974456, 6216322, 6216648], [241866, 326, 0])),
    ('Dhobikhola feeder (Ratnapark DC)', 'EXPORT_DC', 'Baneshwor S/S', 1, trio([2225410] * 3, [2225410] * 3, [0, 0, 0])),
    ('Kapan (Maharajgunj DC) Rajdhani', 'EXPORT_DC', 'Chabhail switching', 1, trio([5917] * 3, [5917] * 3, [0, 0, 0])),
    ('Kapan (Maharajgunj DC) down of Kapan gumba', 'EXPORT_DC', 'Chabhail switching', 1, trio([9345872] * 3, [9345872] * 3, [0, 0, 0])),
    ('Danchhi (Jorpati DC)', 'EXPORT_DC', 'Chabhail switching', 1, trio([1244659] * 3, [1244659] * 3, [0, 0, 0])),
    ('Sundarijal (Jorpati DC) puwar gaun', 'EXPORT_DC', 'Chabhail switching', 1, trio([186085, 197411, 208170], [175063, 186085, 197411], [12473, 12408, '12265.90'])),
    ('Sundarijal (Jorpati DC) melamchi', 'EXPORT_DC', 'Chabhail switching', 1, trio([1035849, 1067204, '1096620.96'], [1003294, 1035849, 1067204], [32555, 31355, '29416.96'])),
    ('KUKL (Jorpati DC) Ramhiti/Gokarna', 'EXPORT_DC', 'Mulpani s/s', 1, trio([63949, 65539, '67486.25'], [62258, 63949, 65539], [1691, 1590, '1947.25'])),
    ('Nepal Trust Karyalaya (Jorpati DC) Ramhiti/Gokarna', 'EXPORT_DC', 'Mulpani s/s', 1, trio([45670, 45987, '46327.48'], [45333, 45670, 45987], [337, 317, '340.48'])),
    ('Sankhu feeder (Jorpati DC) Sundarijal', 'EXPORT_DC', 'Chabhail switching', 1, trio([758727] * 3, [758727] * 3, [0, 0, 0])),
    ('Gothatar (Jorpati DC) Khahare', 'EXPORT_DC', 'Baneshwor S/S', 1, trio([960198] * 3, [960198] * 3, [0, 0, 0])),
]
IMPORT_TYPES = {'SUBSTATION', 'FEEDER_11KV', 'FEEDER_33KV', 'INTERBRANCH', 'IPP', 'ENERGY_IMPORT'}
EXPORT_TYPES = {'EXPORT_DC', 'EXPORT_IPP', 'ENERGY_EXPORT'}


class Command(BaseCommand):
    help = 'Load Baneshwor DC loss report data for F/Y 2083/084 (Shrawan-Ashwin).'

    @transaction.atomic
    def handle(self, *args, **opts):
        fy, created = FiscalYear.objects.get_or_create(
            year_bs='2083/084',
            defaults={'year_ad_start': 2026, 'year_ad_end': 2027,
                      'loss_target_percent': D('3.35'), 'is_active': True},
        )
        if created:
            FiscalYear.objects.exclude(pk=fy.pk).update(is_active=False)

        dc = DistributionCenter.objects.filter(name__icontains='baneshwor').first()
        if not dc:
            prov, _ = Province.objects.get_or_create(code='P3', defaults={'name': 'Bagmati Province'})
            po, _ = ProvincialOffice.objects.get_or_create(
                code='KVDD', defaults={'province': prov, 'name': 'Kathmandu Valley Distribution Division (KVDD)'})
            dc = DistributionCenter.objects.create(
                provincial_office=po, name='Baneshwor Distribution Center', code='BNW-DC',
                address='Old Baneshwor, Kathmandu')

        cat, _ = ConsumerCategory.objects.get_or_create(
            code='BNW-TOTAL-SOLD',
            defaults={'name': 'Total Sold Unit', 'distribution_center': dc, 'display_order': 1})

        mps = []
        for i, (name, stype, src, mf, _rows) in enumerate(POINTS, 1):
            mp, _ = MeterPoint.objects.get_or_create(
                distribution_center=dc, name=name,
                defaults={'code': f'BNW-MP-{i:02d}', 'source_type': stype, 'voltage_level': '11 kV',
                          'multiplying_factor': D(mf), 'connection_source': src})
            mps.append(mp)

        for idx, (month, month_name) in enumerate(MONTHS):
            report, _ = LossReport.objects.get_or_create(
                distribution_center=dc, fiscal_year=fy, month=month, defaults={'status': 'APPROVED'})
            md, _ = MonthlyLossData.objects.get_or_create(
                report=report, month=month, defaults={'month_name': month_name})
            imp = exp = D('0')
            for mp, (_n, stype, _s, mf, rows) in zip(mps, POINTS):
                present, prev, unit = rows[idx]
                mr, _ = MeterReading.objects.update_or_create(
                    monthly_data=md, meter_point=mp,
                    defaults={'present_reading': D(str(present)), 'previous_reading': D(str(prev)),
                              'multiplying_factor': D(mf)})
                unit = D(str(unit))
                if mr.unit_kwh != unit:  # printed figure is authoritative (estimates / rounding)
                    MeterReading.objects.filter(pk=mr.pk).update(unit_kwh=unit)
                if stype in IMPORT_TYPES:
                    imp += unit
                elif stype in EXPORT_TYPES:
                    exp += unit
            EnergyUtilisation.objects.update_or_create(
                monthly_data=md, consumer_category=cat, defaults={'energy_kwh': SOLD[idx]})
            md.total_energy_import, md.total_energy_export = imp, exp
            md.total_energy_utilised = SOLD[idx]
            md.net_energy_received = imp - exp
            md.loss_unit = md.net_energy_received - SOLD[idx]
            md.monthly_loss_percent = md.loss_unit / md.net_energy_received
            md.save()
            report.calculate_summary()
            self.stdout.write(f'  {month_name}: received {md.net_energy_received}, sold {SOLD[idx]}, '
                              f'loss {md.loss_unit} ({md.monthly_loss_percent * 100:.2f}%)')
        self.stdout.write(self.style.SUCCESS(f'Baneshwor data loaded for {fy.year_bs}.'))
