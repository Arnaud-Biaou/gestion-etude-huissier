"""
Modèles pour le module Agenda - Gestion des rendez-vous et tâches
pour une étude d'huissier de justice au Bénin.

Auteur: Maître Martial Arnaud BIAOU
Licence: Propriétaire
"""

import uuid
from datetime import timedelta
from django.db import models
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType


# =============================================================================
# CHOIX ET CONSTANTES
# =============================================================================

class TypeRendezVous(models.TextChoices):
    """Types de rendez-vous disponibles"""
    RENDEZ_VOUS_CLIENT = 'rendez_vous_client', 'Rendez-vous client'
    AUDIENCE_TRIBUNAL = 'audience_tribunal', 'Audience tribunal'
    SIGNIFICATION = 'signification', "Signification d'acte"
    CONSTAT = 'constat', 'Constat'
    SAISIE = 'saisie', 'Saisie'
    EXPULSION = 'expulsion', 'Expulsion'
    REUNION_INTERNE = 'reunion_interne', 'Réunion interne'
    RENDEZ_VOUS_EXTERIEUR = 'rdv_exterieur', 'Rendez-vous extérieur'
    AUTRE = 'autre', 'Autre'


class TypeTache(models.TextChoices):
    """Types de tâches disponibles"""
    REDACTION_ACTE = 'redaction_acte', "Rédaction d'acte"
    SIGNIFICATION = 'signification', 'Signification'
    APPEL_TELEPHONIQUE = 'appel_telephonique', 'Appel téléphonique'
    ENVOI_COURRIER = 'envoi_courrier', 'Envoi de courrier'
    RELANCE = 'relance', 'Relance'
    RECHERCHE = 'recherche', 'Recherche / Vérification'
    PREPARATION_DOSSIER = 'preparation_dossier', 'Préparation de dossier'
    FACTURATION = 'facturation', 'Facturation'
    ENCAISSEMENT = 'encaissement', 'Encaissement'
    SUIVI_PROCEDURE = 'suivi_procedure', 'Suivi procédure'
    AUTRE = 'autre', 'Autre'


class StatutRendezVous(models.TextChoices):
    """Statuts possibles pour un rendez-vous"""
    PLANIFIE = 'planifie', 'Planifié'
    CONFIRME = 'confirme', 'Confirmé'
    EN_COURS = 'en_cours', 'En cours'
    TERMINE = 'termine', 'Terminé'
    REPORTE = 'reporte', 'Reporté'
    ANNULE = 'annule', 'Annulé'


class StatutTache(models.TextChoices):
    """Statuts possibles pour une tâche"""
    A_FAIRE = 'a_faire', 'À faire'
    EN_COURS = 'en_cours', 'En cours'
    EN_ATTENTE = 'en_attente', 'En attente (bloquée)'
    TERMINEE = 'terminee', 'Terminée'
    ANNULEE = 'annulee', 'Annulée'
    REPORTEE = 'reportee', 'Reportée'


class StatutDelegation(models.TextChoices):
    """Statuts de délégation d'une tâche"""
    ASSIGNEE = 'assignee', 'Assignée'
    ACCEPTEE = 'acceptee', 'Acceptée'
    EN_COURS = 'en_cours', 'En cours'
    TERMINEE = 'terminee', 'Terminée'
    REFUSEE = 'refusee', 'Refusée'
    VALIDEE = 'validee', 'Validée par l\'huissier'


class Priorite(models.TextChoices):
    """Niveaux de priorité"""
    BASSE = 'basse', 'Basse'
    NORMALE = 'normale', 'Normale'
    HAUTE = 'haute', 'Haute'
    URGENTE = 'urgente', 'Urgente'


class TypeRecurrence(models.TextChoices):
    """Types de récurrence"""
    UNIQUE = 'unique', 'Unique'
    QUOTIDIEN = 'quotidien', 'Quotidien'
    HEBDOMADAIRE = 'hebdomadaire', 'Hebdomadaire'
    MENSUEL = 'mensuel', 'Mensuel'
    PERSONNALISE = 'personnalise', 'Personnalisé'


class TypeNotification(models.TextChoices):
    """Types de notification"""
    EMAIL = 'email', 'Email'
    SMS = 'sms', 'SMS'
    APPLICATION = 'application', 'Notification dans l\'application'
    TOUS = 'tous', 'Tous les canaux'


class TypeRappel(models.TextChoices):
    """Types de rappel"""
    MINUTES_15 = '15min', '15 minutes avant'
    MINUTES_30 = '30min', '30 minutes avant'
    HEURE_1 = '1h', '1 heure avant'
    JOUR_1 = '1jour', '1 jour avant'
    PERSONNALISE = 'personnalise', 'Personnalisé'


# =============================================================================
# COULEURS POUR DISTINCTION VISUELLE
# =============================================================================

