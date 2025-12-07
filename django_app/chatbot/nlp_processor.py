"""
Processeur NLP pour l'analyse des messages en francais.
Section 18 DSTD v3.2 - Exigence 2: "Commandes vocales en francais"

Analyse:
- Detection d'intention (tresorerie, comptabilite, dossiers, courriers)
- Extraction d'entites (montants, dates, references)
- Normalisation du texte francais
"""

import re
from decimal import Decimal, InvalidOperation
from datetime import datetime, timedelta
from django.utils import timezone


# =============================================================================
# PATTERNS DE RECONNAISSANCE D'INTENTIONS
# =============================================================================

PATTERNS_INTENTIONS = {
    # TRESORERIE
    'tresorerie_solde': [
        r'\b(solde|situation|etat)\b.*(caisse|banque|tresorerie|compte)',
        r'\b(caisse|banque|tresorerie)\b.*(solde|combien|montant)',
        r'combien\b.*(caisse|banque|tresorerie|disponible)',
        r'quel\s+(est\s+le\s+)?solde',
        r'voir\s+(la\s+)?tresorerie',
        r'consulter\s+(la\s+)?tresorerie',
    ],
    'tresorerie_mouvement': [
        r'(creer|faire|enregistrer|nouveau)\b.*mouvement',
        r'mouvement\s+(de\s+)?(caisse|banque|tresorerie)',
        r'(encaisser|decaisser)\b',
        r'(entree|sortie)\s+(de\s+)?(caisse|fonds|argent)',
    ],
    'tresorerie_alerte': [
        r'alerte.*(tresorerie|caisse|banque)',
        r'(tresorerie|caisse|banque).*alerte',
        r'seuil.*(tresorerie|caisse)',
    ],

    # COMPTABILITE
    'compta_ecriture': [
        r'(creer|passer|enregistrer|faire)\b.*(ecriture|operation)\s*comptable',
        r'(ecriture|operation)\s*comptable',
        r'comptabiliser',
        r'(nouvelle|creer)\s+ecriture',
        r'passer\s+(une\s+)?ecriture',
    ],
    'compta_solde': [
        r'solde\s*(du\s+)?compte\s*(\d+)?',
        r'compte\s*(\d+)\s*.*(solde|situation)',
        r'quel\s+(est\s+le\s+)?solde\s*(du\s+)?(\d+)',
        r'consulter\s*(le\s+)?compte\s*(\d+)?',
    ],
    'compta_balance': [
        r'(generer|voir|afficher|sortir)\s*(la\s+)?balance',
        r'balance\s*(generale|comptable)?',
        r'etat\s+des\s+comptes',
    ],
    'compta_grand_livre': [
        r'grand\s*livre',
        r'(voir|consulter)\s*(le\s+)?grand\s*livre',
        r'mouvements\s*(du\s+)?compte',
    ],

    # DOSSIERS
    'dossier_recherche': [
        r'(rechercher|trouver|chercher)\s*(un\s+)?dossier',
        r'dossier\s+(de|du|pour)\s+',
        r'ou\s+est\s+(le\s+)?dossier',
        r'(afficher|voir)\s+(le\s+)?dossier',
    ],
    'dossier_statut': [
        r'(statut|etat|situation)\s*(du\s+)?dossier',
        r'dossier\s*(\d+[/-]\d+)\s*.*(statut|etat)',
        r'ou\s+en\s+est\s+(le\s+)?dossier',
        r'avancement\s*(du\s+)?dossier',
    ],
    'dossier_creer': [
        r'(creer|ouvrir|nouveau)\s*(un\s+)?dossier',
        r'(nouveau|nouvelle)\s+affaire',
        r'ouvrir\s+(une\s+)?procedure',
    ],
    'dossier_encaissement': [
        r'(enregistrer|saisir|faire)\s*(un\s+)?encaissement',
        r'encaissement\s+(de|sur|pour)',
        r'(recevoir|recu)\s*(un\s+)?paiement',
        r'(client|debiteur)\s+(a\s+)?paye',
        r'reglement\s+(recu|entrant)',
    ],

    # COURRIERS
    'courrier_generer': [
        r'(generer|creer|faire|rediger)\s*(un\s+)?(courrier|lettre|mise\s+en\s+demeure|commandement)',
        r'(mise\s+en\s+demeure|commandement|relance|convocation)',
        r'(envoyer|preparer)\s*(une\s+)?lettre',
    ],
    'courrier_liste': [
        r'(liste|voir|afficher)\s*(les\s+)?courriers',
        r'courriers\s+(envoyes|en\s+attente)',
        r'historique\s+(des\s+)?courriers',
    ],
    'courrier_envoyer': [
        r'envoyer\s*(le\s+)?courrier',
        r'expedier\s*(la\s+)?lettre',
        r'poster\s*(le\s+)?document',
    ],

    # AGENDA
    'agenda_rdv': [
        r'(creer|prendre|fixer|planifier)\s*(un\s+)?(rendez-vous|rdv)',
        r'(nouveau|nouvelle)\s+(rendez-vous|rdv)',
        r'(rdv|rendez-vous)\s+(avec|pour|le)',
    ],
    'agenda_tache': [
        r'(creer|ajouter|nouvelle)\s*(une\s+)?tache',
        r'(tache|todo)\s+(a\s+faire|pour)',
        r'(rappeler|rappel)\s+(de|pour)',
        r'a\s+faire',
    ],
    'agenda_aujourdhui': [
        r"(programme|planning|agenda)\s*(d'aujourd'hui|du\s+jour)",
        r"(qu'est-ce\s+que\s+)?j'ai\s+aujourd'hui",
        r"(mes\s+)?(rendez-vous|rdv|taches)\s+(d')?aujourd",
        r"aujourd'hui",
        r'ce\s+jour',
    ],

    # RAPPORTS
    'rapport_generer': [
        r'(generer|creer|faire|sortir)\s*(un\s+)?rapport',
        r'rapport\s+(de|sur|du)',
        r'(statistiques|stats)\s+(de|sur)',
        r'bilan\s+(mensuel|annuel|du\s+mois)',
    ],

    # NAVIGATION
    'navigation': [
        r'(aller|acceder|ouvrir)\s+(a|au|aux|la|le)\s+',
        r'(montre|affiche|voir)\s*(moi\s+)?(le|la|les)\s+',
        r'(ou\s+est|comment\s+acceder)',
        r'page\s+(de|du|des)',
    ],

    # AIDE
    'aide': [
        r'\b(aide|help|assistance)\b',
        r"(que|qu'est-ce\s+que)\s+(tu\s+)?peux\s+(tu\s+)?faire",
        r'(comment|quoi)\s+(faire|ca\s+marche)',
        r'commandes\s+disponibles',
        r"(besoin\s+d')?aide",
    ],
}


