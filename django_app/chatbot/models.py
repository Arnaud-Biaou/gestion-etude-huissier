"""
Module Chatbot / Assistant IA - Section 18 DSTD v3.2
Gestion des conversations, commandes vocales et actions automatisées
pour l'étude d'huissier de justice au Bénin.

Fonctionnalités:
- Interface WebSocket temps réel
- Commandes vocales en français
- Mode guidé pour écritures comptables
- Vérification RBAC avant toute action
- Confirmation obligatoire pour montants > 100 000 FCFA
- Historique conservé 90 jours
- Validation humaine obligatoire pour écritures critiques
"""

import uuid
from decimal import Decimal
from django.db import models
from django.conf import settings
from django.utils import timezone
from django.core.validators import MinValueValidator
from datetime import timedelta


# ═══════════════════════════════════════════════════════════════════════════════
# CONSTANTES ET CHOIX
# ═══════════════════════════════════════════════════════════════════════════════

class TypeMessage(models.TextChoices):
    """Types de messages dans la conversation"""
    UTILISATEUR = 'utilisateur', 'Message utilisateur'
    ASSISTANT = 'assistant', 'Réponse assistant'
    SYSTEME = 'systeme', 'Message système'
    ERREUR = 'erreur', 'Message d\'erreur'
    CONFIRMATION = 'confirmation', 'Demande de confirmation'
    VALIDATION = 'validation', 'En attente de validation humaine'


class TypeCommande(models.TextChoices):
    """Types de commandes reconnues"""
    # Trésorerie
    TRESORERIE_SOLDE = 'tresorerie_solde', 'Consulter solde trésorerie'
    TRESORERIE_MOUVEMENT = 'tresorerie_mouvement', 'Créer mouvement trésorerie'
    TRESORERIE_ALERTE = 'tresorerie_alerte', 'Consulter alertes trésorerie'

    # Comptabilité
    COMPTA_ECRITURE = 'compta_ecriture', 'Créer écriture comptable'
    COMPTA_SOLDE = 'compta_solde', 'Consulter solde compte'
    COMPTA_BALANCE = 'compta_balance', 'Générer balance'
    COMPTA_GRAND_LIVRE = 'compta_grand_livre', 'Consulter grand livre'

    # Dossiers
    DOSSIER_RECHERCHE = 'dossier_recherche', 'Rechercher dossier'
    DOSSIER_STATUT = 'dossier_statut', 'Consulter statut dossier'
    DOSSIER_CREER = 'dossier_creer', 'Créer nouveau dossier'
    DOSSIER_ENCAISSEMENT = 'dossier_encaissement', 'Enregistrer encaissement'

    # Courriers
    COURRIER_GENERER = 'courrier_generer', 'Générer courrier'
    COURRIER_LISTE = 'courrier_liste', 'Lister courriers'
    COURRIER_ENVOYER = 'courrier_envoyer', 'Envoyer courrier'

    # Agenda
    AGENDA_RDV = 'agenda_rdv', 'Créer rendez-vous'
    AGENDA_TACHE = 'agenda_tache', 'Créer tâche'
    AGENDA_AUJOURDHUI = 'agenda_aujourdhui', 'Programme du jour'

    # Rapports
    RAPPORT_GENERER = 'rapport_generer', 'Générer rapport'

    # Navigation
    NAVIGATION = 'navigation', 'Navigation dans l\'application'
    AIDE = 'aide', 'Demande d\'aide'

    # Autre
    AUTRE = 'autre', 'Autre commande'


class StatutAction(models.TextChoices):
    """Statuts des actions demandées"""
    EN_ATTENTE = 'en_attente', 'En attente de traitement'
    EN_COURS = 'en_cours', 'En cours d\'exécution'
    CONFIRMATION_REQUISE = 'confirmation_requise', 'Confirmation requise (montant > 100k)'
    VALIDATION_REQUISE = 'validation_requise', 'Validation humaine requise'
    EXECUTEE = 'executee', 'Action exécutée'
    ANNULEE = 'annulee', 'Action annulée'
    REFUSEE = 'refusee', 'Action refusée (RBAC)'
    ERREUR = 'erreur', 'Erreur d\'exécution'


class NiveauCriticite(models.TextChoices):
    """Niveaux de criticité des actions"""
    LECTURE = 'lecture', 'Lecture seule'
    NORMAL = 'normal', 'Action normale'
    SENSIBLE = 'sensible', 'Action sensible (confirmation requise)'
    CRITIQUE = 'critique', 'Action critique (validation humaine obligatoire)'


