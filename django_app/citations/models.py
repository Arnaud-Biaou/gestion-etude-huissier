"""
ModÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ¨les pour le module MÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂMOIRES DE CÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂDULES DE CITATIONS
Conforme aux dÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ©crets nÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ°2012-143, nÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ°2012-435 et nÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ°2007-155 du BÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ©nin
"""

from django.db import models
from django.utils import timezone
from django.conf import settings
from decimal import Decimal
import json


# =============================================================================
# TABLE DES LOCALITÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂS ET DISTANCES
# =============================================================================

class Localite(models.Model):
    """Table des localitÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ©s avec distances depuis les principales villes"""
    nom = models.CharField(max_length=100, verbose_name='Nom de la localitÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ©')
    departement = models.CharField(max_length=100, blank=True, verbose_name='DÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ©partement')
    commune = models.CharField(max_length=100, blank=True, verbose_name='Commune')

    # Distances depuis les principales villes (en km)
    distance_parakou = models.DecimalField(
        max_digits=8, decimal_places=2, default=0,
        verbose_name='Distance depuis Parakou (km)'
    )
    distance_cotonou = models.DecimalField(
        max_digits=8, decimal_places=2, default=0,
        verbose_name='Distance depuis Cotonou (km)'
    )

    # CoordonnÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ©es GPS optionnelles
    latitude = models.DecimalField(
        max_digits=10, decimal_places=7, null=True, blank=True
    )
    longitude = models.DecimalField(
        max_digits=10, decimal_places=7, null=True, blank=True
    )

    actif = models.BooleanField(default=True)
    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'LocalitÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ©'
        verbose_name_plural = 'LocalitÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ©s'
        ordering = ['nom']
        unique_together = ['nom', 'commune']

    def __str__(self):
        if self.commune:
            return f"{self.nom} ({self.commune})"
        return self.nom


# =============================================================================
# BARÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂMES TARIFAIRES (DÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ©crets nÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ°2012-143 et nÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ°2007-155)
# =============================================================================

class BaremeTarifaire(models.Model):
    """BarÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ¨mes tarifaires pour les frais de citation"""
    TYPE_BAREME_CHOICES = [
        ('signification', 'Frais de signification (Art. 81)'),
        ('copie', 'Frais de copie (Art. 82)'),
        ('transport', 'Frais de transport (Art. 45/89)'),
        ('mission', 'Frais de mission (DÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ©cret 2007-155)'),
        ('sejour', 'IndemnitÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ© de sÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ©jour (Art. 46)'),
    ]

    code = models.CharField(max_length=50, unique=True, verbose_name='Code')
    libelle = models.CharField(max_length=200, verbose_name='LibellÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ©')
    type_bareme = models.CharField(
        max_length=20, choices=TYPE_BAREME_CHOICES,
        verbose_name='Type de barÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ¨me'
    )
    montant = models.DecimalField(
        max_digits=12, decimal_places=0,
        verbose_name='Montant (FCFA)'
    )
    article_reference = models.CharField(
        max_length=100, blank=True,
        verbose_name='Article de rÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ©fÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ©rence'
    )
    description = models.TextField(blank=True, verbose_name='Description')

    # Conditions d'application
    distance_min = models.DecimalField(
        max_digits=8, decimal_places=2, null=True, blank=True,
        verbose_name='Distance minimum (km)'
    )
    distance_max = models.DecimalField(
        max_digits=8, decimal_places=2, null=True, blank=True,
        verbose_name='Distance maximum (km)'
    )

    date_vigueur = models.DateField(
        default=timezone.now,
        verbose_name='Date d\'entrÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ©e en vigueur'
    )
    actif = models.BooleanField(default=True)

    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'BarÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ¨me tarifaire'
        verbose_name_plural = 'BarÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ¨mes tarifaires'
        ordering = ['type_bareme', 'code']

    def __str__(self):
        return f"{self.libelle} - {self.montant:,.0f} FCFA"


# =============================================================================
# AUTORITÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂS REQUÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂRANTES
# =============================================================================

class AutoriteRequerante(models.Model):
    """AutoritÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ©s pouvant ÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ©mettre des cÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ©dules de citation"""
    TYPE_AUTORITE_CHOICES = [
        ('parquet_criet', 'Parquet SpÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ©cial CRIET'),
        ('parquet_tpi', 'Parquet RÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ©publique TPI'),
        ('parquet_ca', 'Parquet GÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ©nÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ©ral Cour d\'Appel'),
        ('tribunal', 'Tribunal'),
        ('cour_appel', 'Cour d\'Appel'),
        ('cour_supreme', 'Cour SuprÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂªme'),
        ('autre', 'Autre'),
    ]

    code = models.CharField(max_length=20, unique=True, verbose_name='Code')
    nom = models.CharField(max_length=200, verbose_name='Nom complet')
    type_autorite = models.CharField(
        max_length=20, choices=TYPE_AUTORITE_CHOICES,
        verbose_name='Type d\'autoritÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ©'
    )
    sigle = models.CharField(max_length=50, blank=True, verbose_name='Sigle')
    adresse = models.TextField(blank=True, verbose_name='Adresse')
    ville = models.CharField(max_length=100, blank=True, verbose_name='Ville')

    # Contact
    telephone = models.CharField(max_length=50, blank=True)
    email = models.EmailField(blank=True)

    # Responsable
    nom_responsable = models.CharField(
        max_length=200, blank=True,
        verbose_name='Nom du responsable'
    )
    fonction_responsable = models.CharField(
        max_length=200, blank=True,
        verbose_name='Fonction'
    )

    actif = models.BooleanField(default=True)
    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'AutoritÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ© requÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ©rante'
        verbose_name_plural = 'AutoritÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ©s requÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ©rantes'
        ordering = ['nom']

    def __str__(self):
        if self.sigle:
            return f"{self.sigle} - {self.nom}"
        return self.nom


