"""
Module Ressources Humaines - Conforme à la législation béninoise
Code du travail, Code de sécurité sociale CNSS, Convention collective
"""

from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError
from django.utils import timezone
from decimal import Decimal
import datetime


# ══════════════════════════════════════════════════════════════════════════════
# CONSTANTES OBSOLÈTES - UTILISER ConfigurationEtude À LA PLACE
# ══════════════════════════════════════════════════════════════════════════════
# Ces constantes sont conservées pour référence et rétrocompatibilité mais ne
# sont plus utilisées dans les calculs. Les valeurs sont maintenant configurables
# dans le module Paramètres via ConfigurationEtude et TrancheIPTS.
#
# Pour récupérer les paramètres actuels, utiliser :
#   from parametres.models import ConfigurationEtude, TrancheIPTS
#   config = ConfigurationEtude.get_solo()
#   bareme = TrancheIPTS.get_bareme_actif()
# ══════════════════════════════════════════════════════════════════════════════

# SMIG (→ config.rh_smig)
SMIG_BENIN = Decimal('52000')

# Plafond CNSS (→ config.rh_plafond_cnss)
PLAFOND_CNSS = Decimal('600000')

# Taux CNSS (→ config.rh_cnss_salarial_vieillesse, etc.)
TAUX_CNSS_SALARIAL_VIEILLESSE = Decimal('3.6')
TAUX_CNSS_PATRONAL_VIEILLESSE = Decimal('6.4')
TAUX_CNSS_PATRONAL_PRESTATIONS_FAMILIALES = Decimal('6.4')
TAUX_CNSS_PATRONAL_RISQUES_PROFESSIONNELS_MIN = Decimal('1.0')
TAUX_CNSS_PATRONAL_RISQUES_PROFESSIONNELS_MAX = Decimal('4.0')

# VPS (→ config.rh_taux_vps)
TAUX_VPS = Decimal('4.0')

# Barème IPTS (→ TrancheIPTS.get_bareme_actif())
BAREME_IPTS = [
    (0, 50000, Decimal('0')),
    (50001, 130000, Decimal('10')),
    (130001, 280000, Decimal('15')),
    (280001, 530000, Decimal('19')),
    (530001, 880000, Decimal('24')),
    (880001, 1380000, Decimal('28')),
    (1380001, 2030000, Decimal('32')),
    (2030001, 2830000, Decimal('35')),
    (2830001, 3780000, Decimal('37')),
    (3780001, float('inf'), Decimal('40')),
]

# Congés (→ config.rh_conges_annuels)
JOURS_CONGES_ANNUELS_BASE = 24
JOURS_SUPPLEMENTAIRES_5_ANS = 1
JOURS_SUPPLEMENTAIRES_10_ANS = 2
JOURS_SUPPLEMENTAIRES_15_ANS = 3
JOURS_SUPPLEMENTAIRES_20_ANS = 5


# =============================================================================
# MODÈLES DE CATÉGORIES ET POSTES
# =============================================================================

class CategorieEmploye(models.Model):
    """Catégories professionnelles selon la convention collective"""
    code = models.CharField(max_length=10, unique=True, verbose_name="Code")
    libelle = models.CharField(max_length=100, verbose_name="Libellé")
    niveau = models.IntegerField(default=1, verbose_name="Niveau hiérarchique")
    coefficient = models.DecimalField(max_digits=6, decimal_places=2, default=Decimal('100'),
                                       verbose_name="Coefficient")
    salaire_minimum = models.DecimalField(max_digits=12, decimal_places=0, default=SMIG_BENIN,
                                           verbose_name="Salaire minimum")
    duree_essai_mois = models.IntegerField(default=1, validators=[MinValueValidator(1), MaxValueValidator(3)],
                                            verbose_name="Durée période d'essai (mois)")
    description = models.TextField(blank=True, verbose_name="Description")

    class Meta:
        verbose_name = "Catégorie professionnelle"
        verbose_name_plural = "Catégories professionnelles"
        ordering = ['niveau', 'code']

    def __str__(self):
        return f"{self.code} - {self.libelle}"


class Poste(models.Model):
    """Postes/fonctions dans l'étude"""
    code = models.CharField(max_length=20, unique=True, verbose_name="Code")
    libelle = models.CharField(max_length=100, verbose_name="Libellé")
    categorie = models.ForeignKey(CategorieEmploye, on_delete=models.PROTECT,
                                   related_name='postes', verbose_name="Catégorie")
    description = models.TextField(blank=True, verbose_name="Description du poste")
    responsabilites = models.TextField(blank=True, verbose_name="Responsabilités")
    competences_requises = models.TextField(blank=True, verbose_name="Compétences requises")
    actif = models.BooleanField(default=True, verbose_name="Actif")

    class Meta:
        verbose_name = "Poste"
        verbose_name_plural = "Postes"
        ordering = ['categorie__niveau', 'libelle']

    def __str__(self):
        return self.libelle


class Site(models.Model):
    """Sites d'affectation"""
    nom = models.CharField(max_length=100, verbose_name="Nom du site")
    adresse = models.TextField(verbose_name="Adresse")
    telephone = models.CharField(max_length=20, blank=True, verbose_name="Téléphone")
    est_principal = models.BooleanField(default=False, verbose_name="Site principal")
    actif = models.BooleanField(default=True, verbose_name="Actif")

    class Meta:
        verbose_name = "Site"
        verbose_name_plural = "Sites"
        ordering = ['-est_principal', 'nom']

    def __str__(self):
        return self.nom


# =============================================================================
# MODÈLE EMPLOYÉ
# =============================================================================

