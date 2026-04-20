from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('nea_loss', '0008_dcmonthlytarget'),
    ]

    operations = [
        migrations.AddField(
            model_name='distributioncenter',
            name='report_start_month',
            field=models.PositiveSmallIntegerField(
                choices=[
                    (1,'Shrawan'),(2,'Bhadra'),(3,'Ashwin'),(4,'Kartik'),
                    (5,'Mangsir'),(6,'Poush'),(7,'Magh'),(8,'Falgun'),
                    (9,'Chaitra'),(10,'Baisakh'),(11,'Jestha'),(12,'Ashadh'),
                ],
                default=1,
                help_text='First month this DC is required to submit a report. Admin sets this.',
            ),
        ),
        migrations.AddField(
            model_name='distributioncenter',
            name='is_active',
            field=models.BooleanField(
                default=True,
                help_text='Inactive DCs are hidden from reports and lists.',
            ),
        ),
    ]