COULEURS_DISPONIBLES = [
    ('#3498db', 'Bleu'),
    ('#2ecc71', 'Vert'),
    ('#e74c3c', 'Rouge'),
    ('#f39c12', 'Orange'),
    ('#9b59b6', 'Violet'),
    ('#1abc9c', 'Turquoise'),
    ('#34495e', 'Gris foncé'),
    ('#e91e63', 'Rose'),
    ('#00bcd4', 'Cyan'),
    ('#ff5722', 'Orange foncé'),
    ('#795548', 'Marron'),
    ('#607d8b', 'Gris bleu'),
    ('#c6a962', 'Or'),  # Couleur de la charte graphique
    ('#1a365d', 'Bleu marine'),  # Couleur principale
]


# =============================================================================
# MODÈLES PRINCIPAUX
# =============================================================================

class Etiquette(models.Model):
    """Étiquettes personnalisées pour les tâches"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    nom = models.CharField(max_length=50, unique=True)
    couleur = models.CharField(max_length=7, default='#3498db')
    description = models.TextField(blank=True, null=True)
    createur = models.ForeignKey(
        'gestion.Utilisateur',
        on_delete=models.SET_NULL,
        null=True,
        related_name='etiquettes_creees'
    )
    date_creation = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['nom']
        verbose_name = 'Étiquette'
        verbose_name_plural = 'Étiquettes'

    def __str__(self):
        return self.nom


class ParticipantExterne(models.Model):
    """Participants externes aux rendez-vous (non-utilisateurs du système)"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    nom = models.CharField(max_length=200)
    email = models.EmailField(blank=True, null=True)
    telephone = models.CharField(max_length=20, blank=True, null=True)
    type_participant = models.CharField(
        max_length=50,
        choices=[
            ('client', 'Client'),
            ('debiteur', 'Débiteur'),
            ('avocat', 'Avocat'),
            ('notaire', 'Notaire'),
            ('expert', 'Expert'),
            ('temoin', 'Témoin'),
            ('autre', 'Autre'),
        ],
        default='autre'
    )
    notes = models.TextField(blank=True, null=True)
    partie_liee = models.ForeignKey(
        'gestion.Partie',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='participations_rdv'
    )
    date_creation = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['nom']
        verbose_name = 'Participant externe'
        verbose_name_plural = 'Participants externes'

    def __str__(self):
        return f"{self.nom} ({self.get_type_participant_display()})"


class RendezVous(models.Model):
    """
    Modèle principal pour les rendez-vous
    Gère tous les types de rendez-vous de l'étude
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Informations de base
    titre = models.CharField(max_length=255)
    type_rdv = models.CharField(
        max_length=30,
        choices=TypeRendezVous.choices,
        default=TypeRendezVous.RENDEZ_VOUS_CLIENT
    )
    description = models.TextField(blank=True, null=True)

    # Dates et heures
    date_debut = models.DateTimeField()
    date_fin = models.DateTimeField()
    journee_entiere = models.BooleanField(default=False)

    # Lieu
    lieu = models.CharField(max_length=255, blank=True, null=True)
    adresse = models.TextField(blank=True, null=True)
    latitude = models.DecimalField(
        max_digits=10,
        decimal_places=7,
        blank=True,
        null=True
    )
    longitude = models.DecimalField(
        max_digits=10,
        decimal_places=7,
        blank=True,
        null=True
    )

    # Liaison avec dossiers
    dossiers = models.ManyToManyField(
        'gestion.Dossier',
        blank=True,
        related_name='rendez_vous'
    )

    # Participants
    createur = models.ForeignKey(
        'gestion.Utilisateur',
        on_delete=models.CASCADE,
        related_name='rdv_crees'
    )
    collaborateurs_assignes = models.ManyToManyField(
        'gestion.Collaborateur',
        blank=True,
        related_name='rdv_assignes'
    )
    participants_externes = models.ManyToManyField(
        ParticipantExterne,
        blank=True,
        related_name='rendez_vous'
    )

    # Statut et priorité
    statut = models.CharField(
        max_length=20,
        choices=StatutRendezVous.choices,
        default=StatutRendezVous.PLANIFIE
    )
    priorite = models.CharField(
        max_length=10,
        choices=Priorite.choices,
        default=Priorite.NORMALE
    )
    couleur = models.CharField(max_length=7, default='#3498db')

    # Récurrence
    type_recurrence = models.CharField(
        max_length=20,
        choices=TypeRecurrence.choices,
        default=TypeRecurrence.UNIQUE
    )
    jours_semaine = models.JSONField(
        blank=True,
        null=True,
        help_text="Jours de la semaine pour récurrence hebdomadaire [0-6]"
    )
    jour_mois = models.IntegerField(
        blank=True,
        null=True,
        validators=[MinValueValidator(1), MaxValueValidator(31)]
    )
    date_fin_recurrence = models.DateField(blank=True, null=True)
    rdv_parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='occurrences'
    )

    # Métadonnées
    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)
    est_actif = models.BooleanField(default=True)

    class Meta:
        ordering = ['date_debut']
        verbose_name = 'Rendez-vous'
        verbose_name_plural = 'Rendez-vous'
        indexes = [
            models.Index(fields=['date_debut', 'statut']),
            models.Index(fields=['createur', 'date_debut']),
            models.Index(fields=['type_rdv', 'statut']),
        ]

    def __str__(self):
        return f"{self.titre} - {self.date_debut.strftime('%d/%m/%Y %H:%M')}"

    @property
    def duree(self):
        """Calcule la durée du rendez-vous en minutes"""
        if self.date_fin and self.date_debut:
            return int((self.date_fin - self.date_debut).total_seconds() / 60)
        return 0

    @property
    def est_passe(self):
        """Vérifie si le rendez-vous est passé"""
        return self.date_fin < timezone.now()

    @property
    def est_aujourdhui(self):
        """Vérifie si le rendez-vous est aujourd'hui"""
        today = timezone.now().date()
        return self.date_debut.date() == today

    def get_parties_concernees(self):
        """Retourne les parties concernées via les dossiers liés"""
        parties = set()
        for dossier in self.dossiers.all():
            parties.update(dossier.demandeurs.all())
            parties.update(dossier.defendeurs.all())
        return list(parties)


