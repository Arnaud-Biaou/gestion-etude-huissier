"""
Modèles du module Recouvrement de Créances
"""

from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from decimal import Decimal
import uuid


# ═══════════════════════════════════════════════════════════════
# CONSTANTES - CHOIX POUR LES CHAMPS
# ═══════════════════════════════════════════════════════════════

MODE_FACTURATION_CHOICES = [
    ('standard', 'Standard - Imputation automatique'),
    ('reserve', 'Réservé - Imputation différée'),
    ('banque', 'Mode Banque - Reversement total + Facture'),
]

TYPE_PAIEMENT_CHOICES = [
    ('especes', 'Espèces'),
    ('cheque', 'Chèque'),
    ('virement', 'Virement'),
    ('mobile', 'Mobile Money'),
    ('autre', 'Autre'),
]

IMPUTATION_CHOICES = [
    ('frais', 'Frais'),
    ('emoluments', 'Émoluments'),
    ('interets', 'Intérêts'),
    ('principal', 'Principal'),
]


class DossierRecouvrement(models.Model):
    """
    Dossier de recouvrement de créances
    Complète le modèle Dossier de gestion avec des informations spécifiques
    """
    STATUT_CHOICES = [
        ('en_cours', 'En cours'),
        ('suspendu', 'Suspendu'),
        ('cloture', 'Clôturé'),
    ]

    TYPE_RECOUVREMENT_CHOICES = [
        ('amiable', 'Recouvrement amiable'),
        ('force', 'Recouvrement forcé'),
    ]

    MOTIF_CLOTURE_CHOICES = [
        ('recouvre', 'Créance recouvrée'),
        ('irrecoverable', 'Créance irrécouvrable'),
        ('abandon', 'Abandon par le créancier'),
        ('prescription', 'Prescription'),
        ('transaction', 'Transaction'),
        ('autre', 'Autre'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    reference = models.CharField(max_length=50, unique=True, verbose_name="Référence")

    # Lien avec le créancier
    creancier = models.ForeignKey(
        'gestion.Creancier',
        on_delete=models.PROTECT,
        related_name='dossiers_recouvrement',
        verbose_name="Créancier"
    )

    # Lien avec le débiteur
    debiteur = models.ForeignKey(
        'gestion.Partie',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='dossiers_debiteur',
        verbose_name="Débiteur"
    )

    # LIEN VERS LE DOSSIER JURIDIQUE PRINCIPAL
    dossier_principal = models.ForeignKey(
        'gestion.Dossier',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='dossiers_recouvrement',
        verbose_name="Dossier juridique principal",
        help_text="Dossier principal de l'étude lié à ce recouvrement"
    )

    # Type et statut
    type_recouvrement = models.CharField(
        max_length=20,
        choices=TYPE_RECOUVREMENT_CHOICES,
        default='amiable',
        verbose_name="Type de recouvrement"
    )
    statut = models.CharField(
        max_length=20,
        choices=STATUT_CHOICES,
        default='en_cours',
        verbose_name="Statut"
    )
    motif_cloture = models.CharField(
        max_length=20,
        choices=MOTIF_CLOTURE_CHOICES,
        blank=True,
        verbose_name="Motif de clôture"
    )

    # Montants
    montant_principal = models.DecimalField(
        max_digits=15,
        decimal_places=0,
        default=0,
        verbose_name="Montant principal"
    )
    montant_interets = models.DecimalField(
        max_digits=15,
        decimal_places=0,
        default=0,
        verbose_name="Intérêts"
    )
    frais_procedure = models.DecimalField(
        max_digits=15,
        decimal_places=0,
        default=0,
        verbose_name="Frais de procédure"
    )
    emoluments = models.DecimalField(
        max_digits=15,
        decimal_places=0,
        default=0,
        verbose_name="Émoluments"
    )
    honoraires_amiable = models.DecimalField(
        max_digits=15,
        decimal_places=0,
        default=0,
        verbose_name="Honoraires (phase amiable)"
    )

    # Encaissements et reversements
    montant_encaisse = models.DecimalField(
        max_digits=15,
        decimal_places=0,
        default=0,
        verbose_name="Montant encaissé"
    )
    montant_reverse = models.DecimalField(
        max_digits=15,
        decimal_places=0,
        default=0,
        verbose_name="Montant reversé"
    )

    # Mode de facturation et imputation
    mode_facturation = models.CharField(
        max_length=20,
        choices=MODE_FACTURATION_CHOICES,
        default='standard',
        verbose_name="Mode de facturation",
        help_text="Standard=imputation auto, Réservé=différé, Banque=reversement total"
    )

    # Frais et émoluments calculés
    frais_engages = models.DecimalField(
        max_digits=15,
        decimal_places=0,
        default=0,
        verbose_name="Frais engagés"
    )
    emoluments_calcules = models.DecimalField(
        max_digits=15,
        decimal_places=0,
        default=0,
        verbose_name="Émoluments calculés"
    )

    # Montants déjà imputés (pour suivi des paiements)
    frais_imputes = models.DecimalField(
        max_digits=15,
        decimal_places=0,
        default=0,
        verbose_name="Frais déjà imputés"
    )
    emoluments_imputes = models.DecimalField(
        max_digits=15,
        decimal_places=0,
        default=0,
        verbose_name="Émoluments déjà imputés"
    )
    interets_imputes = models.DecimalField(
        max_digits=15,
        decimal_places=0,
        default=0,
        verbose_name="Intérêts déjà imputés"
    )
    principal_impute = models.DecimalField(
        max_digits=15,
        decimal_places=0,
        default=0,
        verbose_name="Principal déjà imputé"
    )

    # Total reversé au créancier (cumulé)
    total_reverse = models.DecimalField(
        max_digits=15,
        decimal_places=0,
        default=0,
        verbose_name="Total reversé au créancier"
    )

    # Dates
    date_ouverture = models.DateField(
        default=timezone.now,
        verbose_name="Date d'ouverture"
    )
    date_effet_interets = models.DateField(
        null=True,
        blank=True,
        verbose_name="Date effet intérêts"
    )
    date_decision_executoire = models.DateField(
        null=True,
        blank=True,
        verbose_name="Date décision exécutoire"
    )
    date_cloture = models.DateField(
        null=True,
        blank=True,
        verbose_name="Date de clôture"
    )

    # Suivi
    derniere_action = models.CharField(
        max_length=200,
        blank=True,
        verbose_name="Dernière action"
    )
    prochaine_etape = models.CharField(
        max_length=200,
        blank=True,
        verbose_name="Prochaine étape"
    )

    # Métadonnées
    observations = models.TextField(blank=True, verbose_name="Observations")
    cree_par = models.ForeignKey(
        'gestion.Utilisateur',
        on_delete=models.SET_NULL,
        null=True,
        related_name='dossiers_recouvrement_crees'
    )
    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-date_ouverture', '-date_creation']
        verbose_name = "Dossier de recouvrement"
        verbose_name_plural = "Dossiers de recouvrement"

    def __str__(self):
        return f"{self.reference} - {self.creancier.nom if self.creancier else 'N/A'}"

    @property
    def montant_total(self):
        """Calcule le montant total de la créance"""
        return (
            self.montant_principal +
            self.montant_interets +
            self.frais_procedure +
            self.emoluments
        )

    @property
    def solde_restant(self):
        """Calcule le solde restant dû"""
        return self.montant_total - self.montant_encaisse

    @property
    def taux_recouvrement(self):
        """Calcule le taux de recouvrement"""
        if self.montant_total > 0:
            return (self.montant_encaisse / self.montant_total) * 100
        return Decimal('0')

    # ═══════════════════════════════════════════════════════════════
    # MÉTHODES DE CALCUL DES MONTANTS RESTANTS
    # ═══════════════════════════════════════════════════════════════

    def get_frais_restants(self):
        """Retourne les frais restants à imputer"""
        return max(Decimal('0'), self.frais_engages - self.frais_imputes)

    def get_emoluments_restants(self):
        """Retourne les émoluments restants à imputer"""
        return max(Decimal('0'), self.emoluments_calcules - self.emoluments_imputes)

    def get_interets_restants(self):
        """Retourne les intérêts restants à imputer"""
        return max(Decimal('0'), self.montant_interets - self.interets_imputes)

    def get_principal_restant(self):
        """Retourne le principal restant à imputer"""
        return max(Decimal('0'), self.montant_principal - self.principal_impute)

    def get_total_du(self):
        """Retourne le total restant dû (tous types confondus)"""
        return (
            self.get_frais_restants() +
            self.get_emoluments_restants() +
            self.get_interets_restants() +
            self.get_principal_restant()
        )

    def get_total_paye(self):
        """Retourne le total des paiements reçus"""
        from django.db.models import Sum
        return self.paiements.aggregate(total=Sum('montant'))['total'] or Decimal('0')

    def get_total_a_reverser(self):
        """Retourne le total à reverser au créancier (non encore reversé)"""
        from django.db.models import Sum
        return self.paiements.filter(est_reverse=False).aggregate(
            total=Sum('montant_a_reverser')
        )['total'] or Decimal('0')

    def get_montant_reserve_total(self):
        """Retourne le total des montants réservés (non imputés)"""
        from django.db.models import Sum
        return self.paiements.aggregate(
            total=Sum('montant_reserve')
        )['total'] or Decimal('0')

    def actualiser_imputations(self):
        """
        Met à jour les totaux d'imputation à partir des paiements.
        À appeler après modification des paiements.
        """
        from django.db.models import Sum

        totaux = self.paiements.aggregate(
            frais=Sum('impute_frais'),
            emoluments=Sum('impute_emoluments'),
            interets=Sum('impute_interets'),
            principal=Sum('impute_principal'),
            reverse=Sum('montant_a_reverser'),
        )

        self.frais_imputes = totaux['frais'] or Decimal('0')
        self.emoluments_imputes = totaux['emoluments'] or Decimal('0')
        self.interets_imputes = totaux['interets'] or Decimal('0')
        self.principal_impute = totaux['principal'] or Decimal('0')

        # Calculer le total reversé
        total_reverse = self.paiements.filter(est_reverse=True).aggregate(
            total=Sum('montant_a_reverser')
        )['total'] or Decimal('0')
        self.total_reverse = total_reverse

        self.save(update_fields=[
            'frais_imputes', 'emoluments_imputes',
            'interets_imputes', 'principal_impute', 'total_reverse'
        ])


class PointGlobalCreancier(models.Model):
    """Point récapitulatif multi-dossiers pour un créancier"""

    STATUT_CHOICES = [
        ('brouillon', 'Brouillon'),
        ('genere', 'Généré'),
        ('envoye', 'Envoyé au créancier'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    creancier = models.ForeignKey(
        'gestion.Creancier',
        on_delete=models.CASCADE,
        related_name='points_globaux_recouvrement',
        verbose_name="Créancier"
    )
    date_generation = models.DateTimeField(auto_now_add=True)
    periode_debut = models.DateField(verbose_name="Début période")
    periode_fin = models.DateField(verbose_name="Fin période")

    # Filtres appliqués
    inclure_tous_dossiers = models.BooleanField(default=True)
    inclure_en_cours = models.BooleanField(default=True)
    inclure_clotures = models.BooleanField(default=True)
    inclure_amiable = models.BooleanField(default=True)
    inclure_force = models.BooleanField(default=True)
    dossiers_selectionnes = models.ManyToManyField(
        'DossierRecouvrement',
        blank=True,
        related_name='points_globaux_inclus'
    )

    # Statistiques calculées
    nombre_dossiers = models.PositiveIntegerField(default=0)
    nombre_en_cours = models.PositiveIntegerField(default=0)
    nombre_clotures_succes = models.PositiveIntegerField(default=0)
    nombre_clotures_echec = models.PositiveIntegerField(default=0)
    nombre_amiable = models.PositiveIntegerField(default=0)
    nombre_force = models.PositiveIntegerField(default=0)

    # Montants
    total_creances = models.DecimalField(max_digits=15, decimal_places=0, default=0)
    total_encaisse = models.DecimalField(max_digits=15, decimal_places=0, default=0)
    total_reverse = models.DecimalField(max_digits=15, decimal_places=0, default=0)
    total_reste_du = models.DecimalField(max_digits=15, decimal_places=0, default=0)
    taux_recouvrement = models.DecimalField(max_digits=5, decimal_places=2, default=0)

    # Honoraires
    total_frais_procedure = models.DecimalField(max_digits=15, decimal_places=0, default=0)
    total_emoluments = models.DecimalField(max_digits=15, decimal_places=0, default=0)
    total_honoraires_amiable = models.DecimalField(max_digits=15, decimal_places=0, default=0)
    total_retenu = models.DecimalField(max_digits=15, decimal_places=0, default=0)

    # Document
    document_pdf = models.FileField(upload_to='points_globaux/', null=True, blank=True)
    observations = models.TextField(blank=True)

    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default='brouillon')
    genere_par = models.ForeignKey(
        'gestion.Utilisateur',
        on_delete=models.SET_NULL,
        null=True
    )

    class Meta:
        ordering = ['-date_generation']
        verbose_name = "Point global créancier"
        verbose_name_plural = "Points globaux créanciers"

    def __str__(self):
        return f"Point {self.creancier} - {self.date_generation.strftime('%d/%m/%Y')}"

    def calculer_statistiques(self):
        """Calcule toutes les statistiques à partir des dossiers"""
        from django.db.models import Sum, Q

        # Récupérer les dossiers selon les filtres
        dossiers = self.get_dossiers_filtres()

        # Compter par statut
        self.nombre_dossiers = dossiers.count()
        self.nombre_en_cours = dossiers.filter(statut='en_cours').count()
        self.nombre_clotures_succes = dossiers.filter(statut='cloture', motif_cloture='recouvre').count()
        self.nombre_clotures_echec = dossiers.filter(statut='cloture').exclude(motif_cloture='recouvre').count()
        self.nombre_amiable = dossiers.filter(type_recouvrement='amiable').count()
        self.nombre_force = dossiers.filter(type_recouvrement='force').count()

        # Calculer les montants
        totaux = dossiers.aggregate(
            creances=Sum('montant_principal'),
            encaisse=Sum('montant_encaisse'),
            reverse=Sum('montant_reverse'),
        )

        self.total_creances = totaux['creances'] or 0
        self.total_encaisse = totaux['encaisse'] or 0
        self.total_reverse = totaux['reverse'] or 0
        self.total_reste_du = self.total_creances - self.total_encaisse

        if self.total_creances > 0:
            self.taux_recouvrement = (self.total_encaisse / self.total_creances) * 100

        # Calculer les honoraires
        totaux_honoraires = dossiers.aggregate(
            frais=Sum('frais_procedure'),
            emoluments=Sum('emoluments'),
            honoraires=Sum('honoraires_amiable'),
        )

        self.total_frais_procedure = totaux_honoraires['frais'] or 0
        self.total_emoluments = totaux_honoraires['emoluments'] or 0
        self.total_honoraires_amiable = totaux_honoraires['honoraires'] or 0
        self.total_retenu = self.total_frais_procedure + self.total_emoluments + self.total_honoraires_amiable

        self.save()

    def get_dossiers_filtres(self):
        """Retourne les dossiers selon les filtres configurés"""
        if not self.inclure_tous_dossiers and self.dossiers_selectionnes.exists():
            return self.dossiers_selectionnes.all()

        dossiers = DossierRecouvrement.objects.filter(creancier=self.creancier)

        # Filtre par période
        dossiers = dossiers.filter(
            date_ouverture__gte=self.periode_debut,
            date_ouverture__lte=self.periode_fin
        )

        # Filtre par statut
        statuts = []
        if self.inclure_en_cours:
            statuts.append('en_cours')
        if self.inclure_clotures:
            statuts.append('cloture')
        if statuts:
            dossiers = dossiers.filter(statut__in=statuts)

        # Filtre par type
        types = []
        if self.inclure_amiable:
            types.append('amiable')
        if self.inclure_force:
            types.append('force')
        if types:
            dossiers = dossiers.filter(type_recouvrement__in=types)

        return dossiers

    def to_dict(self):
        """Convertit l'objet en dictionnaire"""
        return {
            'id': str(self.id),
            'creancier_id': self.creancier_id,
            'creancier_nom': self.creancier.nom if self.creancier else '',
            'date_generation': self.date_generation.isoformat() if self.date_generation else None,
            'periode_debut': self.periode_debut.isoformat() if self.periode_debut else None,
            'periode_fin': self.periode_fin.isoformat() if self.periode_fin else None,
            'nombre_dossiers': self.nombre_dossiers,
            'nombre_en_cours': self.nombre_en_cours,
            'nombre_clotures_succes': self.nombre_clotures_succes,
            'nombre_clotures_echec': self.nombre_clotures_echec,
            'nombre_amiable': self.nombre_amiable,
            'nombre_force': self.nombre_force,
            'total_creances': str(self.total_creances),
            'total_encaisse': str(self.total_encaisse),
            'total_reverse': str(self.total_reverse),
            'total_reste_du': str(self.total_reste_du),
            'taux_recouvrement': str(self.taux_recouvrement),
            'total_frais_procedure': str(self.total_frais_procedure),
            'total_emoluments': str(self.total_emoluments),
            'total_honoraires_amiable': str(self.total_honoraires_amiable),
            'total_retenu': str(self.total_retenu),
            'statut': self.statut,
            'document_pdf_url': self.document_pdf.url if self.document_pdf else None,
            'observations': self.observations,
        }


class EnvoiAutomatiquePoint(models.Model):
    """Configuration d'envoi automatique des points globaux"""

    FREQUENCE_CHOICES = [
        ('hebdomadaire', 'Hebdomadaire'),
        ('bimensuel', 'Bimensuel'),
        ('mensuel', 'Mensuel'),
        ('trimestriel', 'Trimestriel'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    creancier = models.OneToOneField(
        'gestion.Creancier',
        on_delete=models.CASCADE,
        related_name='config_envoi_point'
    )
    actif = models.BooleanField(default=False)
    frequence = models.CharField(max_length=20, choices=FREQUENCE_CHOICES, default='mensuel')
    jour_envoi = models.PositiveSmallIntegerField(
        default=1,
        help_text="Jour du mois (1-28)"
    )
    destinataires = models.TextField(
        help_text="Emails séparés par des virgules"
    )

    dernier_envoi = models.DateTimeField(null=True, blank=True)
    prochain_envoi = models.DateTimeField(null=True, blank=True)

    # Filtres par défaut
    inclure_en_cours = models.BooleanField(default=True)
    inclure_clotures = models.BooleanField(default=False)

    class Meta:
        verbose_name = "Configuration envoi automatique"
        verbose_name_plural = "Configurations envois automatiques"

    def __str__(self):
        return f"Envoi auto {self.creancier} - {self.get_frequence_display()}"

    def get_liste_destinataires(self):
        """Retourne la liste des emails destinataires"""
        if not self.destinataires:
            return []
        return [email.strip() for email in self.destinataires.split(',') if email.strip()]

    def to_dict(self):
        return {
            'id': str(self.id),
            'creancier_id': self.creancier_id,
            'creancier_nom': self.creancier.nom if self.creancier else '',
            'actif': self.actif,
            'frequence': self.frequence,
            'frequence_display': self.get_frequence_display(),
            'jour_envoi': self.jour_envoi,
            'destinataires': self.get_liste_destinataires(),
            'dernier_envoi': self.dernier_envoi.isoformat() if self.dernier_envoi else None,
            'prochain_envoi': self.prochain_envoi.isoformat() if self.prochain_envoi else None,
            'inclure_en_cours': self.inclure_en_cours,
            'inclure_clotures': self.inclure_clotures,
        }


# ═══════════════════════════════════════════════════════════════
# MODÈLE : PAIEMENT RECOUVREMENT
# Gère les encaissements avec logique d'imputation
# ═══════════════════════════════════════════════════════════════

class PaiementRecouvrement(models.Model):
    """
    Paiement reçu sur un dossier de recouvrement.
    Gère l'imputation selon le mode (amiable/forcé) et les préférences.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    dossier = models.ForeignKey(
        'DossierRecouvrement',
        on_delete=models.CASCADE,
        related_name='paiements'
    )

    # Informations du paiement
    date_paiement = models.DateField(verbose_name="Date du paiement")
    montant = models.DecimalField(
        max_digits=15,
        decimal_places=0,
        verbose_name="Montant reçu"
    )
    mode_paiement = models.CharField(
        max_length=20,
        choices=TYPE_PAIEMENT_CHOICES,
        default='especes'
    )
    reference_paiement = models.CharField(
        max_length=100,
        blank=True,
        help_text="N° chèque, référence virement, etc."
    )

    # Imputation détaillée
    impute_frais = models.DecimalField(
        max_digits=15,
        decimal_places=0,
        default=0,
        verbose_name="Imputé sur frais"
    )
    impute_emoluments = models.DecimalField(
        max_digits=15,
        decimal_places=0,
        default=0,
        verbose_name="Imputé sur émoluments"
    )
    impute_interets = models.DecimalField(
        max_digits=15,
        decimal_places=0,
        default=0,
        verbose_name="Imputé sur intérêts"
    )
    impute_principal = models.DecimalField(
        max_digits=15,
        decimal_places=0,
        default=0,
        verbose_name="Imputé sur principal"
    )

    # Montant réservé (non imputé, pour imputation ultérieure)
    montant_reserve = models.DecimalField(
        max_digits=15,
        decimal_places=0,
        default=0,
        verbose_name="Montant réservé (frais/émoluments différés)"
    )

    # Montant à reverser au créancier
    montant_a_reverser = models.DecimalField(
        max_digits=15,
        decimal_places=0,
        default=0,
        verbose_name="Montant à reverser au créancier"
    )

    # Reversement effectué
    est_reverse = models.BooleanField(default=False, verbose_name="Reversé au créancier")
    date_reversement = models.DateField(null=True, blank=True)
    reference_reversement = models.CharField(max_length=100, blank=True)

    # Métadonnées
    observations = models.TextField(blank=True)
    cree_par = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='paiements_recouvrement_crees'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Paiement recouvrement"
        verbose_name_plural = "Paiements recouvrement"
        ordering = ['-date_paiement', '-created_at']

    def __str__(self):
        return f"Paiement {self.montant:,.0f} FCFA du {self.date_paiement} - {self.dossier.reference}"

    def save(self, *args, **kwargs):
        """Calcule automatiquement l'imputation si non définie"""
        # Si c'est un nouveau paiement sans imputation définie
        if not self.pk and self.montant > 0:
            total_impute = (
                self.impute_frais +
                self.impute_emoluments +
                self.impute_interets +
                self.impute_principal +
                self.montant_reserve +
                self.montant_a_reverser
            )
            # Si rien n'est imputé, calculer automatiquement
            if total_impute == 0:
                self._calculer_imputation_automatique()

        super().save(*args, **kwargs)

        # Mettre à jour les totaux du dossier
        self.dossier.actualiser_imputations()

    def _calculer_imputation_automatique(self):
        """
        Calcule l'imputation automatique selon le mode du dossier.

        AMIABLE : Tout va au créancier (frais à sa charge séparément)
        FORCÉ STANDARD : Frais → Émoluments → Intérêts → Principal
        FORCÉ RÉSERVÉ : Différé, l'huissier décide plus tard
        BANQUE : Tout au créancier, facture séparée
        """
        dossier = self.dossier
        mode = dossier.mode_facturation

        if mode == 'banque':
            # Mode Banque : tout à reverser, facture séparée
            self.montant_a_reverser = self.montant
            return

        if dossier.type_recouvrement == 'amiable':
            # Amiable : frais à charge du créancier, tout reversé
            self.montant_a_reverser = self.montant
            return

        # Recouvrement forcé
        if mode == 'reserve':
            # Mode réservé : on garde pour imputation ultérieure
            self.montant_reserve = self.montant
            return

        # Mode standard forcé : imputation dans l'ordre légal
        restant = self.montant

        # 1. Frais restants dus
        frais_dus = dossier.get_frais_restants()
        if restant > 0 and frais_dus > 0:
            imputation = min(restant, frais_dus)
            self.impute_frais = imputation
            restant -= imputation

        # 2. Émoluments restants dus
        emoluments_dus = dossier.get_emoluments_restants()
        if restant > 0 and emoluments_dus > 0:
            imputation = min(restant, emoluments_dus)
            self.impute_emoluments = imputation
            restant -= imputation

        # 3. Intérêts restants dus
        interets_dus = dossier.get_interets_restants()
        if restant > 0 and interets_dus > 0:
            imputation = min(restant, interets_dus)
            self.impute_interets = imputation
            restant -= imputation

        # 4. Principal restant dû
        principal_du = dossier.get_principal_restant()
        if restant > 0 and principal_du > 0:
            imputation = min(restant, principal_du)
            self.impute_principal = imputation
            restant -= imputation

        # 5. Excédent éventuel → à reverser
        if restant > 0:
            self.montant_a_reverser = restant

    def get_total_impute(self):
        """Retourne le total imputé"""
        return (
            self.impute_frais +
            self.impute_emoluments +
            self.impute_interets +
            self.impute_principal
        )

    def to_dict(self):
        """Convertit l'objet en dictionnaire"""
        return {
            'id': str(self.id),
            'dossier_id': str(self.dossier_id),
            'dossier_reference': self.dossier.reference,
            'date_paiement': self.date_paiement.isoformat() if self.date_paiement else None,
            'montant': str(self.montant),
            'mode_paiement': self.mode_paiement,
            'mode_paiement_display': self.get_mode_paiement_display(),
            'reference_paiement': self.reference_paiement,
            'impute_frais': str(self.impute_frais),
            'impute_emoluments': str(self.impute_emoluments),
            'impute_interets': str(self.impute_interets),
            'impute_principal': str(self.impute_principal),
            'montant_reserve': str(self.montant_reserve),
            'montant_a_reverser': str(self.montant_a_reverser),
            'est_reverse': self.est_reverse,
            'date_reversement': self.date_reversement.isoformat() if self.date_reversement else None,
            'reference_reversement': self.reference_reversement,
            'observations': self.observations,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }


# ═══════════════════════════════════════════════════════════════
# MODÈLE : IMPUTATION MANUELLE
# Permet d'imputer manuellement les montants réservés
# ═══════════════════════════════════════════════════════════════

class ImputationManuelle(models.Model):
    """
    Imputation manuelle des montants réservés.
    Permet à l'huissier de décider quand imputer les frais/émoluments réservés.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    paiement = models.ForeignKey(
        PaiementRecouvrement,
        on_delete=models.CASCADE,
        related_name='imputations_manuelles'
    )

    date_imputation = models.DateField(auto_now_add=True)

    type_imputation = models.CharField(
        max_length=20,
        choices=IMPUTATION_CHOICES
    )
    montant = models.DecimalField(max_digits=15, decimal_places=0)

    observations = models.TextField(blank=True)
    cree_par = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Imputation manuelle"
        verbose_name_plural = "Imputations manuelles"
        ordering = ['-date_imputation']

    def __str__(self):
        return f"Imputation {self.get_type_imputation_display()} : {self.montant:,.0f} FCFA"

    def save(self, *args, **kwargs):
        """Applique l'imputation sur le paiement et met à jour les réserves"""
        super().save(*args, **kwargs)

        # Mettre à jour le paiement
        paiement = self.paiement
        if self.type_imputation == 'frais':
            paiement.impute_frais += self.montant
        elif self.type_imputation == 'emoluments':
            paiement.impute_emoluments += self.montant
        elif self.type_imputation == 'interets':
            paiement.impute_interets += self.montant
        elif self.type_imputation == 'principal':
            paiement.impute_principal += self.montant

        # Réduire le montant réservé
        paiement.montant_reserve = max(Decimal('0'), paiement.montant_reserve - self.montant)
        paiement.save()

    def to_dict(self):
        return {
            'id': str(self.id),
            'paiement_id': str(self.paiement_id),
            'date_imputation': self.date_imputation.isoformat() if self.date_imputation else None,
            'type_imputation': self.type_imputation,
            'type_imputation_display': self.get_type_imputation_display(),
            'montant': str(self.montant),
            'observations': self.observations,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }


# ═══════════════════════════════════════════════════════════════
# MODÈLE : HISTORIQUE ACTION RECOUVREMENT
# Traçabilité complète des actions sur un dossier
# ═══════════════════════════════════════════════════════════════

class HistoriqueActionRecouvrement(models.Model):
    """
    Historique des actions effectuées sur un dossier de recouvrement.
    Traçabilité complète.
    """

    TYPE_ACTION_CHOICES = [
        ('creation', 'Création du dossier'),
        ('mise_en_demeure', 'Mise en demeure'),
        ('relance', 'Relance'),
        ('appel', 'Appel téléphonique'),
        ('visite', 'Visite sur place'),
        ('sommation', 'Sommation de payer'),
        ('saisie', 'Saisie'),
        ('paiement', 'Paiement reçu'),
        ('reversement', 'Reversement créancier'),
        ('basculement', 'Basculement amiable/forcé'),
        ('cloture', 'Clôture du dossier'),
        ('autre', 'Autre action'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    dossier = models.ForeignKey(
        'DossierRecouvrement',
        on_delete=models.CASCADE,
        related_name='historique_actions'
    )

    date_action = models.DateTimeField(auto_now_add=True)
    type_action = models.CharField(max_length=30, choices=TYPE_ACTION_CHOICES)
    description = models.TextField()

    # Lien optionnel vers un paiement
    paiement_lie = models.ForeignKey(
        PaiementRecouvrement,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    # Métadonnées
    cree_par = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)

    class Meta:
        verbose_name = "Historique action"
        verbose_name_plural = "Historique actions"
        ordering = ['-date_action']

    def __str__(self):
        return f"{self.get_type_action_display()} - {self.dossier.reference}"

    def to_dict(self):
        return {
            'id': str(self.id),
            'dossier_id': str(self.dossier_id),
            'dossier_reference': self.dossier.reference,
            'date_action': self.date_action.isoformat() if self.date_action else None,
            'type_action': self.type_action,
            'type_action_display': self.get_type_action_display(),
            'description': self.description,
            'paiement_lie_id': str(self.paiement_lie_id) if self.paiement_lie_id else None,
            'cree_par': self.cree_par.username if self.cree_par else None,
        }