class Employe(models.Model):
    """Fiche employé complète conforme à la législation béninoise"""

    # Choix pour les champs à sélection
    SEXE_CHOICES = [
        ('M', 'Masculin'),
        ('F', 'Féminin'),
    ]

    SITUATION_MATRIMONIALE_CHOICES = [
        ('celibataire', 'Célibataire'),
        ('marie', 'Marié(e)'),
        ('divorce', 'Divorcé(e)'),
        ('veuf', 'Veuf/Veuve'),
        ('union_libre', 'Union libre'),
    ]

    TYPE_CONTRAT_CHOICES = [
        ('cdi', 'CDI - Contrat à Durée Indéterminée'),
        ('cdd', 'CDD - Contrat à Durée Déterminée'),
        ('stage', 'Contrat de stage'),
        ('apprentissage', 'Contrat d\'apprentissage'),
        ('temporaire', 'Contrat de travail temporaire'),
    ]

    STATUT_CHOICES = [
        ('actif', 'Actif'),
        ('en_conge', 'En congé'),
        ('suspendu', 'Suspendu'),
        ('parti', 'Parti'),
    ]

    # --- Informations personnelles ---
    matricule = models.CharField(max_length=20, unique=True, verbose_name="Matricule interne")
    nom = models.CharField(max_length=100, verbose_name="Nom")
    prenoms = models.CharField(max_length=150, verbose_name="Prénoms")
    date_naissance = models.DateField(verbose_name="Date de naissance")
    lieu_naissance = models.CharField(max_length=100, verbose_name="Lieu de naissance")
    sexe = models.CharField(max_length=1, choices=SEXE_CHOICES, verbose_name="Sexe")
    situation_matrimoniale = models.CharField(max_length=20, choices=SITUATION_MATRIMONIALE_CHOICES,
                                               default='celibataire', verbose_name="Situation matrimoniale")
    nombre_enfants = models.IntegerField(default=0, validators=[MinValueValidator(0)],
                                          verbose_name="Nombre d'enfants à charge")
    nationalite = models.CharField(max_length=50, default='Béninoise', verbose_name="Nationalité")
    numero_cni = models.CharField(max_length=30, blank=True, verbose_name="N° CNI/Passeport")

    # Adresse et contacts
    adresse = models.TextField(verbose_name="Adresse complète")
    telephone = models.CharField(max_length=20, verbose_name="Téléphone")
    telephone_secondaire = models.CharField(max_length=20, blank=True, verbose_name="Téléphone secondaire")
    email = models.EmailField(blank=True, verbose_name="Email")

    # Photo
    photo = models.ImageField(upload_to='employes/photos/', blank=True, null=True,
                               verbose_name="Photo d'identité")

    # Personne à contacter en cas d'urgence
    contact_urgence_nom = models.CharField(max_length=100, blank=True, verbose_name="Contact urgence - Nom")
    contact_urgence_telephone = models.CharField(max_length=20, blank=True,
                                                   verbose_name="Contact urgence - Téléphone")
    contact_urgence_relation = models.CharField(max_length=50, blank=True,
                                                  verbose_name="Contact urgence - Lien de parenté")

    # --- Informations professionnelles ---
    date_embauche = models.DateField(verbose_name="Date d'embauche")
    date_fin_contrat = models.DateField(null=True, blank=True, verbose_name="Date de fin (si CDD)")
    type_contrat = models.CharField(max_length=20, choices=TYPE_CONTRAT_CHOICES, default='cdi',
                                     verbose_name="Type de contrat")
    categorie = models.ForeignKey(CategorieEmploye, on_delete=models.PROTECT, null=True, blank=True,
                                   related_name='employes', verbose_name="Catégorie professionnelle")
    poste = models.ForeignKey(Poste, on_delete=models.PROTECT, null=True, blank=True,
                               related_name='employes', verbose_name="Poste/Fonction")
    site = models.ForeignKey(Site, on_delete=models.SET_NULL, null=True, blank=True,
                              related_name='employes', verbose_name="Site d'affectation")
    superieur = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True,
                                   related_name='subordonnes', verbose_name="Supérieur hiérarchique")
    salaire_base = models.DecimalField(max_digits=12, decimal_places=0, validators=[MinValueValidator(SMIG_BENIN)],
                                        verbose_name="Salaire de base (FCFA)")
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default='actif', verbose_name="Statut")

    # --- Informations légales ---
    numero_cnss = models.CharField(max_length=30, blank=True, verbose_name="N° CNSS")
    numero_ifu = models.CharField(max_length=20, blank=True, verbose_name="N° IFU")
    numero_cip = models.CharField(max_length=30, blank=True, verbose_name="N° CIP (si applicable)")

    # RIB bancaire
    banque = models.CharField(max_length=100, blank=True, verbose_name="Banque")
    rib_code_banque = models.CharField(max_length=10, blank=True, verbose_name="Code banque")
    rib_code_guichet = models.CharField(max_length=10, blank=True, verbose_name="Code guichet")
    rib_numero_compte = models.CharField(max_length=30, blank=True, verbose_name="N° compte")
    rib_cle = models.CharField(max_length=5, blank=True, verbose_name="Clé RIB")

    # Lien avec utilisateur système
    utilisateur = models.OneToOneField('gestion.Utilisateur', on_delete=models.SET_NULL,
                                        null=True, blank=True, related_name='employe_rh',
                                        verbose_name="Compte utilisateur")

    # Audit
    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Employé"
        verbose_name_plural = "Employés"
        ordering = ['nom', 'prenoms']

    def __str__(self):
        return f"{self.matricule} - {self.nom} {self.prenoms}"

    def get_nom_complet(self):
        return f"{self.nom} {self.prenoms}"

    def get_initiales(self):
        return f"{self.nom[0]}{self.prenoms[0]}".upper() if self.nom and self.prenoms else "XX"

    @property
    def anciennete_annees(self):
        """Calcule l'ancienneté en années"""
        today = timezone.now().date()
        delta = today - self.date_embauche
        return delta.days // 365

    @property
    def anciennete_mois(self):
        """Calcule l'ancienneté en mois"""
        today = timezone.now().date()
        delta = today - self.date_embauche
        return delta.days // 30

    @property
    def prime_anciennete_taux(self):
        """Calcule le taux de prime d'ancienneté (2% par an, max 25%)"""
        taux = self.anciennete_annees * 2
        return min(taux, 25)

    @property
    def prime_anciennete_montant(self):
        """Calcule le montant de la prime d'ancienneté"""
        return self.salaire_base * Decimal(self.prime_anciennete_taux) / 100

    @property
    def jours_conges_annuels(self):
        """Calcule le nombre de jours de congés annuels avec ancienneté"""
        jours = JOURS_CONGES_ANNUELS_BASE
        anciennete = self.anciennete_annees

        if anciennete >= 20:
            jours += JOURS_SUPPLEMENTAIRES_20_ANS
        elif anciennete >= 15:
            jours += JOURS_SUPPLEMENTAIRES_15_ANS
        elif anciennete >= 10:
            jours += JOURS_SUPPLEMENTAIRES_10_ANS
        elif anciennete >= 5:
            jours += JOURS_SUPPLEMENTAIRES_5_ANS

        return jours

    @property
    def age(self):
        """Calcule l'âge de l'employé"""
        today = timezone.now().date()
        age = today.year - self.date_naissance.year
        if today.month < self.date_naissance.month or \
           (today.month == self.date_naissance.month and today.day < self.date_naissance.day):
            age -= 1
        return age

    @property
    def rib_complet(self):
        """Retourne le RIB complet formaté"""
        if self.rib_numero_compte:
            return f"{self.rib_code_banque} {self.rib_code_guichet} {self.rib_numero_compte} {self.rib_cle}"
        return ""

    @classmethod
    def generer_matricule(cls):
        """Génère un matricule unique"""
        annee = timezone.now().year
        prefix = f"EMP{annee}"
        last = cls.objects.filter(matricule__startswith=prefix).order_by('-matricule').first()
        if last:
            num = int(last.matricule[-4:]) + 1
        else:
            num = 1
        return f"{prefix}{num:04d}"

    def clean(self):
        import re
        errors = {}

        # Vérifier que le salaire est >= SMIG
        if self.salaire_base and self.salaire_base < SMIG_BENIN:
            errors['salaire_base'] = f"Le salaire ne peut pas être inférieur au SMIG ({SMIG_BENIN} FCFA)"

        # Vérifier la cohérence des dates pour CDD
        if self.type_contrat == 'cdd' and not self.date_fin_contrat:
            errors['date_fin_contrat'] = "Un CDD doit avoir une date de fin"

        # Vérifier date embauche <= aujourd'hui
        if self.date_embauche and self.date_embauche > timezone.now().date():
            errors['date_embauche'] = "La date d'embauche ne peut pas être dans le futur"

        # Vérifier que date_fin_contrat > date_embauche si CDD
        if self.date_fin_contrat and self.date_embauche:
            if self.date_fin_contrat <= self.date_embauche:
                errors['date_fin_contrat'] = "La date de fin doit être postérieure à la date d'embauche"

        # Vérifier âge >= 18 ans
        if self.date_naissance:
            age = self.age
            if age < 18:
                errors['date_naissance'] = "L'employé doit avoir au moins 18 ans"

        # Valider format email
        if self.email:
            email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            if not re.match(email_regex, self.email):
                errors['email'] = "Format d'email invalide"

        # Valider format IFU (13 chiffres au Bénin)
        if self.numero_ifu:
            ifu_clean = re.sub(r'\D', '', self.numero_ifu)
            if len(ifu_clean) != 13:
                errors['numero_ifu'] = "L'IFU doit contenir exactement 13 chiffres"

        # Valider format numéro CNSS
        if self.numero_cnss:
            cnss_clean = re.sub(r'\D', '', self.numero_cnss)
            if len(cnss_clean) < 7:
                errors['numero_cnss'] = "Le numéro CNSS semble invalide"

        if errors:
            raise ValidationError(errors)


class DocumentEmploye(models.Model):
    """Documents archivés pour chaque employé"""
    TYPE_DOCUMENT_CHOICES = [
        ('contrat', 'Contrat de travail'),
        ('avenant', 'Avenant au contrat'),
        ('cv', 'CV'),
        ('diplome', 'Diplôme'),
        ('certificat_travail', 'Certificat de travail antérieur'),
        ('piece_identite', 'Pièce d\'identité'),
        ('certificat_residence', 'Certificat de résidence'),
        ('photo', 'Photo d\'identité'),
        ('attestation_cnss', 'Attestation CNSS'),
        ('bulletin_paie', 'Bulletin de paie'),
        ('evaluation', 'Évaluation'),
        ('sanction', 'Document de sanction'),
        ('formation', 'Attestation de formation'),
        ('autre', 'Autre document'),
    ]

    employe = models.ForeignKey(Employe, on_delete=models.CASCADE,
                                 related_name='documents', verbose_name="Employé")
    type_document = models.CharField(max_length=30, choices=TYPE_DOCUMENT_CHOICES,
                                      verbose_name="Type de document")
    titre = models.CharField(max_length=200, verbose_name="Titre")
    fichier = models.FileField(upload_to='employes/documents/', verbose_name="Fichier")
    date_document = models.DateField(null=True, blank=True, verbose_name="Date du document")
    description = models.TextField(blank=True, verbose_name="Description")
    date_upload = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Document employé"
        verbose_name_plural = "Documents employés"
        ordering = ['-date_upload']

    def __str__(self):
        return f"{self.employe.matricule} - {self.titre}"


# =============================================================================
# GESTION DES CONTRATS
# =============================================================================