# =============================================================================
# CÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂDULES DE CITATION
# =============================================================================

class CeduleReception(models.Model):
    """CÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ©dules reÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ§ues pour signification"""
    URGENCE_CHOICES = [
        ('normale', 'Normale'),
        ('urgente', 'Urgente'),
        ('tres_urgente', 'TrÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ¨s urgente'),
    ]

    STATUT_CHOICES = [
        ('recue', 'ReÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ§ue'),
        ('en_cours', 'En cours de signification'),
        ('signifiee', 'SignifiÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ©e (totalement)'),
        ('partielle', 'Partiellement signifiÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ©e'),
        ('retournee', 'RetournÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ©e au greffe'),
        ('cloturee', 'ClÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ´turÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ©e'),
    ]

    NATURE_ACTE_CHOICES = [
        ('citation_criminelle', 'Citation en matiÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ¨re criminelle'),
        ('citation_correctionnelle', 'Citation en matiÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ¨re correctionnelle'),
        ('citation_police', 'Citation en matiÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ¨re de police'),
        ('mandat_comparution', 'Signification de mandat de comparution'),
        ('ordonnance', 'Signification d\'ordonnance'),
        ('jugement', 'Signification de jugement'),
        ('arret', 'Signification d\'arrÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂªt'),
        ('notification', 'Notification'),
        ('autre', 'Autre acte pÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ©nal'),
    ]

    # RÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ©fÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ©rence unique
    reference = models.CharField(
        max_length=50, unique=True,
        verbose_name='RÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ©fÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ©rence interne'
    )

    # Informations de rÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ©ception
    date_reception = models.DateField(
        default=timezone.now,
        verbose_name='Date de rÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ©ception'
    )
    autorite_requerante = models.ForeignKey(
        AutoriteRequerante, on_delete=models.PROTECT,
        related_name='cedules',
        verbose_name='AutoritÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ© requÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ©rante'
    )

    # RÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ©fÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ©rences de l'affaire
    numero_parquet = models.CharField(
        max_length=100,
        verbose_name='NumÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ©ro de parquet / RÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ©fÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ©rence affaire'
    )
    nature_infraction = models.CharField(
        max_length=500, blank=True,
        verbose_name='Nature de l\'infraction'
    )
    nature_acte = models.CharField(
        max_length=30, choices=NATURE_ACTE_CHOICES,
        default='citation_correctionnelle',
        verbose_name='Nature de l\'acte'
    )

    # Juridiction et audience
    juridiction = models.CharField(
        max_length=200, blank=True,
        verbose_name='Juridiction concernÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ©e'
    )
    date_audience = models.DateField(
        null=True, blank=True,
        verbose_name='Date d\'audience prÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ©vue'
    )
    heure_audience = models.TimeField(
        null=True, blank=True,
        verbose_name='Heure d\'audience'
    )

    # Statut et urgence
    urgence = models.CharField(
        max_length=15, choices=URGENCE_CHOICES,
        default='normale',
        verbose_name='Niveau d\'urgence'
    )
    statut = models.CharField(
        max_length=15, choices=STATUT_CHOICES,
        default='recue',
        verbose_name='Statut'
    )

    # Documents joints
    nombre_pieces_jointes = models.IntegerField(
        default=0,
        verbose_name='Nombre de piÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ¨ces jointes'
    )
    observations = models.TextField(blank=True, verbose_name='Observations')

    # PiÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ¨ce jointe numÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ©rique
    document_cedule = models.FileField(
        upload_to='cedules/', blank=True, null=True,
        verbose_name='Document de la cÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ©dule'
    )

    # TraÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ§abilitÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ©
    cree_par = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True,
        related_name='cedules_creees',
        verbose_name='CrÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ©ÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ© par'
    )
    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'CÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ©dule de citation'
        verbose_name_plural = 'CÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ©dules de citations'
        ordering = ['-date_reception', '-date_creation']

    def __str__(self):
        return f"{self.reference} - {self.numero_parquet}"

    @classmethod
    def generer_reference(cls):
        """GÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ©nÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ¨re une rÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ©fÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ©rence unique pour la cÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ©dule"""
        now = timezone.now()
        count = cls.objects.filter(date_creation__year=now.year).count() + 1
        return f"CED-{now.year}-{str(count).zfill(4)}"

    def save(self, *args, **kwargs):
        if not self.reference:
            self.reference = self.generer_reference()
        super().save(*args, **kwargs)

    def get_nb_destinataires(self):
        """Retourne le nombre de destinataires"""
        return self.destinataires.count()

    def get_nb_signifies(self):
        """Retourne le nombre de destinataires signifiÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ©s"""
        return self.destinataires.filter(acte_signification__isnull=False).distinct().count()

    def calculer_montant_total(self):
        """Calcule le montant total des frais pour cette cÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ©dule"""
        total = Decimal('0')
        for dest in self.destinataires.all():
            if hasattr(dest, 'acte_signification') and dest.acte_signification:
                total += dest.acte_signification.get_montant_total()
        return total


