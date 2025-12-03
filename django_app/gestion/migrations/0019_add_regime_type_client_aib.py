# Generated manually for regime, type_client, client_aib fields

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('gestion', '0018_add_dossier_indexes'),
    ]

    operations = [
        migrations.AddField(
            model_name='facture',
            name='regime',
            field=models.CharField(
                choices=[('tps', 'TPS - Régime simplifié'), ('tva', 'TVA (18%) - Régime normal')],
                default='tps',
                max_length=10,
                verbose_name='Régime fiscal'
            ),
        ),
        migrations.AddField(
            model_name='facture',
            name='type_client',
            field=models.CharField(
                choices=[('prive', 'Client privé (particulier, entreprise)'), ('public', 'Client public (État, mairie, ministère)')],
                default='prive',
                max_length=10,
                verbose_name='Type de client'
            ),
        ),
        migrations.AddField(
            model_name='facture',
            name='client_aib',
            field=models.BooleanField(
                default=False,
                help_text="Acompte sur Impôt sur les Bénéfices (3%) - Suivi interne uniquement",
                verbose_name="Client soumis à l'AIB"
            ),
        ),
    ]