class Contrat(models.Model):
    """Contrats de travail"""
    TYPE_CONTRAT_CHOICES = Employe.TYPE_CONTRAT_CHOICES

    STATUT_CHOICES = [
        ('actif', 'Actif'),
        ('termine', 'Terminé'),
        ('suspendu', 'Suspendu'),
        ('annule', 'Annulé'),
    ]

    employe = models.ForeignKey(Employe, on_delete=models.CASCADE,
                                 related_name='contrats', verbose_name="Employé")
    reference = models.CharField(max_length=50, unique=True, verbose_name="Référence contrat")
    type_contrat = models.CharField(max_length=20, choices=TYPE_CONTRAT_CHOICES,
                                     verbose_name="Type de contrat")
    date_debut = models.DateField(verbose_name="Date de début")
    date_fin = models.DateField(null=True, blank=True, verbose_name="Date de fin prévue")

    # Période d'essai
    periode_essai_mois = models.IntegerField(default=1, validators=[MinValueValidator(0), MaxValueValidator(6)],
                                              verbose_name="Période d'essai (mois)")
    date_fin_essai = models.DateField(null=True, blank=True, verbose_name="Date fin période d'essai")
    essai_renouvele = models.BooleanField(default=False, verbose_name="Période d'essai renouvelée")

    # Conditions
    poste = models.ForeignKey(Poste, on_delete=models.PROTECT, verbose_name="Poste")
    categorie = models.ForeignKey(CategorieEmploye, on_delete=models.PROTECT,
                                   verbose_name="Catégorie professionnelle")
    salaire_base = models.DecimalField(max_digits=12, decimal_places=0, verbose_name="Salaire de base")
    site = models.ForeignKey(Site, on_delete=models.SET_NULL, null=True, blank=True,
                              verbose_name="Site d'affectation")

    # Clauses particulières
    clauses_particulieres = models.TextField(blank=True, verbose_name="Clauses particulières")

    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default='actif', verbose_name="Statut")

    # Documents
    fichier_contrat = models.FileField(upload_to='contrats/', blank=True, null=True,
                                        verbose_name="Fichier contrat signé")

    # Audit
    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Contrat"
        verbose_name_plural = "Contrats"
        ordering = ['-date_debut']

    def __str__(self):
        return f"{self.reference} - {self.employe.get_nom_complet()}"

    def save(self, *args, **kwargs):
        # Calculer automatiquement la date de fin de période d'essai
        if self.date_debut and self.periode_essai_mois:
            from dateutil.relativedelta import relativedelta
            mois = self.periode_essai_mois * 2 if self.essai_renouvele else self.periode_essai_mois
            self.date_fin_essai = self.date_debut + relativedelta(months=mois)
        super().save(*args, **kwargs)

    @classmethod
    def generer_reference(cls):
        """Génère une référence de contrat unique"""
        annee = timezone.now().year
        prefix = f"CTR{annee}"
        last = cls.objects.filter(reference__startswith=prefix).order_by('-reference').first()
        if last:
            num = int(last.reference[-4:]) + 1
        else:
            num = 1
        return f"{prefix}{num:04d}"

    @property
    def est_en_periode_essai(self):
        """Vérifie si le contrat est en période d'essai"""
        if self.date_fin_essai:
            return timezone.now().date() <= self.date_fin_essai
        return False

    @property
    def duree_restante_cdd(self):
        """Calcule la durée restante pour un CDD"""
        if self.type_contrat == 'cdd' and self.date_fin:
            delta = self.date_fin - timezone.now().date()
            return max(0, delta.days)
        return None


class AvenantContrat(models.Model):
    """Avenants aux contrats"""
    TYPE_AVENANT_CHOICES = [
        ('salaire', 'Modification de salaire'),
        ('poste', 'Changement de poste'),
        ('site', 'Changement de site'),
        ('categorie', 'Changement de catégorie'),
        ('horaires', 'Modification des horaires'),
        ('renouvellement', 'Renouvellement CDD'),
        ('autre', 'Autre modification'),
    ]

    contrat = models.ForeignKey(Contrat, on_delete=models.CASCADE,
                                 related_name='avenants', verbose_name="Contrat")
    reference = models.CharField(max_length=50, unique=True, verbose_name="Référence avenant")
    type_avenant = models.CharField(max_length=20, choices=TYPE_AVENANT_CHOICES,
                                     verbose_name="Type d'avenant")
    date_effet = models.DateField(verbose_name="Date d'effet")

    # Modifications
    description = models.TextField(verbose_name="Description des modifications")
    ancien_salaire = models.DecimalField(max_digits=12, decimal_places=0, null=True, blank=True,
                                          verbose_name="Ancien salaire")
    nouveau_salaire = models.DecimalField(max_digits=12, decimal_places=0, null=True, blank=True,
                                           verbose_name="Nouveau salaire")
    ancien_poste = models.ForeignKey(Poste, on_delete=models.SET_NULL, null=True, blank=True,
                                      related_name='avenants_ancien', verbose_name="Ancien poste")
    nouveau_poste = models.ForeignKey(Poste, on_delete=models.SET_NULL, null=True, blank=True,
                                       related_name='avenants_nouveau', verbose_name="Nouveau poste")

    fichier_avenant = models.FileField(upload_to='avenants/', blank=True, null=True,
                                        verbose_name="Fichier avenant signé")

    date_creation = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Avenant"
        verbose_name_plural = "Avenants"
        ordering = ['-date_effet']

    def __str__(self):
        return f"{self.reference} - {self.contrat.employe.get_nom_complet()}"


# =============================================================================
# GESTION DE LA PAIE
# =============================================================================

class ElementPaie(models.Model):
    """Éléments de paie configurables (primes, indemnités, retenues)"""
    TYPE_CHOICES = [
        ('gain', 'Gain'),
        ('retenue', 'Retenue'),
    ]

    NATURE_CHOICES = [
        # Gains
        ('prime_anciennete', 'Prime d\'ancienneté'),
        ('prime_responsabilite', 'Prime de responsabilité'),
        ('prime_rendement', 'Prime de rendement'),
        ('prime_deplacement', 'Prime de déplacement'),
        ('prime_transport', 'Prime de transport'),
        ('heures_sup', 'Heures supplémentaires'),
        ('indemnite_logement', 'Indemnité de logement'),
        ('avantage_nature', 'Avantage en nature'),
        ('autre_gain', 'Autre gain'),
        # Retenues
        ('cnss_salariale', 'Cotisation CNSS salariale'),
        ('ipts', 'IPTS'),
        ('avance_salaire', 'Avance sur salaire'),
        ('pret', 'Remboursement prêt'),
        ('absence', 'Retenue pour absence'),
        ('autre_retenue', 'Autre retenue'),
    ]

    code = models.CharField(max_length=20, unique=True, verbose_name="Code")
    libelle = models.CharField(max_length=100, verbose_name="Libellé")
    type_element = models.CharField(max_length=10, choices=TYPE_CHOICES, verbose_name="Type")
    nature = models.CharField(max_length=30, choices=NATURE_CHOICES, verbose_name="Nature")
    est_imposable = models.BooleanField(default=True, verbose_name="Imposable")
    est_cotisable = models.BooleanField(default=True, verbose_name="Cotisable CNSS")
    taux = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True,
                                verbose_name="Taux (%)")
    montant_fixe = models.DecimalField(max_digits=12, decimal_places=0, null=True, blank=True,
                                        verbose_name="Montant fixe")
    actif = models.BooleanField(default=True, verbose_name="Actif")

    class Meta:
        verbose_name = "Élément de paie"
        verbose_name_plural = "Éléments de paie"
        ordering = ['type_element', 'libelle']

    def __str__(self):
        return f"{self.code} - {self.libelle}"


class PeriodePaie(models.Model):
    """Périodes de paie mensuelles"""
    STATUT_CHOICES = [
        ('ouvert', 'Ouvert'),
        ('cloture', 'Clôturé'),
    ]

    annee = models.IntegerField(verbose_name="Année")
    mois = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(12)],
                                verbose_name="Mois")
    date_debut = models.DateField(verbose_name="Date de début")
    date_fin = models.DateField(verbose_name="Date de fin")
    statut = models.CharField(max_length=10, choices=STATUT_CHOICES, default='ouvert',
                               verbose_name="Statut")
    date_cloture = models.DateTimeField(null=True, blank=True, verbose_name="Date de clôture")

    class Meta:
        verbose_name = "Période de paie"
        verbose_name_plural = "Périodes de paie"
        ordering = ['-annee', '-mois']
        unique_together = ['annee', 'mois']

    def __str__(self):
        mois_noms = ['', 'Janvier', 'Février', 'Mars', 'Avril', 'Mai', 'Juin',
                     'Juillet', 'Août', 'Septembre', 'Octobre', 'Novembre', 'Décembre']
        return f"{mois_noms[self.mois]} {self.annee}"

    @classmethod
    def get_periode_courante(cls):
        """Retourne ou crée la période de paie courante"""
        today = timezone.now().date()
        periode, created = cls.objects.get_or_create(
            annee=today.year,
            mois=today.month,
            defaults={
                'date_debut': today.replace(day=1),
                'date_fin': (today.replace(day=1) + datetime.timedelta(days=32)).replace(day=1) - datetime.timedelta(days=1)
            }
        )
        return periode


