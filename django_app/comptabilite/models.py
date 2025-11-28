from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError
from django.utils import timezone
from decimal import Decimal
import datetime


class ExerciceComptable(models.Model):
    """Exercice comptable (année fiscale)"""
    STATUT_CHOICES = [
        ('ouvert', 'Ouvert'),
        ('cloture', 'Clôturé'),
    ]

    libelle = models.CharField(max_length=100, verbose_name="Libellé")
    date_debut = models.DateField(verbose_name="Date de début")
    date_fin = models.DateField(verbose_name="Date de fin")
    statut = models.CharField(max_length=10, choices=STATUT_CHOICES, default='ouvert', verbose_name="Statut")
    est_premier_exercice = models.BooleanField(default=False, verbose_name="Premier exercice")
    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Exercice comptable"
        verbose_name_plural = "Exercices comptables"
        ordering = ['-date_debut']

    def __str__(self):
        return f"{self.libelle} ({self.date_debut.year})"

    def clean(self):
        if self.date_fin <= self.date_debut:
            raise ValidationError("La date de fin doit être postérieure à la date de début")

    @property
    def est_actif(self):
        """Vérifie si l'exercice est actuellement actif"""
        today = timezone.now().date()
        return self.statut == 'ouvert' and self.date_debut <= today <= self.date_fin

    @classmethod
    def get_exercice_courant(cls):
        """Retourne l'exercice comptable en cours"""
        today = timezone.now().date()
        return cls.objects.filter(
            statut='ouvert',
            date_debut__lte=today,
            date_fin__gte=today
        ).first()


class CompteComptable(models.Model):
    """Plan comptable OHADA (SYSCOHADA)"""
    CLASSE_CHOICES = [
        ('1', 'Classe 1 - Capitaux'),
        ('2', 'Classe 2 - Immobilisations'),
        ('3', 'Classe 3 - Stocks'),
        ('4', 'Classe 4 - Tiers'),
        ('5', 'Classe 5 - Trésorerie'),
        ('6', 'Classe 6 - Charges'),
        ('7', 'Classe 7 - Produits'),
        ('8', 'Classe 8 - Autres charges/produits'),
        ('9', 'Classe 9 - Engagements hors bilan'),
    ]

    TYPE_CHOICES = [
        ('general', 'Compte général'),
        ('auxiliaire', 'Compte auxiliaire'),
    ]

    SOLDE_NORMAL_CHOICES = [
        ('debiteur', 'Débiteur'),
        ('crediteur', 'Créditeur'),
    ]

    numero = models.CharField(max_length=20, unique=True, verbose_name="N° de compte")
    libelle = models.CharField(max_length=200, verbose_name="Libellé")
    classe = models.CharField(max_length=1, choices=CLASSE_CHOICES, verbose_name="Classe")
    type_compte = models.CharField(max_length=20, choices=TYPE_CHOICES, default='general', verbose_name="Type")
    solde_normal = models.CharField(max_length=10, choices=SOLDE_NORMAL_CHOICES, verbose_name="Solde normal")
    compte_parent = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True,
                                       related_name='sous_comptes', verbose_name="Compte parent")
    actif = models.BooleanField(default=True, verbose_name="Actif")
    description = models.TextField(blank=True, verbose_name="Description/Aide")
    date_creation = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Compte comptable"
        verbose_name_plural = "Comptes comptables"
        ordering = ['numero']

    def __str__(self):
        return f"{self.numero} - {self.libelle}"

    def save(self, *args, **kwargs):
        # Déterminer automatiquement la classe à partir du numéro
        if self.numero:
            self.classe = self.numero[0]
        super().save(*args, **kwargs)

    @property
    def est_compte_de_bilan(self):
        """Classes 1 à 5 sont des comptes de bilan"""
        return self.classe in ['1', '2', '3', '4', '5']

    @property
    def est_compte_de_gestion(self):
        """Classes 6 et 7 sont des comptes de gestion"""
        return self.classe in ['6', '7']

    def get_solde(self, exercice=None, date_debut=None, date_fin=None):
        """Calcule le solde du compte pour une période donnée"""
        lignes = LigneEcriture.objects.filter(
            compte=self,
            ecriture__statut='valide'
        )

        if exercice:
            lignes = lignes.filter(
                ecriture__date__gte=exercice.date_debut,
                ecriture__date__lte=exercice.date_fin
            )
        elif date_debut and date_fin:
            lignes = lignes.filter(
                ecriture__date__gte=date_debut,
                ecriture__date__lte=date_fin
            )

        total_debit = lignes.aggregate(total=models.Sum('debit'))['total'] or Decimal('0')
        total_credit = lignes.aggregate(total=models.Sum('credit'))['total'] or Decimal('0')

        return total_debit - total_credit