# =============================================================================
# DESTINATAIRES DES CÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂDULES
# =============================================================================

class DestinataireCedule(models.Model):
    """Destinataires ÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ  citer pour une cÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ©dule"""
    TYPE_DESTINATAIRE_CHOICES = [
        ('prevenu', 'PrÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ©venu'),
        ('temoin', 'TÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ©moin'),
        ('partie_civile', 'Partie civile'),
        ('civilement_responsable', 'Civilement responsable'),
        ('avocat', 'Avocat'),
        ('expert', 'Expert'),
        ('autre', 'Autre'),
    ]

    TYPE_PERSONNE_CHOICES = [
        ('physique', 'Personne physique'),
        ('morale', 'Personne morale'),
    ]

    cedule = models.ForeignKey(
        CeduleReception, on_delete=models.CASCADE,
        related_name='destinataires',
        verbose_name='CÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ©dule'
    )

    # Type de destinataire
    type_destinataire = models.CharField(
        max_length=25, choices=TYPE_DESTINATAIRE_CHOICES,
        default='prevenu',
        verbose_name='QualitÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ©'
    )
    type_personne = models.CharField(
        max_length=10, choices=TYPE_PERSONNE_CHOICES,
        default='physique',
        verbose_name='Type de personne'
    )

    # Personne physique
    nom = models.CharField(max_length=100, blank=True, verbose_name='Nom')
    prenoms = models.CharField(max_length=200, blank=True, verbose_name='PrÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ©noms')

    # Personne morale
    raison_sociale = models.CharField(
        max_length=200, blank=True,
        verbose_name='Raison sociale'
    )
    sigle = models.CharField(max_length=50, blank=True, verbose_name='Sigle')
    representant_legal = models.CharField(
        max_length=200, blank=True,
        verbose_name='ReprÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ©sentant lÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ©gal'
    )

    # Adresse
    adresse = models.TextField(blank=True, verbose_name='Adresse complÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ¨te')
    localite = models.ForeignKey(
        Localite, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='destinataires',
        verbose_name='LocalitÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ©'
    )
    localite_texte = models.CharField(
        max_length=200, blank=True,
        verbose_name='LocalitÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ© (texte libre)'
    )

    # Distance
    distance_km = models.DecimalField(
        max_digits=8, decimal_places=2, default=0,
        verbose_name='Distance depuis rÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ©sidence huissier (km)'
    )

    # Contact
    telephone = models.CharField(max_length=50, blank=True)
    email = models.EmailField(blank=True)

    observations = models.TextField(blank=True)

    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Destinataire de cÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ©dule'
        verbose_name_plural = 'Destinataires de cÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ©dules'
        ordering = ['cedule', 'type_destinataire', 'nom']

    def __str__(self):
        return self.get_nom_complet()

    def get_nom_complet(self):
        """Retourne le nom complet du destinataire"""
        if self.type_personne == 'morale':
            return self.raison_sociale or self.sigle or 'Personne morale'
        return f"{self.nom} {self.prenoms}".strip() or 'Personne physique'

    def save(self, *args, **kwargs):
        # Calculer la distance automatiquement si localitÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ© sÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ©lectionnÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ©e
        if self.localite and not self.distance_km:
            # Utiliser la distance depuis Parakou par dÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ©faut
            self.distance_km = self.localite.distance_parakou
        super().save(*args, **kwargs)


# =============================================================================
# ACTES DE SIGNIFICATION
# =============================================================================

class ActeSignification(models.Model):
    """Actes de signification effectuÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ©s"""
    MODALITE_REMISE_CHOICES = [
        ('personne', 'ÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ personne'),
        ('domicile', 'ÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ domicile'),
        ('mairie', 'ÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ mairie'),
        ('parquet', 'Au parquet'),
        ('affichage', 'Par affichage'),
        ('autre', 'Autre'),
    ]

    destinataire = models.OneToOneField(
        DestinataireCedule, on_delete=models.CASCADE,
        related_name='acte_signification',
        verbose_name='Destinataire'
    )

    # Informations de signification
    date_signification = models.DateField(
        default=timezone.now,
        verbose_name='Date de signification'
    )
    heure_signification = models.TimeField(
        null=True, blank=True,
        verbose_name='Heure de signification'
    )

    modalite_remise = models.CharField(
        max_length=15, choices=MODALITE_REMISE_CHOICES,
        default='personne',
        verbose_name='ModalitÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ© de remise'
    )

    # Personne ayant reÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ§u l'acte
    recepteur_nom = models.CharField(
        max_length=200, blank=True,
        verbose_name='Nom du rÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ©cepteur'
    )
    recepteur_qualite = models.CharField(
        max_length=100, blank=True,
        verbose_name='QualitÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ© du rÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ©cepteur'
    )

    # Lieu de signification
    lieu_signification = models.TextField(
        blank=True,
        verbose_name='Lieu de signification'
    )

    # Documents
    nombre_copies = models.IntegerField(
        default=1,
        verbose_name='Nombre de copies'
    )
    nombre_roles = models.IntegerField(
        default=0,
        verbose_name='Nombre de rÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ´les (42 lignes ÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ 20 syllabes)'
    )

    # Observations
    observations = models.TextField(blank=True)
    difficultes = models.TextField(
        blank=True,
        verbose_name='DifficultÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ©s rencontrÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ©es'
    )

    # TraÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ§abilitÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ©
    signifie_par = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True,
        related_name='actes_signifies',
        verbose_name='SignifiÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ© par'
    )
    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Acte de signification'
        verbose_name_plural = 'Actes de signification'
        ordering = ['-date_signification']

    def __str__(self):
        return f"Signification {self.destinataire} - {self.date_signification}"

    def get_montant_total(self):
        """Calcule le montant total des frais pour cet acte"""
        if hasattr(self, 'frais_signification'):
            return self.frais_signification.get_total_general()
        return Decimal('0')