class BulletinPaie(models.Model):
    """Bulletins de paie"""
    STATUT_CHOICES = [
        ('brouillon', 'Brouillon'),
        ('valide', 'Validé'),
        ('paye', 'Payé'),
        ('annule', 'Annulé'),
    ]

    MODE_PAIEMENT_CHOICES = [
        ('virement', 'Virement bancaire'),
        ('especes', 'Espèces'),
        ('cheque', 'Chèque'),
    ]

    employe = models.ForeignKey(Employe, on_delete=models.PROTECT,
                                 related_name='bulletins', verbose_name="Employé")
    periode = models.ForeignKey(PeriodePaie, on_delete=models.PROTECT,
                                 related_name='bulletins', verbose_name="Période")
    reference = models.CharField(max_length=50, unique=True, verbose_name="Référence")

    # Éléments de base
    salaire_base = models.DecimalField(max_digits=12, decimal_places=0, verbose_name="Salaire de base")
    jours_travailles = models.IntegerField(default=26, verbose_name="Jours travaillés")
    jours_absence = models.IntegerField(default=0, verbose_name="Jours d'absence")
    heures_supplementaires = models.DecimalField(max_digits=6, decimal_places=2, default=0,
                                                   verbose_name="Heures supplémentaires")

    # Totaux calculés
    total_gains = models.DecimalField(max_digits=12, decimal_places=0, default=0,
                                       verbose_name="Total gains")
    salaire_brut = models.DecimalField(max_digits=12, decimal_places=0, default=0,
                                        verbose_name="Salaire brut")
    base_cotisable = models.DecimalField(max_digits=12, decimal_places=0, default=0,
                                          verbose_name="Base cotisable CNSS")
    base_imposable = models.DecimalField(max_digits=12, decimal_places=0, default=0,
                                          verbose_name="Base imposable")

    # Cotisations CNSS
    cnss_salariale = models.DecimalField(max_digits=12, decimal_places=0, default=0,
                                          verbose_name="CNSS salariale")
    cnss_patronale = models.DecimalField(max_digits=12, decimal_places=0, default=0,
                                          verbose_name="CNSS patronale")

    # Impôts
    ipts = models.DecimalField(max_digits=12, decimal_places=0, default=0, verbose_name="IPTS")
    vps = models.DecimalField(max_digits=12, decimal_places=0, default=0, verbose_name="VPS")

    total_retenues = models.DecimalField(max_digits=12, decimal_places=0, default=0,
                                          verbose_name="Total retenues")
    net_a_payer = models.DecimalField(max_digits=12, decimal_places=0, default=0,
                                       verbose_name="Net à payer")

    # Cumuls annuels
    cumul_brut = models.DecimalField(max_digits=15, decimal_places=0, default=0,
                                      verbose_name="Cumul brut annuel")
    cumul_cnss = models.DecimalField(max_digits=15, decimal_places=0, default=0,
                                      verbose_name="Cumul CNSS annuel")
    cumul_ipts = models.DecimalField(max_digits=15, decimal_places=0, default=0,
                                      verbose_name="Cumul IPTS annuel")
    cumul_net = models.DecimalField(max_digits=15, decimal_places=0, default=0,
                                     verbose_name="Cumul net annuel")

    # Paiement
    mode_paiement = models.CharField(max_length=20, choices=MODE_PAIEMENT_CHOICES,
                                      default='virement', verbose_name="Mode de paiement")
    date_paiement = models.DateField(null=True, blank=True, verbose_name="Date de paiement")

    statut = models.CharField(max_length=10, choices=STATUT_CHOICES, default='brouillon',
                               verbose_name="Statut")

    # Audit
    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)
    valide_par = models.ForeignKey('gestion.Utilisateur', on_delete=models.SET_NULL,
                                    null=True, blank=True, verbose_name="Validé par")

    class Meta:
        verbose_name = "Bulletin de paie"
        verbose_name_plural = "Bulletins de paie"
        ordering = ['-periode__annee', '-periode__mois', 'employe__nom']
        unique_together = ['employe', 'periode']

    def __str__(self):
        return f"{self.reference} - {self.employe.get_nom_complet()}"

    @classmethod
    def generer_reference(cls, employe, periode):
        """Génère une référence unique pour le bulletin"""
        return f"BP{periode.annee}{periode.mois:02d}{employe.matricule}"

    @staticmethod
    def get_parametres_rh():
        """Retourne les paramètres RH actuels pour affichage"""
        from parametres.models import ConfigurationEtude
        config = ConfigurationEtude.get_solo()
        return {
            'smig': config.rh_smig,
            'plafond_cnss': config.rh_plafond_cnss,
            'taux_cnss_salarial': config.rh_cnss_salarial_vieillesse,
            'taux_cnss_patronal_vieillesse': config.rh_cnss_patronal_vieillesse,
            'taux_cnss_patronal_pf': config.rh_cnss_patronal_pf,
            'taux_cnss_patronal_at': config.rh_taux_risques_professionnels,
            'taux_vps': config.rh_taux_vps,
        }

    def calculer(self):
        """Calcule tous les éléments du bulletin en utilisant les paramètres configurables"""
        from decimal import ROUND_HALF_UP
        from parametres.models import ConfigurationEtude, TrancheIPTS

        # Récupérer les paramètres configurables
        config = ConfigurationEtude.get_solo()

        plafond_cnss = config.rh_plafond_cnss or Decimal('600000')
        taux_cnss_salarial = config.rh_cnss_salarial_vieillesse or Decimal('3.6')
        taux_cnss_patronal_vieillesse = config.rh_cnss_patronal_vieillesse or Decimal('6.4')
        taux_cnss_patronal_pf = config.rh_cnss_patronal_pf or Decimal('6.4')
        taux_cnss_patronal_at = config.rh_taux_risques_professionnels or Decimal('2.0')
        taux_vps = config.rh_taux_vps or Decimal('4.0')

        # Salaire de base proratisé
        jours_ouvrables = 26
        salaire_journalier = self.salaire_base / jours_ouvrables
        salaire_prorata = salaire_journalier * (self.jours_travailles - self.jours_absence)

        # Prime d'ancienneté
        prime_anciennete = self.employe.prime_anciennete_montant

        # Heures supplémentaires selon Code du Travail Bénin
        # - 1ère à 8ème heure : majoration 15%
        # - Au-delà de 8h : majoration 25%
        taux_horaire = self.salaire_base / (jours_ouvrables * 8)
        heures_sup = self.heures_supplementaires
        if heures_sup <= 8:
            heures_sup_montant = heures_sup * taux_horaire * Decimal('1.15')
        else:
            # 8 premières heures à 15%, le reste à 25%
            heures_sup_montant = (
                Decimal('8') * taux_horaire * Decimal('1.15') +
                (heures_sup - 8) * taux_horaire * Decimal('1.25')
            )

        # Total gains depuis les lignes
        total_lignes_gains = sum(
            l.montant for l in self.lignes.filter(element__type_element='gain')
        )

        self.total_gains = salaire_prorata + prime_anciennete + heures_sup_montant + total_lignes_gains
        self.salaire_brut = self.total_gains

        # Base cotisable (plafonnée selon paramètres)
        self.base_cotisable = min(self.salaire_brut, plafond_cnss)

        # Cotisations salariales CNSS (vieillesse uniquement)
        self.cnss_salariale = (self.base_cotisable * taux_cnss_salarial / 100).quantize(Decimal('1'), ROUND_HALF_UP)

        # Cotisations patronales CNSS (vieillesse + PF + AT/RP)
        cnss_patronale_vieillesse = (self.base_cotisable * taux_cnss_patronal_vieillesse / 100).quantize(Decimal('1'), ROUND_HALF_UP)
        cnss_patronale_pf = (self.base_cotisable * taux_cnss_patronal_pf / 100).quantize(Decimal('1'), ROUND_HALF_UP)
        cnss_patronale_at = (self.base_cotisable * taux_cnss_patronal_at / 100).quantize(Decimal('1'), ROUND_HALF_UP)
        self.cnss_patronale = cnss_patronale_vieillesse + cnss_patronale_pf + cnss_patronale_at

        # VPS (Versement Patronal sur Salaire)
        self.vps = (self.salaire_brut * taux_vps / 100).quantize(Decimal('1'), ROUND_HALF_UP)

        # Base imposable (après déduction CNSS salariale)
        self.base_imposable = self.salaire_brut - self.cnss_salariale

        # IPTS (utiliser le barème configurable)
        self.ipts = self._calculer_ipts(self.base_imposable, self.employe.nombre_enfants)

        # Total retenues depuis les lignes
        total_lignes_retenues = sum(
            l.montant for l in self.lignes.filter(element__type_element='retenue')
        )

        self.total_retenues = self.cnss_salariale + self.ipts + total_lignes_retenues
        self.net_a_payer = self.salaire_brut - self.total_retenues

        # Mise à jour des cumuls
        self._calculer_cumuls()

        self.save()

    def _calculer_ipts(self, base_imposable, nb_enfants):
        """Calcule l'IPTS selon le barème configurable avec abattements pour enfants"""
        from decimal import ROUND_HALF_UP
        from parametres.models import TrancheIPTS

        # Abattement pour charges de famille (5% par enfant, max 25%)
        abattement = Decimal('0')
        if nb_enfants > 0:
            abattement = min(nb_enfants * Decimal('0.05'), Decimal('0.25'))

        base_apres_abattement = base_imposable * (1 - abattement)

        # Utiliser le barème IPTS configurable
        impot = TrancheIPTS.calculer_ipts(base_apres_abattement)

        return impot.quantize(Decimal('1'), ROUND_HALF_UP) if impot else Decimal('0')

    def _calculer_cumuls(self):
        """Calcule les cumuls annuels"""
        bulletins_precedents = BulletinPaie.objects.filter(
            employe=self.employe,
            periode__annee=self.periode.annee,
            periode__mois__lt=self.periode.mois,
            statut__in=['valide', 'paye']
        )

        self.cumul_brut = sum(b.salaire_brut for b in bulletins_precedents) + self.salaire_brut
        self.cumul_cnss = sum(b.cnss_salariale for b in bulletins_precedents) + self.cnss_salariale
        self.cumul_ipts = sum(b.ipts for b in bulletins_precedents) + self.ipts
        self.cumul_net = sum(b.net_a_payer for b in bulletins_precedents) + self.net_a_payer


