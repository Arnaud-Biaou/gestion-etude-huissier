from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
import json


class Utilisateur(AbstractUser):
    """Modele utilisateur personnalise"""
    ROLE_CHOICES = [
        ('admin', 'Administrateur'),
        ('huissier', 'Huissier'),
        ('clerc_principal', 'Clerc Principal'),
        ('clerc', 'Clerc'),
        ('secretaire', 'Secretaire'),
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
    """Collaborateurs de l'etude"""
    ROLE_CHOICES = [
        ('huissier', 'Huissier'),
        ('clerc_principal', 'Clerc Principal'),
        ('clerc', 'Clerc'),
        ('secretaire', 'Secretaire'),
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
    """Parties (demandeur ou defendeur) d'un dossier"""
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
    nationalite = models.CharField(max_length=50, blank=True, default='Beninoise')
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
    """Dossier de l'etude"""
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
        ('archive', 'Archive'),
        ('cloture', 'Cloture'),
    ]
    PHASE_CHOICES = [
        ('amiable', 'Phase amiable'),
        ('force', 'Phase forcée (exécution)'),
    ]

    reference = models.CharField(max_length=20, unique=True)
    is_contentieux = models.BooleanField(default=False, verbose_name='Contentieux')
    type_dossier = models.CharField(max_length=20, choices=TYPE_DOSSIER_CHOICES, blank=True)
    description = models.TextField(blank=True)
    montant_creance = models.DecimalField(max_digits=15, decimal_places=0, null=True, blank=True)
    date_creance = models.DateField(null=True, blank=True)
    date_ouverture = models.DateField(default=timezone.now)
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default='actif')

    # Lien avec le créancier
    creancier = models.ForeignKey(
        'Creancier', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='dossiers', verbose_name='Créancier'
    )

    # Phase du recouvrement (amiable ou forcé)
    phase = models.CharField(
        max_length=10, choices=PHASE_CHOICES, default='amiable',
        verbose_name='Phase de recouvrement'
    )
    date_passage_force = models.DateTimeField(
        null=True, blank=True,
        verbose_name='Date passage en phase forcée'
    )

    # Montants détaillés pour le suivi
    montant_principal = models.DecimalField(
        max_digits=15, decimal_places=0, null=True, blank=True,
        verbose_name='Montant principal'
    )
    montant_interets = models.DecimalField(
        max_digits=15, decimal_places=0, default=0,
        verbose_name='Intérêts'
    )
    montant_frais = models.DecimalField(
        max_digits=15, decimal_places=0, default=0,
        verbose_name='Frais de procédure'
    )
    montant_emoluments = models.DecimalField(
        max_digits=15, decimal_places=0, default=0,
        verbose_name='Émoluments'
    )
    montant_depens = models.DecimalField(
        max_digits=15, decimal_places=0, default=0,
        verbose_name='Dépens'
    )
    montant_accessoires = models.DecimalField(
        max_digits=15, decimal_places=0, default=0,
        verbose_name='Accessoires'
    )

    # Titre exécutoire (pour phase forcée)
    titre_executoire_type = models.CharField(
        max_length=100, blank=True,
        verbose_name='Type de titre exécutoire'
    )
    titre_executoire_reference = models.CharField(
        max_length=100, blank=True,
        verbose_name='Référence du titre'
    )
    titre_executoire_date = models.DateField(
        null=True, blank=True,
        verbose_name='Date du titre'
    )
    titre_executoire_juridiction = models.CharField(
        max_length=200, blank=True,
        verbose_name='Juridiction'
    )

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

    def get_montant_total_du(self):
        """Calcule le montant total dû sur le dossier"""
        total = (
            (self.montant_principal or self.montant_creance or 0) +
            (self.montant_interets or 0) +
            (self.montant_frais or 0) +
            (self.montant_emoluments or 0) +
            (self.montant_depens or 0) +
            (self.montant_accessoires or 0)
        )
        return total

    def get_total_encaisse(self):
        """Retourne le total encaissé sur ce dossier"""
        from django.db.models import Sum
        return self.encaissements.filter(statut='valide').aggregate(
            total=Sum('montant')
        )['total'] or 0

    def get_solde_restant(self):
        """Retourne le solde restant dû"""
        return self.get_montant_total_du() - self.get_total_encaisse()

    def get_taux_recouvrement(self):
        """Retourne le taux de recouvrement"""
        total_du = self.get_montant_total_du()
        if total_du > 0:
            return (self.get_total_encaisse() / total_du) * 100
        return 0

    def basculer_vers_force(self, utilisateur, motif, titre_info=None, frais_supplementaires=None):
        """Bascule le dossier de la phase amiable vers la phase forcée"""
        from django.db.models import Sum

        if self.phase == 'force':
            raise ValueError("Ce dossier est déjà en phase forcée")

        # Calculer l'état actuel de la créance
        total_encaisse = self.get_total_encaisse()
        principal_restant = (self.montant_principal or self.montant_creance or 0)
        interets_restant = self.montant_interets or 0
        frais_restant = self.montant_frais or 0

        # Imputer les encaissements déjà effectués
        reste_a_imputer = total_encaisse
        if reste_a_imputer > 0:
            # Imputer d'abord sur les frais
            if frais_restant > 0:
                imputation_frais = min(reste_a_imputer, frais_restant)
                frais_restant -= imputation_frais
                reste_a_imputer -= imputation_frais
            # Puis sur les intérêts
            if reste_a_imputer > 0 and interets_restant > 0:
                imputation_interets = min(reste_a_imputer, interets_restant)
                interets_restant -= imputation_interets
                reste_a_imputer -= imputation_interets
            # Enfin sur le principal
            if reste_a_imputer > 0:
                principal_restant -= reste_a_imputer

        total_reste_du = principal_restant + interets_restant + frais_restant

        # Créer l'enregistrement de basculement
        basculement = BasculementAmiableForce(
            dossier=self,
            motif=motif,
            effectue_par=utilisateur,
            montant_principal_restant=principal_restant,
            montant_interets_restant=interets_restant,
            montant_frais_restant=frais_restant,
            total_reste_du=total_reste_du,
            donnees_phase_amiable={
                'montant_principal_initial': float(self.montant_principal or self.montant_creance or 0),
                'montant_interets_initial': float(self.montant_interets or 0),
                'montant_frais_initial': float(self.montant_frais or 0),
                'total_encaisse': float(total_encaisse),
                'nb_encaissements': self.encaissements.filter(statut='valide').count(),
                'date_basculement': timezone.now().isoformat()
            }
        )

        # Titre exécutoire
        if titre_info:
            basculement.type_titre = titre_info.get('type', '')
            basculement.reference_titre = titre_info.get('reference', '')
            basculement.juridiction = titre_info.get('juridiction', '')
            basculement.date_titre = titre_info.get('date')

            self.titre_executoire_type = titre_info.get('type', '')
            self.titre_executoire_reference = titre_info.get('reference', '')
            self.titre_executoire_juridiction = titre_info.get('juridiction', '')
            self.titre_executoire_date = titre_info.get('date')

        # Frais supplémentaires
        if frais_supplementaires:
            basculement.depens = frais_supplementaires.get('depens', 0)
            basculement.frais_justice = frais_supplementaires.get('frais_justice', 0)

            # Calculer les émoluments OHADA
            emoluments = basculement.calculer_emoluments_ohada(total_reste_du)
            basculement.emoluments_ohada = emoluments

            # Nouveau total
            basculement.nouveau_total = (
                total_reste_du +
                basculement.depens +
                basculement.frais_justice +
                basculement.emoluments_ohada
            )

            # Mettre à jour le dossier
            self.montant_principal = principal_restant
            self.montant_interets = interets_restant
            self.montant_frais = frais_restant
            self.montant_depens = basculement.depens + basculement.frais_justice
            self.montant_emoluments = basculement.emoluments_ohada
        else:
            basculement.nouveau_total = total_reste_du
            self.montant_principal = principal_restant
            self.montant_interets = interets_restant
            self.montant_frais = frais_restant

        basculement.save()

        # Mettre à jour le dossier
        self.phase = 'force'
        self.date_passage_force = timezone.now()
        self.save()

        return basculement

    @classmethod
    def generer_reference(cls):
        now = timezone.now()
        prefix = 175  # Numero de la loi
        mois = str(now.month).zfill(2)
        annee = str(now.year)[-2:]
        suffix = "MAB"  # Initiales de l'huissier

        # Trouver le prochain numero
        derniers = cls.objects.filter(
            reference__startswith=f"{prefix}_{mois}{annee}"
        ).count()

        return f"{prefix + derniers}_{mois}{annee}_{suffix}"


