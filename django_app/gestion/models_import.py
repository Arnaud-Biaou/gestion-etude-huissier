"""
Modèles pour l'import de données depuis l'ancienne application.
Tables TEMPORAIRES pour validation avant import définitif.
NE MODIFIE PAS les tables existantes.
"""
from django.db import models
from django.contrib.auth.models import User
import json


class SessionImport(models.Model):
    """Session d'import de données - Table temporaire"""

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
    ]

    # Identification
    nom = models.CharField(max_length=200, verbose_name="Nom de la session")
    source_type = models.CharField(max_length=20, choices=SOURCE_CHOICES, default='csv')
    fichier_source = models.FileField(upload_to='imports/', null=True, blank=True)

    # Statistiques
    total_lignes = models.PositiveIntegerField(default=0)
    dossiers_trouves = models.PositiveIntegerField(default=0)
    parties_trouvees = models.PositiveIntegerField(default=0)
    doublons_detectes = models.PositiveIntegerField(default=0)
    erreurs_detectees = models.PositiveIntegerField(default=0)

    # Statut
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default='en_cours')
    progression = models.PositiveIntegerField(default=0)

    # Rapport détaillé
    rapport_json = models.TextField(blank=True)

    # Métadonnées
    cree_par = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
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


class DossierImportTemp(models.Model):
    """
    Dossier temporaire en attente de validation.
    Cette table est INDÉPENDANTE de la table Dossier principale.
    Les données ne sont transférées qu'après validation manuelle.
    """

    STATUT_CHOICES = [
        ('en_attente', 'En attente de validation'),
        ('valide', 'Validé pour import'),
        ('importe', 'Importé avec succès'),
        ('doublon', 'Doublon détecté'),
        ('erreur', 'Erreur'),
        ('ignore', 'Ignoré manuellement'),
    ]

    session = models.ForeignKey(
        SessionImport,
        on_delete=models.CASCADE,
        related_name='dossiers_temp'
    )

    # ═══════════════════════════════════════════════════════════════
    # DONNÉES BRUTES DE L'ANCIENNE BASE
    # ═══════════════════════════════════════════════════════════════
    reference_originale = models.CharField(max_length=500, verbose_name="Référence originale")
    donnees_brutes_json = models.TextField(blank=True, help_text="Toutes les colonnes en JSON")

    # ═══════════════════════════════════════════════════════════════
    # DONNÉES PARSÉES DEPUIS LA RÉFÉRENCE
    # Format: REF_596_1125_MAB_AFF_YEKINI Djamal Dine_ctr_DJADOO
    # ═══════════════════════════════════════════════════════════════
    numero_ordre = models.CharField(max_length=20, blank=True)
    mois_creation = models.PositiveIntegerField(null=True, blank=True)
    annee_creation = models.PositiveIntegerField(null=True, blank=True)
    date_ouverture_parsee = models.DateField(null=True, blank=True)

    # ═══════════════════════════════════════════════════════════════
    # DEMANDEUR EXTRAIT
    # ═══════════════════════════════════════════════════════════════
    demandeur_texte_brut = models.CharField(max_length=500, blank=True)
    demandeur_nom = models.CharField(max_length=300, blank=True)
    demandeur_prenom = models.CharField(max_length=100, blank=True)
    demandeur_est_personne_morale = models.BooleanField(default=False)
    demandeur_raison_sociale = models.CharField(max_length=300, blank=True)
    demandeur_adresse = models.TextField(blank=True)
    demandeur_telephone = models.CharField(max_length=50, blank=True)
    demandeur_email = models.CharField(max_length=200, blank=True)

    # ═══════════════════════════════════════════════════════════════
    # DÉFENDEUR EXTRAIT
    # ═══════════════════════════════════════════════════════════════
    defendeur_texte_brut = models.CharField(max_length=500, blank=True)
    defendeur_nom = models.CharField(max_length=300, blank=True)
    defendeur_prenom = models.CharField(max_length=100, blank=True)
    defendeur_est_personne_morale = models.BooleanField(default=False)
    defendeur_raison_sociale = models.CharField(max_length=300, blank=True)
    defendeur_adresse = models.TextField(blank=True)
    defendeur_telephone = models.CharField(max_length=50, blank=True)
    defendeur_email = models.CharField(max_length=200, blank=True)

    # ═══════════════════════════════════════════════════════════════
    # MONTANTS (si disponibles dans l'ancienne base)
    # ═══════════════════════════════════════════════════════════════
    montant_principal = models.DecimalField(max_digits=15, decimal_places=0, null=True, blank=True)
    montant_interets = models.DecimalField(max_digits=15, decimal_places=0, null=True, blank=True)
    montant_frais = models.DecimalField(max_digits=15, decimal_places=0, null=True, blank=True)

    # ═══════════════════════════════════════════════════════════════
    # DONNÉES GÉNÉRÉES POUR LA NOUVELLE APPLICATION
    # ═══════════════════════════════════════════════════════════════
    intitule_genere = models.CharField(max_length=500, blank=True)
    nouvelle_reference = models.CharField(max_length=100, blank=True)

    # ═══════════════════════════════════════════════════════════════
    # VALIDATION ET CORRESPONDANCES
    # ═══════════════════════════════════════════════════════════════
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default='en_attente')
    message_validation = models.TextField(blank=True)

    # Parties existantes correspondantes (pour éviter les doublons)
    demandeur_existant_id = models.PositiveIntegerField(null=True, blank=True)
    demandeur_existant_nom = models.CharField(max_length=300, blank=True)
    demandeur_score_similarite = models.FloatField(null=True, blank=True)

    defendeur_existant_id = models.PositiveIntegerField(null=True, blank=True)
    defendeur_existant_nom = models.CharField(max_length=300, blank=True)
    defendeur_score_similarite = models.FloatField(null=True, blank=True)

    # Dossier existant correspondant (si doublon)
    dossier_existant_id = models.PositiveIntegerField(null=True, blank=True)
    dossier_existant_ref = models.CharField(max_length=100, blank=True)

    # Référence du dossier créé après import (pour traçabilité)
    dossier_cree_id = models.PositiveIntegerField(null=True, blank=True)

    class Meta:
        verbose_name = "Dossier import temporaire"
        verbose_name_plural = "Dossiers import temporaires"
        ordering = ['annee_creation', 'mois_creation', 'numero_ordre']

    def __str__(self):
        return f"{self.reference_originale} → {self.get_statut_display()}"

    def get_donnees_brutes(self):
        if self.donnees_brutes_json:
            return json.loads(self.donnees_brutes_json)
        return {}

    def set_donnees_brutes(self, donnees_dict):
        self.donnees_brutes_json = json.dumps(donnees_dict, ensure_ascii=False, default=str)
