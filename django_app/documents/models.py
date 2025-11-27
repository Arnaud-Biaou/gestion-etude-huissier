"""
Module Documents - Gestion Automatique de Documents pour Étude d'Huissier
Génération automatique, stockage cloud, modèles, signatures électroniques
"""
from django.db import models
from django.conf import settings
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError
import uuid
import hashlib
import os
import json
from datetime import timedelta


class CloudConnection(models.Model):
    """Connexion aux services de stockage cloud"""
    SERVICE_CHOICES = [
        ('google_drive', 'Google Drive'),
        ('dropbox', 'Dropbox'),
        ('onedrive', 'OneDrive'),
        ('local', 'Stockage Local'),
        ('s3', 'Amazon S3'),
    ]

    STATUT_CHOICES = [
        ('actif', 'Actif'),
        ('inactif', 'Inactif'),
        ('erreur', 'Erreur de connexion'),
        ('expire', 'Token expiré'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    service = models.CharField(max_length=20, choices=SERVICE_CHOICES)
    nom_compte = models.CharField(max_length=200, verbose_name="Nom du compte")
    email_compte = models.EmailField(blank=True, null=True)
    access_token = models.TextField(blank=True, null=True)
    refresh_token = models.TextField(blank=True, null=True)
    token_expiry = models.DateTimeField(blank=True, null=True)
    dossier_racine = models.CharField(max_length=500, default='/', verbose_name="Dossier racine")
    espace_total = models.BigIntegerField(default=0, verbose_name="Espace total (octets)")
    espace_utilise = models.BigIntegerField(default=0, verbose_name="Espace utilisé (octets)")
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default='inactif')
    est_principal = models.BooleanField(default=False, verbose_name="Stockage principal")
    configuration = models.JSONField(default=dict, blank=True, verbose_name="Configuration additionnelle")
    date_connexion = models.DateTimeField(auto_now_add=True)
    derniere_sync = models.DateTimeField(blank=True, null=True)
    utilisateur = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='cloud_connections'
    )

    class Meta:
        verbose_name = "Connexion Cloud"
        verbose_name_plural = "Connexions Cloud"
        ordering = ['-est_principal', 'service', 'nom_compte']

    def __str__(self):
        return f"{self.get_service_display()} - {self.nom_compte}"

    @property
    def espace_disponible(self):
        return max(0, self.espace_total - self.espace_utilise)

    @property
    def pourcentage_utilise(self):
        if self.espace_total == 0:
            return 0
        return round((self.espace_utilise / self.espace_total) * 100, 2)

    def est_token_expire(self):
        if self.token_expiry is None:
            return False
        return timezone.now() >= self.token_expiry


class DossierVirtuel(models.Model):
    """Structure de dossiers virtuels pour l'organisation des documents"""
    TYPE_DOSSIER_CHOICES = [
        ('racine', 'Racine'),
        ('dossier_juridique', 'Dossier Juridique'),
        ('actes', '01_Actes'),
        ('decisions', '02_Decisions_Titres'),
        ('pieces', '03_Pieces_Client'),
        ('correspondances', '04_Correspondances'),
        ('facturation', '05_Facturation'),
        ('divers', '06_Divers'),
        ('archives', 'Archives'),
        ('modeles', 'Modèles'),
        ('corbeille', 'Corbeille'),
        ('personnel', 'Personnel'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    nom = models.CharField(max_length=255)
    type_dossier = models.CharField(max_length=50, choices=TYPE_DOSSIER_CHOICES, default='personnel')
    chemin = models.CharField(max_length=1000, verbose_name="Chemin complet")
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='sous_dossiers'
    )
    dossier_juridique = models.ForeignKey(
        'gestion.Dossier',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='dossiers_virtuels'
    )
    cloud_connection = models.ForeignKey(
        CloudConnection,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    cloud_id = models.CharField(max_length=500, blank=True, null=True, verbose_name="ID Cloud")
    couleur = models.CharField(max_length=7, default='#1a365d', verbose_name="Couleur")
    icone = models.CharField(max_length=50, default='folder', verbose_name="Icône")
    est_systeme = models.BooleanField(default=False, verbose_name="Dossier système")
    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)
    cree_par = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='dossiers_virtuels_crees'
    )

    class Meta:
        verbose_name = "Dossier Virtuel"
        verbose_name_plural = "Dossiers Virtuels"
        ordering = ['chemin']
        unique_together = ['parent', 'nom']

    def __str__(self):
        return self.chemin

    def save(self, *args, **kwargs):
        if self.parent:
            self.chemin = f"{self.parent.chemin}/{self.nom}"
        else:
            self.chemin = f"/{self.nom}"
        super().save(*args, **kwargs)

    @property
    def profondeur(self):
        return self.chemin.count('/') - 1

    def get_arborescence(self):
        """Retourne tous les sous-dossiers récursivement"""
        result = [self]
        for enfant in self.sous_dossiers.all():
            result.extend(enfant.get_arborescence())
        return result


