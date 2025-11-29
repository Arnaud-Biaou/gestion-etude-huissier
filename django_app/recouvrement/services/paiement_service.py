"""
Service de gestion des paiements de recouvrement.
Gère l'imputation automatique et manuelle selon les règles métier.
"""
from decimal import Decimal
from django.db import models, transaction
from django.utils import timezone

from recouvrement.models import (
    DossierRecouvrement,
    PaiementRecouvrement,
    ImputationManuelle,
    HistoriqueActionRecouvrement,
)
from recouvrement.services.baremes import (
    calculer_honoraires_amiable,
    calculer_emoluments_force,
    detail_calcul_droit_recette,
    BAREME_RECOUVREMENT_AMIABLE,
    BAREME_RECOUVREMENT_FORCE,
)


class ServicePaiement:
    """
    Service pour gérer les paiements et imputations sur les dossiers de recouvrement.
    """

    @staticmethod
    @transaction.atomic
    def enregistrer_paiement(
        dossier,
        montant,
        date_paiement=None,
        mode_paiement='especes',
        reference_paiement='',
        observations='',
        utilisateur=None,
        imputation_manuelle=None
    ):
        """
        Enregistre un nouveau paiement sur un dossier.

        Args:
            dossier: DossierRecouvrement
            montant: Decimal ou int
            date_paiement: date (défaut: aujourd'hui)
            mode_paiement: str
            reference_paiement: str
            observations: str
            utilisateur: User
            imputation_manuelle: dict optionnel pour forcer l'imputation
                {
                    'frais': Decimal,
                    'emoluments': Decimal,
                    'interets': Decimal,
                    'principal': Decimal,
                    'reserve': Decimal,
                    'reverser': Decimal,
                }

        Returns:
            PaiementRecouvrement créé
        """
        if date_paiement is None:
            date_paiement = timezone.now().date()

        montant = Decimal(str(montant))

        # Créer le paiement
        paiement = PaiementRecouvrement(
            dossier=dossier,
            date_paiement=date_paiement,
            montant=montant,
            mode_paiement=mode_paiement,
            reference_paiement=reference_paiement,
            observations=observations,
            cree_par=utilisateur,
        )

        # Si imputation manuelle fournie
        if imputation_manuelle:
            paiement.impute_frais = Decimal(str(imputation_manuelle.get('frais', 0)))
            paiement.impute_emoluments = Decimal(str(imputation_manuelle.get('emoluments', 0)))
            paiement.impute_interets = Decimal(str(imputation_manuelle.get('interets', 0)))
            paiement.impute_principal = Decimal(str(imputation_manuelle.get('principal', 0)))
            paiement.montant_reserve = Decimal(str(imputation_manuelle.get('reserve', 0)))
            paiement.montant_a_reverser = Decimal(str(imputation_manuelle.get('reverser', 0)))

        paiement.save()

        # Mettre à jour les totaux du dossier
        dossier.actualiser_imputations()

        # Enregistrer dans l'historique
        HistoriqueActionRecouvrement.objects.create(
            dossier=dossier,
            type_action='paiement',
            description=f"Paiement de {montant:,.0f} FCFA reçu ({paiement.get_mode_paiement_display()})",
            paiement_lie=paiement,
            cree_par=utilisateur,
        )

        return paiement

    @staticmethod
    @transaction.atomic
    def imputer_montant_reserve(
        paiement,
        type_imputation,
        montant,
        observations='',
        utilisateur=None
    ):
        """
        Impute manuellement un montant réservé.

        Args:
            paiement: PaiementRecouvrement avec montant_reserve > 0
            type_imputation: 'frais', 'emoluments', 'interets', 'principal'
            montant: Decimal
            observations: str
            utilisateur: User

        Returns:
            ImputationManuelle créée
        """
        montant = Decimal(str(montant))

        if montant > paiement.montant_reserve:
            raise ValueError(
                f"Montant {montant:,.0f} supérieur au montant réservé {paiement.montant_reserve:,.0f}"
            )

        # Créer l'imputation manuelle
        imputation = ImputationManuelle.objects.create(
            paiement=paiement,
            type_imputation=type_imputation,
            montant=montant,
            observations=observations,
            cree_par=utilisateur,
        )

        # La mise à jour du paiement est faite dans le save() de ImputationManuelle

        # Mettre à jour les totaux du dossier
        paiement.dossier.actualiser_imputations()

        # Historique
        HistoriqueActionRecouvrement.objects.create(
            dossier=paiement.dossier,
            type_action='autre',
            description=f"Imputation manuelle de {montant:,.0f} FCFA sur {type_imputation}",
            paiement_lie=paiement,
            cree_par=utilisateur,
        )

        return imputation

    @staticmethod
    @transaction.atomic
    def effectuer_reversement(
        paiement,
        date_reversement=None,
        reference_reversement='',
        utilisateur=None
    ):
        """
        Marque un paiement comme reversé au créancier.

        Args:
            paiement: PaiementRecouvrement
            date_reversement: date
            reference_reversement: str
            utilisateur: User

        Returns:
            PaiementRecouvrement mis à jour
        """
        if paiement.est_reverse:
            raise ValueError("Ce paiement a déjà été reversé")

        if paiement.montant_a_reverser <= 0:
            raise ValueError("Aucun montant à reverser pour ce paiement")

        if date_reversement is None:
            date_reversement = timezone.now().date()

        paiement.est_reverse = True
        paiement.date_reversement = date_reversement
        paiement.reference_reversement = reference_reversement
        paiement.save()

        # Mettre à jour le total reversé du dossier
        dossier = paiement.dossier
        dossier.total_reverse = dossier.paiements.filter(est_reverse=True).aggregate(
            total=models.Sum('montant_a_reverser')
        )['total'] or 0
        dossier.save()

        # Historique
        HistoriqueActionRecouvrement.objects.create(
            dossier=dossier,
            type_action='reversement',
            description=f"Reversement de {paiement.montant_a_reverser:,.0f} FCFA au créancier",
            paiement_lie=paiement,
            cree_par=utilisateur,
        )

        return paiement

    @staticmethod
    def calculer_situation_dossier(dossier):
        """
        Calcule la situation complète d'un dossier de recouvrement.

        Returns:
            dict avec tous les montants et états
        """
        # Recalculer les émoluments selon le type de recouvrement
        if dossier.type_recouvrement == 'force':
            emoluments_montant = calculer_emoluments_force(float(dossier.montant_principal))
            detail_emoluments = detail_calcul_droit_recette(
                float(dossier.montant_principal),
                BAREME_RECOUVREMENT_FORCE,
                "Recouvrement forcé"
            )
        else:
            emoluments_montant = calculer_honoraires_amiable(float(dossier.montant_principal))
            detail_emoluments = detail_calcul_droit_recette(
                float(dossier.montant_principal),
                BAREME_RECOUVREMENT_AMIABLE,
                "Recouvrement amiable"
            )

        # Agrégation des paiements
        paiements = dossier.paiements.all()
        total_paye = sum(p.montant for p in paiements)
        total_impute_frais = sum(p.impute_frais for p in paiements)
        total_impute_emoluments = sum(p.impute_emoluments for p in paiements)
        total_impute_interets = sum(p.impute_interets for p in paiements)
        total_impute_principal = sum(p.impute_principal for p in paiements)
        total_reserve = sum(p.montant_reserve for p in paiements)
        total_a_reverser = sum(p.montant_a_reverser for p in paiements if not p.est_reverse)
        total_reverse = sum(p.montant_a_reverser for p in paiements if p.est_reverse)

        return {
            # Montants dus
            'principal_du': dossier.montant_principal,
            'interets_dus': dossier.montant_interets,
            'frais_engages': dossier.frais_engages,
            'emoluments_calcules': emoluments_montant,

            # Montants imputés
            'frais_imputes': total_impute_frais,
            'emoluments_imputes': total_impute_emoluments,
            'interets_imputes': total_impute_interets,
            'principal_impute': total_impute_principal,

            # Soldes restants
            'frais_restants': max(0, dossier.frais_engages - total_impute_frais),
            'emoluments_restants': max(0, emoluments_montant - total_impute_emoluments),
            'interets_restants': max(0, dossier.montant_interets - total_impute_interets),
            'principal_restant': max(0, dossier.montant_principal - total_impute_principal),

            # Totaux
            'total_paye': total_paye,
            'total_reserve': total_reserve,
            'total_a_reverser': total_a_reverser,
            'total_reverse': total_reverse,

            # Détail émoluments
            'detail_emoluments': detail_emoluments,

            # État
            'est_solde': (
                dossier.montant_principal - total_impute_principal <= 0 and
                dossier.montant_interets - total_impute_interets <= 0
            ),
            'mode_facturation': dossier.mode_facturation,
            'type_recouvrement': dossier.type_recouvrement,
        }

    @staticmethod
    def generer_rapport_paiements(dossier):
        """
        Génère un rapport détaillé des paiements pour un dossier.

        Returns:
            dict avec l'historique et les totaux
        """
        paiements = dossier.paiements.all().order_by('date_paiement')

        historique = []
        cumul_frais = Decimal('0')
        cumul_emoluments = Decimal('0')
        cumul_interets = Decimal('0')
        cumul_principal = Decimal('0')

        for p in paiements:
            cumul_frais += p.impute_frais
            cumul_emoluments += p.impute_emoluments
            cumul_interets += p.impute_interets
            cumul_principal += p.impute_principal

            historique.append({
                'date': p.date_paiement,
                'montant': p.montant,
                'mode': p.get_mode_paiement_display(),
                'reference': p.reference_paiement,
                'imputation': {
                    'frais': p.impute_frais,
                    'emoluments': p.impute_emoluments,
                    'interets': p.impute_interets,
                    'principal': p.impute_principal,
                    'reserve': p.montant_reserve,
                    'reverser': p.montant_a_reverser,
                },
                'cumuls': {
                    'frais': cumul_frais,
                    'emoluments': cumul_emoluments,
                    'interets': cumul_interets,
                    'principal': cumul_principal,
                },
                'est_reverse': p.est_reverse,
                'date_reversement': p.date_reversement,
            })

        return {
            'dossier': dossier,
            'historique': historique,
            'totaux': {
                'paye': sum(p.montant for p in paiements),
                'impute_frais': cumul_frais,
                'impute_emoluments': cumul_emoluments,
                'impute_interets': cumul_interets,
                'impute_principal': cumul_principal,
                'reserve': sum(p.montant_reserve for p in paiements),
                'reverse': sum(p.montant_a_reverser for p in paiements if p.est_reverse),
                'a_reverser': sum(p.montant_a_reverser for p in paiements if not p.est_reverse),
            },
        }