# =============================================================================
# FRAIS DE SIGNIFICATION (Article 81 - DÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ©cret nÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ°2012-143)
# =============================================================================

class FraisSignification(models.Model):
    """Frais de signification selon Article 81"""
    acte = models.OneToOneField(
        ActeSignification, on_delete=models.CASCADE,
        related_name='frais_signification',
        verbose_name='Acte'
    )

    # Frais de signification (Art. 81)
    premier_original = models.DecimalField(
        max_digits=12, decimal_places=0, default=980,
        verbose_name='Premier original'
    )
    deuxieme_original = models.DecimalField(
        max_digits=12, decimal_places=0, default=980,
        verbose_name='DeuxiÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ¨me original'
    )
    copies_supplementaires = models.DecimalField(
        max_digits=12, decimal_places=0, default=0,
        verbose_name='Copies supplÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ©mentaires (900 ÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ n)'
    )
    mention_repertoire = models.DecimalField(
        max_digits=12, decimal_places=0, default=25,
        verbose_name='Mention sur rÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ©pertoire'
    )
    vacation = models.DecimalField(
        max_digits=12, decimal_places=0, default=3000,
        verbose_name='Vacation'
    )

    # Frais de copie (Art. 82)
    frais_copie_roles = models.DecimalField(
        max_digits=12, decimal_places=0, default=0,
        verbose_name='Frais de copie (1000 ÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ rÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ´les)'
    )

    # Frais de transport (Art. 45 + 89)
    distance_km = models.DecimalField(
        max_digits=8, decimal_places=2, default=0,
        verbose_name='Distance (km)'
    )
    tarif_km = models.DecimalField(
        max_digits=12, decimal_places=0, default=140,
        verbose_name='Tarif au km'
    )
    frais_transport = models.DecimalField(
        max_digits=12, decimal_places=0, default=0,
        verbose_name='Frais de transport'
    )

    # Frais de mission (DÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ©cret nÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ°2007-155 - Groupe II)
    TYPE_MISSION_CHOICES = [
        ('aucune', 'Aucune mission'),
        ('1_repas', 'Mission obligeant ÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ  prendre 1 repas'),
        ('2_repas', 'Mission obligeant ÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ  prendre 2 repas'),
        ('journee', 'Mission journÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ©e complÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ¨te'),
    ]
    type_mission = models.CharField(
        max_length=15, choices=TYPE_MISSION_CHOICES,
        default='aucune',
        verbose_name='Type de mission'
    )
    frais_mission = models.DecimalField(
        max_digits=12, decimal_places=0, default=0,
        verbose_name='Frais de mission'
    )

    # IndemnitÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ© de sÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ©jour (Art. 46)
    indemnite_sejour = models.DecimalField(
        max_digits=12, decimal_places=0, default=0,
        verbose_name='IndemnitÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ© de sÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ©jour'
    )

    # Totaux
    sous_total_signification = models.DecimalField(
        max_digits=12, decimal_places=0, default=0,
        verbose_name='Sous-total signification'
    )
    total_general = models.DecimalField(
        max_digits=12, decimal_places=0, default=0,
        verbose_name='Total gÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ©nÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ©ral'
    )

    # DÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ©tail JSON pour traÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ§abilitÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ©
    detail_calcul = models.JSONField(
        default=dict, blank=True,
        verbose_name='DÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ©tail du calcul'
    )

    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Frais de signification'
        verbose_name_plural = 'Frais de signification'

    def __str__(self):
        return f"Frais {self.acte} - {self.total_general:,.0f} FCFA"

    def calculer_frais(self):
        """Calcule tous les frais selon les barÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ¨mes"""
        # 1. Sous-total signification (Art. 81)
        self.sous_total_signification = (
            self.premier_original +
            self.deuxieme_original +
            self.copies_supplementaires +
            self.mention_repertoire +
            self.vacation
        )

        # 2. Frais de copie (Art. 82) - 1000 FCFA par rÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ´le
        if self.acte.nombre_roles > 0:
            self.frais_copie_roles = Decimal(self.acte.nombre_roles * 1000)

        # 3. Frais de transport (Art. 45 + 89)
        # Si distance > 20 km : distance ÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ 140 ÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ 2 (aller-retour)
        self.distance_km = self.acte.destinataire.distance_km
        if self.distance_km > 20:
            self.frais_transport = self.distance_km * self.tarif_km * 2
        else:
            self.frais_transport = Decimal('0')

        # 4. Frais de mission (DÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ©cret 2007-155 - Groupe II)
        # Si distance >= 100 km
        if self.distance_km >= 100:
            if self.type_mission == '1_repas':
                self.frais_mission = Decimal('15000')
            elif self.type_mission == '2_repas':
                self.frais_mission = Decimal('30000')
            elif self.type_mission == 'journee':
                self.frais_mission = Decimal('45000')
            else:
                # Automatiquement attribuer selon la distance
                if self.distance_km >= 200:
                    self.type_mission = 'journee'
                    self.frais_mission = Decimal('45000')
                elif self.distance_km >= 150:
                    self.type_mission = '2_repas'
                    self.frais_mission = Decimal('30000')
                else:
                    self.type_mission = '1_repas'
                    self.frais_mission = Decimal('15000')
        else:
            self.type_mission = 'aucune'
            self.frais_mission = Decimal('0')

        # 5. Total gÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ©nÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ©ral
        self.total_general = (
            self.sous_total_signification +
            self.frais_copie_roles +
            self.frais_transport +
            self.frais_mission +
            self.indemnite_sejour
        )

        # Sauvegarder le dÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ©tail du calcul
        self.detail_calcul = {
            'signification': {
                'premier_original': float(self.premier_original),
                'deuxieme_original': float(self.deuxieme_original),
                'copies_supplementaires': float(self.copies_supplementaires),
                'mention_repertoire': float(self.mention_repertoire),
                'vacation': float(self.vacation),
                'sous_total': float(self.sous_total_signification),
                'article_reference': 'Article 81 - DÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ©cret nÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ°2012-143'
            },
            'copie': {
                'nombre_roles': self.acte.nombre_roles,
                'tarif_role': 1000,
                'total': float(self.frais_copie_roles),
                'article_reference': 'Article 82 - DÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ©cret nÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ°2012-143'
            },
            'transport': {
                'distance_km': float(self.distance_km),
                'tarif_km': float(self.tarif_km),
                'aller_retour': True,
                'seuil_km': 20,
                'total': float(self.frais_transport),
                'article_reference': 'Articles 45 et 89 - DÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ©cret nÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ°2012-143'
            },
            'mission': {
                'type': self.type_mission,
                'seuil_km': 100,
                'total': float(self.frais_mission),
                'article_reference': 'DÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ©cret nÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ°2007-155 - Groupe II'
            },
            'sejour': {
                'total': float(self.indemnite_sejour),
                'article_reference': 'Article 46 - DÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ©cret nÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ°2012-143'
            },
            'total_general': float(self.total_general)
        }

    def save(self, *args, **kwargs):
        self.calculer_frais()
        super().save(*args, **kwargs)

    def get_total_general(self):
        return self.total_general