class ModeGuidage(models.TextChoices):
    """Modes de guidage disponibles"""
    ECRITURE_SIMPLE = 'ecriture_simple', 'Écriture comptable simple'
    ECRITURE_FACTURE = 'ecriture_facture', 'Écriture de facturation'
    ECRITURE_ENCAISSEMENT = 'ecriture_encaissement', 'Écriture d\'encaissement'
    ECRITURE_SALAIRE = 'ecriture_salaire', 'Écriture de paie'
    CREATION_DOSSIER = 'creation_dossier', 'Création de dossier'
    FACTURATION = 'facturation', 'Facturation guidée'


# Seuil de confirmation obligatoire (FCFA)
SEUIL_CONFIRMATION = Decimal('100000')

# Durée de rétention des conversations (jours)
DUREE_RETENTION_JOURS = 90


# ═══════════════════════════════════════════════════════════════════════════════
# MODÈLE: SESSION DE CONVERSATION
# ═══════════════════════════════════════════════════════════════════════════════

class SessionConversation(models.Model):
    """
    Session de conversation avec l'assistant IA.
    Une session regroupe plusieurs messages et peut avoir un contexte.
    Conservation: 90 jours selon DSTD v3.2.
    """

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )

    utilisateur = models.ForeignKey(
        'gestion.Utilisateur',
        on_delete=models.CASCADE,
        related_name='sessions_chatbot',
        verbose_name="Utilisateur"
    )

    # Informations de session
    titre = models.CharField(
        max_length=255,
        blank=True,
        verbose_name="Titre de la session",
        help_text="Généré automatiquement à partir du premier message"
    )

    # Contexte optionnel
    dossier_contexte = models.ForeignKey(
        'gestion.Dossier',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='sessions_chatbot',
        verbose_name="Dossier en contexte"
    )

    # Mode guidé actif
    mode_guide_actif = models.CharField(
        max_length=30,
        choices=ModeGuidage.choices,
        blank=True,
        null=True,
        verbose_name="Mode guidé actif"
    )
    etape_guidage = models.PositiveIntegerField(
        default=0,
        verbose_name="Étape courante du guidage"
    )
    donnees_guidage = models.JSONField(
        default=dict,
        blank=True,
        verbose_name="Données collectées pendant le guidage"
    )

    # État de la session
    est_active = models.BooleanField(
        default=True,
        verbose_name="Session active"
    )

    # Canal de communication
    canal = models.CharField(
        max_length=20,
        choices=[
            ('web', 'Interface Web'),
            ('websocket', 'WebSocket temps réel'),
            ('api', 'API REST'),
            ('vocal', 'Commande vocale'),
        ],
        default='websocket',
        verbose_name="Canal de communication"
    )

    # Métadonnées techniques
    user_agent = models.TextField(
        blank=True,
        verbose_name="User Agent"
    )
    adresse_ip = models.GenericIPAddressField(
        null=True,
        blank=True,
        verbose_name="Adresse IP"
    )

    # Horodatage
    date_creation = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Date de création"
    )
    date_derniere_activite = models.DateTimeField(
        auto_now=True,
        verbose_name="Dernière activité"
    )
    date_expiration = models.DateTimeField(
        verbose_name="Date d'expiration",
        help_text="Session supprimée après cette date (90 jours)"
    )

    class Meta:
        verbose_name = "Session de conversation"
        verbose_name_plural = "Sessions de conversation"
        ordering = ['-date_derniere_activite']
        indexes = [
            models.Index(fields=['utilisateur', '-date_derniere_activite']),
            models.Index(fields=['date_expiration']),
            models.Index(fields=['est_active', '-date_creation']),
        ]

    def __str__(self):
        return f"Session {self.id} - {self.utilisateur.username}"

    def save(self, *args, **kwargs):
        # Calculer la date d'expiration automatiquement
        if not self.date_expiration:
            self.date_expiration = timezone.now() + timedelta(days=DUREE_RETENTION_JOURS)
        super().save(*args, **kwargs)

    @property
    def nombre_messages(self):
        """Retourne le nombre de messages dans la session"""
        return self.messages.count()

    @property
    def est_expiree(self):
        """Vérifie si la session est expirée"""
        return timezone.now() > self.date_expiration

    def prolonger(self, jours=DUREE_RETENTION_JOURS):
        """Prolonge la durée de vie de la session"""
        self.date_expiration = timezone.now() + timedelta(days=jours)
        self.save(update_fields=['date_expiration'])

    def terminer(self):
        """Termine la session"""
        self.est_active = False
        self.save(update_fields=['est_active'])

    def demarrer_mode_guide(self, mode):
        """Démarre un mode guidé"""
        self.mode_guide_actif = mode
        self.etape_guidage = 1
        self.donnees_guidage = {}
        self.save(update_fields=['mode_guide_actif', 'etape_guidage', 'donnees_guidage'])

    def terminer_mode_guide(self):
        """Termine le mode guidé"""
        self.mode_guide_actif = None
        self.etape_guidage = 0
        self.donnees_guidage = {}
        self.save(update_fields=['mode_guide_actif', 'etape_guidage', 'donnees_guidage'])

    @classmethod
    def nettoyer_sessions_expirees(cls):
        """Supprime les sessions expirées (à appeler via cron/celery)"""
        sessions_expirees = cls.objects.filter(date_expiration__lt=timezone.now())
        count = sessions_expirees.count()
        sessions_expirees.delete()
        return count


