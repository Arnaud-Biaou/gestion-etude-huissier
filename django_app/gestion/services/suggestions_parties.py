"""
Service de suggestions pour les parties.
NE MODIFIE RIEN - Fournit uniquement des suggestions à valider manuellement.
"""
import re
from difflib import SequenceMatcher
from django.db import models


# Formes juridiques reconnues
FORMES_JURIDIQUES = {
    'SA': ['S.A.', 'S.A', 'SA.', 'SOCIETE ANONYME', 'SOCIÉTÉ ANONYME'],
    'SARL': ['S.A.R.L.', 'S.A.R.L', 'SARL.', 'SOCIETE A RESPONSABILITE LIMITEE'],
    'SAS': ['S.A.S.', 'S.A.S', 'SAS.'],
    'SARLU': ['S.A.R.L.U.', 'SARLU.', 'SARL UNIPERSONNELLE'],
    'SNC': ['S.N.C.', 'S.N.C', 'SNC.'],
    'ETS': ['ETS.', 'ETABLISSEMENT', 'ETABLISSEMENTS', 'Ets'],
    'GIE': ['G.I.E.', 'GIE.'],
}

# Préfixes souvent redondants
PREFIXES_REDONDANTS = [
    'SOCIETE', 'SOCIÉTÉ', 'ENTREPRISE', 'ETABLISSEMENT',
    'ETS', 'STE', 'STÉ', 'LA SOCIETE', 'LA SOCIÉTÉ',
]

# Corrections connues (banques, grandes entreprises)
CORRECTIONS_CONNUES = {
    'BANK OF AFRICA': 'BOA',
    'BANK OF AFRICA BENIN': 'BOA BÉNIN',
    'BANK OF AFRICA BÉNIN': 'BOA BÉNIN',
    'BANQUE OF AFRICA': 'BOA',
    'ECOBANK TRANSNATIONAL INCORPORATED': 'ECOBANK',
    'UNITED BANK FOR AFRICA': 'UBA',
}


def suggerer_normalisation(nom, forme_juridique_actuelle=None):
    """
    Suggère une normalisation du nom d'une partie.
    NE MODIFIE RIEN - Retourne uniquement une suggestion.

    Retourne: {
        'nom_original': str,
        'nom_suggere': str,
        'forme_juridique_detectee': str ou None,
        'modifications': list[str],  # Liste des modifications suggérées
        'a_corriger': bool,
    }
    """
    if not nom:
        return None

    nom_original = nom
    nom_travail = nom.strip().upper()
    modifications = []
    forme_detectee = None

    # 1. Vérifier les corrections connues
    for ancien, nouveau in CORRECTIONS_CONNUES.items():
        if ancien.upper() in nom_travail:
            nom_travail = nom_travail.replace(ancien.upper(), nouveau)
            modifications.append(f"Correction connue: {ancien} → {nouveau}")

    # 2. Extraire la forme juridique si elle est dans le nom
    for forme_standard, variantes in FORMES_JURIDIQUES.items():
        for variante in [forme_standard] + variantes:
            variante_upper = variante.upper()
            if nom_travail.endswith(' ' + variante_upper) or nom_travail.endswith(variante_upper):
                nom_travail = nom_travail.replace(variante_upper, '').strip()
                forme_detectee = forme_standard
                modifications.append(f"Forme juridique extraite du nom: {variante} → champ séparé")
                break
            if nom_travail.startswith(variante_upper + ' '):
                nom_travail = nom_travail.replace(variante_upper + ' ', '', 1).strip()
                forme_detectee = forme_standard
                modifications.append(f"Forme juridique extraite du nom: {variante} → champ séparé")
                break
        if forme_detectee:
            break

    # 3. Supprimer les préfixes redondants
    for prefixe in PREFIXES_REDONDANTS:
        if nom_travail.startswith(prefixe.upper() + ' '):
            nom_travail = nom_travail[len(prefixe):].strip()
            modifications.append(f"Préfixe redondant supprimé: {prefixe}")

    # 4. Nettoyer espaces et caractères
    nom_travail = re.sub(r'\s+', ' ', nom_travail).strip(' .,;:-')

    # 5. Normaliser BENIN → BÉNIN
    if 'BENIN' in nom_travail and 'BÉNIN' not in nom_travail:
        nom_travail = nom_travail.replace('BENIN', 'BÉNIN')
        modifications.append("Accent ajouté: BENIN → BÉNIN")

    a_corriger = len(modifications) > 0 or nom_travail != nom_original.upper()

    return {
        'nom_original': nom_original,
        'nom_suggere': nom_travail,
        'forme_juridique_detectee': forme_detectee,
        'forme_juridique_actuelle': forme_juridique_actuelle,
        'modifications': modifications,
        'a_corriger': a_corriger,
    }