# =============================================================================
# MÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂMOIRES DE FRAIS
# =============================================================================

class Memoire(models.Model):
    """MÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ©moires de frais de signification"""
    STATUT_CHOICES = [
        ('brouillon', 'Brouillon'),
        ('certifie', 'CertifiÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ© sincÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ¨re'),
        ('soumis', 'Soumis au Parquet'),
        ('vise', 'VisÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ© par le Procureur'),
        ('taxe', 'TaxÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ© par le PrÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ©sident'),
        ('en_paiement', 'En paiement'),
        ('paye', 'PayÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ©'),
        ('rejete', 'RejetÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ©'),
    ]

    # RÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ©fÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ©rence unique
    numero_memoire = models.CharField(
        max_length=50, unique=True,
        verbose_name='NumÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ©ro du mÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ©moire'
    )

    # PÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ©riode couverte
    mois = models.IntegerField(verbose_name='Mois')
    annee = models.IntegerField(verbose_name='AnnÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ©e')

    # Huissier
    huissier = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
        related_name='memoires_huissier',
        verbose_name='Huissier'
    )
    nom_huissier = models.CharField(
        max_length=200,
        verbose_name='Nom de l\'huissier'
    )
    juridiction_huissier = models.CharField(
        max_length=200, blank=True,
        verbose_name='Juridiction de l\'huissier'
    )

    # AutoritÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ© requÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ©rante
    autorite_requerante = models.ForeignKey(
        AutoriteRequerante, on_delete=models.PROTECT,
        related_name='memoires',
        verbose_name='AutoritÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ© requÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ©rante'
    )

    # Montants
    montant_total = models.DecimalField(
        max_digits=15, decimal_places=0, default=0,
        verbose_name='Montant total'
    )
    montant_en_lettres = models.CharField(
        max_length=500, blank=True,
        verbose_name='Montant en lettres'
    )

    # Statut
    statut = models.CharField(
        max_length=15, choices=STATUT_CHOICES,
        default='brouillon',
        verbose_name='Statut'
    )

    # Dates du circuit de validation
    date_certification = models.DateTimeField(
        null=True, blank=True,
        verbose_name='Date de certification'
    )
    date_soumission = models.DateTimeField(
        null=True, blank=True,
        verbose_name='Date de soumission'
    )
    date_visa = models.DateTimeField(
        null=True, blank=True,
        verbose_name='Date du visa'
    )
    date_taxe = models.DateTimeField(
        null=True, blank=True,
        verbose_name='Date de taxation'
    )
    date_paiement = models.DateTimeField(
        null=True, blank=True,
        verbose_name='Date de paiement'
    )

    # Validateurs
    vise_par = models.CharField(
        max_length=200, blank=True,
        verbose_name='VisÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ© par (Procureur)'
    )
    taxe_par = models.CharField(
        max_length=200, blank=True,
        verbose_name='TaxÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ© par (PrÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ©sident)'
    )

    # RÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ©fÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ©rences des documents gÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ©nÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ©rÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ©s
    reference_requisition = models.CharField(
        max_length=100, blank=True,
        verbose_name='RÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ©fÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ©rence rÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ©quisition'
    )
    reference_executoire = models.CharField(
        max_length=100, blank=True,
        verbose_name='RÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ©fÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ©rence exÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ©cutoire'
    )

    # Documents PDF
    document_memoire = models.FileField(
        upload_to='memoires/pdf/', blank=True, null=True,
        verbose_name='MÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ©moire PDF'
    )
    document_requisition = models.FileField(
        upload_to='memoires/requisitions/', blank=True, null=True,
        verbose_name='RÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ©quisition PDF'
    )
    document_executoire = models.FileField(
        upload_to='memoires/executoires/', blank=True, null=True,
        verbose_name='ExÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ©cutoire PDF'
    )

    # Rejet
    motif_rejet = models.TextField(
        blank=True,
        verbose_name='Motif de rejet'
    )

    observations = models.TextField(blank=True)

    # TraÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ§abilitÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ©
    cree_par = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True,
        related_name='memoires_crees',
        verbose_name='CrÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ©ÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ© par'
    )
    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'MÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ©moire de frais'
        verbose_name_plural = 'MÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ©moires de frais'
        ordering = ['-annee', '-mois', '-date_creation']
        unique_together = ['mois', 'annee', 'autorite_requerante']

    def __str__(self):
        return f"MÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ©moire {self.numero_memoire} - {self.get_mois_display()} {self.annee}"

    def get_mois_display(self):
        """Retourne le nom du mois en franÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ§ais"""
        MOIS = [
            '', 'Janvier', 'FÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ©vrier', 'Mars', 'Avril', 'Mai', 'Juin',
            'Juillet', 'AoÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ»t', 'Septembre', 'Octobre', 'Novembre', 'DÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ©cembre'
        ]
        return MOIS[self.mois] if 1 <= self.mois <= 12 else ''

    @classmethod
    def generer_numero(cls, mois, annee):
        """GÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ©nÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ¨re un numÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ©ro unique pour le mÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ©moire"""
        count = cls.objects.filter(annee=annee).count() + 1
        return f"MEM-{annee}-{str(count).zfill(3)}"

    def save(self, *args, **kwargs):
        if not self.numero_memoire:
            self.numero_memoire = self.generer_numero(self.mois, self.annee)
        super().save(*args, **kwargs)

    def calculer_total(self):
        """Calcule le montant total du mÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ©moire"""
        total = self.lignes.aggregate(
            total=models.Sum('montant_ligne')
        )['total'] or Decimal('0')
        self.montant_total = total
        self.montant_en_lettres = self.convertir_en_lettres(total)
        self.save()
        return total

    @staticmethod
    def convertir_en_lettres(montant):
        """Convertit un montant en lettres"""
        if montant == 0:
            return "ZÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ©ro franc CFA"

        unites = ['', 'un', 'deux', 'trois', 'quatre', 'cinq', 'six', 'sept', 'huit', 'neuf']
        dizaines = ['', 'dix', 'vingt', 'trente', 'quarante', 'cinquante',
                   'soixante', 'soixante', 'quatre-vingt', 'quatre-vingt']
        speciaux = {
            11: 'onze', 12: 'douze', 13: 'treize', 14: 'quatorze', 15: 'quinze',
            16: 'seize', 17: 'dix-sept', 18: 'dix-huit', 19: 'dix-neuf',
            71: 'soixante-et-onze', 72: 'soixante-douze', 73: 'soixante-treize',
            74: 'soixante-quatorze', 75: 'soixante-quinze', 76: 'soixante-seize',
            77: 'soixante-dix-sept', 78: 'soixante-dix-huit', 79: 'soixante-dix-neuf',
            91: 'quatre-vingt-onze', 92: 'quatre-vingt-douze', 93: 'quatre-vingt-treize',
            94: 'quatre-vingt-quatorze', 95: 'quatre-vingt-quinze', 96: 'quatre-vingt-seize',
            97: 'quatre-vingt-dix-sept', 98: 'quatre-vingt-dix-huit', 99: 'quatre-vingt-dix-neuf'
        }

        def convertir_bloc(n):
            if n == 0:
                return ''
            if n < 10:
                return unites[n]
            if n in speciaux:
                return speciaux[n]
            if n < 100:
                d, u = divmod(n, 10)
                if d == 7 or d == 9:
                    return dizaines[d] + '-' + (unites[u + 10] if u > 0 else 'dix')
                if u == 1 and d in [2, 3, 4, 5, 6]:
                    return dizaines[d] + '-et-un'
                if u == 0:
                    return dizaines[d] + ('s' if d == 8 else '')
                return dizaines[d] + '-' + unites[u]
            if n < 1000:
                c, r = divmod(n, 100)
                if c == 1:
                    return 'cent' + (' ' + convertir_bloc(r) if r else '')
                return unites[c] + ' cent' + ('s' if r == 0 else ' ' + convertir_bloc(r))
            return str(n)

        montant = int(montant)
        if montant >= 1000000000:
            milliards, reste = divmod(montant, 1000000000)
            result = (('un milliard' if milliards == 1 else convertir_bloc(milliards) + ' milliards') +
                     (' ' + Memoire.convertir_en_lettres(reste).replace(' francs CFA', '') if reste else ''))
        elif montant >= 1000000:
            millions, reste = divmod(montant, 1000000)
            result = (('un million' if millions == 1 else convertir_bloc(millions) + ' millions') +
                     (' ' + Memoire.convertir_en_lettres(reste).replace(' francs CFA', '') if reste else ''))
        elif montant >= 1000:
            milliers, reste = divmod(montant, 1000)
            result = (('mille' if milliers == 1 else convertir_bloc(milliers) + ' mille') +
                     (' ' + convertir_bloc(reste) if reste else ''))
        else:
            result = convertir_bloc(montant)

        return result.strip().capitalize() + ' francs CFA'

    def certifier(self):
        """Certifie le mÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ©moire"""
        self.statut = 'certifie'
        self.date_certification = timezone.now()
        self.save()

    def soumettre(self):
        """Soumet le mÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ©moire au Parquet"""
        if self.statut != 'certifie':
            raise ValueError("Le mÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ©moire doit ÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂªtre certifiÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ© avant soumission")
        self.statut = 'soumis'
        self.date_soumission = timezone.now()
        self.save()

    def viser(self, procureur):
        """Visa du Procureur"""
        if self.statut != 'soumis':
            raise ValueError("Le mÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ©moire doit ÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂªtre soumis avant visa")
        self.statut = 'vise'
        self.date_visa = timezone.now()
        self.vise_par = procureur
        self.save()

    def taxer(self, president):
        """Taxation par le PrÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ©sident"""
        if self.statut != 'vise':
            raise ValueError("Le mÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ©moire doit ÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂªtre visÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ© avant taxation")
        self.statut = 'taxe'
        self.date_taxe = timezone.now()
        self.taxe_par = president
        self.save()

    def marquer_paye(self):
        """Marque le mÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ©moire comme payÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ©"""
        if self.statut not in ['taxe', 'en_paiement']:
            raise ValueError("Le mÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ©moire doit ÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂªtre taxÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ© avant paiement")
        self.statut = 'paye'
        self.date_paiement = timezone.now()
        self.save()

    def rejeter(self, motif):
        """Rejette le mÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ©moire"""
        self.statut = 'rejete'
        self.motif_rejet = motif
        self.save()