class Document(models.Model):
    """Document stocké dans le système"""
    TYPE_DOCUMENT_CHOICES = [
        # Actes de procédure
        ('acte_commandement', 'Commandement de payer'),
        ('acte_signification', 'Signification de décision'),
        ('acte_pv_saisie', 'Procès-verbal de saisie'),
        ('acte_pv_constat', 'Procès-verbal de constat'),
        ('acte_denonciation', 'Dénonciation'),
        ('acte_autre', 'Autre acte'),
        # Documents juridiques
        ('decision_justice', 'Décision de justice'),
        ('titre_executoire', 'Titre exécutoire'),
        ('jugement', 'Jugement'),
        ('ordonnance', 'Ordonnance'),
        # Documents financiers
        ('facture', 'Facture'),
        ('devis', 'Devis'),
        ('recu', 'Reçu de paiement'),
        ('note_honoraires', 'Note d\'honoraires'),
        ('decompte', 'Décompte de recouvrement'),
        # Correspondances
        ('lettre_mise_demeure', 'Lettre de mise en demeure'),
        ('lettre_relance', 'Lettre de relance'),
        ('courrier', 'Courrier'),
        ('email', 'Email archivé'),
        # Documents administratifs
        ('fiche_dossier', 'Fiche du dossier'),
        ('piece_identite', 'Pièce d\'identité'),
        ('contrat', 'Contrat'),
        ('attestation', 'Attestation'),
        # Autres
        ('photo', 'Photo'),
        ('scan', 'Document scanné'),
        ('autre', 'Autre'),
    ]

    STATUT_CHOICES = [
        ('brouillon', 'Brouillon'),
        ('genere', 'Généré'),
        ('valide', 'Validé'),
        ('signe', 'Signé'),
        ('archive', 'Archivé'),
        ('supprime', 'Supprimé'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    nom = models.CharField(max_length=255, verbose_name="Nom du fichier")
    nom_original = models.CharField(max_length=255, verbose_name="Nom original")
    type_document = models.CharField(max_length=50, choices=TYPE_DOCUMENT_CHOICES, default='autre')
    description = models.TextField(blank=True, verbose_name="Description")

    # Stockage
    fichier = models.FileField(upload_to='documents/%Y/%m/')
    chemin_local = models.CharField(max_length=1000, blank=True)
    cloud_connection = models.ForeignKey(
        CloudConnection,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    cloud_id = models.CharField(max_length=500, blank=True, null=True)
    chemin_cloud = models.CharField(max_length=1000, blank=True)

    # Organisation
    dossier = models.ForeignKey(
        DossierVirtuel,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='documents'
    )
    dossier_juridique = models.ForeignKey(
        'gestion.Dossier',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='documents'
    )

    # Métadonnées
    taille = models.BigIntegerField(default=0, verbose_name="Taille (octets)")
    mime_type = models.CharField(max_length=100, blank=True)
    extension = models.CharField(max_length=20, blank=True)
    hash_md5 = models.CharField(max_length=32, blank=True, verbose_name="Hash MD5")
    hash_sha256 = models.CharField(max_length=64, blank=True, verbose_name="Hash SHA256")

    # Versioning
    version = models.PositiveIntegerField(default=1)
    document_parent = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='versions'
    )

    # Statut et traçabilité
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default='genere')
    est_modele = models.BooleanField(default=False, verbose_name="Est un modèle")
    est_genere = models.BooleanField(default=False, verbose_name="Généré automatiquement")
    contenu_texte = models.TextField(blank=True, verbose_name="Contenu OCR")
    metadata = models.JSONField(default=dict, blank=True, verbose_name="Métadonnées")

    # Dates et utilisateurs
    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)
    date_suppression = models.DateTimeField(blank=True, null=True)
    cree_par = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='documents_crees'
    )
    modifie_par = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='documents_modifies'
    )

    class Meta:
        verbose_name = "Document"
        verbose_name_plural = "Documents"
        ordering = ['-date_creation']

    def __str__(self):
        return f"{self.nom} ({self.get_type_document_display()})"

    def save(self, *args, **kwargs):
        if self.fichier:
            self.nom_original = self.fichier.name.split('/')[-1]
            if not self.extension:
                self.extension = os.path.splitext(self.nom_original)[1].lower()
            if not self.mime_type:
                self.mime_type = self._get_mime_type()
        super().save(*args, **kwargs)

    def _get_mime_type(self):
        mime_types = {
            '.pdf': 'application/pdf',
            '.doc': 'application/msword',
            '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            '.xls': 'application/vnd.ms-excel',
            '.xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.png': 'image/png',
            '.gif': 'image/gif',
            '.txt': 'text/plain',
            '.html': 'text/html',
        }
        return mime_types.get(self.extension, 'application/octet-stream')

    def calculer_hash(self):
        if self.fichier:
            md5 = hashlib.md5()
            sha256 = hashlib.sha256()
            for chunk in self.fichier.chunks():
                md5.update(chunk)
                sha256.update(chunk)
            self.hash_md5 = md5.hexdigest()
            self.hash_sha256 = sha256.hexdigest()

    @property
    def taille_humaine(self):
        for unite in ['o', 'Ko', 'Mo', 'Go']:
            if self.taille < 1024:
                return f"{self.taille:.1f} {unite}"
            self.taille /= 1024
        return f"{self.taille:.1f} To"

    def creer_version(self, nouveau_fichier, utilisateur):
        """Crée une nouvelle version du document"""
        nouvelle_version = Document(
            nom=self.nom,
            nom_original=nouveau_fichier.name,
            type_document=self.type_document,
            fichier=nouveau_fichier,
            dossier=self.dossier,
            dossier_juridique=self.dossier_juridique,
            version=self.version + 1,
            document_parent=self,
            cree_par=utilisateur,
        )
        nouvelle_version.save()
        return nouvelle_version