class LigneBulletinPaie(models.Model):
    """Lignes détaillées du bulletin de paie"""
    bulletin = models.ForeignKey(BulletinPaie, on_delete=models.CASCADE,
                                  related_name='lignes', verbose_name="Bulletin")
    element = models.ForeignKey(ElementPaie, on_delete=models.PROTECT,
                                 verbose_name="Élément de paie")
    libelle = models.CharField(max_length=200, verbose_name="Libellé")
    base = models.DecimalField(max_digits=12, decimal_places=0, null=True, blank=True,
                                verbose_name="Base")
    taux = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True,
                                verbose_name="Taux (%)")
    montant = models.DecimalField(max_digits=12, decimal_places=0, verbose_name="Montant")

    class Meta:
        verbose_name = "Ligne de bulletin"
        verbose_name_plural = "Lignes de bulletin"
        ordering = ['element__type_element', 'id']

    def __str__(self):
        return f"{self.bulletin.reference} - {self.libelle}"


# =============================================================================
# GESTION DES CONGÉS ET ABSENCES
# =============================================================================

class TypeConge(models.Model):
    """Types de congés configurables"""
    code = models.CharField(max_length=20, unique=True, verbose_name="Code")
    libelle = models.CharField(max_length=100, verbose_name="Libellé")
    duree_max = models.IntegerField(null=True, blank=True, verbose_name="Durée max (jours)")
    est_paye = models.BooleanField(default=True, verbose_name="Congé payé")
    decompte_solde = models.BooleanField(default=True, verbose_name="Décompte du solde")
    justificatif_requis = models.BooleanField(default=False, verbose_name="Justificatif requis")
    description = models.TextField(blank=True, verbose_name="Description")
    actif = models.BooleanField(default=True, verbose_name="Actif")

    class Meta:
        verbose_name = "Type de congé"
        verbose_name_plural = "Types de congés"
        ordering = ['libelle']

    def __str__(self):
        return self.libelle


class Conge(models.Model):
    """Demandes et suivi des congés"""
    STATUT_CHOICES = [
        ('en_attente', 'En attente'),
        ('approuve_n1', 'Approuvé N+1'),
        ('approuve', 'Approuvé'),
        ('refuse', 'Refusé'),
        ('annule', 'Annulé'),
        ('en_cours', 'En cours'),
        ('termine', 'Terminé'),
    ]

    employe = models.ForeignKey(Employe, on_delete=models.CASCADE,
                                 related_name='conges', verbose_name="Employé")
    type_conge = models.ForeignKey(TypeConge, on_delete=models.PROTECT,
                                    verbose_name="Type de congé")
    date_debut = models.DateField(verbose_name="Date de début")
    date_fin = models.DateField(verbose_name="Date de fin")
    nombre_jours = models.IntegerField(verbose_name="Nombre de jours")
    motif = models.TextField(blank=True, verbose_name="Motif")

    # Workflow d'approbation
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default='en_attente',
                               verbose_name="Statut")
    approuve_par_n1 = models.ForeignKey('gestion.Utilisateur', on_delete=models.SET_NULL,
                                         null=True, blank=True, related_name='conges_approuves_n1',
                                         verbose_name="Approuvé par (N+1)")
    date_approbation_n1 = models.DateTimeField(null=True, blank=True,
                                                verbose_name="Date approbation N+1")
    approuve_par = models.ForeignKey('gestion.Utilisateur', on_delete=models.SET_NULL,
                                      null=True, blank=True, related_name='conges_approuves',
                                      verbose_name="Approuvé par")
    date_approbation = models.DateTimeField(null=True, blank=True, verbose_name="Date approbation")
    motif_refus = models.TextField(blank=True, verbose_name="Motif de refus")

    # Documents
    justificatif = models.FileField(upload_to='conges/justificatifs/', blank=True, null=True,
                                     verbose_name="Justificatif")

    # Audit
    date_demande = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Congé"
        verbose_name_plural = "Congés"
        ordering = ['-date_debut']

    def __str__(self):
        return f"{self.employe.get_nom_complet()} - {self.type_conge.libelle} ({self.date_debut})"

    def clean(self):
        if self.date_fin < self.date_debut:
            raise ValidationError("La date de fin doit être postérieure à la date de début")

    def save(self, *args, **kwargs):
        # Calculer automatiquement le nombre de jours
        if self.date_debut and self.date_fin:
            delta = self.date_fin - self.date_debut
            self.nombre_jours = delta.days + 1
        super().save(*args, **kwargs)


class SoldeConge(models.Model):
    """Solde de congés par employé et par année"""
    employe = models.ForeignKey(Employe, on_delete=models.CASCADE,
                                 related_name='soldes_conges', verbose_name="Employé")
    annee = models.IntegerField(verbose_name="Année")
    jours_acquis = models.DecimalField(max_digits=5, decimal_places=2, default=0,
                                        verbose_name="Jours acquis")
    jours_pris = models.DecimalField(max_digits=5, decimal_places=2, default=0,
                                      verbose_name="Jours pris")
    jours_reportes = models.DecimalField(max_digits=5, decimal_places=2, default=0,
                                          verbose_name="Jours reportés année précédente")

    class Meta:
        verbose_name = "Solde de congés"
        verbose_name_plural = "Soldes de congés"
        unique_together = ['employe', 'annee']
        ordering = ['-annee', 'employe__nom']

    def __str__(self):
        return f"{self.employe.get_nom_complet()} - {self.annee}"

    @property
    def solde_disponible(self):
        return self.jours_acquis + self.jours_reportes - self.jours_pris


class TypeAbsence(models.Model):
    """Types d'absences"""
    code = models.CharField(max_length=20, unique=True, verbose_name="Code")
    libelle = models.CharField(max_length=100, verbose_name="Libellé")
    impacte_salaire = models.BooleanField(default=True, verbose_name="Impacte le salaire")
    taux_retenue = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('100'),
                                        verbose_name="Taux de retenue (%)")
    actif = models.BooleanField(default=True, verbose_name="Actif")

    class Meta:
        verbose_name = "Type d'absence"
        verbose_name_plural = "Types d'absences"
        ordering = ['libelle']

    def __str__(self):
        return self.libelle


class Absence(models.Model):
    """Enregistrement des absences"""
    employe = models.ForeignKey(Employe, on_delete=models.CASCADE,
                                 related_name='absences', verbose_name="Employé")
    type_absence = models.ForeignKey(TypeAbsence, on_delete=models.PROTECT,
                                      verbose_name="Type d'absence")
    date_debut = models.DateField(verbose_name="Date de début")
    date_fin = models.DateField(verbose_name="Date de fin")
    nombre_jours = models.DecimalField(max_digits=5, decimal_places=2, verbose_name="Nombre de jours")
    justifie = models.BooleanField(default=False, verbose_name="Justifiée")
    justificatif = models.FileField(upload_to='absences/justificatifs/', blank=True, null=True,
                                     verbose_name="Justificatif")
    motif = models.TextField(blank=True, verbose_name="Motif")
    retenue_calculee = models.DecimalField(max_digits=12, decimal_places=0, default=0,
                                            verbose_name="Retenue calculée")

    date_creation = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Absence"
        verbose_name_plural = "Absences"
        ordering = ['-date_debut']

    def __str__(self):
        return f"{self.employe.get_nom_complet()} - {self.type_absence.libelle} ({self.date_debut})"

    def save(self, *args, **kwargs):
        # Calculer le nombre de jours
        if self.date_debut and self.date_fin:
            delta = self.date_fin - self.date_debut
            self.nombre_jours = Decimal(delta.days + 1)

        # Calculer la retenue
        if self.type_absence.impacte_salaire:
            salaire_journalier = self.employe.salaire_base / 26
            self.retenue_calculee = salaire_journalier * self.nombre_jours * self.type_absence.taux_retenue / 100

        super().save(*args, **kwargs)


class Pointage(models.Model):
    """Pointage quotidien des employés"""
    employe = models.ForeignKey(Employe, on_delete=models.CASCADE,
                                 related_name='pointages', verbose_name="Employé")
    date = models.DateField(verbose_name="Date")
    heure_arrivee = models.TimeField(null=True, blank=True, verbose_name="Heure d'arrivée")
    heure_depart = models.TimeField(null=True, blank=True, verbose_name="Heure de départ")
    present = models.BooleanField(default=True, verbose_name="Présent")
    retard_minutes = models.IntegerField(default=0, verbose_name="Retard (minutes)")
    heures_travaillees = models.DecimalField(max_digits=4, decimal_places=2, default=0,
                                              verbose_name="Heures travaillées")
    commentaire = models.TextField(blank=True, verbose_name="Commentaire")

    class Meta:
        verbose_name = "Pointage"
        verbose_name_plural = "Pointages"
        unique_together = ['employe', 'date']
        ordering = ['-date', 'employe__nom']

    def __str__(self):
        return f"{self.employe.get_nom_complet()} - {self.date}"

    def save(self, *args, **kwargs):
        # Calculer les heures travaillées
        if self.heure_arrivee and self.heure_depart:
            debut = datetime.datetime.combine(self.date, self.heure_arrivee)
            fin = datetime.datetime.combine(self.date, self.heure_depart)
            delta = fin - debut
            self.heures_travaillees = Decimal(delta.seconds / 3600)
        super().save(*args, **kwargs)


# =============================================================================
# GESTION DES PRÊTS ET AVANCES
# =============================================================================