# =============================================================================
# PATTERNS D'EXTRACTION D'ENTITES
# =============================================================================

# Montants en FCFA
PATTERN_MONTANT = re.compile(
    r'(\d[\d\s]*(?:[,\.]\d+)?)\s*'
    r'(?:fcfa|f\s*cfa|francs?\s*cfa|cfa|francs?|xof)?',
    re.IGNORECASE
)

# Numeros de compte comptable
PATTERN_COMPTE = re.compile(r'\b(\d{3,8})\b')

# References de dossier (format: YYYY/NNN ou NNN/YYYY ou NNN-YYYY)
PATTERN_REFERENCE_DOSSIER = re.compile(
    r'\b(\d{4}[/-]\d{1,4}|\d{1,4}[/-]\d{4})\b'
)

# Dates en francais
PATTERN_DATE_FR = re.compile(
    r'\b(\d{1,2})[/\-\.](\d{1,2})[/\-\.](\d{2,4})\b'
)

# Mots-cles de date relative
DATES_RELATIVES = {
    "aujourd'hui": 0,
    "aujourdhui": 0,
    "demain": 1,
    "apres-demain": 2,
    "hier": -1,
    "avant-hier": -2,
}

# Jours de la semaine
JOURS_SEMAINE = {
    'lundi': 0, 'mardi': 1, 'mercredi': 2, 'jeudi': 3,
    'vendredi': 4, 'samedi': 5, 'dimanche': 6
}


# =============================================================================
# NORMALISATION DU TEXTE
# =============================================================================