class VersionDocument(models.Model):
    """Historique des versions d'un document"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    document = models.ForeignKey(
        Document,
        on_delete=models.CASCADE,
        related_name='historique_versions'
    )
    numero_version = models.PositiveIntegerField()
    fichier = models.FileField(upload_to='documents/versions/%Y/%m/')
    taille = models.BigIntegerField(default=0)
    hash_md5 = models.CharField(max_length=32, blank=True)
    commentaire = models.TextField(blank=True)
    date = models.DateTimeField(auto_now_add=True)
    auteur = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True
    )

    class Meta:
        verbose_name = "Version de Document"
        verbose_name_plural = "Versions de Documents"
        ordering = ['-numero_version']
        unique_together = ['document', 'numero_version']

    def __str__(self):
        return f"{self.document.nom} - v{self.numero_version}"


class ModeleDocument(models.Model):
    """Modèles de documents avec variables dynamiques"""
    TYPE_MODELE_CHOICES = [
        ('acte', 'Acte de procédure'),
        ('courrier', 'Courrier/Lettre'),
        ('facture', 'Facture'),
        ('fiche', 'Fiche dossier'),
        ('autre', 'Autre'),
    ]

    FORMAT_CHOICES = [
        ('html', 'HTML'),
        ('docx', 'Word DOCX'),
        ('pdf', 'PDF'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    nom = models.CharField(max_length=255, verbose_name="Nom du modèle")
    code = models.CharField(max_length=50, unique=True, verbose_name="Code unique")
    type_modele = models.CharField(max_length=20, choices=TYPE_MODELE_CHOICES, default='autre')
    description = models.TextField(blank=True)

    # Contenu
    contenu_template = models.TextField(verbose_name="Contenu du template (HTML/Markdown)")
    format_sortie = models.CharField(max_length=10, choices=FORMAT_CHOICES, default='pdf')
    fichier_template = models.FileField(
        upload_to='modeles/',
        blank=True,
        null=True,
        verbose_name="Fichier template (DOCX)"
    )

    # Variables disponibles
    variables = models.JSONField(default=list, blank=True, verbose_name="Variables disponibles")
    variables_exemple = models.JSONField(default=dict, blank=True, verbose_name="Exemples de variables")

    # En-tête et pied de page
    avec_entete = models.BooleanField(default=True, verbose_name="Inclure en-tête étude")
    avec_pied_page = models.BooleanField(default=True, verbose_name="Inclure pied de page")

    # Configuration
    orientation = models.CharField(
        max_length=10,
        choices=[('portrait', 'Portrait'), ('paysage', 'Paysage')],
        default='portrait'
    )
    marge_haut = models.PositiveIntegerField(default=20, verbose_name="Marge haute (mm)")
    marge_bas = models.PositiveIntegerField(default=20, verbose_name="Marge basse (mm)")
    marge_gauche = models.PositiveIntegerField(default=20, verbose_name="Marge gauche (mm)")
    marge_droite = models.PositiveIntegerField(default=20, verbose_name="Marge droite (mm)")

    # Statut
    actif = models.BooleanField(default=True)
    est_systeme = models.BooleanField(default=False, verbose_name="Modèle système")
    ordre_affichage = models.PositiveIntegerField(default=100)

    # Traçabilité
    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)
    cree_par = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='documents_modeles_crees'
    )

    class Meta:
        verbose_name = "Modèle de Document"
        verbose_name_plural = "Modèles de Documents"
        ordering = ['ordre_affichage', 'nom']

    def __str__(self):
        return f"{self.nom} ({self.get_type_modele_display()})"

    def get_variables_disponibles(self):
        """Retourne la liste des variables avec leur description"""
        variables_standard = [
            {'nom': 'date_jour', 'description': 'Date du jour (format long)'},
            {'nom': 'date_court', 'description': 'Date du jour (format court)'},
            {'nom': 'heure', 'description': 'Heure actuelle'},
            {'nom': 'etude_nom', 'description': 'Nom de l\'étude'},
            {'nom': 'etude_adresse', 'description': 'Adresse de l\'étude'},
            {'nom': 'etude_telephone', 'description': 'Téléphone de l\'étude'},
            {'nom': 'huissier_nom', 'description': 'Nom de l\'huissier'},
            {'nom': 'utilisateur_nom', 'description': 'Nom de l\'utilisateur connecté'},
        ]
        return variables_standard + self.variables


class SignatureElectronique(models.Model):
    """Signature électronique pour les documents"""
    TYPE_SIGNATURE_CHOICES = [
        ('manuscrite', 'Signature manuscrite numérisée'),
        ('cachet', 'Cachet électronique'),
        ('certificat', 'Signature par certificat'),
        ('externe', 'Signature externe (DocuSign, etc.)'),
    ]

    STATUT_CHOICES = [
        ('en_attente', 'En attente de signature'),
        ('signe', 'Signé'),
        ('refuse', 'Refusé'),
        ('expire', 'Expiré'),
        ('annule', 'Annulé'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    document = models.ForeignKey(
        Document,
        on_delete=models.CASCADE,
        related_name='signatures'
    )
    type_signature = models.CharField(max_length=20, choices=TYPE_SIGNATURE_CHOICES)

    # Signataire
    signataire_nom = models.CharField(max_length=200)
    signataire_email = models.EmailField(blank=True)
    signataire_utilisateur = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    # Signature
    image_signature = models.ImageField(
        upload_to='signatures/',
        blank=True,
        null=True,
        verbose_name="Image de la signature"
    )
    position_x = models.PositiveIntegerField(default=0, verbose_name="Position X (px)")
    position_y = models.PositiveIntegerField(default=0, verbose_name="Position Y (px)")
    page = models.PositiveIntegerField(default=1, verbose_name="Page de signature")

    # Horodatage et vérification
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default='en_attente')
    date_demande = models.DateTimeField(auto_now_add=True)
    date_signature = models.DateTimeField(blank=True, null=True)
    date_expiration = models.DateTimeField(blank=True, null=True)

    # Certificat et validation
    hash_document = models.CharField(max_length=64, blank=True)
    certificat = models.TextField(blank=True, verbose_name="Certificat d'authenticité")
    ip_signataire = models.GenericIPAddressField(blank=True, null=True)
    user_agent = models.TextField(blank=True)

    # Service externe
    service_externe = models.CharField(max_length=50, blank=True)
    reference_externe = models.CharField(max_length=200, blank=True)

    class Meta:
        verbose_name = "Signature Électronique"
        verbose_name_plural = "Signatures Électroniques"
        ordering = ['-date_demande']

    def __str__(self):
        return f"Signature de {self.signataire_nom} - {self.get_statut_display()}"

    def signer(self, ip=None, user_agent=None):
        self.statut = 'signe'
        self.date_signature = timezone.now()
        if ip:
            self.ip_signataire = ip
        if user_agent:
            self.user_agent = user_agent
        self.generer_certificat()
        self.save()

    def generer_certificat(self):
        """Génère un certificat d'authenticité"""
        data = {
            'document_id': str(self.document.id),
            'document_hash': self.document.hash_sha256,
            'signataire': self.signataire_nom,
            'date_signature': self.date_signature.isoformat() if self.date_signature else None,
            'ip': self.ip_signataire,
        }
        self.certificat = json.dumps(data)