class DocumentRdv(models.Model):
    """Documents joints à un rendez-vous"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    rendez_vous = models.ForeignKey(
        RendezVous,
        on_delete=models.CASCADE,
        related_name='documents'
    )
    document = models.ForeignKey(
        'documents.Document',
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )
    fichier = models.FileField(
        upload_to='agenda/rdv_documents/',
        blank=True,
        null=True
    )
    nom = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    date_ajout = models.DateTimeField(auto_now_add=True)
    ajoute_par = models.ForeignKey(
        'gestion.Utilisateur',
        on_delete=models.SET_NULL,
        null=True
    )

    class Meta:
        ordering = ['-date_ajout']
        verbose_name = 'Document de rendez-vous'
        verbose_name_plural = 'Documents de rendez-vous'

    def __str__(self):
        return f"{self.nom} - {self.rendez_vous.titre}"


class RappelRdv(models.Model):
    """Rappels configurés pour un rendez-vous"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    rendez_vous = models.ForeignKey(
        RendezVous,
        on_delete=models.CASCADE,
        related_name='rappels'
    )
    type_rappel = models.CharField(
        max_length=20,
        choices=TypeRappel.choices,
        default=TypeRappel.HEURE_1
    )
    delai_personnalise = models.IntegerField(
        blank=True,
        null=True,
        help_text="Délai en minutes si type personnalisé"
    )
    type_notification = models.CharField(
        max_length=20,
        choices=TypeNotification.choices,
        default=TypeNotification.APPLICATION
    )
    est_envoye = models.BooleanField(default=False)
    date_envoi = models.DateTimeField(blank=True, null=True)
    destinataires = models.ManyToManyField(
        'gestion.Utilisateur',
        blank=True,
        related_name='rappels_rdv_recus'
    )

    class Meta:
        ordering = ['type_rappel']
        verbose_name = 'Rappel de rendez-vous'
        verbose_name_plural = 'Rappels de rendez-vous'

    def __str__(self):
        return f"Rappel {self.get_type_rappel_display()} - {self.rendez_vous.titre}"

    def get_date_rappel(self):
        """Calcule la date d'envoi du rappel"""
        delai_minutes = {
            TypeRappel.MINUTES_15: 15,
            TypeRappel.MINUTES_30: 30,
            TypeRappel.HEURE_1: 60,
            TypeRappel.JOUR_1: 24 * 60,
        }

        if self.type_rappel == TypeRappel.PERSONNALISE:
            minutes = self.delai_personnalise or 60
        else:
            minutes = delai_minutes.get(self.type_rappel, 60)

        return self.rendez_vous.date_debut - timedelta(minutes=minutes)