# ═══════════════════════════════════════════════════════════════════════════════
# MODÈLE: MESSAGE
# ═══════════════════════════════════════════════════════════════════════════════

class Message(models.Model):
    """
    Message individuel dans une conversation.
    Peut être de l'utilisateur, de l'assistant ou du système.
    """

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )

    session = models.ForeignKey(
        SessionConversation,
        on_delete=models.CASCADE,
        related_name='messages',
        verbose_name="Session"
    )

    # Contenu du message
    type_message = models.CharField(
        max_length=20,
        choices=TypeMessage.choices,
        default=TypeMessage.UTILISATEUR,
        verbose_name="Type de message"
    )
    contenu = models.TextField(
        verbose_name="Contenu du message"
    )
    contenu_html = models.TextField(
        blank=True,
        verbose_name="Contenu HTML formaté"
    )

    # Source vocale (si applicable)
    est_vocal = models.BooleanField(
        default=False,
        verbose_name="Entrée vocale"
    )
    transcription_originale = models.TextField(
        blank=True,
        verbose_name="Transcription vocale originale"
    )
    confiance_transcription = models.DecimalField(
        max_digits=5,
        decimal_places=4,
        null=True,
        blank=True,
        verbose_name="Score de confiance transcription"
    )

    # Analyse NLP
    intention_detectee = models.CharField(
        max_length=50,
        choices=TypeCommande.choices,
        blank=True,
        null=True,
        verbose_name="Intention détectée"
    )
    entites_extraites = models.JSONField(
        default=dict,
        blank=True,
        verbose_name="Entités extraites",
        help_text="Montants, dates, références, noms, etc."
    )
    confiance_intention = models.DecimalField(
        max_digits=5,
        decimal_places=4,
        null=True,
        blank=True,
        verbose_name="Score de confiance intention"
    )

    # Contexte de guidage
    etape_guidage = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name="Étape de guidage au moment du message"
    )

    # Métadonnées
    date_creation = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Date de création"
    )
    temps_traitement_ms = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name="Temps de traitement (ms)"
    )

    class Meta:
        verbose_name = "Message"
        verbose_name_plural = "Messages"
        ordering = ['date_creation']
        indexes = [
            models.Index(fields=['session', 'date_creation']),
            models.Index(fields=['type_message']),
            models.Index(fields=['intention_detectee']),
        ]

    def __str__(self):
        return f"{self.get_type_message_display()}: {self.contenu[:50]}..."

    def marquer_comme_vocal(self, transcription, confiance=None):
        """Marque le message comme provenant d'une entrée vocale"""
        self.est_vocal = True
        self.transcription_originale = transcription
        self.confiance_transcription = confiance
        self.save(update_fields=['est_vocal', 'transcription_originale', 'confiance_transcription'])


# ═══════════════════════════════════════════════════════════════════════════════
# MODÈLE: ACTION DEMANDÉE
# ═══════════════════════════════════════════════════════════════════════════════

