from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('nea_loss', '0007_add_energy_import_export_types_single_reading'),
    ]

    operations = [
        migrations.CreateModel(
            name='DCMonthlyTarget',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('month', models.PositiveSmallIntegerField(choices=[
                    (1, 'Shrawan'), (2, 'Bhadra'), (3, 'Ashwin'), (4, 'Kartik'),
                    (5, 'Mangsir'), (6, 'Poush'), (7, 'Magh'), (8, 'Falgun'),
                    (9, 'Chaitra'), (10, 'Baisakh'), (11, 'Jestha'), (12, 'Ashadh'),
                ])),
                ('target_loss_percent', models.DecimalField(decimal_places=3, max_digits=6)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('distribution_center', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='monthly_targets',
                    to='nea_loss.distributioncenter',
                )),
                ('fiscal_year', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='dc_monthly_targets',
                    to='nea_loss.fiscalyear',
                )),
                ('set_by', models.ForeignKey(
                    blank=True, null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='dc_targets_set',
                    to='nea_loss.neauser',
                )),
            ],
            options={
                'ordering': ['fiscal_year', 'distribution_center', 'month'],
                'unique_together': {('distribution_center', 'fiscal_year', 'month')},
            },
        ),
    ]
