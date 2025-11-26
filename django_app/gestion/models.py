from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
import json


class Utilisateur(AbstractUser):
    """Modèle utilisateur personnalisé"""
    ROLE_CHOICES = [
        ('admin', 'Administrateur'),
        ('huissier', 'Huissier'),
        ('clerc_principal', 'Clerc Principal'),
        ('clerc', 'Clerc'),
        ('secretaire', 'Secrétaire'),
    ]
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='clerc')
    telephone = models.CharField(max_length=20, blank=True)

    class Meta:
        verbose_name = 'Utilisateur'
        verbose_name_plural = 'Utilisateurs'

    def __str__(self):
        return f"{self.first_name} {self.last_name}" if self.first_name else self.username

    def get_initials(self):
        if self.first_name and self.last_name:
            return f"{self.first_name[0]}{self.last_name[0]}".upper()
        return self.username[:2].upper()


class Collaborateur(models.Model):
    """Collaborateurs de l'étude"""
    ROLE_CHOICES = [
        ('huissier', 'Huissier'),
        ('clerc_principal', 'Clerc Principal'),
        ('clerc', 'Clerc'),
        ('secretaire', 'Secrétaire'),
    ]
    nom = models.CharField(max_length=100)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    email = models.EmailField(blank=True)
    telephone = models.CharField(max_length=20, blank=True)
    actif = models.BooleanField(default=True)
    utilisateur = models.OneToOneField(
        Utilisateur, on_delete=models.SET_NULL, null=True, blank=True, related_name='collaborateur'
    )

    class Meta:
        verbose_name = 'Collaborateur'
        verbose_name_plural = 'Collaborateurs'

    def __str__(self):
        return self.nom


class Partie(models.Model):
    """Parties (demandeur ou défendeur) d'un dossier"""
    TYPE_PERSONNE_CHOICES = [
        ('physique', 'Personne physique'),
        ('morale', 'Personne morale'),
    ]
    FORME_JURIDIQUE_CHOICES = [
        ('SARL', 'SARL'),
        ('SA', 'SA'),
        ('SAS', 'SAS'),
        ('SNC', 'SNC'),
        ('GIE', 'GIE'),
        ('AUTRE', 'Autre'),
    ]

    type_personne = models.CharField(max_length=10, choices=TYPE_PERSONNE_CHOICES, default='physique')

    # Personne physique
    nom = models.CharField(max_length=100, blank=True)
    prenoms = models.CharField(max_length=150, blank=True)
    nationalite = models.CharField(max_length=50, blank=True, default='Béninoise')
    profession = models.CharField(max_length=100, blank=True)
    domicile = models.TextField(blank=True)

    # Personne morale
    denomination = models.CharField(max_length=200, blank=True)
    capital_social = models.DecimalField(max_digits=15, decimal_places=0, null=True, blank=True)
    forme_juridique = models.CharField(max_length=10, choices=FORME_JURIDIQUE_CHOICES, blank=True)
    siege_social = models.TextField(blank=True)
    representant = models.CharField(max_length=150, blank=True)

    # Commun
    telephone = models.CharField(max_length=20, blank=True)
    ifu = models.CharField(max_length=20, blank=True, verbose_name='IFU')

    class Meta:
        verbose_name = 'Partie'
        verbose_name_plural = 'Parties'

    def __str__(self):
        if self.type_personne == 'morale':
            return self.denomination or 'Personne morale sans nom'
        return f"{self.nom} {self.prenoms}".strip() or 'Personne physique sans nom'

    def get_nom_complet(self):
        if self.type_personne == 'morale':
            return self.denomination
        return f"{self.nom} {self.prenoms}".strip()


class Dossier(models.Model):
    """Dossier de l'étude"""
    TYPE_DOSSIER_CHOICES = [
        ('recouvrement', 'Recouvrement'),
        ('expulsion', 'Expulsion'),
        ('constat', 'Constat'),
        ('signification', 'Signification'),
        ('saisie', 'Saisie'),
        ('autre', 'Autre'),
    ]
    STATUT_CHOICES = [
        ('actif', 'Actif'),
        ('urgent', 'Urgent'),
        ('archive', 'Archivé'),
        ('cloture', 'Clôturé'),
    ]

    reference = models.CharField(max_length=20, unique=True)
    is_contentieux = models.BooleanField(default=False, verbose_name='Contentieux')
    type_dossier = models.CharField(max_length=20, choices=TYPE_DOSSIER_CHOICES, blank=True)
    description = models.TextField(blank=True)
    montant_creance = models.DecimalField(max_digits=15, decimal_places=0, null=True, blank=True)
    date_creance = models.DateField(null=True, blank=True)
    date_ouverture = models.DateField(default=timezone.now)
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default='actif')

    affecte_a = models.ForeignKey(
        Collaborateur, on_delete=models.SET_NULL, null=True, blank=True, related_name='dossiers'
    )
    demandeurs = models.ManyToManyField(Partie, related_name='dossiers_demandeur', blank=True)
    defendeurs = models.ManyToManyField(Partie, related_name='dossiers_defendeur', blank=True)

    cree_par = models.ForeignKey(
        Utilisateur, on_delete=models.SET_NULL, null=True, related_name='dossiers_crees'
    )
    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Dossier'
        verbose_name_plural = 'Dossiers'
        ordering = ['-date_creation']

    def __str__(self):
        return f"{self.reference} - {self.get_intitule()}"

    def get_intitule(self):
        demandeur = self.demandeurs.first()
        defendeur = self.defendeurs.first()
        if self.is_contentieux and demandeur and defendeur:
            return f"{demandeur.get_nom_complet()} C/ {defendeur.get_nom_complet()}"
        elif demandeur:
            return demandeur.get_nom_complet()
        return "Sans parties"

    @classmethod
    def generer_reference(cls):
        now = timezone.now()
        prefix = 175  # Numéro de la loi
        mois = str(now.month).zfill(2)
        annee = str(now.year)[-2:]
        suffix = "MAB"  # Initiales de l'huissier

        # Trouver le prochain numéro
        derniers = cls.objects.filter(
            reference__startswith=f"{prefix}_{mois}{annee}"
        ).count()

        return f"{prefix + derniers}_{mois}{annee}_{suffix}"


