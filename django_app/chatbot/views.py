"""
Vues du module Chatbot.
Interface web et API REST pour le chatbot.
"""

import json
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.db.models import Count, Avg
from datetime import timedelta

from .models import (
    SessionConversation, Message, ActionDemandee,
    ConfigurationChatbot, StatistiquesUtilisation,
    TypeMessage, StatutAction
)
from .permissions import verifier_permission_commande, obtenir_permissions_utilisateur
from .nlp_processor import analyser_message
from .voice_handler import get_config_reconnaissance_vocale, get_config_synthese_vocale


# =============================================================================
# INTERFACE WEB
# =============================================================================

@login_required
def chatbot_home(request):
    """Page principale du chatbot."""
    config = ConfigurationChatbot.get_instance()

    # Récupérer les sessions récentes de l'utilisateur
    sessions = SessionConversation.objects.filter(
        utilisateur=request.user,
        est_active=True
    ).order_by('-date_derniere_activite')[:10]

    # Permissions de l'utilisateur
    permissions = obtenir_permissions_utilisateur(request.user)

    context = {
        'config': config,
        'sessions': sessions,
        'permissions': permissions,
        'config_vocal': get_config_reconnaissance_vocale(),
        'config_synthese': get_config_synthese_vocale(),
    }

    return render(request, 'chatbot/home.html', context)


# =============================================================================
# API REST
# =============================================================================

@login_required
@require_http_methods(["POST"])
def api_envoyer_message(request):
    """
    API pour envoyer un message (fallback si WebSocket indisponible).
    """
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'JSON invalide'}, status=400)

    contenu = data.get('contenu', '').strip()
    session_id = data.get('session_id')

    if not contenu:
        return JsonResponse({'success': False, 'error': 'Message vide'}, status=400)

    # Récupérer ou créer une session
    if session_id:
        session = get_object_or_404(
            SessionConversation,
            id=session_id,
            utilisateur=request.user
        )
    else:
        session = SessionConversation.objects.create(
            utilisateur=request.user,
            canal='api'
        )

    # Sauvegarder le message utilisateur
    message_user = Message.objects.create(
        session=session,
        type_message=TypeMessage.UTILISATEUR,
        contenu=contenu
    )

    # Analyser le message
    analyse = analyser_message(contenu, request.user)

    # Mettre à jour le message avec l'analyse
    message_user.intention_detectee = analyse.get('intention')
    message_user.entites_extraites = analyse.get('entites', {})
    message_user.confiance_intention = analyse.get('confiance')
    message_user.save()

    # Vérifier les permissions
    intention = analyse.get('intention')
    if not verifier_permission_commande(intention, request.user):
        reponse = "Désolé, vous n'avez pas les permissions nécessaires pour cette action."
        type_msg = TypeMessage.ERREUR
    else:
        # Générer une réponse (simplifiée pour l'API REST)
        reponse = generer_reponse_simple(analyse, request.user)
        type_msg = TypeMessage.ASSISTANT

    # Sauvegarder la réponse
    message_reponse = Message.objects.create(
        session=session,
        type_message=type_msg,
        contenu=reponse
    )

    return JsonResponse({
        'success': True,
        'session_id': str(session.id),
        'reponse': {
            'id': str(message_reponse.id),
            'contenu': reponse,
            'type': type_msg,
            'timestamp': message_reponse.date_creation.isoformat()
        },
        'analyse': {
            'intention': analyse.get('intention'),
            'confiance': analyse.get('confiance'),
            'entites': analyse.get('entites', {})
        }
    })


def generer_reponse_simple(analyse, utilisateur):
    """Génère une réponse simple pour l'API REST."""
    intention = analyse.get('intention')

    if intention == 'aide':
        return (
            "Je peux vous aider avec: la trésorerie, la comptabilité, "
            "les dossiers, les courriers et l'agenda. "
            "Que souhaitez-vous faire?"
        )

    if intention == 'tresorerie_solde':
        from .commands import get_solde_tresorerie
        resultat = get_solde_tresorerie(utilisateur)
        return resultat['message']

    if intention == 'agenda_aujourdhui':
        from .commands import get_programme_jour
        resultat = get_programme_jour(utilisateur)
        return resultat['message']

    if intention == 'dossier_recherche':
        terme = analyse.get('entites', {}).get('terme_recherche', '')
        if terme:
            from .commands import rechercher_dossier
            resultat = rechercher_dossier(terme, utilisateur)
            return resultat['message']
        return "Que recherchez-vous? Donnez-moi une référence ou un nom."

    return (
        "Je n'ai pas bien compris. Pour une meilleure expérience, "
        "utilisez l'interface WebSocket temps réel."
    )


@login_required
@require_http_methods(["GET"])
def api_liste_sessions(request):
    """Liste les sessions de l'utilisateur."""
    sessions = SessionConversation.objects.filter(
        utilisateur=request.user
    ).order_by('-date_derniere_activite')[:20]

    data = [{
        'id': str(s.id),
        'titre': s.titre or 'Session sans titre',
        'date_creation': s.date_creation.isoformat(),
        'derniere_activite': s.date_derniere_activite.isoformat(),
        'est_active': s.est_active,
        'nombre_messages': s.nombre_messages,
        'mode_guide_actif': s.mode_guide_actif,
    } for s in sessions]

    return JsonResponse({'success': True, 'sessions': data})


