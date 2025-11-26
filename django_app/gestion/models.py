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


# ============================================================================
# MODÈLES DU MODULE TRÉSORERIE
# ============================================================================

class Caisse(models.Model):
    """Caisse de l'étude - peut y avoir plusieurs caisses (une par site/agence)"""
    STATUT_CHOICES = [
        ('ouverte', 'Ouverte'),
        ('fermee', 'Fermée'),
        ('verification', 'En cours de vérification'),
    ]

    nom = models.CharField(max_length=100, verbose_name='Nom de la caisse')
    site = models.CharField(max_length=200, verbose_name='Site/Localisation')
    solde_initial = models.DecimalField(
        max_digits=15, decimal_places=0, default=0, verbose_name='Solde initial'
    )
    solde_actuel = models.DecimalField(
        max_digits=15, decimal_places=0, default=0, verbose_name='Solde actuel'
    )
    responsable = models.ForeignKey(
        Collaborateur, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='caisses_responsable', verbose_name='Responsable'
    )
    statut = models.CharField(
        max_length=20, choices=STATUT_CHOICES, default='fermee', verbose_name='Statut'
    )
    actif = models.BooleanField(default=True, verbose_name='Caisse active')
    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Caisse'
        verbose_name_plural = 'Caisses'
        ordering = ['nom']

    def __str__(self):
        return f"{self.nom} - {self.site}"

    def get_solde_formate(self):
        return f"{self.solde_actuel:,.0f} FCFA"


class JournalCaisse(models.Model):
    """Journal quotidien de caisse - ouverture/fermeture"""
    caisse = models.ForeignKey(
        Caisse, on_delete=models.CASCADE, related_name='journaux', verbose_name='Caisse'
    )
    date = models.DateField(default=timezone.now, verbose_name='Date')
    date_ouverture = models.DateTimeField(null=True, blank=True, verbose_name='Date/heure ouverture')
    date_fermeture = models.DateTimeField(null=True, blank=True, verbose_name='Date/heure fermeture')
    solde_ouverture = models.DecimalField(
        max_digits=15, decimal_places=0, default=0, verbose_name='Solde à l\'ouverture'
    )
    solde_fermeture = models.DecimalField(
        max_digits=15, decimal_places=0, null=True, blank=True, verbose_name='Solde à la fermeture'
    )
    solde_theorique = models.DecimalField(
        max_digits=15, decimal_places=0, null=True, blank=True, verbose_name='Solde théorique'
    )
    ecart = models.DecimalField(
        max_digits=15, decimal_places=0, null=True, blank=True, verbose_name='Écart constaté'
    )
    observations = models.TextField(blank=True, verbose_name='Observations')
    ouvert_par = models.ForeignKey(
        Utilisateur, on_delete=models.SET_NULL, null=True,
        related_name='caisses_ouvertes', verbose_name='Ouvert par'
    )
    ferme_par = models.ForeignKey(
        Utilisateur, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='caisses_fermees', verbose_name='Fermé par'
    )

    class Meta:
        verbose_name = 'Journal de caisse'
        verbose_name_plural = 'Journaux de caisse'
        ordering = ['-date', '-date_ouverture']
        unique_together = ['caisse', 'date']

    def __str__(self):
        return f"Journal {self.caisse.nom} - {self.date}"

    def calculer_ecart(self):
        if self.solde_fermeture is not None and self.solde_theorique is not None:
            self.ecart = self.solde_fermeture - self.solde_theorique
            return self.ecart
        return None