class Tache(models.Model):
    """
    Modèle principal pour les tâches
    Gère les tâches avec support de délégation et sous-tâches
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Informations de base
    titre = models.CharField(max_length=255)
    type_tache = models.CharField(
        max_length=30,
        choices=TypeTache.choices,
        default=TypeTache.AUTRE
    )
    description = models.TextField(blank=True, null=True)

    # Dates
    date_echeance = models.DateField()
    heure_echeance = models.TimeField(blank=True, null=True)
    date_debut = models.DateField(blank=True, null=True)

    # Liaison avec dossiers
    dossier = models.ForeignKey(
        'gestion.Dossier',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='taches'
    )
    partie_concernee = models.ForeignKey(
        'gestion.Partie',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='taches'
    )
    acte_lie = models.ForeignKey(
        'gestion.ActeProcedure',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='taches'
    )

    # Attribution
    createur = models.ForeignKey(
        'gestion.Utilisateur',
        on_delete=models.CASCADE,
        related_name='taches_creees'
    )
    responsable = models.ForeignKey(
        'gestion.Utilisateur',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='taches_assignees'
    )
    co_responsables = models.ManyToManyField(
        'gestion.Utilisateur',
        blank=True,
        related_name='taches_co_responsables'
    )
    date_delegation = models.DateTimeField(blank=True, null=True)

    # Priorité et catégorisation
    priorite = models.CharField(
        max_length=10,
        choices=Priorite.choices,
        default=Priorite.NORMALE
    )
    etiquettes = models.ManyToManyField(
        Etiquette,
        blank=True,
        related_name='taches'
    )
    couleur = models.CharField(max_length=7, default='#3498db')

    # Suivi
    temps_estime = models.IntegerField(
        blank=True,
        null=True,
        help_text="Temps estimé en minutes"
    )
    temps_passe = models.IntegerField(
        default=0,
        help_text="Temps passé en minutes"
    )
    progression = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )

    # Statut
    statut = models.CharField(
        max_length=20,
        choices=StatutTache.choices,
        default=StatutTache.A_FAIRE
    )
    statut_delegation = models.CharField(
        max_length=20,
        choices=StatutDelegation.choices,
        blank=True,
        null=True
    )

    # Récurrence
    type_recurrence = models.CharField(
        max_length=20,
        choices=TypeRecurrence.choices,
        default=TypeRecurrence.UNIQUE
    )
    jours_semaine = models.JSONField(blank=True, null=True)
    jour_mois = models.IntegerField(
        blank=True,
        null=True,
        validators=[MinValueValidator(1), MaxValueValidator(31)]
    )
    date_fin_recurrence = models.DateField(blank=True, null=True)
    tache_parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='occurrences_recurrentes'
    )

    # Hiérarchie (sous-tâches)
    tache_parente = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='sous_taches'
    )
    ordre = models.IntegerField(default=0)

    # Instructions de délégation
    instructions_delegation = models.TextField(blank=True, null=True)
    demande_compte_rendu = models.BooleanField(default=False)

    # Métadonnées
    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)
    date_terminaison = models.DateTimeField(blank=True, null=True)
    est_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['date_echeance', '-priorite', 'ordre']
        verbose_name = 'Tâche'
        verbose_name_plural = 'Tâches'
        indexes = [
            models.Index(fields=['date_echeance', 'statut']),
            models.Index(fields=['responsable', 'statut']),
            models.Index(fields=['createur', 'date_creation']),
            models.Index(fields=['tache_parente', 'ordre']),
        ]

    def __str__(self):
        return f"{self.titre} - {self.get_statut_display()}"

    @property
    def est_en_retard(self):
        """Vérifie si la tâche est en retard"""
        if self.statut in [StatutTache.TERMINEE, StatutTache.ANNULEE]:
            return False
        today = timezone.now().date()
        return self.date_echeance < today

    @property
    def est_aujourdhui(self):
        """Vérifie si l'échéance est aujourd'hui"""
        return self.date_echeance == timezone.now().date()

    @property
    def est_delegue(self):
        """Vérifie si la tâche est déléguée à quelqu'un d'autre"""
        return self.responsable is not None and self.responsable != self.createur

    @property
    def progression_calculee(self):
        """Calcule la progression basée sur les sous-tâches"""
        sous_taches = self.sous_taches.filter(est_active=True)
        if not sous_taches.exists():
            return self.progression

        total = sous_taches.count()
        terminees = sous_taches.filter(statut=StatutTache.TERMINEE).count()
        return int((terminees / total) * 100)

    def marquer_terminee(self, utilisateur=None):
        """Marque la tâche comme terminée"""
        self.statut = StatutTache.TERMINEE
        self.date_terminaison = timezone.now()
        self.progression = 100
        if self.est_delegue and self.statut_delegation:
            self.statut_delegation = StatutDelegation.TERMINEE
        self.save()


class SousTacheChecklist(models.Model):
    """Éléments de checklist pour une tâche"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tache = models.ForeignKey(
        Tache,
        on_delete=models.CASCADE,
        related_name='checklist_items'
    )
    libelle = models.CharField(max_length=255)
    est_complete = models.BooleanField(default=False)
    ordre = models.IntegerField(default=0)
    date_completion = models.DateTimeField(blank=True, null=True)
    complete_par = models.ForeignKey(
        'gestion.Utilisateur',
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    class Meta:
        ordering = ['ordre', 'id']
        verbose_name = 'Élément de checklist'
        verbose_name_plural = 'Éléments de checklist'

    def __str__(self):
        status = "✓" if self.est_complete else "○"
        return f"{status} {self.libelle}"


class CommentaireTache(models.Model):
    """Commentaires et notes de suivi pour les tâches"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tache = models.ForeignKey(
        Tache,
        on_delete=models.CASCADE,
        related_name='commentaires'
    )
    auteur = models.ForeignKey(
        'gestion.Utilisateur',
        on_delete=models.CASCADE,
        related_name='commentaires_taches'
    )
    contenu = models.TextField()
    type_commentaire = models.CharField(
        max_length=30,
        choices=[
            ('commentaire', 'Commentaire'),
            ('question', 'Question'),
            ('reponse', 'Réponse'),
            ('compte_rendu', 'Compte-rendu'),
            ('demande_aide', "Demande d'aide"),
            ('validation', 'Validation'),
        ],
        default='commentaire'
    )
    date_creation = models.DateTimeField(auto_now_add=True)
    est_prive = models.BooleanField(default=False)

    class Meta:
        ordering = ['-date_creation']
        verbose_name = 'Commentaire de tâche'
        verbose_name_plural = 'Commentaires de tâches'

    def __str__(self):
        return f"Commentaire de {self.auteur} sur {self.tache.titre}"


class DocumentTache(models.Model):
    """Documents joints à une tâche"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tache = models.ForeignKey(
        Tache,
        on_delete=models.CASCADE,
        related_name='documents'
    )
    document = models.ForeignKey(
        'documents.Document',
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )
    fichier = models.FileField(
        upload_to='agenda/tache_documents/',
        blank=True,
        null=True
    )
    nom = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    date_ajout = models.DateTimeField(auto_now_add=True)
    ajoute_par = models.ForeignKey(
        'gestion.Utilisateur',
        on_delete=models.SET_NULL,
        null=True
    )

    class Meta:
        ordering = ['-date_ajout']
        verbose_name = 'Document de tâche'
        verbose_name_plural = 'Documents de tâche'

    def __str__(self):
        return f"{self.nom} - {self.tache.titre}"


