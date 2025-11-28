# Generated manually for Module Comptabilité SYSCOHADA corrections

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('gestion', '0001_initial'),
        ('comptabilite', '0001_initial'),
    ]

    operations = [
        # Mise à jour des choix de classe pour inclure classe 9
        migrations.AlterField(
            model_name='comptecomptable',
            name='classe',
            field=models.CharField(
                choices=[
                    ('1', 'Classe 1 - Capitaux'),
                    ('2', 'Classe 2 - Immobilisations'),
                    ('3', 'Classe 3 - Stocks'),
                    ('4', 'Classe 4 - Tiers'),
                    ('5', 'Classe 5 - Trésorerie'),
                    ('6', 'Classe 6 - Charges'),
                    ('7', 'Classe 7 - Produits'),
                    ('8', 'Classe 8 - Autres charges/produits'),
                    ('9', 'Classe 9 - Engagements hors bilan'),
                ],
                max_length=1,
                verbose_name='Classe'
            ),
        ),
        # Création du modèle Lettrage
        migrations.CreateModel(
            name='Lettrage',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('code', models.CharField(max_length=10, unique=True, verbose_name='Code lettrage')),
                ('date_lettrage', models.DateTimeField(auto_now_add=True, verbose_name='Date de lettrage')),
                ('montant', models.DecimalField(decimal_places=0, default=0, max_digits=15, verbose_name='Montant lettré')),
                ('est_partiel', models.BooleanField(default=False, verbose_name='Lettrage partiel')),
                ('commentaire', models.TextField(blank=True, verbose_name='Commentaire')),
                ('compte', models.ForeignKey(
                    limit_choices_to={'numero__startswith': '4'},
                    on_delete=django.db.models.deletion.PROTECT,
                    to='comptabilite.comptecomptable',
                    verbose_name='Compte lettré'
                )),
                ('lettre_par', models.ForeignKey(
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    to='gestion.utilisateur',
                    verbose_name='Lettré par'
                )),
                ('lignes', models.ManyToManyField(
                    related_name='lettrages',
                    to='comptabilite.ligneecriture',
                    verbose_name='Lignes lettrées'
                )),
            ],
            options={
                'verbose_name': 'Lettrage',
                'verbose_name_plural': 'Lettrages',
                'ordering': ['-date_lettrage'],
            },
        ),
    ]
