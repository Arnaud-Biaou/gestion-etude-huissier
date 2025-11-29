"""
Barèmes de recouvrement conformes au Décret 2017-066 du Bénin

BARÈME RECOUVREMENT AMIABLE (Article 1er - Décret 2017-066)
- Droit de recette à la charge du CRÉANCIER

BARÈME RECOUVREMENT FORCÉ (Article 2 - Décret 2017-066)
- Droit de recette à la charge du DÉBITEUR (sauf disposition contraire)
"""

from decimal import Decimal


# BARÈME RECOUVREMENT AMIABLE (Article 1er - Décret 2017-066)
# Droit de recette à la charge du CRÉANCIER
BAREME_RECOUVREMENT_AMIABLE = [
    (5_000_000, Decimal('0.10')),      # 0 à 5 000 000 : 10%
    (20_000_000, Decimal('0.08')),     # 5 000 001 à 20 000 000 : 8%
    (50_000_000, Decimal('0.06')),     # 20 000 001 à 50 000 000 : 6%
    (None, Decimal('0.04')),           # Au-delà de 50 000 000 : 4%
]

# BARÈME RECOUVREMENT FORCÉ (Article 2 - Décret 2017-066)
# Droit de recette à la charge du DÉBITEUR (sauf disposition contraire)
BAREME_RECOUVREMENT_FORCE = [
    (5_000_000, Decimal('0.10')),      # 0 à 5 000 000 : 10%
    (20_000_000, Decimal('0.035')),    # 5 000 001 à 20 000 000 : 3,5%
    (50_000_000, Decimal('0.02')),     # 20 000 001 à 50 000 000 : 2%
    (None, Decimal('0.01')),           # Au-delà de 50 000 000 : 1%
]

# DROIT DE RECETTE COMPLÉMENTAIRE (si démarches réitérées, à la charge du créancier)
# Même barème que le recouvrement forcé
BAREME_DROIT_COMPLEMENTAIRE = BAREME_RECOUVREMENT_FORCE


def calculer_droit_recette(montant, bareme):
    """
    Calcule le droit de recette proportionnel dégressif HT
    selon le barème applicable (amiable ou forcé)

    Args:
        montant: Montant de la créance à recouvrer
        bareme: Liste des tranches [(seuil, taux), ...]

    Returns:
        Decimal: Montant du droit de recette HT (arrondi à l'entier)
    """
    droit = Decimal('0')
    reste = Decimal(str(montant))
    seuil_precedent = Decimal('0')

    for seuil, taux in bareme:
        if seuil is None:
            # Dernière tranche (au-delà)
            droit += reste * taux
            break

        tranche = min(reste, Decimal(str(seuil)) - seuil_precedent)
        if tranche > 0:
            droit += tranche * taux
            reste -= tranche
            seuil_precedent = Decimal(str(seuil))

        if reste <= 0:
            break

    return droit.quantize(Decimal('1'))  # Arrondi à l'entier


def calculer_honoraires_amiable(montant):
    """
    Calcule les honoraires de recouvrement amiable
    à la charge du CRÉANCIER

    Args:
        montant: Montant de la créance

    Returns:
        Decimal: Montant des honoraires HT
    """
    return calculer_droit_recette(montant, BAREME_RECOUVREMENT_AMIABLE)


def calculer_emoluments_force(montant):
    """
    Calcule les émoluments de recouvrement forcé
    à la charge du DÉBITEUR (sauf disposition contraire)

    Args:
        montant: Montant de la créance

    Returns:
        Decimal: Montant des émoluments HT
    """
    return calculer_droit_recette(montant, BAREME_RECOUVREMENT_FORCE)


def calculer_droit_complementaire(montant):
    """
    Calcule le droit de recette complémentaire
    (si démarches réitérées, à la charge du créancier)

    Args:
        montant: Montant de la créance

    Returns:
        Decimal: Montant du droit complémentaire HT
    """
    return calculer_droit_recette(montant, BAREME_DROIT_COMPLEMENTAIRE)


def detail_calcul_droit_recette(montant, bareme, type_bareme="recouvrement"):
    """
    Retourne le détail du calcul du droit de recette par tranche

    Args:
        montant: Montant de la créance
        bareme: Liste des tranches [(seuil, taux), ...]
        type_bareme: Type de barème pour l'affichage

    Returns:
        dict: {
            'total': montant total,
            'detail': [{
                'tranche_min': min,
                'tranche_max': max ou None,
                'taux': taux en %,
                'montant_tranche': montant dans la tranche,
                'droit': droit calculé pour cette tranche
            }, ...]
        }
    """
    detail = []
    total = Decimal('0')
    reste = Decimal(str(montant))
    seuil_precedent = Decimal('0')

    for seuil, taux in bareme:
        if reste <= 0:
            break

        if seuil is None:
            # Dernière tranche
            montant_tranche = reste
            droit_tranche = (reste * taux).quantize(Decimal('1'))
            detail.append({
                'tranche_min': int(seuil_precedent) + 1 if seuil_precedent > 0 else 0,
                'tranche_max': None,  # Au-delà
                'taux': float(taux * 100),
                'montant_tranche': int(montant_tranche),
                'droit': int(droit_tranche)
            })
            total += droit_tranche
            break

        tranche = min(reste, Decimal(str(seuil)) - seuil_precedent)
        if tranche > 0:
            droit_tranche = (tranche * taux).quantize(Decimal('1'))
            detail.append({
                'tranche_min': int(seuil_precedent) + 1 if seuil_precedent > 0 else 0,
                'tranche_max': int(seuil),
                'taux': float(taux * 100),
                'montant_tranche': int(tranche),
                'droit': int(droit_tranche)
            })
            total += droit_tranche
            reste -= tranche
            seuil_precedent = Decimal(str(seuil))

    return {
        'montant_creance': int(montant),
        'type_bareme': type_bareme,
        'total': int(total),
        'detail': detail
    }
