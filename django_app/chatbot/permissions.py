"""
Vérification des permissions RBAC pour le chatbot.
IMPORTANT: Toute action DOIT passer par ce module AVANT exécution.

Section 18 DSTD v3.2 - Exigence 4:
"Vérification des autorisations RBAC AVANT toute action"
"""

from functools import wraps
from django.core.cache import cache


# =============================================================================
# MAPPING COMMANDES -> PERMISSIONS REQUISES
# =============================================================================

PERMISSIONS_COMMANDES = {
    # Trésorerie
    'tresorerie_solde': {
        'permission': 'tresorerie.view_comptebancaire',
        'roles': ['huissier', 'comptable', 'admin'],
        'description': 'Consulter les soldes de trésorerie',
    },
    'tresorerie_mouvement': {
        'permission': 'tresorerie.add_mouvementtresorerie',
        'roles': ['huissier', 'comptable', 'admin'],
        'description': 'Créer un mouvement de trésorerie',
    },
    'tresorerie_alerte': {
        'permission': 'tresorerie.view_alertetresorerie',
        'roles': ['huissier', 'comptable', 'admin'],
        'description': 'Consulter les alertes de trésorerie',
    },

    # Comptabilité
    'compta_ecriture': {
        'permission': 'comptabilite.add_ecriturecomptable',
        'roles': ['huissier', 'comptable', 'admin'],
        'description': 'Créer une écriture comptable',
        'critique': True,  # Nécessite validation humaine
    },
    'compta_solde': {
        'permission': 'comptabilite.view_comptecomptable',
        'roles': ['huissier', 'comptable', 'clerc', 'admin'],
        'description': 'Consulter le solde d\'un compte',
    },
    'compta_balance': {
        'permission': 'comptabilite.view_rapportcomptable',
        'roles': ['huissier', 'comptable', 'admin'],
        'description': 'Générer une balance comptable',
    },
    'compta_grand_livre': {
        'permission': 'comptabilite.view_ligneecriture',
        'roles': ['huissier', 'comptable', 'admin'],
        'description': 'Consulter le grand livre',
    },

    # Dossiers
    'dossier_recherche': {
        'permission': 'gestion.view_dossier',
        'roles': ['huissier', 'comptable', 'clerc', 'secretaire', 'admin'],
        'description': 'Rechercher un dossier',
    },
    'dossier_statut': {
        'permission': 'gestion.view_dossier',
        'roles': ['huissier', 'comptable', 'clerc', 'secretaire', 'admin'],
        'description': 'Consulter le statut d\'un dossier',
    },
    'dossier_creer': {
        'permission': 'gestion.add_dossier',
        'roles': ['huissier', 'clerc', 'admin'],
        'description': 'Créer un nouveau dossier',
    },
    'dossier_encaissement': {
        'permission': 'gestion.add_encaissement',
        'roles': ['huissier', 'comptable', 'clerc', 'admin'],
        'description': 'Enregistrer un encaissement',
    },

    # Courriers
    'courrier_generer': {
        'permission': 'documents.add_document',
        'roles': ['huissier', 'clerc', 'secretaire', 'admin'],
        'description': 'Générer un courrier',
    },
    'courrier_liste': {
        'permission': 'documents.view_document',
        'roles': ['huissier', 'comptable', 'clerc', 'secretaire', 'admin'],
        'description': 'Lister les courriers',
    },
    'courrier_envoyer': {
        'permission': 'documents.change_document',
        'roles': ['huissier', 'clerc', 'secretaire', 'admin'],
        'description': 'Envoyer un courrier',
    },

    # Agenda
    'agenda_rdv': {
        'permission': 'agenda.add_rendezvous',
        'roles': ['huissier', 'clerc', 'secretaire', 'admin'],
        'description': 'Créer un rendez-vous',
    },
    'agenda_tache': {
        'permission': 'agenda.add_tache',
        'roles': ['huissier', 'comptable', 'clerc', 'secretaire', 'admin'],
        'description': 'Créer une tâche',
    },
    'agenda_aujourdhui': {
        'permission': 'agenda.view_rendezvous',
        'roles': ['huissier', 'comptable', 'clerc', 'secretaire', 'admin'],
        'description': 'Consulter le programme du jour',
    },

    # Rapports
    'rapport_generer': {
        'permission': 'comptabilite.view_rapportcomptable',
        'roles': ['huissier', 'comptable', 'admin'],
        'description': 'Générer un rapport',
    },

    # Navigation et aide (toujours autorisé)
    'navigation': {
        'permission': None,
        'roles': ['*'],
        'description': 'Navigation dans l\'application',
    },
    'aide': {
        'permission': None,
        'roles': ['*'],
        'description': 'Demande d\'aide',
    },
    'autre': {
        'permission': None,
        'roles': ['*'],
        'description': 'Autre action',
    },
}