class Facture(models.Model):
    """Factures de l'étude"""
    STATUT_CHOICES = [
        ('brouillon', 'Brouillon'),
        ('attente', 'En attente'),
        ('payee', 'Payée'),
        ('annulee', 'Annulée'),
    ]

    numero = models.CharField(max_length=20, unique=True)
    dossier = models.ForeignKey(
        Dossier, on_delete=models.SET_NULL, null=True, blank=True, related_name='factures'
    )
    client = models.CharField(max_length=200)
    montant_ht = models.DecimalField(max_digits=15, decimal_places=0)
    taux_tva = models.DecimalField(max_digits=5, decimal_places=2, default=18.00)
    montant_tva = models.DecimalField(max_digits=15, decimal_places=0)
    montant_ttc = models.DecimalField(max_digits=15, decimal_places=0)
    date_emission = models.DateField(default=timezone.now)
    date_echeance = models.DateField(null=True, blank=True)
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default='attente')

    mecef_qr = models.TextField(blank=True, verbose_name='QR Code MECeF')
    mecef_numero = models.CharField(max_length=50, blank=True, verbose_name='Numéro MECeF')

    date_creation = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Facture'
        verbose_name_plural = 'Factures'
        ordering = ['-date_emission']

    def __str__(self):
        return f"{self.numero} - {self.client}"

    def save(self, *args, **kwargs):
        if not self.montant_tva:
            self.montant_tva = self.montant_ht * self.taux_tva / 100
        if not self.montant_ttc:
            self.montant_ttc = self.montant_ht + self.montant_tva
        super().save(*args, **kwargs)

    @classmethod
    def generer_numero(cls):
        now = timezone.now()
        count = cls.objects.filter(date_emission__year=now.year).count() + 1
        return f"FAC-{now.year}-{str(count).zfill(3)}"


class ActeProcedure(models.Model):
    """Actes de procédure du catalogue"""
    code = models.CharField(max_length=20, unique=True)
    libelle = models.CharField(max_length=200)
    tarif = models.DecimalField(max_digits=10, decimal_places=0)
    actif = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'Acte de procédure'
        verbose_name_plural = 'Actes de procédure'
        ordering = ['libelle']

    def __str__(self):
        return f"{self.libelle} ({self.tarif:,.0f} FCFA)"


class HistoriqueCalcul(models.Model):
    """Historique des calculs de recouvrement"""
    MODE_CHOICES = [
        ('complet', 'Calcul complet'),
        ('emoluments', 'Émoluments seuls'),
    ]

    nom = models.CharField(max_length=200)
    mode = models.CharField(max_length=20, choices=MODE_CHOICES)
    donnees = models.JSONField()  # Stocke toutes les données du calcul
    resultats = models.JSONField()  # Stocke les résultats
    total = models.DecimalField(max_digits=15, decimal_places=0)

    utilisateur = models.ForeignKey(
        Utilisateur, on_delete=models.SET_NULL, null=True, related_name='calculs'
    )
    date_creation = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Historique de calcul'
        verbose_name_plural = 'Historiques de calculs'
        ordering = ['-date_creation']

    def __str__(self):
        return f"{self.nom} - {self.total:,.0f} FCFA"


class TauxLegal(models.Model):
    """Taux légaux UEMOA par année"""
    annee = models.IntegerField(unique=True)
    taux = models.DecimalField(max_digits=6, decimal_places=4)
    source = models.CharField(max_length=100, default='BCEAO')

    class Meta:
        verbose_name = 'Taux légal'
        verbose_name_plural = 'Taux légaux'
        ordering = ['-annee']

    def __str__(self):
        return f"{self.annee}: {self.taux}%"


class MessageChatbot(models.Model):
    """Messages du chatbot pour l'historique"""
    TYPE_CHOICES = [
        ('bot', 'Bot'),
        ('user', 'Utilisateur'),
    ]

    session_id = models.CharField(max_length=100)
    type_message = models.CharField(max_length=10, choices=TYPE_CHOICES)
    contenu = models.TextField()
    date_creation = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Message chatbot'
        verbose_name_plural = 'Messages chatbot'
        ordering = ['date_creation']
