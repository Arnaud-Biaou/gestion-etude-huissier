"""
Modèles pour l'import de données depuis l'ancienne application.
Tables temporaires pour validation avant import définitif.
"""
from django.db import models
from django.conf import settings
import json


class SessionImport(models.Model):
    """Session d'import de données"""

    STATUT_CHOICES = [
        ('en_cours', 'En cours'),
        ('analyse', 'Analyse terminée'),
        ('valide', 'Validé'),
        ('importe', 'Importé'),
        ('erreur', 'Erreur'),
        ('annule', 'Annulé'),
    ]

    SOURCE_CHOICES = [
        ('sql_file', 'Fichier SQL'),
        ('csv', 'Fichier CSV'),
        ('excel', 'Fichier Excel'),
        ('direct_db', 'Connexion directe base'),
    ]

    # Identification
    nom = models.CharField(max_length=200, verbose_name="Nom de la session")
    source_type = models.CharField(max_length=20, choices=SOURCE_CHOICES)
    fichier_source = models.FileField(upload_to='imports/', null=True, blank=True)

    # Statistiques
    total_lignes = models.PositiveIntegerField(default=0)
    dossiers_trouves = models.PositiveIntegerField(default=0)
    parties_trouvees = models.PositiveIntegerField(default=0)
    doublons_detectes = models.PositiveIntegerField(default=0)
    erreurs_detectees = models.PositiveIntegerField(default=0)

    # Statut
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default='en_cours')
    progression = models.PositiveIntegerField(default=0, help_text="Pourcentage de progression")

    # Rapport
    rapport_json = models.TextField(blank=True, help_text="Rapport détaillé en JSON")

    # Métadonnées
    cree_par = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Session d'import"
        verbose_name_plural = "Sessions d'import"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.nom} ({self.get_statut_display()})"

    def get_rapport(self):
        if self.rapport_json:
            return json.loads(self.rapport_json)
        return {}

    def set_rapport(self, rapport_dict):
        self.rapport_json = json.dumps(rapport_dict, ensure_ascii=False, default=str)
        self.save()


class DossierImportTemp(models.Model):
    """Dossier temporaire en attente de validation"""

    STATUT_CHOICES = [
        ('en_attente', 'En attente de validation'),
        ('valide', 'Validé'),
        ('importe', 'Importé'),
        ('doublon', 'Doublon détecté'),
        ('erreur', 'Erreur'),
        ('ignore', 'Ignoré'),
    ]

    session = models.ForeignKey(SessionImport, on_delete=models.CASCADE, related_name='dossiers_temp')

    # Données brutes de l'ancienne base
    reference_originale = models.CharField(max_length=500, verbose_name="Référence originale")
    donnees_brutes = models.TextField(blank=True, help_text="Données JSON brutes")

    # Données parsées
    numero_ordre = models.CharField(max_length=20, blank=True)
    mois_creation = models.PositiveIntegerField(null=True, blank=True)
    annee_creation = models.PositiveIntegerField(null=True, blank=True)
    date_ouverture = models.DateField(null=True, blank=True)

    # Parties extraites
    demandeur_nom = models.CharField(max_length=300, blank=True)
    demandeur_prenom = models.CharField(max_length=100, blank=True)
    demandeur_adresse = models.TextField(blank=True)
    demandeur_telephone = models.CharField(max_length=50, blank=True)
    demandeur_email = models.CharField(max_length=200, blank=True)

    defendeur_nom = models.CharField(max_length=300, blank=True)
    defendeur_prenom = models.CharField(max_length=100, blank=True)
    defendeur_adresse = models.TextField(blank=True)
    defendeur_telephone = models.CharField(max_length=50, blank=True)
    defendeur_email = models.CharField(max_length=200, blank=True)

    # Montants
    montant_principal = models.DecimalField(max_digits=15, decimal_places=0, null=True, blank=True)
    montant_interets = models.DecimalField(max_digits=15, decimal_places=0, null=True, blank=True)
    montant_frais = models.DecimalField(max_digits=15, decimal_places=0, null=True, blank=True)

    # Intitulé généré
    intitule_genere = models.CharField(max_length=500, blank=True)

    # Nouvelle référence proposée
    nouvelle_reference = models.CharField(max_length=100, blank=True)

    # Validation
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default='en_attente')
    message_erreur = models.TextField(blank=True)

    # Correspondances trouvées
    dossier_existant = models.ForeignKey(
        'gestion.Dossier',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='imports_correspondants',
        help_text="Dossier existant correspondant (si doublon)"
    )
    demandeur_existant = models.ForeignKey(
        'gestion.Partie',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='imports_demandeur'
    )
    defendeur_existant = models.ForeignKey(
        'gestion.Partie',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='imports_defendeur'
    )

    # Dossier créé après import
    dossier_cree = models.ForeignKey(
        'gestion.Dossier',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='import_source'
    )

    class Meta:
        verbose_name = "Dossier import temporaire"
        verbose_name_plural = "Dossiers import temporaires"
        ordering = ['annee_creation', 'mois_creation', 'numero_ordre']

    def __str__(self):
        return f"{self.reference_originale} → {self.get_statut_display()}"

    def get_donnees_brutes(self):
        if self.donnees_brutes:
            return json.loads(self.donnees_brutes)
        return {}