# =============================================================================
# LIGNES DE MÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂMOIRE
# =============================================================================

class LigneMemoire(models.Model):
    """Lignes dÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ©taillÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ©es d'un mÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ©moire"""
    memoire = models.ForeignKey(
        Memoire, on_delete=models.CASCADE,
        related_name='lignes',
        verbose_name='MÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ©moire'
    )

    # NumÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ©ro d'ordre
    numero_ordre = models.IntegerField(verbose_name='NÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ° d\'ordre')

    # RÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ©fÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ©rence ÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ  la cÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ©dule et au destinataire
    cedule = models.ForeignKey(
        CeduleReception, on_delete=models.PROTECT,
        related_name='lignes_memoire',
        verbose_name='CÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ©dule'
    )
    destinataire = models.ForeignKey(
        DestinataireCedule, on_delete=models.PROTECT,
        related_name='lignes_memoire',
        verbose_name='Destinataire'
    )

    # RÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ©fÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ©rence ÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ  l'acte de signification
    acte = models.ForeignKey(
        ActeSignification, on_delete=models.PROTECT,
        related_name='lignes_memoire', null=True, blank=True,
        verbose_name='Acte de signification'
    )

    # Montant de la ligne
    montant_ligne = models.DecimalField(
        max_digits=12, decimal_places=0, default=0,
        verbose_name='Montant de la ligne'
    )

    # DÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ©tail du calcul (JSON)
    details_calcul = models.JSONField(
        default=dict, blank=True,
        verbose_name='DÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ©tails du calcul'
    )

    observations = models.TextField(blank=True)

    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Ligne de mÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ©moire'
        verbose_name_plural = 'Lignes de mÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ©moire'
        ordering = ['memoire', 'numero_ordre']
        unique_together = ['memoire', 'numero_ordre']

    def __str__(self):
        return f"Ligne {self.numero_ordre} - {self.memoire.numero_memoire}"

    def save(self, *args, **kwargs):
        # RÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ©cupÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ©rer le montant depuis l'acte de signification si disponible
        if self.acte and hasattr(self.acte, 'frais_signification'):
            self.montant_ligne = self.acte.frais_signification.total_general
            self.details_calcul = self.acte.frais_signification.detail_calcul
        super().save(*args, **kwargs)