class Facture(models.Model):
    """Factures de l'etude"""
    STATUT_CHOICES = [
        ('brouillon', 'Brouillon'),
        ('attente', 'En attente'),
        ('payee', 'Payee'),
        ('annulee', 'Annulee'),
    ]

    numero = models.CharField(max_length=20, unique=True)
    dossier = models.ForeignKey(
        Dossier, on_delete=models.SET_NULL, null=True, blank=True, related_name='factures'
    )
    client = models.CharField(max_length=200)
    ifu = models.CharField(max_length=20, blank=True, verbose_name='IFU Client')
    montant_ht = models.DecimalField(max_digits=15, decimal_places=0)
    taux_tva = models.DecimalField(max_digits=5, decimal_places=2, default=18.00)
    montant_tva = models.DecimalField(max_digits=15, decimal_places=0)
    montant_ttc = models.DecimalField(max_digits=15, decimal_places=0)
    date_emission = models.DateField(default=timezone.now)
    date_echeance = models.DateField(null=True, blank=True)
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default='attente')
    observations = models.TextField(blank=True)

    # MECeF
    mecef_qr = models.TextField(blank=True, verbose_name='QR Code MECeF')
    mecef_numero = models.CharField(max_length=50, blank=True, verbose_name='Numero MECeF')
    nim = models.CharField(max_length=20, blank=True, verbose_name='NIM')
    date_mecef = models.DateTimeField(null=True, blank=True, verbose_name='Date normalisation MECeF')

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


class LigneFacture(models.Model):
    """Lignes de facture"""
    facture = models.ForeignKey(Facture, on_delete=models.CASCADE, related_name='lignes')
    description = models.CharField(max_length=500)
    quantite = models.IntegerField(default=1)
    prix_unitaire = models.DecimalField(max_digits=15, decimal_places=0)

    class Meta:
        verbose_name = 'Ligne de facture'
        verbose_name_plural = 'Lignes de facture'

    def __str__(self):
        return f"{self.description} x {self.quantite}"

    @property
    def total(self):
        return self.quantite * self.prix_unitaire


