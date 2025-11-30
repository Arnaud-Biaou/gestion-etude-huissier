# Generated manually for Phase 4 - E-MECeF Billing models
# Structure complète avec ventilation par groupe de taxation

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
        # ═══════════════════════════════════════════════════════════════════════
        # 1. GroupeTaxation - Table de référence E-MECeF
        # ═══════════════════════════════════════════════════════════════════════
        migrations.CreateModel(
            name='GroupeTaxation',
            fields=[
                ('code', models.CharField(
                    max_length=1,
                    choices=[
                        ('A', 'A - EXONÉRÉ (Débours, timbres, enregistrement)'),
                        ('B', 'B - TAXABLE 18% (Honoraires, prestations)'),
                        ('C', 'C - EXPORTATION'),
                        ('D', 'D - TVA RÉGIME EXCEPTION 18%'),
                        ('E', 'E - TPS'),
                        ('F', 'F - RÉSERVÉ'),
                    ],
                    primary_key=True,
                    serialize=False,
                    unique=True,
                    verbose_name='Code E-MECeF'
                )),
                ('libelle', models.CharField(max_length=200, verbose_name='Libellé')),
                ('taux_tva', models.DecimalField(
                    decimal_places=2,
                    default=Decimal('0.00'),
                    max_digits=5,
                    verbose_name='Taux TVA %'
                )),
                ('taxable', models.BooleanField(
                    default=False,
                    help_text="Si True, AIB 3% s'applique",
                    verbose_name='Soumis à AIB'
                )),
            ],
            options={
                'verbose_name': 'Groupe de taxation',
                'verbose_name_plural': 'Groupes de taxation',
            },
        ),

        # ═══════════════════════════════════════════════════════════════════════
        # 2. Données initiales GroupeTaxation
        # ═══════════════════════════════════════════════════════════════════════
        migrations.RunPython(
            code=lambda apps, schema_editor: apps.get_model('gestion', 'GroupeTaxation').objects.bulk_create([
                apps.get_model('gestion', 'GroupeTaxation')(
                    code='A',
                    libelle='Exonéré (débours, timbres, enregistrement)',
                    taux_tva=Decimal('0.00'),
                    taxable=False
                ),
                apps.get_model('gestion', 'GroupeTaxation')(
                    code='B',
                    libelle='Taxable 18% (honoraires, prestations)',
                    taux_tva=Decimal('18.00'),
                    taxable=True
                ),
            ]),
            reverse_code=lambda apps, schema_editor: apps.get_model('gestion', 'GroupeTaxation').objects.filter(
                code__in=['A', 'B']
            ).delete(),
        ),

        # ═══════════════════════════════════════════════════════════════════════
        # 3. ActeDossier - Actes réalisés (version simplifiée)
        # ═══════════════════════════════════════════════════════════════════════
        migrations.CreateModel(
            name='ActeDossier',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('numero_acte', models.CharField(
                    help_text='Format : EXE-2025-001',
                    max_length=50,
                    unique=True,
                    verbose_name="Numéro d'acte"
                )),
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
                ('nombre_feuillets', models.PositiveIntegerField(
                    default=1,
                    help_text='Pour calcul des timbres (1 timbre × 1.200 FCFA par feuillet)',
                    verbose_name='Nombre de feuillets'
                )),
                ('observations', models.TextField(blank=True, verbose_name='Observations')),
                ('date_creation', models.DateTimeField(auto_now_add=True, verbose_name='Date de création')),
                ('date_modification', models.DateTimeField(auto_now=True, verbose_name='Date de modification')),
                ('dossier', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='actes_realises',
                    to='gestion.dossier',
                    verbose_name='Dossier'
                )),
                ('acte_type', models.ForeignKey(
                    blank=True,
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    to='gestion.acteprocedure',
                    verbose_name="Type d'acte (catalogue)"
                )),
                ('document', models.ForeignKey(
                    blank=True,
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='actes_dossier',
                    to='documents.document',
                    verbose_name='Document associé'
                )),
                ('cree_par', models.ForeignKey(
                    on_delete=django.db.models.deletion.PROTECT,
                    related_name='actes_crees',
                    to='gestion.utilisateur',
                    verbose_name='Créé par'
                )),
                ('destinataires', models.ManyToManyField(
                    blank=True,
                    related_name='actes_recus',
                    to='gestion.partie',
                    verbose_name='Destinataires'
                )),
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

        # ═══════════════════════════════════════════════════════════════════════
        # 4. Modification LigneFacture - Ajout champs E-MECeF
        # ═══════════════════════════════════════════════════════════════════════
        migrations.AddField(
            model_name='lignefacture',
            name='acte_dossier',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='lignes_facture',
                to='gestion.actedossier',
                verbose_name='Acte associé'
            ),
        ),
        migrations.AddField(
            model_name='lignefacture',
            name='numero_ligne',
            field=models.PositiveIntegerField(default=1, verbose_name='Numéro de ligne'),
        ),
        migrations.AddField(
            model_name='lignefacture',
            name='ordre',
            field=models.PositiveIntegerField(default=0, verbose_name="Ordre d'affichage"),
        ),
        migrations.AddField(
            model_name='lignefacture',
            name='montant_ht_groupe_a',
            field=models.DecimalField(
                decimal_places=0,
                default=Decimal('0'),
                help_text='Timbres + Enregistrement + Débours (auto-calculé)',
                max_digits=15,
                validators=[django.core.validators.MinValueValidator(Decimal('0'))],
                verbose_name='HT Groupe A (Exonéré)'
            ),
        ),
        migrations.AddField(
            model_name='lignefacture',
            name='montant_ht_groupe_b',
            field=models.DecimalField(
                decimal_places=0,
                default=Decimal('0'),
                help_text='Honoraires (auto-calculé)',
                max_digits=15,
                validators=[django.core.validators.MinValueValidator(Decimal('0'))],
                verbose_name='HT Groupe B (Taxable)'
            ),
        ),
        migrations.AddField(
            model_name='lignefacture',
            name='montant_tva_groupe_b',
            field=models.DecimalField(
                decimal_places=0,
                default=Decimal('0'),
                help_text='18% × montant_ht_groupe_b (auto-calculé)',
                max_digits=15,
                validators=[django.core.validators.MinValueValidator(Decimal('0'))],
                verbose_name='TVA sur Groupe B'
            ),
        ),
        migrations.AddField(
            model_name='lignefacture',
            name='montant_total_ht',
            field=models.DecimalField(
                decimal_places=0,
                default=Decimal('0'),
                help_text='Groupe A + Groupe B (auto-calculé)',
                max_digits=15,
                validators=[django.core.validators.MinValueValidator(Decimal('0'))],
                verbose_name='Total HT'
            ),
        ),
        migrations.AddField(
            model_name='lignefacture',
            name='montant_total_ttc',
            field=models.DecimalField(
                decimal_places=0,
                default=Decimal('0'),
                help_text='Total HT + TVA (auto-calculé)',
                max_digits=15,
                validators=[django.core.validators.MinValueValidator(Decimal('0'))],
                verbose_name='Total TTC'
            ),
        ),
        migrations.AlterUniqueTogether(
            name='lignefacture',
            unique_together={('facture', 'numero_ligne')},
        ),
        migrations.AddIndex(
            model_name='lignefacture',
            index=models.Index(fields=['facture', 'ordre'], name='gestion_lig_facture_ordre_idx'),
        ),

        # ═══════════════════════════════════════════════════════════════════════
        # 5. VentilationLigneFacture - Détail par groupe taxation
        # ═══════════════════════════════════════════════════════════════════════
        migrations.CreateModel(
            name='VentilationLigneFacture',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nature', models.CharField(
                    choices=[
                        ('honoraires', 'Honoraires'),
                        ('timbre', 'Timbre fiscal'),
                        ('enregistrement', "Enregistrement de l'acte"),
                        ('frais_greffe', 'Frais de greffe'),
                        ('frais_transport', 'Frais de transport'),
                        ('autre_debours', 'Autre débours'),
                    ],
                    max_length=50,
                    verbose_name='Nature de la ventilation'
                )),
                ('description', models.CharField(max_length=200, verbose_name='Description')),
                ('montant_ht', models.DecimalField(
                    decimal_places=0,
                    max_digits=15,
                    validators=[django.core.validators.MinValueValidator(Decimal('0'))],
                    verbose_name='Montant HT'
                )),
                ('montant_tva', models.DecimalField(
                    decimal_places=0,
                    default=Decimal('0'),
                    help_text='Auto-calculé',
                    max_digits=15,
                    validators=[django.core.validators.MinValueValidator(Decimal('0'))],
                    verbose_name='Montant TVA'
                )),
                ('montant_ttc', models.DecimalField(
                    decimal_places=0,
                    default=Decimal('0'),
                    help_text='HT + TVA',
                    max_digits=15,
                    validators=[django.core.validators.MinValueValidator(Decimal('0'))],
                    verbose_name='Montant TTC'
                )),
                ('ordre', models.PositiveIntegerField(default=0, verbose_name="Ordre d'affichage")),
                ('ligne_facture', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='ventilations',
                    to='gestion.lignefacture',
                    verbose_name='Ligne facture'
                )),
                ('groupe_taxation', models.ForeignKey(
                    default='A',
                    on_delete=django.db.models.deletion.PROTECT,
                    to='gestion.groupetaxation',
                    verbose_name='Groupe de taxation'
                )),
            ],
            options={
                'verbose_name': 'Ventilation ligne facture',
                'verbose_name_plural': 'Ventilations lignes factures',
                'ordering': ['ordre'],
            },
        ),
        migrations.AddIndex(
            model_name='ventilationlignefacture',
            index=models.Index(fields=['ligne_facture', 'groupe_taxation'], name='gestion_ven_ligne_grp_idx'),
        ),

        # ═══════════════════════════════════════════════════════════════════════
        # 6. CreanceAIB - Suivi des retenues AIB 3%
        # ═══════════════════════════════════════════════════════════════════════
        migrations.CreateModel(
            name='CreanceAIB',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('montant_base_aib', models.DecimalField(
                    decimal_places=0,
                    help_text='Somme des HT Groupe B (taxables)',
                    max_digits=15,
                    validators=[django.core.validators.MinValueValidator(Decimal('0'))],
                    verbose_name='Montant base AIB'
                )),
                ('taux_aib', models.DecimalField(
                    decimal_places=2,
                    default=Decimal('3.00'),
                    max_digits=5,
                    verbose_name='Taux AIB %'
                )),
                ('montant_aib', models.DecimalField(
                    decimal_places=0,
                    default=Decimal('0'),
                    help_text='base_aib × taux_aib',
                    max_digits=15,
                    validators=[django.core.validators.MinValueValidator(Decimal('0'))],
                    verbose_name='Montant AIB retenu'
                )),
                ('statut', models.CharField(
                    choices=[
                        ('genere', 'Générée (en attente)'),
                        ('retenue', 'Retenue par client'),
                        ('recupere', 'Récupérée (impôts)'),
                        ('annule', 'Annulée'),
                    ],
                    default='genere',
                    max_length=20,
                    verbose_name='Statut'
                )),
                ('attestation_aib', models.CharField(
                    blank=True,
                    max_length=100,
                    verbose_name='N° attestation AIB'
                )),
                ('date_retenue', models.DateField(blank=True, null=True, verbose_name='Date de retenue')),
                ('date_recuperation', models.DateField(blank=True, null=True, verbose_name='Date de récupération')),
                ('date_creation', models.DateTimeField(auto_now_add=True, verbose_name='Date de création')),
                ('facture', models.OneToOneField(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='creance_aib',
                    to='gestion.facture',
                    verbose_name='Facture'
                )),
            ],
            options={
                'verbose_name': 'Créance AIB',
                'verbose_name_plural': 'Créances AIB',
            },
        ),

        # ═══════════════════════════════════════════════════════════════════════
        # 7. Proforma - Devis avant facturation
        # ═══════════════════════════════════════════════════════════════════════
        migrations.CreateModel(
            name='Proforma',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('numero', models.CharField(
                    help_text='Format : PRO-2025-001',
                    max_length=50,
                    unique=True,
                    verbose_name='Numéro proforma'
                )),
                ('date_emission', models.DateField(
                    default=django.utils.timezone.now,
                    verbose_name="Date d'émission"
                )),
                ('date_validite', models.DateField(
                    help_text='Proforma expire après cette date',
                    verbose_name='Date de validité'
                )),
                ('client_nom', models.CharField(
                    help_text='Nom du client si pas encore créancier',
                    max_length=200,
                    verbose_name='Nom du client'
                )),
                ('client_adresse', models.TextField(blank=True, verbose_name='Adresse du client')),
                ('client_telephone', models.CharField(blank=True, max_length=50, verbose_name='Téléphone')),
                ('client_email', models.EmailField(blank=True, max_length=254, verbose_name='Email')),
                ('client_ifu', models.CharField(blank=True, max_length=50, verbose_name='IFU client')),
                ('titre', models.CharField(
                    help_text='Ex: Recouvrement de créance 5M FCFA',
                    max_length=200,
                    verbose_name='Titre de la prestation'
                )),
                ('description', models.TextField(verbose_name='Description détaillée')),
                ('montant_ht', models.DecimalField(
                    decimal_places=0,
                    max_digits=15,
                    validators=[django.core.validators.MinValueValidator(Decimal('0'))],
                    verbose_name='Montant HT'
                )),
                ('taux_tva', models.DecimalField(
                    decimal_places=2,
                    default=Decimal('18.00'),
                    max_digits=5,
                    verbose_name='Taux TVA %'
                )),
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
                ('delai_paiement', models.PositiveIntegerField(
                    default=15,
                    verbose_name='Délai de paiement (jours)'
                )),
                ('observations', models.TextField(blank=True, verbose_name='Observations')),
                ('date_creation', models.DateTimeField(auto_now_add=True, verbose_name='Date de création')),
                ('date_modification', models.DateTimeField(auto_now=True, verbose_name='Date de modification')),
                ('creancier', models.ForeignKey(
                    blank=True,
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='proformas',
                    to='gestion.creancier',
                    verbose_name='Créancier'
                )),
                ('dossier', models.ForeignKey(
                    blank=True,
                    help_text='Rempli une fois la proforma acceptée',
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='proformas',
                    to='gestion.dossier',
                    verbose_name='Dossier créé'
                )),
                ('facture', models.OneToOneField(
                    blank=True,
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='proforma_origine',
                    to='gestion.facture',
                    verbose_name='Facture générée'
                )),
                ('cree_par', models.ForeignKey(
                    on_delete=django.db.models.deletion.PROTECT,
                    related_name='proformas_creees',
                    to='gestion.utilisateur',
                    verbose_name='Créé par'
                )),
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

        # ═══════════════════════════════════════════════════════════════════════
        # 8. EtatFrais - État des frais à charge du débiteur
        # ═══════════════════════════════════════════════════════════════════════
        migrations.CreateModel(
            name='EtatFrais',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('numero', models.CharField(
                    help_text='Format : FRAIS-2025-001',
                    max_length=50,
                    unique=True,
                    verbose_name='Numéro état frais'
                )),
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
                ('dossier', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='etats_frais',
                    to='gestion.dossier',
                    verbose_name='Dossier'
                )),
                ('debiteur', models.ForeignKey(
                    blank=True,
                    help_text='Partie qui doit payer ces frais',
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='etats_frais_recus',
                    to='gestion.partie',
                    verbose_name='Débiteur'
                )),
                ('cree_par', models.ForeignKey(
                    on_delete=django.db.models.deletion.PROTECT,
                    related_name='etats_frais_crees',
                    to='gestion.utilisateur',
                    verbose_name='Créé par'
                )),
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
