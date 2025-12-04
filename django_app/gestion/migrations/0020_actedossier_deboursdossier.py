# Generated manually

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('gestion', '0019_lignefacture_type_ligne_fields'),
    ]

    operations = [
        migrations.CreateModel(
            name='ActeDossier',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date_acte', models.DateField(verbose_name="Date de l'acte")),
                ('type_acte', models.CharField(max_length=100, verbose_name="Type d'acte")),
                ('description', models.TextField(blank=True, verbose_name='Description')),
                ('honoraires', models.DecimalField(decimal_places=0, default=0, max_digits=15, verbose_name='Honoraires')),
                ('timbre', models.DecimalField(decimal_places=0, default=0, max_digits=15, verbose_name='Timbre')),
                ('enregistrement', models.DecimalField(decimal_places=0, default=0, max_digits=15, verbose_name='Enregistrement')),
                ('date_creation', models.DateTimeField(auto_now_add=True)),
                ('cree_par', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='actes_dossier_crees', to=settings.AUTH_USER_MODEL)),
                ('dossier', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='actes_dossier', to='gestion.dossier', verbose_name='Dossier')),
            ],
            options={
                'verbose_name': 'Acte du dossier',
                'verbose_name_plural': 'Actes du dossier',
                'ordering': ['-date_acte'],
            },
        ),
        migrations.CreateModel(
            name='DeboursDossier',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date_debours', models.DateField(verbose_name='Date du débours')),
                ('designation', models.CharField(max_length=200, verbose_name='Désignation')),
                ('montant', models.DecimalField(decimal_places=0, max_digits=15, verbose_name='Montant')),
                ('piece_justificative', models.FileField(blank=True, null=True, upload_to='debours/', verbose_name='Pièce justificative')),
                ('date_creation', models.DateTimeField(auto_now_add=True)),
                ('cree_par', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='debours_dossier_crees', to=settings.AUTH_USER_MODEL)),
                ('dossier', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='debours_dossier', to='gestion.dossier', verbose_name='Dossier')),
            ],
            options={
                'verbose_name': 'Débours du dossier',
                'verbose_name_plural': 'Débours du dossier',
                'ordering': ['-date_debours'],
            },
        ),
    ]