class Pret(models.Model):
    """Prêts et avances aux employés"""
    TYPE_CHOICES = [
        ('avance', 'Avance sur salaire'),
        ('pret', 'Prêt employé'),
    ]

    STATUT_CHOICES = [
        ('en_attente', 'En attente'),
        ('approuve', 'Approuvé'),
        ('refuse', 'Refusé'),
        ('en_cours', 'En cours de remboursement'),
        ('solde', 'Soldé'),
        ('annule', 'Annulé'),
    ]

    employe = models.ForeignKey(Employe, on_delete=models.CASCADE,
                                 related_name='prets', verbose_name="Employé")
    reference = models.CharField(max_length=50, unique=True, verbose_name="Référence")
    type_pret = models.CharField(max_length=20, choices=TYPE_CHOICES, verbose_name="Type")
    montant = models.DecimalField(max_digits=12, decimal_places=0, verbose_name="Montant")
    motif = models.TextField(verbose_name="Motif")
    date_demande = models.DateField(verbose_name="Date de demande")
    date_accord = models.DateField(null=True, blank=True, verbose_name="Date d'accord")

    # Remboursement
    nombre_echeances = models.IntegerField(default=1, verbose_name="Nombre d'échéances")
    montant_echeance = models.DecimalField(max_digits=12, decimal_places=0, default=0,
                                            verbose_name="Montant par échéance")
    date_premiere_echeance = models.DateField(null=True, blank=True,
                                               verbose_name="Date 1ère échéance")
    montant_rembourse = models.DecimalField(max_digits=12, decimal_places=0, default=0,
                                             verbose_name="Montant remboursé")

    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default='en_attente',
                               verbose_name="Statut")

    # Approbation
    approuve_par = models.ForeignKey('gestion.Utilisateur', on_delete=models.SET_NULL,
                                      null=True, blank=True, verbose_name="Approuvé par")
    motif_refus = models.TextField(blank=True, verbose_name="Motif de refus")

    date_creation = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Prêt/Avance"
        verbose_name_plural = "Prêts/Avances"
        ordering = ['-date_demande']

    def __str__(self):
        return f"{self.reference} - {self.employe.get_nom_complet()}"

    @property
    def solde_restant(self):
        return self.montant - self.montant_rembourse

    @classmethod
    def generer_reference(cls, type_pret):
        """Génère une référence unique"""
        prefix = "AVS" if type_pret == 'avance' else "PRT"
        annee = timezone.now().year
        last = cls.objects.filter(reference__startswith=f"{prefix}{annee}").order_by('-reference').first()
        if last:
            num = int(last.reference[-4:]) + 1
        else:
            num = 1
        return f"{prefix}{annee}{num:04d}"

    def clean(self):
        # Vérifier le plafond d'avance (50% du salaire)
        if self.type_pret == 'avance':
            plafond = self.employe.salaire_base * Decimal('0.5')
            if self.montant > plafond:
                raise ValidationError(f"Le montant de l'avance ne peut excéder 50% du salaire ({plafond} FCFA)")


class EcheancePret(models.Model):
    """Échéances de remboursement des prêts"""
    STATUT_CHOICES = [
        ('a_venir', 'À venir'),
        ('preleve', 'Prélevé'),
        ('annule', 'Annulé'),
    ]

    pret = models.ForeignKey(Pret, on_delete=models.CASCADE,
                              related_name='echeances', verbose_name="Prêt")
    numero = models.IntegerField(verbose_name="N° échéance")
    date_echeance = models.DateField(verbose_name="Date d'échéance")
    montant = models.DecimalField(max_digits=12, decimal_places=0, verbose_name="Montant")
    bulletin = models.ForeignKey(BulletinPaie, on_delete=models.SET_NULL, null=True, blank=True,
                                  related_name='echeances_pret', verbose_name="Bulletin de paie")
    statut = models.CharField(max_length=10, choices=STATUT_CHOICES, default='a_venir',
                               verbose_name="Statut")

    class Meta:
        verbose_name = "Échéance de prêt"
        verbose_name_plural = "Échéances de prêt"
        ordering = ['pret', 'numero']
        unique_together = ['pret', 'numero']

    def __str__(self):
        return f"{self.pret.reference} - Échéance {self.numero}"


# =============================================================================
# DÉCLARATIONS SOCIALES ET FISCALES
# =============================================================================

class DeclarationSociale(models.Model):
    """Déclarations CNSS et fiscales"""
    TYPE_CHOICES = [
        ('dns_mensuelle', 'DNS Mensuelle'),
        ('dns_trimestrielle', 'DNS Trimestrielle'),
        ('disa', 'DISA (Annuelle)'),
        ('ipts_mensuel', 'État IPTS Mensuel'),
        ('das', 'DAS (Annuelle)'),
        ('vps_mensuel', 'VPS Mensuel'),
    ]

    STATUT_CHOICES = [
        ('brouillon', 'Brouillon'),
        ('genere', 'Généré'),
        ('transmis', 'Transmis'),
        ('paye', 'Payé'),
    ]

    type_declaration = models.CharField(max_length=20, choices=TYPE_CHOICES,
                                         verbose_name="Type de déclaration")
    periode_debut = models.DateField(verbose_name="Début de période")
    periode_fin = models.DateField(verbose_name="Fin de période")
    annee = models.IntegerField(verbose_name="Année")
    trimestre = models.IntegerField(null=True, blank=True, validators=[MinValueValidator(1), MaxValueValidator(4)],
                                     verbose_name="Trimestre")
    mois = models.IntegerField(null=True, blank=True, validators=[MinValueValidator(1), MaxValueValidator(12)],
                                verbose_name="Mois")

    # Montants
    nombre_salaries = models.IntegerField(default=0, verbose_name="Nombre de salariés")
    masse_salariale = models.DecimalField(max_digits=15, decimal_places=0, default=0,
                                           verbose_name="Masse salariale")
    base_cotisable = models.DecimalField(max_digits=15, decimal_places=0, default=0,
                                          verbose_name="Base cotisable")
    cotisations_salariales = models.DecimalField(max_digits=15, decimal_places=0, default=0,
                                                   verbose_name="Cotisations salariales")
    cotisations_patronales = models.DecimalField(max_digits=15, decimal_places=0, default=0,
                                                   verbose_name="Cotisations patronales")
    total_cotisations = models.DecimalField(max_digits=15, decimal_places=0, default=0,
                                             verbose_name="Total cotisations")

    # Impôts
    total_ipts = models.DecimalField(max_digits=15, decimal_places=0, default=0,
                                      verbose_name="Total IPTS")
    total_vps = models.DecimalField(max_digits=15, decimal_places=0, default=0,
                                     verbose_name="Total VPS")

    statut = models.CharField(max_length=10, choices=STATUT_CHOICES, default='brouillon',
                               verbose_name="Statut")
    date_transmission = models.DateField(null=True, blank=True, verbose_name="Date de transmission")
    date_paiement = models.DateField(null=True, blank=True, verbose_name="Date de paiement")
    reference_paiement = models.CharField(max_length=50, blank=True, verbose_name="Référence paiement")

    fichier = models.FileField(upload_to='declarations/', blank=True, null=True,
                                verbose_name="Fichier généré")
    donnees = models.JSONField(default=dict, verbose_name="Données détaillées")

    date_creation = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Déclaration sociale/fiscale"
        verbose_name_plural = "Déclarations sociales/fiscales"
        ordering = ['-annee', '-periode_debut']

    def __str__(self):
        return f"{self.get_type_declaration_display()} - {self.periode_debut} à {self.periode_fin}"

    def generer(self):
        """Génère la déclaration à partir des bulletins de paie"""
        bulletins = BulletinPaie.objects.filter(
            periode__annee=self.annee,
            statut__in=['valide', 'paye']
        )

        if self.mois:
            bulletins = bulletins.filter(periode__mois=self.mois)
        elif self.trimestre:
            mois_debut = (self.trimestre - 1) * 3 + 1
            mois_fin = self.trimestre * 3
            bulletins = bulletins.filter(periode__mois__gte=mois_debut, periode__mois__lte=mois_fin)

        self.nombre_salaries = bulletins.values('employe').distinct().count()
        self.masse_salariale = sum(b.salaire_brut for b in bulletins)
        self.base_cotisable = sum(b.base_cotisable for b in bulletins)
        self.cotisations_salariales = sum(b.cnss_salariale for b in bulletins)
        self.cotisations_patronales = sum(b.cnss_patronale for b in bulletins)
        self.total_cotisations = self.cotisations_salariales + self.cotisations_patronales
        self.total_ipts = sum(b.ipts for b in bulletins)
        self.total_vps = sum(b.vps for b in bulletins)

        # Données détaillées par employé
        self.donnees = {
            'employes': [
                {
                    'matricule': b.employe.matricule,
                    'nom': b.employe.nom,
                    'prenoms': b.employe.prenoms,
                    'numero_cnss': b.employe.numero_cnss,
                    'salaire_brut': float(b.salaire_brut),
                    'base_cotisable': float(b.base_cotisable),
                    'cnss_salariale': float(b.cnss_salariale),
                    'cnss_patronale': float(b.cnss_patronale),
                    'ipts': float(b.ipts),
                }
                for b in bulletins
            ]
        }

        self.statut = 'genere'
        self.save()


# =============================================================================
# ÉVALUATIONS ET CARRIÈRE
# =============================================================================