class ActionDemandee(models.Model):
    """
    Action demandée par l'utilisateur via le chatbot.
    Gère les confirmations, validations RBAC et exécution.

    Règles DSTD v3.2:
    - Vérification RBAC AVANT toute action
    - Confirmation obligatoire pour montants > 100 000 FCFA
    - Validation humaine pour écritures comptables critiques
    """

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )

    message = models.ForeignKey(
        Message,
        on_delete=models.CASCADE,
        related_name='actions',
        verbose_name="Message déclencheur"
    )

    # Type et description de l'action
    type_commande = models.CharField(
        max_length=50,
        choices=TypeCommande.choices,
        verbose_name="Type de commande"
    )
    description = models.TextField(
        verbose_name="Description de l'action"
    )

    # Paramètres de l'action
    parametres = models.JSONField(
        default=dict,
        verbose_name="Paramètres de l'action"
    )

    # Criticité et montant
    niveau_criticite = models.CharField(
        max_length=20,
        choices=NiveauCriticite.choices,
        default=NiveauCriticite.NORMAL,
        verbose_name="Niveau de criticité"
    )
    montant_concerne = models.DecimalField(
        max_digits=15,
        decimal_places=0,
        null=True,
        blank=True,
        verbose_name="Montant concerné (FCFA)"
    )

    # Statut et workflow
    statut = models.CharField(
        max_length=30,
        choices=StatutAction.choices,
        default=StatutAction.EN_ATTENTE,
        verbose_name="Statut"
    )

    # Vérification RBAC
    permission_requise = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="Permission RBAC requise"
    )
    rbac_verifie = models.BooleanField(
        default=False,
        verbose_name="RBAC vérifié"
    )
    rbac_autorise = models.BooleanField(
        default=False,
        verbose_name="RBAC autorisé"
    )
    raison_refus_rbac = models.TextField(
        blank=True,
        verbose_name="Raison du refus RBAC"
    )

    # Confirmation utilisateur (pour montants > 100k)
    confirmation_requise = models.BooleanField(
        default=False,
        verbose_name="Confirmation requise"
    )
    confirmation_donnee = models.BooleanField(
        default=False,
        verbose_name="Confirmation donnée"
    )
    date_confirmation = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Date de confirmation"
    )

    # Validation humaine (pour écritures critiques)
    validation_humaine_requise = models.BooleanField(
        default=False,
        verbose_name="Validation humaine requise"
    )
    validateur = models.ForeignKey(
        'gestion.Utilisateur',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='actions_chatbot_validees',
        verbose_name="Validateur"
    )
    date_validation = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Date de validation"
    )
    commentaire_validation = models.TextField(
        blank=True,
        verbose_name="Commentaire de validation"
    )

    # Résultat de l'exécution
    resultat = models.JSONField(
        default=dict,
        blank=True,
        verbose_name="Résultat de l'exécution"
    )
    message_resultat = models.TextField(
        blank=True,
        verbose_name="Message de résultat"
    )
    erreur = models.TextField(
        blank=True,
        verbose_name="Message d'erreur"
    )

    # Références aux objets créés/modifiés
    objet_cree_type = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="Type d'objet créé"
    )
    objet_cree_id = models.CharField(
        max_length=36,
        blank=True,
        verbose_name="ID de l'objet créé"
    )

    # Horodatage
    date_creation = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Date de création"
    )
    date_execution = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Date d'exécution"
    )

    class Meta:
        verbose_name = "Action demandée"
        verbose_name_plural = "Actions demandées"
        ordering = ['-date_creation']
        indexes = [
            models.Index(fields=['statut', '-date_creation']),
            models.Index(fields=['type_commande']),
            models.Index(fields=['validation_humaine_requise', 'statut']),
        ]

    def __str__(self):
        return f"{self.get_type_commande_display()} - {self.get_statut_display()}"

    def save(self, *args, **kwargs):
        # Déterminer automatiquement si confirmation requise
        if self.montant_concerne and self.montant_concerne > SEUIL_CONFIRMATION:
            self.confirmation_requise = True
            if self.niveau_criticite == NiveauCriticite.NORMAL:
                self.niveau_criticite = NiveauCriticite.SENSIBLE

        # Écritures comptables critiques nécessitent validation humaine
        if self.type_commande in [
            TypeCommande.COMPTA_ECRITURE,
        ] and self.niveau_criticite == NiveauCriticite.CRITIQUE:
            self.validation_humaine_requise = True

        super().save(*args, **kwargs)

    def verifier_rbac(self, utilisateur):
        """
        Vérifie les permissions RBAC de l'utilisateur.
        Doit être appelé AVANT toute exécution.
        """
        from chatbot.permissions import verifier_permission_action

        self.rbac_verifie = True
        autorise, raison = verifier_permission_action(utilisateur, self)
        self.rbac_autorise = autorise

        if not autorise:
            self.raison_refus_rbac = raison
            self.statut = StatutAction.REFUSEE

        self.save(update_fields=['rbac_verifie', 'rbac_autorise', 'raison_refus_rbac', 'statut'])
        return autorise

    def confirmer(self):
        """Enregistre la confirmation utilisateur"""
        if not self.confirmation_requise:
            return True

        self.confirmation_donnee = True
        self.date_confirmation = timezone.now()

        # Passer à l'étape suivante
        if self.validation_humaine_requise:
            self.statut = StatutAction.VALIDATION_REQUISE
        else:
            self.statut = StatutAction.EN_COURS

        self.save()
        return True

    def annuler_confirmation(self):
        """Annule/refuse la confirmation"""
        self.confirmation_donnee = False
        self.statut = StatutAction.ANNULEE
        self.save()

    def valider(self, validateur, commentaire=''):
        """
        Validation humaine pour les actions critiques.
        NE JAMAIS passer d'écriture comptable critique sans cela.
        """
        if not self.validation_humaine_requise:
            return True

        self.validateur = validateur
        self.date_validation = timezone.now()
        self.commentaire_validation = commentaire
        self.statut = StatutAction.EN_COURS
        self.save()
        return True

    def refuser_validation(self, validateur, raison):
        """Refuse la validation humaine"""
        self.validateur = validateur
        self.date_validation = timezone.now()
        self.commentaire_validation = raison
        self.statut = StatutAction.REFUSEE
        self.save()

    def executer(self):
        """
        Exécute l'action si toutes les conditions sont remplies.
        Retourne (succes, message)
        """
        # Vérifications préalables
        if not self.rbac_verifie:
            return False, "Vérification RBAC non effectuée"

        if not self.rbac_autorise:
            return False, f"Permission refusée: {self.raison_refus_rbac}"

        if self.confirmation_requise and not self.confirmation_donnee:
            return False, "Confirmation requise pour cette action"

        if self.validation_humaine_requise and not self.validateur:
            return False, "Validation humaine requise pour cette action"

        # Exécuter l'action
        from chatbot.commands import executer_commande

        try:
            self.statut = StatutAction.EN_COURS
            self.save(update_fields=['statut'])

            succes, resultat, message = executer_commande(self)

            self.date_execution = timezone.now()
            self.resultat = resultat
            self.message_resultat = message

            if succes:
                self.statut = StatutAction.EXECUTEE
            else:
                self.statut = StatutAction.ERREUR
                self.erreur = message

            self.save()
            return succes, message

        except Exception as e:
            self.statut = StatutAction.ERREUR
            self.erreur = str(e)
            self.save()
            return False, str(e)

    def peut_etre_executee(self):
        """Vérifie si l'action peut être exécutée"""
        if not self.rbac_autorise:
            return False, "Permission RBAC refusée"
        if self.confirmation_requise and not self.confirmation_donnee:
            return False, "Confirmation requise"
        if self.validation_humaine_requise and not self.validateur:
            return False, "Validation humaine requise"
        if self.statut in [StatutAction.EXECUTEE, StatutAction.ANNULEE, StatutAction.REFUSEE]:
            return False, f"Action déjà {self.get_statut_display()}"
        return True, "OK"


