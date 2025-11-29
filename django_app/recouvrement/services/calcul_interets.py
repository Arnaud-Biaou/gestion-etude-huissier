"""
Calculateur d'intérêts conforme aux règles OHADA et Loi béninoise 2024-10

Règles de calcul :
- Dies a quo (jour de départ) : COMPTE
- Dies ad quem (jour d'échéance) : NE COMPTE PAS
- Base : 365 jours (année civile) par défaut, 360 pour conventions bancaires
- Majoration 50% après 2 mois si décision de justice exécutoire (Loi 2024-10, Art. 3)
"""

from decimal import Decimal, ROUND_HALF_UP
from datetime import date, timedelta
from parametres.models import TauxLegal


class CalculateurInteretsOHADA:
    """
    Calculateur d'intérêts conforme aux règles OHADA et Loi béninoise 2024-10
    """

    def __init__(self, base_calcul=365):
        """
        Args:
            base_calcul: 365 (année civile) ou 360 (usage bancaire)
        """
        self.base_calcul = base_calcul

    def compter_jours(self, date_debut, date_fin):
        """
        Compte les jours selon les règles OHADA :
        - Dies a quo (jour de départ) : COMPTE
        - Dies ad quem (jour d'échéance) : NE COMPTE PAS
        """
        if date_fin <= date_debut:
            return 0
        # Le jour de départ compte, le jour de fin ne compte pas
        # Donc c'est simplement la différence
        return (date_fin - date_debut).days

    def calculer_interets_periode(self, principal, taux_annuel, date_debut, date_fin):
        """
        Calcule les intérêts pour une période donnée

        Args:
            principal: Montant en principal (Decimal ou int)
            taux_annuel: Taux annuel en pourcentage (ex: 5.5 pour 5,5%)
            date_debut: Date de début (incluse)
            date_fin: Date de fin (exclue)

        Returns:
            Decimal: Montant des intérêts
        """
        principal = Decimal(str(principal))
        taux = Decimal(str(taux_annuel)) / Decimal('100')
        nb_jours = self.compter_jours(date_debut, date_fin)

        interets = principal * taux * Decimal(str(nb_jours)) / Decimal(str(self.base_calcul))
        return interets.quantize(Decimal('1'), rounding=ROUND_HALF_UP)

    def calculer_interets_multi_annees(self, principal, date_debut, date_fin, taux_fixes=None):
        """
        Calcule les intérêts sur plusieurs années avec taux variables

        Args:
            principal: Montant en principal
            date_debut: Date de début
            date_fin: Date de fin
            taux_fixes: Dict {année: taux} ou None pour utiliser taux légaux

        Returns:
            dict: {
                'total': montant total des intérêts,
                'detail': [{annee, jours, taux, interets}, ...]
            }
        """
        if date_fin <= date_debut:
            return {'total': Decimal('0'), 'detail': []}

        detail = []
        total = Decimal('0')
        principal = Decimal(str(principal))

        # Parcourir chaque année
        annee_debut = date_debut.year
        annee_fin = date_fin.year

        for annee in range(annee_debut, annee_fin + 1):
            # Déterminer les bornes pour cette année
            debut_annee = max(date_debut, date(annee, 1, 1))
            fin_annee = min(date_fin, date(annee + 1, 1, 1))

            if fin_annee <= debut_annee:
                continue

            # Obtenir le taux
            if taux_fixes and annee in taux_fixes:
                taux = Decimal(str(taux_fixes[annee]))
            else:
                taux = TauxLegal.get_taux_annee(annee)

            # Calculer les intérêts pour cette période
            nb_jours = self.compter_jours(debut_annee, fin_annee)
            interets = principal * (taux / Decimal('100')) * Decimal(str(nb_jours)) / Decimal(str(self.base_calcul))
            interets = interets.quantize(Decimal('1'), rounding=ROUND_HALF_UP)

            detail.append({
                'annee': annee,
                'date_debut': debut_annee,
                'date_fin': fin_annee,
                'jours': nb_jours,
                'taux': taux,
                'interets': interets
            })
            total += interets

        return {'total': total, 'detail': detail}

    def calculer_avec_majoration(self, principal, date_debut, date_fin, date_decision_executoire=None):
        """
        Calcule les intérêts avec majoration de 50% après 2 mois
        (Loi 2024-10, Article 3)

        Args:
            principal: Montant en principal
            date_debut: Date de début des intérêts
            date_fin: Date de calcul
            date_decision_executoire: Date où la décision est devenue exécutoire

        Returns:
            dict: {
                'interets_normaux': montant,
                'interets_majores': montant,
                'total': montant,
                'detail': [...]
            }
        """
        result = {
            'interets_normaux': Decimal('0'),
            'interets_majores': Decimal('0'),
            'total': Decimal('0'),
            'detail': []
        }

        if date_decision_executoire is None:
            # Pas de majoration, calcul normal
            calcul = self.calculer_interets_multi_annees(principal, date_debut, date_fin)
            result['interets_normaux'] = calcul['total']
            result['total'] = calcul['total']
            result['detail'] = calcul['detail']
            return result

        # Date de début de majoration : 2 mois après décision exécutoire
        date_majoration = date_decision_executoire + timedelta(days=60)  # Approximation 2 mois

        if date_fin <= date_majoration:
            # Pas encore de majoration
            calcul = self.calculer_interets_multi_annees(principal, date_debut, date_fin)
            result['interets_normaux'] = calcul['total']
            result['total'] = calcul['total']
            result['detail'] = calcul['detail']
        else:
            # Période sans majoration
            if date_debut < date_majoration:
                calcul_normal = self.calculer_interets_multi_annees(principal, date_debut, date_majoration)
                result['interets_normaux'] = calcul_normal['total']
                result['detail'].extend(calcul_normal['detail'])

            # Période avec majoration (taux × 1.5)
            calcul_majore = self.calculer_interets_multi_annees(principal, date_majoration, date_fin)
            # Appliquer la majoration de 50%
            interets_majores = (calcul_majore['total'] * Decimal('1.5')).quantize(Decimal('1'), rounding=ROUND_HALF_UP)
            result['interets_majores'] = interets_majores

            for item in calcul_majore['detail']:
                item['majore'] = True
                item['taux_majore'] = item['taux'] * Decimal('1.5')
                item['interets_majores'] = (item['interets'] * Decimal('1.5')).quantize(Decimal('1'), rounding=ROUND_HALF_UP)
            result['detail'].extend(calcul_majore['detail'])

            result['total'] = result['interets_normaux'] + result['interets_majores']

        return result

    def calculer_interets_a_echoir(self, principal, taux_annuel, nb_jours=30):
        """
        Calcule les intérêts à échoir (pour saisie-attribution, délai 1 mois)
        Conformément à l'OHADA

        Args:
            principal: Montant en principal
            taux_annuel: Taux applicable
            nb_jours: Nombre de jours (30 par défaut pour 1 mois)

        Returns:
            Decimal: Montant des intérêts à échoir
        """
        principal = Decimal(str(principal))
        taux = Decimal(str(taux_annuel)) / Decimal('100')

        interets = principal * taux * Decimal(str(nb_jours)) / Decimal(str(self.base_calcul))
        return interets.quantize(Decimal('1'), rounding=ROUND_HALF_UP)