class RappelTache(models.Model):
    """Rappels configurés pour une tâche"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tache = models.ForeignKey(
        Tache,
        on_delete=models.CASCADE,
        related_name='rappels'
    )
    type_rappel = models.CharField(
        max_length=20,
        choices=[
            ('jour_echeance', "Jour de l'échéance"),
            ('veille', 'La veille'),
            ('2jours', '2 jours avant'),
            ('semaine', 'Une semaine avant'),
            ('personnalise', 'Personnalisé'),
        ],
        default='jour_echeance'
    )
    delai_personnalise = models.IntegerField(
        blank=True,
        null=True,
        help_text="Délai en jours si type personnalisé"
    )
    type_notification = models.CharField(
        max_length=20,
        choices=TypeNotification.choices,
        default=TypeNotification.APPLICATION
    )
    est_envoye = models.BooleanField(default=False)
    date_envoi = models.DateTimeField(blank=True, null=True)

    class Meta:
        ordering = ['type_rappel']
        verbose_name = 'Rappel de tâche'
        verbose_name_plural = 'Rappels de tâche'

    def __str__(self):
        return f"Rappel {self.get_type_rappel_display()} - {self.tache.titre}"


# =============================================================================
# NOTIFICATIONS
# =============================================================================

class Notification(models.Model):
    """Notifications système pour agenda"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    destinataire = models.ForeignKey(
        'gestion.Utilisateur',
        on_delete=models.CASCADE,
        related_name='notifications_agenda'
    )
    titre = models.CharField(max_length=255)
    message = models.TextField()
    type_notification = models.CharField(
        max_length=30,
        choices=[
            ('nouveau_rdv', 'Nouveau rendez-vous assigné'),
            ('nouvelle_tache', 'Nouvelle tâche déléguée'),
            ('rappel_rdv', 'Rappel de rendez-vous'),
            ('rappel_tache', 'Rappel de tâche'),
            ('tache_retard', 'Tâche en retard'),
            ('tache_terminee', 'Tâche terminée'),
            ('demande_aide', "Demande d'aide"),
            ('commentaire', 'Nouveau commentaire'),
            ('report', 'Report automatique'),
            ('bilan_journee', 'Bilan de journée'),
            ('autre', 'Autre'),
        ],
        default='autre'
    )

    # Lien générique vers l'objet concerné
    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )
    object_id = models.CharField(max_length=36, null=True, blank=True)
    objet = GenericForeignKey('content_type', 'object_id')

    est_lu = models.BooleanField(default=False)
    date_lecture = models.DateTimeField(blank=True, null=True)
    date_creation = models.DateTimeField(auto_now_add=True)

    # Canal de notification
    canal = models.CharField(
        max_length=20,
        choices=TypeNotification.choices,
        default=TypeNotification.APPLICATION
    )
    est_envoye_email = models.BooleanField(default=False)
    est_envoye_sms = models.BooleanField(default=False)

    class Meta:
        ordering = ['-date_creation']
        verbose_name = 'Notification'
        verbose_name_plural = 'Notifications'
        indexes = [
            models.Index(fields=['destinataire', 'est_lu']),
            models.Index(fields=['date_creation']),
        ]

    def __str__(self):
        return f"{self.titre} - {self.destinataire}"

    def marquer_lu(self):
        """Marque la notification comme lue"""
        if not self.est_lu:
            self.est_lu = True
            self.date_lecture = timezone.now()
            self.save()