# =============================================================================
# FONCTIONS DE VERIFICATION RBAC
# =============================================================================

def verifier_permission_action(utilisateur, action):
    """
    Vérifie si l'utilisateur a la permission d'exécuter l'action.

    Args:
        utilisateur: Instance Utilisateur
        action: Instance ActionDemandee

    Returns:
        (bool, str): (autorisé, raison)
    """
    if not utilisateur or not utilisateur.is_authenticated:
        return False, "Utilisateur non authentifié"

    if not utilisateur.is_active:
        return False, "Compte utilisateur désactivé"

    type_commande = action.type_commande
    config = PERMISSIONS_COMMANDES.get(type_commande)

    if not config:
        return False, f"Commande inconnue: {type_commande}"

    # Commandes toujours autorisées
    if config['roles'] == ['*']:
        return True, "Action autorisée (publique)"

    # Vérifier le rôle de l'utilisateur
    role_utilisateur = getattr(utilisateur, 'role', None)

    if role_utilisateur in config['roles']:
        # Vérifier aussi la permission Django si définie
        permission = config.get('permission')
        if permission:
            if utilisateur.has_perm(permission):
                return True, "Action autorisée"
            else:
                return False, f"Permission Django manquante: {permission}"
        return True, "Action autorisée (rôle)"

    return False, f"Rôle insuffisant. Requis: {', '.join(config['roles'])}"


def verifier_permission_commande(type_commande, utilisateur):
    """
    Vérifie si un utilisateur peut exécuter un type de commande.

    Args:
        type_commande: Code du type de commande
        utilisateur: Instance Utilisateur

    Returns:
        bool: True si autorisé
    """
    config = PERMISSIONS_COMMANDES.get(type_commande)

    if not config:
        return False

    if config['roles'] == ['*']:
        return True

    if not utilisateur or not utilisateur.is_authenticated:
        return False

    role_utilisateur = getattr(utilisateur, 'role', None)
    return role_utilisateur in config['roles']


def est_action_critique(type_commande):
    """
    Vérifie si un type de commande est critique
    (nécessite validation humaine).
    """
    config = PERMISSIONS_COMMANDES.get(type_commande, {})
    return config.get('critique', False)


def obtenir_permissions_utilisateur(utilisateur):
    """
    Retourne la liste des commandes autorisées pour un utilisateur.

    Args:
        utilisateur: Instance Utilisateur

    Returns:
        list: Liste des codes de commandes autorisées
    """
    if not utilisateur or not utilisateur.is_authenticated:
        return ['navigation', 'aide']

    role = getattr(utilisateur, 'role', None)
    commandes_autorisees = []

    for code, config in PERMISSIONS_COMMANDES.items():
        if config['roles'] == ['*'] or role in config['roles']:
            commandes_autorisees.append(code)

    return commandes_autorisees


def obtenir_description_permission(type_commande):
    """Retourne la description d'une permission."""
    config = PERMISSIONS_COMMANDES.get(type_commande, {})
    return config.get('description', 'Action inconnue')


# =============================================================================
# DECORATEUR POUR VUES
# =============================================================================

def require_chatbot_permission(type_commande):
    """
    Décorateur pour vérifier les permissions chatbot sur une vue.

    Usage:
        @require_chatbot_permission('compta_ecriture')
        def ma_vue(request):
            ...
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not verifier_permission_commande(type_commande, request.user):
                from django.http import JsonResponse
                return JsonResponse({
                    'success': False,
                    'error': 'Permission refusée',
                    'message': f"Vous n'avez pas la permission: {obtenir_description_permission(type_commande)}"
                }, status=403)
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator


# =============================================================================
# CACHE DES PERMISSIONS
# =============================================================================

def get_permissions_cache_key(user_id):
    """Génère la clé de cache pour les permissions d'un utilisateur."""
    return f"chatbot_permissions_{user_id}"


def get_cached_permissions(utilisateur):
    """
    Récupère les permissions cachées d'un utilisateur.
    Cache de 5 minutes pour performance.
    """
    if not utilisateur:
        return None

    cache_key = get_permissions_cache_key(utilisateur.id)
    permissions = cache.get(cache_key)

    if permissions is None:
        permissions = obtenir_permissions_utilisateur(utilisateur)
        cache.set(cache_key, permissions, 300)  # 5 minutes

    return permissions


def invalidate_permissions_cache(utilisateur):
    """Invalide le cache des permissions d'un utilisateur."""
    if utilisateur:
        cache_key = get_permissions_cache_key(utilisateur.id)
        cache.delete(cache_key)
