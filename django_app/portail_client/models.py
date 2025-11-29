"""
Modèles de données pour le Portail Client
Gestion des comptes clients, documents accessibles, messages et notifications
"""

from django.db import models
from django.contrib.auth.hashers import make_password, check_password
import secrets
import string


class ClientPortail(models.Model):
    """Compte client pour accès au portail"""

    TYPE_CLIENT_CHOICES = [
        ('creancier', 'Créancier'),
        ('debiteur', 'Débiteur'),
        ('autre', 'Autre justiciable'),
    ]

    # Identification
    code_client = models.CharField(
        max_length=20,
        unique=True,
        verbose_name="Code client"
    )
    email = models.EmailField(unique=True)
    telephone = models.CharField(max_length=50)
    mot_de_passe = models.CharField(max_length=128)

    # Lien avec les parties existantes
    partie = models.ForeignKey(
        'gestion.Partie',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='compte_portail',
        verbose_name="Partie liée"
    )

    # Informations
    type_client = models.CharField(
        max_length=20,
        choices=TYPE_CLIENT_CHOICES,
        default='autre',
        verbose_name="Type de client"
    )
    nom_complet = models.CharField(max_length=300, verbose_name="Nom complet")

    # Sécurité
    est_actif = models.BooleanField(default=True, verbose_name="Compte actif")
    email_verifie = models.BooleanField(default=False, verbose_name="Email vérifié")
    token_verification = models.CharField(max_length=100, blank=True)
    date_derniere_connexion = models.DateTimeField(null=True, blank=True)
    tentatives_connexion = models.PositiveIntegerField(default=0)
    compte_bloque = models.BooleanField(default=False, verbose_name="Compte bloqué")

    # Métadonnées
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Client portail"
        verbose_name_plural = "Clients portail"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.code_client} - {self.nom_complet}"

    def set_password(self, raw_password):
        """Définit le mot de passe hashé"""
        self.mot_de_passe = make_password(raw_password)

    def check_password(self, raw_password):
        """Vérifie le mot de passe"""
        return check_password(raw_password, self.mot_de_passe)

    @classmethod
    def generer_code_client(cls):
        """Génère un code client unique"""
        while True:
            code = 'CLI-' + ''.join(secrets.choice(string.digits) for _ in range(6))
            if not cls.objects.filter(code_client=code).exists():
                return code

    def generer_token_verification(self):
        """Génère un token de vérification d'email"""
        self.token_verification = secrets.token_urlsafe(32)
        self.save()
        return self.token_verification


class AccesDocument(models.Model):
    """Document accessible au client sur le portail"""

    TYPE_DOCUMENT_CHOICES = [
        ('acte', 'Acte formalisé'),
        ('facture', 'Facture'),
        ('decompte', 'Décompte'),
        ('courrier', 'Courrier'),
        ('autre', 'Autre'),
    ]

    client = models.ForeignKey(
        ClientPortail,
        on_delete=models.CASCADE,
        related_name='documents_accessibles'
    )
    dossier = models.ForeignKey(
        'gestion.Dossier',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        verbose_name="Dossier lié"
    )

    type_document = models.CharField(
        max_length=20,
        choices=TYPE_DOCUMENT_CHOICES,
        verbose_name="Type de document"
    )
    titre = models.CharField(max_length=300, verbose_name="Titre")
    description = models.TextField(blank=True, verbose_name="Description")
    fichier = models.FileField(upload_to='portail_documents/')

    # Accès
    date_mise_disposition = models.DateTimeField(auto_now_add=True)
    date_premier_telechargement = models.DateTimeField(null=True, blank=True)
    nombre_telechargements = models.PositiveIntegerField(default=0)

    # Paiement requis
    paiement_requis = models.BooleanField(
        default=False,
        verbose_name="Paiement requis"
    )
    montant_requis = models.DecimalField(
        max_digits=10,
        decimal_places=0,
        null=True,
        blank=True,
        verbose_name="Montant requis (FCFA)"
    )
    est_paye = models.BooleanField(default=False, verbose_name="Est payé")
    date_paiement = models.DateTimeField(null=True, blank=True)
    reference_paiement = models.CharField(max_length=100, blank=True)

    class Meta:
        ordering = ['-date_mise_disposition']
        verbose_name = "Document accessible"
        verbose_name_plural = "Documents accessibles"

    def __str__(self):
        return f"{self.titre} - {self.client.nom_complet}"