# =============================================================================
# JOURNÉE ET CLÔTURE
# =============================================================================

class JourneeAgenda(models.Model):
    """
    Enregistrement d'une journée de travail avec bilan
    Permet la clôture automatique et manuelle
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    date = models.DateField(unique=True)
    utilisateur = models.ForeignKey(
        'gestion.Utilisateur',
        on_delete=models.CASCADE,
        related_name='journees_agenda',
        null=True,
        blank=True,
        help_text="NULL = journée globale de l'étude"
    )

    # Statistiques
    nb_rdv_prevus = models.IntegerField(default=0)
    nb_rdv_termines = models.IntegerField(default=0)
    nb_rdv_annules = models.IntegerField(default=0)
    nb_taches_prevues = models.IntegerField(default=0)
    nb_taches_terminees = models.IntegerField(default=0)
    nb_taches_reportees = models.IntegerField(default=0)

    # Clôture
    est_cloturee = models.BooleanField(default=False)
    date_cloture = models.DateTimeField(blank=True, null=True)
    cloture_par = models.ForeignKey(
        'gestion.Utilisateur',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='journees_cloturees'
    )
    type_cloture = models.CharField(
        max_length=20,
        choices=[
            ('automatique', 'Automatique'),
            ('manuelle', 'Manuelle'),
        ],
        blank=True,
        null=True
    )

    # Commentaires de clôture
    commentaire_cloture = models.TextField(blank=True, null=True)
    bilan_json = models.JSONField(blank=True, null=True)

    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-date']
        verbose_name = 'Journée agenda'
        verbose_name_plural = 'Journées agenda'
        unique_together = ['date', 'utilisateur']

    def __str__(self):
        user = self.utilisateur.get_full_name() if self.utilisateur else "Global"
        return f"Journée du {self.date.strftime('%d/%m/%Y')} - {user}"

    def calculer_statistiques(self):
        """Calcule les statistiques de la journée"""
        from django.db.models import Q

        date_debut = timezone.make_aware(
            timezone.datetime.combine(self.date, timezone.datetime.min.time())
        )
        date_fin = timezone.make_aware(
            timezone.datetime.combine(self.date, timezone.datetime.max.time())
        )

        # Filtrer par utilisateur si défini
        rdv_filter = Q(date_debut__range=[date_debut, date_fin])
        tache_filter = Q(date_echeance=self.date)

        if self.utilisateur:
            rdv_filter &= (
                Q(createur=self.utilisateur) |
                Q(collaborateurs_assignes__utilisateur=self.utilisateur)
            )
            tache_filter &= (
                Q(createur=self.utilisateur) |
                Q(responsable=self.utilisateur)
            )

        # Rendez-vous
        rdv = RendezVous.objects.filter(rdv_filter)
        self.nb_rdv_prevus = rdv.count()
        self.nb_rdv_termines = rdv.filter(statut=StatutRendezVous.TERMINE).count()
        self.nb_rdv_annules = rdv.filter(statut=StatutRendezVous.ANNULE).count()

        # Tâches
        taches = Tache.objects.filter(tache_filter)
        self.nb_taches_prevues = taches.count()
        self.nb_taches_terminees = taches.filter(statut=StatutTache.TERMINEE).count()
        self.nb_taches_reportees = taches.filter(statut=StatutTache.REPORTEE).count()

        self.save()

    def cloturer(self, utilisateur=None, type_cloture='manuelle', commentaire=None):
        """Clôture la journée et reporte les tâches non terminées"""
        self.calculer_statistiques()
        self.est_cloturee = True
        self.date_cloture = timezone.now()
        self.cloture_par = utilisateur
        self.type_cloture = type_cloture
        self.commentaire_cloture = commentaire

        # Générer le bilan JSON
        self.bilan_json = {
            'rdv': {
                'prevus': self.nb_rdv_prevus,
                'termines': self.nb_rdv_termines,
                'annules': self.nb_rdv_annules,
            },
            'taches': {
                'prevues': self.nb_taches_prevues,
                'terminees': self.nb_taches_terminees,
                'reportees': self.nb_taches_reportees,
            },
            'taux_realisation': self._calculer_taux_realisation(),
        }

        self.save()

        # Reporter les tâches non terminées
        self._reporter_taches_non_terminees()

    def _calculer_taux_realisation(self):
        """Calcule le taux de réalisation global"""
        total = self.nb_rdv_prevus + self.nb_taches_prevues
        if total == 0:
            return 100
        termines = self.nb_rdv_termines + self.nb_taches_terminees
        return round((termines / total) * 100, 1)

    def _reporter_taches_non_terminees(self):
        """Reporte les tâches non terminées au lendemain"""
        from django.db.models import Q

        tache_filter = Q(date_echeance=self.date) & ~Q(
            statut__in=[StatutTache.TERMINEE, StatutTache.ANNULEE]
        )

        if self.utilisateur:
            tache_filter &= (
                Q(createur=self.utilisateur) |
                Q(responsable=self.utilisateur)
            )

        taches = Tache.objects.filter(tache_filter)
        lendemain = self.date + timedelta(days=1)

        for tache in taches:
            tache.date_echeance = lendemain
            tache.statut = StatutTache.REPORTEE
            tache.save()

            # Créer une notification
            if tache.responsable:
                Notification.objects.create(
                    destinataire=tache.responsable,
                    titre="Tâche reportée",
                    message=f"La tâche '{tache.titre}' a été reportée au {lendemain.strftime('%d/%m/%Y')}",
                    type_notification='report',
                    content_type=ContentType.objects.get_for_model(Tache),
                    object_id=str(tache.id),
                )


class ReportTache(models.Model):
    """Historique des reports de tâches"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tache = models.ForeignKey(
        Tache,
        on_delete=models.CASCADE,
        related_name='historique_reports'
    )
    date_origine = models.DateField()
    nouvelle_date = models.DateField()
    raison = models.TextField(blank=True, null=True)
    reporte_par = models.ForeignKey(
        'gestion.Utilisateur',
        on_delete=models.SET_NULL,
        null=True
    )
    type_report = models.CharField(
        max_length=20,
        choices=[
            ('automatique', 'Automatique (clôture journée)'),
            ('manuel', 'Manuel'),
        ],
        default='manuel'
    )
    date_creation = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date_creation']
        verbose_name = 'Report de tâche'
        verbose_name_plural = 'Reports de tâches'

    def __str__(self):
        return f"Report de {self.tache.titre}: {self.date_origine} -> {self.nouvelle_date}"


