"""
Modèles du module Trésorerie
Gestion complète de la trésorerie d'une étude d'huissier
"""

from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from decimal import Decimal
import uuid

User = get_user_model()


class CompteBancaire(models.Model):
    """Compte bancaire de l'étude"""
    TYPES_COMPTE = [
        ('courant', 'Compte Courant'),
        ('epargne', 'Compte Épargne'),
        ('sequestre', 'Compte Séquestre'),
        ('caisse', 'Caisse'),
    ]

    STATUTS = [
        ('actif', 'Actif'),
        ('inactif', 'Inactif'),
        ('cloture', 'Clôturé'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    nom = models.CharField(max_length=100, verbose_name='Nom du compte')
    numero = models.CharField(max_length=50, verbose_name='Numéro de compte')
    banque = models.CharField(max_length=100, verbose_name='Banque')
    type_compte = models.CharField(max_length=20, choices=TYPES_COMPTE, default='courant')
    devise = models.CharField(max_length=3, default='XOF', verbose_name='Devise')
    solde_initial = models.DecimalField(max_digits=15, decimal_places=2, default=0, verbose_name='Solde initial')
    solde_actuel = models.DecimalField(max_digits=15, decimal_places=2, default=0, verbose_name='Solde actuel')
    seuil_alerte = models.DecimalField(max_digits=15, decimal_places=2, default=100000, verbose_name='Seuil alerte')
    statut = models.CharField(max_length=20, choices=STATUTS, default='actif')
    iban = models.CharField(max_length=34, blank=True, null=True, verbose_name='IBAN')
    bic = models.CharField(max_length=11, blank=True, null=True, verbose_name='BIC')
    contact_banque = models.CharField(max_length=200, blank=True, null=True, verbose_name='Contact banque')
    date_ouverture = models.DateField(default=timezone.now, verbose_name='Date ouverture')
    date_cloture = models.DateField(blank=True, null=True, verbose_name='Date clôture')
    notes = models.TextField(blank=True, null=True, verbose_name='Notes')
    cree_le = models.DateTimeField(auto_now_add=True)
    modifie_le = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Compte bancaire'
        verbose_name_plural = 'Comptes bancaires'
        ordering = ['nom']

    def __str__(self):
        return f"{self.nom} - {self.banque}"

    def recalculer_solde(self):
        """Recalcule le solde actuel basé sur les mouvements"""
        mouvements = self.mouvements.filter(statut='valide')
        entrees = mouvements.filter(type_mouvement='entree').aggregate(
            total=models.Sum('montant'))['total'] or Decimal('0')
        sorties = mouvements.filter(type_mouvement='sortie').aggregate(
            total=models.Sum('montant'))['total'] or Decimal('0')
        self.solde_actuel = self.solde_initial + entrees - sorties
        self.save()
        return self.solde_actuel


class MouvementTresorerie(models.Model):
    """Mouvement de trésorerie (entrée ou sortie)"""
    TYPES_MOUVEMENT = [
        ('entree', 'Entrée'),
        ('sortie', 'Sortie'),
    ]

    CATEGORIES = [
        ('encaissement', 'Encaissement client'),
        ('reversement', 'Reversement créancier'),
        ('honoraires', 'Honoraires'),
        ('frais_acte', 'Frais d\'acte'),
        ('salaire', 'Salaire'),
        ('loyer', 'Loyer'),
        ('charges', 'Charges'),
        ('impot', 'Impôt et taxes'),
        ('fournitures', 'Fournitures'),
        ('transport', 'Transport'),
        ('virement_interne', 'Virement interne'),
        ('autre', 'Autre'),
    ]

    MODES_PAIEMENT = [
        ('especes', 'Espèces'),
        ('cheque', 'Chèque'),
        ('virement', 'Virement'),
        ('carte', 'Carte bancaire'),
        ('mobile_money', 'Mobile Money'),
        ('prelevement', 'Prélèvement'),
    ]

    STATUTS = [
        ('en_attente', 'En attente'),
        ('valide', 'Validé'),
        ('annule', 'Annulé'),
        ('rapproche', 'Rapproché'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    compte = models.ForeignKey(CompteBancaire, on_delete=models.PROTECT, related_name='mouvements')
    type_mouvement = models.CharField(max_length=10, choices=TYPES_MOUVEMENT)
    categorie = models.CharField(max_length=30, choices=CATEGORIES, default='autre')
    montant = models.DecimalField(max_digits=15, decimal_places=2)
    date_mouvement = models.DateField(default=timezone.now, verbose_name='Date du mouvement')
    date_valeur = models.DateField(blank=True, null=True, verbose_name='Date de valeur')
    libelle = models.CharField(max_length=255, verbose_name='Libellé')
    reference = models.CharField(max_length=100, blank=True, null=True, verbose_name='Référence')
    mode_paiement = models.CharField(max_length=20, choices=MODES_PAIEMENT, default='virement')

    # Liens vers d'autres entités
    dossier_id = models.IntegerField(blank=True, null=True, verbose_name='ID Dossier')
    facture_id = models.IntegerField(blank=True, null=True, verbose_name='ID Facture')

    tiers = models.CharField(max_length=200, blank=True, null=True, verbose_name='Tiers')
    numero_piece = models.CharField(max_length=50, blank=True, null=True, verbose_name='N° pièce')
    numero_cheque = models.CharField(max_length=50, blank=True, null=True, verbose_name='N° chèque')

    statut = models.CharField(max_length=20, choices=STATUTS, default='en_attente')
    notes = models.TextField(blank=True, null=True)

    cree_par = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='mouvements_crees')
    valide_par = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='mouvements_valides')
    date_validation = models.DateTimeField(blank=True, null=True)

    cree_le = models.DateTimeField(auto_now_add=True)
    modifie_le = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Mouvement de trésorerie'
        verbose_name_plural = 'Mouvements de trésorerie'
        ordering = ['-date_mouvement', '-cree_le']

    def __str__(self):
        signe = '+' if self.type_mouvement == 'entree' else '-'
        return f"{signe}{self.montant} XOF - {self.libelle}"

    def valider(self, utilisateur):
        """Valide le mouvement et met à jour le solde du compte"""
        self.statut = 'valide'
        self.valide_par = utilisateur
        self.date_validation = timezone.now()
        self.save()
        self.compte.recalculer_solde()


class RapprochementBancaire(models.Model):
    """Rapprochement bancaire mensuel"""
    STATUTS = [
        ('en_cours', 'En cours'),
        ('termine', 'Terminé'),
        ('valide', 'Validé'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    compte = models.ForeignKey(CompteBancaire, on_delete=models.PROTECT, related_name='rapprochements')
    date_debut = models.DateField(verbose_name='Date début période')
    date_fin = models.DateField(verbose_name='Date fin période')

    solde_releve = models.DecimalField(max_digits=15, decimal_places=2, verbose_name='Solde relevé bancaire')
    solde_comptable = models.DecimalField(max_digits=15, decimal_places=2, verbose_name='Solde comptable')
    ecart = models.DecimalField(max_digits=15, decimal_places=2, default=0, verbose_name='Écart')

    mouvements_rapproches = models.ManyToManyField(MouvementTresorerie, related_name='rapprochements', blank=True)

    statut = models.CharField(max_length=20, choices=STATUTS, default='en_cours')
    notes = models.TextField(blank=True, null=True)

    cree_par = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='rapprochements_crees')
    valide_par = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='rapprochements_valides')
    date_validation = models.DateTimeField(blank=True, null=True)

    cree_le = models.DateTimeField(auto_now_add=True)
    modifie_le = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Rapprochement bancaire'
        verbose_name_plural = 'Rapprochements bancaires'
        ordering = ['-date_fin']

    def __str__(self):
        return f"Rapprochement {self.compte.nom} - {self.date_fin.strftime('%m/%Y')}"

    def calculer_ecart(self):
        """Calcule l'écart entre le solde relevé et le solde comptable"""
        self.ecart = self.solde_releve - self.solde_comptable
        self.save()
        return self.ecart


class PrevisionTresorerie(models.Model):
    """Prévision de trésorerie"""
    TYPES = [
        ('entree', 'Entrée prévue'),
        ('sortie', 'Sortie prévue'),
    ]

    PERIODICITES = [
        ('unique', 'Unique'),
        ('hebdomadaire', 'Hebdomadaire'),
        ('mensuel', 'Mensuel'),
        ('trimestriel', 'Trimestriel'),
        ('annuel', 'Annuel'),
    ]

    STATUTS = [
        ('prevue', 'Prévue'),
        ('realisee', 'Réalisée'),
        ('annulee', 'Annulée'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    compte = models.ForeignKey(CompteBancaire, on_delete=models.CASCADE, related_name='previsions')
    type_prevision = models.CharField(max_length=10, choices=TYPES)
    libelle = models.CharField(max_length=255)
    montant = models.DecimalField(max_digits=15, decimal_places=2)
    date_prevue = models.DateField(verbose_name='Date prévue')
    periodicite = models.CharField(max_length=20, choices=PERIODICITES, default='unique')
    categorie = models.CharField(max_length=30, choices=MouvementTresorerie.CATEGORIES, default='autre')

    mouvement_realise = models.ForeignKey(MouvementTresorerie, on_delete=models.SET_NULL,
                                          null=True, blank=True, related_name='prevision_source')

    statut = models.CharField(max_length=20, choices=STATUTS, default='prevue')
    notes = models.TextField(blank=True, null=True)

    cree_par = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    cree_le = models.DateTimeField(auto_now_add=True)
    modifie_le = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Prévision de trésorerie'
        verbose_name_plural = 'Prévisions de trésorerie'
        ordering = ['date_prevue']

    def __str__(self):
        return f"{self.libelle} - {self.montant} XOF le {self.date_prevue}"


class AlerteTresorerie(models.Model):
    """Alerte de trésorerie"""
    TYPES_ALERTE = [
        ('seuil_bas', 'Seuil bas atteint'),
        ('echeance', 'Échéance proche'),
        ('anomalie', 'Anomalie détectée'),
        ('rapprochement', 'Rapprochement requis'),
    ]

    NIVEAUX = [
        ('info', 'Information'),
        ('warning', 'Avertissement'),
        ('danger', 'Critique'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    compte = models.ForeignKey(CompteBancaire, on_delete=models.CASCADE, related_name='alertes', null=True, blank=True)
    type_alerte = models.CharField(max_length=20, choices=TYPES_ALERTE)
    niveau = models.CharField(max_length=10, choices=NIVEAUX, default='warning')
    message = models.TextField()
    lue = models.BooleanField(default=False)
    traitee = models.BooleanField(default=False)
    date_traitement = models.DateTimeField(blank=True, null=True)
    traite_par = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)

    cree_le = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Alerte trésorerie'
        verbose_name_plural = 'Alertes trésorerie'
        ordering = ['-cree_le']

    def __str__(self):
        return f"{self.get_type_alerte_display()} - {self.message[:50]}"
