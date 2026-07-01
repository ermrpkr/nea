from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('nea_loss', '0017_dcsdetail_provincialoffice_edit_approval_password_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='dcsdetaileditrequest',
            name='pending_image',
            field=models.ImageField(
                blank=True,
                help_text='Image uploaded with edit request; applied on approval',
                null=True,
                upload_to='dcs_images/pending/',
            ),
        ),
    ]
