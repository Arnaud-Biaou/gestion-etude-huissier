"""
Modèles du module Gérance Immobilière
Gestion complète des biens immobiliers pour une étude d'huissier
"""

from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from decimal import Decimal
import uuid

User = get_user_model()


class Proprietaire(models.Model):
    """Propriétaire / Bailleur"""
    TYPES = [
        ('particulier', 'Particulier'),
        ('societe', 'Société'),
        ('sci', 'SCI'),
        ('association', 'Association'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    type_proprietaire = models.CharField(max_length=20, choices=TYPES, default='particulier')

    # Informations personnelles / société
    nom = models.CharField(max_length=200, verbose_name='Nom / Raison sociale')
    prenom = models.CharField(max_length=100, blank=True, null=True, verbose_name='Prénom')
    civilite = models.CharField(max_length=10, blank=True, null=True)

    # Contact
    adresse = models.TextField(verbose_name='Adresse')
    ville = models.CharField(max_length=100)
    code_postal = models.CharField(max_length=10, blank=True, null=True)
    pays = models.CharField(max_length=50, default='Bénin')
    telephone = models.CharField(max_length=20)
    telephone_secondaire = models.CharField(max_length=20, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)

    # Informations légales
    numero_ifu = models.CharField(max_length=50, blank=True, null=True, verbose_name='N° IFU')
    numero_rccm = models.CharField(max_length=50, blank=True, null=True, verbose_name='N° RCCM')

    # Coordonnées bancaires
    banque = models.CharField(max_length=100, blank=True, null=True)
    numero_compte = models.CharField(max_length=50, blank=True, null=True)
    iban = models.CharField(max_length=34, blank=True, null=True)

    # Paramètres de gestion
    taux_honoraires = models.DecimalField(
        max_digits=5, decimal_places=2, default=10.00,
        verbose_name='Taux honoraires (%)'
    )
    mode_reversement = models.CharField(
        max_length=20,
        choices=[('mensuel', 'Mensuel'), ('trimestriel', 'Trimestriel')],
        default='mensuel'
    )
    jour_reversement = models.PositiveIntegerField(default=5, verbose_name='Jour de reversement')

    actif = models.BooleanField(default=True)
    notes = models.TextField(blank=True, null=True)

    cree_le = models.DateTimeField(auto_now_add=True)
    modifie_le = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Propriétaire'
        verbose_name_plural = 'Propriétaires'
        ordering = ['nom']

    def __str__(self):
        if self.prenom:
            return f"{self.nom} {self.prenom}"
        return self.nom


class BienImmobilier(models.Model):
    """Bien immobilier en gérance"""
    TYPES_BIEN = [
        ('appartement', 'Appartement'),
        ('maison', 'Maison'),
        ('villa', 'Villa'),
        ('studio', 'Studio'),
        ('bureau', 'Bureau'),
        ('commerce', 'Local commercial'),
        ('entrepot', 'Entrepôt'),
        ('terrain', 'Terrain'),
        ('immeuble', 'Immeuble entier'),
        ('autre', 'Autre'),
    ]

    STATUTS = [
        ('libre', 'Libre'),
        ('loue', 'Loué'),
        ('reserve', 'Réservé'),
        ('travaux', 'En travaux'),
        ('vente', 'En vente'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    proprietaire = models.ForeignKey(Proprietaire, on_delete=models.PROTECT, related_name='biens')

    # Identification
    reference = models.CharField(max_length=50, unique=True, verbose_name='Référence')
    designation = models.CharField(max_length=200, verbose_name='Désignation')
    type_bien = models.CharField(max_length=20, choices=TYPES_BIEN, default='appartement')

    # Localisation
    adresse = models.TextField(verbose_name='Adresse complète')
    quartier = models.CharField(max_length=100, blank=True, null=True)
    ville = models.CharField(max_length=100)
    code_postal = models.CharField(max_length=10, blank=True, null=True)

    # Caractéristiques
    surface = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True, verbose_name='Surface (m²)')
    nombre_pieces = models.PositiveIntegerField(blank=True, null=True, verbose_name='Nombre de pièces')
    etage = models.CharField(max_length=20, blank=True, null=True)
    meuble = models.BooleanField(default=False, verbose_name='Meublé')

    # Équipements
    parking = models.BooleanField(default=False)
    garage = models.BooleanField(default=False)
    jardin = models.BooleanField(default=False)
    piscine = models.BooleanField(default=False)
    climatisation = models.BooleanField(default=False)
    gardiennage = models.BooleanField(default=False)

    # Valeurs
    loyer_mensuel = models.DecimalField(max_digits=12, decimal_places=2, verbose_name='Loyer mensuel (XOF)')
    charges_mensuelles = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name='Charges (XOF)')
    depot_garantie = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name='Dépôt de garantie (XOF)')

    statut = models.CharField(max_length=20, choices=STATUTS, default='libre')
    date_acquisition = models.DateField(blank=True, null=True, verbose_name='Date acquisition mandat')
    date_fin_mandat = models.DateField(blank=True, null=True, verbose_name='Date fin mandat')

    description = models.TextField(blank=True, null=True)
    notes = models.TextField(blank=True, null=True)

    cree_le = models.DateTimeField(auto_now_add=True)
    modifie_le = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Bien immobilier'
        verbose_name_plural = 'Biens immobiliers'
        ordering = ['reference']

    def __str__(self):
        return f"{self.reference} - {self.designation}"


class Locataire(models.Model):
    """Locataire"""
    TYPES = [
        ('particulier', 'Particulier'),
        ('societe', 'Société'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    type_locataire = models.CharField(max_length=20, choices=TYPES, default='particulier')

    # Informations personnelles
    nom = models.CharField(max_length=200)
    prenom = models.CharField(max_length=100, blank=True, null=True)
    civilite = models.CharField(max_length=10, blank=True, null=True)
    date_naissance = models.DateField(blank=True, null=True)
    lieu_naissance = models.CharField(max_length=100, blank=True, null=True)
    nationalite = models.CharField(max_length=50, default='Béninoise')

    # Pièce d'identité
    type_piece = models.CharField(max_length=50, blank=True, null=True)
    numero_piece = models.CharField(max_length=50, blank=True, null=True)
    date_expiration_piece = models.DateField(blank=True, null=True)

    # Contact
    telephone = models.CharField(max_length=20)
    telephone_secondaire = models.CharField(max_length=20, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)

    # Situation professionnelle
    profession = models.CharField(max_length=100, blank=True, null=True)
    employeur = models.CharField(max_length=200, blank=True, null=True)
    revenu_mensuel = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)

    # Contact d'urgence
    contact_urgence_nom = models.CharField(max_length=200, blank=True, null=True)
    contact_urgence_telephone = models.CharField(max_length=20, blank=True, null=True)
    contact_urgence_lien = models.CharField(max_length=50, blank=True, null=True)

    # Garant
    garant_nom = models.CharField(max_length=200, blank=True, null=True)
    garant_telephone = models.CharField(max_length=20, blank=True, null=True)
    garant_adresse = models.TextField(blank=True, null=True)

    actif = models.BooleanField(default=True)
    notes = models.TextField(blank=True, null=True)

    cree_le = models.DateTimeField(auto_now_add=True)
    modifie_le = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Locataire'
        verbose_name_plural = 'Locataires'
        ordering = ['nom']

    def __str__(self):
        if self.prenom:
            return f"{self.nom} {self.prenom}"
        return self.nom


class Bail(models.Model):
    """Contrat de bail"""
    TYPES_BAIL = [
        ('habitation', 'Habitation'),
        ('commercial', 'Commercial'),
        ('professionnel', 'Professionnel'),
        ('mixte', 'Mixte'),
    ]

    STATUTS = [
        ('actif', 'Actif'),
        ('termine', 'Terminé'),
        ('resilie', 'Résilié'),
        ('suspendu', 'Suspendu'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    bien = models.ForeignKey(BienImmobilier, on_delete=models.PROTECT, related_name='baux')
    locataire = models.ForeignKey(Locataire, on_delete=models.PROTECT, related_name='baux')

    # Informations du bail
    reference = models.CharField(max_length=50, unique=True, verbose_name='N° Bail')
    type_bail = models.CharField(max_length=20, choices=TYPES_BAIL, default='habitation')

    date_debut = models.DateField(verbose_name='Date début')
    date_fin = models.DateField(verbose_name='Date fin')
    duree_mois = models.PositiveIntegerField(verbose_name='Durée (mois)')

    # Conditions financières
    loyer_mensuel = models.DecimalField(max_digits=12, decimal_places=2, verbose_name='Loyer mensuel')
    charges_mensuelles = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    depot_garantie = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    depot_verse = models.BooleanField(default=False, verbose_name='Dépôt versé')

    # Paiement
    jour_paiement = models.PositiveIntegerField(default=5, verbose_name='Jour de paiement')
    mode_paiement = models.CharField(
        max_length=20,
        choices=[
            ('especes', 'Espèces'),
            ('cheque', 'Chèque'),
            ('virement', 'Virement'),
            ('mobile_money', 'Mobile Money'),
        ],
        default='especes'
    )

    # Révision
    date_derniere_revision = models.DateField(blank=True, null=True)
    taux_revision = models.DecimalField(max_digits=5, decimal_places=2, default=0, verbose_name='Taux révision (%)')

    statut = models.CharField(max_length=20, choices=STATUTS, default='actif')
    motif_fin = models.TextField(blank=True, null=True, verbose_name='Motif fin de bail')

    # Lien vers les dossiers contentieux (impayés, expulsions, etc.)
    dossiers_contentieux = models.ManyToManyField(
        'gestion.Dossier',
        blank=True,
        related_name='baux_gerance',
        verbose_name='Dossiers contentieux',
        help_text='Dossiers contentieux liés à ce bail (impayés, procédures d\'expulsion, etc.)'
    )

    notes = models.TextField(blank=True, null=True)

    cree_le = models.DateTimeField(auto_now_add=True)
    modifie_le = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Bail'
        verbose_name_plural = 'Baux'
        ordering = ['-date_debut']

    def __str__(self):
        return f"Bail {self.reference} - {self.bien.designation}"

    @property
    def loyer_total(self):
        return self.loyer_mensuel + self.charges_mensuelles


class Loyer(models.Model):
    """Loyer mensuel"""
    STATUTS = [
        ('a_payer', 'À payer'),
        ('paye', 'Payé'),
        ('partiel', 'Partiellement payé'),
        ('retard', 'En retard'),
        ('impaye', 'Impayé'),
        ('annule', 'Annulé'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    bail = models.ForeignKey(Bail, on_delete=models.CASCADE, related_name='loyers')

    # Période
    mois = models.PositiveIntegerField(verbose_name='Mois (1-12)')
    annee = models.PositiveIntegerField(verbose_name='Année')
    date_echeance = models.DateField(verbose_name='Date échéance')

    # Montants
    montant_loyer = models.DecimalField(max_digits=12, decimal_places=2)
    montant_charges = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    montant_total = models.DecimalField(max_digits=12, decimal_places=2)
    montant_paye = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    reste_a_payer = models.DecimalField(max_digits=12, decimal_places=2)

    # Pénalités
    penalites = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    statut = models.CharField(max_length=20, choices=STATUTS, default='a_payer')
    date_paiement = models.DateField(blank=True, null=True)

    notes = models.TextField(blank=True, null=True)

    cree_le = models.DateTimeField(auto_now_add=True)
    modifie_le = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Loyer'
        verbose_name_plural = 'Loyers'
        ordering = ['-annee', '-mois']
        unique_together = ['bail', 'mois', 'annee']

    def __str__(self):
        return f"Loyer {self.mois}/{self.annee} - {self.bail.bien.designation}"

    def save(self, *args, **kwargs):
        self.reste_a_payer = self.montant_total - self.montant_paye
        if self.reste_a_payer <= 0:
            self.statut = 'paye'
        elif self.montant_paye > 0:
            self.statut = 'partiel'
        elif self.date_echeance < timezone.now().date():
            self.statut = 'retard'
        super().save(*args, **kwargs)


class Quittance(models.Model):
    """Quittance de loyer"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    loyer = models.ForeignKey(Loyer, on_delete=models.CASCADE, related_name='quittances')

    numero = models.CharField(max_length=50, unique=True)
    date_emission = models.DateField(default=timezone.now)
    montant = models.DecimalField(max_digits=12, decimal_places=2)

    # Période couverte
    periode_debut = models.DateField()
    periode_fin = models.DateField()

    cree_le = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Quittance'
        verbose_name_plural = 'Quittances'
        ordering = ['-date_emission']

    def __str__(self):
        return f"Quittance {self.numero}"


class EtatDesLieux(models.Model):
    """État des lieux"""
    TYPES = [
        ('entree', 'Entrée'),
        ('sortie', 'Sortie'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    bail = models.ForeignKey(Bail, on_delete=models.CASCADE, related_name='etats_lieux')
    type_etat = models.CharField(max_length=10, choices=TYPES)

    date_etat = models.DateField(default=timezone.now)

    # Relevés compteurs
    compteur_eau = models.CharField(max_length=50, blank=True, null=True)
    compteur_electricite = models.CharField(max_length=50, blank=True, null=True)
    compteur_gaz = models.CharField(max_length=50, blank=True, null=True)

    # Observations par pièce
    observations = models.JSONField(default=dict)

    # Clés remises
    nombre_cles = models.PositiveIntegerField(default=0)
    detail_cles = models.TextField(blank=True, null=True)

    etat_general = models.CharField(
        max_length=20,
        choices=[
            ('excellent', 'Excellent'),
            ('bon', 'Bon'),
            ('moyen', 'Moyen'),
            ('mauvais', 'Mauvais'),
        ],
        default='bon'
    )

    # Signatures
    signe_bailleur = models.BooleanField(default=False)
    signe_locataire = models.BooleanField(default=False)
    date_signature = models.DateField(blank=True, null=True)

    notes = models.TextField(blank=True, null=True)

    cree_le = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'État des lieux'
        verbose_name_plural = 'États des lieux'
        ordering = ['-date_etat']

    def __str__(self):
        return f"EDL {self.get_type_etat_display()} - {self.bail.bien.designation}"


class Incident(models.Model):
    """Incident / Sinistre / Travaux"""
    TYPES = [
        ('panne', 'Panne'),
        ('sinistre', 'Sinistre'),
        ('travaux', 'Travaux'),
        ('reclamation', 'Réclamation'),
        ('autre', 'Autre'),
    ]

    PRIORITES = [
        ('basse', 'Basse'),
        ('normale', 'Normale'),
        ('haute', 'Haute'),
        ('urgente', 'Urgente'),
    ]

    STATUTS = [
        ('signale', 'Signalé'),
        ('en_cours', 'En cours'),
        ('resolu', 'Résolu'),
        ('annule', 'Annulé'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    bien = models.ForeignKey(BienImmobilier, on_delete=models.CASCADE, related_name='incidents')
    bail = models.ForeignKey(Bail, on_delete=models.SET_NULL, null=True, blank=True, related_name='incidents')

    # LIEN VERS UN DOSSIER JURIDIQUE (si procédure)
    dossier = models.ForeignKey(
        'gestion.Dossier',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='incidents_gerance',
        verbose_name="Dossier juridique"
    )

    type_incident = models.CharField(max_length=20, choices=TYPES, default='panne')
    priorite = models.CharField(max_length=20, choices=PRIORITES, default='normale')

    titre = models.CharField(max_length=200)
    description = models.TextField()

    date_signalement = models.DateTimeField(default=timezone.now)
    date_resolution = models.DateTimeField(blank=True, null=True)

    # Coûts
    cout_estime = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    cout_reel = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    a_charge_de = models.CharField(
        max_length=20,
        choices=[
            ('proprietaire', 'Propriétaire'),
            ('locataire', 'Locataire'),
            ('partage', 'Partagé'),
        ],
        default='proprietaire'
    )

    # Intervenants
    intervenant = models.CharField(max_length=200, blank=True, null=True)
    telephone_intervenant = models.CharField(max_length=20, blank=True, null=True)

    statut = models.CharField(max_length=20, choices=STATUTS, default='signale')
    notes = models.TextField(blank=True, null=True)

    cree_le = models.DateTimeField(auto_now_add=True)
    modifie_le = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Incident'
        verbose_name_plural = 'Incidents'
        ordering = ['-date_signalement']

    def __str__(self):
        return f"{self.titre} - {self.bien.designation}"


class ReversementProprietaire(models.Model):
    """Reversement au propriétaire"""
    STATUTS = [
        ('en_attente', 'En attente'),
        ('effectue', 'Effectué'),
        ('annule', 'Annulé'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    proprietaire = models.ForeignKey(Proprietaire, on_delete=models.PROTECT, related_name='reversements')

    # Période
    mois = models.PositiveIntegerField()
    annee = models.PositiveIntegerField()

    # Montants
    total_loyers = models.DecimalField(max_digits=12, decimal_places=2, verbose_name='Total loyers encaissés')
    honoraires = models.DecimalField(max_digits=12, decimal_places=2, verbose_name='Honoraires de gestion')
    autres_deductions = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    montant_reverse = models.DecimalField(max_digits=12, decimal_places=2, verbose_name='Montant reversé')

    date_reversement = models.DateField(blank=True, null=True)
    mode_reversement = models.CharField(
        max_length=20,
        choices=[
            ('virement', 'Virement'),
            ('cheque', 'Chèque'),
            ('especes', 'Espèces'),
        ],
        default='virement'
    )
    reference_paiement = models.CharField(max_length=100, blank=True, null=True)

    statut = models.CharField(max_length=20, choices=STATUTS, default='en_attente')
    notes = models.TextField(blank=True, null=True)

    cree_le = models.DateTimeField(auto_now_add=True)
    modifie_le = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Reversement propriétaire'
        verbose_name_plural = 'Reversements propriétaires'
        ordering = ['-annee', '-mois']
        unique_together = ['proprietaire', 'mois', 'annee']

    def __str__(self):
        return f"Reversement {self.mois}/{self.annee} - {self.proprietaire.nom}"