def generer_decompte_ohada(creance):
    """
    Génère un décompte conforme aux exigences OHADA (Articles 92, 153, 184)

    Mentions obligatoires :
    - Principal
    - Frais
    - Intérêts échus (avec détail par période)
    - Taux des intérêts
    - Pour saisie-attribution : intérêts à échoir (1 mois)
    """
    calculateur = CalculateurInteretsOHADA()

    # Calcul des intérêts
    calcul = calculateur.calculer_avec_majoration(
        principal=creance.montant_principal,
        date_debut=creance.date_effet_interets,
        date_fin=date.today(),
        date_decision_executoire=getattr(creance, 'date_decision_executoire', None)
    )

    # Intérêts à échoir (pour saisie-attribution)
    taux_actuel = TauxLegal.get_taux_annee(date.today().year)
    interets_a_echoir = calculateur.calculer_interets_a_echoir(
        principal=creance.montant_principal,
        taux_annuel=taux_actuel,
        nb_jours=30
    )

    frais_totaux = getattr(creance, 'frais_totaux', 0) or 0

    decompte = {
        'date_decompte': date.today(),
        'principal': creance.montant_principal,
        'frais': frais_totaux,
        'interets_echus': calcul['total'],
        'detail_interets': calcul['detail'],
        'interets_a_echoir': interets_a_echoir,
        'taux_actuel': taux_actuel,
        'total_general': creance.montant_principal + frais_totaux + calcul['total'],
        'total_avec_echoir': creance.montant_principal + frais_totaux + calcul['total'] + interets_a_echoir,
    }

    return decompte