class Journal(models.Model):
    """Journaux comptables"""
    TYPE_CHOICES = [
        ('AC', 'Achats'),
        ('VE', 'Ventes'),
        ('BQ', 'Banque'),
        ('CA', 'Caisse'),
        ('OD', 'Opérations diverses'),
        ('AN', 'À nouveau'),
        ('CL', 'Clôture'),
    ]

    code = models.CharField(max_length=5, unique=True, verbose_name="Code")
    libelle = models.CharField(max_length=100, verbose_name="Libellé")
    type_journal = models.CharField(max_length=2, choices=TYPE_CHOICES, verbose_name="Type")
    compte_contrepartie = models.ForeignKey(CompteComptable, on_delete=models.SET_NULL,
                                             null=True, blank=True, verbose_name="Compte de contrepartie")
    actif = models.BooleanField(default=True, verbose_name="Actif")
    description = models.TextField(blank=True, verbose_name="Description")

    class Meta:
        verbose_name = "Journal"
        verbose_name_plural = "Journaux"
        ordering = ['code']

    def __str__(self):
        return f"{self.code} - {self.libelle}"


class EcritureComptable(models.Model):
    """Écriture comptable (en-tête)"""
    STATUT_CHOICES = [
        ('brouillon', 'Brouillon'),
        ('valide', 'Validée'),
        ('annulee', 'Annulée'),
    ]

    ORIGINE_CHOICES = [
        ('manuelle', 'Saisie manuelle'),
        ('facture', 'Facture'),
        ('tresorerie', 'Trésorerie'),
        ('automatique', 'Automatique'),
        ('cloture', 'Clôture'),
    ]

    numero = models.CharField(max_length=20, unique=True, verbose_name="N° pièce")
    date = models.DateField(verbose_name="Date")
    journal = models.ForeignKey(Journal, on_delete=models.PROTECT, verbose_name="Journal")
    exercice = models.ForeignKey(ExerciceComptable, on_delete=models.PROTECT, verbose_name="Exercice")
    libelle = models.CharField(max_length=200, verbose_name="Libellé")
    reference = models.CharField(max_length=100, blank=True, verbose_name="Référence externe")
    statut = models.CharField(max_length=10, choices=STATUT_CHOICES, default='brouillon', verbose_name="Statut")
    origine = models.CharField(max_length=15, choices=ORIGINE_CHOICES, default='manuelle', verbose_name="Origine")

    # Lien avec d'autres modules
    facture = models.ForeignKey('gestion.Facture', on_delete=models.SET_NULL, null=True, blank=True,
                                 related_name='ecritures_comptables', verbose_name="Facture liée")
    dossier = models.ForeignKey('gestion.Dossier', on_delete=models.SET_NULL, null=True, blank=True,
                                 related_name='ecritures_comptables', verbose_name="Dossier lié")

    # Audit
    cree_par = models.ForeignKey('gestion.Utilisateur', on_delete=models.SET_NULL, null=True,
                                  related_name='ecritures_creees', verbose_name="Créé par")
    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)
    date_validation = models.DateTimeField(null=True, blank=True, verbose_name="Date de validation")

    class Meta:
        verbose_name = "Écriture comptable"
        verbose_name_plural = "Écritures comptables"
        ordering = ['-date', '-numero']

    def __str__(self):
        return f"{self.numero} - {self.libelle} ({self.date})"

    def clean(self):
        # Vérifier que la date est dans l'exercice
        if self.exercice and (self.date < self.exercice.date_debut or self.date > self.exercice.date_fin):
            raise ValidationError("La date de l'écriture doit être comprise dans l'exercice")

        # Vérifier que l'exercice est ouvert
        if self.exercice and self.exercice.statut != 'ouvert':
            raise ValidationError("Impossible de créer une écriture dans un exercice clôturé")

    @property
    def total_debit(self):
        return self.lignes.aggregate(total=models.Sum('debit'))['total'] or Decimal('0')

    @property
    def total_credit(self):
        return self.lignes.aggregate(total=models.Sum('credit'))['total'] or Decimal('0')

    @property
    def est_equilibree(self):
        return self.total_debit == self.total_credit

    def valider(self):
        """Valide l'écriture si elle est équilibrée"""
        if not self.est_equilibree:
            raise ValidationError(f"L'écriture n'est pas équilibrée (Débit: {self.total_debit}, Crédit: {self.total_credit})")
        self.statut = 'valide'
        self.date_validation = timezone.now()
        self.save()

    @classmethod
    def generer_numero(cls, journal, date):
        """Génère un numéro d'écriture unique"""
        annee = date.year
        mois = date.month
        prefix = f"{journal.code}{annee}{mois:02d}"

        last_ecriture = cls.objects.filter(numero__startswith=prefix).order_by('-numero').first()
        if last_ecriture:
            last_num = int(last_ecriture.numero[-4:])
            new_num = last_num + 1
        else:
            new_num = 1

        return f"{prefix}{new_num:04d}"