class ActeProcedure(models.Model):
    """Actes de procedure du catalogue"""
    code = models.CharField(max_length=20, unique=True)
    libelle = models.CharField(max_length=200)
    tarif = models.DecimalField(max_digits=10, decimal_places=0)
    actif = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'Acte de procedure'
        verbose_name_plural = 'Actes de procedure'
        ordering = ['libelle']

    def __str__(self):
        return f"{self.libelle} ({self.tarif:,.0f} FCFA)"


class HistoriqueCalcul(models.Model):
    """Historique des calculs de recouvrement"""
    MODE_CHOICES = [
        ('complet', 'Calcul complet'),
        ('emoluments', 'Emoluments seuls'),
    ]

    nom = models.CharField(max_length=200)
    mode = models.CharField(max_length=20, choices=MODE_CHOICES)
    donnees = models.JSONField()  # Stocke toutes les donnees du calcul
    resultats = models.JSONField()  # Stocke les resultats
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
    """Taux legaux UEMOA par annee"""
    annee = models.IntegerField(unique=True)
    taux = models.DecimalField(max_digits=6, decimal_places=4)
    source = models.CharField(max_length=100, default='BCEAO')

    class Meta:
        verbose_name = 'Taux legal'
        verbose_name_plural = 'Taux legaux'
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


# =============================================================================
# MODELES POUR LA GESTION DES CREANCIERS
# =============================================================================

class Creancier(models.Model):
    """Créanciers (banques, microfinances, entreprises, particuliers)"""
    TYPE_CREANCIER_CHOICES = [
        ('banque', 'Banque'),
        ('microfinance', 'Institution de Microfinance'),
        ('entreprise', 'Entreprise'),
        ('particulier', 'Particulier'),
        ('etat', 'État/Administration'),
        ('autre', 'Autre'),
    ]

    # Informations générales
    code = models.CharField(max_length=20, unique=True, verbose_name='Code créancier')
    nom = models.CharField(max_length=200, verbose_name='Nom/Dénomination')
    type_creancier = models.CharField(max_length=20, choices=TYPE_CREANCIER_CHOICES, default='entreprise')

    # Coordonnées
    adresse = models.TextField(blank=True, verbose_name='Adresse')
    telephone = models.CharField(max_length=50, blank=True)
    email = models.EmailField(blank=True)
    site_web = models.URLField(blank=True)

    # Informations fiscales et légales
    ifu = models.CharField(max_length=20, blank=True, verbose_name='IFU')
    rccm = models.CharField(max_length=50, blank=True, verbose_name='RCCM')

    # Contact référent
    contact_nom = models.CharField(max_length=100, blank=True, verbose_name='Nom du contact')
    contact_fonction = models.CharField(max_length=100, blank=True, verbose_name='Fonction')
    contact_telephone = models.CharField(max_length=50, blank=True)
    contact_email = models.EmailField(blank=True)

    # Coordonnées bancaires pour les reversements
    banque_nom = models.CharField(max_length=100, blank=True, verbose_name='Banque')
    banque_iban = models.CharField(max_length=50, blank=True, verbose_name='IBAN')
    banque_rib = models.CharField(max_length=50, blank=True, verbose_name='RIB')

    # Paramètres
    taux_commission = models.DecimalField(
        max_digits=5, decimal_places=2, default=10.00,
        verbose_name='Taux de commission (%)'
    )
    delai_reversement = models.IntegerField(
        default=15, verbose_name='Délai de reversement (jours)'
    )

    actif = models.BooleanField(default=True)
    notes = models.TextField(blank=True)

    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Créancier'
        verbose_name_plural = 'Créanciers'
        ordering = ['nom']

    def __str__(self):
        return f"{self.code} - {self.nom}"

    @classmethod
    def generer_code(cls):
        """Génère un code créancier unique"""
        count = cls.objects.count() + 1
        return f"CR-{str(count).zfill(4)}"

    def get_total_creances(self):
        """Retourne le total des créances confiées"""
        from django.db.models import Sum
        return self.dossiers.aggregate(
            total=Sum('montant_creance')
        )['total'] or 0

    def get_total_encaisse(self):
        """Retourne le total encaissé"""
        from django.db.models import Sum
        return Encaissement.objects.filter(
            dossier__creancier=self,
            statut='valide'
        ).aggregate(total=Sum('montant'))['total'] or 0

    def get_total_reverse(self):
        """Retourne le total reversé"""
        from django.db.models import Sum
        return Reversement.objects.filter(
            creancier=self,
            statut='effectue'
        ).aggregate(total=Sum('montant'))['total'] or 0