def normaliser_texte(texte):
    """
    Normalise le texte francais pour l'analyse.
    - Convertit en minuscules
    - Normalise les apostrophes
    - Supprime la ponctuation excessive
    - Normalise les espaces
    """
    if not texte:
        return ""

    texte = texte.lower()

    # Normaliser les apostrophes
    texte = re.sub(r"['`]", "'", texte)

    # Remplacer la ponctuation par des espaces (sauf apostrophes)
    texte = re.sub(r"[^\w\s'\-/]", ' ', texte)

    # Normaliser les espaces multiples
    texte = re.sub(r'\s+', ' ', texte).strip()

    return texte


def corriger_orthographe_commune(texte):
    """Corrige les erreurs d'orthographe courantes en francais."""
    corrections = {
        'tresorerie': 'tresorerie',
        'ecrit': 'ecrit',
        'ecriture': 'ecriture',
        'comptabilite': 'comptabilite',
        'creance': 'creance',
        'creancier': 'creancier',
        'debiteur': 'debiteur',
        'regle': 'regle',
        'reglement': 'reglement',
        'factur': 'facture',
        'encaissment': 'encaissement',
        'solde compte': 'solde du compte',
    }

    for erreur, correction in corrections.items():
        texte = texte.replace(erreur, correction)

    return texte


# =============================================================================
# EXTRACTION D'ENTITES
# =============================================================================

def extraire_montant(texte):
    """
    Extrait un montant en FCFA du texte.
    Retourne un Decimal ou None.
    """
    match = PATTERN_MONTANT.search(texte)
    if match:
        montant_str = match.group(1)
        # Nettoyer le montant
        montant_str = re.sub(r'\s', '', montant_str)
        montant_str = montant_str.replace(',', '.')

        try:
            return Decimal(montant_str)
        except InvalidOperation:
            return None
    return None


def extraire_numero_compte(texte):
    """
    Extrait un numero de compte comptable du texte.
    Retourne une string ou None.
    """
    match = PATTERN_COMPTE.search(texte)
    if match:
        numero = match.group(1)
        # Valider que c'est un numero de compte plausible (3-8 chiffres)
        if 3 <= len(numero) <= 8:
            return numero
    return None


def extraire_reference_dossier(texte):
    """
    Extrait une reference de dossier du texte.
    Retourne une string ou None.
    """
    match = PATTERN_REFERENCE_DOSSIER.search(texte)
    if match:
        return match.group(1)
    return None


def extraire_date(texte):
    """
    Extrait une date du texte.
    Gere les dates absolues et relatives.
    Retourne un objet date ou None.
    """
    texte_lower = texte.lower()

    # Dates relatives
    for mot, delta in DATES_RELATIVES.items():
        if mot in texte_lower:
            return (timezone.now() + timedelta(days=delta)).date()

    # Jours de la semaine
    for jour, num_jour in JOURS_SEMAINE.items():
        if jour in texte_lower:
            aujourdhui = timezone.now().date()
            jour_actuel = aujourdhui.weekday()
            delta = (num_jour - jour_actuel) % 7
            if delta == 0:
                delta = 7  # Prochain occurrence
            return aujourdhui + timedelta(days=delta)

    # Date absolue (format francais: JJ/MM/AAAA)
    match = PATTERN_DATE_FR.search(texte)
    if match:
        jour, mois, annee = match.groups()
        jour, mois = int(jour), int(mois)
        annee = int(annee)

        # Normaliser l'annee a 4 chiffres
        if annee < 100:
            annee += 2000 if annee < 50 else 1900

        try:
            return datetime(annee, mois, jour).date()
        except ValueError:
            return None

    return None


def extraire_nom_partie(texte):
    """
    Tente d'extraire un nom de partie du texte.
    Retourne une string ou None.
    """
    # Patterns pour detecter un nom apres certains mots-cles
    patterns = [
        r'dossier\s+(?:de|du|pour)\s+(\w+(?:\s+\w+)?)',
        r'client\s+(\w+(?:\s+\w+)?)',
        r'(?:monsieur|madame|m\.|mme)\s+(\w+(?:\s+\w+)?)',
        r'societe\s+(\w+(?:\s+\w+)?)',
    ]

    for pattern in patterns:
        match = re.search(pattern, texte, re.IGNORECASE)
        if match:
            nom = match.group(1).strip()
            # Filtrer les mots communs qui ne sont pas des noms
            mots_exclus = {'le', 'la', 'les', 'un', 'une', 'des', 'du', 'de'}
            if nom.lower() not in mots_exclus and len(nom) > 1:
                return nom

    return None