class LigneEcriture(models.Model):
    """Ligne d'écriture comptable"""
    ecriture = models.ForeignKey(EcritureComptable, on_delete=models.CASCADE,
                                  related_name='lignes', verbose_name="Écriture")
    compte = models.ForeignKey(CompteComptable, on_delete=models.PROTECT, verbose_name="Compte")
    libelle = models.CharField(max_length=200, verbose_name="Libellé")
    debit = models.DecimalField(max_digits=15, decimal_places=0, default=0, verbose_name="Débit")
    credit = models.DecimalField(max_digits=15, decimal_places=0, default=0, verbose_name="Crédit")

    # Analytique (optionnel)
    tiers = models.CharField(max_length=200, blank=True, verbose_name="Tiers")

    class Meta:
        verbose_name = "Ligne d'écriture"
        verbose_name_plural = "Lignes d'écriture"
        ordering = ['id']

    def __str__(self):
        return f"{self.compte.numero} - {self.libelle}"

    def clean(self):
        # Une ligne doit avoir soit un débit, soit un crédit, pas les deux
        if self.debit > 0 and self.credit > 0:
            raise ValidationError("Une ligne ne peut pas avoir à la fois un débit et un crédit")
        if self.debit == 0 and self.credit == 0:
            raise ValidationError("Une ligne doit avoir soit un débit, soit un crédit")