# ═══════════════════════════════════════════════════════════════════════════════
# MODÈLE: COMMANDE VOCALE RECONNUE
# ═══════════════════════════════════════════════════════════════════════════════

class CommandeVocale(models.Model):
    """
    Enregistrement des commandes vocales pour amélioration continue.
    Stocke les transcriptions et leur mapping vers les intentions.
    """

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )

    message = models.OneToOneField(
        Message,
        on_delete=models.CASCADE,
        related_name='commande_vocale',
        verbose_name="Message associé"
    )

    # Audio original (optionnel, pour débug/amélioration)
    fichier_audio = models.FileField(
        upload_to='chatbot/audio/',
        blank=True,
        null=True,
        verbose_name="Fichier audio"
    )
    duree_secondes = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Durée (secondes)"
    )

    # Transcription
    transcription_brute = models.TextField(
        verbose_name="Transcription brute"
    )
    transcription_normalisee = models.TextField(
        verbose_name="Transcription normalisée"
    )
    langue_detectee = models.CharField(
        max_length=10,
        default='fr',
        verbose_name="Langue détectée"
    )

    # Qualité
    score_confiance = models.DecimalField(
        max_digits=5,
        decimal_places=4,
        verbose_name="Score de confiance"
    )
    mots_alternatifs = models.JSONField(
        default=list,
        blank=True,
        verbose_name="Mots alternatifs suggérés"
    )

    # Feedback utilisateur
    transcription_correcte = models.BooleanField(
        null=True,
        blank=True,
        verbose_name="Transcription correcte (feedback)"
    )
    correction_utilisateur = models.TextField(
        blank=True,
        verbose_name="Correction par l'utilisateur"
    )

    date_creation = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:
        verbose_name = "Commande vocale"
        verbose_name_plural = "Commandes vocales"
        ordering = ['-date_creation']

    def __str__(self):
        return f"Vocal: {self.transcription_normalisee[:50]}..."