@login_required
@require_http_methods(["GET"])
def api_detail_session(request, session_id):
    """Détail d'une session."""
    session = get_object_or_404(
        SessionConversation,
        id=session_id,
        utilisateur=request.user
    )

    return JsonResponse({
        'success': True,
        'session': {
            'id': str(session.id),
            'titre': session.titre,
            'date_creation': session.date_creation.isoformat(),
            'derniere_activite': session.date_derniere_activite.isoformat(),
            'est_active': session.est_active,
            'canal': session.canal,
            'mode_guide_actif': session.mode_guide_actif,
            'etape_guidage': session.etape_guidage,
            'dossier_contexte_id': str(session.dossier_contexte_id) if session.dossier_contexte_id else None,
        }
    })


@login_required
@require_http_methods(["GET"])
def api_messages_session(request, session_id):
    """Messages d'une session."""
    session = get_object_or_404(
        SessionConversation,
        id=session_id,
        utilisateur=request.user
    )

    messages = session.messages.order_by('date_creation')[:100]

    data = [{
        'id': str(m.id),
        'type': m.type_message,
        'contenu': m.contenu,
        'est_vocal': m.est_vocal,
        'intention': m.intention_detectee,
        'timestamp': m.date_creation.isoformat(),
    } for m in messages]

    return JsonResponse({'success': True, 'messages': data})


# =============================================================================
# VALIDATION DES ACTIONS
# =============================================================================

@login_required
@require_http_methods(["GET"])
def api_actions_en_attente(request):
    """
    Liste les actions en attente de validation.
    Réservé aux superviseurs/huissiers.
    """
    if request.user.role not in ['huissier', 'admin']:
        return JsonResponse({
            'success': False,
            'error': 'Permission refusée'
        }, status=403)

    actions = ActionDemandee.objects.filter(
        statut=StatutAction.VALIDATION_REQUISE,
        validation_humaine_requise=True,
        validateur__isnull=True
    ).order_by('-date_creation')[:50]

    data = [{
        'id': str(a.id),
        'type_commande': a.type_commande,
        'description': a.description,
        'montant': str(a.montant_concerne) if a.montant_concerne else None,
        'niveau_criticite': a.niveau_criticite,
        'date_creation': a.date_creation.isoformat(),
        'demandeur': a.message.session.utilisateur.get_full_name(),
    } for a in actions]

    return JsonResponse({'success': True, 'actions': data})


@login_required
@require_http_methods(["POST"])
def api_valider_action(request, action_id):
    """
    Valide une action en attente.
    Section 18 DSTD v3.2 - Exigence 7: Validation humaine pour écritures critiques.
    """
    if request.user.role not in ['huissier', 'admin']:
        return JsonResponse({
            'success': False,
            'error': 'Seul un huissier ou admin peut valider'
        }, status=403)

    action = get_object_or_404(ActionDemandee, id=action_id)

    if action.statut != StatutAction.VALIDATION_REQUISE:
        return JsonResponse({
            'success': False,
            'error': f'Action non en attente de validation (statut: {action.statut})'
        }, status=400)

    try:
        data = json.loads(request.body)
        commentaire = data.get('commentaire', '')
    except:
        commentaire = ''

    # Valider l'action
    action.valider(request.user, commentaire)

    # Exécuter l'action
    succes, message = action.executer()

    # Notifier l'utilisateur via WebSocket si possible
    notifier_utilisateur_action(action, succes, message)

    return JsonResponse({
        'success': succes,
        'message': message,
        'action_id': str(action.id)
    })


@login_required
@require_http_methods(["POST"])
def api_refuser_action(request, action_id):
    """Refuse une action en attente."""
    if request.user.role not in ['huissier', 'admin']:
        return JsonResponse({
            'success': False,
            'error': 'Permission refusée'
        }, status=403)

    action = get_object_or_404(ActionDemandee, id=action_id)

    try:
        data = json.loads(request.body)
        raison = data.get('raison', 'Refusé par le validateur')
    except:
        raison = 'Refusé par le validateur'

    action.refuser_validation(request.user, raison)

    # Notifier l'utilisateur
    notifier_utilisateur_action(action, False, f"Action refusée: {raison}")

    return JsonResponse({
        'success': True,
        'message': 'Action refusée',
        'action_id': str(action.id)
    })


def notifier_utilisateur_action(action, succes, message):
    """Notifie l'utilisateur du résultat d'une action via WebSocket."""
    try:
        from channels.layers import get_channel_layer
        from asgiref.sync import async_to_sync

        channel_layer = get_channel_layer()
        utilisateur = action.message.session.utilisateur
        group_name = f"chatbot_user_{utilisateur.id}"

        async_to_sync(channel_layer.group_send)(
            group_name,
            {
                'type': 'validation_completee',
                'action_id': str(action.id),
                'statut': 'succes' if succes else 'erreur',
                'message': message
            }
        )
    except Exception as e:
        # Fallback: notification en base (sera vue au prochain chargement)
        pass