# =============================================================================
# CONFIGURATION
# =============================================================================

class ConfigurationAgenda(models.Model):
    """Configuration singleton pour le module agenda"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Heures de travail
    heure_debut_journee = models.TimeField(default='08:00')
    heure_fin_journee = models.TimeField(default='18:00')
    heure_cloture_auto = models.TimeField(default='23:59')

    # Jours de travail (0=Lundi, 6=Dimanche)
    jours_travail = models.JSONField(
        default=list,
        help_text="Jours de travail [0-6]"
    )

    # Durées par défaut
    duree_rdv_defaut = models.IntegerField(
        default=60,
        help_text="Durée par défaut des RDV en minutes"
    )

    # Rappels par défaut
    rappel_rdv_defaut = models.CharField(
        max_length=20,
        choices=TypeRappel.choices,
        default=TypeRappel.HEURE_1
    )
    rappel_tache_defaut = models.CharField(
        max_length=20,
        choices=[
            ('jour_echeance', "Jour de l'échéance"),
            ('veille', 'La veille'),
        ],
        default='jour_echeance'
    )

    # Notifications
    envoyer_recapitulatif_quotidien = models.BooleanField(default=True)
    heure_recapitulatif = models.TimeField(default='07:00')
    activer_notifications_email = models.BooleanField(default=True)
    activer_notifications_sms = models.BooleanField(default=False)

    # Clôture automatique
    activer_cloture_auto = models.BooleanField(default=True)
    reporter_auto_taches = models.BooleanField(default=True)

    # Escalade
    delai_escalade_retard = models.IntegerField(
        default=2,
        help_text="Jours de retard avant escalade"
    )

    # Couleurs par défaut par type
    couleurs_types_rdv = models.JSONField(
        default=dict,
        help_text="Couleurs par type de RDV"
    )
    couleurs_types_tache = models.JSONField(
        default=dict,
        help_text="Couleurs par type de tâche"
    )

    date_modification = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Configuration de l'agenda"
        verbose_name_plural = "Configuration de l'agenda"

    def __str__(self):
        return "Configuration de l'agenda"

    def save(self, *args, **kwargs):
        # S'assurer qu'il n'y a qu'une seule configuration
        if not self.pk and ConfigurationAgenda.objects.exists():
            existing = ConfigurationAgenda.objects.first()
            self.pk = existing.pk

        # Valeurs par défaut pour les jours de travail
        if not self.jours_travail:
            self.jours_travail = [0, 1, 2, 3, 4]  # Lundi à Vendredi

        # Valeurs par défaut pour les couleurs
        if not self.couleurs_types_rdv:
            self.couleurs_types_rdv = {
                'rendez_vous_client': '#3498db',
                'audience_tribunal': '#e74c3c',
                'signification': '#2ecc71',
                'constat': '#9b59b6',
                'saisie': '#f39c12',
                'expulsion': '#e91e63',
                'reunion_interne': '#1abc9c',
                'rdv_exterieur': '#34495e',
                'autre': '#607d8b',
            }

        if not self.couleurs_types_tache:
            self.couleurs_types_tache = {
                'redaction_acte': '#3498db',
                'signification': '#2ecc71',
                'appel_telephonique': '#f39c12',
                'envoi_courrier': '#9b59b6',
                'relance': '#e74c3c',
                'recherche': '#1abc9c',
                'preparation_dossier': '#34495e',
                'facturation': '#c6a962',
                'encaissement': '#27ae60',
                'suivi_procedure': '#00bcd4',
                'autre': '#607d8b',
            }

        super().save(*args, **kwargs)

    @classmethod
    def get_instance(cls):
        """Retourne l'instance unique de configuration"""
        instance, created = cls.objects.get_or_create(pk=cls.objects.first().pk if cls.objects.exists() else None)
        return instance