class Lettrage(models.Model):
    """Lettrage des comptes tiers (clients 411, fournisseurs 401)"""
    code = models.CharField(max_length=10, unique=True, verbose_name="Code lettrage")
    compte = models.ForeignKey(CompteComptable, on_delete=models.PROTECT,
                               verbose_name="Compte lettré",
                               limit_choices_to={'numero__startswith': '4'})
    lignes = models.ManyToManyField(LigneEcriture, related_name='lettrages',
                                     verbose_name="Lignes lettrées")
    date_lettrage = models.DateTimeField(auto_now_add=True, verbose_name="Date de lettrage")
    lettre_par = models.ForeignKey('gestion.Utilisateur', on_delete=models.SET_NULL,
                                    null=True, verbose_name="Lettré par")
    montant = models.DecimalField(max_digits=15, decimal_places=0, default=0,
                                   verbose_name="Montant lettré")
    est_partiel = models.BooleanField(default=False, verbose_name="Lettrage partiel")
    commentaire = models.TextField(blank=True, verbose_name="Commentaire")

    class Meta:
        verbose_name = "Lettrage"
        verbose_name_plural = "Lettrages"
        ordering = ['-date_lettrage']

    def __str__(self):
        return f"Lettrage {self.code} - {self.compte.numero}"

    def clean(self):
        # Vérifier que le lettrage est équilibré (sauf si partiel)
        if not self.est_partiel and self.pk:
            total_debit = self.lignes.aggregate(total=models.Sum('debit'))['total'] or Decimal('0')
            total_credit = self.lignes.aggregate(total=models.Sum('credit'))['total'] or Decimal('0')
            if total_debit != total_credit:
                raise ValidationError(
                    f"Le lettrage n'est pas équilibré: Débit={total_debit}, Crédit={total_credit}"
                )

    @classmethod
    def generer_code(cls, compte):
        """Génère un code de lettrage unique pour un compte"""
        import string
        # Format: 3 lettres + numéro séquentiel (ex: AAA001)
        last_lettrage = cls.objects.filter(compte=compte).order_by('-code').first()
        if last_lettrage:
            last_code = last_lettrage.code
            # Extraire les lettres et le numéro
            letters = last_code[:3]
            num = int(last_code[3:]) + 1
            if num > 999:
                # Passer aux lettres suivantes
                num = 1
                # Incrémenter les lettres
                letter_list = list(letters)
                for i in range(2, -1, -1):
                    if letter_list[i] != 'Z':
                        letter_list[i] = chr(ord(letter_list[i]) + 1)
                        break
                    else:
                        letter_list[i] = 'A'
                letters = ''.join(letter_list)
            return f"{letters}{num:03d}"
        return "AAA001"

    @classmethod
    def creer_lettrage(cls, compte, lignes, utilisateur=None, commentaire=''):
        """Crée un lettrage pour un ensemble de lignes d'écriture"""
        # Vérifier que toutes les lignes appartiennent au même compte
        for ligne in lignes:
            if ligne.compte != compte:
                raise ValidationError(f"La ligne {ligne} n'appartient pas au compte {compte}")

        # Calculer le montant total
        total_debit = sum(l.debit for l in lignes)
        total_credit = sum(l.credit for l in lignes)
        est_partiel = total_debit != total_credit
        montant = min(total_debit, total_credit)

        # Créer le lettrage
        code = cls.generer_code(compte)
        lettrage = cls.objects.create(
            code=code,
            compte=compte,
            montant=montant,
            est_partiel=est_partiel,
            lettre_par=utilisateur,
            commentaire=commentaire
        )
        lettrage.lignes.set(lignes)
        return lettrage


class TypeOperation(models.Model):
    """Types d'opérations pour le mode facile"""
    code = models.CharField(max_length=20, unique=True, verbose_name="Code")
    libelle = models.CharField(max_length=200, verbose_name="Libellé")
    description = models.TextField(verbose_name="Description pour l'utilisateur")
    icone = models.CharField(max_length=50, default='file-text', verbose_name="Icône Lucide")
    journal = models.ForeignKey(Journal, on_delete=models.PROTECT, verbose_name="Journal")
    compte_debit = models.ForeignKey(CompteComptable, on_delete=models.PROTECT,
                                      related_name='operations_debit', verbose_name="Compte à débiter")
    compte_credit = models.ForeignKey(CompteComptable, on_delete=models.PROTECT,
                                       related_name='operations_credit', verbose_name="Compte à créditer")
    ordre_affichage = models.IntegerField(default=0, verbose_name="Ordre d'affichage")
    actif = models.BooleanField(default=True, verbose_name="Actif")

    class Meta:
        verbose_name = "Type d'opération"
        verbose_name_plural = "Types d'opérations"
        ordering = ['ordre_affichage', 'libelle']

    def __str__(self):
        return self.libelle


