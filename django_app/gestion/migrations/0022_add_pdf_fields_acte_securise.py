# Generated manually for ActeSecurise PDF fields

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('gestion', '0021_typeacte_typedebours'),
    ]

    operations = [
        migrations.AddField(
            model_name='actesecurise',
            name='pdf_original',
            field=models.FileField(
                blank=True,
                help_text="Le PDF de l'acte tel qu'uploadé",
                null=True,
                upload_to='actes/originaux/',
                verbose_name='PDF original'
            ),
        ),
        migrations.AddField(
            model_name='actesecurise',
            name='pdf_avec_qr',
            field=models.FileField(
                blank=True,
                help_text='Le PDF avec QR code incrusté (version Original)',
                null=True,
                upload_to='actes/securises/',
                verbose_name='PDF avec QR code'
            ),
        ),
    ]