class PartageDocument(models.Model):
    """Lien de partage pour un document ou dossier"""
    TYPE_PARTAGE_CHOICES = [
        ('lecture', 'Lecture seule'),
        ('telechargement', 'Téléchargement'),
        ('modification', 'Modification'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    document = models.ForeignKey(
        Document,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='partages'
    )
    dossier = models.ForeignKey(
        DossierVirtuel,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='partages'
    )

    # Lien de partage
    token = models.CharField(max_length=100, unique=True, editable=False)
    lien = models.CharField(max_length=500, blank=True)
    type_partage = models.CharField(max_length=20, choices=TYPE_PARTAGE_CHOICES, default='lecture')

    # Sécurité
    mot_de_passe = models.CharField(max_length=100, blank=True, null=True)
    mot_de_passe_hash = models.CharField(max_length=128, blank=True)

    # Validité
    date_creation = models.DateTimeField(auto_now_add=True)
    date_expiration = models.DateTimeField(blank=True, null=True)
    nombre_acces_max = models.PositiveIntegerField(
        default=0,
        verbose_name="Nombre d'accès maximum (0 = illimité)"
    )
    nombre_acces = models.PositiveIntegerField(default=0, verbose_name="Nombre d'accès")

    # Destinataire
    destinataire_email = models.EmailField(blank=True)
    destinataire_nom = models.CharField(max_length=200, blank=True)

    # Traçabilité
    actif = models.BooleanField(default=True)
    cree_par = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True
    )

    class Meta:
        verbose_name = "Partage de Document"
        verbose_name_plural = "Partages de Documents"
        ordering = ['-date_creation']

    def __str__(self):
        obj = self.document or self.dossier
        return f"Partage: {obj}"

    def save(self, *args, **kwargs):
        if not self.token:
            self.token = uuid.uuid4().hex[:32]
        if not self.lien:
            self.lien = f"/partage/{self.token}"
        super().save(*args, **kwargs)

    @property
    def est_expire(self):
        if self.date_expiration and timezone.now() > self.date_expiration:
            return True
        if self.nombre_acces_max > 0 and self.nombre_acces >= self.nombre_acces_max:
            return True
        return False

    def verifier_mot_de_passe(self, mot_de_passe):
        if not self.mot_de_passe_hash:
            return True
        return hashlib.sha256(mot_de_passe.encode()).hexdigest() == self.mot_de_passe_hash

    def enregistrer_acces(self, ip=None, user_agent=None):
        self.nombre_acces += 1
        self.save()
        AccesPartage.objects.create(
            partage=self,
            ip=ip,
            user_agent=user_agent
        )


class AccesPartage(models.Model):
    """Journal des accès aux documents partagés"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    partage = models.ForeignKey(
        PartageDocument,
        on_delete=models.CASCADE,
        related_name='acces'
    )
    date_acces = models.DateTimeField(auto_now_add=True)
    ip = models.GenericIPAddressField(blank=True, null=True)
    user_agent = models.TextField(blank=True)
    action = models.CharField(max_length=50, default='consultation')

    class Meta:
        verbose_name = "Accès Partage"
        verbose_name_plural = "Accès Partages"
        ordering = ['-date_acces']


class AuditDocument(models.Model):
    """Journal d'audit pour tous les documents"""
    ACTION_CHOICES = [
        ('creation', 'Création'),
        ('lecture', 'Lecture'),
        ('modification', 'Modification'),
        ('suppression', 'Suppression'),
        ('restauration', 'Restauration'),
        ('telechargement', 'Téléchargement'),
        ('partage', 'Partage'),
        ('signature', 'Signature'),
        ('impression', 'Impression'),
        ('deplacement', 'Déplacement'),
        ('copie', 'Copie'),
        ('archivage', 'Archivage'),
        ('generation', 'Génération'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    document = models.ForeignKey(
        Document,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='audits'
    )
    dossier = models.ForeignKey(
        DossierVirtuel,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='audits'
    )

    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    details = models.JSONField(default=dict, blank=True)

    utilisateur = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True
    )
    date = models.DateTimeField(auto_now_add=True)
    ip = models.GenericIPAddressField(blank=True, null=True)
    user_agent = models.TextField(blank=True)

    class Meta:
        verbose_name = "Audit Document"
        verbose_name_plural = "Audits Documents"
        ordering = ['-date']
        indexes = [
            models.Index(fields=['document', '-date']),
            models.Index(fields=['utilisateur', '-date']),
            models.Index(fields=['action', '-date']),
        ]

    def __str__(self):
        obj_name = self.document.nom if self.document else (self.dossier.nom if self.dossier else 'N/A')
        return f"{self.get_action_display()} - {obj_name} - {self.date}"


class GenerationDocument(models.Model):
    """Suivi des générations automatiques de documents"""
    STATUT_CHOICES = [
        ('en_attente', 'En attente'),
        ('en_cours', 'En cours'),
        ('termine', 'Terminé'),
        ('erreur', 'Erreur'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    modele = models.ForeignKey(
        ModeleDocument,
        on_delete=models.SET_NULL,
        null=True,
        related_name='generations'
    )
    document_genere = models.ForeignKey(
        Document,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='generation'
    )

    # Contexte
    dossier_juridique = models.ForeignKey(
        'gestion.Dossier',
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    facture = models.ForeignKey(
        'gestion.Facture',
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    # Variables utilisées
    variables = models.JSONField(default=dict)

    # Statut
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default='en_attente')
    message_erreur = models.TextField(blank=True)

    # Traçabilité
    date_demande = models.DateTimeField(auto_now_add=True)
    date_generation = models.DateTimeField(blank=True, null=True)
    duree_generation = models.FloatField(default=0, verbose_name="Durée (secondes)")
    cree_par = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True
    )

    class Meta:
        verbose_name = "Génération de Document"
        verbose_name_plural = "Générations de Documents"
        ordering = ['-date_demande']

    def __str__(self):
        return f"Génération {self.modele.nom if self.modele else 'N/A'} - {self.get_statut_display()}"


class ConfigurationDocuments(models.Model):
    """Configuration singleton pour le module Documents"""
    # Storage
    stockage_local_path = models.CharField(
        max_length=500,
        default='/media/documents',
        verbose_name="Chemin de stockage local"
    )
    limite_upload_mo = models.PositiveIntegerField(
        default=50,
        verbose_name="Limite upload (Mo)"
    )
    types_autorises = models.JSONField(
        default=list,
        verbose_name="Extensions autorisées",
        blank=True
    )

    # Génération PDF
    logo_etude = models.ImageField(
        upload_to='config/',
        blank=True,
        null=True,
        verbose_name="Logo de l'étude"
    )
    nom_etude = models.CharField(max_length=200, default="", verbose_name="Nom de l'étude")
    adresse_etude = models.TextField(default="", verbose_name="Adresse de l'étude")
    telephone_etude = models.CharField(max_length=50, default="", verbose_name="Téléphone")
    email_etude = models.EmailField(default="", blank=True, verbose_name="Email")
    ifu_etude = models.CharField(max_length=50, default="", verbose_name="IFU")
    rccm_etude = models.CharField(max_length=50, default="", verbose_name="RCCM")

    # Huissier
    nom_huissier = models.CharField(max_length=200, default="", verbose_name="Nom de l'huissier")
    qualite_huissier = models.CharField(
        max_length=100,
        default="Huissier de Justice",
        verbose_name="Qualité"
    )
    signature_huissier = models.ImageField(
        upload_to='config/',
        blank=True,
        null=True,
        verbose_name="Signature de l'huissier"
    )
    cachet_etude = models.ImageField(
        upload_to='config/',
        blank=True,
        null=True,
        verbose_name="Cachet de l'étude"
    )

    # Partage
    duree_partage_defaut = models.PositiveIntegerField(
        default=7,
        verbose_name="Durée de partage par défaut (jours)"
    )
    autoriser_partage_public = models.BooleanField(
        default=False,
        verbose_name="Autoriser le partage public"
    )

    # Corbeille
    duree_retention_corbeille = models.PositiveIntegerField(
        default=30,
        verbose_name="Rétention corbeille (jours)"
    )

    # OCR
    ocr_actif = models.BooleanField(default=False, verbose_name="OCR activé")

    # Audit
    audit_actif = models.BooleanField(default=True, verbose_name="Audit activé")
    duree_retention_audit = models.PositiveIntegerField(
        default=365,
        verbose_name="Rétention audit (jours)"
    )

    class Meta:
        verbose_name = "Configuration Documents"
        verbose_name_plural = "Configuration Documents"

    def __str__(self):
        return "Configuration du module Documents"

    @classmethod
    def get_instance(cls):
        """Pattern Singleton - retourne l'unique instance"""
        instance, created = cls.objects.get_or_create(pk=1)
        if created:
            instance.types_autorises = [
                '.pdf', '.doc', '.docx', '.xls', '.xlsx',
                '.jpg', '.jpeg', '.png', '.gif',
                '.txt', '.csv', '.rtf'
            ]
            instance.save()
        return instance

    def save(self, *args, **kwargs):
        self.pk = 1  # Force singleton
        super().save(*args, **kwargs)


class NumeroActe(models.Model):
    """Compteur pour la numérotation automatique des actes"""
    annee = models.PositiveIntegerField(unique=True)
    dernier_numero = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name = "Numéro d'Acte"
        verbose_name_plural = "Numéros d'Actes"

    def __str__(self):
        return f"Compteur {self.annee}: {self.dernier_numero}"

    @classmethod
    def prochain_numero(cls, annee=None):
        """Génère le prochain numéro d'acte pour l'année"""
        if annee is None:
            annee = timezone.now().year
        compteur, created = cls.objects.get_or_create(annee=annee)
        compteur.dernier_numero += 1
        compteur.save()
        return f"{compteur.dernier_numero:04d}/{annee}"