def calculer_similarite(nom1, nom2):
    """Calcule un score de similarité entre deux noms (0 à 1)"""
    if not nom1 or not nom2:
        return 0
    return SequenceMatcher(None, nom1.upper().strip(), nom2.upper().strip()).ratio()


def rechercher_parties_similaires(nom_recherche, partie_model, seuil=0.80, limite=10):
    """
    Recherche des parties similaires dans la base.
    Pour l'autocomplétion et la détection de doublons.

    Retourne une liste de tuples (partie, score_similarite)
    """
    if not nom_recherche or len(nom_recherche) < 2:
        return []

    nom_recherche = nom_recherche.upper().strip()
    resultats = []

    # Recherche par correspondance exacte partielle d'abord
    parties_exactes = partie_model.objects.filter(
        models.Q(raison_sociale__icontains=nom_recherche) |
        models.Q(nom__icontains=nom_recherche)
    )[:limite]

    for partie in parties_exactes:
        nom_partie = partie.raison_sociale or partie.nom or ''
        score = calculer_similarite(nom_recherche, nom_partie)
        resultats.append((partie, score))

    # Si peu de résultats, chercher par similarité
    if len(resultats) < limite:
        toutes_parties = partie_model.objects.exclude(
            pk__in=[p.pk for p, _ in resultats]
        )[:200]  # Limiter pour performance

        for partie in toutes_parties:
            nom_partie = partie.raison_sociale or partie.nom or ''
            score = calculer_similarite(nom_recherche, nom_partie)
            if score >= seuil:
                resultats.append((partie, score))

    # Trier par score décroissant
    resultats.sort(key=lambda x: x[1], reverse=True)

    return resultats[:limite]


def detecter_doublons_potentiels(partie_model, seuil=0.85):
    """
    Détecte les doublons potentiels dans la base.
    NE MODIFIE RIEN - Retourne uniquement un rapport.
    """
    parties_pm = partie_model.objects.filter(est_personne_morale=True)
    groupes_doublons = []
    parties_vues = set()

    for partie in parties_pm:
        if partie.pk in parties_vues:
            continue

        nom = partie.raison_sociale or partie.nom or ''
        if not nom:
            continue

        # Chercher des similaires
        similaires = []
        for autre in parties_pm:
            if autre.pk == partie.pk or autre.pk in parties_vues:
                continue

            autre_nom = autre.raison_sociale or autre.nom or ''
            score = calculer_similarite(nom, autre_nom)

            if score >= seuil:
                similaires.append({'partie': autre, 'score': score})
                parties_vues.add(autre.pk)

        if similaires:
            groupes_doublons.append({
                'reference': partie,
                'similaires': similaires,
            })

        parties_vues.add(partie.pk)

    return groupes_doublons


def verifier_dossier_existant(demandeurs_ids, defendeurs_ids, dossier_model):
    """
    Vérifie si un dossier avec les mêmes parties existe déjà.
    NE BLOQUE PAS - Retourne uniquement une information.
    """
    if not demandeurs_ids and not defendeurs_ids:
        return []

    dossiers_similaires = []

    # Chercher des dossiers avec au moins un demandeur ET un défendeur en commun
    dossiers = dossier_model.objects.all()

    for dossier in dossiers:
        demandeurs_dossier = set(dossier.demandeurs.values_list('pk', flat=True))
        defendeurs_dossier = set(dossier.defendeurs.values_list('pk', flat=True))

        demandeurs_communs = demandeurs_dossier.intersection(set(demandeurs_ids))
        defendeurs_communs = defendeurs_dossier.intersection(set(defendeurs_ids))

        # Si au moins un demandeur ET un défendeur en commun
        if demandeurs_communs and defendeurs_communs:
            dossiers_similaires.append({
                'dossier': dossier,
                'demandeurs_communs': len(demandeurs_communs),
                'defendeurs_communs': len(defendeurs_communs),
            })

    return dossiers_similaires
