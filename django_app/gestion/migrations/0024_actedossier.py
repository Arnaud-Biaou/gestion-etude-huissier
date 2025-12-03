# Generated manually for ActeDossier model

from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('gestion', '0023_actesecurise_position_qr'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='ActeDossier',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('intitule', models.CharField(help_text='Ex: Commandement de payer du 03/12/2025', max_length=500, verbose_name="Intitulé de l'acte")),
                ('date_acte', models.DateField(verbose_name="Date de l'acte")),
                ('honoraires', models.DecimalField(decimal_places=0, default=0, max_digits=15, verbose_name='Honoraires (FCFA)')),
                ('feuillets', models.PositiveIntegerField(default=1, verbose_name='Nombre de feuillets')),
                ('timbre', models.DecimalField(decimal_places=0, default=0, help_text='1200 FCFA par feuillet', max_digits=15, verbose_name='Timbre fiscal')),
                ('enregistrement', models.DecimalField(decimal_places=0, default=0, help_text='2500 FCFA si applicable', max_digits=15, verbose_name="Droit d'enregistrement")),
                ('debours_divers', models.DecimalField(decimal_places=0, default=0, max_digits=15, verbose_name='Débours divers')),
                ('est_facture', models.BooleanField(default=False, verbose_name='Facturé')),
                ('date_facturation', models.DateField(blank=True, null=True, verbose_name='Date de facturation')),
                ('date_creation', models.DateTimeField(auto_now_add=True)),
                ('date_modification', models.DateTimeField(auto_now=True)),
                ('acte_securise', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='acte_dossier', to='gestion.actesecurise', verbose_name='Acte sécurisé associé')),
                ('cree_par', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL, verbose_name='Créé par')),
                ('dossier', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='actes_realises', to='gestion.dossier', verbose_name='Dossier')),
                ('ligne_facture', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='actes_origine', to='gestion.lignefacture', verbose_name='Ligne de facture')),
                ('type_acte', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='gestion.typeacte', verbose_name="Type d'acte")),
            ],
            options={
                'verbose_name': 'Acte réalisé',
                'verbose_name_plural': 'Actes réalisés',
                'ordering': ['-date_acte', '-date_creation'],
            },
        ),
    ]