class OperationTresorerie(models.Model):
    """Opérations de trésorerie (encaissements et décaissements)"""
    TYPE_OPERATION_CHOICES = [
        ('encaissement', 'Encaissement'),
        ('decaissement', 'Décaissement'),
    ]

    TYPE_ENCAISSEMENT_CHOICES = [
        ('honoraires', 'Honoraires'),
        ('provision', 'Provision'),
        ('emoluments', 'Émoluments'),
        ('frais_deplacement', 'Frais de déplacement'),
        ('remboursement_frais', 'Remboursement de frais avancés'),
        ('consignation', 'Consignation reçue'),
        ('recouvrement', 'Somme recouvrée'),
        ('autre_recette', 'Autre recette'),
    ]

    TYPE_DECAISSEMENT_CHOICES = [
        ('reversement_client', 'Reversement au client'),
        ('frais_procedure', 'Frais de procédure'),
        ('timbres', 'Timbres fiscaux'),
        ('frais_actes', 'Frais d\'actes'),
        ('frais_justice', 'Frais de justice'),
        ('frais_deplacement', 'Frais de déplacement'),
        ('remuneration', 'Rémunération collaborateurs'),
        ('loyer', 'Loyer'),
        ('electricite', 'Électricité'),
        ('internet', 'Internet/Téléphone'),
        ('fournitures', 'Fournitures de bureau'),
        ('impots_taxes', 'Impôts et taxes'),
        ('autre_depense', 'Autre dépense'),
    ]

    MODE_PAIEMENT_CHOICES = [
        ('especes', 'Espèces'),
        ('cheque', 'Chèque'),
        ('virement', 'Virement bancaire'),
        ('mobile_money', 'Mobile Money'),
        ('carte', 'Carte bancaire'),
    ]

    STATUT_CHOICES = [
        ('en_attente', 'En attente'),
        ('en_attente_approbation', 'En attente d\'approbation'),
        ('approuve', 'Approuvé'),
        ('valide', 'Validé'),
        ('paye', 'Payé'),
        ('rejete', 'Rejeté'),
        ('annule', 'Annulé'),
    ]

    # Informations générales
    reference = models.CharField(max_length=30, unique=True, verbose_name='Référence')
    type_operation = models.CharField(
        max_length=20, choices=TYPE_OPERATION_CHOICES, verbose_name='Type d\'opération'
    )
    categorie = models.CharField(max_length=30, verbose_name='Catégorie')
    montant = models.DecimalField(max_digits=15, decimal_places=0, verbose_name='Montant')
    date_operation = models.DateField(default=timezone.now, verbose_name='Date opération')
    date_valeur = models.DateField(null=True, blank=True, verbose_name='Date valeur')

    # Mode de paiement
    mode_paiement = models.CharField(
        max_length=20, choices=MODE_PAIEMENT_CHOICES, default='especes', verbose_name='Mode de paiement'
    )
    reference_paiement = models.CharField(
        max_length=100, blank=True, verbose_name='Référence paiement (n° chèque, etc.)'
    )

    # Liens
    caisse = models.ForeignKey(
        Caisse, on_delete=models.PROTECT, related_name='operations', verbose_name='Caisse'
    )
    dossier = models.ForeignKey(
        Dossier, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='operations_tresorerie', verbose_name='Dossier lié'
    )
    partie = models.ForeignKey(
        Partie, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='operations_tresorerie', verbose_name='Partie concernée'
    )
    consignation = models.ForeignKey(
        'Consignation', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='operations', verbose_name='Consignation liée'
    )

    # Tiers (pour encaissements/décaissements)
    emetteur = models.CharField(max_length=200, blank=True, verbose_name='Émetteur du paiement')
    beneficiaire = models.CharField(max_length=200, blank=True, verbose_name='Bénéficiaire')
    motif = models.TextField(blank=True, verbose_name='Motif détaillé')

    # Justificatif
    justificatif = models.FileField(
        upload_to='tresorerie/justificatifs/%Y/%m/', blank=True, verbose_name='Justificatif'
    )

    # Workflow
    statut = models.CharField(
        max_length=25, choices=STATUT_CHOICES, default='en_attente', verbose_name='Statut'
    )
    montant_seuil_validation = models.DecimalField(
        max_digits=15, decimal_places=0, default=100000,
        verbose_name='Seuil de validation obligatoire'
    )

    # Approbation
    approuve_par = models.ForeignKey(
        Utilisateur, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='operations_approuvees', verbose_name='Approuvé par'
    )
    date_approbation = models.DateTimeField(null=True, blank=True, verbose_name='Date approbation')
    motif_rejet = models.TextField(blank=True, verbose_name='Motif de rejet')

    # Annulation
    annule_par = models.ForeignKey(
        Utilisateur, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='operations_annulees', verbose_name='Annulé par'
    )
    date_annulation = models.DateTimeField(null=True, blank=True, verbose_name='Date annulation')
    motif_annulation = models.TextField(blank=True, verbose_name='Motif d\'annulation')

    # Audit
    cree_par = models.ForeignKey(
        Utilisateur, on_delete=models.SET_NULL, null=True,
        related_name='operations_creees', verbose_name='Créé par'
    )
    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Opération de trésorerie'
        verbose_name_plural = 'Opérations de trésorerie'
        ordering = ['-date_operation', '-date_creation']

    def __str__(self):
        return f"{self.reference} - {self.get_type_operation_display()} {self.montant:,.0f} FCFA"

    @classmethod
    def generer_reference(cls, type_op):
        now = timezone.now()
        prefix = 'ENC' if type_op == 'encaissement' else 'DEC'
        count = cls.objects.filter(
            type_operation=type_op,
            date_creation__year=now.year,
            date_creation__month=now.month
        ).count() + 1
        return f"{prefix}-{now.year}{now.month:02d}-{count:04d}"

    def peut_etre_modifie(self):
        """Une opération validée ne peut plus être modifiée"""
        return self.statut in ['en_attente', 'en_attente_approbation']

    def necessite_approbation(self):
        """Les décaissements au-dessus du seuil nécessitent une approbation"""
        return (
            self.type_operation == 'decaissement' and
            self.montant >= self.montant_seuil_validation
        )