class PortefeuilleCreancier(models.Model):
    """Gestion du portefeuille de dossiers d'un créancier"""
    creancier = models.OneToOneField(
        Creancier, on_delete=models.CASCADE, related_name='portefeuille'
    )
    date_debut_relation = models.DateField(verbose_name='Date début de relation')

    # Contact référent au sein de l'étude
    gestionnaire = models.ForeignKey(
        Collaborateur, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='portefeuilles_geres', verbose_name='Gestionnaire référent'
    )

    # Paramètres spécifiques
    parametres = models.JSONField(default=dict, blank=True, verbose_name='Paramètres personnalisés')

    # Statistiques (mises à jour périodiquement)
    nb_dossiers_actifs = models.IntegerField(default=0)
    montant_total_creances = models.DecimalField(max_digits=18, decimal_places=0, default=0)
    montant_total_encaisse = models.DecimalField(max_digits=18, decimal_places=0, default=0)
    montant_total_reverse = models.DecimalField(max_digits=18, decimal_places=0, default=0)
    taux_recouvrement = models.DecimalField(max_digits=5, decimal_places=2, default=0)

    derniere_maj_stats = models.DateTimeField(null=True, blank=True)

    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Portefeuille créancier'
        verbose_name_plural = 'Portefeuilles créanciers'

    def __str__(self):
        return f"Portefeuille {self.creancier.nom}"

    def actualiser_statistiques(self):
        """Met à jour les statistiques du portefeuille"""
        from django.db.models import Sum, Count

        # Dossiers actifs
        dossiers_actifs = self.creancier.dossiers.exclude(statut='cloture')
        self.nb_dossiers_actifs = dossiers_actifs.count()

        # Montants
        self.montant_total_creances = self.creancier.dossiers.aggregate(
            total=Sum('montant_creance')
        )['total'] or 0

        self.montant_total_encaisse = Encaissement.objects.filter(
            dossier__creancier=self.creancier,
            statut='valide'
        ).aggregate(total=Sum('montant'))['total'] or 0

        self.montant_total_reverse = Reversement.objects.filter(
            creancier=self.creancier,
            statut='effectue'
        ).aggregate(total=Sum('montant'))['total'] or 0

        # Taux de recouvrement
        if self.montant_total_creances > 0:
            self.taux_recouvrement = (self.montant_total_encaisse / self.montant_total_creances) * 100

        self.derniere_maj_stats = timezone.now()
        self.save()


# =============================================================================
# MODELES POUR L'HISTORIQUE DES ENCAISSEMENTS
# =============================================================================

class Encaissement(models.Model):
    """Encaissements reçus sur les dossiers"""
    STATUT_CHOICES = [
        ('en_attente', 'En attente de validation'),
        ('valide', 'Validé'),
        ('annule', 'Annulé'),
        ('rembourse', 'Remboursé'),
    ]
    MODE_PAIEMENT_CHOICES = [
        ('especes', 'Espèces'),
        ('cheque', 'Chèque'),
        ('virement', 'Virement bancaire'),
        ('mobile_money', 'Mobile Money'),
        ('carte', 'Carte bancaire'),
        ('compensation', 'Compensation'),
        ('autre', 'Autre'),
    ]

    # Référence unique
    reference = models.CharField(max_length=30, unique=True, verbose_name='Référence')

    # Lien avec le dossier
    dossier = models.ForeignKey(
        'Dossier', on_delete=models.PROTECT, related_name='encaissements'
    )

    # Informations de l'encaissement
    montant = models.DecimalField(max_digits=15, decimal_places=0, verbose_name='Montant')
    date_encaissement = models.DateField(default=timezone.now, verbose_name='Date d\'encaissement')
    date_valeur = models.DateField(null=True, blank=True, verbose_name='Date de valeur')

    mode_paiement = models.CharField(
        max_length=20, choices=MODE_PAIEMENT_CHOICES, default='especes'
    )

    # Informations sur le payeur
    payeur_nom = models.CharField(max_length=200, verbose_name='Nom du payeur')
    payeur_telephone = models.CharField(max_length=50, blank=True)
    payeur_qualite = models.CharField(
        max_length=100, blank=True,
        verbose_name='Qualité du payeur',
        help_text='Ex: Débiteur, Mandataire, Caution, etc.'
    )

    # Informations complémentaires selon le mode de paiement
    reference_paiement = models.CharField(
        max_length=100, blank=True,
        verbose_name='Référence du paiement',
        help_text='N° de chèque, référence virement, etc.'
    )
    banque_emettrice = models.CharField(max_length=100, blank=True)

    # Statut et validation
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default='en_attente')
    date_validation = models.DateTimeField(null=True, blank=True)
    valide_par = models.ForeignKey(
        Utilisateur, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='encaissements_valides'
    )

    # Cumuls (calculés automatiquement)
    cumul_encaisse_avant = models.DecimalField(
        max_digits=15, decimal_places=0, default=0,
        verbose_name='Cumul encaissé avant cet encaissement'
    )
    cumul_encaisse_apres = models.DecimalField(
        max_digits=15, decimal_places=0, default=0,
        verbose_name='Cumul encaissé après cet encaissement'
    )
    solde_restant = models.DecimalField(
        max_digits=15, decimal_places=0, default=0,
        verbose_name='Solde restant dû'
    )

    # Reversement
    montant_a_reverser = models.DecimalField(
        max_digits=15, decimal_places=0, default=0,
        verbose_name='Montant à reverser au créancier'
    )
    reversement_statut = models.CharField(
        max_length=20, default='en_attente',
        choices=[('en_attente', 'En attente'), ('reverse', 'Reversé')],
        verbose_name='Statut reversement'
    )

    # Traçabilité
    observations = models.TextField(blank=True)
    piece_justificative = models.FileField(
        upload_to='encaissements/', blank=True, null=True,
        verbose_name='Pièce justificative'
    )

    cree_par = models.ForeignKey(
        Utilisateur, on_delete=models.SET_NULL, null=True,
        related_name='encaissements_crees'
    )
    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Encaissement'
        verbose_name_plural = 'Encaissements'
        ordering = ['-date_encaissement', '-date_creation']

    def __str__(self):
        return f"{self.reference} - {self.montant:,.0f} FCFA"

    @classmethod
    def generer_reference(cls):
        """Génère une référence unique pour l'encaissement"""
        now = timezone.now()
        count = cls.objects.filter(date_creation__year=now.year).count() + 1
        return f"ENC-{now.year}-{str(count).zfill(5)}"

    def save(self, *args, **kwargs):
        # Générer la référence si nouvelle
        if not self.reference:
            self.reference = self.generer_reference()

        # Calculer les cumuls si validé
        if self.statut == 'valide':
            self.calculer_cumuls()
            self.calculer_montant_a_reverser()

        super().save(*args, **kwargs)

    def calculer_cumuls(self):
        """Calcule les cumuls progressifs"""
        from django.db.models import Sum

        # Cumul avant cet encaissement
        encaissements_anterieurs = Encaissement.objects.filter(
            dossier=self.dossier,
            statut='valide',
            date_encaissement__lt=self.date_encaissement
        ).exclude(pk=self.pk)

        self.cumul_encaisse_avant = encaissements_anterieurs.aggregate(
            total=Sum('montant')
        )['total'] or 0

        # Cumul après
        self.cumul_encaisse_apres = self.cumul_encaisse_avant + self.montant

        # Solde restant (basé sur le montant total dû du dossier)
        montant_total_du = self.dossier.get_montant_total_du()
        self.solde_restant = montant_total_du - self.cumul_encaisse_apres

    def calculer_montant_a_reverser(self):
        """Calcule le montant à reverser au créancier"""
        if hasattr(self.dossier, 'creancier') and self.dossier.creancier:
            # Appliquer le taux de commission du créancier
            taux_commission = self.dossier.creancier.taux_commission / 100
            commission = self.montant * taux_commission
            self.montant_a_reverser = self.montant - commission
        else:
            self.montant_a_reverser = self.montant

    def valider(self, utilisateur):
        """Valide l'encaissement"""
        self.statut = 'valide'
        self.date_validation = timezone.now()
        self.valide_par = utilisateur
        self.save()

    def annuler(self, motif=''):
        """Annule l'encaissement"""
        self.statut = 'annule'
        if motif:
            self.observations = f"{self.observations}\nAnnulation: {motif}"
        self.save()