class CritereEvaluation(models.Model):
    """Critères d'évaluation"""
    code = models.CharField(max_length=20, unique=True, verbose_name="Code")
    libelle = models.CharField(max_length=100, verbose_name="Libellé")
    description = models.TextField(blank=True, verbose_name="Description")
    coefficient = models.DecimalField(max_digits=4, decimal_places=2, default=Decimal('1'),
                                       verbose_name="Coefficient")
    actif = models.BooleanField(default=True, verbose_name="Actif")

    class Meta:
        verbose_name = "Critère d'évaluation"
        verbose_name_plural = "Critères d'évaluation"
        ordering = ['libelle']

    def __str__(self):
        return self.libelle


class Evaluation(models.Model):
    """Évaluations périodiques des employés"""
    STATUT_CHOICES = [
        ('planifiee', 'Planifiée'),
        ('en_cours', 'En cours'),
        ('terminee', 'Terminée'),
        ('validee', 'Validée'),
        ('annulee', 'Annulée'),
    ]

    employe = models.ForeignKey(Employe, on_delete=models.CASCADE,
                                 related_name='evaluations', verbose_name="Employé")
    evaluateur = models.ForeignKey(Employe, on_delete=models.SET_NULL, null=True,
                                    related_name='evaluations_realisees', verbose_name="Évaluateur")
    date_evaluation = models.DateField(verbose_name="Date d'évaluation")
    periode_debut = models.DateField(verbose_name="Début de période évaluée")
    periode_fin = models.DateField(verbose_name="Fin de période évaluée")

    # Notes
    note_globale = models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True,
                                        validators=[MinValueValidator(0), MaxValueValidator(20)],
                                        verbose_name="Note globale (/20)")

    # Commentaires
    points_forts = models.TextField(blank=True, verbose_name="Points forts")
    points_amelioration = models.TextField(blank=True, verbose_name="Points à améliorer")
    commentaire_evaluateur = models.TextField(blank=True, verbose_name="Commentaire évaluateur")
    commentaire_employe = models.TextField(blank=True, verbose_name="Commentaire employé")
    objectifs_prochaine_periode = models.TextField(blank=True, verbose_name="Objectifs prochaine période")

    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default='planifiee',
                               verbose_name="Statut")

    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Évaluation"
        verbose_name_plural = "Évaluations"
        ordering = ['-date_evaluation']

    def __str__(self):
        return f"Évaluation {self.employe.get_nom_complet()} - {self.date_evaluation}"

    def calculer_note_globale(self):
        """Calcule la note globale pondérée"""
        notes = self.notes_criteres.all()
        if not notes:
            return None

        total_pondere = sum(n.note * n.critere.coefficient for n in notes)
        total_coefficients = sum(n.critere.coefficient for n in notes)

        if total_coefficients > 0:
            self.note_globale = total_pondere / total_coefficients
            self.save()

        return self.note_globale


class NoteCritereEvaluation(models.Model):
    """Notes par critère pour une évaluation"""
    evaluation = models.ForeignKey(Evaluation, on_delete=models.CASCADE,
                                    related_name='notes_criteres', verbose_name="Évaluation")
    critere = models.ForeignKey(CritereEvaluation, on_delete=models.PROTECT,
                                 verbose_name="Critère")
    note = models.DecimalField(max_digits=4, decimal_places=2,
                                validators=[MinValueValidator(0), MaxValueValidator(20)],
                                verbose_name="Note (/20)")
    commentaire = models.TextField(blank=True, verbose_name="Commentaire")

    class Meta:
        verbose_name = "Note de critère"
        verbose_name_plural = "Notes de critères"
        unique_together = ['evaluation', 'critere']

    def __str__(self):
        return f"{self.evaluation} - {self.critere.libelle}: {self.note}"


# =============================================================================
# FORMATIONS
# =============================================================================

class Formation(models.Model):
    """Catalogue et suivi des formations"""
    TYPE_CHOICES = [
        ('interne', 'Formation interne'),
        ('externe', 'Formation externe'),
        ('en_ligne', 'Formation en ligne'),
        ('seminaire', 'Séminaire'),
        ('conference', 'Conférence'),
    ]

    STATUT_CHOICES = [
        ('planifiee', 'Planifiée'),
        ('en_cours', 'En cours'),
        ('terminee', 'Terminée'),
        ('annulee', 'Annulée'),
    ]

    intitule = models.CharField(max_length=200, verbose_name="Intitulé")
    type_formation = models.CharField(max_length=20, choices=TYPE_CHOICES,
                                        verbose_name="Type de formation")
    organisme = models.CharField(max_length=200, blank=True, verbose_name="Organisme formateur")
    formateur = models.CharField(max_length=100, blank=True, verbose_name="Formateur")
    date_debut = models.DateField(verbose_name="Date de début")
    date_fin = models.DateField(verbose_name="Date de fin")
    duree_heures = models.IntegerField(null=True, blank=True, verbose_name="Durée (heures)")
    lieu = models.CharField(max_length=200, blank=True, verbose_name="Lieu")
    cout = models.DecimalField(max_digits=12, decimal_places=0, default=0,
                                verbose_name="Coût (FCFA)")
    description = models.TextField(blank=True, verbose_name="Description")
    objectifs = models.TextField(blank=True, verbose_name="Objectifs")

    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default='planifiee',
                               verbose_name="Statut")

    date_creation = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Formation"
        verbose_name_plural = "Formations"
        ordering = ['-date_debut']

    def __str__(self):
        return f"{self.intitule} ({self.date_debut})"


class ParticipationFormation(models.Model):
    """Participation des employés aux formations"""
    STATUT_CHOICES = [
        ('inscrit', 'Inscrit'),
        ('present', 'Présent'),
        ('absent', 'Absent'),
        ('reussi', 'Réussi'),
        ('echec', 'Échec'),
    ]

    formation = models.ForeignKey(Formation, on_delete=models.CASCADE,
                                   related_name='participations', verbose_name="Formation")
    employe = models.ForeignKey(Employe, on_delete=models.CASCADE,
                                 related_name='formations_suivies', verbose_name="Employé")
    date_inscription = models.DateField(auto_now_add=True, verbose_name="Date d'inscription")
    statut = models.CharField(max_length=10, choices=STATUT_CHOICES, default='inscrit',
                               verbose_name="Statut")
    note = models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True,
                                verbose_name="Note")
    commentaire = models.TextField(blank=True, verbose_name="Commentaire")
    attestation = models.FileField(upload_to='formations/attestations/', blank=True, null=True,
                                    verbose_name="Attestation")

    class Meta:
        verbose_name = "Participation formation"
        verbose_name_plural = "Participations formations"
        unique_together = ['formation', 'employe']

    def __str__(self):
        return f"{self.employe.get_nom_complet()} - {self.formation.intitule}"


# =============================================================================
# DISCIPLINE ET SANCTIONS
# =============================================================================

class TypeSanction(models.Model):
    """Types de sanctions selon le Code du travail béninois"""
    NIVEAU_CHOICES = [
        (1, 'Niveau 1 - Avertissement'),
        (2, 'Niveau 2 - Blâme'),
        (3, 'Niveau 3 - Mise à pied'),
        (4, 'Niveau 4 - Licenciement'),
    ]

    code = models.CharField(max_length=20, unique=True, verbose_name="Code")
    libelle = models.CharField(max_length=100, verbose_name="Libellé")
    niveau = models.IntegerField(choices=NIVEAU_CHOICES, verbose_name="Niveau de gravité")
    duree_max_jours = models.IntegerField(null=True, blank=True,
                                           verbose_name="Durée max (jours) pour mise à pied")
    description = models.TextField(blank=True, verbose_name="Description")
    procedure = models.TextField(blank=True, verbose_name="Procédure à suivre")

    class Meta:
        verbose_name = "Type de sanction"
        verbose_name_plural = "Types de sanctions"
        ordering = ['niveau', 'libelle']

    def __str__(self):
        return f"{self.libelle} (Niveau {self.niveau})"


class Sanction(models.Model):
    """Sanctions disciplinaires"""
    STATUT_CHOICES = [
        ('en_cours', 'Procédure en cours'),
        ('notifiee', 'Notifiée'),
        ('executee', 'Exécutée'),
        ('annulee', 'Annulée'),
        ('contestee', 'Contestée'),
    ]

    employe = models.ForeignKey(Employe, on_delete=models.CASCADE,
                                 related_name='sanctions', verbose_name="Employé")
    type_sanction = models.ForeignKey(TypeSanction, on_delete=models.PROTECT,
                                       verbose_name="Type de sanction")
    reference = models.CharField(max_length=50, unique=True, verbose_name="Référence")
    date_faits = models.DateField(verbose_name="Date des faits")
    motif = models.TextField(verbose_name="Motif détaillé")

    # Procédure
    date_convocation = models.DateField(null=True, blank=True, verbose_name="Date de convocation")
    date_entretien = models.DateField(null=True, blank=True, verbose_name="Date de l'entretien")
    compte_rendu_entretien = models.TextField(blank=True, verbose_name="Compte-rendu entretien")

    # Décision
    date_notification = models.DateField(null=True, blank=True, verbose_name="Date de notification")
    duree_mise_pied = models.IntegerField(null=True, blank=True,
                                           verbose_name="Durée mise à pied (jours)")
    date_debut_mise_pied = models.DateField(null=True, blank=True,
                                             verbose_name="Début mise à pied")
    date_fin_mise_pied = models.DateField(null=True, blank=True,
                                           verbose_name="Fin mise à pied")

    # Réponse employé
    reponse_employe = models.TextField(blank=True, verbose_name="Réponse de l'employé")
    date_reponse_employe = models.DateField(null=True, blank=True,
                                             verbose_name="Date réponse employé")

    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default='en_cours',
                               verbose_name="Statut")

    # Documents
    lettre_convocation = models.FileField(upload_to='sanctions/convocations/', blank=True, null=True,
                                           verbose_name="Lettre de convocation")
    lettre_notification = models.FileField(upload_to='sanctions/notifications/', blank=True, null=True,
                                            verbose_name="Lettre de notification")

    decideur = models.ForeignKey('gestion.Utilisateur', on_delete=models.SET_NULL,
                                  null=True, blank=True, verbose_name="Décideur")

    date_creation = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Sanction"
        verbose_name_plural = "Sanctions"
        ordering = ['-date_faits']

    def __str__(self):
        return f"{self.reference} - {self.employe.get_nom_complet()}"

    @classmethod
    def generer_reference(cls):
        """Génère une référence unique"""
        annee = timezone.now().year
        prefix = f"SAN{annee}"
        last = cls.objects.filter(reference__startswith=prefix).order_by('-reference').first()
        if last:
            num = int(last.reference[-4:]) + 1
        else:
            num = 1
        return f"{prefix}{num:04d}"