class Consignation(models.Model):
    """Compte séquestre / Consignations (fonds clients)"""
    STATUT_CHOICES = [
        ('active', 'Active'),
        ('partielle', 'Partiellement reversée'),
        ('reversee', 'Totalement reversée'),
        ('bloquee', 'Bloquée'),
    ]

    reference = models.CharField(max_length=30, unique=True, verbose_name='Référence')

    # Client / Dossier
    client = models.ForeignKey(
        Partie, on_delete=models.PROTECT, related_name='consignations',
        verbose_name='Client (bénéficiaire)'
    )
    dossier = models.ForeignKey(
        Dossier, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='consignations', verbose_name='Dossier lié'
    )

    # Montants
    montant_initial = models.DecimalField(
        max_digits=15, decimal_places=0, verbose_name='Montant initial'
    )
    montant_reverse = models.DecimalField(
        max_digits=15, decimal_places=0, default=0, verbose_name='Montant déjà reversé'
    )
    montant_restant = models.DecimalField(
        max_digits=15, decimal_places=0, verbose_name='Montant restant'
    )

    # Informations
    objet = models.TextField(verbose_name='Objet de la consignation')
    debiteur = models.CharField(max_length=200, blank=True, verbose_name='Débiteur (origine des fonds)')
    date_reception = models.DateField(default=timezone.now, verbose_name='Date de réception')
    date_echeance_reversement = models.DateField(
        null=True, blank=True, verbose_name='Date limite de reversement'
    )

    # Statut
    statut = models.CharField(
        max_length=20, choices=STATUT_CHOICES, default='active', verbose_name='Statut'
    )

    # Audit
    cree_par = models.ForeignKey(
        Utilisateur, on_delete=models.SET_NULL, null=True,
        related_name='consignations_creees', verbose_name='Créé par'
    )
    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Consignation'
        verbose_name_plural = 'Consignations'
        ordering = ['-date_reception']

    def __str__(self):
        return f"{self.reference} - {self.client} ({self.montant_restant:,.0f} FCFA)"

    @classmethod
    def generer_reference(cls):
        now = timezone.now()
        count = cls.objects.filter(date_creation__year=now.year).count() + 1
        return f"CONS-{now.year}-{count:04d}"

    def save(self, *args, **kwargs):
        if not self.montant_restant:
            self.montant_restant = self.montant_initial - self.montant_reverse
        super().save(*args, **kwargs)

    def mettre_a_jour_statut(self):
        if self.montant_restant <= 0:
            self.statut = 'reversee'
        elif self.montant_reverse > 0:
            self.statut = 'partielle'
        else:
            self.statut = 'active'
        self.save()

    def est_en_retard(self):
        if self.date_echeance_reversement:
            return timezone.now().date() > self.date_echeance_reversement and self.montant_restant > 0
        return False