# ═══════════════════════════════════════════════════════════════════════════════
# MODÈLE: TEMPLATE DE RÉPONSE
# ═══════════════════════════════════════════════════════════════════════════════

class TemplateReponse(models.Model):
    """
    Templates de réponses prédéfinies pour le chatbot.
    Permet de personnaliser les réponses par type de commande.
    """

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )

    # Identification
    code = models.CharField(
        max_length=50,
        unique=True,
        verbose_name="Code du template"
    )
    type_commande = models.CharField(
        max_length=50,
        choices=TypeCommande.choices,
        blank=True,
        null=True,
        verbose_name="Type de commande associé"
    )

    # Contenu
    titre = models.CharField(
        max_length=200,
        verbose_name="Titre"
    )
    contenu = models.TextField(
        verbose_name="Contenu du template",
        help_text="Utiliser {variable} pour les substitutions"
    )
    contenu_html = models.TextField(
        blank=True,
        verbose_name="Contenu HTML"
    )

    # Catégorie
    categorie = models.CharField(
        max_length=50,
        choices=[
            ('succes', 'Succès'),
            ('erreur', 'Erreur'),
            ('confirmation', 'Demande de confirmation'),
            ('validation', 'Demande de validation'),
            ('aide', 'Aide/Information'),
            ('guidage', 'Mode guidé'),
        ],
        default='succes',
        verbose_name="Catégorie"
    )

    # Métadonnées
    actif = models.BooleanField(
        default=True,
        verbose_name="Actif"
    )
    date_creation = models.DateTimeField(
        auto_now_add=True
    )
    date_modification = models.DateTimeField(
        auto_now=True
    )

    class Meta:
        verbose_name = "Template de réponse"
        verbose_name_plural = "Templates de réponses"
        ordering = ['code']

    def __str__(self):
        return f"{self.code} - {self.titre}"

    def render(self, **context):
        """Rend le template avec les variables fournies"""
        contenu = self.contenu
        for key, value in context.items():
            contenu = contenu.replace(f"{{{key}}}", str(value))
        return contenu


# ═══════════════════════════════════════════════════════════════════════════════
# MODÈLE: ÉTAPE DE GUIDAGE
# ═══════════════════════════════════════════════════════════════════════════════

class EtapeGuidage(models.Model):
    """
    Définition des étapes pour les modes guidés (ex: écritures comptables).
    Chaque mode a plusieurs étapes ordonnées.
    """

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )

    mode = models.CharField(
        max_length=30,
        choices=ModeGuidage.choices,
        verbose_name="Mode de guidage"
    )
    numero_etape = models.PositiveIntegerField(
        verbose_name="Numéro d'étape"
    )

    # Contenu de l'étape
    titre = models.CharField(
        max_length=200,
        verbose_name="Titre de l'étape"
    )
    question = models.TextField(
        verbose_name="Question à poser"
    )
    aide = models.TextField(
        blank=True,
        verbose_name="Texte d'aide"
    )

    # Type de réponse attendue
    type_reponse = models.CharField(
        max_length=30,
        choices=[
            ('texte', 'Texte libre'),
            ('nombre', 'Nombre'),
            ('montant', 'Montant (FCFA)'),
            ('date', 'Date'),
            ('choix', 'Choix parmi options'),
            ('compte', 'Numéro de compte comptable'),
            ('dossier', 'Référence dossier'),
            ('confirmation', 'Oui/Non'),
        ],
        default='texte',
        verbose_name="Type de réponse attendue"
    )

    # Options pour type 'choix'
    options_choix = models.JSONField(
        default=list,
        blank=True,
        verbose_name="Options de choix"
    )

    # Validation
    champ_obligatoire = models.BooleanField(
        default=True,
        verbose_name="Champ obligatoire"
    )
    regex_validation = models.CharField(
        max_length=200,
        blank=True,
        verbose_name="Expression régulière de validation"
    )
    message_erreur = models.CharField(
        max_length=300,
        blank=True,
        verbose_name="Message d'erreur personnalisé"
    )

    # Nom de la variable pour stockage
    nom_variable = models.CharField(
        max_length=50,
        verbose_name="Nom de la variable",
        help_text="Nom utilisé pour stocker la réponse"
    )

    # Conditions d'affichage
    condition = models.JSONField(
        default=dict,
        blank=True,
        verbose_name="Condition d'affichage",
        help_text="JSON: {'variable': 'valeur'}"
    )

    # Métadonnées
    actif = models.BooleanField(
        default=True,
        verbose_name="Actif"
    )

    class Meta:
        verbose_name = "Étape de guidage"
        verbose_name_plural = "Étapes de guidage"
        ordering = ['mode', 'numero_etape']
        unique_together = ['mode', 'numero_etape']

    def __str__(self):
        return f"{self.get_mode_display()} - Étape {self.numero_etape}: {self.titre}"


