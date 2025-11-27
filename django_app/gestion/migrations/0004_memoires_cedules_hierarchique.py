# Generated migration for Mémoires de Cédules - Structure Hiérarchique à 4 Niveaux

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('gestion', '0003_payment_history_tracking'),
    ]

    operations = [
        # Niveau 0 - Autorités requérantes (juridictions)
        migrations.CreateModel(
            name='AutoriteRequerante',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('code', models.CharField(max_length=50, unique=True, verbose_name='Code')),
                ('nom', models.CharField(max_length=300, verbose_name="Nom de l'autorité")),
                ('type_juridiction', models.CharField(blank=True, help_text="Ex: CRIET, TPI, Cour d'Appel, Cour Suprême, etc.", max_length=100, verbose_name='Type de juridiction')),
                ('adresse', models.TextField(blank=True, verbose_name='Adresse')),
                ('ville', models.CharField(blank=True, max_length=100)),
                ('telephone', models.CharField(blank=True, max_length=50)),
                ('email', models.EmailField(blank=True, max_length=254)),
                ('actif', models.BooleanField(default=True)),
                ('date_creation', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'verbose_name': 'Autorité requérante',
                'verbose_name_plural': 'Autorités requérantes',
                'ordering': ['nom'],
            },
        ),

        # Niveau 1 - Mémoire
        migrations.CreateModel(
            name='Memoire',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('numero', models.CharField(max_length=50, unique=True, verbose_name='Numéro du mémoire')),
                ('mois', models.PositiveSmallIntegerField(help_text='Mois de la période (1-12)', verbose_name='Mois')),
                ('annee', models.PositiveIntegerField(verbose_name='Année')),
                ('residence_huissier', models.CharField(help_text='Ville de résidence pour le calcul des distances', max_length=200, verbose_name="Résidence de l'huissier")),
                ('montant_total_actes', models.DecimalField(decimal_places=0, default=0, max_digits=15, verbose_name='Total des actes')),
                ('montant_total_transport', models.DecimalField(decimal_places=0, default=0, max_digits=15, verbose_name='Total transport')),
                ('montant_total_mission', models.DecimalField(decimal_places=0, default=0, max_digits=15, verbose_name='Total mission')),
                ('montant_total', models.DecimalField(decimal_places=0, default=0, max_digits=15, verbose_name='Total général')),
                ('montant_total_lettres', models.CharField(blank=True, max_length=500, verbose_name='Montant en lettres')),
                ('statut', models.CharField(choices=[('brouillon', 'Brouillon'), ('en_cours', 'En cours de rédaction'), ('a_verifier', 'À vérifier'), ('certifie', 'Certifié'), ('soumis', 'Soumis'), ('paye', 'Payé'), ('rejete', 'Rejeté')], default='brouillon', max_length=20)),
                ('date_certification', models.DateTimeField(blank=True, null=True, verbose_name='Date de certification')),
                ('lieu_certification', models.CharField(blank=True, default='Parakou', max_length=100, verbose_name='Lieu de certification')),
                ('observations', models.TextField(blank=True)),
                ('date_creation', models.DateTimeField(auto_now_add=True)),
                ('date_modification', models.DateTimeField(auto_now=True)),
                ('autorite_requerante', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='memoires', to='gestion.autoriterequerante', verbose_name='Autorité requérante')),
                ('certifie_par', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='memoires_certifies', to=settings.AUTH_USER_MODEL, verbose_name='Certifié par')),
                ('cree_par', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='memoires_crees', to=settings.AUTH_USER_MODEL)),
                ('huissier', models.ForeignKey(limit_choices_to={'role': 'huissier'}, on_delete=django.db.models.deletion.PROTECT, related_name='memoires_cedules', to='gestion.collaborateur', verbose_name='Huissier')),
            ],
            options={
                'verbose_name': 'Mémoire de cédules',
                'verbose_name_plural': 'Mémoires de cédules',
                'ordering': ['-annee', '-mois', '-numero'],
                'unique_together': {('mois', 'annee', 'autorite_requerante', 'huissier')},
            },
        ),

        # Niveau 2 - Affaire
        migrations.CreateModel(
            name='AffaireMemoire',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('numero_parquet', models.CharField(help_text='Ex: CRIET/2021/RP/0928', max_length=100, verbose_name='Numéro de parquet')),
                ('intitule_affaire', models.CharField(help_text='Ex: MP c/ DUPONT Jean et autres', max_length=300, verbose_name="Intitulé de l'affaire")),
                ('nature_infraction', models.CharField(blank=True, max_length=300, verbose_name="Nature de l'infraction")),
                ('date_audience', models.DateField(blank=True, null=True, verbose_name="Date d'audience")),
                ('montant_total_actes', models.DecimalField(decimal_places=0, default=0, max_digits=15, verbose_name='Total des actes')),
                ('montant_total_transport', models.DecimalField(decimal_places=0, default=0, max_digits=15, verbose_name='Total transport')),
                ('montant_total_mission', models.DecimalField(decimal_places=0, default=0, max_digits=15, verbose_name='Total mission')),
                ('montant_total_affaire', models.DecimalField(decimal_places=0, default=0, max_digits=15, verbose_name='Total affaire')),
                ('ordre_affichage', models.PositiveIntegerField(default=0)),
                ('date_creation', models.DateTimeField(auto_now_add=True)),
                ('date_modification', models.DateTimeField(auto_now=True)),
                ('memoire', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='affaires', to='gestion.memoire', verbose_name='Mémoire')),
            ],
            options={
                'verbose_name': 'Affaire du mémoire',
                'verbose_name_plural': 'Affaires du mémoire',
                'ordering': ['ordre_affichage', 'numero_parquet'],
                'unique_together': {('memoire', 'numero_parquet')},
            },
        ),

        # Niveau 3 - Destinataire
        migrations.CreateModel(
            name='DestinataireAffaire',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nom', models.CharField(max_length=100, verbose_name='Nom')),
                ('prenoms', models.CharField(blank=True, max_length=200, verbose_name='Prénoms')),
                ('raison_sociale', models.CharField(blank=True, help_text='Pour les personnes morales', max_length=300, verbose_name='Raison sociale')),
                ('qualite', models.CharField(choices=[('prevenu', 'Prévenu'), ('temoin', 'Témoin'), ('partie_civile', 'Partie civile'), ('civilement_responsable', 'Civilement responsable'), ('avocat', 'Avocat'), ('autre', 'Autre')], max_length=30, verbose_name='Qualité')),
                ('titre', models.CharField(blank=True, help_text='Ex: Me, Dr, etc.', max_length=50, verbose_name='Titre')),
                ('adresse', models.TextField(verbose_name='Adresse de signification')),
                ('localite', models.CharField(max_length=100, verbose_name='Localité/Ville')),
                ('distance_km', models.PositiveIntegerField(default=0, help_text="Distance depuis la résidence de l'huissier", verbose_name='Distance (km)')),
                ('type_mission', models.CharField(choices=[('aucune', 'Aucune mission'), ('2_repas', '2 repas (distance 100-200 km)'), ('journee_incomplete', 'Journée incomplète (distance 200-300 km)'), ('journee_complete', 'Journée complète (distance > 300 km)')], default='aucune', max_length=30, verbose_name='Type de mission')),
                ('frais_transport', models.DecimalField(decimal_places=0, default=0, help_text='Distance × 140 F × 2 (aller-retour) - UNE SEULE FOIS', max_digits=15, verbose_name='Frais de transport')),
                ('frais_mission', models.DecimalField(decimal_places=0, default=0, help_text='15 000 / 30 000 / 45 000 F selon durée - UNE SEULE FOIS', max_digits=15, verbose_name='Frais de mission')),
                ('montant_total_actes', models.DecimalField(decimal_places=0, default=0, max_digits=15, verbose_name='Total des actes')),
                ('montant_total_destinataire', models.DecimalField(decimal_places=0, default=0, max_digits=15, verbose_name='Total destinataire')),
                ('ordre_affichage', models.PositiveIntegerField(default=0)),
                ('observations', models.TextField(blank=True)),
                ('date_creation', models.DateTimeField(auto_now_add=True)),
                ('date_modification', models.DateTimeField(auto_now=True)),
                ('affaire', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='destinataires', to='gestion.affairememoire', verbose_name='Affaire')),
            ],
            options={
                'verbose_name': 'Destinataire',
                'verbose_name_plural': 'Destinataires',
                'ordering': ['ordre_affichage', 'nom'],
            },
        ),

        # Niveau 4 - Acte
        migrations.CreateModel(
            name='ActeDestinataire',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date_acte', models.DateField(verbose_name='Date de signification')),
                ('type_acte', models.CharField(choices=[('invitation', 'Signification invitation à comparaître'), ('citation', 'Signification citation à comparaître'), ('convocation', 'Signification convocation'), ('ordonnance', 'Signification ordonnance'), ('jugement', 'Signification jugement'), ('arret', 'Signification arrêt'), ('mandat', 'Signification mandat de comparution'), ('notification', 'Notification'), ('autre', 'Autre')], max_length=30, verbose_name="Type d'acte")),
                ('type_acte_autre', models.CharField(blank=True, help_text='À renseigner si le type est "Autre"', max_length=200, verbose_name='Précision si autre')),
                ('montant_base', models.DecimalField(decimal_places=0, default=4985, max_digits=10, verbose_name='Montant de base (Art. 81)')),
                ('copies_supplementaires', models.PositiveSmallIntegerField(default=0, verbose_name='Copies supplémentaires')),
                ('montant_copies', models.DecimalField(decimal_places=0, default=0, max_digits=10, verbose_name='Montant copies')),
                ('roles_pieces_jointes', models.PositiveSmallIntegerField(default=0, verbose_name='Nombre de rôles de pièces jointes')),
                ('montant_pieces', models.DecimalField(decimal_places=0, default=0, max_digits=10, verbose_name='Montant pièces jointes')),
                ('montant_total_acte', models.DecimalField(decimal_places=0, default=4985, max_digits=15, verbose_name="Montant total de l'acte")),
                ('observations', models.TextField(blank=True)),
                ('date_creation', models.DateTimeField(auto_now_add=True)),
                ('date_modification', models.DateTimeField(auto_now=True)),
                ('destinataire', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='actes', to='gestion.destinataireaffaire', verbose_name='Destinataire')),
            ],
            options={
                'verbose_name': 'Acte signifié',
                'verbose_name_plural': 'Actes signifiés',
                'ordering': ['date_acte', 'type_acte'],
            },
        ),
    ]
