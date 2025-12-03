# Generated manually for ActeSecurise position_qr field

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('gestion', '0022_add_pdf_fields_acte_securise'),
    ]

    operations = [
        migrations.AddField(
            model_name='actesecurise',
            name='position_qr',
            field=models.CharField(
                choices=[
                    ('bottom-right', 'Bas droite'),
                    ('bottom-left', 'Bas gauche'),
                    ('top-right', 'Haut droite'),
                    ('top-left', 'Haut gauche'),
                ],
                default='bottom-right',
                max_length=20,
                verbose_name='Position du QR code'
            ),
        ),
    ]