class ParametrageFiscal(models.Model):
    """Paramètres fiscaux de l'étude"""
    exercice = models.OneToOneField(ExerciceComptable, on_delete=models.CASCADE,
                                     related_name='parametres_fiscaux', verbose_name="Exercice")

    # TVA
    taux_tva = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('18.00'),
                                    verbose_name="Taux de TVA (%)")
    periodicite_declaration_tva = models.CharField(max_length=20,
                                                    choices=[('mensuel', 'Mensuel'), ('trimestriel', 'Trimestriel')],
                                                    default='mensuel', verbose_name="Périodicité déclaration TVA")

    # Comptes TVA
    compte_tva_collectee = models.ForeignKey(CompteComptable, on_delete=models.PROTECT,
                                              related_name='+', null=True, blank=True,
                                              verbose_name="Compte TVA collectée")
    compte_tva_deductible = models.ForeignKey(CompteComptable, on_delete=models.PROTECT,
                                               related_name='+', null=True, blank=True,
                                               verbose_name="Compte TVA déductible")
    compte_tva_a_payer = models.ForeignKey(CompteComptable, on_delete=models.PROTECT,
                                            related_name='+', null=True, blank=True,
                                            verbose_name="Compte TVA à payer")

    # Autres paramètres
    seuil_paiement_especes = models.DecimalField(max_digits=15, decimal_places=0,
                                                  default=Decimal('100000'),
                                                  verbose_name="Seuil paiement espèces (FCFA)")

    class Meta:
        verbose_name = "Paramétrage fiscal"
        verbose_name_plural = "Paramétrages fiscaux"

    def __str__(self):
        return f"Paramètres fiscaux {self.exercice}"


class DeclarationTVA(models.Model):
    """Déclarations de TVA"""
    STATUT_CHOICES = [
        ('brouillon', 'Brouillon'),
        ('validee', 'Validée'),
        ('declaree', 'Déclarée'),
        ('payee', 'Payée'),
    ]

    exercice = models.ForeignKey(ExerciceComptable, on_delete=models.PROTECT, verbose_name="Exercice")
    periode_debut = models.DateField(verbose_name="Début de période")
    periode_fin = models.DateField(verbose_name="Fin de période")

    # Montants calculés
    tva_collectee = models.DecimalField(max_digits=15, decimal_places=0, default=0, verbose_name="TVA collectée")
    tva_deductible = models.DecimalField(max_digits=15, decimal_places=0, default=0, verbose_name="TVA déductible")
    tva_a_payer = models.DecimalField(max_digits=15, decimal_places=0, default=0, verbose_name="TVA à payer")
    credit_tva = models.DecimalField(max_digits=15, decimal_places=0, default=0, verbose_name="Crédit de TVA")

    statut = models.CharField(max_length=10, choices=STATUT_CHOICES, default='brouillon', verbose_name="Statut")
    date_declaration = models.DateField(null=True, blank=True, verbose_name="Date de déclaration")
    date_paiement = models.DateField(null=True, blank=True, verbose_name="Date de paiement")

    date_creation = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Déclaration TVA"
        verbose_name_plural = "Déclarations TVA"
        ordering = ['-periode_debut']

    def __str__(self):
        return f"TVA {self.periode_debut.strftime('%m/%Y')}"

    def calculer(self):
        """Calcule les montants de TVA pour la période"""
        from django.db.models import Sum

        # Récupérer les paramètres fiscaux
        params = self.exercice.parametres_fiscaux

        if params.compte_tva_collectee:
            lignes_collectee = LigneEcriture.objects.filter(
                compte=params.compte_tva_collectee,
                ecriture__statut='valide',
                ecriture__date__gte=self.periode_debut,
                ecriture__date__lte=self.periode_fin
            )
            self.tva_collectee = lignes_collectee.aggregate(total=Sum('credit'))['total'] or 0

        if params.compte_tva_deductible:
            lignes_deductible = LigneEcriture.objects.filter(
                compte=params.compte_tva_deductible,
                ecriture__statut='valide',
                ecriture__date__gte=self.periode_debut,
                ecriture__date__lte=self.periode_fin
            )
            self.tva_deductible = lignes_deductible.aggregate(total=Sum('debit'))['total'] or 0

        diff = self.tva_collectee - self.tva_deductible
        if diff > 0:
            self.tva_a_payer = diff
            self.credit_tva = 0
        else:
            self.tva_a_payer = 0
            self.credit_tva = abs(diff)

        self.save()