# =============================================================================
# FIN DE CONTRAT
# =============================================================================

class FinContrat(models.Model):
    """Gestion des fins de contrat"""
    TYPE_RUPTURE_CHOICES = [
        ('demission', 'Démission'),
        ('licenciement_personnel', 'Licenciement pour motif personnel'),
        ('licenciement_economique', 'Licenciement économique'),
        ('licenciement_faute', 'Licenciement pour faute'),
        ('fin_cdd', 'Fin de CDD'),
        ('fin_essai', 'Fin de période d\'essai'),
        ('retraite', 'Départ à la retraite'),
        ('deces', 'Décès'),
        ('rupture_conventionnelle', 'Rupture conventionnelle'),
    ]

    STATUT_CHOICES = [
        ('en_cours', 'Procédure en cours'),
        ('notifie', 'Notifié'),
        ('preavis', 'En préavis'),
        ('solde', 'Soldé'),
        ('termine', 'Terminé'),
    ]

    employe = models.ForeignKey(Employe, on_delete=models.CASCADE,
                                 related_name='fins_contrat', verbose_name="Employé")
    contrat = models.ForeignKey(Contrat, on_delete=models.CASCADE,
                                 related_name='fins', verbose_name="Contrat")
    type_rupture = models.CharField(max_length=30, choices=TYPE_RUPTURE_CHOICES,
                                     verbose_name="Type de rupture")
    date_notification = models.DateField(verbose_name="Date de notification")
    date_fin_effective = models.DateField(verbose_name="Date de fin effective")
    motif = models.TextField(verbose_name="Motif")

    # Préavis
    dispense_preavis = models.BooleanField(default=False, verbose_name="Dispense de préavis")
    duree_preavis_jours = models.IntegerField(default=0, verbose_name="Durée préavis (jours)")
    date_debut_preavis = models.DateField(null=True, blank=True, verbose_name="Début préavis")
    date_fin_preavis = models.DateField(null=True, blank=True, verbose_name="Fin préavis")

    # Indemnités calculées
    indemnite_preavis = models.DecimalField(max_digits=12, decimal_places=0, default=0,
                                             verbose_name="Indemnité de préavis")
    indemnite_licenciement = models.DecimalField(max_digits=12, decimal_places=0, default=0,
                                                   verbose_name="Indemnité de licenciement")
    indemnite_conges = models.DecimalField(max_digits=12, decimal_places=0, default=0,
                                            verbose_name="Indemnité compensatrice de congés")
    prorata_13eme_mois = models.DecimalField(max_digits=12, decimal_places=0, default=0,
                                               verbose_name="Prorata 13ème mois")
    autres_indemnites = models.DecimalField(max_digits=12, decimal_places=0, default=0,
                                             verbose_name="Autres indemnités")
    total_solde_compte = models.DecimalField(max_digits=12, decimal_places=0, default=0,
                                              verbose_name="Total solde de tout compte")

    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default='en_cours',
                               verbose_name="Statut")

    # Documents
    lettre_licenciement = models.FileField(upload_to='fins_contrat/lettres/', blank=True, null=True,
                                            verbose_name="Lettre de licenciement/démission")
    certificat_travail = models.FileField(upload_to='fins_contrat/certificats/', blank=True, null=True,
                                           verbose_name="Certificat de travail")
    solde_tout_compte = models.FileField(upload_to='fins_contrat/soldes/', blank=True, null=True,
                                          verbose_name="Solde de tout compte")
    recu_solde_compte = models.FileField(upload_to='fins_contrat/recus/', blank=True, null=True,
                                          verbose_name="Reçu pour solde de tout compte")
    attestation_travail = models.FileField(upload_to='fins_contrat/attestations/', blank=True, null=True,
                                            verbose_name="Attestation de travail")

    date_creation = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Fin de contrat"
        verbose_name_plural = "Fins de contrat"
        ordering = ['-date_fin_effective']

    def __str__(self):
        return f"Fin contrat - {self.employe.get_nom_complet()} ({self.date_fin_effective})"

    def calculer_indemnites(self):
        """Calcule toutes les indemnités de fin de contrat"""
        employe = self.employe
        anciennete = employe.anciennete_annees
        salaire_mensuel = employe.salaire_base

        # Indemnité de préavis (si licenciement sans dispense)
        if not self.dispense_preavis and self.type_rupture.startswith('licenciement'):
            # Préavis selon ancienneté (Code du travail béninois)
            if anciennete < 1:
                self.duree_preavis_jours = 15
            elif anciennete < 5:
                self.duree_preavis_jours = 30
            else:
                self.duree_preavis_jours = 60

            self.indemnite_preavis = salaire_mensuel * Decimal(self.duree_preavis_jours) / 30

        # Indemnité de licenciement (selon Code du travail béninois)
        if self.type_rupture in ['licenciement_personnel', 'licenciement_economique']:
            # 30% du salaire mensuel moyen par année d'ancienneté
            self.indemnite_licenciement = salaire_mensuel * Decimal('0.30') * anciennete

        # Indemnité compensatrice de congés non pris
        try:
            solde = SoldeConge.objects.get(employe=employe, annee=timezone.now().year)
            jours_non_pris = solde.solde_disponible
            if jours_non_pris > 0:
                self.indemnite_conges = (salaire_mensuel / 26) * jours_non_pris
        except SoldeConge.DoesNotExist:
            pass

        # Total
        self.total_solde_compte = (
            self.indemnite_preavis +
            self.indemnite_licenciement +
            self.indemnite_conges +
            self.prorata_13eme_mois +
            self.autres_indemnites
        )

        self.save()


# =============================================================================
# CONFIGURATION RH
# =============================================================================

class ConfigurationRH(models.Model):
    """Configuration globale du module RH (singleton)"""
    # Paramètres généraux
    nom_entreprise = models.CharField(max_length=200, default="Étude d'Huissier",
                                       verbose_name="Nom de l'entreprise")
    adresse_entreprise = models.TextField(blank=True, verbose_name="Adresse")
    telephone_entreprise = models.CharField(max_length=20, blank=True, verbose_name="Téléphone")
    email_entreprise = models.EmailField(blank=True, verbose_name="Email")
    numero_cnss_employeur = models.CharField(max_length=30, blank=True,
                                              verbose_name="N° CNSS Employeur")
    numero_ifu_employeur = models.CharField(max_length=20, blank=True,
                                             verbose_name="N° IFU Employeur")

    # Paramètres de paie
    jour_paiement_salaire = models.IntegerField(default=28, validators=[MinValueValidator(1), MaxValueValidator(31)],
                                                  verbose_name="Jour de paiement des salaires")
    taux_risques_professionnels = models.DecimalField(max_digits=4, decimal_places=2,
                                                        default=TAUX_CNSS_PATRONAL_RISQUES_PROFESSIONNELS_MIN,
                                                        verbose_name="Taux risques professionnels (%)")
    plafond_avance_salaire = models.DecimalField(max_digits=4, decimal_places=2, default=Decimal('50'),
                                                   verbose_name="Plafond avance salaire (%)")

    # Paramètres de congés
    heure_debut_travail = models.TimeField(default=datetime.time(8, 0),
                                            verbose_name="Heure début de travail")
    heure_fin_travail = models.TimeField(default=datetime.time(17, 0),
                                          verbose_name="Heure fin de travail")
    tolerance_retard_minutes = models.IntegerField(default=15,
                                                     verbose_name="Tolérance retard (minutes)")

    # Dates limites déclarations
    date_limite_dns = models.IntegerField(default=15, verbose_name="Date limite DNS (jour du mois)")
    date_limite_ipts = models.IntegerField(default=15, verbose_name="Date limite IPTS (jour du mois)")

    est_configure = models.BooleanField(default=False, verbose_name="Configuration terminée")
    date_configuration = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "Configuration RH"
        verbose_name_plural = "Configuration RH"

    def __str__(self):
        return "Configuration RH"

    @classmethod
    def get_instance(cls):
        """Récupère ou crée l'instance unique de configuration"""
        instance, created = cls.objects.get_or_create(pk=1)
        return instance