# ═══════════════════════════════════════════════════════════════════════════════
# MODÈLE: HISTORIQUE D'UTILISATION (STATISTIQUES)
# ═══════════════════════════════════════════════════════════════════════════════

class StatistiquesUtilisation(models.Model):
    """
    Statistiques d'utilisation du chatbot pour analytics.
    Agrégées par jour et par utilisateur.
    """

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )

    date = models.DateField(
        verbose_name="Date"
    )
    utilisateur = models.ForeignKey(
        'gestion.Utilisateur',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='stats_chatbot',
        verbose_name="Utilisateur",
        help_text="NULL = statistiques globales"
    )

    # Compteurs
    nombre_sessions = models.PositiveIntegerField(
        default=0,
        verbose_name="Nombre de sessions"
    )
    nombre_messages = models.PositiveIntegerField(
        default=0,
        verbose_name="Nombre de messages"
    )
    nombre_commandes_vocales = models.PositiveIntegerField(
        default=0,
        verbose_name="Commandes vocales"
    )
    nombre_actions_executees = models.PositiveIntegerField(
        default=0,
        verbose_name="Actions exécutées"
    )
    nombre_actions_refusees = models.PositiveIntegerField(
        default=0,
        verbose_name="Actions refusées"
    )

    # Répartition par type de commande
    repartition_commandes = models.JSONField(
        default=dict,
        verbose_name="Répartition par type de commande"
    )

    # Temps moyen
    temps_reponse_moyen_ms = models.PositiveIntegerField(
        default=0,
        verbose_name="Temps de réponse moyen (ms)"
    )

    # Taux de succès
    taux_reconnaissance_vocale = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        verbose_name="Taux de reconnaissance vocale (%)"
    )
    taux_succes_actions = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        verbose_name="Taux de succès des actions (%)"
    )

    class Meta:
        verbose_name = "Statistiques d'utilisation"
        verbose_name_plural = "Statistiques d'utilisation"
        ordering = ['-date']
        unique_together = ['date', 'utilisateur']

    def __str__(self):
        user = self.utilisateur.username if self.utilisateur else "Global"
        return f"Stats {self.date} - {user}"


# ═══════════════════════════════════════════════════════════════════════════════
# MODÈLE: CONFIGURATION DU CHATBOT
# ═══════════════════════════════════════════════════════════════════════════════

