"""
Modes guides pas a pas pour le chatbot.
Section 18 DSTD v3.2 - Exigence 3: "Mode guide pas a pas pour les ecritures comptables"
"""

from enum import Enum


class ModeGuide(str, Enum):
    """Types de modes guides disponibles."""
    ECRITURE_SIMPLE = 'ecriture_simple'
    ECRITURE_FACTURE = 'ecriture_facture'
    ECRITURE_ENCAISSEMENT = 'ecriture_encaissement'
    ECRITURE_SALAIRE = 'ecriture_salaire'
    CREATION_DOSSIER = 'creation_dossier'
    FACTURATION = 'facturation'


# Etapes pour chaque mode guide
ETAPES_MODES = {
    ModeGuide.ECRITURE_SIMPLE: [
        {
            'numero': 1,
            'titre': 'Date de l\'ecriture',
            'question': 'Quelle est la date de l\'ecriture? (format: JJ/MM/AAAA ou "aujourd\'hui")',
            'type_reponse': 'date',
            'champ': 'date_ecriture',
            'obligatoire': True,
        },
        {
            'numero': 2,
            'titre': 'Libelle',
            'question': 'Quel est le libelle de l\'ecriture?',
            'type_reponse': 'texte',
            'champ': 'libelle',
            'obligatoire': True,
        },
        {
            'numero': 3,
            'titre': 'Compte a debiter',
            'question': 'Quel compte voulez-vous debiter? (numero de compte)',
            'type_reponse': 'compte',
            'champ': 'compte_debit',
            'obligatoire': True,
        },
        {
            'numero': 4,
            'titre': 'Compte a crediter',
            'question': 'Quel compte voulez-vous crediter? (numero de compte)',
            'type_reponse': 'compte',
            'champ': 'compte_credit',
            'obligatoire': True,
        },
        {
            'numero': 5,
            'titre': 'Montant',
            'question': 'Quel est le montant en FCFA?',
            'type_reponse': 'montant',
            'champ': 'montant',
            'obligatoire': True,
        },
        {
            'numero': 6,
            'titre': 'Confirmation',
            'question': 'Voulez-vous enregistrer cette ecriture?',
            'type_reponse': 'confirmation',
            'champ': 'confirme',
            'obligatoire': True,
        },
    ],
    ModeGuide.CREATION_DOSSIER: [
        {
            'numero': 1,
            'titre': 'Type de dossier',
            'question': 'Quel type de dossier? (recouvrement, contentieux, amiable)',
            'type_reponse': 'choix',
            'champ': 'type_dossier',
            'options': ['recouvrement', 'contentieux', 'amiable'],
            'obligatoire': True,
        },
        {
            'numero': 2,
            'titre': 'Creancier',
            'question': 'Qui est le creancier? (nom ou reference)',
            'type_reponse': 'texte',
            'champ': 'creancier',
            'obligatoire': True,
        },
        {
            'numero': 3,
            'titre': 'Debiteur',
            'question': 'Qui est le debiteur? (nom)',
            'type_reponse': 'texte',
            'champ': 'debiteur',
            'obligatoire': True,
        },
        {
            'numero': 4,
            'titre': 'Montant de la creance',
            'question': 'Quel est le montant de la creance en FCFA?',
            'type_reponse': 'montant',
            'champ': 'montant_creance',
            'obligatoire': True,
        },
        {
            'numero': 5,
            'titre': 'Confirmation',
            'question': 'Confirmer la creation du dossier?',
            'type_reponse': 'confirmation',
            'champ': 'confirme',
            'obligatoire': True,
        },
    ],
}


def get_etapes_mode(mode):
    """Retourne les etapes pour un mode guide."""
    if isinstance(mode, str):
        mode = ModeGuide(mode)
    return ETAPES_MODES.get(mode, [])


def get_etape_courante(mode, numero_etape):
    """Retourne l'etape courante d'un mode guide."""
    etapes = get_etapes_mode(mode)
    for etape in etapes:
        if etape['numero'] == numero_etape:
            return etape
    return None


def valider_reponse(etape, reponse):
    """Valide une reponse pour une etape."""
    type_reponse = etape.get('type_reponse')
    obligatoire = etape.get('obligatoire', False)

    if not reponse and obligatoire:
        return False, "Cette information est obligatoire."

    if not reponse:
        return True, None

    # Validation selon le type
    if type_reponse == 'montant':
        try:
            montant = float(reponse.replace(' ', '').replace(',', '.'))
            if montant <= 0:
                return False, "Le montant doit etre positif."
        except ValueError:
            return False, "Format de montant invalide."

    elif type_reponse == 'compte':
        if not reponse.isdigit() or len(reponse) < 3:
            return False, "Numero de compte invalide (minimum 3 chiffres)."

    elif type_reponse == 'confirmation':
        reponse_lower = reponse.lower()
        if reponse_lower not in ['oui', 'non', 'o', 'n', 'yes', 'no']:
            return False, "Repondez par 'oui' ou 'non'."

    elif type_reponse == 'choix':
        options = etape.get('options', [])
        if reponse.lower() not in [o.lower() for o in options]:
            return False, f"Choisissez parmi: {', '.join(options)}"

    return True, None


def formater_resume(mode, donnees):
    """Formate un resume des donnees collectees."""
    resume = f"Resume de la demande ({mode}):\n"
    for champ, valeur in donnees.items():
        resume += f"- {champ}: {valeur}\n"
    return resume
