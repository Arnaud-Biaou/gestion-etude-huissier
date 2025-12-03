# Generated manually

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('gestion', '0018_add_dossier_indexes'),
    ]

    operations = [
        migrations.AddField(
            model_name='lignefacture',
            name='type_ligne',
            field=models.CharField(
                choices=[('acte', 'Acte'), ('debours', 'Débours')],
                default='acte',
                max_length=20,
                verbose_name='Type de ligne'
            ),
        ),
        migrations.AddField(
            model_name='lignefacture',
            name='honoraires',
            field=models.DecimalField(
                blank=True,
                decimal_places=0,
                max_digits=15,
                null=True,
                verbose_name='Honoraires'
            ),
        ),
        migrations.AddField(
            model_name='lignefacture',
            name='timbre',
            field=models.DecimalField(
                blank=True,
                decimal_places=0,
                max_digits=15,
                null=True,
                verbose_name='Timbre'
            ),
        ),
        migrations.AddField(
            model_name='lignefacture',
            name='enregistrement',
            field=models.DecimalField(
                blank=True,
                decimal_places=0,
                max_digits=15,
                null=True,
                verbose_name='Enregistrement'
            ),
        ),
        migrations.AddField(
            model_name='lignefacture',
            name='montant_ht',
            field=models.DecimalField(
                blank=True,
                decimal_places=0,
                max_digits=15,
                null=True,
                verbose_name='Montant HT'
            ),
        ),
    ]
