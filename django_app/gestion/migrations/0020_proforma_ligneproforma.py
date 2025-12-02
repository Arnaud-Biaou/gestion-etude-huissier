# Generated manually for Proforma and LigneProforma models

from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('gestion', '0019_add_regime_type_client_aib'),
    ]

    operations = [
        migrations.CreateModel(
            name='Proforma',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('numero', models.CharField(max_length=20, unique=True, verbose_name='Numéro proforma')),
                ('client', models.CharField(max_length=200, verbose_name='Nom du client')),
                ('ifu', models.CharField(blank=True, max_length=20, verbose_name='IFU Client')),
                ('description_dossier', models.TextField(blank=True, help_text="Description du dossier si celui-ci n'est pas encore créé", verbose_name='Description du dossier')),
                ('regime', models.CharField(choices=[('tps', 'TPS - Régime simplifié'), ('tva', 'TVA (18%) - Régime normal')], default='tps', max_length=10, verbose_name='Régime fiscal')),
                ('type_client', models.CharField(choices=[('prive', 'Client privé (particulier, entreprise)'), ('public', 'Client public (État, mairie, ministère)')], default='prive', max_length=10, verbose_name='Type de client')),
                ('client_aib', models.BooleanField(default=False, help_text='Acompte sur Impôt sur les Bénéfices (3%)', verbose_name="Client soumis à l'AIB")),
                ('montant_ht', models.DecimalField(decimal_places=0, default=0, max_digits=15, verbose_name='Montant HT (Honoraires)')),
                ('montant_tva', models.DecimalField(decimal_places=0, default=0, max_digits=15, verbose_name='Montant TVA/TPS')),
                ('montant_ttc', models.DecimalField(decimal_places=0, default=0, max_digits=15, verbose_name='Montant TTC')),
                ('date_creation', models.DateField(default=django.utils.timezone.now, verbose_name='Date de création')),
                ('date_validite', models.DateField(blank=True, help_text="Date jusqu'à laquelle la proforma est valide", null=True, verbose_name='Date de validité')),
                ('statut', models.CharField(choices=[('brouillon', 'Brouillon'), ('envoyee', 'Envoyée au client'), ('acceptee', 'Acceptée'), ('refusee', 'Refusée'), ('expiree', 'Expirée'), ('convertie', 'Convertie en facture')], default='brouillon', max_length=20, verbose_name='Statut')),
                ('observations', models.TextField(blank=True, verbose_name='Observations')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('dossier', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='proformas', to='gestion.dossier', verbose_name='Dossier associé')),
                ('facture_generee', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='proforma_origine', to='gestion.facture', verbose_name='Facture générée')),
            ],
            options={
                'verbose_name': 'Proforma',
                'verbose_name_plural': 'Proformas',
                'ordering': ['-date_creation', '-numero'],
            },
        ),
        migrations.CreateModel(
            name='LigneProforma',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('description', models.CharField(max_length=500, verbose_name='Description')),
                ('quantite', models.IntegerField(default=1, verbose_name='Quantité')),
                ('prix_unitaire', models.DecimalField(decimal_places=0, max_digits=15, verbose_name='Prix unitaire (Honoraires)')),
                ('feuillets', models.IntegerField(default=1, verbose_name='Nombre de feuillets')),
                ('enregistrement', models.BooleanField(default=True, verbose_name='Avec enregistrement')),
                ('proforma', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='lignes', to='gestion.proforma')),
            ],
            options={
                'verbose_name': 'Ligne de proforma',
                'verbose_name_plural': 'Lignes de proforma',
            },
        ),
    ]
