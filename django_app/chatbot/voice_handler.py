"""
Gestionnaire de commandes vocales en francais.
Section 18 DSTD v3.2 - Exigence 2: "Commandes vocales en francais"

Fonctionnalites:
- Interface avec Web Speech API (cote client)
- Normalisation des transcriptions
- Gestion des homophones francais
- Validation du score de confiance
"""

import re
from decimal import Decimal
from django.utils import timezone


# =============================================================================
# CONFIGURATION
# =============================================================================

# Seuil de confiance minimum pour accepter une transcription
SEUIL_CONFIANCE_DEFAUT = 0.70

# Langue par defaut
LANGUE_DEFAUT = 'fr-FR'


# =============================================================================
# CORRECTIONS D'HOMOPHONES FRANCAIS
# =============================================================================

# Homophones courants dans le contexte comptable/juridique
HOMOPHONES = {
    # Comptabilite
    'conte': 'compte',
    'contes': 'comptes',
    'comptes': 'compte',
    'balance generale': 'balance generale',
    'bail lance': 'balance',

    # Montants
    'sans': 'cent',
    'sang': 'cent',
    'mille': '1000',
    'un million': '1000000',
    'deux mille': '2000',
    'dix mille': '10000',
    'cent mille': '100000',

    # Juridique
    'mer': 'maire',
    'mise and demeure': 'mise en demeure',
    'command man': 'commandement',
    'huissier': 'huissier',
    'hussier': 'huissier',

    # Actions
    'encaisse': 'encaisser',
    'en caisse et': 'encaisser',
    'an caisse': 'encaisser',
    'decaisse': 'decaisser',
    'des caisse': 'decaisser',

    # Dates
    'au jour dui': "aujourd'hui",
    'au jourdui': "aujourd'hui",
    'de main': 'demain',
}


# =============================================================================
# NORMALISATION DES NOMBRES VOCAUX
# =============================================================================

NOMBRES_TEXTE = {
    'zero': '0',
    'un': '1', 'une': '1',
    'deux': '2',
    'trois': '3',
    'quatre': '4',
    'cinq': '5',
    'six': '6',
    'sept': '7',
    'huit': '8',
    'neuf': '9',
    'dix': '10',
    'onze': '11',
    'douze': '12',
    'treize': '13',
    'quatorze': '14',
    'quinze': '15',
    'seize': '16',
    'dix-sept': '17', 'dix sept': '17',
    'dix-huit': '18', 'dix huit': '18',
    'dix-neuf': '19', 'dix neuf': '19',
    'vingt': '20',
    'trente': '30',
    'quarante': '40',
    'cinquante': '50',
    'soixante': '60',
    'soixante-dix': '70', 'soixante dix': '70',
    'quatre-vingt': '80', 'quatre vingt': '80', 'quatre-vingts': '80',
    'quatre-vingt-dix': '90', 'quatre vingt dix': '90',
    'cent': '100',
    'mille': '1000',
    'million': '1000000',
    'milliard': '1000000000',
}


def convertir_nombre_vocal(texte):
    """
    Convertit les nombres ecrits en toutes lettres en chiffres.
    Ex: "deux cent cinquante mille" -> "250000"
    """
    texte = texte.lower()

    # Remplacements simples
    for mot, chiffre in NOMBRES_TEXTE.items():
        texte = re.sub(r'\b' + mot + r'\b', chiffre, texte)

    # Gerer les compositions
    pattern_compose = r'(\d+)\s*(mille|million|milliard)'

    def remplacer_compose(match):
        nombre = int(match.group(1))
        unite = match.group(2)
        multiplicateur = {'mille': 1000, 'million': 1000000, 'milliard': 1000000000}
        return str(nombre * multiplicateur.get(unite, 1))

    texte = re.sub(pattern_compose, remplacer_compose, texte)

    return texte


# =============================================================================
# NORMALISATION DES TRANSCRIPTIONS
# =============================================================================

