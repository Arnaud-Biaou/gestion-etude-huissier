# Generated manually for Phase 4 - Billing models

from decimal import Decimal
from django.db import migrations, models
import django.db.models.deletion
import django.core.validators
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('gestion', '0020_make_type_dossier_required'),
        ('documents', '0001_initial'),
    ]

    operations = [
        # 1. ActeDossier - Actes réalisés sur un dossier
        migrations.CreateModel(
            name='ActeDossier',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('numero_acte', models.CharField(help_text='Format : EXE-2025-001', max_length=50, unique=True, verbose_name="Numéro d'acte")),
                ('date_acte', models.DateField(verbose_name="Date de l'acte")),
                ('type_acte', models.CharField(
                    choices=[
                        ('commandement', 'Commandement de payer'),
                        ('signification', 'Signification'),
                        ('citation', 'Citation'),
                        ('pv_saisie', 'Procès-verbal de saisie'),
                        ('pv_constat', 'Procès-verbal de constat'),
                        ('mise_demeure', 'Mise en demeure'),
                        ('autre', 'Autre acte'),
                    ],
                    default='autre',
                    max_length=20,
                    verbose_name="Type d'acte"
                )),
                ('montant_base', models.DecimalField(
                    decimal_places=0,
                    max_digits=15,
                    validators=[django.core.validators.MinValueValidator(Decimal('0'))],
                    verbose_name='Montant de base'
                )),
                ('montant_transport', models.DecimalField(
                    blank=True,
                    decimal_places=0,
                    default=Decimal('0'),
                    max_digits=15,
                    null=True,
                    validators=[django.core.validators.MinValueValidator(Decimal('0'))],
                    verbose_name='Frais de transport'
                )),
                ('montant_copies', models.DecimalField(
                    blank=True,
                    decimal_places=0,
                    default=Decimal('0'),
                    max_digits=15,
                    null=True,
                    validators=[django.core.validators.MinValueValidator(Decimal('0'))],
                    verbose_name='Copies supplémentaires'
                )),
                ('montant_total', models.DecimalField(
                    decimal_places=0,
                    help_text='base + transport + copies',
                    max_digits=15,
                    validators=[django.core.validators.MinValueValidator(Decimal('0'))],
                    verbose_name='Montant total'
                )),
                ('observations', models.TextField(blank=True, help_text='Refus, absent, remarques, etc.', verbose_name='Observations')),
                ('facturee', models.BooleanField(default=False, help_text='Cet acte a-t-il été facturé ?', verbose_name='Facturé')),
                ('date_creation', models.DateTimeField(auto_now_add=True, verbose_name='Date de création')),
                ('date_modification', models.DateTimeField(auto_now=True, verbose_name='Date de modification')),
                ('dossier', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='actes_realises', to='gestion.dossier', verbose_name='Dossier')),
                ('acte_type', models.ForeignKey(blank=True, help_text='Référence au catalogue pour le tarif', null=True, on_delete=django.db.models.deletion.SET_NULL, to='gestion.acteprocedure', verbose_name="Type d'acte (catalogue)")),
                ('document', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='actes_dossier', to='documents.document', verbose_name='Document associé')),
                ('facture', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='actes', to='gestion.facture', verbose_name='Facture associée')),
                ('cree_par', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='actes_crees', to='gestion.utilisateur', verbose_name='Créé par')),
                ('destinataires', models.ManyToManyField(blank=True, related_name='actes_recus', to='gestion.partie', verbose_name="Destinataires de l'acte")),
            ],
            options={
                'verbose_name': 'Acte de dossier',
                'verbose_name_plural': 'Actes de dossiers',
                'ordering': ['-date_acte'],
            },
        ),
        migrations.AddIndex(
            model_name='actedossier',
            index=models.Index(fields=['dossier', 'date_acte'], name='gestion_act_dossier_idx'),
        ),
        migrations.AddIndex(
            model_name='actedossier',
            index=models.Index(fields=['numero_acte'], name='gestion_act_numero_idx'),
        ),
        migrations.AddIndex(
            model_name='actedossier',
            index=models.Index(fields=['facturee'], name='gestion_act_facturee_idx'),
        ),

        # 2. Proforma - Devis avant facturation
        migrations.CreateModel(
            name='Proforma',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('numero', models.CharField(help_text='Format : PRO-2025-001', max_length=50, unique=True, verbose_name='Numéro proforma')),
                ('date_emission', models.DateField(default=django.utils.timezone.now, verbose_name="Date d'émission")),
                ('date_validite', models.DateField(help_text='Proforma expire après cette date', verbose_name='Date de validité')),
                ('client_nom', models.CharField(help_text='Nom du client si pas encore créancier', max_length=200, verbose_name='Nom du client')),
                ('client_adresse', models.TextField(blank=True, verbose_name='Adresse du client')),
                ('client_telephone', models.CharField(blank=True, max_length=50, verbose_name='Téléphone')),
                ('client_email', models.EmailField(blank=True, max_length=254, verbose_name='Email')),
                ('client_ifu', models.CharField(blank=True, max_length=50, verbose_name='IFU client')),
                ('titre', models.CharField(help_text='Ex: Recouvrement de créance 5M FCFA', max_length=200, verbose_name='Titre de la prestation')),
                ('description', models.TextField(verbose_name='Description détaillée')),
                ('montant_ht', models.DecimalField(
                    decimal_places=0,
                    max_digits=15,
                    validators=[django.core.validators.MinValueValidator(Decimal('0'))],
                    verbose_name='Montant HT'
                )),
                ('taux_tva', models.DecimalField(decimal_places=2, default=Decimal('18.00'), max_digits=5, verbose_name='Taux TVA %')),
                ('montant_tva', models.DecimalField(
                    decimal_places=0,
                    default=Decimal('0'),
                    max_digits=15,
                    validators=[django.core.validators.MinValueValidator(Decimal('0'))],
                    verbose_name='Montant TVA'
                )),
                ('montant_ttc', models.DecimalField(
                    decimal_places=0,
                    default=Decimal('0'),
                    max_digits=15,
                    validators=[django.core.validators.MinValueValidator(Decimal('0'))],
                    verbose_name='Montant TTC'
                )),
                ('statut', models.CharField(
                    choices=[
                        ('brouillon', 'Brouillon'),
                        ('envoyee', 'Envoyée au client'),
                        ('acceptee', 'Acceptée par client'),
                        ('commandee', 'Commandée (créer dossier)'),
                        ('facturee', 'Convertie en facture'),
                        ('expiree', 'Expirée'),
                        ('annulee', 'Annulée'),
                    ],
                    default='brouillon',
                    max_length=20,
                    verbose_name='Statut'
                )),
                ('delai_paiement', models.PositiveIntegerField(default=15, verbose_name='Délai de paiement (jours)')),
                ('observations', models.TextField(blank=True, verbose_name='Observations')),
                ('date_creation', models.DateTimeField(auto_now_add=True, verbose_name='Date de création')),
                ('date_modification', models.DateTimeField(auto_now=True, verbose_name='Date de modification')),
                ('creancier', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='proformas', to='gestion.creancier', verbose_name='Créancier')),
                ('dossier', models.ForeignKey(blank=True, help_text='Rempli une fois la proforma acceptée', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='proformas', to='gestion.dossier', verbose_name='Dossier créé')),
                ('facture', models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='proforma_origine', to='gestion.facture', verbose_name='Facture générée')),
                ('cree_par', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='proformas_creees', to='gestion.utilisateur', verbose_name='Créé par')),
            ],
            options={
                'verbose_name': 'Proforma',
                'verbose_name_plural': 'Proformas',
                'ordering': ['-date_emission'],
            },
        ),
        migrations.AddIndex(
            model_name='proforma',
            index=models.Index(fields=['numero'], name='gestion_pro_numero_idx'),
        ),
        migrations.AddIndex(
            model_name='proforma',
            index=models.Index(fields=['statut'], name='gestion_pro_statut_idx'),
        ),
        migrations.AddIndex(
            model_name='proforma',
            index=models.Index(fields=['creancier'], name='gestion_pro_creancier_idx'),
        ),

        # 3. EtatFrais - État des frais à charge du débiteur
        migrations.CreateModel(
            name='EtatFrais',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('numero', models.CharField(help_text='Format : FRAIS-2025-001', max_length=50, unique=True, verbose_name='Numéro état frais')),
                ('date_emission', models.DateField(blank=True, null=True, verbose_name="Date d'émission")),
                ('montant_principal', models.DecimalField(
                    decimal_places=0,
                    default=Decimal('0'),
                    help_text='Montant de la créance initiale',
                    max_digits=15,
                    validators=[django.core.validators.MinValueValidator(Decimal('0'))],
                    verbose_name='Principal dû'
                )),
                ('montant_interets', models.DecimalField(
                    decimal_places=0,
                    default=Decimal('0'),
                    max_digits=15,
                    validators=[django.core.validators.MinValueValidator(Decimal('0'))],
                    verbose_name='Intérêts'
                )),
                ('montant_emoluments', models.DecimalField(
                    decimal_places=0,
                    default=Decimal('0'),
                    max_digits=15,
                    validators=[django.core.validators.MinValueValidator(Decimal('0'))],
                    verbose_name='Émoluments'
                )),
                ('montant_frais_signification', models.DecimalField(
                    decimal_places=0,
                    default=Decimal('0'),
                    max_digits=15,
                    validators=[django.core.validators.MinValueValidator(Decimal('0'))],
                    verbose_name='Frais de signification'
                )),
                ('montant_frais_deplacement', models.DecimalField(
                    decimal_places=0,
                    default=Decimal('0'),
                    max_digits=15,
                    validators=[django.core.validators.MinValueValidator(Decimal('0'))],
                    verbose_name='Frais de déplacement'
                )),
                ('montant_depens', models.DecimalField(
                    decimal_places=0,
                    default=Decimal('0'),
                    max_digits=15,
                    validators=[django.core.validators.MinValueValidator(Decimal('0'))],
                    verbose_name='Dépens'
                )),
                ('montant_accessoires', models.DecimalField(
                    decimal_places=0,
                    default=Decimal('0'),
                    max_digits=15,
                    validators=[django.core.validators.MinValueValidator(Decimal('0'))],
                    verbose_name='Accessoires'
                )),
                ('montant_total', models.DecimalField(
                    decimal_places=0,
                    default=Decimal('0'),
                    help_text='Somme de tous les frais + principal',
                    max_digits=15,
                    validators=[django.core.validators.MinValueValidator(Decimal('0'))],
                    verbose_name='Montant total'
                )),
                ('statut', models.CharField(
                    choices=[
                        ('brouillon', 'Brouillon'),
                        ('emis', 'Émis au débiteur'),
                        ('accepte', 'Accepté'),
                        ('conteste', 'Contesté'),
                        ('paye', 'Payé'),
                        ('ajuste', 'Ajusté'),
                    ],
                    default='brouillon',
                    max_length=20,
                    verbose_name='Statut'
                )),
                ('motif_contestation', models.TextField(blank=True, verbose_name='Motif de contestation')),
                ('date_contestation', models.DateField(blank=True, null=True, verbose_name='Date de contestation')),
                ('montant_paye', models.DecimalField(
                    decimal_places=0,
                    default=Decimal('0'),
                    max_digits=15,
                    validators=[django.core.validators.MinValueValidator(Decimal('0'))],
                    verbose_name='Montant payé'
                )),
                ('date_paiement', models.DateField(blank=True, null=True, verbose_name='Date de paiement')),
                ('observations', models.TextField(blank=True, verbose_name='Observations')),
                ('date_creation', models.DateTimeField(auto_now_add=True, verbose_name='Date de création')),
                ('date_modification', models.DateTimeField(auto_now=True, verbose_name='Date de modification')),
                ('dossier', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='etats_frais', to='gestion.dossier', verbose_name='Dossier')),
                ('debiteur', models.ForeignKey(blank=True, help_text='Partie qui doit payer ces frais', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='etats_frais_recus', to='gestion.partie', verbose_name='Débiteur')),
                ('cree_par', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='etats_frais_crees', to='gestion.utilisateur', verbose_name='Créé par')),
            ],
            options={
                'verbose_name': 'État des frais',
                'verbose_name_plural': 'États des frais',
                'ordering': ['-date_creation'],
            },
        ),
        migrations.AddIndex(
            model_name='etatfrais',
            index=models.Index(fields=['numero'], name='gestion_eta_numero_idx'),
        ),
        migrations.AddIndex(
            model_name='etatfrais',
            index=models.Index(fields=['dossier'], name='gestion_eta_dossier_idx'),
        ),
        migrations.AddIndex(
            model_name='etatfrais',
            index=models.Index(fields=['statut'], name='gestion_eta_statut_idx'),
        ),
    ]