class ImputationEncaissement(models.Model):
    """Détail de l'imputation d'un encaissement sur les différentes composantes de la créance"""
    TYPE_IMPUTATION_CHOICES = [
        ('principal', 'Principal'),
        ('interets', 'Intérêts'),
        ('interets_retard', 'Intérêts de retard'),
        ('frais', 'Frais de procédure'),
        ('emoluments', 'Émoluments'),
        ('debours', 'Débours'),
        ('depens', 'Dépens'),
        ('accessoires', 'Accessoires'),
        ('autres', 'Autres'),
    ]

    encaissement = models.ForeignKey(
        Encaissement, on_delete=models.CASCADE, related_name='imputations'
    )

    type_imputation = models.CharField(
        max_length=20, choices=TYPE_IMPUTATION_CHOICES
    )
    montant = models.DecimalField(max_digits=15, decimal_places=0)

    # Soldes avant/après pour ce type
    solde_avant = models.DecimalField(max_digits=15, decimal_places=0, default=0)
    solde_apres = models.DecimalField(max_digits=15, decimal_places=0, default=0)

    observations = models.CharField(max_length=500, blank=True)

    date_creation = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Imputation d\'encaissement'
        verbose_name_plural = 'Imputations d\'encaissements'
        ordering = ['encaissement', 'type_imputation']

    def __str__(self):
        return f"{self.encaissement.reference} - {self.get_type_imputation_display()}: {self.montant:,.0f} FCFA"


# =============================================================================
# MODELES POUR LE SUIVI DES REVERSEMENTS
# =============================================================================