# =============================================================================
# STATISTIQUES ET RAPPORTS
# =============================================================================

class StatistiquesAgenda(models.Model):
    """Statistiques agrégées pour les rapports"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    type_periode = models.CharField(
        max_length=20,
        choices=[
            ('jour', 'Jour'),
            ('semaine', 'Semaine'),
            ('mois', 'Mois'),
            ('annee', 'Année'),
        ]
    )
    date_debut = models.DateField()
    date_fin = models.DateField()

    utilisateur = models.ForeignKey(
        'gestion.Utilisateur',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        help_text="NULL = statistiques globales"
    )

    # Statistiques RDV
    nb_rdv_total = models.IntegerField(default=0)
    nb_rdv_termines = models.IntegerField(default=0)
    nb_rdv_annules = models.IntegerField(default=0)
    nb_rdv_reportes = models.IntegerField(default=0)
    repartition_types_rdv = models.JSONField(default=dict)

    # Statistiques Tâches
    nb_taches_total = models.IntegerField(default=0)
    nb_taches_terminees = models.IntegerField(default=0)
    nb_taches_en_retard = models.IntegerField(default=0)
    nb_taches_reportees = models.IntegerField(default=0)
    repartition_types_tache = models.JSONField(default=dict)

    # Métriques de performance
    taux_realisation_rdv = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0
    )
    taux_realisation_taches = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0
    )
    temps_moyen_completion = models.IntegerField(
        default=0,
        help_text="Temps moyen en minutes"
    )

    # Délégation
    nb_taches_deleguees = models.IntegerField(default=0)
    taux_completion_delegations = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0
    )

    date_generation = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date_debut']
        verbose_name = 'Statistiques agenda'
        verbose_name_plural = 'Statistiques agenda'
        unique_together = ['type_periode', 'date_debut', 'utilisateur']

    def __str__(self):
        user = self.utilisateur.get_full_name() if self.utilisateur else "Global"
        return f"Stats {self.type_periode} - {self.date_debut} - {user}"


# =============================================================================
# HISTORIQUE ET AUDIT
# =============================================================================

class HistoriqueAgenda(models.Model):
    """Historique des modifications pour audit"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    type_objet = models.CharField(
        max_length=30,
        choices=[
            ('rendez_vous', 'Rendez-vous'),
            ('tache', 'Tâche'),
            ('delegation', 'Délégation'),
            ('commentaire', 'Commentaire'),
        ]
    )

    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE
    )
    object_id = models.CharField(max_length=36)
    objet = GenericForeignKey('content_type', 'object_id')

    action = models.CharField(
        max_length=30,
        choices=[
            ('creation', 'Création'),
            ('modification', 'Modification'),
            ('suppression', 'Suppression'),
            ('delegation', 'Délégation'),
            ('reassignation', 'Réassignation'),
            ('completion', 'Complétion'),
            ('report', 'Report'),
            ('annulation', 'Annulation'),
            ('commentaire', 'Ajout commentaire'),
        ]
    )

    utilisateur = models.ForeignKey(
        'gestion.Utilisateur',
        on_delete=models.SET_NULL,
        null=True,
        related_name='historique_agenda'
    )

    details = models.JSONField(blank=True, null=True)
    anciennes_valeurs = models.JSONField(blank=True, null=True)
    nouvelles_valeurs = models.JSONField(blank=True, null=True)

    adresse_ip = models.GenericIPAddressField(blank=True, null=True)
    user_agent = models.TextField(blank=True, null=True)

    date_creation = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date_creation']
        verbose_name = 'Historique agenda'
        verbose_name_plural = 'Historiques agenda'
        indexes = [
            models.Index(fields=['content_type', 'object_id']),
            models.Index(fields=['utilisateur', 'date_creation']),
            models.Index(fields=['action', 'date_creation']),
        ]

    def __str__(self):
        return f"{self.action} - {self.type_objet} - {self.date_creation}"