class MessagePortail(models.Model):
    """Messages entre client et étude"""

    client = models.ForeignKey(
        ClientPortail,
        on_delete=models.CASCADE,
        related_name='messages'
    )
    dossier = models.ForeignKey(
        'gestion.Dossier',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Dossier concerné"
    )

    sujet = models.CharField(max_length=300, verbose_name="Sujet")
    contenu = models.TextField(verbose_name="Contenu")

    # Direction
    est_de_client = models.BooleanField(
        default=True,
        verbose_name="Message du client",
        help_text="True = client vers étude, False = étude vers client"
    )

    # Statut
    lu = models.BooleanField(default=False, verbose_name="Lu")
    date_lecture = models.DateTimeField(null=True, blank=True)

    # Pièces jointes
    piece_jointe = models.FileField(
        upload_to='portail_messages/',
        null=True,
        blank=True,
        verbose_name="Pièce jointe"
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Message portail"
        verbose_name_plural = "Messages portail"

    def __str__(self):
        direction = "→" if self.est_de_client else "←"
        return f"{self.client.nom_complet} {direction} {self.sujet[:50]}"


class NotificationClient(models.Model):
    """Notifications push pour le client"""

    TYPE_CHOICES = [
        ('nouveau_document', 'Nouveau document disponible'),
        ('mise_a_jour_dossier', 'Mise à jour dossier'),
        ('paiement_recu', 'Paiement reçu'),
        ('message', 'Nouveau message'),
        ('rappel', 'Rappel'),
    ]

    client = models.ForeignKey(
        ClientPortail,
        on_delete=models.CASCADE,
        related_name='notifications'
    )
    type_notification = models.CharField(
        max_length=30,
        choices=TYPE_CHOICES,
        verbose_name="Type"
    )
    titre = models.CharField(max_length=200, verbose_name="Titre")
    message = models.TextField(verbose_name="Message")
    lien = models.CharField(max_length=500, blank=True, verbose_name="Lien")

    lu = models.BooleanField(default=False, verbose_name="Lu")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Notification client"
        verbose_name_plural = "Notifications clients"

    def __str__(self):
        return f"{self.titre} - {self.client.nom_complet}"


class DemandeContact(models.Model):
    """Demandes de contact depuis le formulaire public"""

    STATUT_CHOICES = [
        ('nouveau', 'Nouveau'),
        ('en_cours', 'En cours de traitement'),
        ('traite', 'Traité'),
        ('archive', 'Archivé'),
    ]

    nom = models.CharField(max_length=200, verbose_name="Nom complet")
    email = models.EmailField(verbose_name="Email")
    telephone = models.CharField(max_length=50, blank=True, verbose_name="Téléphone")
    message = models.TextField(verbose_name="Message")

    statut = models.CharField(
        max_length=20,
        choices=STATUT_CHOICES,
        default='nouveau',
        verbose_name="Statut"
    )
    notes_internes = models.TextField(blank=True, verbose_name="Notes internes")

    created_at = models.DateTimeField(auto_now_add=True)
    traite_par = models.ForeignKey(
        'gestion.Utilisateur',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='demandes_contact_traitees',
        verbose_name="Traité par"
    )
    date_traitement = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Demande de contact"
        verbose_name_plural = "Demandes de contact"

    def __str__(self):
        return f"{self.nom} - {self.created_at.strftime('%d/%m/%Y')}"