class Reversement(models.Model):
    """Reversements effectués aux créanciers"""
    STATUT_CHOICES = [
        ('en_attente', 'En attente de reversement'),
        ('en_cours', 'En cours'),
        ('effectue', 'Effectué'),
        ('annule', 'Annulé'),
    ]
    MODE_REVERSEMENT_CHOICES = [
        ('virement', 'Virement bancaire'),
        ('cheque', 'Chèque'),
        ('especes', 'Espèces'),
        ('autre', 'Autre'),
    ]

    # Référence unique
    reference = models.CharField(max_length=30, unique=True, verbose_name='Référence')

    # Créancier bénéficiaire
    creancier = models.ForeignKey(
        Creancier, on_delete=models.PROTECT, related_name='reversements'
    )

    # Montant et dates
    montant = models.DecimalField(max_digits=15, decimal_places=0)
    date_reversement = models.DateField(null=True, blank=True, verbose_name='Date de reversement')

    # Mode de reversement
    mode_reversement = models.CharField(
        max_length=20, choices=MODE_REVERSEMENT_CHOICES, default='virement'
    )

    # Références du paiement
    reference_virement = models.CharField(max_length=100, blank=True, verbose_name='Référence virement')
    numero_cheque = models.CharField(max_length=50, blank=True, verbose_name='Numéro de chèque')
    banque = models.CharField(max_length=100, blank=True, verbose_name='Banque émettrice')

    # Encaissements concernés
    encaissements = models.ManyToManyField(
        Encaissement, related_name='reversements', blank=True
    )

    # Statut
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default='en_attente')

    # Preuve de reversement
    preuve_reversement = models.FileField(
        upload_to='reversements/', blank=True, null=True,
        verbose_name='Preuve de reversement'
    )

    # Détails
    observations = models.TextField(blank=True)

    # Traçabilité
    cree_par = models.ForeignKey(
        Utilisateur, on_delete=models.SET_NULL, null=True,
        related_name='reversements_crees'
    )
    effectue_par = models.ForeignKey(
        Utilisateur, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='reversements_effectues'
    )
    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Reversement'
        verbose_name_plural = 'Reversements'
        ordering = ['-date_creation']

    def __str__(self):
        return f"{self.reference} - {self.montant:,.0f} FCFA → {self.creancier.nom}"

    @classmethod
    def generer_reference(cls):
        """Génère une référence unique pour le reversement"""
        now = timezone.now()
        count = cls.objects.filter(date_creation__year=now.year).count() + 1
        return f"REV-{now.year}-{str(count).zfill(4)}"

    def save(self, *args, **kwargs):
        if not self.reference:
            self.reference = self.generer_reference()
        super().save(*args, **kwargs)

    def effectuer(self, utilisateur):
        """Marque le reversement comme effectué"""
        self.statut = 'effectue'
        self.date_reversement = timezone.now().date()
        self.effectue_par = utilisateur
        self.save()

        # Mettre à jour le statut des encaissements liés
        for encaissement in self.encaissements.all():
            encaissement.reversement_statut = 'reverse'
            encaissement.save()

    def annuler(self, motif=''):
        """Annule le reversement"""
        self.statut = 'annule'
        if motif:
            self.observations = f"{self.observations}\nAnnulation: {motif}"
        self.save()

        # Remettre les encaissements en attente
        for encaissement in self.encaissements.all():
            encaissement.reversement_statut = 'en_attente'
            encaissement.save()


# =============================================================================
# MODELES POUR LE PASSAGE AMIABLE → FORCÉ
# =============================================================================

class BasculementAmiableForce(models.Model):
    """Historique des basculements de la phase amiable vers la phase forcée"""
    MOTIF_CHOICES = [
        ('titre_executoire', 'Obtention d\'un titre exécutoire'),
        ('echec_amiable', 'Échec de la phase amiable'),
        ('decision_creancier', 'Décision du créancier'),
        ('autre', 'Autre'),
    ]

    dossier = models.ForeignKey(
        'Dossier', on_delete=models.CASCADE, related_name='basculements'
    )

    # Date et motif du basculement
    date_basculement = models.DateTimeField(default=timezone.now)
    motif = models.CharField(max_length=30, choices=MOTIF_CHOICES)
    motif_detail = models.TextField(blank=True, verbose_name='Détail du motif')

    # Titre exécutoire (si applicable)
    type_titre = models.CharField(max_length=100, blank=True, verbose_name='Type de titre')
    reference_titre = models.CharField(max_length=100, blank=True, verbose_name='Référence du titre')
    juridiction = models.CharField(max_length=200, blank=True, verbose_name='Juridiction')
    date_titre = models.DateField(null=True, blank=True, verbose_name='Date du titre')

    # État de la créance au moment du basculement
    montant_principal_restant = models.DecimalField(
        max_digits=15, decimal_places=0, default=0,
        verbose_name='Principal restant'
    )
    montant_interets_restant = models.DecimalField(
        max_digits=15, decimal_places=0, default=0,
        verbose_name='Intérêts restants'
    )
    montant_frais_restant = models.DecimalField(
        max_digits=15, decimal_places=0, default=0,
        verbose_name='Frais restants'
    )
    total_reste_du = models.DecimalField(
        max_digits=15, decimal_places=0, default=0,
        verbose_name='Total restant dû'
    )

    # Nouveaux frais ajoutés lors du basculement
    depens = models.DecimalField(
        max_digits=15, decimal_places=0, default=0,
        verbose_name='Dépens'
    )
    frais_justice = models.DecimalField(
        max_digits=15, decimal_places=0, default=0,
        verbose_name='Frais de justice'
    )
    emoluments_ohada = models.DecimalField(
        max_digits=15, decimal_places=0, default=0,
        verbose_name='Émoluments OHADA'
    )
    nouveau_total = models.DecimalField(
        max_digits=15, decimal_places=0, default=0,
        verbose_name='Nouveau total après basculement'
    )

    # Données complètes sauvegardées (JSON)
    donnees_phase_amiable = models.JSONField(
        default=dict, blank=True,
        verbose_name='Données de la phase amiable'
    )

    # Traçabilité
    effectue_par = models.ForeignKey(
        Utilisateur, on_delete=models.SET_NULL, null=True,
        related_name='basculements_effectues'
    )
    date_creation = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Basculement amiable → forcé'
        verbose_name_plural = 'Basculements amiable → forcé'
        ordering = ['-date_basculement']

    def __str__(self):
        return f"Basculement {self.dossier.reference} - {self.date_basculement.strftime('%d/%m/%Y')}"

    def calculer_emoluments_ohada(self, montant):
        """Calcule les émoluments selon le barème OHADA"""
        # Barème des émoluments OHADA (simplifié)
        if montant <= 500000:
            return montant * 0.10
        elif montant <= 1000000:
            return 50000 + (montant - 500000) * 0.08
        elif montant <= 5000000:
            return 90000 + (montant - 1000000) * 0.05
        elif montant <= 10000000:
            return 290000 + (montant - 5000000) * 0.03
        else:
            return 440000 + (montant - 10000000) * 0.01