def extraire_toutes_entites(texte):
    """
    Extrait toutes les entites detectables du texte.
    Retourne un dictionnaire.
    """
    entites = {}

    montant = extraire_montant(texte)
    if montant:
        entites['montant'] = str(montant)

    numero_compte = extraire_numero_compte(texte)
    if numero_compte:
        entites['numero_compte'] = numero_compte

    reference = extraire_reference_dossier(texte)
    if reference:
        entites['reference_dossier'] = reference

    date = extraire_date(texte)
    if date:
        entites['date'] = date.isoformat()

    nom = extraire_nom_partie(texte)
    if nom:
        entites['terme_recherche'] = nom

    return entites


# =============================================================================
# DETECTION D'INTENTION
# =============================================================================

def detecter_intention(texte):
    """
    Detecte l'intention principale du message.
    Retourne (intention, score_confiance).
    """
    texte_normalise = normaliser_texte(texte)
    texte_corrige = corriger_orthographe_commune(texte_normalise)

    meilleure_intention = 'autre'
    meilleur_score = 0

    for intention, patterns in PATTERNS_INTENTIONS.items():
        for pattern in patterns:
            match = re.search(pattern, texte_corrige, re.IGNORECASE)
            if match:
                # Calculer un score base sur la longueur du match
                score = len(match.group(0)) / len(texte_corrige)
                score = min(score + 0.5, 1.0)  # Bonus de base

                if score > meilleur_score:
                    meilleur_score = score
                    meilleure_intention = intention

    return meilleure_intention, meilleur_score


# =============================================================================
# FONCTION PRINCIPALE D'ANALYSE
# =============================================================================

def analyser_message(texte, utilisateur=None):
    """
    Analyse complete d'un message.

    Args:
        texte: Le message a analyser
        utilisateur: L'utilisateur (pour contexte)

    Returns:
        dict: {
            'intention': str,
            'confiance': float,
            'entites': dict,
            'texte_normalise': str
        }
    """
    if not texte:
        return {
            'intention': 'autre',
            'confiance': 0,
            'entites': {},
            'texte_normalise': ''
        }

    # Normaliser le texte
    texte_normalise = normaliser_texte(texte)
    texte_corrige = corriger_orthographe_commune(texte_normalise)

    # Detecter l'intention
    intention, confiance = detecter_intention(texte_corrige)

    # Extraire les entites
    entites = extraire_toutes_entites(texte_corrige)

    # Enrichir avec le contexte utilisateur si disponible
    if utilisateur:
        # Potentiellement recuperer le dossier en contexte
        pass

    return {
        'intention': intention,
        'confiance': confiance,
        'entites': entites,
        'texte_normalise': texte_normalise
    }


# =============================================================================
# UTILITAIRES
# =============================================================================

def formater_montant(montant):
    """Formate un montant en FCFA pour affichage."""
    if isinstance(montant, str):
        try:
            montant = Decimal(montant)
        except:
            return montant

    return f"{montant:,.0f} FCFA".replace(',', ' ')


def est_question(texte):
    """Determine si le texte est une question."""
    texte = texte.strip()
    if texte.endswith('?'):
        return True

    mots_interrogatifs = [
        'qui', 'que', 'quoi', 'quel', 'quelle', 'quels', 'quelles',
        'ou', 'quand', 'comment', 'pourquoi', 'combien', "est-ce que"
    ]

    texte_lower = texte.lower()
    return any(texte_lower.startswith(mot) for mot in mots_interrogatifs)


def detecter_negation(texte):
    """Detecte si le message contient une negation."""
    patterns_negation = [
        r'\bne\b.*\bpas\b',
        r'\bne\b.*\bplus\b',
        r'\bne\b.*\bjamais\b',
        r'\bnon\b',
        r'\bpas\s+de\b',
        r'\baucun',
        r'\bsans\b',
    ]

    texte_lower = texte.lower()
    return any(re.search(p, texte_lower) for p in patterns_negation)
