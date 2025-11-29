# Generated migration for Juridiction model with hierarchy

from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('parametres', '0001_initial'),
    ]

    operations = [
        # Remove old Juridiction model and recreate with new structure
        migrations.DeleteModel(
            name='Juridiction',
        ),
        migrations.CreateModel(
            name='Juridiction',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('nom', models.CharField(max_length=200, verbose_name='Nom complet')),
                ('nom_court', models.CharField(max_length=100, verbose_name='Nom abrege')),
                ('type_juridiction', models.CharField(choices=[('tpi', 'Tribunal de Premiere Instance'), ('cour_appel', "Cour d'Appel"), ('cour_speciale', 'Cour Speciale')], max_length=20)),
                ('classe_tpi', models.CharField(blank=True, choices=[('premiere', 'Premiere Classe'), ('deuxieme', 'Deuxieme Classe')], max_length=20, null=True, verbose_name='Classe TPI')),
                ('titre_procureur', models.CharField(default='Procureur de la Republique', max_length=100, verbose_name='Titre du Procureur')),
                ('titre_president', models.CharField(default='President', max_length=100, verbose_name='Titre du President')),
                ('nom_procureur', models.CharField(blank=True, max_length=200, verbose_name='Nom du Procureur actuel')),
                ('nom_president', models.CharField(blank=True, max_length=200, verbose_name='Nom du President actuel')),
                ('titre_procureur_general', models.CharField(blank=True, default='Procureur General', max_length=100, verbose_name='Titre du Procureur General')),
                ('nom_procureur_general', models.CharField(blank=True, max_length=200, verbose_name='Nom du Procureur General')),
                ('nom_president_cour', models.CharField(blank=True, max_length=200, verbose_name='Nom du President de la Cour')),
                ('ville', models.CharField(max_length=100)),
                ('adresse', models.TextField(blank=True)),
                ('telephone', models.CharField(blank=True, max_length=20, verbose_name='Telephone')),
                ('actif', models.BooleanField(default=True)),
                ('ordre', models.PositiveIntegerField(default=0)),
                ('cour_appel_rattachement', models.ForeignKey(blank=True, limit_choices_to={'type_juridiction': 'cour_appel'}, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='juridictions_rattachees', to='parametres.juridiction', verbose_name="Cour d'Appel de rattachement")),
            ],
            options={
                'verbose_name': 'Juridiction',
                'verbose_name_plural': 'Juridictions',
                'ordering': ['ordre', 'nom'],
            },
        ),
    ]