class MouvementConsignation(models.Model):
    """Mouvements sur une consignation"""
    TYPE_MOUVEMENT_CHOICES = [
        ('reception', 'Réception de fonds'),
        ('reversement', 'Reversement au client'),
        ('ajustement', 'Ajustement'),
    ]

    consignation = models.ForeignKey(
        Consignation, on_delete=models.CASCADE, related_name='mouvements',
        verbose_name='Consignation'
    )
    type_mouvement = models.CharField(
        max_length=20, choices=TYPE_MOUVEMENT_CHOICES, verbose_name='Type de mouvement'
    )
    montant = models.DecimalField(max_digits=15, decimal_places=0, verbose_name='Montant')
    date_mouvement = models.DateField(default=timezone.now, verbose_name='Date')

    # Détails
    mode_paiement = models.CharField(max_length=20, blank=True, verbose_name='Mode de paiement')
    reference_paiement = models.CharField(max_length=100, blank=True, verbose_name='Référence')
    observations = models.TextField(blank=True, verbose_name='Observations')

    # Lien avec opération de trésorerie
    operation = models.OneToOneField(
        OperationTresorerie, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='mouvement_consignation', verbose_name='Opération liée'
    )

    # Audit
    cree_par = models.ForeignKey(
        Utilisateur, on_delete=models.SET_NULL, null=True,
        related_name='mouvements_consignation_crees', verbose_name='Créé par'
    )
    date_creation = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Mouvement de consignation'
        verbose_name_plural = 'Mouvements de consignation'
        ordering = ['-date_mouvement', '-date_creation']

    def __str__(self):
        return f"{self.get_type_mouvement_display()} {self.montant:,.0f} FCFA - {self.consignation.reference}"


class CompteBancaire(models.Model):
    """Comptes bancaires de l'étude"""
    TYPE_COMPTE_CHOICES = [
        ('courant', 'Compte courant'),
        ('epargne', 'Compte épargne'),
        ('sequestre', 'Compte séquestre'),
    ]

    nom = models.CharField(max_length=100, verbose_name='Nom du compte')
    banque = models.CharField(max_length=100, verbose_name='Banque')
    numero_compte = models.CharField(max_length=50, verbose_name='Numéro de compte')
    iban = models.CharField(max_length=50, blank=True, verbose_name='IBAN')
    bic = models.CharField(max_length=20, blank=True, verbose_name='BIC/SWIFT')
    type_compte = models.CharField(
        max_length=20, choices=TYPE_COMPTE_CHOICES, default='courant', verbose_name='Type'
    )
    solde_actuel = models.DecimalField(
        max_digits=15, decimal_places=0, default=0, verbose_name='Solde actuel'
    )
    actif = models.BooleanField(default=True, verbose_name='Compte actif')
    date_creation = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Compte bancaire'
        verbose_name_plural = 'Comptes bancaires'
        ordering = ['nom']

    def __str__(self):
        return f"{self.nom} - {self.banque} ({self.numero_compte})"


class RapprochementBancaire(models.Model):
    """Rapprochement bancaire"""
    STATUT_CHOICES = [
        ('en_cours', 'En cours'),
        ('termine', 'Terminé'),
        ('valide', 'Validé'),
    ]

    compte = models.ForeignKey(
        CompteBancaire, on_delete=models.CASCADE, related_name='rapprochements',
        verbose_name='Compte bancaire'
    )
    date_debut = models.DateField(verbose_name='Date début période')
    date_fin = models.DateField(verbose_name='Date fin période')

    # Soldes
    solde_releve = models.DecimalField(
        max_digits=15, decimal_places=0, null=True, blank=True, verbose_name='Solde relevé bancaire'
    )
    solde_comptable = models.DecimalField(
        max_digits=15, decimal_places=0, null=True, blank=True, verbose_name='Solde comptable'
    )
    ecart = models.DecimalField(
        max_digits=15, decimal_places=0, null=True, blank=True, verbose_name='Écart'
    )

    # Fichier importé
    fichier_releve = models.FileField(
        upload_to='tresorerie/releves/%Y/%m/', blank=True, verbose_name='Fichier relevé'
    )
    format_fichier = models.CharField(max_length=10, blank=True, verbose_name='Format (CSV, OFX)')

    # Statut
    statut = models.CharField(
        max_length=20, choices=STATUT_CHOICES, default='en_cours', verbose_name='Statut'
    )
    observations = models.TextField(blank=True, verbose_name='Observations')

    # Validation
    valide_par = models.ForeignKey(
        Utilisateur, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='rapprochements_valides', verbose_name='Validé par'
    )
    date_validation = models.DateTimeField(null=True, blank=True, verbose_name='Date validation')

    # Audit
    cree_par = models.ForeignKey(
        Utilisateur, on_delete=models.SET_NULL, null=True,
        related_name='rapprochements_crees', verbose_name='Créé par'
    )
    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Rapprochement bancaire'
        verbose_name_plural = 'Rapprochements bancaires'
        ordering = ['-date_fin']

    def __str__(self):
        return f"Rapprochement {self.compte.nom} - {self.date_debut} au {self.date_fin}"

    def calculer_ecart(self):
        if self.solde_releve is not None and self.solde_comptable is not None:
            self.ecart = self.solde_releve - self.solde_comptable
            return self.ecart
        return None