# =============================================================================
# MODELES POUR LE POINT CLIENT
# =============================================================================

class PointGlobalCreancier(models.Model):
    """Points globaux générés pour les créanciers"""

    creancier = models.ForeignKey(
        Creancier, on_delete=models.CASCADE, related_name='points_globaux'
    )

    # Période couverte
    date_generation = models.DateTimeField(default=timezone.now)
    periode_debut = models.DateField(verbose_name='Début de période')
    periode_fin = models.DateField(verbose_name='Fin de période')

    # Filtres appliqués
    filtres = models.JSONField(default=dict, blank=True, verbose_name='Filtres appliqués')

    # Statistiques du point
    nb_dossiers_total = models.IntegerField(default=0)
    nb_dossiers_actifs = models.IntegerField(default=0)
    nb_dossiers_clotures = models.IntegerField(default=0)

    montant_total_creances = models.DecimalField(max_digits=18, decimal_places=0, default=0)
    montant_total_encaisse = models.DecimalField(max_digits=18, decimal_places=0, default=0)
    montant_total_reverse = models.DecimalField(max_digits=18, decimal_places=0, default=0)
    montant_reste_a_encaisser = models.DecimalField(max_digits=18, decimal_places=0, default=0)
    montant_reste_a_reverser = models.DecimalField(max_digits=18, decimal_places=0, default=0)

    taux_recouvrement = models.DecimalField(max_digits=5, decimal_places=2, default=0)

    # Données détaillées (JSON)
    donnees_detaillees = models.JSONField(
        default=dict, blank=True,
        verbose_name='Données détaillées du point'
    )

    # Document PDF généré
    document_pdf = models.FileField(
        upload_to='points_creanciers/', blank=True, null=True,
        verbose_name='Document PDF'
    )

    # Traçabilité
    genere_par = models.ForeignKey(
        Utilisateur, on_delete=models.SET_NULL, null=True,
        related_name='points_generes'
    )
    date_creation = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Point global créancier'
        verbose_name_plural = 'Points globaux créanciers'
        ordering = ['-date_generation']

    def __str__(self):
        return f"Point {self.creancier.nom} - {self.date_generation.strftime('%d/%m/%Y')}"

    def generer_donnees(self):
        """Génère les données détaillées du point"""
        from django.db.models import Sum, Count, Q

        # Filtrer les dossiers du créancier
        dossiers = self.creancier.dossiers.all()

        # Appliquer les filtres si présents
        if self.filtres:
            if 'statut' in self.filtres:
                dossiers = dossiers.filter(statut=self.filtres['statut'])
            if 'montant_min' in self.filtres:
                dossiers = dossiers.filter(montant_creance__gte=self.filtres['montant_min'])
            if 'montant_max' in self.filtres:
                dossiers = dossiers.filter(montant_creance__lte=self.filtres['montant_max'])
            if 'gestionnaire' in self.filtres:
                dossiers = dossiers.filter(affecte_a_id=self.filtres['gestionnaire'])

        # Statistiques
        self.nb_dossiers_total = dossiers.count()
        self.nb_dossiers_actifs = dossiers.filter(statut__in=['actif', 'urgent']).count()
        self.nb_dossiers_clotures = dossiers.filter(statut='cloture').count()

        self.montant_total_creances = dossiers.aggregate(
            total=Sum('montant_creance')
        )['total'] or 0

        # Encaissements
        encaissements = Encaissement.objects.filter(
            dossier__in=dossiers,
            statut='valide',
            date_encaissement__gte=self.periode_debut,
            date_encaissement__lte=self.periode_fin
        )

        self.montant_total_encaisse = encaissements.aggregate(
            total=Sum('montant')
        )['total'] or 0

        # Reversements
        reversements = Reversement.objects.filter(
            creancier=self.creancier,
            statut='effectue',
            date_reversement__gte=self.periode_debut,
            date_reversement__lte=self.periode_fin
        )

        self.montant_total_reverse = reversements.aggregate(
            total=Sum('montant')
        )['total'] or 0

        # Calculs
        self.montant_reste_a_encaisser = self.montant_total_creances - self.montant_total_encaisse

        encaisse_non_reverse = Encaissement.objects.filter(
            dossier__in=dossiers,
            statut='valide',
            reversement_statut='en_attente'
        ).aggregate(total=Sum('montant_a_reverser'))['total'] or 0
        self.montant_reste_a_reverser = encaisse_non_reverse

        # Taux de recouvrement
        if self.montant_total_creances > 0:
            self.taux_recouvrement = (self.montant_total_encaisse / self.montant_total_creances) * 100

        # Données détaillées par dossier
        details = []
        for dossier in dossiers:
            enc = dossier.encaissements.filter(statut='valide')
            total_enc = enc.aggregate(total=Sum('montant'))['total'] or 0

            details.append({
                'reference': dossier.reference,
                'intitule': dossier.get_intitule(),
                'statut': dossier.statut,
                'montant_creance': float(dossier.montant_creance or 0),
                'total_encaisse': float(total_enc),
                'solde_restant': float((dossier.montant_creance or 0) - total_enc),
                'nb_encaissements': enc.count(),
                'dernier_encaissement': enc.order_by('-date_encaissement').first().date_encaissement.isoformat() if enc.exists() else None
            })

        self.donnees_detaillees = {
            'dossiers': details,
            'periode': {
                'debut': self.periode_debut.isoformat(),
                'fin': self.periode_fin.isoformat()
            },
            'resume': {
                'nb_dossiers_total': self.nb_dossiers_total,
                'nb_dossiers_actifs': self.nb_dossiers_actifs,
                'montant_creances': float(self.montant_total_creances),
                'montant_encaisse': float(self.montant_total_encaisse),
                'montant_reverse': float(self.montant_total_reverse),
                'taux_recouvrement': float(self.taux_recouvrement)
            }
        }

        self.save()