def normaliser_transcription(transcription):
    """
    Normalise une transcription vocale.

    Args:
        transcription: Texte brut de la transcription

    Returns:
        str: Transcription normalisee
    """
    if not transcription:
        return ""

    texte = transcription.strip().lower()

    # Corriger les homophones
    for erreur, correction in HOMOPHONES.items():
        texte = re.sub(r'\b' + re.escape(erreur) + r'\b', correction, texte, flags=re.IGNORECASE)

    # Convertir les nombres vocaux
    texte = convertir_nombre_vocal(texte)

    # Normaliser les espaces
    texte = re.sub(r'\s+', ' ', texte).strip()

    # Capitaliser la premiere lettre
    if texte:
        texte = texte[0].upper() + texte[1:]

    return texte


def extraire_nombres_vocaux(texte):
    """
    Extrait tous les nombres d'une transcription vocale.

    Returns:
        list: Liste de nombres (Decimal)
    """
    texte_normalise = convertir_nombre_vocal(texte.lower())
    nombres = re.findall(r'\d+(?:[,\.]\d+)?', texte_normalise)

    resultats = []
    for n in nombres:
        try:
            n = n.replace(',', '.')
            resultats.append(Decimal(n))
        except:
            pass

    return resultats


# =============================================================================
# VALIDATION DES TRANSCRIPTIONS
# =============================================================================

def valider_transcription(transcription, confiance, seuil=SEUIL_CONFIANCE_DEFAUT):
    """
    Valide une transcription vocale.

    Args:
        transcription: Texte de la transcription
        confiance: Score de confiance (0-1)
        seuil: Seuil minimum de confiance

    Returns:
        tuple: (est_valide, message, transcription_normalisee)
    """
    if not transcription or not transcription.strip():
        return False, "Transcription vide", ""

    if confiance < seuil:
        transcription_norm = normaliser_transcription(transcription)
        return False, f"Confiance insuffisante ({confiance:.0%}). Avez-vous dit: \"{transcription_norm}\"?", transcription_norm

    transcription_norm = normaliser_transcription(transcription)

    # Verifier la longueur minimale
    if len(transcription_norm) < 2:
        return False, "Message trop court", transcription_norm

    return True, "OK", transcription_norm


# =============================================================================
# COMMANDES VOCALES PREDEFINIES
# =============================================================================

# Commandes vocales courtes reconnues
COMMANDES_RAPIDES = {
    # Navigation
    'accueil': {'action': 'navigation', 'destination': 'dashboard'},
    'tableau de bord': {'action': 'navigation', 'destination': 'dashboard'},
    'dossiers': {'action': 'navigation', 'destination': 'dossiers'},
    'factures': {'action': 'navigation', 'destination': 'facturation'},
    'comptabilite': {'action': 'navigation', 'destination': 'comptabilite'},
    'tresorerie': {'action': 'navigation', 'destination': 'tresorerie'},
    'agenda': {'action': 'navigation', 'destination': 'agenda'},
    'parametres': {'action': 'navigation', 'destination': 'parametres'},

    # Actions rapides
    'aide': {'action': 'aide'},
    'annuler': {'action': 'annulation'},
    'confirmer': {'action': 'confirmation', 'confirme': True},
    'oui': {'action': 'confirmation', 'confirme': True},
    'non': {'action': 'confirmation', 'confirme': False},
    'refuser': {'action': 'confirmation', 'confirme': False},

    # Requetes courantes
    'solde caisse': {'action': 'tresorerie_solde'},
    'solde banque': {'action': 'tresorerie_solde'},
    'balance': {'action': 'compta_balance'},
    "aujourd'hui": {'action': 'agenda_aujourdhui'},
    'programme': {'action': 'agenda_aujourdhui'},
}