class ConfigurationChatbot(models.Model):
    """
    Configuration singleton du module chatbot.
    Paramètres globaux de fonctionnement.
    """

    # Général
    actif = models.BooleanField(
        default=True,
        verbose_name="Chatbot actif"
    )
    nom_assistant = models.CharField(
        max_length=50,
        default="Assistant",
        verbose_name="Nom de l'assistant"
    )
    message_bienvenue = models.TextField(
        default="Bonjour ! Je suis votre assistant. Comment puis-je vous aider ?",
        verbose_name="Message de bienvenue"
    )

    # Sécurité
    seuil_confirmation_fcfa = models.DecimalField(
        max_digits=15,
        decimal_places=0,
        default=SEUIL_CONFIRMATION,
        verbose_name="Seuil de confirmation (FCFA)",
        help_text="Montant au-delà duquel une confirmation est requise"
    )
    duree_retention_jours = models.PositiveIntegerField(
        default=DUREE_RETENTION_JOURS,
        verbose_name="Durée de rétention conversations (jours)"
    )
    ecritures_critiques_validation = models.BooleanField(
        default=True,
        verbose_name="Validation humaine pour écritures critiques"
    )

    # Reconnaissance vocale
    reconnaissance_vocale_active = models.BooleanField(
        default=True,
        verbose_name="Reconnaissance vocale activée"
    )
    langue_defaut = models.CharField(
        max_length=10,
        default='fr-FR',
        verbose_name="Langue par défaut"
    )
    seuil_confiance_vocal = models.DecimalField(
        max_digits=3,
        decimal_places=2,
        default=Decimal('0.70'),
        verbose_name="Seuil de confiance vocal",
        help_text="Score minimum pour accepter une transcription"
    )

    # WebSocket
    timeout_session_minutes = models.PositiveIntegerField(
        default=30,
        verbose_name="Timeout session WebSocket (minutes)"
    )
    max_messages_par_session = models.PositiveIntegerField(
        default=1000,
        verbose_name="Maximum de messages par session"
    )

    # Modes guidés
    modes_guides_actifs = models.JSONField(
        default=list,
        verbose_name="Modes guidés activés",
        help_text="Liste des codes de modes guidés actifs"
    )

    # Notifications
    notifier_validations_en_attente = models.BooleanField(
        default=True,
        verbose_name="Notifier les validations en attente"
    )
    email_notifications = models.EmailField(
        blank=True,
        verbose_name="Email pour notifications critiques"
    )

    # Métadonnées
    date_modification = models.DateTimeField(
        auto_now=True
    )

    class Meta:
        verbose_name = "Configuration du chatbot"
        verbose_name_plural = "Configuration du chatbot"

    def __str__(self):
        return "Configuration du chatbot"

    def save(self, *args, **kwargs):
        # Singleton: s'assurer qu'il n'y a qu'une seule configuration
        if not self.pk and ConfigurationChatbot.objects.exists():
            existing = ConfigurationChatbot.objects.first()
            self.pk = existing.pk

        # Valeurs par défaut pour modes guidés
        if not self.modes_guides_actifs:
            self.modes_guides_actifs = [
                ModeGuidage.ECRITURE_SIMPLE,
                ModeGuidage.ECRITURE_FACTURE,
                ModeGuidage.ECRITURE_ENCAISSEMENT,
            ]

        super().save(*args, **kwargs)

    @classmethod
    def get_instance(cls):
        """Retourne l'instance unique de configuration"""
        instance, created = cls.objects.get_or_create(pk=1)
        return instance


# ═══════════════════════════════════════════════════════════════════════════════
# MODÈLE: RACCOURCIS UTILISATEUR
# ═══════════════════════════════════════════════════════════════════════════════

class RaccourciUtilisateur(models.Model):
    """
    Raccourcis personnalisés par utilisateur.
    Permet de définir des commandes courtes pour des actions fréquentes.
    """

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )

    utilisateur = models.ForeignKey(
        'gestion.Utilisateur',
        on_delete=models.CASCADE,
        related_name='raccourcis_chatbot',
        verbose_name="Utilisateur"
    )

    # Raccourci
    raccourci = models.CharField(
        max_length=50,
        verbose_name="Raccourci",
        help_text="Ex: /solde, /rdv, /dossier123"
    )

    # Action associée
    type_commande = models.CharField(
        max_length=50,
        choices=TypeCommande.choices,
        verbose_name="Type de commande"
    )
    parametres_defaut = models.JSONField(
        default=dict,
        verbose_name="Paramètres par défaut"
    )

    # Métadonnées
    nombre_utilisations = models.PositiveIntegerField(
        default=0,
        verbose_name="Nombre d'utilisations"
    )
    actif = models.BooleanField(
        default=True,
        verbose_name="Actif"
    )
    date_creation = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:
        verbose_name = "Raccourci utilisateur"
        verbose_name_plural = "Raccourcis utilisateurs"
        unique_together = ['utilisateur', 'raccourci']
        ordering = ['-nombre_utilisations']

    def __str__(self):
        return f"{self.raccourci} → {self.get_type_commande_display()}"

    def utiliser(self):
        """Incrémente le compteur d'utilisation"""
        self.nombre_utilisations += 1
        self.save(update_fields=['nombre_utilisations'])