class RapportComptable(models.Model):
    """Rapports comptables générés"""
    TYPE_CHOICES = [
        ('bilan', 'Bilan'),
        ('resultat', 'Compte de résultat'),
        ('grand_livre', 'Grand livre'),
        ('balance', 'Balance'),
        ('journal', 'Journal'),
        ('flux_tresorerie', 'Flux de trésorerie'),
    ]

    exercice = models.ForeignKey(ExerciceComptable, on_delete=models.CASCADE, verbose_name="Exercice")
    type_rapport = models.CharField(max_length=20, choices=TYPE_CHOICES, verbose_name="Type")
    date_generation = models.DateTimeField(auto_now_add=True, verbose_name="Date de génération")
    periode_debut = models.DateField(verbose_name="Début de période")
    periode_fin = models.DateField(verbose_name="Fin de période")
    donnees = models.JSONField(verbose_name="Données du rapport")
    genere_par = models.ForeignKey('gestion.Utilisateur', on_delete=models.SET_NULL, null=True,
                                    verbose_name="Généré par")

    class Meta:
        verbose_name = "Rapport comptable"
        verbose_name_plural = "Rapports comptables"
        ordering = ['-date_generation']

    def __str__(self):
        return f"{self.get_type_rapport_display()} - {self.periode_fin}"


class ConfigurationComptable(models.Model):
    """Configuration globale du module comptabilité (singleton)"""
    est_configure = models.BooleanField(default=False, verbose_name="Configuration terminée")
    date_configuration = models.DateTimeField(null=True, blank=True, verbose_name="Date de configuration")

    # Comptes par défaut
    compte_banque_principal = models.ForeignKey(CompteComptable, on_delete=models.SET_NULL,
                                                 null=True, blank=True, related_name='+',
                                                 verbose_name="Compte banque principal")
    compte_caisse = models.ForeignKey(CompteComptable, on_delete=models.SET_NULL,
                                       null=True, blank=True, related_name='+',
                                       verbose_name="Compte caisse")
    compte_honoraires = models.ForeignKey(CompteComptable, on_delete=models.SET_NULL,
                                           null=True, blank=True, related_name='+',
                                           verbose_name="Compte honoraires")
    compte_clients = models.ForeignKey(CompteComptable, on_delete=models.SET_NULL,
                                        null=True, blank=True, related_name='+',
                                        verbose_name="Compte clients")
    compte_fournisseurs = models.ForeignKey(CompteComptable, on_delete=models.SET_NULL,
                                             null=True, blank=True, related_name='+',
                                             verbose_name="Compte fournisseurs")

    mode_saisie_defaut = models.CharField(max_length=10,
                                           choices=[('facile', 'Facile'), ('guide', 'Guidé'), ('expert', 'Expert')],
                                           default='facile', verbose_name="Mode de saisie par défaut")

    class Meta:
        verbose_name = "Configuration comptable"
        verbose_name_plural = "Configuration comptable"

    def __str__(self):
        return "Configuration comptable"

    @classmethod
    def get_instance(cls):
        """Récupère ou crée l'instance unique de configuration"""
        instance, created = cls.objects.get_or_create(pk=1)
        return instance
