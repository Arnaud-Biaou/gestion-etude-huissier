"""
Modèles du module Recouvrement de Créances
"""

from django.db import models
from django.utils import timezone
from decimal import Decimal
import uuid


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