class LigneRapprochement(models.Model):
    """Lignes de rapprochement bancaire"""
    STATUT_CHOICES = [
        ('non_rapproche', 'Non rapproché'),
        ('rapproche', 'Rapproché'),
        ('ecart', 'Écart à justifier'),
    ]

    rapprochement = models.ForeignKey(
        RapprochementBancaire, on_delete=models.CASCADE, related_name='lignes',
        verbose_name='Rapprochement'
    )

    # Données du relevé
    date_releve = models.DateField(verbose_name='Date relevé')
    libelle_releve = models.CharField(max_length=200, verbose_name='Libellé relevé')
    montant_releve = models.DecimalField(
        max_digits=15, decimal_places=0, verbose_name='Montant relevé'
    )

    # Correspondance comptable
    operation = models.ForeignKey(
        OperationTresorerie, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='lignes_rapprochement', verbose_name='Opération correspondante'
    )

    # Statut
    statut = models.CharField(
        max_length=20, choices=STATUT_CHOICES, default='non_rapproche', verbose_name='Statut'
    )
    observations = models.TextField(blank=True, verbose_name='Observations')

    date_creation = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Ligne de rapprochement'
        verbose_name_plural = 'Lignes de rapprochement'
        ordering = ['date_releve']

    def __str__(self):
        return f"{self.date_releve} - {self.libelle_releve} ({self.montant_releve:,.0f} FCFA)"


class AuditTresorerie(models.Model):
    """Journal d'audit pour toutes les opérations de trésorerie"""
    ACTION_CHOICES = [
        ('creation', 'Création'),
        ('modification', 'Modification'),
        ('validation', 'Validation'),
        ('approbation', 'Approbation'),
        ('rejet', 'Rejet'),
        ('annulation', 'Annulation'),
        ('ouverture_caisse', 'Ouverture de caisse'),
        ('fermeture_caisse', 'Fermeture de caisse'),
    ]

    action = models.CharField(max_length=20, choices=ACTION_CHOICES, verbose_name='Action')

    # Entité concernée
    entite_type = models.CharField(max_length=50, verbose_name='Type d\'entité')
    entite_id = models.PositiveIntegerField(verbose_name='ID de l\'entité')
    entite_reference = models.CharField(max_length=100, blank=True, verbose_name='Référence')

    # Détails
    description = models.TextField(verbose_name='Description')
    donnees_avant = models.JSONField(null=True, blank=True, verbose_name='Données avant')
    donnees_apres = models.JSONField(null=True, blank=True, verbose_name='Données après')

    # Audit
    utilisateur = models.ForeignKey(
        Utilisateur, on_delete=models.SET_NULL, null=True,
        related_name='audits_tresorerie', verbose_name='Utilisateur'
    )
    adresse_ip = models.GenericIPAddressField(null=True, blank=True, verbose_name='Adresse IP')
    date_creation = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Audit trésorerie'
        verbose_name_plural = 'Audits trésorerie'
        ordering = ['-date_creation']

    def __str__(self):
        return f"{self.get_action_display()} - {self.entite_type} {self.entite_reference}"