class EnvoiAutomatiquePoint(models.Model):
    """Configuration d'envoi automatique des points aux créanciers"""
    FREQUENCE_CHOICES = [
        ('quotidien', 'Quotidien'),
        ('hebdomadaire', 'Hebdomadaire'),
        ('bimensuel', 'Bimensuel'),
        ('mensuel', 'Mensuel'),
        ('trimestriel', 'Trimestriel'),
    ]

    creancier = models.ForeignKey(
        Creancier, on_delete=models.CASCADE, related_name='envois_automatiques'
    )

    # Configuration
    frequence = models.CharField(max_length=20, choices=FREQUENCE_CHOICES, default='mensuel')
    jour_envoi = models.IntegerField(
        default=1, verbose_name='Jour d\'envoi',
        help_text='Jour du mois (1-28) ou jour de la semaine (1-7 pour hebdomadaire)'
    )
    heure_envoi = models.TimeField(default='08:00', verbose_name='Heure d\'envoi')

    # Destinataires
    destinataires = models.JSONField(
        default=list, verbose_name='Adresses email destinataires'
    )
    copie_gestionnaire = models.BooleanField(
        default=True, verbose_name='Envoyer copie au gestionnaire'
    )

    # Filtres à appliquer
    filtres_point = models.JSONField(default=dict, blank=True, verbose_name='Filtres')

    # Suivi
    actif = models.BooleanField(default=True)
    dernier_envoi = models.DateTimeField(null=True, blank=True)
    prochain_envoi = models.DateTimeField(null=True, blank=True)
    nb_envois_total = models.IntegerField(default=0)

    # Traçabilité
    cree_par = models.ForeignKey(
        Utilisateur, on_delete=models.SET_NULL, null=True,
        related_name='envois_auto_crees'
    )
    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Envoi automatique de point'
        verbose_name_plural = 'Envois automatiques de points'
        ordering = ['creancier', 'frequence']

    def __str__(self):
        return f"Envoi {self.get_frequence_display()} - {self.creancier.nom}"

    def calculer_prochain_envoi(self):
        """Calcule la date du prochain envoi"""
        from datetime import datetime, timedelta
        from dateutil.relativedelta import relativedelta

        now = timezone.now()

        if self.frequence == 'quotidien':
            prochain = now + timedelta(days=1)
        elif self.frequence == 'hebdomadaire':
            jours_jusqu_au = (self.jour_envoi - now.weekday()) % 7
            if jours_jusqu_au == 0:
                jours_jusqu_au = 7
            prochain = now + timedelta(days=jours_jusqu_au)
        elif self.frequence == 'bimensuel':
            if now.day < 15:
                prochain = now.replace(day=15)
            else:
                prochain = (now + relativedelta(months=1)).replace(day=1)
        elif self.frequence == 'mensuel':
            jour = min(self.jour_envoi, 28)
            if now.day < jour:
                prochain = now.replace(day=jour)
            else:
                prochain = (now + relativedelta(months=1)).replace(day=jour)
        elif self.frequence == 'trimestriel':
            mois_prochain = ((now.month - 1) // 3 + 1) * 3 + 1
            if mois_prochain > 12:
                prochain = now.replace(year=now.year + 1, month=mois_prochain - 12, day=min(self.jour_envoi, 28))
            else:
                prochain = now.replace(month=mois_prochain, day=min(self.jour_envoi, 28))
        else:
            prochain = now + timedelta(days=30)

        self.prochain_envoi = prochain.replace(
            hour=self.heure_envoi.hour,
            minute=self.heure_envoi.minute,
            second=0,
            microsecond=0
        )
        self.save()


class HistoriqueEnvoiPoint(models.Model):
    """Historique des envois de points automatiques"""
    STATUT_CHOICES = [
        ('succes', 'Succès'),
        ('echec', 'Échec'),
        ('partiel', 'Partiel'),
    ]

    envoi_config = models.ForeignKey(
        EnvoiAutomatiquePoint, on_delete=models.CASCADE, related_name='historique'
    )
    point_global = models.ForeignKey(
        PointGlobalCreancier, on_delete=models.SET_NULL, null=True,
        related_name='envois'
    )

    date_envoi = models.DateTimeField(default=timezone.now)
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES)

    destinataires_envoyes = models.JSONField(default=list)
    destinataires_echec = models.JSONField(default=list)

    message_erreur = models.TextField(blank=True)

    class Meta:
        verbose_name = 'Historique d\'envoi de point'
        verbose_name_plural = 'Historiques d\'envois de points'
        ordering = ['-date_envoi']

    def __str__(self):
        return f"Envoi {self.date_envoi.strftime('%d/%m/%Y %H:%M')} - {self.statut}"
