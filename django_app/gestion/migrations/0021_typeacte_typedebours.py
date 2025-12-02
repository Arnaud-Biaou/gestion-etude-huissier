# Generated manually

from django.db import migrations, models


def create_default_types(apps, schema_editor):
    """Créer les types d'actes et débours par défaut"""
    TypeActe = apps.get_model('gestion', 'TypeActe')
    TypeDebours = apps.get_model('gestion', 'TypeDebours')

    # Types d'actes d'huissier courants
    actes_defaut = [
        {'nom': 'Sommation de payer', 'honoraires_defaut': 45000, 'description': 'Mise en demeure de payer une dette'},
        {'nom': 'Commandement de payer', 'honoraires_defaut': 56000, 'description': 'Commandement avant saisie'},
        {'nom': 'Sommation interpellative', 'honoraires_defaut': 45000, 'description': 'Demande d\'explication ou de réponse'},
        {'nom': 'Signification de décision', 'honoraires_defaut': 35000, 'description': 'Notification d\'une décision de justice'},
        {'nom': 'Signification de correspondance', 'honoraires_defaut': 35000, 'description': 'Notification d\'un courrier'},
        {'nom': 'PV de constat', 'honoraires_defaut': 65000, 'description': 'Procès-verbal de constat'},
        {'nom': 'PV de saisie', 'honoraires_defaut': 75000, 'description': 'Procès-verbal de saisie'},
        {'nom': 'PV de vente', 'honoraires_defaut': 85000, 'description': 'Procès-verbal de vente aux enchères'},
        {'nom': 'Procès-verbal de difficultés', 'honoraires_defaut': 55000, 'description': 'PV constatant des difficultés d\'exécution'},
        {'nom': 'Assignation', 'honoraires_defaut': 45000, 'description': 'Convocation en justice'},
        {'nom': 'Itératif commandement', 'honoraires_defaut': 45000, 'description': 'Renouvellement de commandement'},
        {'nom': 'Signification de jugement', 'honoraires_defaut': 35000, 'description': 'Notification d\'un jugement'},
        {'nom': 'Signification d\'ordonnance', 'honoraires_defaut': 35000, 'description': 'Notification d\'une ordonnance'},
        {'nom': 'Dénonce de saisie', 'honoraires_defaut': 35000, 'description': 'Notification de saisie au débiteur'},
        {'nom': 'Signification de contrainte', 'honoraires_defaut': 35000, 'description': 'Notification d\'une contrainte'},
    ]

    for acte_data in actes_defaut:
        TypeActe.objects.create(
            nom=acte_data['nom'],
            description=acte_data.get('description', ''),
            honoraires_defaut=acte_data['honoraires_defaut'],
            est_timbre_defaut=True,
            est_enregistre_defaut=True,
            actif=True
        )

    # Types de débours courants
    debours_defaut = [
        {'nom': 'Transport', 'montant_defaut': 10000},
        {'nom': 'Enrôlement', 'montant_defaut': 5000},
        {'nom': 'Frais de greffe', 'montant_defaut': 3000},
        {'nom': 'Dépôt cahier des charges', 'montant_defaut': 15000},
        {'nom': 'Enrôlement cahier des charges', 'montant_defaut': 10000},
        {'nom': 'Certificat de non appel', 'montant_defaut': 2000},
        {'nom': 'Certificat de non opposition', 'montant_defaut': 2000},
        {'nom': 'Grosse exécutoire', 'montant_defaut': 5000},
        {'nom': 'Copie certifiée', 'montant_defaut': 1500},
        {'nom': 'Frais de publication', 'montant_defaut': 25000},
        {'nom': 'Frais de serrurier', 'montant_defaut': 15000},
        {'nom': 'Frais de gardiennage', 'montant_defaut': 5000},
    ]

    for debours_data in debours_defaut:
        TypeDebours.objects.create(
            nom=debours_data['nom'],
            montant_defaut=debours_data['montant_defaut'],
            actif=True
        )


def reverse_create_default_types(apps, schema_editor):
    """Supprimer les types par défaut"""
    TypeActe = apps.get_model('gestion', 'TypeActe')
    TypeDebours = apps.get_model('gestion', 'TypeDebours')
    TypeActe.objects.all().delete()
    TypeDebours.objects.all().delete()


class Migration(migrations.Migration):

    dependencies = [
        ('gestion', '0020_proforma_ligneproforma'),
    ]

    operations = [
        migrations.CreateModel(
            name='TypeActe',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nom', models.CharField(max_length=200, unique=True, verbose_name="Nom de l'acte")),
                ('description', models.TextField(blank=True, verbose_name='Description')),
                ('honoraires_defaut', models.DecimalField(decimal_places=0, default=0, help_text='Montant des honoraires par défaut en FCFA', max_digits=15, verbose_name='Honoraires par défaut')),
                ('est_timbre_defaut', models.BooleanField(default=True, help_text='Timbre fiscal appliqué par défaut', verbose_name='Timbre par défaut')),
                ('est_enregistre_defaut', models.BooleanField(default=True, help_text='Enregistrement appliqué par défaut', verbose_name='Enregistrement par défaut')),
                ('actif', models.BooleanField(default=True, verbose_name='Actif')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'verbose_name': "Type d'acte",
                'verbose_name_plural': "Types d'actes",
                'ordering': ['nom'],
            },
        ),
        migrations.CreateModel(
            name='TypeDebours',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nom', models.CharField(max_length=200, unique=True, verbose_name='Nom du débours')),
                ('montant_defaut', models.DecimalField(decimal_places=0, default=0, help_text='Montant par défaut en FCFA', max_digits=15, verbose_name='Montant par défaut')),
                ('actif', models.BooleanField(default=True, verbose_name='Actif')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'verbose_name': 'Type de débours',
                'verbose_name_plural': 'Types de débours',
                'ordering': ['nom'],
            },
        ),
        migrations.RunPython(create_default_types, reverse_create_default_types),
    ]