# =============================================================================
# CONFIGURATION
# =============================================================================

@login_required
@require_http_methods(["GET"])
def api_configuration(request):
    """Retourne la configuration du chatbot."""
    config = ConfigurationChatbot.get_instance()

    return JsonResponse({
        'success': True,
        'config': {
            'actif': config.actif,
            'nom_assistant': config.nom_assistant,
            'message_bienvenue': config.message_bienvenue,
            'seuil_confirmation_fcfa': str(config.seuil_confirmation_fcfa),
            'reconnaissance_vocale_active': config.reconnaissance_vocale_active,
            'langue_defaut': config.langue_defaut,
        }
    })


@login_required
@require_http_methods(["GET"])
def api_config_vocal(request):
    """Retourne la configuration de la reconnaissance vocale."""
    return JsonResponse({
        'success': True,
        'reconnaissance': get_config_reconnaissance_vocale(),
        'synthese': get_config_synthese_vocale()
    })


# =============================================================================
# STATISTIQUES
# =============================================================================

@login_required
@require_http_methods(["GET"])
def api_statistiques(request):
    """Retourne les statistiques d'utilisation du chatbot."""
    if request.user.role not in ['huissier', 'admin', 'comptable']:
        # Statistiques personnelles uniquement
        stats = calculer_stats_utilisateur(request.user)
    else:
        # Statistiques globales
        stats = calculer_stats_globales()

    return JsonResponse({'success': True, 'stats': stats})


def calculer_stats_utilisateur(utilisateur):
    """Calcule les statistiques pour un utilisateur."""
    date_debut = timezone.now() - timedelta(days=30)

    sessions = SessionConversation.objects.filter(
        utilisateur=utilisateur,
        date_creation__gte=date_debut
    )

    messages = Message.objects.filter(
        session__utilisateur=utilisateur,
        date_creation__gte=date_debut
    )

    actions = ActionDemandee.objects.filter(
        message__session__utilisateur=utilisateur,
        date_creation__gte=date_debut
    )

    return {
        'periode': '30 derniers jours',
        'sessions': sessions.count(),
        'messages': messages.count(),
        'messages_vocaux': messages.filter(est_vocal=True).count(),
        'actions_executees': actions.filter(statut=StatutAction.EXECUTEE).count(),
        'actions_refusees': actions.filter(statut=StatutAction.REFUSEE).count(),
    }


def calculer_stats_globales():
    """Calcule les statistiques globales."""
    date_debut = timezone.now() - timedelta(days=30)

    sessions = SessionConversation.objects.filter(date_creation__gte=date_debut)
    messages = Message.objects.filter(date_creation__gte=date_debut)
    actions = ActionDemandee.objects.filter(date_creation__gte=date_debut)

    # Répartition par intention
    repartition = messages.filter(
        type_message=TypeMessage.UTILISATEUR,
        intention_detectee__isnull=False
    ).values('intention_detectee').annotate(
        count=Count('id')
    ).order_by('-count')[:10]

    return {
        'periode': '30 derniers jours',
        'sessions_totales': sessions.count(),
        'utilisateurs_uniques': sessions.values('utilisateur').distinct().count(),
        'messages_totaux': messages.count(),
        'messages_vocaux': messages.filter(est_vocal=True).count(),
        'actions_executees': actions.filter(statut=StatutAction.EXECUTEE).count(),
        'actions_refusees': actions.filter(statut=StatutAction.REFUSEE).count(),
        'actions_en_attente': actions.filter(statut=StatutAction.VALIDATION_REQUISE).count(),
        'temps_reponse_moyen_ms': messages.filter(
            temps_traitement_ms__isnull=False
        ).aggregate(Avg('temps_traitement_ms'))['temps_traitement_ms__avg'] or 0,
        'repartition_intentions': list(repartition),
    }


# =============================================================================
# MAINTENANCE
# =============================================================================

@require_http_methods(["POST"])
def api_nettoyer_sessions(request):
    """
    Nettoie les sessions expirées.
    À appeler via un cron job quotidien.
    Section 18 DSTD v3.2 - Exigence 6: "Historique conservé 90 jours"
    """
    # Vérifier un token d'API ou IP autorisée
    api_token = request.headers.get('X-API-Token')
    expected_token = getattr(settings, 'CHATBOT_CLEANUP_TOKEN', None)

    if expected_token and api_token != expected_token:
        return JsonResponse({
            'success': False,
            'error': 'Token invalide'
        }, status=403)

    # Nettoyer les sessions expirées
    count = SessionConversation.nettoyer_sessions_expirees()

    return JsonResponse({
        'success': True,
        'sessions_supprimees': count,
        'timestamp': timezone.now().isoformat()
    })


# Import settings for token verification
from django.conf import settings