def detecter_commande_rapide(transcription):
    """
    Detecte si la transcription correspond a une commande rapide.

    Returns:
        dict ou None: La commande si detectee, None sinon
    """
    texte = transcription.lower().strip()

    # Correspondance exacte
    if texte in COMMANDES_RAPIDES:
        return COMMANDES_RAPIDES[texte]

    # Correspondance partielle
    for commande, action in COMMANDES_RAPIDES.items():
        if commande in texte:
            return action

    return None


# =============================================================================
# FEEDBACK ET AMELIORATION
# =============================================================================

def enregistrer_correction(commande_vocale, correction_utilisateur):
    """
    Enregistre une correction utilisateur pour amelioration future.

    Args:
        commande_vocale: Instance CommandeVocale
        correction_utilisateur: Texte corrige par l'utilisateur
    """
    commande_vocale.transcription_correcte = False
    commande_vocale.correction_utilisateur = correction_utilisateur
    commande_vocale.save()


def calculer_taux_reconnaissance(utilisateur=None, periode_jours=30):
    """
    Calcule le taux de reconnaissance vocale reussie.

    Args:
        utilisateur: Filtrer par utilisateur (optionnel)
        periode_jours: Periode d'analyse en jours

    Returns:
        float: Taux de reconnaissance (0-1)
    """
    from chatbot.models import CommandeVocale
    from django.db.models import Avg, Count

    date_debut = timezone.now() - timezone.timedelta(days=periode_jours)

    queryset = CommandeVocale.objects.filter(date_creation__gte=date_debut)

    if utilisateur:
        queryset = queryset.filter(message__session__utilisateur=utilisateur)

    stats = queryset.aggregate(
        total=Count('id'),
        correctes=Count('id', filter={'transcription_correcte': True}),
        score_moyen=Avg('score_confiance')
    )

    total = stats['total'] or 0
    correctes = stats['correctes'] or 0

    if total == 0:
        return 1.0  # Pas de donnees

    return correctes / total


# =============================================================================
# CONFIGURATION COTE CLIENT
# =============================================================================

def get_config_reconnaissance_vocale():
    """
    Retourne la configuration pour l'API Web Speech cote client.
    """
    from chatbot.models import ConfigurationChatbot

    try:
        config = ConfigurationChatbot.get_instance()
        return {
            'active': config.reconnaissance_vocale_active,
            'langue': config.langue_defaut,
            'seuil_confiance': float(config.seuil_confiance_vocal),
            'continuous': False,
            'interimResults': True,
            'maxAlternatives': 3,
        }
    except:
        return {
            'active': True,
            'langue': LANGUE_DEFAUT,
            'seuil_confiance': SEUIL_CONFIANCE_DEFAUT,
            'continuous': False,
            'interimResults': True,
            'maxAlternatives': 3,
        }


# =============================================================================
# SYNTHESE VOCALE (Text-to-Speech)
# =============================================================================

def preparer_texte_pour_synthese(texte):
    """
    Prepare un texte pour la synthese vocale.
    Simplifie le formatage markdown et les caracteres speciaux.
    """
    if not texte:
        return ""

    # Supprimer le markdown
    texte = re.sub(r'\*\*(.+?)\*\*', r'\1', texte)  # Gras
    texte = re.sub(r'\*(.+?)\*', r'\1', texte)  # Italique
    texte = re.sub(r'`(.+?)`', r'\1', texte)  # Code

    # Supprimer les listes markdown
    texte = re.sub(r'^[-*]\s+', '', texte, flags=re.MULTILINE)
    texte = re.sub(r'^\d+\.\s+', '', texte, flags=re.MULTILINE)

    # Remplacer les montants formates pour une meilleure prononciation
    texte = re.sub(r'(\d{1,3}(?:\s\d{3})*)\s*FCFA', r'\1 francs CFA', texte)

    # Normaliser les espaces
    texte = re.sub(r'\s+', ' ', texte).strip()

    return texte


def get_config_synthese_vocale():
    """
    Retourne la configuration pour la synthese vocale cote client.
    """
    return {
        'langue': 'fr-FR',
        'rate': 1.0,
        'pitch': 1.0,
        'volume': 1.0,
    }