# =============================================================================
# VALIDATIONS DE MÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂMOIRE
# =============================================================================

class ValidationMemoire(models.Model):
    """Historique des validations d'un mÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ©moire"""
    TYPE_VALIDATION_CHOICES = [
        ('creation', 'CrÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ©ation'),
        ('modification', 'Modification'),
        ('certification', 'Certification'),
        ('soumission', 'Soumission'),
        ('visa', 'Visa Procureur'),
        ('taxe', 'Taxation PrÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ©sident'),
        ('paiement', 'Paiement'),
        ('rejet', 'Rejet'),
    ]

    memoire = models.ForeignKey(
        Memoire, on_delete=models.CASCADE,
        related_name='validations',
        verbose_name='MÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ©moire'
    )

    type_validation = models.CharField(
        max_length=15, choices=TYPE_VALIDATION_CHOICES,
        verbose_name='Type de validation'
    )

    date_validation = models.DateTimeField(
        default=timezone.now,
        verbose_name='Date de validation'
    )

    validateur = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True,
        related_name='validations_memoires',
        verbose_name='Validateur'
    )
    validateur_nom = models.CharField(
        max_length=200, blank=True,
        verbose_name='Nom du validateur'
    )

    observations = models.TextField(blank=True)

    class Meta:
        verbose_name = 'Validation de mÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ©moire'
        verbose_name_plural = 'Validations de mÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ©moire'
        ordering = ['-date_validation']

    def __str__(self):
        return f"{self.get_type_validation_display()} - {self.memoire.numero_memoire}"


# =============================================================================
# REGISTRE AU PARQUET (Article 75)
# =============================================================================

class RegistreParquet(models.Model):
    """Registre des actes au parquet (Article 75)"""
    # RÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ©fÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ©rence de l'affaire
    reference_affaire = models.CharField(
        max_length=100,
        verbose_name='RÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ©fÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ©rence de l\'affaire'
    )

    # Nature des diligences
    nature_diligence = models.CharField(
        max_length=200,
        verbose_name='Nature des diligences'
    )

    # Date de l'acte
    date_acte = models.DateField(
        verbose_name='Date de l\'acte'
    )

    # Montant des ÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ©moluments
    montant_emoluments = models.DecimalField(
        max_digits=12, decimal_places=0,
        verbose_name='Montant des ÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ©moluments'
    )

    # Lien avec l'acte de signification
    acte_signification = models.ForeignKey(
        ActeSignification, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='registre_parquet',
        verbose_name='Acte de signification'
    )

    # Lien avec le mÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ©moire
    memoire = models.ForeignKey(
        Memoire, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='registre_parquet',
        verbose_name='MÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ©moire'
    )

    observations = models.TextField(blank=True)

    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'EntrÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ©e registre parquet'
        verbose_name_plural = 'Registre parquet'
        ordering = ['-date_acte']

    def __str__(self):
        return f"{self.reference_affaire} - {self.date_acte}"


# =============================================================================
# CONFIGURATION DU MODULE
# =============================================================================

class ConfigurationCitations(models.Model):
    """Configuration du module citations"""
    # RÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ©sidence de l'huissier (pour calcul des distances)
    ville_residence = models.CharField(
        max_length=100, default='Parakou',
        verbose_name='Ville de rÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ©sidence de l\'huissier'
    )

    # BarÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ¨mes par dÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ©faut
    tarif_premier_original = models.DecimalField(
        max_digits=12, decimal_places=0, default=980,
        verbose_name='Tarif premier original (Art. 81)'
    )
    tarif_deuxieme_original = models.DecimalField(
        max_digits=12, decimal_places=0, default=980,
        verbose_name='Tarif deuxiÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ¨me original (Art. 81)'
    )
    tarif_copie = models.DecimalField(
        max_digits=12, decimal_places=0, default=900,
        verbose_name='Tarif copie supplÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ©mentaire (Art. 81)'
    )
    tarif_mention_repertoire = models.DecimalField(
        max_digits=12, decimal_places=0, default=25,
        verbose_name='Tarif mention rÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ©pertoire (Art. 81)'
    )
    tarif_vacation = models.DecimalField(
        max_digits=12, decimal_places=0, default=3000,
        verbose_name='Tarif vacation (Art. 81)'
    )
    tarif_role = models.DecimalField(
        max_digits=12, decimal_places=0, default=1000,
        verbose_name='Tarif par rÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ´le (Art. 82)'
    )
    tarif_km = models.DecimalField(
        max_digits=12, decimal_places=0, default=140,
        verbose_name='Tarif au km (Art. 45/89)'
    )

    # Seuils de distance
    seuil_transport_km = models.DecimalField(
        max_digits=8, decimal_places=2, default=20,
        verbose_name='Seuil pour frais de transport (km)'
    )
    seuil_mission_km = models.DecimalField(
        max_digits=8, decimal_places=2, default=100,
        verbose_name='Seuil pour frais de mission (km)'
    )

    # Frais de mission Groupe II
    frais_mission_1_repas = models.DecimalField(
        max_digits=12, decimal_places=0, default=15000,
        verbose_name='Frais mission 1 repas'
    )
    frais_mission_2_repas = models.DecimalField(
        max_digits=12, decimal_places=0, default=30000,
        verbose_name='Frais mission 2 repas'
    )
    frais_mission_journee = models.DecimalField(
        max_digits=12, decimal_places=0, default=45000,
        verbose_name='Frais mission journÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ©e complÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ¨te'
    )

    # ParamÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ¨tres de gÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ©nÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ©ration
    prefixe_cedule = models.CharField(
        max_length=10, default='CED',
        verbose_name='PrÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ©fixe des rÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ©fÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ©rences de cÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ©dule'
    )
    prefixe_memoire = models.CharField(
        max_length=10, default='MEM',
        verbose_name='PrÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ©fixe des numÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ©ros de mÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ©moire'
    )

    date_modification = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Configuration citations'
        verbose_name_plural = 'Configuration citations'

    def __str__(self):
        return "Configuration du module Citations"

    @classmethod
    def get_instance(cls):
        """Retourne l'instance unique de configuration"""
        instance, created = cls.objects.get_or_create(pk=1)
        return instance
